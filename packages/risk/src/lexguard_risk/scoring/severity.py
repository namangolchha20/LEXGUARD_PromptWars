from collections import defaultdict
from uuid import uuid4

from lexguard_shared.schemas.clause import ExtractedClause
from lexguard_shared.schemas.risk import (
    CategoryScore,
    DocumentRiskAnalysis,
    RiskCategory,
    RiskFinding,
    RiskFlag,
    RuleEvidence,
)

from lexguard_risk.config import RiskSettings
from lexguard_risk.llm.models import LLMRiskAssessment
from lexguard_risk.rules.base import RuleHit


class SeverityScorer:
    """Computes weighted severity scores from rule hits and LLM assessments."""

    def __init__(self, settings: RiskSettings | None = None) -> None:
        self._settings = settings or RiskSettings()

    def compute_rule_severity(self, hits: list[RuleHit]) -> float:
        if not hits:
            return 0.0
        weights = [h.weight for h in hits]
        max_weight = max(weights)
        avg_weight = sum(weights) / len(weights)
        hit_bonus = min(len(hits) * 5, 20)
        raw = (max_weight * 70 + avg_weight * 30) + hit_bonus
        return round(min(raw, 100.0), 2)

    def blend_scores(self, rule_score: float, llm_score: float) -> float:
        blended = (
            rule_score * self._settings.risk_rule_weight
            + llm_score * self._settings.risk_llm_weight
        )
        return round(min(blended, 100.0), 2)

    def blend_confidence(self, rule_confidence: float, llm_confidence: float) -> float:
        return round((rule_confidence * 0.4 + llm_confidence * 0.6), 3)

    def rule_confidence(self, hits: list[RuleHit], clause_confidence: float) -> float:
        if not hits:
            return 0.0
        pattern_strength = min(sum(h.weight for h in hits) / len(hits), 1.0)
        return round(min(pattern_strength * 0.7 + clause_confidence * 0.3, 1.0), 3)

    def build_finding(
        self,
        clause: ExtractedClause,
        flag: RiskFlag,
        category: RiskCategory,
        hits: list[RuleHit],
        llm: LLMRiskAssessment | None,
    ) -> RiskFinding:
        rule_score = self.compute_rule_severity(hits)
        rule_conf = self.rule_confidence(hits, clause.confidence)

        if llm:
            severity = self.blend_scores(rule_score, llm.severity_score)
            confidence = self.blend_confidence(rule_conf, llm.confidence)
            explanation = llm.plain_language_explanation
            reasoning = llm.legal_reasoning
            parties = llm.affected_parties
            llm_enhanced = True
        else:
            severity = rule_score
            confidence = rule_conf
            explanation = self._fallback_explanation(flag, hits)
            reasoning = self._fallback_reasoning(flag, hits, clause)
            parties = self._fallback_parties(flag)
            llm_enhanced = False

        return RiskFinding(
            finding_id=uuid4().hex,
            clause_id=clause.clause_id,
            clause_title=clause.title,
            category=category,
            flag=flag,
            severity_score=severity,
            confidence=confidence,
            plain_language_explanation=explanation,
            legal_reasoning=reasoning,
            affected_parties=parties,
            rule_evidence=[
                RuleEvidence(
                    rule_id=h.rule_id,
                    rule_name=h.rule_name,
                    matched_text=h.matched_text,
                    pattern=h.pattern,
                    weight=h.weight,
                )
                for h in hits
            ],
            llm_enhanced=llm_enhanced,
        )

    def aggregate(
        self,
        document_id: str,
        findings: list[RiskFinding],
    ) -> DocumentRiskAnalysis:
        if not findings:
            return DocumentRiskAnalysis(
                document_id=document_id,
                overall_severity_score=0.0,
                overall_confidence=0.0,
                summary="No significant legal risks detected in the analyzed clauses.",
                findings=[],
                category_scores=[],
            )

        category_map: dict[RiskCategory, list[float]] = defaultdict(list)
        for f in findings:
            category_map[f.category].append(f.severity_score)

        category_scores = [
            CategoryScore(
                category=cat,
                score=round(sum(scores) / len(scores), 2),
                finding_count=len(scores),
            )
            for cat, scores in sorted(category_map.items(), key=lambda x: -max(x[1]))
        ]

        weighted_severities = sorted(
            (f.severity_score * f.confidence for f in findings),
            reverse=True,
        )
        top_n = weighted_severities[:5]
        overall_severity = round(sum(top_n) / len(top_n), 2) if top_n else 0.0
        overall_confidence = round(
            sum(f.confidence for f in findings) / len(findings),
            3,
        )

        high_risk = [f for f in findings if f.severity_score >= 70]
        summary = self._build_summary(findings, high_risk, overall_severity)

        return DocumentRiskAnalysis(
            document_id=document_id,
            overall_severity_score=overall_severity,
            overall_confidence=overall_confidence,
            summary=summary,
            findings=sorted(findings, key=lambda f: -f.severity_score),
            category_scores=category_scores,
        )

    def _fallback_explanation(self, flag: RiskFlag, hits: list[RuleHit]) -> str:
        names = ", ".join(h.rule_name for h in hits[:3])
        descriptions = {
            RiskFlag.EXPLOITATIVE_LANGUAGE: f"This clause contains potentially exploitative terms: {names}.",
            RiskFlag.VAGUE_LANGUAGE: f"This clause uses vague language that may be unenforceable or abused: {names}.",
            RiskFlag.HIDDEN_LIABILITY: f"This clause may impose hidden financial exposure: {names}.",
            RiskFlag.ONE_SIDED_OBLIGATION: "Obligations in this clause appear heavily weighted toward one party.",
            RiskFlag.EXCESSIVE_RESTRICTION: f"This clause imposes broad restrictions: {names}.",
        }
        return descriptions.get(flag, f"Risk detected: {names}.")

    def _fallback_reasoning(
        self, flag: RiskFlag, hits: list[RuleHit], clause: ExtractedClause
    ) -> str:
        evidence = "; ".join(f'"{h.matched_text}"' for h in hits[:3])
        return (
            f"Rule-based analysis of {flag.value} in clause type '{clause.clause_type.value}' "
            f"identified: {evidence}. These patterns are associated with enforceability challenges "
            f"and asymmetric risk allocation under contract law."
        )

    def _fallback_parties(self, flag: RiskFlag) -> list:
        from lexguard_shared.schemas.risk import AffectedParty

        defaults = {
            RiskFlag.EXPLOITATIVE_LANGUAGE: [
                AffectedParty(
                    party="signing_party",
                    role="weaker_party",
                    impact="Bears unilateral risk",
                    risk_level="high",
                ),
            ],
            RiskFlag.ONE_SIDED_OBLIGATION: [
                AffectedParty(
                    party="obligated_party",
                    role="obligor",
                    impact="Disproportionate duties",
                    risk_level="high",
                ),
            ],
        }
        return defaults.get(
            flag,
            [
                AffectedParty(
                    party="parties",
                    role="both",
                    impact="Potential dispute risk",
                    risk_level="medium",
                ),
            ],
        )

    def _build_summary(
        self,
        findings: list[RiskFinding],
        high_risk: list[RiskFinding],
        overall: float,
    ) -> str:
        if overall >= 70:
            level = "high"
        elif overall >= 40:
            level = "moderate"
        else:
            level = "low"

        flags = {f.flag.value for f in findings}
        flag_summary = ", ".join(sorted(flags)[:4])
        high_count = len(high_risk)
        return (
            f"Document presents {level} overall legal risk (score: {overall}/100). "
            f"Found {len(findings)} risk findings across categories including {flag_summary}. "
            f"{high_count} finding(s) rated high severity (≥70)."
        )
