from arango.database import StandardDatabase

from app.common.enums import AdminScope
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.membership_repository import IMembershipRepository
from app.domain.models.membership import MemberInfo, Membership, UserMembershipInfo


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

    def update_fields(self, key: str, fields: dict) -> Membership | None:
        """Merge ``fields`` into the stored membership and rewrite it (#968 §2).

        **Renamed from ``update``.** The old name shadowed
        :meth:`BaseArangoRepository.update`, whose signature takes a full
        *model*, with one that takes an arbitrary ``dict``. That reads like
        the checked full-model path while accepting whatever keys it is
        handed, so a caller who forwarded request data would have performed
        mass assignment under a reassuring name. The name now says what the
        payload is, and the inherited full-model :meth:`update` is reachable
        again on this repository instead of being shadowed.

        **Caller obligation.** ``fields`` is applied key-by-key, so it must be
        built from named fields or a validated schema's ``model_dump()`` —
        never from a raw request body. ``model_copy(update=...)`` does not
        validate, so an unknown or ill-typed key survives this step; what
        catches an ill-typed *declared* field is the re-validation the
        inherited :meth:`update` performs on the merged model (#968).

        **Not the base class's merge.** This deliberately keeps its
        read-modify-write shape rather than delegating to
        :meth:`BaseArangoRepository.update_fields`: that method writes the
        dict straight through and is documented as unchecked, whereas this
        one materialises a full Membership and therefore gets validated. The
        price is the base method's lost-update commutativity — two concurrent
        calls touching *disjoint* fields can clobber each other here. Swapping
        that trade is a decision of its own, not a side effect of a rename.

        Returns ``None`` when no membership carries ``key``.
        """
        existing = self.get_by_key(key)
        if not existing:
            return None
        merged = existing.model_copy(update=fields)
        return super().update(key, merged)

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

    def list_by_user_with_tenant(self, user_key: str) -> list[UserMembershipInfo]:
        """A user's memberships joined to each tenant's name and slug (#1019).

        The user-perspective twin of :meth:`list_by_tenant`. A membership whose
        tenant document no longer exists is skipped (``FILTER t != null``),
        matching the router AQL this consolidates.
        """
        query = """
        FOR m IN @@memberships
          FILTER m.user_key == @user_key
          LET t = DOCUMENT(CONCAT(@tenants_col, "/", m.tenant_key))
          FILTER t != null
          RETURN {
            membership_key: m._key,
            tenant_key: m.tenant_key,
            tenant_name: t.name,
            tenant_slug: t.slug,
            role: m.role,
            is_active: m.is_active,
            joined_at: m.joined_at
          }
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@memberships": col.MEMBERSHIPS,
                "user_key": user_key,
                "tenants_col": col.TENANTS,
            },
        )
        return [UserMembershipInfo(**doc) for doc in cursor]

    def count(self) -> int:
        """Total number of membership documents (platform-admin statistics, #1019)."""
        return self.collection.count()

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

    def delete_all_for_user(self, user_key: str) -> int:
        """Delete every membership of one user, with its graph edges (#1019).

        The user-perspective twin of :meth:`delete_all_for_tenant`: same
        ``has_membership`` (inbound) + ``membership_in`` (outbound) edge cleanup,
        filtered on ``user_key`` instead of ``tenant_key``. Returns the number of
        memberships removed.
        """
        query = f"""
        FOR m IN {col.MEMBERSHIPS}
          FILTER m.user_key == @user_key
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
        cursor = self._db.aql.execute(query, bind_vars={"user_key": user_key})
        return sum(1 for _ in cursor)
