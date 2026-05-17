import re
from dataclasses import dataclass
from uuid import uuid4

from lexguard_shared.schemas.document import DocumentSection, ParsedDocument

_CLAUSE_SPLIT = re.compile(
    r"(?=\n(?:\d+\.|\([a-z]\)|\([0-9]+\)|Article\s+\d+|Section\s+\d+|Clause\s+\d+))",
    re.IGNORECASE,
)
_MIN_CLAUSE_CHARS = 40


@dataclass(frozen=True)
class ClauseCandidate:
    clause_id: str
    title: str
    text: str
    page: int | None = None


class ClauseBoundaryDetector:
    """Detects clause boundaries from parsed document sections."""

    def detect(self, document: ParsedDocument) -> list[ClauseCandidate]:
        candidates: list[ClauseCandidate] = []
        for section in document.sections:
            candidates.extend(self._from_section(section))
        return self._deduplicate(candidates)

    def _from_section(
        self,
        section: DocumentSection,
        parent_title: str = "",
    ) -> list[ClauseCandidate]:
        title = section.title.strip()
        full_title = f"{parent_title} > {title}" if parent_title else title
        content = section.content.strip()

        results: list[ClauseCandidate] = []

        if section.subsections:
            if content and len(content) >= _MIN_CLAUSE_CHARS:
                results.append(self._make_candidate(full_title, content, section.page))
            for sub in section.subsections:
                results.extend(self._from_section(sub, full_title))
        else:
            combined = f"{title}\n{content}".strip() if content else title
            if len(combined) >= _MIN_CLAUSE_CHARS:
                for chunk in self._split_text(combined):
                    chunk_title, chunk_body = self._split_title_body(chunk, title)
                    results.append(self._make_candidate(chunk_title, chunk_body, section.page))
            elif combined:
                results.append(self._make_candidate(title, combined, section.page))

        return results

    def _split_text(self, text: str) -> list[str]:
        parts = [p.strip() for p in _CLAUSE_SPLIT.split(text) if p.strip()]
        if len(parts) <= 1:
            return [text]
        return [p for p in parts if len(p) >= _MIN_CLAUSE_CHARS] or [text]

    def _split_title_body(self, chunk: str, fallback_title: str) -> tuple[str, str]:
        lines = chunk.split("\n", 1)
        if len(lines) == 2 and len(lines[0]) < 120:
            return lines[0].strip(), lines[1].strip()
        return fallback_title, chunk

    def _make_candidate(self, title: str, text: str, page: int | None) -> ClauseCandidate:
        return ClauseCandidate(
            clause_id=uuid4().hex,
            title=title,
            text=text,
            page=page,
        )

    def _deduplicate(self, candidates: list[ClauseCandidate]) -> list[ClauseCandidate]:
        seen: set[str] = set()
        unique: list[ClauseCandidate] = []
        for candidate in candidates:
            key = candidate.text[:200].lower().strip()
            if key in seen:
                continue
            seen.add(key)
            unique.append(candidate)
        return unique
