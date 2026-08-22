# Rescued: build-identity work from `fix/delivery-path-1210` (#1210)

**Not adopted. Does not apply cleanly. Read this before using it.**

## What this is

Uncommitted work found in the worktree `~/repos/.worktrees/kamerplanter/delivery-1210`
on 2026-08-22, alongside the digest-freshness fix that became #1247. It has
never been committed, never pushed, and has no PR. Preserved here so removing
that worktree cannot destroy it.

| File | Origin |
|---|---|
| `files/*` | the four modified files **in full**, path-flattened with `__` |
| `test_health_build_identity.py` | untracked; belongs at `src/backend/tests/api/` |

**Whole files, not a patch, deliberately.** The first attempt stored a
`git diff`, and the repository's `trim trailing whitespace` hook rewrote it —
stripping the leading space from blank context lines, which in unified-diff
format is exactly the character that marks them as context. `git apply` happens
to tolerate it; `patch(1)` does not, and a rescue that quietly degrades is worse
than no rescue. Whole files have no format to corrupt: diff them against
`develop` yourself.

## What it adds beyond `develop`

The build-identity surface it extends is **partly on develop already** —
`settings.health_expose_build_revision` and `settings.resolve_build_revision()`
exist, and `/api/health` reports `build_revision` behind that flag
(`main.py:417`). What is missing on develop:

* `UNKNOWN_BUILD_IDENTITY = "unknown"` — a named constant, with the reason: a
  word no build can produce, so "I don't know which build this is" can never be
  mistaken for an answer;
* `build_commit` and `build_timestamp` fields, i.e. a wider identity than the
  single revision;
* a 198-line `test_health_build_identity.py` covering them.

## Why it is not a branch you can merge

`git apply --3way` against `develop` @ `ed2c46187` conflicts in **three** of the
four files: `docker-publish.yml`, `settings.py`, `main.py`. Develop moved a long
way since this was written. Adopting it is a reconciliation, not a cherry-pick,
and whoever does it should decide per hunk whether develop's version or this one
is the intended end state.

## Why it is in `.audits/rescued/` and not applied

The same reason `ci/issue-1236-deployed-build-check` is a branch and not a PR:
preserving work whose adoption needs a decision is cheap, and pretending it is
ready is not. See #1236, which owns the delivery-measurement strand this belongs
to.
