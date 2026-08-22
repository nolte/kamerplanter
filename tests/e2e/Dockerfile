# axe-core is fetched in its own stage so the runtime image gains one .js file
# and no node toolchain (#1095). The version lives in tests/e2e/package.json —
# a standard manifest, so Renovate updates it and the license gate sees it, which
# a vendored axe.min.js would not give. The E2E image builds from ./tests/e2e and
# therefore cannot reach src/frontend/node_modules, which is why the dependency
# is declared here rather than borrowed from the frontend tree.
FROM node:22-slim AS axe
WORKDIR /axe
COPY package.json package-lock.json ./
RUN npm ci --omit=dev --ignore-scripts

FROM python:3.14-slim

LABEL org.opencontainers.image.title="kamerplanter-e2e-tests" \
      org.opencontainers.image.description="Kamerplanter Selenium E2E test runner" \
      org.opencontainers.image.source="https://github.com/nolte/kamerplanter" \
      org.opencontainers.image.vendor="Kamerplanter" \
      org.opencontainers.image.licenses="MIT"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

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
