"""Evaluation metrics computation."""

import statistics
from typing import Any


def compute_precision(results: list[Any]) -> float:
    """Precision on FLAG: of predicted FLAGs, how many are truly FLAG."""
    predicted_flag = [r for r in results if r.actual_decision == "FLAG"]
    if not predicted_flag:
        return 0.0
    true_positives = sum(1 for r in predicted_flag if r.expected_decision == "FLAG")
    return true_positives / len(predicted_flag)


def compute_recall(results: list[Any]) -> float:
    """Recall on FLAG: of true FLAGs, how many were predicted FLAG."""
    true_flag = [r for r in results if r.expected_decision == "FLAG"]
    if not true_flag:
        return 0.0
    true_positives = sum(1 for r in true_flag if r.actual_decision == "FLAG")
    return true_positives / len(true_flag)


def compute_brier_score(results: list[Any]) -> float:
    """Brier score: mean squared error of confidence vs binary correctness."""
    if not results:
        return 0.0
    scores = [(r.confidence - (1.0 if r.correct else 0.0)) ** 2 for r in results]
    return statistics.mean(scores)


def compute_confusion_matrix(results: list[Any]) -> dict[str, dict[str, int]]:
    """3x3 confusion matrix: actual → predicted → count."""
    labels = ["PASS", "FLAG", "NEEDS_REVIEW"]
    matrix: dict[str, dict[str, int]] = {a: {p: 0 for p in labels} for a in labels}
    for r in results:
        actual = r.expected_decision
        predicted = r.actual_decision
        if actual in matrix and predicted in matrix[actual]:
            matrix[actual][predicted] += 1
    return matrix


def compute_latency_distribution(results: list[Any]) -> dict[str, int]:
    """Compute p50 and p95 latency in milliseconds."""
    if not results:
        return {"p50": 0, "p95": 0}
    latencies = sorted(r.latency_ms for r in results)
    n = len(latencies)
    p50 = latencies[int(n * 0.50)]
    p95 = latencies[min(int(n * 0.95), n - 1)]
    return {"p50": p50, "p95": p95}
