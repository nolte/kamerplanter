"""Knowledge / RAG API endpoints — semantic search and question answering."""

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.v1.knowledge.schemas import (
    KnowledgeAskRequest,
    KnowledgeAskResponse,
    KnowledgeChunkResponse,
    KnowledgeSearchResponse,
)
from app.common.dependencies import get_knowledge_service
from app.domain.services.knowledge_service import KnowledgeService

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


def _require_knowledge_service(
    service: KnowledgeService | None = Depends(get_knowledge_service),
) -> KnowledgeService:
    """Dependency that returns 503 when the knowledge service is unavailable."""
    if service is None:
        raise HTTPException(
            status_code=503,
            detail="Knowledge service is not available. VectorDB is not enabled.",
        )
    return service


@router.get("/search", response_model=KnowledgeSearchResponse)
def search_knowledge(
    q: str = Query(min_length=1, max_length=500, description="Search query"),
    top_k: int = Query(default=5, ge=1, le=50, description="Number of results"),
    service: KnowledgeService = Depends(_require_knowledge_service),
) -> KnowledgeSearchResponse:
    """Semantic search over the knowledge base.

    Embeds the query and returns the most similar chunks from the vector store.
    Does not require authentication — knowledge base is publicly accessible.
    """
    chunks = service.search(q, top_k=top_k)
    return KnowledgeSearchResponse(
        query=q,
        results=[
            KnowledgeChunkResponse(
                source_key=c.source_key,
                source_type=c.source_type,
                title=c.title,
                content=c.content,
                score=c.score,
                metadata=c.metadata,
            )
            for c in chunks
        ],
        total=len(chunks),
    )


@router.post("/ask", response_model=KnowledgeAskResponse)
def ask_knowledge(
    body: KnowledgeAskRequest,
    service: KnowledgeService = Depends(_require_knowledge_service),
) -> KnowledgeAskResponse:
    """RAG question answering — retrieves context and generates an LLM answer.

    Embeds the question, retrieves relevant chunks, builds a context prompt,
    and sends it to the configured LLM provider. Does not require authentication.
    """
    answer = service.ask(body.question, top_k=body.top_k)
    return KnowledgeAskResponse(
        answer=answer.answer,
        model=answer.model,
        usage=answer.usage,
        sources=[
            KnowledgeChunkResponse(
                source_key=c.source_key,
                source_type=c.source_type,
                title=c.title,
                content=c.content,
                score=c.score,
                metadata=c.metadata,
            )
            for c in answer.sources
        ],
    )
