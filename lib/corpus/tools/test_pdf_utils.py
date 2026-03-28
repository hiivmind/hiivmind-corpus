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


# ---------------------------------------------------------------------------
# dehyphenate tests
# ---------------------------------------------------------------------------

def test_dehyphenate_joins_split_words():
    from lib.corpus.tools.pdf_utils import dehyphenate
    assert dehyphenate("inde- pendent") == "independent"
    assert dehyphenate("multi- variate analysis") == "multivariate analysis"

def test_dehyphenate_preserves_intentional_hyphens():
    from lib.corpus.tools.pdf_utils import dehyphenate
    assert dehyphenate("end- Start") == "end- Start"
    assert dehyphenate("least-squares") == "least-squares"

def test_dehyphenate_preserves_short_fragments():
    from lib.corpus.tools.pdf_utils import dehyphenate
    assert dehyphenate("x- axis") == "x- axis"

def test_dehyphenate_empty_and_no_hyphens():
    from lib.corpus.tools.pdf_utils import dehyphenate
    assert dehyphenate("") == ""
    assert dehyphenate("no hyphens here") == "no hyphens here"


# ---------------------------------------------------------------------------
# Table post-processing tests
# ---------------------------------------------------------------------------

def test_split_subtables_on_empty_rows():
    from lib.corpus.tools.pdf_utils import split_subtables
    extract = [
        ["Source", "DF", "SS"],
        ["Model", "3", "91.7"],
        [None, None, None],
        ["R-Square", "Coeff Var"],
        ["0.94", "9.8"],
    ]
    result = split_subtables(extract)
    assert len(result) == 2
    assert result[0] == [["Source", "DF", "SS"], ["Model", "3", "91.7"]]
    assert result[1] == [["R-Square", "Coeff Var"], ["0.94", "9.8"]]

def test_split_subtables_no_separators():
    from lib.corpus.tools.pdf_utils import split_subtables
    extract = [["A", "B"], ["1", "2"]]
    result = split_subtables(extract)
    assert len(result) == 1

def test_split_subtables_empty_string_rows():
    from lib.corpus.tools.pdf_utils import split_subtables
    extract = [["A"], ["", ""], ["B"]]
    result = split_subtables(extract)
    assert len(result) == 2

def test_expand_newline_cells():
    from lib.corpus.tools.pdf_utils import expand_newline_cells
    rows = [
        ["Source", "DF\nSquares\nMean Square", "F Value"],
        ["Model", "3\n91.7\n30.6", "15.29"],
    ]
    result = expand_newline_cells(rows)
    assert result[0] == ["Source", "DF", "Squares", "Mean Square", "F Value"]
    assert result[1] == ["Model", "3", "91.7", "30.6", "15.29"]

def test_expand_newline_cells_normalizes_columns():
    from lib.corpus.tools.pdf_utils import expand_newline_cells
    rows = [["A\nB", "C"], ["D", "E"]]
    result = expand_newline_cells(rows)
    assert len(result[0]) == len(result[1]) == 3

def test_expand_newline_cells_empty():
    from lib.corpus.tools.pdf_utils import expand_newline_cells
    assert expand_newline_cells([]) == []

def test_merge_continuation_rows_backward():
    from lib.corpus.tools.pdf_utils import merge_continuation_rows
    rows = [
        ["MANOVA", "Requests multivariate mode of eliminating observations with missing"],
        ["", "values"],
    ]
    result = merge_continuation_rows(rows)
    assert len(result) == 1
    assert result[0][0] == "MANOVA"
    assert "missing values" in result[0][1]

def test_merge_continuation_rows_forward_sparse_header():
    from lib.corpus.tools.pdf_utils import merge_continuation_rows
    rows = [
        ["", "", "Sum of", ""],
        ["Source", "DF", "", "F Value"],
        ["Model", "3", "91.7", "15.29"],
    ]
    result = merge_continuation_rows(rows)
    assert len(result) == 2
    assert result[0][2] == "Sum of"

def test_merge_continuation_rows_preserves_normal_rows():
    from lib.corpus.tools.pdf_utils import merge_continuation_rows
    rows = [["A", "B"], ["C", "D"]]
    result = merge_continuation_rows(rows)
    assert len(result) == 2

