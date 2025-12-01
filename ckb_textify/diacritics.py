# ckb_textify/diacritics.py
import re

# --- 1. Tajweed Rules (Iqlab & Idgham) ---
# Y, R, M, L, W, N
YARMALOON_LETTERS = "يرملون"

# A. IQLAB (N -> M before B)
# Match Nun+Sukun followed by Ba
IQLAB_NUN_RE = re.compile(r"ن\u0652(\s*)ب")
# Match Tanween followed by Ba
IQLAB_TANWEEN_FATH_RE = re.compile(r"\u064B(\s*)ب")  # an -> a + m
IQLAB_TANWEEN_KASR_RE = re.compile(r"\u064D(\s*)ب")  # in -> i + m
IQLAB_TANWEEN_DAMM_RE = re.compile(r"\u064C(\s*)ب")  # un -> u + m

# B. IDGHAM (Merge N into Next Letter)
# Match Nun+Sukun followed by Yarmaloon
IDGHAM_NUN_RE = re.compile(rf"ن\u0652(\s*)([{YARMALOON_LETTERS}])")
# Match Tanween followed by Yarmaloon
IDGHAM_TANWEEN_FATH_RE = re.compile(rf"\u064B(\s*)([{YARMALOON_LETTERS}])")
IDGHAM_TANWEEN_KASR_RE = re.compile(rf"\u064D(\s*)([{YARMALOON_LETTERS}])")
IDGHAM_TANWEEN_DAMM_RE = re.compile(rf"\u064C(\s*)([{YARMALOON_LETTERS}])")

# --- 2. Shamsi (Sun) Letter Logic ---
# These letters assimilate the 'L' of 'Al-' (ال).
SHAMSI_LETTERS = "تثدذرزسشصضطظلن"
# Regex to find 'Lam' followed by a Shamsi letter that HAS A SHADDA.
# Added (^|\s) to start to ensure we only match 'Al-' at the start of a word.
# Group 1: Start/Space
# Group 2: Optional Alef/Wasla (ا or ٱ)
# Group 3: Lam (ل)
# Group 4: Shamsi Letter
# Group 5: Intervening vowels
# Group 6: Shadda
SHAMSI_RE = re.compile(
    rf"(^|\s)([ٱا]?)(ل)([{SHAMSI_LETTERS}])([\u064B-\u0650\u0652-\u065F\u0670\u06E1]*)(\u0651)"
)

# --- 3. Shadda (Doubling) Logic ---
NON_DIACRITIC = r"[^\u064B-\u0652\u0670\u06E1\u0640]"
INTERVENING_DIACRITICS = r"[\u064B-\u0650\u0652-\u065F\u0670\u06E1]*"
SHADDA = "\u0651"
SHADDA_RE = re.compile(f"({NON_DIACRITIC})({INTERVENING_DIACRITICS}){SHADDA}")

# --- 4. Special Word Rules ---
# "Allah" Rule Regex:
# Captures preceding context (Char+Diacritic) to determine L/LL
# Group 1: Preceding Char
# Group 2: Preceding Diacritic
# Group 3: Space
# Group 4: The 'Allah' word itself (capturing it to check prefix)
# Group 5: Suffix Diacritic (on the Heh)
ALLAH_FULL_RE = re.compile(
    r"([\w])?"  # 1. Preceding Char
    r"([\u064B-\u0652\u0670\u06E1])?"  # 2. Preceding Diacritic
    r"(\s*)"  # 3. Space
    # Match 'Allah' variants.
    # 1. Starts with Alef/Wasla + L + opt diacritics + L (e.g. الله)
    # 2. Starts with L + opt diacritics + L (e.g. لِلَّهِ)
    # 3. Starts with L + Shadda (e.g. لّه)
    r"((?:(?:(?:ئە|ٱ|ا)ل[\u064B-\u065F\u0670]*ل?)|(?:ل[\u064B-\u065F\u0670]*ل)|(?:ل\u0651))(?:[\u064B-\u065F\u0670]*)(?:[\u0670\u0627]?)[هھە])"
    r"([\u064B-\u0652\u0670\u06E1])?"  # 5. Ending Diacritic
)

# Taa Marbuta with Diacritics regex
# Matches ة followed by a diacritic
TAA_MARBUTA_VOCALIZED_RE = re.compile(r"\u0629(?=[\u064B-\u0652])")

# --- 5. Ra (R) Tajweed Rules ---
# Heavy Letters (Tafkhim): خ ص ض غ ط ق ظ
HEAVY_LETTERS_SET = "خصضغطقظ"

# Rule A: Ra with Heavy Vowel (Fatha, Damma, Tanwin Fath, Tanwin Damm)
RA_HEAVY_VOWEL_RE = re.compile(r"ر(?=[\u064E\u064F\u064B\u064C])")

# Rule B: Ra with Sukun, preceded by Heavy Vowel (Fatha/Damma)
# Matches (Char + Fatha/Damma) + Ra + Sukun
RA_SUKUN_HEAVY_PREV_RE = re.compile(rf"({NON_DIACRITIC}[\u064E\u064F])ر(?=[\u0652])")

