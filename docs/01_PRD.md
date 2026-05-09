# PRD: Certificate Sentinel
## Semantic Exemption Certificate Validation Agent

**Author:** Sandesh KC
**Date:** May 2026
**Status:** Prototype scoping (not a Vertex deliverable; built for Principal PM interview at Vertex Inc)
**Hypothetical reviewers:** VP Product, AI Engineering Lead, Tax Content Director, Customer Success

---

## 1. Problem statement

Vertex Certificate Center provides storage, lifecycle management, customer self-service intake, and field-level validation for sales tax exemption certificates. Vertex Copilot is integrated for in-workflow Q&A.

What is not yet covered at agent-grade depth is **semantic validation**: whether a certificate that passes field-level checks (signature present, date valid, state code correct) actually holds up against the customer's transaction profile and the claimed exemption's state-specific rules.

When a certificate passes field validation but fails semantic validation, the gap surfaces during a state audit, two to four years after the transaction. By that time, the customer owes back taxes, penalties, and interest, and the remediation window is narrow or closed. Industry data suggests poor exemption certificate management contributes to roughly one-third of U.S. sales tax audit penalties.

This is exactly the kind of capability where Vertex's stated direction (moving from AI that assists to AI that safely executes critical compliance work) earns its keep.

---

## 2. Customer and use case

**Primary user:** Senior Indirect Tax Analyst or Tax Manager at a Vertex enterprise customer. Manages thousands of exemption certificates in Certificate Center. Owns the customer's audit defense outcome.

**Today's workflow:**
1. Customer submits an exemption certificate through the self-service portal
2. Certificate Center performs field validation; the analyst accepts or rejects on completeness
3. The substantive validity question (does this exemption actually apply to what this customer buys from us, in this state?) is rarely reviewed deeply at intake because volume is too high
4. The gap is discovered at audit, when the cost is highest

**What the user wants:** Confidence that every certificate on file would survive an audit, without manually deep-reviewing each one at intake.

**Secondary user:** Vertex tax content team, who curates the state rules and is downstream of customer-reported issues.

---

## 3. Hypothesis

An agentic system that reasons across `(parsed certificate, transaction sample for that customer, state exemption rules table)` can flag semantic mismatches with measurable precision and recall, while producing an audit-grade reasoning trace that a tax professional can review, accept, override, or escalate.

This hypothesis is testable, narrow, and falsifiable. If the agent cannot beat field-level validation on the eval set with reasonable precision, the bet does not work.

---

## 4. Success criteria

Prototype-stage targets. Production targets would be substantially higher.

### Quality
| Metric | Target | Why |
| --- | --- | --- |
| Precision on flagged mismatches | ≥ 80% on 25-scenario golden set | False positives erode trust faster than false negatives in a HITL system |
| Recall on known mismatches | ≥ 70% | Misses are the failure mode this product exists to prevent |
| Calibration (Brier score on confidence vs correctness) | < 0.25 | A confidence score we cannot trust is worse than no score |

### Trust and explainability
- Every flag includes the cited certificate field, the cited transaction(s), and the cited state rule(s)
- Reasoning trace is human-readable in the language of tax compliance, not LLM jargon
- Tax professional can override in one click; the override is captured as a labeled training signal

### Operational
- p50 latency per certificate: under 30 seconds
- p95 latency: under 90 seconds
- LLM cost per review: under $0.10

These targets are deliberately set at "prototype demonstrably works"; not "production ready."

---

## 5. Scope

### In scope
- One state: Texas (well-documented exemption rules, high transaction volume)
- Three exemption types: resale, manufacturing, agricultural
- Mock transaction data (10 customers, approximately 50 transactions each)
- Mock state rules table (curated subset, approximately 20 rules)
- Synthetic certificate PDFs: 10 valid, 10 semantically mismatched, 5 with field issues
- Structured reasoning trace output (JSON + human summary)
- HITL routing: every flag goes to a review queue, no auto-actions
- Eval harness with precision, recall, calibration metrics

