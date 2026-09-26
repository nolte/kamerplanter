from datetime import datetime

from app.common.datetimes import now_utc
from app.common.enums import TreatmentType
from app.common.exceptions import ResistanceWarningError
from app.domain.engines.inspection_scheduler import InspectionScheduler
from app.domain.engines.resistance_engine import ResistanceManager
from app.domain.engines.safety_interval_engine import SafetyIntervalValidator
from app.domain.interfaces.ipm_repository import IIpmRepository
from app.domain.models.beneficial import Beneficial
from app.domain.models.ipm import (
    Disease,
    Inspection,
    Pest,
    Treatment,
    TreatmentApplication,
)
from app.domain.models.pest_taxonomy import get_taxon
from app.domain.services.catalogue_authorization import require_platform_admin_for_global_catalogue

# IPM-Hierarchie für die Gegenmaßnahmen-Reihenfolge auf der Detailseite
# (REQ-010 DoD „Kultur > Biologisch > Chemisch"; mechanisch vor chemisch).
_IPM_HIERARCHY: dict[TreatmentType, int] = {
    TreatmentType.CULTURAL: 0,
    TreatmentType.BIOLOGICAL: 1,
    TreatmentType.MECHANICAL: 2,
    TreatmentType.CHEMICAL: 3,
}


def _ipm_rank(treatment: Treatment) -> int:
    return _IPM_HIERARCHY.get(treatment.treatment_type, 99)


