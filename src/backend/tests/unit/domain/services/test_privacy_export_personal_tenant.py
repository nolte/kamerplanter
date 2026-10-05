"""#2135 (MT-039) — the export walk restricts the personal-tenant sources to the subject's *own* personal tenants.

The repository's ``tenant_keys`` argument is the set a source is bounded by. For an
account source (``tenant_scoped``) that is every tenant the subject is a member of; for
a personal-tenant source it must be the personal tenants the subject **owns**
(``TenantService.personal_tenant_keys_of``) — never an organisation they are a member of,
never somebody else's personal garden they were invited into.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock

import pytest

from app.domain.interfaces.personal_data_repository import IPersonalDataRepository
from app.domain.models.membership import Membership
from app.domain.models.privacy import DataExportRequest, DataSourceDefinition
from tests.unit.domain.services.test_privacy_export_bundle import (
    FIXTURE_ROWS,
    USER,
    _download_text,
    _InMemoryStorage,
    _make_service,
)

PERSONAL = "t-personal-owned"
ORG = "t-org-member"
FOREIGN_PERSONAL = "t-personal-of-someone-else"


class _RecordingRepo(IPersonalDataRepository):
    def __init__(self) -> None:
        self.bounds: dict[tuple[str, str | None, bool], list[str]] = {}

    def collect_for_user(
        self, source: DataSourceDefinition, user_key: str, tenant_keys, *, tombstone=None
    ) -> list[dict[str, Any]]:
        key = (source.collection, source.filter_field, source.personal_tenant_scope is not None)
        self.bounds[key] = list(tenant_keys)
        if source.personal_tenant_scope is not None and source.collection == "sites":
            return [{"name": "Balkon", "gps_coordinates": [52.52, 13.405]}]
        return [dict(row) for row in FIXTURE_ROWS.get(source.collection, [])]


def _service(repo: _RecordingRepo):  # type: ignore[no-untyped-def]
    memberships = MagicMock()
    memberships.list_by_user.return_value = [
        Membership(user_key=USER, tenant_key=PERSONAL),
        Membership(user_key=USER, tenant_key=ORG),
        Membership(user_key=USER, tenant_key=FOREIGN_PERSONAL),
    ]
    tenants = MagicMock()
    tenants.personal_tenant_keys_of.return_value = [PERSONAL]
    export = DataExportRequest(key="exp-1", user_key=USER, status="pending", requested_at=datetime.now(UTC))
    storage = _InMemoryStorage()
    svc = _make_service(export, storage, repo, membership_repo=memberships, tenant_service=tenants)
    return svc, tenants


@pytest.mark.asyncio
async def test_personal_tenant_sources_are_bounded_by_the_owned_personal_tenants_only() -> None:
    repo = _RecordingRepo()
    svc, tenants = _service(repo)

    await svc.process_data_export("exp-1")

    tenants.personal_tenant_keys_of.assert_called_once_with(USER)
    personal = {k: v for k, v in repo.bounds.items() if k[2]}
    assert personal, "no personal-tenant source was walked"
    assert all(bound == [PERSONAL] for bound in personal.values()), personal
    # the account sources keep every membership as their bound (#1662 SCR-001)
    assert repo.bounds[("tasks", "assigned_to_user_key", False)] == [PERSONAL, ORG, FOREIGN_PERSONAL]


@pytest.mark.asyncio
async def test_the_bundle_carries_the_home_coordinates() -> None:
    repo = _RecordingRepo()
    svc, _tenants = _service(repo)

    await svc.process_data_export("exp-1")
    bundle = json.loads(await _download_text(svc))

    (site,) = [s for s in bundle["sections"] if s["collection"] == "sites"]
    assert site["records"] == [{"name": "Balkon", "gps_coordinates": [52.52, 13.405]}]
