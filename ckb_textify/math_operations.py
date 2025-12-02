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
    "≈": "نزیکەی",
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
# Regex for a single term (Number OR Function+Number)
# handle scientific notation inside terms
term_pattern = rf"(?:(?:{func_pattern})\s*)?\d+(?:\.\d+)?(?:e[+-]?\d+)?|(?:{func_pattern})"

# Regex for Operators
op_pattern = r"[" + r"".join(re.escape(k) for k in MATH_SYMBOLS_MAP.keys()) + r"]"

# Math Chain Regex (Requires Operator)
MATH_CHAIN_RE = re.compile(
    rf"((?:{term_pattern})\s*(?:{op_pattern}\s*(?:{term_pattern})\s*)+)",
    re.IGNORECASE
)

# Matches 5e-23, 1.5E+10, etc.
SCIENTIFIC_NOTATION_RE = re.compile(r"\b\d+(?:\.\d+)?e[+-]?\d+\b", re.IGNORECASE)

# Matches: Function + optional ( + number + optional )
# e.g. "ln 150", "sin(90)"
STANDALONE_FUNC_RE = re.compile(
    rf"\b({func_pattern})\s*\(?\s*(\d+(?:\.\d+)?(?:e[+-]?\d+)?)\s*\)?",
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
            # Remove potential parens from inside the term string if captured by chain regex
            number_part = number_part.strip("()")
            if number_part:
                converted_num = convert_number_to_text_handler(number_part)
                return f"{func_val} {converted_num}"
            else:
                return func_val
    return convert_number_to_text_handler(term_str)


def _format_scientific(num_val: float) -> str:
    sci_str = f"{num_val:.3e}"
    parts = sci_str.split('e')

    mantissa_val = float(parts[0])
    exponent_val = int(parts[1].lstrip('+'))

    mantissa_text = decimal_to_kurdish_text(mantissa_val)
    exponent_text = number_to_kurdish_text(exponent_val)

    return f"{mantissa_text} جارانی دە توانی {exponent_text}"


def convert_number_to_text_handler(number_str: str) -> str:
    # 1. Handle scientific notation strings (e.g. "5e-23")
    if "e" in number_str.lower():
        try:
            val = float(number_str)
            return _format_scientific(val)
        except ValueError:
            pass

    # 2. Handle Decimals
    if "." in number_str:
        try:
            num_f = float(number_str)
            if 0 < abs(num_f) < SMALL_THRESHOLD:
                return _format_scientific(num_f)
            if abs(num_f) >= LARGE_THRESHOLD:
                return _format_scientific(num_f)
            return decimal_to_kurdish_text(num_f)
        except ValueError:
            return number_str

    # 3. Handle Integers
    try:
        # Leading Zeros
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

        num = int(number_str)
        if num >= LARGE_THRESHOLD:
            return _format_scientific(float(num))
        else:
            result_text = number_to_kurdish_text(num)

        return f"{zeros_prefix}{result_text}"

    except ValueError:
        return number_str


def normalize_math_expressions(text: str) -> str:
    # 1. Handle Standalone Scientific Notation
    text = SCIENTIFIC_NOTATION_RE.sub(
        lambda m: convert_number_to_text_handler(m.group(0)),
        text
    )

    # 2. Handle Math Chains (e.g. "6/6/9" or "ln 4 / ln 3")
    # MOVED UP: Must run before Standalone Functions to correctly handle operators
    def _replace_chain(match):
        full_chain = match.group(0)
        tokens = re.split(rf"(\s*{op_pattern}\s*)", full_chain)

        result = []
        for token in tokens:
            if not token.strip(): continue

            clean_token = token.strip()

            if clean_token in MATH_SYMBOLS_MAP:
                result.append(MATH_SYMBOLS_MAP[clean_token])
            else:
                result.append(_process_single_term(token))

        return " ".join(result)

    text = MATH_CHAIN_RE.sub(_replace_chain, text)

    # 3. Handle Standalone Functions (e.g. ln 150)
    # Runs after chains to catch anything left over
    text = STANDALONE_FUNC_RE.sub(
        lambda m: f"{MATH_FUNCTIONS_MAP[m.group(1).lower()]} {convert_number_to_text_handler(m.group(2))}",
        text
    )

    # 4. Handle Unary Signs
    text = NEGATIVE_SIGN_RE.sub(
        lambda m: f"{m.group(1)}سالب {convert_number_to_text_handler(m.group(2))}",
        text
    )
    text = POSITIVE_SIGN_RE.sub(
        lambda m: f"{m.group(1)}کۆ {convert_number_to_text_handler(m.group(2))}",
        text
    )

    return text