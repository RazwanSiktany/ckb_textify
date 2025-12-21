import pytest
from ckb_textify.core.tokenizer import Tokenizer
from ckb_textify.core.types import NormalizationConfig
from ckb_textify.modules.numbers import NumberNormalizer


@pytest.fixture
def tokenizer():
    return Tokenizer()


@pytest.fixture
def config():
    return NormalizationConfig()


def test_integers(tokenizer, config):
    tokens = tokenizer.tokenize("123")
    normalizer = NumberNormalizer(config)
    normalizer.process(tokens)
    assert tokens[0].text == "سەد و بیست و سێ"


def test_decimals(tokenizer, config):
    # 3.14
    tokens = tokenizer.tokenize("3.14")
    normalizer = NumberNormalizer(config)
    normalizer.process(tokens)
    assert "سێ پۆینت چواردە" in tokens[0].text


def test_half_rule(tokenizer, config):
    # 2.5 -> du w niw
    tokens = tokenizer.tokenize("2.5")
    normalizer = NumberNormalizer(config)
    normalizer.process(tokens)
    assert tokens[0].text == "دوو و نیو"


def test_negative_numbers(tokenizer, config):
    # -5
    tokens = tokenizer.tokenize("-5")
    normalizer = NumberNormalizer(config)
    # The normalizer merges "-" and "5"
    processed = normalizer.process(tokens)

    # Processed list should have 1 token (the minus is consumed)
    assert len(processed) == 1
    assert processed[0].text == "سالب پێنج"