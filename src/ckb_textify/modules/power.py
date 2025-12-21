import re
from typing import List

from ckb_textify.core.types import Token, TokenType
from ckb_textify.modules.base import Module
from ckb_textify.utils.numbers import int_to_kurdish


class PowerNormalizer(Module):
    """
    Handles Unicode Superscripts (Powers) and Subscripts (Bases).
    - Superscripts (e.g. ², ¹⁰):
        - If attached to a Unit -> SKIP (Let UnitNormalizer handle it)
        - Else -> "tawan" (e.g. 5² -> pênc tawan duu)
    - Subscripts (e.g. ₂, ₁₀):
        - Always -> "binçîne" (e.g. log₁₀ -> log binçîne de)
    """

    # Digit Maps using explicit unicode escapes to avoid encoding issues
    SUBSCRIPT_DIGITS = str.maketrans(
        "\u2080\u2081\u2082\u2083\u2084\u2085\u2086\u2087\u2088\u2089",
        "0123456789"
    )
    SUPERSCRIPT_DIGITS = str.maketrans(
        "\u2070\u00B9\u00B2\u00B3\u2074\u2075\u2076\u2077\u2078\u2079",
        "0123456789"
    )

    # Regex to validate purely sub/superscript strings
    SUBSCRIPT_RE = re.compile(r"^[\u2080-\u2089]+$")
    SUPERSCRIPT_RE = re.compile(r"^[\u2070\u00B9\u00B2\u00B3\u2074-\u2079]+$")

    @property
    def name(self) -> str:
        return "PowerNormalizer"

    @property
    def priority(self) -> int:
        return 65  # Run after Numbers/Units (60/70) but before Symbols (40)

    def process(self, tokens: List[Token]) -> List[Token]:
        i = 0
        while i < len(tokens):
            token = tokens[i]

            # --- Handle Subscripts (Base) ---
            if (hasattr(token.type, 'name') and token.type.name == 'SUBSCRIPT') or \
                    (token.type in (TokenType.SYMBOL, TokenType.UNKNOWN, TokenType.WORD) and self.SUBSCRIPT_RE.match(
                        token.text)):

                ascii_digits = token.text.translate(self.SUBSCRIPT_DIGITS)
                if ascii_digits.isdigit():
                    try:
                        val = int(ascii_digits)
                        text_val = int_to_kurdish(val)
                        token.text = f"بنچینە {text_val}"
                        token.type = TokenType.WORD
                        token.whitespace_after = " "
                        token.tags.add("MATH_TERM")  # FIX: Tag as math term for MathNormalizer context

                        prev = self._get_prev(tokens, i)
                        if prev and not prev.whitespace_after:
                            prev.whitespace_after = " "
                    except ValueError:
                        pass
                i += 1
                continue

            # --- Handle Superscripts (Power/Ja) ---
            if (hasattr(token.type, 'name') and token.type.name == 'SUPERSCRIPT') or \
                    (token.type in (TokenType.SYMBOL, TokenType.UNKNOWN, TokenType.WORD) and self.SUPERSCRIPT_RE.match(
                        token.text)):

                prev = self._get_prev(tokens, i)
                is_unit_context = False

                if prev:
                    if "IS_UNIT" in prev.tags or "UNIT_PROCESSED" in prev.tags:
                        is_unit_context = True
                    elif prev.type == TokenType.WORD and (
                            prev.text.endswith("مەتر") or
                            prev.text.endswith("گرام") or
                            prev.text.endswith("لیتر") or
                            prev.text.endswith("چرکە")
                    ):
                        is_unit_context = True

                if is_unit_context:
                    i += 1
                    continue

                ascii_digits = token.text.translate(self.SUPERSCRIPT_DIGITS)
                if ascii_digits.isdigit():
                    try:
                        val = int(ascii_digits)
                        text_val = int_to_kurdish(val)

                        token.text = f"توان {text_val}"
                        token.type = TokenType.WORD
                        token.whitespace_after = " "
                        token.tags.add("MATH_TERM")  # FIX: Tag as math term

                        if prev and not prev.whitespace_after:
                            prev.whitespace_after = " "
                    except ValueError:
                        pass

                i += 1
                continue

            i += 1

        return tokens

    def _get_prev(self, tokens: List[Token], i: int) -> Token | None:
        return tokens[i - 1] if i > 0 else None

    def _apply_izhafa(self, text: str) -> str:
        """Adds 'i' or 'y' for possession/connection (e.g. Metr -> Metri)."""
        if text.endswith(('ا', 'ە', 'ێ', 'ۆ', 'و', 'ی')):
            return text + "ی"
        return text + "ی"