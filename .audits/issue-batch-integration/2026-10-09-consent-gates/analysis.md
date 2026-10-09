# Group pre-analysis: 2026-10-09-consent-gates

> Run-scoped artifact. Committed on the integration branch, removed with a fix-forward
> `git rm` before the bundle merges. It must never reach the default branch, and it must
> never be hidden behind a `.gitignore` entry.

## Scope of this analysis

**Research question:** Do #2174, #2175 and #2159 share one defect class strongly enough to be one bundle, and what does each need so the bundle is reviewable in one sitting?

**The group's single logical change, in one sentence:** Every optional processing path that skips its recorded consent today (interactive reference contribution, `/knowledge/ask`, frontend Sentry) checks that consent and fails closed.

**Out of scope:** the automatic reference path (`photo_router.py:184` → `feed_user_reference`) unless the #2174 run shows it also skips the consent (then: file, don't widen); the daily AI budget for `/knowledge/ask` (needs a tenant, #2110 territory); #2173 (same pipeline, different defect, runs after this group); a general "every route names its consent" guard (see Process finding).

**Tier:** 2 — several files in two components (backend, frontend), no published contract changes unless #2175 removes the route (then OpenAPI changes, see Risks).

## Members

| Issue | Class | Admitting predicate | Evidence |
|---|---|---|---|
| #2174 | security | thematic coupling | `reference_contribution` is defined at `consent_engine.py:186-204` and read by no check; `ReferenceImageService.contribute_user_reference` (`reference_image_service.py:189`) has no consent call; route `recognition/tenant_router.py:166-229` |
| #2175 | security | thematic coupling | `knowledge/router.py:60-80` has the per-account limit only; no consent or toggle. **Weakest member:** `consent_guard.py:3-6` and `glossary_service.py:14` say "a knowledge question without tenant context needs no consent", so consent is a design decision here, not a missing line |
| #2159 | bug | thematic coupling | `errorTracking.ts:207-271` `initErrorTracking()` reads no consent and runs unconditionally from `main.tsx:54`; **`ConsentBanner` is mounted nowhere** (`git grep ConsentBanner origin/develop -- src/frontend/src` outside tests: only its own declaration, `ConsentBanner.tsx:48,70,74`) |

**Dependency ordering:** independent. Suggested order #2174 → #2175 → #2159 (cheapest and clearest first; the two members with an open question last, so a removal leaves a working bundle).

**Shared touch surface:** none by file. The members share the consent concept: `ConsentGuard.require_consent` (`consent_guard.py:36-39`) for #2174 and #2175, and the stored purpose decision for #2159.

## Mode decision

**Mode:** B — sub-branch per member.

**Reason:** removability criterion. #2175 has uncertain acceptance (the issue itself asks "remove the route, or put it behind the same admission"); #2159 hides a prerequisite (no mounted banner, no consent store) that can make it larger than the bundle should carry. Either may have to be dropped. #2174 and #2175 are `security`-classified, so their classification is confirmed once more at dispatch.

## Structural finding

**Cluster shape:** class cluster, weak — one recurring class (a consent purpose or consent decision exists, the processing path never reads it), three different mechanisms (service-level `ConsentGuard`, a route admission decision, a frontend store). The class holds fully for #2174, only conditionally for #2175 (not if the route is removed), and for #2159 only after a consent source exists on the client.

**Root cause or defect class:** a purpose is offered in `ConsentEngine.PURPOSES` or in a banner without a read at the processing path.

**Process finding:** `tests/unit/guards/test_consent_purposes_are_read.py` states its own limit: "'Referenced' is weaker than 'read by a consent check': a key that only appears in a label table elsewhere passes" (module docstring). `reference_contribution` is declared but its only non-engine hits in `app/` are settings names and a task module, not a consent check. Whether the guard passes it by a string literal elsewhere is **not measured** here; the #2174 run measures it first. Not filed as an issue yet (see Open questions).

**Preventive change:** strengthen that guard from "referenced" to "passed to `has_consent` / `require_consent` / `is_processing_allowed`" (AST call argument), so a purpose without a read fails the build.

**Recurrence fed to the portfolio loop:** class "consent purpose without a read": 2 earlier instances named in the guard's docstring (`hibp_check`, `external_enrichment`, retired in #2136) plus this group → 3.

## Plan approval

**Authorised by:** `2026-10-09-consent-gates/plan-approval`, covering the members, mode, and order above. Revoked for undispatched members by any structural regression until re-approved.

