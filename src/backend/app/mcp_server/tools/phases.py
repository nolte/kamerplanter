"""REQ-033 growth-phase and lifecycle tools (§2.1 read, §2.2 write, REQ-003).

The lifecycle engine drives task scheduling, feeding windows, harvest readiness
and overwintering — and until issue #949 exactly one tool in the palette touched
it: ``list_phase_definitions``, which returns the catalogue of *building blocks*.
Not the sequences those blocks are assembled into, not which sequence a species
resolves to, and not the phase state of an actual plant. A question as ordinary
as *"is this plant on the botanically correct phase sequence?"* had no MCP answer;
the entire diagnosis in #949 had to be produced against the REST API.

What the module adds, and why each piece is load-bearing rather than convenient:

* :class:`GetSpeciesPhaseSequence` — the resolved sequence plus ``cycle_type`` and
  ``is_repeating``, which are what separate a perennial houseplant from a 126-day
  vegetable. Without it the central question is unanswerable.
* :class:`ListPhaseSequences` — diagnosing a wrong assignment is half the job;
  *naming the right one* needs the catalogue.
* :class:`ListSpeciesByPhaseSequence` — the reverse lookup, and the strongest
  verification lever in the investigation: seeing *Yucca gigantea* bucketed with
  Rosenkohl and Porree converts "this looks off" into "this is a template
  collision affecting a class of species".
* :class:`GetPlantPhaseStatus` — and specifically its ``phase_state``, because
  ``get_plant``'s bare ``current_phase_key: null`` cannot tell "never
  initialised" from "sitting in an empty phase for 50 days", which is what the
  investigated instance was actually doing.
* :class:`GetPlantPhaseHistory`, :class:`GetSpeciesLifecycle` — the transition
  record and the layer where "perennial and polycarpic" is actually stated.
* :class:`TransitionPlantPhase`, :class:`AssignSpeciesPhaseSequence` — the two
  writes. An agent that has correctly diagnosed a wrong sequence, named the right
  one and verified it against external sources previously had to hand the fix
  back to a human as prose, and could never confirm its own recommendation landed.

**Authoring stays out**, deliberately, on the line #931 drew for nutrient plans:
defining sequences — ordering entries, setting durations, marking terminal and
harvest-allowing steps — is editing work with a UI built for it. These tools
*read* the topology, *bind* an existing sequence and *set* an instance's phase.

Each write tool is paired with the read tool that resolves its references and the
one that surfaces its result again (§4.1 addressability):

* ``transition_plant_phase`` — resolved by ``get_species_phase_sequence`` (which
  produces the legal ``target_phase_key`` values), surfaced by
  ``get_plant_phase_status``.
* ``assign_species_phase_sequence`` — resolved by ``list_phase_sequences``,
  surfaced by ``get_species_phase_sequence``.

Tenant binding is **derived** from each ``Input`` model
(``ToolBase.__init_subclass__``) and never set by hand. Species, sequences and
lifecycles are global catalogue data and carry no tenant; plant instances do.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from app.common.enums import McpPermission
from app.common.exceptions import NotFoundError
from app.domain.models.mcp import McpToolResponse
from app.mcp_server.base import (
    GlobalWriteToolInput,
    McpToolError,
    TenantToolInput,
    ToolBase,
    ToolInput,
    WriteToolBase,
    WriteToolInput,
    mcp_tool,
)
from app.mcp_server.context import ToolContext

#: Upper bound on one page, matching the rest of the palette: a compact answer an
#: LLM can actually read beats a complete one it truncates.
_MAX_LIMIT = 100

#: The catalogue holds ~22 sequences, so a single scan covers it with headroom.
#: Filtering inside one page would report "no match" for a sequence further down —
#: a wrong answer rather than a short one (see nutrition._SCAN_LIMIT).
_SCAN_LIMIT = 500

#: Cap on returned phase-history records. History is append-only and a perennial on
#: a repeating cycle accumulates one row per phase per season indefinitely.
_HISTORY_LIMIT = 200


def _cycle_value(value: Any) -> str | None:
    """Enum → its wire value; passthrough for a plain string; ``None`` stays ``None``."""

    if value is None:
        return None
    return value.value if hasattr(value, "value") else str(value)


def _entry_view(entry: dict[str, Any]) -> dict[str, Any]:
    """One ordered step of a sequence, trimmed to what a phase judgement needs.

    ``effective_duration_days`` is the entry's own override where set, else the
    phase definition's default — already resolved by ``get_full_sequence``, so no
    caller has to re-derive the cascade and reach a second opinion.
    """

    definition = entry.get("phase_definition") or {}
    return {
        "entry_key": entry.get("key"),
        "sequence_order": entry.get("sequence_order"),
        "phase_definition_key": entry.get("phase_definition_key"),
        "name": definition.get("name", ""),
        "display_name": definition.get("display_name") or definition.get("display_name_de") or "",
        "effective_duration_days": entry.get("effective_duration_days"),
        "override_duration_days": entry.get("override_duration_days"),
        # The three flags the issue names explicitly: they are what decides whether
        # a plant is scheduled to be harvested and to end its life.
        "is_terminal": entry.get("is_terminal", False),
        "allows_harvest": entry.get("allows_harvest", False),
        "is_recurring": entry.get("is_recurring", False),
        "stress_tolerance": definition.get("stress_tolerance"),
        "watering_interval_days": definition.get("watering_interval_days"),
    }


def _sequence_shape(sequence: Any, entries: list[dict[str, Any]]) -> dict[str, Any]:
    """The topology facts a caller judges a sequence by, derived once here.

    ``terminates_in_harvest`` is the composite that made the #949 diagnosis
    legible: a non-repeating cycle whose terminal step allows a harvest is a
    scheduled end-of-life, which is correct for a lettuce and wrong for a tree.
    Deriving it in the tool keeps every consumer from rebuilding the same
    three-field conjunction and getting it subtly different.
    """

    total_days = sum(e.get("effective_duration_days") or 0 for e in entries)
    terminal = [e for e in entries if e.get("is_terminal")]
    return {
        "cycle_type": _cycle_value(getattr(sequence, "cycle_type", None)),
        "is_repeating": getattr(sequence, "is_repeating", False),
        "dormancy_required": getattr(sequence, "dormancy_required", False),
        "vernalization_required": getattr(sequence, "vernalization_required", False),
        "cycle_restart_entry_order": getattr(sequence, "cycle_restart_entry_order", None),
        "typical_lifespan_years": getattr(sequence, "typical_lifespan_years", None),
        "photoperiod_type": _cycle_value(getattr(sequence, "photoperiod_type", None)),
        "entry_count": len(entries),
        "total_duration_days": total_days,
        "has_harvest_phase": any(e.get("allows_harvest") for e in entries),
        "terminates_in_harvest": (
            not getattr(sequence, "is_repeating", False) and any(e.get("allows_harvest") for e in terminal)
        ),
    }


@mcp_tool(name="get_species_phase_sequence", permission=McpPermission.READ)
class GetSpeciesPhaseSequence(ToolBase):
    """Return the phase sequence a species resolves to, with its ordered phases."""

    class Input(ToolInput):
        species_key: str = Field(description="Key of the species. Resolve it with list_species or get_plant.")

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        sequence = ctx.phase_sequence_service.get_sequence_by_species(args.species_key)
        if sequence is None:
            # A distinct, explicit answer: the species resolves to nothing at all,
            # which is not the same as resolving to an empty sequence. An agent must
            # be able to tell "unbound" from "bound to something with no phases".
            return self._response(
                summary=f"Species '{args.species_key}' is not bound to any phase sequence.",
                data={"species_key": args.species_key, "sequence": None},
                links=[ctx.global_link(f"/species/{args.species_key}/phase-sequence")],
            )

        full = ctx.phase_sequence_service.get_full_sequence(sequence.key or "")
        entries = sorted(full.get("entries", []), key=lambda e: e.get("sequence_order") or 0)
        views = [_entry_view(e) for e in entries]
        shape = _sequence_shape(sequence, views)

        data = {
            "species_key": args.species_key,
            "sequence": {
                "sequence_key": sequence.key,
                "name": sequence.name,
                "display_name": sequence.display_name or sequence.display_name_de or "",
                "is_system": sequence.is_system,
                "tags": list(sequence.tags or []),
                **shape,
                "entries": views,
            },
        }
        cycle = shape["cycle_type"] or "unknown"
        repeats = "repeating" if shape["is_repeating"] else "non-repeating"
        summary = (
            f"Species '{args.species_key}' follows '{sequence.name}' — {cycle}, {repeats}, "
            f"{shape['entry_count']} phases over {shape['total_duration_days']} days."
        )
        if shape["terminates_in_harvest"]:
            summary += " The cycle ends in a terminal harvest phase and does not restart."
        return self._response(
            summary=summary,
            data=data,
            links=[ctx.global_link(f"/species/{args.species_key}/phase-sequence")],
        )


@mcp_tool(name="list_phase_sequences", permission=McpPermission.READ)
class ListPhaseSequences(ToolBase):
    """List the phase-sequence catalogue, so a correct alternative can be named."""

    class Input(ToolInput):
        query: str | None = Field(
            default=None,
            description="Case-insensitive substring filter over name, display name and tags.",
        )
        include_entries: bool = Field(
            default=False,
            description="Include each sequence's ordered phases. Off by default — the shape "
            "fields alone are usually enough to pick a candidate.",
        )
        offset: int = Field(default=0, ge=0)
        limit: int = Field(default=25, ge=1, le=_MAX_LIMIT)

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        # Scan then filter, never filter within a page — see _SCAN_LIMIT.
        sequences, total = ctx.phase_sequence_service.list_sequences(offset=0, limit=_SCAN_LIMIT)
        selected = list(sequences)
        if args.query:
            needle = args.query.strip().lower()
            selected = [
                s
                for s in selected
                if needle in f"{s.name} {s.display_name} {s.display_name_de} {' '.join(s.tags or [])}".lower()
            ]

        page = selected[args.offset : args.offset + args.limit]
        items = []
        for sequence in page:
            entries = sorted(
                ctx.phase_sequence_service.get_full_sequence(sequence.key or "").get("entries", []),
                key=lambda e: e.get("sequence_order") or 0,
            )
            views = [_entry_view(e) for e in entries]
            item = {
                "sequence_key": sequence.key,
                "name": sequence.name,
                "display_name": sequence.display_name or sequence.display_name_de or "",
                "is_system": sequence.is_system,
                "tags": list(sequence.tags or []),
                **_sequence_shape(sequence, views),
            }
            if args.include_entries:
                item["entries"] = views
            items.append(item)

        truncated = total > _SCAN_LIMIT
        summary = f"{len(selected)} phase sequences match (of {total}); {len(items)} returned."
        if truncated:
            summary += f" Only the first {_SCAN_LIMIT} were searched."
        return self._response(
            summary=summary,
            data={
                "count": len(items),
                "matched": len(selected),
                "total": total,
                "truncated": truncated,
                "items": items,
            },
            links=[ctx.global_link("/phase-sequences")],
        )


@mcp_tool(name="list_species_by_phase_sequence", permission=McpPermission.READ)
class ListSpeciesByPhaseSequence(ToolBase):
    """List every species bound to one phase sequence — the reverse lookup."""

    class Input(ToolInput):
        sequence_key: str = Field(
            description="Key of the phase sequence. Resolve it with list_phase_sequences "
            "or get_species_phase_sequence.",
        )
        offset: int = Field(default=0, ge=0)
        limit: int = Field(default=_MAX_LIMIT, ge=1, le=_MAX_LIMIT)

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        sequence = ctx.phase_sequence_service.get_sequence(args.sequence_key)
        species = ctx.phase_sequence_service.get_species_for_sequence(args.sequence_key)
        page = species[args.offset : args.offset + args.limit]
        return self._response(
            # The count is the finding: a sequence carrying a mixed cohort is how a
            # template collision announces itself.
            summary=f"{len(species)} species are bound to '{sequence.name}' ({len(page)} returned).",
            data={
                "sequence_key": sequence.key,
                "sequence_name": sequence.name,
                "cycle_type": _cycle_value(sequence.cycle_type),
                "is_repeating": sequence.is_repeating,
                "count": len(page),
                "total": len(species),
                "items": [
                    {
                        "species_key": row.get("key"),
                        "scientific_name": row.get("scientific_name") or "",
                        "common_names": list(row.get("common_names") or []),
                    }
                    for row in page
                ],
            },
            links=[ctx.global_link(f"/phase-sequences/{sequence.key}/species")],
        )


@mcp_tool(name="get_species_lifecycle", permission=McpPermission.READ)
class GetSpeciesLifecycle(ToolBase):
    """Return a species' lifecycle: cycle type, flowering strategy, lifespan, dormancy."""

    class Input(ToolInput):
        species_key: str = Field(description="Key of the species. Resolve it with list_species or get_plant.")

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        try:
            lifecycle = ctx.phase_service.get_lifecycle_by_species(args.species_key)
        except NotFoundError:
            # Not an error worth failing on: "this species has no lifecycle record"
            # is itself the finding, and it is exactly what routes the species into
            # the resolver's fallback (issue #949). Saying so beats a bare 404.
            return self._response(
                summary=(
                    f"Species '{args.species_key}' has no lifecycle configuration. Its phase "
                    f"sequence therefore resolves from the species classification alone."
                ),
                data={"species_key": args.species_key, "lifecycle": None},
                links=[ctx.global_link(f"/species/{args.species_key}/lifecycle")],
            )

        cycle = _cycle_value(lifecycle.cycle_type)
        cultivation = _cycle_value(lifecycle.cultivation_cycle_type)
        data = {
            "species_key": args.species_key,
            "lifecycle": {
                "lifecycle_key": lifecycle.key,
                "cycle_type": cycle,
                "cultivation_cycle_type": cultivation,
                # Derived exactly as LifecycleResponse derives it, so REST and MCP
                # cannot disagree about whether a species is grown as an annual.
                "grown_as_annual": cultivation == "annual" and cycle != "annual",
                "flowering_strategy": _cycle_value(lifecycle.flowering_strategy),
                "growth_determinacy": _cycle_value(lifecycle.growth_determinacy),
                "typical_lifespan_years": lifecycle.typical_lifespan_years,
                "dormancy_required": lifecycle.dormancy_required,
                "vernalization_required": lifecycle.vernalization_required,
                "photoperiod_type": _cycle_value(lifecycle.photoperiod_type),
                "critical_day_length_hours": lifecycle.critical_day_length_hours,
                "max_seasons": lifecycle.max_seasons,
                "first_bearing_year": lifecycle.first_bearing_year,
                "expected_productive_years": lifecycle.expected_productive_years,
                "phase_sequence_key": lifecycle.phase_sequence_key,
            },
        }
        strategy = _cycle_value(lifecycle.flowering_strategy) or "unrecorded flowering strategy"
        return self._response(
            summary=f"Species '{args.species_key}': {cycle}, {strategy}.",
            data=data,
            links=[ctx.global_link(f"/species/{args.species_key}/lifecycle")],
        )


