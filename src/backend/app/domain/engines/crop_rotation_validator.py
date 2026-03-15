from dataclasses import dataclass, field
from typing import Literal

from app.common.exceptions import RotationViolationError
from app.config.constants import DEFAULT_ROTATION_WINDOW_YEARS
from app.domain.interfaces.graph_repository import IGraphRepository
from app.domain.interfaces.plant_instance_repository import IPlantInstanceRepository
from app.domain.interfaces.species_repository import ISpeciesRepository


@dataclass
class RotationValidationResult:
    severity: Literal["OK", "INFO", "WARNING", "CRITICAL"]
    message: str
    nitrogen_benefit: str | None = None
    pest_risk: dict | None = field(default=None)
    rotation_benefit: dict | None = field(default=None)


class CropRotationValidator:
    """Validates crop rotation rules for a slot with differentiated severity levels."""

    def __init__(
        self,
        plant_repo: IPlantInstanceRepository,
        species_repo: ISpeciesRepository,
        graph_repo: IGraphRepository | None = None,
    ) -> None:
        self._plant_repo = plant_repo
        self._species_repo = species_repo
        self._graph_repo = graph_repo

    def validate_planting(
        self,
        slot_key: str,
        species_key: str,
        rotation_window_years: int = DEFAULT_ROTATION_WINDOW_YEARS,
    ) -> list[RotationValidationResult]:
        """Check crop rotation and return differentiated results."""
        results: list[RotationValidationResult] = []

        species = self._species_repo.get_by_key(species_key)
        if species is None:
            return [RotationValidationResult(severity="CRITICAL", message="Species not found")]

        planned_family_key = species.family_key
        if not planned_family_key:
            return [RotationValidationResult(severity="INFO", message="No family assigned — cannot evaluate rotation")]

        # Check if planned family is nitrogen-fixing
        planned_family = None
        try:
            from app.common.dependencies import get_family_repo

            family_repo = get_family_repo()
            planned_family = family_repo.get_by_key(planned_family_key)
        except Exception:
            pass

        history = self._plant_repo.get_history_by_slot(slot_key, years=rotation_window_years)

        for past_plant in history:
            past_species = self._species_repo.get_by_key(past_plant.species_key)
            if past_species is None:
                continue

            past_family_key = past_species.family_key
            if not past_family_key:
                continue

            # CRITICAL: Same family planted within rotation window
            if past_family_key == planned_family_key:
                results.append(
                    RotationValidationResult(
                        severity="CRITICAL",
                        message=(
                            f"Same family '{planned_family_key}' was planted in this slot"
                            f" within the last {rotation_window_years} years"
                        ),
                    )
                )
                continue

            # WARNING: shared pest risk (high)
            if self._graph_repo:
                pest_risks = self._graph_repo.get_pest_risks(planned_family_key)
                for pr in pest_risks:
                    pr_family_key = pr["family"].get("_key", "")
                    if pr_family_key == past_family_key and pr.get("risk_level") == "high":
                        results.append(
                            RotationValidationResult(
                                severity="WARNING",
                                message=(
                                    f"High pest risk between family '{planned_family_key}'"
                                    f" and previously planted '{past_family_key}'"
                                ),
                                pest_risk={
                                    "shared_pests": pr.get("shared_pests", []),
                                    "shared_diseases": pr.get("shared_diseases", []),
                                    "risk_level": pr.get("risk_level"),
                                },
                            )
                        )

            # OK: good rotation (benefit edge exists)
            if self._graph_repo:
                successors = self._graph_repo.get_rotation_successors(past_family_key)
                for succ in successors:
                    succ_family_key = succ["family"].get("_key", "")
                    if succ_family_key == planned_family_key:
                        results.append(
                            RotationValidationResult(
                                severity="OK",
                                message=(
                                    f"Good rotation: '{planned_family_key}' is a recommended"
                                    f" successor for '{past_family_key}'"
                                ),
                                rotation_benefit={
                                    "benefit_score": succ.get("benefit_score", 0.0),
                                    "benefit_reason": succ.get("benefit_reason", ""),
                                },
                            )
                        )

        # Nitrogen benefit note
        if planned_family and getattr(planned_family, "nitrogen_fixing", False):
            for r in results:
                r.nitrogen_benefit = "Nitrogen-fixing species improves soil for subsequent crops"

        if not results:
            results.append(
                RotationValidationResult(
                    severity="INFO",
                    message="No specific rotation recommendation for this combination",
                )
            )

        # Legacy compat: return highest severity first
        severity_order = {"CRITICAL": 0, "WARNING": 1, "INFO": 2, "OK": 3}
        results.sort(key=lambda r: severity_order.get(r.severity, 99))

        return results

    def validate_or_raise(
        self,
        slot_key: str,
        species_key: str,
        rotation_window_years: int = DEFAULT_ROTATION_WINDOW_YEARS,
    ) -> None:
        results = self.validate_planting(slot_key, species_key, rotation_window_years)
        for r in results:
            if r.severity == "CRITICAL":
                species = self._species_repo.get_by_key(species_key)
                family = species.family_key if species else "unknown"
                raise RotationViolationError(family, slot_key, rotation_window_years)
