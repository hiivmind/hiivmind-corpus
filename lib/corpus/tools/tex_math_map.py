"""TeX math font encoding tables for MathTime2 and Computer Modern fonts.

Maps garbled pymupdf-extracted characters back to correct Unicode.
These fonts use TeX-internal encodings (OML, OMS, OT1) which pymupdf
cannot decode because the PDFs lack /ToUnicode tables.

The mappings are built from:
1. Standard TeX OML/OMS/OT1 encoding charts (CTAN documentation)
2. Verified against formula context in SAS/STAT User's Guide PDFs
"""

# ---------------------------------------------------------------------------
# MT2MIT / MT2MIF — MathTime2 Math Italic (OML encoding)
# Maps italic math letters and Greek lowercase
# Most ASCII letters (a-z, A-Z) extract correctly as math italic variables.
# Only the non-ASCII-mapped slots need fixing.
# ---------------------------------------------------------------------------
OML_MAP = {
    "\u02DB": "α",   # ˛ (ogonek) -> alpha
    "\u02C7": "β",   # ˇ (caron) -> beta (in italic context)
    "\u0131": "ι",   # ı (dotless i) -> iota
    "\u2020": "δ",   # † (dagger) -> delta
    "\u0152": "ω",   # Œ (OE ligature) -> omega
    "\u02C6": "θ",   # ˆ (circumflex) -> theta
    "\uFFFD": "π",   # replacement char -> pi (most common in these docs)
    # Standard ASCII chars in MT2MIT are math italic variables — no change needed:
    # a-z, A-Z, 0-9, . , ; : < > = etc. extract correctly
}

# ---------------------------------------------------------------------------
# MT2BMIT / MT2BMIS — MathTime2 Bold Math Italic
# Same OML encoding but bold — used for vector/matrix notation (β, etc.)
# ---------------------------------------------------------------------------
OML_BOLD_MAP = {
    "\u02C7": "β",   # ˇ -> bold beta (vector of coefficients)
    "\u02DB": "α",   # ˛ -> bold alpha
    "\u2020": "δ",   # † -> bold delta
    "\u0131": "ι",   # ı -> bold iota
    "\uFFFD": "π",   # replacement char -> bold pi
}

# ---------------------------------------------------------------------------
# MT2SYT / MT2SYF — MathTime2 Symbol (OMS encoding)
# Mathematical operators and relations
# ---------------------------------------------------------------------------
OMS_MAP = {
    "C": "+",         # slot 67 -> plus
    "D": "=",         # slot 68 -> equals
    "j": "|",         # slot 106 -> vertical bar (conditional)
    "N": "≥",         # slot 78 -> greater-or-equal
    "O": "≤",         # slot 79 -> less-or-equal
    "W": "∨",         # slot 87 -> logical or
    "I": "∩",         # slot 73 -> intersection
    "!": "∀",         # slot 33 -> for all
    "3": "∪",         # slot 51 -> union
    "f": "{",         # slot 102 -> left brace
    "g": "}",         # slot 103 -> right brace
    "p": "∈",         # slot 112 -> element of
    "\u02D9": "·",    # ˙ -> centered dot (multiplication)
    "\u02DD": "≠",    # ˝ -> not equal
    "\uFFFD": "−",    # replacement char -> minus sign
}

# ---------------------------------------------------------------------------
# MT2SYS — MathTime2 Symbol Small (subscript/superscript symbols)
# Same OMS encoding at smaller size
# ---------------------------------------------------------------------------
OMS_SMALL_MAP = {
    "D": "=",
    "0": "′",         # prime/transpose mark (common in β'x)
    "p": "∈",
    "\uFFFD": "−",
}

# ---------------------------------------------------------------------------
# MT2EXA — MathTime2 Extension (large delimiters, radicals)
# These are structural elements (big parens, brackets, etc.)
# Most extract as garbled — map common ones
# ---------------------------------------------------------------------------
EXA_MAP = {
    "\uFFFD": "",     # large delimiter fragments — drop
    "\u02C6": "",     # hat/circumflex fragment — drop
    "P": "(",         # large left paren
    "p": ")",         # large right paren
    "b": "]",         # large right bracket
    "r": "√",         # radical sign
    "X": "∑",         # summation
    # Digits in EXA are typically large versions — keep as-is
}

# ---------------------------------------------------------------------------
# MT2MIS — MathTime2 Math Italic Small (subscripts)
# Same letter mappings as OML but at smaller size
# Most chars are subscript letters/digits — extract correctly
# ---------------------------------------------------------------------------
OML_SMALL_MAP = {
    # Subscript letters and digits mostly extract fine
    # Only non-ASCII needs mapping
    "\uFFFD": "π",
}

# ---------------------------------------------------------------------------
# SFRB / SFRM / SFTI — Computer Modern (SliTeX) Roman/Bold/Italic
# These use OT1 encoding which is mostly ASCII-compatible.
# Letters and digits extract correctly. No mapping needed.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Font family -> mapping table
# ---------------------------------------------------------------------------
FONT_MAPS = {
    "MT2MIT":  OML_MAP,
    "MT2MIF":  OML_MAP,       # italic at different size
    "MT2BMIT": OML_BOLD_MAP,
    "MT2BMIS": OML_BOLD_MAP,  # bold italic small
    "MT2SYT":  OMS_MAP,
    "MT2SYF":  OMS_MAP,       # symbol at different size
    "MT2SYS":  OMS_SMALL_MAP,
    "MT2EXA":  EXA_MAP,
    "MT2MIS":  OML_SMALL_MAP,
}


def decode_math_text(text: str, font: str) -> str:
    """Decode garbled TeX math font text to correct Unicode.

    Args:
        text: The extracted text from pymupdf.
        font: The font name (e.g., "MT2MIT").

    Returns:
        Corrected text with proper Unicode math symbols.
    """
    # Find the matching font map
    font_map = None
    for prefix, mapping in FONT_MAPS.items():
        if font.startswith(prefix):
            font_map = mapping
            break

    if font_map is None:
        return text

    result = []
    for ch in text:
        if ch in font_map:
            result.append(font_map[ch])
        else:
            result.append(ch)
    return "".join(result)


def is_math_font(font: str) -> bool:
    """Check if a font is a TeX math font that needs decoding."""
    return any(font.startswith(prefix) for prefix in FONT_MAPS)
