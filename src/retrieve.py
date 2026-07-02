from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

from config import VECTORSTORE_DIR, EMBEDDING_MODEL, GEMINI_API_KEY


def load_vectorstore():
    """Load the existing ChromaDB vector database from disk."""
    embeddings = GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=GEMINI_API_KEY,
    )
    vectorstore = Chroma(
        persist_directory=VECTORSTORE_DIR,
        embedding_function=embeddings,
    )
    return vectorstore


def retrieve_relevant_chunks(query, k=3):
    """Given a query, return the k most relevant chunks from the vector database."""
    vectorstore = load_vectorstore()
    results = vectorstore.similarity_search(query, k=k)
    return results


if __name__ == "__main__":
    query = "how do I stop my container from losing data on restart?"
    chunks = retrieve_relevant_chunks(query)

    print(f"Query: {query}\n")
    for i, chunk in enumerate(chunks, 1):
        source = chunk.metadata.get("source", "unknown")
        print(f"--- Result {i} (from {source}) ---")
        print(chunk.page_content)
        print()