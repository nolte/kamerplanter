"""REQ-035 §3.1 — tenant-scoped glossary endpoints (``/glossary/*``).

Mounted under ``/api/v1/t/{tenant_slug}/glossary``. The endpoints are reachable
for any tenant member (viewer/grower/admin) via ``get_current_tenant``, but they
use **no** tenant data: the Knowledge-Service call runs strictly with
``context=null`` (§3.1). The tenant context is only used to enforce the REQ-031
cloud-processing consent gate when the tenant's default provider is a cloud LLM
(§6).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.v1.glossar.deps import get_glossary_service
from app.common.auth import get_current_tenant
from app.domain.models.glossary_term import (
    ExpertiseLevel,
    GlossaryTermAnswer,
    GlossaryTermSummary,
    Language,
)
from app.domain.models.tenant_context import TenantContext
from app.domain.services.glossary_service import GlossaryService

router = APIRouter(prefix="/glossary", tags=["glossary"])


@router.get("/terms", response_model=list[GlossaryTermSummary])
def list_terms(
    category: str | None = None,
    language: Language = "de",
    _ctx: TenantContext = Depends(get_current_tenant),
    service: GlossaryService = Depends(get_glossary_service),
) -> list[GlossaryTermSummary]:
    """List active glossary terms (slug + localised label + category)."""
    return service.list_terms(category=category, language=language)


@router.get("/term/{slug}", response_model=GlossaryTermAnswer)
async def get_term(
    slug: str,
    expertise: ExpertiseLevel = "beginner",
    language: Language = "de",
    ctx: TenantContext = Depends(get_current_tenant),
    service: GlossaryService = Depends(get_glossary_service),
) -> GlossaryTermAnswer:
    """Explain one term at the requested experience level (cache-first, §4.1).

    ``context=null`` at the Knowledge Service — no tenant data leaves the backend.
    ``allow_cloud=True`` merely asks the service to *evaluate* the cloud gate: a
    consent check only fires when the tenant actually has a cloud default provider
    (§6).
    """
    return await service.get_term(
        slug,
        language=language,
        expertise_level=expertise,
        tenant_key=ctx.tenant_key,
        user_key=ctx.user_key,
        allow_cloud=True,
    )
