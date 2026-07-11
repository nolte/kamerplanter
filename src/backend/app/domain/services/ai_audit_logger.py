"""REQ-031 §4.3 / §3.1 — ``AiAuditLogger`` (privacy-preserving KI audit trail).

Writes one :class:`~app.domain.models.ai_assistant.AiAuditLogEntry` per KI call.
The question is only ever stored as a sha256 hash and the answer only as a length
— never plaintext (NFR-007). Retention is 30 days (NFR-011), enforced by
``tasks/ai_tasks.py``.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

import structlog

from app.data_access.arango.ai_repository import ArangoAiAuditRepository
from app.domain.models.ai_assistant import AiAuditLogEntry, AuditStatus

logger = structlog.get_logger(__name__)


def hash_question(question: str) -> str:
    """Return the sha256 hex digest of a question (stable, non-reversible)."""
    return hashlib.sha256(question.encode("utf-8")).hexdigest()


class AiAuditLogger:
    """Persists hashed KI-call audit records."""

    def __init__(self, audit_repo: ArangoAiAuditRepository) -> None:
        self._audit_repo = audit_repo

    def record(
        self,
        *,
        tenant_key: str,
        endpoint: str,
        question: str,
        answer_length: int,
        user_key: str | None = None,
        context_type: str | None = None,
        context_key: str | None = None,
        model_name: str = "",
        provider_type: str = "",
        kb_version: str | None = None,
        language: str = "de",
        uses_tenant_data: bool = False,
        uses_cloud_provider: bool = False,
        latency_ms: int = 0,
        status: AuditStatus = "ok",
        error_class: str | None = None,
    ) -> AiAuditLogEntry:
        """Write an audit entry, storing only the question hash and answer length.

        Failures to persist the audit entry must never break the user-facing KI
        call, so the write is best-effort (logged, then swallowed).
        """
        entry = AiAuditLogEntry(
            tenant_key=tenant_key,
            user_key=user_key,
            endpoint=endpoint,
            context_type=context_type,
            context_key=context_key,
            question_hash=hash_question(question),
            answer_length=answer_length,
            model_name=model_name,
            provider_type=provider_type,
            kb_version=kb_version,
            language=language,
            uses_tenant_data=uses_tenant_data,
            uses_cloud_provider=uses_cloud_provider,
            latency_ms=latency_ms,
            status=status,
            error_class=error_class,
            created_at=datetime.now(UTC),
        )
        try:
            return self._audit_repo.create(entry)
        except Exception:  # noqa: BLE001 — audit must not break the request
            logger.warning("ai_audit_write_failed", endpoint=endpoint, status=status)
            return entry
