import json
from dataclasses import dataclass

import structlog
from psycopg_pool import ConnectionPool

logger = structlog.get_logger(__name__)

# Knowledge YAML uses ASCII digraphs (ae/oe/ue/ss), but users type real umlauts.
# PostgreSQL German stemmer treats them differently (Blaetter→blaett vs Blätter→blatt).
# We index BOTH forms so full-text search matches regardless of input variant.
_UMLAUT_MAP = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss", "Ä": "Ae", "Ö": "Oe", "Ü": "Ue"})
_DIGRAPH_MAP = {"ae": "ä", "oe": "ö", "ue": "ü", "ss": "ß", "Ae": "Ä", "Oe": "Ö", "Ue": "Ü"}

LANG_TO_TSCONFIG: dict[str, str] = {"de": "german", "en": "english"}


def _add_umlaut_variant(text: str) -> str:
    """Return text with umlauts restored from ASCII digraphs."""
    result = text
    for digraph, umlaut in _DIGRAPH_MAP.items():
        result = result.replace(digraph, umlaut)
    return result


def _build_or_tsquery(text: str) -> str:
    """Build an OR-based tsquery string from natural language text.

    Splits text into words, adds umlaut variants, and joins with ' | '.
    This avoids the strict AND semantics of plainto_tsquery which fails
    when not all query words appear in a document.
    """
    import re

    words = re.findall(r"[a-zA-ZäöüÄÖÜßa-z]{3,}", text)  # skip short words
    terms = set()
    for w in words:
        terms.add(w)
        variant = _add_umlaut_variant(w)
        if variant != w:
            terms.add(variant)
        # Also add digraph→umlaut direction
        w_umlaut = w.translate(_UMLAUT_MAP)
        if w_umlaut != w:
            terms.add(w_umlaut)
    return " | ".join(sorted(terms)) if terms else ""


