#!/usr/bin/env bash
##
## Run E2E tests in a dedicated Docker Compose environment.
## Collects container logs into test-reports/e2e/ regardless of outcome.
##
## Usage:
##   ./scripts/run-e2e.sh                        # Full E2E suite, light mode (~15min)
##   ./scripts/run-e2e.sh --smoke                # Smoke tests only (~2min)
##   ./scripts/run-e2e.sh --profile <name>       # One compose profile:
##                                               #   light | smoke | full | mobile |
##                                               #   tablet | full-mobile | full-tablet
##
set -uo pipefail

COMPOSE_FILE="docker-compose.e2e.yml"
REPORT_DIR="test-reports/e2e/$(date -u +%Y%m%d_%H%M%S)"

# Optional space-separated compose overlay files (e.g. CI layer-cache config:
# E2E_COMPOSE_OVERLAYS="docker-compose.e2e.ci.yml"). Local runs leave this unset.
COMPOSE_ARGS=(-f "$COMPOSE_FILE")
for OVERLAY in ${E2E_COMPOSE_OVERLAYS:-}; do
    COMPOSE_ARGS+=(-f "$OVERLAY")
done

mkdir -p "$REPORT_DIR/logs"

# Pass host UID/GID so the e2e-tests container writes files as the current user
export UID GID="$(id -g)"

# Determine run mode
PROFILE="light"
while [[ $# -gt 0 ]]; do
    case "$1" in
        --smoke)
            PROFILE="smoke"
            shift
            ;;
        --profile)
            PROFILE="${2:?--profile requires a value}"
            shift 2
            ;;
        *)
            echo "Unknown argument: $1" >&2
            echo "Usage: $0 [--smoke | --profile <light|smoke|full|mobile|tablet|full-mobile|full-tablet>]" >&2
            exit 2
            ;;
    esac
done

# Map profile → compose profile flags + test-runner service.
# The full* profiles need "--profile full" too: their runner depends on
# backend-full/frontend-full, which live in the "full" compose profile and
# are not auto-activated by targeting the runner service alone.
case "$PROFILE" in
    light)       PROFILE_FLAG="";                                    SERVICE="e2e-tests" ;;
    smoke)       PROFILE_FLAG="--profile smoke";                     SERVICE="e2e-smoke" ;;
    mobile)      PROFILE_FLAG="--profile mobile";                    SERVICE="e2e-tests-mobile" ;;
    tablet)      PROFILE_FLAG="--profile tablet";                    SERVICE="e2e-tests-tablet" ;;
    full)        PROFILE_FLAG="--profile full";                      SERVICE="e2e-tests-full" ;;
    full-mobile) PROFILE_FLAG="--profile full --profile full-mobile"; SERVICE="e2e-tests-full-mobile" ;;
    full-tablet) PROFILE_FLAG="--profile full --profile full-tablet"; SERVICE="e2e-tests-full-tablet" ;;
    *)
        echo "Unknown profile: $PROFILE" >&2
        exit 2
        ;;
esac

# full* profiles run against the full-mode app stack, everything else light
if [[ "$PROFILE" == full* ]]; then
    APP_SERVICES="backend-full celery-worker-full frontend-full"
    FRONTEND_SERVICE="frontend-full"
else
    APP_SERVICES="backend celery-worker frontend"
    FRONTEND_SERVICE="frontend"
fi
INFRA_SERVICES="arangodb valkey $APP_SERVICES selenium-hub chrome"

echo "=== Building and starting infrastructure (profile: $PROFILE) ==="
docker compose "${COMPOSE_ARGS[@]}" $PROFILE_FLAG up --build -d $INFRA_SERVICES

echo "=== Waiting for $FRONTEND_SERVICE to be healthy ==="
docker compose "${COMPOSE_ARGS[@]}" $PROFILE_FLAG up -d --wait "$FRONTEND_SERVICE"

echo "=== Running E2E tests (service: $SERVICE) ==="
# --build rebuilds the e2e-tests/e2e-smoke image when local test sources changed
# (the infrastructure block above only covers backend/frontend; without --build
# here, edits in tests/e2e/ are silently ignored and the container reuses the
# previously cached image).
docker compose "${COMPOSE_ARGS[@]}" $PROFILE_FLAG run --build --rm "$SERVICE"
EXIT_CODE=$?

echo "=== Collecting container logs ==="
for SVC in $INFRA_SERVICES; do
    docker compose "${COMPOSE_ARGS[@]}" $PROFILE_FLAG logs --no-color "$SVC" > "$REPORT_DIR/logs/${SVC}.log" 2>&1 || true
done

# Move screenshots/protocol from the container-created report dir into our report dir
CONTAINER_REPORT=$(find test-reports/e2e -maxdepth 1 -mindepth 1 -type d -name "2*" ! -path "$REPORT_DIR" -newer "$REPORT_DIR/logs" 2>/dev/null | head -1)
if [ -n "$CONTAINER_REPORT" ] && [ "$CONTAINER_REPORT" != "$REPORT_DIR" ]; then
    cp -r "$CONTAINER_REPORT"/* "$REPORT_DIR/" 2>/dev/null || true
    rm -rf "$CONTAINER_REPORT"
fi

echo "=== Tearing down ==="
docker compose "${COMPOSE_ARGS[@]}" $PROFILE_FLAG down -v

echo ""
echo "Reports: $REPORT_DIR/"
echo "  - logs/        Container logs (backend, frontend, selenium, ...)"
echo "  - screenshots/ Selenium screenshots"
echo "  - protokoll.md Test protocol"
echo ""

exit $EXIT_CODE
