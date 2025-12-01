# ckb_textify/decimal_handler.py

from .number_to_text import number_to_kurdish_text

def decimal_to_kurdish_text(number_input) -> str:
    """
    Convert a decimal number (string, float, or int) to Kurdish text.
    """
    # 1. Convert input to a string safely
    if isinstance(number_input, float):
        number_str = str(number_input)
        # Only force expansion if it's in scientific notation (e.g. "5e-05")
        if "e" in number_str.lower():
            number_str = f"{number_input:.15f}".rstrip('0')
    else:
        number_str = str(number_input)

    # 2. Parse Integer and Decimal parts
    if "." not in number_str:
        return number_to_kurdish_text(int(float(number_str)))

    parts = number_str.split(".")
    integer_part = int(parts[0])
    decimal_str = parts[1]

    # Check for .5 exactly (Special Rule)
    # We check if decimal_str is exactly "5"
    if decimal_str == "5":
        return f"{number_to_kurdish_text(integer_part)} و نیو"

    # Remove trailing zeros (e.g. 12.50 -> 12.5)
    decimal_str = decimal_str.rstrip('0')
    if decimal_str == '':
        return number_to_kurdish_text(integer_part)

    # Count leading zeros (e.g. 0.005)
    leading_zeros_count = 0
    for ch in decimal_str:
        if ch == '0':
            leading_zeros_count += 1
        else:
            break

    leading_zeros_text = " ".join(["سفر"] * leading_zeros_count)

    # Remaining decimal digits
    remaining_decimal = decimal_str[leading_zeros_count:]

    if remaining_decimal:
        # Convert the remaining digits (e.g. "91") to text
        remaining_decimal_number = int(remaining_decimal)
        remaining_decimal_text = number_to_kurdish_text(remaining_decimal_number)
    else:
        remaining_decimal_text = ""

    # Build decimal text parts
    decimal_parts = []
    if leading_zeros_text:
        decimal_parts.append(leading_zeros_text)
    if remaining_decimal_text:
        decimal_parts.append(remaining_decimal_text)

    decimal_text = " ".join(decimal_parts)

    return f"{number_to_kurdish_text(integer_part)} پۆینت {decimal_text}"