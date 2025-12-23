# Mapping for legacy Ali-K / Unikurd style fonts
# These fonts repurposed standard Arabic code points to represent Kurdish letters.

ALI_K_MAP = {
    # Visual Hacks (Combinations first)
    "لاَ": "ڵا",  # Lam + Alif + Fatha -> Heavy Lam + Alif
    "لَ": "ڵ",  # Lam + Fatha -> Heavy Lam
    "رِ": "ڕ",  # Ra + Kasra -> Heavy Ra
    "ر ِ": "ڕ",  # Ra + Space + Kasra (dirty OCR/typing)

    # Direct Repurposed Characters
    "ض": "چ",
    "ص": "ێ",
    "ث": "پ",
    "ط": "گ",
    "ظ": "ڤ",
    "ة": "ە",
    "ه": "ھ",  # Standard Heh -> Kurdish Heh
    "ؤ": "ۆ",
    "ي": "ی",  # Arabic Ya -> Kurdish Ya
    "ى": "ی",  # Alif Maqsurah -> Kurdish Ya
    "ك": "ک",  # Arabic Kaf -> Kurdish Kaf
    "ىَ": "ێ",  # Alif Maqsurah + Fatha -> Ye (sometimes used)
    "ذ": "ژ",  # Thal -> Zhe
}

# Pre-compiled list of keys for iteration (Longest first is crucial for 'لاَ' before 'ل')
ALI_K_KEYS = sorted(ALI_K_MAP.keys(), key=len, reverse=True)