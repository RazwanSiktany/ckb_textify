# ckb_textify/units.py
import re
from .number_to_text import number_to_kurdish_text
from .decimal_handler import decimal_to_kurdish_text
from .math_operations import convert_number_to_text_handler

# --- 1. UNITS MAP ---
UNITS_MAP = {
    # کێش (Weight)
    "kg": "کیلۆگرام",
    "کگم": "کیلۆگرام",
    "کغم": "کیلۆگرام",
    "g": "گرام",
    "گم": "گرام",
    "mg": "میلیگرام",

    # دووری (Distance)
    "km": "کیلۆمەتر",
    "کم": "کیلۆمەتر",
    "m": "مەتر",  # Ambiguous
    "cm": "سانتیمەتر",
    "سم": "سانتیمەتر",  # Ambiguous
    "mm": "میلیمەتر",
    "ملم": "میلیمەتر",  # Ambiguous
    "ملیمەتر": "میلیمەتر",

    # قەبارە (Volume)
    "l": "لیتر",
    "ml": "میلیلیتر",

    # داتا (Data)
    "gb": "گێگابایت",
    "mb": "مێگابایت",
    "kb": "کیلۆبایت",
    "tb": "تێرابایت",

    # --- NEW: کات (Time) ---
    "h": "کاتژمێر",
    "hr": "کاتژمێر",
    "min": "خولەک",
    "sec": "چرکە",
    "s": "چرکە",  # Ambiguous
}

# --- 2. PROTECTED BASE UNITS ---
UNITS_BASE = [
    "کیلۆگرام", "گرام", "میلیگرام",
    "کیلۆمەتر", "مەتر", "سانتیمەتر", "میلیمەتر",
    "لیتر", "میلیلیتر",
    "جێگابایت", "مێگابایت", "کیلۆبایت", "بایت", "تێرابایت",
    "کاتژمێر", "خولەک", "چرکە",
]

# --- 3. AMBIGUOUS UNITS ---
UNITS_AMBIGUOUS = {
    "m", "ملم", "سم", "s"
}

# --- 4. UNAMBIGUOUS MAP ---
UNITS_UNAMBIGUOUS_MAP = {
    abbr: full
    for abbr, full in UNITS_MAP.items()
    if abbr not in UNITS_AMBIGUOUS
}

# Regex for standalone units
standalone_keys = sorted(UNITS_UNAMBIGUOUS_MAP.keys(), key=len, reverse=True)
STANDALONE_UNIT_RE = re.compile(
    r"\b(" + r"|".join(map(re.escape, standalone_keys)) + r")\b",
    re.IGNORECASE
)

# --- SUFFIXES LIST ---
# Base suffixes including pronouns and compound pronouns
BASE_SUFFIXES = [
    "یە", "ە",
    # Main Pronouns
    "م", "مان", "ت", "تان", "ی", "یان",
    # Compound pronouns for م
    "مم", "ممان", "مت", "متان", "می", "میان",
    # Compound pronouns for مان
    "مانم", "مانمان", "مانت", "مانتان", "مانی", "مانیان",
    # Compound pronouns for ت
    "تم", "تمان", "تت", "تتان", "تی", "تیان",
    # Compound pronouns for تان
    "تانم", "تانمان", "تانت", "تانتان", "تانی", "تانیان",
    # Compound pronouns for ی
    "یم", "یمان", "یت", "یتان", "یی", "ییان",
    # Compound pronouns for یان
    "یانم", "یانمان", "یانت", "یانتان", "یانی", "یانیان",
]

DEFINITE_ARTICLES = ["ەکە", "ەکان"]

# Generate comprehensive list: Base + Articles + (Article + Base)
# This ensures we cover things like "ەکەمان", "ەکانم", "ەکانمان", etc.
SUFFIXES = BASE_SUFFIXES + DEFINITE_ARTICLES + [
    f"{art}{sfx}" for art in DEFINITE_ARTICLES for sfx in BASE_SUFFIXES
]

# --- 5. NUMBER+UNIT REGEX ---
all_unit_keys = sorted(
    list(UNITS_MAP.keys()) + UNITS_BASE,
    key=len,
    reverse=True
)

# *** CRITICAL FIX: Sort suffixes by length (Longest First) ***
# This ensures 'مان' is matched before 'م', preventing partial matches.
sorted_suffixes = sorted(SUFFIXES, key=len, reverse=True)

NUMBER_UNIT_RE = re.compile(
    r"(\d+(\.\d+)?)(\s*)(" + r"|".join(map(re.escape, all_unit_keys)) + r")(" +
    r"|".join(map(re.escape, sorted_suffixes)) + r")?\b",
    re.IGNORECASE
)


# --- 6. _replace_unit_match ---
def _replace_unit_match(match):
    number_str = match.group(1)
    unit_key = match.group(4).lower()
    suffix = match.group(5) or ""
    unit_text = UNITS_MAP.get(unit_key, unit_key)

    try:
        number = float(number_str)
    except ValueError:
        return match.group(0)

    if number % 1 == 0.5:
        integer_part = int(number)
        int_text = number_to_kurdish_text(integer_part)

        if suffix in ["یە", "ە"]:
            niw_text = "نیوە"
        else:
            niw_text = "نیو"

        full_suffix = f"{niw_text}{suffix}" if suffix not in ["", "ە", "یە"] else niw_text
        return f"{int_text} {unit_text} و {full_suffix}"
    else:
        number_text = convert_number_to_text_handler(number_str)
        return f"{number_text} {unit_text}{suffix}"


def normalize_units(text: str) -> str:
    return NUMBER_UNIT_RE.sub(_replace_unit_match, text)


# --- 7. normalize_standalone_units ---
def normalize_standalone_units(text: str) -> str:
    def _replace_standalone(match):
        abbr = match.group(1).lower()
        return UNITS_UNAMBIGUOUS_MAP[abbr]

    return STANDALONE_UNIT_RE.sub(_replace_standalone, text)


# --- 8. "PER" RULE LOGIC ---
KURDISH_VOWELS = ['وو', 'و', 'ی', 'ێ', 'ا', 'ە', 'ۆ']

def _handle_per_suffix(unit_text: str) -> str:
    unit_text = unit_text.strip()
    for vowel in KURDISH_VOWELS:
        if unit_text.endswith(vowel):
            return f"بۆ ھەر {unit_text}یێک"
    return f"بۆ ھەر {unit_text}ێک"

PER_RULE_SPACED_RE = re.compile(
    r"([\u0600-\u06FF\s]+)\s+/\s+([\u0600-\u06FF\s]+)"
)
PER_RULE_NO_SPACE_RE = re.compile(
    r"([\u0600-\u06FF]+)/([\u0600-\u06FF]+)"
)

def normalize_per_rule(text: str) -> str:
    text = PER_RULE_SPACED_RE.sub(
        lambda m: f"{m.group(1).strip()} {_handle_per_suffix(m.group(2).strip())}",
        text
    )
    text = PER_RULE_NO_SPACE_RE.sub(
        lambda m: f"{m.group(1).strip()} {_handle_per_suffix(m.group(2).strip())}",
        text
    )
    return text