import pytest
from ckb_textify.core.tokenizer import Tokenizer
from ckb_textify.core.types import NormalizationConfig
from ckb_textify.modules.math import MathNormalizer


@pytest.fixture
def tokenizer():
    return Tokenizer()


@pytest.fixture
def config():
    return NormalizationConfig()


def test_basic_operators(tokenizer, config):
    # 5 + 3
    tokens = tokenizer.tokenize("5 + 3")
    normalizer = MathNormalizer(config)
    processed = normalizer.process(tokens)

    # + should become "کۆ"
    assert processed[1].text == "کۆ"


def test_fractions(tokenizer, config):
    # 1/2 -> نیوە
    tokens = tokenizer.tokenize("1/2")
    normalizer = MathNormalizer(config)
    processed = normalizer.process(tokens)

    assert len(processed) == 1  # Merged into one token
    assert processed[0].text == "نیوە"

    # 1/4 -> چارەک
    tokens = tokenizer.tokenize("1/4")
    processed = normalizer.process(tokens)
    assert processed[0].text == "چارەک"


def test_scientific_notation_tokenization(tokenizer):
    # This tests the PATTERN update more than the math module
    tokens = tokenizer.tokenize("5e-10")
    assert len(tokens) == 1
    assert tokens[0].text == "5e-10"