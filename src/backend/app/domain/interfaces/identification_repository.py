"""REQ-029 — Repository interface for identification/diagnosis requests."""

from abc import ABC, abstractmethod
from typing import Any

from app.domain.models.identification import DiagnosisRequest, IdentificationRequest


class IIdentificationRepository(ABC):
    """Persistence contract for identification and diagnosis requests.

    Image bytes are never persisted — only hashes, results and metadata.
    """

    @abstractmethod
    def create(self, request: IdentificationRequest) -> IdentificationRequest: ...

    @abstractmethod
    def create_diagnosis(self, request: DiagnosisRequest) -> DiagnosisRequest: ...

    @abstractmethod
    def get(self, key: str, tenant_key: str) -> IdentificationRequest | None: ...

    @abstractmethod
    def update_selected_rank(self, key: str, tenant_key: str, selected_rank: int) -> IdentificationRequest | None: ...

    @abstractmethod
    def list_history(self, tenant_key: str, user_key: str, limit: int) -> list[dict[str, Any]]: ...
