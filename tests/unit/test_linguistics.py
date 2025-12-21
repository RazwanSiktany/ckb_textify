import pytest
from ckb_textify.core.tokenizer import Tokenizer
from ckb_textify.core.types import Token, TokenType, NormalizationConfig
from ckb_textify.modules.linguistics import LinguisticsNormalizer


@pytest.fixture
def tokenizer():
    return Tokenizer()


@pytest.fixture
def config():
    return NormalizationConfig()


def test_abbreviations(tokenizer, config):
    # د. needs to be tokenized correctly.
    # Note: Our current tokenizer might split "د." into "د" and ".".
    # Let's check how the Tokenizer handles it first.
    # If it splits, we might need a specific Tokenizer rule or handling logic.
    # For now, let's assume the user types "د." and we want "دکتۆر".

    # If input is "د.", tokenizer might produce [WORD(د), SYMBOL(.)]
    # In V2, we prefer not to use regex lookaheads in tokenizer for every abbreviation.
    # However, let's test the simple case first: "هتد" (Etc)

    tokens = tokenizer.tokenize("هتد")
    normalizer = LinguisticsNormalizer(config)
    normalizer.process(tokens)
    assert tokens[0].text == "ھەتا دوایی"


def test_arabic_names(tokenizer, config):
    # علي -> عەلی
    tokens = tokenizer.tokenize("علي")
    normalizer = LinguisticsNormalizer(config)
    normalizer.process(tokens)
    assert tokens[0].text == "عەلی"


def test_char_normalization(tokenizer, config):
    # كتاب -> کتاب (Kaf fix)
    tokens = tokenizer.tokenize("كتاب")
    normalizer = LinguisticsNormalizer(config)
    normalizer.process(tokens)
    assert tokens[0].text == "کتاب"

    # Tatweel removal: تـە -> تە
    tokens = tokenizer.tokenize("تـە")
    normalizer.process(tokens)
    assert tokens[0].text == "تە"