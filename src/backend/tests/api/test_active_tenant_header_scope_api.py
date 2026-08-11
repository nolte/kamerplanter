"""What the ``X-Active-Tenant`` header actually makes visible and writable (#1091 R4).

The #324 guard for the header mechanism, end-to-end through real HTTP. Every
other module around this one pins *one* link of the chain:

* ``tests/unit/common/test_active_tenant_header.py`` — the resolver's decisions;
* ``tests/api/test_active_tenant_header_api.py`` — that the header reaches the
  resolver from the wire, that both invalid classes answer one indistinguishable
  403, and that the header is documented on every consuming operation;
* ``tests/api/test_species_tenant_scope_api.py`` / ``test_cultivar_tenant_scope_api.py``
  — that a *given* tenant key is threaded into the service (they override
  ``get_active_tenant_key`` outright, so no header is involved);
* ``tests/api/test_species_authorization_api.py`` / ``test_cultivar_authorization_api.py``
  — the create/update/delete role matrix for a *given* role context.

None of them can fail if the chain is right at every link and wrong as a whole.
This module closes that gap: the **real** resolver and the **real**
:class:`SpeciesService` run behind fake repositories, so a request that carries
the header produces the rows, the refusals and the ownership stamps a real caller
would get. Concretely, R4's two halves:

* **reads** — an org member with a valid header sees the global catalogue plus the
  *org's* rows; a foreign tenant's row is absent from every list and answers 404
  (never 403) by key; and their **own personal** rows are gone while the header is
  set. The header *switches* context, it never *unions* — the direction that is
  easiest to get wrong, because a union looks generous rather than broken and
  every "own rows are visible" assertion still passes;
* **writes** — a create is stamped with the **active** tenant, asserted on the
  persisted model (``SpeciesResponse``/``CultivarResponse`` deliberately do not
  serve ``tenant_key``, so the response cannot answer this), and an org **viewer**
  reaching the same route through the header is refused (SEC-005, #1113) by the
  role of their membership *in the org*, not the lead role of their personal
  tenant.

Doubled vs real
---------------
Real: the whole request path — ``_resolve_active_tenant``,
``get_active_tenant_key`` / ``get_creating_tenant_key`` / ``get_active_tenant_context``
/ ``get_is_platform_admin``, all four consuming routers, and ``SpeciesService``
with its hybrid-catalogue scoping and its role gates.
Doubled: the authenticated user, ``TenantService`` (slug→tenant + memberships),
the species/cultivar repository, the botanical-family repository and the graph
repository — the four collaborators that would otherwise be ArangoDB.

That single ``get_tenant_service`` override is what keeps the POST routes
datastore-free here. The sibling modules override ``get_creating_tenant_key`` and
therefore need all three of ``get_creating_tenant_key`` /
``get_active_tenant_context`` / ``get_is_platform_admin`` (R-8; two of three is a
loud ``TierDatabaseAccessError``). This module overrides none of them on purpose —
the header must drive them — and instead doubles the one collaborator all three
resolve through.

Traceability: no TC-ID exists for this strand; the requirement artifact
``project/requirements/active-tenant-resolution.md`` carries R-IDs. Covered here:
**R4** (both halves), **R3** (role from the active tenant's membership) and
**R-1** (the companion-planting router is the fourth resolver consumer).
"""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import Response

from app.api.v1.botanical_families.router import router as families_router
from app.api.v1.companion_planting.router import router as companion_router
from app.api.v1.cultivars.router import router as cultivars_router
from app.api.v1.species.router import router as species_router
from app.common.auth import ACTIVE_TENANT_HEADER, get_current_user
from app.common.dependencies import get_family_repo, get_species_service, get_tenant_service
from app.common.enums import AdminScope, DataOrigin, TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError, NotFoundError
from app.config.settings import settings
from app.domain.models.botanical_family import BotanicalFamily
from app.domain.models.species import Cultivar, Species
from app.domain.services.species_service import SpeciesService

# ── The world under test ─────────────────────────────────────────────────────

