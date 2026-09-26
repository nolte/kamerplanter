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
# stages below resolve `python` and `uvicorn` without an activation step. The
# project environment lives in /opt/venv, built by the `venv` stage below and
# copied into a runtime stage that has no uv at all (#1725).
FROM python:3.14-slim@sha256:caaf356f40667c496d405780745b9ac25771c189a51dfcc42430d531ea09f8a2 AS uv-base
COPY --from=ghcr.io/astral-sh/uv:0.12.19@sha256:04d046b13e60d6bcec73cbc5e1cad25d680dea90c8573340950a0ac2d1aef424 /uv /bin/uv
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
# THE PIN NAMES A COMMIT; THE `sha256sum -c` AFTER IT VERIFIES THE BYTES. A
# commit SHA is an instruction to the server, not a check on what came back:
# huggingface_hub verifies nothing against it, so a compromised mirror, proxy
# or CDN edge could hand over different files for the right revision and the
# build would ship them. Each stage therefore checks the sha256 of every file
# it keeps, in the same RUN, before anything leaves the layer. The expected
# values were taken on 2026-09-24 from the pinned revision and cross-checked
# against the Hub's own record of it
# (`/api/models/<repo>/revision/<sha>?blobs=true`): `lfs.sha256` for LFS files,
# the git blob id for the small ones. THE HASHES CHANGE ONLY TOGETHER WITH THE
# `revision=` LITERAL ABOVE THEM — a re-pin that does not update them fails
# here, which is the point. The guard named above also requires a
# `sha256sum -c` in the RUN of every pinned fetch.
#
# AND SO DO THE GOLDEN OUTPUTS (#1763). `golden/<target>.json` holds what
# each model computes for a few fixed inputs, taken from these bytes; the CI
# contract probe (scripts/ci/probe_model_service_contract.py) fails an image
# whose outputs leave them, which is what catches a right-shaped but wrong
# answer. A re-pin regenerates them with
# `scripts/ci/compute_model_golden_outputs.py reranker <target> <image>` (and its
# `reference-check`); src/backend/tests/unit/guards/test_model_golden_outputs_match_pins.py
# fails while a golden file names another revision or other hashes.
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
# with identical rankings. The pin is what makes that measurement stay true,
# and the six sha256 values below are that revision's bytes: change them only
# together with `revision=`.
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
    printf '%s\n' \
      'faae32b124a9d54afb7e89b5e9896e03c18a9552d56d1d6b273a709a83012486  /model/model.onnx' \
      'f009aa6c6cf21986fd7e0021fa66b20ccce27abc6900a57c7109c8496811bcbe  /model/model.onnx_data' \
      '8bf8afbfd11306bd872018c53bfdf2e160a56f8edbcf49933324404791c148d3  /model/tokenizer.json' \
      'b87c8703482b0300d3da30e201519aa641f6a450f5eb5bf1e624afbf70c74d80  /model/tokenizer_config.json' \
      '8c785abebea9ae3257b61681b4e6fd8365ceafde980c21970d001e834cf10835  /model/special_tokens_map.json' \
      '122e922dcfed6503c8721e6fe1daf090340c3d95ca7f3aa3a72730b321a51cfd  /model/config.json' \
      > /tmp/model.sha256 && \
    sha256sum -c --strict /tmp/model.sha256 && \
    rm -rf /dl /root/.cache /tmp/model.sha256

FROM dl-base AS dl-ms-marco-minilm
# cross-encoder/ms-marco-MiniLM-L12-v2 — English-focused, 33M params,
# Apache-2.0. The model author publishes the ONNX export in its own
# repository, so this one comes from the source. (`ms-marco-MiniLM-L-12-v2`,
# the id this stage used before, is the old name Hugging Face redirects to it.)
# Measured 2026-09-24 against the optimum export: identical inputs
# (`input_ids`, `attention_mask`, `token_type_ids`), byte-identical
# `tokenizer.json`, max |Δscore| 0.0. The five sha256 values below are that
# revision's bytes: change them only together with `revision=`.
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
    printf '%s\n' \
      '2ac389ab6abe08dcbddf2c41a69b6a18853e0dca440adbc2abc1adfcee46483f  /model/model.onnx' \
      'd241a60d5e8f04cc1b2b3e9ef7a4921b27bf526d9f6050ab90f9267a1f9e5c66  /model/tokenizer.json' \
      'a5c2e5a7b1a29a0702cd28c08a399b5ecc110c263009d17f7e3b415f25905fd8  /model/tokenizer_config.json' \
      '3c3507f36dff57bce437223db3b3081d1e2b52ec3e56ee55438193ecb2c94dd6  /model/special_tokens_map.json' \
      '69a745055b0307584d2903ea5cf4e1899254e511834f358be80d049918b144d8  /model/config.json' \
      > /tmp/model.sha256 && \
    sha256sum -c --strict /tmp/model.sha256 && \
    rm -rf /dl /root/.cache /tmp/model.sha256

