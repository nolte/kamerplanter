"""REQ-035 §3.2 — light-mode public glossary endpoints (``/public/glossary/*``).

No auth, no tenant, strictly ``context=null`` at the Knowledge Service and always
the local default provider (no cloud, no consent, §6). IP rate-limited via the
shared app limiter: 30/min for a single term, 10/min for the term list (§6).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.api.v1.auth.router import limiter
from app.api.v1.glossar.deps import get_glossary_service
from app.api.v1.ki_assistent.deps import require_ai_feature_flag
from app.domain.models.glossary_term import (
    ExpertiseLevel,
    GlossaryTermAnswer,
    GlossaryTermSummary,
    Language,
)
from app.domain.services.glossary_service import GlossaryService

router = APIRouter(
    prefix="/public/glossary",
    tags=["glossary-public"],
    dependencies=[Depends(require_ai_feature_flag)],
)

_TERM_RATE_LIMIT = "30/minute"
_TERMS_RATE_LIMIT = "10/minute"


@router.get("/terms", response_model=list[GlossaryTermSummary])
@limiter.limit(_TERMS_RATE_LIMIT)
def public_list_terms(
    request: Request,
    category: str | None = None,
    language: Language = "de",
    service: GlossaryService = Depends(get_glossary_service),
) -> list[GlossaryTermSummary]:
    """List active glossary terms without auth (§3.2)."""
    return service.list_terms(category=category, language=language)


@router.get("/term/{slug}", response_model=GlossaryTermAnswer)
@limiter.limit(_TERM_RATE_LIMIT)
async def public_get_term(
    request: Request,
    slug: str,
    expertise: ExpertiseLevel = "beginner",
    language: Language = "de",
    service: GlossaryService = Depends(get_glossary_service),
) -> GlossaryTermAnswer:
    """Explain one term without auth (local provider only, §3.2, §6)."""
    return await service.get_term(slug, language=language, expertise_level=expertise)
