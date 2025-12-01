# ckb_textify/percentage.py

from .number_to_text import number_to_kurdish_text
from .decimal_handler import decimal_to_kurdish_text

def percentage_to_kurdish_text(value: str) -> str:
    """
    Convert percentage strings like '%15', '15%', '١٥٪' to Kurdish.
    """
    value = value.strip()

    # Remove both Latin (%) and Arabic (٪) percent symbols
    clean_value = value.replace("%", "").replace("٪", "").strip()
    clean_value = clean_value.replace(",", "")

    try:
        # Pass the string directly to preserve "93.91" exactly
        if "." in clean_value:
            text = decimal_to_kurdish_text(clean_value)
        else:
            number = int(clean_value)
            text = number_to_kurdish_text(number)
    except ValueError:
        return value

    return f"لە سەدا {text}"