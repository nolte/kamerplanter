"""Cause class of an unplanned loss (REQ-003 E5 v2.23, REQ-053 §11.3a Nr. 1-2, #2888 F-19).

The one home of the pre-fill table: per ``termination_cause`` the class the dialog pre-fills,
the classes the gardener may pick instead, and whether the wilt follow-up question is asked.
The frontend reads it from ``GET /plant-instances/{key}/termination-options``; the backend
validates every recorded loss against it. Source of every row:
``spec/analysis/agrobiology-soil-hazards-research-2888.md`` §5 (mirrored in REQ-003 E5;
``tests/unit/guards/test_req003_e5_failure_cause_matches_spec.py`` keeps both equal).
"""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.common.enums import (
    FailureCauseClass,
    PathogenConfirmationSource,
    SoilHazard,
    TerminationCause,
    WiltFollowUp,
)

#: The class a "yes" to the wilt follow-up offers: wilting on moist soil, brown vessels in the stem or brown roots
#: can be Verticillium or another soil-borne disease (research R-003, R-004.1 b, 3/3).
WILT_FOLLOW_UP_CLASS: FailureCauseClass = FailureCauseClass.DISEASE_SOIL

#: Families with a wilt risk: an ``unknown`` loss on one of them gets the wilt follow-up (research §5, REQ-053
#: §11.3a Nr. 1). APG IV family names as stored in ``BotanicalFamily.name``.
WILT_PRONE_FAMILIES: frozenset[str] = frozenset({"Solanaceae", "Brassicaceae", "Cucurbitaceae", "Rosaceae"})

#: Classes whose loss may name a pathogen from the soil-hazard list (REQ-053 §11.3a Nr. 5).
SOIL_BORNE_CLASSES: frozenset[FailureCauseClass] = frozenset(
    {FailureCauseClass.PEST_SOIL, FailureCauseClass.DISEASE_SOIL}
)

#: Name of the growth phase a premature bolt enters (REQ-003 E6, ``vegetative → bolting`` with ``is_premature``).
BOLTING_PHASE_NAME: str = "bolting"


class FailureCauseRule(BaseModel):
    """One row of the pre-fill table: what a ``termination_cause`` pre-fills and allows."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    termination_cause: TerminationCause
    prefill: FailureCauseClass | None = Field(
        description="Class the dialog pre-fills; None = no pre-fill, the gardener must choose (disease, pest).",
    )
    choices: tuple[FailureCauseClass, ...] = Field(
        min_length=1,
        description="Every class the gardener may record for this cause, the pre-fill included.",
    )
    wilt_follow_up: WiltFollowUp = WiltFollowUp.NEVER

    @model_validator(mode="after")
    def _row_is_consistent(self) -> Self:
        """The pre-fill is a choice, a mandatory choice offers more than one class, a wilt row offers the wilt class."""
        if len(set(self.choices)) != len(self.choices):
            msg = f"{self.termination_cause}: a class is listed twice"
            raise ValueError(msg)
        if self.prefill is not None and self.prefill not in self.choices:
            msg = f"{self.termination_cause}: the pre-fill {self.prefill} is not among the choices"
            raise ValueError(msg)
        if self.prefill is None and len(self.choices) < 2:  # noqa: PLR2004 - a choice needs two options
            msg = f"{self.termination_cause}: a mandatory choice needs at least two classes"
            raise ValueError(msg)
        if self.wilt_follow_up is not WiltFollowUp.NEVER and WILT_FOLLOW_UP_CLASS not in self.choices:
            msg = f"{self.termination_cause}: the wilt follow-up offers {WILT_FOLLOW_UP_CLASS}, which is no choice"
            raise ValueError(msg)
        return self


class FailureCauseTable(BaseModel):
    """The whole table, one row per ``TerminationCause`` in the enum's order."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    rules: tuple[FailureCauseRule, ...]

    @model_validator(mode="after")
    def _one_row_per_cause(self) -> Self:
        """Every cause of the vocabulary has exactly one row, so a new cause cannot go unclassified."""
        causes = [rule.termination_cause for rule in self.rules]
        duplicates = sorted({cause for cause in causes if causes.count(cause) > 1})
        if duplicates:
            msg = f"causes listed more than once: {duplicates}"
            raise ValueError(msg)
        missing = sorted(set(TerminationCause) - set(causes))
        if missing:
            msg = f"causes without a row: {missing}"
            raise ValueError(msg)
        return self

    def rule_for(self, cause: TerminationCause) -> FailureCauseRule:
        """The row of ``cause``; every cause has one (validated above)."""
        return next(rule for rule in self.rules if rule.termination_cause is cause)


