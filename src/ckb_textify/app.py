import streamlit as st
from ckb_textify.core.pipeline import Pipeline
from ckb_textify.core.types import NormalizationConfig

# --- Page Configuration ---
st.set_page_config(
    page_title="Kurdish Text Normalizer v2",
    page_icon="🦁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for RTL and Fonts ---
st.markdown("""
    <style>
    /* Import Noto Naskh Arabic for better Kurdish rendering if needed */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Naskh+Arabic:wght@400;700&display=swap');

    /* Target all text areas (Input and Output) */
    .stTextArea textarea {
        direction: rtl;
        text-align: right;
        font-family: 'Noto Naskh Arabic', 'Calibri', sans-serif;
        font-size: 22px;
        line-height: 1.6;
    }

    /* Input Labels */
    .stTextArea label {
        font-size: 18px;
        font-weight: bold;
    }

    /* Sidebar Styling */
    .css-1d391kg {
        text-align: left;
    }

    /* Success Message */
    .stSuccess {
        direction: rtl;
        text-align: right;
    }
    </style>
""", unsafe_allow_html=True)

# --- Sidebar: Configuration ---
st.sidebar.title("⚙️ Configuration")
st.sidebar.markdown("Enable/Disable specific modules:")

# 1. Feature Toggles
with st.sidebar.expander("🛠️ Core Features", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        enable_numbers = st.checkbox("Numbers (123)", value=True)
        enable_web = st.checkbox("Web (URLs/Emails)", value=True)
        enable_phone = st.checkbox("Phone Numbers", value=True)
        enable_date = st.checkbox("Date & Time", value=True)
        enable_units = st.checkbox("Units (km, kg)", value=True)
    with col2:
        enable_currency = st.checkbox("Currency ($)", value=True)
        enable_math = st.checkbox("Math (+-*/)", value=True)
        enable_tech = st.checkbox("Technical (IDs)", value=True)
        enable_symbols = st.checkbox("Symbols (&, %)", value=True)

with st.sidebar.expander("🗣️ Linguistics", expanded=True):
    enable_linguistics = st.checkbox("Text Cleanup (Names/Abbr)", value=True)
    enable_transliteration = st.checkbox("Transliteration (English)", value=True)
    enable_diacritics = st.checkbox("Diacritics (Quranic)", value=True)

# 2. Advanced Modes
st.sidebar.markdown("---")
st.sidebar.subheader("🎨 Behaviors")

emoji_mode = st.sidebar.selectbox(
    "Emoji Handling",
    options=["remove", "convert", "ignore"],
    index=0,  # Default: remove
    format_func=lambda x: f"{x.capitalize()} (e.g. 😂)"
)

diacritics_mode = st.sidebar.selectbox(
    "Diacritics Mode",
    options=["convert", "remove", "keep"],
    index=0,  # Default: convert
    help="'Convert' turns Harakat into Kurdish letters. 'Remove' strips them. 'Keep' leaves them."
)

shadda_mode = st.sidebar.selectbox(
    "Shadda Handling",
    options=["double", "remove"],
    index=0,
    help="Double: مّ -> مم | Remove: مّ -> م"
)

# --- Main App Interface ---
st.title("🦁 ckb-textify v2")
st.markdown("##### Advanced Kurdish (Sorani) Text Normalization Engine")

# Input Area
input_text = st.text_area("Input Text (Kurdish/English/Arabic)", height=200,
                          placeholder="Type something here... e.g., Hello! Call 07501234567.")

col_btn, col_info = st.columns([1, 4])

with col_btn:
    process_btn = st.button("Normalize Text", type="primary", use_container_width=True)

if process_btn and input_text:
    # 1. Build Configuration object based on Sidebar inputs
    config = NormalizationConfig(
        enable_numbers=enable_numbers,
        enable_web=enable_web,
        enable_phone=enable_phone,
        enable_date_time=enable_date,
        enable_units=enable_units,
        enable_currency=enable_currency,
        enable_math=enable_math,
        enable_technical=enable_tech,
        enable_symbols=enable_symbols,
        enable_linguistics=enable_linguistics,
        enable_transliteration=enable_transliteration,
        enable_diacritics=enable_diacritics,
        emoji_mode=emoji_mode,
        diacritics_mode=diacritics_mode,
        shadda_mode=shadda_mode
    )

    # 2. Initialize Pipeline
    pipeline = Pipeline(config)

    # 3. Process
    try:
        normalized_text = pipeline.normalize(input_text)

        # 4. Display Output
        st.success("Normalization Complete!")
        st.text_area("Normalized Output", value=normalized_text, height=250)

    except Exception as e:
        st.error(f"An error occurred during processing: {e}")

elif process_btn and not input_text:
    st.warning("Please enter some text to normalize.")

# --- Footer ---
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: grey;'>Built with ❤️ for Kurdish Language Technology</div>",
    unsafe_allow_html=True
)