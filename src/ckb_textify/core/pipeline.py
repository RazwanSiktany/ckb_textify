from typing import List
import re
from ckb_textify.core.types import Token, NormalizationConfig, TokenType
from ckb_textify.core.tokenizer import Tokenizer
from ckb_textify.resources.ali_k_map import ALI_K_MAP, ALI_K_KEYS
from ckb_textify.utils.detector import is_ali_k_text

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
from ckb_textify.modules.grammar import GrammarNormalizer


class Pipeline:
    """
    The main normalization engine. It orchestrates the flow of tokens
    through a series of normalization modules based on the configuration.
    """

    # Regex to split text into segments (sentences/lines) for mixed-script detection
    SENTENCE_SPLIT_RE = re.compile(r'([.\n!؟?;]+)')

    def __init__(self, config: NormalizationConfig = None):
        """Initializes the pipeline with configuration and loads modules."""
        self.config = config or NormalizationConfig()
        self.tokenizer = Tokenizer()

        # List of modules to be executed
        self.modules = []

        # --- High-Priority Rigid Pattern Modules ---
        if self.config.enable_web: self.modules.append(WebNormalizer(self.config))
        if self.config.enable_phone: self.modules.append(PhoneNormalizer(self.config))
        if self.config.enable_date_time: self.modules.append(DateTimeNormalizer(self.config))
        if self.config.enable_technical: self.modules.append(TechnicalNormalizer(self.config))
        if self.config.enable_math: self.modules.append(MathNormalizer(self.config))
        if self.config.enable_currency: self.modules.append(CurrencyNormalizer(self.config))

        # --- Taggers and Conversion Modules ---
        if self.config.enable_units:
            self.modules.append(UnitTagger(self.config))
            self.modules.append(UnitNormalizer(self.config))
            self.modules.append(PowerNormalizer(self.config))

        if self.config.enable_numbers:
            self.modules.append(NumberNormalizer(self.config))

        # --- Spacing Normalizer (Priority 0 puts it last in sorted list) ---
        self.modules.append(SpacingNormalizer(self.config))

        # --- Low-Priority Linguistic & Cleanup Modules ---
        self.modules.append(EmojiNormalizer(self.config))

        if self.config.enable_symbols: self.modules.append(SymbolNormalizer(self.config))
        if self.config.enable_diacritics: self.modules.append(DiacriticsNormalizer(self.config))

        if self.config.enable_linguistics:
            # ScriptTagger is vital for identifying generic scripts
            self.modules.append(ScriptTagger(self.config))
            self.modules.append(LinguisticsNormalizer(self.config))

        if self.config.enable_transliteration:
            self.modules.append(TransliterationNormalizer(self.config))

        self.modules.append(GrammarNormalizer(self.config))

        # Sort modules by priority (High -> Low)
        self.modules.sort(key=lambda m: m.priority, reverse=True)

    def normalize(self, text: str) -> str:
        """
        Processes the input text through the tokenization and normalization pipeline.
        """
        # 0. Pre-processing: Ali-K Decoding
        if self.config.decode_ali_k:
            # SAFETY IMPROVEMENT:
            # Identify actual Quranic/Arabic text by looking for Sukun or Tanween.
            # These markers are ubiquitous in vocalized Arabic but NEVER used in Ali-K Kurdish hacks.
            quran_exclusive_re = re.compile(r"[\u064B\u064C\u064D\u0652]")

            segments = self.SENTENCE_SPLIT_RE.split(text)
            processed_segments = []
            for segment in segments:
                # If a segment contains Quran-exclusive markers, we skip Ali-K decoding
                # to protect the Arabic pronunciation.
                is_actually_vocalized_arabic = bool(quran_exclusive_re.search(segment))

                if not is_actually_vocalized_arabic and is_ali_k_text(segment):
                    # Apply mapping for legacy font character hacks
                    for key in ALI_K_KEYS:
                        if key in segment:
                            segment = segment.replace(key, ALI_K_MAP[key])
                processed_segments.append(segment)
            text = "".join(processed_segments)

        # 0.1 Pre-processing: Fix "Fake Ae" artifacts
        text = re.sub(r"\u0647[\u200b\u200c\u0020]", "\u06d5", text)

        # 1. Tokenize the input text
        tokens = self.tokenizer.tokenize(text)

        # 2. Process tokens through all enabled modules
        for module in self.modules:
            tokens = module.process(tokens)

        # 3. Post-processing: Quranic Ayah End Logic
        # Detect if the context contains Arabic diacritics to identify Quranic verses.
        arabic_diacritics_re = re.compile(r"[\u064B-\u0652\u0670\u06E1\u06D6-\u06ED]")

        for i in range(len(tokens)):
            token = tokens[i]
            is_num = token.type == TokenType.NUMBER or "NUMBER" in token.tags or token.original_text.isdigit()

            if is_num and i > 0:
                prev_token = None
                for j in range(i - 1, -1, -1):
                    if tokens[j].text.strip():
                        prev_token = tokens[j]
                        break

                if prev_token and arabic_diacritics_re.search(prev_token.original_text):
                    if not token.text.endswith("."):
                        token.text += "."
                        if not token.whitespace_after:
                            token.whitespace_after = " "

        # 4. Detokenize the tokens back into a single string
        final_text = self.tokenizer.detokenize(tokens)

        # 5. Final whitespace cleanup
        final_text = re.sub(r'[ \t]+', ' ', final_text)
        final_text = re.sub(r'[\r\n]+', '\n', final_text)
        final_text = re.sub(r' \n', '\n', final_text)
        final_text = re.sub(r'\n ', '\n', final_text)

        return final_text.strip()