# Rule C: Mirsad Case (Ra with Sukun, Kasra before, Heavy Letter after)
# Matches (Char + Kasra) + Ra + Sukun(opt) + Heavy Letter
RA_MIRSAD_RE = re.compile(rf"({NON_DIACRITIC}\u0650)ر\u0652?([{HEAVY_LETTERS_SET}])")

# Rule D: End of Word after Long Alif
# Matches Alif + Ra + (Space/End/Punctuation)
RA_END_ALIF_RE = re.compile(r"(ا)ر(?=[\s\u06D6-\u06ED]|$)")

# --- 6. Alif Wasla (ٱ) Logic ---
ALEF_WASLA = "\u0671"
# Match Wasla OR Alef-before-Lam at the Start of Sentence or after Punctuation/Digits.
# Matches: Start (^) OR Punctuation OR Digit, followed by optional spaces, then Wasla OR Alef+Lam.
WASLA_START_RE = re.compile(r"(^|[\.!\?،؛؟:\"\'\(\)\[\]\{\}-]|\d)(\s*)(?:ٱ|ا(?=ل))")

# Regex for Silent Wasla/Alef (Internal)
# 1. Matches 'ا' (Alef) ONLY if preceded by SPACE and followed by Lam.
# 2. Matches 'ٱ' (Wasla) if preceded by any char (space optional).
WASLA_SILENT_RE = re.compile(
    r"(?:([^\W\d_]|[\u064B-\u0652\u0670\u06E1])(\s+)(ا)(?=ل))|(?:([^\W\d_]|[\u064B-\u0652\u0670\u06E1])(\s*)(ٱ))")

# --- 7. Redundant Alef after Tanween Logic ---
TANWEEN_ALEF_RE = re.compile(r"([\u064B\u064C\u064D])([\u06D6-\u06ED]*)[\u0627\u0671]")

# --- 8. Silent Alef after Waw (Quranic) ---
WAW_SILENT_ALEF_RE = re.compile(r"(و[\u064B-\u0652\u0670\u06E1]*)ا\u06DF")

# --- 9. Conversion Map ---
DIACRITIC_TO_LETTER_MAP = {
    # Vowels
    0x064E: "ە",  # Fatha  (َ ) -> ە
    0x064F: "و",  # Damma  (ُ ) -> و
    0x0650: "ی",  # Kasra  (ِ ) -> ی

    # Tanween (Nunation)
    0x064B: "ەن",  # Tanwin Fath (ً ) -> ەن
    0x064D: "ین",  # Tanwin Kasr (ٍ ) -> ین
    0x064C: "ون",  # Tanwin Damm (ٌ ) -> ون

    # Symbols
    0x0670: "ا",  # Dagger Alif (ٰ ) -> ا

    # Removals (Silent)
    0x0652: "",  # Sukun (ْ ) -> Remove
    0x06E1: "",  # Light Sukun (ۡ ) -> Remove
    0x0651: "",  # Shadda (Cleanup if missed)
    0x0622: "ا",  # Alif Madda -> Alef (Safety mapping)
}

# --- Add Quranic Symbols to Removal Map ---
for code in range(0x06D6, 0x06ED + 1):
    DIACRITIC_TO_LETTER_MAP[code] = ""

# Regex to detect if text has any diacritics/Quranic symbols
HAS_DIACRITICS_RE = re.compile(r"[\u064B-\u0652\u0670\u06E1\u06D6-\u06ED]")

ALL_DIACRITICS_RE = re.compile(r"[\u064B-\u0652\u0670\u06E1\u06D6-\u06ED]")
TATWEEL_RE = re.compile(r"\u0640")


def normalize_diacritics(text: str, mode: str = "convert", remove_tatweel: bool = True,
                         shadda_mode: str = "double") -> str:
    """
    Handles Arabic diacritics (Harakat) including Tajweed rules.
    """

    if remove_tatweel:
        text = TATWEEL_RE.sub('', text)

    if mode == "convert":

        # Check if the text contains diacritics.
        has_diacritics = bool(HAS_DIACRITICS_RE.search(text))

        if has_diacritics:
            # A. Handle Alif Wasla (ٱ) Logic (Strictly Wasla, no Alef)
            # 1. Silent Wasla (Continuation)
            def _silence_wasla(m):
                if m.group(3):  # Matched 'ا' case
                    return f"{m.group(1)}{m.group(2)}"
                else:  # Matched 'ٱ' case
                    return f"{m.group(4)}{m.group(5)}"

            text = WASLA_SILENT_RE.sub(_silence_wasla, text)

            # 2. Start Wasla
            text = WASLA_START_RE.sub(r"\1\2ئە", text)

            # 3. Cleanup remaining Wasla
            text = text.replace(ALEF_WASLA, "")

            # B. Handle "Allah" Context Rule
            def _replace_allah(m):
                prev_char = m.group(1) or ""
                prev_diacritic = m.group(2) or ""
                space = m.group(3) or ""
                full_word = m.group(4) or ""
                suffix_diacritic = m.group(5) or ""

                prefix_str = ""
                # Check if prev_char 'stole' the Alef/Wasla
                if prev_char in ["ا", "ٱ"] and full_word.startswith("ل"):
                    prefix_str = "ئە"
                    prev_char = ""  # Consume it
                elif full_word.startswith("ئە"):
                    prefix_str = "ئە"
                elif full_word.startswith("ٱ"):
                    prefix_str = "ئە"
                elif full_word.startswith("ا"):
                    prefix_str = "ئە"

                # Special Case: Lillahi (starts with Lam + Kasra)
                if full_word.startswith("ل\u0650"):
                    if shadda_mode == "double":
                        lam_str = "ل" * 2
                    else:
                        lam_str = "ل"
                    # "Li" -> "لی" + "llahi"
                    body = f"لی{lam_str}ا"
                    return f"{prev_char}{prev_diacritic}{space}{body}ھ{suffix_diacritic}"

                # Standard Logic
                if prefix_str:
                    lam = "ڵ"
                elif prev_diacritic in ["\u0650", "\u0652"] or prev_char in ["ی", "ي"]:
                    lam = "ل"
                else:
                    lam = "ڵ"

                if shadda_mode == "double":
                    lam_str = lam * 2
                else:
                    lam_str = lam

                body = f"{prefix_str}{lam_str}ا"
                return f"{prev_char}{prev_diacritic}{space}{body}ھ{suffix_diacritic}"

            text = ALLAH_FULL_RE.sub(_replace_allah, text)

            # C. Shamsi (Sun) Rule
            # Updated replacement indices due to new group in SHAMSI_RE
            # Group 1 (Start/Space) + Group 2 (Alef/Wasla) + Group 4 (Shamsi) + Group 5 (Vowels) + Group 6 (Shadda)
            # Skips Group 3 (Lam)
            text = SHAMSI_RE.sub(r"\1\2\4\5\6", text)

            # D. Apply Heavy Ra (ڕ) Rules
            text = RA_MIRSAD_RE.sub(r"\1ڕ\2", text)
            text = RA_HEAVY_VOWEL_RE.sub("ڕ", text)
            text = RA_SUKUN_HEAVY_PREV_RE.sub(r"\1ڕ", text)
            text = RA_END_ALIF_RE.sub(r"\1ڕ", text)

            # E. Tajweed Rules (Iqlab & Idgham)
            text = IQLAB_NUN_RE.sub(r"م\1ب", text)
            text = IQLAB_TANWEEN_FATH_RE.sub("\u064Eم\\1ب", text)
            text = IQLAB_TANWEEN_KASR_RE.sub("\u0650م\\1ب", text)
            text = IQLAB_TANWEEN_DAMM_RE.sub("\u064Fم\\1ب", text)

            text = IDGHAM_NUN_RE.sub(r"\2\1\2", text)
            text = IDGHAM_TANWEEN_FATH_RE.sub("\u064E\\2\\1\\2", text)
            text = IDGHAM_TANWEEN_KASR_RE.sub("\u0650\\2\\1\\2", text)
            text = IDGHAM_TANWEEN_DAMM_RE.sub("\u064F\\2\\1\\2", text)

            # F. Handle Shadda
            if shadda_mode == "double":
                text = SHADDA_RE.sub(r"\1\1\2", text)

            # G. Remove Redundant Vowels
            text = text.replace("\u064Eا", "ا").replace("ا\u064E", "ا")
            text = text.replace("\u064E\u0670", "\u0670").replace("\u0670\u064E", "\u0670")

            text = text.replace("\u0650ی", "ی").replace("ی\u0650", "ی")

            # Remove Alef after Kasra (فِى -> فی)
            text = text.replace("\u0650ا", "\u0650")

            text = text.replace("\u064Fو", "و").replace("و\u064F", "و")

            # Fix for 'أُ' -> 'ئە' + 'ُ' -> 'ئ' + 'ُ' -> 'ئو'
            text = text.replace("ئە\u064F", "ئ\u064F")

            # H. Remove Redundant Alef after Tanween
            text = TANWEEN_ALEF_RE.sub(r"\1\2", text)

            # I. Remove Silent Alef after Waw (Quranic)
            text = WAW_SILENT_ALEF_RE.sub(r"\1", text)

        # -- Logic for BOTH vocalized and unvocalized text --

        # Handle Taa Marbuta (ة)
        # Rule 1: If it has diacritics -> "ت"
        text = TAA_MARBUTA_VOCALIZED_RE.sub("ت", text)
        # Rule 2: If it has NO diacritics -> "ە"
        text = text.replace("\u0629", "ە")

        # Translate vowels/tanween/quranic_marks
        # (If has_diacritics is False, this just cleans up stray marks if any)
        text = text.translate(DIACRITIC_TO_LETTER_MAP)

        # Merge Duplicate Vowels
        text = re.sub(r"([اەۆێ])\1", r"\1", text)

    elif mode == "remove":
        text = ALL_DIACRITICS_RE.sub('', text)
        text = text.replace(ALEF_WASLA, "")
        text = text.replace("\u0629", "ە")

    return text