# ── Runtime environment: built with uv, shipped without it (#1725) ──
#
# The lock is the single source of truth for what gets installed (NFR-009
# §2.3/§6.1). The environment is built HERE and only its directory is copied
# into `runtime`, so uv — a tool that can install anything — is not in the
# shipped image. It lives in /opt/venv rather than under /app because it is
# copied as a unit; like everything else in the runtime it stays owned by
# root, so the serving UID can import it and rewrite none of it. `runtime`
# starts from the SAME digest-pinned base as `uv-base`: the venv's `python`
# is a symlink to /usr/local/bin/python3 of exactly that image.

FROM uv-base AS venv
WORKDIR /src
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev

# ── Runtime base (shared across all final targets) ───────────────────

FROM python:3.14-slim@sha256:caaf356f40667c496d405780745b9ac25771c189a51dfcc42430d531ea09f8a2 AS runtime

LABEL org.opencontainers.image.title="kamerplanter-reranker-service" \
      org.opencontainers.image.description="ONNX cross-encoder reranker (BGE reranker v2 m3) that re-scores RAG retrieval hits for Kamerplanter" \
      org.opencontainers.image.source="https://github.com/nolte/kamerplanter" \
      org.opencontainers.image.vendor="Kamerplanter" \
      org.opencontainers.image.licenses="MIT"

# NO INSTALLER IN THE SHIPPED IMAGE (security review of #1725). uv never
# reaches this stage and the venv it built has no pip; the one installer left
# is the base image's own /usr/local pip — python:3.14-slim ships pip and
# nothing else (no setuptools, no wheel; measured 2026-09-24 on the digest
# above), and nothing at runtime imports it. Removed as root, before USER, with
# the interpreter named absolutely: from the ENV below on, `python` is the
# venv's, which has no pip module to uninstall with. (`ensurepip`'s bundled
# wheel stays: it is part of the standard library, and installing from it
# needs a writable site-packages that UID 1000 on a read-only root does not
# have.)
RUN /usr/local/bin/python3 -m pip uninstall --yes --root-user-action=ignore pip

# `--no-dev` leaves the `build` group out, but that does NOT keep
# huggingface-hub out of the shipped image: `tokenizers` declares it as a
# dependency of its own, so it ships transitively together with hf-xet,
# requests, fsspec and filelock. main.py never calls it — the tokenizer is
# read from `tokenizer.json` on disk — so it is dead weight here, and the
# `HF_HUB_OFFLINE=1` below turns any future accidental hub call (a
# `Tokenizer.from_pretrained`, a stray `snapshot_download`) into an error
# instead of a silent download of an unpinned model at runtime.
#
# `PYTHONDONTWRITEBYTECODE=1`: the root filesystem is read-only in the chart
# and in CI (#1725), and nothing under /app belongs to the serving UID, so
# there is nowhere to write `__pycache__` — the venv's own bytecode was
# compiled at build time (`UV_COMPILE_BYTECODE=1` in `uv-base`).
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    HF_HUB_OFFLINE=1
COPY --from=venv /opt/venv /opt/venv

WORKDIR /app
# NOTHING HERE IS OWNED BY THE SERVING UID (#1725). The code, the environment
# and (in the final targets) the model are root-owned and world-readable, so
# UID 1000 can import and read them and can rewrite none of them — before
# #1725 a `chown -R 1000:1000 /app` and `COPY --chown=1000:1000` made `main.py`
# and the ONNX graph writable by the process serving requests. The user is
# created for a name in `/etc/passwd` only; each final target switches to
# USER 1000 as its last instruction. `--chmod=0644` because ownership no longer
# grants the read: the build context's own mode bits would otherwise decide
# whether UID 1000 can import the code (a checkout under umask 077 would ship
# 0600 files and a server that cannot start).
COPY --chmod=0644 main.py limits.py ./
RUN groupadd -g 1000 app && useradd -u 1000 -g 1000 -d /app -s /usr/sbin/nologin app
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
COPY --from=dl-bge-reranker-v2-m3 /model/ /app/models/onnx/bge-reranker-v2-m3/
USER 1000

FROM runtime AS ms-marco-minilm
ENV RERANKER_MODEL=ms-marco-MiniLM-L-12-v2
COPY --from=dl-ms-marco-minilm /model/ /app/models/onnx/ms-marco-MiniLM-L-12-v2/
USER 1000
