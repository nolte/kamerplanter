"""v0051 — recompute the care profiles whose family FAMILY_CARE_MAP only now knows (#1505).

``FAMILY_CARE_MAP`` covered 14 of the 63 botanical families the seeds create. The
other 49 — Solanaceae, Brassicaceae, Rosaceae, Poaceae, Fabaceae and the rest of
the kitchen garden among them — reached tier 3 and were answered with the
``TROPICAL`` 7-day houseplant preset. A care profile is written once and read
thereafter, so every plant of those families that an installation already holds
carries that answer. This migration is for that population; the map itself is the
fix on the creation path.

## Why v0050 does not already cover it

v0050 recomputes through the **live** engine, so on an installation that has not
booted since #1507 it would pick the extended map up on its own. But an
installation that already ran it did not: for a Solanaceae the recomputation then
produced the same tropical values the profile held, the row was reported
``already_correct``, nothing was written — and v0050 is recorded applied and never
runs again.

The shared machinery therefore lives in
:mod:`app.migrations.support.care_profile_recompute`, **not** in v0050's class.
Extracting a seam from v0050 was the first draft of this change and it was wrong:
``Migration.checksum()`` hashes ``inspect.getsource(type(self))``, so editing an
applied migration's class makes every installation that ran it log
``migration_checksum_drift`` for good (M-7 — applied migrations are immutable). The
support module is a copy of v0050's logic, and
``tests/unit/migrations/support/test_care_profile_recompute_matches_v0050.py``
drives it with v0050's own criterion over v0050's own fixtures and requires the two
reports to match field for field, so the copy cannot drift quietly.

## The criterion, and why it is not v0050's frozen literal

v0050 asks "is this byte-identical to what the broken bootstrap wrote", against a
frozen literal of the tier-3 tropical preset. That criterion is right for its
population and **wrong for this one**: a plant whose species carries a
``WateringGuide`` was already repaired by v0050 (tropical style, guide-derived
watering fields), so it no longer equals that literal, and reusing the check would
file every such plant under ``skipped_user_edited`` — the class of plant the tomato
in the issue title belongs to.

The criterion here is therefore **identity with what the generator produced before
the map grew**: ``auto_generate_profile`` with ``botanical_family=None`` and the
plant's own guide — tier 3 plus tier 1, the two tiers #1505 did not touch. That is
computed from today's engine, which is the thing v0050's docstring warns about, so
it is bounded by a precondition instead of a promise: **if either tier has moved
since this migration was written, the run refuses.** Both are frozen and both are
checked — :data:`_PRE_1505_TROPICAL_FALLBACK` for the no-guide path and
:data:`_PRE_1505_TROPICAL_FALLBACK_WITH_GUIDE` for the guide overlay, because the
criterion exercises the overlay too and a guard that only measured tier 3 would
stay green while every plant with a guide was misclassified. See
:func:`tropical_fallback_drift`.

The order of the two questions is the shared machinery's and stays shared:
**already correct first**. A plant of a family the map knew all along (Araceae,
Cactaceae) recomputes to exactly what it holds and is reported ``already_correct``,
never as "user edited" — and never written.

## What a recomputed profile becomes

``auto_generate_profile`` with the family **name** behind ``species.family_key``
and the plant's watering guide, resolved through the shared
``resolve_care_inputs`` — the same call the creation path makes. A Solanaceae
tomato goes from ``tropical`` / 7 days to ``outdoor_annual_veg`` / 3 days; a
Nymphaea to the new ``aquatic`` preset. Identity, history and the REQ-047 season
state are carried over and the learned intervals reset.

## Preconditions, idempotency, reversibility

From the shared machinery and unchanged from v0050: batched reads under the
startup lock, per-document hydration so no legacy row can abort ``up()`` (a failing
pending migration is a fatal startup, M-4), ``precondition_unmet`` when a required
collection is missing, an exact dry run (M-5), and not reversible (M-6) — the
previous value is the defect. **Idempotent (M-3):** a recomputed profile holds what
the next recomputation produces, so a second run classifies it ``already_correct``
and writes nothing.

One precondition is this migration's own: the tier drift check described above. It
reports ``precondition_unmet`` with ``reason="tropical_fallback_moved"``, which
leaves the migration pending for a later boot (M-1) rather than recorded applied
over a population it could no longer identify.
"""

