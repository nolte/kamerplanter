---
id: F-16
title: Sensor-Historie beim Import wiederherstellen
status: draft
roadmap_item: R-19
sprint: null
created: 2026-11-17
ended: null
verifies_sprint_value: null
consistency_check:
  performed_at: 2026-11-27
  agent_version: feature-consistency-reviewer@unknown
  findings:
    - kind: prior-art
      target: src/backend/app/domain/services/tenant_service.py:2592
      resolution: proceed
      evidence: "_rollback (tenant_export_service.py:1353-1354) ruft erase_abandoned_import → _run_tenant_erasure → _purge_tenant_readings: 'removed = self._observation_repo.delete_by_tenant(tenant_key)' (:2580-2593); Docstring :1331 'every row, edge, object and reading of the tenant'"
    - kind: drift
      target: src/backend/app/domain/engines/tenant_export_engine.py:1220
      resolution: revisit-after Kriterium ergänzt, dass die Prüfsumme des Messwert-Teils vor dem Schreiben geprüft wird
      evidence: "if is_ignored_part(name): '# Listed (above) but never decompressed' … continue (:1220-1224) — vor dem sha256-Vergleich :1226-1228"
    - kind: drift
      target: src/backend/app/domain/services/observation_service.py:64
      resolution: revisit-after Kriterium 1 regelt Messwerte, deren sensor_key nicht im Archiv steht
      evidence: "_require_owned_sensor (:64-74) vor jedem Schreiben (:95-106); Zuordnung deklariert in tenant_export_engine.py:481 '\"sensor_key\": _internal(\"sensors\")'; CSV-Leseregel :82-86 'a reader strips one leading \\''"
    - kind: drift
      target: spec/req/REQ-056_Mandanten-Lebenszyklus-Kontingente.md:683
      resolution: revisit-after Kriterium 6 nennt AK-47, §16.4 und das Runbook DE/EN
      evidence: "AK-47: 'ein Leser des Formats 1 importiert das Archiv, entpackt den Teil nicht und meldet not_imported:…'; Runbook :8 'der Import spielt sie aber noch nicht ein', :26, :146 '(die Messwerte nicht mitgezählt)'"
    - kind: prior-art
      target: src/backend/tests/integration/test_tenant_export_readings_timescale.py:151
      resolution: revisit-after Test-Hook 5 nennt dieses Modul statt test_tenant_export_roundtrip.py
      evidence: "test_the_archive_carries_the_tenants_readings_and_an_import_lists_but_skips_them; Roundtrip-Modul verdrahtet 'observation_repo=NullObservationRepository()' (test_tenant_export_roundtrip.py:358); Timescale-Service in .github/workflows/backend-guards.yml:417-454"
    - kind: drift
      target: project/features/tenant-readings-import.md:36
      resolution: revisit-after Beschreibung an die Entscheidung „eine Installation" angepasst und Abhängigkeit von F-15 eingetragen
      evidence: "'ein umgezogener oder wiederhergestellter Garten' gegen tenant-archive-size-limits.md:106 'Mandanten werden nicht zwischen Installationen verschoben'; References :105 ohne 'depends on F-15'"
---

## Description

Ein Mandanten-Archiv enthält die Sensor-Historie schon heute: Rohwerte der
letzten 90 Tage sowie Stunden- (2 Jahre) und Tageswerte (5 Jahre). Beim Import
wird sie aber übersprungen; ein umgezogener oder wiederhergestellter Garten
startet ohne Messverlauf.

Nach dieser Änderung stellt der Import die Sensor-Historie mit her. Die
Rohwerte werden den Sensoren des neuen Mandanten zugeordnet, die älteren
Stunden- und Tageswerte erscheinen in den Diagrammen wie vor dem Export. Auf
einer Installation ohne Zeitreihendatenbank gelingt der Import weiterhin und
meldet, dass die Messwerte übersprungen wurden. Schlägt ein Import fehl,
werden auch bereits geschriebene Messwerte zurückgerollt.

## Acceptance criteria

