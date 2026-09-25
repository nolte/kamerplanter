"""The tenant service an account erasure hands its personal tenants to, over a test database (#1788).

Since #1788 :class:`PrivacyService` refuses to erase an account without a
:class:`TenantService` that can erase a tenant: the subject's personal tenant
goes through the tenant-erasure inventory (#1769). Every integration test that
runs an account erasure wires this — the service ``get_tenant_service`` builds,
with the stores that are not ArangoDB bound to their no-op implementations.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from app.data_access.arango.invitation_repository import ArangoInvitationRepository
from app.data_access.arango.location_assignment_repository import ArangoLocationAssignmentRepository
from app.data_access.arango.membership_repository import ArangoMembershipRepository
from app.data_access.arango.pest_image_repository import ArangoPestImageRepository
from app.data_access.arango.tenant_erasure_executor import ArangoTenantErasureExecutor
from app.data_access.arango.tenant_erasure_repository import ArangoTenantErasureRepository
from app.data_access.arango.tenant_repository import ArangoTenantRepository
from app.data_access.timescale.null_observation_repository import NullObservationRepository
from app.data_access.vectordb.noop_reference_index_store import NoopReferenceIndexStore
from app.data_access.vectordb.pest_prototype_stores import NoopPestPrototypeStore
from app.domain.services.tenant_service import TenantService


def tenant_erasure_service(database, salt: str, *, reference_index_store=None) -> TenantService:  # type: ignore[no-untyped-def]
    """A :class:`TenantService` that can erase a tenant of *database*, pseudonymising with *salt*.

    *salt* must be the account erasure's own: both write the subject's tombstone
    hash onto the retained harvest/treatment rows, and two salts would make the
    rows of one account unlinkable.
    """
    # The two collections this service reads on every account erasure; a module
    # that builds its database by hand (not through ``ensure_collections``) has
    # neither, where every deployment has both.
    for name in ("tenants", "tenant_erasure_records"):
        if not database.has_collection(name):
            database.create_collection(name)
    return TenantService(
        tenant_repo=ArangoTenantRepository(database),
        membership_repo=ArangoMembershipRepository(database),
        invitation_repo=ArangoInvitationRepository(database),
        assignment_repo=ArangoLocationAssignmentRepository(database),
        tenant_engine=MagicMock(),
        membership_engine=MagicMock(),
        invitation_engine=MagicMock(),
        storage_adapter=None,
        reference_index_store=reference_index_store or NoopReferenceIndexStore(),
        pest_image_repo=ArangoPestImageRepository(database),
        pest_prototype_store=NoopPestPrototypeStore(),
        observation_repo=NullObservationRepository(),
        tenant_erasure_executor=ArangoTenantErasureExecutor(database),
        tenant_erasure_repo=ArangoTenantErasureRepository(database),
        tombstone_salt=salt,
    )
