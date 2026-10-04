# Unreleased

Changes not yet published in a release.

## Added

### Backend

- **REQ-001** Master data management: Botanical families, species, cultivars, lifecycles (ArangoDB); field `propagation_methods` (13 propagation method values, multi-select) added to the species profile — all 143 crop species seed records populated
- **REQ-002** Site management: Sites, locations (recursive hierarchy), slots, location types
- **REQ-003** Phase control: Phase state machine (germination → harvest), GDD/VPD/photoperiod calculation
- **REQ-004** Fertilization logic: Fertilizers, nutrient plans, dosages, mixing safety, flushing, runoff, EC budget, water source/CalMag correction
- **REQ-006** Task planning: Workflow templates, tasks, queue, dependencies, HST validator
- **REQ-007** Harvest management: Harvest indicators, observations, batches, quality assessment, pre-harvest interval gate
- **REQ-010** IPM system: Pests, diseases, treatments, inspections, resistance manager
- **REQ-011** External master data enrichment: GBIF + Perenual adapters, enrichment engine, Celery tasks
- **REQ-012** Master data import: CSV upload, validation, preview, confirmation
- **REQ-013** Planting runs: PlantingRun, batch operations, state machine
- **REQ-014** Tank management: Tanks, tank states, fills, maintenance, sensors
- **REQ-015** Calendar view: iCal feeds, aggregation, token-based access
- **REQ-019** Substrate management: Extended substrate types, lifecycle manager, reuse
- **REQ-020** Onboarding wizard: 5-step assistant, 9 starter kits, experience levels
- **REQ-022** Care reminders: 9 care profiles, FAMILY_CARE_MAP, adaptive intervals, Celery task
- **REQ-023** Authentication: Local accounts (bcrypt), JWT (authlib), refresh token rotation
- **REQ-024** Multi-tenancy: Tenant isolation, memberships, invitations, RBAC
- **REQ-028** Companion planting: Graph-based compatibility
- **REQ-031** AI assistant: RAG-based knowledge base, LLM adapters (Anthropic/Ollama/OpenAI-compatible), hybrid search

### Frontend

- All REQ-001 through REQ-024 frontend pages implemented
- **REQ-020** Onboarding wizard (5-step MUI Stepper)
- **REQ-021** UI experience levels: Field configuration, navigation tiering, ExperienceLevelSwitcher
- **REQ-022** Care dashboard with urgency grouping
- Light/dark theme with localStorage persistence
- i18n German/English (react-i18next)

### Infrastructure

- MkDocs documentation infrastructure with Material Theme and DE/EN i18n (NFR-005)
- ADR-001 through ADR-006: Architecture decisions documented
- Skaffold-based development workflow with Kubernetes/Helm
- pgvector + embedding service for RAG pipeline
- Knowledge container for YAML-based knowledge base
- GitHub Actions CI/CD (Docker lint/build, Skaffold verify)

## Changed

### Frontend