from __future__ import annotations

from typing import Any

import structlog
from arango.database import StandardDatabase

from app.common.enums import WateringMethod
from app.domain.engines.care_reminder_engine import CareReminderEngine
from app.domain.models.care_reminder import CareProfile
from app.domain.models.species import SeasonalWateringAdjustment, WateringGuide
from app.domain.services.care_reminder_service import CareInputs
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport
from app.migrations.support.care_profile_recompute import CareProfileRecompute, comparable

logger = structlog.get_logger(__name__)

#: The tier-3 fallback as it stood when this migration was written (2026-09-18), in
#: the shape :func:`~app.migrations.support.care_profile_recompute.comparable`
#: produces — identical to v0050's ``_BROKEN_BOOTSTRAP_OUTPUT``, and deliberately a
#: second copy: the two answer different questions and must be free to part ways
#: without one silently changing the other's population.
#:
#: It is not the criterion. It is the **guard on** the criterion: this migration
#: recognises its population by asking today's engine what it returns for a plant
#: with no family, and that answer is only the historical one while the tropical
#: preset has not moved.
_PRE_1505_TROPICAL_FALLBACK: dict[str, Any] = {
    "adaptive_learning_enabled": True,
    "auto_create_fertilizing_task": True,
    "auto_create_pest_check_task": True,
    "auto_create_repotting_task": True,
    "auto_create_watering_task": True,
    "auto_generated": True,
    "care_style": "tropical",
    "fertilizing_active_months": [3, 4, 5, 6, 7, 8, 9],
    "fertilizing_interval_days": 14,
    "humidity_check_enabled": True,
    "humidity_check_interval_days": 7,
    "location_check_enabled": False,
    "location_check_months": [],
    "notes": None,
    "pest_check_interval_days": 14,
    "repotting_interval_months": 24,
    "water_quality_hint": None,
    "watering_interval_days": 7,
    "watering_method": "top_water",
    "winter_watering_multiplier": 1.5,
}

#: A guide chosen so that **every** field the tier-1 overlay writes differs from the
#: tier-3 preset: the interval (4 vs 7), the method (bottom vs top water), the water
#: quality hint (set vs ``None``), ``notes`` from ``practical_tip`` (set vs ``None``)
#: and the winter multiplier, which is *computed* (9 / 4 → 2.25) rather than copied
#: and is the field most likely to move unnoticed.
_REFERENCE_GUIDE = WateringGuide(
    interval_days=4,
    watering_method=WateringMethod.BOTTOM_WATER,
    water_quality_hint="Rainwater only",
    practical_tip="Keep it dry in winter",
    seasonal_adjustments=[SeasonalWateringAdjustment(months=[11, 12, 1, 2], interval_days=9)],
)

#: What tier 3 **plus** the tier-1 overlay produced for :data:`_REFERENCE_GUIDE`
#: when this migration was written.
#:
#: Measuring only the no-guide path would leave the larger half of the criterion
#: unguarded (review finding SCR-001): the criterion calls the engine *with* the
#: plant's guide, so a later change to how a guide is applied — the multiplier
#: rounding, ``notes``, which fields the overlay touches — would keep a tier-3-only
#: guard green while every plant with a guide was classified ``skipped_user_edited``
#: and left tropical for good. That is exactly the failure this migration exists to
#: undo, so it is measured rather than assumed.
_PRE_1505_TROPICAL_FALLBACK_WITH_GUIDE: dict[str, Any] = {
    **_PRE_1505_TROPICAL_FALLBACK,
    "notes": "Keep it dry in winter",
    "water_quality_hint": "Rainwater only",
    "watering_interval_days": 4,
    "watering_method": "bottom_water",
    "winter_watering_multiplier": 2.25,
}


