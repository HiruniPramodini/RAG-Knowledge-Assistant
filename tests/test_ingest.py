"""Unit tests for document loading, splitting, and metadata extraction."""

import tempfile
from pathlib import Path
from langchain_core.documents import Document

from src.ingest import (
    extract_document_title,
    compute_file_hash,
    load_documents,
    split_documents,
)


def test_extract_document_title():
    """Extracts H1 markdown title correctly or falls back to default."""
    content_with_h1 = "# Engineering Handbook\n\nSome text."
    assert extract_document_title(content_with_h1, "Default") == "Engineering Handbook"

    content_without_h1 = "## Subheading\n\nSome text."
    assert extract_document_title(content_without_h1, "Default") == "Default"


def test_load_documents_and_skip_empty():
    """Verifies that load_documents loads valid .md files and skips empty ones."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dir_path = Path(temp_dir)

        # Create valid file
        valid_file = dir_path / "valid.md"
        valid_file.write_text("# Valid Title\n\nValid content for testing.", encoding="utf-8")

        # Create empty file
        empty_file = dir_path / "empty.md"
        empty_file.write_text("   \n\n", encoding="utf-8")

        docs = load_documents(temp_dir)
        assert len(docs) == 1
        assert docs[0].metadata["source"] == "valid.md"
        assert docs[0].metadata["title"] == "Valid Title"
        assert "doc_hash" in docs[0].metadata


def test_split_documents_preserves_metadata_and_ids():
    """Verifies that splitting documents generates stable IDs and preserves metadata."""
    doc = Document(
        page_content="A" * 1200,  # Longer than chunk size (500)
        metadata={"source": "test_doc.md", "title": "Test Doc", "doc_hash": "abc123hash"},
    )

    chunks, chunk_ids = split_documents([doc], chunk_size=500, chunk_overlap=50)

    assert len(chunks) > 1
    assert len(chunks) == len(chunk_ids)

    for idx, (chunk, cid) in enumerate(zip(chunks, chunk_ids)):
        assert chunk.metadata["source"] == "test_doc.md"
        assert chunk.metadata["chunk_index"] == idx
        assert cid.startswith("test_doc.md#chunk_")
