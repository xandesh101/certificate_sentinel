"""Streamlit page implementations."""

import json
import time
import uuid
from pathlib import Path

import fitz  # pymupdf
import streamlit as st
import streamlit.components.v1 as components

from src.ui.components import (
    citation_list,
    confidence_meter,
    decision_banner,
    synthetic_data_banner,
)

_CERT_DIR = Path(__file__).parent.parent.parent / "data" / "certificates"
_SCENARIOS_FILE = Path(__file__).parent.parent.parent / "eval_scenarios" / "scenarios.json"
_BASE = Path(__file__).parent.parent.parent


def _load_scenarios() -> list[dict]:
    with open(_SCENARIOS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)["scenarios"]


def _load_cert(pdf_path: str) -> bytes:
    full = _BASE / pdf_path
    if not full.exists():
        raise FileNotFoundError(f"Certificate PDF not found: {full}")
    return full.read_bytes()


def _embed_pdf(pdf_bytes: bytes) -> None:
    """Render the first page of a PDF as an image (avoids Chrome data-URI iframe block)."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[0]
    pix = page.get_pixmap(matrix=fitz.Matrix(1.8, 1.8))
    st.image(pix.tobytes("png"), use_container_width=True)


def overview_page() -> None:
    """Product overview for hiring manager review."""
    st.title("Certificate Sentinel")
    st.caption("An agentic AI prototype for semantic validation of sales tax exemption certificates.")

    st.divider()

    # What it is
    st.subheader("What this is")
    st.markdown("""
Most certificate validation today works at the **field level**: it checks whether required fields are present and correctly formatted.

**Certificate Sentinel adds semantic validation**: an AI agent that asks a tougher question.
*Does this exemption claim actually make sense, given who this customer is and what they actually buy?*

A restaurant chain can submit a perfectly formatted resale certificate. Field validation passes it.
But their transaction history shows food consumed on-premises, not resold.
That's the mismatch this system catches.
""")

    st.divider()

    # How it works - 3 columns
    st.subheader("How it works")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("#### 1. Read the certificate")
        st.markdown("""
The agent receives the exemption certificate as a PDF. Claude reads it natively, with no OCR pipeline needed. It extracts the claimed exemption type, buyer identity, and stated reason.
""")
    with col2:
        st.markdown("#### 2. Pull context")
        st.markdown("""
The agent calls two tools:
- **Transaction history**: what has this customer actually been buying for the past 90 days?
- **State rules**: what does Texas law actually require for this exemption type?
""")
    with col3:
        st.markdown("#### 3. Decide + cite**")
        st.markdown("""
The agent produces a structured decision (**PASS**, **FLAG**, or **NEEDS_REVIEW**)
with a confidence score, plain-language reasoning, and citations to specific
transaction IDs and rule IDs. A human reviewer sees everything and can override.
""")

    st.divider()

    # How the agent works
    st.subheader("How the agent works")
    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown("""
The agent runs on **Claude's native tool use**, with no LangChain and no framework.
The loop is explicit and fully inspectable:

1. Claude receives the PDF + customer ID
2. Claude decides which tools to call and in what order
3. Tool results are appended to the conversation and Claude reasons further
4. Claude calls `record_decision` as its terminal action, which ends the loop
5. A **post-decision verifier** checks every cited rule ID against the actual rules table.
   If Claude hallucinated a rule, the decision is automatically downgraded to `NEEDS_REVIEW`.

The hard cap is **10 tool-use iterations**. If the loop exceeds this, the system returns
`NEEDS_REVIEW` with confidence 0.0 rather than guessing.
""")
    with col2:
        components.html("""
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<script>mermaid.initialize({startOnLoad:true, theme:'dark'});</script>
<div class="mermaid">
sequenceDiagram
    participant U as UI
    participant A as Agent
    participant C as Claude API
    participant T as Tools
    participant V as Verifier

    U->>A: PDF + customer_id
    A->>C: messages + tools
    C->>T: get_transactions
    T-->>C: transaction list
    C->>T: get_rules
    T-->>C: rule set
    C->>T: record_decision
    T-->>A: Decision
    A->>V: validate citations
    V-->>U: Final Decision
