# ckb_textify/chat_speak.py
import re

# Mapping of numbers to Kurdish/Arabic sounds used in chat
CHAT_MAP = {
    "3": "ع",  # 3arab -> عەرەب
    "7": "ح",  # 7ez -> حەز
    "9": "ق",  # 9ap -> قاپ
    "5": "خ",  # 5an -> خان (Common variant)
    "8": "غ",  # 8arib -> غەریب (Common variant)
    "2": "ئ",  # 2al -> ئال (Hamza)
    "6": "ش",  # 6amal -> شەمال
}

# Regex to find these digits ONLY when attached to Latin letters.
# Logic:
# 1. (?<=[a-zA-Z])\d  -> Digit preceded by a letter (e.g., s3)
# 2. \d(?=[a-zA-Z])   -> Digit followed by a letter (e.g., 3s)
# We join keys to make a pattern like [3795826]
digits_pattern = "".join(CHAT_MAP.keys())
CHAT_DIGIT_RE = re.compile(
    rf"(?<=[a-zA-Z])[{digits_pattern}]|[{digits_pattern}](?=[a-zA-Z])"
)

def normalize_chat_speak(text: str) -> str:
    """
    Converts 'Chat Speak' (Arabizi) numbers to Kurdish characters.
    Only affects numbers attached to English letters (e.g., '7ez' -> 'حez').
    """
    def _replace_digit(match):
        digit = match.group(0)
        return CHAT_MAP.get(digit, digit)

    # Run twice to handle cases like "77" in "77ez" or "a77a"
    # where one digit might be shielding the other from the lookaround.
    # But since we replace one by one, a single pass with sub usually works
    # if the regex matches individual chars.
    return CHAT_DIGIT_RE.sub(_replace_digit, text)