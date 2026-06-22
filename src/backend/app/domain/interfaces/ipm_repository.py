from abc import ABC, abstractmethod

from app.common.types import (
    DiseaseKey,
    PestKey,
    TreatmentKey,
)
from app.domain.models.beneficial import Beneficial
from app.domain.models.ipm import (
    Disease,
    Inspection,
    Pest,
    Treatment,
    TreatmentApplication,
)


class IIpmRepository(ABC):
    # ── Pest CRUD ──
    @abstractmethod
    def get_all_pests(self, offset: int = 0, limit: int = 50) -> tuple[list[Pest], int]: ...

    @abstractmethod
    def get_pest_by_key(self, key: PestKey) -> Pest | None: ...

    @abstractmethod
    def get_pest_by_scientific_name(self, scientific_name: str) -> Pest | None: ...

    @abstractmethod
    def create_pest(self, pest: Pest) -> Pest: ...

    @abstractmethod
    def update_pest(self, key: PestKey, pest: Pest) -> Pest: ...

    @abstractmethod
    def delete_pest(self, key: PestKey) -> bool: ...

    # ── Disease CRUD ──
    @abstractmethod
    def get_all_diseases(self, offset: int = 0, limit: int = 50) -> tuple[list[Disease], int]: ...

    @abstractmethod
    def get_disease_by_key(self, key: DiseaseKey) -> Disease | None: ...

    @abstractmethod
    def create_disease(self, disease: Disease) -> Disease: ...

    @abstractmethod
    def update_disease(self, key: DiseaseKey, disease: Disease) -> Disease: ...

    @abstractmethod
    def delete_disease(self, key: DiseaseKey) -> bool: ...

    # ── Treatment CRUD ──
    @abstractmethod
    def get_all_treatments(self, offset: int = 0, limit: int = 50) -> tuple[list[Treatment], int]: ...

    @abstractmethod
    def get_treatment_by_key(self, key: TreatmentKey) -> Treatment | None: ...

    @abstractmethod
    def create_treatment(self, treatment: Treatment) -> Treatment: ...

    @abstractmethod
    def update_treatment(self, key: TreatmentKey, treatment: Treatment) -> Treatment: ...

    @abstractmethod
    def delete_treatment(self, key: TreatmentKey) -> bool: ...

    # ── Inspection CRUD ──
    @abstractmethod
    def create_inspection(self, inspection: Inspection) -> Inspection: ...

    @abstractmethod
    def get_inspections_for_plant(
        self,
        plant_key: str,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Inspection], int]: ...

    @abstractmethod
    def get_inspection_photo_refs_for_pest(self, tenant_key: str, pest_key: PestKey) -> list[str]:
        """Return the deduplicated photo attachment ids of a tenant's inspections.

        Yields every ``photo_refs`` entry of inspections that belong to
        ``tenant_key`` and that detected ``pest_key`` (``pest_key`` is contained
        in ``detected_pest_keys``). Strict tenant isolation: only the calling
        tenant's inspections are considered. The order is stable, newest
        inspection first; duplicate attachment ids are collapsed.
        """
        ...

    # ── TreatmentApplication CRUD ──
    @abstractmethod
    def create_treatment_application(self, app: TreatmentApplication) -> TreatmentApplication: ...

    @abstractmethod
    def get_applications_for_plant(
        self,
        plant_key: str,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[TreatmentApplication], int]: ...

    # ── Edges ──
    @abstractmethod
    def create_targets_pest_edge(self, treatment_key: TreatmentKey, pest_key: PestKey) -> None: ...

    @abstractmethod
    def create_targets_disease_edge(self, treatment_key: TreatmentKey, disease_key: DiseaseKey) -> None: ...

    @abstractmethod
    def create_contraindicated_edge(self, treatment_a_key: TreatmentKey, treatment_b_key: TreatmentKey) -> None: ...

    # ── Queries ──
    @abstractmethod
    def get_active_karenz_periods(self, plant_key: str) -> list[dict]: ...

    @abstractmethod
    def get_recent_applications(self, plant_key: str, days_window: int = 90) -> list[dict]: ...

    @abstractmethod
    def get_treatments_for_pest(self, pest_key: PestKey) -> list[Treatment]: ...

    @abstractmethod
    def get_beneficials_for_pest_slug(self, slug: str) -> list[Beneficial]: ...

    @abstractmethod
    def get_pests_for_treatment(self, treatment_key: TreatmentKey) -> list[Pest]: ...

    @abstractmethod
    def get_diseases_for_treatment(self, treatment_key: TreatmentKey) -> list[Disease]: ...
