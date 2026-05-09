"""Agent and verifier tests. End-to-end tests require ANTHROPIC_API_KEY and certificate PDFs."""

import pytest
from pathlib import Path

from src.agent.orchestrator import Decision, Citation
from src.agent.verifier import verify_decision


def test_verifier_passes_valid_rule():
    decision = Decision(
        decision="PASS",
        confidence=0.85,
        reasoning_summary="Test reasoning.",
        citations=[Citation(source="state_rule", reference_id="TX_RESALE_001", excerpt="test")],
    )
    result = verify_decision(decision)
    assert result.decision == "PASS"
    assert result.confidence == 0.85


def test_verifier_downgrades_hallucinated_rule():
    decision = Decision(
        decision="PASS",
        confidence=0.90,
        reasoning_summary="Test with fake rule.",
        citations=[Citation(source="state_rule", reference_id="TX_FAKE_999", excerpt="invented rule")],
    )
    result = verify_decision(decision)
    assert result.decision == "NEEDS_REVIEW"
    assert result.confidence == 0.3
    assert "TX_FAKE_999" in result.reasoning_summary
    assert "Verifier override" in result.reasoning_summary


def test_verifier_only_checks_state_rule_source():
    decision = Decision(
        decision="FLAG",
        confidence=0.85,
        reasoning_summary="Transaction mismatch.",
        citations=[
            Citation(source="transaction", reference_id="TXN_FAKE_000", excerpt="fake txn"),
            Citation(source="certificate_field", reference_id="signature", excerpt="missing"),
        ],
    )
    result = verify_decision(decision)
    assert result.decision == "FLAG"


def test_verifier_handles_mixed_valid_and_invalid():
    decision = Decision(
        decision="FLAG",
        confidence=0.88,
        reasoning_summary="Mixed citations.",
        citations=[
            Citation(source="state_rule", reference_id="TX_MFG_003", excerpt="eligible buyer types"),
            Citation(source="state_rule", reference_id="TX_HALLUCINATED_001", excerpt="invented"),
        ],
    )
    result = verify_decision(decision)
    assert result.decision == "NEEDS_REVIEW"
    assert "TX_HALLUCINATED_001" in result.reasoning_summary


_CERT_DIR = Path(__file__).parent.parent / "data" / "certificates"


@pytest.mark.skipif(
    not (_CERT_DIR / "C_001_resale_aligned.pdf").exists(),
    reason="Certificate PDFs not generated. Run scripts/generate_certificates.py first.",
)
@pytest.mark.skipif(
    not __import__("os").getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set.",
)
def test_end_to_end_c001_pass():
    from src.agent.orchestrator import validate_certificate
    from src.agent.verifier import verify_decision

    pdf_bytes = (_CERT_DIR / "C_001_resale_aligned.pdf").read_bytes()
    decision, _, _, _ = validate_certificate(pdf_bytes, "CUST_001", scenario_id="C_001_test")
    decision = verify_decision(decision)
    assert decision.decision == "PASS"
    assert decision.confidence > 0.5


@pytest.mark.skipif(
    not (_CERT_DIR / "C_002_mfg_consulting.pdf").exists(),
    reason="Certificate PDFs not generated.",
)
@pytest.mark.skipif(
    not __import__("os").getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set.",
)
def test_end_to_end_c002_flag():
    from src.agent.orchestrator import validate_certificate
    from src.agent.verifier import verify_decision

    pdf_bytes = (_CERT_DIR / "C_002_mfg_consulting.pdf").read_bytes()
    decision, _, _, _ = validate_certificate(pdf_bytes, "CUST_002", scenario_id="C_002_test")
    decision = verify_decision(decision)
    assert decision.decision == "FLAG"
