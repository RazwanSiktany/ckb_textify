# ckb_textify/config.py

DEFAULT_CONFIG = {
    # Foundational
    "normalize_characters": True,
    "normalize_digits": True,

    # Diacritics
    "diacritics_mode": "convert",
    "shadda_mode": "double",
    "remove_tatweel": True,

    # Emoji Configuration
    "emoji_mode": "remove",  # Options: "remove" (Def), "convert", "ignore"

    # Expansion Modules
    "date_time": True,
    "phone_numbers": True,
    "units": True,
    "per_rule": True,
    "math": True,
    "currency": True,
    "percentage": True,

    # Textual Features
    "web": True,
    "technical": True,
    "abbreviations": True,
    "arabic_names": True,

    "chat_speak": False,

    "latin": True,
    "foreign": True,
    "symbols": True,

    # Numbers
    "decimals": True,
    "integers": True
}