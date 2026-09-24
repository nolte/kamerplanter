# Cross-encoder reranker service — ONNX Runtime only, no PyTorch
#
# Multi-stage build: each model downloads, already exported to ONNX and pinned
# to a commit, in a cached stage.
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
# NOTHING IS EXPORTED HERE ANY MORE (#1480). Each stage downloads a graph that
# is already ONNX, plus the tokenizer files, and arranges them in /model the
# way main.py reads them: `model.onnx` (and, for bge, `model.onnx_data`, the
# external-weights file the graph references by RELATIVE name, so the two must
# stay in one directory), `tokenizer.json`, `tokenizer_config.json` (main.py
# reads `pad_token` from it), `special_tokens_map.json` and `config.json`.
#
# These stages used to export with optimum (`ORTModelForSequenceClassification
# .from_pretrained(..., export=True)`), which dragged torch and transformers
# into the build group — and optimum-onnx, the exporter since optimum 2.0,
# caps transformers below 4.58 in every release it has published, holding the
# whole lock on a line with three HIGH CVEs. Downloading the exported graph
# needs `huggingface-hub` and nothing else.
#
# EVERY FETCH IS PINNED TO A COMMIT SHA, AND RENOVATE WILL NOT BUMP IT — BY
# DESIGN. A Hugging Face repository is mutable: a branch name like `main` can
# be force-pushed to a different graph, and a different graph is a different
# ranking, silently. A model change must therefore be a reviewed diff of a
# `revision=` literal, with the parity measurement below repeated for it.
# src/backend/tests/unit/guards/test_hf_model_fetches_pin_a_revision.py fails
# on any Hugging Face fetch in a docker/**/Dockerfile that does not carry one.
#
# Each `mv` names its file explicitly, so a revision that stops carrying one of
# them fails the build here instead of producing an image that cannot become
# ready (#1609); `/dl` (including huggingface_hub's `.cache/` bookkeeping
# inside `local_dir`) is dropped in the same layer.
#
# THE IMPORTS BELOW ARE QUALIFIED (`import x` + `x.f(...)`) RATHER THAN
# `from x import f`, AND THAT IS NOT STYLE (#1554). Renovate's dockerfile
# manager reads a CONTINUED line beginning with `from` as a `FROM`
# instruction, so a
# `from huggingface_hub import snapshot_download; \`
# in these `RUN python -c` bodies would be extracted as an image stage: a
# phantom `huggingface_hub` dependency issuing a real
# `getDigest(index.docker.io, library/huggingface_hub)` lookup on every scan.
# Harmless only until someone publishes that name: Renovate would then propose
# a "version bump" that rewrites a Python import statement inside a RUN step.
#
# Measured with Renovate 44.103.2: the same mis-read covers a heredoc body
# line, an indented continuation, an upper-case `FROM` inside a shell string
# and a continued `copy --from=`. `dockerfile_phantom_stage_lines` in
# scripts/ci/check_renovate_dashboard.py keeps all five spellings out.

FROM dl-base AS dl-bge-reranker-v2-m3
# BAAI/bge-reranker-v2-m3 — multilingual, 568M params, Apache-2.0.
#
# Fetched from `onnx-community/bge-reranker-v2-m3-ONNX`, which is NOT the model
# author: it is Hugging Face's community export of BAAI's weights (its card
# declares no licence of its own; the weights are BAAI's Apache-2.0). That is
# acceptable because of what was measured before switching, 2026-09-24,
# against the optimum export this stage used to run: identical graph inputs
# (`input_ids`, `attention_mask`) and output (`logits`), a byte-identical
# `tokenizer.json`, and over 3 queries x 7 documents a max |Δscore| of 4.7e-6
# with identical rankings. The pin is what makes that measurement stay true.
RUN python -c "\
import huggingface_hub; \
huggingface_hub.snapshot_download(\
repo_id='onnx-community/bge-reranker-v2-m3-ONNX', \
revision='6f5ff65298512715a1e669753bc754d2bc8f367b', \
allow_patterns=['onnx/model.onnx', 'onnx/model.onnx_data', 'tokenizer.json', 'tokenizer_config.json', 'special_tokens_map.json', 'config.json'], \
local_dir='/dl')" && \
    mkdir /model && \
    mv /dl/onnx/model.onnx /dl/onnx/model.onnx_data \
       /dl/tokenizer.json /dl/tokenizer_config.json /dl/special_tokens_map.json /dl/config.json \
       /model/ && \
    rm -rf /dl /root/.cache

FROM dl-base AS dl-ms-marco-minilm
# cross-encoder/ms-marco-MiniLM-L12-v2 — English-focused, 33M params,
# Apache-2.0. The model author publishes the ONNX export in its own
# repository, so this one comes from the source. (`ms-marco-MiniLM-L-12-v2`,
# the id this stage used before, is the old name Hugging Face redirects to it.)
# Measured 2026-09-24 against the optimum export: identical inputs
# (`input_ids`, `attention_mask`, `token_type_ids`), byte-identical
# `tokenizer.json`, max |Δscore| 0.0.
RUN python -c "\
import huggingface_hub; \
huggingface_hub.snapshot_download(\
repo_id='cross-encoder/ms-marco-MiniLM-L12-v2', \
revision='7b0235231ca2674cb8ca8f022859a6eba2b1c968', \
allow_patterns=['onnx/model.onnx', 'tokenizer.json', 'tokenizer_config.json', 'special_tokens_map.json', 'config.json'], \
local_dir='/dl')" && \
    mkdir /model && \
    mv /dl/onnx/model.onnx \
       /dl/tokenizer.json /dl/tokenizer_config.json /dl/special_tokens_map.json /dl/config.json \
       /model/ && \
    rm -rf /dl /root/.cache

# ── Runtime base (shared across all final targets) ───────────────────

FROM uv-base AS runtime

LABEL org.opencontainers.image.title="kamerplanter-reranker-service" \
      org.opencontainers.image.description="ONNX cross-encoder reranker (BGE reranker v2 m3) that re-scores RAG retrieval hits for Kamerplanter" \
      org.opencontainers.image.source="https://github.com/nolte/kamerplanter" \
      org.opencontainers.image.vendor="Kamerplanter" \
      org.opencontainers.image.licenses="MIT"

WORKDIR /app
# The lock is the single source of truth for what gets installed (NFR-009
# §2.3/§6.1). `--no-dev` leaves the `build` group out, but that does NOT keep
# huggingface-hub out of the shipped image: `tokenizers` declares it as a
# dependency of its own, so it ships transitively together with hf-xet,
# requests, fsspec and filelock. main.py never calls it — the tokenizer is
# read from `tokenizer.json` on disk — so it is dead weight here, and the
# `HF_HUB_OFFLINE=1` below turns any future accidental hub call (a
# `Tokenizer.from_pretrained`, a stray `snapshot_download`) into an error
# instead of a silent download of an unpinned model at runtime.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev
ENV HF_HUB_OFFLINE=1
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
