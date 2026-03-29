import structlog

from app.tasks import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(
    name="app.tasks.vector_indexing_tasks.reindex_vector_chunks",
    bind=True,
    max_retries=1,
    default_retry_delay=1800,
)
def reindex_vector_chunks(self) -> dict:
    """Reindex the vector database with knowledge YAML files.

    Reads all YAML files from the knowledge directory, generates
    embeddings via the external embedding service, and upserts into pgvector.
    Runs weekly via Celery beat.
    """
    from app.common.dependencies import get_vectordb_connection
    from app.config.settings import settings
    from app.data_access.vectordb.vector_chunk_repository import VectorChunkRepository
    from app.domain.engines.embedding_engine import EmbeddingEngine
    from app.domain.engines.knowledge_ingestor import KnowledgeIngestor

    vec_conn = get_vectordb_connection()
    if not vec_conn:
        logger.warning("reindex_skipped_vectordb_not_available")
        return {"status": "skipped", "reason": "vectordb_not_available"}

    chunk_repo = VectorChunkRepository(vec_conn.pool)
    embedding_engine = EmbeddingEngine(
        service_url=settings.embedding_service_url,
        model_name=settings.embedding_model,
    )
    ingestor = KnowledgeIngestor(
        embedding_engine=embedding_engine,
        chunk_repo=chunk_repo,
        knowledge_path=settings.knowledge_path,
    )

    result = ingestor.ingest_all()
    logger.info("reindex_vector_chunks_done", **result)
    return result
