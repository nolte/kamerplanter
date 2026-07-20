"""Issue #685 — public KI-Assistent availability probe (``GET /ai/status``).

Unlike the rest of the KI API, this endpoint is deliberately **not** gated by
``require_ai_feature_flag``: its whole purpose is to report the operator flag's
state so the frontend can hide the nav entry and degrade the page instead of
receiving the 404 that the feature guard raises when AI is off. No auth is
required (like ``GET /recognition/status``), so the sidebar can decide
visibility before/independently of the tenant context.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.ki_assistent.schemas import AiStatusResponse
from app.config.settings import settings

router = APIRouter(prefix="/ai", tags=["ki-assistent-status"])


@router.get("/status", response_model=AiStatusResponse)
def ai_status() -> AiStatusResponse:
    """Return whether AI features are enabled cluster-wide (operator flag).

    No authentication required. Graceful degradation: when the operator flag is
    off, ``available`` is False and the frontend hides the KI-Assistent nav
    entry and shows a "not configured" state instead of a generic error.
    """
    return AiStatusResponse(available=settings.ai_features_enabled)
