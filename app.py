import streamlit as st
from ckb_textify import convert_all

# Page Config
st.set_page_config(
    page_title="Kurdish Text Normalizer",
    page_icon="🦁",
    layout="centered"
)

# Custom CSS for Right-to-Left (RTL) support
# This targets ALL text areas (Input and Output)
st.markdown("""
    <style>
    .stTextArea textarea {
        direction: rtl;
        text-align: right;
        font-family: 'Tahoma', 'Calibri', sans-serif;
        font-size: 18px;
    }
    .stMarkdown {
        text-align: right;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.title("🦁 Kurdish Text Normalizer")
st.write("This tool normalizes Central Kurdish (Sorani) text for TTS and NLP.")

# Input Area
text_input = st.text_area(
    "Input Text (دەقی کوردی):",
    height=150,
    placeholder="لێرە بنووسە..."
)

# Sidebar Options
st.sidebar.header("Configuration")
normalize_nums = st.sidebar.checkbox("Phone Numbers", True)
normalize_tech = st.sidebar.checkbox("Technical Codes", True)
normalize_web = st.sidebar.checkbox("Web & Email", True)

# Prepare config
user_config = {
    "phone_numbers": normalize_nums,
    "technical": normalize_tech,
    "web": normalize_web
}

# Button & Logic
if st.button("Normalize (چاکسازی)"):
    if text_input:
        try:
            normalized_text = convert_all(text_input, config=user_config)
            st.success("✅ Result (ئەنجام):")

            # --- UPDATED: Use text_area instead of code ---
            # This enables text wrapping and RTL support
            st.text_area(
                label="Output",
                value=normalized_text,
                height=200,
                label_visibility="collapsed"  # Hides the small "Output" label
            )

        except Exception as e:
            st.error(f"An error occurred: {e}")
    else:
        st.warning("Please enter some text first.")

# Footer
st.markdown("---")
st.caption("Powered by [ckb-textify](https://github.com/RazwanSiktany/ckb-textify)")