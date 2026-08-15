"""Substrates and batches are tenant-scoped (#1195).

Before this, `/api/v1/substrates` carried exactly one dependency across all 15
routes — `get_current_user`. No tenant context, no `require_permission`, no
platform-admin check. Any authenticated user of the instance could read, edit and
delete **every tenant's batches** and the shared catalogue.

Two different scoping rules apply, and conflating them is the easy mistake:

* **`Substrate` is a hybrid catalogue** — the seeded base media (`tenant_key ==
  ""`) plus a tenant's own mixes. Reads take the *union*. A strict filter here
  would blank the seeded catalogue for every real tenant, which is #324 in its
  other direction.
* **`SubstrateBatch` is strictly owned** — there is no global batch to share, so
  reads filter on equality. Admitting `""` would hand every caller the rows the
  `v0043` backfill could not attribute.

The tests are weighted toward the refusals, because a scoping change passes its
happy-path test just as well when it scopes nothing.
"""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.substrates.router import router as substrates_router
from app.common import auth as auth_mod
from app.common.dependencies import get_substrate_service
from app.common.enums import TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError, NotFoundError
from app.domain.models.substrate import Substrate, SubstrateBatch
from app.domain.models.tenant_context import TenantContext
from app.domain.services.substrate_service import SubstrateService

_OWN = "tenant_own"
_FOREIGN = "tenant_foreign"

_GLOBAL_MEDIUM = Substrate(key="sub_global", name_de="Light-Mix", tenant_key="")
_OWN_MIX = Substrate(key="sub_own", name_de="Eigener Mix", tenant_key=_OWN, is_mix=True)
_FOREIGN_MIX = Substrate(key="sub_foreign", name_de="Fremder Mix", tenant_key=_FOREIGN, is_mix=True)

_OWN_BATCH = SubstrateBatch(
    key="batch_own",
    batch_id="B-1",
    substrate_key="sub_global",
    volume_liters=50,
    mixed_on=date(2026, 5, 1),
    tenant_key=_OWN,
)
_FOREIGN_BATCH = SubstrateBatch(
    key="batch_foreign",
    batch_id="B-2",
    substrate_key="sub_global",
    volume_liters=50,
    mixed_on=date(2026, 5, 1),
    tenant_key=_FOREIGN,
)
#: The row `v0043` could not attribute. It must be visible to nobody in full mode.
_UNATTRIBUTED_BATCH = SubstrateBatch(
    key="batch_orphan", batch_id="B-3", substrate_key="sub_global", volume_liters=50, mixed_on=date(2026, 5, 1)
)

_ALL_SUBSTRATES = [_GLOBAL_MEDIUM, _OWN_MIX, _FOREIGN_MIX]
_ALL_BATCHES = [_OWN_BATCH, _FOREIGN_BATCH, _UNATTRIBUTED_BATCH]


class _Repo:
    """Applies the two predicates in Python, so the *service* gates are what is measured.

    The AQL itself is pinned separately; here the subject is which rows the
    service admits and which writes it refuses.
    """

    def __init__(self) -> None:
        self.created: list[object] = []
        self.updated: list[object] = []
        self.deleted: list[str] = []

    def get_all_substrates(self, offset=0, limit=50, query=None, *, tenant_key=None):
        if tenant_key is None:
            rows = list(_ALL_SUBSTRATES)
        else:
            rows = [s for s in _ALL_SUBSTRATES if s.tenant_key in (tenant_key, "")]
        return rows, len(rows)

    def get_substrate_or_raise(self, key):
        found = next((s for s in _ALL_SUBSTRATES if s.key == key), None)
        if found is None:
            raise NotFoundError("Substrate", key)
        return found.model_copy(deep=True)

    def get_batch_or_raise(self, key):
        found = next((b for b in _ALL_BATCHES if b.key == key), None)
        if found is None:
            raise NotFoundError("SubstrateBatch", key)
        return found.model_copy(deep=True)

    def get_batches_by_substrate(self, substrate_key, *, tenant_key=None):
        rows = [b for b in _ALL_BATCHES if b.substrate_key == substrate_key]
        if tenant_key is None:
            return rows
        return [b for b in rows if b.tenant_key == tenant_key]

    def create_substrate(self, substrate):
        self.created.append(substrate)
        return substrate

    def update_substrate(self, key, substrate):
        self.updated.append(substrate)
        return substrate

    def delete_substrate(self, key):
        self.deleted.append(key)
        return True

    def create_batch(self, batch):
        self.created.append(batch)
        return batch

    def update_batch(self, key, batch):
        self.updated.append(batch)
        return batch

    def delete_batch(self, key):
        self.deleted.append(key)
        return True


