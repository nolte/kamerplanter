from abc import ABC, abstractmethod

from app.common.types import ImportJobKey
from app.domain.models.import_job import ImportJob


class IImportJobRepository(ABC):
    @abstractmethod
    def save(self, job: ImportJob) -> ImportJob: ...

    @abstractmethod
    def get_by_key(self, key: ImportJobKey) -> ImportJob | None: ...

    @abstractmethod
    def get_or_raise(self, key: ImportJobKey) -> ImportJob: ...

    @abstractmethod
    def update(self, key: ImportJobKey, job: ImportJob) -> ImportJob: ...

    @abstractmethod
    def list_all(self, offset: int = 0, limit: int = 50, *, tenant_key: str | None) -> tuple[list[ImportJob], int]:
        """List import jobs, scoped to ``tenant_key`` when one is given (#1501).

        No default (#1708): ``None`` means "every tenant", so the caller must say
        it rather than get it by leaving the argument out.

        ``None`` is the unscoped system-context read. Every HTTP caller passes the
        tenant it resolved: a staged job carries the rows of an uploaded CSV, so an
        unscoped list handed one tenant's upload to every other one.
        """
        ...

    @abstractmethod
    def delete(self, key: ImportJobKey) -> bool: ...
