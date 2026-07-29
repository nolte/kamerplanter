#!/usr/bin/env bash
##
## Run a frontend pre-commit gate, and never claim success without running it.
##
## Both frontend hooks used to open with `test -d src/frontend/node_modules ||
## exit 0` — "if the dependencies are absent, exit successfully". pre-commit then
## printed `Passed` for a check that examined nothing, and a commit that did not
## compile went through with two green hooks (#814).
##
## The guard itself was not wrong, only its verdict. Two situations have to be
## told apart:
##
##   * **Locally**, missing `node_modules` means the contributor cannot run the
##     gate. That is worth stopping for, with an instruction — being waved
##     through silently is how the defect reached `develop`.
##   * **In CI**, pre-commit runs in a Python-only job that never installs npm
##     dependencies, so the absence is structural rather than a mistake. Failing
##     there would turn the required `static` job red on every frontend change.
##     Skipping is correct — but it is announced, and it is only defensible
##     because the surface is genuinely covered elsewhere:
##     `lint-test-build (22)` runs ESLint and `tsc --noEmit` over the same files
##     (`.github/workflows/frontend.yml`) and is a REQUIRED check on `develop`
##     (#828). That is the backstop this skip leans on, and it is load-bearing:
##     if the context is ever demoted, this skip has to go with it. Verify the
##     live list rather than the declaration — a `restrictions` entry once made
##     the Settings App drop an entire protection update:
##
##         gh api repos/nolte/kamerplanter/branches/develop/protection \
##           --jq '.required_status_checks.contexts'
##
## Usage:  frontend_hook.sh eslint [files...]
##         frontend_hook.sh tsc
##
set -euo pipefail

TOOL="${1:?usage: frontend_hook.sh <eslint|tsc> [files...]}"
shift || true

FRONTEND_DIR="src/frontend"

if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
    if [[ -n "${CI:-}" ]]; then
        echo "SKIP  frontend $TOOL: $FRONTEND_DIR/node_modules is absent." >&2
        echo "      pre-commit runs in a Python-only CI job, so this is structural." >&2
        echo "      The same surface is gated by the required 'lint-test-build (22)'" >&2
        echo "      check (#828) — this skip is only valid while that stays required." >&2
        exit 0
    fi
    echo "FAIL  frontend $TOOL cannot run: $FRONTEND_DIR/node_modules is missing." >&2
    echo "      Install the dependencies first:" >&2
    echo "          (cd $FRONTEND_DIR && npm ci)" >&2
    echo "      Reporting success here would mean claiming a check ran that did not (#814)." >&2
    exit 1
fi

cd "$FRONTEND_DIR"

case "$TOOL" in
    eslint)
        # pre-commit passes repo-relative paths; eslint runs from src/frontend.
        exec npx eslint --no-error-on-unmatched-pattern "${@/#src\/frontend\//}"
        ;;
    tsc)
        exec npx tsc --noEmit
        ;;
    *)
        echo "frontend_hook.sh: unknown tool '$TOOL' (expected eslint or tsc)" >&2
        exit 2
        ;;
esac
