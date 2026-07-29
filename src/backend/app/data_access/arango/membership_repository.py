from arango.database import StandardDatabase

from app.common.enums import AdminScope
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.membership_repository import IMembershipRepository
from app.domain.models.membership import MemberInfo, Membership


class ArangoMembershipRepository(BaseArangoRepository[Membership], IMembershipRepository):
    _model_cls = Membership

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.MEMBERSHIPS)

    def get_by_user_and_tenant(self, user_key: str, tenant_key: str) -> Membership | None:
        query = """
        FOR doc IN @@collection
          FILTER doc.user_key == @user_key AND doc.tenant_key == @tenant_key
          LIMIT 1
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.MEMBERSHIPS,
                "user_key": user_key,
                "tenant_key": tenant_key,
            },
        )
        docs = list(cursor)
        if not docs:
            return None
        return Membership(**self._from_doc(docs[0]))

    def create(self, membership: Membership) -> Membership:
        created = super().create(membership)
        # Create edges: user -> membership, membership -> tenant
        user_id = f"{col.USERS}/{membership.user_key}"
        membership_id = f"{col.MEMBERSHIPS}/{created.key}"
        tenant_id = f"{col.TENANTS}/{membership.tenant_key}"
        self.create_edge(col.HAS_MEMBERSHIP, user_id, membership_id)
        self.create_edge(col.MEMBERSHIP_IN, membership_id, tenant_id)
        return created

    def update(self, key: str, data: dict) -> Membership | None:
        existing = self.get_by_key(key)
        if not existing:
            return None
        update_data = existing.model_copy(update=data)
        return super().update(key, update_data)

    def delete(self, key: str) -> bool:
        membership_id = f"{col.MEMBERSHIPS}/{key}"
        # Clean up edges
        self.delete_edges(col.HAS_MEMBERSHIP, membership_id, direction="inbound")
        self.delete_edges(col.MEMBERSHIP_IN, membership_id)
        # Delete location assignments for this membership
        query = f"""
        FOR doc IN {col.LOCATION_ASSIGNMENTS}
          FILTER doc.membership_key == @key
          REMOVE doc IN {col.LOCATION_ASSIGNMENTS}
        """
        self._db.aql.execute(query, bind_vars={"key": key})
        return super().delete(key)

    def list_by_tenant(self, tenant_key: str) -> list[MemberInfo]:
        query = """
        FOR m IN @@memberships
          FILTER m.tenant_key == @tenant_key
          LET u = DOCUMENT(CONCAT(@users_col, "/", m.user_key))
          RETURN {
            key: m._key,
            user_key: m.user_key,
            display_name: u.display_name,
            email: u.email,
            role: m.role,
            is_active: m.is_active,
            joined_at: m.joined_at
          }
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@memberships": col.MEMBERSHIPS,
                "tenant_key": tenant_key,
                "users_col": col.USERS,
            },
        )
        return [MemberInfo(**doc) for doc in cursor]

    def list_by_user(self, user_key: str) -> list[Membership]:
        return self.find_by_field("user_key", user_key, sort="created_at")

    def count_managers(self, tenant_key: str) -> int:
        """Active memberships in the tenant holding the ``management`` scope (INV-1).

        Counts on axis 2, not on the domain rank: after REQ-049 a lead is not
        automatically an administrator, and the guard has to protect the people
        who can actually invite someone.
        """
        query = """
        FOR doc IN @@collection
          FILTER doc.tenant_key == @tenant_key
            AND doc.is_active == true
            AND @scope IN doc.admin_scopes
          COLLECT WITH COUNT INTO cnt
          RETURN cnt
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.MEMBERSHIPS,
                "tenant_key": tenant_key,
                "scope": AdminScope.MANAGEMENT.value,
            },
        )
        return next(cursor, 0)

    def delete_all_for_tenant(self, tenant_key: str) -> int:
        # First clean up edges for each membership
        query = f"""
        FOR m IN {col.MEMBERSHIPS}
          FILTER m.tenant_key == @tenant_key
          LET mid = CONCAT("{col.MEMBERSHIPS}/", m._key)
          LET del_has = (
            FOR e IN {col.HAS_MEMBERSHIP} FILTER e._to == mid REMOVE e IN {col.HAS_MEMBERSHIP}
          )
          LET del_in = (
            FOR e IN {col.MEMBERSHIP_IN} FILTER e._from == mid REMOVE e IN {col.MEMBERSHIP_IN}
          )
          REMOVE m IN {col.MEMBERSHIPS}
          RETURN 1
        """
        cursor = self._db.aql.execute(query, bind_vars={"tenant_key": tenant_key})
        return sum(1 for _ in cursor)