def _client(
    repo: _Repo,
    *,
    tenant: str = _OWN,
    role: TenantRole = TenantRole.LEAD,
    is_platform_admin: bool = False,
) -> TestClient:
    app = FastAPI()
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.include_router(substrates_router, prefix="/api/v1")
    app.dependency_overrides[auth_mod.get_current_user] = lambda: SimpleNamespace(key="u1", account_type="user")
    app.dependency_overrides[get_substrate_service] = lambda: SubstrateService(repo)  # type: ignore[arg-type]
    app.dependency_overrides[auth_mod.get_active_tenant_key] = lambda: tenant
    app.dependency_overrides[auth_mod.get_creating_tenant_key] = lambda: tenant
    app.dependency_overrides[auth_mod.get_is_platform_admin] = lambda: is_platform_admin
    app.dependency_overrides[auth_mod.get_active_tenant_context] = lambda: TenantContext(
        tenant_key=tenant, tenant_slug="t", user_key="u1", role=role, admin_scopes=[]
    )
    return TestClient(app)


@pytest.fixture
def repo() -> _Repo:
    return _Repo()


# ── the catalogue: hybrid, so the union must hold in BOTH directions ─────────


def test_the_catalogue_lists_global_media_and_own_mixes(repo: _Repo) -> None:
    names = {s["key"] for s in _client(repo).get("/api/v1/substrates").json()}

    assert names == {"sub_global", "sub_own"}


def test_the_catalogue_does_not_list_a_foreign_mix(repo: _Repo) -> None:
    assert "sub_foreign" not in {s["key"] for s in _client(repo).get("/api/v1/substrates").json()}


def test_the_seeded_media_survive_for_a_real_tenant(repo: _Repo) -> None:
    """#324 in its other direction.

    A strict `== @tenant_key` would pass the leak test above and blank the whole
    seeded catalogue for every tenant — a regression that looks like a fix.
    """
    assert "sub_global" in {s["key"] for s in _client(repo).get("/api/v1/substrates").json()}


def test_a_foreign_mix_is_404_by_key(repo: _Repo) -> None:
    assert _client(repo).get("/api/v1/substrates/sub_foreign").status_code == 404


def test_an_absent_key_answers_exactly_like_a_foreign_one(repo: _Repo) -> None:
    """Ownership hiding: the by-key route must not become an existence oracle."""
    client = _client(repo)

    foreign = client.get("/api/v1/substrates/sub_foreign")
    absent = client.get("/api/v1/substrates/sub_does_not_exist")

    assert foreign.status_code == absent.status_code == 404


# ── the catalogue: write gates ───────────────────────────────────────────────


def test_a_viewer_may_not_create(repo: _Repo) -> None:
    response = _client(repo, role=TenantRole.VIEWER).post("/api/v1/substrates", json={"name_de": "X", "name_en": "X"})

    assert response.status_code == 403, response.text
    assert repo.created == []


def test_a_create_is_stamped_with_the_active_tenant_not_the_body(repo: _Repo) -> None:
    """Ownership is server-side. A client naming its own `tenant_key` could write
    into another tenant's catalogue — the #1000 smuggling vector."""
    _client(repo).post("/api/v1/substrates", json={"name_de": "X", "name_en": "X", "tenant_key": _FOREIGN})

    assert repo.created[0].tenant_key == _OWN


