from app.common.enums import DuplicateStrategy, EntityType, ImportJobStatus
from app.common.exceptions import NotFoundError, ValidationError
from app.domain.engines.csv_parser import CsvParser
from app.domain.engines.import_engine import ImportEngine
from app.domain.engines.row_validator import RowValidator
from app.domain.interfaces.import_job_repository import IImportJobRepository
from app.domain.models.import_job import ImportJob


class ImportService:
    def __init__(
        self,
        import_repo: IImportJobRepository,
        species_repo=None,
        family_repo=None,
    ) -> None:
        self._repo = import_repo
        self._species_repo = species_repo
        self._family_repo = family_repo
        self._parser = CsvParser()
        self._validator = RowValidator()
        self._engine = ImportEngine(self._parser, self._validator)

    def upload(
        self,
        file_bytes: bytes,
        entity_type: EntityType,
        filename: str,
        duplicate_strategy: DuplicateStrategy = DuplicateStrategy.SKIP,
        uploaded_by: str = "",
    ) -> ImportJob:
        existing_keys = self._get_existing_keys(entity_type)
        job = self._engine.upload_and_validate(
            file_bytes,
            entity_type,
            filename,
            duplicate_strategy,
            existing_keys,
        )
        job.uploaded_by = uploaded_by
        return self._repo.save(job)

    def get_job(self, key: str) -> ImportJob:
        job = self._repo.get_by_key(key)
        if job is None:
            raise NotFoundError("ImportJob", key)
        return job

    def list_jobs(self, offset: int = 0, limit: int = 50) -> tuple[list[ImportJob], int]:
        return self._repo.list_all(offset, limit)

    def confirm(self, key: str) -> ImportJob:
        job = self.get_job(key)
        if job.status != ImportJobStatus.PREVIEW_READY:
            raise ValidationError(f"Job must be in PREVIEW_READY status, got {job.status}")

        create_fn = self._get_create_fn(job.entity_type)
        job = self._engine.confirm_import(job, create_fn)
        return self._repo.update(key, job)

    def delete_job(self, key: str) -> bool:
        self.get_job(key)
        return self._repo.delete(key)

    def get_template(self, entity_type: EntityType) -> str:
        return self._parser.get_template(entity_type)

    def _get_existing_keys(self, entity_type: EntityType) -> set[str]:
        if entity_type == EntityType.SPECIES and self._species_repo:
            docs, _ = self._species_repo.get_all(0, 10000)
            return {
                d.get("scientific_name", d.get("_key", ""))
                if isinstance(d, dict)
                else getattr(d, "scientific_name", "")
                for d in docs
            }
        if entity_type == EntityType.BOTANICAL_FAMILY and self._family_repo:
            docs, _ = self._family_repo.get_all(0, 10000)
            return {d.get("name", d.get("_key", "")) if isinstance(d, dict) else getattr(d, "name", "") for d in docs}
        return set()

    def _get_create_fn(self, entity_type: EntityType):
        if entity_type == EntityType.SPECIES and self._species_repo:
            from app.domain.models.species import Species

            def create_species(data: dict):
                species = Species(
                    scientific_name=data["scientific_name"],
                    common_name=data.get("common_name", ""),
                    description=data.get("description", ""),
                )
                self._species_repo.create(species)

            return create_species

        if entity_type == EntityType.BOTANICAL_FAMILY and self._family_repo:
            from app.domain.models.botanical_family import BotanicalFamily

            def create_family(data: dict):
                family = BotanicalFamily(
                    name=data["name"],
                    common_name=data.get("common_name", ""),
                    order_name=data.get("order_name", ""),
                    description=data.get("description", ""),
                )
                self._family_repo.create(family)

            return create_family

        def noop(data: dict):
            pass

        return noop
