import re
from typing import List
from ckb_textify.core.types import Token, TokenType
from ckb_textify.modules.base import Module
from ckb_textify.resources.patterns import SUFFIXES_LIST
from ckb_textify.utils.numbers import int_to_kurdish


class UnitNormalizer(Module):
    UNIT_MAP = {
        # Weights
        "kg": "کیلۆگرام", "g": "گرام", "mg": "میلیگرام",
        "کگم": "کیلۆگرام", "کغم": "کیلۆگرام",
        "کیلۆ": "کیلۆگرام", "کیلۆم": "کیلۆگرام",
        "گم": "گرام",
        "oz": "ئۆنس", "lb": "پاوەند", "ton": "تۆن",

        # Length
        "km": "کیلۆمەتر", "m": "مەتر", "cm": "سانتیمەتر", "mm": "میلیمەتر",
        "سم": "سانتیمەتر", "ملم": "میلیمەتر", "ملیمەتر": "میلیمەتر", "م": "مەتر", "کم": "کیلۆمەتر",
        "in": "ئینج", "″": "ئینج", "′": "پێ", "ft": "پێ", "yd": "یارد", "mi": "مایل",

        "³": "سێجا",

        # Volume (Liquid)
        "l": "لیتر", "ml": "میلیلیتر", "gal": "گالۆن",

        # Time
        "h": "کاتژمێر", "hr": "کاتژمێر", "min": "خولەک", "sec": "چرکە", "s": "چرکە", "ms": "میلی چرکە",

        # Data
        "gb": "گێگابایت", "mb": "مێگابایت", "kb": "کیلۆبایت", "tb": "تێرابایت",

        # Temperature & Energy
        "°c": "پلەی سیلیزی", "c": "پلەی سیلیزی",
        "°f": "پلەی فەھرەنھایت", "f": "پلەی فەھرەنھایت",
        "°": "پلە", "K": "کلڤن",
        "J": "جووڵ", "kJ": "کیلۆجووڵ", "cal": "کالۆری", "kcal": "کیلۆکالۆری",

        # Power & Electric
        "Wh": "وات کاتژمێر", "kWh": "کیلۆوات کاتژمێر", "kW": "کیلۆوات", "W": "وات", "MW": "مێگاوات",
        "HP": "توانائەسپ", "V": "ڤۆڵت", "mV": "میلی ڤۆڵت", "A": "ئەمپێر", "mA": "میلی ئەمپێر", "mAh": "میلی ئەمپێر",
        "Ω": "ئۆم",

        # Pressure & Force
        "Pa": "پاسکاڵ", "kPa": "کیلۆپاسکاڵ", "psi": "پاوەند بۆ ھەر ئینجێک",
        "N": "نیوتن", "kN": "کیلۆ نیوتن",

        # Speed
        "mph": "مایل بۆ ھەر کاتژمێرێک",

        # Directions
        "°n": "پلەی باکور",
        "°s": "پلەی باشور",
        "°e": "پلەی خۆرھەڵات",
        "°w": "پلەی خۆرئاوا",
    }

    # Units that are unambiguous symbols
    SAFE_UNITS = {"°c", "°f", "°", "°n", "°s", "°e", "°w", "²", "³", "Ω", "″", "′"}

    # Ambiguous units that MUST have a number before them (IS_UNIT tag) to be converted.
    # We strictly require these to be standalone (no suffixes) to avoid converting words like "me", "in", "ton".
    AMBIGUOUS_UNITS = {
        "m", "s", "c", "f", "l", "g", "in", "ft", "yd", "mi", "م", "gal", "oz", "lb", "ton",
        "ms", "K", "J", "cal", "W", "HP", "Pa", "V", "A", "N"
    }

    KURDISH_VOWELS = ['وو', 'و', 'ی', 'ێ', 'ا', 'ە', 'ۆ']
    # Use explicit unicode escapes for robustness
    SUPERSCRIPT_DIGITS = str.maketrans(
        "\u2070\u00B9\u00B2\u00B3\u2074\u2075\u2076\u2077\u2078\u2079",
        "0123456789"
    )
    SUPERSCRIPT_REGEX = re.compile(r"^[\u2070\u00B9\u00B2\u00B3\u2074-\u2079]+$")

    # Sort suffixes by length for correct matching
    SUFFIXES = sorted(SUFFIXES_LIST, key=len, reverse=True)

    @property
    def name(self) -> str:
        return "UnitNormalizer"

    @property
    def priority(self) -> int:
        return 60

    def process(self, tokens: List[Token]) -> List[Token]:
        i = 0
        while i < len(tokens):
            token = tokens[i]

            # Skip if already processed
            if "UNIT_PROCESSED" in token.tags:
                i += 1
                continue

            # Check for standalone superscript first
            if self._is_superscript(token):
                self._process_standalone_power(token)
                i += 1
                continue

            # Check 1: Is it tagged by the Tagger?
            is_tagged = "IS_UNIT" in token.tags

            # Check 2: Extract potential core unit
            core_unit, suffix = self._extract_suffix(token.text)

            # Determine if we should process this token as a unit
            should_process = False

            # Identify ambiguity
            # Check if the core unit is in the ambiguous list (case-sensitive, lowercase, or uppercase)
            is_ambiguous = (core_unit in self.AMBIGUOUS_UNITS) or \
                           (core_unit.lower() in self.AMBIGUOUS_UNITS) or \
                           (core_unit.upper() in self.AMBIGUOUS_UNITS)

            if is_tagged:
                # If tagged (preceded by number):
                # Ambiguous units (e.g. 'm', 'م') MUST be standalone (no suffix) to be processed.
                # This avoids cases like "2 me" becoming "2 meters-is".
                if is_ambiguous:
                    if not suffix:
                        should_process = True
                else:
                    # Unambiguous units (e.g. km) can have suffixes (e.g. 2 km-ek)
                    should_process = True

            elif core_unit.lower() in self.SAFE_UNITS:
                should_process = True

            elif core_unit in self.UNIT_MAP or core_unit.lower() in self.UNIT_MAP or core_unit.upper() in self.UNIT_MAP:
                # Untagged (no number before).
                # Only process if NOT ambiguous.
                if not is_ambiguous:
                    should_process = True

            if should_process:
                # --- Heuristic: Strict Case for Single Letters ---
                # If we have a single lowercase letter (e.g. 'a') that isn't in the map exactly,
                # but matches an Uppercase key (e.g. 'A') via loose matching logic,
                # we assume it's just a letter (variable/text) and skip it.
                # Native lowercase units like 'm', 'g', 'l' are in UNIT_MAP so they pass this.
                if len(core_unit) == 1 and core_unit.islower() and core_unit not in self.UNIT_MAP:
                    i += 1
                    continue

                # Resolve unit text (try exact, lower, upper)
                unit_kurdish = self.UNIT_MAP.get(core_unit) or \
                               self.UNIT_MAP.get(core_unit.lower()) or \
                               self.UNIT_MAP.get(core_unit.upper())

                # Safety check: if mapping fails (e.g. 'a' matches regex but isn't in map as 'a'), skip.
                if not unit_kurdish:
                    i += 1
                    continue

                # --- NEW: Fix Number formatting for units (e.g. 2.0 m -> 2 m) ---
                if i > 0:
                    prev = tokens[i - 1]
                    if prev.type == TokenType.NUMBER and prev.original_text.endswith(".0"):
                        # Re-convert to integer text to drop "point sifir"
                        try:
                            val = int(float(prev.original_text))
                            prev.text = int_to_kurdish(val)
                        except ValueError:
                            pass

                # --- Look Ahead for Superscripts (Dynamic Area/Volume) ---
                next_t = self._get_next(tokens, i)
                power_text = ""

                if next_t and self._is_superscript(next_t):
                    ascii_digits = next_t.text.translate(self.SUPERSCRIPT_DIGITS)
                    if ascii_digits.isdigit():
                        try:
                            val = int(ascii_digits)
                            power_text = f" {int_to_kurdish(val)}جا"

                            # Consume the superscript token
                            # FIX: Preserve whitespace
                            if next_t.whitespace_after:
                                token.whitespace_after = (token.whitespace_after or "") + next_t.whitespace_after

                            next_t.text = ""
                            next_t.type = TokenType.UNKNOWN
                        except ValueError:
                            pass

                # --- PER RULE LOGIC (Look Ahead) ---
                next_t = self._get_next(tokens, i)
                next_next_t = self._get_next(tokens, i + 1) if next_t else None

                is_per_rule = False
                if next_t and next_t.text == "/" and next_next_t:
                    core_next, suffix_next = self._extract_suffix(next_next_t.text)
                    # Check next unit validity (relaxed check for per rule context)
                    if core_next.lower() in self.UNIT_MAP:
                        is_per_rule = True

                        if power_text:
                            unit_kurdish = self._apply_izhafa(unit_kurdish)

                        if "APPEND_HALF" in token.tags:
                            if suffix in ["یە", "ە"]:
                                niw_text = "نیوە"
                            else:
                                niw_text = "نیو"
                            full_suffix = f"{niw_text}{suffix}" if suffix not in ["", "ە", "یە"] else niw_text
                            token.text = f"{unit_kurdish}{power_text} و {full_suffix}"
                            token.tags.discard("APPEND_HALF")
                        else:
                            token.text = f"{unit_kurdish}{power_text}{suffix}"

                        token.tags.add("UNIT_PROCESSED")
                        token.tags.discard("IS_UNIT")

                        next_t.text = "بۆ ھەر"
                        next_t.type = TokenType.WORD
                        next_t.tags.add("UNIT_PROCESSED")

                        lower_next_core = core_next.lower()
                        next_unit_kurdish = self.UNIT_MAP.get(core_next, self.UNIT_MAP.get(lower_next_core))
                        per_unit_text = self._apply_per_rule_suffix(next_unit_kurdish)

                        if suffix_next:
                            per_unit_text += suffix_next

                        next_next_t.text = per_unit_text
                        next_next_t.tags.add("UNIT_PROCESSED")

                        token.whitespace_after = " "
                        next_t.whitespace_after = " "

                        i += 1
                        continue

                # --- STANDARD UNIT LOGIC ---
                if power_text:
                    unit_kurdish = self._apply_izhafa(unit_kurdish)

                if "APPEND_HALF" in token.tags:
                    if suffix in ["یە", "ە"]:
                        niw_text = "نیوە"
                    else:
                        niw_text = "نیو"
                    full_suffix = f"{niw_text}{suffix}" if suffix not in ["", "ە", "یە"] else niw_text
                    token.text = f"{unit_kurdish}{power_text} و {full_suffix}"
                    token.tags.discard("APPEND_HALF")
                else:
                    token.text = f"{unit_kurdish}{power_text}{suffix}"

                token.tags.discard("IS_UNIT")
                token.tags.add("UNIT_PROCESSED")

                if i > 0 and not tokens[i - 1].whitespace_after:
                    tokens[i - 1].whitespace_after = " "

            i += 1

        return tokens

    def _is_superscript(self, token: Token):
        """Robust check for superscript token."""
        return (token.type == TokenType.SUPERSCRIPT) or \
            (self.SUPERSCRIPT_REGEX.match(token.text))

    def _process_standalone_power(self, token: Token):
        """Converts a standalone superscript to '...ja'."""
        ascii_digits = token.text.translate(self.SUPERSCRIPT_DIGITS)
        if ascii_digits.isdigit():
            try:
                val = int(ascii_digits)
                token.text = f"{int_to_kurdish(val)}جا"
                token.type = TokenType.WORD
                token.tags.add("UNIT_PROCESSED")
            except ValueError:
                pass

    def _extract_suffix(self, text: str):
        clean_text = text.replace('ـ', '')
        for sfx in self.SUFFIXES:
            if clean_text.endswith(sfx):
                potential_core = clean_text[:-len(sfx)]
                # Check exact or lower or upper
                if potential_core in self.UNIT_MAP or potential_core.lower() in self.UNIT_MAP or potential_core.upper() in self.UNIT_MAP:
                    return potential_core, sfx
        if clean_text in self.UNIT_MAP or clean_text.lower() in self.UNIT_MAP or clean_text.upper() in self.UNIT_MAP:
            return clean_text, ""
        return text, ""

    def _apply_izhafa(self, text: str) -> str:
        if text.endswith(('ا', 'ە', 'ێ', 'ۆ', 'و', 'ی')):
            return text + "ی"
        return text + "ی"

    def _apply_per_rule_suffix(self, unit_text: str) -> str:
        unit_text = unit_text.strip()
        for vowel in self.KURDISH_VOWELS:
            if unit_text.endswith(vowel):
                return f"{unit_text}یێک"
        return f"{unit_text}ێک"

    def _get_next(self, tokens: List[Token], i: int) -> Token | None:
        for j in range(i + 1, len(tokens)):
            if tokens[j].text:
                return tokens[j]
        return None