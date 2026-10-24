"""Semantic Document Retrieval Module for the Enterprise Company Knowledge Assistant.

Queries the ChromaDB vector store using dense vector embeddings, with support
for similarity scoring, metadata enrichment, connection caching, and graceful fallbacks.
"""

from typing import List, Optional, Tuple
from pathlib import Path

from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

from src.config import (
    VECTORSTORE_DIR,
    EMBEDDING_MODEL,
    GEMINI_API_KEY,
    RETRIEVAL_K,
    MIN_RELEVANCE_SCORE,
    validate_config,
)

# Global cache for the vectorstore instance to avoid re-initializing on every query
_CACHED_VECTORSTORE: Optional[Chroma] = None


def load_vectorstore(
    vectorstore_dir: str = VECTORSTORE_DIR,
    force_reload: bool = False,
) -> Chroma:
    """Loads and caches the persistent ChromaDB vector store.

    Args:
        vectorstore_dir: Path to persistent vector database folder.
        force_reload: If True, bypasses cache and initializes a fresh instance.

    Returns:
        Chroma vectorstore instance.
    """
    global _CACHED_VECTORSTORE

    if _CACHED_VECTORSTORE is not None and not force_reload:
        return _CACHED_VECTORSTORE

    validation = validate_config(require_api_key=True)
    if not validation["valid"]:
        raise ValueError("\n".join(validation["errors"]))

    vs_path = Path(vectorstore_dir)
    if not vs_path.exists():
        raise FileNotFoundError(
            f"Vector store directory does not exist at '{vectorstore_dir}'. "
            "Please run 'python -m src.ingest' first to index documents."
        )

    embeddings = GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=GEMINI_API_KEY,
    )

    vectorstore = Chroma(
        persist_directory=vectorstore_dir,
        embedding_function=embeddings,
    )
    _CACHED_VECTORSTORE = vectorstore
    return vectorstore


def enrich_query_with_history(query: str, history: Optional[List[dict]] = None) -> str:
    """If the query is a brief follow-up referencing prior conversation, enriches it.

    Resolves referential phrases (e.g., 'what about sick leave?', 'can you summarize that?',
    'how many days for that?') by combining the current follow-up with the primary topic
    from previous conversation turns so ChromaDB semantic search retrieves the correct chunks.
    """
    if not history or not query:
        return query

    lower_query = query.strip().lower()

    # Signals that indicate the query is a conversational follow-up
    referential_triggers = [
        "that", " it", "it ", "those", "they", "them", "these", "this",
        "what about", "how about", "and what", "tell me more",
        "summarize", "summarise", "summary", "shorten",
        "explain that", "explain more", "in simple terms",
        "can you", "could you", "what does that mean",
        "who owns that", "where is that", "is that allowed",
    ]

    is_referential = any(trigger in lower_query for trigger in referential_triggers) or len(lower_query.split()) <= 4

    if is_referential and len(history) > 0:
        # Find the last substantive question from history
        last_turn = history[-1]
        last_q = (last_turn.get("question") or "").strip()

        # If user is asking to summarize, the search should focus on the prior topic
        if any(sm in lower_query for sm in ["summarize", "summarise", "summary", "shorten"]):
            return f"{last_q} overview guidelines summary"

        # Otherwise combine prior question with current follow-up
        if last_q:
            return f"{last_q} {query}"

    return query


def retrieve_relevant_chunks(
    query: str,
    k: int = RETRIEVAL_K,
    score_threshold: float = MIN_RELEVANCE_SCORE,
    history: Optional[List[dict]] = None,
) -> List[Document]:
    """Retrieves the top-k most semantically relevant document chunks from ChromaDB.

    Args:
        query: User search query.
        k: Maximum number of chunks to return.
        score_threshold: Minimum cosine relevance score (0.0 to 1.0).
        history: Prior conversation turns for contextual query enrichment.

    Returns:
        List of Document objects with metadata (source, title, chunk_index, score).
    """
    cleaned_query = (query or "").strip()
    if not cleaned_query:
        return []

    try:
        vectorstore = load_vectorstore()
    except Exception as e:
        print(f"[Retrieval Error] Could not connect to vector store: {e}")
        return []

    search_query = enrich_query_with_history(cleaned_query, history)

    try:
        # Retrieve chunks with relevance scores (cosine similarity)
        results_with_scores: List[Tuple[Document, float]] = (
            vectorstore.similarity_search_with_relevance_scores(search_query, k=k)
        )
    except Exception as e:
        print(f"[Retrieval Warning] similarity_search_with_relevance_scores failed ({e}), falling back to standard search.")
        try:
            return vectorstore.similarity_search(search_query, k=k)
        except Exception as inner_e:
            print(f"[Retrieval Error] Vector search failed: {inner_e}")
            return []

    filtered_chunks: List[Document] = []
    for doc, score in results_with_scores:
        doc.metadata["relevance_score"] = round(float(score), 3) if score is not None else 0.0
        if score_threshold <= 0.0 or (score is not None and score >= score_threshold):
            filtered_chunks.append(doc)

    return filtered_chunks


if __name__ == "__main__":
    test_query = "What is the annual leave policy and how many days can I carry over?"
    chunks = retrieve_relevant_chunks(test_query, k=3)

    print(f"Query: {test_query}\n")
    print(f"Retrieved {len(chunks)} chunks:\n")
    for i, chunk in enumerate(chunks, 1):
        source = chunk.metadata.get("source", "unknown")
        title = chunk.metadata.get("title", "No Title")
        score = chunk.metadata.get("relevance_score", "N/A")
        print(f"--- Result {i}: {title} [{source}] (Score: {score}) ---")
        print(chunk.page_content[:200] + "...")
        print()