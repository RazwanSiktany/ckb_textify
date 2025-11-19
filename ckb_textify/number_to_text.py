# ckb_textify/number_to_text.py

kurdish_units = [
    "سفر", "یەک", "دوو", "سێ", "چوار", "پێنج", "شەش", "حەوت", "ھەشت", "نۆ",
    "دە", "یازدە", "دوازدە", "سێزدە", "چواردە", "پازدە", "شازدە", "حەڤدە", "ھەژدە", "نۆزدە"
]

kurdish_tens = [
    "", "", "بیست", "سی", "چل", "پەنجا", "شەست", "حەفتا", "ھەشتا", "نەوەد"
]

kurdish_scales = [
    "", "ھەزار", "ملیۆن", "ملیار", "ترلیۆن",
    "کوادرلیۆن",  # 10^15
    "کوینترلێۆن"  # 10^18
]

def number_to_kurdish_text(n: int) -> str:
    if n == 0:
        return kurdish_units[0]

    # Handle Negative Numbers
    is_negative = False
    if n < 0:
        is_negative = True
        n = abs(n)

    def three_digits_to_text(num):
        parts = []
        hundreds = num // 100
        remainder = num % 100

        if hundreds > 0:
            if hundreds == 1:
                parts.append("سەد")
            else:
                parts.append(f"{kurdish_units[hundreds]} سەد")

        if remainder > 0:
            if remainder < 20:
                parts.append(kurdish_units[remainder])
            else:
                tens = remainder // 10
                units = remainder % 10
                if units:
                    parts.append(f"{kurdish_tens[tens]} و {kurdish_units[units]}")
                else:
                    parts.append(kurdish_tens[tens])

        return " و ".join(parts)

    parts = []
    scale_index = 0

    while n > 0:
        chunk = n % 1000
        if chunk:
            chunk_text = three_digits_to_text(chunk)
            scale = kurdish_scales[scale_index]

            # Special rule: don't use یەک for 100 or 1000
            if chunk == 1 and scale in ["", "ھەزار"]:
                parts.insert(0, scale or kurdish_units[1])
            else:
                parts.insert(0, f"{chunk_text} {scale}".strip())
        n //= 1000
        scale_index += 1

    result_text = " و ".join(parts)

    # Prepend "سالب" if it was negative
    if is_negative:
        return f"سالب {result_text}"

    return result_text