**Group requirement artifact (class cluster only):** operator decision 2026-10-09: the spec anchors serve as the requirement, no `requirements-elicit` run. Anchors: REQ-034 §4 (reference contribution consent), UI-NFR-013 CI-001 (:122, Sentry init only after `error_tracking` consent), NFR-001 SE-001/SE-005. Each member's run traces its acceptance to these; a condition they don't cover falls back to the member's own elicitation.

**Operator decisions at the plan gate (2026-10-09):** #2175 → **B** (keep the route behind tenant admission, not removal); requirement artifact → spec anchors; #2159 → stays in the bundle, split off if the consent store exceeds a small hook; guard strengthening → done inside #2174, no separate issue.

## Completeness matrix

Columns derived from the repository: `pyproject.toml`/`package.json` (source), `spec/`, backend and frontend tests, `docs/{de,en}`, OpenAPI export, no workflow change.

| Member | Backend source | Frontend source | Spec | Tests | Docs | OpenAPI / route index |
|---|---|---|---|---|---|---|
| #2174 | `ReferenceImageService.contribute_user_reference` takes a `ConsentGuard` and calls `require_consent(user_key, "reference_contribution")` before work (`reference_image_service.py:189`); wire in `get_reference_image_service` (`dependencies.py:2422`); skip in non-full mode like `cv_diagnosis_service.py:206-218`. Check: `task test:backend:unit` | not applicable — the UI switch stays; the API now enforces it | `spec/req/REQ-034` §4: add the AK that the API refuses without consent; check: `git diff --stat spec/` | red test through the route in `tests/api/test_recognition_router.py`: no consent → 403 `CONSENT_REQUIRED`; granted → 2xx; plus strengthen `tests/unit/guards/test_consent_purposes_are_read.py` from "referenced" to "passed to `has_consent`/`require_consent`/`is_processing_allowed`" (AST). Check: `task test:backend:api` and `task test:backend:unit` | `docs/{de,en}/changelog/unreleased.md` entry; check: `task docs` build | route unchanged, 403 added: `task openapi:export` + `task openapi:lint` |
| #2175 | **Decision B:** move the ask route behind a tenant-scoped router with `require_ai_tenant_enabled` + consent (`require_consent`, purpose per REQ-031) + the daily AI budget (`get_ai_call_budget`, `dependencies.py:2254`), pattern `ki_assistent/tenant_router.py:42`; the old `/api/v1/knowledge/ask` path is removed. Check: `task test:backend:unit` | not applicable — no frontend consumer (`git grep "knowledge/ask"` over `src/frontend/src` empty) | `spec/stack.md:777,790` path update; REQ-031 admission list; check: `git diff --stat spec/` | replace `tests/api/test_knowledge_ask_per_user_limit.py` with tenant-route tests: toggle off → 403/404, no consent → 403 `CONSENT_REQUIRED`, over budget → `AiBudgetExceededError`. Check: `task test:backend:api` | `docs/{de,en}/user-guide/ai-providers.md:266`, `reference/environment-variables.md` RATE_LIMIT_INFERENCE row, changelog (breaking path); check: `task docs` | path changes: `task openapi:export`, `task openapi:lint`, `task check:route-consumers`, `task check:frontend-calls-served` |
| #2159 | not applicable — backend half landed in #2136 (`observability/event_user.py:11-41`) | gate `initErrorTracking()` on a consent source; close the SDK on revoke (`errorTracking.ts` has no teardown today); mount the banner or add the store the gate reads (`ConsentBanner.tsx:29-38` `readConsent` is module-private). Check: `task test:frontend`, `task lint:frontend`, `task typecheck` | UI-NFR-013 CI-001/CI-004 `useConsent` hook: implement or mark; check: `git diff --stat spec/ui-nfr` | `src/test/observability/errorTracking.test.ts`: no event without consent, closes on revoke. Check: `task test:frontend` | `docs/{de,en}/deployment/fehler-tracking.md:73` + changelog; check: `task docs` | not applicable — no API change |

## Risks

