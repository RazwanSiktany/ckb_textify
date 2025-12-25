import sys
from ckb_textify.core.pipeline import Pipeline
from ckb_textify.core.types import NormalizationConfig


def header(title):
    print(f"\n{'=' * 60}")
    print(f"   🦁 {title}")
    print(f"{'=' * 60}")


def run_test_suite(name, pipeline, inputs):
    print(f"\n>> 🧪 Suite: {name}")
    print("-" * 60)
    for text in inputs:
        try:
            result = pipeline.normalize(text)
            print(f"IN : {text}")
            print(f"OUT: {result}")
            print("." * 40)
        except Exception as e:
            print(f"IN : {text}")
            print(f"❌ ERROR: {e}")


# --- 1. Standard Feature Suites ---
test_suites = {

    "🔢 Numbers & Math Stress Test": [
        "Integers: 123456",
        "Decimals: 12.5, 0.005",
        "Negative: -50, +20",
        "Small Scientific (Threshold): 0.00000000000000000000004",  # Should convert to scientific text
        "Large Scientific (Threshold): 34000000000000000000000",  # Should convert to scientific text
        "Explicit Scientific: 5.2e-10",
        "Leading Zeros: 0025 (2 zeros), 000007 (5 zeros)",
        "Fractions: 1/2, 1/4, 3/4, 1/3, 1/8",
        "Math Chain: 5 + 3 - 2 * 4 / 2 = 10",
        "Functions (No Code Conflict): ln 4 / log 10 + sin 90",  # Tests exclusion from Technical Normalizer
        "Approx & Power: val ≈ 3.14 and Area = 50m^2",
        "Complex Bracket: (10 + 5) * [2 - 1]",
    ],

    "📏 Units & Measurements (Context Aware)": [
        "Ambiguity: 10m vs I am m",
        "Ambiguity: 5mm vs 5mm gun",
        "Generic Half Rule: 4.5 مریشک",  # Should be: Chwar mreshk u niw
        "Suffix Half Rule: ١.٥ مریشکەکانم",  # Should be: Yek mreshk u niw-ekan-m
        "Per Rule: 120km/h",  # ... bo her katjhmerek
        "Per Rule + Suffix: 10km/hـە",  # Should handle Tatweel/Suffix correctly
        "Complex Unit: 3.5mg/ml",
        "Data: 500gb hard drive",
    ],

    "💰 Currency": [
        "IQD: 25000 IQD",
        "Dollar: $12.50",
        "Pound: £50",
        "Euro: €100",
        "Yen: ¥1000",
        "Standalone: $ vs د.ع",  # Should convert symbol to name
        "Complex IQD: 15000 د.ع",
    ],

    "📞 Phone & Date": [
        "Local: 07501234567",  # 4-3-2-2 grouping
        "Intl: +9647701234567",  # Country code + grouping
        "Spaced: 0750 123 45 67",
        "Date: 2025/12/03",
        "Date: 03-12-2025",
        "Time: 12:30 PM",
        "Time Suffix: 12:30 PMـە",  # Tests suffix attachment logic
        "Time Text: 06:41ی بەیانی",
    ],

    "🌍 Global Scripts & Transliteration": [
        "English (IPA): Hello World",
        "English (Rule): Razwan",
        "Acronyms: ChatGPT & GPT-4",
        "German: Straẞe",  # ẞ -> ss -> strasse -> kurdish
        "French: République française",  # Accents -> Latin -> kurdish
        "Greek: Χαίρετε (Khairete)",  # Χ -> kh -> ...
        "Russian: Путин (Putin)",  # Cyrillic -> Latin -> Kurdish
        "北京市 ",
        "٧٢٬٢٥٦",
        "Kurmanji: Êvar baş",  # Ê -> ئێ
        "Mixed Script: UKم",  # UK + m suffix
        "Mixed Foreign: Приветـیشمان",  # Privet + ishman suffix
    ],

    "🕌 Tajweed & Diacritics": [
        "ٱللَّهُ",
        "مِن شَرِّ ٱلْوَسْوَاسِ",
        "Allah Context: ٱلْحَمْدُ لِلَّهِ",  # Lillahi rule
        "Compound Allah: عَبدُاللّٰه",  # Abdu-Llah (Heavy Lam trigger)
        "Mirsad: مِرْصَاد",  # Heavy Ra (ڕ)
        "Iqlab: مِنْ بَعْد",  # N -> M
        "Idgham: مَنْ يَقُول",  # N -> Y
        "Shadda: مُحَمَّد",  # Doubling
        "Silent Alif: خَلَوْا۟",
        "Silent Alif:  ٱلَّذِينَ",
    ],

    "💻 Technical & Web": [
        "Email: info@gmail.com",
        "Complex Email: xwshm@êxamplé.com",  # Tests unicode domain splitting
        "URL: https://www.rudaw.net/sorani?id=123",
        "UUID: 123e4567-e89b-12d3",
        "MAC: 00:1A:2B:3C:4D:5E",  # Tests MAC regex and colon conversion
        "Mixed Code: 8-αβγ123",  # Hyphenated Code -> Spell out
        "Negative Number: -αβγ123",  # Leading Hyphen -> Read as Number (after symbol cleaning)
        "Hash/Mention: #Kurdistan @User_1",
        "#Kurdistan",
        "1999 - 2005",
        "کاتی خایەنراو ٤٤:٠٠",
        "دەکرێ ١١١:٢٣",
    ]
}

