import re
from typing import List

from ckb_textify.core.types import Token, TokenType
from ckb_textify.resources.patterns import TOKENIZER_REGEX


class Tokenizer:
    """
    Converts raw text into a list of smart Token objects for the pipeline.
    Handles pre-processing like digit standardization and number/unit splitting.
    """
    # Regex to split Digit-Letter boundaries (e.g. "500gb" -> "500 gb")
    SPLIT_UNIT_RE = re.compile(r"(\d)(?!(?:e|E)[+-]?\d)([a-zA-Z\u0600-\u06FF])")

    # Regex to split Non-Latin Letter-Digit boundaries (e.g. "شاشە19" -> "شاشە 19")
    # We exclude Latin ([a-zA-Z]) to preserve things like "user123" or "MP3".
    SPLIT_NON_LATIN_DIGIT_RE = re.compile(r"([\u0600-\u06FF])(\d)")

    # Regex to split Text/Number from Superscripts/Subscripts
    POWER_CHARS = r"\u2070\u00B9\u00B2\u00B3\u2074-\u2079\u2080-\u2089"
    SPLIT_POWER_START_RE = re.compile(f"([^{POWER_CHARS}\\s])([{POWER_CHARS}])")
    SPLIT_POWER_END_RE = re.compile(f"([{POWER_CHARS}])([^{POWER_CHARS}\\s])")

    # FIX: Regex to split Numbers/Text from Unicode Fractions (½, ¼, ¾, etc.)
    # Expanded Unicode Number Forms block:
    # \u00BC-\u00BE (¼, ½, ¾)
    # \u2150-\u215E (⅐, ⅑, ⅒, ⅓, ⅔, ⅕, ⅖, ⅗, ⅘, ⅙, ⅚, ⅛, ⅜, ⅝, ⅞)
    # \u2189 (↉)
    FRACTION_CHARS = r"\u00BC-\u00BE\u2150-\u215E\u2189"
    SPLIT_FRACTION_START_RE = re.compile(f"([^{FRACTION_CHARS}\\s])([{FRACTION_CHARS}])")
    SPLIT_FRACTION_END_RE = re.compile(f"([{FRACTION_CHARS}])([^{FRACTION_CHARS}\\s])")

    def tokenize(self, text: str) -> List[Token]:
        # 1. Standardize Digits
        text = self._standardize_digits(text)

        # 2. Split Numbers from Units (Digit -> Letter)
        text = self.SPLIT_UNIT_RE.sub(r"\1 \2", text)

        # 3. Split Non-Latin Text from Numbers (Letter -> Digit)
        # This handles cases like "شاشە19" -> "شاشە 19" while ignoring "user123"
        text = self.SPLIT_NON_LATIN_DIGIT_RE.sub(r"\1 \2", text)

        # 4. Split Powers (x³ -> x ³)
        text = self.SPLIT_POWER_START_RE.sub(r"\1 \2", text)
        text = self.SPLIT_POWER_END_RE.sub(r"\1 \2", text)

        # 5. FIX: Split Fractions (5½ -> 5 ½)
        text = self.SPLIT_FRACTION_START_RE.sub(r"\1 \2", text)
        text = self.SPLIT_FRACTION_END_RE.sub(r"\1 \2", text)

        tokens = []
        last_end = 0

        for match in TOKENIZER_REGEX.finditer(text):
            start, end = match.span()
            whitespace = text[last_end:start] if start > last_end else ""

            kind = match.lastgroup
            value = match.group()

            token_type = TokenType.UNKNOWN
            if kind == "URL": token_type = TokenType.URL
            elif kind == "EMAIL": token_type = TokenType.EMAIL
            elif kind == "PHONE": token_type = TokenType.PHONE
            elif kind == "DATE": token_type = TokenType.DATE
            elif kind == "TIME": token_type = TokenType.TIME
            elif kind == "TECHNICAL": token_type = TokenType.TECHNICAL
            elif kind == "UNIT_SPECIAL": token_type = TokenType.WORD
            elif kind == "SUBSCRIPT": token_type = TokenType.SUBSCRIPT
            elif kind == "SUPERSCRIPT": token_type = TokenType.SUPERSCRIPT
            elif kind == "NUMBER": token_type = TokenType.NUMBER
            elif kind == "WORD": token_type = TokenType.WORD
            elif kind == "SYMBOL": token_type = TokenType.SYMBOL

            token = Token(text=value, original_text=value, type=token_type)
            if tokens: tokens[-1].whitespace_after = whitespace
            tokens.append(token)
            last_end = end

        if last_end < len(text):
            trailing_ws = text[last_end:]
            if tokens: tokens[-1].whitespace_after = trailing_ws

        return tokens

    def detokenize(self, tokens: List[Token]) -> str:
        result = []
        for token in tokens:
            result.append(token.text)
            result.append(token.whitespace_after)
        return "".join(result)

    def _standardize_digits(self, text: str) -> str:
        arabic_digits = '٠١٢٣٤٥٦٧٨٩'
        persian_digits = '۰۱۲۳۴۵۶۷۸۹'
        translation_table = str.maketrans(arabic_digits + persian_digits, '0123456789' * 2)
        return text.translate(translation_table)