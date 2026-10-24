from unittest.mock import patch, MagicMock
from src.graph import build_graph


@patch("src.generate.get_gemini_client")
def test_company_policy_question_routes_to_rag(mock_client_factory):
    """A company policy question should trigger the RAG path and return sources."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "At Aurelia Tech, employees receive 20 days of annual leave as outlined in hr_policies.md."
    mock_client.models.generate_content.return_value = mock_response
    mock_client_factory.return_value = mock_client

    graph = build_graph()
    result = graph.invoke({
        "question": "How many days of annual leave do I get at Aurelia?",
        "route": None,
        "answer": None,
        "sources": None,
        "source_details": None,
        "history": [],
        "is_grounded": None,
    })

    assert result["route"] == "rag"
    assert len(result["sources"]) > 0
    assert any("hr_policies" in s for s in result["sources"])


@patch("src.graph.call_gemini_with_retry")
def test_casual_greeting_routes_direct(mock_gemini):
    """A casual greeting should route directly without document retrieval."""
    mock_gemini.return_value = "Hello! I am your Aurelia Knowledge Assistant."
    graph = build_graph()
    result = graph.invoke({
        "question": "Hello! How are you doing today?",
        "route": None,
        "answer": None,
        "sources": None,
        "source_details": None,
        "history": [],
        "is_grounded": None,
    })

    assert result["route"] == "direct"
    assert result["sources"] == []


def test_math_question_routes_to_calculator():
    """A calculation question should route to calculator and evaluate."""
    graph = build_graph()
    result = graph.invoke({
        "question": "If I have 20 annual leave days and take 7, how many are left?",
        "route": None,
        "answer": None,
        "sources": None,
        "source_details": None,
        "history": [],
        "is_grounded": None,
    })

    assert result["route"] == "tool_calculator"
    assert "13" in result["answer"]
