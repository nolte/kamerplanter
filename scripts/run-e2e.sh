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
##   ./scripts/run-e2e.sh --force                # Start even though another E2E stack is
##                                               #   already running (same as
##                                               #   E2E_FORCE_CONCURRENT=1) — see the
##                                               #   concurrency guard below
##
## Exit codes:
##   0/1 … pytest result   2 … usage error   3 … refused, another E2E stack is running
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

# Pass host UID/GID so the e2e-tests container writes files as the current user.
# Assign first, export second, so `id -g`'s exit status is not masked by `export`
# (SC2155). Both variables must reach docker compose's environment: docker-compose.e2e.yml
# interpolates "${UID:-1000}:${GID:-1000}" for the `user:` of eight services. UID is
# readonly in bash (`declare -ir`), which does not prevent exporting it — so keep it in
# the `export`, or those eight services silently fall back to 1000.
GID="$(id -g)"
export UID GID

# Determine run mode
PROFILE="light"
FORCE_CONCURRENT="${E2E_FORCE_CONCURRENT:-0}"
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
        --force)
            FORCE_CONCURRENT="1"
            shift
            ;;
        *)
            echo "Unknown argument: $1" >&2
            echo "Usage: $0 [--smoke | --profile <light|smoke|full|mobile|tablet|full-mobile|full-tablet>] [--force]" >&2
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

##
## ── Concurrency guard ────────────────────────────────────────────────────────
##
## Refuse to start while another E2E stack from this compose file is running.
## Two stacks started from the same compose project reuse one Selenium hub and
## one Chrome node, so both runners compete for a session pool sized for one of
## them; the losing workers time out and the suite reports hundreds of setup
## errors that are indistinguishable from real test failures (#778, H2). On top
## of that, the first run to finish executes "down -v" underneath the other one.
##
## The check reads live Docker state instead of a lock file: the stack publishes
## no host ports, so probing the hub on the host cannot see it, and the compose
## labels are the only observable truth. That also makes the check crash-safe —
## it holds no lock that could go stale, and containers left behind by a crashed
## run are a genuine conflict the operator has to clear anyway.
##
find_conflicting_stacks() {
    local project working_dir config_files name
    docker ps \
        --filter "label=com.docker.compose.project.config_files" \
        --format '{{.Label "com.docker.compose.project"}}|{{.Label "com.docker.compose.project.working_dir"}}|{{.Label "com.docker.compose.project.config_files"}}|{{.Names}}' \
        2>/dev/null |
        while IFS='|' read -r project working_dir config_files name; do
            # config_files is a comma-separated list of absolute paths. Matching
            # the base compose file also catches stacks that carry an overlay
            # (E2E_COMPOSE_OVERLAYS), and ignores unrelated compose projects.
            case ",${config_files}," in
                *"/${COMPOSE_FILE},"*) printf '%s|%s|%s\n' "$project" "$working_dir" "$name" ;;
            esac
        done | sort
}

# Renders "$1" (output of find_conflicting_stacks) as a grouped, indented list.
print_conflicting_stacks() {
    local last_project="" project working_dir name origin
    while IFS='|' read -r project working_dir name; do
        if [[ "$project" != "$last_project" ]]; then
            last_project="$project"
            if [[ "$working_dir" == "$PWD" ]]; then
                origin="this working tree"
            else
                origin="another working tree"
            fi
            echo "  compose project '$project' — $origin: $working_dir" >&2
        fi
        echo "      $name" >&2
    done <<< "$1"
}

# Prints one "down -v" hint per distinct compose project in "$1".
print_teardown_hints() {
    local last_project="" project working_dir name
    while IFS='|' read -r project working_dir name; do
        if [[ "$project" != "$last_project" ]]; then
            last_project="$project"
            echo "  (cd '$working_dir' && docker compose -f $COMPOSE_FILE down -v)" >&2
        fi
    done <<< "$1"
}

CONFLICTING_STACKS="$(find_conflicting_stacks)"
if [[ -n "$CONFLICTING_STACKS" ]]; then
    if [[ "$FORCE_CONCURRENT" == "1" ]]; then
        echo "=== WARNING: --force overrides the concurrency guard ===" >&2
        echo "" >&2
        echo "Another E2E stack is running and this run will NOT be isolated from it:" >&2
        print_conflicting_stacks "$CONFLICTING_STACKS"
        echo "" >&2
        echo "Overridden check: 'another E2E stack from $COMPOSE_FILE is already running'." >&2
        echo "Nothing else changes — both runs still share the Selenium session pool," >&2
        echo "and the first run to finish still tears the shared containers down." >&2
        echo "" >&2
    else
        echo "=== REFUSING TO START: another E2E stack is already running ===" >&2
        echo "" >&2
        echo "A second stack collides with the one below: from this working tree it reuses" >&2
        echo "that stack's Selenium hub and Chrome node — one session pool for two runners —" >&2
        echo "and from any working tree both runs compete for the same host. Either way the" >&2
        echo "suite reports hundreds of setup errors that look exactly like real failures." >&2
        echo "" >&2
        echo "Already running:" >&2
        print_conflicting_stacks "$CONFLICTING_STACKS"
        echo "" >&2
        echo "Stop it first:" >&2
        print_teardown_hints "$CONFLICTING_STACKS"
        echo "" >&2
        echo "If you are certain the detection is wrong (for example the containers above" >&2
        echo "belong to an unrelated project that merely uses a compose file of the same" >&2
        echo "name), re-run with --force or E2E_FORCE_CONCURRENT=1. That opt-in overrides" >&2
        echo "ONLY this concurrency check; it does not isolate the two stacks." >&2
        exit 3
    fi
fi

mkdir -p "$REPORT_DIR/logs"

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
# The runner writes a single merged JUnit XML (xdist-aware) which the protocol
# plugin relocates into the container report dir; the cp move above carries it
# here. Surface it so CI consumers know where the machine-readable report is.
JUNIT_FILE=$(find "$REPORT_DIR" -maxdepth 1 -type f -name "junit-*.xml" 2>/dev/null | head -1)
if [ -n "$JUNIT_FILE" ]; then
    echo "  - $(basename "$JUNIT_FILE")  JUnit XML report (CI-consumable, per-testcase tc_id)"
fi
echo ""

exit $EXIT_CODE
