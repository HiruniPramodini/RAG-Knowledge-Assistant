from src.retrieve import retrieve_relevant_chunks


def test_docker_query_returns_docker_content():
    """A Docker-specific question should retrieve chunks from the Docker doc."""
    results = retrieve_relevant_chunks("what is a docker container?", k=3)
    sources = [chunk.metadata.get("source", "") for chunk in results]

    assert len(results) == 3
    assert any("docker" in source.lower() for source in sources)


def test_kubernetes_query_returns_kubernetes_content():
    """A Kubernetes-specific question should retrieve chunks from the Kubernetes doc."""
    results = retrieve_relevant_chunks("what is a kubernetes pod?", k=3)
    sources = [chunk.metadata.get("source", "") for chunk in results]

    assert any("kubernetes" in source.lower() for source in sources)


def test_fastapi_query_returns_fastapi_content():
    """A FastAPI-specific question should retrieve chunks from the FastAPI doc."""
    results = retrieve_relevant_chunks("how does fastapi validate request data?", k=3)
    sources = [chunk.metadata.get("source", "") for chunk in results]

    assert any("fastapi" in source.lower() for source in sources)


def test_retrieval_respects_k_parameter():
    """Requesting k results should return exactly k chunks."""
    results = retrieve_relevant_chunks("what is a container?", k=2)
    assert len(results) == 2


def test_chunks_have_content():
    """Every retrieved chunk should contain actual, non-empty text."""
    results = retrieve_relevant_chunks("what is docker?", k=3)
    for chunk in results:
        assert len(chunk.page_content.strip()) > 0