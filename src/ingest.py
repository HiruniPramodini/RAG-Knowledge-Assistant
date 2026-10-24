"""Document Ingestion Pipeline for the Enterprise Company Knowledge Assistant.

Handles loading, splitting, embedding, and indexing internal company documentation
into a persistent ChromaDB vector store. Supports stable chunk IDs, incremental updates,
duplicate prevention, and full rebuilds.
"""

import argparse
import hashlib
import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

from src.config import (
    RAW_DOCS_DIR,
    VECTORSTORE_DIR,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    EMBEDDING_MODEL,
    GEMINI_API_KEY,
    validate_config,
)


def extract_document_title(content: str, default_title: str) -> str:
    """Extracts the first H1 markdown heading or falls back to default title."""
    match = re.search(r"^#\s+(.+)$", content, flags=re.MULTILINE)
    if match:
        return match.group(1).strip()
    return default_title


def compute_file_hash(filepath: Path) -> str:
    """Computes SHA-256 hash of a file's content."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_documents(raw_docs_dir: str = RAW_DOCS_DIR) -> List[Document]:
    """Loads all Markdown (.md) documents from the raw docs directory.

    Preserves document filename, relative path, file hash, and extracted title.
    Handles empty files and non-existent directories gracefully.
    """
    docs_path = Path(raw_docs_dir)
    if not docs_path.exists():
        raise FileNotFoundError(f"Knowledge documents directory not found: {raw_docs_dir}")

    documents: List[Document] = []
    skipped_count = 0

    for file_path in sorted(docs_path.glob("*.md")):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()

            if not text.strip():
                print(f"  [Skip] Empty file: {file_path.name}")
                skipped_count += 1
                continue

            file_hash = compute_file_hash(file_path)
            default_title = file_path.stem.replace("_", " ").title()
            title = extract_document_title(text, default_title)

            metadata = {
                "source": file_path.name,
                "source_path": str(file_path.relative_to(docs_path.parent if docs_path.parent.exists() else docs_path)),
                "title": title,
                "doc_hash": file_hash,
            }
            documents.append(Document(page_content=text, metadata=metadata))
        except Exception as e:
            print(f"  [Error] Failed to read {file_path.name}: {e}")
            skipped_count += 1

    print(f"Loaded {len(documents)} valid documents ({skipped_count} skipped).")
    return documents


def split_documents(
    documents: List[Document],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> Tuple[List[Document], List[str]]:
    """Splits documents into overlapping chunks with stable deterministic IDs.

    Returns:
        Tuple of (chunks, chunk_ids)
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
    )

    chunks: List[Document] = []
    chunk_ids: List[str] = []

    for doc in documents:
        doc_chunks = splitter.split_documents([doc])
        for idx, chunk in enumerate(doc_chunks):
            # Include chunk index and metadata
            chunk.metadata["chunk_index"] = idx
            # Stable deterministic ID derived from source, chunk index, and content hash
            content_hash = hashlib.sha256(chunk.page_content.encode("utf-8")).hexdigest()[:16]
            chunk_id = f"{chunk.metadata['source']}#chunk_{idx}_{content_hash}"
            chunks.append(chunk)
            chunk_ids.append(chunk_id)

    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")
    return chunks, chunk_ids


def get_embedding_function() -> GoogleGenerativeAIEmbeddings:
    """Initializes the Gemini embedding model with validated API key."""
    validation = validate_config(require_api_key=True)
    if not validation["valid"]:
        raise ValueError("\n".join(validation["errors"]))

    return GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=GEMINI_API_KEY,
    )


