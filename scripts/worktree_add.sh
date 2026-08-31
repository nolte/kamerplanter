#!/usr/bin/env bash
# Create a git worktree under the configurable portfolio worktree root.
#
# Wired in Taskfile.yml as `task worktree:add -- <branch> [slug]`. It is the
# correct counterpart to the guard-nested-worktree pre-commit hook: that guard
# rejects commits made from a worktree nested under .claude/worktrees/ (where
# the harness materialises isolation worktrees that have no resumable top-level
# transcript), and this helper is the supported way to get a worktree in the
# right place instead.
#
# Guarantees, so every worktree lands in the same predictable place:
#   - <root> comes from NOLTE_WORKTREE_ROOT (default ~/repos/.worktrees)
#   - <repo> is derived from the origin remote, never guessed
#   - the branch is created with an explicit base ref (origin/develop) after a
#     fetch, so the worktree starts from the remote tip and the primary
#     checkout's local develop is irrelevant
set -euo pipefail

usage() {
  cat >&2 <<EOF
Usage: task worktree:add -- <branch> [slug]

  <branch>  Full branch name including its prefix, e.g. feat/parser-fix.
            Allowed prefixes: feat/ fix/ chore/ docs/ exp/ ci/
  [slug]    Optional kebab-case directory name under the worktree root.
            Defaults to the branch name with its prefix stripped.

The worktree is created at:
  \${NOLTE_WORKTREE_ROOT:-~/repos/.worktrees}/<repo>/<slug>/
based on origin/develop. Start a top-level (resumable) session with:
  cd <that path> && claude
EOF
  exit 2
}

branch="${1:-}"
slug="${2:-}"

[ -n "$branch" ] || usage

# Branch-prefix rule — keep in sync with the project's branching convention.
case "$branch" in
  feat/*|fix/*|chore/*|docs/*|exp/*|ci/*) : ;;
  *)
    echo "✖ Branch '$branch' lacks an allowed prefix (feat/ fix/ chore/ docs/ exp/ ci/)." >&2
    echo "  The path slug may drop the prefix, but the branch MUST NOT." >&2
    exit 1
    ;;
esac

# Default slug: branch name minus the prefix segment.
if [ -z "$slug" ]; then
  slug="${branch#*/}"
fi

# A slug MUST be a single path segment — never a traversal or nested path.
case "$slug" in
  */*|*..*|"")
    echo "✖ Slug '$slug' must be a single kebab-case path segment." >&2
    exit 1
    ;;
esac

# Resolve the configurable root. Tilde in the env value is not expanded by the
# shell when it arrives as a variable, so expand a leading ~ ourselves.
root="${NOLTE_WORKTREE_ROOT:-$HOME/repos/.worktrees}"
# shellcheck disable=SC2088 # False positive: "~" and "~/" here are case PATTERNS that
# match a literal tilde arriving inside a variable, not paths meant to expand. Expanding
# them is what the branch bodies do, which is the whole point of this block. The
# directive must sit in front of the entire `case` — shellcheck rejects it on a single
# branch (SC1124) — so it also covers the "~" branch, which reports nothing today.
case "$root" in
  "~") root="$HOME" ;;
  "~/"*) root="$HOME/${root#\~/}" ;;
esac

# Derive <repo> from the origin remote — never inferred from the cwd.
origin_url="$(git remote get-url origin)"
repo="$(basename "$origin_url" .git)"

dest="$root/$repo/$slug"

if [ -e "$dest" ]; then
  echo "✖ Destination already exists: $dest" >&2
  exit 1
fi

echo "→ Worktree root : $root"
echo "→ Repository    : $repo"
echo "→ Branch        : $branch"
echo "→ Destination   : $dest"

git fetch origin develop --quiet
git worktree add -b "$branch" "$dest" origin/develop

echo
echo "✓ Worktree ready. Start a top-level (resumable) session scoped to it with:"
echo "    cd $dest && claude"
