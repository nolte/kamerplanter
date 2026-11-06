# Group csv-import — pre-analysis (2026-11-06)

Members: #2669 (WP 8.26, backend, M), #2670 (WP 8.27, frontend, S). Admission: dependency chain (#2670 consumes the #2669 endpoint) + shared touch surface (plan import flow). Spec: REQ-053 v1.9 §23.1 GP-FR-174, SR-016, SR-018, GP-NFR-017. Prerequisite WP 8.4 (#2647) closed.

## Structural cause
None shared beyond the feature itself: the JSON plan import (`garden_plan_import_service.py`, `plan.quota_exceeded`, rate limit `rate_limit_plan_batch`, lead-only) is the reference path; the CSV import is a second front end onto the same batch write path (containment, revision, audit). Risk: a parallel write path that skips a guard the JSON import applies. Mitigation: the CSV service parses into the same batch-create operations and calls the existing batch path — no own persistence.

## Completeness matrix
| Acceptance line | Member | Proof |
|---|---|---|
| `dry_run` writes nothing; report per faulty line | #2669 | unit (service) + api test: dry_run → no revision bump, no bed |
| Faulty line reported, rest written after confirmation | #2669 | api test: mixed file, confirm → only valid rows created |
| Quota → 422 `plan.quota_exceeded` (≤500 rows / plan quota) | #2669 | api test |
| ≤1 MiB, UTF-8 (BOM tolerated), `;` | #2669 | unit parser tests (BOM, oversize → 413/422) |
| Formula prefixes (`= + - @ \t \r`) discarded on read (GP-FR-104/145) | #2669 | unit parser tests |
| `rect` geometry in one row, gap 0.5 m | #2669 | unit test on placement |
| grower 403; cross-tenant 404; rate limit | #2669 | api + tenant-isolation route walk |
| Guards: keyed-service-writes, route consumers pin, write-route gates ceiling (2804, not raised), bounded lists | #2669 | guard tests |
| Wizard: CSV file choice, report with line errors, confirm, jump to editor | #2670 | vitest |
| axe on the wizard CSV step | #2670 | vitest-axe |
| DE/EN i18n; bundle budget `routeChunks.gardenPlanner` 120 KB not raised | #2670 | i18n parity, bundle-budget check |
| Docs DE/EN (user guide import section, API reference) + changelog | both | mkdocs strict / Vale |

## Work packages
1. #2669 backend — `fullstack-developer`: `domain/services/bed_csv_import_service.py`, parser part in `common/csv_export.py` (or a sibling `csv_import` helper), route `POST /t/{slug}/sites/{key}/beds/import-csv` in `api/v1/garden_plan/tenant_router.py`, schemas, tests.
2. #2670 frontend — `fullstack-developer`: `features/gardenPlanner/io/ImportWizard.tsx`, `ioApi.ts`, types, i18n, tests.
3. Review: `code-security-reviewer` (upload parsing, formula injection, quota, authz), usability pass on the wizard step, docs/changelog.

Plan gate: self-approved per operator mandate (feedback_req053_wave8_autonomous_run).
