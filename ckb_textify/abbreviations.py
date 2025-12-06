# ckb_textify/abbreviations.py
import re

# This map holds the abbreviation and its full-word expansion.
ABBREVIATIONS_MAP = {
    "د.خ": " دوردی خوای لەسەر بێت ",
    "د. خ": " درودی خوای لەسەر بێت ",
    "د. خ.": " درودی خوای لەسەر بێت ",
    "د.": "دکتۆر",
    "پ.": "پڕۆفیسۆر",
    "ی.پ.": "یاریدەدەری پڕۆفیسۆر",
    # "م.": "مامۆستا",
    "پ.ز.": "پێش زایین ",
    "پ. ز.": "پێش زایین ",
    "هتد": "ھەتا دوایی",
    "ھتد": "ھەتا دوایی",
    # Add any others you can think of, like:
    # "و.": "وەرگێڕانی",
}

# --- Regex to find abbreviations ---

# We must sort the keys by length (longest first)
# This ensures we match "ی.پ." before "پ."
ordered_keys = sorted(ABBREVIATIONS_MAP.keys(), key=len, reverse=True)

# This pattern does two things:
# 1. \b(...) finds the abbreviation as a "whole word"
# 2. (\s*) matches any space (or no space) right after it
ABBREVIATION_RE = re.compile(
    r"\b(" + r"|".join(re.escape(k) for k in ordered_keys) + r")(\s*)"
)


def normalize_abbreviations(text: str) -> str:
    """
    Expands common abbreviations like "د." to "دکتۆر".
    It also standardizes spacing.

    Examples:
    - "د. کارزان" -> "دکتۆر کارزان"
    - "د.کارزان"  -> "دکتۆر کارزان"
    """

    def _replace_abbr(match):
        abbreviation = match.group(1)
        # We replace the abbreviation with its expansion
        # and enforce a SINGLE space after it.
        expansion = ABBREVIATIONS_MAP[abbreviation]
        return f"{expansion} "

    return ABBREVIATION_RE.sub(_replace_abbr, text)