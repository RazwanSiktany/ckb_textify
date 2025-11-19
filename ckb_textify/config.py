# ckb_textify/config.py

# Default configuration: All features enabled
DEFAULT_CONFIG = {
    # Foundational (Recommended to keep True)
    "normalize_characters": True,  # Unify letters (ی, ک, ه)
    "normalize_digits": True,  # Convert ١٢٣ -> 123
    "remove_diacritics": True,  # Remove Harakat

    # Expansion Modules
    "date_time": True,  # Dates and Times
    "phone_numbers": True,  # Phone numbers grouping
    "units": True,  # kg, m, cm...
    "per_rule": True,  # km/h -> km bo har kAtZhmryk
    "math": True,  # +, -, scientific notation
    "currency": True,  # $, £, IQD
    "percentage": True,  # 5%

    # Textual Features
    "web": True,  # URLs and Emails
    "technical": True,  # UUIDs, MACs, Codes (A1-B2)
    "abbreviations": True,  # Dr., P.
    "arabic_names": True,  # Muhammad -> Muhamed
    "latin": True,  # English words -> Kurdish Script
    "symbols": True,  # @, #, &

    # Numbers
    "decimals": True,  # 12.5 -> dWazda point penj
    "integers": True  # 12 -> dWazda
}