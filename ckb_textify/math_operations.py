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
    "=": "یەکسانە بە",
    "^": "توان",
    "%": "لە سەدا",
}

MATH_FUNCTIONS_MAP = {
    "ln": "لۆگاریتمی سروشتی",
    "log": "لۆگاریتمی",
    "sin": "ساینی",
    "cos": "کۆساینی",
    "tan": "تانجێنتی",
    "lim": "لیمێتی",
}

# Thresholds
LARGE_THRESHOLD = 1_000_000_000_000_000_000_000  # 10^21
SMALL_THRESHOLD = 0.0001

# --- 2. REGEX PATTERNS ---
func_pattern = "|".join(re.escape(k) for k in MATH_FUNCTIONS_MAP.keys())
term_pattern = rf"(?:(?:{func_pattern})\s*)?\d+(?:\.\d+)?|(?:{func_pattern})"

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
    term_str = term_str.strip()
    for func_key, func_val in MATH_FUNCTIONS_MAP.items():
        if term_str.lower().startswith(func_key):
            number_part = term_str[len(func_key):].strip()
            if number_part:
                converted_num = convert_number_to_text_handler(number_part)
                return f"{func_val} {converted_num}"
            else:
                return func_val
    return convert_number_to_text_handler(term_str)


def _format_scientific(num_val: float) -> str:
    """
    Helper to format any number into Kurdish scientific notation.
    """
    sci_str = f"{num_val:.3e}"
    parts = sci_str.split('e')

    mantissa_val = float(parts[0])
    exponent_val = int(parts[1].lstrip('+'))

    mantissa_text = decimal_to_kurdish_text(mantissa_val)
    exponent_text = number_to_kurdish_text(exponent_val)

    return f"{mantissa_text} جارانی دە توانی {exponent_text}"


def convert_number_to_text_handler(number_str: str) -> str:
    """
    Smart handler for Integers, Decimals, and Scientific Notation.
    """
    # 1. Handle strings that are already scientific (e.g., "5e-23")
    if "e" in number_str.lower():
        try:
            val = float(number_str)
            return _format_scientific(val)
        except ValueError:
            pass  # Fall through

    # 2. Handle Decimals (Float)
    if "." in number_str:
        try:
            num_f = float(number_str)
            # Check for tiny numbers (Power Method)
            if 0 < abs(num_f) < SMALL_THRESHOLD:
                return _format_scientific(num_f)
            # Check for massive numbers
            if abs(num_f) >= LARGE_THRESHOLD:
                return _format_scientific(num_f)

            return decimal_to_kurdish_text(num_f)
        except ValueError:
            return number_str

    # 3. Handle Integers
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

        if num >= LARGE_THRESHOLD:
            return _format_scientific(float(num))
        else:
            result_text = number_to_kurdish_text(num)

        return f"{zeros_prefix}{result_text}"

    except ValueError:
        return number_str


def normalize_math_expressions(text: str) -> str:
    text = NEGATIVE_SIGN_RE.sub(
        lambda m: f"{m.group(1)}سالب {convert_number_to_text_handler(m.group(2))}",
        text
    )
    text = POSITIVE_SIGN_RE.sub(
        lambda m: f"{m.group(1)}کۆ {convert_number_to_text_handler(m.group(2))}",
        text
    )

    def _replace_expression(match):
        left_term = match.group(1)
        symbol = match.group(2)
        right_term = match.group(3)
        left_kurdish = _process_single_term(left_term)
        symbol_kurdish = MATH_SYMBOLS_MAP[symbol]
        right_kurdish = _process_single_term(right_term)
        return f"{left_kurdish} {symbol_kurdish} {right_kurdish}"

    text = MATH_EXPRESSION_RE.sub(_replace_expression, text)
    return text