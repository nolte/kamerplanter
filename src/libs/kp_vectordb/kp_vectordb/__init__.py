"""Shared pgvector connection + migration infrastructure (kp_vectordb).

Single source of truth for the byte-identical connection-pool and
migration-runner code that previously lived twice under ``knowledge-service``
and ``inference-service`` (code review AP-18c / INF-D1). The service-specific
repositories (hybrid full-text search vs. embedding lookups) intentionally stay
in their respective services — only the infrastructure is deduplicated here.

The synced copies under each service's ``app/vectordb/`` are kept byte-identical
to this package via ``tests/test_vectordb_sync_guard.py`` in each service.
"""

from .config import VectorDbConfig
from .connection import VectorDbConnection
from .schema import run_migrations

__all__ = ["VectorDbConfig", "VectorDbConnection", "run_migrations"]
