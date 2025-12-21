from typing import List
import re
from ckb_textify.core.types import Token, NormalizationConfig
from ckb_textify.core.tokenizer import Tokenizer

# Import Modules
from ckb_textify.modules.web import WebNormalizer
from ckb_textify.modules.phone import PhoneNormalizer
from ckb_textify.modules.date_time import DateTimeNormalizer
from ckb_textify.modules.technical import TechnicalNormalizer
from ckb_textify.modules.math import MathNormalizer
from ckb_textify.modules.currency import CurrencyNormalizer
from ckb_textify.modules.taggers import UnitTagger, ScriptTagger
from ckb_textify.modules.numbers import NumberNormalizer
from ckb_textify.modules.units import UnitNormalizer
from ckb_textify.modules.power import PowerNormalizer
from ckb_textify.modules.diacritics import DiacriticsNormalizer
from ckb_textify.modules.symbols import SymbolNormalizer
from ckb_textify.modules.linguistics import LinguisticsNormalizer
from ckb_textify.modules.transliteration import TransliterationNormalizer
from ckb_textify.modules.spacing import SpacingNormalizer
from ckb_textify.modules.emojis import EmojiNormalizer
from ckb_textify.modules.grammar import GrammarNormalizer  # <--- Added


class Pipeline:
    """
    The main normalization engine. It orchestrates the flow of tokens
    through a series of normalization modules based on the configuration.
    """

    def __init__(self, config: NormalizationConfig = None):
        """Initializes the pipeline with configuration and loads modules."""
        self.config = config or NormalizationConfig()
        self.tokenizer = Tokenizer()

        # List of modules to be executed
        self.modules = []

        # --- High-Priority Rigid Pattern Modules (Run First) ---
        if self.config.enable_web: self.modules.append(WebNormalizer(self.config))
        if self.config.enable_phone: self.modules.append(PhoneNormalizer(self.config))
        if self.config.enable_date_time: self.modules.append(DateTimeNormalizer(self.config))
        if self.config.enable_technical: self.modules.append(TechnicalNormalizer(self.config))
        if self.config.enable_math: self.modules.append(MathNormalizer(self.config))
        if self.config.enable_currency: self.modules.append(CurrencyNormalizer(self.config))

        # --- Taggers and Conversion Modules ---
        if self.config.enable_units:
            # Tagger must run before the converter
            self.modules.append(UnitTagger(self.config))
            self.modules.append(UnitNormalizer(self.config))
            # New Power Normalizer (runs after Units but before Numbers sometimes, priority handles it)
            self.modules.append(PowerNormalizer(self.config))

        if self.config.enable_numbers: self.modules.append(NumberNormalizer(self.config))

        # --- Spacing Normalizer (Crucial to run before final sort, but priority 0 puts it last) ---
        self.modules.append(SpacingNormalizer(self.config))

        # --- Low-Priority Linguistic & Cleanup Modules ---

        # EmojiNormalizer handles emoji_mode check internally
        self.modules.append(EmojiNormalizer(self.config))

        if self.config.enable_symbols: self.modules.append(SymbolNormalizer(self.config))
        if self.config.enable_diacritics: self.modules.append(DiacriticsNormalizer(self.config))

        if self.config.enable_linguistics:
            self.modules.append(ScriptTagger(self.config))
            self.modules.append(LinguisticsNormalizer(self.config))

        if self.config.enable_transliteration:
            self.modules.append(TransliterationNormalizer(self.config))

        # Add Grammar Normalizer (Runs late to catch suffixes on converted text)
        self.modules.append(GrammarNormalizer(self.config))

        # Sort by priority (High -> Low). Priority 0 modules (like SpacingNormalizer) go to the end.
        self.modules.sort(key=lambda m: m.priority, reverse=True)

    def normalize(self, text: str) -> str:
        """
        Processes the input text through the tokenization and normalization pipeline.

        Args:
            text: The raw input string.

        Returns:
            The normalized Sorani Kurdish string.
        """
        # 1. Tokenize the input text
        tokens = self.tokenizer.tokenize(text)

        # 2. Process tokens through all enabled modules
        for module in self.modules:
            tokens = module.process(tokens)

        # 3. Detokenize the tokens back into a single string
        final_text = self.tokenizer.detokenize(tokens)

        # 4. Final cleanup: Collapse whitespace, preserving single newlines.

        # A. Collapse multiple horizontal spaces and tabs to a single space
        final_text = re.sub(r'[ \t]+', ' ', final_text)

        # B. Collapse multiple newlines/carriage returns into a single newline
        final_text = re.sub(r'[\r\n]+', '\n', final_text)

        # C. Remove redundant spaces around single newlines
        final_text = re.sub(r' \n', '\n', final_text)
        final_text = re.sub(r'\n ', '\n', final_text)

        # D. Final strip to remove leading/trailing whitespace (spaces AND newlines)
        return final_text.strip()