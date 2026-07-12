"""REQ-036 — FastAPI dependencies for the KI diagnosis router.

The three-stage KI toggle is shared with REQ-031: stage 1 (operator flag → 404)
and stage 2 (tenant setting → 403) are reused verbatim from the KI-Assistent
guards; stage 3 (consent → 403) is enforced inside :class:`DiagnoseService`.
"""

from __future__ import annotations

from app.api.v1.ki_assistent.deps import require_ai_feature_flag, require_ai_tenant_enabled

__all__ = ["require_ai_feature_flag", "require_ai_tenant_enabled"]
