# Lightweight embedding service — ONNX Runtime only, no PyTorch
#
# Multi-stage build: each model downloads, already exported to ONNX, pinned to
# a commit and sha256-verified (#1724), in a cached stage.
# Build the final image by targeting the desired model stage:
#
#   docker build --target e5-base .    (768 dim, default)
#   docker build --target e5-small .   (384 dim, fast)
#   docker build --target e5-large .   (1024 dim, best quality)
#   docker build --target minilm .     (384 dim, baseline)
#
# See ADR-006 for rationale.

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
# Each stage downloads a graph that is already ONNX, plus the tokenizer files,
# and arranges them flat in /model the way main.py reads them: `model.onnx`
# (and, for e5-large, `model.onnx_data`), `tokenizer.json`,
# `tokenizer_config.json`, `special_tokens_map.json`, `sentencepiece.bpe.model`
# (the e5 models only) and `config.json`.
#
# EVERY FETCH IS PINNED TO A COMMIT SHA, AND RENOVATE WILL NOT BUMP IT — BY
# DESIGN (#1724, following the reranker's #1480). These stages used to fetch
# whatever `main` of each repository pointed at on the day of the build. A
# Hugging Face repository is mutable: a branch can be force-pushed to a
# different graph, and a different graph is different vectors — which, against
# an index built with the old ones, is silently worse retrieval, not an error.
# A model change must therefore be a reviewed diff of a `revision=` literal
# (and a re-index). Each pin is the revision the unpinned image downloaded on
# 2026-09-24 — `main` as resolved that day — so pinning is meant to change no
# byte of what ships; each stage records the parity measured for that claim.
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
# `scripts/ci/compute_model_golden_outputs.py embedding <target> <image>` (and its
# `reference-check`); src/backend/tests/unit/guards/test_model_golden_outputs_match_pins.py
# fails while a golden file names another revision or other hashes.
#
# THE IMPORTS BELOW ARE QUALIFIED (`import x` + `x.f(...)`) RATHER THAN
# `from x import f`, AND THAT IS NOT STYLE (#1554). Renovate's dockerfile
# manager reads a CONTINUED line beginning with `from` as a `FROM`
# instruction, so every `from huggingface_hub import snapshot_download; \`
# in these `RUN python -c` bodies was extracted as an image stage: four
# phantom `huggingface_hub` dependencies — one of them typed `final` — each
# issuing a real `getDigest(index.docker.io, library/huggingface_hub)`
# lookup on every scan. Harmless only until someone publishes that name:
# Renovate would then propose a "version bump" that rewrites a Python import
# statement inside a RUN step.
#
# Measured with Renovate 44.103.2: the same mis-read covers a heredoc body
# line, an indented continuation, an upper-case `FROM` inside a shell string
# and a continued `copy --from=`. `dockerfile_phantom_stage_lines` in
# scripts/ci/check_renovate_dashboard.py keeps all five spellings out.

FROM dl-base AS dl-e5-small
# intfloat/multilingual-e5-small — 384 dim, 118M params, MIT. Fetched from the
# model author's own repository, which publishes the ONNX export.
#
# The pin is the revision today's (formerly unpinned) image downloaded:
# `main` of this repository as resolved on 2026-09-24 (#1724).
# Parity measured 2026-09-24 against the unpinned image: every kept file byte-identical (sha256),
# and embeddings for 7 fixed inputs identical (max |delta| 0.0) through the same
# tokenizer + ONNX Runtime path.
# The six sha256 values below are that revision's bytes: change them only
# together with `revision=`.
RUN python -c "\
import huggingface_hub; \
huggingface_hub.snapshot_download(\
repo_id='intfloat/multilingual-e5-small', \
revision='614241f622f53c4eeff9890bdc4f31cfecc418b3', \
allow_patterns=['onnx/model.onnx', 'tokenizer.json', 'tokenizer_config.json', 'special_tokens_map.json', 'sentencepiece.bpe.model', 'config.json'], \
local_dir='/dl')" && \
    mkdir /model && \
    mv /dl/onnx/model.onnx \
       /dl/tokenizer.json /dl/tokenizer_config.json /dl/special_tokens_map.json /dl/sentencepiece.bpe.model /dl/config.json \
       /model/ && \
    printf '%s\n' \
      'ca456c06b3a9505ddfd9131408916dd79290368331e7d76bb621f1cba6bc8665  /model/model.onnx' \
      '0b44a9d7b51c3c62626640cda0e2c2f70fdacdc25bbbd68038369d14ebdf4c39  /model/tokenizer.json' \
      'a1d6bc8734a6f635dc158508bef000f8e2e5a759c7d92f984b2c86e5ff53425b  /model/tokenizer_config.json' \
      'd05497f1da52c5e09554c0cd874037a083e1dc1b9cfd48034d1c717f1afc07a7  /model/special_tokens_map.json' \
      'cfc8146abe2a0488e9e2a0c56de7952f7c11ab059eca145a0a727afce0db2865  /model/sentencepiece.bpe.model' \
      '69137736cab8b8903a07fe8afaafdda25aac55415a12a55d1bffa9f581abf959  /model/config.json' \
      > /tmp/model.sha256 && \
    sha256sum -c --strict /tmp/model.sha256 && \
    rm -rf /dl /root/.cache /tmp/model.sha256

