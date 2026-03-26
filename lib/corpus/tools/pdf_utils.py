"""Building blocks for PDF-to-markdown extraction.

Shared utilities that bespoke extraction scripts import.
Each corpus generates its own extraction script using these building blocks.

Requirements:
    pip install pymupdf
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
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


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------

def extract_text_blocks(page: pymupdf.Page) -> list[TextBlock]:
    """Extract text blocks from a page with font metadata.

    Uses pymupdf's dict-based extraction to get font info per span.
    Groups spans into blocks based on their block membership.
    """
    blocks = []
    page_dict = page.get_text("dict", flags=pymupdf.TEXT_PRESERVE_WHITESPACE)

    for block in page_dict.get("blocks", []):
        if block.get("type") != 0:  # skip image blocks
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "").strip()
                if not text:
                    continue
                blocks.append(TextBlock(
                    text=text,
                    font=span.get("font", ""),
                    size=round(span.get("size", 0), 1),
                    flags=span.get("flags", 0),
                    bbox=tuple(span.get("bbox", (0, 0, 0, 0))),
                    page_num=page.number,
                ))
    return blocks


def strip_headers_footers(
    blocks: list[TextBlock],
    header_pattern: str | None = None,
    header_zone_top: float = 50,
    footer_zone_bottom: float = 40,
    page_height: float = 842,  # A4 default in points
) -> list[TextBlock]:
    """Remove running headers and footers from extracted blocks.

    Args:
        blocks: Text blocks from a page.
        header_pattern: Regex to match header text. If None, uses zone only.
        header_zone_top: Points from top of page — blocks above this are headers.
        footer_zone_bottom: Points from bottom — blocks below (page_height - this) are footers.
        page_height: Page height in points.
    """
    result = []
    footer_threshold = page_height - footer_zone_bottom

    for block in blocks:
        y_pos = block.bbox[1]  # y0 of bounding box

        # Skip footer zone
        if y_pos >= footer_threshold:
            continue

        # Skip header zone
        if y_pos <= header_zone_top:
            if header_pattern is None or re.search(header_pattern, block.text):
                continue

        result.append(block)

    return result


# ---------------------------------------------------------------------------
# Font analysis
# ---------------------------------------------------------------------------

def _aggregate_font_info(blocks: list[TextBlock]) -> dict[str, FontInfo]:
    """Aggregate font usage statistics from text blocks."""
    fonts: dict[str, FontInfo] = {}
    for block in blocks:
        key = f"{block.font}:{block.size}"
        if key not in fonts:
            fonts[key] = FontInfo(name=block.font, size=block.size, flags=block.flags, count=0)
        fonts[key].count += 1
    return fonts


def analyze_fonts(doc: pymupdf.Document, sample_page_nums: list[int] | None = None) -> dict[str, FontInfo]:
    """Analyze font usage across sample pages.

    Args:
        doc: Open PDF document.
        sample_page_nums: Pages to sample (0-indexed). Defaults to first 10 pages.

    Returns:
        Dict mapping "fontname:size" to FontInfo with usage counts.
    """
    if sample_page_nums is None:
        sample_page_nums = list(range(min(10, len(doc))))

    all_blocks: list[TextBlock] = []
    for page_num in sample_page_nums:
        if 0 <= page_num < len(doc):
            all_blocks.extend(extract_text_blocks(doc[page_num]))

    return _aggregate_font_info(all_blocks)


# ---------------------------------------------------------------------------
# Chapter detection
# ---------------------------------------------------------------------------

def detect_chapters_from_toc(doc: pymupdf.Document, level: int = 1) -> list[ChapterBoundary]:
    """Detect chapters from PDF TOC bookmarks.

    Args:
        doc: Open PDF document.
        level: TOC level to use (1 = top-level chapters).

    Returns:
        List of ChapterBoundary objects. Empty if no TOC.
    """
    toc_entries = get_toc(doc)
    if not toc_entries:
        return []
    return detect_chapters_from_toc_entries(toc_entries, get_page_count(doc), level)


def detect_chapters_from_toc_entries(
    entries: list[TocEntry],
    total_pages: int,
    level: int = 1,
) -> list[ChapterBoundary]:
    """Build chapter boundaries from TOC entries at a given level.

    Args:
        entries: TOC entries from get_toc().
        total_pages: Total pages in the document.
        level: TOC level to filter to.

    Returns:
        List of ChapterBoundary with start/end pages.
    """
    filtered = [(e.title, e.page) for e in entries if e.level == level]
    if not filtered:
        return []

    chapters = []
    for i, (title, start) in enumerate(filtered):
        end = filtered[i + 1][1] if i + 1 < len(filtered) else total_pages
        chapters.append(ChapterBoundary(
            index=i + 1,
            title=title,
            start_page=start,
            end_page=end,
        ))
    return chapters


def detect_chapters_from_fonts(
    doc: pymupdf.Document,
    h1_font: str,
    h1_size_min: float,
    top_zone: float = 150,
) -> list[ChapterBoundary]:
    """Detect chapters by finding H1-sized text near the top of pages.

    Fallback when PDF has no TOC bookmarks. Uses the extraction profile's
    font rules to identify chapter title text.

    Args:
        doc: Open PDF document.
        h1_font: Font name for chapter titles (substring match).
        h1_size_min: Minimum font size for chapter titles.
        top_zone: Only consider text within this many points of page top.

    Returns:
        List of ChapterBoundary objects.
    """
    chapter_starts: list[tuple[str, int]] = []

    for page_num in range(len(doc)):
        blocks = extract_text_blocks(doc[page_num])
        for block in blocks:
            if (block.bbox[1] <= top_zone
                    and block.size >= h1_size_min
                    and h1_font.lower() in block.font.lower()):
                chapter_starts.append((block.text.strip(), page_num))
                break  # only first match per page

    if not chapter_starts:
        return []

    total = len(doc)
    chapters = []
    for i, (title, start) in enumerate(chapter_starts):
        end = chapter_starts[i + 1][1] if i + 1 < len(chapter_starts) else total
        chapters.append(ChapterBoundary(
            index=i + 1,
            title=title,
            start_page=start,
            end_page=end,
        ))
    return chapters


# ---------------------------------------------------------------------------
# Markdown emission
# ---------------------------------------------------------------------------

def emit_heading(text: str, level: int) -> str:
    """Emit a markdown heading."""
    return f"{'#' * level} {text}"


def emit_code_block(text: str, language: str = "") -> str:
    """Emit a fenced code block."""
    return f"```{language}\n{text}\n```"


def emit_table(headers: list[str], rows: list[list[str]]) -> str:
    """Emit a markdown table."""
    header_row = "| " + " | ".join(headers) + " |"
    separator = "| " + " | ".join("---" for _ in headers) + " |"
    data_rows = "\n".join("| " + " | ".join(row) + " |" for row in rows)
    return f"{header_row}\n{separator}\n{data_rows}"


def emit_callout(text: str, callout_type: str) -> str:
    """Emit a blockquote-style callout."""
    label = callout_type.capitalize()
    return f"> **{label}:** {text}"


def emit_frontmatter(metadata: dict[str, Any]) -> str:
    """Emit YAML frontmatter block.

    Uses simple serialization — no external YAML library required.
    Handles strings, lists of strings, and lists of dicts.
    """
    lines = ["---"]
    for key, value in metadata.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                if isinstance(item, dict):
                    first = True
                    for k, v in item.items():
                        prefix = "  - " if first else "    "
                        lines.append(f"{prefix}{k}: {_yaml_quote(v)}")
                        first = False
                else:
                    lines.append(f"  - {_yaml_quote(item)}")
        else:
            lines.append(f"{key}: {_yaml_quote(value)}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def _yaml_quote(value: Any) -> str:
    """Quote a YAML value if it contains special characters."""
    s = str(value)
    if any(c in s for c in ":#{}[]|>&*!%@`"):
        return f'"{s}"'
    return s


# ---------------------------------------------------------------------------
# Cross-reference handling
# ---------------------------------------------------------------------------

def find_cross_references(text: str, patterns: list[tuple[str, str]]) -> list[CrossRef]:
    """Find cross-references in text using regex patterns.

    Args:
        text: Document text to search.
        patterns: List of (regex_pattern, ref_type) tuples.
            Expected group layout:
            - chapter_reference: (chapter_num, display_text, page_number)
            - section_reference: (display_text, page_number)
            - see_reference: (display_text, page_number)
    """
    refs = []
    for pattern, ref_type in patterns:
        for match in re.finditer(pattern, text):
            groups = match.groups()
            if ref_type == "chapter_reference" and len(groups) >= 3:
                refs.append(CrossRef(
                    original_text=match.group(0),
                    ref_type=ref_type,
                    display_text=groups[1].rstrip(",").strip(),
                    page_number=int(groups[2]),
                ))
            elif len(groups) >= 2:
                refs.append(CrossRef(
                    original_text=match.group(0),
                    ref_type=ref_type,
                    display_text=groups[0],
                    page_number=int(groups[1]),
                ))
    return refs


def resolve_cross_ref(
    ref: CrossRef,
    chapters: list[ChapterBoundary],
    filename_pattern: str = "{index:02d}_{title}",
) -> str | None:
    """Resolve a cross-reference to a target filename.

    Looks up which chapter contains the referenced page number.
    """
    if ref.page_number is None:
        return None

    for ch in chapters:
        # page_number is 1-indexed in source text, start_page is 0-indexed
        if ch.start_page <= (ref.page_number - 1) < ch.end_page:
            safe_title = sanitize_filename(ch.title)
            return filename_pattern.format(index=ch.index, title=safe_title)
    return None


def make_wikilink(target_file: str, display_text: str) -> str:
    """Create an Obsidian-style wikilink."""
    return f"[[{target_file}|{display_text}]]"


# ---------------------------------------------------------------------------
# File output
# ---------------------------------------------------------------------------

def write_chapter_markdown(path: Path, frontmatter: dict[str, Any], body: str) -> None:
    """Write a markdown file with YAML frontmatter."""
    path.parent.mkdir(parents=True, exist_ok=True)
    content = emit_frontmatter(frontmatter) + "\n" + body
    path.write_text(content, encoding="utf-8")


def sanitize_filename(title: str, max_length: int = 50) -> str:
    """Convert a chapter title to a safe filename."""
    safe = re.sub(r"[^\w\s-]", "", title)
    safe = re.sub(r"[\s]+", "_", safe)
    return safe[:max_length].strip("_")