def test_an_ordinary_lead_may_not_edit_the_global_catalogue(repo: _Repo) -> None:
    """The #1120 rule: a row every tenant reads is curation, not tenant work."""
    response = _client(repo).put("/api/v1/substrates/sub_global", json={"name_de": "Umbenannt", "name_en": "Renamed"})

    assert response.status_code == 403, response.text
    assert repo.updated == []


def test_a_platform_admin_may_edit_the_global_catalogue(repo: _Repo) -> None:
    response = _client(repo, is_platform_admin=True).put(
        "/api/v1/substrates/sub_global", json={"name_de": "Umbenannt", "name_en": "Renamed"}
    )

    assert response.status_code == 200, response.text


def test_editing_an_own_mix_may_not_move_it_into_the_global_catalogue(repo: _Repo) -> None:
    """Ownership is assigned once. A full-replace update that could rewrite it
    would let a tenant push its mix into the shared catalogue — or claim a global
    medium — without any gate noticing."""
    _client(repo).put("/api/v1/substrates/sub_own", json={"name_de": "Neu", "name_en": "New"})

    assert repo.updated[0].tenant_key == _OWN


def test_deleting_a_foreign_mix_is_404_and_deletes_nothing(repo: _Repo) -> None:
    response = _client(repo).delete("/api/v1/substrates/sub_foreign")

    assert response.status_code == 404, response.text
    assert repo.deleted == []


def test_a_grower_may_not_delete_an_own_mix(repo: _Repo) -> None:
    """Delete is the irreversibility boundary — lead only (REQ-049 §2.3)."""
    response = _client(repo, role=TenantRole.GROWER).delete("/api/v1/substrates/sub_own")

    assert response.status_code == 403, response.text
    assert repo.deleted == []


# ── batches: strict, with no global arm at all ───────────────────────────────


def test_batches_of_another_tenant_are_not_listed(repo: _Repo) -> None:
    keys = {b["key"] for b in _client(repo).get("/api/v1/substrates/sub_global/batches").json()}

    assert keys == {"batch_own"}


def test_an_unattributed_batch_is_listed_for_nobody(repo: _Repo) -> None:
    """The `v0043` residue.

    A batch whose owner could not be derived carries `tenant_key == ""`. Were the
    batch read to reuse the *catalogue's* union — the obvious copy-paste — that
    empty key would read as "global" and hand every tenant somebody's unattributed
    batch. Strict equality is what keeps it invisible instead.
    """
    keys = {b["key"] for b in _client(repo).get("/api/v1/substrates/sub_global/batches").json()}

    assert "batch_orphan" not in keys


def test_a_foreign_batch_is_404_by_key(repo: _Repo) -> None:
    assert _client(repo).get("/api/v1/substrates/batches/batch_foreign").status_code == 404


def test_a_foreign_batch_cannot_be_updated(repo: _Repo) -> None:
    response = _client(repo).put(
        "/api/v1/substrates/batches/batch_foreign",
        json={"batch_id": "B-2", "substrate_key": "sub_global", "volume_liters": 1, "mixed_on": "2026-05-01"},
    )

    assert response.status_code == 404, response.text
    assert repo.updated == []


def test_a_foreign_batch_cannot_be_deleted(repo: _Repo) -> None:
    """The single worst call before #1195: any authenticated user could delete
    any tenant's batch."""
    response = _client(repo).delete("/api/v1/substrates/batches/batch_foreign")

    assert response.status_code == 404, response.text
    assert repo.deleted == []


def test_a_created_batch_is_stamped_with_the_active_tenant(repo: _Repo) -> None:
    _client(repo).post(
        "/api/v1/substrates/batches",
        json={
            "batch_id": "B-9",
            "substrate_key": "sub_global",
            "volume_liters": 40,
            "mixed_on": "2026-06-01",
            "tenant_key": _FOREIGN,
        },
    )

    assert repo.created[0].tenant_key == _OWN


