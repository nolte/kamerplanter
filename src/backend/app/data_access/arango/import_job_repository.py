from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.import_job_repository import IImportJobRepository
from app.domain.models.import_job import ImportJob


class ArangoImportJobRepository(BaseArangoRepository[ImportJob], IImportJobRepository):
    _model_cls = ImportJob

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.IMPORT_JOBS)

    def save(self, job: ImportJob) -> ImportJob:
        return super().create(job)

    def list_all(self, offset: int = 0, limit: int = 50) -> tuple[list[ImportJob], int]:
        return super().get_all(offset, limit)
