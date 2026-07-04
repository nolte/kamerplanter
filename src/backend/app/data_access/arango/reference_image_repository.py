"""REQ-029-A §5.2 — ArangoDB persistence for reference-image acquisition jobs.

Stores only the per-species coverage report (counts, license breakdown,
usability flag) — never any image bytes. Jobs are keyed deterministically by
species so re-runs upsert in place (idempotent re-indexing).
"""

from typing import Any

from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.models.reference_image import ReferenceImageJob


def _job_key(species_key: str) -> str:
    return f"refjob_{species_key}"


class ArangoReferenceImageRepository(BaseArangoRepository[ReferenceImageJob]):
    """ArangoDB persistence for reference-image acquisition coverage reports."""

    _model_cls = ReferenceImageJob

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.REFERENCE_IMAGE_JOBS)

    def upsert(self, job: ReferenceImageJob) -> ReferenceImageJob:
        """Insert or replace the coverage report for a species (idempotent)."""
        doc = job.model_dump(by_alias=True, exclude_none=True)
        doc["_key"] = _job_key(job.species_key)
        doc["updated_at"] = self._now()
        if "created_at" not in doc or doc["created_at"] is None:
            doc["created_at"] = self._now()
        self.collection.insert(doc, overwrite=True)
        stored = self.collection.get(doc["_key"])
        return ReferenceImageJob(**stored)

    def get_by_species(self, species_key: str) -> ReferenceImageJob | None:
        doc = self.collection.get(_job_key(species_key))
        return ReferenceImageJob(**doc) if doc else None

    def coverage_report(self) -> list[dict[str, Any]]:
        """Return a compact coverage report across all acquired species."""
        query = """
        FOR job IN @@collection
          SORT job.usable_for_recognition DESC, job.accepted DESC
          RETURN {
            species_key: job.species_key,
            scientific_name: job.scientific_name,
            accepted: job.accepted,
            candidates_found: job.candidates_found,
            usable_for_recognition: job.usable_for_recognition,
            license_breakdown: job.license_breakdown
          }
        """
        cursor = self._db.aql.execute(query, bind_vars={"@collection": col.REFERENCE_IMAGE_JOBS})
        return list(cursor)
