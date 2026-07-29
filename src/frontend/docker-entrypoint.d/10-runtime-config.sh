#!/bin/sh
# Generate runtime config from environment variables.
# This runs at container start, so mode can be changed without rebuilding.
#
# #777 — the error-tracking DSN is injected here rather than baked in at build
# time, for the same reason: one image serves every stage, and error tracking
# stays optional per deployment. With SENTRY_DSN unset the frontend never even
# fetches the SDK chunk.
cat <<EOF > /usr/share/nginx/html/runtime-config.js
window.__RUNTIME_CONFIG__ = {
  KAMERPLANTER_MODE: "${KAMERPLANTER_MODE:-full}",
  SENTRY_DSN: "${SENTRY_DSN:-}",
  SENTRY_ENVIRONMENT: "${SENTRY_ENVIRONMENT:-}",
  SENTRY_RELEASE: "${SENTRY_RELEASE:-}",
  SENTRY_SAMPLE_RATE: "${SENTRY_SAMPLE_RATE:-}"
};
EOF
