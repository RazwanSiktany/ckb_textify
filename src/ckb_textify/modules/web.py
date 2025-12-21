import re
import unicodedata
from ckb_textify.resources.transliteration_maps import GREEK_NAMES_MAP, LETTER_MAP

# --- 1. Common Web Terms (Whole Words) ---
# FIX: Removed surrounding spaces from map values. SpacingNormalizer will handle padding.
COMMON_TERMS_MAP = {
    # Common Websites
    "google": "گووگڵ",
    "facebook": "فەیسبووک",
    "twitter": "تویتەر",
    "youtube": "یوتوب",
    "instagram": "ئینستاگرام",


    # Common Words
    "info": "ئینفۆ",
    "support": "سەپۆرت",
    "contact": "کۆنتاکت",
    "admin": "ئەدمین",
    "user": "یوسەر",
    "login": "لۆگین",
    "signup": "ساین ئەپ",
    "mail": "مەیل",
    "ftp": "ئێف تی پی",  # Added

    # Domains (Bare keys for structural split)
    "com": "کۆم",
    "net": "نێت",
    "org": "ئۆڕگ",
    "edu": "ئیدیو",
    "gov": "گاڤ",
    "gmail": "جیمەیڵ",
    "yahoo": "یاھوو",
    "outlook": "ئاوتلووک",
    "hotmail": "ھۆتمەیڵ",
    "icloud": "ئایکلاود",
}

# --- 2. Symbol & Character Maps ---
# FIX: Removed surrounding spaces from symbol map values.
WEB_SYMBOL_MAP = {
    ".": "دۆت",
    "@": "ئەت",
    "/": "سلاش",
    ":": "دوو خاڵ",
    "-": "داش",
    "_": "ئەندەرسکۆڕ",
    "?": "نیشانەی پرسیار",
    "=": "یەکسانە",
    "&": "ئەند",
    "+": "کۆ",
    "#": "ھاشتاگ",
    "%": "لەسەدا",
}

DIGITS_MAP = {
    "0": "سفر", "1": "یەک", "2": "دوو", "3": "سێ", "4": "چوار",
    "5": "پێنج", "6": "شەش", "7": "حەوت", "8": "ھەشت", "9": "نۆ"
}

# --- 3. Regex Patterns ---
# Expanded to include ALL symbols in WEB_SYMBOL_MAP (:@/?=&%#)
STRUCTURE_SPLIT_RE = re.compile(r"([@.+\-/_:?=&%#])")


# --- 4. Logic ---
def _process_chunk(chunk: str) -> str:
    """
    Processes a single text chunk (e.g. "test" or "example").
    """
    chunk_lower = chunk.lower()

    # 1. Is it a known whole word? (e.g. "info", "mail")
    if chunk_lower in COMMON_TERMS_MAP:
        # Returns bare word form
        return COMMON_TERMS_MAP[chunk_lower]

    # 2. Else: Spell it out char-by-char
    spelled_out = []
    for char in chunk:
        # Check if the character is a symbol that should be spoken
        if char in WEB_SYMBOL_MAP:
            spelled_out.append(WEB_SYMBOL_MAP[char])
            continue

        # FIX: Normalize accented characters (e.g. 'ê' -> 'e', 'é' -> 'e')
        # This decomposes the char into base + accent, and we take the base.
        char_normalized = unicodedata.normalize('NFD', char)
        char_base = char_normalized[0].lower() if char_normalized else char.lower()

        # Check for Greek/Foreign names FIRST
        if char_base in GREEK_NAMES_MAP:
            spelled_out.append(GREEK_NAMES_MAP[char_base])
        elif char_base in LETTER_MAP:
            spelled_out.append(LETTER_MAP[char_base])
        elif char_base in DIGITS_MAP:
            spelled_out.append(DIGITS_MAP[char_base])
        else:
            # Fallback: keep original char if not found
            spelled_out.append(char)

    return " ".join(spelled_out)


def _spell_web_string(text: str) -> str:
    """
    Implements the two-level structural splitting recommended by the expert.
    """
    # Step 1: Global Split (Splits by @, ., -, /, _, +, :, ?, =, &, %, #)
    raw_tokens = STRUCTURE_SPLIT_RE.split(text)

    processed_segments = []

    for raw_token in raw_tokens:
        if not raw_token:
            continue

        # Check if token is a delimiter itself (e.g., ".", "@", "?", "=")
        if raw_token in WEB_SYMBOL_MAP:
            processed_segments.append(WEB_SYMBOL_MAP[raw_token])
            continue

        # If we are here, the token is a chunk (e.g., "test" or "mail" or "example")

        # We need to re-split chunks that still contain symbols (like 'mail+info' or mixed unicode)
        # Updated regex to handle unicode chunks AND catch all symbol delimiters in the second group
        sub_tokens = re.findall(r"([a-zA-Z0-9\u0080-\uFFFF]+)|([@.+\-/_:?=&%#])", raw_token)

        if sub_tokens:
            for letters, symbol in sub_tokens:
                sub_token = letters or symbol

                # If it's a known symbol, use the bare map value
                if sub_token in WEB_SYMBOL_MAP:
                    processed_segments.append(WEB_SYMBOL_MAP[sub_token])
                else:
                    # It's a clean letter/word chunk, process it
                    processed_segments.append(_process_chunk(sub_token))
        else:
            # Treat the whole chunk as a single entity if findall matches nothing (rare)
            processed_segments.append(_process_chunk(raw_token))

    # Final Join: Join all segments with a space. The SpacingNormalizer will handle the rest.
    return " ".join(processed_segments)


class WebNormalizer:
    def __init__(self, config):
        self.config = config

    @property
    def name(self) -> str:
        return "WebNormalizer"

    @property
    def priority(self) -> int:
        return 100

    def process(self, tokens):
        if not self.config.enable_web:
            return tokens

        for token in tokens:
            if token.type in ("URL", "EMAIL") or (hasattr(token.type, 'name') and token.type.name in ("URL", "EMAIL")):
                # When converting, the token's text changes, making token.is_converted = True
                token.text = _spell_web_string(token.text)
                # We change the type to WORD so later modules don't touch it
                token.type = "WORD" if isinstance(token.type, str) else token.type
        return tokens

    # Helper for TechnicalNormalizer
    def _spell_out(self, text: str) -> str:
        return _spell_web_string(text)