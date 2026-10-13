from collections.abc import Callable, Collection
from datetime import datetime
from typing import Any, Literal, cast

import structlog
from arango.cursor import Cursor
from arango.database import StandardDatabase, TransactionDatabase
from arango.exceptions import DocumentInsertError, DocumentUpdateError, TransactionCommitError
from pydantic import TypeAdapter

from app.common.enums import TenantStatus, TenantType
from app.common.exceptions import WriteConflictError
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.tenant_repository import ITenantRepository
from app.domain.models.membership import Membership
from app.domain.models.security_audit import SecurityAuditEntry
from app.domain.models.tenant import Tenant

logger = structlog.get_logger()

#: The only tenant fields :meth:`ArangoTenantRepository.update_fields` clears on an explicit ``None``
#: (REQ-056 SEC-005); ``None`` for any other field is refused.
CLEARABLE_FIELDS = frozenset({"deletion_scheduled_at", "status_before_deletion", "description"})


class ArangoTenantRepository(BaseArangoRepository[Tenant], ITenantRepository):
    _model_cls = Tenant

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.TENANTS)

    def get_by_slug(self, slug: str) -> Tenant | None:
        return self.find_one_by_field("slug", slug)

    def create_with_lead_membership(
        self,
        tenant: Tenant,
        membership: Membership,
        *,
        audit: Callable[[Tenant, Membership], SecurityAuditEntry] | None = None,
        tenant_key: str | None = None,
    ) -> tuple[Tenant, Membership]:
        """Found a tenant atomically: tenant, founder's membership, both edges and the audit row (#2118).

        One **stream transaction** over the five collections, the model :meth:`ArangoCareReminderRepository.
        create_linked_profile` set (#1292): nothing is visible to another connection before the commit, and
        an abort leaves no document behind - which is why a failure needs no cleanup. Measured on ArangoDB
        3.12.8 before this method existed: a failure between the membership's insert and its second edge left
        the tenant (slug taken), the membership and one edge behind, and nobody could delete the tenant.

        A rejection of the unique ``slug`` index reaches the caller as :class:`DuplicateError` (``1210``) or
        :class:`WriteConflictError` (``1200``) through the same translation the plain create uses. The owner
        reference check of the plain path (``_verify_owned_references``) does not apply: neither model
        declares an owned foreign reference.
        """
        # The membership is the *tenant's* founder: its key is the tenant's, known only once the document
        # is written, so the membership payload is built inside the transaction.
        from app.data_access.arango.membership_repository import ArangoMembershipRepository

        memberships = ArangoMembershipRepository(self._db)
        tenant_data = self.insert_payload(tenant)
        if tenant_key:
            tenant_data["_key"] = tenant_key  # a tenant import names the key before the founding (#2138)
        transaction = self._db.begin_transaction(
            write=[col.TENANTS, col.MEMBERSHIPS, col.HAS_MEMBERSHIP, col.MEMBERSHIP_IN, col.SECURITY_AUDIT_LOG]
        )
        try:
            tenant_doc = self._insert_in(transaction, col.TENANTS, tenant_data)
            stored_tenant: Tenant = self.wrap_document(dict(tenant_doc))
            founding = membership.model_copy(update={"tenant_key": stored_tenant.key or ""})
            membership_data = memberships.insert_payload(founding)
            membership_doc = self._insert_in(transaction, col.MEMBERSHIPS, membership_data)
            stored_membership: Membership = memberships.wrap_document(dict(membership_doc))
            now = self._now()
            for edge_collection, source, target in (
                (col.HAS_MEMBERSHIP, f"{col.USERS}/{founding.user_key}", f"{col.MEMBERSHIPS}/{stored_membership.key}"),
                (col.MEMBERSHIP_IN, f"{col.MEMBERSHIPS}/{stored_membership.key}", f"{col.TENANTS}/{stored_tenant.key}"),
            ):
                self._insert_in(transaction, edge_collection, {"_from": source, "_to": target, "created_at": now})
            if audit is not None:
                row = audit(stored_tenant, stored_membership)
                row_data = row.model_dump(by_alias=True, exclude_none=True, mode="json")
                row_data.pop("_key", None)
                row_data["created_at"] = row.created_at.isoformat() if row.created_at else now
                self._insert_in(transaction, col.SECURITY_AUDIT_LOG, row_data)
            try:
                transaction.commit_transaction()
            except TransactionCommitError as exc:
                mapped = self._mapped_insert_error(exc, col.TENANTS, tenant_data)
                if mapped is not None:
                    raise mapped from exc
                raise
        except BaseException:
            self._abort_quietly(transaction)
            raise
        return stored_tenant, stored_membership

    def _insert_in(self, transaction: TransactionDatabase, collection: str, data: dict[str, Any]) -> dict[str, Any]:
        """Insert one document through the transaction handle; a unique-index rejection becomes its domain error."""
        try:
            written = transaction.collection(collection).insert(data, return_new=True)
        except DocumentInsertError as exc:
            mapped = self._mapped_insert_error(exc, collection, data)
            if mapped is not None:
                raise mapped from exc
            raise
        return cast(dict[str, Any], cast(dict[str, Any], written)["new"])

    @staticmethod
    def _abort_quietly(transaction: TransactionDatabase) -> None:
        """Roll back without masking the failure that got us here (the pattern of every transactional writer)."""
        try:
            transaction.abort_transaction()
        except Exception:  # noqa: BLE001 - the primary error is the one to raise; a failed abort is only logged
            logger.warning("tenant_founding_transaction_abort_failed", exc_info=True)

    def update_fields(self, key: str, fields: dict) -> Tenant | None:
        """Merge ``fields`` into the stored tenant in **one** write, validated first (#968 §2, REQ-056).

        **Renamed from ``update``.** The old name shadowed
        :meth:`BaseArangoRepository.update`, whose signature takes a full
        *model*, with one that takes an arbitrary ``dict``; a caller who
        forwarded request data would have performed mass assignment under a
        reassuring name.

        **Caller obligation.** ``fields`` must be built from named fields or a
        validated schema's ``model_dump()`` — never from a raw request body.

        **Validated, then one write.** The stored tenant merged with ``fields``
        is re-validated as a whole :class:`Tenant` (an ill-typed declared field
        raises before anything is written); then only the keys ``fields`` names
        are written, serialised the way the full-document path serialises them,
        in a single ``UPDATE``. Until REQ-056 this rewrote the whole document
        from the merged model, and an explicit ``None`` was dropped by that
        dump (``exclude_none``): measured on ArangoDB, a cancelled deletion left
        ``deletion_scheduled_at`` on the reopened tenant.

        **``None`` clears — only an allowlisted field** (:data:`CLEARABLE_FIELDS`:
        ``deletion_scheduled_at``, ``status_before_deletion``, ``description``);
        the attribute is removed (``keepNull: false``) and reads as the model's
        ``None`` default. ``None`` for any other field raises ``ValueError``: a
        reset nobody declared is a bug, not a write. The lifecycle state itself
        moves through :meth:`transition_status`, which compares and sets.

        Returns ``None`` when no tenant carries ``key``.
        """
        cleared = {name for name, value in fields.items() if value is None}
        refused = cleared - CLEARABLE_FIELDS
        if refused:
            raise ValueError(f"tenant fields cannot be cleared: {sorted(refused)}")
        existing = self.get_by_key(key)
        if not existing:
            return None
        # ``_to_doc`` re-validates the merged model (#968) and raises the domain ValidationError (422).
        doc = self._to_doc(existing.model_copy(update=fields))
        payload: dict[str, Any] = {name: doc[name] for name in fields if name not in cleared and name in doc}
        payload.update(dict.fromkeys(cleared))
        payload = {name: value for name, value in payload.items() if not name.startswith("_")}
        payload["updated_at"] = self._now()
        try:
            result = self.collection.update({**payload, "_key": key}, return_new=True, keep_none=False, merge=False)
        except DocumentUpdateError as exc:
            if exc.error_code == 1202:  # removed between the read and the write
                return None
            if exc.error_code == 1200:
                raise WriteConflictError(self._collection_name) from exc
            raise
        return cast(Tenant, self._wrap(self._from_doc(result["new"])))

    def transition_status(
        self,
        key: str,
        *,
        expected: Collection[TenantStatus],
        status: TenantStatus | None,
        deletion_scheduled_at: datetime | None | Literal["keep"],
        previous: Literal["remember", "clear", "keep"],
        restore_fallback: TenantStatus | None = None,
    ) -> Tenant | None:
        """Compare-and-set of the lifecycle state in one AQL ``UPDATE`` (REQ-056 §4.3, SEC-002).

        ``FILTER current IN @expected`` is the compare (``current`` reads a document that still
        carries the retired ``is_active`` bool the way ``Tenant`` does — ``false`` is ``suspended``
        — and the write drops that bool): a caller whose snapshot is stale
        (a concurrent suspension, cancellation, claim or settlement moved the tenant) matches
        nothing and gets ``None``. ``status_before_deletion`` is taken from ``OLD.status``
        inside the same statement, never from the caller's read. ``OPTIONS { keepNull: false }``
        removes an attribute set to ``null`` (the clears).
        """
        rememberable = [TenantStatus.ACTIVE.value, TenantStatus.SUSPENDED.value]
        query = """
            FOR t IN @@col
              FILTER t._key == @key
              LET current = t.status != null ? t.status : (t.is_active == false ? "suspended" : "active")
              FILTER current IN @expected
              LET restored = POSITION(@rememberable, t.status_before_deletion) ? t.status_before_deletion : @fallback
              LET target = @restore ? restored : @status
              FILTER target != null
              LET remembered = POSITION(@rememberable, current) ? current : t.status_before_deletion
              UPDATE t WITH MERGE(
                { status: target, is_active: null, updated_at: @now },
                @set_at ? { deletion_scheduled_at: @at } : {},
                @previous == "remember" ? { status_before_deletion: remembered } : {},
                @previous == "clear" ? { status_before_deletion: null } : {}
              ) IN @@col OPTIONS { keepNull: false }
              RETURN NEW
        """
        bind_vars: dict[str, Any] = {
            "@col": self._collection_name,
            "key": key,
            "expected": sorted(TenantStatus(item).value for item in expected),
            "rememberable": rememberable,
            "fallback": restore_fallback.value if restore_fallback is not None else None,
            "restore": status is None,
            "status": status.value if status is not None else None,
            "now": self._now(),
            "set_at": deletion_scheduled_at != "keep",
            "at": TypeAdapter(datetime).dump_python(deletion_scheduled_at, mode="json")
            if isinstance(deletion_scheduled_at, datetime)
            else None,
            "previous": previous,
        }
        rows = list(cast(Cursor, self._db.aql.execute(query, bind_vars=bind_vars)))
        if not rows:
            return None
        return cast(Tenant, self._wrap(self._from_doc(rows[0])))

    def list_by_owner(self, owner_user_key: str) -> list[Tenant]:
        return self.find_by_field("owner_user_key", owner_user_key, sort="created_at")

    def list_all(self, *, offset: int | None = None, limit: int | None = None) -> list[Tenant]:
        """Tenants, newest first (platform-admin listing, #1019).

        ``offset``/``limit`` read one window (MT-035, #2131); both ``None`` reads
        every tenant. ``_key`` breaks ``created_at`` ties so pages never overlap.
        """
        docs = self._find_docs(
            [], sort="created_at", sort_direction="DESC", offset=offset, limit=limit, tiebreak_key=True
        )
        return self._wrap_many(docs)

    def count(self, *, active_only: bool = False) -> int:
        """Number of tenant documents; ``active_only`` counts those in state ``active`` (#1019, #2123)."""
        if not active_only:
            return self.collection.count()
        query = """
        FOR doc IN @@collection
          FILTER doc.status == 'active'
          COLLECT WITH COUNT INTO cnt
          RETURN cnt
        """
        cursor = self._db.aql.execute(query, bind_vars={"@collection": col.TENANTS})
        return next(cursor, 0)

    def keys_in_status(self, statuses: Collection[TenantStatus]) -> dict[str, TenantStatus]:
        """``{tenant_key: status}`` of every tenant in one of *statuses* (MT-032, #2128).

        The ``LET`` mirrors ``Tenant._legacy_is_active`` and the field default: a stored
        ``status`` wins, a pre-v0085 ``is_active == false`` reads as ``suspended``, and a
        document with neither is ``active`` — so this selects exactly the tenants
        :class:`~app.tasks.tenant_gate.ActiveTenants` would admit for the same states.
        """
        wanted = sorted({TenantStatus(status).value for status in statuses})
        if not wanted:
            return {}
        query = """
        FOR doc IN @@collection
          LET state = doc.status != null ? doc.status : (doc.is_active == false ? @suspended : @active)
          FILTER state IN @statuses
          SORT doc._key
          RETURN { key: doc._key, status: state }
        """
        bind_vars: dict[str, Any] = {
            "@collection": col.TENANTS,
            "statuses": wanted,
            "suspended": TenantStatus.SUSPENDED.value,
            "active": TenantStatus.ACTIVE.value,
        }
        rows = cast(Cursor, self._db.aql.execute(query, bind_vars=bind_vars))
        return {row["key"]: TenantStatus(row["status"]) for row in rows}

    def count_organizations_by_owner(self, owner_user_key: str) -> int:
        query = """
        FOR doc IN @@collection
          FILTER doc.owner_user_key == @owner AND doc.tenant_type == @type AND doc.status != @deleted
          COLLECT WITH COUNT INTO cnt
          RETURN cnt
        """
        # REQ-056 §6.2 (#2142) — every state counts (a suspended organisation too) except ``deleted``:
        # its erasure has claimed it and the document is on its way out.
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.TENANTS,
                "owner": owner_user_key,
                "type": TenantType.ORGANIZATION.value,
                "deleted": TenantStatus.DELETED.value,
            },
        )
        return next(cursor, 0)

    def personal_tenant_keys_by_owner(self, owner_user_key: str) -> list[str]:
        cursor = self._db.aql.execute(
            """
            FOR doc IN @@collection
              FILTER doc.owner_user_key == @owner AND doc.tenant_type == @type
              SORT DATE_TIMESTAMP(doc.created_at), doc._key
              RETURN doc._key
            """,
            bind_vars={
                "@collection": col.TENANTS,
                "owner": owner_user_key,
                "type": TenantType.PERSONAL.value,
            },
        )
        return list(cursor)
