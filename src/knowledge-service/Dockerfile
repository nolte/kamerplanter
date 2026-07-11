# Multi-target image — dev and prod share one base stage.
#   prod (default, built by CI):   docker build .
#   dev  (built by skaffold):      docker build --target dev .
FROM python:3.14-slim@sha256:b877e50bd90de10af8d82c57a022fc2e0dc731c5320d762a27986facfc3355c1 AS base

LABEL org.opencontainers.image.title="kamerplanter-knowledge-service" \
      org.opencontainers.image.description="Standalone RAG/LLM service answering plant-domain questions over Kamerplanter's knowledge base" \
      org.opencontainers.image.source="https://github.com/nolte/kamerplanter" \
      org.opencontainers.image.vendor="Kamerplanter" \
      org.opencontainers.image.licenses="MIT"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --root-user-action=ignore -r requirements.txt

# ── Development target: hot-reload (skaffold dev syncs app/**/*.py) ──
FROM base AS dev
# hadolint ignore=DL3013
RUN pip install --no-cache-dir --root-user-action=ignore watchfiles
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
    CMD python -c "import socket,sys; s=socket.socket(); s.settimeout(3); sys.exit(s.connect_ex(('127.0.0.1',8000)))"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
