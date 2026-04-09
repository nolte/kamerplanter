#!/usr/bin/env bash
set -euo pipefail

# ── Skaffold Dev Wrapper ────────────────────────────────────
# Starts skaffold dev with sane defaults:
#   - auto-build OFF  (no image rebuild on every file change)
#   - auto-deploy OFF (no helm upgrade on every file change)
#   - auto-sync ON    (file sync still works: .py/.ts/.tsx → container)
#
# Rebuild/redeploy manually by pressing Enter in the terminal.
#
# Usage:
#   ./scripts/skaffold-dev.sh              # full stack (kp module)
#   ./scripts/skaffold-dev.sh -m ki        # knowledge stack
#   ./scripts/skaffold-dev.sh -p backend-only
#   ./scripts/skaffold-dev.sh --auto-build # override: enable auto-build

MODULE="kp"
EXTRA_ARGS=()
AUTO_BUILD="false"
AUTO_DEPLOY="false"

while [[ $# -gt 0 ]]; do
    case "$1" in
        -m|--module)
            MODULE="$2"
            shift 2
            ;;
        --auto-build)
            AUTO_BUILD="true"
            shift
            ;;
        --auto-deploy)
            AUTO_DEPLOY="true"
            shift
            ;;
        *)
            EXTRA_ARGS+=("$1")
            shift
            ;;
    esac
done

exec skaffold dev \
    -m "$MODULE" \
    --auto-build="$AUTO_BUILD" \
    --auto-deploy="$AUTO_DEPLOY" \
    "${EXTRA_ARGS[@]}"
