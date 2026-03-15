from abc import ABC, abstractmethod

from app.common.enums import ReminderType
from app.common.types import CareProfileKey
from app.domain.models.care_reminder import CareConfirmation, CareProfile


class ICareReminderRepository(ABC):
    @abstractmethod
    def get_profile_by_key(self, key: CareProfileKey) -> CareProfile | None: ...

    @abstractmethod
    def get_profile_by_plant_key(self, plant_key: str) -> CareProfile | None: ...

    @abstractmethod
    def create_profile(self, profile: CareProfile) -> CareProfile: ...

    @abstractmethod
    def update_profile(self, key: CareProfileKey, profile: CareProfile) -> CareProfile: ...

    @abstractmethod
    def delete_profile(self, key: CareProfileKey) -> bool: ...

    @abstractmethod
    def get_all_profiles(self) -> list[CareProfile]: ...

    @abstractmethod
    def create_confirmation(self, confirmation: CareConfirmation) -> CareConfirmation: ...

    @abstractmethod
    def get_confirmations_by_plant(
        self,
        plant_key: str,
        reminder_type: ReminderType | None = None,
        limit: int = 50,
    ) -> list[CareConfirmation]: ...

    @abstractmethod
    def get_last_confirmation(
        self,
        plant_key: str,
        reminder_type: ReminderType,
    ) -> CareConfirmation | None: ...

    @abstractmethod
    def create_profile_edge(self, plant_key: str, profile_key: str) -> None: ...

    @abstractmethod
    def create_confirmation_edges(
        self,
        confirmation_key: str,
        profile_key: str,
        plant_key: str,
    ) -> None: ...
