# 06 Test Scenarios

> The 10 eval scenarios. Each must be reproducible: same certificate PDF, same customer data, same rules, same agent should produce a result in the expected range.

## Scenario summary table

| ID | Description | Customer | Cert type | Expected | Conf range |
| --- | --- | --- | --- | --- | --- |
| C_001 | Office supply retailer, valid resale | CUST_001 | resale | PASS | 0.75-0.95 |
| C_002 | Software consulting claiming manufacturing | CUST_002 | manufacturing | FLAG | 0.80-0.95 |
| C_003 | Farm equipment dealer, valid agricultural | CUST_003 | agricultural | PASS | 0.75-0.95 |
| C_004 | Restaurant chain claiming resale | CUST_004 | resale | FLAG | 0.70-0.90 |
| C_005 | Industrial manufacturer, valid manufacturing | CUST_005 | manufacturing | PASS | 0.80-0.95 |
| C_006 | Office supply retailer, mixed transactions | CUST_001 | resale | NEEDS_REVIEW | 0.40-0.70 |
| C_007 | Manufacturer cert, signature missing | CUST_005 | manufacturing | FLAG | 0.85-1.00 |
| C_008 | Office supply retailer claiming agricultural | CUST_001 | agricultural | FLAG | 0.85-1.00 |
| C_009 | New customer, no transaction history | CUST_009 | resale | NEEDS_REVIEW | 0.20-0.50 |
| C_010 | Retailer with one ambiguous transaction | CUST_001 | resale | PASS | 0.60-0.85 |

## Detailed scenarios

### C_001: Aligned resale (PASS)

```json
{
  "scenario_id": "C_001",
  "description": "Office supply retailer submitting valid resale certificate, transactions confirm inventory purchases for resale",
  "certificate_pdf": "data/certificates/C_001_resale_aligned.pdf",
  "customer_id": "CUST_001",
  "claimed_exemption_type": "resale",
  "expected_decision": "PASS",
  "expected_confidence_range": [0.75, 0.95],
  "expected_citation_sources": ["state_rule", "transaction"],
  "expected_reasoning_topics": ["registered retailer", "resale", "office supplies"],
  "rationale": "CUST_001 is registered_retailer; transactions show consistent purchases of office supplies for resale; rule TX_RESALE_001 applies cleanly."
}
```

Certificate PDF should show: buyer Acme Office Supplies LLC, taxpayer ID TX-12345678, exemption reason "resale", description "Office products for resale to commercial customers", signature, current date.

### C_002: Service business claiming manufacturing (FLAG)

```json
{
  "scenario_id": "C_002",
  "description": "Software consulting firm submitting manufacturing exemption certificate; not a manufacturer",
  "certificate_pdf": "data/certificates/C_002_mfg_consulting.pdf",
  "customer_id": "CUST_002",
  "claimed_exemption_type": "manufacturing",
  "expected_decision": "FLAG",
  "expected_confidence_range": [0.80, 0.95],
  "expected_citation_sources": ["state_rule", "transaction", "certificate_field"],
  "expected_reasoning_topics": ["service provider", "manufacturing", "ineligible"],
  "rationale": "CUST_002 is service_provider, not eligible buyer type for manufacturing exemption per TX_MFG_003; transactions are laptops/software/services, not raw materials."
}
```

### C_003: Aligned agricultural (PASS)

```json
{
  "scenario_id": "C_003",
  "description": "Farm equipment dealer submitting valid agricultural exemption certificate",
  "certificate_pdf": "data/certificates/C_003_agricultural_aligned.pdf",
  "customer_id": "CUST_003",
  "claimed_exemption_type": "agricultural",
  "expected_decision": "PASS",
  "expected_confidence_range": [0.75, 0.95],
  "expected_citation_sources": ["state_rule", "transaction"],
  "expected_reasoning_topics": ["agricultural producer", "agricultural exemption", "farm equipment"],
  "rationale": "CUST_003 is agricultural_producer; transactions show purchases consistent with agricultural production."
}
```

### C_004: Restaurant claiming resale (FLAG)

```json
{
  "scenario_id": "C_004",
  "description": "Restaurant chain submitting resale certificate; food consumed at premises is not resale of tangible property",
  "certificate_pdf": "data/certificates/C_004_resale_restaurant.pdf",
  "customer_id": "CUST_004",
  "claimed_exemption_type": "resale",
  "expected_decision": "FLAG",
  "expected_confidence_range": [0.70, 0.90],
  "expected_citation_sources": ["state_rule", "transaction"],
  "expected_reasoning_topics": ["restaurant", "consumed", "not resale"],
  "rationale": "CUST_004 transactions show food/kitchen supplies consumed in service operations, not resale of tangible property per TX_RESALE_003."
}
```

### C_005: Aligned manufacturing (PASS)

```json
{
  "scenario_id": "C_005",
  "description": "Industrial manufacturer submitting valid manufacturing exemption certificate",
  "certificate_pdf": "data/certificates/C_005_mfg_aligned.pdf",
  "customer_id": "CUST_005",
  "claimed_exemption_type": "manufacturing",
  "expected_decision": "PASS",
  "expected_confidence_range": [0.80, 0.95],
  "expected_citation_sources": ["state_rule", "transaction"],
  "expected_reasoning_topics": ["manufacturer", "raw materials", "manufacturing exemption"],
  "rationale": "CUST_005 is manufacturer; transactions show steel, machine parts, lubricants consistent with TX_MFG_001 raw materials and TX_MFG_007 component parts."
}
```

