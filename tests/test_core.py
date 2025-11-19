# tests/test_core.py
import unittest
from ckb_textify import convert_all


class TestCKBTextify(unittest.TestCase):

    def test_basic_numbers(self):
        self.assertEqual(convert_all("12"), "دوازدە")

    def test_phone_numbers(self):
        # Test correct grouping
        text = "07501234567"
        self.assertIn("سفر حەوت سەد و پەنجا", convert_all(text))

    def test_web_normalization(self):
        self.assertIn("ئەت جیمەیڵ دۆت کۆم", convert_all("user@gmail.com"))
        self.assertIn("دۆت نێت", convert_all("rudaw.net"))

    def test_technical_codes(self):
        self.assertIn("ئەی یەک داش بی دوو", convert_all("A1-B2"))

    def test_units_ambiguity(self):
        self.assertIn("دە مەتر", convert_all("10m"))
        self.assertNotIn("مەتر", convert_all("I am m."))

    def test_english_transliteration(self):
        self.assertIn("ئیف", convert_all("If"))

    def test_config_disable(self):
        # *** UPDATED TEST ***
        # We must disable BOTH phone numbers AND general integers
        # so the digits are left alone.
        cfg = {
            "phone_numbers": False,
            "integers": False  # <--- ADD THIS LINE
        }
        self.assertEqual(convert_all("07501234567", config=cfg), "07501234567")


if __name__ == '__main__':
    unittest.main()