_USER = "user_1"
#: An authenticated caller with no personal tenant and no membership anywhere —
#: the "anonymous / no context" class that must resolve to ``""`` (global-only).
_USER_WITHOUT_TENANT = "user_without_tenant"

_PERSONAL = SimpleNamespace(key="tenant_personal_1", slug="user-1-garden")
_ORG = SimpleNamespace(key="tenant_org_1", slug="green-club")
_FOREIGN = SimpleNamespace(key="tenant_foreign", slug="foreign-club")

_ORG_HEADER = {ACTIVE_TENANT_HEADER: _ORG.slug}

#: Scientific names, used as the readable identity of a row in every set assertion.
_GLOBAL_ROSE = "Rosa canina"
_ORG_BASIL = "Ocimum basilicum"
_ORG_SAGE = "Salvia officinalis"
_PERSONAL_MINT = "Mentha spicata"
_FOREIGN_HEMP = "Cannabis sativa"

#: Two org species in one family and one personal species in the *same* family, so
#: the botanical-family counts differ per active tenant (2 vs 1). With one row each
#: the count assertion would hold whichever tenant the route resolved.
_SPECIES = [
    Species(_key="sp_global", scientific_name=_GLOBAL_ROSE, tenant_key="", family_key="fam_rosaceae"),
    Species(_key="sp_org", scientific_name=_ORG_BASIL, tenant_key=_ORG.key, family_key="fam_lamiaceae"),
    Species(_key="sp_org_2", scientific_name=_ORG_SAGE, tenant_key=_ORG.key, family_key="fam_lamiaceae"),
    Species(_key="sp_personal", scientific_name=_PERSONAL_MINT, tenant_key=_PERSONAL.key, family_key="fam_lamiaceae"),
    Species(_key="sp_foreign", scientific_name=_FOREIGN_HEMP, tenant_key=_FOREIGN.key, family_key="fam_cannabaceae"),
]

#: All four hang off the *global* species, so one URL reaches every ownership class
#: and the cultivar assertions isolate the tenant dimension from the parent-species
#: scoping (which ``test_cultivar_authorization_api.py`` owns).
_GLOBAL_CULTIVAR = "Genovese"
_ORG_CULTIVAR = "Org Basil"
_PERSONAL_CULTIVAR = "Personal Mint"
_FOREIGN_CULTIVAR = "Foreign Hemp"

_CULTIVARS = [
    Cultivar(_key="cv_global", name=_GLOBAL_CULTIVAR, species_key="sp_global", tenant_key=""),
    Cultivar(_key="cv_org", name=_ORG_CULTIVAR, species_key="sp_global", tenant_key=_ORG.key),
    Cultivar(_key="cv_personal", name=_PERSONAL_CULTIVAR, species_key="sp_global", tenant_key=_PERSONAL.key),
    Cultivar(_key="cv_foreign", name=_FOREIGN_CULTIVAR, species_key="sp_global", tenant_key=_FOREIGN.key),
]

_FAMILIES = [
    BotanicalFamily(_key="fam_rosaceae", name="Rosaceae"),
    BotanicalFamily(_key="fam_lamiaceae", name="Lamiaceae"),
    BotanicalFamily(_key="fam_cannabaceae", name="Cannabaceae"),
]

_SPECIES_BODY = {"scientific_name": "Thymus vulgaris"}
_CULTIVAR_BODY = {"name": "New Cultivar", "species_key": "sp_global"}


# ── The four doubled collaborators ───────────────────────────────────────────


