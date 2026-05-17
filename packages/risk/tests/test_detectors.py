from lexguard_risk.rules.detectors import (
    EXPLOITATIVE_RULE,
    HIDDEN_LIABILITY_RULE,
    ONE_SIDED_RULE,
    VAGUE_RULE,
)
from lexguard_shared.schemas.clause import ClauseType, ExtractedClause


def _clause(text: str, clause_type: ClauseType = ClauseType.OTHER) -> ExtractedClause:
    return ExtractedClause(
        clause_id="c1",
        clause_type=clause_type,
        title="Test Clause",
        text=text,
        confidence=0.9,
    )


def test_detects_exploitative_language() -> None:
    clause = _clause("The company may terminate at its sole discretion without notice.")
    hits = EXPLOITATIVE_RULE.evaluate(clause)
    assert len(hits) >= 1
    assert any("sole discretion" in h.matched_text.lower() for h in hits)


def test_detects_vague_language() -> None:
    clause = _clause("Party shall use reasonable efforts from time to time as needed.")
    hits = VAGUE_RULE.evaluate(clause)
    assert len(hits) >= 2


def test_detects_hidden_liability() -> None:
    clause = _clause(
        "Licensee shall indemnify and hold harmless Licensor against all claims.",
        ClauseType.INDEMNIFICATION,
    )
    hits = HIDDEN_LIABILITY_RULE.evaluate(clause)
    assert len(hits) >= 2


def test_detects_one_sided_obligations() -> None:
    clause = _clause(
        "Employee shall comply. Employee shall notify. Employee shall return materials. "
        "Employer shall provide access."
    )
    hits = ONE_SIDED_RULE.evaluate(clause)
    assert len(hits) == 1
