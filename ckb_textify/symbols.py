# ckb_textify/symbols.py
import re

# --- 1. Symbol Mappings ---
SYMBOLS_MAP = {
    "&": " و ",  # Ampersand -> and
    "_": " ",  # Underscore -> space
    "~": " نزیکەی ",  # Tilde -> approximately
    "=": " یەکسانە بە ",  # <-- ADDED (Equals)
}

# Regex for '@' (at sign)
AT_RE = re.compile(r"@")

# Regex for '#' (Hashtag/Number)
# Rule 1: Matches a hashtag, e.g., #kurdistan
HASHTAG_RE = re.compile(r"#([\u0600-\u06FF\w]+)")
# Rule 2: Matches a number sign, e.g., #1, #2
NUMBER_SIGN_RE = re.compile(r"#(\d+)")

# Regex for '...' (Ellipsis)
ELLIPSIS_RE = re.compile(r"\.{2,}")


def normalize_common_symbols(text: str) -> str:
    """
    Expands common symbols like @, #, &, = and cleans up others.
    """

    # --- Simple Replacements ---
    for symbol, expansion in SYMBOLS_MAP.items():
        text = text.replace(symbol, expansion)

    # --- @ (At Sign) ---
    # Example: @razwan -> 'ئەت ڕەزوان'
    text = AT_RE.sub(" ئەت ", text)

    # --- # (Hashtag/Number) ---
    # Order matters: We must check for "#1" (number) before "#kurdistan" (hashtag)
    text = NUMBER_SIGN_RE.sub(r" ژمارە \1", text)
    text = HASHTAG_RE.sub(r" ھاشتاگ \1", text)

    # --- ... (Ellipsis) ---
    text = ELLIPSIS_RE.sub(" . ", text)

    return text