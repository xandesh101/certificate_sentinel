# 05 Data Specifications

> Schemas and sample data for all mock data files. These are the source of truth for what `src/data/store.py` exposes.

## Customer profile schema

File: `data/customers.json`

```json
{
  "customers": [
    {
      "customer_id": "CUST_001",
      "name": "Acme Office Supplies LLC",
      "industry": "Office supply retailer",
      "primary_business": "Resale of office products to commercial customers",
      "states_active": ["TX", "OK", "LA"],
      "registered_taxpayer_id": "TX-12345678",
      "registration_type": "registered_retailer"
    }
  ]
}
```

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| customer_id | string | yes | Format `CUST_NNN`, zero-padded |
| name | string | yes | Display name |
| industry | string | yes | Plain English |
| primary_business | string | yes | One sentence describing what they actually do |
| states_active | array of string | yes | Two-letter state codes |
| registered_taxpayer_id | string | yes | Mock ID; format consistent across customers |
| registration_type | string | yes | One of: `registered_retailer`, `registered_wholesaler`, `manufacturer`, `agricultural_producer`, `service_provider`, `unregistered` |

### Required customer set (10 customers)

| customer_id | name | type | Used in scenarios |
| --- | --- | --- | --- |
| CUST_001 | Acme Office Supplies LLC | registered_retailer | C_001 (PASS), C_006 (NEEDS_REVIEW), C_008 (FLAG), C_010 (PASS) |
| CUST_002 | Lighthouse Software Consulting | service_provider | C_002 (FLAG) |
| CUST_003 | Hill Country Farm Equipment | agricultural_producer | C_003 (PASS) |
| CUST_004 | Brisket Barons Restaurants | service_provider | C_004 (FLAG) |
| CUST_005 | Steel & Stone Industrial Mfg | manufacturer | C_005 (PASS), C_007 (FLAG, field issue) |
| CUST_006 | Lone Star Wholesale Distribution | registered_wholesaler | (reserve for future scenarios) |
| CUST_007 | Texas Plumbing Supply Co | registered_wholesaler | (reserve) |
| CUST_008 | Pecan Valley Farms | agricultural_producer | (reserve) |
| CUST_009 | New Customer Inc | unregistered | C_009 (NEEDS_REVIEW, no transactions) |
| CUST_010 | Mixed Goods Trading Co | registered_retailer | (reserve, ambiguous use) |

---

## Transaction schema

File: `data/transactions.json`

```json
{
  "transactions": [
    {
      "transaction_id": "TXN_00001",
      "customer_id": "CUST_001",
      "date": "2026-04-15",
      "state": "TX",
      "product_category": "Office supplies",
      "product_description": "Pens, paper, desk organizers, file folders",
      "amount_usd": 1240.50,
      "tax_charged": false
    }
  ]
}
```

| Field | Type | Notes |
| --- | --- | --- |
| transaction_id | string | Format `TXN_NNNNN`, zero-padded to 5 |
| customer_id | string | Foreign key to customer |
| date | string | ISO 8601 date, all within last 90 days |
| state | string | Two-letter state code; usually matches a customer's active state |
| product_category | string | High-level category |
| product_description | string | Specific items |
| amount_usd | float | Realistic transaction amount |
| tax_charged | boolean | Whether sales tax was charged on this transaction |

### Transaction generation rules

- 30 to 50 transactions per customer (except CUST_009, which has 0)
- Date distribution: spread across last 90 days, with rough weekly cadence
- Amount distribution: log-normal, $100 to $50,000 typical range
- For customers claiming exemptions: most transactions should be `tax_charged: false`
- Product categories should be consistent with the customer's business:
  - CUST_001 (office supply retailer): office supplies, paper products, small electronics
  - CUST_002 (software consulting): laptops, software licenses, office furniture, professional services
  - CUST_003 (farm equipment dealer): tractors, agricultural implements, irrigation equipment, parts
  - CUST_004 (restaurant chain): food supplies, kitchen equipment, cleaning supplies, paper goods
  - CUST_005 (industrial manufacturer): raw steel, machine parts, industrial chemicals, lubricants
  - CUST_006-008 (reserves): generate consistent with their business type
  - CUST_010 (mixed-use retailer): half office supplies (resale), half cleaning chemicals (consumed)

---

## State exemption rules schema

File: `data/rules.json`

```json
{
  "rules": [
    {
      "rule_id": "TX_RESALE_001",
      "state": "TX",
      "exemption_type": "resale",
      "description": "Resale exemption applies only to tangible personal property purchased for resale in the ordinary course of business",
      "eligible_product_categories": ["all tangible personal property"],
      "ineligible_product_categories": ["services", "consumed supplies", "equipment for own use"],
      "eligible_buyer_types": ["registered_retailer", "registered_wholesaler"],
      "required_certificate_fields": ["buyer_name", "buyer_taxpayer_id", "seller_name", "description_of_property", "reason_for_exemption", "signature", "date"],
      "citation": "Texas Tax Code Section 151.302",
      "summary": "Buyer must be a registered retailer or wholesaler purchasing tangible property they will resell."
    }
  ]
}
```

| Field | Type | Notes |
| --- | --- | --- |
| rule_id | string | Format: `STATE_TYPE_NNN`. The agent cites this. |
| state | string | Two-letter state code |
| exemption_type | string | One of: `resale`, `manufacturing`, `agricultural` |
| description | string | The substantive rule, in plain language |
| eligible_product_categories | array | What the rule allows |
| ineligible_product_categories | array | What the rule explicitly excludes |
| eligible_buyer_types | array | Which `registration_type` values can claim this |
| required_certificate_fields | array | Which fields must be present |
| citation | string | The legal reference (real or plausible) |
| summary | string | One-sentence agent-friendly summary |

