"""ArangoDB read model of a bed's standing plants for the plan's markers and bubbles (REQ-053 WP 3.7, GP-API-054).

``locations`` and ``slots`` carry no ``tenant_key`` (E-01, #2107): the service resolves the bed through the
ownership anchor first, and **every** query below still filters the *plants* and everything joined to them
(tasks, care events, detections, harvest batches) on ``@tenant_key`` — a document of another tenant that
happens to name this bed's or a plant's key is never part of the answer. The slot of a plant is read only when
it belongs to the requested bed.

Five statements for a window of plants, whatever its size: the plants (with species, cultivar, slot and phase
joined in), their open tasks, the watering/feeding care events, the open findings, the harvest batches. A phase is
looked up in the phase-sequence key space first and in the legacy growth-phase key space second, the order of
``PhaseKeyResolver`` (#579): a plant on a sequence-driven species carries an entry key.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any, cast

from arango.cursor import Cursor
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.domain.calculators.overdue_calculator import utc_day
from app.domain.calculators.plant_state_calculator import OpenTask
from app.domain.interfaces.plant_state_repository import IPlantStateRepository, NextTask, PlantStateSource

#: Statuses of a task that is still to do. Suggestions (``suggested = true``) are proposals, not work.
_OPEN_TASK_STATUSES = ("pending", "in_progress")
#: Care categories that answer "last watered / last fed" (GP-FR-190).
WATERING_CATEGORY = "watering"
FEEDING_CATEGORY = "feeding"
#: How far back a watering/feeding event counts as "last" — bounds the scan of a bed with years of events.
CARE_LOOKBACK_DAYS = 180
#: A detection is an open finding for this long, unless every finding of it was rejected (REQ-044 feedback).
#: A placeholder, operator question 1 of #2455.
FINDING_OPEN_DAYS = 30
#: Finding categories that need action; beneficials and rejects do not (REQ-044 §9.1).
_ACTIONABLE_FINDING_CATEGORIES = ("pest", "symptom")
#: Harvest types that keep the plant standing (§11.3 "in Ernte").
_STANDING_HARVEST_TYPES = ("partial", "continuous")


def _date(value: Any) -> date | None:
    """An ISO date (or datetime) string of a stored document as a ``date``; anything else is ``None``."""
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _due_day(value: Any) -> date | None:
    """The UTC calendar day a task is due: the one definition of "overdue" (#2461), not the date prefix."""
    return utc_day(value or None)


def _datetime(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def _latest(care: dict[tuple[str | None, str], datetime], plant_key: str, category: str) -> datetime | None:
    """The newer of the plant's own event and the bed-wide one (no plants named) of ``category``."""
    own: datetime | None = care.get((plant_key, category))
    wide: datetime | None = care.get((None, category))
    moments = [moment for moment in (own, wide) if moment is not None]
    return max(moments) if moments else None


class ArangoPlantStateRepository(IPlantStateRepository):
    def __init__(self, db: StandardDatabase) -> None:
        self._db = db

    def list_bed_plants(
        self, location_key: str, *, tenant_key: str, now: datetime, offset: int, limit: int
    ) -> list[PlantStateSource]:
        if not tenant_key:
            raise ValueError("list_bed_plants needs a tenant_key (an empty tenant is no tenant, #2107).")
        plants = self._plants(location_key, tenant_key, offset, limit)
        if not plants:
            return []
        plant_keys = [row["plant_key"] for row in plants]
        run_keys = sorted({row["run_key"] for row in plants if row["run_key"]})
        tasks = self._tasks(plant_keys, run_keys, tenant_key)
        care = self._care(location_key, plant_keys, tenant_key, now)
        findings = self._findings(plant_keys, tenant_key, now)
        harvests = self._harvests(plant_keys, tenant_key)
        return [self._source(row, tasks, care, findings, harvests) for row in plants]

    # ── Statements ────────────────────────────────────────────────────

    def _plants(self, location_key: str, tenant_key: str, offset: int, limit: int) -> list[dict[str, Any]]:
        bind_vars: dict[str, Any] = {
            "@plants": col.PLANT_INSTANCES,
            "@run_contains": col.RUN_CONTAINS,
            "species": col.SPECIES,
            "cultivars": col.CULTIVARS,
            "slots": col.SLOTS,
            "phases": col.GROWTH_PHASES,
            "entries": col.PHASE_SEQUENCE_ENTRIES,
            "definitions": col.PHASE_DEFINITIONS,
            "tenant_key": tenant_key,
            "location_key": location_key,
            "offset": offset,
            "limit": limit,
        }
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                """
            FOR p IN @@plants
                FILTER p.tenant_key == @tenant_key AND p.location_key == @location_key AND p.removed_on == null
                SORT p._key ASC
                LIMIT @offset, @limit
                LET species = DOCUMENT(@species, p.species_key)
                LET cultivar = p.cultivar_key == null ? null : DOCUMENT(@cultivars, p.cultivar_key)
                LET slot = p.slot_key == null ? null : DOCUMENT(@slots, p.slot_key)
                LET entry = p.current_phase_key == null ? null : DOCUMENT(@entries, p.current_phase_key)
                LET definition = entry == null ? null : DOCUMENT(@definitions, entry.phase_definition_key)
                LET legacy = (p.current_phase_key == null OR entry != null)
                    ? null
                    : DOCUMENT(@phases, p.current_phase_key)
                LET run_key = FIRST(
                    FOR e IN @@run_contains
                        FILTER e._to == p._id AND e.detached_at == null
                        SORT e._from ASC
                        LIMIT 1
                        RETURN PARSE_IDENTIFIER(e._from).key
                )
                RETURN {
                    plant_key: p._key,
                    instance_id: p.instance_id,
                    species_key: p.species_key,
                    cultivar_key: p.cultivar_key,
                    planted_on: p.planted_on,
                    slot_key: slot != null AND slot.location_key == @location_key ? slot._key : null,
                    slot_id: slot != null AND slot.location_key == @location_key ? slot.slot_id : null,
                    species_name: species == null ? null : FIRST(species.common_names),
                    scientific_name: species == null ? null : species.scientific_name,
                    cultivar_name: cultivar == null ? null : cultivar.name,
                    phase_key: p.current_phase_key,
                    phase_name: entry != null
                        ? (definition == null ? null : (definition.display_name || definition.name))
                        : (legacy == null ? null : (legacy.display_name || legacy.name)),
                    phase_started_at: p.current_phase_started_at,
                    phase_typical_days: entry != null
                        ? (entry.override_duration_days
                            || (definition == null ? null : definition.typical_duration_days))
                        : (legacy == null ? null : legacy.typical_duration_days),
                    phase_allows_harvest: entry != null
                        ? entry.allows_harvest == true
                        : (legacy != null AND legacy.allows_harvest == true),
                    phase_is_terminal: entry != null
                        ? entry.is_terminal == true
                        : (legacy != null AND legacy.is_terminal == true),
                    cover_photo_ref: p.cover_photo_ref || FIRST(p.photo_refs),
                    run_key: run_key
                }
            """,
                bind_vars=bind_vars,
            ),
        )
        return list(cursor)

    def _tasks(self, plant_keys: list[str], run_keys: list[str], tenant_key: str) -> list[dict[str, Any]]:
        """Open tasks on the plants themselves and on the runs they belong to (watering is run-scoped)."""
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                """
            FOR t IN @@tasks
                FILTER t.tenant_key == @tenant_key
                    AND t.status IN @open
                    AND t.suggested != true
                    AND (
                        (t.entity_type == "plant_instance" AND t.entity_key IN @plant_keys)
                        OR (t.entity_type == "planting_run" AND t.entity_key IN @run_keys)
                        OR t.planting_run_key IN @run_keys
                    )
                RETURN {
                    entity_type: t.entity_type,
                    entity_key: t.entity_key,
                    run_key: t.planting_run_key,
                    name: t.name,
                    category: t.category,
                    due: t.due_date
                }
            """,
                bind_vars={
                    "@tasks": col.TASKS,
                    "tenant_key": tenant_key,
                    "open": list(_OPEN_TASK_STATUSES),
                    "plant_keys": plant_keys,
                    "run_keys": run_keys,
                },
            ),
        )
        return list(cursor)

    def _care(
        self, location_key: str, plant_keys: list[str], tenant_key: str, now: datetime
    ) -> dict[tuple[str | None, str], datetime]:
        """The newest watering / feeding per plant; the key ``None`` holds the bed-wide events (no plants named)."""
        since: datetime = now - timedelta(days=CARE_LOOKBACK_DAYS)
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                """
            FOR e IN @@events
                FILTER e.tenant_key == @tenant_key AND e.location_key == @location_key
                    AND e.voided_at == null
                    AND e.superseded_by_key == null
                    AND e.category IN @categories
                    AND DATE_TIMESTAMP(e.performed_at) >= DATE_TIMESTAMP(@since)
                LET targets = LENGTH(e.plant_keys) == 0 ? [null] : e.plant_keys
                FOR plant IN targets
                    FILTER plant == null OR plant IN @plant_keys
                    COLLECT who = plant, category = e.category AGGREGATE last = MAX(e.performed_at)
                    RETURN {plant: who, category, last}
            """,
                bind_vars={
                    "@events": col.CARE_EVENTS,
                    "tenant_key": tenant_key,
                    "location_key": location_key,
                    "categories": [WATERING_CATEGORY, FEEDING_CATEGORY],
                    "since": since.isoformat(),
                    "plant_keys": plant_keys,
                },
            ),
        )
        found: dict[tuple[str | None, str], datetime] = {}
        for row in cursor:
            moment = _datetime(row["last"])
            if moment is not None:
                found[(row["plant"], row["category"])] = moment
        return found

    def _findings(self, plant_keys: list[str], tenant_key: str, now: datetime) -> dict[str, tuple[int, str | None]]:
        """Open findings per plant: how many detections still stand, and the label of the newest."""
        since: datetime = now - timedelta(days=FINDING_OPEN_DAYS)
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                """
            FOR d IN @@detections
                FILTER d.tenant_key == @tenant_key AND d.plant_instance_key IN @plant_keys
                    AND DATE_TIMESTAMP(d.created_at) >= DATE_TIMESTAMP(@since)
                LET standing = (
                    FOR f IN (d.findings || [])
                        FILTER f.category IN @categories
                        FILTER LENGTH(
                            FOR fb IN (d.feedback || [])
                                FILTER fb.finding_label == f.label AND fb.confirmed == false
                                RETURN 1
                        ) == 0
                        RETURN f
                )
                FILTER LENGTH(standing) > 0
                SORT DATE_TIMESTAMP(d.created_at) DESC
                RETURN {
                    plant: d.plant_instance_key,
                    label: standing[0].common_name || standing[0].label
                }
            """,
                bind_vars={
                    "@detections": col.PEST_DETECTIONS,
                    "tenant_key": tenant_key,
                    "plant_keys": plant_keys,
                    "since": since.isoformat(),
                    "categories": list(_ACTIONABLE_FINDING_CATEGORIES),
                },
            ),
        )
        found: dict[str, tuple[int, str | None]] = {}
        for row in cursor:  # newest first: the first label seen per plant is the newest finding's
            count, label = found.get(row["plant"], (0, None))
            found[row["plant"]] = (count + 1, label or row["label"])
        return found

    def _harvests(self, plant_keys: list[str], tenant_key: str) -> dict[str, tuple[int, float | None]]:
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                """
            FOR b IN @@batches
                FILTER b.tenant_key == @tenant_key AND b.plant_key IN @plant_keys
                COLLECT plant = b.plant_key AGGREGATE
                    standing = SUM(b.harvest_type IN @standing ? 1 : 0),
                    total = SUM(b.wet_weight_g),
                    weighed = SUM(b.wet_weight_g != null ? 1 : 0)
                RETURN {plant, standing, total: weighed > 0 ? total : null}
            """,
                bind_vars={
                    "@batches": col.HARVEST_BATCHES,
                    "tenant_key": tenant_key,
                    "plant_keys": plant_keys,
                    "standing": list(_STANDING_HARVEST_TYPES),
                },
            ),
        )
        return {row["plant"]: (int(row["standing"] or 0), row["total"]) for row in cursor}

    # ── Assembly ──────────────────────────────────────────────────────

    @staticmethod
    def _source(
        row: dict[str, Any],
        tasks: list[dict[str, Any]],
        care: dict[tuple[str | None, str], datetime],
        findings: dict[str, tuple[int, str | None]],
        harvests: dict[str, tuple[int, float | None]],
    ) -> PlantStateSource:
        plant_key = row["plant_key"]
        run_key = row["run_key"]
        # A task scoped to another plant of the run (it carries the run key too) is that plant's, not this one's.
        mine = [
            task
            for task in tasks
            if (task["entity_type"] == "plant_instance" and task["entity_key"] == plant_key)
            or (
                run_key is not None
                and task["entity_type"] != "plant_instance"
                and (task["run_key"] == run_key or task["entity_key"] == run_key)
            )
        ]
        open_tasks = tuple(OpenTask(str(task["category"] or ""), _due_day(task["due"])) for task in mine)
        dated = sorted(
            (task for task in mine if _due_day(task["due"]) is not None),
            key=lambda task: (_due_day(task["due"]) or date.max, str(task["name"] or "")),
        )
        first = dated[0] if dated else (mine[0] if mine else None)
        next_task = (
            None
            if first is None
            else NextTask(str(first["name"] or ""), str(first["category"] or ""), _due_day(first["due"]))
        )

        finding_count, finding_label = findings.get(plant_key, (0, None))
        batches, harvested = harvests.get(plant_key, (0, None))
        phase_started = _date(row["phase_started_at"])
        return PlantStateSource(
            plant_key=plant_key,
            instance_id=row["instance_id"],
            species_key=row["species_key"],
            planted_on=_date(row["planted_on"]) or date.min,
            slot_key=row["slot_key"],
            slot_id=row["slot_id"],
            cultivar_key=row["cultivar_key"],
            species_name=row["species_name"],
            scientific_name=row["scientific_name"],
            cultivar_name=row["cultivar_name"],
            phase_key=row["phase_key"],
            phase_name=row["phase_name"],
            phase_started_on=phase_started,
            phase_typical_days=row["phase_typical_days"],
            phase_allows_harvest=bool(row["phase_allows_harvest"]),
            phase_is_terminal=bool(row["phase_is_terminal"]),
            open_tasks=open_tasks,
            next_task=next_task,
            last_watering_at=_latest(care, plant_key, WATERING_CATEGORY),
            last_feeding_at=_latest(care, plant_key, FEEDING_CATEGORY),
            open_finding_count=finding_count,
            finding_label=finding_label,
            harvest_batch_count=batches,
            harvested_total_g=harvested,
            cover_photo_ref=row["cover_photo_ref"],
        )
