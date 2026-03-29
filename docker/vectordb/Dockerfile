FROM postgres:16-bookworm

# Install pgvector extension
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        postgresql-server-dev-16 \
        git \
        ca-certificates && \
    git clone --branch v0.8.0 https://github.com/pgvector/pgvector.git /tmp/pgvector && \
    cd /tmp/pgvector && \
    make && \
    make install && \
    apt-get purge -y build-essential postgresql-server-dev-16 git && \
    apt-get autoremove -y && \
    rm -rf /tmp/pgvector /var/lib/apt/lists/*
