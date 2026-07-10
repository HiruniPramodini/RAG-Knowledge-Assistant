from src.graph import build_graph


def test_technical_question_routes_to_rag():
    """A technical question should trigger the RAG path and return sources."""
    graph = build_graph()
    result = graph.invoke({
        "question": "What is a Docker volume?",
        "needs_retrieval": None,
        "answer": None,
        "sources": None,
    })

    assert result["needs_retrieval"] is True
    assert len(result["sources"]) > 0


