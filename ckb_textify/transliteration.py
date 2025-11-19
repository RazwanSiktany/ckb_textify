# ckb_textify/transliteration.py
import re
from .latin import normalize_latin

try:
    from anyascii import anyascii
except ImportError:
    anyascii = None

# --- Regex for Script Detection ---
CYRILLIC_RE = re.compile(r'[\u0400-\u04FF]+')
CJK_RE = re.compile(r'[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]+')
KURMANJI_WORD_RE = re.compile(r'\b\w*[êîûçşÊÎÛÇŞ]\w*\b')
GREEK_RE = re.compile(r'[\u0370-\u03FF]+')
EXTENDED_LATIN_RE = re.compile(r'\b\w*[\u00C0-\u024F\u1E00-\u1EFF]\w*\b')

# *** NEW: South Asian Scripts (Devanagari, Bengali, Tamil, etc.) ***
SOUTH_ASIAN_RE = re.compile(r'[\u0900-\u0DFF]+')

# --- 1. Kurdish Cyrillic to Sorani Map ---
CYRILLIC_MAP = {
    'а': 'ا', 'б': 'ب', 'в': 'ڤ', 'г': 'گ', 'д': 'د',
    'е': 'ێ', 'ә': 'ە', 'ж': 'ژ', 'з': 'ز', 'и': 'ی',
    'й': 'ی', 'к': 'ک', 'л': 'ل', 'м': 'م', 'н': 'ن',
    'о': 'ۆ', 'п': 'پ', 'р': 'ڕ', 'с': 'س', 'т': 'ت',
    'у': 'و', 'ф': 'ف', 'х': 'خ', 'һ': 'ھ', 'ч': 'چ',
    'ш': 'ش', 'щ': 'ش', 'ь': '', 'э': 'ێ', 'ю': 'یو',
    'я': 'یا',
}

# --- 2. Kurmanji to Sorani Map ---
KURMANJI_MAP = {
    'ê': 'ێ', 'î': 'ی', 'û': 'وو',
    'ç': 'چ', 'ş': 'ش',
    'a': 'ا', 'b': 'ب', 'c': 'ج', 'd': 'د', 'e': 'ە',
    'f': 'ف', 'g': 'گ', 'h': 'ھ', 'i': '',
    'j': 'ژ', 'k': 'ک', 'l': 'ل', 'm': 'م', 'n': 'ن',
    'o': 'ۆ', 'p': 'پ', 'q': 'ق', 'r': 'ر', 's': 'س',
    't': 'ت', 'u': 'و', 'v': 'ڤ', 'w': 'و', 'x': 'خ',
    'y': 'ی', 'z': 'ز'
}

SORANI_VOWELS = {'ا', 'ێ', 'ۆ', 'ە', 'ی', 'وو'}


def _ensure_initial_hamza(text: str) -> str:
    if not text: return text
    first_char = text[0]
    if first_char in SORANI_VOWELS or text.startswith("وو"):
        return "ئ" + text
    return text


def _transliterate_cyrillic(text):
    result = []
    for char in text:
        lower_char = char.lower()
        result.append(CYRILLIC_MAP.get(lower_char, char))
    return _ensure_initial_hamza("".join(result))


def _transliterate_kurmanji(text):
    result = []
    for char in text:
        lower_char = char.lower()
        result.append(KURMANJI_MAP.get(lower_char, char))
    return _ensure_initial_hamza("".join(result))


def normalize_foreign_scripts(text: str) -> str:
    """
    Detects non-Arabic/non-English scripts and transliterates them.
    """

    # 1. Handle Cyrillic
    if CYRILLIC_RE.search(text):
        text = CYRILLIC_RE.sub(lambda m: _transliterate_cyrillic(m.group(0)), text)

    # 2. Handle Kurmanji
    if KURMANJI_WORD_RE.search(text):
        text = KURMANJI_WORD_RE.sub(lambda m: _transliterate_kurmanji(m.group(0)), text)

    # 3. Handle "The Rest" via Latin Bridge
    if anyascii:

        def _bridge_to_sorani(match):
            # Step A: Foreign -> Latin
            latin_text = anyascii(match.group(0))
            # Step B: Latin -> Sorani
            return normalize_latin(latin_text)

        # CJK (Chinese/Japanese/Korean)
        if CJK_RE.search(text):
            text = CJK_RE.sub(_bridge_to_sorani, text)

        # Extended Latin (French/German)
        if EXTENDED_LATIN_RE.search(text):
            text = EXTENDED_LATIN_RE.sub(_bridge_to_sorani, text)

        # Greek
        if GREEK_RE.search(text):
            text = GREEK_RE.sub(_bridge_to_sorani, text)

        # *** NEW: South Asian (Devanagari, etc.) ***
        if SOUTH_ASIAN_RE.search(text):
            text = SOUTH_ASIAN_RE.sub(_bridge_to_sorani, text)

    return text