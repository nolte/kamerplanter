# Pre-analysis — #1769 tenant deletion leaves domain data behind

- Issue: nolte/kamerplanter#1769 (author `nolte`, repository owner → trusted). No comments.
- Classification: `bug` (secondary `security`/privacy). Rationale: an erasure entry point
  (`TenantService.delete_tenant`) records success while personal data of the tenant survives.
- Requirements gate: operator override (repository owner, 2026-09-24/25, full autonomy); the issue
  carries explicit acceptance criteria.
- Route: implement directly (one PR strand: inventory + guard + executor + record/retry). Split out:
  personal-tenant residue after account erasure, REQ-024 soft-delete wording, R-16..R-18 retention
  purge (see "Split issues").

## Measurements (established, on 2fd9fbd34)

- `delete_tenant` (`src/backend/app/domain/services/tenant_service.py:254-268`): storage purge
  (reference vectors, pest prototypes, `attachments`, `pest_image_contributions`, `t/{key}/`),
  then `location_assignments`, `invitations`, `memberships`, the tenant document. Nothing else.
- Tenant-bearing collections derived from the source with the #1708 derivation
  (`build_inventory` in `tests/unit/guards/test_tenant_scoped_reads_are_derived.py`): 88
  (own 65, parent 15, hybrid 8). Raw-written collections with `tenant_key` and no model:
  `ha_publish_settings`; legacy backfill (`migrations/backfill_tenant_key.py`) stamped
  `pests`, `diseases`, `treatments`, `harvest_indicators`, `onboarding_states`, `user_preferences`.
- `DELETE /t/{slug}` has no platform-tenant guard (`api/v1/tenants/router.py:101`); only the admin
  route checks `is_platform` (`api/v1/admin/platform/router.py:249`).
- Pest-prototype configuration error is raised after the reference vectors were removed
  (`tenant_service.py:302-322`) — a configuration error after a change.
- Account erasure keeps the personal tenant (rule `tenants.owner_user_key`, `rename_fields`,
  `erasure_engine.py`), so its domain data survives the account indefinitely.
- REQ-024 AK-16 / §API still say "Soft-Delete"; code and docs hard-delete.
- NFR-011 R-16 (harvest_batches, quality_assessments, yield_metrics, CanG 5 y), R-17
  (treatment_applications, PflSchG 3 y), R-18 (inspections, 3 y): retained, not deleted.

## Work packages

| id | package | specialist |
|----|---------|------------|
| WP1 | Declared tenant-erasure inventory (engine) + guard deriving tenant-bearing collections from the source | generalist (orchestrator), following #1776 precedent |
| WP2 | `ArangoTenantErasureExecutor`: one transaction, parent chains, generic edge sweep, retention rows pseudonymised, post-commit residue incl. undeclared collections | generalist |
| WP3 | `TenantErasureRecord` persisted proof, claim, backoff, beat retry; config errors refused before change; platform-tenant guard in the service | generalist |
| WP4 | Red-first unit tests via both routes; integration test against ArangoDB; reach probe (T2) | generalist + capability-reach-audit |
| WP5 | Docs DE/EN (tenant/admin/data-retention) | mkdocs-documentation |
| WP6 | Reviews | gdpr-data-protection-reviewer, code-security-reviewer, /code-review medium |

Order: WP1 → WP2 → WP3 → WP4 → WP5 → WP6.
