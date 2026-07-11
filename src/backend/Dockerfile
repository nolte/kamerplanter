# Multi-target image — dev and prod share one base stage (no duplicated apt/pip
# logic, no separate Dockerfile.dev).
#   prod (default, built by CI):   docker build .
#   dev  (built by skaffold):      docker build --target dev .
FROM python:3.14-slim@sha256:b877e50bd90de10af8d82c57a022fc2e0dc731c5320d762a27986facfc3355c1 AS base

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

COPY pyproject.toml .

# ── Development target: hot-reload + debugpy (skaffold dev syncs app/**/*.py) ──
# Runs as root by design; values-dev.yaml sets runAsUser:0 for the writable
# rootfs the hot-reload/__pycache__ needs.
FROM base AS dev
# hadolint ignore=DL3013
RUN pip install --no-cache-dir debugpy && pip install --no-cache-dir -e ".[dev]"
COPY . .
# Own /app as UID 1000 so the non-root dev pod (values-dev runAsUser:1000) can
# hot-reload (__pycache__) and receive skaffold file-sync writes.
RUN chown -R 1000:1000 /app
ENV PYTHONUNBUFFERED=1 \
    WATCHFILES_FORCE_POLLING=true
EXPOSE 8000 5678
HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
    CMD curl -f http://localhost:8000/api/v1/health/live || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ── Production target (default; last stage, so CI's untargeted build picks it) ──
FROM base AS prod
RUN pip install --no-cache-dir .
COPY . .
# Run as a non-root numeric user. UID 1000 matches the deployment's
# fsGroup:1000 so the mounted attachments PVC stays writable.
RUN groupadd -g 1000 app && useradd -u 1000 -g 1000 -d /app -s /usr/sbin/nologin app \
    && chown -R 1000:1000 /app
USER 1000
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health/live || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
