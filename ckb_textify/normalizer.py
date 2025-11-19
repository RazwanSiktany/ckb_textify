# ckb_textify/normalizer.py
import re
import unicodedata

# ... (CHAR_MAP, PUNCTUATION_MAP, HEH, etc. remain the same) ...
CHAR_MAP = {
    'أ': 'ا', 'إ': 'ا', 'آ': 'ا', 'ي': 'ی', 'ى': 'ی',
    'ك': 'ک', 'ة': 'ه',
}
PUNCTUATION_MAP = {'،': ',', '؛': ';', '؟': '?'}
HEH = "\u0647"
E_VOWEL = "\u06D5"
HEH_DOACHASHMEE = "\u06BE"
ZWNJ = "\u200C"
ALEF = "\u0627"
O_VOWEL = "\u06C6"
E_VOWEL_WITH_DOT = "\u06CE"

DIACRITICS_RE = re.compile(r"[\u064B-\u0652]")
WHITESPACE_RE = re.compile(r"\s+")
NOISY_PUNCTUATION_RE = re.compile(r"[\(\)\[\]\{\}<>\"“”‘’'«»]")
HEH_END_OF_WORD_RE = re.compile(rf"{HEH}(\s|$)")
HEH_LIKE_CHARS = f"[{E_VOWEL}{HEH}{HEH_DOACHASHMEE}]"
VOWELS = f"[{ALEF}{O_VOWEL}{E_VOWEL_WITH_DOT}]"
HEH_LIKE_BEFORE_VOWEL_RE = re.compile(rf"({HEH_LIKE_CHARS})(?={VOWELS})")
VOWEL_BEFORE_HEH_LIKE_RE = re.compile(rf"(?<={VOWELS})({HEH_LIKE_CHARS})")


# --- Normalization Functions ---

def normalize_digits(text: str) -> str:
    arabic_digits = '٠١٢٣٤٥٦٧٨٩'
    hindi_digits = '۰۱۲۳۴۵۶۷۸۹'
    translation_table = {}
    for i, digit in enumerate(arabic_digits):
        translation_table[ord(digit)] = str(i)
    for i, digit in enumerate(hindi_digits):
        translation_table[ord(digit)] = str(i)

    text = text.translate(translation_table)

    # --- *** NEW: Fix Arabic Decimal Separator *** ---
    # Convert "٢٫٥" (after digit transliteration) to "2.5"
    text = text.replace("٫", ".")

    # Smart Number Formatting (European/US detection) from previous step
    def _clean_number(match):
        num_str = match.group(0)
        if '.' in num_str and ',' in num_str:
            last_dot = num_str.rfind('.')
            last_comma = num_str.rfind(',')
            if last_comma > last_dot:
                return num_str.replace('.', '').replace(',', '.')
            else:
                return num_str.replace(',', '')
        elif ',' in num_str and '.' not in num_str:
            return num_str.replace(',', '')
        return num_str

    return re.sub(r'\d[\d,.]*\d', _clean_number, text)


def normalize_characters(text: str) -> str:
    text = unicodedata.normalize('NFKC', text)
    for src, dest in CHAR_MAP.items():
        text = text.replace(src, dest)
    text = text.replace(f"{HEH}{ZWNJ}", E_VOWEL)
    text = HEH_END_OF_WORD_RE.sub(f"{E_VOWEL}\\1", text)
    text = text.replace(HEH, HEH_DOACHASHMEE)
    text = HEH_LIKE_BEFORE_VOWEL_RE.sub(HEH_DOACHASHMEE, text)
    text = VOWEL_BEFORE_HEH_LIKE_RE.sub(HEH_DOACHASHMEE, text)
    return text


def remove_diacritics(text: str) -> str:
    return DIACRITICS_RE.sub('', text)


def standardize_punctuation(text: str) -> str:
    for src, dest in PUNCTUATION_MAP.items():
        text = text.replace(src, dest)
    text = NOISY_PUNCTUATION_RE.sub('', text)
    return text


def normalize_whitespace(text: str) -> str:
    return WHITESPACE_RE.sub(' ', text).strip()