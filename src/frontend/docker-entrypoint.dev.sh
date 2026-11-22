#!/bin/sh
# Generate runtime-config.js from environment variables (same as production entrypoint)
cat > /app/public/runtime-config.js <<EOF
window.__RUNTIME_CONFIG__ = {
  KAMERPLANTER_MODE: "${KAMERPLANTER_MODE:-full}",
  PWA_CACHING_ENABLED: "${PWA_CACHING_ENABLED:-true}"
};
EOF

exec "$@"
