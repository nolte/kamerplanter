#!/usr/bin/env bash
##
## Run E2E tests in a dedicated Docker Compose environment.
## Collects container logs into test-reports/ regardless of outcome.
##
## Usage:
##   ./scripts/run-e2e.sh
##
set -uo pipefail

COMPOSE_FILE="docker-compose.e2e.yml"
REPORT_DIR="test-reports/$(date -u +%Y%m%d_%H%M%S)"

mkdir -p "$REPORT_DIR/logs"

echo "=== Starting E2E test environment ==="
docker compose -f "$COMPOSE_FILE" up --build --abort-on-container-exit
EXIT_CODE=$?

echo "=== Collecting container logs ==="
for SERVICE in arangodb valkey backend celery-worker frontend selenium-hub chrome e2e-tests; do
    docker compose -f "$COMPOSE_FILE" logs --no-color "$SERVICE" > "$REPORT_DIR/logs/${SERVICE}.log" 2>&1 || true
done

# Move screenshots from the container-created report dir into our report dir
CONTAINER_REPORT=$(find test-reports -maxdepth 1 -mindepth 1 -type d -name "2*" ! -path "$REPORT_DIR" -newer "$REPORT_DIR/logs" 2>/dev/null | head -1)
if [ -n "$CONTAINER_REPORT" ] && [ "$CONTAINER_REPORT" != "$REPORT_DIR" ]; then
    cp -r "$CONTAINER_REPORT"/* "$REPORT_DIR/" 2>/dev/null || true
    rm -rf "$CONTAINER_REPORT"
fi

echo "=== Tearing down ==="
docker compose -f "$COMPOSE_FILE" down -v

echo ""
echo "Reports: $REPORT_DIR/"
echo "  - logs/        Container logs (backend, frontend, selenium, ...)"
echo "  - screenshots/ Selenium screenshots"
echo "  - protokoll.md Test protocol"
echo ""

exit $EXIT_CODE
