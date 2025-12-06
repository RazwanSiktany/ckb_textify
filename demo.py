import sys
import time
from ckb_textify import convert_all

# --- 1. Standard Test Suites (Default Config) ---
test_suites = {

    "🔢 Numbers & Math": [
        "Integers: 123456",
        "Decimals: 12.5, 0.005",
        "Negative: -50, +20",
        "Small Scientific: 0.00000000000000000000004",          # Should be: ...sAlb bIst w sI
        "Large Scientific: 34000000000000000000000",
        "Zeros: 0025 (2 zeros), 000007 (5 zeros)",
        "Fractions: 1/2, 1/4, 3/4, 1/3, 1/8", # Niw, Charek...
        "Math Chain: 5 + 3 - 2 * 4 / 2 = 10",
        "کردارە بیرکارییەکان: 5 + 3 - 2 * 4 / 2 = 10",
        "Functions: ln 4 / log 10 + sin 90",
        "Approx: val ≈ 3.14",
        "Power: Area = 50m^2",
    ],

    "📏 Units & Measurements": [
        "Ambiguity: 10m vs I am m",         # Unit vs Letter
        "Ambiguity: 5mm vs 5mm gun",
        "Suffixes: 10kgm (My 10kg)",        # 10 Kilogram-m
        "Per Rule: 120km/h",                # ... bo her katjhmerek
        "Complex: 3.5mg/ml",
        "Data: 500gb hard drive",
    ],

    "💰 Currency": [
        "IQD: 25000 IQD",
        "Dollar: $12.50",
        "Pound: £50",
        "Euro: €100",
        "Yen: ¥1000",
        "Standalone: $ vs د.ع",             # Should convert symbol to name
    ],

    "📞 Phone & Date": [
        "Local: 07501234567",               # 4-3-2-2 grouping
        "Intl: +9647701234567",             # Country code + grouping
        "Spaced: 0750 123 45 67",
        "Date: 2025/12/03",
        "Date: 03-12-2025",
        "Time: 12:30 PM",
        "Time: 06:41ی بەیانی",
    ],

    "🌍 Global Scripts (Transliteration)": [
        "English (IPA): Hello World",       # Phonetic (Hêllo)
        "English (Rule): Razwan",           # Fallback
        "Acronyms: ChatGPT & GPT-4",        # Chat (IPA) + GPT (Letters)
        "German: Straẞe",                   # ẞ -> ss
        "French: République française",     # Accents -> Latin
        "Greek: Χαίρετε",
        "Russian: Путин",
        "Chinese: 你好",
        "Kurmanji: Êvar baş",               # Ê -> ئێ (Initial Hamza)
    ],

    "🕌 Tajweed & Diacritics": [
        "Basmala: بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ", # Shamsi, Wasla, Allah
        "Allah Context: ٱلْحَمْدُ لِلَّهِ",  # Lillahi rule
        "Mirsad: مِرْصَاد",                 # Heavy Ra (ڕ)
        "Iqlab: مِنْ بَعْد",                # N -> M
        "Idgham: مَنْ يَقُول",              # N -> Y
        "Shadda: مُحَمَّد",                 # Doubling
        "Dagger Alif: مَـٰلِكِ",
        "Silent Alif: خَلَوْا۟",
    ],

    "💻 Technical & Web": [
        "Email: info@gmail.com",            # Smart domain reading
        "URL: www.rudaw.net",
        "UUID: 123e4567-e89b-12d3",         # Char-by-char
        "MAC: 00:1A:2B:3C:4D:5E",
        "بِسْمِ ٱللَّهِ",
    ]
}

# --- 2. Special Config Tests ---
special_tests = {
    "💬 Chat Speak (Config Enabled)": {
        "text": "7az dakam, s3at chand?",
        "config": {"chat_speak": True}
    },
    "😀 Emojis (Convert Mode)": {
        "text": "سڵاو 😂 دڵم ❤️",
        "config": {"emoji_mode": "convert"}
    },
    "😶 Emojis (Remove Mode - Default)": {
        "text": "سڵاو 😂 دڵم ❤️",
        "config": {"emoji_mode": "remove"}
    }
}

def run_demo():
    print(f"========================================")
    print(f"   🚀 CKB-TEXTIFY ULTIMATE DEMO 🚀")
    print(f"========================================")

    # Run Standard Suites
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

    # Run Special Config Tests
    print(f"\n>> ⚙️ Special Configuration Tests")
    print("-" * 60)
    for name, data in special_tests.items():
        text = data["text"]
        conf = data["config"]
        try:
            normalized = convert_all(text, config=conf)
            print(f"TEST: {name}")
            print(f"IN  : {text}")
            print(f"OUT : {normalized}")
            print("." * 20)
        except Exception as e:
            print(f"❌ ERROR: {e}")

    print("\n========================================")
    print(f"   ✅ DEMO COMPLETED")
    print(f"========================================")


if __name__ == "__main__":
    run_demo()