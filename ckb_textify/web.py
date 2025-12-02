# ckb_textify/web.py
import re

# --- 1. Common Web Terms ---
COMMON_TERMS_MAP = {
    # Email Providers
    "@gmail.com": " ئەت جیمەیڵ دۆت کۆم ",
    "@yahoo.com": " ئەت یاھوو دۆت کۆم ",
    "@outlook.com": " ئەت ئاوتلووک دۆت کۆم ",
    "@hotmail.com": " ئەت ھۆتمەیڵ دۆت کۆم ",
    "@icloud.com": " ئەت ئایکلاود دۆت کۆم ",

    # Protocols & Prefixes
    "https://": " ئێچ تی تی پی ئێس دوو خاڵ سلاش سلاش ",
    "http://": " ئێچ تی تی پی دوو خاڵ سلاش سلاش ",
    "www.": " دابڵیو دابڵیو دابڵیو دۆت ",

    # Domains
    ".com": " دۆت کۆم ",
    ".net": " دۆت نێت ",
    ".org": " دۆت ئۆڕگ ",
    ".edu": " دۆت ئیدیو ",
    ".gov": " دۆت گاڤ ",
    ".io": " دۆت ئای ئۆ ",
    ".krd": " دۆت کورد ",
    ".iq": " دۆت ئای کیو ",
}

# Regex to find these terms.
# We use capturing groups () so re.split will return the separators.
ordered_terms = sorted(COMMON_TERMS_MAP.keys(), key=len, reverse=True)
COMMON_TERMS_RE = re.compile(
    r"(" + r"|".join(re.escape(k) for k in ordered_terms) + r")",
    re.IGNORECASE
)

# --- 2. Symbol & Character Maps ---
WEB_SYMBOL_MAP = {
    ".": " دۆت ",
    "@": " ئەت ",
    "/": " سلاش ",
    ":": " دوو خاڵ ",
    "-": " داش ",
    "_": " ئەندەرسکۆڕ ",
    "?": " نیشانەی پرسیار ",
    "=": " یەکسانە ",
    "&": " ئەند ",
}

LETTER_MAP = {
    "a": "ئەی", "b": "بی", "c": "سی", "d": "دی", "e": "ئی", "f": "ئێف",
    "g": "جی", "h": "ئێچ", "i": "ئای", "j": "جەی", "k": "کەی", "l": "ئێڵ",
    "m": "ئێم", "n": "ئێن", "o": "ئۆ", "p": "پی", "q": "کیو", "r": "ئاڕ",
    "s": "ئێس", "t": "تی", "u": "یو", "v": "ڤی", "w": "دەبڵیو", "x": "ئێکس",
    "y": "وای", "z": "زێت",
}

DIGITS_MAP = {
    "0": "سفر", "1": "یەک", "2": "دوو", "3": "سێ", "4": "چوار",
    "5": "پێنج", "6": "شەش", "7": "حەوت", "8": "ھەشت", "9": "نۆ"
}

# --- 3. Detection Regex Patterns ---
EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")

URL_RE = re.compile(
    r"\b((?:https?://|www\.)[-a-zA-Z0-9+&@#/%?=~_|!:,.;]*[-a-zA-Z0-9+&@#/%=~_|])"
    r"|"
    r"\b([a-zA-Z0-9-]+\.(com|net|org|edu|gov|mil|io|co|kr|iq|krd))\b",
    re.IGNORECASE
)


# --- 4. Logic to Split and Spell ---
def _spell_web_string(text: str) -> str:
    """
    Converts a string (URL/Email) to spoken Kurdish.
    Splits the string by 'Known Terms' so we don't double-process them.
    """
    # 1. Split text by common terms (e.g. splits "www.rudaw.com" into ["", "www.", "rudaw", ".com", ""])
    parts = COMMON_TERMS_RE.split(text)

    result_parts = []

    for part in parts:
        if not part:
            continue  # Skip empty splits

        part_lower = part.lower()

        # CASE A: It is a Known Common Term (e.g., ".com")
        if part_lower in COMMON_TERMS_MAP:
            # Append the full Kurdish word directly (do not spell check it)
            result_parts.append(COMMON_TERMS_MAP[part_lower])

        # CASE B: It is Unknown Text (e.g., "rudaw")
        else:
            # Spell this part character by character
            spelled_chars = []
            for char in part:
                char_lower = char.lower()
                if char_lower in WEB_SYMBOL_MAP:
                    spelled_chars.append(WEB_SYMBOL_MAP[char_lower])
                elif char_lower in LETTER_MAP:
                    spelled_chars.append(LETTER_MAP[char_lower])
                elif char_lower in DIGITS_MAP:
                    spelled_chars.append(DIGITS_MAP[char_lower])
                else:
                    # If it's already Kurdish or unknown, keep it
                    spelled_chars.append(char)

            # Join the characters with spaces
            result_parts.append(" ".join(spelled_chars))

    # Join all parts and clean up extra spaces
    final_text = " ".join(result_parts)
    return re.sub(r'\s+', ' ', final_text).strip()


def normalize_web(text: str) -> str:
    """
    Finds Emails and URLs and converts them to spoken text.
    """
    text = EMAIL_RE.sub(lambda m: _spell_web_string(m.group(0)), text)
    text = URL_RE.sub(lambda m: _spell_web_string(m.group(0)), text)
    return text