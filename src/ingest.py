import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

from config import RAW_DOCS_DIR, VECTORSTORE_DIR, CHUNK_SIZE, CHUNK_OVERLAP, EMBEDDING_MODEL, GEMINI_API_KEY


def load_documents():
    """Load all markdown files from the raw docs directory."""
    loader = DirectoryLoader(
        RAW_DOCS_DIR,
        glob="*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    documents = loader.load()
    print(f"Loaded {len(documents)} documents")
    return documents


def split_documents(documents):
    """Split documents into smaller overlapping chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = splitter.split_documents(documents)
    print(f"Split into {len(chunks)} chunks")
    return chunks


def embed_and_store(chunks):
    """Convert chunks to embeddings and store them in ChromaDB."""
    embeddings = GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=GEMINI_API_KEY,
    )

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=VECTORSTORE_DIR,
    )
    print(f"Stored {len(chunks)} chunks in vector database at '{VECTORSTORE_DIR}'")
    return vectorstore


if __name__ == "__main__":
    docs = load_documents()
    chunks = split_documents(docs)
    embed_and_store(chunks)
    print("Ingestion complete.")