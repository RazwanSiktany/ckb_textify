import pytest
from ckb_textify.core.types import Token, TokenType, NormalizationConfig
from ckb_textify.modules.taggers import ScriptTagger, UnitTagger


@pytest.fixture
def config():
    return NormalizationConfig()


def test_script_tagger(config):
    # Input: "Hello سڵاو"
    tokens = [
        Token("Hello", "Hello", TokenType.WORD),
        Token("سڵاو", "سڵاو", TokenType.WORD)
    ]

    tagger = ScriptTagger(config)
    tagger.process(tokens)

    assert "SCRIPT_LATIN" in tokens[0].tags
    assert "SCRIPT_KURDISH" in tokens[1].tags


def test_unit_tagger_context(config):
    # Scenario 1: "10 m" -> m should be a UNIT
    # Scenario 2: "I am m" -> m should NOT be a unit

    # [NUMBER: 10] [WORD: m]
    tokens_1 = [
        Token("10", "10", TokenType.NUMBER),
        Token("m", "m", TokenType.WORD)
    ]

    # [WORD: I] [WORD: am] [WORD: m]
    tokens_2 = [
        Token("I", "I", TokenType.WORD),
        Token("am", "am", TokenType.WORD),
        Token("m", "m", TokenType.WORD)
    ]

    tagger = UnitTagger(config)

    # Process Scenario 1
    tagger.process(tokens_1)
    assert "IS_UNIT" in tokens_1[1].tags  # The 'm' after 10

    # Process Scenario 2
    tagger.process(tokens_2)
    assert "IS_UNIT" not in tokens_2[2].tags  # The 'm' after 'am'