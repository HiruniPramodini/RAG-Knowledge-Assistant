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

