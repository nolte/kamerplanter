"""Knowledge Service -- standalone microservice for RAG-based plant knowledge."""

from contextlib import asynccontextmanager
from typing import Literal

import structlog
from fastapi import FastAPI, HTTPException, Query

from app.config import settings
from app.embedding import EmbeddingEngine
from app.ingestor import KnowledgeIngestor
from app.llm import create_llm_adapter
from app.prompt_engine import PromptEngine
from app.reranker import RerankerEngine
from app.schemas import (
    AskRequest,
    AskResponse,
    ClassifyRequest,
    ClassifyResponse,
    IngestResponse,
    KnowledgeChunkResponse,
    SearchResponse,
)
from app.service import KnowledgeService
from app.vectordb.connection import VectorDbConnection
from app.vectordb.schema import ensure_vectordb_schema

logger = structlog.get_logger(__name__)

_service: KnowledgeService | None = None
_ingestor: KnowledgeIngestor | None = None
_vec_conn: VectorDbConnection | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: connect to vectordb, build components, and cleanup on shutdown."""
    global _service, _ingestor, _vec_conn

    # Connect to VectorDB
    _vec_conn = VectorDbConnection(settings)
    pool = _vec_conn.connect()
    ensure_vectordb_schema(pool)
    logger.info("vectordb_ready")

    # Build components
    embedding_engine = EmbeddingEngine(
        service_url=settings.embedding_service_url,
        model_name=settings.embedding_model,
    )
    from app.vectordb.repository import VectorChunkRepository

    chunk_repo = VectorChunkRepository(pool)
    llm_adapter = create_llm_adapter(settings)
    prompt_engine = PromptEngine()

    reranker = RerankerEngine(settings.reranker_url or None)
    if reranker.available:
        logger.info("reranker_enabled", url=settings.reranker_url)
    else:
        logger.info("reranker_disabled")

    _service = KnowledgeService(
        embedding_engine=embedding_engine,
        chunk_repo=chunk_repo,
        llm_adapter=llm_adapter,
        prompt_engine=prompt_engine,
        reranker=reranker,
        reranker_initial_k=settings.reranker_initial_k,
        reranker_top_k=settings.reranker_top_k,
        max_tokens=settings.llm_max_tokens,
        temperature=settings.llm_temperature,
        default_doc_language=settings.rag_doc_language,
        default_prompt_language=settings.rag_prompt_language,
    )

    _ingestor = KnowledgeIngestor(
        embedding_engine=embedding_engine,
        chunk_repo=chunk_repo,
        knowledge_path=settings.knowledge_path,
    )

    logger.info(
        "knowledge_service_ready",
        llm_provider=settings.llm_provider,
        llm_model=settings.llm_model,
    )

    yield

    # Shutdown
    if _vec_conn:
        _vec_conn.close()
    logger.info("knowledge_service_shutdown")


app = FastAPI(
    title="Kamerplanter Knowledge Service",
    description="RAG-based plant knowledge assistant",
    version="1.0.0",
    lifespan=lifespan,
)


def _require_service() -> KnowledgeService:
    """Return the singleton KnowledgeService or raise 503."""
    if _service is None:
        raise HTTPException(status_code=503, detail="Knowledge service not initialized.")
    return _service


def _require_ingestor() -> KnowledgeIngestor:
    """Return the singleton KnowledgeIngestor or raise 503."""
    if _ingestor is None:
        raise HTTPException(status_code=503, detail="Knowledge ingestor not initialized.")
    return _ingestor


@app.get("/health")
def health() -> dict:
    """Liveness probe -- always responds, reports vectordb connectivity."""
    ready = _vec_conn is not None and _vec_conn.is_connected()
    return {"status": "ok" if ready else "degraded", "ready": ready}


@app.get("/ready")
def ready() -> dict:
    """Readiness probe -- returns 503 if service is not fully initialized."""
    if _service is None or _vec_conn is None or not _vec_conn.is_connected():
        raise HTTPException(status_code=503, detail="Not ready")
    return {"status": "ok"}


@app.get("/search", response_model=SearchResponse)
def search(
    q: str = Query(min_length=1, max_length=500),
    top_k: int = Query(default=5, ge=1, le=50),
    doc_language: Literal["de", "en", "all"] | None = Query(default=None),
) -> SearchResponse:
    """Semantic search over the knowledge base."""
    service = _require_service()
    chunks = service.search(q, top_k=top_k, doc_language=doc_language)
    return SearchResponse(
        query=q,
        results=[
            KnowledgeChunkResponse(
                source_key=c.source_key,
                source_type=c.source_type,
                title=c.title,
                content=c.content,
                score=c.score,
                metadata=c.metadata,
                language=c.language,
            )
            for c in chunks
        ],
        total=len(chunks),
        doc_language=doc_language,
    )


@app.post("/ask", response_model=AskResponse)
def ask(body: AskRequest) -> AskResponse:
    """RAG question answering -- retrieves context and generates an LLM answer."""
    service = _require_service()
    context_dict = body.context.model_dump(exclude_none=True) if body.context else None
    answer = service.ask(
        body.question,
        top_k=body.top_k,
        doc_language=body.doc_language,
        prompt_language=body.prompt_language,
        context=context_dict,
    )
    return AskResponse(
        answer=answer.answer,
        question_type=answer.question_type,
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
                language=c.language,
            )
            for c in answer.sources
        ],
    )


@app.post("/classify", response_model=ClassifyResponse)
def classify(body: ClassifyRequest) -> ClassifyResponse:
    """Classify a question into diagnosis, howto, or factual."""
    engine = PromptEngine()
    q_type = engine.classify(body.question)
    return ClassifyResponse(question_type=q_type)


@app.post("/ingest", response_model=IngestResponse)
def ingest() -> IngestResponse:
    """Trigger re-indexing of knowledge YAML files."""
    ingestor = _require_ingestor()
    result = ingestor.ingest_all()
    return IngestResponse(**result)
