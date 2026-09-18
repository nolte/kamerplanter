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
    def create_linked_profile(self, profile: CareProfile, plant_key: str) -> CareProfile:
        """Store the profile and its ``has_care_profile`` edge in ONE transaction (#1292).

        There is deliberately no way to store a care profile without its edge. The
        pair used to be ``create_profile`` + ``create_profile_edge``, and between the
        two the document was committed and readable while nothing linked it — a
        window in which a concurrent reader answered with a document that was about
        to be deleted again as a lost racer's orphan. Removing the two narrow methods
        from this interface is what makes that shape unspellable rather than merely
        unused.

        Raises :class:`DuplicateError`/:class:`WriteConflictError` when the plant
        already owns an edge; nothing is persisted in that case.

        There is no ``delete_profile`` here either, for the same reason and since
        the same review: deleting the document while the ``has_care_profile`` edge
        survives leaves the plant permanently unable to get a profile — every later
        create hits the unique ``_from`` index and the edge resolves to nothing, so
        the race resolution re-raises for good. Its only caller was the orphan
        cleanup this change removed.
        """
        ...

    @abstractmethod
    def update_profile(self, key: CareProfileKey, profile: CareProfile) -> CareProfile: ...

    @abstractmethod
    def get_all_profiles(self) -> list[CareProfile]: ...

    @abstractmethod
    def count_plants_without_profile(self, *, tenant_key: str | None) -> int:
        """Count non-removed plants with no ``CareProfile`` (#1444).

        ``None`` counts the whole installation; the empty string is refused, never
        read as "all tenants".
        """
        ...

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
    def get_linked_profile(self, plant_key: str) -> CareProfile | None: ...

    @abstractmethod
    def create_confirmation_edges(
        self,
        confirmation_key: str,
        profile_key: str,
        plant_key: str,
    ) -> None: ...