FROM dl-base AS dl-e5-base
# intfloat/multilingual-e5-base — 768 dim, 278M params, MIT. Fetched from the
# model author's own repository, which publishes the ONNX export.
#
# The pin is the revision today's (formerly unpinned) image downloaded:
# `main` of this repository as resolved on 2026-09-24 (#1724).
# Parity measured 2026-09-24 against the unpinned image: every kept file byte-identical (sha256),
# and embeddings for 7 fixed inputs identical (max |delta| 0.0) through the same
# tokenizer + ONNX Runtime path.
# The six sha256 values below are that revision's bytes: change them only
# together with `revision=`.
RUN python -c "\
import huggingface_hub; \
huggingface_hub.snapshot_download(\
repo_id='intfloat/multilingual-e5-base', \
revision='d128750597153bb5987e10b1c3493a34e5a4502a', \
allow_patterns=['onnx/model.onnx', 'tokenizer.json', 'tokenizer_config.json', 'special_tokens_map.json', 'sentencepiece.bpe.model', 'config.json'], \
local_dir='/dl')" && \
    mkdir /model && \
    mv /dl/onnx/model.onnx \
       /dl/tokenizer.json /dl/tokenizer_config.json /dl/special_tokens_map.json /dl/sentencepiece.bpe.model /dl/config.json \
       /model/ && \
    printf '%s\n' \
      '84a4d426f7e87a6bf5bf195f0bae2c4a7d15f675b23ca96f42fab8326d7a77aa  /model/model.onnx' \
      '62c24cdc13d4c9952d63718d6c9fa4c287974249e16b7ade6d5a85e7bbb75626  /model/tokenizer.json' \
      'efb5c0d09722e5fe59a462cd2a9976ee216d55b037597d997cd3fe833216da15  /model/tokenizer_config.json' \
      '06e405a36dfe4b9604f484f6a1e619af1a7f7d09e34a8555eb0b77b66318067f  /model/special_tokens_map.json' \
      'cfc8146abe2a0488e9e2a0c56de7952f7c11ab059eca145a0a727afce0db2865  /model/sentencepiece.bpe.model' \
      '9dab198f24c8c0879e481cf7822005d5ecbceedbacb390ffafa594e28d31bac4  /model/config.json' \
      > /tmp/model.sha256 && \
    sha256sum -c --strict /tmp/model.sha256 && \
    rm -rf /dl /root/.cache /tmp/model.sha256

FROM dl-base AS dl-e5-large
# intfloat/multilingual-e5-large — 1024 dim, 560M params, MIT. Fetched from the
# model author's own repository, which publishes the ONNX export. The graph
# keeps its weights in `model.onnx_data`, referenced by RELATIVE name from
# `model.onnx`, so the two must stay in one directory. The file exists at the
# pinned revision, so its `mv` is explicit: a revision without it fails here.
#
# The pin is the revision today's (formerly unpinned) image downloaded:
# `main` of this repository as resolved on 2026-09-24 (#1724).
# Parity measured 2026-09-24 against the unpinned image: every kept file byte-identical (sha256),
# and embeddings for 7 fixed inputs identical (max |delta| 0.0) through the same
# tokenizer + ONNX Runtime path.
# The seven sha256 values below are that revision's bytes: change them only
# together with `revision=`.
RUN python -c "\
import huggingface_hub; \
huggingface_hub.snapshot_download(\
repo_id='intfloat/multilingual-e5-large', \
revision='3d7cfbdacd47fdda877c5cd8a79fbcc4f2a574f3', \
allow_patterns=['onnx/model.onnx', 'onnx/model.onnx_data', 'tokenizer.json', 'tokenizer_config.json', 'special_tokens_map.json', 'sentencepiece.bpe.model', 'config.json'], \
local_dir='/dl')" && \
    mkdir /model && \
    mv /dl/onnx/model.onnx /dl/onnx/model.onnx_data \
       /dl/tokenizer.json /dl/tokenizer_config.json /dl/special_tokens_map.json /dl/sentencepiece.bpe.model /dl/config.json \
       /model/ && \
    printf '%s\n' \
      'bb5a52503a3ef35247f5b5ae6c473aaae60505dd3ffaef56d7b69e2f84683c05  /model/model.onnx' \
      '0cf1883fee81c63819a44e2ba0efa51d4043d9759685a4ebebbde97e0623d15c  /model/model.onnx_data' \
      '62c24cdc13d4c9952d63718d6c9fa4c287974249e16b7ade6d5a85e7bbb75626  /model/tokenizer.json' \
      'efb5c0d09722e5fe59a462cd2a9976ee216d55b037597d997cd3fe833216da15  /model/tokenizer_config.json' \
      '06e405a36dfe4b9604f484f6a1e619af1a7f7d09e34a8555eb0b77b66318067f  /model/special_tokens_map.json' \
      'cfc8146abe2a0488e9e2a0c56de7952f7c11ab059eca145a0a727afce0db2865  /model/sentencepiece.bpe.model' \
      'e42d98d0c211928d788467aa951000391017f647c76ca8ce2ef6dd8d0c9ce5ca  /model/config.json' \
      > /tmp/model.sha256 && \
    sha256sum -c --strict /tmp/model.sha256 && \
    rm -rf /dl /root/.cache /tmp/model.sha256

