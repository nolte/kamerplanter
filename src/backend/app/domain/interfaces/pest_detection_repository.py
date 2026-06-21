"""REQ-044 §5 — repository contract for pest detections + beneficials."""

from abc import ABC, abstractmethod

from app.domain.models.beneficial import Beneficial
from app.domain.models.pest_detection import PestDetection, PestFeedback


class IPestDetectionRepository(ABC):
    @abstractmethod
    def create(self, detection: PestDetection) -> PestDetection: ...

    @abstractmethod
    def get(self, key: str, tenant_key: str) -> PestDetection | None: ...

    @abstractmethod
    def list_for_plant(
        self,
        tenant_key: str,
        plant_instance_key: str,
        limit: int = 20,
    ) -> list[PestDetection]: ...

    @abstractmethod
    def add_feedback(self, key: str, tenant_key: str, feedback: PestFeedback) -> PestDetection | None: ...

    @abstractmethod
    def link_suggested_inspection(self, detection_key: str, inspection_key: str) -> None: ...

    # ── WP-8 beneficials reference data ──
    @abstractmethod
    def get_beneficial_by_slug(self, slug: str) -> Beneficial | None: ...

    @abstractmethod
    def upsert_beneficial(self, beneficial: Beneficial) -> Beneficial: ...
