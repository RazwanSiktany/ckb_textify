from typing import List
from ckb_textify.core.types import Token
from ckb_textify.modules.base import Module


class SpacingNormalizer(Module):
    """
    Final Reassembly Module (Layer 4).
    Guarantees a single space before and after any token that was converted
    from its original form (e.g., Number, Symbol, or Acronyms).
    """

    @property
    def name(self) -> str:
        return "SpacingNormalizer"

    @property
    def priority(self) -> int:
        return 0  # Run LAST (lowest priority)

    def process(self, tokens: List[Token]) -> List[Token]:
        for i, token in enumerate(tokens):

            # We only care about tokens that actually changed content.
            if token.is_converted:

                # A. Add Space AFTER this token
                # This fixes the "X + Y" -> "XکۆY" problem.
                if not token.whitespace_after:
                    token.whitespace_after = " "

                # B. Add Space BEFORE this token
                # We do this by modifying the PREVIOUS token's whitespace
                if i > 0:
                    prev_token = tokens[i - 1]

                    # We check if the previous token ALREADY has spacing attached
                    if not prev_token.whitespace_after:

                        # Optimization/Exception: Don't add space if previous token is an open bracket
                        if prev_token.text not in ["(", "[", "{", "”", "“", '"']:
                            prev_token.whitespace_after = " "

        return tokens