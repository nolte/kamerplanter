# Cross-encoder reranker service — ONNX Runtime only, no PyTorch
#
# Multi-stage build: each model downloads in a cached stage.
# Build the final image by targeting the desired model stage:
#
#   docker build --target bge-reranker-v2-m3 .   (multilingual, default)
#   docker build --target ms-marco-minilm .       (English-focused, lighter)
#
# See ADR-007 for rationale.

# ── Shared uv layer: the toolchain and the environment settings ──────
# uv is the lock toolchain (NFR-009 §2.3), exactly as in src/backend/Dockerfile:
# one static binary, copied from its own digest-pinned image so Renovate's
# dockerfile manager ages it together with `[tool.uv].required-version`. The
# environment pins uv to the interpreter this image ships (no managed-Python
# download, no cache layer) and puts the project environment on PATH, so the
# stages below resolve `python` and `uvicorn` without an activation step. It
# lives in /opt/venv, OUTSIDE /app, because the runtime stage chowns /app to
# UID 1000 and a venv inside it would end up writable by the server's UID.
FROM python:3.14-slim@sha256:caaf356f40667c496d405780745b9ac25771c189a51dfcc42430d531ea09f8a2 AS uv-base
COPY --from=ghcr.io/astral-sh/uv:0.12.18@sha256:3adc3706091ce7c2fe595e669628caedd6d951551b92b258b7e7dbe06d9440bc /uv /bin/uv
ENV UV_PYTHON=/usr/local/bin/python3 \
    UV_PYTHON_DOWNLOADS=never \
    UV_NO_CACHE=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# ── Shared base for downloads ────────────────────────────────────────

FROM uv-base AS dl-base
WORKDIR /src
COPY pyproject.toml uv.lock ./
# The download toolchain comes from the same lock as the runtime, through the
# `build` dependency group: `--only-group` installs that group alone, `--locked`
# verifies every artifact against its recorded hash.
RUN uv sync --locked --only-group build

# ── Download stages (cached independently) ───────────────────────────
#
# THE IMPORTS BELOW ARE QUALIFIED (`import x` + `x.f(...)`) RATHER THAN
# `from x import f`, AND THAT IS NOT STYLE (#1554). Renovate's dockerfile
# manager reads a CONTINUED line beginning with `from` as a `FROM`
# instruction, so every
# `from optimum.onnxruntime import ORTModelForSequenceClassification; \`
# in these `RUN python -c` bodies was extracted as an image stage: two
# phantom `optimum.onnxruntime` dependencies, each issuing a real
# `getDigest(index.docker.io, library/optimum.onnxruntime)` lookup on every
# scan. Harmless only until someone publishes that name: Renovate would then
# propose a "version bump" that rewrites a Python import statement inside a
# RUN step.
#
# Measured with Renovate 44.103.2: the same mis-read covers a heredoc body
# line, an indented continuation, an upper-case `FROM` inside a shell string
# and a continued `copy --from=`. `dockerfile_phantom_stage_lines` in
# scripts/ci/check_renovate_dashboard.py keeps all five spellings out.

FROM dl-base AS dl-bge-reranker-v2-m3
# BAAI/bge-reranker-v2-m3 — multilingual, 568M params, Apache-2.0
# Export to ONNX via optimum
# THE TOKENIZER IS SAVED BESIDE THE GRAPH, AND THAT IS THE WHOLE POINT (#1609).
#
# `ORTModelForSequenceClassification.save_pretrained()` writes `config.json`,
# `model.onnx` and `model.onnx_data` — the graph and its config, and nothing
# else. It does NOT write a tokenizer. `main.py` then calls
# `AutoTokenizer.from_pretrained()` on that directory, transformers finds no
# vocabulary, falls back to converting a slow tokenizer whose `vocab_file` is
# `None`, and dies with `AttributeError: 'NoneType' object has no attribute
# 'endswith'`. In a DAEMON thread: the process survives, `/health` keeps
# answering 200, and `/ready` is a permanent 503. The image built green for
# weeks in exactly that state.
#
# Both saves must target the same `/model`, and both must live in this one RUN:
# the runtime stage copies that directory wholesale.
RUN python -c "\
import optimum.onnxruntime; \
import transformers; \
model = optimum.onnxruntime.ORTModelForSequenceClassification.from_pretrained('BAAI/bge-reranker-v2-m3', export=True); \
model.save_pretrained('/model'); \
transformers.AutoTokenizer.from_pretrained('BAAI/bge-reranker-v2-m3').save_pretrained('/model')" && \
    rm -rf /root/.cache

