"""Integration test for #1506 — a care-profile write that means ``null`` writes ``null``.

``ArangoCareReminderRepository`` inherited the default merge semantics of
:attr:`BaseArangoRepository._update_is_full_replace` (``False``): the model is
dumped with ``exclude_none=True`` and handed to ``collection.update(...,
keep_none=True)``, so a field the writer set to ``None`` is **absent from the
payload** and the stored value survives an update that meant to clear it.

Measured 2026-09-17 while writing the v0050 repair migration: it set
``watering_interval_learned = None``, wrote the profile through ``update_profile``
and read the old value back. The migration routed around it with a second
``update_fields`` write; the product paths did not, so:

* ``CareReminderService.reset_profile`` cannot clear ``notes``,
  ``water_quality_hint`` or either learned interval — a reset hands back the
  preset values *plus* whatever the replaced profile happened to hold;
* ``DormancyCareActivator.deactivate`` cannot clear ``dormancy_watering``, so a
  plant that left winter dormancy keeps the winter regime next to
  ``dormancy_care_mode = False`` (REQ-047 §3.5);
* ``PATCH .../profile`` with ``notes: null`` cannot clear the note — the field the
  frontend's care form sends as ``null`` the moment the user empties it.

**Why this file needs a real ArangoDB.** The defect *is* the driver/server null
handling: which attributes ``collection.update`` removes, keeps or ignores under
``keepNull``. A repository double is free to invent that semantics — the very
failure class ``_FakeDb`` would hide here (memory: "fixture/double invents an
impossible form → the positive test certifies nothing"). Only the server can
answer whether the attribute is gone from the stored document.

Run with: pytest tests/integration/test_care_profile_null_clearing.py -v
(requires an ArangoDB; see ``tests/integration/conftest.py``).
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from arango import ArangoClient

from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("#1506 is a driver/server null-handling contract; no double may answer it"),
]

_DB_NAME = "kamerplanter_care_profile_null_test"
_TENANT_KEY = "tenant-alpha"
_PLANT_KEY = "plant-basil-null"
_SPECIES_KEY = "ocimum-basilicum"
#: A family ``_key`` in the numeric shape ArangoDB assigns — never the name (#1489).
_FAMILY_KEY = "7242"
#: ``Lamiaceae`` maps to ``HERB_TROPICAL``, a preset that carries **no**
#: ``water_quality_hint`` — so a reset from a profile that holds one is a clear.
_FAMILY_NAME = "Lamiaceae"

#: What the stored profile holds before each write under test. Every nullable field
#: of :class:`CareProfile` is populated, so "the writer meant ``None``" and "the
#: stored value survived" are distinguishable for each of them.
_STORED_NULLABLES = {
    "notes": "Kalkarmes Wasser, im Sommer taeglich pruefen",
    "water_quality_hint": "Filtered or rainwater only — sensitive to fluoride and chlorine",
    "watering_interval_learned": 11,
    "fertilizing_interval_learned": 19,
    "dormancy_watering": "minimal",
}

#: The nullables a **reset** is supposed to drop: everything the presets replace.
#: ``dormancy_watering`` is not among them — it belongs to the REQ-047 season state
#: machine, which a preset recomputation may not speak for (``SEASON_STATE_FIELDS``).
_RESET_CLEARS = sorted(set(_STORED_NULLABLES) - {"dormancy_watering"})

#: Attributes the stored document carries that :class:`CareProfile` does not declare.
#:
#: ``tenant_key`` is the real one — ``app/migrations/backfill_tenant_key.py`` stamps
#: it onto documents whose model has no such field — and it is the reason
#: full-replace mode is safe here at all: ``collection.update`` **merges**, so an
#: attribute absent from the payload keeps its stored value; only an attribute
#: explicitly sent as ``null`` is removed. That claim carries the whole design
#: decision in #1506, so it is measured rather than asserted in a comment.
_UNDECLARED_ATTRIBUTES = {"tenant_key": _TENANT_KEY, "legacy_attr": "written-by-an-older-schema"}


def _settings():
    from app.config.settings import Settings

    return Settings(arangodb_database=_DB_NAME)


def _connect():
    from app.data_access.arango.connection import ArangoConnection

    conn = ArangoConnection(_settings())
    return conn, conn.connect()


def _make_service(db):
    """A real service on real Arango repositories — the production write path, unfaked.

    Wired the way ``dependencies.get_care_reminder_service`` wires it, because
    ``reset_profile`` resolves the plant's species, cultivar and family name itself
    (#1489); a service without those collaborators would reset from the TROPICAL
    fallback and measure a different write.
    """
    from app.data_access.arango.botanical_family_repository import ArangoBotanicalFamilyRepository
    from app.data_access.arango.care_reminder_repository import ArangoCareReminderRepository
    from app.data_access.arango.plant_instance_repository import ArangoPlantInstanceRepository
    from app.data_access.arango.species_repository import ArangoSpeciesRepository
    from app.domain.engines.care_reminder_engine import CareReminderEngine
    from app.domain.services.care_reminder_service import CareReminderService

    family_repo = ArangoBotanicalFamilyRepository(db)

    def _resolve_family_name(family_key: str) -> str | None:
        family = family_repo.get_by_key(family_key)
        return getattr(family, "name", None) if family else None

    return CareReminderService(
        ArangoCareReminderRepository(db),
        CareReminderEngine(),
        plant_repo=ArangoPlantInstanceRepository(db),
        species_repo=ArangoSpeciesRepository(db),
        family_name_resolver=_resolve_family_name,
    )


def _stored_profile(db) -> dict:
    """The raw stored document — not the model, so an *absent* attribute is visible.

    ``CareProfile`` gives every nullable field the default ``None``, so reading the
    profile back through the repository cannot distinguish "the attribute was
    removed" from "the attribute is still there holding ``null``". Both are a pass
    for this issue, but only the raw document proves the write reached the server.
    """
    from app.data_access.arango import collections as col

    docs = list(
        db.aql.execute(
            f"FOR doc IN {col.CARE_PROFILES} FILTER doc.plant_key == @plant_key RETURN doc",
            bind_vars={"plant_key": _PLANT_KEY},
        )
    )
    assert len(docs) == 1, f"expected exactly one stored profile, got {len(docs)}"
    return docs[0]


@pytest.fixture
def db():
    """A bootstrapped test database, dropped afterwards."""
    from app.data_access.arango.collections import ensure_collections

    conn, database = _connect()
    ensure_collections(database)
    yield database
    conn.close()
    system = ArangoClient(hosts=ARANGO_URL).db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)


@pytest.fixture
def profile_key(db) -> str:
    """Seed a plant, its species/family, and a care profile holding every nullable.

    The profile document is inserted **directly**, not through the service's
    create path: this file measures the *update* semantics, and going through the
    bootstrap would couple it to a path being changed elsewhere (#1292).
    """
    from app.data_access.arango import collections as col

    db.collection(col.SPECIES).insert(
        {"_key": _SPECIES_KEY, "scientific_name": "Ocimum basilicum", "family_key": _FAMILY_KEY},
        overwrite=True,
    )
    db.collection(col.BOTANICAL_FAMILIES).insert({"_key": _FAMILY_KEY, "name": _FAMILY_NAME}, overwrite=True)
    db.collection(col.PLANT_INSTANCES).insert(
        {
            "_key": _PLANT_KEY,
            "tenant_key": _TENANT_KEY,
            "instance_id": f"P-{_PLANT_KEY}",
            "species_key": _SPECIES_KEY,
            "plant_name": "Basil",
            "planted_on": "2026-01-01",
        },
        overwrite=True,
    )
    meta = db.collection(col.CARE_PROFILES).insert(
        {
            "plant_key": _PLANT_KEY,
            "care_style": "calathea",
            "watering_interval_days": 5,
            "dormancy_care_mode": True,
            # Deliberately not the model default (30): a reset that overwrote the
            # season state with a freshly generated profile would write 30 here, and
            # a seed holding the default could not tell that apart from preservation.
            "dormancy_check_interval_days": 21,
            "auto_generated": True,
            "created_at": "2026-01-01T00:00:00+00:00",
            **_STORED_NULLABLES,
            **_UNDECLARED_ATTRIBUTES,
        }
    )
    return str(meta["_key"])


# ── reset_profile ────────────────────────────────────────────────────────────


@pytest.mark.parametrize("field", _RESET_CLEARS)
def test_reset_profile_clears_every_nullable_field_the_presets_replace(db, profile_key, field):
    """A reset to the ``Lamiaceae``/``HERB_TROPICAL`` presets leaves nothing behind.

    The presets set none of :data:`_RESET_CLEARS` — ``HERB_TROPICAL`` has no
    ``water_quality_hint``, the plant has no ``WateringGuide`` so
    ``auto_generate_profile`` produces ``notes=None``, and a freshly generated
    profile has no learned intervals. So every one of them is a value the reset
    means to drop.

    Against the merge-mode repository each assertion here failed with the stored
    value still in place — the defect #1506 reports.
    """
    service = _make_service(db)

    returned = service.reset_profile(_PLANT_KEY)

    assert getattr(returned, field) is None, f"reset answered with the replaced {field}"
    assert _stored_profile(db).get(field) is None, f"the replaced {field} survived the reset in storage"


def test_reset_profile_leaves_the_season_state_to_the_season_state_machine(db, profile_key):
    """The REQ-047 dormancy fields survive a reset of the care presets.

    ``SEASON_STATE_FIELDS`` is owned by ``DormancyCareActivator``, driven by the
    ``winter_dormancy`` / ``pre_spring`` transitions. A recomputation from the family
    presets knows nothing about the season, so it may not answer for it — the rule
    v0050 already follows with ``_PRESERVED_FIELDS``.

    This is the half #1506 could have broken while fixing the other one: before the
    repository became full-replace, ``dormancy_watering`` was preserved *by accident*
    (the ``None`` was dropped) while ``dormancy_care_mode=False`` and
    ``dormancy_check_interval_days=30`` from the freshly generated profile were
    already being written over a live winter state. The exclusion makes all three
    deliberate.
    """
    service = _make_service(db)

    returned = service.reset_profile(_PLANT_KEY)

    stored = _stored_profile(db)
    assert returned.dormancy_watering == _STORED_NULLABLES["dormancy_watering"]
    assert stored["dormancy_watering"] == _STORED_NULLABLES["dormancy_watering"]
    assert returned.dormancy_care_mode is True
    assert stored["dormancy_care_mode"] is True
    assert stored["dormancy_check_interval_days"] == 21


def test_reset_profile_keeps_an_attribute_the_model_does_not_declare(db, profile_key):
    """Full-replace removes an explicit ``null``; it does not replace the document.

    ``collection.update`` merges either way, so ``tenant_key`` — stamped onto stored
    documents by ``app/migrations/backfill_tenant_key.py``, and absent from
    :class:`CareProfile` — survives a write that never mentions it. The whole reason
    flipping the flag is safe for this collection rests on that, so it is measured
    here rather than argued in a comment.
    """
    service = _make_service(db)

    service.reset_profile(_PLANT_KEY)

    stored = _stored_profile(db)
    for attribute, value in _UNDECLARED_ATTRIBUTES.items():
        assert stored.get(attribute) == value, f"the full-replace write dropped the undeclared {attribute}"


def test_reset_profile_keeps_writing_the_values_the_presets_do_set(db, profile_key):
    """The falsification companion: clearing nulls must not clear everything.

    A "fix" that simply stopped writing the nullable fields, or one that wrote an
    empty document, would pass the test above. This pins that the same write still
    carries the preset values — the reset's actual purpose.
    """
    service = _make_service(db)

    returned = service.reset_profile(_PLANT_KEY)

    stored = _stored_profile(db)
    assert returned.care_style.value == "herb_tropical"
    assert stored["care_style"] == "herb_tropical"
    assert stored["watering_interval_days"] == 5  # HERB_TROPICAL preset
    assert stored["plant_key"] == _PLANT_KEY
    # ``created_at`` is the stored document's: full-replace mode pops it from the
    # payload, so a model without one cannot erase it and one with it cannot move it.
    assert datetime.fromisoformat(stored["created_at"]) == datetime(2026, 1, 1, tzinfo=UTC)


# ── update_profile ───────────────────────────────────────────────────────────


def test_update_profile_with_an_explicit_none_clears_the_stored_note(db, profile_key):
    """``{"notes": None}`` is a clear, not a no-op.

    This is the service half of the ``PATCH .../profile`` contract; the router half
    (an explicit ``null`` in the JSON body reaching the service at all) is pinned in
    ``tests/api/test_care_profile_update_null_semantics.py``.
    """
    service = _make_service(db)

    returned = service.update_profile(_PLANT_KEY, {"notes": None})

    assert returned.notes is None
    assert _stored_profile(db).get("notes") is None


def test_update_profile_leaves_the_fields_it_was_not_given_alone(db, profile_key):
    """A partial edit is still partial: untouched nullables keep their values.

    Full-replace semantics apply to the *model* the service builds, and the service
    builds it from the stored profile — so switching the repository's null handling
    must not turn every PATCH into a reset.
    """
    service = _make_service(db)

    returned = service.update_profile(_PLANT_KEY, {"watering_interval_days": 9})

    stored = _stored_profile(db)
    assert stored["watering_interval_days"] == 9
    assert returned.notes == _STORED_NULLABLES["notes"]
    assert stored["notes"] == _STORED_NULLABLES["notes"]
    assert stored["water_quality_hint"] == _STORED_NULLABLES["water_quality_hint"]
    assert stored["dormancy_watering"] == _STORED_NULLABLES["dormancy_watering"]
    # #622: an explicit watering-interval edit resets the learned watering interval
    # — and now that reset actually reaches storage. Its fertilizing sibling, which
    # this edit does not touch, must survive.
    assert stored.get("watering_interval_learned") is None
    assert stored["fertilizing_interval_learned"] == _STORED_NULLABLES["fertilizing_interval_learned"]


# ── REQ-047 dormancy toggles ─────────────────────────────────────────────────


def test_dormancy_deactivate_clears_the_winter_watering_regime(db, profile_key):
    """Leaving dormancy drops ``dormancy_watering`` instead of leaving it stale.

    ``DormancyCareActivator.deactivate`` writes ``dormancy_care_mode=False`` and
    ``dormancy_watering=None`` in one model. Under merge mode only the first half
    reached storage, so a plant back in growth still advertised "minimal winter
    watering" to every reader of the profile (REQ-047 §3.5).
    """
    from app.data_access.arango.care_reminder_repository import ArangoCareReminderRepository
    from app.domain.services.dormancy_care_activator import DormancyCareActivator

    activator = DormancyCareActivator(ArangoCareReminderRepository(db))

    returned = activator.deactivate(_PLANT_KEY)

    assert returned is not None
    assert returned.dormancy_care_mode is False
    assert returned.dormancy_watering is None
    stored = _stored_profile(db)
    assert stored["dormancy_care_mode"] is False
    assert stored.get("dormancy_watering") is None


def test_dormancy_activate_without_a_winter_regime_clears_a_stale_one(db, profile_key):
    """An ``OverwinteringProfile`` with no ``winter_watering`` means "no regime".

    ``activate`` computes ``watering = None`` in that case and writes it. Under
    merge mode the previously stored regime survived, so the plant entered dormancy
    advertising a regime its overwintering profile does not name.
    """
    from app.common.enums import HardinessRating, WinterAction
    from app.data_access.arango.care_reminder_repository import ArangoCareReminderRepository
    from app.domain.models.overwintering_profile import OverwinteringProfile
    from app.domain.services.dormancy_care_activator import DormancyCareActivator

    activator = DormancyCareActivator(ArangoCareReminderRepository(db))

    returned = activator.activate(
        _PLANT_KEY,
        OverwinteringProfile(
            plant_key=_PLANT_KEY,
            tenant_key=_TENANT_KEY,
            hardiness_rating=HardinessRating.NEEDS_PROTECTION,
            winter_action=WinterAction.FLEECE,
            winter_action_month=11,
            storage_check_interval_days=21,
        ),
    )

    assert returned is not None
    assert returned.dormancy_watering is None
    stored = _stored_profile(db)
    assert stored["dormancy_care_mode"] is True
    assert stored["dormancy_check_interval_days"] == 21
    assert stored.get("dormancy_watering") is None
