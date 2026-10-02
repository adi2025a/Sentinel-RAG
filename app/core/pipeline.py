"""
app/core/pipeline.py
====================
Unified SentinelRAG Pipeline

Merges:
  - Ingestion  : PDF → text → chunks → vector store
  - Security   : PID (RegexDetector + FAISS semantic scorer)
  - Retrieval  : vector store similarity search
  - Generation : LLM answer with retrieved context

Callers (API, dashboard, CLI) import SentinelPipeline and call:
    pipeline.ingest(contents)          → IngestResult
    pipeline.query(query_text)         → QueryResult
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.rag import (
    secure_pdf_to_text,
    split_text_into_chunks,
    get_embedder,
    build_vector_store,
    search_query,
    answer_query_with_context,
)
from app.security import PIDPipeline, PIDResult, Decision, RegexDetector
from app.utils.logger import get_logger

logger = get_logger(name=__name__)


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------

class IngestStatus(str, Enum):
    OK      = "OK"
    FAILED  = "FAILED"


@dataclass
class IngestResult:
    status:      IngestStatus
    num_chunks:  int   = 0
    elapsed_ms:  float = 0.0
    error:       str   = ""

    def __str__(self) -> str:
        if self.status == IngestStatus.OK:
            return (
                f"[IngestResult] OK — {self.num_chunks} chunks "
                f"in {self.elapsed_ms:.0f}ms"
            )
        return f"[IngestResult] FAILED — {self.error}"


@dataclass
class QueryResult:
    query:         str
    answer:        str
    decision:      Decision
    pid:           PIDResult
    sources:       list[str]      = field(default_factory=list)
    elapsed_ms:    float          = 0.0
    blocked:       bool           = False
    block_reason:  str            = ""

    def __str__(self) -> str:
        if self.blocked:
            return (
                f"[QueryResult] BLOCKED\n"
                f"  Query    : {self.query!r}\n"
                f"  Reason   : {self.block_reason}\n"
                f"  PID score: {self.pid.fused_score:.3f} "
                f"({self.pid.risk_level.value})"
            )
        return (
            f"[QueryResult] ALLOWED — {self.elapsed_ms:.0f}ms\n"
            f"  Query    : {self.query!r}\n"
            f"  PID score: {self.pid.fused_score:.3f} "
            f"({self.pid.risk_level.value})\n"
            f"  Answer   : {self.answer[:120]}{'...' if len(self.answer) > 120 else ''}"
        )


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

class SentinelPipeline:
    """
    Single entry-point for all SentinelRAG operations.

    Parameters
    ----------
    pid_block_threshold  : fused PID score that triggers a BLOCK (default 0.65)
    pid_review_threshold : fused PID score that triggers a REVIEW log (default 0.40)
    retrieval_top_k      : number of chunks to retrieve per query (default 4)
    semantic_top_k       : FAISS neighbours for semantic PID scoring (default 5)
    """

    def __init__(
        self,
        pid_block_threshold:  float = 0.65,
        pid_review_threshold: float = 0.40,
        retrieval_top_k:      int   = 4,
        semantic_top_k:       int   = 5,
    ):
        self.retrieval_top_k = retrieval_top_k

        logger.info("Initialising SentinelPipeline...")

        self._pid = PIDPipeline(
            block_threshold  = pid_block_threshold,
            review_threshold = pid_review_threshold,
            top_k            = semantic_top_k,
        )

        self._embedder      = get_embedder()
        self._vector_store  = None   # populated after first ingest()

        logger.info("SentinelPipeline ready.")

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    def ingest(self, contents: Any) -> IngestResult:
        """
        Full ingestion pipeline: PDF bytes → text → chunks → vector store.

        Parameters
        ----------
        contents : raw PDF bytes (same as your existing secure_pdf_to_text input)

        Returns
        -------
        IngestResult
        """
        t0 = time.perf_counter()
        logger.info("Pipeline: ingestion started.")

        try:
            # 1. Extract text
            text = secure_pdf_to_text(contents)
            logger.info("Pipeline: text extraction complete.")

            # 2. Chunk
            chunks = split_text_into_chunks(text)
            logger.info(f"Pipeline: {len(chunks)} chunks produced.")

            # 3. Build / rebuild vector store
            self._vector_store = build_vector_store(chunks, self._embedder)
            logger.info("Pipeline: vector store built.")

        except Exception as exc:
            logger.error(f"Pipeline: ingestion failed — {exc}")
            return IngestResult(
                status    = IngestStatus.FAILED,
                elapsed_ms= (time.perf_counter() - t0) * 1000,
                error     = str(exc),
            )

        elapsed = (time.perf_counter() - t0) * 1000
        logger.info(f"Pipeline: ingestion complete in {elapsed:.0f}ms.")
        return IngestResult(
            status     = IngestStatus.OK,
            num_chunks = len(chunks),
            elapsed_ms = elapsed,
        )

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def query(self, query_text: str) -> QueryResult:
        """
        Full query pipeline: PID check → retrieval → LLM answer.

        Parameters
        ----------
        query_text : raw user query string

        Returns
        -------
        QueryResult  (blocked=True if PID rejects the query)
        """
        if self._vector_store is None:
            raise RuntimeError(
                "No documents ingested yet. Call pipeline.ingest() first."
            )

        t0 = time.perf_counter()
        logger.info(f"Pipeline: query received — {query_text!r}")

        # ── Stage 1: PID security check ──────────────────────────────
        pid_result = self._pid.run(query_text)
        logger.info(
            f"Pipeline: PID — fused={pid_result.fused_score:.3f} "
            f"risk={pid_result.risk_level.value} "
            f"decision={pid_result.decision.value}"
        )

        if pid_result.decision == Decision.BLOCK:
            logger.warning(
                f"Pipeline: BLOCKED query — score={pid_result.fused_score:.3f} "
                f"risk={pid_result.risk_level.value}"
            )
            return QueryResult(
                query        = query_text,
                answer       = "",
                decision     = pid_result.decision,
                pid          = pid_result,
                blocked      = True,
                block_reason = (
                    f"Query flagged as {pid_result.risk_level.value} "
                    f"(score {pid_result.fused_score:.2f}). Request denied."
                ),
                elapsed_ms   = (time.perf_counter() - t0) * 1000,
            )

        if pid_result.decision == Decision.REVIEW:
            logger.warning(
                f"Pipeline: REVIEW flag on query — "
                f"score={pid_result.fused_score:.3f}. Allowing with audit log."
            )

        # ── Stage 2: Retrieval ────────────────────────────────────────
        results = search_query(query_text)
        logger.info(f"Pipeline: {len(results)} chunks retrieved.")

        sources = [res.page_content for res in results]

        for i, res in enumerate(results):
            logger.debug(f"Pipeline: chunk {i+1} — {res.page_content[:80]}...")

        # ── Stage 3: LLM generation ───────────────────────────────────
        answer = answer_query_with_context(sources, query_text)
        logger.info("Pipeline: LLM answer generated.")

        elapsed = (time.perf_counter() - t0) * 1000
        logger.info(f"Pipeline: query complete in {elapsed:.0f}ms.")

        return QueryResult(
            query      = query_text,
            answer     = answer,
            decision   = pid_result.decision,
            pid        = pid_result,
            sources    = sources,
            elapsed_ms = elapsed,
            blocked    = False,
        )

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    @property
    def is_ready(self) -> bool:
        """True once a document has been ingested."""
        return self._vector_store is not None

    def status(self) -> dict:
        """Return a summary dict suitable for a /health endpoint."""
        return {
            "ready":           self.is_ready,
            "pid_patterns":    self._pid._regex.summary(),
            "retrieval_top_k": self.retrieval_top_k,
        }