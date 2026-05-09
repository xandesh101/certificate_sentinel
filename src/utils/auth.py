"""Streamlit password gate."""

import os

import streamlit as st


def require_password() -> bool:
    """Return True if authenticated. Shows password input and blocks otherwise."""
    expected = os.getenv("APP_PASSWORD", "")
    if not expected:
        st.warning("APP_PASSWORD not set. Running without authentication.")
        return True

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    st.title("Certificate Sentinel")
    st.write("This prototype is password-protected.")
    pw = st.text_input("Password", type="password")
    if st.button("Enter"):
        if pw == expected:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    return False
