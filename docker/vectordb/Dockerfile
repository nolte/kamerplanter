FROM postgres:17-bookworm

LABEL org.opencontainers.image.title="kamerplanter-vectordb" \
      org.opencontainers.image.description="PostgreSQL with pgvector extension for Kamerplanter RAG embeddings" \
      org.opencontainers.image.source="https://github.com/nolte/kamerplanter" \
      org.opencontainers.image.vendor="Kamerplanter" \
      org.opencontainers.image.licenses="UNLICENSED"

# Install pgvector extension from source — build tools are purged after install
# hadolint ignore=DL3003,DL3008
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        postgresql-server-dev-17 \
        git \
        ca-certificates && \
    git clone --branch v0.8.0 https://github.com/pgvector/pgvector.git /tmp/pgvector && \
    cd /tmp/pgvector && \
    make && \
    make install && \
    apt-get purge -y build-essential postgresql-server-dev-17 git && \
    apt-get autoremove -y && \
    rm -rf /tmp/pgvector /var/lib/apt/lists/*
