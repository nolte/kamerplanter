---
artifact-type: issue-orchestration-analysis
repo: "nolte/kamerplanter"
issue: "570"
classification: "infra"
secondary-classes: ["spec-change"]
route: "direct"
status: done
created: "2026-07-12"
---

# Issue Orchestration — Pre-analysis

## Issue metadata

- **Repository**: nolte/kamerplanter
- **Issue**: #570 — Implement single-source-of-truth for Python backend dependencies (Option A, follow-up to #566)
- **URL**: https://github.com/nolte/kamerplanter/issues/570
- **Labels**: chore, dependencies, backend
- **Linked items**: #566 (audit issue, closed), PR #569 (audit report, MERGED). No open implementation PR; `closedByPullRequestsReferences` empty.
- **Prior art checked**: `spec/analysis/python-dependency-management-audit.md` (merged via #569) — the analysis basis. No `project/features/` entry, no `project/roadmap.md` item, no open PR implements this. PR #563 (pydantic-core drift) restored the compile header + `requirements-dev.txt` but left the architecture untouched. No merged fix closes the issue.

## Classification

- **Primary class**: infra
- **Secondary class(es)**: spec-change
- **Rationale**: Restructures the Python build/CI/Renovate/dependency-tooling flow (infra); one work package rewords NFR-009 §5.2 (spec-change). The `infra → workflow-health-triage` short-circuit does NOT apply — this is a build-architecture change, not a red-CI triage. Operator-confirmed 2026-07-12.

## Scope

- **In scope**: Make `pyproject.toml` the abstract SSOT with upper bounds; recompile both locks; make every consumer (prod image, dev image, CI lint/test + coverage) install from the committed lock; add a lock-staleness CI check; add `pip-audit` + `pip-licenses` CI gates; repoint Renovate to the `pep621` manager with `pipCompileOutput`; add a `Taskfile.yaml` `deps:compile` target; reword NFR-009 §5.2 to remove the §5.2-vs-§2.3/§6.1 contradiction. Closes the 5 NFR-009 deviations named in the issue (§2.1, §2.3/§6.1, §4.1, §4.3, §6.1).
- **Out of scope**: Frontend (npm) dependency flow; TimescaleDB/Arango client version policy; any runtime code change. `--generate-hashes`/`--require-hashes` is evaluated (issue step 2) but only enabled if all native wheels resolve on Python 3.14 — otherwise documented why not (not forced).

## Route

- **Decision**: direct
- **Rationale**: One coherent outcome (SSOT dependency flow), one PR strand, no new/retargeted roadmap item. Operator-confirmed 2026-07-12.
- **Pipeline hand-off**: n/a

## Requirements gate

No `project/requirements/` artefact exists for #570. **Operator override recorded (2026-07-12):** the requirements are specified at `τ_high`-equivalent detail by the merged formal audit (`spec/analysis/python-dependency-management-audit.md`, #566/#569) with explicit, testable acceptance criteria in the issue body. `requirements-elicit` skipped by operator decision.

## Work packages

The issue's 7 sequenced steps are recorded here as atomic, individually-testable packages for traceability. **Dispatch bundling (see Dispatch note):** P1–P6 all target `fullstack-developer` and all mutate the same tightly-coupled lock/build/CI surface (the recompiled lock is the shared pivot), so they are dispatched as **one** `fullstack-developer` invocation to avoid lock-drift-between-agents and shared-tree write conflicts (per the "schreibende Agenten auf geteiltem Tree sequenziell" rule). P7 (spec-change, disjoint file) is a separate dispatch.

### P1 — Tighten pyproject.toml + recompile locks

- **Problem statement**: `[project].dependencies` and the `dev` extra carry only `>=` lower bounds, no upper bounds (NFR-009 §2.1) → non-reproducible resolution. Add upper bounds and recompile both `requirements.txt` and `requirements-dev.txt`.
- **Acceptance criteria**: Every direct dep in `pyproject.toml` (runtime + dev) has a bounded constraint; both locks recompiled from it and internally consistent (a fresh `pip-compile` produces no diff).
- **Touched files / artifacts**: `src/backend/pyproject.toml`, `src/backend/requirements.txt`, `src/backend/requirements-dev.txt`
- **Specialist**: fullstack-developer
- **Depends on**: none

### P2 — Prod Dockerfile consumes the lock

- **Problem statement**: `Dockerfile:52` prod stage runs `pip install .` (reads pyproject), and `requirements.txt` is copied but never installed. Switch to `pip install -r requirements.txt` then `pip install --no-deps .`. Evaluate `--generate-hashes`/`--require-hashes` against native wheels (`weasyprint`, `psycopg[binary]`, `aquacropeto`) on Python 3.14; enable if all resolve, else document why not.
- **Acceptance criteria**: Prod image installs all deps from the lock; only the app package installs via `--no-deps .`; image builds green. Hashes enabled or a documented rationale present.
- **Touched files / artifacts**: `src/backend/Dockerfile`
- **Specialist**: fullstack-developer
- **Depends on**: P1

### P3 — CI consumes the lock + staleness check

- **Problem statement**: `backend.yml:34` (lint/test) and `:51` (coverage) install `-e ".[dev]"` from pyproject. Switch to `-r requirements-dev.txt`; add a `pip-compile --dry-run`/diff check failing when the committed lock is stale vs pyproject.
- **Acceptance criteria**: Both CI jobs install from the dev lock; CI fails when the lock is stale relative to `pyproject.toml`.
- **Touched files / artifacts**: `.github/workflows/backend.yml`
- **Specialist**: fullstack-developer
- **Depends on**: P1

### P4 — pip-audit + pip-licenses CI gates

- **Problem statement**: No `pip-audit` (NFR-009 §4.1) and no `pip-licenses` allowlist gate (§4.3). Add a `pip-audit -r requirements.txt` job (PR + push to develop + weekly) and a `pip-licenses` allowlist gate.
- **Acceptance criteria**: `pip-audit` and `pip-licenses` run in CI on the committed lock; license allowlist enforced.
- **Touched files / artifacts**: `.github/workflows/backend.yml` (or a new workflow file)
- **Specialist**: fullstack-developer (no dedicated dependency-audit specialist in the live catalog; security-sensitive → verified by `security-review` skill at operation 6)
- **Depends on**: P1

### P5 — Repoint Renovate to pep621 + pipCompileOutput

- **Problem statement**: `renovate.json5:37-73` uses 3× `pip_requirements` rules editing only the decorative locks. Replace with `pep621` manager rules on `src/backend/pyproject.toml` + `postUpdateOptions: ['pipCompileOutput']` (or `lockFileMaintenance`), preserving grouping (fastapi-stack, minor/patch, major). Confirm no inherited/preset config re-enables a stray `pip_requirements` scan.
- **Acceptance criteria**: A Renovate bump produces a single PR that moves the `pyproject.toml` constraint AND recompiles the locks atomically; existing groups preserved; no stray `pip_requirements` scan.
- **Touched files / artifacts**: `renovate.json5`
- **Specialist**: fullstack-developer
- **Depends on**: P1

### P6 — Taskfile deps:compile target

- **Problem statement**: No one-command local lock regeneration. Add a `Taskfile.yaml` `deps:compile` target wrapping both `pip-compile` commands.
- **Acceptance criteria**: `task deps:compile` regenerates both locks in one command with the same flags CI's staleness check uses.
- **Touched files / artifacts**: `Taskfile.yaml`
- **Specialist**: fullstack-developer
- **Depends on**: P1 (must match P1's compile flags)

### P7 — Reword NFR-009 §5.2

- **Problem statement**: NFR-009 §5.2 (`spec/nfr/NFR-009_Dependency-Management.md:598-605`) blesses `pip install .` for build verification, contradicting §2.3/§6.1. Reword so build verification uses `pip install --no-deps .` after `-r requirements.txt`.
- **Acceptance criteria**: §5.2 no longer contradicts §2.3/§6.1; DE-canonical + EN-mirror kept in sync per DOCS.md.
- **Touched files / artifacts**: `spec/nfr/NFR-009_Dependency-Management.md` (+ EN mirror if present)
- **Specialist**: nolte-shared:spec
- **Depends on**: none (disjoint file; dispatched after P1–P6 to keep shared-tree writes sequential)

## Dependency ordering

`P1 → {P2, P3, P4, P5, P6}` (all consume P1's recompiled lock). `P7` independent (disjoint file). Dispatch order: **bundle[P1→P6] (fullstack-developer)**, then **P7 (nolte-shared:spec)**.

## Verification (operation 6)

- **Quality (orchestrator-run in worktree):** ruff check + ruff format ✅; `backend.yml` valid YAML with 3 new gates (`lock-staleness`, `pip-audit`, `pip-licenses`); Taskfile `deps:compile` present; **lock idempotency byte-identical** (re-`pip-compile` → same sha256) ⇒ staleness gate green, no #563 drift; renovate.json5 schema-validated (Renovate 42.99.0); no app-code change ⇒ pytest unaffected.
- **Security-review (general-purpose, worktree diff):** **PASS-WITH-NOTES**. #563 build-reproducibility gap closed for runtime deps. No Critical/High. Medium (external preset `enabledManagers`) already cleared by orchestrator (common.json@v1.1.25 has no such pin). Positively verified: Actions SHA-pinned, no `pull_request_target`, no `continue-on-error` masking a gate, pip-audit `--no-deps` on the full lock misses no transitive CVE, license allowlist explicit (no wildcard; GPL/AGPL/UNKNOWN reject), no automerge loosening for Python/security/major.
- **Applied hardening (fullstack-developer follow-up):** `pip-audit --strict --desc` (NFR-009 §4.1 template), `pip-tools` pinned in staleness job + Taskfile (deterministic gate), weekly dev-lock `pip-audit`. **Documented residual (Low, not #563-class):** PEP-517 build-isolation pulls setuptools/wheel un-hashed (build tooling only, pure-Python app package); license ignore-list is version-independent for 4 permissive packages.

## Risks

- **Native-wheel hash resolution** (P2): `weasyprint`/`psycopg[binary]`/`aquacropeto` may lack hashes for all Python 3.14 wheels → mitigation: evaluate first, enable `--require-hashes` only if all resolve, else document. Non-blocking.
- **Renovate preset re-enabling pip_requirements** (P5): an inherited preset could re-scan the locks → mitigation: explicitly confirm no stray scan after repoint.
- **Lock-drift between agents**: mitigated by bundling P1–P6 into one dispatch; P7 touches a disjoint file dispatched sequentially.
- **Security-sensitive paths** (P4 adds `pip-audit`/`pip-licenses` gates; dependency locks): before PR, the `security-review` skill MUST verify the produced diff (dependency-tooling + CI security gates). `code-security-reviewer` agent not present in the live catalog; `security-review` (harness built-in) covers the diff verification.

## Open questions

none — all three gates (requirements override, classification, route) operator-confirmed 2026-07-12.

## Dispatch log

- 2026-07-12 bundle[P1–P6] dispatched to `fullstack-developer` — all 6 done & locally verified. Upper bounds on all 28 runtime + 8 dev deps; both locks recompiled idempotently (zero version drift). Prod Dockerfile + dev stage now `pip install --require-hashes -r requirements*.txt` + `--no-deps .` (**hashes enabled**, all native wheels resolve cp314/abi3). CI lint-test+coverage install from dev lock; new `lock-staleness`, `pip-audit` (PR+push+weekly), `pip-licenses` allowlist jobs. Renovate: 3× `pip_requirements` → `pip-compile` manager (deviation from literal `pep621`+`pipCompileOutput` — the latter is an invalid Renovate option; `pip-compile` manager natively moves constraint AND recompiles lock in one PR, groups preserved; config schema-validated). Taskfile `deps:compile` added. Python 3.14.6, pip-tools 7.5.3. **Follow-ups for orchestrator:** (a) confirm inherited preset `github>nolte/gh-plumbing//renovate-configs/common#v1.1.25` doesn't pin `enabledManagers` excluding `pip-compile`; (b) 3 new jobs are real gates but not in branch protection (only `static` required) — operator may add them; (c) 4 permissive licenses (python-dateutil, uvloop, qrcode, pyphen) explicitly allowlisted with inline justification.
- 2026-07-12 P7 dispatched to `general-purpose` (worktree-isolated) — nominal specialist `nolte-shared:spec`, but a skill runs in-thread against the primary checkout, which the worktree-isolation hard rule forbids; executed via worktree-scoped generalist following `spec/style-guides/DOCS.md`. **Done** — §5.2 Build-Verifikations-Tabelle Backend-Zeile: `pip install .` → `pip install -r requirements.txt && pip install --no-deps .` (Beschreibung „Abhängigkeitsauflösung" → „Lock-Installierbarkeit"). No further `pip install .` contradiction in §5.2. Contradiction with §2.3/§6.1 resolved. File: `spec/nfr/NFR-009_Dependency-Management.md`.

**Follow-up (a) resolved by orchestrator:** inherited preset `common.json@v1.1.25` has no `enabledManagers` pin (only Vale `customManagers`) → `pip-compile` manager is active by default; the new Renovate rules fire. P5 risk cleared.
