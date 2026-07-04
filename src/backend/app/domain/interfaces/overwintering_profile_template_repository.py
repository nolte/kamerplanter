from abc import ABC, abstractmethod

from app.domain.models.overwintering_profile_template import OverwinteringProfileTemplate


class IOverwinteringProfileTemplateRepository(ABC):
    """REQ-022 §OverwinteringProfile — species-level *template* persistence contract.

    Templates are reusable: many subjects (plant instances / planting runs) may
    reference the same template through the ``uses_overwintering_template`` edge.
    """

    @abstractmethod
    def get_template_by_key(self, key: str) -> OverwinteringProfileTemplate | None: ...

    @abstractmethod
    def get_template_by_species_key(self, species_key: str) -> OverwinteringProfileTemplate | None: ...

    @abstractmethod
    def get_template_by_scientific_name(self, scientific_name: str) -> OverwinteringProfileTemplate | None: ...

    @abstractmethod
    def link_subject(
        self,
        template_key: str,
        *,
        plant_key: str | None = None,
        planting_run_key: str | None = None,
    ) -> None: ...

    @abstractmethod
    def get_template_for_subject(
        self,
        *,
        plant_key: str | None = None,
        planting_run_key: str | None = None,
    ) -> OverwinteringProfileTemplate | None: ...

    @abstractmethod
    def unlink_subject(
        self,
        *,
        plant_key: str | None = None,
        planting_run_key: str | None = None,
    ) -> int: ...

    @abstractmethod
    def count_subjects(self, template_key: str) -> int: ...

    @abstractmethod
    def list_links_for_tenant(
        self, tenant_key: str
    ) -> list[tuple[str | None, str | None, OverwinteringProfileTemplate]]: ...
