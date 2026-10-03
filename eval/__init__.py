"""
eval package
============
SentinelRAG evaluation suite powered by DeepEval and custom benchmarks.
"""

from eval.judge import GeminiJudge
from eval.retriever.run_retriever_eval import run_retriever_evaluation
from eval.generator.run_generator_eval import run_generator_evaluation

__all__ = [
    "GeminiJudge",
    "run_retriever_evaluation",
    "run_generator_evaluation",
]