def test_strip_empty_columns():
    from lib.corpus.tools.pdf_utils import strip_empty_columns
    headers = ["Source", "", "DF", "", "SS"]
    rows = [["Model", "", "3", "", "91.7"], ["Error", "", "10", "", "6.0"]]
    h, r = strip_empty_columns(headers, rows)
    assert h == ["Source", "DF", "SS"]
    assert r == [["Model", "3", "91.7"], ["Error", "10", "6.0"]]

def test_strip_empty_columns_keeps_nonempty():
    from lib.corpus.tools.pdf_utils import strip_empty_columns
    headers = ["A", "B"]
    rows = [["1", "2"]]
    h, r = strip_empty_columns(headers, rows)
    assert h == ["A", "B"]


# ---------------------------------------------------------------------------
# emit_layout_table tests
# ---------------------------------------------------------------------------

def test_emit_layout_table_simple():
    from lib.corpus.tools.pdf_utils import emit_layout_table
    table_data = {
        "extract": [
            ["Source", "DF", "SS"],
            ["Model", "3", "91.7"],
            ["Error", "10", "6.0"],
        ],
        "col_count": 3,
    }
    result = emit_layout_table(table_data)
    assert "| Source | DF | SS |" in result
    assert "| Model | 3 | 91.7 |" in result

def test_emit_layout_table_splits_subtables():
    from lib.corpus.tools.pdf_utils import emit_layout_table
    table_data = {
        "extract": [
            ["A", "B"],
            ["1", "2"],
            [None, None],
            ["C", "D"],
            ["3", "4"],
        ],
        "col_count": 2,
    }
    result = emit_layout_table(table_data)
    assert result.count("| --- |") == 2

def test_emit_layout_table_empty_returns_empty():
    from lib.corpus.tools.pdf_utils import emit_layout_table
    assert emit_layout_table({"extract": []}) == ""
    assert emit_layout_table({"extract": [[None, None]]}) == ""

def test_emit_layout_table_merges_continuations():
    from lib.corpus.tools.pdf_utils import emit_layout_table
    table_data = {
        "extract": [
            ["Option", "Description"],
            ["MANOVA", "Requests multivariate mode of eliminating observations with missing"],
            [None, "values"],
        ],
        "col_count": 2,
    }
    result = emit_layout_table(table_data)
    assert "missing values" in result
    lines = [l for l in result.strip().split("\n") if l.startswith("|")]
    assert len(lines) == 3


# ---------------------------------------------------------------------------
# tex_math_map tests
# ---------------------------------------------------------------------------

def test_decode_math_text_oml_greek():
    from lib.corpus.tools.tex_math_map import decode_math_text
    assert decode_math_text("\u02DB", "MT2MIT") == "α"
    assert decode_math_text("\u02C7", "MT2MIT") == "β"
    assert decode_math_text("\uFFFD", "MT2MIT") == "π"

def test_decode_math_text_oms_operators():
    from lib.corpus.tools.tex_math_map import decode_math_text
    assert decode_math_text("C", "MT2SYT") == "+"
    assert decode_math_text("D", "MT2SYT") == "="
    assert decode_math_text("j", "MT2SYT") == "|"

def test_decode_math_text_preserves_ascii():
    from lib.corpus.tools.tex_math_map import decode_math_text
    assert decode_math_text("x", "MT2MIT") == "x"
    assert decode_math_text("Y", "MT2MIT") == "Y"

def test_decode_math_text_unknown_font():
    from lib.corpus.tools.tex_math_map import decode_math_text
    assert decode_math_text("hello", "NimbusRomNo9L-Regu") == "hello"

def test_is_math_font():
    from lib.corpus.tools.tex_math_map import is_math_font
    assert is_math_font("MT2MIT") is True
    assert is_math_font("MT2SYT") is True
    assert is_math_font("MT2BMIT") is True
    assert is_math_font("NimbusRomNo9L-Regu") is False
    assert is_math_font("AlbanyAMT,Bold") is False

def test_decode_math_text_bold_beta():
    from lib.corpus.tools.tex_math_map import decode_math_text
    assert decode_math_text("\u02C7", "MT2BMIT") == "β"

def test_decode_math_text_prime():
    from lib.corpus.tools.tex_math_map import decode_math_text
    assert decode_math_text("0", "MT2SYS") == "′"