def ingest_documents(
    rebuild: bool = False,
    raw_docs_dir: str = RAW_DOCS_DIR,
    vectorstore_dir: str = VECTORSTORE_DIR,
) -> Dict[str, int]:
    """Ingests documents into ChromaDB with duplicate prevention and incremental updates.

    Args:
        rebuild: If True, clears existing index and rebuilds completely.
        raw_docs_dir: Directory containing source markdown files.
        vectorstore_dir: Directory for persistent ChromaDB storage.

    Returns:
        Summary dictionary with ingestion statistics.
    """
    print("=" * 60)
    print("Enterprise Knowledge Ingestion Pipeline")
    print(f"Source Directory: {raw_docs_dir}")
    print(f"Vector Database:  {vectorstore_dir}")
    print(f"Rebuild Mode:     {rebuild}")
    print("=" * 60)

    docs = load_documents(raw_docs_dir)
    if not docs:
        print("No documents found to ingest.")
        return {"documents": 0, "chunks_added": 0, "chunks_total": 0}

    embeddings = get_embedding_function()

    if rebuild and os.path.exists(vectorstore_dir):
        print(f"Cleaning existing vectorstore at '{vectorstore_dir}' for full rebuild...")
        try:
            shutil.rmtree(vectorstore_dir)
        except Exception as e:
            print(f"Warning: could not delete folder directly ({e}), will reset via Chroma API.")

    vectorstore = Chroma(
        persist_directory=vectorstore_dir,
        embedding_function=embeddings,
    )

    # Inspect current collection
    existing_data = vectorstore.get(include=["metadatas"])
    existing_ids = set(existing_data.get("ids", []))
    existing_metas = existing_data.get("metadatas", []) or []

    # Map existing source -> set of IDs, and source -> doc_hash
    source_to_existing_ids: Dict[str, set] = {}
    source_to_existing_hash: Dict[str, str] = {}
    for cid, meta in zip(existing_data.get("ids", []), existing_metas):
        src = meta.get("source", "unknown")
        source_to_existing_ids.setdefault(src, set()).add(cid)
        if "doc_hash" in meta:
            source_to_existing_hash[src] = meta["doc_hash"]

    current_sources = {doc.metadata["source"] for doc in docs}

    # 1. Prune obsolete documents that were deleted from disk
    obsolete_sources = set(source_to_existing_ids.keys()) - current_sources
    for obs_src in obsolete_sources:
        ids_to_del = list(source_to_existing_ids[obs_src])
        print(f"  [Prune] Document deleted from disk: {obs_src} (removing {len(ids_to_del)} chunks)")
        vectorstore.delete(ids=ids_to_del)

    # 2. Identify new or modified documents
    docs_to_index: List[Document] = []
    for doc in docs:
        src = doc.metadata["source"]
        current_hash = doc.metadata["doc_hash"]
        prev_hash = source_to_existing_hash.get(src)

        if prev_hash == current_hash and not rebuild:
            # File is unchanged!
            continue

        if prev_hash and prev_hash != current_hash:
            # File changed, delete old chunks first
            old_ids = list(source_to_existing_ids.get(src, []))
            if old_ids:
                print(f"  [Update] Document modified: {src} (updating {len(old_ids)} stale chunks)")
                vectorstore.delete(ids=old_ids)

        docs_to_index.append(doc)

    if not docs_to_index:
        total_chunks = len(vectorstore.get()["ids"])
        print(f"\nAll {len(docs)} documents are already up to date. Total chunks in index: {total_chunks}")
        return {"documents": len(docs), "chunks_added": 0, "chunks_total": total_chunks}

    # Split documents to index
    chunks_to_add, chunk_ids_to_add = split_documents(docs_to_index)

    # Filter out any IDs already present (safety check against duplicates)
    filtered_chunks: List[Document] = []
    filtered_ids: List[str] = []
    for c, cid in zip(chunks_to_add, chunk_ids_to_add):
        if cid not in existing_ids or rebuild:
            filtered_chunks.append(c)
            filtered_ids.append(cid)

    if filtered_chunks:
        batch_size = 25
        print(f"Embedding and storing {len(filtered_chunks)} chunks into ChromaDB in batches of {batch_size}...")
        
        import time
        for i in range(0, len(filtered_chunks), batch_size):
            batch_docs = filtered_chunks[i : i + batch_size]
            batch_ids = filtered_ids[i : i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(filtered_chunks) + batch_size - 1) // batch_size
            print(f"  Indexing batch {batch_num}/{total_batches} ({len(batch_docs)} chunks)...")

            max_retries = 4
            for attempt in range(max_retries):
                try:
                    vectorstore.add_documents(documents=batch_docs, ids=batch_ids)
                    break
                except Exception as e:
                    err_msg = str(e)
                    if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "Quota exceeded" in err_msg:
                        wait_sec = 35
                        print(f"  [Rate Limit] Gemini embedding quota hit. Waiting {wait_sec}s for quota replenishment (attempt {attempt+1}/{max_retries})...")
                        time.sleep(wait_sec)
                    else:
                        print(f"  [Error] Batch {batch_num} failed: {e}")
                        raise e
            # Polite pause between batches
            time.sleep(2)

        print(f"Successfully stored {len(filtered_chunks)} chunks.")

    total_chunks = len(vectorstore.get()["ids"])
    print("=" * 60)
    print(f"Ingestion Complete! Vector store now contains {total_chunks} chunks.")
    print("=" * 60)

    return {
        "documents": len(docs),
        "chunks_added": len(filtered_chunks),
        "chunks_total": total_chunks,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest company knowledge documents into ChromaDB.")
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Perform a complete index rebuild, removing previous chunks.",
    )
    args = parser.parse_args()

    ingest_documents(rebuild=args.rebuild)