class IpmService:
    """IPM service — global catalogue plus the tenant-scoped observation records.

    **The catalogue half is installation-wide** (#1501). ``Pest``, ``Disease`` and
    ``Treatment`` are global reference data — ``app/api/v1/ipm/tenant_router.py``
    says so in its own module docstring, and the models bear it out: none of the
    three carries a ``tenant_key``, so one pest row is the row every tenant's IPM
    plan resolves. Their nine write methods therefore take ``is_platform_admin``
    **keyword-only and without a default**, and refuse anyone else through the
    same :func:`~app.domain.services.catalogue_authorization.require_platform_admin_for_global_catalogue`
    the species, substrate and import paths call.

    Until #1501 the nine routes above them resolved ``get_current_user`` alone, so
    any authenticated member of any tenant could delete a catalogue pest for
    everyone. ``create_disease`` / ``create_treatment`` stamp
    ``origin=DataOrigin.TENANT``, which reads like tenant ownership and is not:
    with no ``tenant_key`` on the model the marker records *that* a user created
    the row, never *which tenant owns* it, and nothing anywhere scopes a read by
    it. That marker is precisely why these creates looked tenant-local.

    The **tenant-scoped** half below (inspections, treatment applications, pest
    images) carries a ``tenant_key`` on its models, and its routes are gated on
    ``require_permission`` / ``require_attachment_permission`` — but that gate
    only answers *may this caller write in their own tenant*, never *is this
    plant theirs*. Until #1619 nothing asked the second question on the read
    side: ``GET .../plants/{plant_key}/karenz``, ``/harvest-safety``,
    ``/treatment-applications``, ``/inspections`` and ``/inspection-schedule``
    took the key from the path and answered 200 with another tenant's active
    ingredient, treatment name, Karenz window and inspection notes. The write
    half beside them was already correct (``create_inspection`` /
    ``create_treatment_application`` verify the plant at the repository, #517),
    and that asymmetry is exactly what made the read half easy to miss.

    Every plant-scoped method below therefore takes ``tenant_key`` **keyword-only
    and without a default** and runs :meth:`_require_own_plant` first.
    """

    #: The catalogue entity each refusal names. One map, so a 403 cannot name the
    #: wrong catalogue.
    _PEST = "pest"
    _DISEASE = "disease"
    _TREATMENT = "treatment"

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
        return self._repo.get_pest_or_raise(key)

    def get_inspection_photo_refs_for_pest(self, tenant_key: str, pest_key: str) -> list[str]:
        """Return a tenant's inspection photo attachment ids for a given pest.

        REQ-010 — feeds the pest detail gallery with the real photos of the
        tenant's own inspections in which this pest was detected. Strictly
        tenant-scoped and deduplicated (newest inspection first).
        """
        return self._repo.get_inspection_photo_refs_for_pest(tenant_key, pest_key)

    @staticmethod
    def _require_catalogue_admin(is_platform_admin: bool, entity: str) -> None:
        """Refuse a non-platform-admin write to the global IPM catalogue (#1501).

        One call site per write method rather than a decorator or a router-level
        dependency alone: the rule has to be reachable from a caller that is not an
        HTTP request, which is the argument ``catalogue_authorization`` makes about
        why it is not a FastAPI dependency in the first place.
        """
        require_platform_admin_for_global_catalogue(is_platform_admin=is_platform_admin, entity=entity)

    def create_pest(self, pest: Pest, *, is_platform_admin: bool) -> Pest:
        self._require_catalogue_admin(is_platform_admin, self._PEST)
        return self._repo.create_pest(pest)

    def update_pest(self, key: str, data: dict, *, is_platform_admin: bool) -> Pest:
        self._require_catalogue_admin(is_platform_admin, self._PEST)
        existing = self.get_pest(key)
        allowed = {
            "scientific_name",
            "common_name",
            "common_name_de",
            "pest_type",
            "lifecycle_days",
            "optimal_temp_min",
            "optimal_temp_max",
            "detection_difficulty",
            "description",
            "description_de",
            "damage_symptoms",
            "damage_symptoms_de",
            "affected_plant_parts",
            "host_plants",
            "host_plants_de",
            "prevention_tips",
            "prevention_tips_de",
            "monitoring_hints",
            "monitoring_hints_de",
            "severity",
            "optimal_humidity_min",
            "optimal_humidity_max",
            "detection_slug",
            "reference_image_refs",
        }
        for field, value in data.items():
            if field in allowed:
                setattr(existing, field, value)
        return self._repo.update_pest(key, existing)

    def delete_pest(self, key: str, *, is_platform_admin: bool) -> bool:
        self._require_catalogue_admin(is_platform_admin, self._PEST)
        self.get_pest(key)
        return self._repo.delete_pest(key)

    def get_pest_detail(self, key: str) -> dict:
        """Aggregierte Detailansicht: Stammdaten + Gegenmaßnahmen (nach
        IPM-Hierarchie) + passende Nützlinge + Schadbild-Hinweis (REQ-044)."""
        pest = self.get_pest(key)
        # Defensiv nach _key deduplizieren (falls mehrfache identische
        # targets_pest-Edges existieren) und nach IPM-Hierarchie sortieren.
        unique = {t.key: t for t in self._repo.get_treatments_for_pest(key)}
        treatments = sorted(unique.values(), key=_ipm_rank)
        beneficials: list[Beneficial] = []
        symptom_hint: str | None = None
        if pest.detection_slug:
            beneficials = self._repo.get_beneficials_for_pest_slug(pest.detection_slug)
            taxon = get_taxon(pest.detection_slug)
            symptom_hint = taxon.symptom_hint_de if taxon else None
        return {
            "pest": pest,
            "treatments": treatments,
            "beneficials": beneficials,
            "detection_symptom_hint": symptom_hint,
        }

    # ── Disease CRUD ──

    def list_diseases(self, offset: int = 0, limit: int = 50) -> tuple[list[Disease], int]:
        return self._repo.get_all_diseases(offset, limit)

    def get_disease(self, key: str) -> Disease:
        return self._repo.get_disease_or_raise(key)

    def create_disease(self, disease: Disease, *, is_platform_admin: bool) -> Disease:
        self._require_catalogue_admin(is_platform_admin, self._DISEASE)
        return self._repo.create_disease(disease)

    def update_disease(self, key: str, data: dict, *, is_platform_admin: bool) -> Disease:
        self._require_catalogue_admin(is_platform_admin, self._DISEASE)
        existing = self.get_disease(key)
        allowed = {
            "scientific_name",
            "common_name",
            "pathogen_type",
            "incubation_period_days",
            "environmental_triggers",
            "affected_plant_parts",
            "description",
        }
        for field, value in data.items():
            if field in allowed:
                setattr(existing, field, value)
        return self._repo.update_disease(key, existing)

    def delete_disease(self, key: str, *, is_platform_admin: bool) -> bool:
        self._require_catalogue_admin(is_platform_admin, self._DISEASE)
        self.get_disease(key)
        return self._repo.delete_disease(key)

    # ── Treatment CRUD ──

    def list_treatments(self, offset: int = 0, limit: int = 50) -> tuple[list[Treatment], int]:
        return self._repo.get_all_treatments(offset, limit)

    def get_treatment(self, key: str) -> Treatment:
        return self._repo.get_treatment_or_raise(key)

    def create_treatment(self, treatment: Treatment, *, is_platform_admin: bool) -> Treatment:
        self._require_catalogue_admin(is_platform_admin, self._TREATMENT)
        return self._repo.create_treatment(treatment)

    def update_treatment(self, key: str, data: dict, *, is_platform_admin: bool) -> Treatment:
        self._require_catalogue_admin(is_platform_admin, self._TREATMENT)
        existing = self.get_treatment(key)
        allowed = {
            "name",
            "name_de",
            "treatment_type",
            "active_ingredient",
            "application_method",
            "safety_interval_days",
            "dosage_per_liter",
            "protective_equipment",
            "description",
            "description_de",
            "how_to_apply",
            "how_to_apply_de",
            "mode_of_action",
            "mode_of_action_de",
            "precautions",
            "precautions_de",
        }
        for field, value in data.items():
            if field in allowed:
                setattr(existing, field, value)
        return self._repo.update_treatment(key, existing)

    def get_treatment_detail(self, key: str) -> dict:
        """Aggregierte Behandlungs-Detailansicht: Stammdaten der Maßnahme +
        die behandelten Schädlinge und Krankheiten (Reverse-Edges)."""
        treatment = self.get_treatment(key)
        pests = list({p.key: p for p in self._repo.get_pests_for_treatment(key)}.values())
        diseases = list({d.key: d for d in self._repo.get_diseases_for_treatment(key)}.values())
        return {
            "treatment": treatment,
            "targeted_pests": pests,
            "targeted_diseases": diseases,
        }

    def delete_treatment(self, key: str, *, is_platform_admin: bool) -> bool:
        self._require_catalogue_admin(is_platform_admin, self._TREATMENT)
        self.get_treatment(key)
        return self._repo.delete_treatment(key)

    # ── Inspection ──

    def _require_own_plant(self, plant_key: str, tenant_key: str) -> None:
        """The one predicate every plant-scoped operation below runs (#1619).

        One private method rather than a check per public method: the six
        callers cannot drift apart, and a seventh added later either calls it or
        has no ``tenant_key`` to pass, because the parameter is keyword-only
        **without a default** on every signature. That is what makes an unscoped
        call unwritable instead of merely discouraged — the #948 failure this
        repository has paid for repeatedly is a guard each call site opts into.
        """
        self._repo.verify_plant_ownership(plant_key, tenant_key)

    def create_inspection(self, plant_key: str, inspection: Inspection) -> Inspection:
        inspection.plant_key = plant_key
        return self._repo.create_inspection(inspection)

    def get_inspections(
        self,
        plant_key: str,
        offset: int = 0,
        limit: int = 50,
        *,
        tenant_key: str,
    ) -> tuple[list[Inspection], int]:
        self._require_own_plant(plant_key, tenant_key)
        return self._repo.get_inspections_for_plant(plant_key, offset, limit)

    # ── Treatment Application ──

    def create_treatment_application(
        self,
        plant_key: str,
        application: TreatmentApplication,
    ) -> TreatmentApplication:
        application.plant_key = plant_key
        # The plant first (#1871 B7): the resistance read below looks at the
        # plant's history without a tenant filter, and an over-limit ingredient
        # answered 422 with a count — for a foreign plant, before the repository's
        # 404. Resolved here, a foreign and an unknown plant answer the same.
        self._require_own_plant(plant_key, application.tenant_key)

        # Resistance check
        treatment = self.get_treatment(application.treatment_key)
        if treatment.active_ingredient:
            recent = self._repo.get_recent_applications(plant_key)
            is_safe, warning = self._resistance.validate_treatment(
                recent,
                treatment.active_ingredient,
            )
            if not is_safe:
                raise ResistanceWarningError(
                    treatment.active_ingredient,
                    len([r for r in recent if r.get("active_ingredient") == treatment.active_ingredient]),
                )

        return self._repo.create_treatment_application(application)

    def get_applications(
        self,
        plant_key: str,
        offset: int = 0,
        limit: int = 50,
        *,
        tenant_key: str,
    ) -> tuple[list[TreatmentApplication], int]:
        self._require_own_plant(plant_key, tenant_key)
        return self._repo.get_applications_for_plant(plant_key, offset, limit)

    # ── Karenz-Gate API ──

    def check_harvest_safety(
        self,
        plant_key: str,
        planned_date: datetime | None = None,
        *,
        tenant_key: str,
    ) -> tuple[bool, list[dict]]:
        """Check if harvest is safe for a plant (Karenz-Gate).

        A foreign plant now raises rather than answering ``(True, [])``: an
        unscoped Karenz check is not merely a leak of the other tenant's active
        ingredient, it is also a gate that says *yes* about a plant whose
        treatment history the caller cannot see.
        """
        self._require_own_plant(plant_key, tenant_key)
        karenz_periods = self._repo.get_active_karenz_periods(plant_key)
        if not karenz_periods:
            return True, []
        if planned_date is None:
            planned_date = now_utc()
        return self._safety.can_harvest(karenz_periods, planned_date)

    def get_karenz_periods(self, plant_key: str, *, tenant_key: str) -> list[dict]:
        self._require_own_plant(plant_key, tenant_key)
        return self._repo.get_active_karenz_periods(plant_key)

    # ── Recommendations ──

    def get_treatment_recommendations(self, plant_key: str, pest_key: str, *, tenant_key: str) -> list[dict]:
        self._require_own_plant(plant_key, tenant_key)
        treatments = self._repo.get_treatments_for_pest(pest_key)
        recent = self._repo.get_recent_applications(plant_key)
        available = [
            {"name": t.name, "treatment_type": t.treatment_type, "active_ingredient": t.active_ingredient, "key": t.key}
            for t in treatments
        ]
        return self._resistance.suggest_alternatives(recent, available)

    # ── Inspection Schedule ──

    def get_inspection_schedule(
        self,
        plant_key: str,
        current_phase: str,
        pressure_level: str,
        *,
        tenant_key: str,
    ) -> dict:
        self._require_own_plant(plant_key, tenant_key)
        inspections, _ = self._repo.get_inspections_for_plant(plant_key, 0, 1)
        last_at = inspections[0].inspected_at if inspections else None
        next_date = self._scheduler.next_inspection_date(last_at, current_phase, pressure_level)
        urgency = self._scheduler.calculate_urgency(next_date)
        return {
            "next_inspection": next_date.isoformat(),
            "last_inspection": last_at.isoformat() if last_at else None,
            **urgency,
        }
