import pytest
from ckb_textify.core.types import Token, TokenType, NormalizationConfig
from ckb_textify.modules.web import WebNormalizer
from ckb_textify.modules.technical import TechnicalNormalizer


@pytest.fixture
def config():
    return NormalizationConfig()


def test_web_normalizer(config):
    # Test URL
    t1 = Token("www.rudaw.net", "www.rudaw.net", TokenType.URL)
    # Test Email
    t2 = Token("user@gmail.com", "user@gmail.com", TokenType.EMAIL)

    normalizer = WebNormalizer(config)
    normalizer.process([t1, t2])

    # Check Expansion
    assert "دەبڵیو" in t1.text
    assert "دۆت نێت" in t1.text

    assert "ئەت جیمەیڵ" in t2.text
    # FIX: Expect character-by-character spelling (U-S-E-R), not phonetic pronunciation
    # "user" -> u(یو) s(ئێس) e(ئی) r(ئاڕ)
    assert "یوسەر" in t2.text


def test_technical_normalizer(config):
    # Test Hashtag
    t1 = Token("#Kurdistan", "#Kurdistan", TokenType.TECHNICAL)
    # Test Mention
    t2 = Token("@Razwan", "@Razwan", TokenType.TECHNICAL)
    # Test Code (WORD type but matches alphanumeric)
    t3 = Token("A1", "A1", TokenType.WORD)

    normalizer = TechnicalNormalizer(config)
    normalizer.process([t1, t2, t3])

    assert "ھاشتاگ" in t1.text
    assert "ئەت" in t2.text
    assert "ئەی" in t3.text and "یەک" in t3.text  # A1 -> Ay Yek