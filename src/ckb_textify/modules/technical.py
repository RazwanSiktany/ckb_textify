import re
from typing import List

from ckb_textify.core.types import Token, TokenType
from ckb_textify.modules.base import Module
from ckb_textify.modules.web import WebNormalizer


class TechnicalNormalizer(Module):
    ALPHANUMERIC_RE = re.compile(r"(?=.*\d)(?=\w*[^\W\d_])[\w\-]+\b")
    CODE_SPLITTER_RE = re.compile(r"[a-zA-Z0-9\u0080-\uFFFF]+|[\-@\#_\+\\\/]")

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

                if is_tight_binding and prev and next_t and self._is_potential_code(prev) and self._is_potential_code(next_t):
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

            if token.type == TokenType.TECHNICAL:
                text = token.text
                if text.startswith("#"):
                    core = text[1:]
                    spoken_core = self.helper._spell_out(core)
                    new_tokens.append(Token("ھاشتاگ", "ھاشتاگ", TokenType.WORD, whitespace_after=" "))
                    new_tokens.append(Token(spoken_core, core, TokenType.WORD, tags={"IS_SPELLED_OUT"}, whitespace_after=token.whitespace_after))
                    processed_by_expansion = True
                elif text.startswith("@"):
                    core = text[1:]
                    spoken_core = self.helper._spell_out(core)
                    new_tokens.append(Token("ئەت", "ئەت", TokenType.WORD, whitespace_after=" "))
                    new_tokens.append(Token(spoken_core, core, TokenType.WORD, tags={"IS_SPELLED_OUT"}, whitespace_after=token.whitespace_after))
                    processed_by_expansion = True
                else:
                    token.text = self.helper._spell_out(token.text)
                    token.type = TokenType.WORD
                    token.tags.add("IS_SPELLED_OUT")

            elif i in tech_indices:
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
                    if re.match(r"[\-@\#_\+\\\/]", part):
                        new_word = self.helper._spell_out(part)
                        new_tokens.append(Token(new_word, part, TokenType.WORD, whitespace_after=" "))
                    else:
                        new_word = self.helper._spell_out(part)
                        ws_after = token.whitespace_after if j == len(sub_parts) - 1 else " "
                        new_tokens.append(Token(new_word, part, TokenType.WORD, tags={"IS_SPELLED_OUT"}, whitespace_after=ws_after))
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

    def _is_potential_code(self, token: Token) -> bool:
        if token.type == TokenType.WORD:
             if token.text.lower() in self.MATH_TERMS: return False
             if token.text.upper() in self.CURRENCY_CODES: return False
             if token.text.lower() in self.UNIT_CODES: return False

        if token.type == TokenType.WORD:
            return bool(self.ALPHANUMERIC_RE.fullmatch(token.text)) or \
                (any(c.isdigit() for c in token.text) and any(c.isalpha() for c in token.text)) or \
                all(c in "abcdefABCDEF0123456789" for c in token.text)

        if token.type == TokenType.NUMBER:
            return True

        return False