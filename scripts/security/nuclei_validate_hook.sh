#!/usr/bin/env bash
##
## Validate the project's own Nuclei templates, and never claim success without
## running the validation.
##
## The hook this replaces was:
##
##     command -v nuclei >/dev/null 2>&1 || { echo "skipping"; exit 0; }
##
## "If the tool is absent, exit successfully." The reusable `static` job is a
## Python-only runner that never installs nuclei, so on the ONE required check of
## this repository the hook printed `Passed` for a validation that examined
## nothing — for every template change, every time. Same shape as #814.
##
## The comment above it named the CI security-nuclei workflow as "the
## authoritative gate". That gate did not exist: neither security-nuclei-pr.yml
## nor security-nuclei-nightly.yml ran `nuclei -validate`. A skip is only
## defensible when the surface is genuinely covered elsewhere, so the backstop
## was created rather than merely asserted:
## .github/workflows/security-nuclei-templates.yml validates the directory on
## every pull request that touches it, in seconds and without building a stack.
##
## Two situations, told apart the way scripts/frontend_hook.sh tells them apart:
##
##   * **Locally**, a missing nuclei means the contributor cannot run the gate.
##     Worth stopping for, with an instruction — being waved through silently is
##     how a malformed template reaches `develop`.
##   * **In CI**, its absence from the Python-only pre-commit job is structural.
##     Skipping is correct, but it is announced, and it leans on the named
##     backstop above. If that step is ever removed, this skip has to go with it.
##
set -euo pipefail

TEMPLATE_DIR="tests/security/nuclei-templates"

if [[ ! -d "$TEMPLATE_DIR" ]]; then
    echo "FAIL  $TEMPLATE_DIR is missing — nothing to validate, and that is not a pass." >&2
    exit 1
fi

if ! command -v nuclei >/dev/null 2>&1; then
    if [[ -n "${CI:-}" ]]; then
        echo "SKIP  nuclei template validation: nuclei is not on PATH." >&2
        echo "      pre-commit runs in a Python-only CI job, so this is structural." >&2
        echo "      The same templates are validated by the" >&2
        echo "      .github/workflows/security-nuclei-templates.yml gate —" >&2
        echo "      this skip is only valid while that workflow exists." >&2
        exit 0
    fi
    echo "FAIL  nuclei template validation cannot run: nuclei is not on PATH." >&2
    echo "      Install it first:" >&2
    echo "          go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest" >&2
    echo "      or grab a release binary from" >&2
    echo "          https://github.com/projectdiscovery/nuclei/releases" >&2
    echo "      Reporting success here would mean claiming a check ran that did not (#814)." >&2
    exit 1
fi

exec nuclei -validate -t "$TEMPLATE_DIR/"
