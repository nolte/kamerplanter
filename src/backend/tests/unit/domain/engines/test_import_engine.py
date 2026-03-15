import pytest

from app.common.enums import DuplicateStrategy, EntityType, ImportJobStatus, RowStatus
from app.domain.engines.import_engine import ImportEngine


@pytest.fixture
def engine():
    return ImportEngine()


class TestUploadAndValidate:
    def test_valid_csv(self, engine):
        csv = b"scientific_name,common_name\nRosa canina,Dog rose\nLavandula angustifolia,Lavender\n"
        job = engine.upload_and_validate(csv, EntityType.SPECIES, "test.csv", DuplicateStrategy.SKIP)
        assert job.status == ImportJobStatus.PREVIEW_READY
        assert job.row_count == 2
        assert all(r.status == RowStatus.VALID for r in job.preview_rows)

    def test_mixed_valid_invalid(self, engine):
        csv = b"scientific_name,common_name\nRosa canina,Dog rose\n,Missing name\n"
        job = engine.upload_and_validate(csv, EntityType.SPECIES, "test.csv", DuplicateStrategy.SKIP)
        assert job.status == ImportJobStatus.PREVIEW_READY
        assert job.preview_rows[0].status == RowStatus.VALID
        assert job.preview_rows[1].status == RowStatus.INVALID

    def test_invalid_csv_header(self, engine):
        csv = b"wrong_column\nvalue\n"
        job = engine.upload_and_validate(csv, EntityType.SPECIES, "test.csv", DuplicateStrategy.SKIP)
        assert job.status == ImportJobStatus.FAILED
        assert "Missing required columns" in (job.error_message or "")

    def test_duplicate_detection(self, engine):
        csv = b"scientific_name\nRosa canina\nNew species\n"
        existing = {"Rosa canina"}
        job = engine.upload_and_validate(csv, EntityType.SPECIES, "test.csv", DuplicateStrategy.SKIP, existing)
        assert job.preview_rows[0].status == RowStatus.DUPLICATE
        assert job.preview_rows[1].status == RowStatus.VALID


class TestConfirmImport:
    def test_creates_valid_rows(self, engine):
        csv = b"scientific_name,common_name\nRosa canina,Dog rose\nLavandula angustifolia,Lavender\n"
        job = engine.upload_and_validate(csv, EntityType.SPECIES, "test.csv", DuplicateStrategy.SKIP)

        created = []

        def mock_create(data):
            created.append(data)

        job = engine.confirm_import(job, mock_create)
        assert job.status == ImportJobStatus.COMPLETED
        assert job.result is not None
        assert job.result.created == 2
        assert len(created) == 2

    def test_skips_duplicates(self, engine):
        csv = b"scientific_name\nRosa canina\n"
        existing = {"Rosa canina"}
        job = engine.upload_and_validate(csv, EntityType.SPECIES, "test.csv", DuplicateStrategy.SKIP, existing)

        created = []
        job = engine.confirm_import(job, lambda d: created.append(d))
        assert job.result is not None
        assert job.result.skipped == 1
        assert job.result.created == 0
        assert len(created) == 0

    def test_fail_on_duplicates(self, engine):
        csv = b"scientific_name\nRosa canina\n"
        existing = {"Rosa canina"}
        job = engine.upload_and_validate(csv, EntityType.SPECIES, "test.csv", DuplicateStrategy.FAIL, existing)

        job = engine.confirm_import(job, lambda d: None)
        assert job.result is not None
        assert job.result.failed == 1

    def test_handles_create_error(self, engine):
        csv = b"scientific_name\nRosa canina\n"
        job = engine.upload_and_validate(csv, EntityType.SPECIES, "test.csv", DuplicateStrategy.SKIP)

        def failing_create(data):
            raise RuntimeError("DB error")

        job = engine.confirm_import(job, failing_create)
        assert job.result is not None
        assert job.result.failed == 1
