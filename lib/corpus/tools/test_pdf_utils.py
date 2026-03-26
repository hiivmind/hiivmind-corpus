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
