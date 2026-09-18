"""v0050 — recompute the care profiles that fell to TROPICAL since #1440 (#1489/#1481).

``_bootstrap_care_profile`` handed ``CareReminderEngine.auto_generate_profile`` the
value of ``Species.family_key`` — the server-assigned numeric ``_key`` of a
``botanical_families`` document — as ``botanical_family``, which
``FAMILY_CARE_MAP`` keys by **name**. Nothing matched, the engine returned the
``TROPICAL`` 7-day preset, and a care profile is written once and read thereafter:
every plant created through ``create_plant``, ``_spawn_pup`` or
``PlantingRunService.create_plants`` since #1440 carries tropical presets, a
Cactaceae included. ``watering_guide`` — the tier the engine's docstring calls
highest — was passed by nobody at all (#1481), so no stored profile has ever been
shaped by its species' own watering data.

Both are fixed on the creation path. This migration is for the population that
already exists.

## The criterion, and why it is not the one the issue proposed

The plan called for "a numeric family field **or** values equal to the TROPICAL
preset". Measured 2026-09-17: **``CareProfile`` has no family field at all**
(``app/domain/models/care_reminder.py``) — the family is consumed by the engine
and only the resulting ``care_style`` and interval values are stored. Half of the
proposed criterion therefore cannot be evaluated against anything, and the whole
weight falls on the second half.

The provenance marker was measured too, because a marker would have been the
better criterion: ``CareProfile.auto_generated`` exists and
``auto_generate_profile`` sets it — but ``CareReminderService.update_profile``
carries it through unchanged (``CareProfileUpdate`` does not expose it, and the
update merges over the stored document), so a profile a user edited by hand still
reads ``auto_generated: true``. It is a **necessary** condition here, never a
sufficient one, and it is used as such. There is no ``source`` / ``generated_by``
field on the model or written by v0048.

So the criterion is **exact identity with what the defective bootstrap produced**:
a profile is recomputed only when every field the generator writes still equals
:data:`_BROKEN_BOOTSTRAP_OUTPUT` — the tier-3 ``TROPICAL`` fallback as it stood
between #1440 and #1489, **frozen as a literal**. Deriving it from the live engine
would make this migration inert the day the presets move: every damaged profile
would read as "user-edited" and the run would repair nothing while reporting
cheerfully. Anything else is reported as ``skipped_user_edited`` and is not touched.

The two questions are asked in this order: **already correct first**, identity with
the broken output second. A profile this migration has repaired is no longer
identical to the broken output, so the other order filed every repaired row under
``skipped_user_edited`` on a second run — no wrong write, but a report that told the
operator their installation was full of hand-edited profiles.

``CareReminderService.update_profile`` now clears ``auto_generated`` on a real edit,
so future repairs have a marker this one could not have. It marks going forward
only, which is why the criterion here stays value-based. A user who shortened one interval and
left the rest keeps their whole profile: the moment a profile stops being exactly
the value nobody chose, this migration has no business deciding what part of it
was deliberate.

Two fields are deliberately outside the comparison:

* ``watering_interval_learned`` / ``fertilizing_interval_learned`` are written by
  the adaptive-learning engine from confirmations, not by a user — and they were
  learned *around the wrong base interval*. They are **reset to ``None``** on a
  repair, which is what ``update_profile`` already does when the base interval is
  edited explicitly (``care_reminder_service.py``, #622). The clear needs its own
  write: ``care_profiles`` is a merge-mode repository, so the full-model update
  drops a ``None`` instead of storing it — see :meth:`_clear_learned_intervals`.
* ``dormancy_care_mode`` / ``dormancy_watering`` / ``dormancy_check_interval_days``
  are toggled by the REQ-047 season state machine, not the user. They are
  **preserved** across the repair: comparing them would skip every plant whose site
  happens to be wintering, and overwriting them would take a live season state
  away.

## What a repaired profile becomes

The same call the creation path now makes: ``auto_generate_profile`` with the
family **name** behind ``species.family_key`` and the plant's watering guide
(the cultivar's ``watering_guide_override`` ahead of the species' own), through
the shared :func:`~app.domain.services.care_reminder_service.resolve_care_inputs`
— not a copy of that resolution. A copy is what produced the defect: three places
resolved the family and the one that mattered did not.

``_key``, ``plant_key``, ``created_at`` and the dormancy fields are carried over
from the stored document; ``updated_at`` is the repository's.

**A profile whose recomputation equals what it already holds is not written.** A
plant of an unknown family with no guide *should* be TROPICAL, and it is reported
as ``already_correct``, not as a change.

## Preconditions, idempotency, reversibility

**No document can abort the run.** ``Species``, ``Cultivar`` and ``CareProfile``
carry field constraints, and a stored document older than the current constraint
raises ``ValidationError`` on hydration. Unhandled, one such row would fail ``up()``
— and a failing pending migration is a fatal startup (``framework/runner.py``, M-4),
so a single legacy document would keep an installation from booting. Each is
hydrated on its own and a refusal is reported under ``unreadable`` (never as
``already_correct``: "we could not read it" must not be filed as "it is fine").

**Batched.** The population is read as keys and processed :data:`_BATCH_SIZE` at a
time, each batch scoping its own plant/species/cultivar/family reads, because this
runs under the startup lock where an installation-sized set of hydrated models is a
memory profile nobody chose.

``care_profiles``, ``plant_instances``, ``species``, ``cultivars`` and
``botanical_families`` are created unconditionally by ``ensure_collections``, so a
missing one means a partially bootstrapped or restored database — and it would
change what gets *written* (without the catalogues every profile would look
correct and stay tropical). The run then reports ``precondition_unmet`` and stays
pending for a later boot (M-1) rather than being recorded applied over work it
could not do.

**Idempotent (M-3):** a repaired profile already holds what the recomputation
produces, so a second run classifies it as ``already_correct`` and writes nothing.
**Dry-run (M-5):** every category, every itemised row and every total is computed
without a write, identically to the real run.

**Not reversible (M-6).** The previous values are the defect, and restoring them
would be indistinguishable from overwriting an edit a user made in between. Every
changed row is itemised in ``details["repaired"]`` with its before/after care
style and watering interval (capped at 500 rows; the ``*_total`` counters are
exact), so a run can be read position by position before and after it happens.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, TypeVar

import structlog
from arango.database import StandardDatabase
from pydantic import BaseModel, ValidationError

from app.data_access.arango import collections as col
from app.data_access.arango.care_reminder_repository import ArangoCareReminderRepository
from app.domain.engines.care_reminder_engine import CareReminderEngine
from app.domain.models.care_reminder import CareProfile
from app.domain.models.species import Cultivar, Species
from app.domain.services.care_reminder_service import resolve_care_inputs
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger(__name__)

#: Everything this migration reads from or writes to.
REQUIRED_COLLECTIONS: tuple[str, ...] = (
    col.CARE_PROFILES,
    col.PLANT_INSTANCES,
    col.SPECIES,
    col.CULTIVARS,
    col.BOTANICAL_FAMILIES,
)

#: Fields carried over from the stored profile onto the recomputed one. Identity
#: (``_key``/``plant_key``), history (``created_at``) and the REQ-047 season state,
#: which the state machine owns and no recomputation may take away.
_PRESERVED_FIELDS: frozenset[str] = frozenset(
    {
        "key",
        "plant_key",
        "created_at",
        "dormancy_care_mode",
        "dormancy_watering",
        "dormancy_check_interval_days",
    }
)

#: Reset on a repair rather than compared: learned around the wrong base interval,
#: and ``update_profile`` already resets them when the base is edited (#622).
_LEARNED_FIELDS: frozenset[str] = frozenset({"watering_interval_learned", "fertilizing_interval_learned"})

#: Never part of the comparison: assigned by the repository on write.
_VOLATILE_FIELDS: frozenset[str] = frozenset({"updated_at"})

#: **What the broken bootstrap actually wrote**, frozen as a literal (2026-09-17).
#:
#: This was computed from the live engine at first — and a migration that asks the
#: *current* code what the *old* code produced is inert the moment the presets move:
#: the next edit to ``CARE_STYLE_PRESETS[TROPICAL]`` would make every damaged profile
#: look "user-edited" and this migration would repair nothing while reporting
#: cheerfully. The population it has to recognise is historical, so the value has to
#: be historical too.
#:
#: It is the tier-3 fallback ``auto_generate_profile()`` returned with no family and
#: no guide between #1440 and #1489, in the shape :func:`_comparable` produces.
#: ``tests/unit/migrations/versions/test_v0050_repair_care_profiles_family_and_guide.py``
#: compares it against today's engine and goes red — with the reason — as soon as the
#: two part ways, which is the signal to decide whether the remaining population is
#: still worth repairing, not a licence to update the literal.
_BROKEN_BOOTSTRAP_OUTPUT: dict[str, Any] = {
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

#: How many rows each itemised list carries. Totals are always exact.
_REPORT_SAMPLE_LIMIT = 500

#: Profiles per batch. The population is read as keys and the documents are then
#: fetched a batch at a time, because this runs under the startup migration lock and
#: an installation-sized collection of hydrated models is not a memory profile
#: anybody chose. Each batch also scopes its own plant/species/cultivar/family reads.
_BATCH_SIZE = 1000

#: The report categories. ``repaired``, ``skipped_user_edited``, ``already_correct``,
#: ``plant_missing`` and ``unreadable`` are **exclusive** — every scanned profile
#: lands in exactly one. ``family_unresolved`` is **additive**: it records a species
#: whose ``family_key`` names no family document, which is an observation about the
#: data rather than a verdict on the profile.
_CATEGORIES: tuple[str, ...] = (
    "repaired",
    "skipped_user_edited",
    "already_correct",
    "plant_missing",
    "unreadable",
    "family_unresolved",
)

_ModelT = TypeVar("_ModelT", bound=BaseModel)


@dataclass
class _RunState:
    """Counters and capped row lists, carried across the batches of one run."""

    scanned: int = 0
    totals: dict[str, int] = field(default_factory=lambda: dict.fromkeys(_CATEGORIES, 0))
    buckets: dict[str, list[dict[str, Any]]] = field(default_factory=lambda: {name: [] for name in _CATEGORIES})

    def count(self, category: str, row: Mapping[str, Any]) -> None:
        """Count one row exactly, and itemise it up to :data:`_REPORT_SAMPLE_LIMIT`.

        The total and the list are incremented together on purpose: they drifted
        apart in the first draft of v0048's report, and a capped list beside an
        exact counter is only readable while nothing can update one without the
        other.
        """
        self.totals[category] += 1
        if len(self.buckets[category]) < _REPORT_SAMPLE_LIMIT:
            self.buckets[category].append(dict(row))


def _comparable(profile: CareProfile) -> dict[str, Any]:
    """The fields that decide "nobody has touched this profile".

    Everything the model holds except identity, history, the season state, the
    learned intervals and the write timestamp — so a field added to ``CareProfile``
    later is compared by default. Defaulting to *compared* means a new field makes
    this migration more conservative (more rows skipped), never less.
    """
    excluded = _PRESERVED_FIELDS | _LEARNED_FIELDS | _VOLATILE_FIELDS
    return {field: value for field, value in profile.model_dump(mode="json").items() if field not in excluded}


class RepairCareProfilesFamilyAndGuideMigration(Migration):
    version = "0050"
    name = "repair_care_profiles_family_and_guide"
    description = (
        "Recompute the auto-generated care profiles that still hold the TROPICAL "
        "fallback the broken bootstrap produced, from the family name and the "
        "species' watering guide (#1489, #1481)."
    )
    reversible = False

    # ── reads ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _auto_generated_profile_keys(db: StandardDatabase) -> list[str]:
        """The ``_key`` of every profile the system generated — the whole population.

        Keys only, and then the documents in batches (:data:`_BATCH_SIZE`): this runs
        under the startup migration lock, where holding an installation's entire
        ``care_profiles`` collection as hydrated models is a memory profile nobody
        chose. ``auto_generated`` is *necessary* and not sufficient (a user edit
        leaves it ``true``), so it narrows the read and decides nothing — the
        per-profile comparison does that.

        The keys are taken once, up front, and the batches then fetch by key. Paging
        the population with ``LIMIT``/``SKIP`` while writing into it would skip or
        repeat rows; a key list taken under the lock cannot.
        """
        query = f"FOR profile IN {col.CARE_PROFILES} FILTER profile.auto_generated == true RETURN profile._key"
        return [str(key) for key in db.aql.execute(query)]

    @staticmethod
    def _profiles(db: StandardDatabase, profile_keys: list[str]) -> list[dict[str, Any]]:
        """The full documents of one batch."""
        query = f"FOR profile IN {col.CARE_PROFILES} FILTER profile._key IN @keys RETURN profile"
        return [dict(row) for row in db.aql.execute(query, bind_vars={"keys": profile_keys})]

    @staticmethod
    def _plants(db: StandardDatabase, plant_keys: list[str]) -> dict[str, dict[str, Any]]:
        """``plant _key → {species_key, cultivar_key, tenant_key, removed_on}``.

        A projection to four scalars rather than a hydrated ``PlantInstance``: this
        read must not be able to fail on a plant document that no longer satisfies
        the model's constraints, because such a plant's *profile* is still this
        migration's business (see :meth:`_hydrate` for the same reasoning where a
        model is unavoidable).
        """
        query = (
            f"FOR plant IN {col.PLANT_INSTANCES} FILTER plant._key IN @keys "
            "RETURN {key: plant._key, species: plant.species_key, cultivar: plant.cultivar_key, "
            "tenant: plant.tenant_key, removed_on: plant.removed_on}"
        )
        return {str(row["key"]): dict(row) for row in db.aql.execute(query, bind_vars={"keys": plant_keys})}

    @classmethod
    def _species_index(cls, db: StandardDatabase, species_keys: list[str]) -> tuple[dict[str, Species], set[str]]:
        """``species _key → Species``, plus the keys that would not hydrate.

        ``Species`` and ``Cultivar`` carry field constraints, and a stored document
        older than the current constraint raises ``ValidationError``. Unhandled, one
        such row would abort ``up()`` — and the runner does not catch a failing
        pending migration (``framework/runner.py``, M-4 fatal startup), so a single
        legacy species document would keep the whole installation from booting. The
        row is skipped and *reported* instead; the profiles that depend on it become
        ``unreadable`` rather than silently "already correct".
        """
        query = f"FOR s IN {col.SPECIES} FILTER s._key IN @keys RETURN s"
        return cls._hydrate(db.aql.execute(query, bind_vars={"keys": species_keys}), Species, "species")

    @classmethod
    def _cultivar_index(cls, db: StandardDatabase, cultivar_keys: list[str]) -> tuple[dict[str, Cultivar], set[str]]:
        """``cultivar _key → Cultivar``, plus the keys that would not hydrate."""
        query = f"FOR c IN {col.CULTIVARS} FILTER c._key IN @keys RETURN c"
        return cls._hydrate(db.aql.execute(query, bind_vars={"keys": cultivar_keys}), Cultivar, "cultivars")

    @staticmethod
    def _hydrate(rows: Any, model: type[_ModelT], collection: str) -> tuple[dict[str, _ModelT], set[str]]:
        """Hydrate ``rows`` into ``model``, collecting the keys that refuse to."""
        index: dict[str, _ModelT] = {}
        unreadable: set[str] = set()
        for row in rows:
            document = dict(row)
            key = str(document.get("_key") or "")
            try:
                index[key] = model(**document)
            except ValidationError as exc:
                unreadable.add(key)
                logger.warning(
                    "repair_care_profiles_document_unreadable",
                    collection=collection,
                    document_key=key,
                    errors=exc.error_count(),
                )
        return index, unreadable

    @staticmethod
    def _family_names(db: StandardDatabase, family_keys: list[str]) -> dict[str, str]:
        """``botanical_families _key → name`` — the value ``FAMILY_CARE_MAP`` keys by.

        A family whose ``name`` is empty or absent is left **out** of the index, so
        the resolver answers ``None`` for it rather than handing the engine an empty
        string: ``""`` matches no map entry either, but it travels as if it were a
        name and would be reported as a resolved family.
        """
        query = f"FOR f IN {col.BOTANICAL_FAMILIES} FILTER f._key IN @keys RETURN {{key: f._key, name: f.name}}"
        return {
            str(row["key"]): str(row["name"])
            for row in db.aql.execute(query, bind_vars={"keys": family_keys})
            if row.get("name")
        }

    # ── entry point ───────────────────────────────────────────────────────────

    def _preconditions_unmet(self, db: StandardDatabase, *, dry_run: bool) -> MigrationReport | None:
        missing = [name for name in REQUIRED_COLLECTIONS if not db.has_collection(name)]
        if not missing:
            return None
        logger.warning(
            "repair_care_profiles_precondition_unmet",
            missing_collections=missing,
            dry_run=dry_run,
        )
        return self._report(
            dry_run=dry_run,
            scanned=0,
            changed=0,
            precondition_unmet=True,
            reason="required_collections_missing",
            missing_collections=missing,
        )

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        unmet = self._preconditions_unmet(db, dry_run=dry_run)
        if unmet is not None:
            return unmet

        profile_keys = self._auto_generated_profile_keys(db)
        if not profile_keys:
            logger.info("repair_care_profiles_noop", scanned=0, changed=0, dry_run=dry_run)
            return self._report(dry_run=dry_run, scanned=0, changed=0)

        engine = CareReminderEngine()
        repository = ArangoCareReminderRepository(db)
        state = _RunState()

        for start in range(0, len(profile_keys), _BATCH_SIZE):
            self._process_batch(
                db,
                profile_keys[start : start + _BATCH_SIZE],
                engine=engine,
                repository=repository,
                state=state,
                dry_run=dry_run,
            )

        logger.info(
            "repair_care_profiles",
            scanned=state.scanned,
            changed=state.totals["repaired"],
            skipped_user_edited=state.totals["skipped_user_edited"],
            already_correct=state.totals["already_correct"],
            plant_missing=state.totals["plant_missing"],
            unreadable=state.totals["unreadable"],
            family_unresolved=state.totals["family_unresolved"],
            dry_run=dry_run,
        )
        details: dict[str, Any] = {}
        for bucket, rows in state.buckets.items():
            details[bucket] = rows
            details[f"{bucket}_total"] = state.totals[bucket]
        return self._report(
            dry_run=dry_run,
            scanned=state.scanned,
            changed=state.totals["repaired"],
            **details,
        )

    def _process_batch(  # noqa: C901, PLR0912
        self,
        db: StandardDatabase,
        profile_keys: list[str],
        *,
        engine: CareReminderEngine,
        repository: ArangoCareReminderRepository,
        state: _RunState,
        dry_run: bool,
    ) -> None:
        """Classify — and, unless ``dry_run``, repair — one batch of profiles."""
        profiles = self._profiles(db, profile_keys)
        state.scanned += len(profiles)

        plants = self._plants(db, sorted({str(p.get("plant_key") or "") for p in profiles if p.get("plant_key")}))
        species, unreadable_species = self._species_index(
            db, sorted({str(p["species"]) for p in plants.values() if p.get("species")})
        )
        cultivars, unreadable_cultivars = self._cultivar_index(
            db, sorted({str(p["cultivar"]) for p in plants.values() if p.get("cultivar")})
        )
        families = self._family_names(db, sorted({s.family_key for s in species.values() if s.family_key}))

        for document in profiles:
            profile_key = str(document.get("_key") or "")
            plant_key = str(document.get("plant_key") or "")

            try:
                stored = CareProfile(**document)
            except ValidationError as exc:
                # The profile itself does not satisfy the model. Reported, never
                # raised: `up()` failing is a fatal startup (M-4), and one legacy
                # document must not cost an installation its boot.
                state.count(
                    "unreadable",
                    {
                        "profile_key": profile_key,
                        "plant_key": plant_key or None,
                        "reason": "profile_document_unreadable",
                        "errors": exc.error_count(),
                    },
                )
                continue

            plant = plants.get(plant_key)
            if plant is None or plant.get("removed_on") is not None:
                state.count(
                    "plant_missing",
                    {
                        "profile_key": profile_key,
                        "plant_key": plant_key or None,
                        "reason": "plant_removed" if plant is not None else "plant_document_missing",
                    },
                )
                continue

            species_key = str(plant.get("species") or "")
            cultivar_key = str(plant.get("cultivar") or "")
            if species_key in unreadable_species or cultivar_key in unreadable_cultivars:
                state.count(
                    "unreadable",
                    {
                        "profile_key": profile_key,
                        "plant_key": plant_key,
                        "reason": (
                            "species_unreadable" if species_key in unreadable_species else "cultivar_unreadable"
                        ),
                        "species_key": species_key or None,
                        "cultivar_key": cultivar_key or None,
                    },
                )
                continue

            species_record = species.get(species_key)
            cultivar_record = cultivars.get(cultivar_key)
            inputs = resolve_care_inputs(species_record, cultivar_record, resolve_family_name=families.get)
            recomputed = engine.auto_generate_profile(
                botanical_family=inputs.family_name,
                plant_key=plant_key,
                watering_guide=inputs.watering_guide,
            )

            row = {
                "profile_key": profile_key,
                "plant_key": plant_key,
                "tenant_key": plant.get("tenant"),
                "care_style": stored.care_style.value,
                "watering_interval_days": stored.watering_interval_days,
            }

            # Additive, not a bucket: a species whose `family_key` names no family
            # document can only be answered with TROPICAL, and that answer may well
            # be `already_correct` below. The operator still has to see it — it is
            # the difference between "correctly tropical" and "we could not tell".
            if species_record is not None and species_record.family_key and inputs.family_name is None:
                state.count(
                    "family_unresolved",
                    {
                        "profile_key": profile_key,
                        "plant_key": plant_key,
                        "species_key": species_key,
                        "family_key": species_record.family_key,
                    },
                )

            # ORDER MATTERS, and the first version had it wrong. "Already correct"
            # is asked FIRST: a profile this migration has already repaired is, by
            # construction, no longer identical to the broken output — so asking
            # "does it still look untouched?" first classified every repaired row as
            # ``skipped_user_edited``, and a second run would have reported the whole
            # installation as hand-edited. Nothing would have been written either way,
            # but the report is how an operator reads the run, and that report lied.
            if _comparable(recomputed) == _comparable(stored):
                state.count("already_correct", {**row, "family_name": inputs.family_name})
                continue

            # Identity with what the broken bootstrap wrote is the whole criterion,
            # against the FROZEN literal rather than today's engine — see
            # :data:`_BROKEN_BOOTSTRAP_OUTPUT`.
            if _comparable(stored) != _BROKEN_BOOTSTRAP_OUTPUT:
                state.count("skipped_user_edited", row)
                continue

            repaired = self._merge(stored, recomputed)
            state.count(
                "repaired",
                {
                    **row,
                    "family_name": inputs.family_name,
                    "watering_guide": inputs.watering_guide is not None,
                    "new_care_style": repaired.care_style.value,
                    "new_watering_interval_days": repaired.watering_interval_days,
                },
            )

            if not dry_run and profile_key:
                repository.update_profile(profile_key, repaired)
                self._clear_learned_intervals(repository, profile_key, stored)

    # ── the write ─────────────────────────────────────────────────────────────

    @staticmethod
    def _merge(stored: CareProfile, recomputed: CareProfile) -> CareProfile:
        """The recomputed profile, wearing the stored one's identity and season state.

        The learned intervals are dropped: they were learned around the interval
        this run is replacing, which is the same reason ``update_profile`` resets
        them on an explicit interval edit (#622).
        """
        data = recomputed.model_dump()
        stored_data = stored.model_dump()
        for preserved in _PRESERVED_FIELDS:
            data[preserved] = stored_data[preserved]
        for learned in _LEARNED_FIELDS:
            data[learned] = None
        data["auto_generated"] = True
        return CareProfile(**data)

    @staticmethod
    def _clear_learned_intervals(
        repository: ArangoCareReminderRepository,
        profile_key: str,
        stored: CareProfile,
    ) -> None:
        """Null the learned intervals — a second write, because the first cannot.

        Measured: ``care_profiles`` is a **merge**-mode repository
        (``BaseArangoRepository._update_is_full_replace`` is ``False`` for it), so
        ``update_profile`` serialises with ``exclude_none=True`` and a field set to
        ``None`` is dropped from the payload rather than written as ``null`` — the
        stored value survives an update that meant to clear it. ``update_fields``
        is the path that writes ``keep_none=True``, so the clear goes through it,
        and only for a profile that actually holds a learned value.

        (The same property means ``CareReminderService.reset_profile`` cannot clear
        a field either; that is outside this migration and reported separately.)
        """
        pending = {field: None for field in sorted(_LEARNED_FIELDS) if getattr(stored, field) is not None}
        if pending:
            repository.update_fields(profile_key, pending)

    # ── report plumbing ───────────────────────────────────────────────────────

    def _report(
        self,
        *,
        dry_run: bool,
        scanned: int,
        changed: int,
        precondition_unmet: bool = False,
        **details: Any,
    ) -> MigrationReport:
        """One report shape for every exit, so a consumer never has to probe keys."""
        payload: dict[str, Any] = {}
        for category in _CATEGORIES:
            payload[category] = []
            payload[f"{category}_total"] = 0
        payload.update(details)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=scanned,
            changed=changed,
            dry_run=dry_run,
            precondition_unmet=precondition_unmet,
            details=payload,
        )


migration = RepairCareProfilesFamilyAndGuideMigration()
