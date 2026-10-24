"""Unit tests for configuration validation and defaults."""

import os
from src.config import validate_config, CHUNK_SIZE, CHUNK_OVERLAP, RETRIEVAL_K, HISTORY_LIMIT


def test_config_defaults():
    """Verifies that default configuration values are positive and reasonable."""
    assert CHUNK_SIZE > 0
    assert CHUNK_OVERLAP >= 0
    assert CHUNK_OVERLAP < CHUNK_SIZE
    assert RETRIEVAL_K >= 1
    assert HISTORY_LIMIT >= 1


def test_validate_config_with_key():
    """When GEMINI_API_KEY is present, validation should succeed."""
    res = validate_config(require_api_key=False)
    assert res["valid"] is True
    assert len(res["errors"]) == 0


def test_validate_config_missing_key(monkeypatch):
    """When GEMINI_API_KEY is forced empty, validation should report an error."""
    monkeypatch.setattr("src.config.GEMINI_API_KEY", "")
    res = validate_config(require_api_key=True)
    assert res["valid"] is False
    assert any("GEMINI_API_KEY" in err for err in res["errors"])
