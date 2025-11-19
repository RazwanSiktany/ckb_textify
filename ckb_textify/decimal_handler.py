# ckb_textify/decimal_handler.py

from .number_to_text import number_to_kurdish_text


def decimal_to_kurdish_text(number: float) -> str:
    integer_part = int(number)

    # Check for .5 exactly
    if number - integer_part == 0.5:
        return f"{number_to_kurdish_text(integer_part)} و نیو"

    decimal_str = str(number).split(".")[1]

    # Remove trailing zeros
    decimal_str = decimal_str.rstrip('0')
    if decimal_str == '':
        return number_to_kurdish_text(integer_part)

    # Count leading zeros
    leading_zeros_count = 0
    for ch in decimal_str:
        if ch == '0':
            leading_zeros_count += 1
        else:
            break

    leading_zeros_text = " ".join(["سفر"] * leading_zeros_count)

    # Remaining decimal digits after leading zeros
    remaining_decimal = decimal_str[leading_zeros_count:]

    if remaining_decimal:
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