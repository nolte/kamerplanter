"""Resolves which soil-hazard durations may carry a time statement (REQ-054 §5.2a).

Pure logic over a preloaded :class:`SoilHazardKnowledge` row. The one rule this
engine owns: **only a 3/3-evidenced duration is usable** for a time statement in a
warning or for a block (H-10). Every other status — insufficient, contradictory,
not found — resolves to ``None`` even when the table records a value, so the
consumers (bed soil hazards F-20, replant hint F-21, planner H-10) can never turn
a 2/3 figure into a date. Whether a value is usable is read from its status only;
changing the status in the data changes the result without touching code.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.common.enums import EvidenceKind, EvidenceStatus, SoilHazard
from app.domain.models.soil_hazard_knowledge import EvidencedYears, SoilHazardKnowledge


class ResolvedSoilHazardDurations(BaseModel):
    """Durations of one hazard that may carry a time statement; ``None`` = no time statement.

    Each duration comes with its evidence kind, so a consumer can tell "at least 15
    years" (``lower_bound``) from "15 years" (``number``) or a value inside every
    source's range (``range``). The kind is ``None`` exactly when the duration is.
    """

    model_config = ConfigDict(frozen=True)

    hazard: SoilHazard
    soil_persistence_years: int | None
    soil_persistence_kind: EvidenceKind | None
    max_survival_years: int | None
    max_survival_kind: EvidenceKind | None
    soft: bool


class SoilHazardKnowledgeEngine:
    """Stateless: no data access, input is a loaded knowledge row."""

    def usable_years(self, value: EvidencedYears) -> int | None:
        """Return the duration if it is 3/3-evidenced, else ``None``."""
        if value.evidence.status is EvidenceStatus.EVIDENCED:
            return value.years
        return None

    def usable_kind(self, value: EvidencedYears) -> EvidenceKind | None:
        """Return the evidence kind of a usable duration, else ``None``."""
        if self.usable_years(value) is None:
            return None
        return value.evidence.kind

    def resolve_durations(self, row: SoilHazardKnowledge) -> ResolvedSoilHazardDurations:
        """Return the usable cultivation pause and maximum survival of ``row`` with their kinds."""
        return ResolvedSoilHazardDurations(
            hazard=row.hazard,
            soil_persistence_years=self.usable_years(row.soil_persistence_years),
            soil_persistence_kind=self.usable_kind(row.soil_persistence_years),
            max_survival_years=self.usable_years(row.max_survival_years),
            max_survival_kind=self.usable_kind(row.max_survival_years),
            soft=row.soft,
        )
