"""
app/main.py
===========
SentinelRAG — FastAPI application

Routes
------
POST /admin/upload-pdf/   — ingest a PDF into the vector store (admin only)
POST /user/query/         — query the RAG pipeline (PID-protected)
GET  /health              — pipeline status
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Query, Header, HTTPException, Depends
from fastapi.responses import JSONResponse

from app.core.pipeline import SentinelPipeline, IngestStatus, Decision
from app.utils.logger import get_logger

logger = get_logger(name=__name__)


# ---------------------------------------------------------------------------
# Pipeline — single instance, lives for the lifetime of the process
# ---------------------------------------------------------------------------

pipeline = SentinelPipeline(
    pid_block_threshold  = float(os.getenv("PID_BLOCK_THRESHOLD",  "0.65")),
    pid_review_threshold = float(os.getenv("PID_REVIEW_THRESHOLD", "0.40")),
    retrieval_top_k      = int(os.getenv("RETRIEVAL_TOP_K",        "4")),
)


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("SentinelRAG API starting up.")
    yield
    logger.info("SentinelRAG API shutting down.")

app = FastAPI(
    title       = "SentinelRAG",
    description = "Secure RAG pipeline with prompt injection detection.",
    version     = "0.1.0",
    lifespan    = lifespan,
)


# ---------------------------------------------------------------------------
# Auth dependency
# ---------------------------------------------------------------------------

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")   

def require_admin(x_admin_token: str = Header(..., description="Admin bearer token")):
    """
    Reads the token from the X-Admin-Token header instead of a query param
    so it never appears in server logs or browser history.
    """
    if x_admin_token != ADMIN_TOKEN:
        logger.warning("Unauthorised admin access attempt.")
        raise HTTPException(status_code=403, detail="Not authorised.")
    return True



# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/health", tags=["system"])
async def health():
    """Liveness + pipeline readiness check."""
    status = pipeline.status()
    return JSONResponse(content={
        "ready":        status["ready"],
        "pid_patterns": status["pid_patterns"]["total_patterns"],
        "fuzzy_phrases": status["pid_patterns"]["fuzzy_phrases"],
    })


@app.post("/admin/upload-pdf/", tags=["admin"])
async def upload_pdf(
    file:       UploadFile = File(...),
    _:          bool       = Depends(require_admin),
):
    """
    Ingest a PDF into the vector store.
    Replaces the previous document — call again to re-ingest.
    """
    if file.content_type not in ("application/pdf",):
        raise HTTPException(status_code=415, detail="Only PDF files are accepted.")

    logger.info(f"Admin upload: {file.filename}")
    contents = await file.read()

    result = pipeline.ingest(contents)

    if result.status == IngestStatus.FAILED:
        logger.error(f"Ingestion failed: {result.error}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {result.error}")

    return JSONResponse(content={
        "filename":    file.filename,
        "chunks":      result.num_chunks,
        "elapsed_ms":  round(result.elapsed_ms, 1),
        "message":     f"'{file.filename}' ingested successfully.",
    })


@app.post("/user/query/", tags=["user"])
async def user_query(
    query: str = Query(..., min_length=1, max_length=1000, description="User query string"),
):
    """
    Query the RAG pipeline.
    Returns a 400 if the query is flagged as a prompt injection attempt.
    """
    if not pipeline.is_ready:
        raise HTTPException(
            status_code=503,
            detail="No documents ingested yet. Ask an admin to upload a PDF first.",
        )

    result = pipeline.query(query)

    if result.blocked:
        logger.warning(f"Blocked query: score={result.pid.fused_score:.3f}")
        raise HTTPException(status_code=400, detail=result.block_reason)

    return JSONResponse(content={
        "query":      result.query,
        "answer":     result.answer,
        "pid": {
            "score":      result.pid.fused_score,
            "risk_level": result.pid.risk_level.value,
            "decision":   result.pid.decision.value,
            "regex_score":    result.pid.regex_score,
            "semantic_score": result.pid.semantic_score,
        },
        "elapsed_ms": round(result.elapsed_ms, 1),
    })