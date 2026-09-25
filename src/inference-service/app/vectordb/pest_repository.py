"""Data access for the pest_embeddings table (REQ-044 few-shot prototypes).

Parallel to SpeciesEmbeddingRepository but for pest/symptom/beneficial
prototypes (frozen DINOv2 few-shot, REQ-044 §3.2 / WP-3.4). All queries are
parameterised; the query vector is cast to ::vector as a bind parameter.
"""

from dataclasses import dataclass

import structlog
from psycopg_pool import ConnectionPool

from app.vectordb.repository import require_erasure_key

logger = structlog.get_logger(__name__)

#: How a promoted pest-image contribution is recorded (backend
#: ``app/tasks/pest_image_tasks.py``): ``source_record_id`` is the contribution
#: key, ``source_url`` is ``contribution://<tenant key>/<contribution key>``.
CONTRIBUTION_URL_SCHEME = "contribution://"

# Static statements: the source filter is part of the text, so no caller can
# drop or widen it; the keys are always bind parameters (#1759).
_DELETE_CONTRIBUTIONS_SQL = (
    "DELETE FROM pest_embeddings WHERE source = 'user_contributed' AND source_record_id = ANY(%s)"
)
# ``starts_with`` and not ``LIKE``: a tenant key may contain ``%`` or ``_``.
_DELETE_TENANT_CONTRIBUTIONS_SQL = (
    "DELETE FROM pest_embeddings WHERE source = 'user_contributed' AND starts_with(source_url, %s)"
)


def tenant_contribution_prefix(tenant_key: str | None) -> str:
    """The ``source_url`` prefix of one tenant's contributions, or refuse the key.

    A blank key would widen to every tenant's rows; a key with a ``/`` could
    reach into another tenant's prefix. Shared with the test fake.
    """
    key = require_erasure_key("tenant_key", tenant_key)
    if "/" in key:
        msg = "tenant_key must not contain '/'; refusing an unscoped erasure"
        raise ValueError(msg)
    return f"{CONTRIBUTION_URL_SCHEME}{key}/"


#: Upper bound of keys per erase request; the backend sends batches below it.
MAX_CONTRIBUTION_KEYS = 1000


def require_contribution_keys(contribution_keys: list[str] | None) -> list[str]:
    """Return the keys unchanged, or refuse an empty/oversized list or a blank key.

    The size check lives here and not as a schema ``max_length``: FastAPI's 422
    for a schema violation echoes the input, and the input is a list of keys.
    """
    if not contribution_keys:
        msg = "contribution_keys must name at least one contribution; refusing an unscoped erasure"
        raise ValueError(msg)
    if len(contribution_keys) > MAX_CONTRIBUTION_KEYS:
        msg = f"contribution_keys holds more than {MAX_CONTRIBUTION_KEYS} keys; send them in batches"
        raise ValueError(msg)
    for key in contribution_keys:
        require_erasure_key("contribution_keys[]", key)
    return list(contribution_keys)


@dataclass
class PestMatch:
    """A matched pest/symptom/beneficial class with its best cosine score."""

    label: str
    category: str
    score: float


def _to_vector_literal(vector: list[float]) -> str:
    return f"[{','.join(repr(float(v)) for v in vector)}]"


