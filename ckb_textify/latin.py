# ckb_textify/latin.py
import re
from .english_ipa import ipa_transliterate

# --- 1. Multi-Character Mappings ---
MULTI_CHAR_MAP = {
    "tion": "شن", "ght": "ت", "ph": "ف", "sh": "ش", "ch": "چ",
    "kh": "خ", "gh": "غ", "th": "س", "zh": "ژ", "oo": "وو",
    "ee": "ی", "qu": "کو", "ck": "ک",
}

# --- 2. Single Character Mappings (Phonetic) ---
SINGLE_CHAR_MAP = {
    "a": "ا", "b": "ب", "c": "ک", "d": "د", "e": "ێ", "f": "ف",
    "g": "گ", "h": "ه", "i": "ی", "j": "ج", "k": "ک", "l": "ل",
    "m": "م", "n": "ن", "o": "ۆ", "p": "پ", "q": "ک", "r": "ڕ",
    "s": "س", "t": "ت", "u": "و", "v": "ڤ", "w": "و", "x": "کس",
    "y": "ی", "z": "ز",
}

# --- 3. Letter Names (For Acronyms like GPT) ---
LETTER_NAMES = {
    "a": "ئەی", "b": "بی", "c": "سی", "d": "دی", "e": "ئی", "f": "ئێف",
    "g": "جی", "h": "ئێچ", "i": "ئای", "j": "جەی", "k": "کەی", "l": "ئێڵ",
    "m": "ئێم", "n": "ئێن", "o": "ئۆ", "p": "پی", "q": "کیو", "r": "ئاڕ",
    "s": "ئێس", "t": "تی", "u": "یو", "v": "ڤی", "w": "دەبڵیو", "x": "ئێکس",
    "y": "وای", "z": "زێت",
}

# *** UPDATED REGEX ***
# Removed \b to match "GPT" inside "ChatGPT" or "چاتGPT"
LATIN_WORD_RE = re.compile(r"[a-zA-Z]+")


def _fallback_transliterate(word: str) -> str:
    word = word.lower()
    result = ""

    # Initial Vowel Rule
    if word and word[0] in "aeiou":
        result += "ئ"

    i = 0
    n = len(word)
    while i < n:
        if i + 4 <= n and word[i:i + 4] in MULTI_CHAR_MAP:
            result += MULTI_CHAR_MAP[word[i:i + 4]]
            i += 4
            continue
        if i + 3 <= n and word[i:i + 3] in MULTI_CHAR_MAP:
            result += MULTI_CHAR_MAP[word[i:i + 3]]
            i += 3
            continue
        if i + 2 <= n and word[i:i + 2] in MULTI_CHAR_MAP:
            result += MULTI_CHAR_MAP[word[i:i + 2]]
            i += 2
            continue
        char = word[i]
        if char in SINGLE_CHAR_MAP:
            result += SINGLE_CHAR_MAP[char]
        else:
            result += char
        i += 1
    return result


def _process_latin_word(match) -> str:
    word = match.group(0)

    # --- *** NEW: Handle Acronyms (All Uppercase) *** ---
    # If "GPT", "USA", "KRG" -> Spell it out
    # Exception: 'I' and 'A' are single letters but often words,
    # but spelling them out (Ai, Ey) is usually safe/correct for TTS.
    if word.isupper():
        spelled_out = []
        for char in word:
            char_lower = char.lower()
            if char_lower in LETTER_NAMES:
                spelled_out.append(LETTER_NAMES[char_lower])
            else:
                spelled_out.append(char)
        return " ".join(spelled_out)

    # --- Standard Phonetic Transliteration ---

    # 1. Try Accurate IPA Transliteration
    ipa_result = ipa_transliterate(word)
    if ipa_result:
        return ipa_result

    # 2. Fallback to Rules
    return _fallback_transliterate(word)


def normalize_latin(text: str) -> str:
    """
    Finds English words/acronyms and converts them to Sorani.
    Handles attached words (e.g. چاتGPT).
    """
    return LATIN_WORD_RE.sub(_process_latin_word, text)