"""Integration tests for semantic vector retrieval against the indexed company knowledge base."""

from src.retrieve import retrieve_relevant_chunks


def test_hr_query_returns_hr_content():
    """An HR-specific question should retrieve chunks from hr_policies.md."""
    results = retrieve_relevant_chunks("What is the annual leave carryover policy?", k=3)
    sources = [chunk.metadata.get("source", "") for chunk in results]

    assert len(results) > 0
    assert any("hr_policies" in source.lower() for source in sources)


def test_it_query_returns_it_content():
    """An IT-specific question should retrieve chunks from it_onboarding.md."""
    results = retrieve_relevant_chunks("How do I connect to the company VPN and setup MFA?", k=3)
    sources = [chunk.metadata.get("source", "") for chunk in results]

    assert len(results) > 0
    assert any("it_onboarding" in source.lower() for source in sources)


def test_engineering_query_returns_engineering_content():
    """An engineering-specific question should retrieve chunks from engineering_standards.md."""
    results = retrieve_relevant_chunks("What are the pull request and code review rules?", k=3)
    sources = [chunk.metadata.get("source", "") for chunk in results]

    assert len(results) > 0
    assert any("engineering_standards" in source.lower() for source in sources)


def test_retrieval_respects_k_parameter():
    """Requesting k results should return at most k chunks."""
    results = retrieve_relevant_chunks("Aurelia mission and values", k=2)
    assert len(results) <= 2


def test_chunks_have_content_and_metadata():
    """Every retrieved chunk should contain non-empty content and valid source metadata."""
    results = retrieve_relevant_chunks("What is Project Atlas?", k=3)
    assert len(results) > 0
    for chunk in results:
        assert len(chunk.page_content.strip()) > 0
        assert "source" in chunk.metadata
        assert "title" in chunk.metadata