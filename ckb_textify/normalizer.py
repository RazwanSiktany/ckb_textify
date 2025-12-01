# ckb_textify/normalizer.py
import re
import unicodedata

# --- 1. Character Maps ---

# Quranic Muqatta'at (Disjointed Letters)
# Mapped to their spoken Kurdish form.
MUQATTAAT_MAP = {
    "الٓمٓصٓ": "ئەلیف لام میم صاد",
    "الٓمٓر ۚ": "ئەلیف لام میم ڕائ",
    "كٓهيعٓصٓ": "کاف ھائ عەین صاد",
    "طسٓمٓ": "طا سین میم",
    "الٓمٓ": "ئەلیف لام میم",
    "الٓر ۚ": "ئەلیف لام ڕائ",
    "طسٓ ۚ": "طا سین",
    "يسٓ": "یا سین",
    "صٓ ۚ": "صاد",
    "قٓ ۚ": "قاف",
    "نٓ ۚ": "نون",
    "حمٓ": "حائ میم",
    "طه": "طاھا",
}

CHAR_MAP = {
    # Alif Variants
    'أ': 'ئە',  # Alif Hamza Above
    'إ': 'ئی',  # Alif Hamza Below
    # 'آ': 'ئا', (Handled explicitly)
    'ى': 'ا',  # Alif Maqsura
    'ء': 'ئ',  # Hamza
    'ؤ': 'وئ',  # Waw with Hamza
    'ئ': 'ئ',  # Yaa with Hamza
    'وٰ': 'ا',  # Waw with Dagger Alif
    # 'ٰ': 'ا',    <-- REMOVED (Handled in diacritics.py to protect from Wasla logic)
    'ٓ': '',  # Maddah (Remove stray maddahs)
    'ٔ': 'ئ',  # Hamza Above
    'ٴ': 'ئ',  # High Hamza

    # Presentation Forms
    '\ufe8d': 'ا',
    '\ufe8e': 'ا',

    # Standard Normalization
    'ك': 'ک',
    # 'ة': 'ه', (Handled in diacritics.py)
    'ي': 'ی',
}

PUNCTUATION_MAP = {'،': ',', '؛': ';', '؟': '?'}

# --- 2. Constants & Regex ---
HEH = "\u0647"
E_VOWEL = "\u06D5"
HEH_DOACHASHMEE = "\u06BE"
ZWNJ = "\u200C"
ALEF = "\u0627"
O_VOWEL = "\u06C6"
E_VOWEL_WITH_DOT = "\u06CE"
ALEF_WASLA = "\u0671"
WASLA_PLACEHOLDER = "\uE000"

# Alif Madda Logic
ALEF_MADDA = "آ"
# Regex for Alif Madda at the start of a word
ALEF_MADDA_START_RE = re.compile(r'(?<![\w\u0640-\u065F\u0670])' + ALEF_MADDA)

WHITESPACE_RE = re.compile(r"\s+")
NOISY_PUNCTUATION_RE = re.compile(r"[\(\)\[\]\{\}<>\"“”‘’'«»]")
HEH_END_OF_WORD_RE = re.compile(rf"{HEH}(\s|$)")

# Heh Rule 4 Regexes
HEH_LIKE_CHARS = f"[{E_VOWEL}{HEH}{HEH_DOACHASHMEE}]"
VOWELS = f"[{ALEF}{O_VOWEL}{E_VOWEL_WITH_DOT}]"
HEH_LIKE_BEFORE_VOWEL_RE = re.compile(rf"({HEH_LIKE_CHARS})(?={VOWELS})")
VOWEL_BEFORE_HEH_LIKE_RE = re.compile(rf"(?<={VOWELS})({HEH_LIKE_CHARS})")


# --- 3. Functions ---

def normalize_digits(text: str) -> str:
    arabic_digits = '٠١٢٣٤٥٦٧٨٩'
    hindi_digits = '۰۱۲۳۴۵۶۷۸۹'
    translation_table = {}
    for i, digit in enumerate(arabic_digits):
        translation_table[ord(digit)] = str(i)
    for i, digit in enumerate(hindi_digits):
        translation_table[ord(digit)] = str(i)

    text = text.translate(translation_table)
    text = text.replace("٬", "")
    text = text.replace("٫", ".")

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
    # 1. Protect Alif Wasla
    text = text.replace('\ufdf0', ALEF_WASLA).replace('\ufb51', ALEF_WASLA)
    text = text.replace(ALEF_WASLA, WASLA_PLACEHOLDER)

    # 2. Standard Unicode Normalization
    text = unicodedata.normalize('NFKC', text)

    # 3. Restore Alif Wasla
    text = text.replace(WASLA_PLACEHOLDER, ALEF_WASLA)

    # 4. Handle Muqatta'at
    for src, dest in MUQATTAAT_MAP.items():
        text = text.replace(src, dest)

    # 5. Handle Alif Madda
    text = ALEF_MADDA_START_RE.sub('ئا', text)
    text = text.replace(ALEF_MADDA, 'ا')

    # 6. Handle Alif Hamza Above
    text = re.sub(r'أ(?=\u064F)', 'ئ', text)

    # 7. Handle Fatha + Hamza Above (e.g. in ٱلْـَٔاخِرَةِ)
    # Replaces Fatha-Hamza with just Hamza 'ئ' to prevent Fatha becoming 'ە'
    text = text.replace("\u064E\u0654", "ئ")

    # 8. Apply Map Replacements
    for src, dest in CHAR_MAP.items():
        text = text.replace(src, dest)

    # 9. Remove Silent Alef
    text = text.replace("وا۟", "و")

    # 10. Handle Heh Rules
    text = text.replace(f"{HEH}{ZWNJ}", E_VOWEL)
    text = HEH_END_OF_WORD_RE.sub(f"{E_VOWEL}\\1", text)
    text = text.replace(HEH, HEH_DOACHASHMEE)

    # 11. Handle Heh next to Vowels
    text = HEH_LIKE_BEFORE_VOWEL_RE.sub(HEH_DOACHASHMEE, text)
    text = VOWEL_BEFORE_HEH_LIKE_RE.sub(HEH_DOACHASHMEE, text)

    return text


def standardize_punctuation(text: str) -> str:
    for src, dest in PUNCTUATION_MAP.items():
        text = text.replace(src, dest)
    text = NOISY_PUNCTUATION_RE.sub('', text)
    return text


def normalize_whitespace(text: str) -> str:
    return WHITESPACE_RE.sub(' ', text).strip()