# ckb_textify/latin.py
import re
from .english_ipa import ipa_transliterate

# --- Mappings (Same as before) ---
MULTI_CHAR_MAP = {
    "tion": "شن", "ght": "ت", "ph": "ف", "sh": "ش", "ch": "چ",
    "kh": "خ", "gh": "غ", "th": "س", "zh": "ژ", "oo": "وو",
    "ee": "ی", "qu": "کو", "ck": "ک",
}

SINGLE_CHAR_MAP = {
    "a": "ا", "b": "ب", "c": "ک", "d": "د", "e": "ێ", "f": "ف",
    "g": "گ", "h": "ه", "i": "ی", "j": "ج", "k": "ک", "l": "ل",
    "m": "م", "n": "ن", "o": "ۆ", "p": "پ", "q": "ک", "r": "ڕ",
    "s": "س", "t": "ت", "u": "و", "v": "ڤ", "w": "و", "x": "کس",
    "y": "ی", "z": "ز",
}

LETTER_NAMES = {
    "a": "ئەی", "b": "بی", "c": "سی", "d": "دی", "e": "ئی", "f": "ئێف",
    "g": "جی", "h": "ئێچ", "i": "ئای", "j": "جەی", "k": "کەی", "l": "ئێڵ",
    "m": "ئێم", "n": "ئێن", "o": "ئۆ", "p": "پی", "q": "کیو", "r": "ئاڕ",
    "s": "ئێس", "t": "تی", "u": "یو", "v": "ڤی", "w": "دەبڵیو", "x": "ئێکس",
    "y": "وای", "z": "زێت",
}

# Regex to split mixed case words (e.g. ChatGPT -> Chat, GPT)
# Matches: Sequence of Uppercase letters OR Sequence of Title/Lower letters
SPLIT_MIXED_RE = re.compile(r'[A-Z]+(?![a-z])|[A-Z]?[a-z]+')

# Regex to find Latin words
LATIN_WORD_RE = re.compile(r"[a-zA-Z]+")


def _fallback_transliterate(word: str) -> str:
    word = word.lower()
    result = ""
    if word and word[0] in "aeiou": result += "ئ"

    i = 0
    n = len(word)
    while i < n:
        found = False
        for length in [4, 3, 2]:
            if i + length <= n and word[i:i + length] in MULTI_CHAR_MAP:
                result += MULTI_CHAR_MAP[word[i:i + length]]
                i += length
                found = True
                break
        if found: continue

        char = word[i]
        if char in SINGLE_CHAR_MAP:
            result += SINGLE_CHAR_MAP[char]
        else:
            result += char
        i += 1
    return result


def _process_single_chunk(chunk: str) -> str:
    """Process a single clean chunk (e.g. 'Chat' or 'GPT')"""

    # Acronyms (GPT, USA)
    if chunk.isupper() and len(chunk) > 1:
        spelled_out = []
        for char in chunk:
            char_lower = char.lower()
            if char_lower in LETTER_NAMES:
                spelled_out.append(LETTER_NAMES[char_lower])
            else:
                spelled_out.append(char)
        return " ".join(spelled_out)

    # Standard Phonetic
    ipa_result = ipa_transliterate(chunk)
    if ipa_result: return ipa_result
    return _fallback_transliterate(chunk)


def _process_latin_word(match) -> str:
    full_word = match.group(0)

    # Split "ChatGPT" -> ["Chat", "GPT"]
    # Split "iPhone"  -> ["i", "Phone"]
    parts = SPLIT_MIXED_RE.findall(full_word)

    # If regex failed to split anything useful, use whole word
    if not parts: parts = [full_word]

    processed_parts = [_process_single_chunk(p) for p in parts]
    return " ".join(processed_parts)


def normalize_latin(text: str) -> str:
    return LATIN_WORD_RE.sub(_process_latin_word, text)