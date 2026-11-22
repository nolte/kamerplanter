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

## Risks

- Writing into continuous-aggregate materialisation tables relies on TimescaleDB internals; an upgrade can break it — the layout pin (criterion 5) turns that into a red test instead of silent data loss.
- Large readings imports lengthen the import job; progress is shown by F-17.

## References

- Issue #2138 (MT-042), roadmap item R-19
- `project/requirements/tenant-export-import-remainder.md` (R3, R4, R9, R13, R14)
