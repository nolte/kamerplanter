#!/usr/bin/env bash
set -euo pipefail

CLUSTER_NAME="kamerplanter"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# ── Check prerequisites ──────────────────────────────────────
check_command() {
    if ! command -v "$1" &>/dev/null; then
        error "$1 is not installed. $2"
        return 1
    fi
    info "$1 found: $(command -v "$1")"
}

info "Checking prerequisites..."
MISSING=0
check_command docker "Install: https://docs.docker.com/get-docker/"            || MISSING=1
check_command kind "Install: go install sigs.k8s.io/kind@latest"               || MISSING=1
check_command kubectl "Install: https://kubernetes.io/docs/tasks/tools/"        || MISSING=1
check_command helm "Install: https://helm.sh/docs/intro/install/"              || MISSING=1
check_command skaffold "Install: https://skaffold.dev/docs/install/"           || MISSING=1

if [ "$MISSING" -eq 1 ]; then
    error "Missing prerequisites. Please install them and try again."
    exit 1
fi

# ── Create Kind cluster ──────────────────────────────────────
if kind get clusters 2>/dev/null | grep -q "^${CLUSTER_NAME}$"; then
    warn "Kind cluster '${CLUSTER_NAME}' already exists. Skipping creation."
else
    info "Creating Kind cluster '${CLUSTER_NAME}'..."
    kind create cluster --config "${ROOT_DIR}/kind-config.yaml" --name "${CLUSTER_NAME}"
fi

# ── Set kubectl context ──────────────────────────────────────
info "Setting kubectl context..."
kubectl cluster-info --context "kind-${CLUSTER_NAME}"

# ── Install Nginx Ingress Controller ─────────────────────────
info "Installing Nginx Ingress Controller..."
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

info "Waiting for Ingress Controller to be ready..."
kubectl wait --namespace ingress-nginx \
    --for=condition=ready pod \
    --selector=app.kubernetes.io/component=controller \
    --timeout=120s 2>/dev/null || warn "Ingress controller not ready yet — it may need more time."

# ── Add Helm repos ────────────────────────────────────────────
info "Adding Helm repositories..."
helm repo add bitnami https://charts.bitnami.com/bitnami 2>/dev/null || true
helm repo update

# ── Done ──────────────────────────────────────────────────────
echo ""
info "Kind cluster '${CLUSTER_NAME}' is ready!"
echo ""
echo "Next steps:"
echo "  1. Start development:    ./scripts/skaffold-dev.sh"
echo "  2. Backend only:         ./scripts/skaffold-dev.sh -p backend-only"
echo "  3. KI stack:             ./scripts/skaffold-dev.sh -m ki"
echo "  4. Debug mode:           skaffold debug"
echo "  5. Access services:"
echo "     - Frontend:           http://localhost:3000"
echo "     - Backend API:        http://localhost:8000"
echo "     - ArangoDB UI:        http://localhost:8529"
echo "  6. Tear down:            ./scripts/dev-teardown.sh"
