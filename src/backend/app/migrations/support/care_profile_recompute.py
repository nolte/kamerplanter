"""The care-profile recompute machinery, outside any ``Migration`` class (#1505).

Two migrations recompute stored care profiles from the current engine: v0050
(#1489/#1481, the profiles the broken bootstrap wrote) and v0052 (#1505, the
profiles whose botanical family ``FAMILY_CARE_MAP`` only now covers). Everything
but the *criterion* is the same work: the batched reads under the startup lock,
the per-document hydration that keeps a legacy row from aborting ``up()``, the
order of the classification questions, the merge that preserves identity and the
REQ-047 season state, the learned-interval clear, and the report shape.

Why a module and not a base class
=================================

The obvious move — have v0052 subclass v0050 and override one method — was the
first draft of #1505 and it is **wrong**, because ``Migration.checksum()`` hashes
``inspect.getsource(type(self))`` (``framework/base.py``). Extracting a seam from
v0050's class changes v0050's class source, so every installation that had already
applied v0050 would log ``migration_checksum_drift`` forever: applied migrations
are immutable (M-7), and a correction ships as a new version, never as an edit.

So v0050's source is frozen exactly as it shipped — ``tests/unit/migrations/
versions/test_v0050_source_is_frozen.py`` pins its class checksum — and this
module carries the machinery for everything that comes after it. It is therefore
a **copy** of v0050's logic, which is the thing this project distrusts most: a
copy is free to disagree with its original. That is why
``tests/unit/migrations/support/test_care_profile_recompute_matches_v0050.py``
drives this module with v0050's own criterion over v0050's own fixtures and
requires the two reports to be equal, field for field. The copy cannot drift
silently; it can only drift loudly.

What the caller supplies
========================

A :class:`CareProfileRecompute` is built with the migration's ``version`` and
``name`` (they go into the report) and one predicate, ``is_untouched`` — "does
this stored profile still hold exactly what generated it, with no user edit?".
That predicate is the *only* thing the two migrations disagree about:

* v0050 asks for identity with a frozen literal of the tier-3 tropical preset.
* v0052 asks for identity with what the generator produced before the family map
  grew (tier 3 plus the plant's own ``WateringGuide``).

The question **before** it — "is the recomputation already what the profile
holds?" — is asked first and is not configurable, because getting that order
wrong made v0050's second run report a whole installation as hand-edited.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
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
from app.domain.services.care_reminder_service import CareInputs, resolve_care_inputs
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger(__name__)

#: Everything a recompute run reads from or writes to.
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
PRESERVED_FIELDS: frozenset[str] = frozenset(
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
LEARNED_FIELDS: frozenset[str] = frozenset({"watering_interval_learned", "fertilizing_interval_learned"})

#: Never part of the comparison: assigned by the repository on write.
VOLATILE_FIELDS: frozenset[str] = frozenset({"updated_at"})

#: The report categories. ``repaired``, ``skipped_user_edited``, ``already_correct``,
#: ``plant_missing`` and ``unreadable`` are **exclusive** — every scanned profile
#: lands in exactly one. ``family_unresolved`` is **additive**: it records a species
#: whose ``family_key`` names no family document, which is an observation about the
#: data rather than a verdict on the profile.
CATEGORIES: tuple[str, ...] = (
    "repaired",
    "skipped_user_edited",
    "already_correct",
    "plant_missing",
    "unreadable",
    "family_unresolved",
)

#: How many rows each itemised list carries. Totals are always exact.
REPORT_SAMPLE_LIMIT = 500

#: Profiles per batch. The population is read as keys and the documents are then
#: fetched a batch at a time, because this runs under the startup migration lock and
#: an installation-sized collection of hydrated models is not a memory profile
#: anybody chose. Each batch also scopes its own plant/species/cultivar/family reads.
BATCH_SIZE = 1000

_ModelT = TypeVar("_ModelT", bound=BaseModel)

#: ``(stored, engine, plant_key, inputs) -> bool`` — see the module docstring.
UntouchedPredicate = Callable[[CareProfile, CareReminderEngine, str, CareInputs], bool]


def comparable(profile: CareProfile) -> dict[str, Any]:
    """The fields that decide "nobody has touched this profile".

    Everything the model holds except identity, history, the season state, the
    learned intervals and the write timestamp — so a field added to ``CareProfile``
    later is compared by default. Defaulting to *compared* means a new field makes
    a recompute run more conservative (more rows skipped), never less.
    """
    excluded = PRESERVED_FIELDS | LEARNED_FIELDS | VOLATILE_FIELDS
    return {name: value for name, value in profile.model_dump(mode="json").items() if name not in excluded}


@dataclass
class RunState:
    """Counters and capped row lists, carried across the batches of one run."""

    scanned: int = 0
    totals: dict[str, int] = field(default_factory=lambda: dict.fromkeys(CATEGORIES, 0))
    buckets: dict[str, list[dict[str, Any]]] = field(default_factory=lambda: {name: [] for name in CATEGORIES})

    def count(self, category: str, row: Mapping[str, Any]) -> None:
        """Count one row exactly, and itemise it up to :data:`REPORT_SAMPLE_LIMIT`.

        The total and the list are incremented together on purpose: they drifted
        apart in the first draft of v0048's report, and a capped list beside an
        exact counter is only readable while nothing can update one without the
        other.
        """
        self.totals[category] += 1
        if len(self.buckets[category]) < REPORT_SAMPLE_LIMIT:
            self.buckets[category].append(dict(row))


class CareProfileRecompute:
    """One recompute run: the shared machinery plus the caller's criterion."""

    def __init__(self, *, version: str, name: str, is_untouched: UntouchedPredicate) -> None:
        self.version = version
        self.name = name
        self._is_untouched = is_untouched

    # ── reads ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _auto_generated_profile_keys(db: StandardDatabase) -> list[str]:
        """The ``_key`` of every profile the system generated — the whole population.

        Keys only, and then the documents in batches (:data:`BATCH_SIZE`): this runs
        under the startup migration lock, where holding an installation's entire
        ``care_profiles`` collection as hydrated models is a memory profile nobody
        chose. ``auto_generated`` is *necessary* and not sufficient (a user edit
        leaves it ``true`` on profiles written before #1507), so it narrows the read
        and decides nothing — the per-profile comparison does that.

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
        run's business (see :meth:`_hydrate` for the same reasoning where a model is
        unavoidable).
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
                    "recompute_care_profiles_document_unreadable",
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

    # ── entry points ──────────────────────────────────────────────────────────

    def preconditions_unmet(self, db: StandardDatabase, *, dry_run: bool) -> MigrationReport | None:
        """``None`` when every required collection exists, else the pending report.

        ``care_profiles``, ``plant_instances``, ``species``, ``cultivars`` and
        ``botanical_families`` are created unconditionally by ``ensure_collections``,
        so a missing one means a partially bootstrapped or restored database — and it
        would change what gets *written* (without the catalogues every profile would
        look correct and stay tropical). The run then reports ``precondition_unmet``
        and stays pending for a later boot (M-1) rather than being recorded applied
        over work it could not do.
        """
        missing = [name for name in REQUIRED_COLLECTIONS if not db.has_collection(name)]
        if not missing:
            return None
        logger.warning(
            "recompute_care_profiles_precondition_unmet",
            migration=self.version,
            missing_collections=missing,
            dry_run=dry_run,
        )
        return self.report(
            dry_run=dry_run,
            scanned=0,
            changed=0,
            precondition_unmet=True,
            reason="required_collections_missing",
            missing_collections=missing,
        )

    def run(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        """Classify — and, unless ``dry_run``, recompute — the whole population."""
        profile_keys = self._auto_generated_profile_keys(db)
        if not profile_keys:
            logger.info("recompute_care_profiles_noop", migration=self.version, scanned=0, changed=0, dry_run=dry_run)
            return self.report(dry_run=dry_run, scanned=0, changed=0)

        engine = CareReminderEngine()
        repository = ArangoCareReminderRepository(db)
        state = RunState()

        for start in range(0, len(profile_keys), BATCH_SIZE):
            self._process_batch(
                db,
                profile_keys[start : start + BATCH_SIZE],
                engine=engine,
                repository=repository,
                state=state,
                dry_run=dry_run,
            )

        logger.info(
            "recompute_care_profiles",
            migration=self.version,
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
        return self.report(
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
        state: RunState,
        dry_run: bool,
    ) -> None:
        """Classify — and, unless ``dry_run``, recompute — one batch of profiles."""
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

            # ORDER MATTERS, and v0050's first draft had it wrong. "Already correct"
            # is asked FIRST: a profile a run has already recomputed is, by
            # construction, no longer what generated it — so asking "does it still
            # look untouched?" first classified every recomputed row as
            # ``skipped_user_edited``, and a second run reported the whole
            # installation as hand-edited. Nothing would have been written either
            # way, but the report is how an operator reads the run.
            if comparable(recomputed) == comparable(stored):
                state.count("already_correct", {**row, "family_name": inputs.family_name})
                continue

            if not self._is_untouched(stored, engine, plant_key, inputs):
                state.count("skipped_user_edited", row)
                continue

            repaired = self.merge(stored, recomputed)
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
                self.clear_learned_intervals(repository, profile_key, stored)

    # ── the write ─────────────────────────────────────────────────────────────

    @staticmethod
    def merge(stored: CareProfile, recomputed: CareProfile) -> CareProfile:
        """The recomputed profile, wearing the stored one's identity and season state.

        The learned intervals are dropped: they were learned around the interval the
        run is replacing, which is the same reason ``update_profile`` resets them on
        an explicit interval edit (#622).
        """
        data = recomputed.model_dump()
        stored_data = stored.model_dump()
        for preserved in PRESERVED_FIELDS:
            data[preserved] = stored_data[preserved]
        for learned in LEARNED_FIELDS:
            data[learned] = None
        data["auto_generated"] = True
        return CareProfile(**data)

    @staticmethod
    def clear_learned_intervals(
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
        """
        pending = {name: None for name in sorted(LEARNED_FIELDS) if getattr(stored, name) is not None}
        if pending:
            repository.update_fields(profile_key, pending)

    # ── report plumbing ───────────────────────────────────────────────────────

    def report(
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
        for category in CATEGORIES:
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
