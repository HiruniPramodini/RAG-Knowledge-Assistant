"""Centralized configuration for the Enterprise Company Knowledge Assistant.

Loads configuration from environment variables (.env) with safe production-minded defaults.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Secrets and API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# Model Definitions
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")
GENERATION_MODEL = os.getenv("GENERATION_MODEL", "gemini-3.5-flash")
ROUTING_MODEL = os.getenv("ROUTING_MODEL", "gemini-3.5-flash")

# Directory Paths
RAW_DOCS_DIR = os.getenv("RAW_DOCS_DIR", str(BASE_DIR / "data" / "raw_docs"))
VECTORSTORE_DIR = os.getenv("VECTORSTORE_DIR", str(BASE_DIR / "vectorstore"))

# Ingestion & Chunking Settings
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))          # characters per chunk
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))      # characters shared between chunks

# Retrieval Settings
RETRIEVAL_K = int(os.getenv("RETRIEVAL_K", "3"))           # top-k chunks to retrieve
MIN_RELEVANCE_SCORE = float(os.getenv("MIN_RELEVANCE_SCORE", "0.0"))  # optional threshold

# Conversation Memory
HISTORY_LIMIT = int(os.getenv("HISTORY_LIMIT", "3"))       # previous turns in prompt context


def validate_config(require_api_key: bool = True) -> dict:
    """Validates core configuration and returns status dictionary.

    Args:
        require_api_key: Whether to enforce that GEMINI_API_KEY must be set.

    Returns:
        Dictionary with status, errors, and warnings.
    """
    errors = []
    warnings = []

    if require_api_key and not GEMINI_API_KEY:
        errors.append(
            "GEMINI_API_KEY is missing. Please set it in your .env file or environment."
        )

    docs_path = Path(RAW_DOCS_DIR)
    if not docs_path.exists():
        warnings.append(f"Knowledge documents directory does not exist yet: {docs_path}")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }