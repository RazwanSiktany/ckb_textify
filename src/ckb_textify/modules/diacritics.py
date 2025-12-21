import re
from typing import List

from ckb_textify.core.types import Token, TokenType
from ckb_textify.modules.base import Module
from ckb_textify.resources.dictionaries import MUQATTAAT_MAP

# --- GLOBAL CONSTANTS ---
# Y, R, M, L, W, N
YARMALOON_LETTERS = "يرملون"
# Consonants and Diacritics
NON_DIACRITIC = r"[^\u064B-\u0652\u0670\u06E1\u0640]"
INTERVENING_DIACRITICS = r"[\u064B-\u0650\u0652-\u065F\u0670\u06E1]*"
SHADDA = "\u0651"
ALEF_WASLA = "\u0671"
HEAVY_LETTERS_SET = "خصضغطقظ"  # For Ra rules
SHAMSI_LETTERS = "تثدذرزسشصضطظلن"

# --- Conversion Map ---
DIACRITIC_TO_LETTER_MAP = {
    # Vowels
    0x064E: "ە",  # Fatha
    0x064F: "و",  # Damma
    0x0650: "ی",  # Kasra

    # Tanween (Nunation)
    0x064B: "ەن",  # Tanwin Fath
    0x064D: "ین",  # Tanwin Kasr
    0x064C: "ون",  # Tanwin Damm

    # Symbols & Alifs (Updated per user request)
    0x0670: "ا",  # Dagger Alif (ٰ) -> ا
    0x0622: "ا",  # Alif Madda (آ) -> ا
    0x0649: "ی",  # Alif Maqsurah (ى) -> ا
    0xFE8D: "ا",  # Isolated Alif (ﺍ) -> ا
    0xFE8E: "ا",  # Final Alif (ﺎ) -> ا

    # Hamzas
    0x0623: "ئە",  # Alif Hamza Above (أ) -> ئە
    0x0625: "ئی",  # Alif Hamza Below (إ) -> ئی
    0x0621: "ئ",  # Standalone Hamza (ء) -> ئ
    0x0624: "وئ",  # Waw Hamza (ؤ) -> وئ
    0x0654: "ئ",  # Hamza Above (ٔ) -> ئ
    0x0655: "ئ",  # Hamza Below (ٕ) -> ئ

    # Removals/Ignored
    0x0652: "",  # Sukun (Silent)
    0x06E1: "",  # Light Sukun (Silent)
    0x0651: "",  # Shadda (Ignored in basic mode, removed)
    0x0653: "",  # Maddah Above (ٓ) -> Remove
    0x0671: "",  # Alif Wasla (ٱ) -> Removed (Handled by logic, fallback silent)
    0xFDF0: "",  # Alif variant isolated (ﭐ) -> silent
    0xFB51: "",  # Another Qur'anic alif variant (ﭑ) -> silent
}
# Add Quranic Symbols to Removal Map
for code in range(0x06D6, 0x06ED + 1):
    DIACRITIC_TO_LETTER_MAP[code] = ""


