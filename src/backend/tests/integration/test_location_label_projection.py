"""#1397 group C — the location/slot labels these two queries project, against a real ArangoDB.

`ArangoPlantInstanceRepository.list_active_in_phase_definition` and
`list_active_for_tenant` guard their label projections with
``location.tenant_key == @tenant_key`` (and the same on ``slot``). That field is
**not** what identifies a location's tenant:

* `POST /t/{slug}/locations` builds ``Location(**body.model_dump())`` and
  `LocationCreate` cannot carry a ``tenant_key`` (`check_tenant_body_field.py`,
  #1000), so every location created through the API stores ``""``;
* `PUT /slots/{key}` replaces the whole slot document the same way.

A location is tenant-resolved through its parent **site**, which is the only
document in the chain that carries the key — the rule
`ArangoSiteRepository.get_slot_for_plant` and `PlantInstanceService._resolve_placement`
already follow, and the one the rest of #1397 was fixed to.

**Why this file, and why against a real database.** The unit tier here asserts on
the AQL *string* (the capturing-fake style of `test_dashboard_counts_repo.py`),
which can pin that the query mentions the right anchor but not one thing about the
answer. This defect is entirely in the answer: the query parses, runs, returns
every row, and silently reports ``location_name: null`` for a location the caller
owns. Nothing about the query text looks wrong.

**The data shape is the point.** Every location below is stored with
``tenant_key: ""``, because that is what the write path produces. A fixture that
filled the field would make the broken projection pass — the #947 / #1155 class,
and the failure mode #1397 names explicitly as the reason nobody noticed.

The one row that keeps the guard honest is `loc-foreign`: a location under another
tenant's site, still reachable by key. Its label must stay ``null``, or the repair
has traded a missing name for a cross-tenant leak.

Runs in CI against a service container; locally it needs a database of its own
(a missing one is a failure in CI, a loud skip locally — ``conftest.py``). Start one
with::

    docker run -d -p 8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_location_label_projection.py -v

`tests/integration/` runs in CI since #1432 (the `Integration tests (ArangoDB)` job in
`.github/workflows/backend.yml`); before that it was absent, because without a database
it self-skipped and would have reported green having tested nothing. A second,
statically-checkable guard for this rule lives in the unit tier.
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.plant_instance_repository import ArangoPlantInstanceRepository
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME

TEST_DATABASE = "kamerplanter_location_label_test"

TENANT = "tenant-a"
FOREIGN_TENANT = "tenant-b"


pytestmark = pytest.mark.usefixtures("arango_db")

PHASE_DEFINITION = "pd-veg"
PHASE_ENTRY = "pse-veg"


@pytest.fixture(scope="module")
def db():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    database = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)

    for name in (
        col.PLANT_INSTANCES,
        col.SITES,
        col.LOCATIONS,
        col.SLOTS,
        col.SPECIES,
        col.PHASE_DEFINITIONS,
        col.PHASE_SEQUENCE_ENTRIES,
        col.GROWTH_PHASES,
        col.TASKS,
        col.CULTIVARS,
    ):
        database.create_collection(name)

    # Sites carry the tenant. Locations and slots do not — exactly as the write
    # path stores them.
    database.collection(col.SITES).insert({"_key": "site-own", "tenant_key": TENANT, "name": "Mein Garten"})
    database.collection(col.SITES).insert(
        {"_key": "site-foreign", "tenant_key": FOREIGN_TENANT, "name": "Fremder Garten"}
    )

    database.collection(col.LOCATIONS).insert(
        {"_key": "loc-own", "tenant_key": "", "site_key": "site-own", "name": "Gewächshaus"}
    )
    database.collection(col.LOCATIONS).insert(
        {"_key": "loc-foreign", "tenant_key": "", "site_key": "site-foreign", "name": "Fremdes Beet"}
    )
    database.collection(col.SLOTS).insert(
        {"_key": "slot-own", "tenant_key": "", "location_key": "loc-own", "slot_id": "A1"}
    )
    database.collection(col.SLOTS).insert(
        {"_key": "slot-foreign", "tenant_key": "", "location_key": "loc-foreign", "slot_id": "Z9"}
    )
    # A location whose site is gone. `delete_site` does not cascade to its locations
    # (`site_service.py`), so this state is reachable, and `v0004` may have stamped
    # such a row's `tenant_key` before its site was deleted.
    database.collection(col.LOCATIONS).insert(
        {"_key": "loc-orphan", "tenant_key": TENANT, "site_key": "site-deleted", "name": "Verwaistes Beet"}
    )

    database.collection(col.PHASE_DEFINITIONS).insert({"_key": PHASE_DEFINITION, "name": "vegetative"})
    database.collection(col.PHASE_SEQUENCE_ENTRIES).insert(
        {"_key": PHASE_ENTRY, "phase_definition_key": PHASE_DEFINITION}
    )
    database.collection(col.SPECIES).insert(
        {"_key": "sp-1", "scientific_name": "Solanum lycopersicum", "common_names": ["Tomate"]}
    )

    plants = database.collection(col.PLANT_INSTANCES)
    plants.insert(
        {
            "_key": "plant-own",
            "tenant_key": TENANT,
            "species_key": "sp-1",
            "instance_id": "P-1",
            "plant_name": "Tomate 1",
            "removed_on": None,
            "current_phase_key": PHASE_ENTRY,
            "current_phase_started_at": "2026-08-01T00:00:00+00:00",
            "location_key": "loc-own",
            "slot_key": "slot-own",
        }
    )
    plants.insert(
        {
            "_key": "plant-orphan",
            "tenant_key": TENANT,
            "species_key": "sp-1",
            "instance_id": "P-3",
            "plant_name": "Tomate 3",
            "removed_on": None,
            "current_phase_key": PHASE_ENTRY,
            "current_phase_started_at": "2026-08-03T00:00:00+00:00",
            "location_key": "loc-orphan",
            "slot_key": None,
        }
    )
    # The honesty control: a row of the caller's own tenant pointing at another
    # tenant's location. Legacy data can be in this state, and the projection's
    # guard exists for exactly it.
    plants.insert(
        {
            "_key": "plant-misplaced",
            "tenant_key": TENANT,
            "species_key": "sp-1",
            "instance_id": "P-2",
            "plant_name": "Tomate 2",
            "removed_on": None,
            "current_phase_key": PHASE_ENTRY,
            "current_phase_started_at": "2026-08-02T00:00:00+00:00",
            "location_key": "loc-foreign",
            "slot_key": "slot-foreign",
        }
    )

    yield database

    system.delete_database(TEST_DATABASE)
    client.close()


@pytest.fixture
def repo(db):
    return ArangoPlantInstanceRepository(db)


def _by_key(rows: list[dict], field: str = "key") -> dict[str, dict]:
    return {row[field]: row for row in rows}


class TestListActiveInPhaseDefinition:
    def test_the_caller_own_location_and_slot_are_labelled(self, repo):
        """The defect: both came back ``null`` although the caller owns them."""
        rows = _by_key(repo.list_active_in_phase_definition(TENANT, PHASE_DEFINITION))

        own = rows["plant-own"]
        assert own["location_name"] == "Gewächshaus", (
            "the caller's own location projected no name; the guard is comparing "
            "location.tenant_key, which the write path stores empty (#1397)"
        )
        assert own["slot_label"] == "A1", "the caller's own slot projected no label (#1397)"

    def test_a_foreign_location_is_still_not_labelled(self, repo):
        """The control. Without it, 'always return the name' would pass the test above."""
        rows = _by_key(repo.list_active_in_phase_definition(TENANT, PHASE_DEFINITION))

        misplaced = rows["plant-misplaced"]
        assert misplaced["location_name"] is None, "another tenant's location name leaked into this list"
        assert misplaced["slot_label"] is None, "another tenant's slot label leaked into this list"

    def test_the_keys_are_projected_either_way(self, repo):
        """Keys are not gated and must not become collateral of the repair.

        The row still says *where* the plant points; only the human-readable label
        is withheld. A fix that dropped the keys would change an API contract to
        close a label leak.
        """
        rows = _by_key(repo.list_active_in_phase_definition(TENANT, PHASE_DEFINITION))

        assert rows["plant-own"]["location_key"] == "loc-own"
        assert rows["plant-misplaced"]["location_key"] == "loc-foreign"


class TestListActiveForTenant:
    def test_the_caller_own_location_is_labelled(self, repo):
        rows = _by_key(repo.list_active_for_tenant(TENANT, limit=50), field="_key")

        assert rows["plant-own"]["location_name"] == "Gewächshaus", (
            "the dashboard list projected no location name for a location the caller owns (#1397)"
        )

    def test_a_foreign_location_is_still_not_labelled(self, repo):
        rows = _by_key(repo.list_active_for_tenant(TENANT, limit=50), field="_key")

        assert rows["plant-misplaced"]["location_name"] is None


class TestALocationWhoseSiteIsGone:
    """An observable change the anchor brings, recorded rather than discovered later.

    `delete_site` does not cascade to its locations, so a location can outlive its
    site. Such a row used to project its name whenever ``v0004_backfill_tenant_key``
    had stamped its ``tenant_key`` before the deletion; anchored on the site it now
    resolves ``null``, and the label is withheld.

    That is the right answer — ownership genuinely cannot be established for an
    orphan, and the alternative is trusting a field the write path does not
    maintain — but it is a behaviour change, and a dashboard row quietly losing its
    location name is the kind of thing that gets reported as a fresh bug a month
    later if nobody wrote it down.
    """

    def test_its_label_is_withheld_rather_than_read_from_the_stale_field(self, repo):
        rows = _by_key(repo.list_active_for_tenant(TENANT, limit=50), field="_key")

        orphan = rows["plant-orphan"]
        assert orphan["location_name"] is None, (
            "an orphaned location's name was projected; the tenant_key on it is stale data, not an ownership fact"
        )
        # The key is still reported, so the row still says where it points.
        assert orphan["location_key"] == "loc-orphan"
