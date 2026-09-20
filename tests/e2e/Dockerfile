# axe-core is fetched in its own stage so the runtime image gains one .js file
# and no node toolchain (#1095). The version lives in tests/e2e/package.json —
# a standard manifest, so Renovate updates it and the license gate sees it, which
# a vendored axe.min.js would not give. The E2E image builds from ./tests/e2e and
# therefore cannot reach src/frontend/node_modules, which is why the dependency
# is declared here rather than borrowed from the frontend tree.
FROM node:24-slim@sha256:0e0ff40c39bc087845bfb27465a0df4ea419520094bc35842ff83dd8cbe6f9b6 AS axe
WORKDIR /axe
COPY package.json package-lock.json ./
RUN npm ci --omit=dev --ignore-scripts

FROM python:3.14-slim@sha256:caaf356f40667c496d405780745b9ac25771c189a51dfcc42430d531ea09f8a2

LABEL org.opencontainers.image.title="kamerplanter-e2e-tests" \
      org.opencontainers.image.description="Kamerplanter Selenium E2E test runner" \
      org.opencontainers.image.source="https://github.com/nolte/kamerplanter" \
      org.opencontainers.image.vendor="Kamerplanter" \
      org.opencontainers.image.licenses="MIT"

WORKDIR /app

# uv is the lock toolchain (NFR-009 section 2.3), exactly as in
# src/backend/Dockerfile: one static binary, copied from its own digest-pinned
# image so Renovate's dockerfile manager ages it together with
# `[tool.uv].required-version` in pyproject.toml. Until #1509 this stage ran
# `pip install --no-cache-dir -r requirements.txt` against unpinned ranges, so
# the only Python install left in a BUILT image here resolved whatever PyPI
# served that minute and verified no hash. The environment pins uv to the
# interpreter this image ships (no managed-Python download, no cache layer) and
# puts the project environment on PATH, so the ENTRYPOINT resolves `pytest`
# without an activation step. It lives in /opt/venv, OUTSIDE /app, because the
# stage below chowns /app to UID 1000 and a venv inside it would end up
# writable by the test user.
COPY --from=ghcr.io/astral-sh/uv:0.12.17@sha256:10787c682e4184e4f290de1171fd4703dc63de99221f10fe1c99002ce7fa9acc /uv /bin/uv
ENV UV_PYTHON=/usr/local/bin/python3 \
    UV_PYTHON_DOWNLOADS=never \
    UV_NO_CACHE=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# The lock is the single source of truth for what gets installed; `--locked`
# verifies every artifact against its recorded hash and refuses a lock that no
# longer matches pyproject.toml.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked

COPY . .

# The bundle the a11y journey injects. Copied to a fixed path so the helper does
# not have to guess a node_modules layout that this image does not otherwise have.
COPY --from=axe /axe/node_modules/axe-core/axe.min.js /app/vendor/axe.min.js

# Run as a non-root numeric user. A mounted report/screenshot volume needs
# a matching fsGroup:1000 in the deployment to stay writable.
RUN groupadd -g 1000 app && useradd -u 1000 -g 1000 -d /app -s /usr/sbin/nologin app \
    && chown -R 1000:1000 /app
USER 1000

ENTRYPOINT ["pytest", "--tb=short", "--generate-protocol"]