class DiacriticsNormalizer(Module):
    """
    Handles Arabic/Quranic Diacritics (Harakat) and Tajweed rules specific to Sorani Kurdish pronunciation.
    Converts vocalized Arabic into phonetic Kurdish/Sorani text for TTS/NLP.
    """
    # --- REGEX CONSTANTS ---
    # A. IQLAB
    IQLAB_NUN_RE = re.compile(r"ن\u0652(\s*)ب")
    IQLAB_TANWEEN_FATH_RE = re.compile(r"\u064B(\s*)ب")
    IQLAB_TANWEEN_KASR_RE = re.compile(r"\u064D(\s*)ب")
    IQLAB_TANWEEN_DAMM_RE = re.compile(r"\u064C(\s*)ب")

    # B. IDGHAM
    IDGHAM_NUN_RE = re.compile(rf"ن\u0652(\s*)([{YARMALOON_LETTERS}])")
    IDGHAM_TANWEEN_FATH_RE = re.compile(rf"\u064B(\s*)([{YARMALOON_LETTERS}])")
    IDGHAM_TANWEEN_KASR_RE = re.compile(rf"\u064D(\s*)([{YARMALOON_LETTERS}])")
    IDGHAM_TANWEEN_DAMM_RE = re.compile(rf"\u064C(\s*)([{YARMALOON_LETTERS}])")

    # B2. IDGHAM SHAFAWI (Mim Sakinah + Mim)
    # Merges Mim+Sukun into following Mim
    IDGHAM_MIM_RE = re.compile(r"م\u0652(\s*)م")

    # C. SHAMSI
    # Updated to include 'ئە' as a valid prefix, allowing assimilation even after Wasla conversion.
    SHAMSI_RE = re.compile(
        rf"(^|\s)((?:ئە|[ٱا])?)(ل)([{SHAMSI_LETTERS}])({INTERVENING_DIACRITICS})({SHADDA}?)"
    )

    # D. SHADDA
    SHADDA_RE = re.compile(f"({NON_DIACRITIC})({INTERVENING_DIACRITICS}){SHADDA}")

    # E. ALLAH
    # Updated Regex to capture preceding context within the string
    # Group 1: Preceding Char
    # Group 2: Preceding Diacritic
    # Group 3: Space
    # Group 4: The 'Allah' word itself (capturing it to check prefix)
    # Group 5: Suffix Diacritic (on the Heh)
    ALLAH_FULL_RE = re.compile(
        r"([\w])?"  # 1. Preceding Char
        r"([\u064B-\u0652\u0670\u06E1])?"  # 2. Preceding Diacritic
        r"(\s*)"  # 3. Space
        # 4. Body: Strict matching to avoid single Lam words like 'Lahum'
        # Matches:
        # A. (Alif/Wasla/Kurdish Alef) + Lam + (optional diacritics) + Lam
        # B. Lam + (optional diacritics) + Lam
        # REMOVED single Lam + Shadda branch to prevent 'Lahu' matching
        r"((?:(?:(?:ئە|ٱ|ا)ل[\u064B-\u065F\u0670]*ل)|(?:ل[\u064B-\u065F\u0670]*ل))(?:[\u064B-\u065F\u0670]*)(?:[\u0670\u0627]?)[هھە])"
        r"([\u064B-\u0652\u0670\u06E1])?"  # 5. Ending Diacritic
    )

    # F. TAA MARBUTA
    TAA_MARBUTA_VOCALIZED_RE = re.compile(r"\u0629(?=[\u064B-\u0652])")

    # G. RA RULES
    RA_HEAVY_VOWEL_RE = re.compile(r"ر(?=\u0651?[\u064E\u064F\u064B\u064C])")
    RA_SUKUN_HEAVY_PREV_RE = re.compile(rf"({NON_DIACRITIC}[\u064E\u064F])ر(?=[\u0652])")
    RA_MIRSAD_RE = re.compile(rf"({NON_DIACRITIC}\u0650)ر\u0652?([{HEAVY_LETTERS_SET}])")
    RA_END_ALIF_RE = re.compile(r"(ا)ر(?=[\s\u06D6-\u06ED]|$)")

    # H. WASLA
    WASLA_START_RE = re.compile(r"(^|[\.!\?،؛؟:\"\'\(\)\[\]\{\}-])(\s*)(?:ٱ|ا(?=ل))")
    WASLA_SILENT_RE = re.compile(
        r"(?:([^\W_]|[\u064B-\u0652\u0670\u06E1])(\s+)(ا)(?=ل))|(?:([^\W_]|[\u064B-\u0652\u0670\u06E1])(\s*)(ٱ))")

    # I. REDUNDANT ALEF
    # Updated to include \u0649 (Alif Maqsurah) so it is removed after Tanween
    TANWEEN_ALEF_RE = re.compile(r"([\u064B\u064C\u064D])([\u06D6-\u06ED]*)[\u0627\u0671\u0649]")

    # J. SILENT ALEF AFTER WAW
    # Updated: Now includes \u0653 (Maddah) in the allowed diacritics before the Alef
    WAW_SILENT_ALEF_RE = re.compile(r"(و[\u064B-\u0652\u0670\u06E1\u0653]*)ا\u06DF")

    # K. Detection Regexes
    HAS_DIACRITICS_RE = re.compile(r"[\u064B-\u0652\u0670\u06E1\u06D6-\u06ED]")
    ALL_DIACRITICS_RE = re.compile(r"[\u064B-\u0652\u0670\u06E1\u06D6-\u06ED]")
    TATWEEL_RE = re.compile(r"\u0640")

    @property
    def name(self) -> str:
        return "DiacriticsNormalizer"

    @property
    def priority(self) -> int:
        return 55

    def process(self, tokens: List[Token]) -> List[Token]:
        if not self.config.enable_diacritics:
            return tokens

        mode = self.config.diacritics_mode
        shadda_mode = self.config.shadda_mode

        for i, token in enumerate(tokens):
            if token.type == TokenType.WORD:
                token.text = self.TATWEEL_RE.sub('', token.text)

                # --- 1. Muqatta'at Check (High Priority) ---
                if token.text in MUQATTAAT_MAP:
                    token.text = MUQATTAAT_MAP[token.text]
                    token.type = TokenType.WORD
                    token.tags.add("MUQATTAAT")
                    continue
                # ---------------------------------------------

                if mode == "convert":
                    force_silent_wasla = False
                    force_light_lam = False

                    prev = self._get_prev(tokens, i)
                    if prev:
                        # Preceding word means Wasla should be silent
                        # Numbers do NOT silence Wasla (e.g. 1 Al-Hamd -> Yek E-lhamd)
                        # We check original_text for digits because NumberNormalizer changes type to WORD.
                        is_numeric = bool(re.search(r'\d', prev.original_text))

                        if (prev.type == TokenType.WORD or prev.is_converted) and not is_numeric:
                            force_silent_wasla = True

                        # Check previous token's original text for Kasra/Ya to force Light Lam
                        if prev.original_text:
                            # Use original text to check diacritics before they were converted away
                            has_kasra = "\u0650" in prev.original_text[-3:]
                            has_ya = prev.original_text.strip().endswith(("ي", "ی"))
                            if has_kasra or has_ya:
                                force_light_lam = True

                    token.text = self._normalize_text(
                        token.text,
                        force_silent_wasla,
                        force_light_lam,
                        shadda_mode
                    )

                elif mode == "remove":
                    token.text = self.ALL_DIACRITICS_RE.sub('', token.text)
                    token.text = token.text.replace(ALEF_WASLA, "").replace("\u0629", "ە")

        return tokens

    def _replace_allah(self, m: re.Match, force_light_lam: bool, force_silent_wasla: bool, shadda_mode: str) -> str:
        """
        Handles the complex heavy (ڵ) or light (ل) Lam in "Allah".
        Groups:
        1: Preceding Char
        2: Preceding Diacritic
        3: Space
        4: Full Word (e.g., للّٰه)
        5: Suffix Diacritics
        """
        prev_char = m.group(1) or ""
        prev_diacritic = m.group(2) or ""
        space = m.group(3) or ""
        full_word = m.group(4) or ""
        suffix_diacritics = m.group(5) or ""

        # Check if prev_char 'stole' the Alef/Wasla (regex artifact with [\w])
        has_initial_alef = False
        if prev_char in ["ا", "ٱ"] and full_word.startswith("ل"):
            has_initial_alef = True
            prev_char = ""  # Consume it
        elif full_word.startswith("ئە") or full_word.startswith("ٱ") or full_word.startswith("ا"):
            has_initial_alef = True

        # Check for explicit prefixes like 'لِ' (Li) - starts with Lam + Kasra
        if full_word.startswith("ل\u0650"):
            is_heavy = False
        # Check if external context (previous token) forces light Lam
        elif force_light_lam:
            is_heavy = False
        # Check if internal context (preceding char/diacritic in same token) forces Light Lam
        elif prev_diacritic in ["\u0650", "\u0652"] or prev_char in ["ی", "ي"]:
            is_heavy = False
        else:
            # Default or forced by Fatha/Damma/Start-of-word (Heavy)
            is_heavy = True

        lam_char = "ڵ" if is_heavy else "ل"

        # Apply Shadda doubling (Only applies to the core Lam)
        if shadda_mode == "double":
            lam_str = f"{lam_char}{SHADDA}"
        else:
            lam_str = lam_char

        # Reconstruct the output based on prefix type
        if has_initial_alef:
            # Case: الله / ٱللَّهِ
            # If force_silent_wasla is True (preceded by word), OR if there is an attached prefix (prev_char captured earlier),
            # we consume the Alif/Wasla (prefix is empty).
            # Otherwise (Start of sentence/token), we pronounce it 'ئە'
            if force_silent_wasla or (prev_char and prev_char.strip()):
                prefix_part = ""
            else:
                prefix_part = "ئە"

            output_body = f"{prefix_part}{lam_str}اھ"
        else:
            # Case: لله (Lillahi) -> The initial 'ل' must be included first, then the Light Lam
            # If it started with "Li" (Kasra), preserve the Li part.
            if full_word.startswith("ل\u0650"):
                output_body = f"لی{lam_str}اھ"
            else:
                output_body = f"{lam_str}اھ"

        return f"{prev_char}{prev_diacritic}{space}{output_body}{suffix_diacritics}"

    def _get_wasla_vowel(self, text: str) -> str:
        """
        Determines the pronunciation (ئە, ئی, ئو) for an Alef Wasla (ٱ) at the start of a word.
        """
        # 1. Definite Article (ٱل) -> Fatha 'ئە'
        if text.startswith(ALEF_WASLA + "ل"):
            return "ئە"

        # Remove diacritics for text comparisons
        skeleton = re.sub(r"[\u064B-\u065F\u0670\u06E1\u0651]", "", text)

        # 4. "Fake Damma" Verbs -> Kasra 'ئی'
        fake_damma = ["ٱبنوا", "ٱمشوا", "ٱقضوا", "ٱئتوز", "ٱمضوا", "ٱئتوا"]
        if any(skeleton.startswith(v) for v in fake_damma):
            return "ئی"

        # 4. Specific Nouns -> Kasra 'ئی'
        nouns = ["ٱبن", "ٱبنة", "ٱمرؤ", "ٱمرأة", "ٱثنين", "ٱثنتين", "ٱسم"]
        if any(skeleton.startswith(n) for n in nouns):
            return "ئی"

        # 2 & 3. Verb 3rd Letter Rule
        # Scan for the 3rd Arabic letter index
        letter_count = 0
        idx_3rd = -1

        for i, char in enumerate(text):
            # Check if char is a base letter (Alef to Ya) or special chars
            if 'ء' <= char <= 'ي' or char == 'ٱ':
                letter_count += 1
                if letter_count == 3:
                    idx_3rd = i
                    break

        # Check vowel on 3rd letter
        if idx_3rd != -1 and idx_3rd + 1 < len(text):
            next_char = text[idx_3rd + 1]
            if next_char == '\u064F':  # Damma
                return "ئو"

        # Default fallback -> Kasra 'ئی'
        return "ئی"

    def _normalize_text(self, text: str, force_silent_wasla: bool = False, force_light_lam: bool = False,
                        shadda_mode: str = "double") -> str:
        """
        Core normalization logic for diacritics and Tajweed rules.
        """
        text = self.TATWEEL_RE.sub('', text)
        has_diacritics = bool(self.HAS_DIACRITICS_RE.search(text))

        if not has_diacritics and not force_silent_wasla:
            return text

        # -- 1. Handle Allah Context Rule (Priority 1) --
        # We process this BEFORE generic Wasla removal to handle cases like "Bi-Allahi" vs "Bismillahi"
        def allah_replacer(m):
            return self._replace_allah(m, force_light_lam, force_silent_wasla, shadda_mode)

        text = self.ALLAH_FULL_RE.sub(allah_replacer, text)

        # -- 2. Handle Alif Wasla (ٱ) Logic --
        if force_silent_wasla:
            # 1. Force Silence Wasla/Alef (from previous word context)
            text = text.replace(ALEF_WASLA, "")
            text = re.sub(r"ا(?=ل[\u064B-\u065F\u0670]*\u0651)", "", text, 1)  # Silence Alef-Lam if needed
        else:
            # 2. Pronounce Start Wasla
            if text.startswith(ALEF_WASLA):
                vowel_prefix = self._get_wasla_vowel(text)
                text = vowel_prefix + text[1:]

            # 3. Fallback for internal sentence boundary Waslas
            text = self.WASLA_START_RE.sub(r"\1\2ئە", text)

        # Remove redundant ALLAH check that was here previously

        if has_diacritics:
            # C. Shamsi (Sun) Rule - Assimilates 'L'
            text = self.SHAMSI_RE.sub(r"\1\2\4\5\6", text)

            # D. Apply Heavy Ra (ڕ) Rules
            text = self.RA_MIRSAD_RE.sub(r"\1ڕ\2", text)
            text = self.RA_HEAVY_VOWEL_RE.sub("ڕ", text)
            text = self.RA_SUKUN_HEAVY_PREV_RE.sub(r"\1ڕ", text)
            text = self.RA_END_ALIF_RE.sub(r"\1ڕ", text)

            # E. Tajweed Rules (Iqlab & Idgham)
            text = self.IQLAB_NUN_RE.sub(r"م\1ب", text)
            text = self.IQLAB_TANWEEN_FATH_RE.sub("\u064Eم\\1ب", text)
            text = self.IQLAB_TANWEEN_KASR_RE.sub("\u0650م\\1ب", text)
            text = self.IQLAB_TANWEEN_DAMM_RE.sub("\u064Fم\\1ب", text)

            text = self.IDGHAM_NUN_RE.sub(r"\2\1\2", text)
            text = self.IDGHAM_TANWEEN_FATH_RE.sub("\u064E\\2\\1\\2", text)
            text = self.IDGHAM_TANWEEN_KASR_RE.sub("\u0650\\2\\1\\2", text)
            text = self.IDGHAM_TANWEEN_DAMM_RE.sub("\u064F\\2\\1\\2", text)

            # Idgham Shafawi (Mim + Mim) - remove Sukun to allow merge
            text = self.IDGHAM_MIM_RE.sub(r"م\1م", text)

            # F. Handle Shadda
            if shadda_mode == "double":
                text = self.SHADDA_RE.sub(r"\1\1\2", text)

            # G. Remove Redundant Vowels (Long Vowel extension rules)

            # Fix 0: Alif Hamza Above + Damma -> 'ئو'
            # Must run BEFORE Damma+Waw conversion to avoid breaking the sequence.
            text = text.replace("\u0623\u064F", "\u0621\u064F")

            # Quranic spelling: Waw followed by Dagger Alif usually pronounced as Alif (e.g. Salah, Zakat)
            # Moved up to ensure Fatha + Resulting Alif are merged
            text = text.replace("\u0648\u0670", "ا")

            # Fix 4: Alif Maqsurah followed by Tanween Damm or Kasr -> 'ی' (e.g. عمیٌ -> عومیون)
            text = re.sub(r"\u0649(?=[\u064C\u064D])", "ی", text)

            # Fix: Handle Hamza Above/Below Decomposed sequences
            text = re.sub(r"\u064E\u0654\u0627", "ئا", text)  # Fatha + Hamza Above + Alef -> ئا
            text = re.sub(r"\u0654\u0627", "ئا", text)  # Hamza Above + Alef -> ئا
            text = re.sub(r"\u064E\u0654", "ئە", text)  # Fatha + Hamza Above -> ئە

            # Fix 1: Fatha + Alif-type chars -> 'ا'
            # Covers: ا (0627), آ (0622), ى (0649), ٰ (0670), ﺍ (FE8D), ﺎ (FE8E)
            alif_pattern = r"[\u0627\u0622\u0649\u0670\uFE8D\uFE8E]"
            text = re.sub(f"\u064E({alif_pattern})", "ا", text)  # Fatha + Alif -> ا
            text = re.sub(f"({alif_pattern})\u064E", "ا", text)  # Alif + Fatha -> ا

            # Fix 2: Kasra + Ya -> 'ی'
            text = text.replace("\u0650ی", "ی").replace("ی\u0650", "ی")
            text = text.replace("\u0650ي", "ی").replace("ي\u0650", "ی")
            text = text.replace("\u0650\u0649", "ی")  # Fix for Kasra + Alif Maqsurah (e.g. فى -> فی)

            # Fix 3: Damma + Waw -> 'و'
            text = text.replace("\u064Fو", "و").replace("و\u064F", "و")

            # Misc fixes from before
            text = text.replace("\u0650ا", "\u0650")  # Remove Alef after Kasra
            text = text.replace("ئە\u064F", "ئ\u064F")  # Fix for 'أُ'
            text = text.replace("\u0625\u0650", "\u0625")  # Remove Kasra after Alef Hamza Below

            # H. Remove Redundant Alef after Tanween
            text = self.TANWEEN_ALEF_RE.sub(r"\1\2", text)

            # I. Remove Silent Alef after Waw (Quranic)
            text = self.WAW_SILENT_ALEF_RE.sub(r"\1", text)

        # -- Final Cleanup --

        # Handle Taa Marbuta (ة)
        text = self.TAA_MARBUTA_VOCALIZED_RE.sub("ت", text)
        text = text.replace("\u0629", "ە")

        # Translate vowels/tanween/quranic_marks
        text = text.translate(DIACRITIC_TO_LETTER_MAP)

        # Merge Duplicate Vowels
        text = re.sub(r"([اەۆێی])\1", r"\1", text)

        return text

    def _get_prev(self, tokens: List[Token], i: int) -> Token | None:
        """Helper to get the previous token."""
        return tokens[i - 1] if i > 0 else None