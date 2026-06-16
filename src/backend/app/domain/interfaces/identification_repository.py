"""REQ-029 §2 — repository interface for identification requests."""

from abc import ABC, abstractmethod

from app.domain.models.identification import IdentificationRequest


class IIdentificationRepository(ABC):
    @abstractmethod
    def create(self, request: IdentificationRequest) -> IdentificationRequest: ...

    @abstractmethod
    def get(self, key: str, tenant_key: str) -> IdentificationRequest | None: ...

    @abstractmethod
    def set_selected_rank(self, key: str, tenant_key: str, selected_rank: int) -> IdentificationRequest | None: ...

    @abstractmethod
    def list_for_user(
        self,
        tenant_key: str,
        user_key: str,
        limit: int = 20,
    ) -> list[IdentificationRequest]: ...
