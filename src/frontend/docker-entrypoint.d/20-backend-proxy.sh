#!/bin/sh
# Configure nginx backend proxy target from environment variable.
# Default: "backend" (matches docker-compose service name).
# Override with BACKEND_HOST for alternative service names (e.g. "backend-full").
BACKEND_HOST="${BACKEND_HOST:-backend}"
sed -i "s|proxy_pass http://backend:8000|proxy_pass http://${BACKEND_HOST}:8000|g" \
    /etc/nginx/conf.d/default.conf
