"""v0040 — bring stored phase bindings and plant placements back in line (#1146, #1150).

Two defects with one repair, because they end in the same place: a plant sitting
in a phase its species cannot reach.

**#1146 — the binding drifted.** Both binding paths are skip-if-bound, and
idempotency is right for both, so every resolver improvement reaches newly bound
species and leaves existing ones where they were. ``Yucca gigantea`` sat on the
126-day annual ``indoor_default`` cycle while the resolver had answered
``evergreen_foliage_perennial`` for it since #949 — fixed in the classifier, never
in the data.

**#1150 — the sequence was deleted underneath the plant.** ``indoor_default`` was
deleted and recreated during the fine-typing work (#616 / v0027); the old entry
documents survived and the plants pointing at them were never re-pointed. A
sunflower and a *Monstera deliciosa* share one entry key, and the Monstera reports
``flowering`` one month after planting through the sunflower's phase. ``v0021``
does not catch it: those keys *resolve*, so they are orphaned rather than
dangling.

**One placement rule**, from :mod:`app.domain.engines.phase_placement`: name
anchor first, then elapsed days, with a **backdated** ``entered_at``. #1150 asks
for exactly that — two repairs inventing their own placement is how they end up
disagreeing about where the same plant belongs.

**The target is re-derived from the resolver**, not copied into a frozen map the
way v0024/v0027/v0029 did. Those are one-off cohorts; this migration exists
because one-off cohorts do not scale, and a hand-listed target here would be the
same mistake one version later. It agrees with
``seed_data.report_binding_divergence`` because both call
``resolve_phase_sequence_name`` — not because they share a wrapper.

**What it will not touch:**

* a binding whose edge says ``bound_by: manual`` — an override, not drift (#1146
  decision 3). No such edge can exist yet (#1099), which is precisely why the
  exclusion is written before it can be exercised;
* a plant the placement rule declines to place. Nothing is guessed; it is reported
  and left, exactly as v0021 refuses to guess a dangling key;
* the pre-sequence ``GrowthPhase`` key space. ``phase_reachability`` reports it
  under its own kind, and migrating it is a separate decision about a different
  model.

Idempotent (M-3): a second run finds the bindings already correct and every plant
already placed by name in its own sequence, so it reports ``changed == 0``.
``today`` is taken once at the start and threaded through, so a re-run places a
plant where the first run placed it.

Irreversible (M-6): the prior binding and the prior ``entered_at`` are not
retained per row, and re-deriving them would mean re-running the rule that was
wrong.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.domain.engines.cycle_resolver import resolve_effective_cycle
from app.domain.engines.phase_placement import PlacementCandidate, place_plant_in_sequence
from app.domain.engines.phase_sequence_resolver import (
    INDOOR_DEFAULT_SEQUENCE,
    resolve_phase_sequence_name,
)
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger(__name__)

#: Provenance stamped on every edge this migration re-points (#1146 decision 3).
BOUND_BY = "migration:v0040"

#: An edge carrying this was set by a human and is never corrected.
_BOUND_BY_MANUAL = "manual"


def _enum_value(value: object) -> str | None:
    if value is None:
        return None
    return value.value if hasattr(value, "value") else str(value)


class RepairPhaseBindingsAndPlacementsMigration(Migration):
    version = "0040"
    name = "repair_phase_bindings_and_placements"
    description = "Re-point diverged species bindings and place plants left in unreachable phases (#1146, #1150)."
    reversible = False

    # ── reads ────────────────────────────────────────────────────────────────

    def _scan(self, db: StandardDatabase, collection: str) -> list[dict[str, Any]]:
        if not db.has_collection(collection):
            return []
        return list(db.aql.execute(f"FOR d IN {collection} RETURN d"))

    # ── planning (pure, dry-run-safe) ────────────────────────────────────────

    def _plan(self, db: StandardDatabase, today: date) -> tuple[list[dict[str, str]], list[dict[str, Any]], list[str]]:
        """Return ``(rebinds, placements, unplaceable)``.

        Computed in one pass and in this order because the second half depends on
        the first: a plant is placed into the sequence its species will be bound
        to *after* the rebind, not the one it is bound to now. Planning them
        separately would place half the plants into a sequence this same migration
        is about to move them off.
        """
        species = self._scan(db, col.SPECIES)
        sequences = self._scan(db, col.PHASE_SEQUENCES)
        entries = self._scan(db, col.PHASE_SEQUENCE_ENTRIES)
        definitions = self._scan(db, col.PHASE_DEFINITIONS)
        edges = self._scan(db, col.HAS_PHASE_SEQUENCE)
        plants = self._scan(db, col.PLANT_INSTANCES)
        histories = self._scan(db, col.PHASE_HISTORIES)
        lifecycles = self._scan(db, col.LIFECYCLE_CONFIGS)

        seq_key_by_name = {s.get("name"): s["_key"] for s in sequences}
        live_sequence_keys = set(seq_key_by_name.values())
        def_name_by_key = {d["_key"]: d.get("name", "") for d in definitions}
        def_days_by_key = {d["_key"]: int(d.get("typical_duration_days") or 1) for d in definitions}
        lifecycle_by_species = {lc.get("species_key"): lc for lc in lifecycles}

        entries_by_sequence: dict[str, list[dict[str, Any]]] = {}
        for entry in entries:
            entries_by_sequence.setdefault(entry.get("phase_sequence_key", ""), []).append(entry)

        edge_by_species: dict[str, dict[str, Any]] = {}
        for edge in edges:
            key = str(edge.get("_from", "")).removeprefix(f"{col.SPECIES}/")
            edge_by_species[key] = edge

        histories_by_plant: dict[str, list[dict[str, Any]]] = {}
        for history in histories:
            histories_by_plant.setdefault(history.get("plant_instance_key", ""), []).append(history)

        # ── half 1: bindings that disagree with the resolver ──
        rebinds: list[dict[str, str]] = []
        target_sequence_by_species: dict[str, str] = {}
        for record in species:
            species_key = record["_key"]
            edge = edge_by_species.get(species_key)
            if edge is None or edge.get("bound_by") == _BOUND_BY_MANUAL:
                continue

            target_name = self._resolve_target(record, lifecycle_by_species.get(species_key))
            target_key = seq_key_by_name.get(target_name)
            if not target_key:
                continue

            target_sequence_by_species[species_key] = target_key
            current_to = str(edge.get("_to", "")).removeprefix(f"{col.PHASE_SEQUENCES}/")
            if current_to != target_key:
                rebinds.append({"edge_key": edge["_key"], "to_key": target_key, "species_key": species_key})

        # ── half 2: plants whose phase is unreachable from the target ──
        placements: list[dict[str, Any]] = []
        unplaceable: list[str] = []
        entry_by_key = {e["_key"]: e for e in entries}

        for plant in plants:
            current = plant.get("current_phase_key")
            if not current:
                continue
            species_key = plant.get("species_key") or ""
            target_key = target_sequence_by_species.get(species_key)
            if not target_key:
                continue

            entry = entry_by_key.get(current)
            reachable = (
                entry is not None and entry.get("phase_sequence_key") == target_key and target_key in live_sequence_keys
            )
            if reachable:
                continue

            candidates = [
                PlacementCandidate(
                    entry_key=e["_key"],
                    phase_name=def_name_by_key.get(e.get("phase_definition_key", ""), ""),
                    duration_days=int(
                        e.get("override_duration_days") or def_days_by_key.get(e.get("phase_definition_key", ""), 1)
                    ),
                    sequence_order=int(e.get("sequence_order") or 0),
                )
                for e in entries_by_sequence.get(target_key, [])
            ]
            open_history = self._open_history(histories_by_plant.get(plant["_key"], []))
            placement = place_plant_in_sequence(
                current_phase_name=(open_history or {}).get("phase_name"),
                planted_on=self._as_date(plant.get("planted_on")),
                today=today,
                candidates=candidates,
            )
            if placement is None:
                unplaceable.append(plant["_key"])
                continue

            placements.append(
                {
                    "plant_key": plant["_key"],
                    "entry_key": placement.entry_key,
                    "phase_name": placement.phase_name,
                    "entered_at": placement.entered_at,
                    "history_key": (open_history or {}).get("_key"),
                    "anchored_by": placement.anchored_by,
                }
            )

        return rebinds, placements, unplaceable

    def _resolve_target(self, species: dict[str, Any], lifecycle: dict[str, Any] | None) -> str:
        """The resolver's verdict, translated the way both binding paths translate it.

        ``None`` from the resolver means "the blanket is correct for this known
        determinate cycle" — comparing the raw ``None`` against a stored name would
        make every annual in the catalogue look diverged.
        """
        effective_cycle = resolve_effective_cycle(None, _AsObject(lifecycle)) if lifecycle else None
        target = resolve_phase_sequence_name(
            species.get("scientific_name") or "",
            cycle_type=_enum_value(effective_cycle),
            flowering_strategy=(lifecycle or {}).get("flowering_strategy"),
            photosynthesis_type=species.get("photosynthesis_type"),
            photoperiod_type=(lifecycle or {}).get("photoperiod_type"),
            growth_habit=species.get("growth_habit"),
        )
        return target or INDOOR_DEFAULT_SEQUENCE

    @staticmethod
    def _open_history(histories: list[dict[str, Any]]) -> dict[str, Any] | None:
        for history in histories:
            if history.get("exited_at") is None:
                return history
        return None

    @staticmethod
    def _as_date(value: Any) -> date | None:
        if not value:
            return None
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, datetime):
            return value.date()
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
        except ValueError:
            return None

    # ── entry point ──────────────────────────────────────────────────────────

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        today = datetime.now(UTC).date()
        rebinds, placements, unplaceable = self._plan(db, today)
        changed = len(rebinds) + len(placements)

        if not dry_run:
            for item in rebinds:
                db.aql.execute(
                    f"UPDATE {{_key: @key, _to: @to_id, bound_by: @bound_by, bound_at: @at}} "
                    f"IN {col.HAS_PHASE_SEQUENCE}",
                    bind_vars={
                        "key": item["edge_key"],
                        "to_id": f"{col.PHASE_SEQUENCES}/{item['to_key']}",
                        "bound_by": BOUND_BY,
                        "at": datetime.now(UTC).isoformat(),
                    },
                )
            for item in placements:
                db.aql.execute(
                    f"UPDATE {{_key: @key, current_phase_key: @entry}} IN {col.PLANT_INSTANCES}",
                    bind_vars={"key": item["plant_key"], "entry": item["entry_key"]},
                )
                if item["history_key"]:
                    db.aql.execute(
                        f"UPDATE {{_key: @key, phase_key: @entry, phase_name: @name, entered_at: @entered}} "
                        f"IN {col.PHASE_HISTORIES}",
                        bind_vars={
                            "key": item["history_key"],
                            "entry": item["entry_key"],
                            "name": item["phase_name"],
                            # Backdated, not "now" — see the module docstring. This is
                            # what makes the corrected plant self-correcting instead of
                            # restarting a phase it is most of the way through.
                            "entered": datetime.combine(item["entered_at"], datetime.min.time(), UTC).isoformat(),
                        },
                    )

        logger.info(
            "repair_phase_bindings_and_placements",
            rebound=len(rebinds),
            placed=len(placements),
            unplaceable=len(unplaceable),
            dry_run=dry_run,
        )
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=changed + len(unplaceable),
            changed=0 if dry_run else changed,
            dry_run=dry_run,
            details={
                "rebound": len(rebinds),
                "placed": len(placements),
                # Named, not just counted: a plant this migration declined to place
                # is the one an operator has to look at by hand.
                "unplaceable": unplaceable[:25],
                "by_name_anchor": sum(1 for p in placements if p["anchored_by"] == "name"),
                "by_elapsed_days": sum(1 for p in placements if p["anchored_by"] == "elapsed_days"),
            },
        )


class _AsObject:
    """Attribute view over a lifecycle dict, for ``resolve_effective_cycle``.

    That resolver takes models, and a migration reads raw documents. Wrapping is
    cheaper than a second cycle-resolution rule — and a second one is exactly what
    ADR-006 E1 exists to prevent.
    """

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    def __getattr__(self, item: str) -> Any:
        return self._data.get(item)


#: Module-level instance the discovery loader binds (framework contract).
migration = RepairPhaseBindingsAndPlacementsMigration()
