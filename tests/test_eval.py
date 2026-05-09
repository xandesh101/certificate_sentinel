"""Tests for eval metrics computation."""

import pytest
from src.eval.metrics import (
    compute_brier_score,
    compute_confusion_matrix,
    compute_latency_distribution,
    compute_precision,
    compute_recall,
)


class _FakeResult:
    def __init__(self, expected, actual, confidence, latency_ms=1000):
        self.expected_decision = expected
        self.actual_decision = actual
        self.confidence = confidence
        self.latency_ms = latency_ms

    @property
    def correct(self):
        return self.expected_decision == self.actual_decision


def _results():
    return [
        _FakeResult("FLAG", "FLAG", 0.90),
        _FakeResult("FLAG", "FLAG", 0.85),
        _FakeResult("FLAG", "NEEDS_REVIEW", 0.45),
        _FakeResult("PASS", "PASS", 0.80),
        _FakeResult("NEEDS_REVIEW", "NEEDS_REVIEW", 0.30),
    ]


def test_precision():
    results = _results()
    p = compute_precision(results)
    assert p == pytest.approx(1.0)


def test_recall():
    results = _results()
    r = compute_recall(results)
    assert r == pytest.approx(2 / 3)


def test_brier_score_perfect():
    results = [_FakeResult("PASS", "PASS", 1.0)]
    assert compute_brier_score(results) == pytest.approx(0.0)


def test_brier_score_worst():
    # confidence=1.0 on a wrong prediction → (1.0 - 0)^2 = 1.0
    results = [_FakeResult("PASS", "FLAG", 1.0)]
    assert compute_brier_score(results) == pytest.approx(1.0)


def test_confusion_matrix():
    results = _results()
    cm = compute_confusion_matrix(results)
    assert cm["FLAG"]["FLAG"] == 2
    assert cm["FLAG"]["NEEDS_REVIEW"] == 1
    assert cm["PASS"]["PASS"] == 1
    assert cm["NEEDS_REVIEW"]["NEEDS_REVIEW"] == 1


def test_latency_distribution():
    results = [_FakeResult("PASS", "PASS", 0.8, lm) for lm in [1000, 2000, 3000, 4000, 5000]]
    dist = compute_latency_distribution(results)
    assert dist["p50"] == 3000
    assert dist["p95"] == 5000


def test_empty_results():
    assert compute_precision([]) == 0.0
    assert compute_recall([]) == 0.0
    assert compute_brier_score([]) == 0.0
    assert compute_latency_distribution([]) == {"p50": 0, "p95": 0}