#: ``phase_state`` values of :class:`GetPlantPhaseStatus`. The whole point of the
#: field is that ``current_phase_key: null`` conflates three different situations
#: and an agent needs to act differently in each.
PHASE_STATE_NEVER_INITIALISED = "never_initialised"
PHASE_STATE_UNRESOLVED = "unresolved"
PHASE_STATE_IN_PHASE = "in_phase"
PHASE_STATE_BETWEEN_CYCLES = "between_cycles"


@mcp_tool(name="get_plant_phase_status", permission=McpPermission.READ)
class GetPlantPhaseStatus(ToolBase):
    """Return a plant's phase state: days in phase, next phase, cycle number, harvest."""

    class Input(TenantToolInput):
        plant_key: str = Field(description="Key of the plant. Resolve it with list_plants.")

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        # Tenant-scoped read first: a foreign key raises not_found before any phase
        # data is touched (SEC-001, the fetch-then-use guard).
        plant = ctx.plant_service.get_plant(args.plant_key, tenant_key=ctx.tenant_key)
        current = ctx.phase_service.get_current_phase(plant.key)
        history = ctx.phase_service.get_phase_history(plant.key)

        phase_key = current.get("phase_key") or ""
        phase_name = current.get("phase") or ""
        state = _classify_phase_state(phase_key, phase_name, history)

        data = {
            "plant_key": plant.key,
            "instance_id": plant.instance_id,
            "species_key": plant.species_key,
            "planted_on": plant.planted_on,
            # ── The discriminator the issue asked for ──
            "phase_state": state,
            "phase": phase_name,
            "phase_key": phase_key or None,
            "days_in_phase": current.get("days_in_phase", 0),
            "next_phase": current.get("next_phase"),
            "cycle_type": current.get("cycle_type"),
            "cycle_number": current.get("cycle_number", 1),
            "has_harvest_phase": current.get("has_harvest_phase", False),
            "is_terminal": current.get("is_terminal", False),
            "source": current.get("source"),
            "transition_count": len(history),
        }
        return self._response(
            summary=_phase_state_summary(plant, data),
            data=data,
            links=[
                ctx.api_link(f"/plant-instances/{plant.key}/phases/current"),
                ctx.ui_link(f"/plants/{plant.key}"),
            ],
        )


