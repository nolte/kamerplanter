"""REQ-038 §5 — contract for CV disease-diagnosis persistence."""

from abc import ABC, abstractmethod

from app.domain.models.plant_diagnosis_request import PlantDiagnosisRequest


class IPlantDiagnosisRepository(ABC):
    """Tenant-scoped persistence for ``plant_diagnosis_requests``."""

    @abstractmethod
    def create(self, request: PlantDiagnosisRequest) -> PlantDiagnosisRequest:
        """Insert a diagnosis request and wire its provenance edges."""

    @abstractmethod
    def get(self, key: str, tenant_key: str) -> PlantDiagnosisRequest | None:
        """Fetch one request, strictly filtered by ``tenant_key`` (no oracle)."""

    @abstractmethod
    def list_for_user(self, tenant_key: str, user_key: str, limit: int = 20) -> list[PlantDiagnosisRequest]:
        """List the user's recent diagnosis requests (tenant + user filtered)."""

    @abstractmethod
    def mark_confirmed(
        self,
        key: str,
        tenant_key: str,
        *,
        confirmed_labels: list[str],
        inspection_key: str | None = None,
    ) -> PlantDiagnosisRequest | None:
        """Record the confirmed classes and (optionally) link the IPM inspection."""
