import re
from typing import List

from ckb_textify.core.types import Token, TokenType
from ckb_textify.modules.base import Module
from ckb_textify.utils.numbers import int_to_kurdish


class PhoneNormalizer(Module):
    """
    Parses and reads phone numbers in standard Iraqi format (4-3-2-2).
    Optionally inserts pause markers for TTS rhythm.
    """

    # Regex to pull parts out of a matched phone string
    # Group 1: Country Code (+964)
    # Group 2: Company Code (0750)
    # Group 3, 4, 5: Rest of digits
    PARSER_RE = re.compile(
        r"(?P<prefix>(?:\+|00)\s*964)?[\s-]*"
        r"(?P<code>0?7[5789]\d)[\s-]*"
        r"(?P<g1>\d{3})[\s-]*"
        r"(?P<g2>\d{2})[\s-]*"
        r"(?P<g3>\d{2})"
    )

    @property
    def name(self) -> str:
        return "PhoneNormalizer"

    @property
    def priority(self) -> int:
        return 95  # Very high priority (after Web)

    def process(self, tokens: List[Token]) -> List[Token]:
        if not self.config.enable_phone:
            return tokens

        pause = f" {self.config.pause_token} " if self.config.enable_pause_markers else " "

        for token in tokens:
            if token.type == TokenType.PHONE:
                match = self.PARSER_RE.search(token.text)
                if match:
                    parts = []

                    # 1. Country Code
                    prefix = match.group("prefix")
                    if prefix:
                        clean_prefix = prefix.replace(" ", "").replace("-", "")
                        if "+" in clean_prefix:
                            parts.append("کۆ")
                            parts.append(int_to_kurdish(964))
                        elif "00" in clean_prefix:
                            parts.append("سفر سفر")
                            parts.append(int_to_kurdish(964))

                    # 2. Company Code (0750 -> Sifir heft sed...)
                    code = match.group("code")
                    parts.append(self._read_group(code))

                    # 3. Digits Groups (3-2-2)
                    parts.append(self._read_group(match.group("g1")))
                    parts.append(self._read_group(match.group("g2")))
                    parts.append(self._read_group(match.group("g3")))

                    # Join parts with pause token if enabled, otherwise space
                    token.text = pause.join(parts)
                    token.type = TokenType.WORD  # Lock it

        return tokens

    def _read_group(self, num_str: str) -> str:
        """Reads a group of digits naturally (handling leading zero)."""
        if num_str.startswith("0") and len(num_str) > 1:
            try:
                val = int(num_str)
                # "0750" -> "sifir" + "750"
                return f"سفر {int_to_kurdish(val)}"
            except ValueError:
                return num_str

        try:
            return int_to_kurdish(int(num_str))
        except ValueError:
            return num_str