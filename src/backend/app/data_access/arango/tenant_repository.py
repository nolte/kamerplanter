from collections.abc import Callable
from typing import Any, cast

import structlog
from arango.database import StandardDatabase, TransactionDatabase
from arango.exceptions import DocumentInsertError, TransactionCommitError

from app.common.enums import TenantType
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.tenant_repository import ITenantRepository
from app.domain.models.membership import Membership
from app.domain.models.security_audit import SecurityAuditEntry
from app.domain.models.tenant import Tenant

logger = structlog.get_logger()


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
        """Merge ``fields`` into the stored tenant and rewrite it (#968 §2).

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
        one materialises a full Tenant and therefore gets validated. The
        price is the base method's lost-update commutativity — two concurrent
        calls touching *disjoint* fields can clobber each other here. Swapping
        that trade is a decision of its own, not a side effect of a rename.

        Returns ``None`` when no tenant carries ``key``.
        """
        existing = self.get_by_key(key)
        if not existing:
            return None
        merged = existing.model_copy(update=fields)
        return super().update(key, merged)

    def list_by_owner(self, owner_user_key: str) -> list[Tenant]:
        return self.find_by_field("owner_user_key", owner_user_key, sort="created_at")

    def list_all(self) -> list[Tenant]:
        """Every tenant, newest first (platform-admin listing, #1019)."""
        docs = self._find_docs([], sort="created_at", sort_direction="DESC")
        return self._wrap_many(docs)

    def count(self, *, active_only: bool = False) -> int:
        """Number of tenant documents; ``active_only`` counts ``is_active`` ones (#1019)."""
        if not active_only:
            return self.collection.count()
        query = """
        FOR doc IN @@collection
          FILTER doc.is_active == true
          COLLECT WITH COUNT INTO cnt
          RETURN cnt
        """
        cursor = self._db.aql.execute(query, bind_vars={"@collection": col.TENANTS})
        return next(cursor, 0)

    def count_organizations_by_owner(self, owner_user_key: str) -> int:
        query = """
        FOR doc IN @@collection
          FILTER doc.owner_user_key == @owner AND doc.tenant_type == @type
          COLLECT WITH COUNT INTO cnt
          RETURN cnt
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.TENANTS,
                "owner": owner_user_key,
                "type": TenantType.ORGANIZATION.value,
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
