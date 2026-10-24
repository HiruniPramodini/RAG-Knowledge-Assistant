"""Unit tests for evaluation metrics and checkpoint recovery."""

import tempfile
import os
from langchain_core.documents import Document

from eval.metrics import compute_precision, compute_recall
from eval.run_evaluation import save_checkpoint, load_checkpoint, RESULTS_FILE


def test_compute_precision_and_recall():
    """Verifies precision and recall calculations against expected sources."""
    chunks = [
        Document(page_content="Text 1", metadata={"source": "hr_policies.md"}),
        Document(page_content="Text 2", metadata={"source": "hr_policies.md"}),
        Document(page_content="Text 3", metadata={"source": "unrelated.md"}),
    ]

    expected = ["hr_policies.md"]

    precision = compute_precision(chunks, expected)
    recall = compute_recall(chunks, expected)

    assert precision == 0.667  # 2 out of 3 chunks are from hr_policies.md
    assert recall == 1.0       # 1 out of 1 expected source was captured


def test_precision_recall_out_of_scope():
    """Out-of-scope questions with empty expected sources should return None."""
    chunks = [Document(page_content="Text", metadata={"source": "hr_policies.md"})]
    assert compute_precision(chunks, []) is None
    assert compute_recall(chunks, []) is None


def test_checkpoint_save_and_load(monkeypatch):
    """Verifies atomic saving and loading of evaluation checkpoints."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_checkpoint_path = os.path.join(tmpdir, "checkpoint.json")
        monkeypatch.setattr("eval.run_evaluation.RESULTS_FILE", test_checkpoint_path)

        sample_results = [
            {"question": "Q1", "precision": 1.0, "recall": 1.0},
            {"question": "Q2", "precision": 0.8, "recall": 1.0},
        ]

        save_checkpoint(sample_results)
        loaded = load_checkpoint()

        assert len(loaded) == 2
        assert loaded[0]["question"] == "Q1"
        assert loaded[1]["precision"] == 0.8
