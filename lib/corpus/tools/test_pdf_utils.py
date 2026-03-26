import pytest
from pathlib import Path

def test_text_block_dataclass():
    from lib.corpus.tools.pdf_utils import TextBlock
    block = TextBlock(
        text="Hello world",
        font="TimesNewRoman",
        size=12.0,
        flags=0,
        bbox=(0, 0, 100, 20),
        page_num=0,
    )
    assert block.text == "Hello world"
    assert block.font == "TimesNewRoman"
    assert block.is_bold is False

def test_text_block_bold_detection():
    from lib.corpus.tools.pdf_utils import TextBlock
    # pymupdf flags: bit 4 (16) = bold
    block = TextBlock(text="Bold", font="Arial-Bold", size=12.0, flags=16, bbox=(0,0,100,20), page_num=0)
    assert block.is_bold is True

def test_chapter_boundary_dataclass():
    from lib.corpus.tools.pdf_utils import ChapterBoundary
    ch = ChapterBoundary(index=1, title="Introduction", start_page=0, end_page=15)
    assert ch.page_count == 15
    assert ch.page_range == "1-15"

def test_cross_ref_dataclass():
    from lib.corpus.tools.pdf_utils import CrossRef
    ref = CrossRef(
        original_text='Chapter 5, "Scopes of Macro Variables," on page 57',
        ref_type="chapter_reference",
        display_text="Scopes of Macro Variables",
        page_number=57,
    )
    assert ref.page_number == 57

def test_toc_entry_dataclass():
    from lib.corpus.tools.pdf_utils import TocEntry
    entry = TocEntry(level=1, title="Chapter 1", page=0)
    assert entry.level == 1

def test_font_info_dataclass():
    from lib.corpus.tools.pdf_utils import FontInfo
    info = FontInfo(name="Arial", size=12.0, flags=0, count=5)
    assert info.name == "Arial"
    assert info.count == 5


def test_extract_text_blocks_returns_list():
    """Integration test — requires a real PDF. Skip if not available."""
    from lib.corpus.tools.pdf_utils import open_pdf, extract_text_blocks
    # Use any available PDF for integration testing
    test_pdf = Path(__file__).parent.parent.parent.parent / "tests" / "fixtures" / "sample.pdf"
    if not test_pdf.exists():
        pytest.skip("No test PDF available")
    doc = open_pdf(test_pdf)
    blocks = extract_text_blocks(doc[0])
    assert isinstance(blocks, list)
    if blocks:
        assert hasattr(blocks[0], "text")
        assert hasattr(blocks[0], "font")
    doc.close()

def test_analyze_fonts_returns_font_map():
    from lib.corpus.tools.pdf_utils import FontInfo
    # Unit test with mock data — just test the aggregation logic
    from lib.corpus.tools.pdf_utils import _aggregate_font_info, TextBlock
    blocks = [
        TextBlock("Hello", "Arial", 12.0, 0, (0,0,100,20), 0),
        TextBlock("World", "Arial", 12.0, 0, (0,20,100,40), 0),
        TextBlock("Code", "Courier", 10.0, 8, (0,40,100,60), 0),
    ]
    result = _aggregate_font_info(blocks)
    assert "Arial" in result or any("Arial" in k for k in result)

def test_strip_headers_footers():
    from lib.corpus.tools.pdf_utils import TextBlock, strip_headers_footers
    blocks = [
        TextBlock("Chapter 3 / Macro Variables", "Arial", 8.0, 0, (0, 10, 500, 20), 0),  # header at y=10
        TextBlock("Body text here", "Times", 12.0, 0, (0, 100, 500, 120), 0),  # body
        TextBlock("42", "Arial", 8.0, 0, (250, 780, 270, 790), 0),  # footer page number
    ]
    result = strip_headers_footers(
        blocks,
        header_pattern=r"Chapter \d+",
        header_zone_top=50,
        footer_zone_bottom=40,
        page_height=800,
    )
    assert len(result) == 1
    assert result[0].text == "Body text here"

