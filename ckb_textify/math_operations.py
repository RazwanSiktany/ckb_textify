# ckb_textify/math_operations.py

import re
from .number_to_text import number_to_kurdish_text
from .decimal_handler import decimal_to_kurdish_text

# --- 1. MATH SYMBOLS & FUNCTIONS ---
MATH_SYMBOLS_MAP = {
    "+": "کۆ",
    "*": "کەڕەتی",
    "-": "کەم",
    "/": "دابەش",
    "=": "یەکسانە",
    "^": "توان",
    "%": "لە سەدا",
}

# Map for common math functions
MATH_FUNCTIONS_MAP = {
    "ln": "لەین",
    "log": "لۆگ",
    "sin": "ساین",
    "cos": "کۆساین",
    "tan": "تانجێنت",
    "lim": "لیمێت",
}

SCIENTIFIC_THRESHOLD = 1_000_000_000_000_000_000_000

# --- 2. REGEX PATTERNS ---

# A "Math Term" can be:
# 1. A Number (12.5)
# 2. A Function + Number (ln 4)
# 3. Just a Function (ln)
# We use this to detect "Math / Math" patterns.
func_pattern = "|".join(re.escape(k) for k in MATH_FUNCTIONS_MAP.keys())
# Regex parts: (Function)? + (Space)? + (Number)
term_pattern = rf"(?:(?:{func_pattern})\s*)?\d+(?:\.\d+)?|(?:{func_pattern})"

# Matches: Term + Symbol + Term
# e.g. "5 + 3", "ln 4 / ln 3", "log 10 / 2"
MATH_EXPRESSION_RE = re.compile(
    rf"({term_pattern})\s*(" +
    r"|".join(re.escape(k) for k in MATH_SYMBOLS_MAP.keys()) +
    rf")\s*({term_pattern})",
    re.IGNORECASE
)

NEGATIVE_SIGN_RE = re.compile(r"(^|\s)-(\d+(\.\d+)?)")
POSITIVE_SIGN_RE = re.compile(r"(^|\s)\+(\d+(\.\d+)?)")


# --- 3. Functions ---

def _process_single_term(term_str: str) -> str:
    """
    Converts a single math term like "ln 4" or "12.5" to Kurdish.
    """
    term_str = term_str.strip()

    # Check if it starts with a function (e.g. "ln 4")
    for func_key, func_val in MATH_FUNCTIONS_MAP.items():
        # Check if term starts with "ln" (case insensitive)
        if term_str.lower().startswith(func_key):
            # Remove the function name to get the number part
            number_part = term_str[len(func_key):].strip()

            # If there is a number, convert it
            if number_part:
                converted_num = convert_number_to_text_handler(number_part)
                return f"{func_val} {converted_num}"
            else:
                # It's just "ln"
                return func_val

    # If no function, it's just a number
    return convert_number_to_text_handler(term_str)


def convert_number_to_text_handler(number_str: str) -> str:
    # 1. Check for float first
    if "." in number_str:
        try:
            num_f = float(number_str)
            return decimal_to_kurdish_text(num_f)
        except ValueError:
            return number_str

    # 2. Handle as integer
    try:
        # Handle Leading Zeros
        zeros_prefix = ""
        is_all_zeros = False
        if number_str.startswith("0") and len(number_str) > 1:
            zeros_count = 0
            for char in number_str:
                if char == '0':
                    zeros_count += 1
                else:
                    break

            if zeros_count == len(number_str): is_all_zeros = True

            if zeros_count <= 2:
                zeros_text = " ".join(["سفر"] * zeros_count)
            else:
                count_text = number_to_kurdish_text(zeros_count)
                zeros_text = f"{count_text} جار سفر"

            if is_all_zeros: return zeros_text
            zeros_prefix = f"{zeros_text} "

        # Standard Integer
        num = int(number_str)
        result_text = ""
        if num >= SCIENTIFIC_THRESHOLD:
            sci_str = f"{num:.3e}"
            parts = sci_str.split('e')
            mantissa_val = float(parts[0])
            exponent_val = int(parts[1].lstrip('+'))
            mantissa_text = decimal_to_kurdish_text(mantissa_val)
            exponent_text = number_to_kurdish_text(exponent_val)
            result_text = f"{mantissa_text} جارانی دە توانی {exponent_text}"
        else:
            result_text = number_to_kurdish_text(num)

        return f"{zeros_prefix}{result_text}"

    except ValueError:
        return number_str


def normalize_math_expressions(text: str) -> str:
    """
    Normalizes math expressions, including functions like ln, log, sin.
    """

    # Handle "Negative" (سالب)
    text = NEGATIVE_SIGN_RE.sub(
        lambda m: f"{m.group(1)}سالب {convert_number_to_text_handler(m.group(2))}",
        text
    )

    # Handle "Positive" (کۆ)
    text = POSITIVE_SIGN_RE.sub(
        lambda m: f"{m.group(1)}کۆ {convert_number_to_text_handler(m.group(2))}",
        text
    )

    # Handle Math Expressions (e.g. "ln 4 / ln 3" or "5 + 3")
    def _replace_expression(match):
        left_term = match.group(1)  # e.g. "ln 4"
        symbol = match.group(2)  # e.g. "/"
        right_term = match.group(3)  # e.g. "ln 3"

        left_kurdish = _process_single_term(left_term)
        symbol_kurdish = MATH_SYMBOLS_MAP[symbol]
        right_kurdish = _process_single_term(right_term)

        return f"{left_kurdish} {symbol_kurdish} {right_kurdish}"

    text = MATH_EXPRESSION_RE.sub(_replace_expression, text)

    return text