from typing import List
from ckb_textify.core.types import Token, TokenType
from ckb_textify.modules.base import Module


class GrammarNormalizer(Module):
    """
    Handles grammatical suffixes and attachment rules.
    Specifically handles the "Definite State" or "Copula" suffix (ە / ـە).

    Rule:
    - If the word ends in a vowel (ا, ە, ۆ, ێ), insert 'ی' -> "...یە"
    - Otherwise, append directly -> "...ە"
    """

    # Vowels that require a 'y' buffer before 'e'
    # User specified: ۆ ، ە، ێ، ا
    VOWELS_REQUIRING_Y = ('ا', 'ە', 'ۆ', 'ێ')

    # Target suffixes to attach
    SUFFIXES = {"ە", "ـە"}

    @property
    def name(self) -> str:
        return "GrammarNormalizer"

    @property
    def priority(self) -> int:
        # Run AFTER text conversion (Numbers=70, Transliteration=10)
        # But BEFORE Spacing (0). Priority 5 ensures it sees the final converted text.
        return 5

    def process(self, tokens: List[Token]) -> List[Token]:
        i = 0
        while i < len(tokens):
            token = tokens[i]

            # Check if this token is a suffix we need to attach
            if token.text in self.SUFFIXES:
                prev = self._get_prev(tokens, i)

                # We can only attach if there is a previous word
                if prev and prev.type != TokenType.UNKNOWN:
                    self._attach_suffix(prev, token)
                    # Mark current suffix token as consumed
                    token.text = ""
                    token.type = TokenType.UNKNOWN

                    # Ensure whitespace from the suffix is preserved on the main word
                    if token.whitespace_after:
                        prev.whitespace_after = (prev.whitespace_after or "") + token.whitespace_after

            i += 1

        # Filter out consumed tokens
        return [t for t in tokens if t.text]

    def _attach_suffix(self, base_token: Token, suffix_token: Token):
        text = base_token.text.strip()

        # Determine strict suffix form (normalize "ـە" to "ە")
        # The logic below handles the "y" insertion, so we effectively append "ە" or "یە"

        if text.endswith(self.VOWELS_REQUIRING_Y):
            # Case 1: Ends in specific vowel -> Add 'ی' + 'ە'
            # Example: نۆ (9) -> نۆیە
            base_token.text = text + "یە"
        else:
            # Case 2: Ends in consonant or other char -> Add 'ە'
            # Example: هەشت (8) -> هەشتە
            base_token.text = text + "ە"

        # No need to manually set is_converted; Token class handles it automatically
        # whenever text != original_text

    def _get_prev(self, tokens: List[Token], i: int) -> Token | None:
        return tokens[i - 1] if i > 0 else None