def tropical_fallback_drift(engine: CareReminderEngine) -> list[str]:
    """The fields in which today's pre-#1505 generator output differs from the frozen one.

    Both paths the criterion uses are measured: tier 3 alone, and tier 3 with
    :data:`_REFERENCE_GUIDE` laid over it. A field is reported as ``"<field>"`` when
    the no-guide path moved and ``"guide:<field>"`` when the overlay did, so the
    refusal names which half drifted.

    Empty ⇒ the engine still answers a plant of an unknown family exactly as it did
    when this migration was written, so "what the generator produced before the map
    grew" can be computed from it.
    """
    drift: list[str] = []
    for prefix, guide, frozen in (
        ("", None, _PRE_1505_TROPICAL_FALLBACK),
        ("guide:", _REFERENCE_GUIDE, _PRE_1505_TROPICAL_FALLBACK_WITH_GUIDE),
    ):
        current = comparable(engine.auto_generate_profile(botanical_family=None, plant_key="", watering_guide=guide))
        fields = set(current) | set(frozen)
        drift.extend(f"{prefix}{name}" for name in sorted(fields) if current.get(name) != frozen.get(name))
    return drift


def _is_pre_1505_generator_output(
    stored: CareProfile,
    engine: CareReminderEngine,
    plant_key: str,
    inputs: CareInputs,
) -> bool:
    """Is ``stored`` exactly what the generator produced before the map grew?

    Tier 3 (the tropical fallback) plus tier 1 (the species' or cultivar's
    ``WateringGuide``, which #1481 made real and v0050 already applied) — the two
    tiers #1505 left untouched. Passing ``botanical_family=None`` reproduces the
    *absence* of a family entry, which is what an unmapped family amounted to.

    The guide has to take part: without it this would only recognise the plants
    whose species carries no watering data, and the ones v0050 already repaired —
    tropical style, guide-derived watering — would be filed as hand-edited.
    """
    previous = engine.auto_generate_profile(
        botanical_family=None,
        plant_key=plant_key,
        watering_guide=inputs.watering_guide,
    )
    return comparable(stored) == comparable(previous)


class RecomputeCareProfilesNewlyMappedFamiliesMigration(Migration):
    """The shared recompute run, with "untouched" meaning "the pre-#1505 output"."""

    version = "0051"
    name = "recompute_care_profiles_newly_mapped_families"
    description = (
        "Recompute the auto-generated care profiles that still hold the TROPICAL "
        "fallback for a botanical family FAMILY_CARE_MAP only now covers (#1505)."
    )
    reversible = False

    def _recompute(self) -> CareProfileRecompute:
        return CareProfileRecompute(
            version=self.version,
            name=self.name,
            is_untouched=_is_pre_1505_generator_output,
        )

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        recompute = self._recompute()

        unmet = recompute.preconditions_unmet(db, dry_run=dry_run)
        if unmet is not None:
            return unmet

        drift = tropical_fallback_drift(CareReminderEngine())
        if drift:
            # The yardstick moved. Recomputing anyway would classify the whole
            # population as user-edited (no write, and a report that says the
            # installation is clean) or, worse, recognise profiles that were never
            # the fallback.
            logger.warning(
                "recompute_care_profiles_tropical_fallback_moved",
                changed_fields=drift,
                dry_run=dry_run,
            )
            return recompute.report(
                dry_run=dry_run,
                scanned=0,
                changed=0,
                precondition_unmet=True,
                reason="tropical_fallback_moved",
                changed_fields=drift,
            )

        return recompute.run(db, dry_run=dry_run)


migration = RecomputeCareProfilesNewlyMappedFamiliesMigration()
