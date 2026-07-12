"""REQ-044 §5 — ArangoDB repository for pest detections + beneficials."""

from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.pest_detection_repository import IPestDetectionRepository
from app.domain.models.beneficial import Beneficial
from app.domain.models.pest_detection import PestDetection, PestFeedback


class ArangoPestDetectionRepository(BaseArangoRepository[PestDetection], IPestDetectionRepository):
    _model_cls = PestDetection

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.PEST_DETECTIONS)
        self._beneficials = BaseArangoRepository[Beneficial](db, col.BENEFICIALS, Beneficial)

    def create(self, detection: PestDetection) -> PestDetection:
        # #517 — the plant instance / planting run are caller-supplied foreign
        # references; verify existence + tenant ownership before persisting the
        # detection and its support edge (fail-closed 404, no cross-tenant oracle).
        if detection.plant_instance_key:
            self.verify_entity_ownership(
                col.PLANT_INSTANCES, detection.plant_instance_key, detection.tenant_key, entity_name="PlantInstance"
            )
        elif detection.planting_run_key:
            self.verify_entity_ownership(
                col.PLANTING_RUNS, detection.planting_run_key, detection.tenant_key, entity_name="PlantingRun"
            )

        created = super().create(detection)

        # §5.2 — dual-support edge to the plant instance or planting run.
        det_id = f"{col.PEST_DETECTIONS}/{created.key}"
        if detection.plant_instance_key:
            self.create_edge(col.PEST_DETECTION_OF, det_id, f"{col.PLANT_INSTANCES}/{detection.plant_instance_key}")
        elif detection.planting_run_key:
            self.create_edge(col.PEST_DETECTION_OF, det_id, f"{col.PLANTING_RUNS}/{detection.planting_run_key}")

        # §5.2 — flag edge per finding mapped against REQ-010 pests stammdaten.
        for finding in detection.findings:
            if finding.matched_pest_key:
                self.create_edge(
                    col.PEST_DETECTION_FLAGGED,
                    det_id,
                    f"{col.PESTS}/{finding.matched_pest_key}",
                    data={
                        "confidence": finding.confidence,
                        "mode": finding.mode.value,
                        "confirmed": False,
                    },
                )
        return created

    def get(self, key: str, tenant_key: str) -> PestDetection | None:
        detection = super().get_by_key(key)
        if detection is None or detection.tenant_key != tenant_key:
            return None
        return detection

    def list_for_plant(
        self,
        tenant_key: str,
        plant_instance_key: str,
        limit: int = 20,
    ) -> list[PestDetection]:
        return self.find_by_field(
            "tenant_key",
            tenant_key,
            sort="created_at",
            sort_direction="DESC",
            offset=0,
            limit=limit,
            extra_filters=[("plant_instance_key", "==", plant_instance_key)],
        )

    def add_feedback(self, key: str, tenant_key: str, feedback: PestFeedback) -> PestDetection | None:
        detection = self.get(key, tenant_key)
        if detection is None:
            return None
        detection.feedback.append(feedback)
        # Mirror confirmation onto the matching flag edge (HITL → calibration).
        if feedback.confirmed:
            det_id = f"{col.PEST_DETECTIONS}/{key}"
            update = (
                f"FOR e IN {col.PEST_DETECTION_FLAGGED} FILTER e._from == @from "
                f"UPDATE e WITH {{confirmed: true}} IN {col.PEST_DETECTION_FLAGGED}"
            )
            self._db.aql.execute(update, bind_vars={"from": det_id})
        feedback_docs = [f.model_dump(mode="json") for f in detection.feedback]
        self.collection.update({"_key": key, "feedback": feedback_docs, "updated_at": self._now()})
        return self.get(key, tenant_key)

    def link_suggested_inspection(self, detection_key: str, inspection_key: str) -> None:
        self.create_edge(
            col.PEST_DETECTION_SUGGESTED_INSPECTION,
            f"{col.PEST_DETECTIONS}/{detection_key}",
            f"{col.INSPECTIONS}/{inspection_key}",
        )

    # ── WP-8 beneficials ──

    def get_beneficial_by_slug(self, slug: str) -> Beneficial | None:
        return self._beneficials.find_one_by_field("slug", slug)

    def upsert_beneficial(self, beneficial: Beneficial) -> Beneficial:
        existing = self.get_beneficial_by_slug(beneficial.slug)
        coll = self._db.collection(col.BENEFICIALS)
        data = beneficial.model_dump(by_alias=True, exclude_none=True, mode="json")
        data.pop("_key", None)
        if existing is not None:
            data["updated_at"] = self._now()
            result = coll.update({"_key": existing.key, **data}, return_new=True)
        else:
            data["created_at"] = self._now()
            data["updated_at"] = self._now()
            result = coll.insert(data, return_new=True)
        return Beneficial(**self._from_doc(result["new"]))
