"""
eval/run_eval.py
================
Main CLI runner for SentinelRAG evaluations using DeepEval.

Usage:
    python -m eval.run_eval --type retriever
    python -m eval.run_eval --type retriever --top-k 5 --threshold 0.75
"""

import argparse
from eval.retriever.run_retriever_eval import run_retriever_evaluation


def main():
    parser = argparse.ArgumentParser(
        description="🎯 SentinelRAG DeepEval Evaluation Suite",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--type",
        choices=["retriever", "generator", "all"],
        default="retriever",
        help="Evaluation target",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=None,
        help="Custom dataset path (defaults to built-in datasets in eval/datasets/)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=4,
        help="Number of chunks retrieved per query",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.7,
        help="Minimum metric passing threshold",
    )
    parser.add_argument(
        "--judge-model",
        type=str,
        default=None,
        help="Gemini judge model name (defaults to GEMINI_CHAT_MODEL in .env)",
    )

    args = parser.parse_args()

    if args.type == "retriever":
        run_retriever_evaluation(
            dataset_path=args.dataset,
            top_k=args.top_k,
            threshold=args.threshold,
            judge_model=args.judge_model,
        )
    else:
        print(f"Evaluation type '{args.type}' is coming up next!")


if __name__ == "__main__":
    main()
