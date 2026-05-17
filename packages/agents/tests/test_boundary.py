from lexguard_agents.clause.boundary import ClauseBoundaryDetector
from lexguard_shared.schemas.document import DocumentSection, ParsedDocument


def test_detects_sections_and_subsections() -> None:
    document = ParsedDocument(
        document_id="doc-1",
        sections=[
            DocumentSection(
                title="Article 1 - Confidentiality",
                content="The receiving party shall not disclose confidential information.",
                page=1,
                subsections=[
                    DocumentSection(
                        title="1.1 Definition",
                        content="Confidential Information means all proprietary data.",
                        page=1,
                    ),
                ],
            ),
            DocumentSection(
                title="Article 2 - Termination",
                content="Either party may terminate with thirty (30) days written notice.",
                page=2,
            ),
        ],
    )

    candidates = ClauseBoundaryDetector().detect(document)

    assert len(candidates) >= 2
    titles = [c.title for c in candidates]
    assert any("Confidentiality" in t for t in titles)
    assert any("Termination" in t for t in titles)