</div>
""", height=340)

    st.divider()

    # Claude API integration
    st.subheader("How Claude API is integrated")
    st.markdown("""
| What | How |
|---|---|
| **Model** | `claude-sonnet-4-6`: strong reasoning + tool use, ~$0.05 per validation |
| **PDF input** | Certificate sent as a `document` content block (base64-encoded); Claude reads it natively |
| **Tool use** | 3 tools defined as JSON schemas; Claude decides when and how to call them |
| **Retry logic** | Exponential backoff on 5xx errors and connection failures; rate limit errors sleep 30s |
| **Token budget** | `max_tokens=4000` per call; hard loop cap of 10 iterations |
| **No streaming** | Decisions are structured JSON, not chat. Streaming adds complexity with no user benefit here. |
| **Verifier** | Post-call check: cited `rule_id` values are looked up in the rules table; hallucinations caught before the result reaches the reviewer |
""")

    st.divider()

    # What this proves
    st.subheader("What this proves, and why it matters for Vertex")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**For the product**")
        st.success(
            "Semantic validation catches mismatches that field validation misses. "
            "A restaurant claiming resale, a software firm claiming manufacturing: "
            "these pass field checks today. This agent flags them with cited evidence, "
            "reducing audit risk and compliance penalties for Vertex customers.",
        )
        st.markdown("**For the AI design**")
        st.success(
            "Human-in-the-loop is non-negotiable for tax compliance. Every decision "
            "shows its reasoning and citations. Reviewers can override with a reason code. "
            "The verifier ensures the agent can't quietly hallucinate a rule and have it "
            "accepted. Confidence scores tell reviewers where to focus attention."
        )
    with col2:
        st.markdown("**For the eval discipline**")
        st.success(
            "10 golden scenarios with expected decisions, confidence ranges, citation sources, "
            "and reasoning topics. Precision and recall measured on FLAG decisions, the "
            "highest-stakes outcome. Brier score measures calibration. "
            "This is how you ship AI responsibly: measure before you ship, not after."
        )
        st.markdown("**For Vertex specifically**")
        st.success(
            "Vertex already has the certificate data and the customer transaction data. "
            "The integration surface is narrow: a validation API that sits alongside "
            "Certificate Center and returns a structured decision with evidence. "
            "No new data collection. No model training. Deployable on existing infrastructure."
        )

    st.divider()
    st.caption("Python 3.11 · Anthropic claude-sonnet-4-6 · Streamlit · Synthetic data only")


def validation_page() -> None:
    """Main certificate validation page."""
    synthetic_data_banner()
    st.title("Certificate Sentinel")
    st.caption("Agentic semantic validation of sales tax exemption certificates")

    scenarios = _load_scenarios()
    scenario_options = {s["scenario_id"]: f"{s['scenario_id']}: {s['description']}" for s in scenarios}
    scenario_ids = list(scenario_options.keys())

    selected_id = st.selectbox(
        "Select a scenario",
        options=scenario_ids,
        format_func=lambda x: scenario_options[x],
    )

    selected = next(s for s in scenarios if s["scenario_id"] == selected_id)

    with st.expander("Scenario details & certificate preview", expanded=False):
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown(f"**Scenario ID:** `{selected['scenario_id']}`")
            st.markdown(f"**Customer:** `{selected['customer_id']}`")
            st.markdown(f"**Claimed exemption:** `{selected['claimed_exemption_type']}`")
            st.markdown(f"**Expected decision:** `{selected['expected_decision']}`")
            conf = selected["expected_confidence_range"]
            st.markdown(f"**Expected confidence range:** `{conf[0]} – {conf[1]}`")
            st.markdown(f"**Expected citations:** `{', '.join(selected['expected_citation_sources'])}`")
            st.markdown("**Rationale:**")
            st.info(selected["rationale"])
        with col2:
            st.markdown("**Certificate PDF:**")
            try:
                pdf_bytes_preview = _load_cert(selected["certificate_pdf"])
                _embed_pdf(pdf_bytes_preview)
            except FileNotFoundError:
                st.warning("PDF not yet generated.")

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


def scenarios_page() -> None:
    """Scenario browser: all 10 test cases with PDFs for hiring team review."""
    synthetic_data_banner()
    st.title("Scenario Browser")
    st.caption("All 10 evaluation scenarios with certificates and expected outcomes.")

    scenarios = _load_scenarios()

    decision_colors = {"PASS": "🟢", "FLAG": "🔴", "NEEDS_REVIEW": "🟡"}

    for s in scenarios:
        icon = decision_colors.get(s["expected_decision"], "⚪")
        header = f"{icon} {s['scenario_id']}: {s['description']}"
        with st.expander(header):
            col1, col2 = st.columns([1, 1])
            with col1:
                st.markdown(f"**Customer:** `{s['customer_id']}`")
                st.markdown(f"**Exemption type claimed:** `{s['claimed_exemption_type']}`")
                st.markdown(f"**Expected decision:** `{s['expected_decision']}`")
                conf = s["expected_confidence_range"]
                st.markdown(f"**Expected confidence:** `{conf[0]} – {conf[1]}`")
                st.markdown(f"**Expected citation sources:** `{', '.join(s['expected_citation_sources'])}`")
                st.markdown(f"**Expected reasoning topics:** `{', '.join(s['expected_reasoning_topics'])}`")
                st.markdown("**Why this outcome:**")
                st.info(s["rationale"])

                pdf_path = _BASE / s["certificate_pdf"]
                if pdf_path.exists():
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            label="Download Certificate PDF",
                            data=f.read(),
                            file_name=pdf_path.name,
                            mime="application/pdf",
                            key=f"dl_{s['scenario_id']}",
                        )
            with col2:
                st.markdown("**Certificate PDF:**")
                try:
                    pdf_bytes = _load_cert(s["certificate_pdf"])
                    _embed_pdf(pdf_bytes)
                except FileNotFoundError:
                    st.warning("PDF not generated yet.")


def architecture_page() -> None:
    """System design diagram page."""
    st.title("System Architecture")
    st.caption("How Certificate Sentinel works, for engineering and product review.")

    st.markdown("""
