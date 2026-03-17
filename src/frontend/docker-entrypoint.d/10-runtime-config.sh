#!/bin/sh
# Generate runtime config from environment variables.
# This runs at container start, so mode can be changed without rebuilding.
cat <<EOF > /usr/share/nginx/html/runtime-config.js
window.__RUNTIME_CONFIG__ = {
  KAMERPLANTER_MODE: "${KAMERPLANTER_MODE:-full}"
};
EOF
