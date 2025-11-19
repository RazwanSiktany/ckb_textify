# ckb_textify/units.py
import re
from .number_to_text import number_to_kurdish_text
from .decimal_handler import decimal_to_kurdish_text
from .math_operations import convert_number_to_text_handler

# --- 1. UNITS MAP ---
UNITS_MAP = {
    # کێش (Weight)
    "kg": "کیلۆگرام",
    "کیلۆ": "کیلۆگرام",
    "کیلۆم": "کیلۆگرام",
    "کگم": "کیلۆگرام",
    "کغم": "کیلۆگرام",
    "g": "گرام",
    "گم": "گرام",
    "mg": "میلیگرام",

    # دووری (Distance)
    "km": "کیلۆمەتر",
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
    "gb": "جێگابایت",
    "mb": "مێگابایت",
    "kb": "کیلۆبایت",
    "tb": "تێرابایت",

    # --- NEW: کات (Time) ---
    "h": "کاتژمێر",
    "hr": "کاتژمێر",
    "min": "خولەک",
    "sec": "چرکە",
    "s": "چرکە",  # Ambiguous, but usually seconds in math context
}

# --- 2. PROTECTED BASE UNITS ---
UNITS_BASE = [
    "کیلۆگرام", "گرام", "میلیگرام",
    "کیلۆمەتر", "مەتر", "سانتیمەتر", "میلیمەتر",
    "لیتر", "میلیلیتر",
    "جێگابایت", "مێگابایت", "کیلۆبایت", "بایت", "تێرابایت",
    "کاتژمێر", "خولەک", "چرکە",  # Added time units
]

# --- 3. AMBIGUOUS UNITS ---
# These will ONLY be converted if they follow a number.
UNITS_AMBIGUOUS = {
    "m",  # Can mean "I" (من)
    "ملم",  # Can mean "my neck" (ملم)
    "سم",  # Can mean "hoof" (سم)
    "s",  # 's' letter vs seconds (safe to keep ambiguous)
}

# --- 4. UNAMBIGUOUS MAP ---
UNITS_UNAMBIGUOUS_MAP = {
    abbr: full
    for abbr, full in UNITS_MAP.items()
    if abbr not in UNITS_AMBIGUOUS
}

# Regex for standalone, unambiguous units
standalone_keys = sorted(UNITS_UNAMBIGUOUS_MAP.keys(), key=len, reverse=True)
STANDALONE_UNIT_RE = re.compile(
    r"\b(" + r"|".join(map(re.escape, standalone_keys)) + r")\b",
    re.IGNORECASE
)

SUFFIXES = ["یە", "ە", "م", "مان", "ت", "تان", "ی", "یان", "یت"]

# --- 5. NUMBER+UNIT REGEX ---
all_unit_keys = sorted(
    list(UNITS_MAP.keys()) + UNITS_BASE,
    key=len,
    reverse=True
)
NUMBER_UNIT_RE = re.compile(
    r"(\d+(\.\d+)?)(\s*)(" + r"|".join(map(re.escape, all_unit_keys)) + r")(" +
    r"|".join(map(re.escape, SUFFIXES)) + r")?\b",
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