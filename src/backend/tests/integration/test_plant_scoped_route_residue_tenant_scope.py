"""The 16 plant-scoped routes the guard could not follow, measured (#1627).

``scripts/check_plant_scoped_route_tenant.py`` enumerates every route whose URL
carries a non-terminal path parameter naming a tenant-ownable entity. After
#1619/#1626 it reported 46 such sites, of which **16 reached their tenant check
through a positional or nested argument** — a form a static single-file reader
cannot tie to a parameter. Three had been spot-checked by hand; thirteen were
unverified. "Unverified" is not "safe": #1619 began as a suspicion about three
routes, measured five, and turned up a cross-tenant *write* nobody suspected.

So all of them were measured here rather than read: a request through the real
route with a **foreign** tenant's entity key, against a real ArangoDB, real
router → real service → real repository → real AQL, with only
:func:`get_current_tenant` overridden.

Result: every one of them is genuinely scoped. Twelve answer ``404``; the
thirteenth — ``GET /plants/{plant_key}/overwintering/status`` — answers ``200``
**by contract**, and this file pins the reason that is not a leak: its body for a
foreign plant is byte-identical to its body for a plant that does not exist
anywhere, so it is not an existence oracle (the alternative, 404 for exactly the
foreign-plant-with-profile case, would be one).

Why the assertions are paired
-----------------------------
Every foreign case is run together with an **own** case through the same
handler. A 404 alone proves nothing — a mistyped URL, an absent fixture or a
route that no longer exists all answer 404 too. Only the pair "foreign refused,
own served" shows the 404 is a tenant decision. The own direction is also the
#324 guard: a fix that hides the caller's own rows is not a fix.

Needs a real ArangoDB (``tests/integration/conftest.py`` holds the contract:
in CI a missing server is a failure, locally a loud skip).
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME

pytestmark = pytest.mark.usefixtures("arango_db")

_DB_NAME = "kamerplanter_route_residue_test"

TENANT_A = "tenant-a"
TENANT_B = "tenant-b"
SLUG = "anna"
NOW = "2026-02-01T00:00:00+00:00"

#: Values that exist only on tenant-b's documents. Any of them in a response
#: body is a leak regardless of the status code.
SECRETS = (
    "SECRET-B-DIARY-TEXT",
    "SECRET-B-TRAIT",
    "SECRET-B-OW",
    "SECRET-B-PLANT",
    "SECRET-B-NOPROFILE",
)


@pytest.fixture(scope="module")
def client():
    """The real tenant-scoped router over a real, throwaway ArangoDB."""
    from app.common import dependencies as deps
    from app.config.settings import Settings
    from app.data_access.arango import collections as col
    from app.data_access.arango.connection import ArangoConnection

    settings = Settings(arangodb_database=_DB_NAME)
    conn = ArangoConnection(settings)
    db = conn.connect()
    col.ensure_collections(db)

    # The routers resolve their repositories through ``dependencies.get_db()``,
    # which reads the process-wide connection — not the one built here. Without
    # this the app would answer out of the developer's own database and every
    # assertion below would be about the wrong data.
    previous_connection = deps._connection
    deps._connection = conn

    from app.domain.models.overwintering_profile import OverwinteringProfile
    from app.domain.models.plant_diary_entry import PlantDiaryEntry
    from app.domain.models.plant_instance import PlantInstance
    from app.domain.models.planting_run import PlantingRun
    from app.domain.models.privacy import ConsentRecord
    from app.domain.models.propagation import PhenotypeNote
    from app.domain.models.site import Site
    from app.domain.models.species import Species

    def put(collection, model, **raw):
        doc = {k: v for k, v in model.model_dump(by_alias=True, mode="json").items() if v is not None}
        doc.update(raw)
        db.collection(collection).insert(doc, overwrite=True)

    # ``is_mother`` and friends live on the raw plant document, not on the lean
    # PlantInstance model (REQ-017 §2) — the mother routes read them from there.
    mother = {
        "is_mother": True,
        "mother_priority": "high",
        "mother_health_score": 42,
        "mother_designated_at": NOW,
    }

    def plant(key, tenant, name, site_key):
        return PlantInstance(
            _key=key,
            tenant_key=tenant,
            instance_id=f"P-{key}",
            species_key="tomato",
            plant_name=name,
            planted_on="2026-01-01",
            site_key=site_key,
        )

    put(
        col.SITES,
        Site(
            _key="site-a", tenant_key=TENANT_A, name="Garden A", type="outdoor", climate_zone="7a", hardiness_zone="7a"
        ),
    )
    put(
        col.SITES,
        Site(
            _key="site-b", tenant_key=TENANT_B, name="Garden B", type="outdoor", climate_zone="6a", hardiness_zone="6a"
        ),
    )
    put(col.PLANT_INSTANCES, plant("plant-a1", TENANT_A, "own plant", "site-a"), **mother)
    put(col.PLANT_INSTANCES, plant("plant-a2", TENANT_A, "own no-profile", "site-a"), **mother)
    put(col.PLANT_INSTANCES, plant("plant-b1", TENANT_B, "SECRET-B-PLANT", "site-b"), **mother)
    put(col.PLANT_INSTANCES, plant("plant-b2", TENANT_B, "SECRET-B-NOPROFILE", "site-b"), **mother)

    # Frost-sensitive species on a frost-exposed site: without this the
    # hardiness status would answer "unknown" for the caller's OWN plant too,
    # and the foreign "unknown" would prove nothing.
    put(
        col.SPECIES,
        Species(
            _key="tomato",
            scientific_name="Solanum lycopersicum",
            common_name="Tomate",
            hardiness_zones=["8a"],
            frost_sensitivity="sensitive",
        ),
    )

    for key, tenant in (("run-a", TENANT_A), ("run-b", TENANT_B)):
        put(
            col.PLANTING_RUNS,
            PlantingRun(_key=key, tenant_key=tenant, name=f"Run {key}", run_type="monoculture", status="active"),
        )

    # Four own entries: the delete and the two analysis cases each consume one.
    for key, tenant, plant_key, text in (
        ("entry-a1", TENANT_A, "plant-a1", "own note"),
        ("entry-a2", TENANT_A, "plant-a1", "own note 2"),
        ("entry-a3", TENANT_A, "plant-a1", "own note 3"),
        ("entry-a4", TENANT_A, "plant-a1", "own note 4"),
        ("entry-b1", TENANT_B, "plant-b1", "SECRET-B-DIARY-TEXT"),
    ):
        put(
            col.PLANT_DIARY_ENTRIES,
            PlantDiaryEntry(
                _key=key,
                tenant_key=tenant,
                plant_key=plant_key,
                entry_type="observation",
                text=text,
                created_by="user-a",
                created_at=NOW,
                updated_at=NOW,
            ),
        )

    for key, tenant, plant_key, note in (
        ("note-a1", TENANT_A, "plant-a1", "own trait"),
        ("note-b1", TENANT_B, "plant-b1", "SECRET-B-TRAIT"),
    ):
        put(
            col.PHENOTYPE_NOTES,
            PhenotypeNote(_key=key, tenant_key=tenant, plant_key=plant_key, note=note, observed_at=NOW),
        )

    for key, tenant, plant_key, notes in (
        ("ow-a1", TENANT_A, "plant-a1", "own"),
        ("ow-b1", TENANT_B, "plant-b1", "SECRET-B-OW"),
    ):
        put(
            col.OVERWINTERING_PROFILES,
            OverwinteringProfile(
                _key=key,
                tenant_key=tenant,
                plant_key=plant_key,
                hardiness_rating="needs_protection",
                winter_action="fleece",
                winter_action_month=11,
                user_overridden=False,
                notes=notes,
            ),
        )

    # REQ-050 §7.1 — without the granted purpose the two analysis routes stop at
    # a consent gate *downstream* of the scope check, and the own direction
    # would never reach the code under test.
    put(
        col.CONSENT_RECORDS,
        ConsentRecord(_key="c1", user_key="user-a", purpose="diary_ai_analysis", granted=True, granted_at=NOW),
    )

    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    from fastapi.testclient import TestClient

    from app.api.v1.tenant_scoped.router import tenant_scoped_router
    from app.common.auth import get_current_tenant
    from app.common.enums import TenantRole
    from app.common.exceptions import KamerplanterError
    from app.domain.models.tenant_context import TenantContext

    app = FastAPI()
    app.include_router(tenant_scoped_router, prefix="/api/v1")

    @app.exception_handler(KamerplanterError)
    def _handler(_request, exc: KamerplanterError):
        return JSONResponse(status_code=exc.status_code, content={"error_code": exc.error_code, "message": str(exc)})

    def _ctx() -> TenantContext:
        # LEAD: the highest domain role, so a refusal can only come from the
        # ownership check and never from the rank gate.
        return TenantContext(tenant_key=TENANT_A, tenant_slug=SLUG, user_key="user-a", role=TenantRole.LEAD)

    app.dependency_overrides[get_current_tenant] = _ctx

    yield TestClient(app, raise_server_exceptions=False)

    deps._connection = previous_connection
    sysdb = ArangoClient(hosts=ARANGO_URL).db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if sysdb.has_database(_DB_NAME):
        sysdb.delete_database(_DB_NAME)
    conn.close()


BASE = f"/api/v1/t/{SLUG}"
RUN_DIARY = f"{BASE}/planting-runs/run-a/plants"

#: ``(site, foreign request, own request, expected own status)``. The site id is
#: the guard's own ``path:line METHOD url`` spelling, so a reader can match a row
#: here to a row of ``check_plant_scoped_route_tenant.py --list``.
PAIRS = [
    (
        "planting_runs GET /{key}/plants/{plant_key}/diary/{entry_key}",
        ("GET", f"{RUN_DIARY}/plant-b1/diary/entry-b1", None),
        ("GET", f"{RUN_DIARY}/plant-a1/diary/entry-a1", None),
        200,
    ),
    (
        "planting_runs PUT /{key}/plants/{plant_key}/diary/{entry_key}",
        ("PUT", f"{RUN_DIARY}/plant-b1/diary/entry-b1", {"text": "cross-tenant overwrite"}),
        ("PUT", f"{RUN_DIARY}/plant-a1/diary/entry-a1", {"text": "own edit"}),
        200,
    ),
    (
        "planting_runs DELETE /{key}/plants/{plant_key}/diary/{entry_key}",
        ("DELETE", f"{RUN_DIARY}/plant-b1/diary/entry-b1", None),
        ("DELETE", f"{RUN_DIARY}/plant-a1/diary/entry-a4", None),
        204,
    ),
    (
        "planting_runs POST /{key}/plants/{plant_key}/diary/{entry_key}/request-analysis",
        ("POST", f"{RUN_DIARY}/plant-b1/diary/entry-b1/request-analysis", None),
        ("POST", f"{RUN_DIARY}/plant-a1/diary/entry-a2/request-analysis", None),
        200,
    ),
    (
        "planting_runs DELETE /{key}/plants/{plant_key}/diary/{entry_key}/request-analysis",
        ("DELETE", f"{RUN_DIARY}/plant-b1/diary/entry-b1/request-analysis", None),
        # entry-a3 was never marked, so the own call reaches the state machine and
        # is refused there with 409 — past the scope check, which is the point.
        ("DELETE", f"{RUN_DIARY}/plant-a1/diary/entry-a3/request-analysis", None),
        409,
    ),
    (
        "propagation PATCH /propagation/mothers/{plant_key}/designate",
        ("PATCH", f"{BASE}/propagation/mothers/plant-b1/designate", {"priority": "high"}),
        ("PATCH", f"{BASE}/propagation/mothers/plant-a1/designate", {"priority": "high"}),
        200,
    ),
    (
        "propagation PATCH /propagation/mothers/{plant_key}/retire",
        ("PATCH", f"{BASE}/propagation/mothers/plant-b1/retire", {"reason": "cross-tenant"}),
        ("PATCH", f"{BASE}/propagation/mothers/plant-a1/retire", {"reason": "done"}),
        200,
    ),
    (
        "propagation PATCH /propagation/mothers/{plant_key}/health",
        ("PATCH", f"{BASE}/propagation/mothers/plant-b1/health", {"health_score": 1}),
        ("PATCH", f"{BASE}/propagation/mothers/plant-a1/health", {"health_score": 90}),
        200,
    ),
    (
        "propagation GET /plant-instances/{plant_key}/lineage",
        ("GET", f"{BASE}/plant-instances/plant-b1/lineage", None),
        ("GET", f"{BASE}/plant-instances/plant-a1/lineage", None),
        200,
    ),
    (
        "propagation GET /plant-instances/{plant_key}/descendants",
        ("GET", f"{BASE}/plant-instances/plant-b1/descendants", None),
        ("GET", f"{BASE}/plant-instances/plant-a1/descendants", None),
        200,
    ),
    (
        "propagation GET /plant-instances/{plant_key}/phenotypes",
        ("GET", f"{BASE}/plant-instances/plant-b1/phenotypes", None),
        ("GET", f"{BASE}/plant-instances/plant-a1/phenotypes", None),
        200,
    ),
    (
        "propagation DELETE /plant-instances/{plant_key}/phenotypes/{note_key}",
        ("DELETE", f"{BASE}/plant-instances/plant-b1/phenotypes/note-b1", None),
        ("DELETE", f"{BASE}/plant-instances/plant-a1/phenotypes/note-a1", None),
        204,
    ),
    (
        "season GET /plants/{plant_key}/overwintering",
        ("GET", f"{BASE}/plants/plant-b1/overwintering", None),
        ("GET", f"{BASE}/plants/plant-a1/overwintering", None),
        200,
    ),
    (
        "season PATCH /plants/{plant_key}/overwintering",
        ("PATCH", f"{BASE}/plants/plant-b1/overwintering", {"notes": "cross-tenant"}),
        ("PATCH", f"{BASE}/plants/plant-a1/overwintering", {"notes": "own"}),
        200,
    ),
    (
        "season POST /plants/{plant_key}/overwintering/reset",
        ("POST", f"{BASE}/plants/plant-b1/overwintering/reset", None),
        ("POST", f"{BASE}/plants/plant-a1/overwintering/reset", None),
        200,
    ),
]


@pytest.mark.parametrize(("site", "foreign", "own", "own_status"), PAIRS, ids=[row[0] for row in PAIRS])
def test_foreign_plant_is_refused_and_own_plant_is_served(client, site, foreign, own, own_status):
    """A foreign entity key answers 404, and the same handler still serves an own one."""
    method, url, body = foreign
    response = client.request(method, url, json=body)

    assert response.status_code == 404, f"{site}: foreign key answered {response.status_code}: {response.text[:300]}"
    leaked = [secret for secret in SECRETS if secret in response.text]
    assert not leaked, f"{site}: leaked {leaked}"

    method, url, body = own
    own_response = client.request(method, url, json=body)
    assert own_response.status_code == own_status, (
        f"{site}: the own-direction control answered {own_response.status_code} "
        f"instead of {own_status} — the 404 above proves nothing without it: "
        f"{own_response.text[:300]}"
    )


def test_refusal_is_404_and_never_403(client):
    """No cross-tenant existence oracle: a foreign plant is *absent*, not forbidden."""
    forbidden = [
        site
        for site, (method, url, body), _own, _status in PAIRS
        if client.request(method, url, json=body).status_code == 403
    ]
    assert not forbidden, f"these sites answer 403 for a foreign plant, confirming it exists: {forbidden}"


#: The one in-class site that does NOT answer 404 for a foreign plant, and why
#: that is its contract rather than a hole: it promises an always-200 answer, so
#: a 404 for exactly "foreign plant that has a profile" would be the oracle.
_STATUS_URL = f"{BASE}/plants/{{key}}/overwintering/status"


def test_hardiness_status_tells_a_foreign_plant_from_nothing_at_all(client):
    """``GET …/overwintering/status`` answers 200 for a foreign plant — identically to nothing.

    Three bodies must be byte-identical: a foreign plant *with* a profile, a
    foreign plant *without* one, and a key that exists nowhere. If the first
    differed from the third, the endpoint would confirm that another tenant owns
    that plant.
    """
    bodies = {
        label: client.get(_STATUS_URL.format(key=key))
        for label, key in (
            ("foreign with profile", "plant-b1"),
            ("foreign without profile", "plant-b2"),
            ("absent everywhere", "plant-nowhere"),
        )
    }
    for label, response in bodies.items():
        assert response.status_code == 200, f"{label}: {response.status_code}"
        assert not [s for s in SECRETS if s in response.text], f"{label} leaked: {response.text}"

    distinct = {response.text for response in bodies.values()}
    assert len(distinct) == 1, f"the three answers are distinguishable — that is an oracle: {distinct}"


def test_hardiness_status_still_answers_for_the_callers_own_plant(client):
    """The #324 direction: the guard must not blank out the caller's own answer.

    Without this the test above would pass on an endpoint that returns the empty
    shape to *everyone*, which is not scoping, it is a broken endpoint.
    """
    own = client.get(_STATUS_URL.format(key="plant-a1"))

    assert own.status_code == 200
    assert own.json()["hardiness_light"] is not None
    assert own.text != client.get(_STATUS_URL.format(key="plant-nowhere")).text
