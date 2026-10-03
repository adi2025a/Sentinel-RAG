"""
eval/generator/metrics.py
=========================
DeepEval metrics tailored for RAG Generator (LLM) evaluation:
1. FaithfulnessMetric    - Is the answer factually grounded in the retrieved chunks? (No hallucinations)
2. AnswerRelevancyMetric - Does the answer directly address the user's question?
3. HallucinationMetric   - Quantifies hallucination contradictions against context.
"""

from __future__ import annotations
from typing import Optional
from deepeval.metrics import (
    FaithfulnessMetric,
    AnswerRelevancyMetric,
    HallucinationMetric,
)
from eval.judge import GeminiJudge


def get_generator_metrics(
    judge: Optional[GeminiJudge] = None,
    threshold: float = 0.7,
    include_reason: bool = True,
    include_hallucination: bool = True,
) -> list:
    """
    Returns configured DeepEval generator metrics powered by the Gemini judge.

    Args:
        judge: GeminiJudge instance (creates one if not provided).
        threshold: Minimum score threshold (0.0 to 1.0) to pass the test.
        include_reason: Whether the LLM judge should provide an explanation.
        include_hallucination: Whether to include the HallucinationMetric.

    Returns:
        list of configured DeepEval metrics.
    """
    eval_model = judge or GeminiJudge()

    faithfulness_metric = FaithfulnessMetric(
        threshold=threshold,
        model=eval_model,
        include_reason=include_reason,
    )

    relevancy_metric = AnswerRelevancyMetric(
        threshold=threshold,
        model=eval_model,
        include_reason=include_reason,
    )

    metrics = [faithfulness_metric, relevancy_metric]

    if include_hallucination:
        # Hallucination threshold: in DeepEval, lower is better (0.0 = no hallucination)
        # Passing threshold is <= threshold (e.g. 0.3 or 0.5)
        hallucination_metric = HallucinationMetric(
            threshold=1.0 - threshold,
            model=eval_model,
            include_reason=include_reason,
        )
        metrics.append(hallucination_metric)

    return metrics
