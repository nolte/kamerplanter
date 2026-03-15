from abc import ABC, abstractmethod

from app.common.types import (
    DiseaseKey,
    PestKey,
    TreatmentKey,
)
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
