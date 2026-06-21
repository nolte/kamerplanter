"""REQ-044 §5 — ArangoDB repository for pest detections + beneficials."""

from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.pest_detection_repository import IPestDetectionRepository
from app.domain.models.beneficial import Beneficial
from app.domain.models.pest_detection import PestDetection, PestFeedback


class ArangoPestDetectionRepository(IPestDetectionRepository, BaseArangoRepository):
    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.PEST_DETECTIONS)

    def create(self, detection: PestDetection) -> PestDetection:
        doc = BaseArangoRepository.create(self, detection)
        created = PestDetection(**doc)

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
        doc = BaseArangoRepository.get_by_key(self, key)
        if doc is None or doc.get("tenant_key") != tenant_key:
            return None
        return PestDetection(**doc)

    def list_for_plant(
        self,
        tenant_key: str,
        plant_instance_key: str,
        limit: int = 20,
    ) -> list[PestDetection]:
        query = f"""
        FOR d IN {col.PEST_DETECTIONS}
          FILTER d.tenant_key == @tenant_key AND d.plant_instance_key == @plant_key
          SORT d.created_at DESC
          LIMIT @limit
          RETURN d
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={"tenant_key": tenant_key, "plant_key": plant_instance_key, "limit": limit},
        )
        return [PestDetection(**self._from_doc(doc)) for doc in cursor]

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
        query = f"FOR b IN {col.BENEFICIALS} FILTER b.slug == @slug LIMIT 1 RETURN b"
        cursor = self._db.aql.execute(query, bind_vars={"slug": slug})
        doc = next(cursor, None)
        return Beneficial(**self._from_doc(doc)) if doc else None

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