This prototype adds a **semantic validation layer** on top of Vertex's existing field-level certificate validation.
The agent reasons across three evidence sources before producing a structured decision.
""")

    components.html("""
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<script>mermaid.initialize({startOnLoad:true, theme:'dark'});</script>
<div class="mermaid" style="font-size:14px;">
flowchart TD
    A["📄 Certificate PDF\n(user selects scenario)"] --> B

    subgraph Agent["🤖 Agent Orchestrator (orchestrator.py)"]
        B["Build initial message\n(PDF as document block)"]
        B --> C["Claude claude-sonnet-4-6\ntool_use loop"]
        C -->|"tool_use"| D{"Dispatch tool"}
        D -->|"get_customer_transactions"| E["Transaction lookup\n(store.py)"]
        D -->|"get_state_exemption_rules"| F["Rules lookup\n(store.py)"]
        E --> G["Append tool_result\nto messages"]
        F --> G
        G --> C
        D -->|"record_decision\n(terminal)"| H["Extract Decision\nPASS / FLAG / NEEDS_REVIEW"]
        C -->|"Hard cap: 10 iterations"| H
    end

    subgraph Data["📦 Mock Data (JSON)"]
        E2["customers.json\n10 customer profiles"]
        F2["transactions.json\n200+ transactions"]
        R2["rules.json\n20 Texas exemption rules"]
    end

    E -.-> E2
    E -.-> F2
    F -.-> R2

    H --> I["🔍 Post-Decision Verifier\n(verifier.py)\nValidates cited rule_ids exist"]
    I -->|"Hallucinated rule_id detected"| J["Downgrade to NEEDS_REVIEW\nconfidence = 0.3"]
    I -->|"All citations valid"| K["Final Decision"]
    J --> K

    K --> L["📝 Run Logger\n(logs/runs.jsonl)"]
    K --> M["🖥️ Streamlit UI\nDecision banner + citations"]
    M --> N["👤 Human Reviewer\nAccept or Override"]
    N --> O["📝 Override Logger\n(logs/overrides.jsonl)"]
