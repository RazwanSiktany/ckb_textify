# 🦁 ckb-textify

[![PyPI version](https://badge.fury.io/py/ckb-textify.svg)](https://badge.fury.io/py/ckb-textify)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://ckb-textify.streamlit.app/)

**ckb-textify** is an industrial-strength **Text Normalization** and **Transliteration** library designed specifically for **Central Kurdish (Sorani)**.

While most normalizers perform simple "Find & Replace", `ckb-textify` uses a context-aware pipeline to transform "messy" real-world text—including mixed languages, scientific notation, Quranic Tajweed, and technical jargon—into clean, spoken Kurdish text. It is the perfect pre-processor for **Text-to-Speech (TTS)** and **NLP** models.

---

## 🚀 Live Demo

Try the library instantly in your browser:
👉 **[Click here to open the Live App](https://ckb-textify.streamlit.app/)**

## 🔮 The Ecosystem

`ckb-textify` handles **Normalization** (Text-to-Text). For **Phonemization** (Text-to-Sounds/IPA), check out the companion project:

* **🦁 ckb-g2p (Grapheme-to-Phoneme):** [GitHub](https://github.com/RazwanSiktany/ckb_g2p) | [Demo](https://ckb-g2p.streamlit.app/)

---

## 📦 Installation

```bash
pip install ckb-textify
```

**Key Dependencies:**
* `eng-to-ipa`: For accurate English pronunciation (e.g., "Phone" -> "Fôn").
* `anyascii`: For universal script transliteration (Chinese, Russian, etc.).

---

## ⚡ Quick Start

```python
from ckb_textify import convert_all

text = """
سڵاو! تکایە پەیوەندی بکە بە 07501234567.
نرخی زێڕ ≈ $2500.
کۆدەکە A1-B2 یە.
سڵاو لە Putin و Xi Jinping.
"""

# Default normalization (All features enabled)
normalized = convert_all(text)

print(normalized)
```

**Output:**
```text
سڵاو! تکایە پەیوەندی بکە بە سفر حەوت سەد و پەنجا سەد و بیست و سێ چل و پێنج شەست و حەوت.
نرخی زێڕ نزیکەی دوو ھەزار و پێنج سەد دۆلار.
کۆدەکە ئەی یەک داش بی دوو یە.
سڵاو لە پوتین و سی جینپینگ.
```

---

## 🏛️ Architecture

`ckb-textify` processes text through a strictly ordered pipeline to handle dependencies (e.g., Units must be processed before Technical codes).

---

## 🌟 Advanced Features

### 1. 🕌 Deep Linguistic & Tajweed Support
Unlike basic normalizers, this library respects complex phonological rules for Arabic/Islamic text embedded in Kurdish.

* **Shamsi (Sun) Letters:** Automatically assimilates the 'L' in 'Al-'.
    * Input: `بِسْمِ ٱللَّهِ`
    * Output: `بیسمی للاھی` (Handles the "Light Lam" vs "Dark Lam" rule automatically).
* **Context-Aware "Allah":** Determines pronunciation (L vs LL) based on the preceding vowel.
* **Alif Wasla (ٱ):** Treated as silent in continuation, but pronounced as 'E' at the start.
* **Tajweed Rules:** Handles *Iqlab* (N->M) and *Idgham*.
* **Heavy 'R' (ڕ):** Detects heavy R based on Arabic vowel context (e.g., `مِرْصَاد` -> `میڕساد`).

### 2. 🌍 Universal Script Support ("The Latin Bridge")
Transliterates almost any world script into Sorani using a smart "Latin Bridge" technique.

| Language | Input | Output (Sorani) |
| :--- | :--- | :--- |
| **Chinese** | `你好` | `نی هاو` |
| **Russian** | `Путин` | `پوتین` |
| **Greek** | `Χαίρετε` | `چایرێت` |
| **German** | `Straẞe` | `ستراسسە` |
| **French** | `République` | `ڕیپەبلیک` |
| **English** | `Phone` | `فۆن` (IPA-based, not rule-based) |

### 3. ➗ Scientific & Mathematical Logic
Handles complex math that breaks most normalizers.

* **Scientific Notation:** `5e-23` $\\rightarrow$ `پێنج جارانی دە توانی سالب بیست و سێ`
* **Functions:** `ln 4` $\\rightarrow$ `لۆگاریتمی سروشتی چوار`
* **Fraction Logic:**
    * `1/2` $\\rightarrow$ `نیوە`
    * `3/4` $\\rightarrow$ `سێ چارەک`
    * `120km/h` $\\rightarrow$ `... بۆ هەر کاتژمێرێک` (Context-aware "Per" rule)
    * `7/6` $\\rightarrow$ `حەوت دابەش شەش` (Context-aware "Division" rule)

### 4. 📞 Smart Phone Numbers
Recognizes Iraqi and International phone formats and groups digits for natural reading (4-3-2-2 format).

* `07501234567` $\\rightarrow$ `سفر حەوت سەد و پەنجا ...`
* `+964...` $\\rightarrow$ `کۆ نۆ سەد و شەست و چوار ...`

### 5. 💻 Web & Technical Entities
* **URLs:** `www.rudaw.net` $\\rightarrow$ `دابڵیو دابڵیو دابڵیو دۆت رووداو دۆت نێت`
* **Emails:** `info@gmail.com` $\\rightarrow$ `... ئەت جیمەیڵ دۆت کۆم` (Recognizes common domains)
* **Codes:** `A1-B2` $\\rightarrow$ `ئەی یەک داش بی دوو` (Character-by-character reading)

### 6. 📏 Context-Aware Units
Solves the ambiguity between units and letters.
* `10m` $\\rightarrow$ `دە مەتر`
* `I am m` $\\rightarrow$ `ئای ئەم ئێم` (Letter M)
* `12.5kg` $\\rightarrow$ `دوازدە کیلۆگرام و نیو` (Handles .5 as "Half")

---

## 🎛️ Configuration

You can fully customize the pipeline by passing a `config` dictionary.

```python
from ckb_textify import convert_all

custom_config = {
    "phone_numbers": False,    # Keep phone numbers as digits
    "foreign": False,          # Disable Chinese/Russian transliteration
    "shadda_mode": "remove",   # "remove" or "double" (default)
    "emoji_mode": "convert",   # "remove" (default), "convert", "ignore"
    "chat_speak": True         # Enable '7ez' -> 'حەز' conversion
}

print(convert_all("Text...", config=custom_config))
```

### Available Options
| Key | Default | Description |
| :--- | :--- | :--- |
| `diacritics_mode` | `"convert"` | Convert Arabic Harakat to Kurdish vowels. |
| `shadda_mode` | `"double"` | Doubles the letter for Shadda (`مّ` -> `مم`). |
| `emoji_mode` | `"remove"` | Removes emojis. Set to `"convert"` to speak them. |
| `chat_speak` | `False` | Converts Arabizi numbers (`7`->`ح`, `3`->`ع`). |
| `math` | `True` | Normalizes math expressions and functions. |
| `web` | `True` | Spells out URLs and Emails. |
| `technical` | `True` | Spells out codes like UUIDs. |

---

## 🤝 Contributing

Contributions are widely welcomed! If you have ideas for new rules, found a bug, or want to add support for more units:

1.  **Fork** the repository.
2.  **Clone** locally.
3.  **Create a branch** (`git checkout -b feature/new-rule`).
4.  **Run Tests** (`python -m unittest discover tests`).
5.  **Submit a Pull Request**.

## 👨‍💻 Author

**Razwan M. Haji**
* **GitHub:** [RazwanSiktany](https://github.com/RazwanSiktany/)
* **PyPI:** [ckb-textify](https://pypi.org/project/ckb-textify/)

## 📄 License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).