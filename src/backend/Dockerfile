# Multi-target image — dev and prod share one base stage (no duplicated apt/pip
# logic, no separate Dockerfile.dev).
#   prod (default, built by CI):   docker build .
#   dev  (built by skaffold):      docker build --target dev .
FROM python:3.14-slim@sha256:cea0e6040540fb2b965b6e7fb5ffa00871e632eef63719f0ea54bca189ce14a6 AS base

LABEL org.opencontainers.image.title="kamerplanter-backend" \
      org.opencontainers.image.description="Kamerplanter core REST API and business logic (FastAPI) for plant lifecycle, phases, fertilizing, tasks and multi-tenant data" \
      org.opencontainers.image.source="https://github.com/nolte/kamerplanter" \
      org.opencontainers.image.vendor="Kamerplanter" \
      org.opencontainers.image.licenses="MIT"

WORKDIR /app

# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libglib2.0-0 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libfontconfig1 \
    libfreetype6 \
    libgdk-pixbuf-2.0-0 \
    libcairo2 \
    libffi-dev \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Copy the abstract source (pyproject.toml) and the compiled locks up front so
# the dependency-install layers are cached independently of application code.
# The locks are the single source of truth for what actually gets installed
# (NFR-009 §2.3/§6.1); pyproject.toml is only used for the app package itself.
COPY pyproject.toml requirements.txt requirements-dev.txt ./

# ── Development target: hot-reload + debugpy (skaffold dev syncs app/**/*.py) ──
# Runs as root by design; values-dev.yaml sets runAsUser:0 for the writable
# rootfs the hot-reload/__pycache__ needs.
FROM base AS dev
# Install the pinned, hash-verified dev lock, then add the app package itself as
# an editable install with --no-deps (deps already satisfied from the lock).
# Editable keeps hot-reload working while the install set stays reproducible.
# hadolint ignore=DL3013
RUN pip install --no-cache-dir debugpy \
    && pip install --no-cache-dir --require-hashes -r requirements-dev.txt \
    && pip install --no-cache-dir --no-deps -e .
COPY . .
# Own /app as UID 1000 so the non-root dev pod (values-dev runAsUser:1000) can
# hot-reload (__pycache__) and receive skaffold file-sync writes.
RUN chown -R 1000:1000 /app
ENV PYTHONUNBUFFERED=1 \
    WATCHFILES_FORCE_POLLING=true
EXPOSE 8000 5678
HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
    CMD ["curl", "-f", "http://localhost:8000/api/v1/health/live"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ── Production target (default; last stage, so CI's untargeted build picks it) ──
FROM base AS prod
# Install the exact pinned, hash-verified dependency set from the lock, then add
# the app package with --no-deps so nothing is re-resolved from PyPI. This makes
# the shipped image reproducible: two builds of the same commit install byte-for-
# byte the same wheels (NFR-009 §2.3/§6.1). Hash pinning verified feasible for
# all native wheels (weasyprint, psycopg[binary], aquacropeto) on Python 3.14.
RUN pip install --no-cache-dir --require-hashes -r requirements.txt \
    && pip install --no-cache-dir --no-deps .
COPY . .
# Run as a non-root numeric user. UID 1000 matches the deployment's
# fsGroup:1000 so the mounted attachments PVC stays writable.
RUN groupadd -g 1000 app && useradd -u 1000 -g 1000 -d /app -s /usr/sbin/nologin app \
    && chown -R 1000:1000 /app
USER 1000
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["curl", "-f", "http://localhost:8000/api/v1/health/live"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