FROM dl-base AS dl-ms-marco-minilm
# cross-encoder/ms-marco-MiniLM-L-12-v2 — English-focused, 33M params, Apache-2.0
RUN python -c "\
import optimum.onnxruntime; \
import transformers; \
model = optimum.onnxruntime.ORTModelForSequenceClassification.from_pretrained('cross-encoder/ms-marco-MiniLM-L-12-v2', export=True); \
model.save_pretrained('/model'); \
transformers.AutoTokenizer.from_pretrained('cross-encoder/ms-marco-MiniLM-L-12-v2').save_pretrained('/model')" && \
    rm -rf /root/.cache

# ── Runtime base (shared across all final targets) ───────────────────

FROM uv-base AS runtime

LABEL org.opencontainers.image.title="kamerplanter-reranker-service" \
      org.opencontainers.image.description="ONNX cross-encoder reranker (BGE reranker v2 m3) that re-scores RAG retrieval hits for Kamerplanter" \
      org.opencontainers.image.source="https://github.com/nolte/kamerplanter" \
      org.opencontainers.image.vendor="Kamerplanter" \
      org.opencontainers.image.licenses="MIT"

WORKDIR /app
# The lock is the single source of truth for what gets installed (NFR-009
# §2.3/§6.1); `--no-dev` leaves the export toolchain (optimum, torch) out of the
# shipped image — the runtime needs onnxruntime only.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev
COPY main.py .
# Create the non-root numeric user; each final target COPYs its model with
# --chown=1000 and switches to USER 1000 as its last instruction.
RUN groupadd -g 1000 app && useradd -u 1000 -g 1000 -d /app -s /usr/sbin/nologin app \
    && chown -R 1000:1000 /app
EXPOSE 8081
# THE HEALTHCHECK ASSERTS READINESS, NOT A SOCKET (#1609).
#
# It used to open a TCP connection to the uvicorn port, which succeeds the
# instant the server binds — long before, and quite independently of, the model
# loading. That is how an image that could never serve a request reported
# healthy for weeks. Docker has no liveness/readiness split: this is the only
# signal `docker ps`, `docker-compose --wait` and `depends_on:
# condition: service_healthy` have, so it must assert the thing that
# distinguishes a usable service from an open port.
#
# `--start-period` is generous because the model load is: a failing probe inside
# it does not count against `--retries`. Kubernetes ignores this instruction
# entirely and uses the chart's probes (helm/kamerplanter/values-dev-ki.yaml),
# which already point at this same `/ready`.
#
# `urlopen` raises on a 503, so the non-200 case exits non-zero through the
# exception rather than through the comparison.
HEALTHCHECK --interval=30s --timeout=10s --start-period=300s --retries=3 \
    CMD ["python", "-c", "import sys,urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8081/ready', timeout=8).status == 200 else 1)"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8081"]

# ── Final images (one per model, select via --target) ────────────────

FROM runtime AS bge-reranker-v2-m3
ENV RERANKER_MODEL=bge-reranker-v2-m3
COPY --from=dl-bge-reranker-v2-m3 --chown=1000:1000 /model/ /app/models/onnx/bge-reranker-v2-m3/
USER 1000

FROM runtime AS ms-marco-minilm
ENV RERANKER_MODEL=ms-marco-MiniLM-L-12-v2
COPY --from=dl-ms-marco-minilm --chown=1000:1000 /model/ /app/models/onnx/ms-marco-MiniLM-L-12-v2/
USER 1000
