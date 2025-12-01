# ckb-textify

[![PyPI version](https://badge.fury.io/py/ckb-textify.svg)](https://badge.fury.io/py/ckb-textify)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://ckb-textify.streamlit.app/)

**ckb-textify** is an industrial-strength Text Normalization and Transliteration library designed specifically for **Central Kurdish (Sorani)**.

It transforms "messy" real-world text (mixed languages, symbols, math, codes) into clean, spoken Kurdish text, making it the perfect pre-processor for **Text-to-Speech (TTS)** and NLP models.

## 🚀 Live Demo

Try the library instantly without installing anything:
👉 [**Click here to open the Live App**](https://ckb-textify.streamlit.app/)

## 🔮 Next Step: Phonemization (G2P)

This library handles **normalization** (Text-to-Text). If you need **Phonemization** (Text-to-Sounds/IPA) for building a TTS model, check out the companion project:

**🦁 ckb-g2p (Central Kurdish Grapheme-to-Phoneme)**

* **GitHub:** [RazwanSiktany/ckb_g2p](https://github.com/RazwanSiktany/ckb_g2p)

* **Live Demo:** [ckb-g2p.streamlit.app](https://ckb-g2p.streamlit.app/)

## 📦 Installation

```bash
pip install ckb-textify
```

**Dependencies:**

* `eng-to-ipa`: For accurate English pronunciation.

* `anyascii`: For universal transliteration (Chinese, Russian, etc.).

## ⚡ Usage

```python
from ckb_textify import convert_all

text = """
سڵاو، پەیوەندی بکە بە 07501234567.
نرخی زێڕ ≈ $2500.
کۆدەکە A1-B2 یە.
سڵاو لە Peter و Xi Jinping.
"""

normalized = convert_all(text)

print(normalized)

# Output:
# سڵاو, پەیوەندی بکە بە سفر حەوت سەد و پەنجا سەد و بیست و سێ چل و پێنج شەست و حەوت.
# نرخی زێڕ نزیکەی دوو هەزار و پێنج سەد دۆلار یە.
# کۆدەکە ئەی یەک داش بی دوو یە.
# سڵاو لە پیتەر و سی جینپینگ.
```

## 🌟 Features (v3.0.0)

### 1. 🌍 Universal Script Support

Transliterates almost any language into Sorani script using a "Latin Bridge" technique.

* **Chinese:** `你好` → `نی هاو`

* **Russian:** `Путин` → `پوتین`

* **Greek:** `Χαίρετε` → `چایرێت`

* **German/French:** Handles accents (`Straẞe` → `ستراسسە`, `République` → `ڕیپەبلیک`).

### 2. ➗ Advanced Math & Science

* **Scientific Notation:** `5e-23` → `پێنج جارانی دە توانی سالب بیست و سێ`

* **Functions:** `ln 4` → `لۆگاریتمی سروشتی چوار`

* **Context-Aware:** Distinguishes Division (`7/6`) from Rates (`km/h`).

### 3. 📞 Smart Phone Numbers

Handles Iraqi/Kurdish formats with intelligent grouping (4-3-2-2).

* `07501234567` → `سفر حەوت سەد و پەنجا...`

* `+964...` → `کۆ نۆ سەد و شەست و چوار...`

### 4. 🔡 English Transliteration (IPA)

Uses the International Phonetic Alphabet to pronounce English words correctly.

* `Phone` → `فۆن` (Not "پھۆنە")

* `Google` → `گووگڵ`

* **Acronyms:** `GPT` → `جی پی تی`

### 5. 💻 Web & Technical

Reads technical strings character-by-character.

* **Emails:** `info@gmail.com` → `ئای ئێن ئێف ئۆ ئەت جیمەیڵ دۆت کۆم`

* **URLs:** `www.razwan.net` → `دابڵیو دابڵیو دابڵیو دۆت ئاڕ ئەی زێت یو ئەی ئێن دۆت نێت`

* **Codes:** `A1-B2` → `ئەی یەک داش بی دوو`

### 6. 📏 Units & Measurements

Solves ambiguity between units and nouns.

* `10m` → `دە مەتر` (Unit) vs `m` → `m` (Noun/Letter)

* `120km/h` → `سەد و بیست کیلۆمەتر بۆ هەر کاتژمێرێک`

## 🎛️ Configuration

`ckb-textify` is fully configurable. You can enable or disable specific normalization modules by passing a dictionary to `convert_all`.

### Default Configuration

By default, **all features are enabled** (`True`), and the diacritics mode is set to `"convert"`.

Here is the full list of available options:

```python
config = {
    # --- Foundational ---
    "normalize_characters": True,   # Unify letters (ی, ک, ه)
    "normalize_digits": True,       # Convert ١٢٣ -> 123

    # --- Diacritics & Harakat ---
    "diacritics_mode": "convert",   # Options: "convert" (Fatha->ە), "remove", "keep"
    "shadda_mode": "double",        # Options: "double" (مّ -> مم), "remove"
    "remove_tatweel": True,         # Remove elongation character (ـ)

    # --- Expansion Modules ---
    "date_time": True,              # Dates and Times
    "phone_numbers": True,          # Phone numbers grouping
    "units": True,                  # Unit expansion (kg, m, cm...)
    "per_rule": True,               # Rates (km/h -> ... bo her ...)
    "math": True,                   # Math operations (+, -, scientific)
    "currency": True,               # Currency symbols ($, IQD)
    "percentage": True,             # Percentages (%, ٪)

    # --- Textual Features ---
    "web": True,                    # URLs and Emails
    "technical": True,              # Technical codes (UUID, MAC)
    "abbreviations": True,          # Expand abbr (د. -> دکتۆر)
    "arabic_names": True,           # Normalize names (محمد -> موحەمەد)
    "latin": True,                  # Transliterate English/Latin text
    "foreign": True,                # Transliterate other scripts (Chinese, Russian)
    "symbols": True,                # Common symbols (@, #, &)

    # --- Number Types ---
    "decimals": True,               # Decimal numbers
    "integers": True                # Integer numbers
}

# Example: Disable phone numbers and change diacritics mode
convert_all(text, config={"phone_numbers": False, "diacritics_mode": "remove"})
```

## 🤝 Contributing

Contributions are widely welcomed! If you have ideas for new rules, found a bug, or want to add support for more units, please feel free to open a Pull Request.

1. **Fork** the repository on GitHub.

2. **Clone** your fork locally.

3. **Create a new branch** for your feature (`git checkout -b feature/amazing-feature`).

4. **Run Tests** to ensure everything is working (`python -m unittest discover tests`).

5. **Commit** your changes.

6. **Push** to the branch and open a Pull Request.

## 🤝 Author

### Razwan M. Haji

* **GitHub:** [RazwanSiktany](https://github.com/RazwanSiktany/)

## 📄 License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).