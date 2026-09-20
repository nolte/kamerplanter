# Multi-target image — dev and prod share one base stage.
#   prod (default, built by CI):   docker build .
#   dev  (built by skaffold):      docker build --target dev .
FROM python:3.14-slim@sha256:caaf356f40667c496d405780745b9ac25771c189a51dfcc42430d531ea09f8a2 AS base

LABEL org.opencontainers.image.title="kamerplanter-knowledge-service" \
      org.opencontainers.image.description="Standalone RAG/LLM service answering plant-domain questions over Kamerplanter's knowledge base" \
      org.opencontainers.image.source="https://github.com/nolte/kamerplanter" \
      org.opencontainers.image.vendor="Kamerplanter" \
      org.opencontainers.image.licenses="MIT"

WORKDIR /app

# uv is the lock toolchain (NFR-009 §2.3), exactly as in src/backend/Dockerfile:
# one static binary, copied from its own digest-pinned image so Renovate's
# dockerfile manager ages it together with `[tool.uv].required-version`. The
# environment lives in /opt/venv, OUTSIDE /app, because the stages below
# `chown -R 1000:1000 /app` and a venv under /app would be copied into that
# layer and left writable by the UID the server runs as.
COPY --from=ghcr.io/astral-sh/uv:0.12.17@sha256:10787c682e4184e4f290de1171fd4703dc63de99221f10fe1c99002ce7fa9acc /uv /bin/uv
ENV UV_PYTHON=/usr/local/bin/python3 \
    UV_PYTHON_DOWNLOADS=never \
    UV_NO_CACHE=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# The lock is the single source of truth for what gets installed (NFR-009
# §2.3/§6.1): `--locked` verifies it against pyproject.toml and every artifact
# against its recorded hash, so a stale lock or a tampered wheel fails the build
# instead of installing something else. Copied before the source so the install
# layer is cached independently of application code.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

# ── Development target: hot-reload (skaffold dev syncs app/**/*.py) ──
FROM base AS dev
# The `dev` dependency group adds watchfiles (the reload watcher) from the same
# lock — it used to be an unpinned `pip install` outside any lock.
RUN uv sync --locked --no-install-project
COPY app/ ./app/
# Own /app as UID 1000 for the non-root dev pod (hot-reload + skaffold sync).
RUN chown -R 1000:1000 /app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ── Production target (default; last stage) ──
FROM base AS prod
COPY app/ ./app/
# Run as a non-root numeric user.
RUN groupadd -g 1000 app && useradd -u 1000 -g 1000 -d /app -s /usr/sbin/nologin app \
    && chown -R 1000:1000 /app
USER 1000
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD ["python", "-c", "import socket,sys; s=socket.socket(); s.settimeout(3); sys.exit(s.connect_ex(('127.0.0.1',8000)))"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
