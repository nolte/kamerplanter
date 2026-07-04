from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.overwintering_profile_template_repository import (
    IOverwinteringProfileTemplateRepository,
)
from app.domain.models.overwintering_profile_template import OverwinteringProfileTemplate


class ArangoOverwinteringProfileTemplateRepository(
    BaseArangoRepository[OverwinteringProfileTemplate],
    IOverwinteringProfileTemplateRepository,
):
    """REQ-022 §OverwinteringProfile — species-level *template* repository.

    Templates are global reference data (not tenant-scoped) and are *reusable*: a
    single template is referenced by many plant instances / planting runs through
    the ``uses_overwintering_template`` edge (N subjects → 1 template).
    """

    _model_cls = OverwinteringProfileTemplate
    is_tenant_scoped = False

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.OVERWINTERING_PROFILE_TEMPLATES)

    # ── Reads ──────────────────────────────────────────────────────────

    def get_template_by_key(self, key: str) -> OverwinteringProfileTemplate | None:
        return super().get_by_key(key)

    def get_template_by_species_key(self, species_key: str) -> OverwinteringProfileTemplate | None:
        return self.find_one_by_field("species_key", species_key)

    def get_template_by_scientific_name(self, scientific_name: str) -> OverwinteringProfileTemplate | None:
        return self.find_one_by_field("species_scientific_name", scientific_name)

    # ── Reuse edges (subject → shared template, N:1) ───────────────────

    @staticmethod
    def _subject_id(plant_key: str | None, planting_run_key: str | None) -> str | None:
        if planting_run_key:
            return f"{col.PLANTING_RUNS}/{planting_run_key}"
        if plant_key:
            return f"{col.PLANT_INSTANCES}/{plant_key}"
        return None

    def link_subject(
        self,
        template_key: str,
        *,
        plant_key: str | None = None,
        planting_run_key: str | None = None,
    ) -> None:
        """Point a subject at a shared template (idempotent; re-link replaces).

        The edge ``_key`` is derived deterministically from the subject, so the write
        is a single atomic upsert: re-linking (even concurrently) replaces the one
        edge instead of racing a delete-then-insert against the unique ``_from`` index.
        """
        from_id = self._subject_id(plant_key, planting_run_key)
        if from_id is None:
            return
        edge = {
            "_key": from_id.replace("/", "__"),
            "_from": from_id,
            "_to": f"{col.OVERWINTERING_PROFILE_TEMPLATES}/{template_key}",
            "created_at": self._now(),
        }
        self._db.collection(col.USES_OVERWINTERING_TEMPLATE).insert(edge, overwrite_mode="replace")

    def get_template_for_subject(
        self,
        *,
        plant_key: str | None = None,
        planting_run_key: str | None = None,
    ) -> OverwinteringProfileTemplate | None:
        """Resolve the shared template a subject references, if any."""
        from_id = self._subject_id(plant_key, planting_run_key)
        if from_id is None:
            return None
        edges = self.get_edges(col.USES_OVERWINTERING_TEMPLATE, from_id, direction="outbound")
        if not edges:
            return None
        return self._wrap(edges[0]["vertex"])

    def unlink_subject(
        self,
        *,
        plant_key: str | None = None,
        planting_run_key: str | None = None,
    ) -> int:
        from_id = self._subject_id(plant_key, planting_run_key)
        if from_id is None:
            return 0
        return self.delete_edges(col.USES_OVERWINTERING_TEMPLATE, from_id)

    def count_subjects(self, template_key: str) -> int:
        """How many subjects currently reuse this template (inbound edges)."""
        to_id = f"{col.OVERWINTERING_PROFILE_TEMPLATES}/{template_key}"
        return len(self.get_edges(col.USES_OVERWINTERING_TEMPLATE, to_id, direction="inbound"))

    def list_links_for_tenant(
        self, tenant_key: str
    ) -> list[tuple[str | None, str | None, OverwinteringProfileTemplate]]:
        """All (plant_key, planting_run_key, template) links owned by a tenant.

        Joins each ``uses_overwintering_template`` edge to its subject (to filter
        by tenant) and its template. Used by the winter-hardiness dashboard so
        shared-template subjects appear alongside per-instance profiles.
        """
        query = """
        FOR e IN @@edge
          LET subj = DOCUMENT(e._from)
          FILTER subj != null AND subj.tenant_key == @tenant
          LET tpl = DOCUMENT(e._to)
          FILTER tpl != null
          RETURN {from_id: e._from, template: tpl}
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={"@edge": col.USES_OVERWINTERING_TEMPLATE, "tenant": tenant_key},
        )
        results: list[tuple[str | None, str | None, OverwinteringProfileTemplate]] = []
        for row in cursor:
            from_id: str = row["from_id"]
            collection, _, key = from_id.partition("/")
            plant_key = key if collection == col.PLANT_INSTANCES else None
            planting_run_key = key if collection == col.PLANTING_RUNS else None
            results.append((plant_key, planting_run_key, self._wrap(row["template"])))
        return results
