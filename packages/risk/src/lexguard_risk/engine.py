import asyncio
import logging
from collections import defaultdict

from lexguard_ai import AIClient, AISettings
from lexguard_shared.schemas.clause import ClauseExtractionResult, ExtractedClause
from lexguard_shared.schemas.risk import DocumentRiskAnalysis, RiskCategory, RiskFlag

from lexguard_risk.config import RiskSettings
from lexguard_risk.llm.analyzer import LLMRiskAnalyzer
from lexguard_risk.rules import ALL_RULES
from lexguard_risk.rules.base import RuleHit
from lexguard_risk.scoring.severity import SeverityScorer

logger = logging.getLogger(__name__)


class RiskAnalysisEngine:
    """Hybrid rule-based + LLM legal risk analysis engine."""

    def __init__(
        self,
        ai_client: AIClient | None = None,
        settings: RiskSettings | None = None,
        ai_settings: AISettings | None = None,
    ) -> None:
        self._settings = settings or RiskSettings()
        self._scorer = SeverityScorer(self._settings)
        self._llm = LLMRiskAnalyzer(ai_client, ai_settings)
        self._semaphore = asyncio.Semaphore((ai_settings or AISettings()).gemini_max_concurrency)

    async def analyze(self, clauses: ClauseExtractionResult) -> DocumentRiskAnalysis:
        logger.info(
            "Analyzing %d clauses for document %s",
            len(clauses.clauses),
            clauses.document_id,
        )

        tasks = [self._analyze_clause(clause) for clause in clauses.clauses]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_findings = []
        for clause, result in zip(clauses.clauses, results, strict=True):
            if isinstance(result, Exception):
                logger.error("Risk analysis failed for clause %s: %s", clause.clause_id, result)
                continue
            all_findings.extend(result)

        return self._scorer.aggregate(clauses.document_id, all_findings)

    async def _analyze_clause(self, clause: ExtractedClause) -> list:
        hits_by_flag: dict[RiskFlag, list[RuleHit]] = defaultdict(list)

        for rule in ALL_RULES:
            for hit in rule.evaluate(clause):
                hits_by_flag[hit.flag].append(hit)

        if not hits_by_flag:
            return []

        findings = []
        for flag, hits in hits_by_flag.items():
            category = self._primary_category(hits)
            llm = await self._maybe_enrich(clause, flag, category, hits)
            finding = self._scorer.build_finding(clause, flag, category, hits, llm)
            findings.append(finding)

        return findings

    async def _maybe_enrich(
        self,
        clause: ExtractedClause,
        flag: RiskFlag,
        category: RiskCategory,
        hits: list[RuleHit],
    ):
        rule_score = self._scorer.compute_rule_severity(hits)
        if rule_score < self._settings.risk_llm_enhancement_threshold * 100:
            return None

        async with self._semaphore:
            try:
                return await self._llm.enrich(clause, flag, category, hits)
            except Exception as exc:
                logger.warning("LLM enrichment failed for clause %s: %s", clause.clause_id, exc)
                return None

    def _primary_category(self, hits: list[RuleHit]) -> RiskCategory:
        category_weights: dict[RiskCategory, float] = defaultdict(float)
        for hit in hits:
            for cat in hit.categories:
                category_weights[cat] += hit.weight
        return max(category_weights, key=lambda k: category_weights[k])
