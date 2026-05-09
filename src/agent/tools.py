"""Tool implementations and registry for the Certificate Sentinel agent."""

import json
from pathlib import Path

from src.data import store

_SCHEMAS_PATH = Path(__file__).parent.parent.parent / "prompts" / "tool_schemas.json"
with open(_SCHEMAS_PATH, "r", encoding="utf-8") as _f:
    _TOOL_SCHEMAS = json.load(_f)["tools"]


def get_customer_transactions(customer_id: str, limit: int = 30) -> dict:
    """Return recent transactions for a customer as a JSON-serializable dict."""
    customer = store.get_customer(customer_id)
    if customer is None:
        return {"error": f"Customer {customer_id} not found", "transactions": []}

    txns = store.get_transactions(customer_id, limit)
    return {
        "customer": customer.model_dump(),
        "transactions": [t.model_dump() for t in txns],
        "count": len(txns),
    }


def get_state_exemption_rules(state: str, exemption_type: str) -> dict:
    """Return exemption rules for a state and exemption type."""
    rules = store.get_rules(state, exemption_type)
    if not rules:
        return {
            "state": state,
            "exemption_type": exemption_type,
            "rules": [],
            "message": f"No rules found for {state} {exemption_type} exemption.",
        }
    return {
        "state": state,
        "exemption_type": exemption_type,
        "rules": [r.model_dump() for r in rules],
        "count": len(rules),
    }


def record_decision(
    decision: str,
    confidence: float,
    reasoning_summary: str,
    citations: list,
) -> dict:
    """Terminal tool: capture the agent's final decision. Returns the inputs unchanged."""
    return {
        "decision": decision,
        "confidence": confidence,
        "reasoning_summary": reasoning_summary,
        "citations": citations,
        "recorded": True,
    }


TOOL_REGISTRY: dict[str, callable] = {
    "get_customer_transactions": get_customer_transactions,
    "get_state_exemption_rules": get_state_exemption_rules,
    "record_decision": record_decision,
}

TOOL_SCHEMAS: list[dict] = _TOOL_SCHEMAS
