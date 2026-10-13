#!/usr/bin/env bash
##
## Run the full pre-commit suite, and refuse to let its verdict be quoted as if
## it described a tree nobody else was touching.
##
## Why this exists. This repository's verification discipline is "paste the
## actual output, never an assertion that it passed", and `task precommit` is the
## local half of that. Two things were measured against that claim; both are
## written up with their numbers in spec/dev-tooling/PRECOMMIT-CONCURRENCY.md.
##
##   * #1641 — two WORKTREES sharing ~/.cache/pre-commit. 175 deliberately
##     concurrent runs, seeded violation, full CPU starvation, cold store: no
##     wrong verdict in either direction. The shared store is not the problem,
##     which is why this script neither serialises the runs nor gives each
##     worktree its own store (measured cost of that: 253 MB and ~1:26 of
##     environment rebuilding per worktree, 41 of them on this machine).
##
##   * #1649 — two WRITERS in ONE worktree. That one is real, and it goes BOTH
##     ways. #1649 recorded a false red (a hook named for a file it cannot
##     write). The false green was then constructed deliberately: a file staged
##     45 s into a 9-minute run is not in the list pre-commit enumerated with
##     `git ls-files` at start, so the whole suite reported 0 Failed and exit 0
##     over a tree that the very next run called Failed. A hook can only answer
##     about the tree it was handed.
##
## So this script reports two facts the verdict itself cannot carry:
##
##   1. whether a sibling `task precommit` overlapped this run — by liveness of
##      a registered pid, not by matching process names: each run drops $$ into
##      a registry directory inside the store and removes it on exit. Both ends
##      are checked, a sibling already running at the start and one that appears
##      during the run.
##   2. whether THE TREE ITSELF changed while the suite was in flight — the
##      #1649 mechanism, and the one that can produce a false green. The
##      fingerprint is `git status --porcelain -uall` plus size+mtime of every
##      tracked file, taken before and after; it costs ~0.1 s. The changed paths
##      are printed, because that list is the whole value: seeing an unrelated
##      Markdown file in it is what tells the next reader that the hook named in
##      the failure was never the writer.
##
## Hooks that repair files (`ruff --fix`, end-of-file-fixer) change the tree too,
## and pre-commit says so in its own output. The notice therefore names the paths
## rather than pretending it can tell the two apart. It never changes the verdict
## and never changes the exit code.
##
set -uo pipefail

# The runner is overridable so the guard test can drive this script without
# invoking the real 7-minute suite. Nothing else should set it.
PRE_COMMIT_BIN="${PRE_COMMIT_BIN:-pre-commit}"

store="${PRE_COMMIT_HOME:-${XDG_CACHE_HOME:-$HOME/.cache}/pre-commit}"
registry="$store/kamerplanter-task-precommit"
self="$registry/$$"

if ! mkdir -p "$registry" 2>/dev/null; then
    echo "WARN  cannot write $registry — this run cannot tell you whether a" >&2
    echo "      sibling 'task precommit' overlapped it (#1641). The verdict" >&2
    echo "      below stands on its own; the isolation claim does not." >&2
    registry=""
fi

cleanup() { [ -n "$registry" ] && rm -f "$self"; }
trap cleanup EXIT INT TERM HUP

# Print one line per live sibling; reap the entries whose process is gone.
# $1, when given, is a space-delimited set of pids to leave out — that is how
# the closing check reports only siblings that appeared DURING this run rather
# than repeating the ones the opening check already named.
siblings() {
    [ -n "$registry" ] || return 0
    local skip=" ${1:-} "
    local entry pid
    for entry in "$registry"/*; do
        [ -e "$entry" ] || continue
        pid="${entry##*/}"
        [ "$pid" = "$$" ] && continue
        if ! kill -0 "$pid" 2>/dev/null; then
            rm -f "$entry"
            continue
        fi
        case "$skip" in *" $pid "*) continue ;; esac
        printf '    pid %s  in %s\n' "$pid" "$(cat "$entry" 2>/dev/null)"
    done
}

# The pids siblings() just reported, as a flat set for the skip argument.
pids_of() { printf '%s' "$1" | awk '{print $2}' | tr '\n' ' '; }

# A fingerprint of everything pre-commit can see: the index/untracked state,
# plus size and mtime of every tracked file. `git ls-files` is what pre-commit
# itself enumerates, so this covers exactly the surface a verdict speaks about.
tree_fingerprint() {
    git status --porcelain=v1 -uall 2>/dev/null
    git ls-files -z 2>/dev/null | xargs -0 -r stat -c '%n|%s|%Y' 2>/dev/null
}

notice() { # $1 = when, $2 = the sibling listing
    echo "" >&2
    echo "================================================================" >&2
    echo "CONCURRENT 'task precommit' $1 (#1641)" >&2
    printf '%s' "$2" >&2
    echo "" >&2
    echo "  This verdict was NOT produced in isolation. Say so when you paste" >&2
    echo "  it, or re-run it once the sibling has finished. Measured: 175" >&2
    echo "  concurrent runs produced no wrong verdict — see" >&2
    echo "  spec/dev-tooling/PRECOMMIT-CONCURRENCY.md — so this is a caveat on" >&2
    echo "  the evidence, not a reason to distrust the result." >&2
    echo "================================================================" >&2
    echo "" >&2
}

tree_notice() { # $1 = the changed-path listing
    echo "" >&2
    echo "================================================================" >&2
    echo "THE TREE CHANGED WHILE THIS RUN WAS IN FLIGHT (#1649)" >&2
    printf '%s' "$1" >&2
    echo "  A hook answers about the tree it was handed at the start of the" >&2
    echo "  run. Anything written after that is outside every verdict above —" >&2
    echo "  a file staged mid-run is not in the list pre-commit enumerated, and" >&2
    echo "  the suite reports green over it (measured, see" >&2
    echo "  spec/dev-tooling/PRECOMMIT-CONCURRENCY.md). A path here that a" >&2
    echo "  repairing hook did not claim means a second writer shared this" >&2
    echo "  worktree: re-run before quoting this verdict." >&2
    echo "================================================================" >&2
    echo "" >&2
}

[ -n "$registry" ] && printf '%s\n' "$PWD" > "$self"

before="$(siblings)"
[ -n "$before" ] && notice "was already running when this run started" "$before"

tree_before="$(tree_fingerprint)"

"$PRE_COMMIT_BIN" run --all-files "$@"
rc=$?

after="$(siblings "$(pids_of "$before")")"
[ -n "$after" ] && notice "started while this run was in flight" "$after"

tree_after="$(tree_fingerprint)"
if [ "$tree_before" != "$tree_after" ]; then
    changed="$(
        diff <(printf '%s\n' "$tree_before") <(printf '%s\n' "$tree_after") 2>/dev/null |
            grep -E '^[<>]' | sed -E 's/^(.) /  \1 /' | cut -d'|' -f1 | sort -u | head -40
    )"
    tree_notice "$changed
"
fi

exit "$rc"
