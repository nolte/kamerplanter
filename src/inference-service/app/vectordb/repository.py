"""Data access for the species_embeddings table (pgvector).

All queries are parameterised (never f-string interpolated) to prevent SQL
injection. The query vector is rendered into the pgvector literal form and
passed as a bind parameter cast to ::vector.
"""

from dataclasses import dataclass
from datetime import UTC, datetime

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
        is_active: bool = True,
        contributed_by: str | None = None,
        tenant_key: str | None = None,
    ) -> None:
        """Insert or update one reference embedding (keyed by species/source/record).

        ``is_active`` controls whether the row participates in ``/match``: the
        license-clean acquisition pipeline indexes active rows (default), while
        interactive user contributions (SEC-001, issue #447) are written
        quarantined (``is_active=False``) and only enter recognition after a
        platform admin activates them. ``contributed_by`` / ``tenant_key`` carry
        the provenance needed for GDPR erasure (SEC-005). On a repeat upsert of
        the same (species, source, record) the curation flag and the original
        provenance are **preserved** — a re-submission never silently
        re-activates a row an admin has already deselected/rejected.
        """
        embedding_str = _to_vector_literal(embedding)
        contributed_at = datetime.now(tz=UTC) if contributed_by is not None else None

        with self._pool.connection() as conn:
            conn.execute(
                """
                INSERT INTO species_embeddings
                    (species_key, scientific_name, organ, embedding, model,
                     source, source_record_id, license, attribution, source_url,
                     is_active, contributed_by, tenant_key, contributed_at)
                VALUES (%s, %s, %s, %s::vector, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s)
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
                    is_active,
                    contributed_by,
                    tenant_key,
                    contributed_at,
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

        Manually excluded reference images (``is_active = FALSE``) are never
        considered, so a deselected bad image can no longer skew the result.
        """
        embedding_str = _to_vector_literal(query_vector)

        # Inner query computes per-row cosine similarity (1 - cosine distance);
        # outer query reduces to the best score per species. ``is_active`` is
        # always enforced so curated-out images drop out of every match.
        sql = """
            SELECT species_key, scientific_name, MAX(score) AS best_score
            FROM (
                SELECT species_key, scientific_name,
                       1 - (embedding <=> %s::vector) AS score
                FROM species_embeddings
                WHERE is_active = TRUE {model_filter}
            ) AS scored
            GROUP BY species_key, scientific_name
            ORDER BY best_score DESC
            LIMIT %s
        """

        params: list = [embedding_str]
        if model:
            sql = sql.format(model_filter="AND model = %s")
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

    def list_by_species(
        self,
        species_key: str,
        limit: int = 50,
        *,
        active_only: bool = False,
    ) -> list[dict]:
        """Return the stored reference image provenance for a species.

        Only rows that actually carry a ``source_url`` are returned (manually
        upserted embeddings without provenance are not displayable). Used by the
        UI gallery; embeddings themselves are never returned. ``id`` and the
        curation flags (``is_active``, ``exclusion_reason``) are returned so the
        admin gallery can drive per-image deselection.

        When ``active_only`` is set, excluded images are omitted entirely -- used
        for the public gallery so end users never see deselected images.
        """
        active_filter = "AND is_active = TRUE" if active_only else ""
        sql = f"""
            SELECT id, source_url, license, attribution, organ, source,
                   source_record_id, is_active, exclusion_reason
            FROM species_embeddings
            WHERE species_key = %s AND source_url IS NOT NULL AND source_url <> ''
                  {active_filter}
            ORDER BY indexed_at DESC
            LIMIT %s
        """
        with self._pool.connection() as conn:
            rows = conn.execute(sql, (species_key, limit)).fetchall()
        return [
            {
                "id": row[0],
                "source_url": row[1],
                "license": row[2],
                "attribution": row[3],
                "organ": row[4],
                "source": row[5],
                "source_record_id": row[6],
                "is_active": row[7],
                "exclusion_reason": row[8],
            }
            for row in rows
        ]

    def set_active(
        self,
        species_key: str,
        embedding_id: int,
        *,
        is_active: bool,
        reason: str | None = None,
    ) -> bool:
        """Activate/deactivate one reference embedding (manual curation).

        Deactivating (``is_active=False``) stores ``reason`` so the audit trail
        records why the image was deselected; reactivating clears it. Returns
        ``True`` when a matching row was updated, ``False`` otherwise (unknown
        id / species mismatch).
        """
        sql = """
            UPDATE species_embeddings
            SET is_active        = %s,
                exclusion_reason = %s,
                marked_at        = NOW()
            WHERE id = %s AND species_key = %s
        """
        stored_reason = reason if not is_active else None
        with self._pool.connection() as conn:
            result = conn.execute(sql, (is_active, stored_reason, embedding_id, species_key))
            return (result.rowcount or 0) > 0

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
