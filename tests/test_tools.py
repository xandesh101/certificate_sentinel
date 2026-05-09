"""Tests for tool implementations."""

import pytest
from src.agent.tools import get_customer_transactions, get_state_exemption_rules, record_decision, TOOL_SCHEMAS


def test_get_customer_transactions_happy_path():
    result = get_customer_transactions("CUST_001")
    assert "customer" in result
    assert "transactions" in result
    assert result["count"] >= 30
    assert result["customer"]["registration_type"] == "registered_retailer"


def test_get_customer_transactions_limit():
    result = get_customer_transactions("CUST_001", limit=5)
    assert result["count"] == 5
    assert len(result["transactions"]) == 5


def test_get_customer_transactions_unknown():
    result = get_customer_transactions("CUST_999")
    assert "error" in result
    assert result["transactions"] == []


def test_get_state_exemption_rules_happy_path():
    result = get_state_exemption_rules("TX", "resale")
    assert "rules" in result
    assert result["count"] == 6
    rule_ids = [r["rule_id"] for r in result["rules"]]
    assert "TX_RESALE_001" in rule_ids


def test_get_state_exemption_rules_manufacturing():
    result = get_state_exemption_rules("TX", "manufacturing")
    assert result["count"] == 8


def test_get_state_exemption_rules_not_found():
    result = get_state_exemption_rules("CA", "resale")
    assert result["rules"] == []
    assert "message" in result


def test_record_decision_returns_inputs():
    citations = [{"source": "state_rule", "reference_id": "TX_RESALE_001", "excerpt": "test"}]
    result = record_decision("PASS", 0.85, "Test reasoning", citations)
    assert result["decision"] == "PASS"
    assert result["confidence"] == 0.85
    assert result["recorded"] is True


def test_tool_schemas_match_expected_names():
    names = {t["name"] for t in TOOL_SCHEMAS}
    assert names == {"get_customer_transactions", "get_state_exemption_rules", "record_decision"}


def test_tool_schemas_have_required_fields():
    for schema in TOOL_SCHEMAS:
        assert "name" in schema
        assert "description" in schema
        assert "input_schema" in schema
