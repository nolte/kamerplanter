"""Soil-hazard knowledge table (REQ-054 §5.2a, #2888 F-18).

Read-only reference data: per soil hazard the cultivation pause after a confirmed
infestation (``soil_persistence_years``), the maximum survival of the pathogen
without a host (``max_survival_years``), the hosts at family, genus or species
level and an evidence status per value. Source of every value:
``spec/analysis/agrobiology-soil-hazards-research-2888.md``.

The models enforce the evidence invariants, so a table that claims 3/3 for a value
it does not carry, or a duration it has no evidence shape for, is refused at load
time instead of producing a time statement later.
"""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.common.enums import EvidenceKind, EvidenceStatus, HostLevel, SoilHazard

#: Number of independent full-text sources that make a value usable (method E-10).
EVIDENCED_SOURCE_COUNT: int = 3

#: Upper bound for a duration in the table; the longest researched value is 20 years.
MAX_TABLE_YEARS: int = 50


class Evidence(BaseModel):
    """How well one value of the table is backed."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    status: EvidenceStatus
    sources: int = Field(
        ge=0,
        le=EVIDENCED_SOURCE_COUNT,
        description="Independent full-text sources supporting the stated value, capped at 3.",
    )
    kind: EvidenceKind | None = Field(
        default=None,
        description="Shape of the agreement; required for an evidenced duration.",
    )
    basis: str = Field(min_length=1, description="Short citation of the sources behind the value.")
    ref: str = Field(min_length=1, description="Section of the research document.")

    @model_validator(mode="after")
    def _status_matches_sources(self) -> Self:
        """``evidenced`` is exactly 3/3; anything below three sources is not."""
        if self.status is EvidenceStatus.EVIDENCED and self.sources != EVIDENCED_SOURCE_COUNT:
            msg = f"status 'evidenced' needs {EVIDENCED_SOURCE_COUNT} sources, got {self.sources}"
            raise ValueError(msg)
        if self.status is EvidenceStatus.INSUFFICIENT and self.sources >= EVIDENCED_SOURCE_COUNT:
            msg = "status 'insufficient' needs fewer than three sources"
            raise ValueError(msg)
        if self.status is EvidenceStatus.NOT_FOUND and self.sources != 0:
            msg = "status 'not_found' cannot name supporting sources"
            raise ValueError(msg)
        return self


class EvidencedYears(BaseModel):
    """A duration in whole years with its evidence; ``years`` is ``None`` when unknown."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    years: int | None = Field(default=None, ge=1, le=MAX_TABLE_YEARS)
    evidence: Evidence

    @model_validator(mode="after")
    def _value_matches_evidence(self) -> Self:
        """An evidenced duration has a value and an evidence shape; ``not_found`` has no value."""
        status = self.evidence.status
        if status is EvidenceStatus.EVIDENCED:
            if self.years is None:
                msg = "an evidenced duration needs a value"
                raise ValueError(msg)
            if self.evidence.kind is None:
                msg = "an evidenced duration needs evidence.kind (number, lower_bound or range)"
                raise ValueError(msg)
        if status is EvidenceStatus.NOT_FOUND and self.years is not None:
            msg = "status 'not_found' cannot carry a value"
            raise ValueError(msg)
        return self


class HostEntry(BaseModel):
    """A host (or non-host) at one taxonomic level.

    ``name`` is the APG IV family name, the genus, or the scientific species name
    as stored in ``Species.scientific_name``.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    level: HostLevel
    name: str = Field(min_length=1)
    evidence: Evidence


class SoilHazardKnowledge(BaseModel):
    """Knowledge-table row of one soil hazard."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    hazard: SoilHazard
    pathogens: list[str] = Field(min_length=1)
    soil_persistence_years: EvidencedYears = Field(
        description="Cultivation pause after a confirmed infestation — not the rotation length.",
    )
    max_survival_years: EvidencedYears = Field(
        description="Maximum survival of the pathogen without a host (residual risk).",
    )
    hosts: list[HostEntry] = Field(min_length=1)
    non_hosts: list[HostEntry] = Field(default_factory=list)
    soft: bool = Field(
        default=False,
        description="Host range so broad that the hazard only ever yields a hint, never a block.",
    )
    notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _hosts_are_unique(self) -> Self:
        """A taxon is listed once, and never as host and non-host at the same time."""
        host_ids = [(entry.level, entry.name) for entry in self.hosts]
        non_host_ids = [(entry.level, entry.name) for entry in self.non_hosts]
        if len(set(host_ids)) != len(host_ids) or len(set(non_host_ids)) != len(non_host_ids):
            msg = f"{self.hazard}: a host or non-host is listed twice"
            raise ValueError(msg)
        both = set(host_ids) & set(non_host_ids)
        if both:
            msg = f"{self.hazard}: listed as host and non-host: {sorted(name for _, name in both)}"
            raise ValueError(msg)
        return self


class SoilHazardKnowledgeTable(BaseModel):
    """The whole table, one row per hazard."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    hazards: list[SoilHazardKnowledge]

    @model_validator(mode="after")
    def _one_row_per_hazard(self) -> Self:
        """Every hazard of the vocabulary has exactly one row."""
        keys = [row.hazard for row in self.hazards]
        duplicates = sorted({key for key in keys if keys.count(key) > 1})
        if duplicates:
            msg = f"hazards listed more than once: {duplicates}"
            raise ValueError(msg)
        missing = sorted(set(SoilHazard) - set(keys))
        if missing:
            msg = f"hazards without a row: {missing}"
            raise ValueError(msg)
        return self
