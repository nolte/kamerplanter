"""REQ-038 §5 — ArangoDB repository for CV disease-diagnosis requests.

Tenant-scoped (``is_tenant_scoped=True``): every read is strictly filtered by
``tenant_key`` and single-value reads reject the empty-tenant sentinel
(``_require_tenant_key``, SEC-B4). All AQL is parametrised via ``bind_vars`` —
never f-string interpolation.
"""

from app.common.enums import DiagnosisCategory
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.plant_diagnosis_repository import IPlantDiagnosisRepository
from app.domain.models.plant_diagnosis_request import PlantDiagnosisRequest


class ArangoPlantDiagnosisRepository(BaseArangoRepository[PlantDiagnosisRequest], IPlantDiagnosisRepository):
    """ArangoDB-backed repository for ``plant_diagnosis_requests``."""

    _model_cls = PlantDiagnosisRequest
    is_tenant_scoped = True

    def __init__(self, db) -> None:
        super().__init__(db, col.PLANT_DIAGNOSIS_REQUESTS)

    def create(self, request: PlantDiagnosisRequest) -> PlantDiagnosisRequest:
        # #517 — the plant instance / planting run / harvest observation are all
        # caller-supplied foreign references; verify existence + tenant ownership
        # before persisting the request and its provenance edges (fail-closed
        # 404, no cross-tenant oracle). Matched disease/pest keys reference global
        # REQ-010 stammdaten (not tenant-owned) and are left unguarded here.
        if request.plant_instance_key:
            self.verify_entity_ownership(
                col.PLANT_INSTANCES, request.plant_instance_key, request.tenant_key, entity_name="PlantInstance"
            )
        if request.planting_run_key:
            self.verify_entity_ownership(
                col.PLANTING_RUNS, request.planting_run_key, request.tenant_key, entity_name="PlantingRun"
            )
        if request.harvest_observation_key:
            self.verify_entity_ownership(
                col.HARVEST_OBSERVATIONS,
                request.harvest_observation_key,
                request.tenant_key,
                entity_name="HarvestObservation",
            )

        created = super().create(request)
        req_id = f"{col.PLANT_DIAGNOSIS_REQUESTS}/{created.key}"

        # Bind the request to a plant instance or planting run (dual-support edge).
        if request.plant_instance_key:
            self.create_edge(col.CV_DIAGNOSED_FOR, req_id, f"{col.PLANT_INSTANCES}/{request.plant_instance_key}")
        elif request.planting_run_key:
            self.create_edge(col.CV_DIAGNOSED_FOR, req_id, f"{col.PLANTING_RUNS}/{request.planting_run_key}")

        # One found-edge per mapped class against REQ-010 diseases / pests.
        # Deficiencies stay null (no stammdaten) and produce no edge (§ REQ-036).
        for rank, classification in enumerate(request.classifications, start=1):
            if classification.matched_disease_key:
                self.create_edge(
                    col.CV_DIAGNOSIS_FOUND,
                    req_id,
                    f"{col.DISEASES}/{classification.matched_disease_key}",
                    data={
                        "confidence": classification.probability,
                        "rank": rank,
                        "category": DiagnosisCategory.DISEASE.value,
                        "confirmed": False,
                    },
                )
            elif classification.matched_pest_key:
                self.create_edge(
                    col.CV_DIAGNOSIS_FOUND,
                    req_id,
                    f"{col.PESTS}/{classification.matched_pest_key}",
                    data={
                        "confidence": classification.probability,
                        "rank": rank,
                        "category": DiagnosisCategory.PEST.value,
                        "confirmed": False,
                    },
                )

        # Bridge the phenotype to a harvest observation (REQ-007 time series).
        if request.phenotype is not None and request.harvest_observation_key:
            self.create_edge(
                col.CV_PHENOTYPE_OF,
                req_id,
                f"{col.HARVEST_OBSERVATIONS}/{request.harvest_observation_key}",
            )
        return created

    def get(self, key: str, tenant_key: str) -> PlantDiagnosisRequest | None:
        self._require_tenant_key(tenant_key, "get")
        request = super().get_by_key(key)
        if request is None or request.tenant_key != tenant_key:
            return None
        return request

    def list_for_user(self, tenant_key: str, user_key: str, limit: int = 20) -> list[PlantDiagnosisRequest]:
        self._require_tenant_key(tenant_key, "list_for_user")
        query = """
        FOR req IN @@collection
          FILTER req.tenant_key == @tenant_key AND req.user_key == @user_key
          SORT req.created_at DESC
          LIMIT @limit
          RETURN req
        """
        bind_vars = {
            "@collection": self._collection_name,
            "tenant_key": tenant_key,
            "user_key": user_key,
            "limit": limit,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [PlantDiagnosisRequest(**self._from_doc(doc)) for doc in cursor]

    def mark_confirmed(
        self,
        key: str,
        tenant_key: str,
        *,
        confirmed_labels: list[str],
        inspection_key: str | None = None,
    ) -> PlantDiagnosisRequest | None:
        self._require_tenant_key(tenant_key, "mark_confirmed")
        query = """
        FOR req IN @@collection
          FILTER req._key == @key AND req.tenant_key == @tenant_key
          UPDATE req WITH {
            confirmed_labels: @confirmed_labels,
            inspection_key: @inspection_key,
            updated_at: @now
          } IN @@collection
          RETURN NEW
        """
        bind_vars = {
            "@collection": self._collection_name,
            "key": key,
            "tenant_key": tenant_key,
            "confirmed_labels": confirmed_labels,
            "inspection_key": inspection_key,
            "now": self._now(),
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        updated = next(cursor, None)
        if updated is None:
            return None
        # Mark the matching found-edges confirmed (HITL → future calibration).
        if inspection_key:
            self.create_edge(
                col.CV_ATTACHED_TO_INSPECTION,
                f"{col.PLANT_DIAGNOSIS_REQUESTS}/{key}",
                f"{col.INSPECTIONS}/{inspection_key}",
            )
        return PlantDiagnosisRequest(**self._from_doc(updated))
