# ckb_textify/currency.py
from .number_to_text import number_to_kurdish_text

CURRENCY_MAP = {
    "IQD": ("دیناری عێڕاقی", "فلس", 100),
    "د.ع": ("دیناری عێڕاقی", "فلس", 100),
    "د،ع": ("دیناری عێڕاقی", "فلس", 100),
    "$": ("دۆلار", "سەنت", 100),
    "USD": ("دۆلار", "سەنت", 100),
    "€": ("یۆرۆ", "سەنت", 100),
    "EUR": ("یۆرۆ", "سەنت", 100),
    # --- NEW ADDITIONS ---
    "£": ("پاوەند", "پێنس", 100),
    "GBP": ("پاوەند", "پێنس", 100),
    "¥": ("یەن", "سێن", 100),
    "JPY": ("یەن", "سێن", 100),
}


def currency_to_kurdish_text(amount: str) -> str:
    amount = amount.strip()
    currency_key = None
    value_str = None

    for key in CURRENCY_MAP:
        if amount.startswith(key):
            currency_key = key
            value_str = amount[len(key):].strip()
            break
        elif amount.endswith(key):
            currency_key = key
            value_str = amount[:-len(key)].strip()
            break

    if currency_key is None and " " in amount:
        parts = amount.split(" ", 1)
        if parts[0] in CURRENCY_MAP:
            currency_key = parts[0]
            value_str = parts[1].strip()

    if currency_key is None:
        return amount

    kurd_currency, kurd_subunit, subunit_factor = CURRENCY_MAP[currency_key]

    try:
        value_str = value_str.replace(",", "")
        value = float(value_str)
    except (ValueError, TypeError):
        return amount

    integer_part = int(value)
    decimal_part = round((value - integer_part) * subunit_factor)
    integer_text = number_to_kurdish_text(integer_part)

    if decimal_part == 0:
        return f"{integer_text} {kurd_currency}"
    else:
        decimal_text = number_to_kurdish_text(decimal_part)
        return f"{integer_text} {kurd_currency} و {decimal_text} {kurd_subunit}"