class _FakeTenantService:
    """Slug→tenant and membership lookup, without ArangoDB.

    Extends the double of ``test_active_tenant_header_api.py``: same three
    tenants, same ``NotFoundError`` contract on an unknown slug (the 404 the
    resolver has to convert into a 403), but the caller's role **in the org** is a
    constructor argument. This module needs the same person as a grower (who may
    create) and as a viewer (who may not) acting through the very same header.

    Two properties are load-bearing beyond the lookups:

    * the caller is a ``LEAD`` in their personal tenant and something else in the
      org, so "the role came from the active tenant" is observable rather than
      assumed (R3);
    * there is no membership in the technical ``platform`` tenant, so
      ``get_is_platform_admin`` resolves ``False`` through the real code path and
      the role gate is actually reached instead of being bypassed.
    """

    def __init__(self, *, org_role: TenantRole) -> None:
        self._by_slug = {tenant.slug: tenant for tenant in (_PERSONAL, _ORG, _FOREIGN)}
        self._memberships = {
            (_USER, _PERSONAL.key): SimpleNamespace(
                role=TenantRole.LEAD, admin_scopes=[AdminScope.MANAGEMENT], is_active=True
            ),
            (_USER, _ORG.key): SimpleNamespace(role=org_role, admin_scopes=[], is_active=True),
        }

    def get_personal_tenant(self, user_key: str) -> SimpleNamespace | None:
        return _PERSONAL if user_key == _USER else None

    def get_tenant_by_slug(self, slug: str) -> SimpleNamespace:
        tenant = self._by_slug.get(slug)
        if tenant is None:
            raise NotFoundError("tenants", slug)
        return tenant

    def get_membership(self, user_key: str, tenant_key: str) -> SimpleNamespace | None:
        return self._memberships.get((user_key, tenant_key))


class _FakeSpeciesRepo:
    """The species/cultivar repository, modelling the hybrid-catalogue union.

    The union is the production predicate
    (:func:`~app.data_access.arango.tenant_scope.tenant_union_predicate`) written
    in Python: the caller's own rows plus the global ones (``tenant_key == ""`` or
    ``null``), never a foreign tenant's; ``tenant_key is None`` is the unscoped
    system-context read the service uses for its ownership gates. Getting this
    wrong in the double would make every visibility assertion below certify the
    double instead of the route, so it is written once, here, and used by the
    family repository too.
    """

    def __init__(self) -> None:
        self._species = {s.key: s.model_copy(deep=True) for s in _SPECIES}
        self._cultivars = {c.key: c.model_copy(deep=True) for c in _CULTIVARS}
        #: The persisted rows — what the stamping assertions read. The response
        #: cannot answer them: neither response schema serves ``tenant_key``.
        self.created: list[Species] = []
        self.created_cultivars: list[Cultivar] = []

    @staticmethod
    def _is_visible(row: Species | Cultivar, tenant_key: str | None) -> bool:
        if tenant_key is None:
            return True
        return row.tenant_key in (tenant_key, "", None)

    # ── reads ────────────────────────────────────────────────────────────────

    def get_all(self, offset: int = 0, limit: int = 50, *, tenant_key: str | None = None) -> tuple[list[Species], int]:
        rows = [s for s in self._species.values() if self._is_visible(s, tenant_key)]
        return rows[offset : offset + limit], len(rows)

    def get_or_raise(self, key: str) -> Species:
        species = self._species.get(key)
        if species is None:
            raise NotFoundError("Species", key)
        return species

    def get_cultivars(self, species_key: str, *, tenant_key: str | None = None) -> list[Cultivar]:
        return [c for c in self._cultivars.values() if c.species_key == species_key and self._is_visible(c, tenant_key)]

    def get_cultivar_or_raise(self, key: str) -> Cultivar:
        cultivar = self._cultivars.get(key)
        if cultivar is None:
            raise NotFoundError("Cultivar", key)
        return cultivar

    def species_in_family(self, family_key: str, tenant_key: str | None) -> list[Species]:
        """The rows a family's species listing and count are both derived from."""
        return [s for s in self._species.values() if s.family_key == family_key and self._is_visible(s, tenant_key)]

    # ── the create paths ─────────────────────────────────────────────────────

    def get_by_normalized_scientific_name(self, name: str) -> Species | None:
        return None

    def find_synonym_match_candidates(self, species: Species) -> list[Species]:
        return []

    def upsert_by_normalized_scientific_name(self, species: Species) -> Species:
        self.created.append(species)
        return species.model_copy(update={"key": "sp_new"})

    def create_cultivar(self, cultivar: Cultivar) -> Cultivar:
        self.created_cultivars.append(cultivar)
        return cultivar.model_copy(update={"key": "cv_new"})


