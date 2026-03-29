import json
from dataclasses import dataclass

import structlog
from psycopg_pool import ConnectionPool

logger = structlog.get_logger(__name__)


@dataclass
class VectorChunk:
    """A retrieved chunk with similarity score."""

    source_key: str
    source_type: str
    title: str
    content: str
    metadata: dict
    score: float = 0.0


class VectorChunkRepository:
    """Data access for ai_vector_chunks table (pgvector)."""

    def __init__(self, pool: ConnectionPool) -> None:
        self._pool = pool

    def upsert(
        self,
        source_key: str,
        source_type: str,
        title: str,
        content: str,
        embedding: list[float],
        metadata: dict | None = None,
    ) -> None:
        """Insert or update a vector chunk."""
        embedding_str = f"[{','.join(str(v) for v in embedding)}]"
        metadata_json = json.dumps(metadata or {})

        with self._pool.connection() as conn:
            conn.execute(
                """
                INSERT INTO ai_vector_chunks (source_key, source_type, title, content, embedding, metadata)
                VALUES (%s, %s, %s, %s, %s::vector, %s::jsonb)
                ON CONFLICT (source_key) DO UPDATE SET
                    source_type = EXCLUDED.source_type,
                    title = EXCLUDED.title,
                    content = EXCLUDED.content,
                    embedding = EXCLUDED.embedding,
                    metadata = EXCLUDED.metadata,
                    updated_at = NOW()
                """,
                (source_key, source_type, title, content, embedding_str, metadata_json),
            )

    def upsert_batch(self, chunks: list[dict]) -> int:
        """Batch upsert multiple chunks. Returns count of upserted rows."""
        if not chunks:
            return 0

        with self._pool.connection() as conn:
            for chunk in chunks:
                embedding_str = f"[{','.join(str(v) for v in chunk['embedding'])}]"
                metadata_json = json.dumps(chunk.get("metadata") or {})
                conn.execute(
                    """
                    INSERT INTO ai_vector_chunks (source_key, source_type, title, content, embedding, metadata)
                    VALUES (%s, %s, %s, %s, %s::vector, %s::jsonb)
                    ON CONFLICT (source_key) DO UPDATE SET
                        source_type = EXCLUDED.source_type,
                        title = EXCLUDED.title,
                        content = EXCLUDED.content,
                        embedding = EXCLUDED.embedding,
                        metadata = EXCLUDED.metadata,
                        updated_at = NOW()
                    """,
                    (
                        chunk["source_key"],
                        chunk["source_type"],
                        chunk["title"],
                        chunk["content"],
                        embedding_str,
                        metadata_json,
                    ),
                )

        return len(chunks)

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        source_types: list[str] | None = None,
    ) -> list[VectorChunk]:
        """Cosine similarity search on ai_vector_chunks."""
        embedding_str = f"[{','.join(str(v) for v in query_embedding)}]"

        sql = """
            SELECT source_key, source_type, title, content, metadata,
                   1 - (embedding <=> %s::vector) AS score
            FROM ai_vector_chunks
        """
        params: list = [embedding_str]

        if source_types:
            placeholders = ",".join(["%s"] * len(source_types))
            sql += f" WHERE source_type IN ({placeholders})"
            params.extend(source_types)

        sql += " ORDER BY embedding <=> %s::vector LIMIT %s"
        params.extend([embedding_str, top_k])

        with self._pool.connection() as conn:
            rows = conn.execute(sql, params).fetchall()

        return [
            VectorChunk(
                source_key=row[0],
                source_type=row[1],
                title=row[2],
                content=row[3],
                metadata=row[4] if isinstance(row[4], dict) else {},
                score=float(row[5]),
            )
            for row in rows
        ]

    def delete_by_source_type(self, source_type: str) -> int:
        """Delete all chunks of a given source type. Returns count."""
        with self._pool.connection() as conn:
            result = conn.execute(
                "DELETE FROM ai_vector_chunks WHERE source_type = %s",
                (source_type,),
            )
            return result.rowcount or 0

    def count(self, source_type: str | None = None) -> int:
        """Count chunks, optionally filtered by source_type."""
        if source_type:
            sql = "SELECT COUNT(*) FROM ai_vector_chunks WHERE source_type = %s"
            params: tuple = (source_type,)
        else:
            sql = "SELECT COUNT(*) FROM ai_vector_chunks"
            params = ()

        with self._pool.connection() as conn:
            row = conn.execute(sql, params).fetchone()
            return row[0] if row else 0
