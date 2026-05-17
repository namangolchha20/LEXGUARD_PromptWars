from pathlib import Path

from lexguard_ingestion.config import IngestionSettings
from lexguard_ingestion.exceptions import FileTooLargeError, UnsupportedFormatError, ValidationError
from lexguard_ingestion.models import DocumentFormat


def validate_upload(filename: str, size_bytes: int, settings: IngestionSettings) -> DocumentFormat:
    if not filename:
        raise ValidationError("Filename is required")

    suffix = Path(filename).suffix.lower()
    if suffix not in settings.allowed_extensions:
        raise UnsupportedFormatError(
            f"Unsupported file type '{suffix}'. Allowed: {', '.join(sorted(settings.allowed_extensions))}"
        )

    if size_bytes <= 0:
        raise ValidationError("File is empty")

    if size_bytes > settings.max_file_size_bytes:
        raise FileTooLargeError(
            f"File exceeds maximum size of {settings.ingestion_max_file_size_mb} MB"
        )

    if suffix == ".pdf":
        return DocumentFormat.PDF
    if suffix == ".docx":
        return DocumentFormat.DOCX

    raise UnsupportedFormatError(f"Unsupported file type '{suffix}'")
