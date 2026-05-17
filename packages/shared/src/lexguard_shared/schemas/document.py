from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class IngestionStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentSection(BaseModel):
    title: str
    content: str
    page: int | None = None
    subsections: list[DocumentSection] = Field(default_factory=list)


class ParsedDocument(BaseModel):
    document_id: str
    sections: list[DocumentSection] = Field(default_factory=list)


class IngestionJobResponse(BaseModel):
    document_id: str
    status: IngestionStatus
    message: str | None = None


class IngestionStatusResponse(BaseModel):
    document_id: str
    status: IngestionStatus
    error: str | None = None
    result: ParsedDocument | None = None
