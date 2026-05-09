"""Reusable Streamlit UI components."""

import streamlit as st


def synthetic_data_banner() -> None:
    st.warning(
        "SYNTHETIC DATA ONLY — All customer names, taxpayer IDs, transactions, and certificates "
        "are fictional and generated for demonstration purposes. No real customer data is used.",
        icon="⚠️",
    )


def decision_banner(decision: str) -> None:
    if decision == "PASS":
        st.success(f"Decision: **{decision}** — Certificate validated. Exemption appears legitimate.", icon="✅")
    elif decision == "FLAG":
        st.error(f"Decision: **{decision}** — Certificate flagged. Tax team review required.", icon="🚩")
    else:
        st.warning(f"Decision: **{decision}** — Insufficient data for automated determination. Human review required.", icon="🔍")


def confidence_meter(confidence: float) -> None:
    label = "Confidence"
    if confidence >= 0.85:
        color = "green"
    elif confidence >= 0.65:
        color = "orange"
    else:
        color = "red"

    st.metric(label, f"{confidence:.0%}")
    st.progress(confidence)


def citation_list(citations: list) -> None:
    if not citations:
        st.caption("No citations recorded.")
        return

    by_source: dict[str, list] = {}
    for c in citations:
        src = c.get("source") if isinstance(c, dict) else c.source
        by_source.setdefault(src, []).append(c)

    source_labels = {
        "state_rule": "State Rules",
        "transaction": "Transaction History",
        "certificate_field": "Certificate Fields",
    }

    for source, items in by_source.items():
        with st.expander(f"{source_labels.get(source, source)} ({len(items)})"):
            for item in items:
                if isinstance(item, dict):
                    ref_id = item.get("reference_id", "")
                    excerpt = item.get("excerpt", "")
                else:
                    ref_id = item.reference_id
                    excerpt = item.excerpt
                st.markdown(f"**`{ref_id}`** — {excerpt}")
