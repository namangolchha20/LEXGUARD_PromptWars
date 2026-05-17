from lexguard_ingestion.extractors.sections import SectionExtractor
from lexguard_ingestion.models import TextBlock


def test_builds_hierarchy_from_headings() -> None:
    blocks = [
        TextBlock(text="Chapter 1", page=1, font_size=18.0, is_bold=True, level=1),
        TextBlock(text="Intro paragraph.", page=1, font_size=12.0),
        TextBlock(text="Section 1.1", page=2, font_size=14.0, is_bold=True, level=2),
        TextBlock(text="Detail text.", page=2, font_size=12.0),
    ]

    nodes = SectionExtractor().from_blocks(blocks)
    sections = SectionExtractor().to_schema(nodes)

    assert len(sections) == 1
    assert sections[0].title == "Chapter 1"
    assert "Intro paragraph" in sections[0].content
    assert len(sections[0].subsections) == 1
    assert sections[0].subsections[0].title == "Section 1.1"
    assert sections[0].subsections[0].content == "Detail text."
