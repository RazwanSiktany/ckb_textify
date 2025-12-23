import re

# --- 1. Rigid Patterns (High Priority - Tokenizer) ---
# Expanded URL pattern to include ftp, sftp, file schemes
URL_PATTERN = r"\b(?:https?|ftp|sftp|file)://\S+|\bwww\.\S+|\b[a-zA-Z0-9.-]+\.[a-z]{2,}\b"

# Allow extended Latin characters (unicode 0080-FFFF) in emails
EMAIL_PATTERN = r"\b[a-zA-Z0-9._%+\-\u0080-\uFFFF]+@[a-zA-Z0-9.\-\u0080-\uFFFF]+\.[a-zA-Z]{2,}\b"

# Phone Numbers
PHONE_PATTERN = r"""
    (?:\b(?=\d)|(?=\+))              
    (?:(?:\+|00)\s*964[\s-]?)?       
    (?:0?7[5789]\d)                  
    (?:[\s-]?\d{3})                  
    (?:[\s-]?\d{2})                  
    (?:[\s-]?\d{2})                  
    \b
"""

# Date/Time
DATE_PATTERN = r"\b(?:\d{4}[/-]\d{1,2}[/-]\d{1,2})|(?:\d{1,2}[/-]\d{1,2}[/-]\d{4})\b"
TIME_PATTERN = r"\b\d{1,2}:\d{2}(?::\d{2})?(?:\s*(?:[AaPp]\.?[Mm]\.?))?\b"

# Technical
HASHTAG_PATTERN = r"\#\w+"
MENTION_PATTERN = r"@\w+"
UUID_PATTERN = r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
# MAC Address Pattern (e.g. 00:1A:2B:3C:4D:5E)
MAC_PATTERN = r"\b(?:(?:[0-9]\s[a-fA-F]|[0-9a-fA-F]{2})[:-]){5}(?:[0-9]\s[a-fA-F]|[0-9a-fA-F]{2})\b"

DEGREE_UNIT_PATTERN = r"°[CcFfNnSsEeWw]?"

# --- New: Math Subscripts & Superscripts ---
# Subscripts (0-9): \u2080-\u2089
SUBSCRIPT_PATTERN = r"[\u2080-\u2089]+"
# Superscripts (0, 1, 2, 3, 4-9): \u2070, \u00B9, \u00B2, \u00B3, \u2074-\u2079
SUPERSCRIPT_PATTERN = r"[\u2070\u00B9\u00B2\u00B3\u2074-\u2079]+"

# --- 2. Building Block Patterns ---
NUMBER_PATTERN = r"\b(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?:e[+-]?\d+)?\b"

ARABIC_DIACRITICS = r"\u064B-\u065F\u0670\u06E1\u06D6-\u06ED"
# FIX: Removed \u00B2\u00B3 from WORD_PATTERN to force splitting of units (m²)
WORD_PATTERN = rf"[\w{ARABIC_DIACRITICS}]+"

SYMBOL_PATTERN = r"[^\w\s]"

# --- 3. Master Tokenizer ---
TOKENIZER_REGEX = re.compile(
    rf"""
    (?P<URL>{URL_PATTERN})|
    (?P<EMAIL>{EMAIL_PATTERN})|
    (?P<PHONE>{PHONE_PATTERN})|
    (?P<TECHNICAL>{MAC_PATTERN}|{UUID_PATTERN}|{HASHTAG_PATTERN}|{MENTION_PATTERN})|
    (?P<DATE>{DATE_PATTERN})|         
    (?P<TIME>{TIME_PATTERN})|         
    (?P<UNIT_SPECIAL>{DEGREE_UNIT_PATTERN})|
    (?P<SUBSCRIPT>{SUBSCRIPT_PATTERN})|    
    (?P<SUPERSCRIPT>{SUPERSCRIPT_PATTERN})| 
    (?P<NUMBER>{NUMBER_PATTERN})|
    (?P<WORD>{WORD_PATTERN})|         
    (?P<SYMBOL>{SYMBOL_PATTERN})
    """,
    re.VERBOSE | re.IGNORECASE
)

# --- 4. Logic Patterns (Taggers & Suffixes) ---

# Base Pronoun Suffixes
BASE_SUFFIXES = [
    "یە", "ە",
    "م", "مان", "ت", "تان", "ی", "یان",
    "مم", "ممان", "مت", "متان", "می", "میان",
    "مانم", "مانمان", "مانت", "مانتان", "مانی", "مانیان",
    "تم", "تمان", "تت", "تتان", "تی", "تیان",
    "تانم", "تانمان", "تانت", "تانتان", "تانی", "تانیان",
    "یم", "یمان", "یت", "یتان", "یی", "ییان",
    "یانم", "یانمان", "یانت", "یانتان", "یانی", "یانیان",
]

# Definite Articles
DEFINITE_ARTICLES = ["ەکە", "ەکان", "یەکە", "یەکان", "یش"]

# Generate all combinations
SUFFIXES_LIST = BASE_SUFFIXES + DEFINITE_ARTICLES + [
    f"{art}{sfx}" for art in DEFINITE_ARTICLES for sfx in BASE_SUFFIXES
]
# Sort by length (descending) to ensure greedy regex matching
SUFFIXES_LIST.sort(key=len, reverse=True)

SUFFIX_REGEX_PART = "|".join(SUFFIXES_LIST)

# Expanded Unit Regex with new units
# Multiline string for Verbose regex must rely on whitespace handling
# We ensure lines end with pipes where needed to connect alternatives
UNIT_CORE = r"""
    km|m|cm|mm|kg|g|mg|l|ml|
    in|ft|yd|mi|gal|oz|lb|ton|mph|ms|
    K|J|kJ|cal|kcal|Wh|kWh|kW|W|MW|HP|Pa|kPa|psi|V|mV|A|mA|Ω|N|kN|mAh|
    کیلۆمەتر|مەتر|سانتیمەتر|میلیمەتر|کم|
    کیلۆگرام|گرام|میلیگرام|
    لیتر|میلیلیتر|
    کاتژمێر|خولەک|چرکە|
    جێگابایت|مێگابایت|کیلۆبایت|تێرابایت|
    gb|mb|kb|tb|h|hr|min|sec|s|
    °c|°f|c|f|°n|°s|°e|°w|°|″|′|
    کگم|کغم|کیلۆ|کیلۆم|گم|سم|ملم|ملیمەتر|م
"""

UNIT_PATTERN = rf"\b(?:{UNIT_CORE})(?:{SUFFIX_REGEX_PART})?\b"