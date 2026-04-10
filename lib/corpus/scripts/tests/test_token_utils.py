"""Tests for token_utils.py — shared token counting."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from token_utils import estimate_tokens


class TestEstimateTokens:
    """Token estimation with graceful fallback."""

    def test_empty_string_returns_zero(self):
        assert estimate_tokens("") == 0

    def test_single_word(self):
        result = estimate_tokens("hello")
        assert result >= 1

    def test_approximation_scales_with_length(self):
        short = estimate_tokens("one two three")
        long = estimate_tokens("one two three four five six seven eight nine ten")
        assert long > short

    def test_none_returns_zero(self):
        assert estimate_tokens(None) == 0

    def test_whitespace_only_returns_zero(self):
        assert estimate_tokens("   \n\t  ") == 0

    def test_returns_integer(self):
        result = estimate_tokens("some words here for testing purposes")
        assert isinstance(result, int)
