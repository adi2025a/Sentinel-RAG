"""
eval/retriever package
======================
DeepEval-based retriever evaluation modules for SentinelRAG.
"""

from eval.retriever.metrics import get_retriever_metrics
from eval.retriever.run_retriever_eval import run_retriever_evaluation

__all__ = ["get_retriever_metrics", "run_retriever_evaluation"]