class _FakeFamilyRepo:
    """Botanical families, with their species counts derived from the same catalogue.

    Deliberately *derived* rather than hard-coded: the count route's whole claim is
    that it counts the species the caller can see, so a double returning a fixed
    number per family would make the count assertions unfalsifiable.
    """

    def __init__(self, species_repo: _FakeSpeciesRepo) -> None:
        self._species_repo = species_repo
        self._families = {f.key: f for f in _FAMILIES}

    def get_all_families(self, offset: int = 0, limit: int = 50) -> tuple[list[BotanicalFamily], int]:
        rows = list(self._families.values())
        return rows[offset : offset + limit], len(rows)

    def get_by_key(self, key: str) -> BotanicalFamily | None:
        return self._families.get(key)

    def get_species_by_family(self, family_key: str, *, tenant_key: str | None = None) -> list[Species]:
        return self._species_repo.species_in_family(family_key, tenant_key)

    def get_species_count_by_family(self, family_key: str, *, tenant_key: str | None = None) -> int:
        return len(self.get_species_by_family(family_key, tenant_key=tenant_key))

    def get_species_counts_by_family(self, *, tenant_key: str | None = None) -> dict[str, int]:
        # Families with no visible species are absent from the map, exactly as the
        # real repository leaves them absent — that is what the route's ``.get(k, 0)``
        # default exists for, so the double must exercise it rather than paper over it.
        counts = {key: self.get_species_count_by_family(key, tenant_key=tenant_key) for key in self._families}
        return {key: count for key, count in counts.items() if count}


class _FakeGraphRepo:
    """Companion edges — global reference data, with no tenant dimension at all.

    Returns one fixed edge for every anchor so that *reaching* the graph produces
    an assertable payload. The seam under test is the anchor **resolution**, which
    happens in ``SpeciesService.get_species`` before this object is ever touched.
    """

    _EDGE_SPECIES = {"_key": "sp_global", "scientific_name": _GLOBAL_ROSE, "common_names": ["Hundsrose"]}

    def get_compatible_species(self, species_key: str) -> list[dict[str, Any]]:
        return [{"species": self._EDGE_SPECIES, "score": 0.8}]

    def get_incompatible_species(self, species_key: str) -> list[dict[str, Any]]:
        return [{"species": self._EDGE_SPECIES, "reason": "allelopathy"}]


# ── Harness ──────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class _Harness:
    client: TestClient
    species_repo: _FakeSpeciesRepo


def _harness(*, org_role: TenantRole = TenantRole.GROWER, user_key: str = _USER) -> _Harness:
    """Mount the four resolver-consuming routers over the doubled collaborators.

    Note what is *not* overridden: ``get_active_tenant_key``,
    ``get_creating_tenant_key``, ``get_active_tenant_context`` and
    ``get_is_platform_admin`` all run for real, which is the entire point — the
    request header has to travel the production path to reach the query scope and
    the ownership stamp.
    """
    app = FastAPI()
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    for router in (species_router, cultivars_router, families_router, companion_router):
        app.include_router(router, prefix="/api/v1")

    species_repo = _FakeSpeciesRepo()
    family_repo = _FakeFamilyRepo(species_repo)
    service = SpeciesService(species_repo, graph_repo=_FakeGraphRepo())  # type: ignore[arg-type]
    tenant_service = _FakeTenantService(org_role=org_role)

    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(key=user_key)
    app.dependency_overrides[get_tenant_service] = lambda: tenant_service
    app.dependency_overrides[get_species_service] = lambda: service
    app.dependency_overrides[get_family_repo] = lambda: family_repo
    return _Harness(client=TestClient(app), species_repo=species_repo)


