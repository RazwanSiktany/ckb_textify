# ckb_textify/date_time.py

from datetime import timedelta, datetime
import re
from .number_to_text import number_to_kurdish_text

KURDISH_MONTHS = {
    1: "کانونی دووەم", 2: "شوبات", 3: "ئازار", 4: "نیسان",
    5: "ئایار", 6: "حوزەیران", 7: "تەمموز", 8: "ئاب",
    9: "ئەیلوول", 10: "تشرینی یەکەم", 11: "تشرینی دووەم", 12: "کانونی یەکەم"
}

AM_SUFFIXES = ["AM", "پ.ن", "بەیانی", "پێش نیوەڕۆ", "پێشنیوەڕۆ"]
PM_SUFFIXES = [
    "PM", "د.ن",
    "دوای نیوەڕۆ", "دوای نیوەرۆ","دوا نیوەڕۆ",
    "پاش نیوەڕۆ", "پاش نیوەرۆ", "پاشنیوەڕۆ",
    "شەو", "ئێوارە", "عەسر", "نیوەڕۆ"
]
ALL_SUFFIXES = AM_SUFFIXES + PM_SUFFIXES


def date_to_kurdish_text(date_str: str, format: str = None) -> str:
    date_str = date_str.strip()
    try:
        parts = re.split(r'[/\-]', date_str)

        if len(parts) != 3:
            return date_str

        p0, p1, p2 = parts[0], parts[1], parts[2]
        day, month, year = 0, 0, 0

        # Case 1: YYYY/MM/DD
        if len(p0) == 4:
            year, month, day = map(int, [p0, p1, p2])

        # Case 2: DD/MM/YYYY or MM/DD/YYYY
        elif len(p2) == 4:
            year = int(p2)
            v1, v2 = int(p0), int(p1)
            if v1 > 12:
                day, month = v1, v2
            elif v2 > 12:
                month, day = v1, v2
            else:
                day, month = v1, v2
        else:
            return date_str

        day_text = number_to_kurdish_text(day)
        month_text = KURDISH_MONTHS.get(month, f"مانگی {month}")
        year_text = number_to_kurdish_text(year)

        return f"{day_text}ی {month_text}ی ساڵی {year_text}"

    except Exception:
        return date_str


def normalize_time_string(time_str: str) -> tuple[int, int, int | None]:
    parts = list(map(int, time_str.strip().split(":")))
    while len(parts) < 3:
        parts.append(0)
    hour, minute, second = parts
    total_seconds = hour * 3600 + minute * 60 + second
    normalized = timedelta(seconds=total_seconds)
    dt = (datetime.min + normalized).time()
    return dt.hour, dt.minute, dt.second if dt.second != 0 else None


def get_kurdish_time_label(hour: int) -> str:
    if 0 <= hour < 1:
        return "نیوەشەو"
    elif 1 <= hour < 3:
        return "شەو"
    elif 3 <= hour < 6:
        return "بەرەبەیان"
    elif 6 <= hour < 10:
        return "بەیانی"
    elif 10 <= hour < 12:
        return "پێش نیوەڕۆ"
    elif 12 <= hour < 14:
        return "نیوەڕۆ"
    elif 14 <= hour < 18:
        return "دوای نیوەڕۆ"
    elif 18 <= hour < 21:
        return "ئێوارە"
    else:
        return "شەو"


def strip_suffix(time_str: str) -> tuple[str, str | None]:
    time_str = time_str.strip()
    for suffix in ALL_SUFFIXES:
        pattern = rf"(?<!ی)\s*{re.escape(suffix)}$"
        if re.search(pattern, time_str):
            clean_str = re.sub(pattern, "", time_str).strip()
            return clean_str, suffix
    return time_str, None


def convert_suffix_to_24hour(hour: int, suffix: str | None) -> int:
    if suffix in AM_SUFFIXES:
        if hour == 12: return 0
        return hour
    elif suffix in PM_SUFFIXES:
        if hour < 12: return hour + 12
        return hour
    else:
        return hour


def time_to_kurdish_text(time_str: str) -> str:
    time_str = time_str.strip()

    # 1. Check for explicit suffix (e.g., "06:41ی بەیانی")
    suffix_pattern = '|'.join(map(re.escape, ALL_SUFFIXES))
    pattern_with_ye = rf"^(.*?)(ی)\s*({suffix_pattern})$"
    m = re.match(pattern_with_ye, time_str)

    if m:
        time_part = m.group(1).strip()
        ye = m.group(2)
        explicit_suffix = m.group(3)

        try:
            # Parse the time part (e.g. "06:41")
            hour, minute, second = normalize_time_string(time_part)

            # Convert hour to 12-hour format for reading
            hour_12 = hour % 12 or 12
            hour_text = number_to_kurdish_text(hour_12)

            # Construct the text based on minutes/seconds
            if minute == 0 and (second is None or second == 0):
                return f"{hour_text}{ye} {explicit_suffix}"

            if minute == 30 and (second is None or second == 0):
                return f"{hour_text} و نیو{ye} {explicit_suffix}"

            # Standard minutes
            parts = [hour_text]
            if minute > 0:
                parts.append(number_to_kurdish_text(minute))
            if second is not None and second > 0:
                parts.append(number_to_kurdish_text(second))

            # Join parts with " و "
            base_text = " و ".join(parts)

            # Attach suffix to the very end with a space
            return f"{base_text}{ye} {explicit_suffix}"

        except Exception:
            return time_str

    # 2. Standard Logic (No explicit suffix found)
    try:
        clean_time, suffix = strip_suffix(time_str)
        hour, minute, second = normalize_time_string(clean_time)
        hour = convert_suffix_to_24hour(hour, suffix)
    except Exception:
        return time_str

    hour_12 = hour % 12 or 12
    hour_text = number_to_kurdish_text(hour_12)
    label = get_kurdish_time_label(hour)

    if minute == 30 and (second is None or second == 0):
        return f"{hour_text} و نیوی {label}"
    if minute == 0 and (second is None or second == 0):
        return f"{hour_text}ی {label}"

    minute_text = number_to_kurdish_text(minute)
    result = f"{hour_text} و {minute_text} خولەکی {label}"

    if second is not None:
        second_text = number_to_kurdish_text(second)
        result += f" و {second_text} چرکە"

    return result