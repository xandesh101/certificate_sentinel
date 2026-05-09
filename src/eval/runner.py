"""Eval runner: executes all scenarios and computes aggregate metrics."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from pydantic import BaseModel

from src.eval.metrics import (
    compute_brier_score,
    compute_confusion_matrix,
    compute_latency_distribution,
    compute_precision,
    compute_recall,
)

_BASE = Path(__file__).parent.parent.parent
_SCENARIOS_FILE = _BASE / "eval_scenarios" / "scenarios.json"


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


def run_eval(progress_callback: Optional[Callable[[str], None]] = None) -> EvalReport:
    """Run all scenarios and return an EvalReport."""
    from src.agent.orchestrator import MODEL, validate_certificate
    from src.agent.verifier import verify_decision

    def _progress(msg: str) -> None:
        if progress_callback:
            progress_callback(msg)

    with open(_SCENARIOS_FILE, "r", encoding="utf-8") as f:
        scenarios = json.load(f)["scenarios"]

    results: list[ScenarioResult] = []

    for scenario in scenarios:
        sid = scenario["scenario_id"]
        _progress(f"Running {sid}...")

        pdf_path = _BASE / scenario["certificate_pdf"]
        if not pdf_path.exists():
            _progress(f"  SKIP: PDF not found at {pdf_path}")
            continue

        pdf_bytes = pdf_path.read_bytes()
        try:
            decision, _, tool_calls, latency_ms = validate_certificate(
                pdf_bytes=pdf_bytes,
                customer_id=scenario["customer_id"],
                scenario_id=sid,
            )
            decision = verify_decision(decision)
        except Exception as e:
            _progress(f"  ERROR: {e}")
            from src.agent.orchestrator import Decision
            decision = Decision(
                decision="NEEDS_REVIEW",
                confidence=0.0,
                reasoning_summary=f"Eval error: {e}",
                citations=[],
            )
            tool_calls = 0
            latency_ms = 0

        actual = decision.decision
        expected = scenario["expected_decision"]
        conf_range = scenario["expected_confidence_range"]
        conf_in_range = conf_range[0] <= decision.confidence <= conf_range[1]

        actual_sources = {c.source for c in decision.citations}
        expected_sources = set(scenario["expected_citation_sources"])
        sources_match = expected_sources.issubset(actual_sources)

        reasoning_lower = decision.reasoning_summary.lower()
        topics_match = all(
            topic.lower() in reasoning_lower
            for topic in scenario["expected_reasoning_topics"]
        )

        result = ScenarioResult(
            scenario_id=sid,
            expected_decision=expected,
            actual_decision=actual,
            correct=(actual == expected),
            confidence=decision.confidence,
            confidence_in_range=conf_in_range,
            citation_sources_match=sources_match,
            reasoning_topics_match=topics_match,
            latency_ms=latency_ms,
            tool_calls=tool_calls,
        )
        results.append(result)
        _progress(f"  {sid}: {actual} (expected {expected}) conf={decision.confidence:.2f}")

        time.sleep(1)

    latency_dist = compute_latency_distribution(results)
    avg_tool_calls = sum(r.tool_calls for r in results) / max(len(results), 1)

    return EvalReport(
        timestamp=datetime.now(timezone.utc).isoformat(),
        model=MODEL,
        scenarios=results,
        precision=compute_precision(results),
        recall=compute_recall(results),
        brier_score=compute_brier_score(results),
        confusion_matrix=compute_confusion_matrix(results),
        latency_p50=latency_dist["p50"],
        latency_p95=latency_dist["p95"],
        avg_tool_calls=avg_tool_calls,
    )
