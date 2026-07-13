#!/usr/bin/env bash
# Guard: refuse a pull request whose branch tip still tracks .resume/ files.
#
# Wired in .pre-commit-config.yaml as the `guard-resume-files` hook
# (always_run, pass_filenames: false). The reusable `static` CI job runs
# `pre-commit run --all-files`, so this fires there and is the required check
# that gates every merge to develop.
#
# Why this exists: files under .resume/ are worktree-local working artifacts —
# the crash-recovery plan `.resume/<slug>/plan.md` written by `task worktree:add`
# and the resumable-skill state under `.resume/pull-request-*/`. Per
# spec/project/parallel-working-copies/ §"Lebenszyklus: Planen vor der Arbeit"
# that path is gitignored and MUST NOT become a committed artifact; it must
# never reach the default branch. Twelve such plan.md files leaked onto develop
# through PRs #385–#486 before this guard existed.
#
# Deliberately INVERSE to guard_nested_worktree.sh: that guard targets a local
# `git commit` and skips in CI; this one is a no-op locally so a developer may
# still checkpoint .resume/ into git DURING work (`git add -f`) for crash
# recovery, and only bites in CI — forcing the strip (`git rm -r --cached
# .resume/`) as part of preparing the PR.
set -euo pipefail

# Local no-op: only enforce inside CI. `CI` is set by GitHub Actions and every
# other mainstream CI provider. Locally, intermediate .resume/ commits are fine.
if [ -z "${CI:-}" ]; then
  exit 0
fi

tracked="$(git ls-files -- .resume/)"

if [ -n "$tracked" ]; then
  cat >&2 <<EOF
✖ Merge blocked — this branch still tracks .resume/ files:

$(printf '  %s\n' $tracked)

  Files under .resume/ are worktree-local working artifacts (crash-recovery
  plans, resumable-skill state). They are gitignored and MUST NOT reach the
  default branch (spec/project/parallel-working-copies/ §"Planen vor der Arbeit").

  Committing them DURING work for a checkpoint is fine, but preparing the PR
  must untrack them so they are not part of the merge. Strip them and push:

    git rm -r --cached .resume/
    git commit -m "chore: drop worktree-local .resume/ artifacts"
    git push

  The working-tree copies stay on disk (they are gitignored); only the git
  tracking is removed.
EOF
  exit 1
fi

exit 0
