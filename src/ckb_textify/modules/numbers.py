import re
from typing import List
from ckb_textify.core.types import Token, TokenType
from ckb_textify.modules.base import Module
from ckb_textify.utils.numbers import int_to_kurdish
from ckb_textify.resources.patterns import SUFFIXES_LIST
from ckb_textify.resources.dictionaries import EXCLUDED_HALF_RULE_WORDS


class NumberNormalizer(Module):
    """
    Converts remaining NUMBER tokens into Kurdish text.
    Handles integers, decimals, and special cases like '2.5'.
    Also handles Unary Signs (+20, -50) and Percentages.
    Now includes thresholds for Scientific Notation.
    """

    # Thresholds
    LARGE_THRESHOLD = 1_000_000_000_000_000_000_000  # 10^21
    SMALL_THRESHOLD = 0.0001

    # Sort suffixes by length for correct matching (longest match first)
    # Imported from patterns.py now
    SORTED_SUFFIXES = sorted(SUFFIXES_LIST, key=len, reverse=True)

    @property
    def name(self) -> str:
        return "NumberNormalizer"

    @property
    def priority(self) -> int:
        return 70

    def process(self, tokens: List[Token]) -> List[Token]:
        for i, token in enumerate(tokens):
            if token.type == TokenType.NUMBER:
                text = token.text

                # --- Unary Sign Logic (+/-) ---
                prev = self._get_prev(tokens, i)
                next_t = self._get_next(tokens, i)  # Get next token early
                is_negative = False
                is_positive = False

                # Check for signs (+/-)
                if prev and prev.type == TokenType.SYMBOL:
                    symbol = prev.text
                    prev_prev = self._get_prev(tokens, i - 1) if i > 0 else None

                    is_math_sign = True
                    # FIX: Handle standard hyphen (-) and unicode minus (−)
                    if (symbol == "-" or symbol == "−") and prev_prev and prev_prev.type == TokenType.WORD:
                        if not prev_prev.whitespace_after:
                            is_math_sign = False

                    if is_math_sign:
                        if symbol == "-" or symbol == "−":
                            is_negative = True
                            prev.text = ""
                        elif symbol == "+":
                            is_positive = True
                            prev.text = ""

                # --- Percentage Logic ---
                has_percentage = False

                # Check for percentage symbol BEFORE the number
                # FIX: Check both text and original_text for robustness
                if prev:
                    # Check text content for symbols or keywords
                    is_percent_symbol = "%" in prev.text or "٪" in prev.text
                    is_percent_word = "لەسەدا" in prev.text
                    # Also check original text in case previous normalizers changed it but left original
                    is_percent_orig = "%" in prev.original_text or "٪" in prev.original_text

                    if is_percent_symbol or is_percent_word or is_percent_orig:
                        has_percentage = True
                        # Only consume if it's the symbol itself (text or original)
                        if is_percent_symbol or is_percent_orig:
                            prev.text = ""

                            # Check for percentage symbol AFTER the number
                if not has_percentage and next_t:
                    if "%" in next_t.text or "٪" in next_t.text:
                        has_percentage = True
                        next_t.text = ""  # Consume symbol

                # --- 1. Scientific Notation Explicit Input ---
                if "e" in text.lower():
                    token.text = self._convert_scientific(text, is_negative, is_positive)
                    if has_percentage: token.text = "لەسەدا " + token.text
                    token.type = TokenType.WORD
                    continue

                # --- 2. Threshold Checks (Prevent Crash on Huge Numbers) ---
                try:
                    clean_text = text.replace(",", "")
                    val = float(clean_text)
                    abs_val = abs(val)

                    # Check for Large Numbers (> 10^21)
                    if abs_val >= self.LARGE_THRESHOLD:
                        token.text = self._convert_scientific(text, is_negative, is_positive)
                        if has_percentage: token.text = "لەسەدا " + token.text
                        token.type = TokenType.WORD
                        continue

                    # Check for Very Small Numbers (< 0.0001), ignoring zero
                    if 0 < abs_val < self.SMALL_THRESHOLD:
                        token.text = self._convert_scientific(text, is_negative, is_positive)
                        if has_percentage: token.text = "لەسەدا " + token.text
                        token.type = TokenType.WORD
                        continue

                except ValueError:
                    pass  # If parsing fails, fall through to standard processing

                # --- Look Ahead for Unit (Half Rule) ---
                # We only apply the "Move Niw to End" logic if it is NOT a percentage.
                is_half_case = False

                if "." in text and not has_percentage:
                    parts = text.split(".")
                    if len(parts) > 1 and parts[1] == "5":

                        # next_t is already fetched

                        # Scenario A: Standard Unit (Tagged by UnitTagger)
                        if next_t and "IS_UNIT" in next_t.tags:
                            is_half_case = True
                            next_t.tags.add("APPEND_HALF")

                            int_part = text.split(".")[0]
                            token.text = self._convert_integer(int_part, is_negative, is_positive)

                        # Scenario B: Generic Word (The "Mrishk" Rule)
                        # If it's NOT a standard unit, but it is a word, treat it as a unit for the half rule.
                        elif next_t and next_t.type == TokenType.WORD and next_t.text:
                            # 1. Extract suffix from the word (e.g. Mrishkm -> Mrishk, m)
                            base_word, suffix = self._extract_suffix_generic(next_t.text)

                            # FIX: Check if the word contains Latin characters
                            # If it is English/Latin (e.g. "Pro", "kg"), DO NOT apply the half rule.
                            # We want "2.5 Pro" -> "Duu u Niw Pro", NOT "Duu Pro u Niw"
                            is_latin = bool(re.search(r'[a-zA-Z]', next_t.text))

                            # Check if the base word is in the EXCLUSION list AND not Latin
                            if base_word not in EXCLUDED_HALF_RULE_WORDS and not is_latin:
                                is_half_case = True

                                # 2. Prepare Integer Text
                                int_part = text.split(".")[0]
                                int_text = self._convert_integer(int_part, is_negative, is_positive)

                                # 3. Prepare "Niw" text with suffix
                                if suffix in ["یە", "ە"]:
                                    niw_text = "نیوە"
                                else:
                                    niw_text = "نیو"
                                full_suffix_text = f"{niw_text}{suffix}" if suffix not in ["", "ە", "یە"] else niw_text

                                # 4. Construct Final String: "Chwar Mrishk u Niwm"
                                # We combine everything into the NUMBER token and consume the WORD token
                                token.text = f"{int_text} {base_word} و {full_suffix_text}"

                                # Consume the next token
                                next_t.text = ""
                                next_t.type = TokenType.UNKNOWN

                if not is_half_case:
                    if "." in text:
                        # For percentages, we typically want "duu u niw" (2.5), not "duu point penc"
                        # Passing is_percentage=False allows "u niw" logic to run inside _convert_decimal
                        # We pass False here because even for percentages, you preferred "u niw" phrasing in your feedback
                        token.text = self._convert_decimal(text, is_negative, is_positive)
                    else:
                        token.text = self._convert_integer(text, is_negative, is_positive)

                # Add Percentage Prefix if detected
                if has_percentage:
                    token.text = "لەسەدا " + token.text

                token.type = TokenType.WORD

        return [t for t in tokens if t.text]

    def _extract_suffix_generic(self, text: str):
        """
        Splits a word into base and suffix based on the global suffix list.
        Returns (base, suffix). If no suffix, returns (text, "").
        """
        for sfx in self.SORTED_SUFFIXES:
            if text.endswith(sfx):
                # Ensure we don't reduce the word to nothing or just 1 char if suffix is long
                # (Simple heuristic: base should probably be meaningful, but for now just split)
                potential_base = text[:-len(sfx)]
                if potential_base:
                    return potential_base, sfx

        return text, ""

    def _convert_scientific(self, text: str, is_negative: bool, is_positive: bool = False) -> str:
        try:
            # Clean commas if present in mantissa before float conversion
            clean_text = text.replace(",", "")
            val = float(clean_text)
            if is_negative: val = -val

            # Format to scientific with 3 decimal places (matching user preference)
            sci_str = f"{val:.3e}".lower()

            mantissa_str, exponent_str = sci_str.split('e')

            # Clean trailing zeros/dots in mantissa
            if "." in mantissa_str:
                mantissa_str = mantissa_str.rstrip('0').rstrip('.')

            if "." in mantissa_str:
                mantissa_text = self._convert_decimal(mantissa_str, False, is_positive)
            else:
                mantissa_text = self._convert_integer(mantissa_str, False, is_positive)

            # Exponent is always an integer
            try:
                exp_val = int(exponent_str)
                exp_is_neg = exp_val < 0
                # Pass explicit sign flags so "sallib" is added correctly for negative exponents
                exponent_text = self._convert_integer(exponent_str, exp_is_neg, False)
            except ValueError:
                exponent_text = self._convert_integer(exponent_str, False, False)

            return f"{mantissa_text} جارانی دە توانی {exponent_text}"
        except ValueError:
            return text

    def _convert_integer(self, text: str, is_negative: bool, is_positive: bool = False) -> str:
        try:
            # FIX: Clean commas (2,000 -> 2000)
            clean_text = text.replace(",", "")
            val = int(clean_text)

            # Handle Leading Zeros
            clean_text_unsigned = clean_text.lstrip("+-")
            num_str = str(abs(val))
            zeros_count = 0

            if len(clean_text_unsigned) > len(num_str):
                zeros_count = len(clean_text_unsigned) - len(num_str)

            zeros_text = ""
            if zeros_count > 0:
                if zeros_count <= 2:
                    zeros_text = " ".join(["سفر"] * zeros_count)
                else:
                    count_text = int_to_kurdish(zeros_count)
                    zeros_text = f"{count_text} جار سفر"

            base_text = int_to_kurdish(abs(val))

            parts = []
            if is_negative:
                parts.append("سالب")
            elif is_positive:
                parts.append("موجەب")

            if zeros_text:
                parts.append(zeros_text)

            parts.append(base_text)

            return " ".join(parts)

        except ValueError:
            return text

    def _convert_decimal(self, text: str, is_negative: bool, is_positive: bool = False) -> str:
        try:
            if "e" in text.lower(): return text
            # FIX: Clean commas
            clean_text = text.replace(",", "")

            parts = clean_text.split(".")
            if len(parts) != 2: return text
            int_part = int(parts[0])
            frac_part_str = parts[1]

            # --- Rule: Limit fractional part to 5 digits ---
            if len(frac_part_str) > 5:
                frac_part_str = frac_part_str[:5]

            prefix = ""
            if is_negative:
                prefix = "سالب "
            elif is_positive:
                prefix = "موجەب "

            # Always try to use "u niw" for .5 unless caller overrides (but here we removed override)
            # This aligns with user request: 2.5% -> "leseda duu u niw"
            if frac_part_str == "5":
                base = int_to_kurdish(int_part)
                suffix = "و نیو"
                return f"{prefix}{base} {suffix}".strip()

            base = int_to_kurdish(int_part)
            leading_zeros = "".join(["سفر " for c in frac_part_str if c == "0"])

            if frac_part_str:
                frac_val = int(frac_part_str)
                # If frac_val is 0 (e.g. 0.00), leading zeros handles the text
                frac_text = int_to_kurdish(frac_val) if frac_val > 0 else ""
            else:
                frac_text = ""

            return f"{prefix}{base} پۆینت {leading_zeros}{frac_text}".strip()
        except ValueError:
            return text

    def _get_prev(self, tokens, i):
        """Helper to get the previous valid token (skipping empty ones)."""
        for j in range(i - 1, -1, -1):
            if tokens[j].text:
                return tokens[j]
        return None

    def _get_next(self, tokens, i):
        """Helper to get the next valid token (skipping empty ones)."""
        for j in range(i + 1, len(tokens)):
            if tokens[j].text:
                return tokens[j]
        return None