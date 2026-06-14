#!/usr/bin/env bash
# Guard: refuse commits made from a worktree nested under .claude/worktrees/.
#
# Wired in .pre-commit-config.yaml as the `guard-nested-worktree` hook
# (always_run, pass_filenames: false), so it fires on every `git commit`.
#
# Why this exists: the Claude Code harness materialises isolation worktrees
# (Agent({isolation:"worktree"}), and some EnterWorktree flows) UNDER
# .claude/worktrees/<name>/. Those are auto-cleaned, and a session run from
# there has no resumable top-level transcript: after a crash, `claude --resume`
# finds nothing for that path and the in-flight work is stranded. This actually
# happened (the nfr-lektorat run on 2026-06-11 was lost this way). Long feature
# work belongs in a worktree under the centralised worktree root instead, where
# a top-level session IS resumable.
#
# This guard catches the most common failure mode — committing from such a
# nested worktree — and points at the supported alternative (`task worktree:add`).
set -euo pipefail

# Skip in CI and other non-interactive automation. This guard targets a
# developer's local `git commit`, not CI. `CI` is set by GitHub Actions and
# essentially every other CI provider.
if [ -n "${CI:-}" ]; then
  exit 0
fi

# The worktree root for the commit being made. Resolve symlinks so the match is
# reliable regardless of how the path was entered.
toplevel="$(cd "$(git rev-parse --show-toplevel)" && pwd -P)"

case "$toplevel" in
  */.claude/worktrees/*)
    cat >&2 <<EOF
✖ Commit blocked — this worktree is nested under .claude/worktrees/.

  $toplevel

  Worktrees under .claude/worktrees/ are harness-managed isolation copies.
  They get auto-cleaned and a session run from here has NO resumable
  top-level transcript: after a crash, \`claude --resume\` finds nothing for
  this path and the work is stranded (this is how the nfr-lektorat run was
  lost on 2026-06-11).

  Move the work to a worktree under the centralised root instead, where a
  top-level session is resumable:

    # from the primary checkout (~/repos/github/kamerplanter):
    task worktree:add -- <prefix>/<branch>
    cd \${NOLTE_WORKTREE_ROOT:-~/repos/.worktrees}/kamerplanter/<slug>
    claude          # a top-level, --resume-able session

  If you already committed here, cherry-pick or re-apply the change in the
  proper worktree, then remove this one: git worktree remove "$toplevel"
EOF
    exit 1
    ;;
esac

exit 0
