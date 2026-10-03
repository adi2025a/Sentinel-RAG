"""
eval/generator package
======================
DeepEval-based generator evaluation modules for SentinelRAG.
"""

from eval.generator.metrics import get_generator_metrics
from eval.generator.run_generator_eval import run_generator_evaluation

__all__ = ["get_generator_metrics", "run_generator_evaluation"]
