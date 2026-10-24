"""Unit tests for citation validation, abstention handling, and prompt generation."""

from src.generate import (
    format_history,
    build_prompt,
    validate_citations,
    generate_answer,
)
from langchain_core.documents import Document


def test_format_history_sliding_window():
    """History formatter should honor the sliding window limit."""
    history = [
        {"question": "Q1", "answer": "A1"},
        {"question": "Q2", "answer": "A2"},
        {"question": "Q3", "answer": "A3"},
        {"question": "Q4", "answer": "A4"},
    ]

    formatted = format_history(history, limit=2)
    assert "Q3" in formatted
    assert "Q4" in formatted
    assert "Q1" not in formatted
    assert "Q2" not in formatted


def test_validate_citations_with_valid_sources():
    """Retrieved sources should be validated and deduplicated when answer is grounded."""
    answer = "Employees accrue 20 days of annual leave according to company policy."
    sources = ["hr_policies.md", "hr_policies.md", "company_overview.md"]

    validated = validate_citations(answer, sources)
    assert validated == ["company_overview.md", "hr_policies.md"]


def test_validate_citations_with_abstention():
    """If the answer states information is not available, sources should be cleared."""
    answer = "The requested information is not available in the internal knowledge base."
    sources = ["it_onboarding.md"]

    validated = validate_citations(answer, sources)
    assert validated == []


def test_generate_answer_empty_chunks_returns_abstention():
    """When no chunks are provided, generate_answer returns an honest abstention without calling LLM."""
    res = generate_answer("What is the policy for space travel?", chunks=[])

    assert res["is_grounded"] is False
    assert res["sources"] == []
    assert "couldn't find enough information" in res["answer"].lower() or "not available" in res["answer"].lower()
