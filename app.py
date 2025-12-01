import streamlit as st
from ckb_textify import convert_all

# Page Config
st.set_page_config(
    page_title="Kurdish Text Normalizer",
    page_icon="🦁",
    layout="centered"
)

# Custom CSS for Right-to-Left (RTL) support and Font Styling
# Sets font to Calibri 15px for input and output areas
st.markdown("""
    <style>
    /* Target all text areas (Input and Output) */
    .stTextArea textarea {
        direction: rtl;
        text-align: right;
        font-family: 'Calibri', sans-serif;
        font-size: 20px;
    }
    /* Align markdown text to right */
    .stMarkdown {
        text-align: right;
    }
    /* Fix alignment for sidebar */
    .css-1d391kg {
        text-align: left;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.title("🦁 Kurdish Text Normalizer")
st.markdown("This tool normalizes Central Kurdish (Sorani) text for TTS and NLP.")

# --- Sidebar Configuration ---
st.sidebar.title("Configuration (ڕێکخستنەکان)")

# 1. Expansion Modules
st.sidebar.header("Expansion Modules")
opt_phone = st.sidebar.checkbox("Phone Numbers", True)
opt_date = st.sidebar.checkbox("Date & Time", True)
opt_units = st.sidebar.checkbox("Units (kg, m...)", True)
opt_per = st.sidebar.checkbox("Per Rule (km/h)", True)
opt_math = st.sidebar.checkbox("Math Operations", True)
opt_currency = st.sidebar.checkbox("Currency", True)
opt_percent = st.sidebar.checkbox("Percentage", True)

# 2. Textual Features
st.sidebar.header("Textual Features")
opt_web = st.sidebar.checkbox("Web & Email", True)
opt_tech = st.sidebar.checkbox("Technical Codes", True)
opt_abbr = st.sidebar.checkbox("Abbreviations (د. -> دکتۆر)", True)
opt_names = st.sidebar.checkbox("Arabic Names", True)
opt_latin = st.sidebar.checkbox("Latin/English Transliteration", True)
opt_foreign = st.sidebar.checkbox("Foreign Scripts (Chinese/Russian)", True)
opt_symbols = st.sidebar.checkbox("Symbols (@, #)", True)

# 3. Numbers
st.sidebar.header("Number Types")
opt_decimal = st.sidebar.checkbox("Decimal Numbers", True)
opt_integer = st.sidebar.checkbox("Integer Numbers", True)

# 4. Diacritics & Harakat
st.sidebar.header("Quranic Diacritics (حەرەکات)")
diacritics_mode = st.sidebar.selectbox(
    "Diacritics Mode",
    options=["convert", "remove", "keep"],
    index=0,
    help="'convert': Fatha->ە, 'remove': Delete all, 'keep': Do nothing"
)
shadda_mode = st.sidebar.selectbox(
    "Shadda Mode",
    options=["double", "remove"],
    index=0,
    help="'double': مّ -> مم, 'remove': Delete Shadda"
)
remove_tatweel = st.sidebar.checkbox("Remove Tatweel (ـ)", True)

# Compile Configuration Dictionary
user_config = {
    "diacritics_mode": diacritics_mode,
    "shadda_mode": shadda_mode,
    "remove_tatweel": remove_tatweel,
    "phone_numbers": opt_phone,
    "date_time": opt_date,
    "units": opt_units,
    "per_rule": opt_per,
    "math": opt_math,
    "currency": opt_currency,
    "percentage": opt_percent,
    "web": opt_web,
    "technical": opt_tech,
    "abbreviations": opt_abbr,
    "arabic_names": opt_names,
    "latin": opt_latin,
    "foreign": opt_foreign,
    "symbols": opt_symbols,
    "decimals": opt_decimal,
    "integers": opt_integer
}

# --- Main UI ---

# Input Area
text_input = st.text_area(
    "Input Text (دەقی کوردی):",
    height=150,
    placeholder="لێرە بنووسە..."
)

# Button & Logic
if st.button("Normalize (گۆڕین)"):
    if text_input:
        try:
            # Process text with user configuration
            normalized_text = convert_all(text_input, config=user_config)

            st.success("✅ Result (ئەنجام):")

            # Output Area (using text_area for wrapping)
            st.text_area(
                label="Output",
                value=normalized_text,
                height=200,
                label_visibility="collapsed"
            )

        except Exception as e:
            st.error(f"An error occurred: {e}")
    else:
        st.warning("Please enter some text first.")

# Footer
st.markdown("---")
st.caption("Powered by [ckb-textify](https://github.com/RazwanSiktany/ckb_textify)")