@pytest.fixture(autouse=True)
def _full_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pin ``full`` mode for every test in this module.

    Not cosmetic: in ``light`` mode (REQ-027) ``is_platform_admin`` returns ``True``
    for everyone, which bypasses the create role gate. A module that inherited the
    ambient mode would report the viewer as refused or admitted depending on the
    environment it ran in — and would go green in exactly the deployment where the
    gate is disarmed.
    """
    monkeypatch.setattr(settings, "kamerplanter_mode", "full")


# ── Readers ──────────────────────────────────────────────────────────────────
#
# Each one fails loudly rather than returning an empty value for "I could not
# look" (T3): a refused request read as "the catalogue is empty" would satisfy
# every absence assertion in this file.


def _species_names(response: Response) -> set[str]:
    """Scientific names carried by a species-list response."""
    assert response.status_code == 200, response.text
    return {item["scientific_name"] for item in response.json()["items"]}


def _cultivar_names(response: Response) -> set[str]:
    """Names carried by a cultivar-list response."""
    assert response.status_code == 200, response.text
    return {item["name"] for item in response.json()}


def _family_counts(response: Response) -> dict[str, int]:
    """Family name → served species count, for the whole page."""
    assert response.status_code == 200, response.text
    rows = response.json()
    assert rows, "the family list came back empty — the per-family counts would assert nothing"
    return {row["name"]: row["species_count"] for row in rows}


def _comparable(body: dict[str, Any]) -> dict[str, Any]:
    """The error body minus its four per-occurrence fields (A-11 hand-over).

    ``error_id`` is a fresh UUID per raise, ``timestamp`` is stamped at response
    time, and ``path``/``method`` describe the request rather than the answer.
    Everything that is left is the part a caller could use to tell two refusals
    apart.
    """
    return {k: v for k, v in body.items() if k not in ("error_id", "timestamp", "path", "method")}


# ── R4 reads: the species list ───────────────────────────────────────────────


def test_species_list_with_the_org_header_serves_global_plus_org_and_nothing_else():
    # AC 1, 2 and 3 in one both-direction assertion: what is served, and the two
    # classes that must not be (#324 foreign, R4 personal-while-switched).
    harness = _harness()

    response = harness.client.get("/api/v1/species", headers=_ORG_HEADER)

    names = _species_names(response)
    assert names == {_GLOBAL_ROSE, _ORG_BASIL, _ORG_SAGE}
    assert _FOREIGN_HEMP not in names
    assert _PERSONAL_MINT not in names
    assert response.json()["total"] == 3


def test_species_list_without_the_header_serves_global_plus_personal_and_nothing_else():
    # AC 4: the pre-#1091 answer, unregressed — and the counterpart that makes the
    # test above a *switch* rather than a coincidence. The org rows are as absent
    # here as the personal ones are there.
    harness = _harness()

    response = harness.client.get("/api/v1/species")

    names = _species_names(response)
    assert names == {_GLOBAL_ROSE, _PERSONAL_MINT}
    assert _ORG_BASIL not in names
    assert _ORG_SAGE not in names
    assert _FOREIGN_HEMP not in names
    assert response.json()["total"] == 2


def test_a_caller_with_no_tenant_at_all_sees_exactly_the_global_catalogue():
    # AC 6: absence of context narrows to global-only ("" collapses the union) and
    # is never an error — the fail-safe direction, unchanged by the header work.
    harness = _harness(user_key=_USER_WITHOUT_TENANT)

    response = harness.client.get("/api/v1/species")

    names = _species_names(response)
    assert names == {_GLOBAL_ROSE}
    assert _PERSONAL_MINT not in names
    assert _ORG_BASIL not in names
    assert _FOREIGN_HEMP not in names


# ── R4 reads: species by key ─────────────────────────────────────────────────


def test_the_org_species_resolves_by_key_only_while_the_org_header_is_set():
    # AC 1 by key, stated as the difference the header makes.
    harness = _harness()

    with_header = harness.client.get("/api/v1/species/sp_org", headers=_ORG_HEADER)
    without_header = harness.client.get("/api/v1/species/sp_org")

    assert with_header.status_code == 200
    assert with_header.json()["scientific_name"] == _ORG_BASIL
    assert without_header.status_code == 404


def test_the_personal_species_stops_resolving_by_key_while_the_org_header_is_set():
    # AC 3, the direction most easily got wrong. Asserting both requests on the
    # *same* key is what makes the 404 mean "out of scope" instead of "no such
    # row": the first request proves the row is there and readable.
    harness = _harness()

    without_header = harness.client.get("/api/v1/species/sp_personal")
    with_header = harness.client.get("/api/v1/species/sp_personal", headers=_ORG_HEADER)

    assert without_header.status_code == 200
    assert without_header.json()["scientific_name"] == _PERSONAL_MINT
    assert with_header.status_code == 404
    assert with_header.json()["error_code"] == "ENTITY_NOT_FOUND"


def test_a_foreign_species_is_404_and_never_403_for_the_org_member():
    # AC 2. Paired with a row of the same shape the caller *may* read, so a route
    # that 404s everything cannot pass this.
    harness = _harness()

    foreign = harness.client.get("/api/v1/species/sp_foreign", headers=_ORG_HEADER)
    own = harness.client.get("/api/v1/species/sp_org", headers=_ORG_HEADER)

    assert foreign.status_code == 404
    assert foreign.json()["error_code"] == "ENTITY_NOT_FOUND"
    assert own.status_code == 200


def test_a_foreign_species_answers_the_same_404_whichever_tenant_the_caller_acts_in():
    # The by-key refusal must carry no signal about the caller's active context:
    # switching headers is free, so a body that differed would let an attacker
    # enumerate which tenant a row belongs to by trying each of their own.
    harness = _harness()

    in_the_org = harness.client.get("/api/v1/species/sp_foreign", headers=_ORG_HEADER)
    in_the_personal_tenant = harness.client.get("/api/v1/species/sp_foreign")

    assert in_the_org.status_code == in_the_personal_tenant.status_code == 404
    assert _comparable(in_the_org.json()) == _comparable(in_the_personal_tenant.json())
    assert in_the_org.json()["error_id"] != in_the_personal_tenant.json()["error_id"]


# ── R4 writes: the stamp binds the active tenant ─────────────────────────────


def test_species_create_stamps_the_active_tenant_and_the_stamp_moves_with_the_header():
    # AC 5, asserted on the *persisted* model: ``SpeciesResponse`` does not serve
    # ``tenant_key`` (operator decision Q4), so the response cannot answer this —
    # and a stamping bug would be invisible to any status-code assertion.
    harness = _harness(org_role=TenantRole.GROWER)

    with_header = harness.client.post("/api/v1/species", json=_SPECIES_BODY, headers=_ORG_HEADER)
    without_header = harness.client.post("/api/v1/species", json=_SPECIES_BODY)

    assert with_header.status_code == 201
    assert without_header.status_code == 201
    # Both directions in one comparison: the stamp is the org's with the header and
    # the personal one without it. A stamp that ignored the header would come out
    # as two personal keys, one that ignored the fallback as two org keys.
    assert [s.tenant_key for s in harness.species_repo.created] == [_ORG.key, _PERSONAL.key]
    assert [s.origin for s in harness.species_repo.created] == [DataOrigin.TENANT, DataOrigin.TENANT]


def test_cultivar_create_stamps_the_active_tenant_and_the_stamp_moves_with_the_header():
    # AC 5 / AC 7 for the cultivar create — the same property on the second write
    # surface the header binds.
    harness = _harness(org_role=TenantRole.GROWER)

    with_header = harness.client.post("/api/v1/species/sp_global/cultivars", json=_CULTIVAR_BODY, headers=_ORG_HEADER)
    without_header = harness.client.post("/api/v1/species/sp_global/cultivars", json=_CULTIVAR_BODY)

    assert with_header.status_code == 201
    assert without_header.status_code == 201
    assert [c.tenant_key for c in harness.species_repo.created_cultivars] == [_ORG.key, _PERSONAL.key]


def test_a_header_the_caller_may_not_use_stamps_nothing_at_all():
    # The read side of the two 403 classes is pinned in
    # ``test_active_tenant_header_api.py``; what only a *write* can show is that the
    # refusal lands before the stamp. A silent fallback would not surface as a 403
    # there — it would surface as a row quietly created in the personal catalogue.
    harness = _harness()

    response = harness.client.post("/api/v1/species", json=_SPECIES_BODY, headers={ACTIVE_TENANT_HEADER: _FOREIGN.slug})

    assert response.status_code == 403
    assert response.json()["error_code"] == "FORBIDDEN"
    assert harness.species_repo.created == []


# ── R5 end-to-end: the org viewer reaching the create routes via the header ──


def test_an_org_viewer_acting_through_the_header_is_refused_on_both_create_routes():
    # The attacker case A-3 gated on this package, now through the *real* resolver
    # chain: the role is read from the org membership the header selected, not from
    # an overridden context object.
    harness = _harness(org_role=TenantRole.VIEWER)

    species = harness.client.post("/api/v1/species", json=_SPECIES_BODY, headers=_ORG_HEADER)
    cultivar = harness.client.post("/api/v1/species/sp_global/cultivars", json=_CULTIVAR_BODY, headers=_ORG_HEADER)

    assert species.status_code == 403
    assert species.json()["error_code"] == "FORBIDDEN"
    assert cultivar.status_code == 403
    assert cultivar.json()["error_code"] == "FORBIDDEN"
    assert harness.species_repo.created == []
    assert harness.species_repo.created_cultivars == []


def test_the_same_org_viewer_may_still_create_in_their_own_personal_tenant():
    # The pair to the test above, and the R3 proof: the identical caller with the
    # identical body is a LEAD in their personal tenant. The 403 above is therefore
    # the role of the *active* tenant's membership — not a blanket refusal, and not
    # the personal-tenant role leaking into the org.
    harness = _harness(org_role=TenantRole.VIEWER)

    response = harness.client.post("/api/v1/species", json=_SPECIES_BODY)

    assert response.status_code == 201
    assert [s.tenant_key for s in harness.species_repo.created] == [_PERSONAL.key]


# ── AC 7: the cultivar catalogue ─────────────────────────────────────────────


def test_cultivar_list_with_the_org_header_serves_global_plus_org_and_nothing_else():
    harness = _harness()

    response = harness.client.get("/api/v1/species/sp_global/cultivars", headers=_ORG_HEADER)

    names = _cultivar_names(response)
    assert names == {_GLOBAL_CULTIVAR, _ORG_CULTIVAR}
    assert _FOREIGN_CULTIVAR not in names
    assert _PERSONAL_CULTIVAR not in names


def test_cultivar_list_without_the_header_serves_global_plus_personal_and_nothing_else():
    harness = _harness()

    response = harness.client.get("/api/v1/species/sp_global/cultivars")

    names = _cultivar_names(response)
    assert names == {_GLOBAL_CULTIVAR, _PERSONAL_CULTIVAR}
    assert _ORG_CULTIVAR not in names
    assert _FOREIGN_CULTIVAR not in names


def test_a_caller_with_no_tenant_at_all_lists_exactly_the_global_cultivars():
    harness = _harness(user_key=_USER_WITHOUT_TENANT)

    response = harness.client.get("/api/v1/species/sp_global/cultivars")

    names = _cultivar_names(response)
    assert names == {_GLOBAL_CULTIVAR}
    assert _PERSONAL_CULTIVAR not in names
    assert _ORG_CULTIVAR not in names


def test_the_personal_cultivar_stops_resolving_by_key_while_the_org_header_is_set():
    harness = _harness()

    without_header = harness.client.get("/api/v1/species/sp_global/cultivars/cv_personal")
    with_header = harness.client.get("/api/v1/species/sp_global/cultivars/cv_personal", headers=_ORG_HEADER)

    assert without_header.status_code == 200
    assert without_header.json()["name"] == _PERSONAL_CULTIVAR
    assert with_header.status_code == 404


def test_the_org_cultivar_resolves_by_key_only_while_the_org_header_is_set():
    harness = _harness()

    with_header = harness.client.get("/api/v1/species/sp_global/cultivars/cv_org", headers=_ORG_HEADER)
    without_header = harness.client.get("/api/v1/species/sp_global/cultivars/cv_org")

    assert with_header.status_code == 200
    assert with_header.json()["name"] == _ORG_CULTIVAR
    assert without_header.status_code == 404


def test_a_foreign_cultivar_is_404_and_never_403_for_the_org_member():
    harness = _harness()

    foreign = harness.client.get("/api/v1/species/sp_global/cultivars/cv_foreign", headers=_ORG_HEADER)
    own = harness.client.get("/api/v1/species/sp_global/cultivars/cv_org", headers=_ORG_HEADER)

    assert foreign.status_code == 404
    assert foreign.json()["error_code"] == "ENTITY_NOT_FOUND"
    assert own.status_code == 200


# ── AC 7: the botanical-family surface ───────────────────────────────────────


def test_the_family_species_counts_move_with_the_active_tenant():
    # The counts are the number the catalogue page shows next to each family; if
    # they did not move with the header they would contradict the species list the
    # same page renders. Two org species share the family the personal one is in,
    # so the two answers differ by value, not just by which rows produced them.
    harness = _harness()

    with_header = _family_counts(harness.client.get("/api/v1/botanical-families", headers=_ORG_HEADER))
    without_header = _family_counts(harness.client.get("/api/v1/botanical-families"))

    assert with_header == {"Rosaceae": 1, "Lamiaceae": 2, "Cannabaceae": 0}
    assert without_header == {"Rosaceae": 1, "Lamiaceae": 1, "Cannabaceae": 0}
    # Both directions restated where it matters most: the foreign tenant's species
    # is counted in neither answer, so no count leaks a row the list route hides.
    assert with_header["Cannabaceae"] == 0
    assert without_header["Cannabaceae"] == 0


def test_a_caller_with_no_tenant_at_all_counts_only_the_global_species():
    harness = _harness(user_key=_USER_WITHOUT_TENANT)

    counts = _family_counts(harness.client.get("/api/v1/botanical-families"))

    assert counts == {"Rosaceae": 1, "Lamiaceae": 0, "Cannabaceae": 0}


def test_the_species_listing_of_a_family_moves_with_the_active_tenant():
    # The row-level pendant of the counts: same family, same URL, different rows.
    harness = _harness()

    with_header = harness.client.get("/api/v1/botanical-families/fam_lamiaceae/species", headers=_ORG_HEADER)
    without_header = harness.client.get("/api/v1/botanical-families/fam_lamiaceae/species")

    assert with_header.status_code == 200
    assert without_header.status_code == 200
    assert {row["scientific_name"] for row in with_header.json()} == {_ORG_BASIL, _ORG_SAGE}
    assert {row["scientific_name"] for row in without_header.json()} == {_PERSONAL_MINT}


# ── AC 8 / R-1: the companion-planting anchor, the fourth consumer ───────────


def test_a_foreign_companion_anchor_is_404_while_an_org_anchor_resolves_with_the_header():
    # R-1: the companion router is the resolver consumer that gets forgotten. Its
    # anchor lookup is the same scoped ``get_species`` the by-key read uses, so it
    # must move with the header too.
    harness = _harness()

    foreign = harness.client.get("/api/v1/companion-planting/species/sp_foreign/compatible", headers=_ORG_HEADER)
    org = harness.client.get("/api/v1/companion-planting/species/sp_org/compatible", headers=_ORG_HEADER)

    assert foreign.status_code == 404
    assert foreign.json()["error_code"] == "ENTITY_NOT_FOUND"
    assert org.status_code == 200
    # The 200 really reached the graph — an empty list would make the pair pass
    # while the anchor resolution silently returned nothing.
    assert [row["species_key"] for row in org.json()] == ["sp_global"]


def test_the_companion_anchor_scope_moves_with_the_header_in_both_directions():
    # Both consuming companion routes, both directions of the switch: the org
    # anchor becomes reachable and the personal anchor becomes unreachable, from
    # the same caller, by adding one header.
    harness = _harness()
    org_url = "/api/v1/companion-planting/species/sp_org/compatible"
    personal_url = "/api/v1/companion-planting/species/sp_personal/incompatible"

    assert harness.client.get(org_url).status_code == 404
    assert harness.client.get(org_url, headers=_ORG_HEADER).status_code == 200
    assert harness.client.get(personal_url).status_code == 200
    assert harness.client.get(personal_url, headers=_ORG_HEADER).status_code == 404
