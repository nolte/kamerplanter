"""Visual state of one plant on the garden plan — a pure function (REQ-053 GP-FR-192, GP-UX-059/060).

``compute(plant, phase, tasks, findings, ..., now)`` turns what the plan already knows about a plant into
what the marker draws: the lifecycle (ring style, §11.3), the phase and its progress (ring colour and
segment), the sorted reasons that need attention (the one badge, GP-UX-060) and whether the plant is ready
to harvest. No I/O, no clock: ``now`` is an argument. This module is the Python reference of the shared
Backend <-> Frontend logic (§19.6): the TypeScript port in ``features/gardenPlanner/model/plantState.ts``
runs against the same vectors in ``spec/e2e-testcases/fixtures/garden-plan-vectors.json`` (operation
``plant_state``, GP-ACC-050), and the server answer wins on any difference.

**Calendar days, UTC.** Every comparison works on UTC calendar days, never on instants: a task due at any time
of day *before today* is overdue, a task due *today* is "due today" (it is not overdue yet). That keeps the
answer independent of the hour at which the plan is opened and identical between server and client.

**Priority (GP-UX-060).** ``problem > frost > overdue > water > harvest``. :data:`ATTENTION_PRIORITY` is the
order of ``attention``; the first entry is the one badge, the others are text in the plant info.

**Missing sources drop their reason** (§11.4, data availability): a plant without findings data has no
``problem`` reason, a bed without a frost flag no ``frost`` reason — never an error.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Literal

type Lifecycle = Literal["planned", "sown", "active", "harvesting", "failed", "historic"]
type AttentionCode = Literal["problem", "frost", "overdue", "water", "harvest"]

#: Lifecycle values (§11.3) — the ring style of the marker.
LIFECYCLES: tuple[Lifecycle, ...] = ("planned", "sown", "active", "harvesting", "failed", "historic")
#: Reasons that need attention, highest priority first (GP-UX-060).
ATTENTION_PRIORITY: tuple[AttentionCode, ...] = ("problem", "frost", "overdue", "water", "harvest")
#: ``termination_type`` values that count as a failure (§11.3 "ausgefallen").
FAILED_TERMINATIONS = frozenset({"died", "senesced"})
#: Task category of a watering task: due today it is the reason ``water``.
WATERING_CATEGORY = "watering"

type PlantKind = Literal["plant", "planned", "sown"]


@dataclass(frozen=True)
class PlantFacts:
    """What the plan knows about the plant itself.

    ``kind`` ``planned``/``sown`` is a reservation without a plant (§11.3): the other fields are then unused.
    """

    kind: PlantKind = "plant"
    removed_on: date | None = None
    termination_type: str | None = None


@dataclass(frozen=True)
class PhaseFacts:
    """The plant's current growth phase; ``typical_days`` is ``None`` when the phase has no typical length."""

    key: str
    started_on: date
    typical_days: int | None = None
    allows_harvest: bool = False
    is_terminal: bool = False


@dataclass(frozen=True)
class OpenTask:
    """An open task of the plant: its category and the calendar day it is due (``None`` = no due date)."""

    category: str
    due: date | None = None


@dataclass(frozen=True)
class PhaseProgress:
    """``elapsed_d`` whole days in the phase, ``typical_d`` its usual length, ``fraction`` in ``[0, 1]``."""

    elapsed_d: int
    typical_d: int | None
    fraction: float | None
    next_phase_eta: date | None


@dataclass(frozen=True)
class AttentionReason:
    reason: AttentionCode
    count: int


@dataclass(frozen=True)
class PlantVisualState:
    lifecycle: Lifecycle
    phase_key: str | None
    phase_progress: PhaseProgress | None
    attention: tuple[AttentionReason, ...]
    harvest_ready: bool
    harvest_ready_from: date | None


def _lifecycle(plant: PlantFacts, harvest_batches: int) -> Lifecycle:
    if plant.kind != "plant":
        return plant.kind
    if plant.termination_type in FAILED_TERMINATIONS:
        return "failed"
    if plant.removed_on is not None or plant.termination_type is not None:
        return "historic"
    return "harvesting" if harvest_batches > 0 else "active"


def _progress(phase: PhaseFacts, today: date) -> PhaseProgress:
    elapsed = max((today - phase.started_on).days, 0)
    typical = phase.typical_days if phase.typical_days is not None and phase.typical_days > 0 else None
    fraction = None if typical is None else min(elapsed / typical, 1.0)
    eta = None if typical is None or phase.is_terminal else phase.started_on + timedelta(days=typical)
    return PhaseProgress(elapsed_d=elapsed, typical_d=typical, fraction=fraction, next_phase_eta=eta)


def compute(
    plant: PlantFacts,
    phase: PhaseFacts | None,
    tasks: Sequence[OpenTask],
    *,
    open_findings: int,
    frost_risk: bool,
    harvest_batches: int,
    now: datetime,
) -> PlantVisualState:
    """The visual state of ``plant`` at ``now`` (UTC calendar day). See the module docstring for the rules."""
    today = (now.astimezone(UTC) if now.tzinfo is not None else now).date()
    lifecycle = _lifecycle(plant, harvest_batches)
    live = lifecycle in {"active", "harvesting"}
    progress = _progress(phase, today) if phase is not None and plant.kind == "plant" else None
    harvest_ready = bool(live and phase is not None and phase.allows_harvest)

    counts: dict[AttentionCode, int] = {}
    if live:
        overdue = sum(1 for task in tasks if task.due is not None and task.due < today)
        water = sum(1 for task in tasks if task.category == WATERING_CATEGORY and task.due == today)
        counts = {
            "problem": max(open_findings, 0),
            "frost": 1 if frost_risk else 0,
            "overdue": overdue,
            "water": water,
            "harvest": 1 if harvest_ready else 0,
        }
    attention = tuple(AttentionReason(reason, counts[reason]) for reason in ATTENTION_PRIORITY if counts.get(reason))
    return PlantVisualState(
        lifecycle=lifecycle,
        phase_key=phase.key if phase is not None and plant.kind == "plant" else None,
        phase_progress=progress,
        attention=attention,
        harvest_ready=harvest_ready,
        harvest_ready_from=phase.started_on if harvest_ready and phase is not None else None,
    )
