"""The shared recompute machinery answers exactly as v0050's copy does (#1505).

``app/migrations/support/care_profile_recompute.py`` is a **copy** of the logic
inside v0050's class — it had to be, because v0050 has been applied and its class
source is hashed by ``Migration.checksum()`` (M-7), so it could not be refactored
into a shared base. A copy is free to disagree with its original, and this project
has paid for that more than once.

So the copy is driven here with **v0050's own criterion** (identity with
``_BROKEN_BOOTSTRAP_OUTPUT``) over **v0050's own fixtures**, and the two reports
are required to be equal field for field. Everything the two migrations share — the
batch loop, the classification order, the merge, the learned-interval clear, the
report shape, the additive ``family_unresolved`` observation — is covered by that
equality. What they legitimately differ in, the criterion, is injected, so this test
cannot mask it.

The fixtures are imported from v0050's test module rather than rebuilt: a second
fake would be free to disagree about what a stored profile looks like, which is the
same failure one level down.
"""

from __future__ import annotations

import copy
from typing import Any

import pytest

from app.data_access.arango import collections as col
from app.domain.models.care_reminder import CareProfile
from app.migrations.support.care_profile_recompute import CareProfileRecompute, comparable
from app.migrations.versions.v0050_repair_care_profiles_family_and_guide import (
    _BROKEN_BOOTSTRAP_OUTPUT,
)
from app.migrations.versions.v0050_repair_care_profiles_family_and_guide import (
    migration as v0050,
)
from tests.unit.migrations.versions.test_v0050_repair_care_profiles_family_and_guide import (
    CULTIVAR_KEY,
    FAMILY_KEY,
    FAMILY_NAME,
    PLANT,
    SPECIES_KEY,
    _db,
    _plant,
    _species,
    _tropical_document,
)

_GUIDE = {
    "interval_days": 4,
    "watering_method": "bottom_water",
    "water_quality_hint": "Rainwater only",
    "practical_tip": "Keep it dry in winter",
}


def _v0050_criterion(stored: CareProfile, engine: Any, plant_key: str, inputs: Any) -> bool:
    """v0050's criterion, expressed against the shared machinery."""
    return comparable(stored) == _BROKEN_BOOTSTRAP_OUTPUT


def _shared_run() -> CareProfileRecompute:
    return CareProfileRecompute(version=v0050.version, name=v0050.name, is_untouched=_v0050_criterion)


def _fixture(scenario: str) -> dict[str, Any]:
    """A fresh copy of one scenario.

    Deliberately rebuilt per call: the runs mutate the documents they repair, so
    handing the same lists to both sides would let the first run turn the second
    one's population into ``already_correct`` — a parity test that compares two
    different inputs and passes for the wrong reason.
    """
    return copy.deepcopy(_scenarios()[scenario])


def _scenarios() -> dict[str, dict[str, Any]]:
    """One entry per classification v0050 can produce."""
    return {
        # repaired — a Cactaceae still holding the tropical fallback
        "repaired": {},
        # repaired through the tier-1 guide as well
        "repaired_with_guide": {"species": [_species(watering_guide=_GUIDE)]},
        # repaired with a cultivar override winning over the species guide
        "repaired_with_cultivar_override": {
            "plants": [_plant(cultivar_key=CULTIVAR_KEY)],
            "species": [_species(watering_guide=_GUIDE)],
            "cultivars": [
                {
                    "_key": CULTIVAR_KEY,
                    "name": "Nana",
                    "species_key": SPECIES_KEY,
                    "watering_guide_override": {**_GUIDE, "interval_days": 9},
                }
            ],
        },
        # skipped_user_edited — one field differs from the generator's output
        "user_edited": {"profiles": [_tropical_document(watering_interval_days=11)]},
        # already_correct — an unmapped family is correctly tropical
        "already_correct": {"families": [{"_key": FAMILY_KEY, "name": "Nothofagaceae"}]},
        # plant_missing — the plant was removed
        "plant_removed": {"plants": [_plant(removed_on="2026-09-01")]},
        # plant_missing — no plant document at all
        "plant_absent": {"plants": []},
        # family_unresolved — the species names a family document that is gone
        "family_unresolved": {"families": []},
        # unreadable — the profile document does not satisfy the model
        "unreadable_profile": {"profiles": [_tropical_document(watering_interval_days=0)]},
        # the season state and the learned intervals take their own paths
        "season_state": {
            "profiles": [
                _tropical_document(
                    dormancy_care_mode=True,
                    dormancy_watering="minimal",
                    watering_interval_learned=6,
                )
            ]
        },
        # an empty installation
        "empty": {"profiles": [], "plants": [], "species": [], "families": []},
    }


