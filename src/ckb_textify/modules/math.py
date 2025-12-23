import re
from typing import List

from ckb_textify.core.types import Token, TokenType
from ckb_textify.modules.base import Module
from ckb_textify.utils.numbers import int_to_kurdish
from ckb_textify.resources.transliteration_maps import GREEK_NAMES_MAP, LETTER_MAP


class MathNormalizer(Module):
    """
    Handles Math Operators, Functions, and Fractions.
    Converts these elements into spoken Kurdish text.
    Also handles Subscripts, Superscripts, Unicode Fractions, and Variables.
    """

    MATH_SYMBOLS = {
        "+": "کۆ",
        "*": "کەڕەتی",
        "×": "کەڕەتی",
        "/": "دابەش",
        "÷": "دابەش",
        "±": "کەم کۆ",
        "√": "ڕەگی دووجای",
        "-": "کەم",
        "−": "کەم",
        "=": "یەکسانە بە",
        "^": "توان",
        "%": "لە سەدا",
        "≈": "نزیکەی",
    }

    MATH_FUNCTIONS = {
        "ln": "لۆگاریتمی سروشتی",
        "log": "لۆگاریتمی",
        "sin": "ساینی",
        "cos": "کۆساینی",
        "tan": "تانجێنتی",
        "lim": "لیمێتی",
        "mod": "مۆد",
        "exp": "ئێکسپۆنێنشیاڵ",
        "μ": "میو",
        "π": "پای"
    }

    # Units that should NEVER be treated as variables even if tagged IS_UNIT
    STRICT_UNITS = {
        'm', 'g', 'l', 's', 'h', 'kg', 'km', 'cm', 'mm', 'ml', 'mg',
        'gb', 'mb', 'kb', 'tb', 'ft', 'yd', 'mi', 'in', 'oz', 'lb',
        'v', 'w', 'j', 'pa', 'n', 'wh', 'kwh', 'kw', 'mw', 'hp',
        'mv', 'ma', 'kn', 'psi', 'kpa', 'cal', 'kcal', 'kj', 'gal', 'mph', 'ms'
    }

    MATH_BRACKETS = {"(", ")", "[", "]"}

    SUBSCRIPT_DIGITS = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
    SUPERSCRIPT_DIGITS = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")

    # Map Unicode Fractions to (Numerator, Denominator) integers
    FRACTION_VALUES = {
        "½": (1, 2), "¼": (1, 4), "¾": (3, 4),
        "⅓": (1, 3), "⅔": (2, 3),
        "⅕": (1, 5), "⅖": (2, 5), "⅗": (3, 5), "⅘": (4, 5),
        "⅙": (1, 6), "⅚": (5, 6),
        "⅛": (1, 8), "⅜": (3, 8), "⅝": (5, 8), "⅞": (7, 8),
        "⅐": (1, 7), "⅑": (1, 9), "⅒": (1, 10),
        "↉": (0, 3),
    }

    # Optimization: Pre-compiled Regex Patterns
    SUBSCRIPT_RE = re.compile(r"^[\u2080-\u2089]+$")
    SUPERSCRIPT_RE = re.compile(r"^[\u2070\u00B9\u00B2\u00B3\u2074-\u2079]+$")
    VARIABLE_RE = re.compile(r"^[a-zA-Z]{1,2}$")
    HAS_DIGIT_RE = re.compile(r"\d")
    NUMERIC_FORMAT_RE = re.compile(r"^[\d,]+(\.\d+)?$")

    @property
    def name(self) -> str:
        return "MathNormalizer"

    @property
    def priority(self) -> int:
        return 80

    def process(self, tokens: List[Token]) -> List[Token]:
        i = 0
        while i < len(tokens):
            token = tokens[i]

            # --- Handle Unicode Fractions (½, ⅜, etc.) ---
            if token.text in self.FRACTION_VALUES:
                num, denom = self.FRACTION_VALUES[token.text]

                prev = self._get_prev(tokens, i)
                is_mixed = self._is_numeric_token(prev)

                token.text = self._format_fraction(num, denom, is_mixed)
                token.type = TokenType.WORD
                token.whitespace_after = " "

                if prev and not prev.whitespace_after:
                    prev.whitespace_after = " "

                i += 1
                continue

            # --- 0. Handle Subscripts (Base) ---
            if hasattr(token.type, 'name') and token.type.name == 'SUBSCRIPT' or \
                    (token.type in (TokenType.SYMBOL, TokenType.UNKNOWN) and self.SUBSCRIPT_RE.match(token.text)):

                ascii_digits = token.text.translate(self.SUBSCRIPT_DIGITS)
                if ascii_digits.isdigit():
                    val = int(ascii_digits)
                    token.text = f"بنچینە {int_to_kurdish(val)}"
                    token.type = TokenType.WORD
                    token.tags.add("MATH_TERM")
                    token.whitespace_after = " "
                    if i > 0 and not tokens[i - 1].whitespace_after:
                        tokens[i - 1].whitespace_after = " "
                i += 1
                continue

            # --- 0. Handle Superscripts (Power/Ja) ---
            if hasattr(token.type, 'name') and token.type.name == 'SUPERSCRIPT' or \
                    (token.type in (TokenType.SYMBOL, TokenType.UNKNOWN) and self.SUPERSCRIPT_RE.match(token.text)):

                prev = self._get_prev(tokens, i)
                is_unit_context = False
                if prev:
                    # FIX: Only treat as unit context if IS_UNIT is present AND MATH_TERM is NOT present.
                    # If MathNormalizer claimed the previous token (variable), it's a math term, not a unit.
                    if ("IS_UNIT" in prev.tags or "UNIT_PROCESSED" in prev.tags) and "MATH_TERM" not in prev.tags:
                        is_unit_context = True
                    elif prev.type == TokenType.WORD and (
                            prev.text.endswith("مەتر") or prev.text.endswith("گرام") or
                            prev.text.endswith("لیتر") or prev.text.endswith("چرکە")
                    ):
                        is_unit_context = True

                if is_unit_context:
                    i += 1
                    continue

                ascii_digits = token.text.translate(self.SUPERSCRIPT_DIGITS)
                if ascii_digits.isdigit():
                    val = int(ascii_digits)
                    base_text = int_to_kurdish(val)
                    token.text = f"توان {base_text}"
                    token.type = TokenType.WORD
                    token.tags.add("MATH_TERM")
                    token.whitespace_after = " "
                    if i > 0 and not tokens[i - 1].whitespace_after:
                        tokens[i - 1].whitespace_after = " "
                i += 1
                continue

            # --- 1. Math Functions, Greek, and Variables ---
            if token.type == TokenType.WORD:
                token_lower = token.text.lower()

                if token_lower in self.MATH_FUNCTIONS:
                    token.text = self.MATH_FUNCTIONS[token_lower]
                    token.tags.add("MATH_FUNCTION")
                    token.type = TokenType.WORD
                    i += 1
                    continue
                elif token.text in GREEK_NAMES_MAP:
                    token.text = GREEK_NAMES_MAP[token.text]
                    token.tags.add("MATH_FUNCTION")
                    token.type = TokenType.WORD
                    i += 1
                    continue

                # Check for Latin Variables (x, y, a, b, ac...)
                if self.VARIABLE_RE.match(token.text):
                    # Logic to override IS_UNIT for potential variables like 'a' in '2a'
                    is_strict_unit = "IS_UNIT" in token.tags and token.text.lower() in self.STRICT_UNITS

                    # IMPORTANT: If token is "داش", skip variable check (it's handled below as an operator)
                    if token.text == "داش":
                        pass
                    elif not is_strict_unit:
                        prev = self._get_prev(tokens, i)
                        next_t = self._get_next(tokens, i)

                        if self._check_math_context(token, prev, next_t):
                            # Spell out letters: "ac" -> "ئەی سی"
                            spelled_out = []
                            for char in token.text.lower():
                                spelled_out.append(LETTER_MAP.get(char, char))

                            token.text = " ".join(spelled_out)
                            token.tags.add("MATH_TERM")

                            # CRITICAL FIX: If we identify this as a math variable, remove the IS_UNIT tag.
                            # This prevents the superscript logic (in next iteration) from treating it as a unit power.
                            token.tags.discard("IS_UNIT")

                            token.type = TokenType.WORD
                            token.whitespace_after = " "
                            if prev and not prev.whitespace_after:
                                prev.whitespace_after = " "
                            i += 1
                            continue

            # --- 2. Math Operators & Brackets ---
            is_math_symbol = token.type == TokenType.SYMBOL and (
                        token.text in self.MATH_SYMBOLS or token.text in self.MATH_BRACKETS)
            # FIX: Handle "dash" word from TechnicalNormalizer (for 1990-2000)
            is_dash_word = token.type == TokenType.WORD and token.text == "داش"

            if is_math_symbol or is_dash_word:
                prev = self._get_prev(tokens, i)
                next_t = self._get_next(tokens, i)

                # Normalize text for checks (Treat "داش" as "-")
                check_text = "-" if is_dash_word else token.text

                # Special Check for '+'
                if check_text == "+" and prev and next_t:
                    if prev.type == TokenType.WORD and next_t.type == TokenType.WORD:
                        if len(prev.text) > 1 and "MATH_TERM" not in prev.tags:
                            token.text = "لەگەڵ"
                            token.type = TokenType.WORD
                            token.whitespace_after = " "
                            if not prev.whitespace_after: prev.whitespace_after = " "
                            i += 1
                            continue
                    elif prev.type == TokenType.WORD and next_t.type == TokenType.NUMBER:
                        if "MATH_TERM" in prev.tags:
                            pass
                        else:
                            i += 1
                            continue

                # --- Range vs Minus Check (Prioritized for both Symbol - and Word داش) ---
                if check_text == "-" or check_text == "−":
                    prev_prev = self._get_prev(tokens, i - 1) if prev else None
                    next_next = self._get_next(tokens, i + 1) if next_t else None
                    is_prev_num = self._is_numeric_token(prev)
                    is_next_num = self._is_numeric_token(next_t)

                    def is_active_math(t):
                        if not t: return False
                        if t.text in self.MATH_SYMBOLS: return True
                        if t.text in self.MATH_BRACKETS: return True
                        if self._is_math_term(t.text): return True
                        if "MATH_TERM" in t.tags: return True
                        return False

                    is_isolated = not (is_active_math(prev_prev) or is_active_math(next_next))

                    if is_prev_num and is_next_num and is_isolated:
                        token.text = "بۆ"
                        token.type = TokenType.WORD
                        token.whitespace_after = " "
                        if prev: prev.whitespace_after = " "
                        i += 1
                        continue

                # Determine Context
                is_math_context = False
                if is_dash_word:
                    # Proxy check: treat this token as if it were a math symbol '-'
                    is_math_context = self._check_math_context_logic("-", TokenType.SYMBOL, prev, next_t)
                else:
                    is_math_context = self._check_math_context(token, prev, next_t)

                if is_math_context:
                    if check_text in self.MATH_BRACKETS:
                        token.type = TokenType.WORD
                        token.whitespace_after = " "

                    elif check_text in self.MATH_SYMBOLS:
                        handled_fraction = False

                        # Division
                        if check_text == "/" or check_text == "÷":
                            if prev and next_t:
                                # FIX: Check if neighbors are UNITS. If so, SKIP division (let UnitNormalizer handle it).
                                prev_is_unit = "IS_UNIT" in prev.tags or "UNIT_PROCESSED" in prev.tags
                                next_is_unit = "IS_UNIT" in next_t.tags or "UNIT_PROCESSED" in next_t.tags

                                if prev_is_unit and next_is_unit:
                                    # Skip this slash, it's for units (e.g. km/h)
                                    i += 1
                                    continue

                            if prev and next_t and prev.type == TokenType.NUMBER and next_t.type == TokenType.NUMBER:
                                prev_prev = self._get_prev(tokens, i - 1)
                                is_mixed = self._is_numeric_token(prev_prev)
                                if self._handle_fraction(prev, next_t, is_mixed):
                                    token.text = ""
                                    next_t.text = ""
                                    next_t.type = TokenType.UNKNOWN
                                    token.type = TokenType.UNKNOWN
                                    prev.whitespace_after = " "
                                    handled_fraction = True
                                    i += 2
                                    continue

                        if not handled_fraction:
                            # --- UNARY OPERATOR CHECK ---
                            is_unary = not prev or \
                                       prev.text in ["(", "[", "{", "=", ","] or \
                                       (prev.type == TokenType.SYMBOL and prev.text in self.MATH_SYMBOLS)

                            if is_unary and check_text in ["-", "−", "+"]:
                                if check_text in ["-", "−"]:
                                    token.text = "سالب"
                                elif check_text == "+":
                                    token.text = "موجەب"
                            else:
                                token.text = self.MATH_SYMBOLS[check_text]

                            token.type = TokenType.WORD
                            token.whitespace_after = " "
                            if prev: prev.whitespace_after = " "

                        if handled_fraction:
                            continue

            i += 1

        return [t for t in tokens if t.text]

    def _is_numeric_token(self, token: Token) -> bool:
        if not token: return False
        if token.type == TokenType.NUMBER: return True
        has_digit = bool(self.HAS_DIGIT_RE.search(token.original_text))
        is_num_format = bool(self.NUMERIC_FORMAT_RE.match(token.original_text))
        return has_digit and is_num_format

    def _format_fraction(self, num: int, denom: int, is_mixed: bool) -> str:
        if num == 1 and denom == 2: return "و نیو" if is_mixed else "نیوە"
        if num == 1 and denom == 4: return "و چارەک" if is_mixed else "چارەک"
        num_text = int_to_kurdish(num)
        denom_text = int_to_kurdish(denom)
        if is_mixed:
            return f"ژمارەی تەواو و {num_text} لەسەر {denom_text}"
        else:
            return f"{num_text} دابەش {denom_text}"

    def _check_math_context(self, current: Token, prev: Token | None, next_t: Token | None) -> bool:
        """Checks if current token is in a mathematical context."""
        return self._check_math_context_logic(current.text, current.type, prev, next_t)

    def _check_math_context_logic(self, text: str, type: TokenType, prev: Token | None, next_t: Token | None) -> bool:
        def is_mathy(t):
            if not t: return False
            if t.type == TokenType.NUMBER: return True
            if "MATH_TERM" in t.tags: return True
            if self._is_math_term(t.text): return True
            # FIX: Check explicitly for Superscript/Subscript type OR tag/pattern
            if hasattr(t.type, 'name') and t.type.name in ('SUBSCRIPT', 'SUPERSCRIPT'): return True
            # Also check if text matches the patterns (in case tokenizer typed it as SYMBOL)
            if self.SUPERSCRIPT_RE.match(t.text) or self.SUBSCRIPT_RE.match(t.text): return True

            # FIX: Detect Variables (Single Latin Letter Words)
            if t.type == TokenType.WORD and len(t.text) == 1 and t.text.isalpha(): return True
            # Check for Greek letters
            if t.text in GREEK_NAMES_MAP: return True
            return False

        if text in self.MATH_BRACKETS:
            is_start_or_unary = (prev is None) or (prev.text in ["(", "[", "{", "=", ","]) or (
                    prev.text in self.MATH_SYMBOLS)
            prev_valid = is_start_or_unary or is_mathy(prev) or prev.text in [")", "]"]
            next_valid = next_t and (is_mathy(next_t) or next_t.text in ["(", "[", "sin", "cos"])
            if prev_valid or next_valid: return True

        if text in self.MATH_SYMBOLS:
            is_start_or_unary = (prev is None) or (prev.text in ["(", "[", "{", "=", ","]) or (
                    prev.text in self.MATH_SYMBOLS)
            prev_valid = is_start_or_unary or is_mathy(prev) or prev.text in [")"]
            next_valid = next_t and (is_mathy(next_t) or next_t.text in ["("])
            if prev_valid and next_valid: return True

        # New check for Variables (e.g. x, ac) in implicit math context (e.g. 2a)
        if type == TokenType.WORD and self.VARIABLE_RE.match(text):
            if text.lower() in self.STRICT_UNITS: return False
            if prev and prev.type == TokenType.NUMBER: return True
            if next_t:
                if next_t.type == TokenType.NUMBER: return True
                # FIX: Explicitly allow following superscript (e.g. a²)
                if self.SUPERSCRIPT_RE.match(next_t.text) or (
                        hasattr(next_t.type, 'name') and next_t.type.name == 'SUPERSCRIPT'):
                    return True

            if prev and prev.text in self.MATH_SYMBOLS: return True
            if next_t and next_t.text in self.MATH_SYMBOLS: return True
            if prev and prev.text in self.MATH_BRACKETS: return True
            if next_t and next_t.text in self.MATH_BRACKETS: return True

        return False

    def _is_math_term(self, text: str) -> bool:
        lower = text.lower()
        if lower in self.MATH_FUNCTIONS: return True
        if text in GREEK_NAMES_MAP: return True
        if text in self.MATH_FUNCTIONS.values(): return True
        return False

    def _handle_fraction(self, num_token: Token, denom_token: Token, is_mixed: bool) -> bool:
        try:
            num = int(num_token.text.replace(',', ''))
            denom = int(denom_token.text.replace(',', ''))
        except ValueError:
            return False

        num_token.text = self._format_fraction(num, denom, is_mixed)
        num_token.type = TokenType.WORD
        num_token.tags.add("FRACTION")
        return True

    def _get_prev(self, tokens: List[Token], i: int) -> Token | None:
        return tokens[i - 1] if i > 0 else None

    def _get_next(self, tokens: List[Token], i: int) -> Token | None:
        return tokens[i + 1] if i < len(tokens) - 1 else None