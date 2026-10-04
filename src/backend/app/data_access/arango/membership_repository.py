from datetime import UTC, datetime
from typing import cast

from arango.cursor import Cursor
from arango.database import StandardDatabase
from arango.exceptions import AQLQueryExecuteError

from app.common.datetimes import ensure_aware_utc
from app.common.enums import AdminScope
from app.common.exceptions import WriteConflictError
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.engines.tenant_erasure_engine import TenantErasureEngine
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
        self._remove_dependents(key)
        return super().delete(key)

    def _remove_dependents(self, key: str) -> None:
        """Remove the edges and location assignments that hang off membership *key*."""
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

    #: Attempts at the rollback below when a concurrent write on the deletion
    #: record (its withdrawal or its claim) conflicts with the touch.
    _ROLLBACK_ATTEMPTS = 3

    #: A record no run ever claimed — the only one the erasure can still withdraw
    #: (``ArangoTenantErasureRepository.delete_unclaimed``'s own condition).
    _UNCLAIMED = (
        "record.origin == 'account_erasure' AND record.status == 'in_progress' "
        "AND record.last_attempt_at == null AND (record.attempt_count == null OR record.attempt_count == 0)"
    )

    def delete_while_tenant_frozen(self, key: str, tenant_key: str) -> bool:
        """Remove membership *key* only while the tenant's deletion record is open, atomically (#1924).

        Against a record **no run has claimed** — the only state the erasure can
        still withdraw — one AQL statement reads the record, **writes** it
        (``updated_at``) and removes the membership. The write is what makes the
        two decisions that meet on a join exclusive: the erasure withdraws the
        record (``delete_unclaimed``, a write on the same document) and then reads
        the members again; a read-then-delete on the joiner's side would let the
        joiner's delete land after that read, and the tenant would be kept for a
        member nobody has any more. With the touch, the withdrawal and this
        rollback cannot both succeed on the document: whichever commits first is
        seen by the other — a rollback that commits first is seen by the
        erasure's re-read, a withdrawal that commits first leaves this statement
        nothing to match, and the membership stands.

        Against a record a run **has claimed** the erasure has decided to erase and
        can no longer keep the tenant, so there is nothing to arbitrate and the
        record is left untouched: a write here would conflict with the running
        erasure's own heartbeat and read as a lost claim.

        Returns ``True`` when the membership was removed, ``False`` when no open
        record exists any more (withdrawn, completed, or never there) — the
        membership stands then.

        Raises:
            WriteConflictError: the record kept conflicting with a concurrent
                write for :attr:`_ROLLBACK_ATTEMPTS` attempts.
        """
        unclaimed = f"""
        FOR record IN @@records
          FILTER record._key == @record_key AND {self._UNCLAIMED}
          UPDATE record WITH {{ updated_at: @now }} IN @@records
          FOR member IN @@memberships
            FILTER member._key == @key AND member.tenant_key == @tenant_key
            REMOVE member IN @@memberships
            RETURN OLD._key
        """
        claimed = f"""
        FOR record IN @@records
          FILTER record._key == @record_key AND record.status != 'completed' AND NOT ({self._UNCLAIMED})
          FOR member IN @@memberships
            FILTER member._key == @key AND member.tenant_key == @tenant_key
            REMOVE member IN @@memberships
            RETURN OLD._key
        """
        bind_vars = {
            "@records": col.TENANT_ERASURE_RECORDS,
            "@memberships": col.MEMBERSHIPS,
            "record_key": TenantErasureEngine.record_key(tenant_key),
            "key": key,
            "tenant_key": tenant_key,
        }
        for _attempt in range(self._ROLLBACK_ATTEMPTS):
            try:
                # Claimed after the first statement looked: the second sees it claimed.
                for query, extra in ((unclaimed, {"now": datetime.now(UTC).isoformat()}), (claimed, {})):
                    cursor = cast(Cursor, self._db.aql.execute(query, bind_vars={**bind_vars, **extra}))
                    if list(cursor):
                        self._remove_dependents(key)
                        return True
                return False
            except AQLQueryExecuteError as exc:
                if exc.error_code != 1200:
                    raise
        raise WriteConflictError(col.TENANT_ERASURE_RECORDS)

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

    def deactivate_all_for_tenant(self, tenant_key: str) -> int:
        """Deactivate every membership of the tenant; the rows are removed by the tenant erasure (#1769).

        A deactivated membership is refused by ``_membership_for_slug`` (403), so
        no member request writes into a tenant while it is being erased.
        """
        cursor = self._db.aql.execute(
            """
            FOR m IN @@collection
              FILTER m.tenant_key == @tenant_key AND m.is_active != false
              UPDATE m WITH { is_active: false } IN @@collection
              COLLECT WITH COUNT INTO affected
              RETURN affected
            """,
            bind_vars={"@collection": col.MEMBERSHIPS, "tenant_key": tenant_key},
        )
        return int(next(cursor, 0))

    def active_member_user_keys(self, *, tenant_key: str) -> list[str]:
        """The distinct accounts that still use the tenant: an active membership of an active account (#1788).

        "Active" membership is what :meth:`deactivate_all_for_tenant` switches
        off (``is_active != false``), so a missing flag counts as active, as the
        model default says. The **account** must exist and be active too: an
        account whose own erasure is pending is deactivated when it is requested
        (#1788 review GDPR-01) — counting it would keep a tenant for someone who
        is leaving, and nobody would reach that tenant again once both are gone.
        """
        cursor = self._db.aql.execute(
            """
            FOR m IN @@collection
              FILTER m.tenant_key == @tenant_key AND m.is_active != false
              FILTER m.user_key != null AND m.user_key != ""
              LET account = DOCUMENT(@@users, m.user_key)
              FILTER account != null AND account.is_active != false
              COLLECT user_key = m.user_key
              RETURN user_key
            """,
            bind_vars={"@collection": col.MEMBERSHIPS, "@users": col.USERS, "tenant_key": tenant_key},
        )
        return list(cursor)

    def active_member_joined_at(self, *, tenant_key: str) -> dict[str, datetime | None]:
        """Active member account key -> start of the membership (#1824), as ``active_member_user_keys`` counts them."""
        cursor = self._db.aql.execute(
            """
            FOR m IN @@collection
              FILTER m.tenant_key == @tenant_key AND m.is_active != false
              FILTER m.user_key != null AND m.user_key != ""
              LET account = DOCUMENT(@@users, m.user_key)
              FILTER account != null AND account.is_active != false
              RETURN { user_key: m.user_key, joined_at: m.joined_at }
            """,
            bind_vars={"@collection": col.MEMBERSHIPS, "@users": col.USERS, "tenant_key": tenant_key},
        )
        # One row per account: the (user_key, tenant_key) index is unique.
        return {row["user_key"]: _parse_instant(row.get("joined_at")) for row in cursor}


def _parse_instant(value: object) -> datetime | None:
    """A stored start as an aware instant; ``None`` when absent or unreadable (#1824).

    An unreadable value must not raise: it would fail every retry of the account
    erasure that reads it. ``None`` is the "start not recorded" answer the caller
    already handles.
    """
    if not isinstance(value, str | datetime) or value == "":
        return None
    try:
        return ensure_aware_utc(value)
    except ValueError:
        return None
