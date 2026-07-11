"""REQ-031 §4.3 — ``ConsentGuard`` for stage 3 of the KI feature toggle.

Bridges the REQ-025 consent store to the KI endpoints. A knowledge question
without tenant context needs no consent; tip cards / daily tip / "why" / chat
need ``ai_tenant_data_access``; a cloud provider additionally needs
``ai_cloud_processing`` (§7.1).
"""

from __future__ import annotations

from app.common.exceptions import ConsentRequiredError
from app.data_access.arango.consent_repository import ArangoConsentRepository
from app.domain.engines.consent_engine import ConsentEngine

#: Consent purpose keys added in REQ-031 (mirrors ``consent_engine.PURPOSES``).
AI_TENANT_DATA_ACCESS = "ai_tenant_data_access"
AI_CLOUD_PROCESSING = "ai_cloud_processing"


class ConsentGuard:
    """Checks per-user KI consent, raising :class:`ConsentRequiredError` (403)."""

    def __init__(
        self,
        consent_repo: ArangoConsentRepository,
        consent_engine: ConsentEngine | None = None,
    ) -> None:
        self._consent_repo = consent_repo
        self._consent_engine = consent_engine or ConsentEngine()

    def has_consent(self, user_key: str, purpose: str) -> bool:
        """True when the user currently grants ``purpose`` (required or opt-in)."""
        record = self._consent_repo.get_by_user_and_purpose(user_key, purpose)
        return self._consent_engine.is_processing_allowed(purpose, record)

    def require_consent(self, user_key: str, purpose: str) -> None:
        """Raise :class:`ConsentRequiredError` when ``purpose`` is not granted."""
        if not self.has_consent(user_key, purpose):
            raise ConsentRequiredError(purpose)