def _classify_phase_state(phase_key: str, phase_name: str, history: list[Any]) -> str:
    """Tell the three situations ``current_phase_key: null`` collapses into apart.

    The investigated instance in #949 had been sitting in an **empty** phase for 50
    days — a history row whose ``phase_key`` resolves to no phase at all. That is a
    different problem from a plant whose lifecycle was never started, and a
    different one again from a perennial resting between cycles; each calls for a
    different action, and none of them is distinguishable from ``null``.
    """

    if phase_key and phase_name:
        return PHASE_STATE_IN_PHASE
    if phase_key or any(h.exited_at is None for h in history):
        # There *is* an open phase record, but it points at nothing resolvable —
        # a dangling key or an entry whose definition disappeared.
        return PHASE_STATE_UNRESOLVED
    if history:
        # Every recorded phase has been exited: the plant completed a cycle and is
        # waiting for the next one, which is a normal perennial state.
        return PHASE_STATE_BETWEEN_CYCLES
    return PHASE_STATE_NEVER_INITIALISED


def _phase_state_summary(plant: Any, data: dict[str, Any]) -> str:
    """A one-line answer that never silently reads as "fine" when it is not."""

    name = plant.plant_name or plant.instance_id
    state = data["phase_state"]
    if state == PHASE_STATE_IN_PHASE:
        line = (
            f"'{name}' is in phase '{data['phase']}' for {data['days_in_phase']} days (cycle {data['cycle_number']})."
        )
        if data["next_phase"]:
            line += f" Next: '{data['next_phase']}'."
        return line
    if state == PHASE_STATE_UNRESOLVED:
        return (
            f"'{name}' has an open phase record that resolves to no phase, after "
            f"{data['days_in_phase']} days. Its lifecycle is not advancing."
        )
    if state == PHASE_STATE_BETWEEN_CYCLES:
        return f"'{name}' is between cycles — {data['transition_count']} completed phases, none currently open."
    return f"'{name}' has no phase history at all: its lifecycle was never initialised."


