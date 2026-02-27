from abc import ABC, abstractmethod

from app.common.types import ImportJobKey
from app.domain.models.import_job import ImportJob


class IImportJobRepository(ABC):
    @abstractmethod
    def save(self, job: ImportJob) -> ImportJob: ...

    @abstractmethod
    def get_by_key(self, key: ImportJobKey) -> ImportJob | None: ...

    @abstractmethod
    def update(self, key: ImportJobKey, job: ImportJob) -> ImportJob: ...

    @abstractmethod
    def list_all(self, offset: int = 0, limit: int = 50) -> tuple[list[ImportJob], int]: ...

    @abstractmethod
    def delete(self, key: ImportJobKey) -> bool: ...
