"""Read access to the soil-hazard knowledge table (REQ-054 §5.2a, #2888 F-18)."""

from abc import ABC, abstractmethod

from app.common.enums import SoilHazard
from app.domain.models.soil_hazard_knowledge import SoilHazardKnowledge, SoilHazardKnowledgeTable


class ISoilHazardKnowledgeSource(ABC):
    """Global, read-only knowledge table; one row per :class:`SoilHazard`."""

    @abstractmethod
    def get_table(self) -> SoilHazardKnowledgeTable: ...

    @abstractmethod
    def get(self, hazard: SoilHazard) -> SoilHazardKnowledge: ...