def test_a_batch_cannot_be_hung_off_a_foreign_mix(repo: _Repo) -> None:
    response = _client(repo).post(
        "/api/v1/substrates/batches",
        json={
            "batch_id": "B-9",
            "substrate_key": "sub_foreign",
            "volume_liters": 40,
            "mixed_on": "2026-06-01",
        },
    )

    assert response.status_code == 404, response.text
    assert repo.created == []


# ── the mix paths, including the one that persists nothing ───────────────────


def test_a_mix_is_owned_by_the_tenant_that_made_it(repo: _Repo) -> None:
    """Operator decision on #1098: a garden that blends its own medium keeps it."""
    _client(repo).post(
        "/api/v1/substrates/mix",
        json={
            "name_de": "50/50",
            "name_en": "50/50",
            "components": [
                {"substrate_key": "sub_global", "fraction": 0.5},
                {"substrate_key": "sub_global", "fraction": 0.5},
            ],
        },
    )

    assert repo.created[0].tenant_key == _OWN


def test_a_mix_cannot_be_built_from_a_foreign_component(repo: _Repo) -> None:
    response = _client(repo).post(
        "/api/v1/substrates/mix",
        json={
            "name_de": "X",
            "name_en": "X",
            "components": [
                {"substrate_key": "sub_global", "fraction": 0.5},
                {"substrate_key": "sub_foreign", "fraction": 0.5},
            ],
        },
    )

    assert response.status_code == 404, response.text
    assert repo.created == []


def test_the_preview_is_scoped_although_it_persists_nothing(repo: _Repo) -> None:
    """A preview that resolved components unscoped would report a foreign
    tenant's pH, EC, CEC and composition back to the caller — a read of their
    data wearing a calculation as cover."""
    response = _client(repo).post(
        "/api/v1/substrates/preview-mix",
        json={
            "name_de": "X",
            "name_en": "X",
            "components": [
                {"substrate_key": "sub_global", "fraction": 0.5},
                {"substrate_key": "sub_foreign", "fraction": 0.5},
            ],
        },
    )

    assert response.status_code == 404, response.text


def test_an_unattributed_batch_is_not_readable_by_key_either(repo: _Repo) -> None:
    """The list and the by-key read are *separate* filters, and only one of them
    is in the repository.

    Found by counterfactual: switching the by-key check from strict equality to
    the catalogue's union — the obvious copy-paste between two methods a dozen
    lines apart — left every test above green, because they all go through the
    listing. A `tenant_key == ""` batch would then be readable by every tenant,
    which is precisely the state `v0043` leaves those rows in and precisely what
    the strictness is for.
    """
    response = _client(repo).get("/api/v1/substrates/batches/batch_orphan")

    assert response.status_code == 404, response.text


def test_the_batch_query_filters_on_equality_and_never_admits_the_empty_key() -> None:
    """The listing's own predicate, pinned at the source.

    Every listing test above runs against the double's Python filter, so it
    asserts what the *service* does with the rows it is handed — not what AQL asks
    for. This reads the query text, so a repository that quietly grew an
    `OR doc.tenant_key == ""` arm cannot pass by having a faithful double.
    """
    import inspect

    from app.data_access.arango.substrate_repository import ArangoSubstrateRepository

    raw = inspect.getsource(ArangoSubstrateRepository.get_batches_by_substrate)
    # Backslashes stripped before the comparison. Without this the check misses a
    # global arm written as an escaped literal inside the AQL string — found by
    # counterfactual: injecting `OR doc.tenant_key == \"\"` left this test green,
    # which made the guard against a global arm itself the thing with a hole.
    source = raw.replace("\\", "")

    assert "doc.tenant_key == @tenant_key" in source
    assert '== ""' not in source, "the batch read grew a global arm; batches have no global rows"
    assert "tenant_union_predicate" not in source, (
        "the batch read now uses the catalogue's union — that admits the rows v0043 could not attribute"
    )
