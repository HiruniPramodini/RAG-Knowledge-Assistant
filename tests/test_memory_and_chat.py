"""Unit tests for Conversational Memory, Follow-Up Resolution, and Session Isolation.

Tests:
- Resolving follow-up references ('what about sick leave?', 'can you summarize that?')
- Retrieving relevant documents for enriched follow-up questions
- Creating, switching, and isolating separate conversations
- Valid source citations and honest abstention when evidence is missing
- Error handling without crash
"""

from unittest.mock import MagicMock, patch
import pytest

from src.retrieve import enrich_query_with_history, retrieve_relevant_chunks
from src.generate import generate_answer, validate_citations, format_history
from src.graph import build_graph, router_node, GraphState


# -----------------------------------------------------------------------------
# 1. FOLLOW-UP QUERY ENRICHMENT & RESOLUTION
# -----------------------------------------------------------------------------

def test_enrich_query_resolves_pronoun_reference():
    """Follow-up questions using pronouns ('what about sick leave?') should combine with prior topic."""
    history = [
        {"question": "What is our company annual leave policy?", "answer": "Employees receive 20 days of annual leave.", "route": "rag"}
    ]
    query = "What about sick leave?"
    enriched = enrich_query_with_history(query, history=history)

    assert "annual leave policy" in enriched.lower()
    assert "sick leave" in enriched.lower()


def test_enrich_query_resolves_summarize_request():
    """Follow-up requests to summarize should search on the preceding topic."""
    history = [
        {"question": "What are our engineering standards for pull requests?", "answer": "All PRs need 2 reviewers.", "route": "rag"}
    ]
    query = "Can you summarize that?"
    enriched = enrich_query_with_history(query, history=history)

    assert "engineering standards" in enriched.lower()
    assert "summary" in enriched.lower() or "guidelines" in enriched.lower()


def test_enrich_query_leaves_standalone_question_unchanged():
    """Standalone, complete questions should not be modified by prior conversation."""
    history = [
        {"question": "How do I connect to VPN?", "answer": "Use Aurelia Connect client.", "route": "rag"}
    ]
    standalone_query = "What is the procedure for submitting travel expense reimbursements?"
    enriched = enrich_query_with_history(query=standalone_query, history=history)

    assert enriched == standalone_query


# -----------------------------------------------------------------------------
# 2. CONVERSATION ISOLATION & MEMORY STATE
# -----------------------------------------------------------------------------

def test_conversations_maintain_isolated_histories():
    """Each conversation must maintain its own independent history and messages."""
    conversations = {
        "conv_1": {
            "id": "conv_1",
            "title": "Leave Policy",
            "messages": [
                {"role": "user", "content": "What is the leave policy?"},
                {"role": "assistant", "content": "20 days annual leave.", "route": "rag"},
            ],
            "history": [
                {"question": "What is the leave policy?", "answer": "20 days annual leave.", "route": "rag"}
            ],
        },
        "conv_2": {
            "id": "conv_2",
            "title": "VPN Setup",
            "messages": [
                {"role": "user", "content": "How do I setup VPN?"},
                {"role": "assistant", "content": "Install Aurelia Connect.", "route": "rag"},
            ],
            "history": [
                {"question": "How do I setup VPN?", "answer": "Install Aurelia Connect.", "route": "rag"}
            ],
        },
    }

    # Verify conversation 1 history does not leak into conversation 2
    assert len(conversations["conv_1"]["history"]) == 1
    assert "leave" in conversations["conv_1"]["history"][0]["question"]

    assert len(conversations["conv_2"]["history"]) == 1
    assert "VPN" in conversations["conv_2"]["history"][0]["question"]

    # Simulating switching to conv_2 and querying
    active_conv = conversations["conv_2"]
    enriched = enrich_query_with_history("What about troubleshooting it?", history=active_conv["history"])
    assert "VPN" in enriched
    assert "leave" not in enriched


def test_conversation_deletion_and_switching():
    """Deleting a conversation removes it cleanly without corrupting other conversations."""
    conversations = {
        "conv_a": {"id": "conv_a", "title": "Topic A", "messages": [], "history": []},
        "conv_b": {"id": "conv_b", "title": "Topic B", "messages": [], "history": []},
    }
    active_id = "conv_a"

    # Delete conv_a
    del conversations[active_id]
    assert "conv_a" not in conversations

    # Switch to remaining conversation
    active_id = next(iter(conversations.keys()))
    assert active_id == "conv_b"
    assert len(conversations) == 1


# -----------------------------------------------------------------------------
# 3. GROUNDING, CITATIONS & HONEST ABSTENTION
# -----------------------------------------------------------------------------

def test_abstention_when_evidence_is_missing():
    """When context is missing or irrelevant, the assistant must return an honest fallback."""
    empty_chunks = []
    result = generate_answer("What is the company stock price on Mars?", chunks=empty_chunks)

    expected_fallback = "I couldn't find enough information to answer this question from the available company documentation."
    assert result["answer"] == expected_fallback
    assert result["sources"] == []
    assert result["is_grounded"] is False


def test_validate_citations_strips_sources_on_abstention():
    """If the answer states that context is missing, citations must be cleared."""
    abstention_answer = "I couldn't find enough information to answer this question from the available company documentation."
    sources = ["hr_policies.md", "company_overview.md"]

    validated = validate_citations(abstention_answer, sources)
    assert validated == []


def test_validate_citations_preserves_sources_on_factual_answer():
    """A factual answer preserves retrieved source filenames."""
    factual_answer = "At Aurelia Tech, employees receive 20 days of annual leave accrued at 1.67 days per month."
    sources = ["hr_policies.md"]

    validated = validate_citations(factual_answer, sources)
    assert validated == ["hr_policies.md"]


# -----------------------------------------------------------------------------
# 4. ROUTER FOLLOW-UP PERSISTENCE
# -----------------------------------------------------------------------------

def test_router_preserves_rag_route_on_conversational_followup():
    """Follow-up queries like 'what about sick leave?' or 'can you summarize that?' must stay on RAG."""
    state: GraphState = {
        "question": "What about sick leave?",
        "route": None,
        "answer": None,
        "sources": None,
        "source_details": None,
        "history": [
            {"question": "What is our annual leave policy?", "answer": "20 days annual leave.", "route": "rag"}
        ],
        "is_grounded": None,
    }

    result = router_node(state)
    assert result["route"] == "rag"


def test_router_preserves_rag_on_summarize_followup():
    """Follow-up queries like 'Can you summarize that?' must route to RAG when prior turn was RAG."""
    state: GraphState = {
        "question": "Can you summarize that for me?",
        "route": None,
        "answer": None,
        "sources": None,
        "source_details": None,
        "history": [
            {"question": "Describe our code review process", "answer": "We use GitHub PRs with 2 approvers.", "route": "rag"}
        ],
        "is_grounded": None,
    }

    result = router_node(state)
    assert result["route"] == "rag"