# --- 2. Special Config Tests ---
special_tests = {
    "😀 Emojis (Convert Mode)": {
        "text": "سڵاو 😂 دڵم ❤️",
        "config": {"emoji_mode": "convert"}
    },
    "😶 Emojis (Remove Mode)": {
        "text": "سڵاو 😂 دڵم ❤️",
        "config": {"emoji_mode": "remove"}
    },
    "🛑 Symbols (Strict Mode)": {
        "text": "Hello!!! (Test) ???",
        "config": {"enable_symbols": True}  # Should filter multiple punct and parens
    },
    "⏸️ Pause Markers (Enabled)": {
        "text": "07501234567",
        "config": {"enable_pause_markers": True}
    }
}


def run_comprehensive_paragraph():
    header("📜 COMPREHENSIVE PARAGRAPH TEST")
    text = """
    سڵاو! ئەمڕۆ ڕێکەوتی 2025/10/05ـە و کاتژمێر 12:30 PMـە. لە بازاڕ 4.5kg سێوم کڕی بە 5000 IQD، هەروەها 1.5 مریشکیشم بۆ نیوەڕۆ خوارد. 
    تکایە سەردانی https://www.rudaw.net/sorani?ref=123 بکە یان ئیمەیڵ بنێرە بۆ support@êxamplé.com ئەگەر پرسیارت هەیە.
    کۆدی تایبەت: #KRD-v2 و MAC: 00:1A:2B:3C:4D:5E. 
    بیرت نەچێت: (10 + 5) * 2 = 30 و log 100 = 2. 
    پلەی گەرمی ئەمڕۆ 45°Cـە و خێرایی با 10km/hـە. 
    وشەی "Hello" بە ئینگلیزییە، "Straẞe" ئەڵمانییە، "Χαίρετε" یۆنانییە. 
    لە کۆتاییدا: بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ ❤️.
    """

    pipe = Pipeline(NormalizationConfig(emoji_mode="convert"))
    print(f"IN:\n{text}\n")
    print("-" * 60)
    try:
        result = pipe.normalize(text)
        print(f"OUT:\n{result}")
    except Exception as e:
        print(f"❌ ERROR: {e}")


if __name__ == "__main__":
    # 1. Run Categorized Suites
    default_pipe = Pipeline()
    for category, inputs in test_suites.items():
        run_test_suite(category, default_pipe, inputs)

    # 2. Run Special Configs
    header("SPECIAL CONFIGURATIONS")
    valid_keys = NormalizationConfig.__dataclass_fields__.keys()

    for name, data in special_tests.items():
        text = data["text"]
        raw_config = data["config"]
        filtered_config = {k: v for k, v in raw_config.items() if k in valid_keys}

        if len(filtered_config) < len(raw_config):
            skipped = set(raw_config) - set(filtered_config)
            print(f"\n⚠️  Skipping unknown config keys for '{name}': {skipped}")

        config = NormalizationConfig(**filtered_config)
        special_pipe = Pipeline(config)

        run_test_suite(name, special_pipe, [text])

    # 3. Run The Big One
    run_comprehensive_paragraph()

    print("\n✅ Advanced Demo Complete.")