import pytest
from ckb_textify.core.tokenizer import Tokenizer
from ckb_textify.core.types import NormalizationConfig
from ckb_textify.modules.currency import CurrencyNormalizer


@pytest.fixture
def tokenizer():
    return Tokenizer()


@pytest.fixture
def config():
    return NormalizationConfig()


def test_currency_suffix(tokenizer, config):
    # Case: 100 $ (Suffix)
    tokens = tokenizer.tokenize("100 $")
    normalizer = CurrencyNormalizer(config)
    processed = normalizer.process(tokens)

    assert len(processed) == 1  # Symbol consumed
    # 100 -> سەد, $ -> دۆلار
    assert processed[0].text == "سەد دۆلار"


def test_currency_prefix(tokenizer, config):
    # Case: $ 50 (Prefix)
    tokens = tokenizer.tokenize("$ 50")
    normalizer = CurrencyNormalizer(config)
    processed = normalizer.process(tokens)

    assert processed[0].text == "پەنجا دۆلار"


def test_currency_decimals(tokenizer, config):
    # Case: $ 12.50
    # Note: Tokenizer keeps "12.50" as one token now
    tokens = tokenizer.tokenize("$ 12.50")
    normalizer = CurrencyNormalizer(config)
    processed = normalizer.process(tokens)

    # 12 -> دوازدە دۆلار, 0.50 -> پەنجا سەنت
    assert "دوازدە دۆلار" in processed[0].text
    assert "پەنجا سەنت" in processed[0].text