FROM dl-base AS dl-minilm
# sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 — 384 dim,
# 118M params, Apache-2.0.
#
# Fetched from `Xenova/paraphrase-multilingual-MiniLM-L12-v2`, which is NOT
# the model author: it is a THIRD-PARTY ONNX export of sentence-transformers'
# weights (made for transformers.js). That is what this stage has always
# downloaded; the pin freezes that export at the revision the image shipped,
# so a re-export pushed to its `main` cannot change the vectors silently. The
# repository carries no sentencepiece file — the tokenizer is `tokenizer.json`.
#
# The pin is the revision today's (formerly unpinned) image downloaded:
# `main` of this repository as resolved on 2026-09-24 (#1724).
# Parity measured 2026-09-24 against the unpinned image: every kept file byte-identical (sha256),
# and embeddings for 7 fixed inputs identical (max |delta| 0.0) through the same
# tokenizer + ONNX Runtime path.
# The five sha256 values below are that revision's bytes: change them only
# together with `revision=`.
RUN python -c "\
import huggingface_hub; \
huggingface_hub.snapshot_download(\
repo_id='Xenova/paraphrase-multilingual-MiniLM-L12-v2', \
revision='2c4055b12046f11709e9df2c122e59ffbdc2f900', \
allow_patterns=['onnx/model.onnx', 'tokenizer.json', 'tokenizer_config.json', 'special_tokens_map.json', 'config.json'], \
local_dir='/dl')" && \
    mkdir /model && \
    mv /dl/onnx/model.onnx \
       /dl/tokenizer.json /dl/tokenizer_config.json /dl/special_tokens_map.json /dl/config.json \
       /model/ && \
    printf '%s\n' \
      '185ae63f47e17a7e8d30d0e6a3cde6a6e4b79bc5b81666ecffc279a6856ca113  /model/model.onnx' \
      'b60b6b43406a48bf3638526314f3d232d97058bc93472ff2de930d43686fa441  /model/tokenizer.json' \
      '3f5961b9ac86288cccdb97f32fb848d6187c78e1603958c53f3ea1f296b7d8a2  /model/tokenizer_config.json' \
      '06e405a36dfe4b9604f484f6a1e619af1a7f7d09e34a8555eb0b77b66318067f  /model/special_tokens_map.json' \
      '05b570bff786faa5c4604152aa16f19f77ed6dfc31e47dd0f3dd987078693ac7  /model/config.json' \
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

LABEL org.opencontainers.image.title="kamerplanter-embedding-service" \
      org.opencontainers.image.description="ONNX multilingual text-embedding service turning knowledge and queries into vectors for Kamerplanter's RAG pipeline" \
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

# `--no-dev` leaves the `build` group out, but huggingface-hub still ships:
# `tokenizers` depends on it (uv.lock, #1752 — transformers, which used to pull
# it in as well, is gone). main.py never fetches — `tokenization.load_tokenizer`
# reads `tokenizer.json` from the model directory on disk — and
# `HF_HUB_OFFLINE=1` turns any future accidental hub call (a `from_pretrained`
# of a hub id, a stray `snapshot_download`) into an error instead of a silent
# download of an unpinned model at runtime.
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
COPY --chmod=0644 main.py limits.py feed.py tokenization.py ./
RUN groupadd -g 1000 app && useradd -u 1000 -g 1000 -d /app -s /usr/sbin/nologin app
EXPOSE 8080
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
    CMD ["python", "-c", "import sys,urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/ready', timeout=8).status == 200 else 1)"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

# ── Final images (one per model, select via --target) ────────────────

FROM runtime AS e5-small
ENV EMBEDDING_MODEL=multilingual-e5-small
COPY --from=dl-e5-small /model/ /app/models/onnx/multilingual-e5-small/
USER 1000

FROM runtime AS e5-base
ENV EMBEDDING_MODEL=multilingual-e5-base
COPY --from=dl-e5-base /model/ /app/models/onnx/multilingual-e5-base/
USER 1000

FROM runtime AS e5-large
ENV EMBEDDING_MODEL=multilingual-e5-large
COPY --from=dl-e5-large /model/ /app/models/onnx/multilingual-e5-large/
USER 1000

FROM runtime AS minilm
ENV EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2
COPY --from=dl-minilm /model/ /app/models/onnx/paraphrase-multilingual-MiniLM-L12-v2/
USER 1000
