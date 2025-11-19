# ckb_textify/percentage.py

from .number_to_text import number_to_kurdish_text
from .decimal_handler import decimal_to_kurdish_text

def percentage_to_kurdish_text(value: str) -> str:
    """
    Convert percentage strings like '%15' or '15%' to Kurdish.
    Handles decimals like 12.5% too.
    """
    value = value.strip()

    if value.startswith('%'):
        value = value[1:]
    elif value.endswith('%'):
        value = value[:-1]

    value = value.strip().replace(",", "")

    try:
        if "." in value:
            number = float(value)
            text = decimal_to_kurdish_text(number)
        else:
            number = int(value)
            text = number_to_kurdish_text(number)
    except ValueError:
        return value # Return original on error

    return f"لە سەدا {text}"