### Required rule set (~20 rules total)

Six resale rules, eight manufacturing rules, six agricultural rules. Specific rule IDs to generate:

**Resale (TX_RESALE_001 through TX_RESALE_006):**
- 001: General resale exemption (tangible property for resale)
- 002: Buyer must be registered retailer or wholesaler
- 003: Property cannot be consumed by the buyer
- 004: Required certificate fields list
- 005: Exemption does not apply to services
- 006: Resale certificate validity period (4 years from issue)

**Manufacturing (TX_MFG_001 through TX_MFG_008):**
- 001: General manufacturing exemption (raw materials)
- 002: Manufacturing equipment exemption
- 003: Buyer must be a manufacturer engaged in tangible production
- 004: Excluded: office supplies, administrative items
- 005: Excluded: items used in service businesses
- 006: Required certificate fields
- 007: Component parts that become part of finished product
- 008: Equipment used directly in production

**Agricultural (TX_AG_001 through TX_AG_006):**
- 001: General agricultural exemption
- 002: Buyer must be engaged in agricultural production
- 003: Eligible categories: equipment, feed, seed
- 004: Excluded: items for personal use
- 005: Required certificate fields
- 006: Equipment used directly in agricultural production

Use real-sounding language but the rules don't need to perfectly match Texas law. They need to be consistent and citable by the agent.

---

## Certificate scenario schema

File: `eval_scenarios/scenarios.json`

```json
{
  "scenarios": [
    {
      "scenario_id": "C_001",
      "description": "Office supply retailer submitting valid resale certificate, transactions confirm inventory purchases",
      "certificate_pdf": "data/certificates/C_001_resale_aligned.pdf",
      "customer_id": "CUST_001",
      "claimed_exemption_type": "resale",
      "expected_decision": "PASS",
      "expected_confidence_range": [0.7, 0.95],
      "expected_citation_sources": ["transaction", "state_rule"],
      "expected_reasoning_topics": ["registered retailer", "resale exemption", "office supplies inventory"],
      "rationale": "Customer is a registered retailer, transactions show purchases for resale, all rule conditions met."
    }
  ]
}
```

| Field | Type | Notes |
| --- | --- | --- |
| scenario_id | string | Format `C_NNN` |
| description | string | One-sentence what's happening |
| certificate_pdf | string | Path to the synthetic PDF |
| customer_id | string | Which customer's transactions to use |
| claimed_exemption_type | string | What the cert claims |
| expected_decision | string | One of: `PASS`, `FLAG`, `NEEDS_REVIEW` |
| expected_confidence_range | array of two floats | Acceptable confidence bracket |
| expected_citation_sources | array | Which source types should appear in citations |
| expected_reasoning_topics | array | Keywords that should appear in reasoning summary |
| rationale | string | Why this scenario expects this outcome |

The full 10-scenario specification is in `docs/06_TEST_SCENARIOS.md`.

---

## Decision output schema

This is what `validate_certificate` returns and what `record_decision` populates:

```python
class Citation(BaseModel):
    source: Literal["certificate_field", "transaction", "state_rule"]
    reference_id: str
    excerpt: str

class Decision(BaseModel):
    decision: Literal["PASS", "FLAG", "NEEDS_REVIEW"]
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning_summary: str
    citations: list[Citation]
    metadata: dict = {}
```

The agent always populates citations. An empty citations list with confidence > 0.3 is treated as a soft warning by the verifier (not currently downgraded, but logged).

---

## Run log schema

File: `logs/runs.jsonl` (one JSON object per line)

```json
{
  "run_id": "uuid-v4",
  "timestamp": "2026-05-09T18:00:00Z",
  "scenario_id": "C_001",
  "customer_id": "CUST_001",
  "input_summary": {
    "claimed_exemption_type": "resale",
    "certificate_path": "data/certificates/C_001_resale_aligned.pdf"
  },
  "decision": {
    "decision": "PASS",
    "confidence": 0.85,
    "reasoning_summary": "...",
    "citations": [...]
  },
  "verifier_action": "none | downgraded",
  "tool_calls": 2,
  "latency_ms": 14820,
  "model": "claude-sonnet-4-6",
  "raw_messages": [...]
}
```

## Override log schema

File: `logs/overrides.jsonl` (one JSON object per line)

```json
{
  "override_id": "uuid-v4",
  "run_id": "uuid-v4",
  "timestamp": "2026-05-09T18:05:00Z",
  "original_decision": "FLAG",
  "override_decision": "PASS",
  "reason_code": "agent_misread_transaction | rule_misinterpreted | data_outdated | other",
  "reviewer_note": "Free-text optional"
}
```

## Eval report schema

What `run_eval()` returns:

```python
class ScenarioResult(BaseModel):
    scenario_id: str
    expected_decision: str
    actual_decision: str
    correct: bool
    confidence: float
    confidence_in_range: bool
    citation_sources_match: bool
    reasoning_topics_match: bool
    latency_ms: int
    tool_calls: int

class EvalReport(BaseModel):
    timestamp: str
    model: str
    scenarios: list[ScenarioResult]
    precision: float
    recall: float
    brier_score: float
    confusion_matrix: dict
    latency_p50: int
    latency_p95: int
    avg_tool_calls: float
```
