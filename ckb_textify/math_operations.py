# ckb_textify/math_operations.py

import re
from .number_to_text import number_to_kurdish_text
from .decimal_handler import decimal_to_kurdish_text

# --- 1. MATH SYMBOLS & FUNCTIONS ---
MATH_SYMBOLS_MAP = {
    "+": "کۆ",
    "*": "کەڕەتی",
    "-": "کەم",
    "/": "دابەش",  # Default, changes to 'لەسەر' etc. in fraction context
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
term_pattern = rf"(?:(?:{func_pattern})\s*)?\d+(?:\.\d+)?(?:e[+-]?\d+)?|(?:{func_pattern})"

# Regex for Operators
op_pattern = r"[" + r"".join(re.escape(k) for k in MATH_SYMBOLS_MAP.keys()) + r"]"

# Math Chain Regex (Requires Operator)
# Matches sequence of: Term + (Op + Term) repeated
MATH_CHAIN_RE = re.compile(
    rf"((?:{term_pattern})\s*(?:{op_pattern}\s*(?:{term_pattern})\s*)+)",
    re.IGNORECASE
)

SCIENTIFIC_NOTATION_RE = re.compile(r"\b\d+(?:\.\d+)?e[+-]?\d+\b", re.IGNORECASE)
STANDALONE_FUNC_RE = re.compile(rf"\b({func_pattern})\s*\(?\s*(\d+(?:\.\d+)?(?:e[+-]?\d+)?)\s*\)?", re.IGNORECASE)

NEGATIVE_SIGN_RE = re.compile(r"(^|\s)-(\d+(\.\d+)?)")
POSITIVE_SIGN_RE = re.compile(r"(^|\s)\+(\d+(\.\d+)?)")


# --- 3. Functions ---

def _process_single_term(term_str: str) -> str:
    term_str = term_str.strip()
    for func_key, func_val in MATH_FUNCTIONS_MAP.items():
        if term_str.lower().startswith(func_key):
            number_part = term_str[len(func_key):].strip()
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
    if "e" in number_str.lower():
        try:
            val = float(number_str)
            return _format_scientific(val)
        except ValueError:
            pass

    if "." in number_str:
        try:
            num_f = float(number_str)
            if 0 < abs(num_f) < SMALL_THRESHOLD: return _format_scientific(num_f)
            if abs(num_f) >= LARGE_THRESHOLD: return _format_scientific(num_f)
            return decimal_to_kurdish_text(num_f)
        except ValueError:
            return number_str

    try:
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
    # 1. Handle Scientific Notation
    text = SCIENTIFIC_NOTATION_RE.sub(lambda m: convert_number_to_text_handler(m.group(0)), text)

    # 2. Handle Math Chains with Context-Aware Fraction Logic
    def _replace_chain(match):
        full_chain = match.group(0)
        # Split by operators, keeping them
        tokens = re.split(rf"(\s*{op_pattern}\s*)", full_chain)

        # We need to iterate carefully to spot fractions (A / B)
        # processed_tokens will store the final Kurdish parts
        processed_tokens = []

        i = 0
        while i < len(tokens):
            token = tokens[i]
            clean_token = token.strip()

            if not clean_token:
                # Keep whitespace tokens as space
                if token: processed_tokens.append(" ")
                i += 1
                continue

            # Check if this token is a Division Operator '/'
            if clean_token == '/':
                # Look back and forward for simple numbers
                prev_idx = i - 1
                next_idx = i + 1

                # Find valid previous term (skip whitespace)
                while prev_idx >= 0 and not tokens[prev_idx].strip():
                    prev_idx -= 1

                # Find valid next term (skip whitespace)
                while next_idx < len(tokens) and not tokens[next_idx].strip():
                    next_idx += 1

                is_fraction = False
                if prev_idx >= 0 and next_idx < len(tokens):
                    prev_term = tokens[prev_idx].strip()
                    next_term = tokens[next_idx].strip()

                    # Check if both are single digits 1-9
                    if prev_term.isdigit() and next_term.isdigit():
                        num = int(prev_term)
                        denom = int(next_term)

                        if 1 <= num <= 9 and 1 <= denom <= 9:
                            # It is a small fraction!
                            is_fraction = True

                            while processed_tokens and not processed_tokens[-1].strip():
                                processed_tokens.pop()  # Remove trailing spaces
                            if processed_tokens:
                                processed_tokens.pop()  # Remove the converted numerator

                            # Generate Fraction Text
                            frac_text = ""
                            if num == 1 and denom == 2:
                                frac_text = "نیوە"
                            elif num == 1 and denom == 4:
                                frac_text = "چارەک"
                            elif num == 1:
                                frac_text = f"{number_to_kurdish_text(denom)}یەک"
                            else:
                                frac_text = f"{number_to_kurdish_text(num)} لەسەر {number_to_kurdish_text(denom)}"

                            processed_tokens.append(frac_text)

                            # Skip the next term (denominator) in the main loop
                            i = next_idx + 1
                            continue

            # If not a fraction, or handled above
            if clean_token in MATH_SYMBOLS_MAP:
                processed_tokens.append(MATH_SYMBOLS_MAP[clean_token])
            else:
                processed_tokens.append(_process_single_term(token))

            i += 1

        return " ".join(processed_tokens)

    text = MATH_CHAIN_RE.sub(_replace_chain, text)

    # 3. Standalone Functions
    text = STANDALONE_FUNC_RE.sub(
        lambda m: f"{MATH_FUNCTIONS_MAP[m.group(1).lower()]} {convert_number_to_text_handler(m.group(2))}",
        text
    )

    # 4. Unary Signs
    text = NEGATIVE_SIGN_RE.sub(lambda m: f"{m.group(1)}سالب {convert_number_to_text_handler(m.group(2))}", text)
    text = POSITIVE_SIGN_RE.sub(lambda m: f"{m.group(1)}کۆ {convert_number_to_text_handler(m.group(2))}", text)

    return text