- [ ] **acceptance-1** Der Import stellt die Rohwerte ab dem frühesten Rohwert im Archiv wieder her, zugeordnet zu den Sensoren des neuen Mandanten.
- [ ] **acceptance-2** Stunden- und Tageswerte vor dem frühesten Rohwert erscheinen nach dem Import in den Diagrammen wie vor dem Export, auch nachdem die Aggregate für das Rohwert-Fenster neu berechnet wurden.
- [ ] **acceptance-3** Messwerte werden auch bei großen Archiven vollständig importiert (nur die Archivgrenze gilt), und ein fehlgeschlagener Import hinterlässt keine Messwerte.
- [ ] **acceptance-4** Ohne Zeitreihendatenbank gelingt der Import und meldet ausdrücklich, dass die Messwerte übersprungen wurden.
- [ ] **acceptance-5** Export → leere Datenbank → Import ergibt einen leeren Unterschied einschließlich der Messwerte; ein Test schlägt fehl, wenn sich das Tabellenlayout der Aggregate ändert.
- [ ] **acceptance-6** REQ-056 §8.3/§8.4 beschreibt den Messwert-Import.

## Test hooks

- **acceptance-1** — integration test (Timescale container): sensor key remapping of raw rows — pending
- **acceptance-2** — integration test: written hourly/daily buckets survive `refresh_continuous_aggregate` over the raw window — pending
- **acceptance-3** — integration test: readings beyond `MAX_ROWS`; induced failure → `delete_by_tenant` leaves zero rows — pending
- **acceptance-4** — unit test with `NullObservationRepository`: report says skipped — pending
- **acceptance-5** — extend `test_tenant_export_roundtrip.py` (AK-32) with readings + a layout pin on `resolve_aggregate_tables()` — pending
- **acceptance-6** — spec diff review — pending

## Consistency notes

**REQ-056 §8.3 (drift, proceed).** Established:
`REQ-056_Mandanten-Lebenszyklus-Kontingente.md:364` and the service docstring
(`tenant_export_service.py:49-53`) exclude importing readings from the current
version; this feature amends §8.3/§8.4 (criterion 6). No MUST is violated.

**Aggregate tables (prior-art, proceed).** Established:
`resolve_aggregate_tables()` (`observation_repository.py:117-144`) resolves the
continuous aggregates' materialisation tables and raises when one is missing;
the export side exists (`iter_tenant_readings` `:320-346`,
`ArchivedReading` `observation.py:35-58`). Reused for writing and for the
layout pin (criterion 5).

**Refresh boundary (decision).** Unestablished but derived from TimescaleDB
semantics: `sensor_daily` is computed from `sensor_hourly`
(`migrations/002_continuous_aggregates.sql:23-35`), and an explicit refresh
over a range without raw rows removes already materialised buckets there.
Operator decision 2026-11-17: raw rows from the earliest raw timestamp,
hourly/daily only before it, refresh only the raw window; criterion 2 proves
the older buckets survive.

**Missing TimescaleDB (prior-art, proceed).** Established: the import already
reports `not_imported:<part>` (`tenant_export_service.py:1240-1242`) and has
no readings repository without Timescale (`:272-273`); criterion 4 pins it.

**Bounds and rollback (prior-art, proceed).** Established: the format-1 reader
skips the readings part and is not bounded for it
(`tenant_export_engine.py:1011-1012,1311-1313`); the rollback
(`tenant_export_service.py:1245`) does not cover readings although
`delete_by_tenant` exists (`observation_repository.py:300-318`). Operator
decision 2026-11-17: stream readings from the stored archive, bounded only by
the archive limit, and include them in the rollback (criterion 3).

### Re-run 2026-11-27

Re-run by `feature-consistency-reviewer@unknown` against develop `cc8531492`; same run, triggers and caveats as recorded in `tenant-archive-size-limits.md` (no test run; resolutions are proposals; line references into this file are those of `cc8531492`). The frontmatter holds the six findings of this run; the four findings of 2026-11-17 (`feature-consistency-reviewer@1004fe514`) are listed with their fate.

**Findings of 2026-11-17 — fate.**

