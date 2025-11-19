# ckb_textify/math_operations.py

import re
from .number_to_text import number_to_kurdish_text
from .decimal_handler import decimal_to_kurdish_text

# --- 1. MATH_SYMBOLS_MAP (No Changes) ---
MATH_SYMBOLS_MAP = {
    "+": "کۆ",
    "*": "کەڕەتی",
    "-": "کەم",
    "/": "دابەش",
    "=": "یەکسانە",
    "^": "توان",
    "%": "لە سەدا",
}

# --- 2. CONSTANTS (No Changes) ---
SCIENTIFIC_THRESHOLD = 1_000_000_000_000_000_000_000

# --- 3. REGEX PATTERNS (No Changes) ---
MATH_SYMBOLS_SPACED_RE = re.compile(
    r"(\d+(\.\d+)?)\s*(" + r"|".join(re.escape(k) for k in MATH_SYMBOLS_MAP.keys()) + r")\s*(\d+(\.\d+)?)"
)
MATH_NO_SPACE_RE = re.compile(
    r"(\d+(\.\d+)?)(" + r"|".join(re.escape(k) for k in MATH_SYMBOLS_MAP.keys()) + r")(\d+(\.\d+)?)"
)
NEGATIVE_SIGN_RE = re.compile(r"(^|\s)-(\d+(\.\d+)?)")
POSITIVE_SIGN_RE = re.compile(r"(^|\s)\+(\d+(\.\d+)?)")


# --- 4. UPDATED: convert_number_to_text_handler ---
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
        # --- NEW: Handle Leading Zeros with Count Logic ---
        zeros_prefix = ""
        is_all_zeros = False

        if number_str.startswith("0") and len(number_str) > 1:
            # Count leading zeros
            zeros_count = 0
            for char in number_str:
                if char == '0':
                    zeros_count += 1
                else:
                    break

            # Check if the number is ALL zeros (e.g., "000")
            if zeros_count == len(number_str):
                is_all_zeros = True

            # --- Apply the Rule ---
            # Rule 1: 1 or 2 zeros -> "سفر" or "سفر سفر"
            if zeros_count <= 2:
                zeros_text = " ".join(["سفر"] * zeros_count)
            # Rule 2: > 2 zeros -> "X جار سفر"
            else:
                count_text = number_to_kurdish_text(zeros_count)
                zeros_text = f"{count_text} جار سفر"

            # If the number was ONLY zeros (e.g. "0000"), we are done.
            if is_all_zeros:
                return zeros_text

            # Otherwise, add a space to connect it to the rest of the number
            zeros_prefix = f"{zeros_text} "

        # 3. Standard Integer Conversion for the rest
        num = int(number_str)

        result_text = ""
        if num >= SCIENTIFIC_THRESHOLD:
            sci_str = f"{num:.3e}"
            parts = sci_str.split('e')
            mantissa_str = parts[0]
            exponent_str = parts[1].lstrip('+')
            mantissa_val = float(mantissa_str)
            exponent_val = int(exponent_str)
            mantissa_text = decimal_to_kurdish_text(mantissa_val)
            exponent_text = number_to_kurdish_text(exponent_val)
            result_text = f"{mantissa_text} جارانی دە توانی {exponent_text}"
        else:
            result_text = number_to_kurdish_text(num)

        # Combine prefix (if any) with the result
        return f"{zeros_prefix}{result_text}"

    except ValueError:
        return number_str


# --- 5. normalize_math_expressions (No Changes) ---
def normalize_math_expressions(text: str) -> str:
    text = NEGATIVE_SIGN_RE.sub(
        lambda m: f"{m.group(1)}سالب {convert_number_to_text_handler(m.group(2))}",
        text
    )
    text = POSITIVE_SIGN_RE.sub(
        lambda m: f"{m.group(1)}کۆ {convert_number_to_text_handler(m.group(2))}",
        text
    )
    text = MATH_NO_SPACE_RE.sub(
        lambda
            m: f"{convert_number_to_text_handler(m.group(1))} {MATH_SYMBOLS_MAP[m.group(3)]} {convert_number_to_text_handler(m.group(4))}",
        text
    )
    text = MATH_SYMBOLS_SPACED_RE.sub(
        lambda
            m: f"{convert_number_to_text_handler(m.group(1))} {MATH_SYMBOLS_MAP[m.group(3)]} {convert_number_to_text_handler(m.group(4))}",
        text
    )
    return text