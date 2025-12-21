# Abstract Base Class for all normalizers
from abc import ABC, abstractmethod
from typing import List
from ckb_textify.core.types import Token, NormalizationConfig


class Module(ABC):
    """
    Abstract Base Class for all pipeline modules.
    """

    def __init__(self, config: NormalizationConfig):
        self.config = config

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name for the module."""
        pass

    @property
    def priority(self) -> int:
        """
        Execution order. Higher numbers run first.
        100 = Safety (URLs)
        50  = Classification (Taggers)
        10  = Transformation (Text Normalization)
        """
        return 50

    @abstractmethod
    def process(self, tokens: List[Token]) -> List[Token]:
        """
        Modify the tokens in-place or return a new list.
        """
        pass