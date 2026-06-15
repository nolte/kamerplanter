"""REQ-029 — ArangoDB persistence for identification/diagnosis requests."""

from typing import Any

from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.identification_repository import IIdentificationRepository
from app.domain.models.identification import DiagnosisRequest, IdentificationRequest


class ArangoIdentificationRepository(IIdentificationRepository, BaseArangoRepository):
    """ArangoDB persistence for REQ-029 identification requests.

    No image bytes are stored — only the image hash, enriched results and
    metadata. Diagnosis requests live in a separate collection.
    """

    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.IDENTIFICATION_REQUESTS)
        self._diagnosis_col = db.collection(col.DIAGNOSIS_REQUESTS)

    def create(self, request: IdentificationRequest) -> IdentificationRequest:
        doc = BaseArangoRepository.create(self, request)
        return IdentificationRequest(**doc)

    def create_diagnosis(self, request: DiagnosisRequest) -> DiagnosisRequest:
        repo = BaseArangoRepository(self._db, col.DIAGNOSIS_REQUESTS)
        doc = repo.create(request)
        return DiagnosisRequest(**doc)

    def get(self, key: str, tenant_key: str) -> IdentificationRequest | None:
        doc = BaseArangoRepository.get_by_key(self, key)
        if doc is None or doc.get("tenant_key") != tenant_key:
            return None
        return IdentificationRequest(**doc)

    def update_selected_rank(
        self,
        key: str,
        tenant_key: str,
        selected_rank: int,
    ) -> IdentificationRequest | None:
        existing = self.get(key, tenant_key)
        if existing is None:
            return None
        self.collection.update({"_key": key, "selected_result_rank": selected_rank, "updated_at": self._now()})
        updated = BaseArangoRepository.get_by_key(self, key)
        return IdentificationRequest(**updated) if updated else None

    def list_history(self, tenant_key: str, user_key: str, limit: int) -> list[dict[str, Any]]:
        query = """
        FOR req IN @@collection
          FILTER req.tenant_key == @tenant_key AND req.user_key == @user_key
          SORT req.created_at DESC
          LIMIT @limit
          RETURN {
            request_key: req._key,
            created_at: req.created_at,
            adapter_key: req.adapter_key,
            request_type: req.request_type,
            image_organ: req.image_organ,
            status: req.status,
            results: req.results,
            selected_result_rank: req.selected_result_rank
          }
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.IDENTIFICATION_REQUESTS,
                "tenant_key": tenant_key,
                "user_key": user_key,
                "limit": limit,
            },
        )
        return list(cursor)