</div>
""", height=700)

    st.divider()

    st.subheader("Key Design Decisions")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Why native tool use, not LangChain?**")
        st.info(
            "The agent loop is explicit and inspectable. Every tool call, result, and reasoning step "
            "is visible in the 'raw agent trace' expander. LangChain abstracts this away, making it "
            "harder to debug failures or explain the agent's reasoning to a tax team."
        )
        st.markdown("**Why a post-decision verifier?**")
        st.info(
            "Claude can hallucinate rule IDs. The verifier checks every cited state_rule reference "
            "against the actual rules table. If a rule doesn't exist, the decision is downgraded to "
            "NEEDS_REVIEW. This is the defense-in-depth pattern that makes AI decisions auditable."
        )
        st.markdown("**Why NEEDS_REVIEW as a third decision state?**")
        st.info(
            "Binary PASS/FLAG forces the agent to guess on ambiguous cases, overstating confidence. "
            "NEEDS_REVIEW lets the agent be honest about uncertainty (new customer, mixed transactions) "
            "and routes these to a human rather than making a potentially wrong automated call."
        )
    with col2:
        st.markdown("**Why mock JSON data instead of a real database?**")
        st.info(
            "This is a 10-hour prototype. A real database adds infrastructure complexity without "
            "changing what the agent can demonstrate. The JSON store is typed (Pydantic), "
            "schema-validated, and swappable for a real DB in production."
        )
        st.markdown("**Why no streaming?**")
        st.info(
            "Streaming is a UX optimization for chat interfaces. This produces a structured "
            "JSON decision, not flowing text. The latency (~15s) is acceptable for a compliance "
            "review workflow. Adding streaming would complicate logging without user benefit."
        )
        st.markdown("**Eval harness design**")
        st.info(
            "10 golden scenarios with expected decision, confidence range, citation sources, and "
            "reasoning topics. Precision and recall measured on FLAG decisions specifically, "
            "the highest-stakes outcome. Brier score measures calibration: does confidence "
            "correlate with correctness?"
        )

    st.divider()
    st.subheader("What this is NOT (by design)")
    st.markdown("""
| Not built | Why not |
|---|---|
| Real OCR | Claude reads PDFs natively. No OCR pipeline needed for this demo. |
| Real Vertex API calls | Out of scope for a prototype. The mock data proves the reasoning pattern. |
| Multi-state rules | Texas only. Adding states is a data problem, not an architecture problem. |
| Streaming responses | Not a chat interface. Structured decisions don't benefit from streaming. |
| Production observability | Local JSONL logs only. Grafana/Datadog would be next iteration. |
| User authentication | Single password gate. Real product would use SSO/RBAC. |
""")


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
        with st.expander(f"{icon} {r.scenario_id} | Expected: {r.expected_decision}, Got: {r.actual_decision}"):
            col1, col2, col3 = st.columns(3)
            col1.metric("Correct", str(r.correct))
            col2.metric("Confidence", f"{r.confidence:.0%}")
            col3.metric("Latency", f"{r.latency_ms / 1000:.1f}s")
            st.markdown(f"**Confidence in range:** {r.confidence_in_range}")
            st.markdown(f"**Citation sources match:** {r.citation_sources_match}")
            st.markdown(f"**Reasoning topics match:** {r.reasoning_topics_match}")
