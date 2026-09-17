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
what ``auto_generate_profile`` returns with no family and no guide — the tier-3
``TROPICAL`` fallback — for that plant. Anything else is reported as
``skipped_user_edited`` and is not touched. A user who shortened one interval and
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

``care_profiles``, ``plant_instances``, ``species``, ``cultivars`` and
``botanical_families`` are created unconditionally by ``ensure_collections``, so a
missing one means a partially bootstrapped or restored database — and it would
change what gets *written* (without the catalogues every profile would look
correct and stay tropical). The run then reports ``precondition_unmet`` and stays
pending for a later boot (M-1) rather than being recorded applied over work it
could not do.

**Idempotent (M-3):** a repaired profile no longer equals the tier-3 fallback, so
a second run classifies it as ``skipped_user_edited`` or ``already_correct`` and
writes nothing. **Dry-run (M-5):** every category, every itemised row and every
total is computed without a write, identically to the real run.

**Not reversible (M-6).** The previous values are the defect, and restoring them
would be indistinguishable from overwriting an edit a user made in between. Every
changed row is itemised in ``details["repaired"]`` with its before/after care
style and watering interval (capped at 500 rows; the ``*_total`` counters are
exact), so a run can be read position by position before and after it happens.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import structlog
from arango.database import StandardDatabase

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