@mcp_tool(name="get_plant_phase_history", permission=McpPermission.READ)
class GetPlantPhaseHistory(ToolBase):
    """Return a plant's phase transitions with their reason, dates and duration."""

    class Input(TenantToolInput):
        plant_key: str = Field(description="Key of the plant. Resolve it with list_plants.")
        limit: int = Field(
            default=50,
            ge=1,
            le=_HISTORY_LIMIT,
            description="Most recent transitions to return.",
        )

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        plant = ctx.plant_service.get_plant(args.plant_key, tenant_key=ctx.tenant_key)
        history = ctx.phase_service.get_phase_history(plant.key)
        ordered = sorted(history, key=lambda h: h.entered_at)
        page = ordered[-args.limit :]

        items = [
            {
                "history_key": h.key,
                "phase_key": h.phase_key,
                # Kept even when empty: an empty name on a populated record is the
                # symptom that started #949, and dropping it would hide it.
                "phase_name": h.phase_name,
                "entered_at": h.entered_at,
                "exited_at": h.exited_at,
                "actual_duration_days": h.actual_duration_days,
                "cycle_number": h.cycle_number,
                "transition_reason": h.transition_reason,
                "is_premature": h.is_premature,
                "performance_score": h.performance_score,
                "is_current": h.exited_at is None,
            }
            for h in page
        ]
        name = plant.plant_name or plant.instance_id
        return self._response(
            summary=f"'{name}' has {len(ordered)} phase transitions ({len(items)} returned).",
            data={
                "plant_key": plant.key,
                "count": len(items),
                "total": len(ordered),
                "items": items,
            },
            links=[ctx.api_link(f"/plant-instances/{plant.key}/phases/history")],
        )


