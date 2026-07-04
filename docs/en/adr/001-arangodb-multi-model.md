# ADR-001: ArangoDB as Multi-Model Database

**Status:** Accepted
**Date:** 2026-01-15
**Deciders:** Kamerplanter Development Team

## Context

Kamerplanter manages both structured entity data (plants, nutrient plans, tasks) and complex graph relations (companion planting compatibility, genetic lineage, crop rotation). A database was needed that handles both requirements without operating two separate systems.

## Decision

ArangoDB 3.11+ is used as the primary database. It natively supports both document storage and graph traversals. Both use a single query language: AQL — ArangoDB Query Language.

## Rationale

### Evaluated Alternatives

| Criterion | PostgreSQL + pgvector | Neo4j | ArangoDB |
|-----------|----------------------|-------|----------|
| Document storage | Good (JSONB) | Poor (properties only) | Very good |
| Graph traversal | Medium (recursive CTEs) | Very good (Cypher) | Very good (AQL) |
| Operational complexity | Low | High (enterprise costs) | Medium |
| Python client | Very good (psycopg3) | Good | Good (python-arango) |
| License | PostgreSQL (open) | Community/Enterprise | Apache 2.0 |

ArangoDB offers the best balance of document storage and native graph support. It does so without enterprise license costs.

## Consequences

### Positive
- Single database for all data types
- Native AQL graph traversals for companion plant graph and lineage tree
- Named graph `kamerplanter_graph` as central abstraction layer

### Negative
- AQL is less widespread than SQL or Cypher — smaller talent pool
- TimescaleDB is additionally required for time-series sensor data

### Risks
- ArangoDB Community Edition has limitations for cluster features. This is sufficient for single-node operation.

## References

- [ArangoDB Documentation](https://docs.arangodb.com/)
- NFR-001: 5-Layer Architecture
