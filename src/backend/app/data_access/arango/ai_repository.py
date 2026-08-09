"""REQ-031 §3 — ArangoDB repositories for the KI-Assistent collections.

One module hosts the four small KI repositories (provider configs, conversations,
tip cache, audit log). They are tenant-scoped and back the retention cleanups in
``tasks/ai_tasks.py``.
"""

from __future__ import annotations

from datetime import UTC, datetime

from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.data_access.arango.tenant_scope import tenant_union_predicate
from app.domain.models.ai_assistant import (
    AiAuditLogEntry,
    AiConversation,
    AiProviderConfig,
    AiTipCard,
)


class ArangoAiProviderRepository(BaseArangoRepository[AiProviderConfig]):
    """``ai_provider_configs`` — LLM provider configurations (§3.1)."""

    _model_cls = AiProviderConfig

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.AI_PROVIDER_CONFIGS)

    def list_for_tenant(self, tenant_key: str) -> list[AiProviderConfig]:
        """Tenant providers plus system defaults (``tenant_key == null``).

        Uses the shared union helper with the empty-string arm **off**: system
        defaults here are seeded with a *null* ``tenant_key`` (never ``""``), so
        this repository stays deliberately two-arm — admitting the ``== ""`` arm
        would widen its read scope (see :func:`tenant_union_predicate`).
        """
        predicate, predicate_vars = tenant_union_predicate(tenant_key, include_empty_string=False)
        query = f"""
        FOR doc IN @@collection
          FILTER doc.is_active == true
          FILTER {predicate}
          SORT doc.is_default DESC, doc.display_name ASC
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={"@collection": self._collection_name, **predicate_vars},
        )
        return [AiProviderConfig(**doc) for doc in cursor]

    def get_default(self, tenant_key: str, provider_key: str | None) -> AiProviderConfig | None:
        """Resolve the effective default provider for a tenant.

        Prefers the explicit ``provider_key`` (tenant setting), then the tenant's
        own default, then any system default — so a fresh tenant still gets the
        local Ollama fallback without extra configuration.
        """
        providers = self.list_for_tenant(tenant_key)
        if provider_key:
            for provider in providers:
                if provider.key == provider_key:
                    return provider
        for provider in providers:
            if provider.is_default:
                return provider
        return providers[0] if providers else None


class ArangoAiConversationRepository(BaseArangoRepository[AiConversation]):
    """``ai_conversations`` — chat histories (retention 90 days, §3.1)."""

    _model_cls = AiConversation
    is_tenant_scoped = True

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.AI_CONVERSATIONS)

    def list_for_user(self, tenant_key: str, user_key: str) -> list[AiConversation]:
        return self.find_by_field(
            "tenant_key",
            tenant_key,
            extra_filters=[("user_key", "==", user_key)],
            sort="updated_at",
            sort_direction="DESC",
        )

    def delete_expired(self, *, now: datetime | None = None) -> int:
        """Remove conversations whose ``expires_at`` has passed. Returns count."""
        cutoff = (now or datetime.now(UTC)).isoformat()
        query = """
        FOR doc IN @@collection
          FILTER doc.expires_at != null AND doc.expires_at < @cutoff
          REMOVE doc IN @@collection
          COLLECT WITH COUNT INTO removed
          RETURN removed
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={"@collection": self._collection_name, "cutoff": cutoff},
        )
        return next(cursor, 0)


class ArangoAiTipCacheRepository(BaseArangoRepository[AiTipCard]):
    """``ai_tip_cache`` — cached tip cards / daily tips / explanations (§3.1)."""

    _model_cls = AiTipCard
    is_tenant_scoped = True

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.AI_TIP_CACHE)

    def find_valid(
        self,
        tenant_key: str,
        context_type: str,
        context_key: str,
        *,
        now: datetime | None = None,
    ) -> list[AiTipCard]:
        """Return non-dismissed, still-valid cached tips for a context."""
        stamp = (now or datetime.now(UTC)).isoformat()
        query = """
        FOR doc IN @@collection
          FILTER doc.tenant_key == @tenant_key
          FILTER doc.context_type == @context_type
          FILTER doc.context_key == @context_key
          FILTER doc.dismissed_at == null
          FILTER doc.valid_until == null OR doc.valid_until > @now
          SORT doc.priority ASC, doc.generated_at DESC
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": self._collection_name,
                "tenant_key": tenant_key,
                "context_type": context_type,
                "context_key": context_key,
                "now": stamp,
            },
        )
        return [AiTipCard(**doc) for doc in cursor]

    def invalidate_context(self, tenant_key: str, context_type: str, context_key: str) -> int:
        """Hard-delete cached tips for a context (used on ``/tips/refresh``)."""
        query = """
        FOR doc IN @@collection
          FILTER doc.tenant_key == @tenant_key
          FILTER doc.context_type == @context_type
          FILTER doc.context_key == @context_key
          REMOVE doc IN @@collection
          COLLECT WITH COUNT INTO removed
          RETURN removed
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": self._collection_name,
                "tenant_key": tenant_key,
                "context_type": context_type,
                "context_key": context_key,
            },
        )
        return next(cursor, 0)


class ArangoAiAuditRepository(BaseArangoRepository[AiAuditLogEntry]):
    """``ai_audit_log`` — hashed KI-call audit trail (retention 30 days, §3.1)."""

    _model_cls = AiAuditLogEntry
    is_tenant_scoped = True

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.AI_AUDIT_LOG)

    def list_for_user(self, tenant_key: str, user_key: str, *, limit: int = 200) -> list[AiAuditLogEntry]:
        return self.find_by_field(
            "tenant_key",
            tenant_key,
            extra_filters=[("user_key", "==", user_key)],
            sort="created_at",
            sort_direction="DESC",
            limit=limit,
        )

    def delete_older_than(self, cutoff: datetime) -> int:
        """Remove audit entries created before ``cutoff``. Returns count."""
        query = """
        FOR doc IN @@collection
          FILTER doc.created_at != null AND doc.created_at < @cutoff
          REMOVE doc IN @@collection
          COLLECT WITH COUNT INTO removed
          RETURN removed
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={"@collection": self._collection_name, "cutoff": cutoff.isoformat()},
        )
        return next(cursor, 0)

    def anonymize_user(self, user_key: str) -> int:
        """DSGVO Art. 17 — null out ``user_key`` while keeping the hashes (§7.5)."""
        query = """
        FOR doc IN @@collection
          FILTER doc.user_key == @user_key
          UPDATE doc WITH { user_key: null } IN @@collection
          COLLECT WITH COUNT INTO updated
          RETURN updated
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={"@collection": self._collection_name, "user_key": user_key},
        )
        return next(cursor, 0)
