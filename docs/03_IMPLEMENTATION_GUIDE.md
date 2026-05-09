# 03 Implementation Guide

> Step-by-step build runbook. Follow hour by hour. Each hour ends with a working state and a commit.

## Pre-flight checklist (before hour 1)

- [ ] Anthropic API key obtained from https://console.anthropic.com
- [ ] Spending limit set on Anthropic account: $20 USD
- [ ] Python 3.11 installed locally
- [ ] Git installed locally
- [ ] GitHub account ready
- [ ] Streamlit Cloud account created (free, sign in with GitHub)
- [ ] Decided on a project name (suggested: `certificate-sentinel` or `cert-validator-prototype`; do not include "Vertex" in the name)

---

## Hour 1: Repo setup

**Goal:** A clean Python project skeleton, version controlled, with environment management.

**Tasks:**

1. Create a private GitHub repo with the chosen name. Do not initialize with README or .gitignore (we'll add our own).
2. Clone locally:
   ```
   git clone git@github.com:<user>/<repo>.git
   cd <repo>
   ```
3. Copy the contents of this build package's `templates/` folder to the repo root:
   - `.gitignore`
   - `.env.example` (rename to `.env.example`)
   - `requirements.txt`
4. Create a `.env` file (NOT committed) with your real `ANTHROPIC_API_KEY` and a chosen `APP_PASSWORD`.
5. Create a Python virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate    # macOS/Linux
   # .venv\Scripts\activate     # Windows
   ```
6. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
7. Create the project structure (empty `__init__.py` files where directories exist):
   ```
   src/{agent,data,eval,ui,utils}/__init__.py
   data/certificates/.gitkeep
   eval_scenarios/.gitkeep
   tests/.gitkeep
   logs/.gitkeep
   ```
8. Create `streamlit_app.py` with a placeholder "Hello Certificate Sentinel" page that confirms environment is wired.
9. Test: `streamlit run streamlit_app.py` should open a browser with the placeholder.
10. Copy this entire build package's `docs/` folder into the repo at `docs/` so reviewers can find it.
11. Write a brief `README.md` in the repo root (separate from this build package's README; should describe the project for reviewers).
12. Commit: `[hour-1] initial repo setup`

**Done when:**
- `streamlit run streamlit_app.py` opens a working page
- `python -c "import anthropic; print('ok')"` works
- The repo has a clean structure committed
- `.env` is NOT in the repo

---

## Hour 2: Mock data

**Goal:** Customer profiles, transactions, and state rules as JSON files. All schemas defined in `docs/05_DATA_SPECIFICATIONS.md`.

**Tasks:**

1. In `data/customers.json`, create 10 customer profiles per the schema. Use diverse industries:
   - 2 office supply retailers (one for resale, one with edge cases)
   - 1 software consulting firm (services, used for FLAG scenario)
   - 1 farm equipment dealer (agricultural)
   - 1 industrial manufacturer (manufacturing)
   - 1 restaurant chain (used for FLAG scenario)
   - 2 wholesale distributors
   - 1 new customer (no transactions yet, used for NEEDS_REVIEW scenario)
   - 1 mixed-use retailer (used for ambiguous scenario)

2. In `data/transactions.json`, create transaction histories for 9 of the 10 customers (the new customer has zero transactions). Aim for 30-50 transactions each. Vary product categories, dates within last 90 days, amounts.

3. In `data/rules.json`, create approximately 20 state exemption rules covering Texas resale, manufacturing, and agricultural exemptions. Reference real Texas Tax Code citations where reasonable (the rules don't need to be perfectly accurate; they need to be self-consistent).

4. In `src/data/store.py`, write a module that:
   - Loads all three JSON files at import time into module-level dicts
   - Exposes lookup functions: `get_customer(id)`, `get_transactions(customer_id, limit)`, `get_rules(state, exemption_type)`
   - Returns Pydantic models, not raw dicts, so type safety propagates

5. Write `tests/test_data.py`: load each file, assert schema validity, assert minimum record counts.

6. Commit: `[hour-2] mock customer, transaction, and rules data`

**Done when:**
- All three JSON files validate
- `src/data/store.py` loads and exposes typed accessors
- `pytest tests/test_data.py` passes

---

## Hour 3: Synthetic certificate PDFs

**Goal:** 10 synthetic certificate PDFs, one per scenario.

**Tasks:**

1. Create `scripts/generate_certificates.py` that uses `reportlab` to render PDFs.

2. For each of the 10 scenarios in `docs/06_TEST_SCENARIOS.md`, generate a PDF that visually resembles a Texas exemption certificate. Include:
   - Form title (e.g., "Texas Sales and Use Tax Resale Certificate")
   - Buyer name and address (matching customer profile)
   - Buyer taxpayer ID
   - Seller name (use a generic placeholder seller)
   - Description of property to be purchased
   - Reason for exemption (the type)
   - Date
   - Signature (or omit for the field-issue scenario)

3. Save PDFs to `data/certificates/C_001_*.pdf` through `C_010_*.pdf`.

4. Add `data/certificates/*.pdf` to `.gitignore` (we don't commit binaries; the generator script reproduces them).

5. Commit: `[hour-3] synthetic certificate PDF generator and outputs`

**Done when:**
- 10 PDFs exist in `data/certificates/`
- Running `python scripts/generate_certificates.py` regenerates them deterministically
- Each PDF visually looks like an exemption certificate (it doesn't need to be beautiful, just plausible)

**Note on time:** If hour 3 stretches past 90 minutes, simplify. The PDFs need to be parseable by Claude's PDF input, not photo-realistic.

---

## Hour 4: Tool implementations

**Goal:** The three tool functions the agent will call, plus their schemas.

**Tasks:**

1. In `src/agent/tools.py`, implement three Python functions:
   - `get_customer_transactions(customer_id: str, limit: int = 30) -> dict`
   - `get_state_exemption_rules(state: str, exemption_type: str) -> dict`
   - `record_decision(decision: str, confidence: float, reasoning_summary: str, citations: list) -> dict`

   Each function pulls from `src/data/store.py` and returns a JSON-serializable dict.

2. Define the tool schemas (matching `prompts/tool_schemas.json` from this build package). Load the JSON at module import.

3. Build a `TOOL_REGISTRY` dict mapping tool name to (function, schema) for the orchestrator to use.

4. Write `tests/test_tools.py`: exercise each tool with valid input, assert return shape.

5. Commit: `[hour-4] tool implementations and registry`

**Done when:**
- All three tools return data correctly
- `pytest tests/test_tools.py` passes
- The tool schemas match `prompts/tool_schemas.json` exactly

---

## Hour 5: Agent orchestrator

**Goal:** The agent loop that takes a certificate PDF and customer ID, runs Claude with tool use, and returns a structured decision.

**Tasks:**

1. In `src/agent/prompts.py`, paste the system prompt from `prompts/system_prompt.md`.

2. In `src/agent/orchestrator.py`, implement `validate_certificate(pdf_bytes: bytes, customer_id: str) -> Decision`:
   - Build the initial user message with the PDF as a `document` content block (see `docs/04_API_REFERENCE.md` for the exact format)
   - Initialize the Anthropic client (read API key from env)
   - Loop:
     - Call `client.messages.create` with system, tools, messages, model `claude-sonnet-4-6`, max_tokens 4000
     - If `stop_reason == "tool_use"`: extract tool calls, dispatch through `TOOL_REGISTRY`, append results, continue
     - If `stop_reason == "end_turn"`: parse the final `record_decision` tool call (the agent should always end by calling this), return the structured `Decision`
     - Hard cap: if loop reaches 10 iterations without termination, return `Decision(decision="NEEDS_REVIEW", confidence=0.0, reasoning_summary="Agent loop exceeded budget", citations=[])`
   - Use exponential backoff on transient API errors (`anthropic.APIStatusError` with 5xx, `anthropic.APIConnectionError`)

3. Define `Decision` as a Pydantic model in `src/agent/orchestrator.py` matching the schema in the PRD.

4. In `src/agent/verifier.py`, implement `verify_decision(decision: Decision) -> Decision`:
   - For each citation where `source == "state_rule"`, look up `reference_id` in `src/data/store.py` rules
   - If any cited rule_id is not found, downgrade decision to NEEDS_REVIEW, set confidence to 0.3, append a note to `reasoning_summary`: "[Verifier override: cited rule X not found in rules table]"
   - Return the (possibly modified) Decision

5. Write `tests/test_agent.py`:
   - End-to-end test on scenario C_001 (PASS case): assert decision is PASS, confidence > 0.5
   - End-to-end test on scenario C_002 (FLAG case): assert decision is FLAG
   - Verifier test: hand-craft a Decision with a fake rule_id, assert verifier downgrades to NEEDS_REVIEW

6. Commit: `[hour-5] agent orchestrator and post-decision verifier`

**Done when:**
- Validation runs end-to-end on at least 3 scenarios
- Verifier catches hand-crafted hallucinated rule_ids
- All tests pass

**This is the failure-prone hour.** If the agent isn't producing structured output reliably, iterate on the system prompt before adding more scenarios. Don't move forward until the loop is solid on 3 scenarios.

---

## Hour 6: Streamlit UI

**Goal:** A working Streamlit page for the validation flow.

**Tasks:**

1. In `src/utils/auth.py`, implement a password gate using `st.text_input(type="password")` compared against `APP_PASSWORD` env var.

2. In `src/ui/components.py`, build reusable components:
   - `decision_banner(decision)`: renders green/yellow/red banner per decision type
   - `confidence_meter(confidence)`: visual confidence display
   - `citation_list(citations)`: expandable per-source breakdown
   - `synthetic_data_banner()`: top-of-page banner

3. In `src/ui/pages.py`, build the validation page:
   - Synthetic data banner
   - Scenario picker (dropdown of 10 scenarios with short descriptions)
   - Run button
   - Progress indicator while agent runs
   - Result display: decision banner, confidence, reasoning, citations
   - Override controls: accept or override with reason code dropdown
   - "View raw agent trace" expander

4. Wire the page into `streamlit_app.py`:
   - Password gate first
   - Then page navigation (validation page, eval page placeholder)

5. Smoke test by running each scenario in the UI.

6. Commit: `[hour-6] streamlit ui for validation flow`

**Done when:**
- Streamlit app loads with password gate
- All 10 scenarios are pickable
- Running a scenario shows a result with banner, confidence, reasoning, citations
- Override capture works (saves to log)

---

## Hour 7: Run logging and trace expander

**Goal:** Every run is logged. Reviewers can inspect the full agent trace.

**Tasks:**

1. In `src/utils/logging.py`:
   - Configure Python `logging` module
   - Implement `log_run(run_id, scenario_id, input_summary, decision, raw_messages, latency_ms)` that appends one JSON line to `logs/runs.jsonl`
   - Make sure logs directory exists; create if not

2. Wire `log_run` into `validate_certificate` in `src/agent/orchestrator.py`. Log every run regardless of outcome.

3. In the UI's "View raw agent trace" expander, display the full message history (user, assistant, tool calls, tool results) in a readable format. JSON-pretty-print is fine.

4. Capture overrides: when the user overrides a decision, log a separate event to `logs/overrides.jsonl` with the run_id, original decision, override decision, reason code.

5. Commit: `[hour-7] run logging and trace inspection`

**Done when:**
- Every run produces a line in `logs/runs.jsonl`
- The UI's trace expander shows the full agent conversation
- Overrides are captured to `logs/overrides.jsonl`

---

## Hour 8: Eval harness

**Goal:** A page (and a script) that runs all 10 scenarios and computes precision, recall, calibration.

**Tasks:**

1. In `eval_scenarios/scenarios.json`, define the 10 scenarios per the schema in `docs/06_TEST_SCENARIOS.md`. Include `expected_decision`, `expected_confidence_range`, `expected_citation_sources`, `expected_reasoning_topics`.

2. In `src/eval/runner.py`, implement `run_eval() -> EvalReport`:
   - Load all scenarios
   - For each: load the cert PDF, call `validate_certificate`, capture result and timing
   - Compare actual vs expected
   - Return an `EvalReport` Pydantic model with per-scenario results and aggregate metrics

3. In `src/eval/metrics.py`, implement:
   - `compute_precision(results)`: of predicted FLAGs, how many are truly FLAG
   - `compute_recall(results)`: of true FLAGs, how many were predicted FLAG
   - `compute_brier_score(results)`: calibration metric using confidence as predicted probability of correctness
   - `compute_confusion_matrix(results)`: 3x3 matrix
   - `compute_latency_distribution(results)`: p50, p95, p99

4. In `src/ui/pages.py`, add an eval page:
   - Headline metrics (precision, recall, Brier, p50/p95 latency)
   - Confusion matrix
   - Per-scenario table with drill-down expanders
   - "Run full eval" button (warning: takes about 5 minutes and costs ~$0.50 in API)

5. Write `tests/test_eval.py`: assert metric computations are correct on a hand-crafted small results set.

6. Commit: `[hour-8] eval harness with metrics and ui page`

**Done when:**
- Eval runs all 10 scenarios end-to-end
- Metrics are computed correctly (verified by hand on the small results set)
- Eval page in UI shows headline metrics + per-scenario detail
- The eval results are deterministic enough to inspect: same scenarios, same agent should produce similar outcomes (model temperature can introduce some variance)

---

## Hour 9: Deployment

**Goal:** Live on Streamlit Cloud, password-gated, smoke-tested.

**Tasks:**

1. Push all changes to GitHub `main`.
2. In Streamlit Cloud, "New app" -> select repo -> select `streamlit_app.py` as entry point -> deploy.
3. In Streamlit Cloud "Settings -> Secrets", add:
   - `ANTHROPIC_API_KEY = "..."`
   - `APP_PASSWORD = "..."`
4. Wait for deployment. First load may take 60-90 seconds.
5. Smoke test in browser: enter password, run scenario C_001, confirm result renders.
6. Set up basic monitoring: bookmark the Streamlit Cloud logs page for the app.
7. Pre-warm: hit the URL once before any interview to wake the app from sleep.
8. Update the repo README with the live URL (in a "Demo (password-protected)" section).
9. Commit and push: `[hour-9] deployment configuration`

**Done when:**
- The app is live at a `streamlit.app` URL
- Password gate works
- At least one scenario runs successfully end-to-end on the deployed version
- Anthropic spending limit confirmed at $20

**If deployment fails:** common causes are missing secrets (check spelling), missing requirements (check `requirements.txt`), or import errors that didn't surface locally. Streamlit Cloud logs are accessible from the management UI.

---

## Hour 10: Documentation and walkthrough

**Goal:** README that a reviewer can read in 5 minutes, plus a recorded walkthrough.

**Tasks:**

1. Update the repo README to include:
   - Project overview (3 sentences)
   - Live demo URL (password-protected)
   - Architecture diagram (mermaid, embedded in README)
   - "How to read this repo" section pointing to the docs/
   - "What this is not" section listing the explicit non-goals
   - Build budget note (built in 10 hours)

2. Generate the architecture diagram. Either embed mermaid directly in README (GitHub renders it), or use a tool like Excalidraw and embed an image.

3. Final code cleanup: remove debug prints, run `ruff check` or similar, ensure type hints are present.

4. Record a Loom video (5-7 minutes):
   - Minute 1: Problem statement (one-third of audit penalties from bad certs)
   - Minute 2: Architecture (walk through the mermaid diagram)
   - Minute 3-4: Live demo of one PASS and one FLAG scenario
   - Minute 5: The eval page and what the metrics tell us
   - Minute 6: Honest list of what's NOT in the prototype and why
   - Minute 7: Closing thought on how this maps to Vertex's stated AI direction

5. Final commit: `[hour-10] documentation and walkthrough recording`

**Done when:**
- A reviewer landing on the GitHub repo can understand the project in 5 minutes
- The Loom video is recorded and the URL is in the README (or sent in followup email)
- The repo is in a state you'd be comfortable showing a Principal at any AI company

---

## Recovery protocols

**If you slip behind schedule:**
- **Slip in hour 3 (PDFs):** simplify to 5 scenarios instead of 10
- **Slip in hour 5 (agent):** the orchestrator must work; cut scenario count before cutting orchestrator quality
- **Slip in hour 8 (eval):** smaller golden set (5 scenarios) is acceptable; the harness pattern matters more than the count
- **Slip in hour 9 (deployment):** if Streamlit Cloud fails, fall back to a Loom demo of the local app and document the deployment plan in README

**If something breaks at the end:**
- Better to ship a working app with 5 scenarios than a broken app with 10
- Better to commit honest "this is what works, this is what didn't" notes in the README than to hide failures

**Hard rule:** never ship a demo with `# TODO` comments visible in the code reviewers see. Either finish or remove.
