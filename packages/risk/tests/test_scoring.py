from lexguard_risk.rules.base import RuleHit
from lexguard_risk.scoring.severity import SeverityScorer
from lexguard_shared.schemas.clause import ClauseType, ExtractedClause
from lexguard_shared.schemas.risk import RiskCategory, RiskFlag


def test_compute_rule_severity() -> None:
    hits = [
        RuleHit(
            "R1",
            "Test",
            "matched",
            "pat",
            0.9,
            RiskFlag.VAGUE_LANGUAGE,
            (RiskCategory.COMPLIANCE_RISK,),
        ),
        RuleHit(
            "R2",
            "Test2",
            "matched2",
            "pat2",
            0.7,
            RiskFlag.VAGUE_LANGUAGE,
            (RiskCategory.COMPLIANCE_RISK,),
        ),
    ]
    score = SeverityScorer().compute_rule_severity(hits)
    assert 50 < score <= 100


def test_build_finding_without_llm() -> None:
    clause = ExtractedClause(
        clause_id="c1",
        clause_type=ClauseType.OTHER,
        title="Test",
        text="reasonable efforts required",
        confidence=0.8,
    )
    hits = [
        RuleHit(
            "V1",
            "Vague",
            "reasonable",
            "pat",
            0.6,
            RiskFlag.VAGUE_LANGUAGE,
            (RiskCategory.COMPLIANCE_RISK,),
        ),
    ]
    finding = SeverityScorer().build_finding(
        clause, RiskFlag.VAGUE_LANGUAGE, RiskCategory.COMPLIANCE_RISK, hits, None
    )
    assert finding.llm_enhanced is False
    assert finding.severity_score > 0
    assert finding.rule_evidence
