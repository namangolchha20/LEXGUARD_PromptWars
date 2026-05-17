import pytest
from lexguard_ingestion.config import IngestionSettings
from lexguard_ingestion.exceptions import FileTooLargeError, UnsupportedFormatError
from lexguard_ingestion.models import DocumentFormat
from lexguard_ingestion.validators import validate_upload


@pytest.fixture
def settings() -> IngestionSettings:
    return IngestionSettings(ingestion_max_file_size_mb=10)


def test_validate_pdf(settings: IngestionSettings) -> None:
    fmt = validate_upload("contract.pdf", 1024, settings)
    assert fmt == DocumentFormat.PDF


def test_validate_docx(settings: IngestionSettings) -> None:
    fmt = validate_upload("agreement.docx", 1024, settings)
    assert fmt == DocumentFormat.DOCX


def test_reject_unsupported_extension(settings: IngestionSettings) -> None:
    with pytest.raises(UnsupportedFormatError):
        validate_upload("image.png", 1024, settings)


def test_reject_oversized_file(settings: IngestionSettings) -> None:
    with pytest.raises(FileTooLargeError):
        validate_upload("large.pdf", settings.max_file_size_bytes + 1, settings)
