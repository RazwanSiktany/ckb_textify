import re
from typing import List

from ckb_textify.core.types import Token, TokenType
from ckb_textify.modules.base import Module
from ckb_textify.utils.numbers import int_to_kurdish
from ckb_textify.resources.patterns import SUFFIXES_LIST


class DateTimeNormalizer(Module):
    """
    Converts Dates (YYYY/MM/DD) and Times.
    Smart handling for:
    - 3-part times (HH:MM:SS) -> Explicit Duration (Hours, Minutes, Seconds)
    - 2-part times (HH:MM) -> Clock (if explicit context) vs Digital (if ambiguous)
    """

    KURDISH_MONTHS = {
        1: "کانونی دووەم", 2: "شوبات", 3: "ئازار", 4: "نیسان",
        5: "ئایار", 6: "حوزەیران", 7: "تەمموز", 8: "ئاب",
        9: "ئەیلوول", 10: "تشرینی یەکەم", 11: "تشرینی دووەم", 12: "کانونی یەکەم"
    }

    # --- Time Context Prefixes (High Confidence Indicators) ---
    CLOCK_PREFIXES = {
        "کاتژمێر", "کاتژمێری", "لەکاتژمێر",
        "کاژێر", "کاژێری", "لەکاژێر",
        "سەعات", "سەعاتی", "لەسەعات",
        "سعات", "سعاتی",
        "کاتی"
    }

    # --- Kurdish Time Suffixes (Expanded) ---
    AM_SUFFIXES = ["AM", "A.M.", "پ.ن", "بەیانی", "پێش نیوەڕۆ", "پێشنیوەڕۆ"]
    PM_SUFFIXES = [
        "PM", "P.M.", "د.ن",
        "دوای نیوەڕۆ", "دوای نیوەرۆ", "دوا نیوەڕۆ",
        "پاش نیوەڕۆ", "پاش نیوەرۆ", "پاشنیوەڕۆ",
        "ئێوارە", "عەسر", "نیوەڕۆ"
    ]
    SPECIAL_SUFFIXES = ["شەو"]

    SUFFIX_TOKENS = AM_SUFFIXES + PM_SUFFIXES + SPECIAL_SUFFIXES
    SIMPLE_SUFFIX_RE = re.compile(r"^[یي]?\s*(" + "|".join([s.replace(' ', r'\s*') for s in SUFFIX_TOKENS]) + r")$",
                                  re.IGNORECASE)

    SORTED_GRAMMAR_SUFFIXES = sorted(SUFFIXES_LIST, key=len, reverse=True)
    KURDISH_VOWELS = ['وو', 'و', 'ی', 'ێ', 'ا', 'ە', 'ۆ']

    @property
    def name(self) -> str:
        return "DateTimeNormalizer"

    @property
    def priority(self) -> int:
        return 95

    def process(self, tokens: List[Token]) -> List[Token]:
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
                # 1. Check for Clock Prefix (Look Behind)
                has_prefix = False
                prev_t = self._get_prev(tokens, i)
                if prev_t and prev_t.text in self.CLOCK_PREFIXES:
                    has_prefix = True

                # 2. Suffix Detection (Look Ahead)
                suffix_text = ""
                extra_grammatical_suffix = ""
                consumed_indices = []

                found_match = False
                for j in range(3, 0, -1):
                    if i + j < len(tokens):
                        phrase_tokens = tokens[i + 1:i + 1 + j]
                        phrase = " ".join([t.text for t in phrase_tokens if t.text]).strip()

                        clean_phrase = phrase.replace(' ', '')
                        if len(clean_phrase) > 1 and clean_phrase[0] in ['ی', 'ي']:
                            clean_phrase = clean_phrase[1:]
                        clean_phrase = clean_phrase.replace('ـ', '').replace('\u200c', '')
                        clean_phrase_upper = clean_phrase.upper()

                        for s in self.SUFFIX_TOKENS:
                            s_clean = s.replace(' ', '').upper()
                            if clean_phrase_upper.startswith(s_clean):
                                remainder = clean_phrase[len(s_clean):]
                                if remainder:
                                    is_valid_suffix = False
                                    for gs in self.SORTED_GRAMMAR_SUFFIXES:
                                        if remainder == gs:
                                            is_valid_suffix = True
                                            break
                                    if not is_valid_suffix:
                                        continue

                                suffix_text = s
                                extra_grammatical_suffix = remainder
                                consumed_indices = list(range(i + 1, i + 1 + j))
                                found_match = True
                                break
                        if found_match: break

                if not suffix_text:
                    next_t = self._get_next(tokens, i)
                    if next_t and self.SIMPLE_SUFFIX_RE.match(next_t.text):
                        suffix_text = next_t.text
                        consumed_indices.append(i + 1)

                attached_suffix = re.sub(r"[\d:]", "", token.text).strip()
                final_suffix = suffix_text or attached_suffix

                has_suffix = bool(final_suffix)

                # 3. Consume Suffix Tokens
                for idx in consumed_indices:
                    if idx < len(tokens):
                        if tokens[idx].whitespace_after:
                            token.whitespace_after = (token.whitespace_after or "") + tokens[idx].whitespace_after
                        tokens[idx].text = ""

                # 4. Convert based on Mode
                converted_time = self._convert_time_smart(token.text, final_suffix, has_prefix, has_suffix)

                if extra_grammatical_suffix:
                    converted_time = self._append_suffix(converted_time, extra_grammatical_suffix)

                token.text = converted_time
                token.type = TokenType.WORD
                token.tags.add("TIME")

            i += 1
        return [t for t in tokens if t.text]

    def _convert_time_smart(self, text: str, suffix: str, has_prefix: bool, has_suffix: bool) -> str:
        """
        Intelligent time conversion strategy.
        """
        try:
            clean_time = re.sub(r"[^\d:]", "", text)
            parts = list(map(int, clean_time.split(":")))

            # --- Case 1: 3-Part Time (A:B:C) -> Explicit Duration ---
            if len(parts) >= 3:
                h, m, s = parts[0], parts[1], parts[2]
                text_parts = []

                # Logic: Skip parts that are zero, unless the whole thing is zero
                if h > 0 or (m == 0 and s == 0):
                    text_parts.append(f"{int_to_kurdish(h)} کاتژمێر")

                if m > 0:
                    text_parts.append(f"{int_to_kurdish(m)} خولەک")

                if s > 0:
                    text_parts.append(f"{int_to_kurdish(s)} چرکە")

                return " و ".join(text_parts)

            # --- Case 2: 2-Part Time (A:B) ---
            if len(parts) == 2:
                hour, minute = parts[0], parts[1]

                # Sub-Case 2.1: Explicit Clock (High Confidence)
                # Condition: Hour is 0-23 AND (Contextual Prefix present OR Explicit Suffix present)
                is_valid_clock_hour = 0 <= hour <= 23
                if is_valid_clock_hour and (has_prefix or has_suffix):
                    return self._generate_clock_speech(hour, minute, suffix)

                # Sub-Case 2.2: Ambiguous / Digital Read (Safe Mode)
                # Invalid Hour (>23) OR Valid Hour but no Context
                # Action: Digital Read (Number and Number)
                # FIX: If minute is 0, don't read it (44:00 -> 44)
                if minute == 0:
                    return int_to_kurdish(hour)

                return f"{int_to_kurdish(hour)} و {int_to_kurdish(minute)}"

            return text

        except Exception:
            return text

    def _generate_clock_speech(self, hour: int, minute: int, suffix: str) -> str:
        """
        Generates standard 12-hour clock speech (e.g., "Chwar u niwi dway niwero").
        """
        # 1. Analyze Suffix for AM/PM
        s_clean = suffix.replace('.', '').strip().replace(' ', '')
        if len(s_clean) > 1 and s_clean[0] in ['ی', 'ي']:
            s_clean = s_clean[1:]
        s_clean = s_clean.replace('ـ', '')
        s_upper = s_clean.upper()

        is_pm_suffix = any(s.replace(' ', '').upper() == s_upper for s in self.PM_SUFFIXES)
        is_am_suffix = any(s.replace(' ', '').upper() == s_upper for s in self.AM_SUFFIXES)
        is_shew = "شەو" in suffix

        # 2. Logic to align 24h hour with suffix
        hour_24 = hour

        # Adjust 24h logic if input was 12h with suffix
        if is_shew:
            if hour == 12:
                # 12 Shew is Midnight (00:xx)
                is_am_suffix = True
                is_pm_suffix = False
                hour_24 = 0
            elif 1 <= hour <= 4:
                is_am_suffix = True
                is_pm_suffix = False
            else:
                is_pm_suffix = True
                is_am_suffix = False

        if is_pm_suffix:
            if hour >= 1 and hour < 12: hour_24 = hour + 12
        elif is_am_suffix:
            if hour == 12: hour_24 = 0

        hour_24 %= 24

        # 3. Calculate Display Hour (12-hour format)
        hour_12 = hour_24 % 12 or 12
        hour_text = int_to_kurdish(hour_12)
        min_text = int_to_kurdish(minute)

        # 4. Generate Label
        label = self._get_time_period(hour_24)

        if minute == 0:
            return f"{hour_text}ی {label}"

        if minute == 30:
            return f"{hour_text} و نیوی {label}"

        return f"{hour_text} و {min_text} خولەکی {label}"

    def _get_time_period(self, hour: int) -> str:
        if 0 <= hour < 1:
            return "نیوەشەو"
        elif 1 <= hour < 4:
            return "شەو"
        elif 4 <= hour < 6:
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

    def _convert_date(self, text: str) -> str:
        # (Same as before)
        try:
            parts = re.split(r'[/\-.]', text)
            if len(parts) != 3: return text
            p0, p1, p2 = parts[0], parts[1], parts[2]
            day, month, year = 0, 0, 0
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

    def _append_suffix(self, text: str, suffix: str) -> str:
        if not suffix: return text
        text = text.strip()
        needs_y = False
        if suffix in ["ە", "ەکە", "ەکان"]:
            for v in self.KURDISH_VOWELS:
                if text.endswith(v):
                    needs_y = True
                    break
        if needs_y:
            if suffix == "ە": return f"{text}یە"
            return f"{text}ی{suffix}"
        return f"{text}{suffix}"

    def _get_prev(self, tokens: List[Token], i: int) -> Token | None:
        return tokens[i - 1] if i > 0 else None

    def _get_next(self, tokens: List[Token], i: int) -> Token | None:
        return tokens[i + 1] if i < len(tokens) - 1 else None