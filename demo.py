import sys
import time
from ckb_textify import convert_all

# --- Complex Test Suites ---
test_suites = {

    # 1. CRITICAL VERIFICATION: Scientific Notation & Zeros
    "🔬 Scientific & Small Numbers": [
        # The bug fix verification:
        "0.00000000000000000000005",  # 5 * 10^-23 -> Should say "sAlb bIst w sI" at the end
        "-0.00005",  # Negative small number
        "0.0005",  # Positive small number
        "34000000000000000000000",  # Massive number
        "00025",  # Leading zeros logic (3 times zero...)
    ],

    # 2. Foreign Scripts & Transliteration
    "🌍 Global Scripts": [
        "German: Straẞe",  # Extended Latin (ẞ -> ss)
        "French: République",  # Accents (é -> e)
        "Greek: Χαίρετε",  # Greek Map
        "Russian: Путин",  # Cyrillic Map
        "Chinese: 你好",  # CJK -> Latin Bridge -> Sorani
        "Kurmanji: Êvar baş",  # Initial Vowel 'Ê' -> 'ئێ'
    ],

    # 3. Advanced Math & Logic
    "➗ Math Functions": [
        "ln 4 / ln 3",  # Functions + Division
        "sin 90 + cos 0",  # Trig functions
        "Area = 50m^2",  # Mixed Text/Math symbols
        "val ≈ 12.5",  # Approx symbol
        "5 + 3 = 8",  # Standard Math
    ],

    # 4. Web & Technical Data
    "💻 Tech & Web": [
        "info@gmail.com",  # Smart Email (Gmail -> جیمەیڵ)
        "www.rudaw.net",  # Smart URL (Split domains)
        "Code: A1-B2",  # Mixed alphanumeric (Spell out)
        "ChatGPT & GPT-4",  # Acronym detection (GPT -> Gee Pee Tee)
        "MAC: 00:1A:2B:3C:4D:5E",  # Character reading
    ],

    # 5. Units & Context
    "📏 Units & Context": [
        "Speed = 120km/h",  # "Per" rule with English header
        "10kg vs 10m",  # Unambiguous vs Ambiguous units
        "m and mm",  # Nouns (should NOT change)
        "نزیکەی 93.91٪ی",  # Smart comma removal
        "تەنیا 7٪ـیان",  # Date formatting
    ],

    # 6. Diacritics & Tajweed
    "🕌 Diacritics Modes": [
        "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ",
        "سڵاو لە مُحَمَّد", # Should double the Meem (Shadda)
    ],
}


def run_demo():
    print(f"========================================")
    print(f"   🚀 CKB-TEXTIFY FINAL VERIFICATION 🚀")
    print(f"========================================")

    for category, tests in test_suites.items():
        print(f"\n>> {category}")
        print("-" * 60)
        for text in tests:
            try:
                normalized = convert_all(text)
                print(f"IN : {text}")
                print(f"OUT: {normalized}")
                print("." * 20)
            except Exception as e:
                print(f"IN : {text}")
                print(f"❌ ERROR: {e}")

    print("\n========================================")
    print(f"   ✅ DEMO COMPLETED")
    print(f"========================================")


if __name__ == "__main__":
    run_demo()