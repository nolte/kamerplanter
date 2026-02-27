from datetime import datetime

from app.common.exceptions import NotFoundError, ResistanceWarningError
from app.domain.engines.inspection_scheduler import InspectionScheduler
from app.domain.engines.resistance_engine import ResistanceManager
from app.domain.engines.safety_interval_engine import SafetyIntervalValidator
from app.domain.interfaces.ipm_repository import IIpmRepository
from app.domain.models.ipm import (
    Disease,
    Inspection,
    Pest,
    Treatment,
    TreatmentApplication,
)


class IpmService:
    def __init__(
        self,
        repo: IIpmRepository,
        safety_validator: SafetyIntervalValidator,
        resistance_mgr: ResistanceManager,
        inspection_scheduler: InspectionScheduler,
    ) -> None:
        self._repo = repo
        self._safety = safety_validator
        self._resistance = resistance_mgr
        self._scheduler = inspection_scheduler

    # ── Pest CRUD ──

    def list_pests(self, offset: int = 0, limit: int = 50) -> tuple[list[Pest], int]:
        return self._repo.get_all_pests(offset, limit)

    def get_pest(self, key: str) -> Pest:
        pest = self._repo.get_pest_by_key(key)
        if not pest:
            raise NotFoundError("Pest", key)
        return pest

    def create_pest(self, pest: Pest) -> Pest:
        return self._repo.create_pest(pest)

    def update_pest(self, key: str, data: dict) -> Pest:
        existing = self.get_pest(key)
        allowed = {"scientific_name", "common_name", "pest_type", "lifecycle_days",
                    "optimal_temp_min", "optimal_temp_max", "detection_difficulty", "description"}
        for field, value in data.items():
            if field in allowed:
                setattr(existing, field, value)
        return self._repo.update_pest(key, existing)

    def delete_pest(self, key: str) -> bool:
        self.get_pest(key)
        return self._repo.delete_pest(key)

    # ── Disease CRUD ──

    def list_diseases(self, offset: int = 0, limit: int = 50) -> tuple[list[Disease], int]:
        return self._repo.get_all_diseases(offset, limit)

    def get_disease(self, key: str) -> Disease:
        disease = self._repo.get_disease_by_key(key)
        if not disease:
            raise NotFoundError("Disease", key)
        return disease

    def create_disease(self, disease: Disease) -> Disease:
        return self._repo.create_disease(disease)

    def update_disease(self, key: str, data: dict) -> Disease:
        existing = self.get_disease(key)
        allowed = {"scientific_name", "common_name", "pathogen_type", "incubation_period_days",
                    "environmental_triggers", "affected_plant_parts", "description"}
        for field, value in data.items():
            if field in allowed:
                setattr(existing, field, value)
        return self._repo.update_disease(key, existing)

    def delete_disease(self, key: str) -> bool:
        self.get_disease(key)
        return self._repo.delete_disease(key)

    # ── Treatment CRUD ──

    def list_treatments(self, offset: int = 0, limit: int = 50) -> tuple[list[Treatment], int]:
        return self._repo.get_all_treatments(offset, limit)

    def get_treatment(self, key: str) -> Treatment:
        treatment = self._repo.get_treatment_by_key(key)
        if not treatment:
            raise NotFoundError("Treatment", key)
        return treatment

    def create_treatment(self, treatment: Treatment) -> Treatment:
        return self._repo.create_treatment(treatment)

    def update_treatment(self, key: str, data: dict) -> Treatment:
        existing = self.get_treatment(key)
        allowed = {"name", "treatment_type", "active_ingredient", "application_method",
                    "safety_interval_days", "dosage_per_liter", "protective_equipment", "description"}
        for field, value in data.items():
            if field in allowed:
                setattr(existing, field, value)
        return self._repo.update_treatment(key, existing)

    def delete_treatment(self, key: str) -> bool:
        self.get_treatment(key)
        return self._repo.delete_treatment(key)

    # ── Inspection ──

    def create_inspection(self, plant_key: str, inspection: Inspection) -> Inspection:
        inspection.plant_key = plant_key
        return self._repo.create_inspection(inspection)

    def get_inspections(self, plant_key: str, offset: int = 0, limit: int = 50) -> tuple[list[Inspection], int]:
        return self._repo.get_inspections_for_plant(plant_key, offset, limit)

    # ── Treatment Application ──

    def create_treatment_application(
        self, plant_key: str, application: TreatmentApplication,
    ) -> TreatmentApplication:
        application.plant_key = plant_key

        # Resistance check
        treatment = self.get_treatment(application.treatment_key)
        if treatment.active_ingredient:
            recent = self._repo.get_recent_applications(plant_key)
            is_safe, warning = self._resistance.validate_treatment(
                recent, treatment.active_ingredient,
            )
            if not is_safe:
                raise ResistanceWarningError(
                    treatment.active_ingredient,
                    len([r for r in recent if r.get("active_ingredient") == treatment.active_ingredient]),
                )

        return self._repo.create_treatment_application(application)

    def get_applications(
        self, plant_key: str, offset: int = 0, limit: int = 50,
    ) -> tuple[list[TreatmentApplication], int]:
        return self._repo.get_applications_for_plant(plant_key, offset, limit)

    # ── Karenz-Gate API ──

    def check_harvest_safety(self, plant_key: str, planned_date: datetime | None = None) -> tuple[bool, list[dict]]:
        """Check if harvest is safe for a plant (Karenz-Gate)."""
        karenz_periods = self._repo.get_active_karenz_periods(plant_key)
        if not karenz_periods:
            return True, []
        if planned_date is None:
            planned_date = datetime.now()
        return self._safety.can_harvest(karenz_periods, planned_date)

    def get_karenz_periods(self, plant_key: str) -> list[dict]:
        return self._repo.get_active_karenz_periods(plant_key)

    # ── Recommendations ──

    def get_treatment_recommendations(self, plant_key: str, pest_key: str) -> list[dict]:
        treatments = self._repo.get_treatments_for_pest(pest_key)
        recent = self._repo.get_recent_applications(plant_key)
        available = [
            {"name": t.name, "treatment_type": t.treatment_type,
             "active_ingredient": t.active_ingredient, "key": t.key}
            for t in treatments
        ]
        return self._resistance.suggest_alternatives(recent, available)

    # ── Inspection Schedule ──

    def get_inspection_schedule(self, plant_key: str, current_phase: str, pressure_level: str) -> dict:
        inspections, _ = self._repo.get_inspections_for_plant(plant_key, 0, 1)
        last_at = inspections[0].inspected_at if inspections else None
        next_date = self._scheduler.next_inspection_date(last_at, current_phase, pressure_level)
        urgency = self._scheduler.calculate_urgency(next_date)
        return {
            "next_inspection": next_date.isoformat(),
            "last_inspection": last_at.isoformat() if last_at else None,
            **urgency,
        }
