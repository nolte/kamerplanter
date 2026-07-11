FROM postgres:18-bookworm@sha256:d9c83446333daec3f0588cc709adb80c26090b7f9f0f7ec8d43c243385d79818

LABEL org.opencontainers.image.title="kamerplanter-vectordb" \
      org.opencontainers.image.description="PostgreSQL with the pgvector extension storing Kamerplanter's embedding vectors for RAG knowledge retrieval" \
      org.opencontainers.image.source="https://github.com/nolte/kamerplanter" \
      org.opencontainers.image.vendor="Kamerplanter" \
      org.opencontainers.image.licenses="MIT"

# Install pgvector extension from source — build tools are purged after install
# hadolint ignore=DL3003,DL3008,SC2086
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        postgresql-server-dev-${PG_MAJOR} \
        git \
        ca-certificates && \
    git clone --branch v0.8.2 https://github.com/pgvector/pgvector.git /tmp/pgvector && \
    cd /tmp/pgvector && \
    make && \
    make install && \
    apt-get purge -y build-essential postgresql-server-dev-${PG_MAJOR} git && \
    apt-get autoremove -y && \
    rm -rf /tmp/pgvector /var/lib/apt/lists/*

# Run as the non-root postgres user (UID 999). The Kubernetes deployment sets
# runAsUser/runAsGroup/fsGroup:999 and PGDATA to a subdir; in Compose a fresh
# named volume inherits the image's 999-owned /var/lib/postgresql/data. A raw
# host bind mount would need a host-side chown to 999:999.
USER 999
