# Integer and Decimal normalization logic
# Shared logic for converting integers to Kurdish text.
# Used by Currency, Date, and Number modules.

# Using Standard Heh (ھ) U+0647 to match test expectations exactly.
KURDISH_UNITS = [
    "سفر", "یەک", "دوو", "سێ", "چوار", "پێنج", "شەش", "حەوت", "ھەشت", "نۆ",
    "دە", "یازدە", "دوازدە", "سێزدە", "چواردە", "پازدە", "شازدە", "حەڤدە", "ھەژدە", "نۆزدە"
]

KURDISH_TENS = [
    "", "", "بیست", "سی", "چل", "پەنجا", "شەست", "حەفتا", "ھەشتا", "نەوەد"
]

KURDISH_SCALES = [
    "", "ھەزار", "ملیۆن", "ملیار", "ترلیۆن", "کوادرلیۆن", "کوینترلێۆن"
]

def int_to_kurdish(n: int) -> str:
    if n == 0:
        return KURDISH_UNITS[0]

    prefix = ""
    if n < 0:
        prefix = "سالب "
        n = abs(n)

    parts = []
    scale_index = 0

    while n > 0:
        chunk = n % 1000
        if chunk > 0:
            chunk_text = _three_digits_to_text(chunk)
            scale = KURDISH_SCALES[scale_index]

            # Grammar Rule: Don't say "Yek Hezar", just say "Hezar"
            if chunk == 1 and scale == "ھەزار":
                chunk_text = ""

            if scale:
                if chunk_text:
                    parts.insert(0, f"{chunk_text} {scale}")
                else:
                    parts.insert(0, scale)
            else:
                parts.insert(0, chunk_text)

        n //= 1000
        scale_index += 1

    return prefix + " و ".join(parts)


def _three_digits_to_text(num: int) -> str:
    parts = []
    hundreds = num // 100
    remainder = num % 100

    if hundreds > 0:
        if hundreds == 1:
            parts.append("سەد")
        else:
            parts.append(f"{KURDISH_UNITS[hundreds]} سەد")

    if remainder > 0:
        if remainder < 20:
            parts.append(KURDISH_UNITS[remainder])
        else:
            tens = remainder // 10
            units = remainder % 10
            if units:
                parts.append(f"{KURDISH_TENS[tens]} و {KURDISH_UNITS[units]}")
            else:
                parts.append(KURDISH_TENS[tens])

    return " و ".join(parts)