### Out of scope
- Production OCR (use Claude's native PDF reading)
- Real Vertex API or Cert Center integration (mocked)
- Multi-state rule reasoning
- Production observability stack (local logs only)
- Custom model training or fine-tuning
- UI polish (Streamlit is enough)

---

## 6. Non-goals (deliberately rejected)

1. **We are not replacing the tax professional.** Every decision is HITL. The agent flags and explains; the human decides.
2. **We are not solving field validation.** Vertex Certificate Center already does this.
3. **We are not building a chat interface.** Vertex Copilot already does Q&A. This is autonomous validation, not assistance.
4. **We are not optimizing for state-of-the-art accuracy.** We are demonstrating that the architecture pattern is sound and the evaluation strategy is rigorous.

---

## 7. AI-specific requirements

This section is the heart of the PRD. The JD requirements (data strategy, learning signals, feedback loops, evaluation, HITL, responsible AI) all map here.

### Data strategy
- **Input data:** parsed certificate, customer transaction sample, claimed exemption type
- **Reference data:** curated state rules table (in production, owned by Vertex tax content team)
- **Learning signal:** every HITL override produces a labeled example: `(input, agent decision, human decision, reason code)`
- **Feedback loop:** weekly review of overrides; recurring patterns become new eval scenarios or new rules in the reference table
- **Data lifecycle:** retention policy assumed; not implemented in prototype

### Evaluation strategy
- **Pre-deployment golden set:** 25 hand-labeled scenarios across valid, field-invalid, semantically mismatched, and edge cases
- **Gating:** precision ≥ 80%, recall ≥ 70%, calibration Brier < 0.25 to release
- **Production evaluation (hypothetical):** continuous sampling of HITL overrides; drift detection on confidence distributions; weekly precision/recall report on override-derived ground truth
- **LLM-as-judge layer:** for reasoning trace quality, a separate evaluator checks whether cited rules and transactions actually exist and are relevant

### HITL controls
- 100% of flags route to a human review queue (no auto-rejections)
- Confidence-based prioritization: low-confidence flags surface first for human attention
- Override is captured with a structured reason code (rule misinterpreted, transaction sample not representative, customer industry mislabeled, etc.)
- Disagreement between agent and human is logged for eval-set expansion and prompt or model iteration

### Responsible AI principles
| Principle | How it is implemented |
| --- | --- |
| Traceability | Every flag cites field, transaction, and rule; full request and response logged |
| Auditability | Reproducible given identical inputs; logs persisted |
| Bias awareness | Eval set spans customer industry, certificate type, exemption category; we monitor for systematic blind spots |
| Transparency | Reasoning is in tax language, not model jargon; confidence is exposed |
| Human oversight | No autonomous action on customer data without human approval |

### Drift and monitoring (production-hypothetical)
- Rolling 30-day precision and recall on override-derived labels
- Alert on confidence distribution shift (model or prompt drift signal)
- Alert on HITL override rate change (regression signal)

---

## 8. Risks and mitigations

### Risk 1: The agent hallucinates rules
The agent could cite a state rule that does not exist.

*Mitigation:* All cited rules must come from the curated rules table via tool use. The agent cannot cite from internal model knowledge. Reasoning traces are validated against the rules table.

### Risk 2: Over-flagging (low precision)
False positives create review burden and erode user trust quickly.

*Mitigation:* Conservative confidence threshold for flagging. Quick-override UX. Track override rate as a leading indicator.

### Risk 3: Under-flagging (low recall)
Missing real semantic mismatches defeats the purpose.

*Mitigation:* Eval set explicitly includes known mismatches. Recall is a tracked, gated metric.

### Risk 4: Customer data sensitivity
Production handles confidential business data including transaction history.

*Mitigation:* Prototype uses synthetic data only. Production design would require enterprise data residency, model deployment options (e.g., AWS Bedrock private endpoints), and legal review.

### Risk 5: Misalignment with Vertex tax content
The agent's logic could diverge from how Vertex tax content team interprets rules.

*Mitigation:* Reference rules table is the single source of truth and is owned by tax content. Agent cannot reason outside it.

---

## 9. Assumptions

1. Vertex tax content team can produce and maintain a curated rules table consistent with their existing content business
2. Customer transaction data is accessible from Cert Center sync with the tax engine
3. The user (tax analyst) will trust an agent flag enough to act on it, given a strong reasoning trace
4. Audit liability framing is the primary value driver for the customer; productivity is secondary

Each of these is an assumption I would want to validate with customer interviews before committing engineering investment beyond the prototype.

---

## 10. Open questions

The questions a Principal PM would raise before scaling beyond prototype:

1. State coverage for v1: top 10 by certificate volume, or all 50?
2. Reasoning trigger: at certificate intake only, or also as a periodic re-validation across the existing inventory?
3. Action on flag: notify analyst, email customer for clarification, pause exempt-status until resolved?
4. Surface area: a feature inside Certificate Center, or a horizontal capability the entire Vertex platform can call?
5. Monetization: included in Cert Center, premium add-on, or usage-based pricing on validations performed?

---

## 11. Acceptance criteria

The prototype is complete when:

1. A user uploads a synthetic certificate PDF and triggers validation
2. The agent extracts fields, retrieves the customer's transaction sample, retrieves applicable state rules, and produces a decision
3. The decision includes confidence, structured reasoning, human-readable summary
4. Flagged certificates appear in a review queue with override capability
5. The eval harness runs the 25-scenario golden set and reports precision, recall, calibration
6. All five scenarios from the eval set are reproducible end-to-end

---

## 12. What this PRD is deliberately not

This is not a feature specification. It does not detail UI states, button placement, or notification copy. A real Principal PRD for an AI product is primarily a document about how we know the system works, how we know when it stops working, and what we do when it does. Feature spec lives downstream of this in design and engineering documents.

---

## Appendix A: Interview talking points

When walking through this PRD in the interview:

- Lead with the problem (one-third of audit penalties), not the solution
- Show I scoped tight: one state, three cert types, 25-scenario eval
- Call out non-goals explicitly: this is principal-level discipline
- Defend every metric target as a tradeoff, not a guess
- Be ready with 90-second, 5-minute, and 15-minute versions
- Bring this back to Vertex's stated AI direction: "AI that safely executes critical compliance work"
- Connect to my Samsung experience: HITL routing maps to OPTIC; eval harness maps to OPTIC's evaluation framework; rules-as-tool-use maps to RAGSaaS reusability pattern
