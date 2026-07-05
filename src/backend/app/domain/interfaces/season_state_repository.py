"""REQ-047 §2.1 — persistence contract for :class:`SeasonState`."""

from abc import ABC, abstractmethod

from app.domain.models.season_state import SeasonState


class ISeasonStateRepository(ABC):
    """Tenant-scoped persistence of the per-site season state (1:1 per site)."""

    @abstractmethod
    def get_by_site(self, site_key: str, tenant_key: str) -> SeasonState | None: ...

    @abstractmethod
    def upsert(self, state: SeasonState) -> SeasonState: ...

    @abstractmethod
    def list_for_tenant(self, tenant_key: str, offset: int = 0, limit: int = 200) -> tuple[list[SeasonState], int]: ...
