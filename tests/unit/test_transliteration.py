import pytest
from ckb_textify.core.tokenizer import Tokenizer
from ckb_textify.core.types import Token, TokenType, NormalizationConfig
from ckb_textify.modules.transliteration import TransliterationNormalizer

@pytest.fixture
def tokenizer():
    return Tokenizer()

@pytest.fixture
def config():
    return NormalizationConfig()

def test_english_ipa(config):
    # "Phone" -> IPA is /foʊn/ -> فۆن
    t = Token("Phone", "Phone", TokenType.WORD)
    normalizer = TransliterationNormalizer(config)
    normalizer.process([t])
    assert t.text == "فۆن"

def test_english_fallback(config):
    # "Razwan" -> Might not be in IPA dict -> R(ڕ)a(ا)z(ز)w(و)a(ا)n(ن)
    # Note: R usually maps to ڕ in our fallback
    t = Token("Razwan", "Razwan", TokenType.WORD)
    normalizer = TransliterationNormalizer(config)
    normalizer.process([t])
    assert "ڕازوان" in t.text

def test_foreign_script(config):
    # Russian "Путин" -> "Putin" -> "پوتین"
    t = Token("Путин", "Путин", TokenType.WORD)
    normalizer = TransliterationNormalizer(config)
    normalizer.process([t])
    # P(پ) u(و) t(ت) i(ی) n(ن)
    assert t.text == "پوتین"

def test_ignore_technical(config):
    # A technical token (like a code) should NOT be transliterated
    # even if it looks like words
    t = Token("User", "User", TokenType.TECHNICAL)
    normalizer = TransliterationNormalizer(config)
    normalizer.process([t])
    assert t.text == "User"  # Unchanged