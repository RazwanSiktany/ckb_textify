import re
from typing import List

from ckb_textify.core.types import Token, TokenType
from ckb_textify.modules.base import Module
from ckb_textify.modules.web import WebNormalizer


class TechnicalNormalizer(Module):
    ALPHANUMERIC_RE = re.compile(r"(?=.*\d)(?=\w*[^\W\d_])[\w\-]+\b")
    CODE_SPLITTER_RE = re.compile(r"[a-zA-Z0-9\u0080-\uFFFF]+|[\-@\#_\+\\\/]")

    # Optimization: Pre-compiled regex for symbol detection inside split parts
    SYMBOL_PART_RE = re.compile(r"^[\-@\#_\+\\\/]$")

    # Optimization: Pre-compiled regex for Hexadecimal strings
    HEX_RE = re.compile(r"^[a-fA-F0-9]+$")

    # Regex to detect pure number-hyphen-number sequences (which should be skipped here)
    RANGE_RE = re.compile(r"^\d+-\d+$")

    MATH_TERMS = {"ln", "log", "sin", "cos", "tan", "lim", "mod", "exp"}
    CURRENCY_CODES = {"IQD", "USD", "EUR", "GBP", "JPY", "AED", "TRY", "IRR", "KWD", "SAR", "AUD", "CAD"}
    UNIT_CODES = {
        "mg", "ml", "gb", "mb", "kb", "tb", "km", "kg", "cm", "mm",
        "ft", "yd", "mi", "in", "oz", "lb", "gal", "mph", "ms",
        "kwh", "mw", "hp", "kpa", "psi", "kn", "cal", "kcal"
    }

    def __init__(self, config):
        super().__init__(config)
        self.helper = WebNormalizer(config)

    @property
    def name(self) -> str:
        return "TechnicalNormalizer"

    @property
    def priority(self) -> int:
        return 90

    def process(self, tokens: List[Token]) -> List[Token]:
        new_tokens = []
        tech_indices = set()

        for i, token in enumerate(tokens):
            if token.text == "-":
                prev = tokens[i - 1] if i > 0 else None
                next_t = tokens[i + 1] if i < len(tokens) - 1 else None
                has_space_before = prev and bool(prev.whitespace_after)
                has_space_after = bool(token.whitespace_after)
                is_tight_binding = not (has_space_before or has_space_after)

                if is_tight_binding and prev and next_t and self._is_potential_code(prev) and self._is_potential_code(
                        next_t):
                    tech_indices.add(i)
                    tech_indices.add(i - 1)
                    tech_indices.add(i + 1)

        for i, token in enumerate(tokens):
            processed_by_expansion = False

            if token.type == TokenType.WORD:
                text_lower = token.text.lower()
                text_upper = token.text.upper()
                if text_lower in self.MATH_TERMS or text_upper in self.CURRENCY_CODES or text_lower in self.UNIT_CODES:
                    new_tokens.append(token)
                    continue

            # FIX: Skip processing if it's a numeric range (1990-2000) that tokenizer grouped as WORD
            if token.type == TokenType.WORD and self.RANGE_RE.fullmatch(token.text):
                new_tokens.append(token)
                continue

            if token.type == TokenType.TECHNICAL:
                text = token.text
                if text.startswith("#") or text.startswith("@"):
                    is_hashtag = text.startswith("#")
                    prefix_text = "ھاشتاگ" if is_hashtag else "ئەت"
                    core = text[1:]

                    new_tokens.append(Token(prefix_text, prefix_text, TokenType.WORD, whitespace_after=" "))

                    # Decompose the core into Words, Digits, and Symbols to ensure preservation
                    # e.g., "User_1" -> Token("User"), Token("_"), Token("1")
                    decomposed_tokens = self._decompose_hash_mention_core(core, token.whitespace_after)
                    new_tokens.extend(decomposed_tokens)

                    processed_by_expansion = True
                else:
                    token.text = self.helper._spell_out(token.text)
                    token.type = TokenType.WORD
                    token.tags.add("IS_SPELLED_OUT")

            elif i in tech_indices:
                # Check if this is a purely numeric range context (Number-Number) and skip tech processing if so
                prev = tokens[i - 1] if i > 0 else None
                next_t = tokens[i + 1] if i < len(tokens) - 1 else None

                is_pure_numeric_range = False
                if token.text == "-":
                    if prev and next_t and prev.type == TokenType.NUMBER and next_t.type == TokenType.NUMBER:
                        is_pure_numeric_range = True
                elif token.type == TokenType.NUMBER:
                    if next_t and next_t.text == "-" and tokens[i + 2].type == TokenType.NUMBER:
                        is_pure_numeric_range = True
                    if prev and prev.text == "-" and tokens[i - 2].type == TokenType.NUMBER:
                        is_pure_numeric_range = True

                if is_pure_numeric_range:
                    new_tokens.append(token)
                    continue

                if token.text == "-":
                    token.text = "داش"
                    token.type = TokenType.WORD
                    token.whitespace_after = " "
                else:
                    token.text = self.helper._spell_out(token.text)
                    token.type = TokenType.WORD
                    token.tags.add("IS_SPELLED_OUT")

            elif token.type == TokenType.WORD and ("-" in token.text or "_" in token.text):
                sub_parts = [match.group(0) for match in self.CODE_SPLITTER_RE.finditer(token.text)]
                for j, part in enumerate(sub_parts):
                    new_word = part
                    if self.SYMBOL_PART_RE.match(part):
                        new_word = self.helper._spell_out(part)
                        new_tokens.append(Token(new_word, part, TokenType.WORD, whitespace_after=" "))
                    else:
                        new_word = self.helper._spell_out(part)
                        ws_after = token.whitespace_after if j == len(sub_parts) - 1 else " "
                        new_tokens.append(
                            Token(new_word, part, TokenType.WORD, tags={"IS_SPELLED_OUT"}, whitespace_after=ws_after))
                processed_by_expansion = True

            elif token.type == TokenType.WORD and self.ALPHANUMERIC_RE.fullmatch(token.text):
                token.text = self.helper._spell_out(token.text)
                token.type = TokenType.WORD
                token.tags.add("IS_SPELLED_OUT")

            next_t = tokens[i + 1] if i < len(tokens) - 1 else None
            if not processed_by_expansion and token.type == TokenType.WORD and next_t and next_t.text == "-" and i + 1 in tech_indices:
                new_tokens.append(token)
                continue

            if not processed_by_expansion:
                new_tokens.append(token)

        return new_tokens

    def _decompose_hash_mention_core(self, core: str, final_whitespace: str) -> List[Token]:
        """
        Splits a hashtag/mention core (e.g. "User_1") into constituent tokens
        (User, _, 1) so downstream modules (Transliteration, Symbol, Number)
        can process them individually without dropping parts.
        """
        tokens = []
        # 1. Split into chunks by symbols (using existing splitter logic)
        sub_parts = [match.group(0) for match in self.CODE_SPLITTER_RE.finditer(core)]

        final_parts = []
        for p in sub_parts:
            if self.SYMBOL_PART_RE.match(p):
                # Is a separator/symbol
                final_parts.append((p, TokenType.SYMBOL))
            elif p.isdigit():
                # Is a number
                final_parts.append((p, TokenType.NUMBER))
            else:
                # Is text/alphanumeric (e.g. "User" or "User1")
                # Split any digits attached to words so Transliteration doesn't eat them
                # Regex matches sequences of non-digits (\D+) OR digits (\d+)
                mixed_parts = re.findall(r"\d+|\D+", p)
                for mp in mixed_parts:
                    if mp.isdigit():
                        final_parts.append((mp, TokenType.NUMBER))
                    else:
                        final_parts.append((mp, TokenType.WORD))

        # 2. Create Token objects
        for j, (text, t_type) in enumerate(final_parts):
            # Last token gets the original whitespace; others get a single space
            ws = final_whitespace if j == len(final_parts) - 1 else " "
            tokens.append(Token(text, text, t_type, whitespace_after=ws))

        return tokens

    def _is_potential_code(self, token: Token) -> bool:
        if token.type == TokenType.WORD:
            if token.text.lower() in self.MATH_TERMS: return False
            if token.text.upper() in self.CURRENCY_CODES: return False
            if token.text.lower() in self.UNIT_CODES: return False

        if token.type == TokenType.WORD:
            # Check 1: Standard Alphanumeric (Word + Digit mix)
            if self.ALPHANUMERIC_RE.fullmatch(token.text):
                return True

            # Check 2: Simple Mixed content check (redundant but safe fallback)
            has_digit = any(c.isdigit() for c in token.text)
            has_alpha = any(c.isalpha() for c in token.text)
            if has_digit and has_alpha:
                return True

            # Check 3: Hex strings (all valid hex chars)
            if self.HEX_RE.fullmatch(token.text):
                return True

        if token.type == TokenType.NUMBER:
            return True

        return False