
from typing import TYPE_CHECKING

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.import_job_repository import IImportJobRepository
from app.domain.models.import_job import ImportJob

if TYPE_CHECKING:
    from arango.database import StandardDatabase

    from app.common.types import ImportJobKey


class ArangoImportJobRepository(IImportJobRepository, BaseArangoRepository):
    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.IMPORT_JOBS)

    def save(self, job: ImportJob) -> ImportJob:
        doc = BaseArangoRepository.create(self, job)
        return ImportJob(**doc)

    def get_by_key(self, key: ImportJobKey) -> ImportJob | None:
        doc = BaseArangoRepository.get_by_key(self, key)
        return ImportJob(**doc) if doc else None

    def update(self, key: ImportJobKey, job: ImportJob) -> ImportJob:
        doc = BaseArangoRepository.update(self, key, job)
        return ImportJob(**doc)

    def list_all(self, offset: int = 0, limit: int = 50) -> tuple[list[ImportJob], int]:
        docs, total = BaseArangoRepository.get_all(self, offset, limit)
        return [ImportJob(**doc) for doc in docs], total

    def delete(self, key: ImportJobKey) -> bool:
        return BaseArangoRepository.delete(self, key)
