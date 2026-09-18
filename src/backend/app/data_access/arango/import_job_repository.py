from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.import_job_repository import IImportJobRepository
from app.domain.models.import_job import ImportJob


class ArangoImportJobRepository(BaseArangoRepository[ImportJob], IImportJobRepository):
    _model_cls = ImportJob

    #: SEC-B4 (#1501 review SCR-001). Without this the ``_enforce_tenant_scope``
    #: guard in :class:`BaseArangoRepository` is **inert** for this collection, and
    #: the inertness was not academic: ``_list_docs`` applies its filter under
    #: ``if tenant_key:``, so an empty string — which is exactly what
    #: ``get_active_tenant_context`` resolves for an anonymous, light-mode or
    #: personal-tenant-less caller — fell straight through to an unfiltered list and
    #: returned every tenant's jobs, ``preview_rows`` (the uploaded CSV content)
    #: included. The guard now raises on that call instead, and the service refuses
    #: an empty context before it ever gets here; both, because a guard that can only
    #: be reached through one caller is one refactor from being inert again.
    is_tenant_scoped = True

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.IMPORT_JOBS)

    def save(self, job: ImportJob) -> ImportJob:
        return super().create(job)

    def list_all(
        self, offset: int = 0, limit: int = 50, *, tenant_key: str | None = None
    ) -> tuple[list[ImportJob], int]:
        """List jobs; ``tenant_key=None`` is the explicit system-context read.

        ``all_tenants=True`` rather than "no filter": with
        :attr:`is_tenant_scoped` set, an unbound list is a ``ValueError``, and the
        system context has to say out loud that it means every tenant. An empty
        string is **not** a system context and never reaches here — the service
        answers it with an empty list — but if it did, the guard would raise.
        """
        return super().get_all(offset, limit, tenant_key, all_tenants=tenant_key is None)
