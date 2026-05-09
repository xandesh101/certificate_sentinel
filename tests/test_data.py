"""Tests for data loading and schema validation."""

import pytest
from src.data.store import get_customer, get_transactions, get_rules, all_rule_ids, Customer, Transaction, Rule


def test_customers_load():
    cust = get_customer("CUST_001")
    assert cust is not None
    assert isinstance(cust, Customer)
    assert cust.name == "Acme Office Supplies LLC"
    assert cust.registration_type == "registered_retailer"


def test_all_ten_customers_present():
    for i in range(1, 11):
        cid = f"CUST_{i:03d}"
        assert get_customer(cid) is not None, f"{cid} missing"


def test_transactions_load():
    txns = get_transactions("CUST_001")
    assert len(txns) >= 30
    for t in txns:
        assert isinstance(t, Transaction)
        assert t.customer_id == "CUST_001"


def test_transactions_sorted_by_date_descending():
    txns = get_transactions("CUST_001", limit=10)
    dates = [t.date for t in txns]
    assert dates == sorted(dates, reverse=True)


def test_new_customer_has_no_transactions():
    txns = get_transactions("CUST_009")
    assert txns == []


def test_rules_load():
    rules = get_rules("TX", "resale")
    assert len(rules) == 6
    for r in rules:
        assert isinstance(r, Rule)
        assert r.state == "TX"
        assert r.exemption_type == "resale"


def test_all_rule_sets_present():
    assert len(get_rules("TX", "resale")) == 6
    assert len(get_rules("TX", "manufacturing")) == 8
    assert len(get_rules("TX", "agricultural")) == 6


def test_rule_ids_unique():
    ids = all_rule_ids()
    assert len(ids) == 20


def test_missing_customer_returns_none():
    assert get_customer("CUST_999") is None


def test_unknown_state_rules_empty():
    rules = get_rules("CA", "resale")
    assert rules == []
