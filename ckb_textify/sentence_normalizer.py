# ckb_textify/sentence_normalizer.py

import re
import logging
from .config import DEFAULT_CONFIG
from .normalizer import (
    normalize_digits, normalize_characters,
    standardize_punctuation, normalize_whitespace
)
from .diacritics import normalize_diacritics
from .symbols import normalize_common_symbols
from .currency import currency_to_kurdish_text, CURRENCY_MAP
from .percentage import percentage_to_kurdish_text
from .date_time import date_to_kurdish_text, time_to_kurdish_text, ALL_SUFFIXES
from .math_operations import normalize_math_expressions, convert_number_to_text_handler
from .units import normalize_units, normalize_per_rule, normalize_standalone_units
from .abbreviations import normalize_abbreviations
from .phone_numbers import normalize_phone_numbers
from .arabic_names import normalize_arabic_names
from .number_to_text import number_to_kurdish_text
from .decimal_handler import decimal_to_kurdish_text
from .technical import normalize_technical
from .web import normalize_web
from .latin import normalize_latin
from .transliteration import normalize_foreign_scripts

# Setup Logger
logger = logging.getLogger("ckb_textify")
if not logger.hasHandlers():
    logging.basicConfig(level=logging.WARNING, format='%(name)s - %(levelname)s - %(message)s')

SUFFIXES = ["یە", "ە", "م", "مان", "ت", "تان", "ی", "یان", "یت"]

# --- Regex Patterns ---
DATE_PATTERN = re.compile(r"\b(\d{1,4}[/\-]\d{1,2}[/\-]\d{2,4})\b")
time_suffixes_pattern = '|'.join(map(re.escape, ALL_SUFFIXES))
TIME_PATTERN = re.compile(
    rf"\b\d{{1,2}}:\d{{2}}(?::\d{{2}})?(\s*ی)?\s*({time_suffixes_pattern})?\b",
    re.IGNORECASE
)
CURRENCY_PATTERN = re.compile(
    rf"((?:{'|'.join(map(re.escape, CURRENCY_MAP.keys()))})(?:\s*\d+(\.\d+)?)?|\d+(\.\d+)?\s*(?:{'|'.join(map(re.escape, CURRENCY_MAP.keys()))}))"
)
NUMBER_PATTERN = re.compile(r"(\d+(\.\d+)?)")

# --- UPDATED PERCENT REGEX ---
# Matches both % and ٪
PERCENT_PATTERN = re.compile(
    r"(?<!\d)[%٪]\s*(\d+(\.\d+)?)|(\d+(\.\d+)?)\s*[%٪](?!\d)"
)

DECIMAL_UNIT_PATTERN = re.compile(r"(\d+\.\d+)\s*([^\W\d_،؛؟]+)?")


# --- Handlers ---
def replace_decimal_with_unit(match):
    number_str = match.group(1)
    unit_and_suffix = match.group(2)
    try:
        number = float(number_str)
    except ValueError:
        return match.group(0)

    if number % 1 == 0.5:
        integer_part = int(number)
        int_text = number_to_kurdish_text(integer_part)
        if not unit_and_suffix:
            return f"{int_text} و نیو"

        unit = unit_and_suffix.strip()
        suffix = ""
        for sfx in sorted(SUFFIXES, key=len, reverse=True):
            if unit.endswith(sfx):
                unit = unit[:-len(sfx)]
                suffix = sfx
                break

        if suffix in ["یە", "ە"]:
            niw_text = "نیوە"
        else:
            niw_text = "نیو"
        full_suffix = f"{niw_text}{suffix}" if suffix not in ["", "ە", "یە"] else niw_text
        return f"{int_text} {unit} و {full_suffix}"
    else:
        decimal_text = convert_number_to_text_handler(str(number))
        return f"{decimal_text} {unit_and_suffix}" if unit_and_suffix else decimal_text


# --- Main Pipeline ---
def normalize_sentence_kurdish(text: str, config: dict = None) -> str:
    cfg = DEFAULT_CONFIG.copy()
    if config:
        unknown_keys = set(config.keys()) - set(DEFAULT_CONFIG.keys())
        if unknown_keys: logger.warning(f"Unknown config keys: {unknown_keys}")
        cfg.update(config)

    try:
        # 1. Text-to-Text Normalization
        if cfg["normalize_characters"]: text = normalize_characters(text)
        if cfg["normalize_digits"]: text = normalize_digits(text)

        # Arabic Names (Moved BEFORE Diacritics)
        # This ensures names like "الله" are handled by dictionary lookup first.
        if cfg["arabic_names"]: text = normalize_arabic_names(text)

        # Diacritics (Harakat) & Tatweel
        text = normalize_diacritics(
            text,
            mode=cfg.get("diacritics_mode", "convert"),
            remove_tatweel=cfg.get("remove_tatweel", True),
            shadda_mode=cfg.get("shadda_mode", "double")
        )

        # 2. Specific Patterns
        if cfg["date_time"]:
            text = DATE_PATTERN.sub(
                lambda m: date_to_kurdish_text(m.group(1), "dd/mm/yyyy" if "/" in m.group(1) else "yyyy-mm-dd"), text)
            text = TIME_PATTERN.sub(lambda m: time_to_kurdish_text(m.group().strip()), text)

        if cfg["phone_numbers"]: text = normalize_phone_numbers(text)

        if cfg["units"]:
            text = normalize_units(text)
            text = normalize_standalone_units(text)
        if cfg["per_rule"]: text = normalize_per_rule(text)

        if cfg["web"]: text = normalize_web(text)
        if cfg["technical"]: text = normalize_technical(text)
        if cfg["abbreviations"]: text = normalize_abbreviations(text)

        # Removed arabic_names from here (Moved up)

        if cfg["math"]: text = normalize_math_expressions(text)
        if cfg["percentage"]: text = PERCENT_PATTERN.sub(lambda m: percentage_to_kurdish_text(m.group()), text)
        if cfg["currency"]: text = CURRENCY_PATTERN.sub(lambda m: currency_to_kurdish_text(m.group()) + " ", text)

        if cfg["foreign"]: text = normalize_foreign_scripts(text)
        if cfg["latin"]: text = normalize_latin(text)
        if cfg["symbols"]: text = normalize_common_symbols(text)

        if cfg["decimals"]: text = DECIMAL_UNIT_PATTERN.sub(replace_decimal_with_unit, text)
        if cfg["integers"]: text = NUMBER_PATTERN.sub(lambda m: convert_number_to_text_handler(m.group()), text)

        text = standardize_punctuation(text)
        text = normalize_whitespace(text)

    except Exception as e:
        logger.error(f"Normalization failed: {e}")
        return text

    return text


def convert_all(text: str, config: dict = None) -> str:
    return normalize_sentence_kurdish(text, config)