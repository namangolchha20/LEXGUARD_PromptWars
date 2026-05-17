from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path


class DocumentFormat(StrEnum):
    PDF = "pdf"
    DOCX = "docx"


@dataclass
class TextBlock:
    text: str
    page: int
    font_size: float = 12.0
    is_bold: bool = False
    level: int = 0


@dataclass
class SectionNode:
    title: str
    content: str = ""
    page: int | None = None
    level: int = 1
    children: list["SectionNode"] = field(default_factory=list)


@dataclass
class ParseContext:
    document_id: str
    file_path: Path
    format: DocumentFormat
