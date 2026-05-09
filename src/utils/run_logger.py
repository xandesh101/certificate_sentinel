"""Run and override logging utilities."""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

_LOG_DIR = Path(__file__).parent.parent.parent / "logs"
_LOG_DIR.mkdir(exist_ok=True)

_RUNS_FILE = _LOG_DIR / "runs.jsonl"
_OVERRIDES_FILE = _LOG_DIR / "overrides.jsonl"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("certificate_sentinel")


def log_run(
    run_id: str,
    scenario_id: str,
    customer_id: str,
    input_summary: dict,
    decision: "Decision",  # noqa: F821
    raw_messages: list,
    latency_ms: int,
    tool_calls: int,
    model: str,
) -> None:
    verifier_action = decision.metadata.get("verifier_action", "none")
    record = {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "scenario_id": scenario_id,
        "customer_id": customer_id,
        "input_summary": input_summary,
        "decision": {
            "decision": decision.decision,
            "confidence": decision.confidence,
            "reasoning_summary": decision.reasoning_summary,
            "citations": [c.model_dump() for c in decision.citations],
        },
        "verifier_action": verifier_action,
        "tool_calls": tool_calls,
        "latency_ms": latency_ms,
        "model": model,
        "raw_messages": raw_messages,
    }
    with open(_RUNS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    logger.info("run=%s scenario=%s decision=%s latency_ms=%d", run_id, scenario_id, decision.decision, latency_ms)


def log_override(
    override_id: str,
    run_id: str,
    original_decision: str,
    override_decision: str,
    reason_code: str,
    reviewer_note: str = "",
) -> None:
    record = {
        "override_id": override_id,
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "original_decision": original_decision,
        "override_decision": override_decision,
        "reason_code": reason_code,
        "reviewer_note": reviewer_note,
    }
    with open(_OVERRIDES_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    logger.info("override=%s run=%s %s->%s", override_id, run_id, original_decision, override_decision)