1. `spec/req/REQ-056_Mandanten-Lebenszyklus-Kontingente.md:364` (drift, proceed) — moved to `:365`. Service docstring `:49-53` still true.
2. `src/backend/app/data_access/timescale/observation_repository.py:117` (prior-art, proceed) — moved: `resolve_aggregate_tables` is at `:132-144` (`AGGREGATE_VIEWS` `:119`). `iter_tenant_readings` `:320-346` and `ArchivedReading` `observation.py:35-58` still true.
3. `src/backend/app/domain/services/tenant_export_service.py:1240` (prior-art, proceed) — still true (`:1240-1242`, `:272-273`).
4. `src/backend/app/domain/engines/tenant_export_engine.py:1011` (prior-art, proceed) — `:1011-1012` and `:1311-1313` still true, `delete_by_tenant` `:300-318` still true. **The statement "rollback does not cover readings" is obsolete** (first new finding). It holds only when tenant erasure is not configured; then the tenant stays `importing` and the request `cleanup_pending`. The note "Bounds and rollback" above is to be corrected when the feature is promoted.

The block of 2026-11-17 as it stood in the frontmatter until this re-run:

```yaml
consistency_check:
  performed_at: 2026-11-17
  agent_version: feature-consistency-reviewer@1004fe514
  findings:
    - kind: drift
      target: spec/req/REQ-056_Mandanten-Lebenszyklus-Kontingente.md:364
      resolution: proceed
      evidence: "§8.3 says importing readings is not part of this version; service docstring :49-53 says the same — REQ-056 amended with this feature."
    - kind: prior-art
      target: src/backend/app/data_access/timescale/observation_repository.py:117
      resolution: proceed
      evidence: "resolve_aggregate_tables() (:117-144) resolves the materialisation tables via timescaledb_information.continuous_aggregates and raises when one is missing; export side done (iter_tenant_readings :320-346, ArchivedReading observation.py:35-58)."
    - kind: prior-art
      target: src/backend/app/domain/services/tenant_export_service.py:1240
      resolution: proceed
      evidence: "Import already reports not_imported:<part> for timeseries parts; without Timescale self._readings is None (:272-273) — criterion 4 pins today's behaviour."
    - kind: prior-art
      target: src/backend/app/domain/engines/tenant_export_engine.py:1011
      resolution: proceed
      evidence: "The format-1 reader skips the readings part, unbounded by MAX_ROWS / 1 GiB (:1011-1012,1311-1313); rollback (service :1245) does not cover readings, delete_by_tenant exists (repo :300-318) — operator decision: stream readings and include them in the rollback."
```

**New findings.**

- **Rollback already covers readings (prior-art, proceed, `tenant_service.py:2592`).** `_rollback` (`tenant_export_service.py:1353-1354`) calls `erase_abandoned_import` → `_run_tenant_erasure` → `_purge_tenant_readings`, which runs `self._observation_repo.delete_by_tenant(tenant_key)` (`:2580-2593`); the docstring (`:1331`) says "every row, edge, object and reading of the tenant". Readings and aggregates are covered through the erasure inventory; criterion 3 needs a test for it, not a new path.
- **The checksum of the readings part is never compared (drift, `tenant_export_engine.py:1220`).** For an ignored part the reader continues (`:1220-1224`, "Listed (above) but never decompressed") before the sha256 comparison (`:1226-1228`). F-16 writes from that part straight into internal Timescale tables; a criterion should require the checksum of the readings part to be verified before writing.
- **Readings whose `sensor_key` is not in the archive (drift, `observation_service.py:64`).** The normal write path requires an own sensor (`_require_owned_sensor` `:64-74` before every write `:95-106`); the mapping is declared in `tenant_export_engine.py:481` (`"sensor_key": _internal("sensors")`), the CSV read rule at `:82-86`. The rule for rows that cannot be mapped (skip and count, or refuse) is missing in criterion 1.
- **AK-47 and the runbook are reversed without a documentation criterion (drift, `REQ-056:683`).** AK-47 says a format-1 reader imports the archive, does not unpack the part and reports `not_imported:…`; the runbook says the same at `:8`, `:26` and `:146`. Criterion 6 should name AK-47, §16.4 and the runbook DE/EN.
- **The Timescale test module exists (prior-art, `test_tenant_export_readings_timescale.py:151`).** `test_the_archive_carries_the_tenants_readings_and_an_import_lists_but_skips_them` already runs export → import into a second database in CI (Timescale service in `.github/workflows/backend-guards.yml:417-454`); the roundtrip module wires `observation_repo=NullObservationRepository()` (`test_tenant_export_roundtrip.py:358`) and has no time-series database. Test hook 5 should name the Timescale module.
- **Description against "one installation", missing dependency (drift, this file `:36`).** "ein umgezogener oder wiederhergestellter Garten" contradicts the decision that tenants are not moved between installations (`tenant-archive-size-limits.md:106`). Criterion 3 ("only the archive limit applies") presupposes the tmp and size values of F-15; the dependency is now recorded under References.

