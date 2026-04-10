#!/usr/bin/env python3
"""Shared token counting with graceful fallback.

Tries fastembed's tokenizer first (accurate), falls back to
word-count approximation (len(text.split()) * 1.3).

Usage as module:
  from token_utils import estimate_tokens
  count = estimate_tokens("some text here")
"""

TOKENS_PER_WORD = 1.3

_tokenizer = None
_tokenizer_checked = False


def _get_tokenizer():
    """Try to load fastembed tokenizer once, cache result."""
    global _tokenizer, _tokenizer_checked
    if _tokenizer_checked:
        return _tokenizer
    _tokenizer_checked = True
    try:
        from fastembed import TextEmbedding

        model = TextEmbedding("BAAI/bge-small-en-v1.5")
        _tokenizer = model.model.tokenizer
    except Exception:
        _tokenizer = None
    return _tokenizer


def estimate_tokens(text: str | None) -> int:
    """Estimate token count for text.

    Returns 0 for None, empty, or whitespace-only strings.
    Uses fastembed tokenizer if available, else word-count * 1.3.
    """
    if not text or not text.strip():
        return 0

    tokenizer = _get_tokenizer()
    if tokenizer is not None:
        try:
            return len(tokenizer.encode(text).ids)
        except Exception:
            pass

    return int(len(text.split()) * TOKENS_PER_WORD)
