from abc import ABC, abstractmethod

from app.common.types import OverwinteringProfileKey
from app.domain.models.overwintering_profile import OverwinteringProfile


class IOverwinteringProfileRepository(ABC):
    """REQ-022 §OverwinteringProfile — persistence contract (G-002)."""

    @abstractmethod
    def get_profile_by_key(self, key: OverwinteringProfileKey) -> OverwinteringProfile | None: ...

    @abstractmethod
    def get_profile_by_plant_key(self, plant_key: str) -> OverwinteringProfile | None: ...

    @abstractmethod
    def get_profile_by_run_key(self, run_key: str) -> OverwinteringProfile | None: ...

    @abstractmethod
    def create_profile(self, profile: OverwinteringProfile) -> OverwinteringProfile: ...

    @abstractmethod
    def update_profile(self, key: OverwinteringProfileKey, profile: OverwinteringProfile) -> OverwinteringProfile: ...

    @abstractmethod
    def delete_profile(self, key: OverwinteringProfileKey) -> bool: ...

    @abstractmethod
    def list_by_tenant(
        self, tenant_key: str, offset: int = 0, limit: int = 50
    ) -> tuple[list[OverwinteringProfile], int]: ...

    @abstractmethod
    def create_subject_edge(
        self,
        profile_key: str,
        *,
        plant_key: str | None = None,
        planting_run_key: str | None = None,
    ) -> None: ...

    @abstractmethod
    def create_winter_quarter_edge(self, profile_key: str, location_key: str) -> None: ...
