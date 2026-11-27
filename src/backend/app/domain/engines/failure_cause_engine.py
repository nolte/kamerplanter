"""Derives and checks the cause class of an unplanned loss (REQ-003 E5/E6, REQ-053 §11.3a Nr. 1-2, 5, #2888 F-19).

Pure logic over the one pre-fill table (``FAILURE_CAUSE_TABLE``). Two readers share the rule:
the request schema of ``POST /plant-instances/{key}/remove`` turns the violations into a 422 at
the boundary, the plant-instance service into a ``ValidationError`` for every other caller (MCP,
internal). A loss that names no cause and no class keeps no class — the bulk "clear bed" path and
legacy data behave as before (acceptance-5).
"""

from __future__ import annotations

from app.common.enums import (
    FailureCauseClass,
    PathogenConfirmationSource,
    SoilHazard,
    TerminationCause,
    TerminationType,
    WiltFollowUp,
)
from app.domain.models.failure_cause import (
    BOLTING_PHASE_NAME,
    FAILURE_CAUSE_TABLE,
    SOIL_BORNE_CLASSES,
    WILT_PRONE_FAMILIES,
    FailureCauseTable,
    FailureRecord,
    ResolvedFailureCauseRule,
    TerminationOptions,
)
from app.domain.models.phase import PhaseHistory

_WILT_PRONE_NORMALISED: frozenset[str] = frozenset(name.casefold() for name in WILT_PRONE_FAMILIES)


def find_failure_cause_violations(
    *,
    termination_type: TerminationType | None,
    termination_cause: TerminationCause | None,
    failure_cause_class: FailureCauseClass | None,
    failure_pathogen: SoilHazard | None,
    failure_pathogen_confirmed: bool | None,
    failure_pathogen_source: PathogenConfirmationSource | None,
    table: FailureCauseTable = FAILURE_CAUSE_TABLE,
) -> list[str]:
    """Every reason the cause-class fields of a loss are refused; empty = acceptable.

    Reports instead of raising, so each reader shapes its own error (BACKEND.md §5.4).
    """
    violations: list[str] = []
    captured = (
        failure_cause_class is not None
        or failure_pathogen is not None
        or failure_pathogen_confirmed is not None
        or failure_pathogen_source is not None
    )
    if captured and termination_type is not TerminationType.DIED:
        violations.append("failure_cause_class and the pathogen fields are only valid for termination_type='died'")
        return violations

    if termination_cause is not None:
        rule = table.rule_for(termination_cause)
        if failure_cause_class is None and rule.prefill is None:
            options = ", ".join(rule.choices)
            violations.append(f"termination_cause '{termination_cause}' needs a failure_cause_class: one of {options}")
        if failure_cause_class is not None and failure_cause_class not in rule.choices:
            options = ", ".join(rule.choices)
            violations.append(
                f"failure_cause_class '{failure_cause_class}' does not fit termination_cause "
                f"'{termination_cause}': one of {options}"
            )

    resolved_class = failure_cause_class
    if resolved_class is None and termination_cause is not None:
        resolved_class = table.rule_for(termination_cause).prefill
    if failure_pathogen is not None and resolved_class not in SOIL_BORNE_CLASSES:
        violations.append("failure_pathogen needs failure_cause_class 'pest_soil' or 'disease_soil'")
    if failure_pathogen_confirmed is not None and failure_pathogen is None:
        violations.append("failure_pathogen_confirmed needs a failure_pathogen")
    if failure_pathogen_source is not None and failure_pathogen_confirmed is not True:
        violations.append("failure_pathogen_source needs failure_pathogen_confirmed=true")
    if failure_pathogen_confirmed is True and failure_pathogen_source is None:
        violations.append("a confirmed pathogen needs failure_pathogen_source (who confirmed it)")
    return violations


class FailureCauseEngine:
    """Stateless: no data access, input is the loss as stated and preloaded plant facts."""

    def __init__(self, table: FailureCauseTable = FAILURE_CAUSE_TABLE) -> None:
        self._table = table

    def resolve(
        self,
        *,
        termination_cause: TerminationCause | None,
        failure_cause_class: FailureCauseClass | None,
        failure_pathogen: SoilHazard | None,
        failure_pathogen_confirmed: bool | None,
        failure_pathogen_source: PathogenConfirmationSource | None,
    ) -> FailureRecord:
        """The fields to store for an accepted ``died`` loss (call after ``find_failure_cause_violations``).

        A cause without a class gets the pre-fill of its row; no cause and no class stays without a class.
        A named pathogen is recorded as unconfirmed unless stated otherwise.
        """
        resolved = failure_cause_class
        if resolved is None and termination_cause is not None:
            resolved = self._table.rule_for(termination_cause).prefill
        confirmed = failure_pathogen_confirmed
        if failure_pathogen is not None and confirmed is None:
            confirmed = False
        return FailureRecord(
            failure_cause_class=resolved,
            failure_pathogen=failure_pathogen,
            failure_pathogen_confirmed=confirmed,
            failure_pathogen_source=failure_pathogen_source,
        )

    def suggested_cause(self, open_phase: PhaseHistory | None) -> TerminationCause | None:
        """``bolting`` when the plant stands in a bolting phase it entered prematurely (REQ-003 E6), else ``None``."""
        if open_phase is None or open_phase.exited_at is not None:
            return None
        if open_phase.is_premature and open_phase.phase_name == BOLTING_PHASE_NAME:
            return TerminationCause.BOLTING
        return None

    def is_wilt_prone(self, family_name: str | None) -> bool:
        """Whether the family is one of the wilt-prone families of research §5.

        The name is the only identifier a family has that is the same in every installation, so it is matched
        - with case and surrounding whitespace ignored: a family created through the API is checked only for
        its ``-aceae`` ending, not for the catalogue's spelling.
        """
        if family_name is None:
            return False
        return family_name.strip().casefold() in _WILT_PRONE_NORMALISED

    def options(self, *, open_phase: PhaseHistory | None, family_name: str | None) -> TerminationOptions:
        """The table resolved for one plant: its suggested cause and where the wilt follow-up is asked."""
        wilt_prone = self.is_wilt_prone(family_name)
        rules = tuple(
            ResolvedFailureCauseRule(
                termination_cause=rule.termination_cause,
                prefill=rule.prefill,
                choices=rule.choices,
                asks_wilt_follow_up=rule.wilt_follow_up is WiltFollowUp.ALWAYS
                or (rule.wilt_follow_up is WiltFollowUp.WILT_PRONE_FAMILY and wilt_prone),
            )
            for rule in self._table.rules
        )
        return TerminationOptions(
            suggested_cause=self.suggested_cause(open_phase),
            wilt_prone_family=wilt_prone,
            rules=rules,
            pathogen_classes=tuple(cls for cls in FailureCauseClass if cls in SOIL_BORNE_CLASSES),
        )
