# ckb_textify/english_ipa.py
import re
import logging

# Setup Logger
logger = logging.getLogger("ckb_textify")

try:
    import eng_to_ipa as ipa

    _HAS_IPA_LIB = True
except ImportError:
    _HAS_IPA_LIB = False
    # Log a warning so the user knows why IPA isn't working
    logger.warning("Optional dependency 'eng-to-ipa' not found. English transliteration will fall back to basic rules.")

# --- IPA Vowels List ---
# If a word starts with these sounds, we must add 'ئ'
IPA_VOWELS = {
    "ɑ", "æ", "ə", "ɛ", "i", "ɪ", "ɔ", "o", "u", "ʊ", "ʌ", "e", "a"
}

# --- IPA to Sorani Map ---
IPA_MAP = {
    # --- Consonants ---
    "b": "ب", "d": "د", "f": "ف", "g": "گ",
    "h": "ھ", "j": "ی", "k": "ک", "l": "ل",
    "m": "م", "n": "ن", "p": "پ", "r": "ڕ",
    "s": "س", "t": "ت", "v": "ڤ", "w": "و",
    "z": "ز",
    "ʃ": "ش", "ʒ": "ژ", "θ": "س", "ð": "ز",
    "ŋ": "نگ", "ʧ": "چ", "ʤ": "ج",

    # --- Vowels ---
    "ɑ": "ا", "æ": "ا", "ə": "ە", "ɛ": "ێ",
    "i": "ی", "ɪ": "ی", "ɔ": "ۆ", "o": "ۆ",
    "u": "و", "ʊ": "و", "ʌ": "ە", "e": "ێ",
    "a": "ا",

    # --- Diphthongs ---
    "aɪ": "ای", "eɪ": "ەی", "ɔɪ": "ۆێ",
    "aʊ": "ەو", "oʊ": "ۆ",
}


def ipa_transliterate(word: str) -> str | None:
    if not _HAS_IPA_LIB:
        return None

    # Get IPA (returns "word*" if unknown)
    ipa_text = ipa.convert(word)

    if "*" in ipa_text:
        return None

    # Clean stress markers
    ipa_text = re.sub(r"[ˈˌ]", "", ipa_text)

    kurdish_word = ""

    # Handle Initial Vowel Rule: Prepend Hamza (ئ)
    if len(ipa_text) > 0 and ipa_text[0] in IPA_VOWELS:
        kurdish_word += "ئ"

    i = 0
    n = len(ipa_text)

    while i < n:
        # Try 2-char match (Diphthongs)
        if i + 2 <= n and ipa_text[i:i + 2] in IPA_MAP:
            kurdish_word += IPA_MAP[ipa_text[i:i + 2]]
            i += 2
            continue

        # Single char match
        char = ipa_text[i]
        if char in IPA_MAP:
            kurdish_word += IPA_MAP[char]
        else:
            kurdish_word += char
        i += 1

    return kurdish_word