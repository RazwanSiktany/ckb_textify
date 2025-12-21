import re
from typing import List
import logging

try:
    import eng_to_ipa as ipa
    import anyascii
except ImportError:
    ipa = None
    anyascii = None

from ckb_textify.core.types import Token, TokenType
from ckb_textify.modules.base import Module
from ckb_textify.resources.transliteration_maps import (
    IPA_MAP, IPA_VOWELS, MULTI_CHAR_MAP, SINGLE_CHAR_MAP, CUSTOM_CHAR_MAP, LETTER_MAP
)

logger = logging.getLogger(__name__)


class TransliterationNormalizer(Module):
    """
    Converts Latin (English) and other scripts to Sorani Kurdish.
    Handles Acronyms (GPT -> Ji Pi Ti) and Mixed Case (ChatGPT).
    Now also handles Mixed-Script Tokens (UKم -> UK + م).
    """

    ARABIC_RE = re.compile(r"[\u0600-\u06FF]")

    # Regex to split mixed case
    SPLIT_MIXED_RE = re.compile(r'[A-Z]+(?![a-z])|[A-Z]?[a-z]+')

    # Regex for Mixed Script (Foreign + Kurdish Suffix)
    # Matches: Start, Foreign chars (Latin, Cyrillic, Greek), Arabic chars, End
    # Added \u0400-\u04FF (Cyrillic) and \u0370-\u03FF (Greek)
    MIXED_SCRIPT_RE = re.compile(r"^([a-zA-Z0-9\u0400-\u04FF\u0370-\u03FF]+)([\u0600-\u06FF]+)$")

    @property
    def name(self) -> str:
        return "TransliterationNormalizer"

    @property
    def priority(self) -> int:
        return 10

    def process(self, tokens: List[Token]) -> List[Token]:
        if not self.config.enable_transliteration:
            return tokens

        for token in tokens:
            if token.type == TokenType.WORD:

                # Check for Mixed Script (UKم, Приветـیشمان)
                # If found, we split, process Foreign part, and re-attach suffix
                mixed_match = self.MIXED_SCRIPT_RE.match(token.text)
                if mixed_match:
                    foreign_part = mixed_match.group(1)
                    suffix_part = mixed_match.group(2)

                    # Process the Foreign part (Acronym or Word)
                    processed_foreign = self._process_latin_text(foreign_part)

                    # Recombine
                    token.text = f"{processed_foreign}{suffix_part}"
                    continue

                # Standard: If it contains Arabic/Kurdish characters, skip it.
                if self.ARABIC_RE.search(token.text):
                    continue

                # Process Pure Foreign Text
                token.text = self._process_latin_text(token.text)

        return tokens

    def _normalize_custom_chars(self, text: str) -> str:
        """
        Replaces specific foreign characters with their Latin phonetic equivalents
        before any other processing.
        """
        res = []
        for char in text:
            if char in CUSTOM_CHAR_MAP:
                res.append(CUSTOM_CHAR_MAP[char])
            elif char.lower() in CUSTOM_CHAR_MAP:
                 # fallback to lowercase map if uppercase not found
                 val = CUSTOM_CHAR_MAP[char.lower()]
                 res.append(val.capitalize() if char.isupper() else val)
            else:
                res.append(char)
        return "".join(res)

    def _process_latin_text(self, text: str) -> str:
        # 0. Pre-normalize Custom Chars (Extended Latin, Greek, Cyrillic)
        # This converts "Straẞe" -> "Strasse", "Χαίρετε" -> "Khairete"
        normalized_text = self._normalize_custom_chars(text)

        # 1. Foreign -> Latin Bridge (Handles Chinese/Others -> Latin via library)
        latin_text = normalized_text
        if anyascii and not text_is_pure_latin(normalized_text):
            latin_text = anyascii.anyascii(normalized_text)

        # 2. Split Mixed Case (ChatGPT -> Chat, GPT)
        parts = self.SPLIT_MIXED_RE.findall(latin_text)
        if not parts: parts = [latin_text]

        processed_parts = []
        for part in parts:
            # Acronym Check (All Upper & Length > 1) -> Spell out
            if part.isupper() and len(part) > 1:
                processed_parts.append(self._spell_acronym(part))
            else:
                # Regular Word -> IPA
                processed_parts.append(self._transliterate_chunk(part))

        return " ".join(processed_parts)

    def _spell_acronym(self, text: str) -> str:
        chars = []
        for char in text.lower():
            # Use imported LETTER_MAP
            chars.append(LETTER_MAP.get(char, char))
        return " ".join(chars)

    def _transliterate_chunk(self, text: str) -> str:
        ipa_result = self._ipa_transliterate(text)
        if ipa_result:
            return ipa_result
        return self._fallback_transliterate(text)

    def _ipa_transliterate(self, word: str) -> str | None:
        if not ipa: return None
        ipa_text = ipa.convert(word)
        if "*" in ipa_text: return None

        ipa_text = re.sub(r"[ˈˌ]", "", ipa_text)
        kurdish_word = ""

        if len(ipa_text) > 0 and ipa_text[0] in IPA_VOWELS:
            kurdish_word += "ئ"

        i = 0
        n = len(ipa_text)
        while i < n:
            if i + 2 <= n and ipa_text[i:i + 2] in IPA_MAP:
                kurdish_word += IPA_MAP[ipa_text[i:i + 2]]
                i += 2
                continue
            char = ipa_text[i]
            if char in IPA_MAP:
                kurdish_word += IPA_MAP[char]
            else:
                kurdish_word += char
            i += 1
        return kurdish_word

    def _fallback_transliterate(self, word: str) -> str:
        word = word.lower()
        result = ""
        if word and word[0] in "aeiou": result += "ئ"

        i = 0
        n = len(word)
        while i < n:
            found = False
            for length in [4, 3, 2]:
                if i + length <= n and word[i:i + length] in MULTI_CHAR_MAP:
                    result += MULTI_CHAR_MAP[word[i:i + length]]
                    i += length
                    found = True
                    break
            if found: continue

            char = word[i]
            if char in SINGLE_CHAR_MAP:
                result += SINGLE_CHAR_MAP[char]
            else:
                result += char
            i += 1
        return result


def text_is_pure_latin(text: str) -> bool:
    return all(ord(c) < 128 for c in text)