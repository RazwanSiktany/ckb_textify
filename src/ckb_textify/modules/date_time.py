import re
from typing import List

from ckb_textify.core.types import Token, TokenType
from ckb_textify.modules.base import Module
from ckb_textify.utils.numbers import int_to_kurdish
from ckb_textify.resources.patterns import SUFFIXES_LIST


class DateTimeNormalizer(Module):
    """
    Converts Dates (YYYY/MM/DD, DD-MM-YYYY, etc.) and Times (12:30, 2 PM) to Kurdish.
    """

    KURDISH_MONTHS = {
        1: "کانونی دووەم", 2: "شوبات", 3: "ئازار", 4: "نیسان",
        5: "ئایار", 6: "حوزەیران", 7: "تەمموز", 8: "ئاب",
        9: "ئەیلوول", 10: "تشرینی یەکەم", 11: "تشرینی دووەم", 12: "کانونی یەکەم"
    }

    # --- Kurdish Time Suffixes (Expanded) ---
    AM_SUFFIXES = ["AM", "A.M.", "پ.ن", "بەیانی", "پێش نیوەڕۆ", "پێشنیوەڕۆ"]
    # Removed "شەو" from PM list to handle it dynamically
    PM_SUFFIXES = [
        "PM", "P.M.", "د.ن",
        "دوای نیوەڕۆ", "دوای نیوەرۆ", "دوا نیوەڕۆ",
        "پاش نیوەڕۆ", "پاش نیوەرۆ", "پاشنیوەڕۆ",
        "ئێوارە", "عەسر", "نیوەڕۆ"
    ]
    # "شەو" is special context (AM or PM)
    SPECIAL_SUFFIXES = ["شەو"]

    # Regex to capture potential AM/PM/Kurdish suffix (with optional linking 'ی' or 'ي').
    SUFFIX_TOKENS = AM_SUFFIXES + PM_SUFFIXES + SPECIAL_SUFFIXES

    # Use a simpler regex pattern for lookahead check against individual words/tokens
    SIMPLE_SUFFIX_RE = re.compile(r"^[یي]?\s*(" + "|".join([s.replace(' ', r'\s*') for s in SUFFIX_TOKENS]) + r")$",
                                  re.IGNORECASE)

    # Sorted grammatical suffixes for matching (longest first)
    SORTED_GRAMMAR_SUFFIXES = sorted(SUFFIXES_LIST, key=len, reverse=True)

    KURDISH_VOWELS = ['وو', 'و', 'ی', 'ێ', 'ا', 'ە', 'ۆ']

    @property
    def name(self) -> str:
        return "DateTimeNormalizer"

    @property
    def priority(self) -> int:
        return 95  # High priority (before Math/Numbers)

    def process(self, tokens: List[Token]) -> List[Token]:
        """Iterates through tokens and converts recognized DATE and TIME types."""
        if not self.config.enable_date_time:
            return tokens

        i = 0
        while i < len(tokens):
            token = tokens[i]

            if token.type == TokenType.DATE:
                token.text = self._convert_date(token.text)
                token.type = TokenType.WORD
                token.tags.add("DATE")

            elif token.type == TokenType.TIME:
                suffix_text = ""
                extra_grammatical_suffix = ""
                consumed_indices = []

                # --- 1. Multi-Token Suffix Check (e.g., 'پێش', 'نیوەڕۆ') ---
                # Check up to 3 tokens ahead
                found_match = False
                for j in range(3, 0, -1):  # Check longest match first
                    if i + j < len(tokens):
                        # Construct phrase from next j tokens
                        phrase_tokens = tokens[i + 1:i + 1 + j]
                        phrase = " ".join([t.text for t in phrase_tokens if t.text]).strip()

                        # Logic to identify Time Suffix + Grammatical Suffix
                        # e.g. "PM-e" -> Time: PM, Suffix: e

                        clean_phrase = phrase.replace(' ', '')
                        # Remove leading Y/I if present (e.g. "i PM")
                        if len(clean_phrase) > 1 and clean_phrase[0] in ['ی', 'ي']:
                            clean_phrase = clean_phrase[1:]

                        # Remove Tatweel/ZWNJ for comparison (e.g. PMـە -> PMە)
                        clean_phrase = clean_phrase.replace('ـ', '').replace('\u200c', '')
                        clean_phrase_upper = clean_phrase.upper()

                        for s in self.SUFFIX_TOKENS:
                            s_clean = s.replace(' ', '').upper()

                            # Check if the token STARTS with a known time suffix
                            if clean_phrase_upper.startswith(s_clean):
                                remainder = clean_phrase[len(s_clean):]

                                # If remainder exists, check if it's a valid grammatical suffix
                                if remainder:
                                    # Check against sorted suffix list
                                    is_valid_suffix = False
                                    for gs in self.SORTED_GRAMMAR_SUFFIXES:
                                        if remainder == gs:
                                            is_valid_suffix = True
                                            break

                                    if not is_valid_suffix:
                                        continue  # Not a valid suffix match, try next time suffix

                                # Match found!
                                suffix_text = s  # The core time suffix (e.g. PM)
                                extra_grammatical_suffix = remainder  # The extra bit (e.g. ە)
                                consumed_indices = list(range(i + 1, i + 1 + j))
                                found_match = True
                                break

                    if found_match:
                        break

                # --- 2. Single-Token Suffix Check (e.g., 'PM', 'بەیانی') ---
                # Fallback if the loop didn't catch it (mostly for simple regex matches)
                if not suffix_text:
                    next_t = self._get_next(tokens, i)
                    if next_t and self.SIMPLE_SUFFIX_RE.match(next_t.text):
                        suffix_text = next_t.text
                        consumed_indices.append(i + 1)

                # --- 3. Attached Suffix Check (e.g. "12:30pm") ---
                attached_suffix = re.sub(r"[\d:]", "", token.text).strip()

                # If we found an attached suffix, we need to split it too (e.g. 12:30pme -> pm, e)
                # But typically attached suffixes are simple (am/pm).
                # If regex didn't handle "pme", we assume it's just the time suffix.

                final_suffix = suffix_text or attached_suffix

                # Consume adjacent suffix tokens AND preserve their whitespace
                for idx in consumed_indices:
                    if idx < len(tokens):
                        # Capture whitespace before deleting
                        if tokens[idx].whitespace_after:
                            token.whitespace_after = (token.whitespace_after or "") + tokens[idx].whitespace_after

                        tokens[idx].text = ""  # Consume suffix token

                converted_time = self._convert_time(token.text, final_suffix)

                # Append the grammatical suffix if found (e.g. "ye")
                if extra_grammatical_suffix:
                    converted_time = self._append_suffix(converted_time, extra_grammatical_suffix)

                token.text = converted_time
                token.type = TokenType.WORD
                token.tags.add("TIME")

            i += 1

        # Filter out empty tokens (consumed AM/PM suffixes)
        return [t for t in tokens if t.text]

    def _append_suffix(self, text: str, suffix: str) -> str:
        """
        Attaches a grammatical suffix to the Kurdish text, adding 'y' buffer if needed.
        """
        if not suffix: return text

        # If suffix starts with a vowel (usually 'e' or 'a'), and text ends with vowel -> add 'y'
        # Specifically for "ە" (is), it becomes "یە" after vowel.

        text = text.strip()
        needs_y = False

        if suffix in ["ە", "ەکە", "ەکان"]:
            for v in self.KURDISH_VOWELS:
                if text.endswith(v):
                    needs_y = True
                    break

        if needs_y:
            # If suffix is just 'ە', it becomes 'یە'
            if suffix == "ە":
                return f"{text}یە"
            # Otherwise prepend 'y' to suffix?
            # Actually standard rule: "kat" + "a" -> "kata", "cher" + "a" -> "chera"
            # "naw" + "a" -> "nawa"
            # "kurd" + "e" -> "kurde"
            # "kurd" + "ye" -> "kurdye" (Wrong)

            # The suffixes in our list usually don't include the buffer 'y' unless it's "ye".
            # If we detected "e" (from 'PM-e') and text ends in vowel, we output "ye".
            return f"{text}ی{suffix}"

        return f"{text}{suffix}"

    def _convert_date(self, text: str) -> str:
        """Converts date strings (e.g. 2023/12/30) into Kurdish text."""
        try:
            parts = re.split(r'[/\-.]', text)
            if len(parts) != 3: return text

            p0, p1, p2 = parts[0], parts[1], parts[2]
            day, month, year = 0, 0, 0

            # Heuristic for Date Format Detection:
            if len(p0) == 4 and 1 <= int(p1) <= 12:
                year, month, day = map(int, [p0, p1, p2])
            elif len(p2) == 4:
                year = int(p2)
                v1, v2 = int(p0), int(p1)
                if v1 > 12 and v2 <= 12:
                    day, month = v1, v2
                elif v2 > 12 and v1 <= 12:
                    month, day = v1, v2
                else:
                    day, month = v1, v2
            else:
                return text

            day_text = int_to_kurdish(day)
            month_text = self.KURDISH_MONTHS.get(month, f"مانگی {int_to_kurdish(month)}")
            year_text = int_to_kurdish(year)

            return f"{day_text}ی {month_text}ی ساڵی {year_text}"
        except Exception:
            return text

    def _get_time_period(self, hour: int) -> str:
        """
        Returns the specific Kurdish time period label (e.g., بەیانی, ئێوارە)
        based on the 24-hour clock hour.
        """
        if 0 <= hour < 1:
            return "نیوەشەو"
        elif 1 <= hour < 4:
            return "شەو"  # Late night / Early morning
        elif 4 <= hour < 6:
            return "بەرەبەیان"  # Dawn
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

    def _convert_time(self, text: str, suffix: str = "") -> str:
        """Converts time strings (e.g. 14:30, 4:00 PM) into Kurdish text."""
        try:
            clean_time = re.sub(r"[^\d:]", "", text)
            parts = list(map(int, clean_time.split(":")))
            hour = parts[0]
            minute = parts[1] if len(parts) > 1 else 0

            # 1. Normalize values (Carry-over)
            hour_carry = minute // 60
            minute %= 60
            hour += hour_carry

            # The current hour value is normalized by carry-over
            hour_24 = hour

            # --- 2. Suffix Analysis (Determine AM/PM status) ---
            s_clean = suffix.replace('.', '').strip().replace(' ', '')
            # Remove leading Y/I for check
            if len(s_clean) > 1 and s_clean[0] in ['ی', 'ي']:
                s_clean = s_clean[1:]

            # Remove Tatweel for check
            s_clean = s_clean.replace('ـ', '')
            s_upper = s_clean.upper()

            is_pm_suffix = any(s.replace(' ', '').upper() == s_upper for s in self.PM_SUFFIXES)
            is_am_suffix = any(s.replace(' ', '').upper() == s_upper for s in self.AM_SUFFIXES)
            is_shew = "شەو" in suffix  # Check specifically for Shew

            # 3. Adjust 24-hour clock based on 12-hour input and suffix

            # Special Handling for "Shew" (Night)
            if is_shew:
                if hour == 12 or (1 <= hour <= 4):
                    is_am_suffix = True
                    is_pm_suffix = False
                else:
                    is_pm_suffix = True
                    is_am_suffix = False

            if is_pm_suffix:
                # If it's PM, add 12 hours, unless it's 12 PM (which is 12:xx 24h)
                if hour >= 1 and hour < 12: hour_24 = hour + 12
            elif is_am_suffix:
                # If it's AM, and hour is 12 (like 12:30 AM), it means 00:30 (midnight)
                if hour == 12: hour_24 = 0

            hour_24 %= 24

            # Calculate Display Hour (12-hour format)
            hour_12 = hour_24 % 12 or 12
            hour_text = int_to_kurdish(hour_12)
            min_text = int_to_kurdish(minute)

            # --- Output Construction ---

            has_explicit_period = is_pm_suffix or is_am_suffix or is_shew or hour > 12 or hour == 0

            if has_explicit_period:
                # Use the calculated time period based on 24h hour (e.g., 'بەیانی', 'نیوەڕۆ')
                label = self._get_time_period(hour_24)

                if minute == 0:
                    return f"{hour_text}ی {label}"

                if minute == 30:
                    return f"{hour_text} و نیوی {label}"

                    # General minutes
                return f"{hour_text} و {min_text} خولەکی {label}"

                # Fallback: No suffix and Ambiguous hour (1-12) -> Simple Numbers
            if minute == 0:
                return hour_text

            if minute == 30:
                return f"{hour_text} و نیو"

            return f"{hour_text} و {min_text} خولەک"

        except Exception:
            return text

    def _get_next(self, tokens: List[Token], i: int) -> Token | None:
        """Helper to get the next token."""
        return tokens[i + 1] if i < len(tokens) - 1 else None