from lexguard_agents.consequence.templates import template_scenarios
from lexguard_shared.schemas.clause import ClauseType, ExtractedClause
from lexguard_shared.schemas.risk import RiskCategory, RiskFinding, RiskFlag


def test_financial_template() -> None:
    clause = ExtractedClause(
        clause_id="c1",
        clause_type=ClauseType.INDEMNIFICATION,
        title="Indemnity",
        text="Indemnify and hold harmless.",
        confidence=0.9,
    )
    finding = RiskFinding(
        finding_id="f1",
        clause_id="c1",
        clause_title="Indemnity",
        category=RiskCategory.FINANCIAL_RISK,
        flag=RiskFlag.HIDDEN_LIABILITY,
        severity_score=75.0,
        confidence=0.8,
        plain_language_explanation="High exposure.",
        legal_reasoning="Uncapped.",
        affected_parties=[],
        rule_evidence=[],
    )
    scenarios = template_scenarios(finding, clause)
    assert len(scenarios) >= 1
    assert "financial" in scenarios[0].scenario.lower() or "exposure" in scenarios[0].impact.lower()
