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
from .chat_speak import normalize_chat_speak
from .emojis import normalize_emojis

# Setup Logger
logger = logging.getLogger("ckb_textify")
if not logger.hasHandlers():
    logging.basicConfig(level=logging.WARNING, format='%(name)s - %(levelname)s - %(message)s')

SUFFIXES = ["یە", "ە", "م", "مان", "ت", "تان", "ی", "یان", "یت"]

# --- Regex Patterns ---
DATE_PATTERN = re.compile(r"\b(\d{1,4}[/\-]\d{1,2}[/\-]\d{1,4})\b")
time_suffixes_pattern = '|'.join(map(re.escape, ALL_SUFFIXES))
TIME_PATTERN = re.compile(
    rf"\b\d{{1,2}}:\d{{2}}(?::\d{{2}})?(\s*ی)?\s*({time_suffixes_pattern})?\b",
    re.IGNORECASE
)
CURRENCY_PATTERN = re.compile(
    rf"((?:{'|'.join(map(re.escape, CURRENCY_MAP.keys()))})(?:\s*\d+(\.\d+)?)?|\d+(\.\d+)?\s*(?:{'|'.join(map(re.escape, CURRENCY_MAP.keys()))}))"
)
NUMBER_PATTERN = re.compile(r"(\d+(\.\d+)?)")
PERCENT_PATTERN = re.compile(
    r"(?<!\d)[%٪]\s*(\d+(\.\d+)?)|(\d+(\.\d+)?)\s*[%٪](?!\d)"
)
DECIMAL_UNIT_PATTERN = re.compile(r"(\d+\.\d+)\s*([^\W\d_،؛؟]+)?")

# --- Special Text Patterns ---
# Matches "+" between two letters (non-digit/non-symbol chars).
# e.g., "Word + Word" -> "Word lagal Word"
TEXT_PLUS_RE = re.compile(r"([^\W\d_])\s*\+\s*([^\W\d_])")

# --- PRE-UNIT FIXES ---
KURDISH_UNIT_FIX_MAP = {"م": "m", "مل": "ml", "سم": "cm"}
KURDISH_UNIT_FIX_RE = re.compile(r"(?<=\d)(\s*)(م|مل|سم)(?=[^\w]|$)")


# --- Handlers ---
def replace_decimal_with_unit(match):
    number_str = match.group(1)
    unit_and_suffix = match.group(2)
    result = ""

    try:
        number = float(number_str)
        if number % 1 == 0.5:
            integer_part = int(number)
            int_text = number_to_kurdish_text(integer_part)
            if not unit_and_suffix:
                result = f"{int_text} و نیو"
            else:
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
                result = f"{int_text} {unit} و {full_suffix}"
        else:
            decimal_text = convert_number_to_text_handler(str(number))
            result = f"{decimal_text} {unit_and_suffix}" if unit_and_suffix else decimal_text

    except ValueError:
        return match.group(0)

    # Pad result with spaces
    return f" {result} "


# --- Main Pipeline ---
def normalize_sentence_kurdish(text: str, config: dict = None) -> str:
    cfg = DEFAULT_CONFIG.copy()
    if config:
        unknown_keys = set(config.keys()) - set(DEFAULT_CONFIG.keys())
        if unknown_keys: logger.warning(f"Unknown config keys: {unknown_keys}")
        cfg.update(config)

    try:
        # 1. Text-to-Text Normalization
        text = standardize_punctuation(text)

        if cfg["normalize_characters"]: text = normalize_characters(text)
        if cfg["normalize_digits"]: text = normalize_digits(text)

        text = normalize_diacritics(
            text,
            mode=cfg.get("diacritics_mode", "convert"),
            remove_tatweel=cfg.get("remove_tatweel", True),
            shadda_mode=cfg.get("shadda_mode", "double")
        )

        # 2. Specific Patterns
        if cfg["date_time"]:
            text = DATE_PATTERN.sub(
                lambda m: f" {date_to_kurdish_text(m.group(1), 'dd/mm/yyyy' if '/' in m.group(1) else 'yyyy-mm-dd')} ",
                text)
            text = TIME_PATTERN.sub(lambda m: f" {time_to_kurdish_text(m.group().strip())} ", text)

        if cfg["phone_numbers"]: text = normalize_phone_numbers(text)

        if cfg["units"]:
            text = KURDISH_UNIT_FIX_RE.sub(lambda m: f"{m.group(1)}{KURDISH_UNIT_FIX_MAP[m.group(2)]}", text)
            text = normalize_units(text)
            text = normalize_standalone_units(text)

        if cfg["per_rule"]: text = normalize_per_rule(text)

        if cfg.get("chat_speak", False):
            text = normalize_chat_speak(text)

        if cfg["web"]: text = normalize_web(text)
        if cfg["technical"]: text = normalize_technical(text)
        if cfg["abbreviations"]: text = normalize_abbreviations(text)
        if cfg["arabic_names"]: text = normalize_arabic_names(text)

        if cfg["math"]:
            # 1. Handle Math expressions (Numbers + Operators)
            text = normalize_math_expressions(text)
            # 2. Handle Text + Text case (e.g. "Word + Word" -> "Word lagal Word")
            text = TEXT_PLUS_RE.sub(r"\1 لەگەڵ \2", text)
            # 3. Handle leftover "+" (Standalone or non-math) -> "ko"
            text = text.replace("+", " کۆ ")

        if cfg["percentage"]: text = PERCENT_PATTERN.sub(lambda m: f" {percentage_to_kurdish_text(m.group())} ", text)
        if cfg["currency"]: text = CURRENCY_PATTERN.sub(lambda m: f" {currency_to_kurdish_text(m.group())} ", text)

        if cfg["foreign"]: text = normalize_foreign_scripts(text)
        if cfg["latin"]: text = normalize_latin(text)

        # Emojis (Before Symbols)
        text = normalize_emojis(text, mode=cfg.get("emoji_mode", "remove"))

        if cfg["symbols"]: text = normalize_common_symbols(text)

        if cfg["decimals"]: text = DECIMAL_UNIT_PATTERN.sub(replace_decimal_with_unit, text)
        if cfg["integers"]: text = NUMBER_PATTERN.sub(lambda m: f" {convert_number_to_text_handler(m.group())} ", text)

        # Final Clean-up (Removes the extra spaces we just added)
        text = normalize_whitespace(text)

    except Exception as e:
        logger.error(f"Normalization failed: {e}")
        return text

    return text


def convert_all(text: str, config: dict = None) -> str:
    return normalize_sentence_kurdish(text, config)