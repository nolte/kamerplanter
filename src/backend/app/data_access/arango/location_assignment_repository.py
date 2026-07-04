from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.location_assignment_repository import (
    ILocationAssignmentRepository,
)
from app.domain.models.location_assignment import LocationAssignment


class ArangoLocationAssignmentRepository(BaseArangoRepository[LocationAssignment], ILocationAssignmentRepository):
    _model_cls = LocationAssignment

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.LOCATION_ASSIGNMENTS)

    def create(self, assignment: LocationAssignment) -> LocationAssignment:
        created = super().create(assignment)
        # Create edges
        membership_id = f"{col.MEMBERSHIPS}/{assignment.membership_key}"
        location_id = f"locations/{assignment.location_key}"
        tenant_id = f"{col.TENANTS}/{assignment.tenant_key}"
        assignment_id = f"{col.LOCATION_ASSIGNMENTS}/{created.key}"
        self.create_edge(col.ASSIGNED_TO_LOCATION, assignment_id, location_id)
        self.create_edge(col.ASSIGNMENT_FOR, assignment_id, membership_id)
        self.create_edge(col.ASSIGNMENT_IN_TENANT, assignment_id, tenant_id)
        return created

    def update(self, key: str, data: dict) -> LocationAssignment | None:
        existing = self.get_by_key(key)
        if not existing:
            return None
        update_data = existing.model_copy(update=data)
        return super().update(key, update_data)

    def delete(self, key: str) -> bool:
        assignment_id = f"{col.LOCATION_ASSIGNMENTS}/{key}"
        # Clean up edges
        for edge_col in (
            col.ASSIGNED_TO_LOCATION,
            col.ASSIGNMENT_FOR,
            col.ASSIGNMENT_IN_TENANT,
        ):
            self.delete_edges(edge_col, assignment_id)
        return super().delete(key)

    def list_by_tenant(self, tenant_key: str) -> list[LocationAssignment]:
        return self.find_by_field("tenant_key", tenant_key, sort="created_at")

    def list_by_membership(self, membership_key: str) -> list[LocationAssignment]:
        return self.find_by_field("membership_key", membership_key, sort="created_at")

    def get_by_membership_and_location(self, membership_key: str, location_key: str) -> LocationAssignment | None:
        query = """
        FOR doc IN @@collection
          FILTER doc.membership_key == @membership_key
             AND doc.location_key == @location_key
          LIMIT 1
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.LOCATION_ASSIGNMENTS,
                "membership_key": membership_key,
                "location_key": location_key,
            },
        )
        docs = list(cursor)
        if not docs:
            return None
        return LocationAssignment(**self._from_doc(docs[0]))

    def delete_all_for_tenant(self, tenant_key: str) -> int:
        query = f"""
        FOR doc IN {col.LOCATION_ASSIGNMENTS}
          FILTER doc.tenant_key == @tenant_key
          LET aid = CONCAT("{col.LOCATION_ASSIGNMENTS}/", doc._key)
          LET d1 = (FOR e IN {col.ASSIGNED_TO_LOCATION} FILTER e._from == aid REMOVE e IN {col.ASSIGNED_TO_LOCATION})
          LET d2 = (FOR e IN {col.ASSIGNMENT_FOR} FILTER e._from == aid REMOVE e IN {col.ASSIGNMENT_FOR})
          LET d3 = (FOR e IN {col.ASSIGNMENT_IN_TENANT} FILTER e._from == aid REMOVE e IN {col.ASSIGNMENT_IN_TENANT})
          REMOVE doc IN {col.LOCATION_ASSIGNMENTS}
          RETURN 1
        """
        cursor = self._db.aql.execute(query, bind_vars={"tenant_key": tenant_key})
        return sum(1 for _ in cursor)
