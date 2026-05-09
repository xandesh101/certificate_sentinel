"""Streamlit page implementations."""

import json
import time
import uuid
from pathlib import Path

import streamlit as st

from src.ui.components import (
    citation_list,
    confidence_meter,
    decision_banner,
    synthetic_data_banner,
)

_CERT_DIR = Path(__file__).parent.parent.parent / "data" / "certificates"
_SCENARIOS_FILE = Path(__file__).parent.parent.parent / "eval_scenarios" / "scenarios.json"


def _load_scenarios() -> list[dict]:
    with open(_SCENARIOS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)["scenarios"]


def _load_cert(pdf_path: str) -> bytes:
    full = Path(__file__).parent.parent.parent / pdf_path
    if not full.exists():
        raise FileNotFoundError(f"Certificate PDF not found: {full}")
    return full.read_bytes()


def validation_page() -> None:
    """Main certificate validation page."""
    synthetic_data_banner()
    st.title("Certificate Sentinel")
    st.caption("Agentic semantic validation of sales tax exemption certificates")

    scenarios = _load_scenarios()
    scenario_options = {s["scenario_id"]: f"{s['scenario_id']} — {s['description']}" for s in scenarios}
    scenario_ids = list(scenario_options.keys())

    selected_id = st.selectbox(
        "Select a scenario",
        options=scenario_ids,
        format_func=lambda x: scenario_options[x],
    )

    selected = next(s for s in scenarios if s["scenario_id"] == selected_id)

    with st.expander("Scenario details"):
        st.markdown(f"**Customer:** `{selected['customer_id']}`")
        st.markdown(f"**Claimed exemption:** `{selected['claimed_exemption_type']}`")
        st.markdown(f"**Expected decision:** `{selected['expected_decision']}`")
        st.markdown(f"**Rationale:** {selected['rationale']}")

    run_btn = st.button("Run Validation", type="primary", use_container_width=True)

    if run_btn:
        try:
            pdf_bytes = _load_cert(selected["certificate_pdf"])
        except FileNotFoundError as e:
            st.error(str(e))
            st.info("Run `python scripts/generate_certificates.py` to generate certificate PDFs.")
            return

        with st.status("Running agent validation...", expanded=True) as status:
            st.write("Loading certificate PDF...")
            st.write("Calling Certificate Sentinel agent...")
            t0 = time.time()

            from src.agent.orchestrator import validate_certificate
            from src.agent.verifier import verify_decision

            decision, raw_messages, tool_calls, latency_ms = validate_certificate(
                pdf_bytes=pdf_bytes,
                customer_id=selected["customer_id"],
                scenario_id=selected_id,
            )
            decision = verify_decision(decision)
            elapsed = time.time() - t0
            status.update(label=f"Validation complete ({elapsed:.1f}s)", state="complete")

        st.divider()
        decision_banner(decision.decision)

        col1, col2 = st.columns(2)
        with col1:
            confidence_meter(decision.confidence)
        with col2:
            st.metric("Tool Calls", tool_calls)
            st.metric("Latency", f"{latency_ms / 1000:.1f}s")

        st.subheader("Reasoning")
        st.write(decision.reasoning_summary)

        st.subheader("Citations")
        cit_dicts = [c.model_dump() for c in decision.citations]
        citation_list(cit_dicts)

        st.divider()
        st.subheader("Human Override")
        with st.form("override_form"):
            override_decision = st.selectbox("Override decision to:", ["(no override)", "PASS", "FLAG", "NEEDS_REVIEW"])
            reason_code = st.selectbox(
                "Reason code:",
                ["agent_misread_transaction", "rule_misinterpreted", "data_outdated", "other"],
            )
            reviewer_note = st.text_input("Note (optional)")
            submit_override = st.form_submit_button("Submit Override")

        if submit_override and override_decision != "(no override)":
            from src.utils.run_logger import log_override
            oid = str(uuid.uuid4())
            run_id = str(uuid.uuid4())
            log_override(
                override_id=oid,
                run_id=run_id,
                original_decision=decision.decision,
                override_decision=override_decision,
                reason_code=reason_code,
                reviewer_note=reviewer_note,
            )
            st.success(f"Override logged: {decision.decision} → {override_decision}")

        with st.expander("View raw agent trace"):
            st.json(raw_messages)


def eval_page() -> None:
    """Evaluation harness page."""
    synthetic_data_banner()
    st.title("Eval Harness")
    st.caption("Run all 10 scenarios and compute precision, recall, and calibration metrics.")

    st.warning(
        "Running the full eval calls the Anthropic API for all 10 scenarios. "
        "This takes approximately 5 minutes and costs ~$0.50 in API usage.",
        icon="💰",
    )

    if st.button("Run Full Eval", type="primary"):
        with st.status("Running eval harness...", expanded=True) as status:
            from src.eval.runner import run_eval
            report = run_eval(progress_callback=lambda msg: st.write(msg))
            status.update(label="Eval complete", state="complete")

        _display_eval_report(report)
    elif "eval_report" in st.session_state:
        _display_eval_report(st.session_state.eval_report)
    else:
        st.info("Click 'Run Full Eval' to execute all 10 scenarios against the live API.")


def _display_eval_report(report) -> None:
    st.session_state.eval_report = report

    st.subheader("Headline Metrics")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Precision", f"{report.precision:.0%}")
    col2.metric("Recall", f"{report.recall:.0%}")
    col3.metric("Brier Score", f"{report.brier_score:.3f}")
    col4.metric("p50 Latency", f"{report.latency_p50 / 1000:.1f}s")
    col5.metric("p95 Latency", f"{report.latency_p95 / 1000:.1f}s")

    st.subheader("Confusion Matrix")
    labels = ["PASS", "FLAG", "NEEDS_REVIEW"]
    cm = report.confusion_matrix
    matrix_data = {f"Predicted {p}": {f"Actual {a}": cm.get(a, {}).get(p, 0) for a in labels} for p in labels}
    st.dataframe(matrix_data)

    st.subheader("Per-Scenario Results")
    for r in report.scenarios:
        icon = "✅" if r.correct else "❌"
        with st.expander(f"{icon} {r.scenario_id} — Expected: {r.expected_decision}, Got: {r.actual_decision}"):
            col1, col2, col3 = st.columns(3)
            col1.metric("Correct", str(r.correct))
            col2.metric("Confidence", f"{r.confidence:.0%}")
            col3.metric("Latency", f"{r.latency_ms / 1000:.1f}s")
            st.markdown(f"**Confidence in range:** {r.confidence_in_range}")
            st.markdown(f"**Citation sources match:** {r.citation_sources_match}")
            st.markdown(f"**Reasoning topics match:** {r.reasoning_topics_match}")