#: How many rows each itemised list carries. Totals are always exact.
_REPORT_SAMPLE_LIMIT = 500


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
    def _auto_generated_profiles(db: StandardDatabase) -> list[dict[str, Any]]:
        """Every profile the system generated — the only population that can qualify.

        ``auto_generated`` is necessary and not sufficient (a user edit leaves it
        ``true``), so it narrows the read and decides nothing; the per-profile
        comparison does that.
        """
        query = f"FOR profile IN {col.CARE_PROFILES} FILTER profile.auto_generated == true RETURN profile"
        return [dict(row) for row in db.aql.execute(query)]

    @staticmethod
    def _plants(db: StandardDatabase, plant_keys: list[str]) -> dict[str, dict[str, Any]]:
        """``plant _key → {species_key, cultivar_key, tenant_key, removed_on}``."""
        query = (
            f"FOR plant IN {col.PLANT_INSTANCES} FILTER plant._key IN @keys "
            "RETURN {key: plant._key, species: plant.species_key, cultivar: plant.cultivar_key, "
            "tenant: plant.tenant_key, removed_on: plant.removed_on}"
        )
        return {str(row["key"]): dict(row) for row in db.aql.execute(query, bind_vars={"keys": plant_keys})}

    @staticmethod
    def _species_index(db: StandardDatabase, species_keys: list[str]) -> dict[str, Species]:
        query = f"FOR s IN {col.SPECIES} FILTER s._key IN @keys RETURN s"
        rows = db.aql.execute(query, bind_vars={"keys": species_keys})
        return {str(row["_key"]): Species(**dict(row)) for row in rows}

    @staticmethod
    def _cultivar_index(db: StandardDatabase, cultivar_keys: list[str]) -> dict[str, Cultivar]:
        query = f"FOR c IN {col.CULTIVARS} FILTER c._key IN @keys RETURN c"
        return {
            str(row["_key"]): Cultivar(**dict(row)) for row in db.aql.execute(query, bind_vars={"keys": cultivar_keys})
        }

    @staticmethod
    def _family_names(db: StandardDatabase, family_keys: list[str]) -> dict[str, str]:
        """``botanical_families _key → name`` — the value ``FAMILY_CARE_MAP`` keys by."""
        query = f"FOR f IN {col.BOTANICAL_FAMILIES} FILTER f._key IN @keys RETURN {{key: f._key, name: f.name}}"
        return {
            str(row["key"]): str(row["name"] or "") for row in db.aql.execute(query, bind_vars={"keys": family_keys})
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

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:  # noqa: C901
        unmet = self._preconditions_unmet(db, dry_run=dry_run)
        if unmet is not None:
            return unmet

        profiles = self._auto_generated_profiles(db)
        if not profiles:
            logger.info("repair_care_profiles_noop", scanned=0, changed=0, dry_run=dry_run)
            return self._report(dry_run=dry_run, scanned=0, changed=0)

        plants = self._plants(db, sorted({str(p.get("plant_key") or "") for p in profiles if p.get("plant_key")}))
        species = self._species_index(db, sorted({str(p["species"]) for p in plants.values() if p.get("species")}))
        cultivars = self._cultivar_index(db, sorted({str(p["cultivar"]) for p in plants.values() if p.get("cultivar")}))
        families = self._family_names(db, sorted({s.family_key for s in species.values() if s.family_key}))

        engine = CareReminderEngine()
        repository = ArangoCareReminderRepository(db)

        buckets: dict[str, list[dict[str, Any]]] = {
            "repaired": [],
            "skipped_user_edited": [],
            "already_correct": [],
            "plant_missing": [],
        }
        totals: dict[str, int] = dict.fromkeys(buckets, 0)

        for document in profiles:
            profile_key = str(document.get("_key") or "")
            plant_key = str(document.get("plant_key") or "")
            stored = CareProfile(**document)
            plant = plants.get(plant_key)

            if plant is None or plant.get("removed_on") is not None:
                totals["plant_missing"] += 1
                self._append(
                    buckets["plant_missing"],
                    {
                        "profile_key": profile_key,
                        "plant_key": plant_key or None,
                        "reason": "plant_removed" if plant is not None else "plant_document_missing",
                    },
                )
                continue

            species_record = species.get(str(plant.get("species") or ""))
            cultivar_record = cultivars.get(str(plant.get("cultivar") or ""))

            # What the broken bootstrap produced for this plant: no family, no guide.
            # Identity with it is the whole criterion — see the module docstring.
            untouched = engine.auto_generate_profile(plant_key=plant_key)
            inputs = resolve_care_inputs(
                species_record,
                cultivar_record,
                resolve_family_name=families.get,
            )
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

            if _comparable(stored) != _comparable(untouched):
                totals["skipped_user_edited"] += 1
                self._append(buckets["skipped_user_edited"], row)
                continue

            if _comparable(recomputed) == _comparable(stored):
                totals["already_correct"] += 1
                self._append(buckets["already_correct"], {**row, "family_name": inputs.family_name})
                continue

            repaired = self._merge(stored, recomputed)
            totals["repaired"] += 1
            self._append(
                buckets["repaired"],
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

        logger.info(
            "repair_care_profiles",
            scanned=len(profiles),
            changed=totals["repaired"],
            skipped_user_edited=totals["skipped_user_edited"],
            already_correct=totals["already_correct"],
            plant_missing=totals["plant_missing"],
            dry_run=dry_run,
        )
        details: dict[str, Any] = {}
        for bucket, rows in buckets.items():
            details[bucket] = rows
            details[f"{bucket}_total"] = totals[bucket]
        return self._report(dry_run=dry_run, scanned=len(profiles), changed=totals["repaired"], **details)

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
        for field in _PRESERVED_FIELDS:
            data[field] = stored_data[field]
        for field in _LEARNED_FIELDS:
            data[field] = None
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

    @staticmethod
    def _append(sink: list[dict[str, Any]], row: Mapping[str, Any]) -> None:
        """Append one report row, up to :data:`_REPORT_SAMPLE_LIMIT`."""
        if len(sink) >= _REPORT_SAMPLE_LIMIT:
            return
        sink.append(dict(row))

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
        payload: dict[str, Any] = {
            "repaired": [],
            "repaired_total": 0,
            "skipped_user_edited": [],
            "skipped_user_edited_total": 0,
            "already_correct": [],
            "already_correct_total": 0,
            "plant_missing": [],
            "plant_missing_total": 0,
        }
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
