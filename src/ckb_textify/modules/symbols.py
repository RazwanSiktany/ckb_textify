from typing import List
import re
from ckb_textify.core.types import Token, TokenType
from ckb_textify.modules.base import Module
from ckb_textify.utils.numbers import int_to_kurdish
from ckb_textify.resources.transliteration_maps import CUSTOM_CHAR_MAP


class SymbolNormalizer(Module):
    """
    Handles Punctuation, converts non-mathematical spoken symbols,
    and performs final cleanup based on strict TTS requirements:
    1. Normalize necessary punctuation (، ؟) -> (, ?)
    2. Keep only (. , ! ? :)
    3. Remove everything else (Brackets, obscure symbols)
    4. Convert any surviving raw digits to text.
    """

    # --- Spoken Symbols (Converted to words) ---
    SPOKEN_SYMBOLS_MAP = {
        "&": "و",
        "_": "ئەندەرسکۆڕ",
        "~": "نزیکەی",
        "≈": "نزیکەی",
        "=": "یەکسانە بە",
        "+": "لەگەڵ",
        "-": "داش",
        "*": "کەڕەتی",
        "×": "کەڕەتی",
        "/": "دابەش",
        "÷": "دابەش",
        "±": "کەم کۆ",
        "√": "ڕەگی دووجای",
        "@": "ئەت",
        "%": "لەسەدا",
        "#": "ھاشتاگ",
        "^": "توان",
    }

    # --- Punctuation Normalization Map ---
    PUNCTUATION_NORM_MAP = {
        '،': ',',
        '٬': ',',
        '؟': '?',
    }

    # --- Allowed Punctuation for TTS ---
    # FIX: Added '|' to allow pause markers through the cleanup
    ALLOWED_PUNCTUATION = {".", ",", "!", "?", ":", "|"}

    @property
    def name(self) -> str:
        return "SymbolNormalizer"

    @property
    def priority(self) -> int:
        return 40

    def process(self, tokens: List[Token]) -> List[Token]:
        new_tokens = []

        # Regex for ANY valid character we want to keep AS IS.
        # Includes:
        # - Latin, Digits, Arabic/Kurdish
        # - CJK (\u4E00-\u9FFF)
        # - Hiragana (\u3040-\u309F) & Katakana (\u30A0-\u30FF)  <-- ADDED
        # - Hangul (\uAC00-\uD7AF) & Jamo (\u1100-\u11FF)       <-- ADDED
        # - Greek, Cyrillic
        # - Punctuation, Whitespace
        # - Emojis & Symbols
        VALID_CHAR_RE = re.compile(
            r"["
            r"a-zA-Z0-9"
            r"\u0080-\u02AF"  # Latin Extended & IPA
            r"\u0300-\u036F"  # Combining Diacritics
            r"\u0370-\u03FF"  # Greek
            r"\u0400-\u04FF"  # Cyrillic
            r"\u0600-\u06FF"  # Arabic/Kurdish
            r"\u1E00-\u1EFF"  # Latin Extended Additional
            r"\u2300-\u23FF"  # Misc Technical
            r"\u2600-\u27BF"  # Misc Symbols
            r"\u4E00-\u9FFF"  # CJK Unified Ideographs
            r"\u3040-\u309F"  # Hiragana
            r"\u30A0-\u30FF"  # Katakana
            r"\uAC00-\uD7AF"  # Hangul Syllables
            r"\u1100-\u11FF"  # Hangul Jamo
            r"\uFE00-\uFE0F"  # Variation Selectors
            r"\U00010000-\U0010FFFF"  # Supplementary Planes (Emojis)
            r"\u2070-\u209F"  # Superscripts/Subscripts
            r"\u00B2\u00B3\u00B9"  # Specific Superscripts
            r"\u00BC-\u00BE\u2150-\u215E\u2189"  # Fractions
            r"\.\,\!\?\:\|\s"  # Punctuation & Whitespace
            r"]"
        )

        for i, token in enumerate(tokens):

            # --- Rule 1: Spoken Symbols ---
            if token.text in self.SPOKEN_SYMBOLS_MAP:
                converted_text = self.SPOKEN_SYMBOLS_MAP[token.text]
                if converted_text.strip() == " ":
                    token.text = converted_text
                elif converted_text.strip() == "و":
                    token.text = " و "
                else:
                    token.text = f" {converted_text} "

                token.type = TokenType.WORD
                token.whitespace_after = " "

                if i > 0 and not tokens[i - 1].whitespace_after.strip():
                    if tokens[i - 1].text not in ["(", "[", "{", "“", '"']:
                        tokens[i - 1].whitespace_after = " "

                new_tokens.append(token)
                continue

            # --- Rule 2: Normalization & Filtering ---
            text = token.text
            text = self.PUNCTUATION_NORM_MAP.get(text, text)

            # SYMBOL type check
            if token.type == TokenType.SYMBOL:
                # Keep allowed punctuation OR Emojis that were tokenized as symbols
                if text in self.ALLOWED_PUNCTUATION or VALID_CHAR_RE.match(text):
                    token.text = text
                    new_tokens.append(token)
                else:
                    self._preserve_spacing(new_tokens, token)
                    token.text = ""
                continue

            # WORD/NUMBER type cleaning
            cleaned_parts = []
            for char in text:
                # 1. Keep if it is in our CUSTOM mapping (e.g. ß, ç, é)
                if char in CUSTOM_CHAR_MAP or char.lower() in CUSTOM_CHAR_MAP:
                    cleaned_parts.append(char)
                # 2. Keep if it matches standard valid regex
                elif VALID_CHAR_RE.match(char):
                    cleaned_parts.append(char)

            cleaned_text = "".join(cleaned_parts)
            cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()

            # Safety Check: If the token contains ONLY Variation Selectors
            if not cleaned_text.strip(
                    "\uFE00\uFE01\uFE02\uFE03\uFE04\uFE05\uFE06\uFE07\uFE08\uFE09\uFE0A\uFE0B\uFE0C\uFE0D\uFE0E\uFE0F"):
                self._preserve_spacing(new_tokens, token)
                token.text = ""
                continue

            if not cleaned_text:
                self._preserve_spacing(new_tokens, token)
                token.text = ""
                continue

            # --- Rule 3: Digits Fallback ---
            def _replace_num(m):
                try:
                    return int_to_kurdish(int(m.group(0)))
                except:
                    return m.group(0)

            cleaned_text = re.sub(r'\b\d+\b', _replace_num, cleaned_text)

            token.text = cleaned_text
            new_tokens.append(token)

        return [t for t in new_tokens if t.text.strip() or t.whitespace_after]

    def _preserve_spacing(self, new_tokens: List[Token], current_token: Token):
        if new_tokens:
            if current_token.whitespace_after:
                new_tokens[-1].whitespace_after = (new_tokens[
                                                       -1].whitespace_after or "") + current_token.whitespace_after
            elif not new_tokens[-1].whitespace_after:
                new_tokens[-1].whitespace_after = " "