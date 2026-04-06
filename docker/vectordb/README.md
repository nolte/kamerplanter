# VectorDB

PostgreSQL 18 with pgvector extension for vector similarity search in the Kamerplanter Knowledge API.

## Purpose

Provides the vector store for RAG (Retrieval-Augmented Generation). The embedding service generates vectors from knowledge documents; this database stores and queries them using pgvector's indexing and distance operators.

## What's Included

- PostgreSQL 18 (Debian Bookworm)
- [pgvector](https://github.com/pgvector/pgvector) v0.8.2 — compiled from source, build tools purged after install

## Usage

```bash
docker build -t kamerplanter-vectordb .
docker run -p 5432:5432 -e POSTGRES_PASSWORD=secret kamerplanter-vectordb
```

Enable the extension in your database:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

> **Note:** In production this image is built and deployed via Skaffold/Helm, not manually.
