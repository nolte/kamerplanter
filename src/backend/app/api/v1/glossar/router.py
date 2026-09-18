"""REQ-035 §3.1 — tenant-scoped glossary endpoints (``/glossary/*``).

Mounted under ``/api/v1/t/{tenant_slug}/glossary``. The endpoints are reachable
for any tenant member (viewer/grower/admin) via ``get_current_tenant``, but they
use **no** tenant data: the Knowledge-Service call runs strictly with
``context=null`` (§3.1). The tenant context is only used to enforce the REQ-031
cloud-processing consent gate when the tenant's default provider is a cloud LLM
(§6).

The router is intentionally **not** gated by ``require_ai_feature_flag``: the
term list and the editorial fallback text need no AI/RAG stack and must stay
usable when ``ai_features_enabled`` is off (default). Only the on-demand RAG
explanation requires the operator flag, which is enforced inside
:class:`~app.domain.services.glossary_service.GlossaryService` at the RAG-call
boundary (#684). With the flag off, ``/term/{slug}`` degrades to the curated
fallback text (``is_fallback=true``) instead of returning 404.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.api.v1.glossar.deps import get_glossary_service
from app.common.auth import get_current_tenant, require_permission
from app.core.permissions import Action, ResourceType
from app.domain.models.glossary_term import (
    ExpertiseLevel,
    GlossaryTermAnswer,
    GlossaryTermSummary,
    Language,
)
from app.domain.models.tenant_context import TenantContext
from app.domain.services.glossary_service import GlossaryService

router = APIRouter(
    prefix="/glossary",
    tags=["glossary"],
)


@router.get("/terms", response_model=list[GlossaryTermSummary])
def list_terms(
    category: str | None = Query(None, description="Filter terms by category."),
    language: Language = Query("de", description="Language of the returned term labels (de or en)."),
    _ctx: TenantContext = Depends(get_current_tenant),
    service: GlossaryService = Depends(get_glossary_service),
) -> list[GlossaryTermSummary]:
    """List active glossary terms (slug + localised label + category)."""
    return service.list_terms(category=category, language=language)


@router.get("/term/{slug}", response_model=GlossaryTermAnswer)
def get_term(
    slug: Annotated[str, Path(description="Slug identifier of the glossary term.")],
    expertise: ExpertiseLevel = Query("beginner", description="Experience level the explanation targets."),
    language: Language = Query("de", description="Language of the returned explanation (de or en)."),
    _ctx: TenantContext = Depends(get_current_tenant),
    service: GlossaryService = Depends(get_glossary_service),
) -> GlossaryTermAnswer:
    """Explain one term at the requested experience level (§4.1) — a **read**.

    The tenant-scoped sibling of the public route and the same answer: cached RAG
    explanation, or the curated editorial short definition. It does not generate
    and does not write (#1460); ``POST …/generate`` below is what does.
    """
    return service.get_term(slug, language=language, expertise_level=expertise)


@router.post("/term/{slug}/generate", response_model=GlossaryTermAnswer)
async def generate_term(
    slug: Annotated[str, Path(description="Slug identifier of the glossary term.")],
    expertise: ExpertiseLevel = Query("beginner", description="Experience level the explanation targets."),
    language: Language = Query("de", description="Language of the returned explanation (de or en)."),
    ctx: TenantContext = Depends(require_permission(ResourceType.GLOSSARY, Action.CREATE)),
    service: GlossaryService = Depends(get_glossary_service),
) -> GlossaryTermAnswer:
    """Ask the Knowledge Service for this term's explanation and cache it (§4.1).

    The write half of the pair above (#1460). Gated on the domain role because it
    spends an LLM call on the installation's behalf; idempotent while a cached
    entry is still valid, so a second request is not a second call.

    ``context=null`` at the Knowledge Service — no tenant data leaves the backend.
    ``allow_cloud=True`` merely asks the service to *evaluate* the cloud gate: a
    consent check only fires when the tenant actually has a cloud default provider
    (§6). That gate lives here rather than on the read for the same reason the LLM
    call does — with no call there is no cloud processing to consent to.
    """
    return await service.generate_term(
        slug,
        language=language,
        expertise_level=expertise,
        tenant_key=ctx.tenant_key,
        user_key=ctx.user_key,
        allow_cloud=True,
    )
