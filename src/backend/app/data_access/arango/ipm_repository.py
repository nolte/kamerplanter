from datetime import UTC, datetime, timedelta

from arango.database import StandardDatabase

from app.common.types import DiseaseKey, PestKey, TreatmentKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.ipm_repository import IIpmRepository
from app.domain.models.beneficial import Beneficial
from app.domain.models.ipm import (
    Disease,
    Inspection,
    Pest,
    Treatment,
    TreatmentApplication,
)


class ArangoIpmRepository(BaseArangoRepository[Pest], IIpmRepository):
    _model_cls = Pest

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.PESTS)
        self._diseases = BaseArangoRepository[Disease](db, col.DISEASES, Disease)
        self._treatments = BaseArangoRepository[Treatment](db, col.TREATMENTS, Treatment)
        self._inspections = BaseArangoRepository[Inspection](db, col.INSPECTIONS, Inspection)
        self._applications = BaseArangoRepository[TreatmentApplication](
            db, col.TREATMENT_APPLICATIONS, TreatmentApplication
        )

    # ── Pest CRUD ──

    def get_all_pests(self, offset: int = 0, limit: int = 50) -> tuple[list[Pest], int]:
        return super().get_all(offset, limit)

    def get_pest_by_key(self, key: PestKey) -> Pest | None:
        return super().get_by_key(key)

    def get_pest_by_scientific_name(self, scientific_name: str) -> Pest | None:
        return self.find_one_by_field("scientific_name", scientific_name)

    def create_pest(self, pest: Pest) -> Pest:
        return super().create(pest)

    def update_pest(self, key: PestKey, pest: Pest) -> Pest:
        return super().update(key, pest)

    def delete_pest(self, key: PestKey) -> bool:
        pest_id = f"{col.PESTS}/{key}"
        for edge_col in [col.TARGETS_PEST, col.DETECTED_PEST]:
            self.delete_edges(edge_col, pest_id, direction="inbound")
        return super().delete(key)

    # ── Disease CRUD ──

    def get_all_diseases(self, offset: int = 0, limit: int = 50) -> tuple[list[Disease], int]:
        return self._diseases.get_all(offset, limit)

    def get_disease_by_key(self, key: DiseaseKey) -> Disease | None:
        return self._diseases.get_by_key(key)

    def create_disease(self, disease: Disease) -> Disease:
        return self._diseases.create(disease)

    def update_disease(self, key: DiseaseKey, disease: Disease) -> Disease:
        return self._diseases.update(key, disease)

    def delete_disease(self, key: DiseaseKey) -> bool:
        disease_id = f"{col.DISEASES}/{key}"
        for edge_col in [col.TARGETS_DISEASE, col.DETECTED_DISEASE]:
            self.delete_edges(edge_col, disease_id, direction="inbound")
        return self._diseases.delete(key)

    # ── Treatment CRUD ──

    def get_all_treatments(self, offset: int = 0, limit: int = 50) -> tuple[list[Treatment], int]:
        return self._treatments.get_all(offset, limit)

    def get_treatment_by_key(self, key: TreatmentKey) -> Treatment | None:
        return self._treatments.get_by_key(key)

    def create_treatment(self, treatment: Treatment) -> Treatment:
        return self._treatments.create(treatment)

    def update_treatment(self, key: TreatmentKey, treatment: Treatment) -> Treatment:
        return self._treatments.update(key, treatment)

    def delete_treatment(self, key: TreatmentKey) -> bool:
        treatment_id = f"{col.TREATMENTS}/{key}"
        for edge_col in [col.TARGETS_PEST, col.TARGETS_DISEASE, col.CONTRAINDICATED_WITH, col.TREATMENT_USES]:
            self.delete_edges(edge_col, treatment_id, direction="any")
        return self._treatments.delete(key)

    # ── Inspection ──

    def create_inspection(self, inspection: Inspection) -> Inspection:
        insp = self._inspections.create(inspection, default_now_fields=("inspected_at",))

        # Create edges
        plant_id = f"{col.PLANT_INSTANCES}/{inspection.plant_key}"
        insp_id = f"{col.INSPECTIONS}/{insp.key}"
        self.create_edge(col.INSPECTED_BY, plant_id, insp_id)

        for pest_key in inspection.detected_pest_keys:
            self.create_edge(col.DETECTED_PEST, insp_id, f"{col.PESTS}/{pest_key}")

        for disease_key in inspection.detected_disease_keys:
            self.create_edge(col.DETECTED_DISEASE, insp_id, f"{col.DISEASES}/{disease_key}")

        return insp

    def get_inspections_for_plant(
        self,
        plant_key: str,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Inspection], int]:
        return self._inspections.get_page(
            offset=offset,
            limit=limit,
            filters=[("plant_key", "==", plant_key)],
            sort="inspected_at",
            sort_direction="DESC",
        )

    def get_inspection_photo_refs_for_pest(self, tenant_key: str, pest_key: PestKey) -> list[str]:
        # Strict tenant isolation: only the calling tenant's inspections are
        # scanned. ``pest_key in detected_pest_keys`` selects the inspections
        # that documented this pest. Photo refs are flattened newest-first and
        # deduplicated in Python so the first (newest) occurrence wins.
        query = (
            f"FOR doc IN {col.INSPECTIONS} "
            f"FILTER doc.tenant_key == @tenant_key "
            f"FILTER @pest_key IN doc.detected_pest_keys "
            f"SORT doc.inspected_at DESC "
            f"RETURN doc.photo_refs"
        )
        cursor = self._db.aql.execute(query, bind_vars={"tenant_key": tenant_key, "pest_key": pest_key})
        seen: set[str] = set()
        ordered: list[str] = []
        for refs in cursor:
            for ref in refs or []:
                if ref and ref not in seen:
                    seen.add(ref)
                    ordered.append(ref)
        return ordered

    # ── TreatmentApplication ──

    def create_treatment_application(self, app: TreatmentApplication) -> TreatmentApplication:
        ta = self._applications.create(app, default_now_fields=("applied_at",))

        # Create edges
        ta_id = f"{col.TREATMENT_APPLICATIONS}/{ta.key}"
        self.create_edge(col.APPLIED_TO_PLANT, ta_id, f"{col.PLANT_INSTANCES}/{app.plant_key}")
        self.create_edge(col.TREATMENT_USES, ta_id, f"{col.TREATMENTS}/{app.treatment_key}")

        return ta

    def get_applications_for_plant(
        self,
        plant_key: str,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[TreatmentApplication], int]:
        return self._applications.get_page(
            offset=offset,
            limit=limit,
            filters=[("plant_key", "==", plant_key)],
            sort="applied_at",
            sort_direction="DESC",
        )

    # ── Edge creation ──

    def create_targets_pest_edge(self, treatment_key: TreatmentKey, pest_key: PestKey) -> None:
        from_id = f"{col.TREATMENTS}/{treatment_key}"
        to_id = f"{col.PESTS}/{pest_key}"
        self.create_edge(col.TARGETS_PEST, from_id, to_id)

    def create_targets_disease_edge(self, treatment_key: TreatmentKey, disease_key: str) -> None:
        from_id = f"{col.TREATMENTS}/{treatment_key}"
        to_id = f"{col.DISEASES}/{disease_key}"
        self.create_edge(col.TARGETS_DISEASE, from_id, to_id)

    def create_contraindicated_edge(self, treatment_a_key: TreatmentKey, treatment_b_key: TreatmentKey) -> None:
        from_id = f"{col.TREATMENTS}/{treatment_a_key}"
        to_id = f"{col.TREATMENTS}/{treatment_b_key}"
        self.create_edge(col.CONTRAINDICATED_WITH, from_id, to_id)

    # ── Queries ──

    def get_active_karenz_periods(self, plant_key: str) -> list[dict]:
        query = """
        FOR ta IN treatment_applications
            FILTER ta.plant_key == @plant_key
            FOR t IN treatments
                FILTER t._key == ta.treatment_key
                FILTER t.safety_interval_days > 0
                FILTER DATE_ADD(ta.applied_at, t.safety_interval_days, 'days') > DATE_NOW()
                RETURN {
                    active_ingredient: t.active_ingredient,
                    treatment_name: t.name,
                    applied_at: ta.applied_at,
                    safety_interval_days: t.safety_interval_days,
                    safe_date: DATE_ADD(ta.applied_at, t.safety_interval_days, 'days')
                }
        """
        cursor = self._db.aql.execute(query, bind_vars={"plant_key": plant_key})
        return list(cursor)

    def get_recent_applications(self, plant_key: str, days_window: int = 90) -> list[dict]:
        cutoff = (datetime.now(UTC) - timedelta(days=days_window)).isoformat()
        query = """
        FOR ta IN treatment_applications
            FILTER ta.plant_key == @plant_key
            FILTER ta.applied_at >= @cutoff
            FOR t IN treatments
                FILTER t._key == ta.treatment_key
                RETURN {
                    active_ingredient: t.active_ingredient,
                    treatment_type: t.treatment_type,
                    applied_at: ta.applied_at,
                    treatment_name: t.name
                }
        """
        cursor = self._db.aql.execute(query, bind_vars={"plant_key": plant_key, "cutoff": cutoff})
        return list(cursor)

    def get_treatments_for_pest(self, pest_key: PestKey) -> list[Treatment]:
        pest_id = f"{col.PESTS}/{pest_key}"
        # COLLECT dedupliziert mehrfache identische targets_pest-Edges (entstehen,
        # weil create_edge nicht idempotent ist und der Seed-Loader bei jedem Lauf
        # eine neue Edge anlegt) — sonst erscheint dasselbe Treatment mehrfach.
        query = f"""
        FOR e IN {col.TARGETS_PEST}
            FILTER e._to == @pest_id
            COLLECT from_id = e._from
            FOR t IN {col.TREATMENTS}
                FILTER t._key == PARSE_IDENTIFIER(from_id).key
                RETURN t
        """
        cursor = self._db.aql.execute(query, bind_vars={"pest_id": pest_id})
        return [Treatment(**self._from_doc(doc)) for doc in cursor]

    def get_beneficials_for_pest_slug(self, slug: str) -> list[Beneficial]:
        query = f"FOR b IN {col.BENEFICIALS} FILTER @slug IN b.preys_on RETURN b"
        cursor = self._db.aql.execute(query, bind_vars={"slug": slug})
        return [Beneficial(**self._from_doc(doc)) for doc in cursor]

    def get_pests_for_treatment(self, treatment_key: TreatmentKey) -> list[Pest]:
        treatment_id = f"{col.TREATMENTS}/{treatment_key}"
        # COLLECT dedupliziert mehrfache identische targets_pest-Edges.
        query = f"""
        FOR e IN {col.TARGETS_PEST}
            FILTER e._from == @treatment_id
            COLLECT to_id = e._to
            FOR p IN {col.PESTS}
                FILTER p._id == to_id
                RETURN p
        """
        cursor = self._db.aql.execute(query, bind_vars={"treatment_id": treatment_id})
        return [Pest(**self._from_doc(doc)) for doc in cursor]

    def get_diseases_for_treatment(self, treatment_key: TreatmentKey) -> list[Disease]:
        treatment_id = f"{col.TREATMENTS}/{treatment_key}"
        query = f"""
        FOR e IN {col.TARGETS_DISEASE}
            FILTER e._from == @treatment_id
            COLLECT to_id = e._to
            FOR d IN {col.DISEASES}
                FILTER d._id == to_id
                RETURN d
        """
        cursor = self._db.aql.execute(query, bind_vars={"treatment_id": treatment_id})
        return [Disease(**self._from_doc(doc)) for doc in cursor]