class PestEmbeddingRepository:
    """CRUD + nearest-neighbour classification over pest_embeddings."""

    def __init__(self, pool: ConnectionPool) -> None:
        self._pool = pool

    def upsert_prototype(
        self,
        *,
        label: str,
        category: str,
        embedding: list[float],
        model: str = "dinov2_vits14",
        source: str = "manual",
        source_record_id: str | None = None,
        license: str | None = None,
        attribution: str | None = None,
        source_url: str | None = None,
    ) -> None:
        """Insert or update one prototype embedding (keyed by label/source/record)."""
        embedding_str = _to_vector_literal(embedding)
        with self._pool.connection() as conn:
            conn.execute(
                """
                INSERT INTO pest_embeddings
                    (label, category, embedding, model, source,
                     source_record_id, license, attribution, source_url)
                VALUES (%s, %s, %s::vector, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (label, source, source_record_id) DO UPDATE SET
                    category    = EXCLUDED.category,
                    embedding   = EXCLUDED.embedding,
                    model       = EXCLUDED.model,
                    license     = EXCLUDED.license,
                    attribution = EXCLUDED.attribution,
                    source_url  = EXCLUDED.source_url,
                    indexed_at  = NOW()
                """,
                (
                    label,
                    category,
                    embedding_str,
                    model,
                    source,
                    source_record_id,
                    license,
                    attribution,
                    source_url,
                ),
            )

    def classify(
        self,
        query_vector: list[float],
        k: int = 5,
        model: str | None = None,
    ) -> list[PestMatch]:
        """Return the top-``k`` classes by best cosine similarity (per-label MAX).

        Excluded prototypes (``is_active = FALSE``) are never considered.
        """
        embedding_str = _to_vector_literal(query_vector)
        sql = """
            SELECT label, category, MAX(score) AS best_score
            FROM (
                SELECT label, category,
                       1 - (embedding <=> %s::vector) AS score
                FROM pest_embeddings
                WHERE is_active = TRUE {model_filter}
            ) AS scored
            GROUP BY label, category
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
        return [PestMatch(label=row[0], category=row[1], score=float(row[2])) for row in rows]

    def list_by_label(self, label: str, limit: int = 200, *, active_only: bool = False) -> list[dict]:
        """Return stored prototype provenance for a class (gallery source).

        Only rows carrying a ``source_url`` are returned; embeddings are never
        returned. ``is_active`` / ``exclusion_reason`` drive the admin curation.
        """
        active_filter = "AND is_active = TRUE" if active_only else ""
        sql = f"""
            SELECT id, source_url, license, attribution, source,
                   source_record_id, is_active, exclusion_reason
            FROM pest_embeddings
            WHERE label = %s AND source_url IS NOT NULL AND source_url <> ''
                  {active_filter}
            ORDER BY indexed_at DESC
            LIMIT %s
        """
        with self._pool.connection() as conn:
            rows = conn.execute(sql, (label, limit)).fetchall()
        return [
            {
                "id": row[0],
                "source_url": row[1],
                "license": row[2],
                "attribution": row[3],
                "source": row[4],
                "source_record_id": row[5],
                "is_active": row[6],
                "exclusion_reason": row[7],
            }
            for row in rows
        ]

    def set_active(self, label: str, prototype_id: int, *, is_active: bool, reason: str | None = None) -> bool:
        """Activate/deactivate one prototype (manual curation). Returns True if updated."""
        sql = """
            UPDATE pest_embeddings
            SET is_active = %s, exclusion_reason = %s, marked_at = NOW()
            WHERE id = %s AND label = %s
        """
        stored_reason = reason if not is_active else None
        with self._pool.connection() as conn:
            result = conn.execute(sql, (is_active, stored_reason, prototype_id, label))
            return (result.rowcount or 0) > 0

    def coverage(self) -> list[dict]:
        """Per-class prototype counts (total + active), highest first."""
        sql = """
            SELECT label, category,
                   COUNT(*) AS total,
                   COUNT(*) FILTER (WHERE is_active) AS active
            FROM pest_embeddings
            GROUP BY label, category
            ORDER BY active DESC, total DESC
        """
        with self._pool.connection() as conn:
            rows = conn.execute(sql).fetchall()
        return [{"label": r[0], "category": r[1], "total": r[2], "active": r[3]} for r in rows]

    def delete_by_label(self, label: str) -> int:
        """Delete all prototypes for a class. Returns rows deleted."""
        with self._pool.connection() as conn:
            result = conn.execute("DELETE FROM pest_embeddings WHERE label = %s", (label,))
            return result.rowcount or 0

    def delete_contributions(self, contribution_keys: list[str]) -> int:
        """REQ-025 Art. 17 — delete the prototypes indexed from these contributions (#1759).

        Removes every row with ``source = 'user_contributed'`` whose
        ``source_record_id`` is one of *contribution_keys*, active or
        deactivated (a demoted contribution keeps a deactivated row). Rows of
        any other source are never touched. Returns the number deleted.

        Raises:
            ValueError: the list is empty or holds a blank key.
        """
        keys = require_contribution_keys(contribution_keys)
        with self._pool.connection() as conn:
            deleted = conn.execute(_DELETE_CONTRIBUTIONS_SQL, (keys,)).rowcount or 0
        logger.info("pest_contributions_deleted", scope="contributions", deleted=deleted)
        return deleted

    def delete_tenant_contributions(self, tenant_key: str) -> int:
        """REQ-024 / REQ-025 — delete every prototype contributed within a tenant (#1759).

        Matches ``source = 'user_contributed'`` rows whose ``source_url`` starts
        with ``contribution://<tenant_key>/`` — which also reaches a row whose
        contribution document is already gone. Returns the number deleted.

        Raises:
            ValueError: ``tenant_key`` is blank or contains ``/``.
        """
        prefix = tenant_contribution_prefix(tenant_key)
        with self._pool.connection() as conn:
            deleted = conn.execute(_DELETE_TENANT_CONTRIBUTIONS_SQL, (prefix,)).rowcount or 0
        logger.info("pest_contributions_deleted", scope="tenant", deleted=deleted)
        return deleted

    def count(self, label: str | None = None) -> int:
        """Count prototypes, optionally for a single class."""
        if label:
            sql = "SELECT COUNT(*) FROM pest_embeddings WHERE label = %s"
            params: tuple = (label,)
        else:
            sql = "SELECT COUNT(*) FROM pest_embeddings"
            params = ()
        with self._pool.connection() as conn:
            row = conn.execute(sql, params).fetchone()
            return row[0] if row else 0
