# Requirements — Tenant export/import remainder (#2138)

<!--
Produced via the `requirements-elicit` skill, following
spec/project/requirements-elicitation/.
Interview conducted 2026-11-17 with the operator (German); artifact in English.
`c_d` is an uncertainty proxy (self-consistency-derived), not a calibrated
probability. A requirement is `confirmed` only after an explicit teach-back.
-->

## Bounded context

- **What:** close the remaining gaps of the delivered tenant export/import (#2267, #2288, #2290, #2295, #2300) so a tenant can be restored or moved **completely and at realistic size**: (a) import the Timescale readings, (b) lift the size limits, (d) preflight with member mapping by e-mail and an import history.
- **For whom:** platform admins (import) and tenant leads with `management` (export), as today.
- **Out of scope:** (c) old builds reading new archives (only the reverse direction matters); changing archive format 1; shared → dedicated migration; e-mail addresses inside the archive (REQ-056 E-09 stays).
- _source_: Q1 "passt".

## Understanding KPI

- Thresholds: `τ_low = 0.4`, `τ_high = 0.8`, self-consistency `k = 2`, question budget = `8` (6 used)
- `U_gate = min_d c_d` over required dimensions = **0.8**
- Termination: `saturation` (final teach-back Q6 confirmed)

### Gap matrix

| Dimension | Applicable | `c_d` | Uncertainty source | Evidence event |
|---|---|---|---|---|
| `functional` | yes | 0.85 | specification (resolved) | Q3 "B", Q4, Q5 "B", Q6 teach-back |
| `non_functional` | yes | 0.85 | specification (resolved) | Q2 "B passt" (~500 MiB) |
| `constraints` | yes | 0.85 | specification | E-09 / SEC-003 measured and kept (Q5) |
| `domain_objects` | yes | 0.8 | interpretation | `ArchivedReading` series raw/hourly/daily, `TenantArchiveMember` (no e-mail) |
| `actors` | yes | 0.9 | specification | Q1 |
| `acceptance_criteria` | yes | 0.8 | specification | roundtrip incl. readings, runbook (Q6) |
| `edge_cases` | yes | 0.8 | specification | 413 above limit, unmatched e-mail, unmapped members, 24 h preflight expiry (Q6) |
| `scope_boundaries` | yes | 0.9 | specification (resolved) | Q1, Q5 |

Self-consistency (k=2) diverged on the target size (config-only vs. presigned/chunked upload → Q2), on the readings depth (raw only vs. full history → Q3) and on the e-mail source (archive vs. admin input → Q5).

## Requirements

- **R1** — Export and import SHALL handle archives up to about 500 MiB; spool budget, worker `/tmp`/tmpfs, memory limit and the import body ceiling SHALL be raised together via Helm values and configuration.
  - _dimension_: `non_functional` · _status_: `confirmed` · _source_: Q2 "B passt !"
- **R2** — WHEN an uploaded archive exceeds the limit, the API SHALL answer 413 with a message naming the limit; WHEN an export would exceed it, the export job SHALL end with a clear error instead of `internal_error`.
  - _dimension_: `edge_cases` · _status_: `confirmed` · _source_: Q2 recommendation, Q6
- **R3** — WHEN an archive contains `timeseries/readings.csv` and TimescaleDB is available, the import SHALL restore the raw readings (90 days) with sensor keys remapped to the new keys and refresh the continuous aggregates for that window.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Q3 "B", Q6
- **R4** — The import SHALL write the archived `hourly` and `daily` buckets older than the raw window directly into the materialisation tables of the continuous aggregates (as the erasure path already addresses them, `observation_repository.py:117-142`), guarded by tests against Timescale upgrades.
  - _dimension_: `functional`, `constraints` · _status_: `confirmed` · _source_: Q3 "B"
- **R5** — WHEN an archive is uploaded for import, the system SHALL verify signature and format and return the manifest and the member list (display name/pseudonym, archived role and scopes); the subsequent import SHALL reuse the uploaded content without a second upload.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Q4 "ja", Q6
- **R6** — A preflighted archive that is not imported SHALL be deleted after 24 hours.
  - _dimension_: `edge_cases` · _status_: `confirmed` · _source_: Q4, Q6
- **R7** — For each archive member the admin SHALL enter the e-mail of the target account; the backend SHALL resolve it to the account and report an unmatched e-mail on that row. The archived role is preselected but SHALL only become a grant after the admin confirms it (SEC-003). Unmapped members SHALL be shown as "will be pseudonymised" before the import.
  - _dimension_: `functional`, `constraints` · _status_: `confirmed` · _source_: Q4 "ja mach es über die email", Q5 "B"
- **R8** — The admin import page SHALL list previous imports (date, source, target tenant, admin, status, error text) and show the progress of a running import; entries SHALL be purged per NFR-011.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Q4, Q6
- **R9** — The roundtrip test SHALL include readings (export → empty DB → import → empty diff), and the runbook SHALL describe size limits and the resources to raise.
  - _dimension_: `acceptance_criteria` · _status_: `confirmed` · _source_: issue AC, Q6

- **R10** — The export SHALL stop at min(effective storage quota + 10 %, import limit) so every exported archive is importable; REQ-056 §8.3 SHALL be amended.
  - _dimension_: `constraints` · _status_: `confirmed` · _source_: revisit 2026-11-17 decision 1 "pass übernehme das!"
- **R11** — `TenantExportFailureReason` SHALL gain `too_large`, used for the pre-check and for a `/tmp` overflow during assembly.
  - _dimension_: `edge_cases` · _status_: `confirmed` · _source_: revisit decision 2
- **R12** — The backend SHALL only stream an uploaded archive to storage; verification and parsing SHALL run only in the worker (memory limit ~2 GiB), so the backend memory limit does not grow.
  - _dimension_: `non_functional` · _status_: `confirmed` · _source_: revisit decision 3
- **R13** — Raw readings SHALL be imported from the earliest raw timestamp in the archive; `hourly`/`daily` buckets SHALL be written only for times before it; only the raw window SHALL be refreshed, and a test SHALL prove the directly written older buckets survive the refresh.
  - _dimension_: `functional`, `edge_cases` · _status_: `confirmed` · _source_: revisit decision 4
- **R14** — Readings SHALL be streamed from the stored archive, bounded only by the archive limit (not `MAX_ROWS` / 1 GiB), and included in the import rollback.
  - _dimension_: `non_functional`, `edge_cases` · _status_: `confirmed` · _source_: revisit decision 5
- **R15** — The `tenant_import` step-up SHALL be required at preflight, bound to the archive's SHA-256, and reused by the import of the same archive; nothing is parsed before it (invariant `tenant_export_service.py:750-771`).
  - _dimension_: `constraints` · _status_: `confirmed` · _source_: revisit decision 6
- **R16** — Refused uploads SHALL stay audit-only and not appear in the import list; the list's source column SHALL show name and slug from the archive's `tenant.json` (stored at import); progress SHALL be shown in coarse phases (verifying, writing documents, writing readings, done).
  - _dimension_: `functional` · _status_: `confirmed` · _source_: revisit decisions 7+8
- **R17** — REQ-056 (§8.2, §8.3, §13.5, §14) and the stale NFR-011 R-40 status SHALL be updated in the implementing features.
  - _dimension_: `acceptance_criteria` · _status_: `confirmed` · _source_: revisit, operator approval of all eight recommendations

## Surviving assumptions / open risks

- **Revisit 2026-11-17:** the consistency check showed that the e-mail member mapping (`member_mapping {email, role, admin_scopes}`, `tenant_export_service.py:954-982`) and the 413 response already exist — R7 reduces to pre-filling the rows from the preflight; the import history retention is NFR-011 R-40 (30 days, `REQUEST_RETENTION`).

- **Timescale internals:** writing into continuous-aggregate materialisation tables relies on undocumented internals; a TimescaleDB upgrade can break it. Mitigated by tests; the erasure path carries the same dependency.
- **Resource cost:** ~500 MiB archives raise the permanent memory/tmpfs footprint of backend and worker pods. `assumed` acceptable for the self-hosted single-household model.
- **E-mail lookup:** the lookup reveals whether an e-mail has an account on the instance; it is platform-admin-only, so no enumeration risk for regular users. `assumed`.
