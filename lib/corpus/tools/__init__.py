"""Corpus tools for PDF and document processing.

This module provides utilities for preparing documents for corpus import.

Available tools:
    split_pdf: Split large PDFs into chapters based on Table of Contents
"""

from lib.corpus.tools.split_pdf import Chapter, detect_chapters, split_pdf

__all__ = ["Chapter", "detect_chapters", "split_pdf"]
