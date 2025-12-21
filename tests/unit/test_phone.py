import pytest
from ckb_textify.core.tokenizer import Tokenizer
from ckb_textify.core.types import TokenType, NormalizationConfig
from ckb_textify.modules.phone import PhoneNormalizer


@pytest.fixture
def tokenizer():
    return Tokenizer()


@pytest.fixture
def config():
    return NormalizationConfig()


def test_local_phone(tokenizer, config):
    # 0750 123 45 67
    text = "07501234567"
    tokens = tokenizer.tokenize(text)

    # Ensure Tokenizer picked it up as PHONE
    assert tokens[0].type == TokenType.PHONE

    norm = PhoneNormalizer(config)
    norm.process(tokens)

    # 0750 -> sifir heft sed w penja
    # 123 -> sed w bist w se
    # 45 -> chil w penj
    # 67 -> shest w hewt
    assert "سفر حەوت سەد و پەنجا" in tokens[0].text
    assert "شەست و حەوت" in tokens[0].text


def test_international_phone(tokenizer, config):
    # +964 770 123 4567
    text = "+9647701234567"
    tokens = tokenizer.tokenize(text)

    norm = PhoneNormalizer(config)
    norm.process(tokens)

    assert "کۆ نۆ سەد و شەست و چوار" in tokens[0].text