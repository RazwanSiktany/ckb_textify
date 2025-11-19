# ckb_textify/phone_numbers.py
import re
from .number_to_text import number_to_kurdish_text

# 1. --- UPDATED REGEX ---
# Replaced the \b at the start with (^|\s) to correctly capture
# phone numbers that start with a "+" or are at the beginning of the text.
PHONE_RE = re.compile(
    # Group 1: Start of string or a space
    r"(^|\s)"
    # Group 2 & 3: International prefix (e.g., +964, 00964)
    r"((\+?|0+)\s*964[\s-]?)?"
    # Group 4: Company code (e.g., 0750 or 750)
    r"(0?7[578]\d)[\s-]?"
    # Group 5: Next 3 digits (e.g., 778)
    r"(\d{3})[\s-]?"
    # Group 6: Next 2 digits (e.g., 58)
    r"(\d{2})[\s-]?"
    # Group 7: Last 2 digits (e.g., 06)
    r"(\d{2})\b"
)


# 2. --- Helper Function (Unchanged) ---
def _read_number_group(num_str: str) -> str:
    """
    Converts a number string to Kurdish based on your rules.
    - "0750" -> "سفر حەوت سەد و پەنجا"
    - "06"   -> "سفر شەش"
    """
    if num_str.startswith("0") and len(num_str) > 1:
        part1 = "سفر"
        try:
            part2_int = int(num_str[1:])
        except ValueError:
            return ""

        part2 = number_to_kurdish_text(part2_int)

        if part2 == "سفر":
            return "سفر سفر"

        return f"{part1} {part2}"

    try:
        return number_to_kurdish_text(int(num_str))
    except ValueError:
        return ""


# 3. --- UPDATED REPLACEMENT FUNCTION ---
def normalize_phone_numbers(text: str) -> str:
    """
    Finds phone numbers and converts them to spoken Kurdish
    using the new international prefix rule and 4+3+2+2 grouping.
    """

    def _replace_phone(match):

        # Handle the new regex group assignments
        leading_space_or_start = match.group(1) or ""
        prefix_group = match.group(2) or ""
        company_code = match.group(4) or ""
        group2 = match.group(5) or ""
        group3 = match.group(6) or ""
        group4 = match.group(7) or ""

        spoken_parts = []

        # 1. Handle International Prefix
        if prefix_group:
            prefix_clean = re.sub(r"[\s-]", "", prefix_group)
            digits = ""

            if prefix_clean.startswith("+"):
                spoken_parts.append("کۆ")
                digits = prefix_clean.lstrip("+")  # e.g., "964"

            elif prefix_clean.startswith("0"):
                m = re.match(r"(0+)(.*)", prefix_clean)
                if m:
                    zeros = m.group(1)  # "00" or "000"
                    digits = m.group(2)  # "964"
                    spoken_parts.extend(["سفر"] * len(zeros))
                else:
                    digits = prefix_clean

            try:
                if digits:
                    spoken_parts.append(number_to_kurdish_text(int(digits)))
            except ValueError:
                pass

        # 2. Handle 4+3+2+2 Groups
        spoken_parts.append(_read_number_group(company_code))
        spoken_parts.append(_read_number_group(group2))
        spoken_parts.append(_read_number_group(group3))
        spoken_parts.append(_read_number_group(group4))

        # Join all parts, preserving the original leading space/start
        return leading_space_or_start + " ".join(part for part in spoken_parts if part) + " "

    return PHONE_RE.sub(_replace_phone, text)