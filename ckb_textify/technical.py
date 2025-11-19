# ckb_textify/technical.py
import re

# Digits map
DIGITS_MAP = {
    "0": "سفر", "1": "یەک", "2": "دوو", "3": "سێ", "4": "چوار",
    "5": "پێنج", "6": "شەش", "7": "حەوت", "8": "ھەشت", "9": "نۆ"
}

# Letters map
LETTER_MAP = {
    "a": "ئەی", "b": "بی", "c": "سی", "d": "دی", "e": "ئی", "f": "ئێف",
    "g": "جی", "h": "ئێچ", "i": "ئای", "j": "جەی", "k": "کەی", "l": "ئێڵ",
    "m": "ئێم", "n": "ئێن", "o": "ئۆ", "p": "پی", "q": "کیو", "r": "ئاڕ",
    "s": "ئێس", "t": "تی", "u": "یو", "v": "ڤی", "w": "دەبڵیو", "x": "ئێکس",
    "y": "وای", "z": "زێت",
    ":": " دوو خاڵ ", "-": " داش "
}

# UUID and MAC (Existing)
UUID_RE = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
MAC_RE = re.compile(r"\b([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}\b")

# --- NEW: Generic Alphanumeric Code ---
# Matches words that contain at least 1 digit AND at least 1 letter
# e.g. "A1", "Code-2", "A1-B2"
ALPHANUMERIC_RE = re.compile(r"\b(?=\w*\d)(?=\w*[a-zA-Z])[\w\-]+\b")


def _spell_out(text: str) -> str:
    result = []
    for char in text.lower():
        if char in DIGITS_MAP:
            result.append(DIGITS_MAP[char])
        elif char in LETTER_MAP:
            result.append(LETTER_MAP[char])
        else:
            result.append(char)
    return " ".join(result)


def normalize_technical(text: str) -> str:
    """
    Finds Technical IDs (UUID, MAC, Codes) and converts them to
    spoken character-by-character sequences.
    """
    text = UUID_RE.sub(lambda m: _spell_out(m.group(0)), text)
    text = MAC_RE.sub(lambda m: _spell_out(m.group(0)), text)
    # Expand generic codes
    text = ALPHANUMERIC_RE.sub(lambda m: _spell_out(m.group(0)), text)

    return text