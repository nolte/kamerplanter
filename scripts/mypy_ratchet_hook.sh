#!/usr/bin/env bash
##
## pre-commit entry for the backend mypy ratchet (#2169). Never claims success
## without running it.
##
## The ratchet needs the whole locked backend environment — mypy, the pydantic
## plugin and every typed dependency at their locked versions — because a
## different mypy or a missing stub moves the per-file counts. An isolated
## pre-commit venv carrying mypy only (the pattern of the sibling-package hooks)
## would therefore produce numbers the baseline cannot be compared against.
##
##   * **Locally** the hook runs `task typecheck:backend`'s exact invocation. A
##     missing `uv` is a FAIL with an instruction, not a pass (#814).
##   * **In CI** pre-commit runs in the Python-only `static` job, which never
##     builds the backend environment. Skipping there is structural, and it is
##     announced. The backstop is the `mypy ratchet` step of the `lint-test` job
##     in .github/workflows/backend.yml, which runs the same script under
##     `uv sync --locked --extra dev`. That job is ADVISORY (not a required
##     context on `develop`) — so in CI this gate reports, it does not block,
##     until an operator makes `lint-test` (or a lane carrying this step)
##     required. This skip becomes invalid if that step is removed.
##
set -euo pipefail

if [[ -n "${CI:-}" ]]; then
    echo "SKIP  mypy ratchet (backend): the static CI job has no locked backend environment." >&2
    echo "      Backstop: the 'mypy ratchet' step of Backend CI / lint-test (advisory)." >&2
    echo "      This skip is only valid while that step exists." >&2
    exit 0
fi

if ! command -v uv >/dev/null 2>&1; then
    echo "FAIL  mypy ratchet (backend) cannot run: 'uv' is not on PATH." >&2
    echo "      Install the uv version pinned in src/backend/pyproject.toml ([tool.uv].required-version)," >&2
    echo "      then run: task typecheck:backend" >&2
    echo "      Reporting success here would mean claiming a check ran that did not (#814)." >&2
    exit 1
fi

cd src/backend
exec uv run --locked --extra dev python ../../scripts/check_mypy_ratchet.py