def test_detect_chapters_from_toc_entries():
    from lib.corpus.tools.pdf_utils import detect_chapters_from_toc_entries, TocEntry
    entries = [
        TocEntry(level=1, title="Introduction", page=0),
        TocEntry(level=1, title="Getting Started", page=15),
        TocEntry(level=1, title="Advanced Topics", page=42),
    ]
    chapters = detect_chapters_from_toc_entries(entries, total_pages=60)
    assert len(chapters) == 3
    assert chapters[0].title == "Introduction"
    assert chapters[0].start_page == 0
    assert chapters[0].end_page == 15
    assert chapters[1].start_page == 15
    assert chapters[1].end_page == 42
    assert chapters[2].end_page == 60

def test_detect_chapters_from_toc_entries_filters_level():
    from lib.corpus.tools.pdf_utils import detect_chapters_from_toc_entries, TocEntry
    entries = [
        TocEntry(level=1, title="Part 1", page=0),
        TocEntry(level=2, title="Chapter 1.1", page=0),
        TocEntry(level=2, title="Chapter 1.2", page=10),
        TocEntry(level=1, title="Part 2", page=20),
    ]
    chapters = detect_chapters_from_toc_entries(entries, total_pages=40, level=1)
    assert len(chapters) == 2
    assert chapters[0].title == "Part 1"
    assert chapters[1].title == "Part 2"


def test_emit_heading():
    from lib.corpus.tools.pdf_utils import emit_heading
    assert emit_heading("Macro Variables", 1) == "# Macro Variables"
    assert emit_heading("Using Macros", 3) == "### Using Macros"

def test_emit_code_block():
    from lib.corpus.tools.pdf_utils import emit_code_block
    result = emit_code_block("%let x=1;", "sas")
    assert result == "```sas\n%let x=1;\n```"

def test_emit_code_block_no_language():
    from lib.corpus.tools.pdf_utils import emit_code_block
    result = emit_code_block("some output")
    assert result == "```\nsome output\n```"

def test_emit_table():
    from lib.corpus.tools.pdf_utils import emit_table
    result = emit_table(
        headers=["Name", "Type"],
        rows=[["SYSDATE", "Read-only"], ["SYSERR", "Read and Write"]],
    )
    assert "| Name | Type |" in result
    assert "| SYSDATE | Read-only |" in result
    assert "| --- | --- |" in result

def test_emit_callout():
    from lib.corpus.tools.pdf_utils import emit_callout
    result = emit_callout("Only printable characters should be used.", "note")
    assert result == "> **Note:** Only printable characters should be used."

def test_emit_frontmatter():
    from lib.corpus.tools.pdf_utils import emit_frontmatter
    result = emit_frontmatter({"title": "Test", "tags": ["a", "b"]})
    assert result.startswith("---\n")
    assert result.endswith("---\n")
    assert "title: Test" in result

def test_make_wikilink():
    from lib.corpus.tools.pdf_utils import make_wikilink
    assert make_wikilink("16_Scopes", "Scopes of Macro Variables") == "[[16_Scopes|Scopes of Macro Variables]]"

def test_find_cross_references():
    from lib.corpus.tools.pdf_utils import find_cross_references
    text = 'See Chapter 5, \u201cScopes of Macro Variables,\u201d on page 57.'
    patterns = [
        (r'Chapter (\d+), ["\u201c](.+?)["\u201d],? on page (\d+)', "chapter_reference"),
    ]
    refs = find_cross_references(text, patterns)
    assert len(refs) == 1
    assert refs[0].display_text == "Scopes of Macro Variables"
    assert refs[0].page_number == 57

def test_resolve_cross_ref():
    from lib.corpus.tools.pdf_utils import resolve_cross_ref, CrossRef, ChapterBoundary
    chapters = [
        ChapterBoundary(1, "Intro", 0, 20),
        ChapterBoundary(2, "Scopes", 20, 60),
        ChapterBoundary(3, "Advanced", 60, 80),
    ]
    ref = CrossRef("see page 57", "section_reference", "Scopes", page_number=57)
    result = resolve_cross_ref(ref, chapters, filename_pattern="{index:02d}_{title}")
    assert result is not None
    assert "Scopes" in result

def test_sanitize_filename():
    from lib.corpus.tools.pdf_utils import sanitize_filename
    assert sanitize_filename("Chapter 3: Macro Variables!") == "Chapter_3_Macro_Variables"
    assert len(sanitize_filename("A" * 100, max_length=50)) <= 50
