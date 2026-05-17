class IngestionError(Exception):
    """Base exception for ingestion failures."""


class ValidationError(IngestionError):
    """Raised when uploaded file fails validation."""


class UnsupportedFormatError(ValidationError):
    """Raised when file type is not supported."""


class FileTooLargeError(ValidationError):
    """Raised when file exceeds size limit."""


class ParseError(IngestionError):
    """Raised when document parsing fails."""


class OCRError(IngestionError):
    """Raised when OCR processing fails."""
