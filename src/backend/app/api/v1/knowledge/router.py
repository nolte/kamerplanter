"""Knowledge / RAG API endpoints -- proxies to the Knowledge Service microservice.

Search only. The question-answering route that used to live here
(``POST /api/v1/knowledge/ask``) put an LLM call behind nothing but a login: no
KI toggle, no consent, no daily budget (#2175). It is now
``POST /api/v1/t/{tenant_slug}/ai/knowledge/ask`` on the KI-Assistent tenant
router, behind the same admission as every other generating KI route.
``GET /knowledge/search`` runs no language model and stays here.
"""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.v1.knowledge.schemas import (
    KnowledgeChunkResponse,
    KnowledgeSearchResponse,
)
from app.common.auth import get_current_user
from app.common.dependencies import get_knowledge_client
from app.common.openapi_responses import AUTH_RESPONSES
from app.data_access.external.knowledge_service_client import KnowledgeServiceClient

router = APIRouter(
    prefix="/knowledge",
    tags=["knowledge"],
    dependencies=[Depends(get_current_user)],
    responses=AUTH_RESPONSES,
)


def _require_knowledge_client(
    client: KnowledgeServiceClient | None = Depends(get_knowledge_client),
) -> KnowledgeServiceClient:
    """Dependency that returns 503 when the knowledge service is unavailable."""
    if client is None:
        raise HTTPException(
            status_code=503,
            detail="Knowledge service is not available.",
        )
    return client


@router.get("/search", response_model=KnowledgeSearchResponse)
def search_knowledge(
    q: str = Query(min_length=1, max_length=500, description="Search query"),
    top_k: int = Query(default=5, ge=1, le=50, description="Number of results"),
    doc_language: Literal["de", "en", "all"] | None = Query(
        default=None,
        description="Filter chunks by language. None uses server default.",
    ),
    client: KnowledgeServiceClient = Depends(_require_knowledge_client),
) -> KnowledgeSearchResponse:
    """Semantic search over the knowledge base (proxied to Knowledge Service)."""
    data = client.search(q, top_k=top_k, doc_language=doc_language)
    return KnowledgeSearchResponse(
        query=data["query"],
        results=[KnowledgeChunkResponse(**r) for r in data["results"]],
        total=data["total"],
        doc_language=data.get("doc_language"),
    )
