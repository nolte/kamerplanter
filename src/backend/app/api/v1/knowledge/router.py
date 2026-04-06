"""Knowledge / RAG API endpoints -- proxies to the Knowledge Service microservice."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.v1.knowledge.schemas import (
    KnowledgeAskRequest,
    KnowledgeAskResponse,
    KnowledgeChunkResponse,
    KnowledgeSearchResponse,
)
from app.common.auth import get_current_user
from app.common.dependencies import get_knowledge_client
from app.data_access.external.knowledge_service_client import KnowledgeServiceClient

router = APIRouter(
    prefix="/knowledge",
    tags=["knowledge"],
    dependencies=[Depends(get_current_user)],
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


@router.post("/ask", response_model=KnowledgeAskResponse)
def ask_knowledge(
    body: KnowledgeAskRequest,
    client: KnowledgeServiceClient = Depends(_require_knowledge_client),
) -> KnowledgeAskResponse:
    """RAG question answering (proxied to Knowledge Service)."""
    context_dict = body.context.model_dump(exclude_none=True) if body.context else None
    data = client.ask(
        body.question,
        top_k=body.top_k,
        doc_language=body.doc_language,
        prompt_language=body.prompt_language,
        context=context_dict,
    )
    return KnowledgeAskResponse(
        answer=data["answer"],
        question_type=data.get("question_type", "factual"),
        model=data["model"],
        usage=data["usage"],
        sources=[KnowledgeChunkResponse(**s) for s in data["sources"]],
    )
