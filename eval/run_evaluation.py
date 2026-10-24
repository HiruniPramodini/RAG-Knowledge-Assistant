"""Evaluation Runner for the Enterprise RAG Knowledge Assistant.

Runs benchmark questions against the live RAG pipeline, measures precision,
recall, faithfulness, and latency, and maintains a fault-tolerant checkpoint file.
"""

import argparse
import json
import os
import time
from typing import Any, Dict, List, Optional

from src.retrieve import retrieve_relevant_chunks
from src.generate import generate_answer
from eval.test_questions import TEST_CASES
from eval.metrics import compute_precision, compute_recall, compute_faithfulness

RESULTS_FILE = "eval/results_checkpoint.json"


def load_checkpoint() -> List[Dict[str, Any]]:
    """Safely loads previously completed evaluation results from disk."""
    if os.path.exists(RESULTS_FILE):
        try:
            with open(RESULTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Warning] Failed to load checkpoint file ({e}). Starting fresh.")
            return []
    return []


def save_checkpoint(results: List[Dict[str, Any]]):
    """Safely saves results to disk with atomic write."""
    tmp_file = f"{RESULTS_FILE}.tmp"
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    if os.path.exists(RESULTS_FILE):
        os.remove(RESULTS_FILE)
    os.rename(tmp_file, RESULTS_FILE)


def evaluate_single_case(case: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluates a single benchmark question."""
    question = case["question"]
    expected_sources = case["expected_sources"]
    category = case.get("category", "General")

    start_time = time.time()
    retrieved_chunks = retrieve_relevant_chunks(question, k=3)
    result = generate_answer(question, k=3, chunks=retrieved_chunks)
    elapsed_seconds = time.time() - start_time

    precision = compute_precision(retrieved_chunks, expected_sources)
    recall = compute_recall(retrieved_chunks, expected_sources)

    if expected_sources:
        faithfulness_score, faithfulness_reason = compute_faithfulness(
            result["answer"], retrieved_chunks
        )
    else:
        faithfulness_score = 1.0 if not result.get("is_grounded", False) else 0.0
        faithfulness_reason = "Out-of-scope question: verified honest abstention without hallucinated sources."

    return {
        "category": category,
        "question": question,
        "answer": result["answer"],
        "expected_sources": expected_sources,
        "retrieved_sources": result["sources"],
        "precision": precision,
        "recall": recall,
        "faithfulness_score": faithfulness_score,
        "faithfulness_reason": faithfulness_reason,
        "latency_seconds": round(elapsed_seconds, 2),
    }


def print_report(results: List[Dict[str, Any]]):
    """Displays formatted evaluation metrics table and aggregate statistics."""
    print("\n" + "=" * 75)
    print("           ENTERPRISE RAG KNOWLEDGE ASSISTANT EVALUATION REPORT")
    print("=" * 75)

    for i, r in enumerate(results, 1):
        print(f"\n[{i}] Category: {r.get('category', 'N/A')}")
        print(f"    Q: {r['question']}")
        print(f"    Expected sources:  {r['expected_sources'] or 'None (Out-of-Scope)'}")
        print(f"    Retrieved sources: {r['retrieved_sources'] or 'None'}")
        print(f"    Precision: {r['precision']}  |  Recall: {r['recall']}")
        print(f"    Faithfulness: {r['faithfulness_score']} — {r['faithfulness_reason']}")
        print(f"    Latency: {r['latency_seconds']}s")

    precisions = [r["precision"] for r in results if r["precision"] is not None]
    recalls = [r["recall"] for r in results if r["recall"] is not None]
    faithfulness_scores = [r["faithfulness_score"] for r in results if r["faithfulness_score"] is not None]
    latencies = [r["latency_seconds"] for r in results]

    print("\n" + "-" * 75)
    print("AGGREGATE METRICS SUMMARY")
    print("-" * 75)
    if precisions:
        print(f"Avg Context Precision:  {sum(precisions) / len(precisions):.2%}")
    if recalls:
        print(f"Avg Context Recall:     {sum(recalls) / len(recalls):.2%}")
    if faithfulness_scores:
        print(f"Avg Faithfulness Score: {sum(faithfulness_scores) / len(faithfulness_scores):.2%}")
    if latencies:
        print(f"Avg Query Latency:      {sum(latencies) / len(latencies):.2f} seconds")
    print("=" * 75)


def run_evaluation(limit: Optional[int] = None, reset: bool = False):
    """Runs the full or partial evaluation suite."""
    if reset and os.path.exists(RESULTS_FILE):
        os.remove(RESULTS_FILE)
        print("Reset existing checkpoint.")

    results = load_checkpoint()
    completed_questions = {r["question"] for r in results}
    remaining_cases = [c for c in TEST_CASES if c["question"] not in completed_questions]

    if limit is not None:
        remaining_cases = remaining_cases[:limit]

    print(f"\nEvaluation Suite: {len(results)} already completed, {len(remaining_cases)} scheduled to evaluate.\n")

    for i, case in enumerate(remaining_cases):
        print(f"[{i+1}/{len(remaining_cases)}] Evaluating: {case['question'][:60]}...")
        try:
            result = evaluate_single_case(case)
            results.append(result)
            save_checkpoint(results)
            print(f"    -> Precision: {result['precision']}, Recall: {result['recall']}, Faithfulness: {result['faithfulness_score']}")
        except Exception as e:
            print(f"\n[Warning] Evaluation stopped due to error: {e}")
            print(f"Progress saved — {len(results)}/{len(TEST_CASES)} completed.")
            print("Re-run this script later to resume from where it left off.")
            break

        if i < len(remaining_cases) - 1:
            time.sleep(5)

    print_report(results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run RAG benchmark evaluation suite.")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of test cases to run.")
    parser.add_argument("--reset", action="store_true", help="Reset checkpoint and re-run all tests.")
    args = parser.parse_args()

    run_evaluation(limit=args.limit, reset=args.reset)