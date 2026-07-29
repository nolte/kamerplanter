# ADR-011: E2E Smoke as a Merge Gate for `develop`

**Status:** Accepted
**Date:** 2026-07-26
**Decision-makers:** Kamerplanter Development Team

## Context

Issue #773 asked whether the `E2E smoke (compose, light)` job (workflow `e2e-smoke.yml`, Compose-based, running `scripts/run-e2e.sh --smoke`) should block merges into `develop`.

The trigger was a concrete incident: PR #763 was merged while `E2E smoke (compose, light)` was **red** — with the assertion "TC-004-092 FAIL (View 3): exactly one new pending '— watering' follow-up task must exist, found 0". `develop` then carried a permanently red E2E check, and the underlying backend defect went undetected until issue #770 exercised the scenario directly and surfaced it. Neither code review nor the merge gate caught the defect, because only `static / Static CI Tests` was registered as a required context on this repository.

Verifying the starting position via the GitHub API (not the UI) confirmed two findings:

1. `develop` did in fact carry only a single required context (`static / Static CI Tests`), with `strict: true` and `enforce_admins: true` at 0 required approvals.
2. `.github/settings.yml` had **never** carried a `branches:` block, throughout its entire history. The state actually enforced live by GitHub therefore existed only in GitHub's own state — contrary to `spec/project/pull-request-workflow` §74/§119, which require an as-code declaration of required checks.

