[![PyPI version](https://badge.fury.io/py/ckb-textify.svg)](https://badge.fury.io/py/ckb-textify)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/ckb-textify)](https://pepy.tech/project/ckb-textify)

# ckb-textify

**ckb-textify** is a comprehensive, industrial-strength Text
Normalization and Transliteration library designed specifically for
**Central Kurdish (Sorani)**.

It is built to prepare "messy" real-world text for Natural Language
Processing (NLP) tasks, with a specific focus on **Text-to-Speech
(TTS)** engines. It handles complex ambiguity, mixed-script
(English/Kurdish) text, technical codes, and locale-specific formats
like Iraqi phone numbers.

## 📦 Installation

You can install the package directly from PyPI:

``` bash
pip install ckb-textify
```

Dependencies:

-   **eng-to-ipa**: Used for accurate English-to-Sorani transliteration.

## 🚀 Quick Start

### Python Example

``` python
from ckb_textify import convert_all

text = "سڵاو، پەیوەندی بکە بە 07501234567.
نرخی کاڵاکە $12.50 یە.
کۆدەکە A1-B2 یە."

normalized = convert_all(text)

print(normalized)
```

**Output:**

    سڵاو, پەیوەندی بکە بە سفر حەوت سەد و پەنجا سەد و بیست و سێ چل و پێنج شەست و حەوت.
    نرخی کاڵاکە دوازدە دۆلار و پەنجا سەنت یە.
    کۆدەکە ئەی یەک داش بی دوو یە.

## 🎛️ Configuration

You can enable or disable specific normalization modules using a config
dictionary.\
By default, **all features are enabled**.

``` python
from ckb_textify import convert_all

my_config = {
    "phone_numbers": False,
    "technical": False
}

text = "Call 07501234567 regarding ID: 550e8400."
normalized = convert_all(text, config=my_config)
print(normalized)
```

Output will **keep the phone number and ID unchanged**.

------------------------------------------------------------------------

## 🌟 Features & Examples

### 1. Smart Phone Numbers

Handles Iraqi/Kurdish formats with intelligent grouping (4-3-2-2).

    07501234567 → سفر حەوت سەد و پەنجا سەد و بیست و سێ چل و پێنج شەست و حەوت
    +964... → کۆ نۆ سەد و شەست و چوار...

### 2. Math & Scientific Notation

Context-aware processing:

-   `7/6` → حەوت دابەش شەش\
-   `km/h` → کیلۆمەتر بۆ هەر کاتژمێرێک\
-   `34000000000000000000` → سێ پۆینت چوار جارانی دە توانی نۆزدە\
-   `00025` → سێ جار سفر بیست و پێنج

### 3. English Transliteration (IPA-Based)

    Phone → فۆن
    Action → ئاکشن
    Google → گووگڵ
    GPT → جی پی تی
    USA → یو ئێس ئەی

### 4. Web & Technical Entities

Reads symbols character-by-character:

-   **Emails:** `info@gmail.com` → ئای ئێن ئێف ئۆ ئەت جیمەیڵ دۆت کۆم\
-   **URLs:** `www.razwan.net` → دابڵیو دابڵیو دابڵیو دۆت ئاڕ ئەی زێت دابڵیو ئەی ئێن دۆت نێت\
-   **Codes:** `A1-B2` → ئەی یەک داش بی دوو\
-   **MAC/UUID:** Handles patterns like `00:1A:2B...`

### 5. Units & Measurements

    10m → دە مەتر
    m (alone) → m
    10kg → ده کیلۆگرام

### 6. Currency & Finance

    $12.5 → دوازدە دۆلار و نیو
    IQD 5000 → پێنج هەزار دیناری عێڕاقی
    £50, ¥1000, €20 → Supported

### 7. Standardization

-   Fixes Unicode inconsistencies (ی, ە, ه, ھ, ة)
-   Expands abbreviations (د. ← دکتۆر)
-   Normalizes Arabic names (محمد ← موحەمەد)

------------------------------------------------------------------------

## 📄 License

This project is licensed under the **MIT License**.\
See the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome!\
Open an issue or submit a pull request with improvements or new rules.
