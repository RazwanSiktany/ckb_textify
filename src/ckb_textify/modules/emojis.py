import re
from typing import List

from ckb_textify.core.types import Token, TokenType
from ckb_textify.modules.base import Module
from ckb_textify.resources.emoji_map import EMOJI_MAP


class EmojiNormalizer(Module):
    """
    Handles Emojis based on config.emoji_mode:
    - "remove": Deletes all emojis.
    - "convert": Translates known emojis to text (e.g. 😂 -> ئیمۆجییەکی پێکەنین).
    - "ignore": Leaves them as is.
    """

    # Regex matching a wide range of Emojis and Pictographs
    EMOJI_REGEX = re.compile(
        r"["
        r"\U0001F000-\U0001F9FF"  # Standard Emojis (Faces, Objects)
        r"\U0001FA00-\U0001FAFF"  # Extended Emojis
        r"\u2600-\u26FF"  # Misc Symbols (Sun, Cloud, Checkbox)
        r"\u2700-\u27BF"  # Dingbats (Checkmark, Cross)
        r"\u2300-\u23FF"  # Technical (Watch, Timer)
        r"\u2B50"  # Star
        r"\u203C\u2049"  # !! ?!
        r"\uFE0F"  # Variation Selector-16 (Critical for matching full emoji sequences like ❤️)
        r"]+",
        flags=re.UNICODE
    )

    @property
    def name(self) -> str:
        return "EmojiNormalizer"

    @property
    def priority(self) -> int:
        return 45  # Run near Symbols/Linguistics

    def process(self, tokens: List[Token]) -> List[Token]:
        mode = self.config.emoji_mode

        if mode == "ignore":
            return tokens

        for token in tokens:
            # We scan WORD and SYMBOL tokens for emojis
            if token.type in (TokenType.WORD, TokenType.SYMBOL, TokenType.UNKNOWN):

                # Check if token contains emojis
                if self.EMOJI_REGEX.search(token.text):
                    if mode == "remove":
                        token.text = self.EMOJI_REGEX.sub("", token.text).strip()
                        if not token.text:
                            # If token became empty, mark it to be skipped/removed later
                            token.text = ""

                    elif mode == "convert":
                        token.text = self.EMOJI_REGEX.sub(self._replace_emoji, token.text)
                        # Ensure converted text is treated as words
                        token.type = TokenType.WORD

        # Filter out tokens that became empty (from remove mode)
        return [t for t in tokens if t.text]

    def _replace_emoji(self, match):
        char = match.group(0)

        # 1. Try exact lookup (Input matches Map exactly)
        description = EMOJI_MAP.get(char)

        # 2. Try stripping Variation Selector-16 (\uFE0F)
        # Case: Input is fully qualified (\u2764\uFE0F), Map has base (\u2764)
        if not description and '\uFE0F' in char:
            clean_char = char.replace('\uFE0F', '')
            description = EMOJI_MAP.get(clean_char)

        # 3. Try adding Variation Selector-16 (\uFE0F)
        # Case: Input is base (\u2764), Map has fully qualified (\u2764\uFE0F)
        if not description and '\uFE0F' not in char:
            char_with_vs = char + '\uFE0F'
            description = EMOJI_MAP.get(char_with_vs)

        if description:
            # FIX: Add prefix "Emoji-yeki" before the description
            return f" ئیمۆجییەکی {description} "

        # If emoji unknown, remove it to avoid silence/errors
        return ""