Before deciding, the actual track record of `E2E smoke (compose, light)` was measured, not estimated: 13 consecutive green runs since 2026-07-25 (every prior red run traces back to the defect fixed in #770), with a real-world runtime of about 11 minutes. The second E2E workflow, `e2e-nightly.yml` (a full 5-profile matrix: light, full, mobile, tablet, full-mobile), was red on 14 of 14 runs by contrast; issue #746 is open, PR #759 is unmerged. The stabilization precondition named in the original issue therefore concerns the nightly profiles — not the gate candidate being decided here.

## Decision

`E2E smoke (compose, light)` becomes a required context on `develop`, alongside `static / Static CI Tests` (`.github/settings.yml`, `strict: true`, `enforce_admins: true`).

The selection of **when** the suite runs at all is made via a deny-by-default allowlist of runtime-inert paths (`docs/`, `spec/`, `project/`, `.audits/`, `.resume/`, `.claude/`, `styles/`, `*.md`, `.github/**` except `e2e-*.yml`, `mkdocs.yml`, `.vale.ini`, `LICENSE`, `.gitignore`, `CODEOWNERS`, `Taskfile.yaml`, `.pre-commit-config.yaml`), evaluated in an upstream `changes` job (`dorny/paths-filter`) with a job-level `if:` on the `smoke` job — **not** via a path filter on the trigger.

The reason for this conditional instead of a trigger path filter: a required check whose workflow never starts because of a path filter on the `pull_request` trigger never reports a status, leaving the pull request stuck on "Expected — waiting for status to be reported" — and with `enforce_admins: true` there is no override for that. GitHub explicitly advises against applying path filters to required workflows for exactly this reason. A job skipped by a job-level conditional, by contrast, correctly reports `Success`. The trap is not hypothetical: 11 of the last 30 merged pull requests (37%) would never have produced the check under a plain trigger path filter.

The gate goes live immediately with this pull request, without waiting for the nightly stabilization (#759, #768) — their outcome concerns a different profile that remains advisory.

## Consequences

### Positive

- The failure mode from #763 — a red-merged E2E check masking a real backend defect — cannot recur without blocking the merge.
- The required-checks configuration now exists as code (`.github/settings.yml`, `branches:` block) instead of only in GitHub's state — resolving the second finding from the context.
- Supersedes R2 in `project/requirements/e2e-ci-selenium.md`, which deliberately kept E2E checks non-required while their flake behavior was unknown; that guard condition is now answered by the measured track record.

### Negative

- Pull requests touching at least one runtime-relevant path incur roughly 11 minutes of additional merge latency. Measured against the corpus of the last 45 merged PRs, 33% skip the suite entirely (allowlist applies).
- Because of `strict: true`, every remaining open PR turns `BEHIND` after each merge into `develop` and must rebuild. Measured: 8 of 12 dependency PRs trigger the E2E suite; a batch of 5 Renovate PRs therefore costs roughly 55 minutes instead of roughly 10 minutes. This trade-off is deliberately accepted — relief via a merge queue is routed to its own follow-up issue, not part of this decision.
- The allowlist is security-relevant, not merely a performance optimization: a *missing* entry only costs one unnecessary, roughly 11-minute run (fail-safe). A runtime path *wrongly added* to it, however, silently disables the gate (fail-open). The list must be re-checked whenever a new top-level directory structure appears.
- The conditional itself is fail-safe by construction: the suite is skipped **only** when the selection job succeeded *and* reported the diff as inert. If it fails, the suite runs. This is load-bearing — `always()` merely causes the condition to be evaluated at all, it does not make it true. Without the explicit `needs.changes.result` check, a failed job's outputs would be empty strings, the job would be skipped, and a skipped job reports the required check as `Success` — the gate would go green without the suite ever running.

### Rollback rule

If the required check fails twice within 7 days without the failure being reproducibly traceable to a code change, the context is removed via a **regular pull request** against `.github/settings.yml` — never a one-off bypass; `enforce_admins` stays `true`.

## Alternatives considered

| Criterion | Complexity/size score | Learned test selection | Coverage-based TIA | Remove the path filter outright | Duplicate workflow (same job name) | Merge queue | Status quo (document only) | **Chosen** |
|---|---|---|---|---|---|---|---|---|
| Effect across the 45-PR corpus | only 4/45 additional PRs caught (~1 min on average), while missing exactly the riskiest cases (#718, #747, #716) | unknown — no historical corpus exists | unknown — a project of its own | 100% (every PR runs), but with no gain on docs-only PRs | technically possible, but fragile | addresses latency, not selection | no gate — the failure mode from #763 persists | Suite runs on 67% of PRs, no misjudgments on risky changes |
| Data basis | size does not correlate with risk (Nagappan & Ball, ICSE 2005: absolute churn is not a viable predictor, only relative churn — and even that predicts defect density, not test coverage) | needs a large corpus of historical test outcomes (Machalica et al.); kamerplanter has ~3 days of E2E CI history | needs coverage from the system under test — instrumented containers across process boundaries | no data basis needed | no data basis needed | no data basis needed | no data basis needed | deny-by-default, no statistical calibration needed |
| Operational risk | misjudgments on tenant-relevant changes | insufficient data basis available | a project of its own, and it answers the wrong question ("which tests" instead of "does the suite run") | ~11 min on every PR, including docs-only | two workflows sharing the same job name; a later rename silently breaks the gate | touches the inherited `automerge` workflow from `gh-plumbing` — its own outcome | failure mode from #763 persists | fail-safe on a missing entry, fail-open risk known and documented |
| Decision | rejected | rejected | rejected (own project) | rejected | rejected | deferred (follow-up issue) | rejected | **chosen** |

Detailed rationale:

- **Complexity/size score instead of an allowlist:** measured on a prototype against the last 45 merged PRs. The yield over the plain allowlist is only 4 additional PRs out of 45 (about 1 minute on average), while it misjudges exactly the riskiest changes — #718 (1 file, 1 line, tenant check), #747 (tenant ownership), and #716 would have run untested. Size does not correlate with risk.
- **Learned test selection** (Machalica et al., Predictive Test Selection): requires a large corpus of historical test outcomes; kamerplanter has about 3 days of E2E CI history — too little to calibrate.
- **Coverage-based test impact analysis** (Datadog TIA, pytest-testmon): would need coverage from the system under test, i.e. instrumented containers across process boundaries. A project of its own that also answers the finer-grained question of "which tests" rather than the binary gate decided here.
- **Removing the path filter outright** (suite runs on every PR): the simplest option, but costs roughly 11 minutes even on pure docs PRs with no gain whatsoever.
- **Duplicate workflow with an identical job name** (a path GitHub also documents): rejected, because two workflows would have to carry the same job name, and a later rename would silently break the gate.
- **Merge queue:** effectively addresses the latency consequence, but touches the inherited `automerge` workflow from `gh-plumbing` — its own outcome with its own issue, not part of this decision.
- **Keeping the status quo and only documenting it:** rejected, because the failure mode from #763 would remain unchanged.

## References

- Issue #773 — the originating question of whether `E2E smoke (compose, light)` should become required
- PR #763 — the red-merged E2E check that triggered this decision
- Issue #770 — surfaced the underlying backend defect (documented in ADR-010)
- `project/requirements/e2e-smoke-merge-gate.md` — the full, operator-confirmed requirements record (R1–R10)
- `project/requirements/e2e-ci-selenium.md` — R2, marked superseded
- `.github/workflows/e2e-smoke.yml` — `changes` job (`dorny/paths-filter`) + job-level `if:` on the `smoke` job
- `.github/settings.yml` — `branches:` block for `develop` with both required contexts
- `spec/project/pull-request-workflow` §74/§77/§119 — as-code requirement for required checks, rollback procedure
- Issue #746, PR #759, PR #768 — nightly stabilization, out of scope for this decision
- Nagappan, N.; Ball, T. (2005): "Use of Relative Code Churn Measures to Predict System Defect Density", ICSE 2005
- Machalica, M. et al. (2019): "Predictive Test Selection", ICSE-SEIP 2019

---

## Addendum 2026-07-28 — merge-train latency measured and deliberately accepted (#792)

The latency accepted under "Consequences" above was measured, because the
estimate in #773 was derived from pull-request history. Window
2026-07-27 15:00 – 2026-07-28 17:00, during which 14 pull requests merged into
`develop`:

**60 `e2e-smoke` runs.** A single Renovate container-digest bump
(`renovate/ollama-ollama-latest`) accounted for **10** of them — 7 completed, 3
cancelled by the next update — roughly 110 minutes of runner time for a change
that never differed between runs. Every rerun was `strict: true` reacting to
*another* pull request's merge.

So the cost driver is `strict: true`, not the gate itself.

**Options evaluated (#792):**

- **Merge queue** — keeps the guarantee and removes the serial cost by testing
  the projected merge result. Blocked on a cross-repository prerequisite:
  `nolte/gh-plumbing`'s `reusable-automerge.yaml` (pinned at `bab4f9d29`) carries
  no `merge_group` trigger and merges via `pascalgn/automerge-action` — a queue
  merges too, and the two are mutually exclusive. The portfolio commons would
  need a queue-aware mode first.
- **Drop `strict: true`** — removes the cost immediately and locally, but gives
  up exactly the guarantee it exists for: that a pull request green on its own is
  still green once merged.
- **Accept the cost** — chosen.

**Reasoning:** this is unattended machine time, not maintainer time. Revisit once
pull-request volume rises enough that the drift window — how long `develop` and
the open pull requests disagree — produces real conflicts rather than just
reruns. The figure is also recorded beside `strict: true` in
`.github/settings.yml`, where it will be read the next time branch protection is
touched.