def _abiotic(cause: TerminationCause, *, wilt: bool = False) -> FailureCauseRule:
    """An abiotic cause: pre-filled ``abiotic``; with the wilt follow-up it may become ``disease_soil``."""
    if wilt:
        return FailureCauseRule(
            termination_cause=cause,
            prefill=FailureCauseClass.ABIOTIC,
            choices=(FailureCauseClass.ABIOTIC, WILT_FOLLOW_UP_CLASS),
            wilt_follow_up=WiltFollowUp.ALWAYS,
        )
    return FailureCauseRule(
        termination_cause=cause, prefill=FailureCauseClass.ABIOTIC, choices=(FailureCauseClass.ABIOTIC,)
    )


#: Research §5 / REQ-003 E5, row by row, in the order of ``TerminationCause``.
FAILURE_CAUSE_TABLE: FailureCauseTable = FailureCauseTable(
    rules=(
        FailureCauseRule(
            termination_cause=TerminationCause.DISEASE,
            prefill=None,
            choices=(FailureCauseClass.DISEASE_FOLIAR, FailureCauseClass.DISEASE_SOIL),
        ),
        FailureCauseRule(
            termination_cause=TerminationCause.PEST,
            prefill=None,
            choices=(FailureCauseClass.PEST_FOLIAR, FailureCauseClass.PEST_SOIL),
        ),
        _abiotic(TerminationCause.FROST),
        _abiotic(TerminationCause.HEAT, wilt=True),
        _abiotic(TerminationCause.DROUGHT, wilt=True),
        _abiotic(TerminationCause.WATERLOGGING, wilt=True),
        _abiotic(TerminationCause.NEGLECT),
        FailureCauseRule(
            termination_cause=TerminationCause.MECHANICAL,
            prefill=FailureCauseClass.MECHANICAL,
            choices=(FailureCauseClass.MECHANICAL,),
        ),
        _abiotic(TerminationCause.BOLTING),
        FailureCauseRule(
            termination_cause=TerminationCause.UNKNOWN,
            prefill=FailureCauseClass.UNKNOWN,
            choices=tuple(FailureCauseClass),
            wilt_follow_up=WiltFollowUp.WILT_PRONE_FAMILY,
        ),
    )
)


class FailureRecord(BaseModel):
    """The cause-class fields a ``died`` loss stores on the plant instance; all ``None`` = no class (legacy)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    failure_cause_class: FailureCauseClass | None = None
    failure_pathogen: SoilHazard | None = None
    failure_pathogen_confirmed: bool | None = None
    failure_pathogen_source: PathogenConfirmationSource | None = None


class ResolvedFailureCauseRule(BaseModel):
    """A table row resolved for one plant: whether the wilt follow-up is asked for it."""

    model_config = ConfigDict(frozen=True)

    termination_cause: TerminationCause
    prefill: FailureCauseClass | None
    choices: tuple[FailureCauseClass, ...]
    asks_wilt_follow_up: bool


class TerminationOptions(BaseModel):
    """What the termination dialog of one plant offers (REQ-003 E5/E6, REQ-053 §11.3a Nr. 1-2, 5)."""

    model_config = ConfigDict(frozen=True)

    suggested_cause: TerminationCause | None
    wilt_prone_family: bool
    rules: tuple[ResolvedFailureCauseRule, ...]
    wilt_follow_up_class: FailureCauseClass = WILT_FOLLOW_UP_CLASS
    pathogen_classes: tuple[FailureCauseClass, ...]
    pathogens: tuple[SoilHazard, ...] = tuple(SoilHazard)
    confirmation_sources: tuple[PathogenConfirmationSource, ...] = tuple(PathogenConfirmationSource)
