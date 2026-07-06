import time
import json
import os

from src.retrieve import retrieve_relevant_chunks
from src.generate import generate_answer
from eval.test_questions import TEST_CASES
from eval.metrics import compute_precision, compute_recall, compute_faithfulness

RESULTS_FILE = "eval/results_checkpoint.json"


def load_checkpoint():
    """Load previously completed results, if any exist."""
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "r") as f:
            return json.load(f)
    return []


def save_checkpoint(results):
    """Save results so far to disk, so progress isn't lost on failure."""
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)


def evaluate_single_case(case):
    question = case["question"]
    expected_sources = case["expected_sources"]

    start_time = time.time()
    retrieved_chunks = retrieve_relevant_chunks(question, k=3)
    result = generate_answer(question, k=3)
    elapsed_seconds = time.time() - start_time

    precision = compute_precision(retrieved_chunks, expected_sources)
    recall = compute_recall(retrieved_chunks, expected_sources)

    if expected_sources:
        faithfulness_score, faithfulness_reason = compute_faithfulness(
            result["answer"], retrieved_chunks
        )
    else:
        faithfulness_score, faithfulness_reason = None, "N/A (out-of-scope question)"

    return {
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

def print_report(results):
    print("\n" + "=" * 70)
    print("RAG EVALUATION REPORT")
    print("=" * 70)

    for i, r in enumerate(results, 1):
        print(f"\n[{i}] {r['question']}")
        print(f"    Expected sources:  {r['expected_sources'] or 'none (out-of-scope)'}")
        print(f"    Retrieved sources: {r['retrieved_sources']}")
        print(f"    Precision: {r['precision']}  |  Recall: {r['recall']}")
        print(f"    Faithfulness: {r['faithfulness_score']} — {r['faithfulness_reason']}")
        print(f"    Latency: {r['latency_seconds']}s")

    precisions = [r["precision"] for r in results if r["precision"] is not None]
    recalls = [r["recall"] for r in results if r["recall"] is not None]
    faithfulness_scores = [r["faithfulness_score"] for r in results if r["faithfulness_score"] is not None]
    latencies = [r["latency_seconds"] for r in results]

    print("\n" + "-" * 70)
    print("AGGREGATE METRICS")
    print("-" * 70)
    print(f"Avg Precision:    {sum(precisions) / len(precisions):.2f}")
    print(f"Avg Recall:       {sum(recalls) / len(recalls):.2f}")
    print(f"Avg Faithfulness: {sum(faithfulness_scores) / len(faithfulness_scores):.2f}")
    print(f"Avg Latency:      {sum(latencies) / len(latencies):.2f}s")
    print("=" * 70)


if __name__ == "__main__":
    results = load_checkpoint()
    completed_questions = {r["question"] for r in results}
    remaining_cases = [c for c in TEST_CASES if c["question"] not in completed_questions]

    print(f"{len(results)} already completed, {len(remaining_cases)} remaining.\n")

    for i, case in enumerate(remaining_cases):
        print(f"Evaluating: {case['question'][:60]}...")
        try:
            result = evaluate_single_case(case)
            results.append(result)
            save_checkpoint(results)
        except Exception as e:
            print(f"\nStopped due to error: {e}")
            print(f"Progress saved — {len(results)}/{len(TEST_CASES)} completed.")
            print("Re-run this script later to continue from where it left off.")
            break

        if i < len(remaining_cases) - 1:
            time.sleep(15)

    if len(results) == len(TEST_CASES):
        print_report(results)
    else:
        print(f"\nIncomplete: {len(results)}/{len(TEST_CASES)} questions evaluated so far.")