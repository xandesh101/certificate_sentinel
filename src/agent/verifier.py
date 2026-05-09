"""Post-decision verifier. Validates cited rule_ids against the rules table."""

from src.data import store


def verify_decision(decision: "Decision") -> "Decision":  # noqa: F821
    """Check cited state_rule references exist; downgrade to NEEDS_REVIEW if any are hallucinated."""
    from src.agent.orchestrator import Decision, Citation

    flagged_ids = []
    for citation in decision.citations:
        if citation.source == "state_rule":
            rule = store.get_rule_by_id(citation.reference_id)
            if rule is None:
                flagged_ids.append(citation.reference_id)

    if not flagged_ids:
        return decision

    ids_str = ", ".join(flagged_ids)
    note = f" [Verifier override: cited rule(s) {ids_str} not found in rules table]"

    return Decision(
        decision="NEEDS_REVIEW",
        confidence=0.3,
        reasoning_summary=decision.reasoning_summary + note,
        citations=decision.citations,
        metadata={**decision.metadata, "verifier_action": "downgraded", "invalid_rule_ids": flagged_ids},
    )
