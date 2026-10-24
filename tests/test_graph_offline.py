"""Unit tests for LangGraph routing logic and state transitions (offline / mocked)."""

from unittest.mock import patch
from src.graph import router_node, build_graph, calculator_node, direct_answer_node, GraphState


def test_router_deterministic_forced_rag_after_clarify():
    """If the prior turn was a clarification, the router MUST deterministically route to RAG."""
    state: GraphState = {
        "question": "Engineering team",
        "route": None,
        "answer": None,
        "sources": None,
        "source_details": None,
        "history": [
            {"question": "How do I request software?", "answer": "Which team are you on?", "route": "clarify"}
        ],
        "is_grounded": None,
    }

    result = router_node(state)
    assert result["route"] == "rag"


def test_router_deterministic_greeting_routes_direct():
    """Simple greetings should route directly without requiring LLM calls."""
    state: GraphState = {
        "question": "Hello!",
        "route": None,
        "answer": None,
        "sources": None,
        "source_details": None,
        "history": [],
        "is_grounded": None,
    }

    result = router_node(state)
    assert result["route"] == "direct"


@patch("src.graph.call_gemini_with_retry")
def test_calculator_node_executes_expression(mock_llm):
    """Calculator node should extract expression and evaluate accurately."""
    mock_llm.return_value = "20 - 12"

    state: GraphState = {
        "question": "If I have 20 days and take 12, how many are left?",
        "route": "tool_calculator",
        "answer": None,
        "sources": None,
        "source_details": None,
        "history": [],
        "is_grounded": None,
    }

    result = calculator_node(state)
    assert "8" in result["answer"]
    assert result["sources"] == []


@patch("src.graph.call_gemini_with_retry")
def test_direct_answer_node_provides_friendly_greeting(mock_llm):
    """Direct node should return a polite response with empty sources."""
    mock_llm.return_value = "Hello! I am your Aurelia Knowledge Assistant."

    state: GraphState = {
        "question": "Good morning!",
        "route": "direct",
        "answer": None,
        "sources": None,
        "source_details": None,
        "history": [],
        "is_grounded": None,
    }

    result = direct_answer_node(state)
    assert "Aurelia" in result["answer"]
    assert result["sources"] == []
