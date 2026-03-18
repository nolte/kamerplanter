from app.common.enums import DuplicateStrategy, EntityType, ImportJobStatus, RowStatus
from app.domain.engines.csv_parser import CsvParser
from app.domain.engines.row_validator import RowValidator
from app.domain.models.import_job import ImportJob, ImportResult, RowValidationError


class ImportEngine:
    """Orchestrates CSV upload, validation, and import execution."""

    def __init__(
        self,
        csv_parser: CsvParser | None = None,
        row_validator: RowValidator | None = None,
    ) -> None:
        self._parser = csv_parser or CsvParser()
        self._validator = row_validator or RowValidator()

    def upload_and_validate(
        self,
        file_bytes: bytes,
        entity_type: EntityType,
        filename: str,
        duplicate_strategy: DuplicateStrategy,
        existing_keys: set[str] | None = None,
    ) -> ImportJob:
        """Parse CSV, validate rows, return job with preview."""
        try:
            rows, warnings = self._parser.parse(file_bytes, entity_type)
        except ValueError as e:
            return ImportJob(
                entity_type=entity_type,
                filename=filename,
                duplicate_strategy=duplicate_strategy,
                status=ImportJobStatus.FAILED,
                error_message=str(e),
            )

        preview_rows = []
        for i, row in enumerate(rows, start=1):
            preview = self._validator.validate_row(row, entity_type, i, existing_keys)
            # SEC-M-008: Attach CSV injection warnings as validation errors
            for warning in warnings:
                if warning.startswith(f"Row {i},"):
                    preview.errors.append(
                        RowValidationError(
                            row=i,
                            field="",
                            message=warning,
                        )
                    )
            preview_rows.append(preview)

        return ImportJob(
            entity_type=entity_type,
            filename=filename,
            duplicate_strategy=duplicate_strategy,
            status=ImportJobStatus.PREVIEW_READY,
            row_count=len(rows),
            preview_rows=preview_rows,
        )

    def confirm_import(
        self,
        job: ImportJob,
        create_fn,
        find_fn=None,
        update_fn=None,
    ) -> ImportJob:
        """Execute the import: create/update/skip entities based on preview."""
        result = ImportResult()

        for preview in job.preview_rows:
            if preview.status == RowStatus.INVALID:
                result.failed += 1
                result.errors.extend(preview.errors)
                continue

            if preview.status == RowStatus.DUPLICATE:
                if job.duplicate_strategy == DuplicateStrategy.FAIL:
                    result.failed += 1
                    result.errors.append(
                        RowValidationError(
                            row=preview.row_number,
                            field="",
                            message=f"Duplicate: {preview.duplicate_key}",
                        )
                    )
                    continue
                if job.duplicate_strategy == DuplicateStrategy.SKIP:
                    result.skipped += 1
                    continue
                if job.duplicate_strategy == DuplicateStrategy.UPDATE and update_fn:
                    try:
                        update_fn(preview.data)
                        result.updated += 1
                    except Exception as e:
                        result.failed += 1
                        result.errors.append(
                            RowValidationError(
                                row=preview.row_number,
                                field="",
                                message=str(e),
                            )
                        )
                    continue

            # VALID row — create
            try:
                create_fn(preview.data)
                result.created += 1
            except Exception as e:
                result.failed += 1
                result.errors.append(
                    RowValidationError(
                        row=preview.row_number,
                        field="",
                        message=str(e),
                    )
                )

        job.result = result
        job.status = ImportJobStatus.COMPLETED
        return job
