"""
eval/retriever/metrics.py
=========================
DeepEval metrics tailored for RAG Retriever evaluation:
1. ContextualRelevancyMetric  - Are retrieved chunks relevant to the user query?
2. ContextualRecallMetric     - Does the context capture all facts in expected output?
3. ContextualPrecisionMetric  - Are the highest relevance chunks ranked at the top?
"""

from __future__ import annotations
from typing import Optional
from deepeval.metrics import (
    ContextualRelevancyMetric,
    ContextualRecallMetric,
    ContextualPrecisionMetric,
)
from eval.judge import GeminiJudge


def get_retriever_metrics(
    judge: Optional[GeminiJudge] = None,
    threshold: float = 0.7,
    include_reason: bool = True,
) -> list:
    """
    Returns configured DeepEval retriever metrics powered by the Gemini judge.

    Args:
        judge: GeminiJudge instance (creates one if not provided).
        threshold: Minimum score threshold (0.0 to 1.0) to pass the test.
        include_reason: Whether the LLM judge should provide an explanation.

    Returns:
        list: [ContextualRelevancyMetric, ContextualRecallMetric, ContextualPrecisionMetric]
    """
    eval_model = judge or GeminiJudge()

    relevancy_metric = ContextualRelevancyMetric(
        threshold=threshold,
        model=eval_model,
        include_reason=include_reason,
    )

    recall_metric = ContextualRecallMetric(
        threshold=threshold,
        model=eval_model,
        include_reason=include_reason,
    )

    precision_metric = ContextualPrecisionMetric(
        threshold=threshold,
        model=eval_model,
        include_reason=include_reason,
    )

    return [relevancy_metric, recall_metric, precision_metric]
