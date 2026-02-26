"""Unit tests for src/config.py — startup validation behaviour.

Uses unittest.mock.patch to override the module-level ANTHROPIC_API_KEY
variable so no real environment variable or .env file is required.
"""

import pytest
from unittest.mock import patch

from src.config import validate_config


def test_validate_config_raises_when_key_is_empty():
    """validate_config() must raise RuntimeError when the API key is an empty string."""
    with patch("src.config.ANTHROPIC_API_KEY", ""):
        with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
            validate_config()


def test_validate_config_passes_when_key_is_present():
    """validate_config() must not raise when the API key is a non-empty string."""
    with patch("src.config.ANTHROPIC_API_KEY", "sk-ant-test-key"):
        validate_config()  # should complete without raising