@mcp_tool(name="transition_plant_phase", permission=McpPermission.WRITE)
class TransitionPlantPhase(WriteToolBase):
    """Move a plant into a phase of its resolved sequence, or correct a wrong one."""

    class Input(WriteToolInput):
        plant_key: str = Field(description="Key of the plant. Resolve it with list_plants.")
        target_phase_key: str = Field(
            description="Key of the target phase — an entry_key from get_species_phase_sequence.",
        )
        reason: str = Field(
            default="manual",
            max_length=200,
            description="Why the phase changed; stored on the transition record.",
        )
        force: bool = Field(
            default=False,
            description="Skip the engine's own ordering checks. Use only to repair a wrong phase.",
        )

    async def preview(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        plant, target, current = self._resolve(ctx, args)
        return self._response(
            summary=(
                f"Would move plant '{plant.key}' from '{current.get('phase') or '(none)'}' "
                f"to '{target['name'] or args.target_phase_key}'."
            ),
            data={
                "plant_key": plant.key,
                "from_phase_key": current.get("phase_key") or None,
                "from_phase": current.get("phase") or None,
                "target_phase_key": args.target_phase_key,
                "target_phase": target["name"],
                # A transition into a terminal, harvest-allowing phase ends the
                # lifecycle. Naming that before it happens is the reason a dry run
                # exists for this tool.
                "target_is_terminal": target["is_terminal"],
                "target_allows_harvest": target["allows_harvest"],
                "reason": args.reason,
                "force": args.force,
            },
        )

    async def execute(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        plant, target, _current = self._resolve(ctx, args)
        updated = ctx.phase_service.transition_phase(
            plant.key,
            args.target_phase_key,
            args.reason,
            force=args.force,
        )
        name = plant.plant_name or plant.instance_id
        return self._response(
            summary=f"'{name}' is now in phase '{target['name'] or args.target_phase_key}'.",
            data={
                "plant_key": plant.key,
                "phase_key": updated.current_phase_key,
                "phase": target["name"],
                "target_is_terminal": target["is_terminal"],
                "target_allows_harvest": target["allows_harvest"],
                "reason": args.reason,
            },
            links=[
                # get_plant_phase_status is the read tool that surfaces this write
                # again (§4.1 addressability).
                ctx.api_link(f"/plant-instances/{plant.key}/phases/current"),
                ctx.ui_link(f"/plants/{plant.key}"),
            ],
        )

    @staticmethod
    def _resolve(ctx: ToolContext, args: Input) -> tuple[Any, dict[str, Any], dict[str, Any]]:
        """Ownership-check the plant and validate the target against its own sequence.

        Runs on the dry-run path too, so a preview cannot approve a transition the
        write would refuse.

        The target is validated against the sequence the **plant's species** resolves
        to, not against the global set of phase keys. Without that, a phase key
        belonging to some other species' sequence would be accepted and the plant
        would end up on a phase its own lifecycle can never advance out of — the
        stuck, unresolvable state issue #949 found the reference instance in.
        """

        plant = ctx.plant_service.get_plant(args.plant_key, tenant_key=ctx.tenant_key)
        current = ctx.phase_service.get_current_phase(plant.key)

        sequence = ctx.phase_sequence_service.get_sequence_by_species(plant.species_key)
        if sequence is None:
            raise McpToolError(
                "validation.no_phase_sequence",
                f"Species '{plant.species_key}' is not bound to a phase sequence, so it has no "
                f"valid target phases. Bind one with assign_species_phase_sequence first.",
                details={"plant_key": plant.key, "species_key": plant.species_key},
            )

        full = ctx.phase_sequence_service.get_full_sequence(sequence.key or "")
        entries = sorted(full.get("entries", []), key=lambda e: e.get("sequence_order") or 0)
        match = next((e for e in entries if e.get("key") == args.target_phase_key), None)
        if match is None:
            raise McpToolError(
                "validation.phase_not_in_sequence",
                f"Phase '{args.target_phase_key}' is not part of sequence '{sequence.name}', "
                f"which is what species '{plant.species_key}' resolves to.",
                details={
                    "plant_key": plant.key,
                    "sequence_key": sequence.key,
                    "sequence_name": sequence.name,
                    "valid_phase_keys": [e.get("key") for e in entries],
                },
            )

        view = _entry_view(match)
        return plant, view, current


@mcp_tool(name="assign_species_phase_sequence", permission=McpPermission.SETUP)
class AssignSpeciesPhaseSequence(WriteToolBase):
    """Bind a species to an existing phase sequence — the sequence itself is never edited."""

    class Input(GlobalWriteToolInput):
        species_key: str = Field(description="Key of the species. Resolve it with list_species.")
        sequence_key: str = Field(
            description="Key of an existing phase sequence. Resolve it with list_phase_sequences.",
        )

    async def preview(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        target, current = self._resolve(ctx, args)
        replaces = getattr(current, "name", None) if current is not None else None
        return self._response(
            summary=(
                f"Would bind species '{args.species_key}' to '{target.name}'"
                + (f", replacing '{replaces}'." if replaces else ", which currently has no sequence.")
            ),
            data={
                "species_key": args.species_key,
                "sequence_key": target.key,
                "sequence_name": target.name,
                "cycle_type": _cycle_value(target.cycle_type),
                "is_repeating": target.is_repeating,
                # Re-binding replaces the existing edge. Naming what is lost is the
                # point of the dry run — a species' whole schedule changes with it.
                "replaces_sequence_key": getattr(current, "key", None) if current is not None else None,
                "replaces_sequence_name": replaces,
            },
        )

    async def execute(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        target, _current = self._resolve(ctx, args)
        result = ctx.phase_service.assign_phase_sequence(args.species_key, args.sequence_key)
        replaced = result.get("previous_sequence_key")
        return self._response(
            summary=f"Species '{args.species_key}' now follows phase sequence '{target.name}'."
            + (" The previous binding was replaced." if replaced else ""),
            data={
                "species_key": args.species_key,
                "sequence_key": target.key,
                "sequence_name": target.name,
                "cycle_type": _cycle_value(target.cycle_type),
                "is_repeating": target.is_repeating,
                "replaced_sequence_key": replaced,
                # None when the species has no LifecycleConfig — a valid state; the
                # edge alone drives the engine.
                "lifecycle_key": result.get("lifecycle_key"),
            },
            links=[
                # get_species_phase_sequence is the read tool that surfaces this
                # write again (§4.1 addressability).
                ctx.global_link(f"/species/{args.species_key}/phase-sequence"),
            ],
        )

    @staticmethod
    def _resolve(ctx: ToolContext, args: Input) -> tuple[Any, Any]:
        """Check the sequence exists and read the binding being replaced.

        Runs on the dry-run path too, so a preview cannot approve a binding the
        write would refuse with a 404.
        """

        target = ctx.phase_sequence_service.get_sequence(args.sequence_key)
        current = ctx.phase_sequence_service.get_sequence_by_species(args.species_key)
        return target, current


__all__ = [
    "AssignSpeciesPhaseSequence",
    "GetPlantPhaseHistory",
    "GetPlantPhaseStatus",
    "GetSpeciesLifecycle",
    "GetSpeciesPhaseSequence",
    "ListPhaseSequences",
    "ListSpeciesByPhaseSequence",
    "TransitionPlantPhase",
]
