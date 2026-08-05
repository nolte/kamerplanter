"""In-memory doubles for the REQ-013 / REQ-050 diary API tests.

The diary repository double stores **dicts**, not models, for one reason that
matters to the acceptance criteria: an entry written before REQ-050 carries no
``analysis_state`` attribute at all, and a model-based double could not express
that state — it would materialise the field default and quietly make AK-26
untestable. Filtering goes through the production
:func:`analysis_state_bind_values`, so the double cannot silently disagree with
the real AQL about whether a missing attribute counts as ``none``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.common.datetimes import ensure_aware_utc
from app.common.enums import AttachmentCategory, DiaryAnalysisState, DiaryEntryType
from app.common.exceptions import (
    DiaryAnalysisConcurrentUpdateError,
    NotFoundError,
)
from app.data_access.arango.plant_diary_repository import (
    analysis_state_bind_values,
    stored_states_for_display,
)
from app.domain.interfaces.plant_diary_repository import DiaryOverviewFilter
from app.domain.models.attachment import Attachment
from app.domain.models.plant_diary_entry import PlantDiaryEntry
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.species import Species


def _as_datetime(value: Any) -> datetime | None:
    """Read a stored timestamp the way both AQL and the domain model read it."""
    return ensure_aware_utc(value)


class FakeDiaryRepository:
    """In-memory ``IPlantDiaryRepository`` with a revision counter and CAS."""

    def __init__(self, plants: dict[str, PlantInstance] | None = None) -> None:
        self.docs: dict[str, dict[str, Any]] = {}
        #: Stand-in for the ``plant_instances`` collection the ``species_key``
        #: filter joins against — the real query resolves it in AQL.
        self.plants: dict[str, PlantInstance] = plants or {}
        #: Stand-in for the ``run_contains`` edges: run key → plant keys. Only
        #: :meth:`get_by_run` needs it; the real query walks the edge collection.
        self.run_plants: dict[str, list[str]] = {}
        self._rev_counter = 0
        self._key_counter = 0

    # ── test helpers ────────────────────────────────────────────────────
    def seed(self, key: str, **fields: Any) -> dict[str, Any]:
        doc: dict[str, Any] = {
            "_key": key,
            "tenant_key": "tenant-a",
            "plant_key": "plant-1",
            "entry_type": "problem",
            "title": "Braune Flecken unten",
            "text": "Seit dem Umtopfen hängen die unteren Blätter.",
            "photo_refs": [],
            "tags": [],
            "created_by": "user-author",
            "created_at": "2026-08-03T18:22:11+00:00",
            "updated_at": "2026-08-03T18:22:11+00:00",
            "analysis_state": DiaryAnalysisState.NONE.value,
        }
        doc.update(fields)
        doc["_rev"] = self._next_rev()
        self.docs[key] = doc
        return doc

    def _next_rev(self) -> str:
        self._rev_counter += 1
        return f"rev-{self._rev_counter}"

    # ── CRUD ────────────────────────────────────────────────────────────
    def create(self, entry: PlantDiaryEntry) -> PlantDiaryEntry:
        self._key_counter += 1
        key = entry.key or f"entry-{self._key_counter}"
        doc = entry.model_dump(by_alias=True, mode="json")
        doc["_key"] = key
        doc["_rev"] = self._next_rev()
        self.docs[key] = doc
        return PlantDiaryEntry(**dict(doc))

    def get_by_key(self, key: str) -> PlantDiaryEntry | None:
        doc = self.docs.get(key)
        return PlantDiaryEntry(**dict(doc)) if doc else None

    def get_or_raise(self, key: str) -> PlantDiaryEntry:
        entry = self.get_by_key(key)
        if entry is None:
            raise NotFoundError("PlantDiaryEntry", key)
        return entry

    def update(self, key: str, entry: PlantDiaryEntry) -> PlantDiaryEntry:
        doc = self.docs.get(key)
        if doc is None:
            raise NotFoundError("PlantDiaryEntry", key)
        doc.update(entry.model_dump(by_alias=True, mode="json", exclude_none=True))
        doc["_key"] = key
        doc["_rev"] = self._next_rev()
        return PlantDiaryEntry(**dict(doc))

    def update_fields(self, key: str, fields: dict[str, Any]) -> PlantDiaryEntry:
        doc = self.docs[key]
        doc.update(fields)
        doc["_rev"] = self._next_rev()
        return PlantDiaryEntry(**dict(doc))

    def delete(self, key: str) -> bool:
        return self.docs.pop(key, None) is not None

    def get_by_plant(
        self,
        plant_key: str,
        *,
        tenant_key: str,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[PlantDiaryEntry], int]:
        """Mirror of the production read, tenant predicate included (SEC-002).

        The double used to select on ``plant_key`` alone, exactly like the AQL it
        stands in for — which is why it reproduced the cross-tenant leak faithfully
        instead of hiding it. It now mirrors the fixed query, including the refusal
        of the empty ``tenant_key`` sentinel: a double that quietly accepted it
        would let a caller-side regression pass here and fail only in production.
        """
        self._require_tenant_key(tenant_key, "get_by_plant")
        matches = [
            doc
            for doc in self.docs.values()
            if doc.get("plant_key") == plant_key and doc.get("tenant_key") == tenant_key
        ]
        matches.sort(key=lambda doc: doc.get("created_at") or "", reverse=True)
        page = matches[offset : offset + limit]
        return [PlantDiaryEntry(**dict(doc)) for doc in page], len(matches)

    @staticmethod
    def _require_tenant_key(tenant_key: str, method: str) -> None:
        """The production guard from ``BaseArangoRepository``, verbatim in effect."""
        if not tenant_key:
            raise ValueError(
                f"{method} is tenant-scoped and requires a non-empty tenant_key (SEC-B4 tenant isolation)."
            )

    def get_by_run(
        self,
        run_key: str,
        *,
        tenant_key: str,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[dict], int]:
        """Rows of the run-wide aggregation, in the shape the router receives.

        The production query returns raw dicts, but not *arbitrary* ones: it
        validates every entry through ``PlantDiaryEntry`` and dumps it by alias
        before handing it out (``plant_diary_repository.get_by_run``). The
        double does the same, because the router now parses that dict back into
        the model — a double that shipped a hand-made dict instead would test a
        shape production never produces.
        """
        self._require_tenant_key(tenant_key, "get_by_run")
        plant_keys = self.run_plants.get(run_key, [])
        matches = [
            doc
            for doc in self.docs.values()
            if doc.get("plant_key") in plant_keys and doc.get("tenant_key") == tenant_key
        ]
        matches.sort(key=lambda doc: doc.get("created_at") or "", reverse=True)
        rows: list[dict] = []
        for doc in matches[offset : offset + limit]:
            plant = self.plants.get(doc.get("plant_key") or "")
            rows.append(
                {
                    "plant_key": doc.get("plant_key"),
                    "plant_id": plant.instance_id if plant else "",
                    "plant_name": plant.plant_name if plant else None,
                    "diary_entry": PlantDiaryEntry(**dict(doc)).model_dump(by_alias=True, mode="json"),
                }
            )
        return rows, len(matches)

    # ── REQ-050 analysis ────────────────────────────────────────────────
    def get_with_revision(self, key: str) -> tuple[PlantDiaryEntry, str] | None:
        doc = self.docs.get(key)
        if doc is None:
            return None
        return PlantDiaryEntry(**dict(doc)), str(doc["_rev"])

    def update_fields_checked(
        self, key: str, fields: dict[str, Any], *, expected_rev: str
    ) -> tuple[PlantDiaryEntry, str]:
        doc = self.docs.get(key)
        if doc is None:
            raise NotFoundError("PlantDiaryEntry", key)
        if doc["_rev"] != expected_rev:
            raise DiaryAnalysisConcurrentUpdateError(key)
        doc.update(fields)  # keep_none: an explicit None is written
        doc["_rev"] = self._next_rev()
        return PlantDiaryEntry(**dict(doc)), str(doc["_rev"])

    def list_pending_analyses(self, tenant_key, *, limit=20, include_stale=True, now=None):
        raise NotImplementedError

    def list_overview(
        self,
        tenant_key: str,
        filters: DiaryOverviewFilter | None = None,
        *,
        offset: int = 0,
        limit: int = 50,
        now: datetime | None = None,
    ) -> tuple[list[PlantDiaryEntry], int]:
        """Mirror of the production overview query, clause for clause.

        The double is deliberately kept close to the AQL it stands in for: the
        state widening goes through the production
        :func:`stored_states_for_display` / :func:`analysis_state_bind_values`, the
        date range compares instants rather than strings, and the free-text search
        is anchored on the same two attributes. Where a double cannot help — that
        the *real* query uses the index and counts the whole set — the
        ArangoDB-backed tests in ``tests/integration/test_diary_overview_query.py``
        take over.
        """
        spec = filters or DiaryOverviewFilter()
        moment = now or datetime.now(UTC)
        matches = [
            doc
            for doc in self.docs.values()
            if doc.get("tenant_key") == tenant_key and self._overview_matches(doc, spec, moment)
        ]
        matches.sort(key=lambda doc: self._overview_sort_key(doc, spec.sort), reverse=True)
        page = matches[offset : offset + limit]
        return [PlantDiaryEntry(**dict(doc)) for doc in page], len(matches)

    def _overview_matches(self, doc: dict[str, Any], spec: DiaryOverviewFilter, now: datetime) -> bool:
        wanted = [DiaryAnalysisState(state) for state in dict.fromkeys(spec.analysis_states)]
        if wanted and set(wanted) != set(DiaryAnalysisState):
            # ``doc.get`` returns ``None`` for the attribute a pre-REQ-050
            # document simply does not have — the exact value AQL sees, and the
            # one ``analysis_state_bind_values`` exists to match (AK-26).
            stored = doc.get("analysis_state")
            if stored not in analysis_state_bind_values(stored_states_for_display(wanted)):
                return False
            if self._displayed_state(doc, now) not in wanted:
                return False

        if spec.plant_key and doc.get("plant_key") != spec.plant_key:
            return False
        if spec.entry_type and doc.get("entry_type") != DiaryEntryType(spec.entry_type).value:
            return False
        if spec.tag and spec.tag.lower() not in {str(t).lower() for t in doc.get("tags") or []}:
            return False
        if spec.created_from is not None or spec.created_to is not None:
            created = _as_datetime(doc.get("created_at"))
            if created is None:
                return False
            if spec.created_from is not None and created.date() < spec.created_from:
                return False
            if spec.created_to is not None and created.date() > spec.created_to:
                return False
        if spec.search:
            needle = spec.search.lower()
            if needle not in f"{doc.get('title') or ''}\n{doc.get('text') or ''}".lower():
                return False
        if spec.species_key:
            plant = self.plants.get(doc.get("plant_key") or "")
            if plant is None or plant.tenant_key != doc.get("tenant_key"):
                return False
            if plant.species_key != spec.species_key:
                return False
        return True

    @staticmethod
    def _displayed_state(doc: dict[str, Any], now: datetime) -> DiaryAnalysisState:
        """The state a reader sees — an expired lease reads as ``requested``."""
        stored = doc.get("analysis_state")
        if stored == DiaryAnalysisState.IN_PROGRESS.value:
            expires = _as_datetime(doc.get("analysis_lease_expires_at"))
            if expires is None or expires <= now:
                return DiaryAnalysisState.REQUESTED
        return DiaryAnalysisState.NONE if stored is None else DiaryAnalysisState(stored)

    @staticmethod
    def _overview_sort_key(doc: dict[str, Any], sort: str) -> tuple[str, str, str]:
        created = str(doc.get("created_at") or "")
        key = str(doc.get("_key") or "")
        if sort == "analyzed_at":
            analyzed = str((doc.get("analysis") or {}).get("analyzed_at") or "")
            return analyzed, created, key
        return created, created, key


class FakeAttachmentRepository:
    """Tenant-scoped stand-in for the ``attachments`` catalogue (SEC-003).

    Only :meth:`get` is implemented — it is the one lookup
    :meth:`PlantDiaryService._require_attachable_photos` performs, and it is
    tenant-scoped in production (``ArangoAttachmentRepository.get(key,
    tenant_key)`` filters on ``tenant_key``). The double filters too: a fake that
    ignored the tenant would let a cross-tenant regression pass here.
    """

    def __init__(self) -> None:
        self.docs: dict[str, Attachment] = {}

    def add(
        self,
        key: str,
        *,
        tenant_key: str,
        created_by: str,
        category: AttachmentCategory = AttachmentCategory.DIARY,
        mime_type: str = "image/jpeg",
    ) -> Attachment:
        attachment = Attachment(
            _key=key,
            tenant_key=tenant_key,
            mime_type=mime_type,
            byte_size=1024,
            sha256="0" * 64,
            original_filename=f"{key}.jpg",
            created_by=created_by,
            category=category,
            storage_key=f"t/{tenant_key}/{category.value}/2026/08/{key}.jpg",
        )
        self.docs[key] = attachment
        return attachment

    def get(self, key: str, tenant_key: str) -> Attachment | None:
        attachment = self.docs.get(key)
        if attachment is None or attachment.tenant_key != tenant_key:
            return None
        return attachment


class FakePlantInstanceService:
    """Minimal stand-in for the plant lookups the diary routers need."""

    def __init__(
        self,
        plants: dict[str, PlantInstance] | None = None,
        species: dict[str, Species] | None = None,
    ) -> None:
        self.plants = plants or {}
        self.species = species or {}
        self.get_plant_calls = 0

    def get_plant(self, key: str, tenant_key: str = "") -> PlantInstance:
        self.get_plant_calls += 1
        plant = self.plants.get(key)
        if plant is None or (tenant_key and plant.tenant_key != tenant_key):
            # Same answer for "gone" and "someone else's" (AK-12).
            raise NotFoundError("PlantInstance", key)
        return plant

    def resolve_species(self, species_key: str) -> Species | None:
        return self.species.get(species_key)


class FakePlantingRunService:
    """Stand-in that only answers the tenant-scoped run lookup."""

    def __init__(self, runs: dict[str, str] | None = None) -> None:
        #: run key → owning tenant key
        self.runs = runs or {}

    def get_run(self, key: str, tenant_key: str = ""):
        owner = self.runs.get(key)
        if owner is None or (tenant_key and owner != tenant_key):
            raise NotFoundError("PlantingRun", key)
        return {"_key": key, "tenant_key": owner}