@pytest.mark.parametrize("scenario", sorted(_scenarios()))
@pytest.mark.parametrize("dry_run", [False, True], ids=["write", "dry_run"])
def test_the_shared_machinery_reports_what_v0050_reports(scenario: str, dry_run: bool) -> None:
    original = v0050.up(_db(**_fixture(scenario)), dry_run=dry_run)  # type: ignore[arg-type]
    shared = _shared_run().run(_db(**_fixture(scenario)), dry_run=dry_run)

    assert shared.scanned == original.scanned
    assert shared.changed == original.changed
    assert shared.dry_run == original.dry_run
    assert shared.precondition_unmet == original.precondition_unmet
    assert shared.details == original.details


def _without_write_timestamp(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The documents without ``updated_at``.

    It is the repository's wall clock, so the two runs differ in it by microseconds
    and by nothing else. Stripping exactly one named field — rather than comparing a
    subset of the rest — keeps every other field in the comparison, including any
    added later.
    """
    return [{name: value for name, value in row.items() if name != "updated_at"} for row in rows]


@pytest.mark.parametrize("scenario", sorted(_scenarios()))
def test_the_shared_machinery_writes_what_v0050_writes(scenario: str) -> None:
    """Not just the report — the stored document and the write calls."""
    original_db = _db(**_fixture(scenario))
    shared_db = _db(**_fixture(scenario))
    v0050.up(original_db)  # type: ignore[arg-type]
    _shared_run().run(shared_db)

    assert _without_write_timestamp(shared_db.collections[col.CARE_PROFILES]) == _without_write_timestamp(
        original_db.collections[col.CARE_PROFILES]
    )
    assert [(kind, name) for kind, name, _ in shared_db.writes] == [
        (kind, name) for kind, name, _ in original_db.writes
    ]
    assert _without_write_timestamp([payload for _, _, payload in shared_db.writes]) == _without_write_timestamp(
        [payload for _, _, payload in original_db.writes]
    )


def test_a_missing_collection_yields_the_same_pending_report() -> None:
    original_db = _db()
    shared_db = _db()
    del original_db.collections[col.SPECIES]
    del shared_db.collections[col.SPECIES]

    original = v0050.up(original_db)  # type: ignore[arg-type]
    shared = _shared_run().preconditions_unmet(shared_db, dry_run=False)

    assert shared is not None
    assert original.precondition_unmet is True
    assert shared.precondition_unmet is True
    assert shared.details == original.details


def test_the_parity_check_can_fail() -> None:
    """The measuring tool has to be able to bite.

    Driven with a criterion that accepts nothing, the shared machinery must report
    a *different* result than v0050 — otherwise this module would be green no matter
    what the copy does.
    """
    never = CareProfileRecompute(
        version=v0050.version,
        name=v0050.name,
        is_untouched=lambda *_args: False,
    )

    original = v0050.up(_db())  # type: ignore[arg-type]
    crippled = never.run(_db())

    assert original.changed == 1
    assert crippled.changed == 0
    assert crippled.details != original.details


def test_the_fixture_actually_exercises_every_category() -> None:
    """A parity test over scenarios that all land in one bucket proves little."""
    reached = set()
    for scenario in _scenarios():
        report = v0050.up(_db(**_fixture(scenario)))  # type: ignore[arg-type]
        reached.update(
            name
            for name in (
                "repaired",
                "skipped_user_edited",
                "already_correct",
                "plant_missing",
                "unreadable",
                "family_unresolved",
            )
            if report.details[f"{name}_total"]
        )
    assert reached == {
        "repaired",
        "skipped_user_edited",
        "already_correct",
        "plant_missing",
        "unreadable",
        "family_unresolved",
    }, f"scenarios only reach {sorted(reached)}"


def test_the_plant_key_travels_into_the_criterion() -> None:
    """The injected predicate is called with the arguments v0052 relies on."""
    seen: list[tuple[str, Any]] = []

    def record(stored: CareProfile, engine: Any, plant_key: str, inputs: Any) -> bool:
        seen.append((plant_key, inputs))
        return True

    CareProfileRecompute(version="0050", name="parity", is_untouched=record).run(
        _db(species=[_species(watering_guide=_GUIDE)])
    )

    assert [key for key, _ in seen] == [PLANT]
    assert seen[0][1].family_name == FAMILY_NAME
    assert seen[0][1].watering_guide is not None
