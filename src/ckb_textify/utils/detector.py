import re

# Regex for "Impossible Taa Marbuta"
# Matches a Taa Marbuta (ة) sandwiched directly between two Arabic characters.
# In standard Arabic, ة is ALWAYS final. In Ali-K, it is 'Ae' (ە).
IMPOSSIBLE_TAA_MARBUTA_RE = re.compile(r"[\u0600-\u06FF]\u0629[\u0600-\u06FF]")

# Regex for specific Ali-K characters/combinations that are rare in standard Arabic
# ؤ: Waw Hamza (Common in Kurdish for 'o', specific positions in Arabic)
# رِ: Ra + Kasra (Visual hack for 'ڕ')
# لاَ: Lam-Alif + Fatha (Visual hack for 'ڵا')
# ة$: Taa Marbuta at end of word (Weak signal, but useful if combined)
ALI_K_INDICATORS_RE = re.compile(r"(?:[\u0600-\u06FF]\u0629[\u0600-\u06FF])|ر\u0650|لا\u064e|ؤ")


def is_ali_k_text(text: str) -> bool:
    """
    Determines if a text segment is likely encoded in Ali-K.
    Checks for:
    1. Taa Marbuta (ة) in the middle of a word (Strongest).
    2. Specific Ali-K hacks like Ra+Kasra (رِ) or Waw+Hamza (ؤ).
    """
    if not text:
        return False

    return bool(ALI_K_INDICATORS_RE.search(text))