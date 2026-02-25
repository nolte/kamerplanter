#!/usr/bin/env bash
set -euo pipefail

CLUSTER_NAME="kamerplanter"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }

# ── Delete Kind cluster ──────────────────────────────────────
if kind get clusters 2>/dev/null | grep -q "^${CLUSTER_NAME}$"; then
    info "Deleting Kind cluster '${CLUSTER_NAME}'..."
    kind delete cluster --name "${CLUSTER_NAME}"
    info "Cluster deleted."
else
    warn "Kind cluster '${CLUSTER_NAME}' does not exist."
fi

# ── Optional Docker cleanup ──────────────────────────────────
if [ "${1:-}" = "--clean" ]; then
    info "Cleaning up Docker resources..."
    docker system prune -f --filter "label=io.x-k8s.kind.cluster=${CLUSTER_NAME}"
    info "Docker cleanup complete."
else
    echo ""
    echo "Tip: Run with --clean to also prune Docker resources:"
    echo "  ./scripts/dev-teardown.sh --clean"
fi
