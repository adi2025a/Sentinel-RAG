"""
eval/retriever/run_retriever_eval.py
===================================
Retriever Evaluation Runner using DeepEval and Google Gemini.
Evaluates Contextual Relevancy, Contextual Recall, and Contextual Precision
over chunks retrieved from SentinelRAG's FAISS vector store.
"""

from __future__ import annotations
import json
import time
from pathlib import Path
from typing import Any, Optional

from deepeval.test_case import LLMTestCase
from deepeval import evaluate

from app.rag import search_query
from app.config import settings
from eval.judge import GeminiJudge
from eval.retriever.metrics import get_retriever_metrics


def load_dataset(dataset_path: Path) -> list[dict[str, Any]]:
    """Loads JSONL retrieval evaluation samples."""
    records = []
    with open(dataset_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def run_retriever_evaluation(
    dataset_path: Optional[Path | str] = None,
    top_k: int = 4,
    threshold: float = 0.7,
    judge_model: Optional[str] = None,
    save_report: bool = True,
    output_dir: Optional[Path | str] = None,
) -> list[dict[str, Any]]:
    """
    Runs DeepEval retriever evaluation on benchmark test cases.
    """
    default_dataset = settings.ROOT_DIR / "eval" / "datasets" / "retriever_dataset.jsonl"
    data_file = Path(dataset_path) if dataset_path else default_dataset

    if not data_file.exists():
        raise FileNotFoundError(f"Retriever dataset not found at: {data_file}")

    samples = load_dataset(data_file)
    print(f"\n🔍 Initializing DeepEval Retriever Evaluation on {len(samples)} samples...")
    print(f"   Dataset: {data_file.name}")
    print(f"   Retrieval top_k: {top_k}")
    print(f"   Metric passing threshold: {threshold}\n")

    # Initialize Gemini Judge
    judge = GeminiJudge(model_name=judge_model)
    print(f"   Judge Model: {judge.get_model_name()}\n")

    metrics = get_retriever_metrics(judge=judge, threshold=threshold)
    relevancy_metric, recall_metric, precision_metric = metrics

    results_summary = []
    t0 = time.perf_counter()

    for idx, sample in enumerate(samples, start=1):
        query = sample["input"]
        expected_output = sample.get("expected_output", "")

        print(f"[{idx}/{len(samples)}] Query: {query!r}")

        # 1. Retrieve chunks from SentinelRAG's FAISS vector store
        docs = search_query(query, k=top_k)
        retrieval_context = [doc.page_content for doc in docs]
        print(f"    Retrieved {len(retrieval_context)} context chunks.")

        # 2. Build DeepEval LLMTestCase
        test_case = LLMTestCase(
            input=query,
            expected_output=expected_output,
            retrieval_context=retrieval_context,
        )

        # 3. Score with each metric
        print("    Evaluating Contextual Relevancy...")
        relevancy_metric.measure(test_case)

        print("    Evaluating Contextual Recall...")
        recall_metric.measure(test_case)

        print("    Evaluating Contextual Precision...")
        precision_metric.measure(test_case)

        res_entry = {
            "id": sample.get("id", f"case_{idx}"),
            "query": query,
            "expected_output": expected_output,
            "retrieved_chunks_count": len(retrieval_context),
            "relevancy": {
                "score": round(relevancy_metric.score, 3) if relevancy_metric.score is not None else 0.0,
                "passed": relevancy_metric.is_successful(),
                "reason": relevancy_metric.reason,
            },
            "recall": {
                "score": round(recall_metric.score, 3) if recall_metric.score is not None else 0.0,
                "passed": recall_metric.is_successful(),
                "reason": recall_metric.reason,
            },
            "precision": {
                "score": round(precision_metric.score, 3) if precision_metric.score is not None else 0.0,
                "passed": precision_metric.is_successful(),
                "reason": precision_metric.reason,
            },
        }
        results_summary.append(res_entry)

    total_time_ms = (time.perf_counter() - t0) * 1000

    # Format Summary Table
    _print_summary(results_summary, total_time_ms, threshold)

    if save_report:
        rep_dir = Path(output_dir) if output_dir else (settings.ROOT_DIR / "eval" / "reports")
        rep_dir.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")

        json_path = rep_dir / f"retriever_eval_{timestamp}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "judge_model": judge.get_model_name(),
                    "threshold": threshold,
                    "top_k": top_k,
                    "elapsed_ms": round(total_time_ms, 2),
                    "results": results_summary,
                },
                f,
                indent=2,
            )
        print(f"\n💾 Saved detailed report to: {json_path}")

    return results_summary


def _print_summary(results: list[dict[str, Any]], elapsed_ms: float, threshold: float):
    """Prints a formatted evaluation table."""
    print("\n" + "=" * 90)
    print("                    🎯 DEEPEVAL RETRIEVER BENCHMARK RESULTS")
    print("=" * 90)
    print(f"Total Test Cases: {len(results)} | Passing Threshold: {threshold} | Elapsed: {elapsed_ms / 1000:.1f}s")
    print("-" * 90)
    print(f"{'ID':<10} | {'Relevancy':<12} | {'Recall':<12} | {'Precision':<12} | Query")
    print("-" * 90)

    avg_rel, avg_rec, avg_prec = 0.0, 0.0, 0.0
    for r in results:
        rel = r["relevancy"]["score"]
        rec = r["recall"]["score"]
        prec = r["precision"]["score"]
        avg_rel += rel
        avg_rec += rec
        avg_prec += prec

        rel_icon = "✅" if r["relevancy"]["passed"] else "❌"
        rec_icon = "✅" if r["recall"]["passed"] else "❌"
        prec_icon = "✅" if r["precision"]["passed"] else "❌"

        short_q = (r['query'][:38] + "...") if len(r['query']) > 38 else r['query']
        print(
            f"{r['id']:<10} | {rel_icon} {rel:<9.2f} | {rec_icon} {rec:<9.2f} | {prec_icon} {prec:<9.2f} | {short_q}"
        )

    n = max(len(results), 1)
    avg_rel /= n
    avg_rec /= n
    avg_prec /= n
    print("-" * 90)
    print(f"{'AVERAGE':<10} |   {avg_rel:<10.2f} |   {avg_rec:<10.2f} |   {avg_prec:<10.2f} |")
    print("=" * 90 + "\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="DeepEval Retriever Evaluation")
    parser.add_argument("--dataset", type=str, default=None, help="Path to JSONL dataset")
    parser.add_argument("--top-k", type=int, default=4, help="Number of chunks to retrieve per query")
    parser.add_argument("--threshold", type=float, default=0.7, help="Passing score threshold")
    parser.add_argument("--model", type=str, default=None, help="Gemini judge model name")
    parser.add_argument("--no-save", action="store_true", help="Do not save JSON report")

    args = parser.parse_args()

    run_retriever_evaluation(
        dataset_path=args.dataset,
        top_k=args.top_k,
        threshold=args.threshold,
        judge_model=args.model,
        save_report=not args.no_save,
    )