### C_006: Mixed-use ambiguity (NEEDS_REVIEW)

```json
{
  "scenario_id": "C_006",
  "description": "Office supply retailer with mostly aligned transactions but several recent purchases that appear to be office furniture for own use",
  "certificate_pdf": "data/certificates/C_006_resale_mixed.pdf",
  "customer_id": "CUST_001",
  "claimed_exemption_type": "resale",
  "expected_decision": "NEEDS_REVIEW",
  "expected_confidence_range": [0.40, 0.70],
  "expected_citation_sources": ["state_rule", "transaction"],
  "expected_reasoning_topics": ["mixed", "ambiguous", "own use"],
  "rationale": "Most transactions support resale, but 3-5 transactions in the 90-day window show purchases that look like own-use (executive desks, conference room chairs); ambiguous, needs human review."
}
```

For this scenario, manually inject 3-5 own-use transactions into CUST_001's history.

### C_007: Field issue, signature missing (FLAG)

```json
{
  "scenario_id": "C_007",
  "description": "Manufacturer submitting valid-on-content certificate but missing signature field",
  "certificate_pdf": "data/certificates/C_007_mfg_no_signature.pdf",
  "customer_id": "CUST_005",
  "claimed_exemption_type": "manufacturing",
  "expected_decision": "FLAG",
  "expected_confidence_range": [0.85, 1.00],
  "expected_citation_sources": ["state_rule", "certificate_field"],
  "expected_reasoning_topics": ["signature", "missing field", "required"],
  "rationale": "Even though customer is eligible and transactions align, signature is a required field per TX_MFG_006; field-level invalidity is sufficient to FLAG."
}
```

The PDF for this scenario should explicitly omit the signature line.

### C_008: Wrong exemption type for retailer (FLAG)

```json
{
  "scenario_id": "C_008",
  "description": "Office supply retailer submitting agricultural exemption certificate; not engaged in agriculture",
  "certificate_pdf": "data/certificates/C_008_agricultural_retailer.pdf",
  "customer_id": "CUST_001",
  "claimed_exemption_type": "agricultural",
  "expected_decision": "FLAG",
  "expected_confidence_range": [0.85, 1.00],
  "expected_citation_sources": ["state_rule", "transaction"],
  "expected_reasoning_topics": ["agricultural", "not agricultural producer", "ineligible"],
  "rationale": "CUST_001 is registered_retailer in office supplies; not eligible buyer type for agricultural exemption per TX_AG_002."
}
```

### C_009: New customer, insufficient data (NEEDS_REVIEW)

```json
{
  "scenario_id": "C_009",
  "description": "New customer with no transaction history submitting resale certificate",
  "certificate_pdf": "data/certificates/C_009_resale_new_customer.pdf",
  "customer_id": "CUST_009",
  "claimed_exemption_type": "resale",
  "expected_decision": "NEEDS_REVIEW",
  "expected_confidence_range": [0.20, 0.50],
  "expected_citation_sources": ["state_rule"],
  "expected_reasoning_topics": ["new customer", "no transactions", "insufficient data"],
  "rationale": "Field-valid certificate but customer has no transaction history; cannot validate semantic alignment between exemption claim and purchasing pattern."
}
```

### C_010: Edge case, mostly aligned (PASS)

```json
{
  "scenario_id": "C_010",
  "description": "Office supply retailer with one transaction that could be read as own-use, but pattern is overwhelmingly resale",
  "certificate_pdf": "data/certificates/C_010_resale_edge.pdf",
  "customer_id": "CUST_001",
  "claimed_exemption_type": "resale",
  "expected_decision": "PASS",
  "expected_confidence_range": [0.60, 0.85],
  "expected_citation_sources": ["state_rule", "transaction"],
  "expected_reasoning_topics": ["resale", "consistent pattern"],
  "rationale": "Pattern is clearly resale; one ambiguous transaction is statistical noise, not evidence of misuse. Confidence is moderate to acknowledge the noise."
}
```

For this scenario, do NOT inject the same 3-5 own-use transactions as C_006. C_010 should have only 1 ambiguous transaction in the history. The point is to test that the agent doesn't over-react to edge cases.

## How to validate the eval set

After all scenarios are built, run the eval harness. Expected aggregate behavior:
- Precision on FLAG: >= 80% (4 of the 5 FLAG scenarios should be predicted FLAG; one allowed miss)
- Recall on FLAG: >= 80% (same logic)
- PASS predictions: 3 of 3 PASS scenarios should be predicted PASS
- NEEDS_REVIEW: 2 of 2 NEEDS_REVIEW scenarios should be predicted NEEDS_REVIEW or have low confidence

If the eval shows wide misses (50% accuracy or worse), iterate on the system prompt before iterating on the agent code. Most prototype-stage misses are prompt issues, not architectural ones.