- Admin: After deleting an organization the interface reports "Deletion accepted" instead of "Organization deleted" — the deletion runs in the background (issue #1792)
- Plant instances are displayed everywhere with a speaking name (e.g. `BASIL-001 (Basil – Genovese)`) instead of only the technical instance ID; the instance ID is preserved as secondary information
- Tasks: the forms in the **Edit** and **Complete** tabs now render validation errors as helper text directly on the affected field instead of a short-lived native browser bubble (`noValidate`)
- Account: the email verification page now offers a **Log in** button in the error case as well (invalid or expired link) — previously that page was a dead end

### Backend

- **Security:** Every change of a tenant membership (add, change of role or scopes, removal, leaving, accepting an invitation, creating a tenant) now writes a row to the persistent security audit `security_audit_log` (issue #2111, MT-014, NFR-011 R-38, migration `v0082`): who, whose membership, which tenant, old and new role or scopes, request id and time — account and tenant keys only, no free text. Kept 730 days (daily task `security_audit.purge_expired`); an account erasure turns both account keys into tombstone hashes. Platform admins read the rows through `GET /api/v1/admin/platform/security-audit`. The service call `change_member_scopes` takes the acting account (`actor_user_key`) for it.
- **Security (API):** `POST /api/v1/admin/platform/tenants/{key}/members` and `POST /api/v1/admin/platform/users/{key}/memberships` now require the administrator's own step-up (issue #2106, MT-008, REQ-024 AK-59): the body carries `current_password` (or `step_up_token` / `step_up_code` for the act `admin_membership_add`, bound to `<tenant_key>|<user_key>`); without it `401`, from an API key `403`, after failed attempts `429`. A platform admin cannot add themselves to the `platform` tenant (`422`), and the `lead` role in the `platform` tenant is handed out only by someone who holds it. Before, the admin session alone added any account — the `platform` tenant with `lead` included — without a trace. The two admin pages (tenant, user) ask for the step-up when adding.
- **Security:** The e-mail notification channel now mails only addresses whose owner proved them (`email_confirmed_at`, issue #1948, REQ-023 v1.38, REQ-030 v1.7). An account registered with `REQUIRE_EMAIL_VERIFICATION=false` receives no notification mail until it follows a verification link — not even after the setting is switched to `true`; `POST /auth/resend-verification` issues the link to such accounts too. Existing verified accounts keep their mail (migration v0080 stamps them; the dry run counts them). At startup `email_channel_without_verification` warns when a sender is configured and verification is off.
- **BREAKING (API):** The platform-admin account deletion is asynchronous (issue #1949, REQ-024 §1a.2, REQ-025 AK-IE-01). `DELETE /api/v1/admin/platform/users/{key}` now answers `202 Accepted` with a body `{erasure_key, status, requested_at, message}` (formerly `204` without a body). The request checks the step-up, records the erasure request, deactivates the account, revokes its sessions and tells the other members of its personal gardens right away (still no grace period); a Celery task (`retention.run_account_erasure`) then runs the erasure — the personal tenants in bounded batches with a heartbeat, then the account's own plan. The `500 ERASURE_INCOMPLETE` and `502` answers of this endpoint are gone — a failed or incomplete run is the request status `partially_completed` (retried by the daily run), readable at the new `GET /api/v1/admin/platform/erasures/{erasure_key}`. Still decided synchronously: `401`/`403`/`404`/`422`/`429` (step-up, permission), `409` (a run holds the request) and `503` (the deployment cannot erase; nothing changed). Callers that waited for a finished erasure must poll the status. Deletions started by the old synchronous route before the deploy finish as before; the daily run resumes one that was cut off
- **Security (API):** `PATCH /api/v1/admin/platform/users/{key}` now requires the administrator's own step-up whenever it **changes** `email_verified` or `is_active` — lowering them, too (issue #1992; formerly only raising them). Previously one `PATCH email_verified=false`, also through an API key, made an established local account the next run's candidate of the unverified-account clean-up, which erased it with neither a step-up nor a notice to the other members of its personal garden. A lowered `email_verified` is now recorded (`email_verified_lowered_at`) and such an account is never removed by the clean-up; the clean-up also tells the other members of a personal garden before erasing it. Accounts an administrator demoted before this release carry no marker; the clean-up also spares every account that ever signed in (`last_login_at`), which covers them unless they never signed in
- **BREAKING (API):** Tenant deletion is asynchronous (issue #1792, REQ-024 AK-53). `DELETE /api/v1/tenants/{slug}` and `DELETE /api/v1/admin/platform/tenants/{key}` now answer `202 Accepted` with a body `{tenant_key, status, requested_at, message}` (formerly `200` with `{"message": "Tenant deleted"}` or `204` without a body). The request checks the permission and the step-up, creates the deletion record and freezes the tenant (memberships deactivated); a Celery task (`app.tasks.tenant_tasks.run_tenant_erasure`) then deletes in batches of 1000 records, each in its own ArangoDB transaction, and reports a heartbeat on the record between batches. The `500 TENANT_ERASURE_INCOMPLETE` and `502` error responses of the delete endpoints are gone — failures of the run are recorded on the record and retried by the daily run; from the third unsuccessful attempt on, the log event `tenant_erasure.escalated` appears. Callers that waited for a completed deletion must treat the tenant as frozen. Deletions already running at deploy time are taken over by the daily run after six hours without a heartbeat
- Plant-instance and planting-run plant responses now embed `species` and `cultivar` summaries (denormalization), so the frontend can build readable names without extra requests
- Harvest: `batch_id` is nullable in API responses (`string | null`) instead of an empty string; the uniqueness index on `harvest_batches.batch_id` is `unique + sparse`. Existing data is migrated by `v0030`
- Tenancy: the plant id (`instance_id`) and the lot label (`batch_id`) are unique per tenant, the slot id (`slot_id`) per location — no longer across all tenants (issue #2065, migration `v0079`). Until now onboarding skipped every plant of the second tenant to pick the same species (`onb-<species>-<n>` was taken), and an identifier another tenant used was refused with `409` — the refusal revealed that another tenant holds it. Within a tenant or location a duplicate identifier is still a `409`
- Tenancy: a planting run no longer follows an entry's stored species into another tenant's private species (issue #1963, migration `v0081`). Rows written before the #1871 fixes can still name such a species after migration `v0067` removed its edge; starting such a run now answers `404` for the species (edit the entry to a species you can read), its phase timeline and irrigation demand skip it. Migration `v0081` also clears `equipment.location_key` and the foreign keys of `watering_logs.slot_keys` that name another tenant's location or slot; it only counts location assignments and run entries (their field is required), so check the counts before the deploy
- Tenancy: a plant that a legacy planting run created with another tenant's private species no longer shows that species' name. The plant lists, the plant detail, the diary overview, print labels and checklists, the overwintering labels, the photo assessment, the diagnosis context, the watering suggestion and the MCP plant detail now resolve the stored species under your tenant: a species you cannot read is shown as unknown, never as the foreign name (issue #2082). Readers that still resolve it unscoped are listed in the guard `test_stored_species_key_readers_are_decided`.
- Tenancy: the care dashboard, the winter-reminder gating and the care-profile presets of a plant that a legacy planting run created with another tenant's private species no longer use that species: the dashboard shows no species name for it (it used to show the foreign one), and the foreign species' frost sensitivity, family and watering guide no longer drive its reminders or presets (issue #2082).
- Plant-protection reference data: the pests, diseases and treatments of `plant_info.yaml` and `adventskalender.yaml`, with their treatment links, are now seeded — the loaders read keys the files do not use (*Bemisia tabaci*, *Septoria apiicola* and Ferramol, among others, were missing). A row the model refuses is skipped and logged (`ipm_seed_row_invalid`) instead of inventing data; currently "Alcohol Spray" (chemical without a waiting period)
- **Operations (rollback):** No image rollback below the first migration of a retired index (issue #2064). An older backend image re-creates, at startup, the unique indexes a migration dropped, and the migration never runs again — measured on ArangoDB 3.12.8. Floors: `v0030` (dense index on `harvest_batches.batch_id`, shipped since v0.0.24), `v0041` (global index on `species.scientific_name_normalized`, since v0.2.1), `v0062` (unique index on `attachments.storage_key`), `v0064` (`auth_providers` without the configuration), `v0069` (`fertilizers` across tenants), `v0075` (`tanks.name`), `v0076` (`activities.name`), `v0077` (`workflow_templates.name`), `v0079` (`plant_instances.instance_id`, `harvest_batches.batch_id`, `slots.slot_id`) — the last seven are in no release yet, so no rollback below the next release. Every start of a new image drops such a re-created index again (log event `retired_index_reappeared`); if its replacement is missing it stays, `retired_index_refused_without_replacement` is logged at `error` level and `/api/v1/health/ready` reports `retired_indexes_refused` above 0 (the status stays `ready`). The unique index on `attachments.storage_key` is not dropped again. An old pod that starts *after* the new ones re-creates the index until the next new pod starts. Where two tenants already share a name, the old image does not start at all (`ERR 1210 unique constraint violated`)
- Care reminders: completing a due watering task creates the follow-up task immediately — previously it only appeared with the nightly planning run
- Care reminders: a confirmation now only closes care tasks that are due today or earlier; a follow-up task already scheduled is left in place

## In Development

- REQ-025 (Privacy/GDPR): GDPR Art. 15–21 data subject rights — specified, not implemented
- REQ-027 (Light mode): Anonymous access for local instances — specified, not implemented
- OAuth/OIDC: Full implementation (engine currently stubbed)
- TimescaleDB integration: Repository and migrations in place, feature-flag controlled
