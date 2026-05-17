import asyncio
import logging
from uuid import uuid4

from lexguard_ai import AIClient, AISettings
from lexguard_shared.schemas.clause import ClauseExtractionResult, ExtractedClause
from lexguard_shared.schemas.document import ParsedDocument

from lexguard_agents.clause.boundary import ClauseBoundaryDetector, ClauseCandidate
from lexguard_agents.clause.models import ClauseAnalysisResponse
from lexguard_agents.clause.prompts import CLAUSE_EXTRACTION_SYSTEM, CLAUSE_EXTRACTION_USER

logger = logging.getLogger(__name__)


class ClauseExtractionAgent:
    """Extracts, classifies, and structures legal clauses from parsed documents."""

    def __init__(
        self,
        ai_client: AIClient | None = None,
        settings: AISettings | None = None,
    ) -> None:
        self._ai = ai_client or AIClient(settings)
        self._settings = settings or AISettings()
        self._boundary_detector = ClauseBoundaryDetector()
        self._semaphore = asyncio.Semaphore(self._settings.gemini_max_concurrency)

    async def extract(self, document: ParsedDocument) -> ClauseExtractionResult:
        candidates = self._boundary_detector.detect(document)
        if not candidates:
            logger.warning("No clause boundaries detected for document %s", document.document_id)
            return ClauseExtractionResult(document_id=document.document_id, clauses=[])

        logger.info(
            "Extracting %d clauses from document %s",
            len(candidates),
            document.document_id,
        )

        tasks = [self._extract_clause(candidate) for candidate in candidates]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        clauses: list[ExtractedClause] = []
        for candidate, result in zip(candidates, results, strict=True):
            if isinstance(result, Exception):
                logger.error("Clause extraction failed for %s: %s", candidate.clause_id, result)
                continue
            clauses.append(result)

        clauses.sort(key=lambda c: c.confidence, reverse=True)
        return ClauseExtractionResult(document_id=document.document_id, clauses=clauses)

    async def _extract_clause(self, candidate: ClauseCandidate) -> ExtractedClause:
        async with self._semaphore:
            prompt = CLAUSE_EXTRACTION_USER.format(
                title=candidate.title,
                text=candidate.text,
            )
            analysis = await self._ai.gemini.generate_structured(
                prompt=prompt,
                response_model=ClauseAnalysisResponse,
                system_instruction=CLAUSE_EXTRACTION_SYSTEM,
            )

            confidence = self._adjust_confidence(analysis.confidence, analysis)

            return ExtractedClause(
                clause_id=candidate.clause_id,
                clause_type=analysis.clause_type,
                title=analysis.title or candidate.title,
                text=candidate.text,
                obligations=analysis.obligations,
                penalties=analysis.penalties,
                rights=analysis.rights,
                durations=analysis.durations,
                financial_liabilities=analysis.financial_liabilities,
                confidence=confidence,
            )

    def _adjust_confidence(
        self,
        model_confidence: float,
        analysis: ClauseAnalysisResponse,
    ) -> float:
        """Blend model confidence with extraction completeness signals."""
        score = model_confidence
        extracted_fields = sum(
            1
            for field in (
                analysis.obligations,
                analysis.penalties,
                analysis.rights,
                analysis.durations,
                analysis.financial_liabilities,
            )
            if field
        )
        completeness_bonus = min(extracted_fields * 0.03, 0.12)
        adjusted = min(score + completeness_bonus, 1.0)
        return round(adjusted, 3)

    @staticmethod
    def new_clause_id() -> str:
        return uuid4().hex