@dataclass
class VectorChunk:
    """A retrieved chunk with similarity score."""

    source_key: str
    source_type: str
    title: str
    content: str
    metadata: dict
    score: float = 0.0
    language: str = "de"


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
        language: str = "de",
        ts_config: str = "german",
    ) -> None:
        """Insert or update a vector chunk."""
        embedding_str = f"[{','.join(str(v) for v in embedding)}]"
        metadata_json = json.dumps(metadata or {})

        with self._pool.connection() as conn:
            conn.execute(
                """
                INSERT INTO ai_vector_chunks
                    (source_key, source_type, title, content, embedding, metadata,
                     language, ts_config, search_text)
                VALUES (%s, %s, %s, %s, %s::vector, %s::jsonb, %s, %s,
                        to_tsvector(%s::regconfig, %s || ' ' || %s) ||
                        to_tsvector(%s::regconfig, %s || ' ' || %s))
                ON CONFLICT (source_key) DO UPDATE SET
                    source_type = EXCLUDED.source_type,
                    title = EXCLUDED.title,
                    content = EXCLUDED.content,
                    embedding = EXCLUDED.embedding,
                    metadata = EXCLUDED.metadata,
                    language = EXCLUDED.language,
                    ts_config = EXCLUDED.ts_config,
                    search_text = EXCLUDED.search_text,
                    updated_at = NOW()
                """,
                (
                    source_key,
                    source_type,
                    title,
                    content,
                    embedding_str,
                    metadata_json,
                    language,
                    ts_config,
                    ts_config,
                    title,
                    content,
                    ts_config,
                    _add_umlaut_variant(title),
                    _add_umlaut_variant(content),
                ),
            )

    def upsert_batch(self, chunks: list[dict]) -> int:
        """Batch upsert multiple chunks. Returns count of upserted rows."""
        if not chunks:
            return 0

        with self._pool.connection() as conn:
            for chunk in chunks:
                embedding_str = f"[{','.join(str(v) for v in chunk['embedding'])}]"
                metadata_json = json.dumps(chunk.get("metadata") or {})
                language = chunk.get("language", "de")
                ts_cfg = chunk.get("ts_config", LANG_TO_TSCONFIG.get(language, "simple"))
                conn.execute(
                    """
                    INSERT INTO ai_vector_chunks
                        (source_key, source_type, title, content, embedding, metadata,
                         language, ts_config, search_text)
                    VALUES (%s, %s, %s, %s, %s::vector, %s::jsonb, %s, %s,
                            to_tsvector(%s::regconfig, %s || ' ' || %s) ||
                            to_tsvector(%s::regconfig, %s || ' ' || %s))
                    ON CONFLICT (source_key) DO UPDATE SET
                        source_type = EXCLUDED.source_type,
                        title = EXCLUDED.title,
                        content = EXCLUDED.content,
                        embedding = EXCLUDED.embedding,
                        metadata = EXCLUDED.metadata,
                        language = EXCLUDED.language,
                        ts_config = EXCLUDED.ts_config,
                        search_text = EXCLUDED.search_text,
                        updated_at = NOW()
                    """,
                    (
                        chunk["source_key"],
                        chunk["source_type"],
                        chunk["title"],
                        chunk["content"],
                        embedding_str,
                        metadata_json,
                        language,
                        ts_cfg,
                        ts_cfg,
                        chunk["title"],
                        chunk["content"],
                        ts_cfg,
                        _add_umlaut_variant(chunk["title"]),
                        _add_umlaut_variant(chunk["content"]),
                    ),
                )

        return len(chunks)

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        source_types: list[str] | None = None,
        language: str | None = None,
    ) -> list[VectorChunk]:
        """Cosine similarity search on ai_vector_chunks."""
        embedding_str = f"[{','.join(str(v) for v in query_embedding)}]"

        sql = """
            SELECT source_key, source_type, title, content, metadata,
                   1 - (embedding <=> %s::vector) AS score, language
            FROM ai_vector_chunks
        """
        params: list = [embedding_str]
        conditions: list[str] = []

        if source_types:
            placeholders = ",".join(["%s"] * len(source_types))
            conditions.append(f"source_type IN ({placeholders})")
            params.extend(source_types)

        if language and language != "all":
            conditions.append("language = %s")
            params.append(language)

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

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
                language=row[6],
            )
            for row in rows
        ]

    def hybrid_search(
        self,
        query_embedding: list[float],
        query_text: str,
        top_k: int = 5,
        source_types: list[str] | None = None,
        vector_weight: float = 0.5,
        language: str | None = None,
    ) -> list[VectorChunk]:
        """Hybrid search combining vector similarity and BM25 full-text search.

        Uses Reciprocal Rank Fusion (RRF) to merge rankings from both methods.
        RRF score = vector_weight / (k + vector_rank) + (1 - vector_weight) / (k + text_rank)
        where k = 60 (standard RRF constant).

        Args:
            query_embedding: Normalized embedding vector for the query.
            query_text: Raw query text for full-text search.
            top_k: Number of results to return.
            source_types: Optional filter on source_type.
            vector_weight: Weight for vector results in RRF (0.0-1.0).
            language: Filter chunks by language ("de", "en", or "all"/None for no filter).

        Returns:
            List of VectorChunk ordered by RRF score (descending).
        """
        embedding_str = f"[{','.join(str(v) for v in query_embedding)}]"

        # Build WHERE conditions for both CTEs
        vector_conditions: list[str] = []
        vector_params: list = []
        if source_types:
            placeholders = ",".join(["%s"] * len(source_types))
            vector_conditions.append(f"source_type IN ({placeholders})")
            vector_params.extend(source_types)
        if language and language != "all":
            vector_conditions.append("language = %s")
            vector_params.append(language)

        vector_where = ("WHERE " + " AND ".join(vector_conditions)) if vector_conditions else ""

        # Build OR-based tsquery from natural language text (both umlaut variants)
        or_query = _build_or_tsquery(query_text)
        if not or_query:
            return self.search(
                query_embedding,
                top_k=top_k,
                source_types=source_types,
                language=language,
            )

        # Select tsquery regconfig: match doc language, or 'simple' for cross-language
        query_regconfig = LANG_TO_TSCONFIG.get(language, "simple") if language and language != "all" else "german"

        # Text CTE WHERE conditions
        text_conditions = ["search_text @@ to_tsquery(%s::regconfig, %s)"]
        if source_types:
            text_conditions.append(f"source_type IN ({placeholders})")
        if language and language != "all":
            text_conditions.append("language = %s")
        text_where = "WHERE " + " AND ".join(text_conditions)

        sql = f"""
            WITH vector_results AS (
                SELECT source_key, source_type, title, content, metadata, language,
                       1 - (embedding <=> %s::vector) AS cosine_score,
                       ROW_NUMBER() OVER (ORDER BY embedding <=> %s::vector) AS vector_rank
                FROM ai_vector_chunks
                {vector_where}
                ORDER BY embedding <=> %s::vector
                LIMIT 50
            ),
            text_results AS (
                SELECT source_key, source_type, title, content, metadata, language,
                       ts_rank_cd(search_text, to_tsquery(%s::regconfig, %s)) AS text_score,
                       ROW_NUMBER() OVER (
                           ORDER BY ts_rank_cd(search_text, to_tsquery(%s::regconfig, %s)) DESC
                       ) AS text_rank
                FROM ai_vector_chunks
                {text_where}
                ORDER BY text_score DESC
                LIMIT 50
            )
            SELECT
                COALESCE(v.source_key, t.source_key) AS source_key,
                COALESCE(v.source_type, t.source_type) AS source_type,
                COALESCE(v.title, t.title) AS title,
                COALESCE(v.content, t.content) AS content,
                COALESCE(v.metadata, t.metadata) AS metadata,
                COALESCE(v.cosine_score, 0) AS cosine_score,
                (
                    %s / (60.0 + COALESCE(v.vector_rank, 51))
                    + %s / (60.0 + COALESCE(t.text_rank, 51))
                ) AS rrf_score,
                COALESCE(v.language, t.language) AS language
            FROM vector_results v
            FULL OUTER JOIN text_results t ON v.source_key = t.source_key
            ORDER BY rrf_score DESC
            LIMIT %s
        """

        # Build full params list
        full_params: list = []
        # vector CTE: embedding x3 + WHERE params
        full_params.append(embedding_str)
        full_params.append(embedding_str)
        full_params.extend(vector_params)
        full_params.append(embedding_str)
        # text CTE: ts_rank_cd (regconfig + query), ROW_NUMBER (regconfig + query), WHERE (regconfig + query)
        full_params.append(query_regconfig)
        full_params.append(or_query)
        full_params.append(query_regconfig)
        full_params.append(or_query)
        # text WHERE: tsquery match
        full_params.append(query_regconfig)
        full_params.append(or_query)
        if source_types:
            full_params.extend(source_types)
        if language and language != "all":
            full_params.append(language)
        # RRF weights
        full_params.append(vector_weight)
        full_params.append(1.0 - vector_weight)
        # LIMIT
        full_params.append(top_k)

        with self._pool.connection() as conn:
            rows = conn.execute(sql, full_params).fetchall()

        return [
            VectorChunk(
                source_key=row[0],
                source_type=row[1],
                title=row[2],
                content=row[3],
                metadata=row[4] if isinstance(row[4], dict) else {},
                score=float(row[5]),  # cosine_score for display compatibility
                language=row[7],
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
