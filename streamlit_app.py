"""Certificate Sentinel — Streamlit entry point."""

from dotenv import load_dotenv

load_dotenv()

import streamlit as st

from src.utils.auth import require_password

st.set_page_config(
    page_title="Certificate Sentinel",
    page_icon="🛡️",
    layout="wide",
)

if not require_password():
    st.stop()

pages = {
    "Validation": "validation",
    "Eval Harness": "eval",
}

with st.sidebar:
    st.title("Certificate Sentinel")
    st.caption("Semantic validation prototype")
    page = st.radio("Navigate", list(pages.keys()))

if pages[page] == "validation":
    from src.ui.pages import validation_page
    validation_page()
elif pages[page] == "eval":
    from src.ui.pages import eval_page
    eval_page()
