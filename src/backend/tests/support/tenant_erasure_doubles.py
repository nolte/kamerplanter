"""Doubles for the tenant deletion (#1769) — shaped like the real ones, refusing what they refuse.

:class:`FakeTenantErasureRepository` mirrors ``ArangoTenantErasureRepository``:
``create_with_key`` refuses a second record for the same key (the real insert
fails on the primary key), ``claim_for_run`` applies the same filter as the AQL
``UPDATE`` (never a completed record, never a fresh ``in_progress`` one that was
already claimed), and ``update_fields`` merges like ``collection.update`` does.
Values are round-tripped through the model, so a field the real record cannot
hold is refused here too.

:class:`RecordingTenantErasureExecutor` records the plan it was handed and calls
``pseudonymize`` for each account key it is told to find, so a test sees the
value the service's salt produces.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from unittest.mock import MagicMock

from app.common.enums import AdminScope, TenantRole
from app.common.exceptions import DuplicateError
from app.domain.interfaces.tenant_erasure_executor import ITenantErasureExecutor
from app.domain.interfaces.tenant_erasure_repository import ITenantErasureRepository
from app.domain.models.membership import Membership
from app.domain.models.tenant import Tenant
from app.domain.models.tenant_erasure import (
    TenantDeletionConfirmation,
    TenantErasureOrigin,
    TenantErasurePlan,
    TenantErasureRecord,
    TenantErasureReport,
)
from app.domain.models.user import User
from app.domain.services.tenant_service import TenantService

#: NFR-011 §4 wants >= 32 characters. Synthetic, test-only.
SALT = "unit-tenant-erasure-salt-0123456789abcdef"

#: The requester every deletion test that is *not* about authorisation uses: a
#: federated account (no password to verify — bcrypt is slow and beside the
#: point there) holding lead + management in every tenant it is asked about, and
#: the platform-admin membership (#1791). The authorisation itself is pinned
#: through the routes in ``tests/unit/api/test_tenant_delete_authorization.py``.
AUTHORIZED_REQUESTER = User.model_validate(
    {"_key": "requester-1", "email": "requester@example.org", "display_name": "Requester"}
)


def authorized(slug: str = "t-1", *, origin: TenantErasureOrigin = "tenant_management") -> dict[str, Any]:
    """Keyword arguments of an authorised ``delete_tenant`` call for the tenant slugged *slug*."""
    return {
        "requester": AUTHORIZED_REQUESTER,
        "authenticated_with_api_key": False,
        "confirmation": TenantDeletionConfirmation(confirm_slug=slug),
        "origin": origin,
    }


def authorizing_membership_repo() -> MagicMock:
    """A membership repo granting :data:`AUTHORIZED_REQUESTER` lead + management everywhere."""
    repo = MagicMock()
    repo.get_by_user_and_tenant.side_effect = lambda user_key, tenant_key: (
        Membership(
            user_key=user_key,
            tenant_key=tenant_key,
            role=TenantRole.LEAD,
            admin_scopes=[AdminScope.MANAGEMENT],
        )
        if user_key == AUTHORIZED_REQUESTER.key
        else None
    )
    return repo


class FakeTenantErasureRepository(ITenantErasureRepository):
    def __init__(self) -> None:
        self.records: dict[str, dict[str, Any]] = {}

    def _model(self, key: str) -> TenantErasureRecord:
        return TenantErasureRecord.model_validate({**self.records[key], "_key": key})

    def get(self, key: str) -> TenantErasureRecord | None:
        return self._model(key) if key in self.records else None

    def create_with_key(self, record: TenantErasureRecord, key: str) -> TenantErasureRecord:
        if key in self.records:
            raise DuplicateError("tenant_erasure_records", "_key", key)
        self.records[key] = record.model_dump(mode="json", exclude={"key"})
        return self._model(key)

    def claim_for_run(self, key: str, *, now_iso: str, stale_before_iso: str) -> TenantErasureRecord | None:
        doc = self.records.get(key)
        if doc is None or doc["status"] == "completed":
            return None
        claimed_fresh = (
            doc["status"] == "in_progress"
            and doc.get("last_attempt_at") is not None
            and doc.get("updated_at") is not None
            and doc["updated_at"] > stale_before_iso
        )
        if claimed_fresh:
            return None
        doc.update(status="in_progress", last_attempt_at=now_iso, updated_at=now_iso)
        return self._model(key)

    def update_fields(self, key: str, fields: dict[str, Any]) -> TenantErasureRecord | None:
        merged = {**self.records[key], **fields}
        TenantErasureRecord.model_validate({**merged, "_key": key})  # the real store holds only valid records
        self.records[key] = merged
        return self._model(key)

    def list_due(self, *, stale_before_iso: str) -> list[TenantErasureRecord]:
        due = [
            key
            for key, doc in self.records.items()
            if doc["status"] == "partially_completed"
            or (doc["status"] == "in_progress" and (doc.get("updated_at") or "") <= stale_before_iso)
        ]
        return [self._model(key) for key in due]


class RecordingTenantErasureExecutor(ITenantErasureExecutor):
    def __init__(
        self,
        *,
        unreached: list[str] | None = None,
        account_keys: list[str] | None = None,
        raises: BaseException | None = None,
        on_run: Callable[[], None] | None = None,
    ) -> None:
        self.plans: list[TenantErasurePlan] = []
        self.pseudonyms: dict[str, str] = {}
        self._unreached = unreached or []
        self._account_keys = account_keys or []
        self._raises = raises
        self._on_run = on_run

    def run_tenant_erasure(self, plan: TenantErasurePlan, *, pseudonymize: Callable[[str], str]) -> TenantErasureReport:
        if self._on_run is not None:
            self._on_run()
        self.plans.append(plan)
        if self._raises is not None:
            raise self._raises
        self.pseudonyms = {key: pseudonymize(key) for key in self._account_keys}
        return TenantErasureReport(tenant_document_removed=True, unreached=list(self._unreached))


def tenant(key: str = "t-1", *, is_platform: bool = False, tenant_type: str = "organization") -> Tenant:
    return Tenant.model_validate(
        {
            "_key": key,
            "name": f"Garden {key}",
            "slug": key,
            "tenant_type": tenant_type,
            "owner_user_key": "owner-1",
            "is_platform": is_platform,
        }
    )


def tenant_service_for_deletion(
    *,
    existing: Tenant | None = None,
    executor: ITenantErasureExecutor | None = None,
    record_repo: ITenantErasureRepository | None = None,
    salt: str = SALT,
    **overrides: Any,
) -> TenantService:
    """A ``TenantService`` wired for deletion the way ``get_tenant_service`` wires it."""
    tenant_repo = MagicMock()
    tenant_repo.get_by_key.return_value = existing if existing is not None else tenant()
    kwargs: dict[str, Any] = {
        "tenant_repo": tenant_repo,
        "membership_repo": authorizing_membership_repo(),
        "invitation_repo": MagicMock(),
        "assignment_repo": MagicMock(),
        "tenant_engine": MagicMock(),
        "membership_engine": MagicMock(),
        "invitation_engine": MagicMock(),
        "tenant_erasure_executor": executor if executor is not None else RecordingTenantErasureExecutor(),
        "tenant_erasure_repo": record_repo if record_repo is not None else FakeTenantErasureRepository(),
        "tombstone_salt": salt,
        "observation_repo": MagicMock(**{"delete_by_tenant.return_value": 0}),
    }
    kwargs.update(overrides)
    return TenantService(**kwargs)
