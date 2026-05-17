from lexguard_shared.schemas.clause import ExtractedClause
from lexguard_shared.schemas.consequence import ConsequenceScenario
from lexguard_shared.schemas.risk import RiskCategory, RiskFinding, RiskFlag


def template_scenarios(
    finding: RiskFinding,
    clause: ExtractedClause,
) -> list[ConsequenceScenario]:
    """Rule-based fallback scenarios when LLM is unavailable."""
    builders = _TEMPLATE_MAP.get(finding.category, _generic_templates)
    return [
        ConsequenceScenario(
            scenario=s["scenario"],
            impact=s["impact"],
            likelihood=s["likelihood"],
            severity=min(s["severity"], finding.severity_score),
            explanation=s["explanation"].format(
                title=clause.title,
                text=clause.text[:200],
            ),
            clause_id=clause.clause_id,
            clause_title=clause.title,
            finding_id=finding.finding_id,
        )
        for s in builders(finding, clause)
    ]


def _financial_templates(finding: RiskFinding, clause: ExtractedClause) -> list[dict]:
    return [
        {
            "scenario": "Uncapped financial exposure from indemnification",
            "impact": "You may pay unlimited legal defense costs, settlements, and damages out of pocket.",
            "likelihood": 65.0,
            "severity": finding.severity_score,
            "explanation": (
                "The '{title}' clause requires you to cover the other party's losses without a stated cap. "
                "In a dispute, costs can exceed the contract's value."
            ),
        },
    ]


def _employment_templates(finding: RiskFinding, clause: ExtractedClause) -> list[dict]:
    return [
        {
            "scenario": "Career mobility restricted after leaving",
            "impact": "You may be unable to work in your field or region for the restricted period.",
            "likelihood": 70.0,
            "severity": finding.severity_score,
            "explanation": (
                "'{title}' limits where and how you can earn income after the relationship ends. "
                "Courts may enforce broad restrictions depending on jurisdiction."
            ),
        },
    ]


def _ip_templates(finding: RiskFinding, clause: ExtractedClause) -> list[dict]:
    return [
        {
            "scenario": "Loss of intellectual property rights",
            "impact": "Work you create may belong to the other party, limiting your ability to reuse or monetize it.",
            "likelihood": 75.0,
            "severity": finding.severity_score,
            "explanation": (
                "'{title}' may assign ownership of inventions, code, or content to the counterparty. "
                "You could lose rights to portfolio work tied to this agreement."
            ),
        },
    ]


def _arbitration_templates(finding: RiskFinding, clause: ExtractedClause) -> list[dict]:
    return [
        {
            "scenario": "Limited dispute resolution options",
            "impact": "You may be required to arbitrate individually, waiving court and class action remedies.",
            "likelihood": 80.0,
            "severity": finding.severity_score,
            "explanation": (
                "'{title}' can force private arbitration in a forum favorable to the drafter. "
                "Individual claims are harder and costlier to pursue at scale."
            ),
        },
    ]


def _privacy_templates(finding: RiskFinding, clause: ExtractedClause) -> list[dict]:
    return [
        {
            "scenario": "Personal data exposure or misuse",
            "impact": "Your data may be shared, retained, or used beyond what you expect with limited recourse.",
            "likelihood": 60.0,
            "severity": finding.severity_score,
            "explanation": (
                "'{title}' may grant broad data use rights. Vague terms make it harder to challenge misuse."
            ),
        },
    ]


def _compliance_templates(finding: RiskFinding, clause: ExtractedClause) -> list[dict]:
    if finding.flag == RiskFlag.VAGUE_LANGUAGE:
        return [
            {
                "scenario": "Unpredictable enforcement of vague terms",
                "impact": "The other party may interpret obligations broadly against you in a dispute.",
                "likelihood": 55.0,
                "severity": finding.severity_score * 0.85,
                "explanation": (
                    "'{title}' uses undefined standards like 'reasonable' or 'as needed.' "
                    "Ambiguity often resolves against the non-drafting party."
                ),
            },
        ]
    return [
        {
            "scenario": "Automatic renewal or lock-in",
            "impact": "The agreement may renew without clear notice, extending obligations you intended to end.",
            "likelihood": 50.0,
            "severity": finding.severity_score * 0.8,
            "explanation": (
                "'{title}' may include evergreen or auto-renewal language. "
                "Missing a notice window can bind you for another term."
            ),
        },
    ]


def _generic_templates(finding: RiskFinding, clause: ExtractedClause) -> list[dict]:
    return [
        {
            "scenario": f"Adverse outcome from {finding.flag.value}",
            "impact": "You may face disproportionate obligations or limited remedies if a dispute arises.",
            "likelihood": 50.0,
            "severity": finding.severity_score,
            "explanation": (
                f"The '{clause.title}' clause was flagged for {finding.flag.value}. Review before signing and negotiate clearer limits."
            ),
        },
    ]


_TEMPLATE_MAP = {
    RiskCategory.FINANCIAL_RISK: _financial_templates,
    RiskCategory.EMPLOYMENT_RISK: _employment_templates,
    RiskCategory.IP_RISK: _ip_templates,
    RiskCategory.ARBITRATION_RISK: _arbitration_templates,
    RiskCategory.PRIVACY_RISK: _privacy_templates,
    RiskCategory.COMPLIANCE_RISK: _compliance_templates,
}
