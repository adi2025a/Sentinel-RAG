"""
eval/generator/run_generator_eval.py
===================================
Generator (LLM) Evaluation Runner using DeepEval and Google Gemini.
Evaluates Faithfulness (Hallucination detection) and Answer Relevancy
of answers produced by SentinelRAG's generation layer.
"""

from __future__ import annotations
import json
import time
from pathlib import Path
from typing import Any, Optional

from deepeval.test_case import LLMTestCase

from app.rag import search_query, answer_query_with_context
from app.config import settings
from eval.judge import GeminiJudge
from eval.generator.metrics import get_generator_metrics


def load_dataset(dataset_path: Path) -> list[dict[str, Any]]:
    """Loads JSONL generator evaluation samples."""
    records = []
    with open(dataset_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def run_generator_evaluation(
    dataset_path: Optional[Path | str] = None,
    top_k: int = 4,
    threshold: float = 0.7,
    judge_model: Optional[str] = None,
    include_hallucination: bool = True,
    save_report: bool = True,
    output_dir: Optional[Path | str] = None,
) -> list[dict[str, Any]]:
    """
    Runs DeepEval generator evaluation on benchmark test cases.
    """
    default_dataset = settings.ROOT_DIR / "eval" / "datasets" / "generator_dataset.jsonl"
    data_file = Path(dataset_path) if dataset_path else default_dataset

    if not data_file.exists():
        # Fallback to retriever_dataset.jsonl if generator_dataset.jsonl doesn't exist
        fallback_file = settings.ROOT_DIR / "eval" / "datasets" / "retriever_dataset.jsonl"
        if fallback_file.exists():
            data_file = fallback_file
        else:
            raise FileNotFoundError(f"Generator dataset not found at: {data_file}")

    samples = load_dataset(data_file)
    print(f"\n🧠 Initializing DeepEval Generator Evaluation on {len(samples)} samples...")
    print(f"   Dataset: {data_file.name}")
    print(f"   Retrieval top_k: {top_k}")
    print(f"   Metric passing threshold: {threshold}")

    # Initialize Gemini Judge
    judge = GeminiJudge(model_name=judge_model)
    print(f"   Judge Model: {judge.get_model_name()}\n")

    metrics = get_generator_metrics(
        judge=judge,
        threshold=threshold,
        include_hallucination=include_hallucination,
    )
    faithfulness_metric = metrics[0]
    relevancy_metric = metrics[1]
    hallucination_metric = metrics[2] if len(metrics) > 2 else None

    results_summary = []
    t0 = time.perf_counter()

    for idx, sample in enumerate(samples, start=1):
        query = sample["input"]
        expected_output = sample.get("expected_output", "")

        print(f"[{idx}/{len(samples)}] Query: {query!r}")

        # 1. Retrieve chunks from vector store
        docs = search_query(query, k=top_k)
        retrieval_context = [doc.page_content for doc in docs]

        # 2. Call SentinelRAG Generator
        print("    Generating answer via Gemini...")
        actual_output = answer_query_with_context(retrieval_context, query)
        print(f"    Answer: {actual_output[:100]}...")

        # 3. Build DeepEval LLMTestCase
        test_case = LLMTestCase(
            input=query,
            actual_output=actual_output,
            expected_output=expected_output,
            context=retrieval_context,
            retrieval_context=retrieval_context,
        )

        # 4. Score with metrics
        print("    Evaluating Faithfulness (Groundedness / Hallucinations)...")
        faithfulness_metric.measure(test_case)

        print("    Evaluating Answer Relevancy...")
        relevancy_metric.measure(test_case)

        hal_score, hal_passed, hal_reason = None, None, None
        if hallucination_metric:
            print("    Evaluating Hallucination Metric...")
            hallucination_metric.measure(test_case)
            hal_score = round(hallucination_metric.score, 3) if hallucination_metric.score is not None else 0.0
            hal_passed = hallucination_metric.is_successful()
            hal_reason = hallucination_metric.reason

        res_entry = {
            "id": sample.get("id", f"case_{idx}"),
            "query": query,
            "actual_output": actual_output,
            "expected_output": expected_output,
            "retrieved_chunks_count": len(retrieval_context),
            "faithfulness": {
                "score": round(faithfulness_metric.score, 3) if faithfulness_metric.score is not None else 0.0,
                "passed": faithfulness_metric.is_successful(),
                "reason": faithfulness_metric.reason,
            },
            "answer_relevancy": {
                "score": round(relevancy_metric.score, 3) if relevancy_metric.score is not None else 0.0,
                "passed": relevancy_metric.is_successful(),
                "reason": relevancy_metric.reason,
            },
        }

        if hallucination_metric:
            res_entry["hallucination"] = {
                "score": hal_score,
                "passed": hal_passed,
                "reason": hal_reason,
            }

        results_summary.append(res_entry)

    total_time_ms = (time.perf_counter() - t0) * 1000

    # Print Summary Table
    _print_summary(results_summary, total_time_ms, threshold, include_hallucination)

    if save_report:
        rep_dir = Path(output_dir) if output_dir else (settings.ROOT_DIR / "eval" / "reports")
        rep_dir.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")

        json_path = rep_dir / f"generator_eval_{timestamp}.json"
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


def _print_summary(
    results: list[dict[str, Any]],
    elapsed_ms: float,
    threshold: float,
    include_hallucination: bool,
):
    """Prints a formatted evaluation table."""
    print("\n" + "=" * 95)
    print("                    ✨ DEEPEVAL GENERATOR BENCHMARK RESULTS")
    print("=" * 95)
    print(f"Total Test Cases: {len(results)} | Passing Threshold: {threshold} | Elapsed: {elapsed_ms / 1000:.1f}s")
    print("-" * 95)

    if include_hallucination:
        print(f"{'ID':<10} | {'Faithfulness':<14} | {'Relevancy':<12} | {'Hallucination':<14} | Query")
    else:
        print(f"{'ID':<10} | {'Faithfulness':<14} | {'Relevancy':<12} | Query")
    print("-" * 95)

    avg_faith, avg_rel, avg_hal = 0.0, 0.0, 0.0
    for r in results:
        faith = r["faithfulness"]["score"]
        rel = r["answer_relevancy"]["score"]
        avg_faith += faith
        avg_rel += rel

        faith_icon = "✅" if r["faithfulness"]["passed"] else "❌"
        rel_icon = "✅" if r["answer_relevancy"]["passed"] else "❌"

        short_q = (r['query'][:30] + "...") if len(r['query']) > 30 else r['query']

        if include_hallucination and "hallucination" in r:
            hal = r["hallucination"]["score"]
            avg_hal += hal
            hal_icon = "✅" if r["hallucination"]["passed"] else "❌"
            print(
                f"{r['id']:<10} | {faith_icon} {faith:<11.2f} | {rel_icon} {rel:<9.2f} | {hal_icon} {hal:<11.2f} | {short_q}"
            )
        else:
            print(
                f"{r['id']:<10} | {faith_icon} {faith:<11.2f} | {rel_icon} {rel:<9.2f} | {short_q}"
            )

    n = max(len(results), 1)
    avg_faith /= n
    avg_rel /= n
    avg_hal /= n
    print("-" * 95)
    if include_hallucination:
        print(f"{'AVERAGE':<10} |   {avg_faith:<12.2f} |   {avg_rel:<10.2f} |   {avg_hal:<12.2f} |")
    else:
        print(f"{'AVERAGE':<10} |   {avg_faith:<12.2f} |   {avg_rel:<10.2f} |")
    print("=" * 95 + "\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="DeepEval Generator Evaluation")
    parser.add_argument("--dataset", type=str, default=None, help="Path to JSONL dataset")
    parser.add_argument("--top-k", type=int, default=4, help="Number of chunks to retrieve per query")
    parser.add_argument("--threshold", type=float, default=0.7, help="Passing score threshold")
    parser.add_argument("--model", type=str, default=None, help="Gemini judge model name")
    parser.add_argument("--no-hallucination", action="store_true", help="Skip hallucination metric")
    parser.add_argument("--no-save", action="store_true", help="Do not save JSON report")

    args = parser.parse_args()

    run_generator_evaluation(
        dataset_path=args.dataset,
        top_k=args.top_k,
        threshold=args.threshold,
        judge_model=args.model,
        include_hallucination=not args.no_hallucination,
        save_report=not args.no_save,
    )
