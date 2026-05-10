"""Certificate Sentinel — Streamlit entry point."""

from dotenv import load_dotenv

load_dotenv()

from pathlib import Path

def _ensure_certificates():
    cert_dir = Path(__file__).parent / "data" / "certificates"
    pdfs = list(cert_dir.glob("*.pdf"))
    if not pdfs:
        from scripts.generate_certificates import generate_all
        generate_all()

_ensure_certificates()

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
    "Overview": "overview",
    "Validation": "validation",
    "Scenario Browser": "scenarios",
    "Architecture": "architecture",
    "Eval Harness": "eval",
}

with st.sidebar:
    st.title("Certificate Sentinel")
    st.caption("Semantic validation prototype")
    page = st.radio("Navigate", list(pages.keys()))

if pages[page] == "overview":
    from src.ui.pages import overview_page
    overview_page()
elif pages[page] == "validation":
    from src.ui.pages import validation_page
    validation_page()
elif pages[page] == "scenarios":
    from src.ui.pages import scenarios_page
    scenarios_page()
elif pages[page] == "architecture":
    from src.ui.pages import architecture_page
    architecture_page()
elif pages[page] == "eval":
    from src.ui.pages import eval_page
    eval_page()
