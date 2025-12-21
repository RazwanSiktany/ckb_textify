from typing import List

from ckb_textify.core.types import Token, TokenType
from ckb_textify.modules.base import Module
from ckb_textify.resources.dictionaries import ABBREVIATIONS, ARABIC_NAMES, CHAR_MAP


class LinguisticsNormalizer(Module):
    """
    Handles Text Cleanup, Arabic Names conversion, Abbreviations expansion,
    and general Unicode normalization specific to Sorani.
    """

    @property
    def name(self) -> str:
        return "LinguisticsNormalizer"

    @property
    def priority(self) -> int:
        return 50  # Default priority. Runs after major rigid patterns.

    def process(self, tokens: List[Token]) -> List[Token]:
        """Applies normalization rules to word tokens."""
        if not self.config.enable_linguistics:
            return tokens

        i = 0
        while i < len(tokens):
            token = tokens[i]

            # Skip consumed tokens
            if not token.text:
                i += 1
                continue

            if token.type == TokenType.WORD:
                text = token.text

                # --- 1. Abbreviations Logic ---
                # A. Check for Single Word Exact Match (e.g. "tb")
                if text in ABBREVIATIONS:
                    token.text = ABBREVIATIONS[text]
                    i += 1
                    continue

                # B. Greedy Multi-Token Lookahead
                # Scans ahead to match sequences like "د." or "پ.ز." or "ر.خ"
                # regardless of trailing dots, as long as they exist in the dictionary.

                matches = []
                current_key = text
                current_indices = []  # Indices consumed AFTER the initial token 'i'

                scan_idx = i

                while True:
                    next_idx = self._find_next_index(tokens, scan_idx)
                    if next_idx == -1:
                        break

                    next_token = tokens[next_idx]

                    # We extend the key if the next token is a dot or a word
                    # This allows constructing "Word.Word" or "Word.Word."
                    if next_token.text == "." or next_token.type == TokenType.WORD:
                        current_key += next_token.text
                        current_indices.append(next_idx)

                        if current_key in ABBREVIATIONS:
                            matches.append((current_key, list(current_indices)))

                        scan_idx = next_idx
                    else:
                        # Stop scanning if we hit something else (e.g. parens, numbers, symbols)
                        break

                if matches:
                    # Pick the longest match found
                    best_key, consumed_indices = matches[-1]

                    # DEFENSIVE CHECK: Currency Conflict (e.g. "د.ع")
                    # If the match is specifically "د." and the next token is "ع", skip it.
                    is_currency_conflict = False
                    if best_key == "د.":
                        last_used_idx = consumed_indices[-1]
                        check_idx = self._find_next_index(tokens, last_used_idx)
                        if check_idx != -1 and tokens[check_idx].text == "ع":
                            is_currency_conflict = True

                    if not is_currency_conflict:
                        token.text = ABBREVIATIONS[best_key]

                        # Preserve whitespace from the last token consumed
                        last_token_idx = consumed_indices[-1]
                        if tokens[last_token_idx].whitespace_after:
                            token.whitespace_after = tokens[last_token_idx].whitespace_after

                        # Consume tokens
                        for idx in consumed_indices:
                            tokens[idx].text = ""
                            tokens[idx].type = TokenType.UNKNOWN

                        i += 1
                        continue

                # --- 2. Arabic Name Lookup ---
                # Convert common Arabic names to their Sorani phonetic equivalents
                if text in ARABIC_NAMES:
                    token.text = ARABIC_NAMES[text]
                    i += 1
                    continue

                # --- 3. Unicode Normalization ---
                # Converts characters like 'ك' to 'ک' or 'ي' to 'ی'
                token.text = self._normalize_chars(text)

            i += 1

        # Filter out consumed dot tokens
        return [t for t in tokens if t.text]

    def _normalize_chars(self, text: str) -> str:
        """Applies character mapping (e.g., Arabic Kaf to Kurdish Kaf)."""
        res = []
        for char in text:
            res.append(CHAR_MAP.get(char, char))
        return "".join(res)

    def _get_next(self, tokens: List[Token], i: int) -> Token | None:
        """Helper to get the next token."""
        for j in range(i + 1, len(tokens)):
            if tokens[j].text:
                return tokens[j]
        return None

    def _find_next_index(self, tokens: List[Token], start_idx: int) -> int:
        """Helper to find index of next non-empty token."""
        for j in range(start_idx + 1, len(tokens)):
            if tokens[j].text:
                return j
        return -1