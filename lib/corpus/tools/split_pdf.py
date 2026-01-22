#!/usr/bin/env python3
"""Split a PDF into chapters based on its Table of Contents.

This tool helps import large PDFs into hiivmind-corpus by splitting them
into smaller, chapter-sized files that can be indexed individually.

Usage:
    python -m lib.corpus.tools.split_pdf detect <input.pdf>           # Show detected chapters
    python -m lib.corpus.tools.split_pdf split <input.pdf> [-o DIR]   # Split with confirmation
    python -m lib.corpus.tools.split_pdf split <input.pdf> --yes      # Split without confirmation

Requirements:
    pip install pymupdf
"""

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    import pymupdf
except ImportError:
    print("Error: pymupdf is required. Install with: pip install pymupdf")
    sys.exit(1)


@dataclass
class Chapter:
    """Represents a detected chapter boundary."""

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


def detect_chapters(input_path: str, level: int = 1) -> list[Chapter]:
    """
    Detect chapter boundaries from PDF TOC.

    Args:
        input_path: Path to the input PDF file.
        level: TOC level to split at (1 = top-level chapters, 2 = sections, etc.)

    Returns:
        List of Chapter objects with boundaries.
    """
    doc = pymupdf.open(input_path)
    toc = doc.get_toc()
    total_pages = len(doc)
    doc.close()

    if not toc:
        return _detect_chapters_by_text(input_path)

    # Filter to requested level
    entries = [(title, page - 1) for lvl, title, page in toc if lvl == level]

    if not entries:
        # Try falling back to text detection if no entries at requested level
        return _detect_chapters_by_text(input_path)

    # Build chapters with boundaries
    chapters = []
    for i, (title, start) in enumerate(entries):
        end = entries[i + 1][1] if i + 1 < len(entries) else total_pages
        chapters.append(
            Chapter(
                index=i + 1,
                title=title,
                start_page=start,
                end_page=end,
            )
        )

    return chapters


def _detect_chapters_by_text(input_path: str) -> list[Chapter]:
    """Fallback: detect chapters by searching for 'Chapter X' patterns in text."""
    doc = pymupdf.open(input_path)
    total_pages = len(doc)
    chapter_starts: list[tuple[str, int]] = []
    pattern = re.compile(r"^Chapter\s+(\d+|[IVXLC]+)", re.IGNORECASE)

    for page_num in range(total_pages):
        text = doc[page_num].get_text()
        for line in text.split("\n")[:10]:  # Check first 10 lines of each page
            if match := pattern.match(line.strip()):
                # Use the matched line as title, truncated
                title = line.strip()[:60]
                chapter_starts.append((title, page_num))
                break

    doc.close()

    if not chapter_starts:
        return []

    # Convert to Chapter objects with proper boundaries
    result = []
    for i, (title, start) in enumerate(chapter_starts):
        end = chapter_starts[i + 1][1] if i + 1 < len(chapter_starts) else total_pages
        result.append(
            Chapter(
                index=i + 1,
                title=title,
                start_page=start,
                end_page=end,
            )
        )

    return result


def display_chapters(chapters: list[Chapter], input_path: str) -> None:
    """Display detected chapters in a formatted table."""
    filename = Path(input_path).name
    print(f"\nDetected {len(chapters)} chapters in {filename}:\n")
    print(f"  {'#':>3}  {'Title':<45} {'Pages':>10} {'Size':>12}")
    print(f"  {'-' * 3}  {'-' * 45} {'-' * 10} {'-' * 12}")

    for ch in chapters:
        title = ch.title[:42] + "..." if len(ch.title) > 45 else ch.title
        print(f"  {ch.index:>3}  {title:<45} {ch.page_range:>10} {ch.page_count:>8} pages")
    print()


def confirm_split() -> bool:
    """Prompt user to confirm the split."""
    try:
        response = input("Proceed with split? [Y/n]: ").strip().lower()
        return response in ("", "y", "yes")
    except (EOFError, KeyboardInterrupt):
        print()
        return False


