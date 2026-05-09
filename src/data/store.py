"""Data store module. Loads JSON files at import time and exposes typed accessors."""

import json
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

_DATA_DIR = Path(__file__).parent.parent.parent / "data"


class Customer(BaseModel):
    customer_id: str
    name: str
    industry: str
    primary_business: str
    states_active: list[str]
    registered_taxpayer_id: str
    registration_type: str


class Transaction(BaseModel):
    transaction_id: str
    customer_id: str
    date: str
    state: str
    product_category: str
    product_description: str
    amount_usd: float
    tax_charged: bool


class Rule(BaseModel):
    rule_id: str
    state: str
    exemption_type: str
    description: str
    eligible_product_categories: list[str]
    ineligible_product_categories: list[str]
    eligible_buyer_types: list[str]
    required_certificate_fields: list[str]
    citation: str
    summary: str


def _load_json(filename: str) -> dict:
    with open(_DATA_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)


_customers_raw = _load_json("customers.json")
_transactions_raw = _load_json("transactions.json")
_rules_raw = _load_json("rules.json")

_customers: dict[str, Customer] = {
    c["customer_id"]: Customer(**c) for c in _customers_raw["customers"]
}
_transactions_by_customer: dict[str, list[Transaction]] = {}
for t in _transactions_raw["transactions"]:
    txn = Transaction(**t)
    _transactions_by_customer.setdefault(txn.customer_id, []).append(txn)

_rules_by_state_type: dict[tuple[str, str], list[Rule]] = {}
for r in _rules_raw["rules"]:
    rule = Rule(**r)
    key = (rule.state, rule.exemption_type)
    _rules_by_state_type.setdefault(key, []).append(rule)

_rules_by_id: dict[str, Rule] = {
    r["rule_id"]: Rule(**r) for r in _rules_raw["rules"]
}


def get_customer(customer_id: str) -> Optional[Customer]:
    return _customers.get(customer_id)


def get_transactions(customer_id: str, limit: int = 30) -> list[Transaction]:
    txns = _transactions_by_customer.get(customer_id, [])
    txns_sorted = sorted(txns, key=lambda t: t.date, reverse=True)
    return txns_sorted[:limit]


def get_rules(state: str, exemption_type: str) -> list[Rule]:
    return _rules_by_state_type.get((state, exemption_type), [])


def get_rule_by_id(rule_id: str) -> Optional[Rule]:
    return _rules_by_id.get(rule_id)


def all_rule_ids() -> set[str]:
    return set(_rules_by_id.keys())
