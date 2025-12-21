from typing import List, Tuple
from ckb_textify.core.types import Token, TokenType
from ckb_textify.modules.base import Module
from ckb_textify.utils.numbers import int_to_kurdish
from ckb_textify.resources.patterns import SUFFIXES_LIST


class CurrencyNormalizer(Module):
    """
    Handles currency symbols ($) and codes (IQD / د.ع) and converts the associated
    numerical value into Sorani Kurdish spelled-out text.
    Also handles standalone currency symbols.
    """

    # Map: Symbol/Code -> (Main Unit Kurdish Name, Sub Unit Kurdish Name, Sub Unit Factor)
    CURRENCY_MAP = {
        "IQD": ("دیناری عێڕاقی", "فلس", 1000),
        "د.ع": ("دیناری عێڕاقی", "فلس", 1000),  # Included for context, but handled as split tokens
        "$": ("دۆلار", "سەنت", 100),
        "USD": ("دۆلار", "سەنت", 100),
        "€": ("یۆرۆ", "سەنت", 100),
        "EUR": ("یۆرۆ", "سەنت", 100),
        "£": ("پاوەند", "پێنس", 100),
        "GBP": ("پاوەند", "پێنس", 100),
        "¥": ("یەن", "سێن", 100),
        "JPY": ("یەن", "سێن", 100),
    }

    # Sort suffixes by length for correct matching
    SUFFIXES = sorted(SUFFIXES_LIST, key=len, reverse=True)

    @property
    def name(self) -> str:
        return "CurrencyNormalizer"

    @property
    def priority(self) -> int:
        return 75  # Run before generic NumberNormalizer (70) and Linguistics (50)

    def process(self, tokens: List[Token]) -> List[Token]:
        """Iterates through tokens to find and convert currency patterns."""
        if not self.config.enable_currency:
            return tokens

        i = 0
        while i < len(tokens):
            token = tokens[i]

            # Skip empty tokens
            if not token.text:
                i += 1
                continue

            # --- 1. Multi-Token Iraqi Dinar (Number + د . ع) Check ---
            # (No suffix logic needed here as 'ع' is rarely suffixed in this specific context)
            if token.type == TokenType.NUMBER:
                next_d = self._get_next(tokens, i)
                next_dot = self._get_next(tokens, i + 1)
                next_ayn = self._get_next(tokens, i + 2)

                if next_d and next_d.text == "د" and \
                        next_dot and next_dot.text == "." and \
                        next_ayn and next_ayn.text == "ع":
                    currency_info = self.CURRENCY_MAP["IQD"]
                    self._convert_currency(token, next_d, currency_info)  # Pass 'next_d' as symbol placeholder

                    # Consume the three currency symbol tokens and preserve their whitespace
                    for t_consumed in [next_d, next_dot, next_ayn]:
                        if t_consumed.whitespace_after:
                            token.whitespace_after = (token.whitespace_after or "") + t_consumed.whitespace_after
                        t_consumed.text = ""

                    i += 3
                    continue

            # --- 2. Standalone Multi-Token Iraqi Dinar (د . ع) Check ---
            if token.text == "د":
                next_dot = self._get_next(tokens, i)
                next_ayn = self._get_next(tokens, i + 1)

                if next_dot and next_dot.text == "." and next_ayn and next_ayn.text == "ع":
                    currency_info = self.CURRENCY_MAP["IQD"]
                    main_unit, _, _ = currency_info

                    token.text = main_unit
                    token.type = TokenType.WORD
                    token.whitespace_after = " "

                    # Consume and preserve whitespace
                    for t_consumed in [next_dot, next_ayn]:
                        if t_consumed.whitespace_after:
                            token.whitespace_after = (token.whitespace_after or "") + t_consumed.whitespace_after
                        t_consumed.text = ""

                    i += 2
                    continue

            # --- 3. Standard Currency Check (IQD, $, USD) ---
            # Detect Suffix (e.g. IQDە -> IQD + ە)
            core_currency = token.text
            suffix_found = ""

            if token.text not in self.CURRENCY_MAP:
                core_currency, suffix_found = self._extract_suffix(token.text)

            if core_currency in self.CURRENCY_MAP:
                currency_info = self.CURRENCY_MAP[core_currency]
                currency_handled = False

                # Case A: [Number] [Currency] (e.g. 25000 IQD)
                prev = self._get_prev(tokens, i)
                if prev and prev.type == TokenType.NUMBER and prev.text:
                    # Pass suffix_found to handle it properly (don't delete the token completely if suffix exists)
                    self._convert_currency(prev, token, currency_info, suffix_found)
                    currency_handled = True

                # Case B: [Currency] [Number] (e.g. $ 100)
                # Suffixes on the prefix symbol are rare ($ە 100?) but we handle them by ignoring suffix for now or treating as word
                elif not currency_handled:
                    next_t = self._get_next(tokens, i)
                    if next_t and next_t.type == TokenType.NUMBER and next_t.text:
                        self._convert_currency(next_t, token, currency_info, suffix_found)
                        currency_handled = True

                # Case C: Standalone Symbol (e.g. "Price in $")
                if not currency_handled:
                    main_unit, _, _ = currency_info
                    token.text = main_unit
                    token.type = TokenType.WORD
                    token.whitespace_after = " "

                    # If we found a suffix on a standalone currency (e.g. IQDە -> Dinari Iraqiye)
                    # We insert the suffix as a new token so GrammarNormalizer can pick it up
                    if suffix_found:
                        # Insert suffix token next
                        # Since we are iterating with 'while', inserting changes indices.
                        # Easier strategy: Append suffix to whitespace or rely on GrammarNormalizer?
                        # GrammarNormalizer needs a separate token.
                        # We can just change CURRENT token to "Dinari Iraqi" and INSERT suffix next.

                        # However, strictly splitting token in loop is complex.
                        # Alternative: Just handle grammar here for standalone case.
                        # But GrammarNormalizer logic (vowel check) is best kept there.

                        # Let's use the same trick as Case A: keep the token alive as the suffix.
                        # But wait, 'token' IS the currency word here.
                        # So we set token.text = main_unit.
                        # And we need to ADD the suffix.
                        # Ideally, we insert a token.
                        tokens.insert(i + 1, Token(suffix_found, suffix_found, TokenType.WORD,
                                                   whitespace_after=token.whitespace_after))
                        token.whitespace_after = ""  # Connect immediate
                        # We increment i once more to skip the inserted suffix in next loop (it's a suffix, Currency won't match it)
                        # But suffix 'ە' is not in CURRENCY_MAP, so next loop will just skip it.
                        pass

            i += 1

        # Filter out consumed tokens (text is empty)
        return [t for t in tokens if t.text]

    def _extract_suffix(self, text: str) -> Tuple[str, str]:
        """Peels off grammar suffixes to find the currency code."""
        # Clean ZWNJ
        clean_text = text.replace('ـ', '')
        for sfx in self.SUFFIXES:
            if clean_text.endswith(sfx):
                potential_core = clean_text[:-len(sfx)]
                if potential_core in self.CURRENCY_MAP:
                    return potential_core, sfx
        return text, ""

    def _convert_currency(self, number_token: Token, symbol_token: Token, info: Tuple[str, str, int], suffix: str = ""):
        """Converts the numerical token to Kurdish text using the currency info."""
        main_unit, sub_unit, factor = info

        clean_text = number_token.text.replace(",", "")

        try:
            val = float(clean_text)
        except ValueError:
            return

        integer_part = int(val)
        decimal_val = round((val - integer_part) * factor)

        text_parts = []

        if integer_part > 0 or decimal_val == 0:
            text_parts.append(f"{int_to_kurdish(integer_part)} {main_unit}")

        if decimal_val > 0:
            if text_parts and not text_parts[-1].endswith((" و ")):
                text_parts.append(" و ")
            text_parts.append(f"{int_to_kurdish(decimal_val)} {sub_unit}")

        number_token.text = "".join(text_parts)
        number_token.type = TokenType.WORD
        number_token.tags.add("CURRENCY")

        # Preserve whitespace from the consumed symbol token
        if symbol_token.whitespace_after:
            number_token.whitespace_after = (number_token.whitespace_after or "") + symbol_token.whitespace_after

        # Handle the symbol token:
        # If there was a suffix (e.g. IQDە), the symbol token becomes the suffix ("ە").
        # GrammarNormalizer will later see [Number converted...] + [Suffix] and merge them.
        if suffix:
            symbol_token.text = suffix
            symbol_token.type = TokenType.WORD
            # Remove whitespace before suffix to ensure attachment
            # (The number token's whitespace_after + suffix)
            # Actually, GrammarNormalizer expects the previous token to have whitespace?
            # No, GrammarNormalizer consumes whitespace.
            # But we want: "5000 IQDە" -> "Penc... Iraqi" + "ە".
            # They should be adjacent or close.
            # We already appended symbol_token.whitespace_after to number_token.
            # We should probably clear number_token.whitespace_after if we want tight binding,
            # but GrammarNormalizer handles " " or "" via _attach_suffix.
            pass
        else:
            # Mark as consumed
            symbol_token.text = ""

    def _get_prev(self, tokens: List[Token], i: int) -> Token | None:
        """Helper to get the previous valid token (skipping empty ones)."""
        for j in range(i - 1, -1, -1):
            if tokens[j].text:
                return tokens[j]
        return None

    def _get_next(self, tokens: List[Token], i: int) -> Token | None:
        """Helper to get the next valid token."""
        for j in range(i + 1, len(tokens)):
            if tokens[j].text:
                return tokens[j]
        return None