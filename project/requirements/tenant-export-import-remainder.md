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

- **R18** — The import SHALL validate every document of an archive against its domain model in the background check (worker) before a tenant is founded; an archive with a document outside the model (for example an enum value out of range) SHALL be refused with the affected documents named, and nothing SHALL be written. The pre-check SHALL show the result (REQ-056 §12.4).
  - _dimension_: `functional`, `constraints` · _status_: `confirmed` · _source_: operator decision 2026-11-27 (own small feature in R-19, F-32)

### Revisit 2026-11-27 (operator decisions, recorded 2026-11-28)

- **R12** is made precise (option B): synchronous stay role, size, step-up, "plan exists" and e-mail → account; everything else runs asynchronously in the worker; the refusal details are stored on the import record. The backend's `/tmp` moves to disk instead of growing in memory.
- **R15** is limited (D2): the step-up confirmation of the pre-check is valid for one hour for the subsequent import and bound to the same admin; after that, or for another admin, a new step-up is required.
- **R16** is limited (D1): archive errors appear as a failed pre-check in the import list; "audit-only" applies only to refusals before the upload is stored (role, size, step-up). The phase "writing readings" is delivered with the readings import (F-16), not with the list (F-17).
- **R18** is new (see above). Sprint 5 contains only R-19; implementation order F-15 → F-32 → F-17 → F-16.
- The bounded context's "restored or moved" is narrowed by the decision that there is only one installation: tenants are restored, not moved between installations.

### Revisit 2026-11-28 (operator decisions)

- **R13** is replaced: the import writes every archived `hourly` and `daily` bucket directly and recomputes nothing. A refresh runs over a time range, not per tenant; for an archive reaching back beyond the 90 days of raw retention it would rebuild, and so delete, other tenants' buckets. R3's "refresh the continuous aggregates for that window" falls with it.
- **R14** is made precise: readings (raw, hourly, daily) of a sensor the archive does not hold are skipped and counted in the report.
- **R1** is made precise: the worker's `/tmp` moves to disk like the backend's.
- **R9** is made precise: the manual run with a ~500 MiB archive is mandatory for closing sprint 5; its test hook may only end `passing`.
- **R10** is extended: the export also refuses what the import's read limits would refuse (rows, document bytes, unpacked size, entries, JSON values, compression ratio), not only the byte limit.

### Revisit 2026-11-28, third round (operator decisions and a measurement)

- **Split:** R5, R7 and R15 are carried by F-17 (pre-check and start), R6, R8 and R16 by F-33 (import list and expiry), R3 and R14 by F-16 (raw readings), R4 and R13 by F-34 (hourly and daily values); R9's roundtrip is F-34's value-verifying criterion.
- **R15** is made precise (decision B): whoever starts the import acts (audit actor, fallback owner), the uploader stays on the record; every admin sees the member names only after a fresh confirmation of their own (at most one hour) for this archive, through a route that only confirms.
- **R16** is made precise (decision C): refusals before the upload is stored (role, size, confirmation) are written to the audit by F-15; a 413 from proxy or middleware and an unauthenticated request know no account and are not audited.
- **R3/R14** are limited (measurement against TimescaleDB 2.32.1-pg16, 2026-11-28): raw readings older than the target installation's raw retention are not imported but counted and named in the report. Writing raw rows marks their time range; the next refresh over it rebuilds the buckets of all tenants from raw rows and deletes those that have none left.
- **R18** is extended: fields of `tenant.json` that are missing or of the wrong type refuse the archive instead of being replaced by a default.
- **R10** is made precise: the export refuses whatever the import's archive reader and object check would refuse, including a `manifest.json` above 1 MiB.

### Revisit 2026-11-28, fourth round (operator decisions D and E, further measurements)

- **R13** is replaced again (decision D): the import writes the archived hourly and daily values directly and then has exactly the imported periods recomputed, first `sensor_hourly` over the imported raw period, then `sensor_daily` over the imported hourly period. Measured against TimescaleDB 2.32.1-pg16: a directly inserted hourly row marks its day for the daily values of all tenants; a bounded refresh over a range in which every tenant still has its source rows leaves the others unchanged.
- **R3/R4/R14** are layered by the target installation's retentions: raw readings older than the raw retention (90 days), hourly values older than the hourly retention (2 years) and daily values older than the daily retention (5 years) are not imported but counted; each cut lies on a day boundary inside the retention.
- **R9** is made precise (decision E): the sprint value and the roundtrip speak of the sensor history "within the retention periods".
- New: a restore into an installation whose aggregates were never fully refreshed keeps the imported values (F-34); the policies' behaviour there is not measured.

## Surviving assumptions / open risks

- **Revisit 2026-11-17:** the consistency check showed that the e-mail member mapping (`member_mapping {email, role, admin_scopes}`, `tenant_export_service.py:954-982`) and the 413 response already exist — R7 reduces to pre-filling the rows from the preflight; the import history retention is NFR-011 R-40 (30 days, `REQUEST_RETENTION`).

- **Timescale internals:** writing into continuous-aggregate materialisation tables relies on undocumented internals; a TimescaleDB upgrade can break it. Mitigated by tests; the erasure path carries the same dependency.
- **Resource cost:** ~500 MiB archives raise the permanent memory/tmpfs footprint of backend and worker pods. `assumed` acceptable for the self-hosted single-household model.
- **E-mail lookup:** the lookup reveals whether an e-mail has an account on the instance; it is platform-admin-only, so no enumeration risk for regular users. `assumed`.
