"""REQ-035 §3.3 — platform-admin glossary endpoints (``/admin/glossary/*``).

Term CRUD (including inactive terms) plus cache invalidation. Platform-admin
gated. Soft-delete flips ``is_active=false`` rather than removing the term, so
existing references (REQ-006/022/009 slugs) never dangle.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.v1.glossar.deps import get_glossary_service
from app.api.v1.glossar.schemas import CacheInvalidateResponse, GlossaryTermUpsertRequest
from app.common.auth import require_platform_admin
from app.common.dependencies import get_glossary_term_repo
from app.common.exceptions import NotFoundError
from app.data_access.arango.glossary_repository import ArangoGlossaryTermRepository
from app.domain.models.glossary_term import GlossaryTerm
from app.domain.services.glossary_service import GlossaryService

router = APIRouter(
    prefix="/admin/glossary",
    tags=["glossary-admin"],
    dependencies=[Depends(require_platform_admin)],
)


def _to_term(body: GlossaryTermUpsertRequest) -> GlossaryTerm:
    return GlossaryTerm(
        slug=body.slug,
        labels=body.labels,
        long_labels=body.long_labels,
        aliases=body.aliases,
        category=body.category,
        default_expertise_level=body.default_expertise_level,
        applicable_phases=body.applicable_phases,
        related_term_slugs=body.related_term_slugs,
        fallback_text=body.fallback_text,
        rag_query_template=body.rag_query_template,
        is_active=body.is_active,
    )


@router.get("/terms", response_model=list[GlossaryTerm])
def list_terms_admin(
    category: str | None = None,
    repo: ArangoGlossaryTermRepository = Depends(get_glossary_term_repo),
) -> list[GlossaryTerm]:
    """List every term, including soft-deleted ones (§3.3)."""
    return repo.list_all_including_inactive(category=category)


@router.post("/terms", response_model=GlossaryTerm, status_code=status.HTTP_201_CREATED)
def create_term_admin(
    body: GlossaryTermUpsertRequest,
    repo: ArangoGlossaryTermRepository = Depends(get_glossary_term_repo),
) -> GlossaryTerm:
    """Create a new curated term (§3.3)."""
    return repo.create_term(_to_term(body))


@router.put("/term/{slug}", response_model=GlossaryTerm)
def update_term_admin(
    slug: str,
    body: GlossaryTermUpsertRequest,
    repo: ArangoGlossaryTermRepository = Depends(get_glossary_term_repo),
    service: GlossaryService = Depends(get_glossary_service),
) -> GlossaryTerm:
    """Edit an existing term and invalidate its cached answers (§3.3)."""
    updated = repo.update_term(slug, _to_term(body))
    service.invalidate_cache(slug)
    return updated


@router.delete("/term/{slug}", status_code=status.HTTP_204_NO_CONTENT)
def delete_term_admin(
    slug: str,
    repo: ArangoGlossaryTermRepository = Depends(get_glossary_term_repo),
    service: GlossaryService = Depends(get_glossary_service),
) -> None:
    """Soft-delete a term (``is_active=false``) and drop its cache (§3.3)."""
    if not repo.soft_delete(slug):
        raise NotFoundError("GlossaryTerm", slug)
    service.invalidate_cache(slug)


@router.post("/term/{slug}/cache/invalidate", response_model=CacheInvalidateResponse)
def invalidate_term_cache(
    slug: str,
    service: GlossaryService = Depends(get_glossary_service),
) -> CacheInvalidateResponse:
    """Invalidate the cache for one term (e.g. after a KB reingest, §3.3)."""
    return CacheInvalidateResponse(removed=service.invalidate_cache(slug))


@router.post("/cache/invalidate-all", response_model=CacheInvalidateResponse)
def invalidate_all_cache(
    service: GlossaryService = Depends(get_glossary_service),
) -> CacheInvalidateResponse:
    """Invalidate the entire glossary cache (§3.3)."""
    return CacheInvalidateResponse(removed=service.invalidate_cache(None))
