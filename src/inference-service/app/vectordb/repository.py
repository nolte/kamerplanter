"""Data access for the species_embeddings table (pgvector).

All queries are parameterised (never f-string interpolated) to prevent SQL
injection. The query vector is rendered into the pgvector literal form and
passed as a bind parameter cast to ::vector.
"""

from dataclasses import dataclass

import structlog
from psycopg_pool import ConnectionPool

logger = structlog.get_logger(__name__)


@dataclass
class SpeciesMatch:
    """A matched species with its best per-species cosine similarity score."""

    species_key: str
    scientific_name: str
    score: float


def _to_vector_literal(vector: list[float]) -> str:
    """Render a float list into the pgvector text literal '[v1,v2,...]'."""
    return f"[{','.join(repr(float(v)) for v in vector)}]"


class SpeciesEmbeddingRepository:
    """CRUD + nearest-neighbour search over species_embeddings."""

    def __init__(self, pool: ConnectionPool) -> None:
        self._pool = pool

    def upsert_reference(
        self,
        *,
        species_key: str,
        scientific_name: str,
        embedding: list[float],
        organ: str | None = None,
        model: str = "dinov2_vits14",
        source: str = "manual",
        source_record_id: str | None = None,
        license: str | None = None,
        attribution: str | None = None,
        source_url: str | None = None,
    ) -> None:
        """Insert or update one reference embedding (keyed by species/source/record)."""
        embedding_str = _to_vector_literal(embedding)

        with self._pool.connection() as conn:
            conn.execute(
                """
                INSERT INTO species_embeddings
                    (species_key, scientific_name, organ, embedding, model,
                     source, source_record_id, license, attribution, source_url)
                VALUES (%s, %s, %s, %s::vector, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (species_key, source, source_record_id) DO UPDATE SET
                    scientific_name = EXCLUDED.scientific_name,
                    organ           = EXCLUDED.organ,
                    embedding       = EXCLUDED.embedding,
                    model           = EXCLUDED.model,
                    license         = EXCLUDED.license,
                    attribution     = EXCLUDED.attribution,
                    source_url      = EXCLUDED.source_url,
                    indexed_at      = NOW()
                """,
                (
                    species_key,
                    scientific_name,
                    organ,
                    embedding_str,
                    model,
                    source,
                    source_record_id,
                    license,
                    attribution,
                    source_url,
                ),
            )

    def match(
        self,
        query_vector: list[float],
        k: int = 5,
        model: str | None = None,
    ) -> list[SpeciesMatch]:
        """Return the top-``k`` species by best cosine similarity to ``query_vector``.

        Aggregates per species (a species has many reference embeddings) and
        keeps the single closest reference as that species' score -- equivalent
        to the MAX(score) COLLECT pattern in REQ-029-A 5.3.
        """
        embedding_str = _to_vector_literal(query_vector)

        # Inner query computes per-row cosine similarity (1 - cosine distance);
        # outer query reduces to the best score per species.
        sql = """
            SELECT species_key, scientific_name, MAX(score) AS best_score
            FROM (
                SELECT species_key, scientific_name,
                       1 - (embedding <=> %s::vector) AS score
                FROM species_embeddings
                {model_filter}
            ) AS scored
            GROUP BY species_key, scientific_name
            ORDER BY best_score DESC
            LIMIT %s
        """

        params: list = [embedding_str]
        if model:
            sql = sql.format(model_filter="WHERE model = %s")
            params.append(model)
        else:
            sql = sql.format(model_filter="")
        params.append(k)

        with self._pool.connection() as conn:
            rows = conn.execute(sql, params).fetchall()

        return [
            SpeciesMatch(
                species_key=row[0],
                scientific_name=row[1],
                score=float(row[2]),
            )
            for row in rows
        ]

    def delete_by_species(self, species_key: str) -> int:
        """Delete all reference embeddings for a species. Returns rows deleted."""
        with self._pool.connection() as conn:
            result = conn.execute(
                "DELETE FROM species_embeddings WHERE species_key = %s",
                (species_key,),
            )
            return result.rowcount or 0

    def count(self, species_key: str | None = None) -> int:
        """Count reference embeddings, optionally for a single species."""
        if species_key:
            sql = "SELECT COUNT(*) FROM species_embeddings WHERE species_key = %s"
            params: tuple = (species_key,)
        else:
            sql = "SELECT COUNT(*) FROM species_embeddings"
            params = ()

        with self._pool.connection() as conn:
            row = conn.execute(sql, params).fetchone()
            return row[0] if row else 0