- **#2159 grows.** With the banner unmounted, "init only after consent" disables frontend Sentry for everyone until a consent source exists. Cost: a silent loss of error reports, or a banner/store feature larger than the bundle. Mitigation: Mode B; drop it into its own issue if the store is more than a small hook.
- **#2175 B changes the public path.** The old `/api/v1/knowledge/ask` disappears and a tenant-scoped one appears; an external consumer (Home Assistant, Grafana) leaves no trace in the repo (`scripts/route_consumer_exemptions.yaml` tracks only known ones). Cost: a breaking change for an unknown caller. Mitigation: changelog entry as breaking; no deprecated alias unless the operator asks. B is also the largest member (new router wiring, budget, consent) and the first candidate to drop under Mode B.
- **Second contribution path.** `photo_router.py:184` (`feed_user_reference`) may also skip the consent. Cost: #2174 fixed only the interactive half. Mitigation: the #2174 run reads it first and files, rather than widens.
- **Light mode.** `cv_diagnosis_service.py:206-218` skips consent when `kamerplanter_mode != "full"`; the same exemption must apply (UI-NFR-013 CB-001), or Light mode breaks.

## Open questions for the operator

- Answered 2026-10-09: #2175 B, spec anchors as requirement, #2159 stays (split if the store grows), guard strengthening inside #2174. Remaining: explicit approval of this updated plan.

## Member results

| Member | Specialist | Check | Actual output |
|---|---|---|---|
| #2174 | nolte-engineering:fullstack-developer | asserted cause (no consent read on the interactive path): `grep -n -i consent app/domain/services/reference_image_service.py` | no match at 917ccd7bc; route only docstring mentions. Verified. Prior-art risk "automatic path also open": refuted, `reference_contribution_tasks.py:69-72` checks it |
| #2174 | same | red/green (check call removed via `cp`, restored) over 5 test files | red: `10 failed, 77 passed`; green: `87 passed`; order falsification (check moved before `embed`): `8 failed, 24 passed`; wiring removed from `dependencies.py`: `4 failed, 20 passed` |
| #2174 | orchestrator (independent) | `pytest` 7 files incl. `test_consent_purposes_are_read.py`, `test_recognition_write_gates.py` | `102 passed, 44 warnings` with `app.__file__` in the worktree |
| #2174 | nolte-engineering:code-security-reviewer | diff review (read-only, no Bash, files read at HEAD) | no Critical/Warning; gate not bypassable; order correct; two small Infos fixed directly (see Findings) |

## Group-level log (2026-10-09)
- Environment: worktree has no `.venv`; primary `.venv` lacks `prometheus_client`, uv 0.11.33 installed vs pinned 0.12.24. Tests ran with `prometheus-client==0.26.0` in a scratchpad `--target` on `PYTHONPATH`. 5 guard tests that spawn a subprocess (`test_log_redaction_has_no_residual_gaps`, `test_uncaught_exceptions_are_redacted`) fail only for that reason; CI is the proof for them.
- Open for later members: the frontend reference toggle (`PlantIdentificationPage.tsx:67`, `SpeciesListPage.tsx:183`) is shown by active adapter, not by consent or mode; it joins #2159's consent store. `pest_image_tasks.py` feeds a pest few-shot index with `user_contributed` rows without a consent purpose; spec question (REQ-010/044), not touched here, not filed.
## Deviations

| Member | Kind | What changed |
|---|---|---|
| #2174 | local adaptation | planned guard strengthening (`test_consent_purposes_are_read.py`: referenced → read by a check) dropped: the guard already passes because the automatic path reads the purpose, so it stays green with the defect present. Class sweep: no mechanical guard (writers do not share one spelling, "reachable only through a check" is a call-graph property); the route and service tests pin the one enumerable writer and the order. |
| #2174 | local adaptation | Light mode refuses (409) instead of skipping the check, per REQ-034 §4.1 Guard 2 / AC-16; operator confirmed 2026-10-09. Behaviour change: interactive contribution no longer works in Light mode. |

## Findings

| Finding | Source | Outcome | Reproduction | Issue |
|---|---|---|---|---|
| `docs/{de,en}/reference/api-reference.md:~903` lacked the consent 403 and Light 409 | member run | fixed directly (8c5ff557a, aeed2feaf) | rows now present | — |
| `tests/support/fake_consent_repo.py:27` builds "revoked" without `revoked_at` (production always sets it) | security review | fixed directly (in progress) | – | — |
| `reference_image_service.py:261` resolves the species unscoped, the automatic path uses `readable_species(…, tenant_key)` (`reference_contribution_tasks.py:79`) | security review (suspected) | reproduce first, then fixed directly (in progress) | red test pending | — |
