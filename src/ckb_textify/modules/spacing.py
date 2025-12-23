from typing import List
from ckb_textify.core.types import Token
from ckb_textify.modules.base import Module


class SpacingNormalizer(Module):
    """
    Final Reassembly Module (Layer 4).
    Guarantees a single space before and after any token that was converted
    from its original form (e.g., Number, Symbol, or Acronyms),
    while respecting punctuation rules (e.g. no space before period).
    """

    # Punctuation that should NOT have a space before it
    # Includes standard and Kurdish/Arabic variants just in case
    ATTACHED_PUNCTUATION = {".", ",", "!", "?", ":", ";", "،", "؟", ")", "]", "}", "”", "’", "%"}

    # Punctuation that should NOT have a space after it (Openers)
    OPEN_PUNCTUATION = {"(", "[", "{", "“", "‘", "\"", "'"}

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
                # Check next token to ensure we don't separate punctuation (e.g. "Word .")
                next_token = tokens[i+1] if i + 1 < len(tokens) else None
                should_add_space_after = True

                if next_token and next_token.text in self.ATTACHED_PUNCTUATION:
                    should_add_space_after = False

                # If passed checks, apply space (only if not already present)
                if should_add_space_after and not token.whitespace_after:
                    token.whitespace_after = " "

                # B. Add Space BEFORE this token
                # We do this by modifying the PREVIOUS token's whitespace
                if i > 0:
                    prev_token = tokens[i - 1]

                    # Don't add space if CURRENT token is attached punctuation (e.g. converted comma)
                    is_current_attached = token.text in self.ATTACHED_PUNCTUATION

                    # We check if the previous token ALREADY has spacing attached
                    if not prev_token.whitespace_after and not is_current_attached:

                        # Exception: Don't add space if previous token is an open bracket
                        if prev_token.text not in self.OPEN_PUNCTUATION:
                            prev_token.whitespace_after = " "

        return tokens