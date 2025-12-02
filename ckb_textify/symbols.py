# ckb_textify/symbols.py
import re

# --- 1. Symbol Mappings ---
SYMBOLS_MAP = {
    "&": " و ",
    "_": " ",
    "~": " نزیکەی ",
    "=": " یەکسانە بە ",
    "≈": " نزیکەی ",
    "^": " توان ",
    "/": "سلاش ",
    "\\": "سلاش ",
    "$": "دۆلار ",
}

# Regex for '@' (at sign)
AT_RE = re.compile(r"@")

# Regex for '#' (Hashtag/Number)
HASHTAG_RE = re.compile(r"#([\u0600-\u06FF\w]+)")
NUMBER_SIGN_RE = re.compile(r"#(\d+)")

# Regex for '...' (Ellipsis)
ELLIPSIS_RE = re.compile(r"\.{2,}")


def normalize_common_symbols(text: str) -> str:
    # Simple Replacements
    for symbol, expansion in SYMBOLS_MAP.items():
        text = text.replace(symbol, expansion)

    # @ (At Sign)
    text = AT_RE.sub(" ئەت ", text)

    # # (Hashtag/Number)
    text = NUMBER_SIGN_RE.sub(r" ژمارە \1", text)
    text = HASHTAG_RE.sub(r" ھاشتاگ \1", text)

    # ... (Ellipsis)
    text = ELLIPSIS_RE.sub(" . ", text)

    return text