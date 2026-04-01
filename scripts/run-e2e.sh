#!/usr/bin/env bash
##
## Run E2E tests in a dedicated Docker Compose environment.
## Collects container logs into test-reports/e2e/ regardless of outcome.
##
## Usage:
##   ./scripts/run-e2e.sh           # Full E2E suite (~15min)
##   ./scripts/run-e2e.sh --smoke   # Smoke tests only (~2min)
##
set -uo pipefail

COMPOSE_FILE="docker-compose.e2e.yml"
REPORT_DIR="test-reports/e2e/$(date -u +%Y%m%d_%H%M%S)"

mkdir -p "$REPORT_DIR/logs"

# Pass host UID/GID so the e2e-tests container writes files as the current user
export UID GID="$(id -g)"

# Determine run mode: full or smoke
PROFILE_FLAG=""
SERVICE="e2e-tests"
if [[ "${1:-}" == "--smoke" ]]; then
    PROFILE_FLAG="--profile smoke"
    SERVICE="e2e-smoke"
    shift
fi

echo "=== Building and starting infrastructure ==="
docker compose -f "$COMPOSE_FILE" $PROFILE_FLAG up --build -d arangodb valkey backend celery-worker frontend selenium-hub chrome

echo "=== Waiting for frontend to be healthy ==="
docker compose -f "$COMPOSE_FILE" $PROFILE_FLAG up -d --wait frontend

echo "=== Running E2E tests (service: $SERVICE) ==="
docker compose -f "$COMPOSE_FILE" $PROFILE_FLAG run --rm "$SERVICE"
EXIT_CODE=$?

echo "=== Collecting container logs ==="
for SVC in arangodb valkey backend celery-worker frontend selenium-hub chrome; do
    docker compose -f "$COMPOSE_FILE" $PROFILE_FLAG logs --no-color "$SVC" > "$REPORT_DIR/logs/${SVC}.log" 2>&1 || true
done

# Move screenshots/protocol from the container-created report dir into our report dir
CONTAINER_REPORT=$(find test-reports/e2e -maxdepth 1 -mindepth 1 -type d -name "2*" ! -path "$REPORT_DIR" -newer "$REPORT_DIR/logs" 2>/dev/null | head -1)
if [ -n "$CONTAINER_REPORT" ] && [ "$CONTAINER_REPORT" != "$REPORT_DIR" ]; then
    cp -r "$CONTAINER_REPORT"/* "$REPORT_DIR/" 2>/dev/null || true
    rm -rf "$CONTAINER_REPORT"
fi

echo "=== Tearing down ==="
docker compose -f "$COMPOSE_FILE" $PROFILE_FLAG down -v

echo ""
echo "Reports: $REPORT_DIR/"
echo "  - logs/        Container logs (backend, frontend, selenium, ...)"
echo "  - screenshots/ Selenium screenshots"
echo "  - protokoll.md Test protocol"
echo ""

exit $EXIT_CODE
