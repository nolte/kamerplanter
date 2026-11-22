#!/usr/bin/env bash
##
## Entrypoint of the parallel E2E runners (docker-compose.e2e.yml, #3032).
##
## Pass 1 runs the suite on four xdist workers without the `bulk_seed` tests.
## Pass 2 then runs the `bulk_seed` tests alone, serially, once nothing else is
## left. Those tests provision thousands of records into the one shared tenant
## (light mode has exactly one, so tenant isolation is no way out): run next to
## the journeys they pushed planting-run POSTs from 0.03 s to 5-7 s, the
## journeys' API helpers timed out and later pickers lost the journeys' plants.
##
## Usage: two_pass_entrypoint.sh <junit-stem> [pytest args...]
##   <junit-stem>  e.g. `junit-default`: pass 1 writes test-reports/e2e/<stem>.xml,
##                 pass 2 test-reports/e2e/<stem>-bulk-seed.xml. Both keep the
##                 `junit-*.xml` shape the report steps glob for.
##   pytest args   handed to both passes. A `-m <expr>` among them is combined
##                 with the pass's own selection instead of replacing it.
##
## Exit status: non-zero when either pass failed. Pass 2 runs even after a red
## pass 1 (but not after an interrupted one: exit 2 or a signal) (its tests are independent of the journeys), and its "no tests
## collected" (5) counts as success - a selection may legitimately contain no
## bulk_seed test. Pass 1's 5 stays a failure, as it was before the split.
##
## With --generate-protocol, pass 2 resumes pass 1's report directory
## (`--resume`), so one protokoll.md, one checkpoint.jsonl and one screenshots/
## hold both passes and both JUnit files are relocated next to them.
##
## `set -u` only: `set -e` would end the script at a red pass 1 and lose pass 2.
set -u

PYTEST="${E2E_PYTEST:-pytest}"
REPORT_ROOT="test-reports/e2e"
NO_TESTS_COLLECTED=5

if [ "$#" -lt 1 ]; then
    echo "usage: $0 <junit-stem> [pytest args...]" >&2
    exit 2
fi
junit_stem="$1"
shift

# Split a caller's marker expression off the remaining arguments.
user_marks=""
generate_protocol=0
rest=()
while [ "$#" -gt 0 ]; do
    case "$1" in
        -m)
            if [ "$#" -lt 2 ]; then
                echo "$0: -m needs an expression" >&2
                exit 2
            fi
            user_marks="$2"
            shift 2
            ;;
        -m*)
            user_marks="${1#-m}"
            shift
            ;;
        *)
            if [ "$1" = "--generate-protocol" ]; then
                generate_protocol=1
            fi
            rest+=("$1")
            shift
            ;;
    esac
done

if [ -n "$user_marks" ]; then
    parallel_marks="($user_marks) and not bulk_seed"
    serial_marks="($user_marks) and bulk_seed"
else
    parallel_marks="not bulk_seed"
    serial_marks="bulk_seed"
fi

# Pass 1 creates its report directory (test-reports/e2e/<timestamp>) itself;
# the stamp tells it apart from every directory that existed before.
# Known limit: this assumes the runner has test-reports/ to itself. Two runners
# writing into one volume at the same time could make it pick the other's dir.
stamp="$(mktemp)"
trap 'rm -f "$stamp"' EXIT

echo "=== E2E pass 1/2: parallel, -m '$parallel_marks' ==="
"$PYTEST" -n 4 --dist=loadfile -m "$parallel_marks" \
    "--junitxml=$REPORT_ROOT/$junit_stem.xml" "${rest[@]}"
parallel_status=$?

# pytest's 2 is "interrupted" and >= 128 a signal: the run was stopped, so the
# serial pass must not start and load the tenant on its own.
if [ "$parallel_status" = "2" ] || [ "$parallel_status" -ge 128 ]; then
    echo "=== E2E pass 1 was interrupted (exit $parallel_status); pass 2 skipped ===" >&2
    exit "$parallel_status"
fi

resume=()
if [ "$generate_protocol" = "1" ]; then
    report_dir="$(find "$REPORT_ROOT" -mindepth 1 -maxdepth 1 -type d -name '2*' \
        -newer "$stamp" 2>/dev/null | sort | tail -n 1)"
    if [ -n "$report_dir" ]; then
        resume=(--resume "$report_dir")
    else
        echo "=== pass 1 left no report directory; pass 2 writes its own ===" >&2
    fi
fi

echo "=== E2E pass 2/2: serial, -m '$serial_marks' ==="
"$PYTEST" -m "$serial_marks" "--junitxml=$REPORT_ROOT/$junit_stem-bulk-seed.xml" \
    "${resume[@]}" "${rest[@]}"
serial_status=$?
if [ "$serial_status" = "$NO_TESTS_COLLECTED" ]; then
    serial_status=0
fi

echo "=== E2E passes: parallel exit $parallel_status, serial exit $serial_status ==="
if [ "$parallel_status" != "0" ]; then
    exit "$parallel_status"
fi
exit "$serial_status"
