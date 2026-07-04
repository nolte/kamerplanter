"""Shared VectorDB configuration for the pgvector connection pool.

Decoupled from any service-specific settings object so the same infrastructure
module can be shared verbatim across knowledge-service and inference-service
(code review AP-18c / INF-D1). There is deliberately no password default:
callers must supply every field explicitly from their own configuration.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VectorDbConfig:
    """Immutable connection parameters for the pgvector database."""

    host: str
    port: int
    database: str
    username: str
    password: str
    pool_min_size: int
    pool_max_size: int