def sanitize_filename(title: str, max_length: int = 50) -> str:
    """Convert a chapter title to a safe filename."""
    # Replace problematic characters with underscores
    safe = re.sub(r"[^\w\s-]", "_", title)
    # Collapse multiple spaces/underscores
    safe = re.sub(r"[\s_]+", "_", safe)
    # Truncate and strip
    return safe[:max_length].strip("_")


def split_pdf(
    input_path: str, chapters: list[Chapter], output_dir: Path
) -> list[Path]:
    """
    Execute the split, creating chapter PDFs and manifest.

    Args:
        input_path: Path to the input PDF file.
        chapters: List of Chapter objects defining split boundaries.
        output_dir: Directory to write output files.

    Returns:
        List of paths to created chapter PDF files.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(input_path)

    output_files = []
    manifest_chapters = []

    for ch in chapters:
        # Create safe filename from title
        safe_title = sanitize_filename(ch.title)
        filename = f"{ch.index:02d}_{safe_title}.pdf"
        output_path = output_dir / filename

        # Create chapter PDF
        new_doc = pymupdf.open()
        new_doc.insert_pdf(doc, from_page=ch.start_page, to_page=ch.end_page - 1)
        new_doc.save(output_path)
        new_doc.close()

        output_files.append(output_path)
        manifest_chapters.append(
            {
                "index": ch.index,
                "title": ch.title,
                "file": filename,
                "pages": ch.page_range,
            }
        )

        print(f"  Created: {filename}")

    doc.close()

    # Write manifest
    manifest = {
        "source": Path(input_path).name,
        "chapters": manifest_chapters,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"\n  Manifest: {manifest_path}")

    return output_files


def main(argv: Optional[list[str]] = None) -> int:
    """Main entry point for CLI."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Split PDF into chapters based on Table of Contents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s detect book.pdf              Show detected chapters
  %(prog)s detect book.pdf -l 2         Show sections (level 2)
  %(prog)s split book.pdf               Split with confirmation
  %(prog)s split book.pdf -o chapters/  Split to specific directory
  %(prog)s split book.pdf --yes         Split without confirmation
        """,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # detect command
    detect_parser = subparsers.add_parser(
        "detect", help="Show detected chapters without splitting"
    )
    detect_parser.add_argument("input", help="Input PDF file")
    detect_parser.add_argument(
        "-l",
        "--level",
        type=int,
        default=1,
        help="TOC level to detect (default: 1 for top-level chapters)",
    )

    # split command
    split_parser = subparsers.add_parser("split", help="Split PDF into chapter files")
    split_parser.add_argument("input", help="Input PDF file")
    split_parser.add_argument(
        "-o", "--output", help="Output directory (default: input filename without .pdf)"
    )
    split_parser.add_argument(
        "-l",
        "--level",
        type=int,
        default=1,
        help="TOC level to split at (default: 1 for top-level chapters)",
    )
    split_parser.add_argument(
        "-y", "--yes", action="store_true", help="Skip confirmation prompt"
    )

    args = parser.parse_args(argv)

    # Validate input file exists
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: File not found: {args.input}")
        return 1

    if not input_path.suffix.lower() == ".pdf":
        print(f"Warning: File does not have .pdf extension: {args.input}")

    # Detect chapters
    chapters = detect_chapters(str(input_path), args.level)

    if not chapters:
        print(f"No chapters detected in {args.input}")
        print("\nPossible reasons:")
        print("  - The PDF has no bookmarks/TOC")
        print("  - No entries at the requested level (-l option)")
        print("  - Chapter text patterns not recognized")
        print("\nConsider specifying manual page ranges or adding bookmarks first.")
        return 1

    display_chapters(chapters, str(input_path))

    if args.command == "split":
        if not args.yes and not confirm_split():
            print("Aborted.")
            return 0

        # Determine output directory
        if args.output:
            output_dir = Path(args.output)
        else:
            output_dir = input_path.with_suffix("")

        print(f"\nSplitting to {output_dir}/\n")
        split_pdf(str(input_path), chapters, output_dir)
        print(f"\nDone! {len(chapters)} chapters created.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
