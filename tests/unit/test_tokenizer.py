import pytest
from ckb_textify.core.tokenizer import Tokenizer
from ckb_textify.core.types import TokenType


# Fixture: Creates a fresh tokenizer for every test function
@pytest.fixture
def tokenizer():
    return Tokenizer()


def test_basic_tokenization(tokenizer):
    text = "Hello 123!"
    tokens = tokenizer.tokenize(text)

    # We expect 3 tokens: "Hello", "123", "!"
    assert len(tokens) == 3

    assert tokens[0].text == "Hello"
    assert tokens[0].type == TokenType.WORD
    # The space between "Hello" and "123" is attached to "Hello"
    assert tokens[0].whitespace_after == " "

    assert tokens[1].text == "123"
    assert tokens[1].type == TokenType.NUMBER

    assert tokens[2].text == "!"
    assert tokens[2].type == TokenType.SYMBOL


def test_rigid_patterns(tokenizer):
    """Ensure URLs and Emails are preserved as single tokens."""
    text = "Visit www.rudaw.net or mail test@gmail.com"
    tokens = tokenizer.tokenize(text)

    # Check URL
    url_token = next(t for t in tokens if t.type == TokenType.URL)
    assert url_token.text == "www.rudaw.net"

    # Check Email
    email_token = next(t for t in tokens if t.type == TokenType.EMAIL)
    assert email_token.text == "test@gmail.com"


def test_technical_patterns(tokenizer):
    """Ensure Hashtags and Mentions are detected."""
    text = "#Kurdistan @Official"
    tokens = tokenizer.tokenize(text)

    assert tokens[0].type == TokenType.TECHNICAL
    assert tokens[0].text == "#Kurdistan"

    assert tokens[1].type == TokenType.TECHNICAL
    assert tokens[1].text == "@Official"


def test_fidelity(tokenizer):
    """
    Round-trip Test: Input -> Tokenize -> Detokenize -> Output.
    The output should match the input (ignoring leading whitespace for now).
    """
    inputs = [
        "Simple sentence.",
        "Numbers: 1, 2, 3.",
        "URLs: https://google.com/path?query=1",
        "Mixed script: سڵاو Hello 123"
    ]

    for text in inputs:
        tokens = tokenizer.tokenize(text)
        result = tokenizer.detokenize(tokens)
        assert result == text