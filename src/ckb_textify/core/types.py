from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Set


class TokenType(Enum):
    WORD = auto()
    NUMBER = auto()
    SYMBOL = auto()
    URL = auto()
    EMAIL = auto()
    PHONE = auto()
    DATE = auto()
    TIME = auto()
    TECHNICAL = auto()
    FOREIGN = auto()
    SUBSCRIPT = auto()
    SUPERSCRIPT = auto()
    UNKNOWN = auto()


@dataclass
class Token:
    text: str
    original_text: str
    type: TokenType
    tags: Set[str] = field(default_factory=set)
    whitespace_after: str = ""

    @property
    def is_converted(self) -> bool:
        """Returns True if the text has changed from the original."""
        return self.text != self.original_text

    def __repr__(self):
        return f"Token({self.type.name}: '{self.text}')"


@dataclass
class NormalizationConfig:
    # --- Feature Toggles ---
    enable_web: bool = True
    enable_phone: bool = True
    enable_date_time: bool = True
    enable_technical: bool = True
    enable_math: bool = True
    enable_currency: bool = True
    enable_units: bool = True
    enable_numbers: bool = True
    enable_symbols: bool = True
    enable_linguistics: bool = True
    enable_transliteration: bool = True
    enable_diacritics: bool = True

    # --- Pre-processing ---
    decode_ali_k: bool = False

    # --- Behaviors ---
    emoji_mode: str = "remove"
    diacritics_mode: str = "convert"
    shadda_mode: str = "double"

    # --- TTS/G2P Specific ---
    enable_pause_markers: bool = False
    pause_token: str = "|"