**Criterion by criterion.**

- **Criterion 2** is observable through `GET …/sensors/{key}/readings` with `resolution=hourly|daily`. Missing as a test case: the edge bucket, i.e. the hour and the day that contain the earliest raw value.
- **Criterion 4** is today's behaviour. After F-16 the report must tell "skipped, no time-series database" from "imported". Without Timescale the service gets `readings=None` (`dependencies.py:1787`), not a null repository; the hook should reflect that.
- **Criterion 5** bundles two checks (roundtrip and layout pin) and should be split. "Empty difference" needs a tolerance for recomputed floating-point aggregates and the exception `sensor_key`.
- No new route, so no entry in the route counter or the isolation matrix.
- Notification rows (#3143) are excluded from the export (`tenant_export_engine.py:210,260-262`) and irrelevant for R-19.

**Already implemented:** the export side, the `not_imported` message, the rollback of readings.

**Cross-feature.** F-16 depends on F-15 (sizes); F-17 criterion 5 (phase "Messwerte") depends on F-16. F-16 criterion 5 is the automated criterion closest to the roadmap promise "complete". The remaining cross-feature points and the comparison with issue #3140 are in `tenant-archive-size-limits.md`.

**Edits required before `ready`** (the report's verdict for F-16: ready after edits; translated):

1. Add the checksum of the readings part as a criterion.
2. Fix the rule for `sensor_key` values that cannot be mapped.
3. Extend criterion 6 by AK-47 and the runbook DE/EN.
4. Switch hook 5 to `test_tenant_export_readings_timescale.py` and split criterion 5.
5. Record the dependency on F-15 (done under References in this change).
6. Correct the rollback note.
7. Add the section "Betreiberentscheidungen 2026-11-27" (done in this change).

## Risks

- Writing into continuous-aggregate materialisation tables relies on TimescaleDB internals; an upgrade can break it — the layout pin (criterion 5) turns that into a red test instead of silent data loss.
- Large readings imports lengthen the import job; progress is shown by F-17.

## References

- Issue #2138 (MT-042), roadmap item R-19
- `project/requirements/tenant-export-import-remainder.md` (R3, R4, R9, R13, R14)
- Depends on F-15 (archive size and `/tmp` values; criterion 3) — recorded by the consistency re-run 2026-11-27

## Betreiberentscheidungen 2026-11-27

- Es gibt nur **eine** Installation; Mandanten werden nicht zwischen Installationen verschoben. Die Datenschutz-Befunde zum Archiv laufen in einer eigenen Lane.
- Der Test mit einem Archiv von etwa 500 MiB läuft **nur manuell** (`workflow_dispatch`).
- Ein Speicherlimit des Workers von rund 2 GiB ist akzeptabel.

## Offene Betreiberentscheidungen (Re-run 2026-11-27)

Der Bericht nennt für F-16 keine blockierende Betreiberentscheidung. Eine Regel ist beim Hochstufen festzulegen:

- **Messwerte, deren `sensor_key` nicht im Archiv steht.** Heute verlangt der normale Schreibpfad einen eigenen Sensor (`observation_service.py:64-74`, `:95-106`); der Import schreibt Messwerte noch gar nicht.
  - **Überspringen und zählen:** Der Import läuft durch; der Bericht nennt die Zahl der ausgelassenen Zeilen.
  - **Ablehnen:** Ein Archiv mit einer unzuordenbaren Zeile scheitert ganz und wird zurückgerollt.
