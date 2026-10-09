"""REQ-031 §4.3 — ``FeatureGuard`` for stage 2 of the KI feature toggle.

Stage 1 (operator flag ``AI_FEATURES_ENABLED``) is enforced at the router
boundary as a plain 404 — this guard covers stage 2 (per-tenant setting). Pure
logic over an already-loaded :class:`~app.domain.models.ai_assistant.
AiTenantSettings`; no I/O.
"""

from __future__ import annotations

from app.common.exceptions import AiDisabledError
from app.domain.models.ai_assistant import AiTenantSettings
from app.domain.models.tenant import TenantSettings


class FeatureGuard:
    """Decides whether KI features are enabled for a tenant (stage 2)."""

    @staticmethod
    def extract_settings(tenant_settings: TenantSettings | dict | None) -> AiTenantSettings:
        """Read the ``ai_*`` block from a tenant ``settings`` sub-object.

        Missing keys fall back to the safe defaults (all off), so a tenant that
        never opted in stays KI-free out of the box (§1.3). The values are the
        typed :class:`TenantSettings` fields (MT-056) — a stored ``"false"`` is
        off, not ``bool("false")``; a plain dict (a document read raw) is
        validated through the same model.
        """
        typed = (
            tenant_settings
            if isinstance(tenant_settings, TenantSettings)
            else TenantSettings.model_validate(tenant_settings or {})
        )
        return AiTenantSettings(
            ai_features_enabled=typed.ai_features_enabled,
            ai_default_provider_key=typed.ai_default_provider_key,
            ai_allow_cloud_providers=typed.ai_allow_cloud_providers,
            ai_daily_tip_enabled=typed.ai_daily_tip_enabled,
        )

    @classmethod
    def require_ai_enabled(cls, tenant_settings: TenantSettings | dict | None) -> AiTenantSettings:
        """Return the parsed settings or raise :class:`AiDisabledError` (403).

        Raises the stable ``ai.disabled_for_tenant`` marker when the tenant admin
        has not turned KI on (stage 2 of the toggle).
        """
        settings = cls.extract_settings(tenant_settings)
        if not settings.ai_features_enabled:
            raise AiDisabledError()
        return settings
