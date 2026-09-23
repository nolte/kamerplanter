"""The queries #1638 moved out of the onboarding services, against a real ArangoDB.

``FavoritesService`` and ``StarterKitService`` used to drive a ``StandardDatabase``
themselves. Their AQL now lives in :class:`ArangoFavoritesRepository`,
:meth:`ArangoNutrientPlanRepository.list_template_plan_summaries` /
``list_edge_fertilizer_keys`` and :meth:`ArangoSpeciesRepository.list_visible_keys`.
The move is only a refactoring if every scoping arm survived it, and a scoping arm
lives in AQL text — which a double that returns a canned list cannot see. So each
moved query is measured here with a row that must **not** come back: another
tenant's row, another user's edge, another plan's fertilizer. Each test also
asserts the row that *must* come back, so an over-strict filter (the #324
direction) fails as loudly as a leak.
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.common.exceptions import NotFoundError
from app.data_access.arango import collections as col
from app.data_access.arango.favorites_repository import ArangoFavoritesRepository
from app.data_access.arango.nutrient_plan_repository import ArangoNutrientPlanRepository
from app.data_access.arango.species_repository import ArangoSpeciesRepository
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name
from tests.support.onboarding_wiring import build_favorites_service

pytestmark = pytest.mark.usefixtures("arango_db")

TEST_DATABASE = run_database_name("onboarding_repositories")
CALLER_TENANT = "tenant-alice"
FOREIGN_TENANT = "tenant-bob"
CALLER_USER = "users/alice"
OTHER_USER = "users/bob"


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)

    for name in (
        col.SPECIES,
        col.NUTRIENT_PLANS,
        col.NUTRIENT_PLAN_PHASE_ENTRIES,
        col.FERTILIZERS,
        col.SUBSTRATES,
        col.ACTIVITIES,
        col.BOTANICAL_FAMILIES,
    ):
        db.create_collection(name)
    for name in (col.PLAN_USES_FERTILIZER, col.TENANT_HAS_ACCESS):
        db.create_collection(name, edge=True)
    favourites = db.create_collection(col.USER_FAVORITES, edge=True)
    # The production index (collections.py): the insert race relies on it.
    favourites.add_persistent_index(fields=["_from", "_to"], unique=True)

    yield db

    system.delete_database(TEST_DATABASE)


@pytest.fixture
def db(database):
    """A clean slate per test — each one seeds exactly the rows it reasons about."""
    for name in database.collections():
        if not name["system"]:
            database.collection(name["name"]).truncate()
    return database


# ── ArangoSpeciesRepository.list_visible_keys ────────────────────────────────


class TestVisibleSpeciesKeys:
    def test_a_foreign_species_is_not_visible_and_the_three_arms_are(self, db) -> None:
        species = db.collection(col.SPECIES)
        species.insert({"_key": "sp-foreign", "tenant_key": FOREIGN_TENANT})
        species.insert({"_key": "sp-global", "tenant_key": ""})
        species.insert({"_key": "sp-null"})
        species.insert({"_key": "sp-own", "tenant_key": CALLER_TENANT})
        species.insert({"_key": "sp-granted", "tenant_key": FOREIGN_TENANT})
        db.collection(col.TENANT_HAS_ACCESS).insert(
            {"_from": f"{col.TENANTS}/{CALLER_TENANT}", "_to": f"{col.SPECIES}/sp-granted"}
        )

        visible = ArangoSpeciesRepository(db).list_visible_keys(tenant_key=CALLER_TENANT)

        assert visible == {"sp-global", "sp-null", "sp-own", "sp-granted"}

    def test_a_grant_to_another_tenant_admits_nobody_else(self, db) -> None:
        db.collection(col.SPECIES).insert({"_key": "sp-shared", "tenant_key": FOREIGN_TENANT})
        db.collection(col.TENANT_HAS_ACCESS).insert(
            {"_from": f"{col.TENANTS}/tenant-carol", "_to": f"{col.SPECIES}/sp-shared"}
        )

        assert ArangoSpeciesRepository(db).list_visible_keys(tenant_key=CALLER_TENANT) == set()


# ── ArangoNutrientPlanRepository ─────────────────────────────────────────────


class TestTemplatePlanSummaries:
    def test_a_foreign_template_plan_is_not_served_and_own_and_global_are(self, db) -> None:
        plans = db.collection(col.NUTRIENT_PLANS)
        plans.insert({"_key": "plan-foreign", "tenant_key": FOREIGN_TENANT, "is_template": True})
        plans.insert({"_key": "plan-global", "tenant_key": "", "is_template": True})
        plans.insert({"_key": "plan-own", "tenant_key": CALLER_TENANT, "is_template": True})

        rows = ArangoNutrientPlanRepository(db).list_template_plan_summaries(tenant_key=CALLER_TENANT)

        assert {row["plan_key"] for row in rows} == {"plan-global", "plan-own"}

    def test_the_fertilizer_projection_unions_edges_and_embedded_dosages(self, db) -> None:
        db.collection(col.NUTRIENT_PLANS).insert({"_key": "plan-own", "tenant_key": CALLER_TENANT, "is_template": True})
        db.collection(col.FERTILIZERS).insert({"_key": "f-edge", "product_name": "Edge", "brand": "B"})
        db.collection(col.FERTILIZERS).insert({"_key": "f-embedded", "product_name": "Embedded", "brand": "B"})
        db.collection(col.NUTRIENT_PLAN_PHASE_ENTRIES).insert(
            {
                "_key": "pe-1",
                "plan_key": "plan-own",
                "delivery_channels": [{"fertilizer_dosages": [{"fertilizer_key": "f-embedded"}]}],
            }
        )
        db.collection(col.PLAN_USES_FERTILIZER).insert(
            {"_from": f"{col.NUTRIENT_PLAN_PHASE_ENTRIES}/pe-1", "_to": f"{col.FERTILIZERS}/f-edge"}
        )

        (row,) = ArangoNutrientPlanRepository(db).list_template_plan_summaries(tenant_key=CALLER_TENANT)

        assert row["fertilizer_count"] == 2
        assert {f["key"] for f in row["fertilizers"]} == {"f-edge", "f-embedded"}


class TestEdgeFertilizerKeys:
    def test_only_the_named_plans_fertilizers_are_returned(self, db) -> None:
        entries = db.collection(col.NUTRIENT_PLAN_PHASE_ENTRIES)
        entries.insert({"_key": "pe-mine", "plan_key": "plan-mine"})
        entries.insert({"_key": "pe-other", "plan_key": "plan-other"})
        uses = db.collection(col.PLAN_USES_FERTILIZER)
        uses.insert({"_from": f"{col.NUTRIENT_PLAN_PHASE_ENTRIES}/pe-mine", "_to": f"{col.FERTILIZERS}/f-mine"})
        uses.insert({"_from": f"{col.NUTRIENT_PLAN_PHASE_ENTRIES}/pe-mine", "_to": f"{col.FERTILIZERS}/f-mine"})
        uses.insert({"_from": f"{col.NUTRIENT_PLAN_PHASE_ENTRIES}/pe-other", "_to": f"{col.FERTILIZERS}/f-other"})

        keys = ArangoNutrientPlanRepository(db).list_edge_fertilizer_keys("plan-mine")

        assert keys == ["f-mine"]


# ── ArangoFavoritesRepository ────────────────────────────────────────────────


def _edge(from_id: str, to_id: str, **extra: object) -> dict:
    return {"_from": from_id, "_to": to_id, "source": "manual", "cascade_from_key": None, **extra}


class TestFavouriteEdges:
    def test_find_and_list_see_only_the_callers_edges(self, db) -> None:
        edges = db.collection(col.USER_FAVORITES)
        edges.insert(_edge(CALLER_USER, "species/tomato", target_type=col.SPECIES))
        edges.insert(_edge(CALLER_USER, "fertilizers/calmag", target_type=col.FERTILIZERS))
        edges.insert(_edge(OTHER_USER, "species/basil", target_type=col.SPECIES))
        repo = ArangoFavoritesRepository(db)

        assert repo.find_edge(CALLER_USER, "species/tomato") is not None
        assert repo.find_edge(CALLER_USER, "species/basil") is None
        assert {e["_to"] for e in repo.list_edges(CALLER_USER)} == {"species/tomato", "fertilizers/calmag"}
        assert [e["_to"] for e in repo.list_edges(CALLER_USER, col.SPECIES)] == ["species/tomato"]

    def test_removal_leaves_another_users_edge_to_the_same_key(self, db) -> None:
        edges = db.collection(col.USER_FAVORITES)
        edges.insert(_edge(CALLER_USER, "species/tomato"))
        edges.insert(_edge(OTHER_USER, "species/tomato"))

        removed = ArangoFavoritesRepository(db).remove_edges_to_key(CALLER_USER, "tomato")

        assert removed == 1
        assert [e["_from"] for e in edges.all()] == [OTHER_USER]

    def test_cascade_cleanup_removes_only_that_plans_cascade_edges_of_that_user(self, db) -> None:
        edges = db.collection(col.USER_FAVORITES)
        edges.insert(_edge(CALLER_USER, "fertilizers/a", source="cascade", cascade_from_key="plan-1"))
        edges.insert(_edge(CALLER_USER, "fertilizers/b", source="cascade", cascade_from_key="plan-2"))
        edges.insert(_edge(CALLER_USER, "fertilizers/c", source="manual", cascade_from_key="plan-1"))
        edges.insert(_edge(OTHER_USER, "fertilizers/a", source="cascade", cascade_from_key="plan-1"))

        removed = ArangoFavoritesRepository(db).remove_cascade_edges(CALLER_USER, "plan-1")

        assert removed == 1
        remaining = {(e["_from"], e["_to"]) for e in edges.all()}
        assert remaining == {
            (CALLER_USER, "fertilizers/b"),
            (CALLER_USER, "fertilizers/c"),
            (OTHER_USER, "fertilizers/a"),
        }

    def test_promotion_stores_the_null_it_writes(self, db) -> None:
        """The raw driver write keeps ``None`` (``keep_none`` defaults to True) —
        the verdict the merge-mode guard used to record for this write while it
        still sat in the service, now measured instead of asserted."""
        meta = db.collection(col.USER_FAVORITES).insert(
            _edge(CALLER_USER, "fertilizers/a", source="cascade", cascade_from_key="plan-1")
        )

        ArangoFavoritesRepository(db).promote_to_manual(meta["_key"])

        stored = db.collection(col.USER_FAVORITES).get(meta["_key"])
        assert stored["source"] == "manual"
        assert "cascade_from_key" in stored
        assert stored["cascade_from_key"] is None

    def test_a_duplicate_insert_returns_the_stored_edge_instead_of_raising(self, db) -> None:
        repo = ArangoFavoritesRepository(db)
        first = repo.insert_edge(_edge(CALLER_USER, "species/tomato", favorited_at="first"))

        second = repo.insert_edge(_edge(CALLER_USER, "species/tomato", favorited_at="second"))

        assert second["_key"] == first["_key"]
        assert second["favorited_at"] == "first"


class TestCatalogueProbes:
    def test_a_grant_to_another_tenant_does_not_admit_the_caller(self, db) -> None:
        db.collection(col.TENANT_HAS_ACCESS).insert(
            {"_from": f"{col.TENANTS}/{FOREIGN_TENANT}", "_to": f"{col.SPECIES}/sp-shared"}
        )
        repo = ArangoFavoritesRepository(db)

        assert repo.is_granted(col.SPECIES, "sp-shared", FOREIGN_TENANT) is True
        assert repo.is_granted(col.SPECIES, "sp-shared", CALLER_TENANT) is False

    def test_a_missing_catalogue_answers_none_not_an_error(self, db) -> None:
        assert ArangoFavoritesRepository(db).get_catalogue_row("no_such_catalogue", "k") is None


class TestServiceOverTheRealRepositories:
    """The visibility decision stayed in the service; measured end to end once."""

    def test_a_foreign_species_cannot_be_favourited_and_a_global_one_can(self, db) -> None:
        species = db.collection(col.SPECIES)
        species.insert({"_key": "sp-foreign", "tenant_key": FOREIGN_TENANT})
        species.insert({"_key": "sp-global", "tenant_key": ""})
        service = build_favorites_service(db)

        with pytest.raises(NotFoundError):
            service.add_favorite("alice", "sp-foreign", tenant_key=CALLER_TENANT)
        edge = service.add_favorite("alice", "sp-global", tenant_key=CALLER_TENANT)

        assert edge["_to"] == f"{col.SPECIES}/sp-global"
        assert [e["_to"] for e in db.collection(col.USER_FAVORITES).all()] == [f"{col.SPECIES}/sp-global"]
