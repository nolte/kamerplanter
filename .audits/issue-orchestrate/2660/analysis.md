# Pre-analysis: #2660 — accept and dismiss suggested tasks (REQ-053 WP 8.17)

> Run-scoped artifact, removed with `git rm` before the PR merges.

## Issue
- #2660 `feat(tasks): accept and dismiss suggested tasks, suggestions section in the bed care tab (WP 8.17)`, author `nolte` (trusted), milestone REQ-053 Welle 8. Handed over by partition `2026-11-06-req053` (single).

## Classification
- **Primary:** feature-request — new endpoints (GP-API-040) and a UI section (GP-FR-086). No secondary.

## Requirements gate
- **Operator override (standing wave-8 authorisation):** the requirement artefact is REQ-053 v1.10 GP-FR-086 (`spec/req/REQ-053_Grafische-Garten-Beetplanung.md:818`), GP-API-040 (`:1618`, "Ab Gärtner"), E-02, plus the issue's acceptance lines; #2643 Q3 answer 2026-11-03: "ship accept/dismiss and the UI section without a producer". No `project/requirements/` artefact elicited.

## Established facts (origin/develop b686929c5 / 46ce435b5)
- `Task.suggested: bool = False`, `Task.suggestion_reason` exist — `src/backend/app/domain/models/task.py:161-163`; read filters already exclude suggestions null-safe (`t.suggested != true`) in `garden_plan_repository.py:309,348`, `plant_state_repository.py:231`, `watering_queries.py:60`.
- Response schema already carries `suggested`/`suggestion_reason` — `api/v1/tasks/schemas.py:311-312`.
- GP-API-040 not mounted (`git grep accept-suggestion` → no hit; REQ-053:78 says "fehlt").
- No producer exists (E-02: belongs to ADR-008 phase 2, REQ-053:1857) → the feature ships **inert** in production; tests seed suggestions through the repository.

## Scope
- In: `POST /api/v1/t/{slug}/tasks/{key}/accept-suggestion` (→ `suggested = false`, task stays), `…/dismiss-suggestion` (→ status cancelled with reason, no `care_event`), 409 when `suggested != true`, grower+ (viewer 403), cross-tenant 404; service method `*, tenant_key: str` with ownership check inside; "Vorschläge" section in the bed care tab with `suggestion_reason`, rendered only when suggestions exist; DE/EN i18n; docs DE/EN; REQ-053 status rows (:70, :78) updated.
- Out: any producer (ADR-008 phase 2); reach-into watering/zone demand (GP-FR-113).

## Work packages
| Id | Problem | Acceptance | Files | Specialist | Depends |
|---|---|---|---|---|---|
| WP-1 | Backend GP-API-040 | integration: accept/dismiss, non-suggestion 409, viewer 403, cross-tenant 404; guard tests (keyed writes take tenant, route walk, route consumers pin, write-route gates) green | `domain/services/task_service.py`, `api/v1/tasks/tenant_router.py`, tests | fullstack-developer | — |
| WP-2 | Frontend section | vitest + axe for the section; empty → not rendered | `features/gardenPlanner/care/{BedCareTab,SuggestionList}.tsx`, api client, i18n | fullstack-developer (same dispatch, one strand) | WP-1 |
| WP-3 | Docs + spec status | `mkdocs build --strict` in CI; REQ-053 §12/§21 status rows | `docs/{de,en}/`, `spec/req/REQ-053*.md` | fullstack-developer (same dispatch) | WP-1, WP-2 |

## Route
- Implement directly: one outcome, one PR strand, no roadmap item.

## Risks
- Inert feature (no producer) — named in the PR.
- Dismiss must not write a `care_event` and must not count as completion; the cancelled task must leave open-task counters.

## Approval
- Self-approved under the standing wave-8 authorisation (no open decision).
