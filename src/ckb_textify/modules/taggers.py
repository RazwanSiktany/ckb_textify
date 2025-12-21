import re
from typing import List

from ckb_textify.core.types import Token, TokenType
from ckb_textify.modules.base import Module
from ckb_textify.resources.patterns import UNIT_PATTERN


class ScriptTagger(Module):
    """
    Identifies the script of WORD tokens (Latin vs Arabic/Kurdish).
    """

    ARABIC_CHAR_RE = re.compile(r"[\u0600-\u06FF]")

    @property
    def name(self) -> str:
        return "ScriptTagger"

    @property
    def priority(self) -> int:
        return 50  # Run mid-stream

    def process(self, tokens: List[Token]) -> List[Token]:
        for token in tokens:
            if token.type == TokenType.WORD:
                if self.ARABIC_CHAR_RE.search(token.text):
                    token.tags.add("SCRIPT_KURDISH")
                else:
                    token.tags.add("SCRIPT_LATIN")
        return tokens


class UnitTagger(Module):
    """
    Context-Aware Tagger for Measurement Units.
    Rule 1: 'm' is a UNIT if it follows a NUMBER.
    Rule 2: 'm' is a UNIT if it is followed by a SUPERSCRIPT (e.g. m³).
    """

    UNIT_RE = re.compile(UNIT_PATTERN, re.VERBOSE | re.IGNORECASE)
    # Simple check for superscript chars if token type check fails or isn't available
    SUPERSCRIPT_CHAR_RE = re.compile(r"^[\u2070\u00B9\u00B2\u00B3\u2074-\u2079]+$")

    @property
    def name(self) -> str:
        return "UnitTagger"

    @property
    def priority(self) -> int:
        # Priority 85: Runs before MathNormalizer (80) & PowerNormalizer (65)
        return 85

    def process(self, tokens: List[Token]) -> List[Token]:
        for i, token in enumerate(tokens):
            if token.type == TokenType.WORD and self.UNIT_RE.fullmatch(token.text):

                # Rule 1: Preceded by Number
                prev_token = self._get_prev_meaningful_token(tokens, i)
                if prev_token and prev_token.type == TokenType.NUMBER:
                    token.tags.add("IS_UNIT")
                    continue

                # Rule 2: Followed by Superscript (e.g. m³)
                next_token = self._get_next(tokens, i)
                if next_token:
                    is_superscript = (next_token.type == TokenType.SUPERSCRIPT) or \
                                     (next_token.type in (TokenType.SYMBOL,
                                                          TokenType.UNKNOWN) and self.SUPERSCRIPT_CHAR_RE.match(
                                         next_token.text))

                    if is_superscript:
                        token.tags.add("IS_UNIT")
                        continue

        return tokens

    def _get_prev_meaningful_token(self, tokens: List[Token], current_index: int):
        if current_index > 0:
            return tokens[current_index - 1]
        return None

    def _get_next(self, tokens: List[Token], i: int) -> Token | None:
        return tokens[i + 1] if i < len(tokens) - 1 else None