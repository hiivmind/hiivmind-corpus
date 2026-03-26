"""Building blocks for PDF-to-markdown extraction.

Shared utilities that bespoke extraction scripts import.
Each corpus generates its own extraction script using these building blocks.

Requirements:
    pip install pymupdf
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import pymupdf
except ImportError:
    print("Error: pymupdf is required. Install with: pip install pymupdf")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class TextBlock:
    """A block of text extracted from a PDF page with font metadata."""
    text: str
    font: str
    size: float
    flags: int  # pymupdf font flags
    bbox: tuple[float, float, float, float]  # (x0, y0, x1, y1)
    page_num: int

    @property
    def is_bold(self) -> bool:
        """Check if font is bold (pymupdf flags bit 4)."""
        return bool(self.flags & 16)

    @property
    def is_italic(self) -> bool:
        """Check if font is italic (pymupdf flags bit 1)."""
        return bool(self.flags & 2)

    @property
    def is_monospace(self) -> bool:
        """Check if font is monospace (pymupdf flags bit 3)."""
        return bool(self.flags & 8)


@dataclass
class TocEntry:
    """A table-of-contents entry from PDF bookmarks."""
    level: int
    title: str
    page: int  # 0-indexed


@dataclass
class ChapterBoundary:
    """A detected chapter with page boundaries."""
    index: int
    title: str
    start_page: int  # 0-indexed
    end_page: int  # exclusive

    @property
    def page_count(self) -> int:
        return self.end_page - self.start_page

    @property
    def page_range(self) -> str:
        """Human-readable page range (1-indexed)."""
        return f"{self.start_page + 1}-{self.end_page}"


@dataclass
class CrossRef:
    """A cross-reference found in document text."""
    original_text: str
    ref_type: str  # "chapter_reference", "section_reference", "see_reference"
    display_text: str
    page_number: int | None = None


@dataclass
class FontInfo:
    """Summary of a font used in the document."""
    name: str
    size: float
    flags: int
    count: int = 0  # how many blocks use this font


# ---------------------------------------------------------------------------
# Document analysis
# ---------------------------------------------------------------------------

def open_pdf(path: str | Path) -> pymupdf.Document:
    """Open a PDF document."""
    return pymupdf.open(str(path))


def get_toc(doc: pymupdf.Document) -> list[TocEntry]:
    """Extract table of contents from PDF bookmarks."""
    raw_toc = doc.get_toc()
    return [TocEntry(level=lvl, title=title, page=page - 1) for lvl, title, page in raw_toc]


def get_page_count(doc: pymupdf.Document) -> int:
    """Return total page count."""
    return len(doc)
