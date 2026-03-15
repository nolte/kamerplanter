from datetime import UTC, datetime, timedelta

from arango.database import StandardDatabase

from app.common.types import DiseaseKey, PestKey, TreatmentKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.ipm_repository import IIpmRepository
from app.domain.models.ipm import (
    Disease,
    Inspection,
    Pest,
    Treatment,
    TreatmentApplication,
)


class ArangoIpmRepository(IIpmRepository, BaseArangoRepository):
    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.PESTS)

    # ── Pest CRUD ──

    def get_all_pests(self, offset: int = 0, limit: int = 50) -> tuple[list[Pest], int]:
        docs, total = BaseArangoRepository.get_all(self, offset, limit)
        return [Pest(**doc) for doc in docs], total

    def get_pest_by_key(self, key: PestKey) -> Pest | None:
        doc = BaseArangoRepository.get_by_key(self, key)
        return Pest(**doc) if doc else None

    def create_pest(self, pest: Pest) -> Pest:
        doc = BaseArangoRepository.create(self, pest)
        return Pest(**doc)

    def update_pest(self, key: PestKey, pest: Pest) -> Pest:
        doc = BaseArangoRepository.update(self, key, pest)
        return Pest(**doc)

    def delete_pest(self, key: PestKey) -> bool:
        pest_id = f"{col.PESTS}/{key}"
        for edge_col in [col.TARGETS_PEST, col.DETECTED_PEST]:
            query = f"FOR e IN {edge_col} FILTER e._to == @id REMOVE e IN {edge_col}"
            self._db.aql.execute(query, bind_vars={"id": pest_id})
        return BaseArangoRepository.delete(self, key)

    # ── Disease CRUD ──

    def get_all_diseases(self, offset: int = 0, limit: int = 50) -> tuple[list[Disease], int]:
        query = f"FOR doc IN {col.DISEASES} SORT doc._key LIMIT {offset}, {limit} RETURN doc"
        count_query = f"FOR doc IN {col.DISEASES} COLLECT WITH COUNT INTO total RETURN total"
        cursor = self._db.aql.execute(query)
        items = [Disease(**self._from_doc(doc)) for doc in cursor]
        count_cursor = self._db.aql.execute(count_query)
        total = next(count_cursor, 0)
        return items, total

    def get_disease_by_key(self, key: DiseaseKey) -> Disease | None:
        coll = self._db.collection(col.DISEASES)
        doc = coll.get(key)
        return Disease(**self._from_doc(doc)) if doc else None

    def create_disease(self, disease: Disease) -> Disease:
        coll = self._db.collection(col.DISEASES)
        data = self._to_doc(disease)
        now = self._now()
        data["created_at"] = now
        data["updated_at"] = now
        result = coll.insert(data, return_new=True)
        return Disease(**self._from_doc(result["new"]))

    def update_disease(self, key: DiseaseKey, disease: Disease) -> Disease:
        coll = self._db.collection(col.DISEASES)
        data = self._to_doc(disease)
        data["updated_at"] = self._now()
        data["_key"] = key
        result = coll.update(data, return_new=True)
        return Disease(**self._from_doc(result["new"]))

    def delete_disease(self, key: DiseaseKey) -> bool:
        disease_id = f"{col.DISEASES}/{key}"
        for edge_col in [col.TARGETS_DISEASE, col.DETECTED_DISEASE]:
            query = f"FOR e IN {edge_col} FILTER e._to == @id REMOVE e IN {edge_col}"
            self._db.aql.execute(query, bind_vars={"id": disease_id})
        coll = self._db.collection(col.DISEASES)
        coll.delete(key)
        return True

    # ── Treatment CRUD ──

    def get_all_treatments(self, offset: int = 0, limit: int = 50) -> tuple[list[Treatment], int]:
        query = f"FOR doc IN {col.TREATMENTS} SORT doc._key LIMIT {offset}, {limit} RETURN doc"
        count_query = f"FOR doc IN {col.TREATMENTS} COLLECT WITH COUNT INTO total RETURN total"
        cursor = self._db.aql.execute(query)
        items = [Treatment(**self._from_doc(doc)) for doc in cursor]
        count_cursor = self._db.aql.execute(count_query)
        total = next(count_cursor, 0)
        return items, total

    def get_treatment_by_key(self, key: TreatmentKey) -> Treatment | None:
        coll = self._db.collection(col.TREATMENTS)
        doc = coll.get(key)
        return Treatment(**self._from_doc(doc)) if doc else None

    def create_treatment(self, treatment: Treatment) -> Treatment:
        coll = self._db.collection(col.TREATMENTS)
        data = self._to_doc(treatment)
        now = self._now()
        data["created_at"] = now
        data["updated_at"] = now
        result = coll.insert(data, return_new=True)
        return Treatment(**self._from_doc(result["new"]))

    def update_treatment(self, key: TreatmentKey, treatment: Treatment) -> Treatment:
        coll = self._db.collection(col.TREATMENTS)
        data = self._to_doc(treatment)
        data["updated_at"] = self._now()
        data["_key"] = key
        result = coll.update(data, return_new=True)
        return Treatment(**self._from_doc(result["new"]))

    def delete_treatment(self, key: TreatmentKey) -> bool:
        treatment_id = f"{col.TREATMENTS}/{key}"
        for edge_col in [col.TARGETS_PEST, col.TARGETS_DISEASE, col.CONTRAINDICATED_WITH, col.TREATMENT_USES]:
            query = f"FOR e IN {edge_col} FILTER e._from == @id OR e._to == @id REMOVE e IN {edge_col}"
            self._db.aql.execute(query, bind_vars={"id": treatment_id})
        coll = self._db.collection(col.TREATMENTS)
        coll.delete(key)
        return True

    # ── Inspection ──

    def create_inspection(self, inspection: Inspection) -> Inspection:
        coll = self._db.collection(col.INSPECTIONS)
        data = self._to_doc(inspection)
        now = self._now()
        data["created_at"] = now
        data["updated_at"] = now
        if not data.get("inspected_at"):
            data["inspected_at"] = now
        result = coll.insert(data, return_new=True)
        insp = Inspection(**self._from_doc(result["new"]))

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
        query = (
            f"FOR doc IN {col.INSPECTIONS} "
            f"FILTER doc.plant_key == @plant_key "
            f"SORT doc.inspected_at DESC "
            f"LIMIT {offset}, {limit} RETURN doc"
        )
        count_query = (
            f"FOR doc IN {col.INSPECTIONS} "
            f"FILTER doc.plant_key == @plant_key "
            f"COLLECT WITH COUNT INTO total RETURN total"
        )
        cursor = self._db.aql.execute(query, bind_vars={"plant_key": plant_key})
        items = [Inspection(**self._from_doc(doc)) for doc in cursor]
        count_cursor = self._db.aql.execute(count_query, bind_vars={"plant_key": plant_key})
        total = next(count_cursor, 0)
        return items, total

    # ── TreatmentApplication ──

    def create_treatment_application(self, app: TreatmentApplication) -> TreatmentApplication:
        coll = self._db.collection(col.TREATMENT_APPLICATIONS)
        data = self._to_doc(app)
        now = self._now()
        data["created_at"] = now
        data["updated_at"] = now
        if not data.get("applied_at"):
            data["applied_at"] = now
        result = coll.insert(data, return_new=True)
        ta = TreatmentApplication(**self._from_doc(result["new"]))

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
        query = (
            f"FOR doc IN {col.TREATMENT_APPLICATIONS} "
            f"FILTER doc.plant_key == @plant_key "
            f"SORT doc.applied_at DESC "
            f"LIMIT {offset}, {limit} RETURN doc"
        )
        count_query = (
            f"FOR doc IN {col.TREATMENT_APPLICATIONS} "
            f"FILTER doc.plant_key == @plant_key "
            f"COLLECT WITH COUNT INTO total RETURN total"
        )
        cursor = self._db.aql.execute(query, bind_vars={"plant_key": plant_key})
        items = [TreatmentApplication(**self._from_doc(doc)) for doc in cursor]
        count_cursor = self._db.aql.execute(count_query, bind_vars={"plant_key": plant_key})
        total = next(count_cursor, 0)
        return items, total

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
        query = f"""
        FOR e IN {col.TARGETS_PEST}
            FILTER e._to == @pest_id
            FOR t IN {col.TREATMENTS}
                FILTER t._key == PARSE_IDENTIFIER(e._from).key
                RETURN t
        """
        cursor = self._db.aql.execute(query, bind_vars={"pest_id": pest_id})
        return [Treatment(**self._from_doc(doc)) for doc in cursor]
