---
id: F-16
title: Rohwerte der Sensor-Historie beim Import wiederherstellen
status: ready
roadmap_item: R-19
sprint: 5
created: 2026-11-17
ended: null
verifies_sprint_value: null
consistency_check:
  performed_at: 2026-11-28
  agent_version: feature-consistency-reviewer@unknown
  findings:
    - kind: drift
      target: src/backend/app/data_access/timescale/observation_repository.py:245
      resolution: proceed
      evidence: "'Buckets older than the raw retention (90 days) cannot be recomputed at all … a wider refresh would wipe other tenants' history' (:245-251); Rohwerte 90 Tage (migrations/003_retention_policies.sql:3). Ein Neuberechnen über das Rohwert-Fenster des Archivs träfe andere Mandanten. Betreiberentscheidung 2026-11-28: alle archivierten Buckets direkt schreiben, nichts neu berechnen (damaliger Stand; seit der Entscheidung D vom selben Tag lässt der Import gezielt neu berechnen: acceptance-4 hier, F-34 acceptance-1 und -3)."
    - kind: drift
      target: src/backend/app/data_access/timescale/migrations/002_continuous_aggregates.sql:16
      resolution: proceed
      evidence: "Policies: sensor_hourly start_offset 3 hours / end_offset 1 hour / stündlich (:16-19), sensor_daily 3 days / 1 day / täglich (:37-40). Was ein Policy-Lauf mit einem direkt geschriebenen Bucket in seinem Fenster tut, war aus dem Repository nur teilweise belegt; durch die Messungen der Hauptsitzung vom 2026-11-28 geklärt (Consistency notes). Offen bleibt nur das Policy-Verhalten auf einer frischen Installation (F-34 acceptance-4)."
    - kind: prior-art
      target: src/backend/tests/integration/test_tenant_export_readings_timescale.py:49
      resolution: proceed
      evidence: "Die Fixture schreibt Messwerte unter SHARED_SENSOR ohne Sensor-Dokument (:49, :68-85); unter 'auslassen und zählen' würde jede Zeile übersprungen. Die Hooks zu acceptance-1 und -4 hier und die Hooks von F-34 verlangen eigene Sensoren im Seed."
    - kind: drift
      target: project/features/tenant-readings-import.md
      resolution: proceed
      evidence: "Offen war, ob eine falsche Prüfsumme des Messwert-Teils in der Vorprüfung (F-17) oder erst nach dem Start scheitert. Festgelegt: in der Hintergrundprüfung (heute acceptance-3); das Tabellenlayout prüft der Lauf (heute F-34 acceptance-5)."
    - kind: prior-art
      target: docs/de/deployment/tenant-export-import.md:136
      resolution: proceed
      evidence: "Ein Import neben dem Original scheitert an eigenen Arten (:136-137); der Wertnachweis braucht zwei ArangoDB-Datenbanken und Fotos ohne EXIF in der Quelle (_with_stored_bodies, tenant_export_service.py:1286-1312). Heute im Hook zu F-34 acceptance-6 benannt."
    - kind: overlap
      target: F-17
      resolution: proceed
      evidence: "Stand des ersten Agentenlaufs: acceptance-9 ergänzt die Phasenanzeige aus F-17 acceptance-8; acceptance-7 nutzt den Weg über die Vorprüfung; acceptance-2 scheitert als fehlgeschlagene Vorprüfung in der Liste aus F-17. Seit der Teilung: Phase und Liste liegen in F-33, der Rundlauf in F-34."
    - kind: overlap
      target: F-15
      resolution: proceed
      evidence: "Aus dem ersten Agentenlauf nachgetragen: 'nur die Archivgrenze gilt' setzt Größen und /tmp aus F-15 voraus, Fehler laufen über das Detailfeld aus F-15 acceptance-6. Begründung in den Consistency notes (manueller Durchgang, 'Überschneidung mit F-15')."
    - kind: drift
      target: src/backend/app/data_access/timescale/migrations/003_retention_policies.sql:3
      resolution: proceed
      evidence: "Zweiter Lauf und Messung der Hauptsitzung (TimescaleDB 2.32.1-pg16, 2026-11-28): Ein Rohwert-Insert merkt seinen Zeitbereich vor; das nächste Neuberechnen darüber bildet die Buckets aller Mandanten aus Rohwerten neu und löscht die, für die keine mehr da sind. Vorgabe der Hauptsitzung: Rohwerte älter als die Rohwert-Aufbewahrung der Zielinstallation (heute 90 Tage) werden nicht eingespielt, sondern gezählt (acceptance-2)."
    - kind: overlap
      target: F-34
      resolution: split-out F-34
      evidence: "Betreiberentscheidung A (2026-11-28): Stunden- und Tageswerte, Mandantentrennung nach dem Neuberechnen, Tabellenlayout und der Rundlauf als Wertnachweis gehen in das neue Feature F-34 (tenant-readings-aggregates-import.md); verifies_sprint_value wandert dorthin."
    - kind: drift
      target: src/backend/app/data_access/timescale/migrations/003_retention_policies.sql:6
      resolution: proceed
      evidence: "Dritter Lauf, Messungen und Betreiberentscheidung D (2026-11-28): Der Import lässt am Ende gezielt neu berechnen. Für die Rohwerte heißt das: Stichtag auf einer Tagesgrenze (acceptance-2), danach sensor_hourly und sensor_daily über den eingespielten Rohwert-Zeitraum (acceptance-4), auch am Ende eines Rollbacks (acceptance-5). Der Bericht nennt bis F-34 die nicht eingespielten Stunden- und Tageswerte (acceptance-6)."
    - kind: drift
      target: src/backend/app/data_access/timescale/observation_repository.py:278
      resolution: proceed
      evidence: "Vierter Lauf und Betreiberentscheidung F (2026-11-28): Jedes Löschen von Rohwerten merkt seinen Zeitraum vor und lässt ihn liegen: delete_by_sensor (:278), delete_by_tenant (:300), der Rollback eines Imports (tenant_export_service.py:1354) und der Sweep abgebrochener Importe (_sweep_abandoned_import :1429-1460 → erase_abandoned_import, tenant_service.py:487). Neues Kriterium acceptance-9: Das Löschen berechnet seinen Zeitraum an einer Stelle im Datenzugriff gezielt neu; acceptance-5 nennt den Sweep-Pfad."
    - kind: drift
      target: src/backend/app/data_access/timescale/migrations/003_retention_policies.sql:3
      resolution: proceed
      evidence: "Fünfter Lauf und fünfte Messreihe der Hauptsitzung (2026-11-28): Die Rohwert-Aufbewahrung selbst hinterlässt Vormerkungen; ein Neuberechnen von sensor_hourly jenseits der Rohwert-Frist löscht die Stundenwerte aller Mandanten. Die Prüfung 'volles Neuberechnen ändert nichts' in acceptance-4, -5 und -9 ist deshalb auf ein Neuberechnen innerhalb der Fristen umgestellt; die Löschwege berechnen Stundenwerte nur innerhalb der Rohwert-Frist und Tageswerte nur innerhalb der Stundenwert-Frist neu; Hook zu acceptance-9 um einen gelöschten Mandanten mit Stundenwerten älter als die Rohwert-Frist ergänzt."
---

## Description

Ein Mandanten-Archiv enthält die Sensor-Historie schon heute: Rohwerte der
letzten 90 Tage sowie Stunden- (2 Jahre) und Tageswerte (5 Jahre). Beim Import
wird sie aber übersprungen; ein wiederhergestellter Garten startet ohne
Messverlauf.

Nach dieser Änderung stellt der Import die Rohwerte mit her und ordnet sie den
Sensoren des neuen Mandanten zu. Rohwerte, die älter sind als die
Aufbewahrungsfrist der Installation, spielt er nicht ein; der Importbericht
nennt ihre Zahl. Für den wiederhergestellten Zeitraum zeigen die Diagramme
auch Stunden- und Tageswerte, gebildet aus den eingespielten Rohwerten. Auf
einer Installation ohne Zeitreihendatenbank gelingt der Import weiterhin und
meldet, dass die Messwerte übersprungen wurden. Schlägt ein Import fehl,
bleiben keine Messwerte zurück. Während die Messwerte geschrieben werden,
zeigt die Importliste das als eigene Phase.

Zugleich schließt das Feature eine Lücke beim Löschen von Messwerten: Wird ein
Sensor oder ein Garten gelöscht oder ein Import zurückgerollt, bleiben danach
keine Reste in der Zeitreihendatenbank vorgemerkt, die bei einem späteren
Neuberechnen die Stunden- und Tageswerte anderer Gärten löschen könnten.

Die älteren Stunden- und Tageswerte aus dem Archiv stellt F-34 wieder her; bis
dahin sagt der Importbericht ausdrücklich, dass sie nicht eingespielt wurden.

## Acceptance criteria

- [ ] **acceptance-1** Der Import stellt die Rohwerte des Archivs ab dem Stichtag wieder her, zugeordnet zu den Sensoren des neuen Mandanten, vollständig auch bei mehr als 1 000 000 Messwert-Zeilen; für Messwerte gilt nur die Größengrenze des Archivs.
- [ ] **acceptance-2** Nicht eingespielt und im Importbericht je Grund gezählt werden Rohwerte eines Sensors, der nicht im Archiv steht, und Rohwerte vor dem Stichtag; der Stichtag ist die früheste Grenze eines Tageswerts (Tagesbeginn in UTC), die nach dem ersten Rohwert des Archivs liegt und mindestens einen Tag jünger ist als die Rohwert-Aufbewahrung der Zielinstallation (heute 90 Tage) — auch ein junger Garten verliert so die Rohwerte seines ersten, angebrochenen Tages.
- [ ] **acceptance-3** Stimmt die Prüfsumme des Messwert-Teils nicht, scheitert schon die Hintergrundprüfung: Die Vorprüfung endet als fehlgeschlagen und lässt sich nicht starten.
- [ ] **acceptance-4** Nach dem Ende des Imports liefert die Messwert-Abfrage für den eingespielten Rohwert-Zeitraum auch Stunden- und Tageswerte des neuen Mandanten, gebildet aus seinen Rohwerten, und es ist keine Vormerkung des Imports offen: Ein anschließendes Neuberechnen innerhalb der Aufbewahrungsfristen (Stundenwerte über den Rohwert-Zeitraum, Tageswerte über den Stundenwert-Zeitraum der Installation) ändert keinen Stunden- oder Tageswert irgendeines Mandanten; außerhalb der Rohwert-Aufbewahrung berechnet der Import nichts neu.
- [ ] **acceptance-5** Ein Import, der nach dem Schreiben von Rohwerten fehlschlägt — ob er sofort zurückgerollt oder als abgebrochener Import später vom stündlichen Aufräumlauf entfernt wird —, hinterlässt keinen Rohwert und keinen Stunden- oder Tageswert des neuen Mandanten und keine offene Vormerkung: Ein anschließendes Neuberechnen innerhalb der Aufbewahrungsfristen (Stundenwerte über den Rohwert-Zeitraum, Tageswerte über den Stundenwert-Zeitraum der Installation) ändert keinen Stunden- oder Tageswert irgendeines Mandanten.
- [ ] **acceptance-6** Der Importbericht nennt die Zahl der importierten Rohwerte und sagt ausdrücklich, wie viele archivierte Stunden- und Tageswerte nicht eingespielt wurden; ohne Zeitreihendatenbank gelingt der Import und der Bericht sagt ausdrücklich, dass die Messwerte übersprungen wurden.
- [ ] **acceptance-7** Während ein Import Messwerte schreibt oder ihre Stunden- und Tageswerte neu berechnen lässt, zeigt die Importliste die Phase „Messwerte“.
- [ ] **acceptance-8** REQ-056 §8.3, §8.4, AK-47 und ein neues Abnahmekriterium in §16.4, REQ-005 (Löschen von Messwerten) sowie das Runbook (DE + EN) beschreiben den Import der Rohwerte, den Stichtag samt dem verlorenen ersten Tag, die beiden Regeln für nicht eingespielte Rohwerte, das gezielte Neuberechnen nach Import und Löschung und das Verhalten ohne Zeitreihendatenbank.
- [ ] **acceptance-9** Wird ein Sensor oder ein Mandant gelöscht, sind danach seine Rohwerte, Stunden- und Tageswerte entfernt, und kein Wert eines anderen Mandanten geht verloren, auch keiner, der älter ist als die Rohwert-Aufbewahrung; es ist keine Vormerkung der Löschung offen: Ein anschließendes Neuberechnen innerhalb der Aufbewahrungsfristen (Stundenwerte über den Rohwert-Zeitraum, Tageswerte über den Stundenwert-Zeitraum der Installation) ändert keinen Stunden- oder Tageswert irgendeines Mandanten. Stundenwerte berechnet die Löschung nur innerhalb der Rohwert-Aufbewahrung neu, Tageswerte nur innerhalb der Stundenwert-Aufbewahrung.

## Test hooks

- **acceptance-1** — `src/backend/tests/integration/test_tenant_export_readings_timescale.py` (Timescale service of `.github/workflows/backend-guards.yml`): the seed gains sensor documents of the source tenant (today the readings hang on `SHARED_SENSOR` without one, `:49`, `:68-85`); raw rows from the cut-off day on arrive under the new sensor keys; an archive with more than `MAX_ROWS` reading rows (`tenant_export_engine.py:1012`) imports every such row, streamed from the stored archive — pending
- **acceptance-2** — same module: raw rows of a `sensor_key` that is not a sensor of the archive, and raw rows before the cut-off, are not written and counted separately in the report; the cut-off is the start of a UTC day (a boundary of the daily bucket, `time_bucket('1 day', …)`, `data_access/timescale/migrations/002_continuous_aggregates.sql:26`), lies after the archive's first raw row and at least one day inside the target's raw retention, which is read from the target's effective retention policy (`003_retention_policies.sql:3` sets 90 days; a test with a changed policy proves it is not hard-coded); a garden whose first raw row is three days old loses the rows of that first partial day and the report counts them — pending
- **acceptance-3** — `src/backend/tests/unit/domain/services/test_tenant_export_service.py`: a readings part with a wrong SHA-256 ends the background check `failed`/`IMPORT_CHECKSUM_MISMATCH` (today the part is skipped before the comparison, `tenant_export_engine.py:1220-1228`) and a start is refused — pending
- **acceptance-4** — `src/backend/tests/integration/test_tenant_export_readings_timescale.py`: the target's aggregates are refreshed once before the import (as the fixture does, `:86-87`); a second tenant has raw rows and buckets in the imported raw period and older buckets without raw rows; after the import `query_hourly` / `query_daily` (`observation_repository.py:196-228`) return the new tenant's buckets of the raw period with the `sample_count` of its raw rows; the second tenant's older buckets come from the measured course R1–R2 (built by policy windows, raw rows then removed by `drop_chunks`), so the retention's pending marks are present; a snapshot of both materialisation tables before and after a refresh of `sensor_hourly` over the raw retention period and of `sensor_daily` over the hourly retention period is identical for every tenant; the test pins that the import issues no refresh of `sensor_hourly` before the raw cut-off and no refresh of `sensor_daily` outside the raw period (every range inside the retention of its level, so the guard of #3172 would admit it) — pending
- **acceptance-5** — same module, two scenarios: (a) induced failure after the raw rows were written → immediate rollback through `erase_abandoned_import` (`tenant_export_service.py:1354`); (b) the rollback is made to fail so the request stays `cleanup_pending` (`:1100-1106`), then the hourly sweep removes the half tenant (`_sweep_abandoned_import`, `:1429-1460`). In both: zero raw rows and zero buckets of the new tenant, and the before/after snapshot around the bounded refresh of acceptance-4 is identical for every tenant — pending
- **acceptance-6** — unit test with `readings=None` (the wiring without TimescaleDB, `src/backend/app/common/dependencies.py:1789`): the report says skipped for lack of a time-series database; integration test: the report carries the raw count and names the archived hourly and daily rows as not imported with their counts (F-34 replaces that entry by the imported counts) — pending
- **acceptance-7** — service test (phase on the record while readings are written and while the refresh runs) + vitest of the import list from F-33 (phase label DE/EN) — pending
- **acceptance-8** — `mkdocs build --strict` + spec diff review (REQ-056, `spec/req/REQ-005_Hybrid-Sensorik.md`, runbook DE/EN) — pending
- **acceptance-9** — new integration test against TimescaleDB next to the module above: `delete_by_sensor` and `delete_by_tenant` (`observation_repository.py:278`, `:300`) recompute, in one place of the data-access layer (not per caller), `sensor_hourly` over the period of the deleted raw rows, clipped to the raw retention, and then `sensor_daily` over the period of the deleted hourly rows, clipped to the hourly retention (`_purge_aggregates` deletes hourly rows directly, `:265-275`, which marks their days for the daily values — derived from the measured direct insert); fixtures: a second tenant with raw rows and buckets in the same period and with old buckets whose raw rows the retention removed (course R1–R2); a deleted tenant that itself has hourly values older than the raw retention; afterwards the deleted tenant's or sensor's rows and buckets are gone, every row of the second tenant is still there (its daily values inside the recomputed period equal what its hourly values yield), and the before/after snapshot around the bounded refresh of acceptance-4 is identical for every tenant; no refresh call leaves the retention of its level (the guard of #3172 would admit each) — pending

## Consistency notes

Manual pass performed by: Claude (Subagent der Planungssitzung vom 2026-11-28, im Auftrag des Betreibers nolte) — betrifft den Abschnitt „Re-run 2026-11-28“; die älteren Läufe stammen vom `feature-consistency-reviewer`.

Geltend sind Beschreibung, Kriterien, Hooks und der jüngste Abschnitt dieser Notizen („Stand nach dem fünften Agentenlauf“). Alle älteren Abschnitte sind Verlauf: Ihre Kriteriennummern, Feature-Zuschnitte und Aussagen geben den Stand ihres Laufs wieder.

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

**Korrektur 2026-11-28 zur Notiz „Bounds and rollback“.** Der Rollback erfasst Messwerte bereits: `_rollback` (Definition `tenant_export_service.py:1324`) ruft `erase_abandoned_import` auf (`:1354`), das über das Löschinventar `delete_by_tenant` ausführt (`tenant_service.py:2580-2594`). „does not cover readings“ gilt nur ohne konfiguriertes Löschinventar. Verrutschte Anker der Notizen oben: `observation_repository.py:117-144` ist `:132-144` (`AGGREGATE_VIEWS` `:119`); `migrations/002_continuous_aggregates.sql` liegt unter `src/backend/app/data_access/timescale/migrations/`. Die Entscheidung vom 2026-11-17 „hourly/daily only before it“ ist in acceptance-3 um die Rand-Buckets präzisiert.

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

### Re-run 2026-11-28

Manueller, rein lesender Durchgang gegen develop `17e1034d2`; Lauf, Auslöser und Vorbehalte wie in `tenant-archive-size-limits.md` (kein Test gelaufen; manueller Durchgang statt Agent, als Workflow-Health-Befund vermerkt). Die Zeilenanker dieses Features wurden nachgelesen; korrigiert sind zwei (unten).

**Befunde vom 2026-11-27 — Verbleib.**

1. `src/backend/app/domain/services/tenant_service.py:2592` (prior-art, proceed) — unverändert richtig (`_purge_tenant_readings` `:2580-2594`). acceptance-5 ist ein Test für den bestehenden Pfad.
2. `src/backend/app/domain/engines/tenant_export_engine.py:1220` (drift) — erledigt durch acceptance-2.
3. `src/backend/app/domain/services/observation_service.py:64` (drift) — erledigt: Regel in acceptance-1 (auslassen und zählen), Herleitung unten.
4. `spec/req/REQ-056_Mandanten-Lebenszyklus-Kontingente.md:683` (drift) — erledigt durch acceptance-10.
5. `src/backend/tests/integration/test_tenant_export_readings_timescale.py:151` (prior-art) — erledigt: Die Hooks nennen dieses Modul.
6. `project/features/tenant-readings-import.md:36` (drift) — erledigt: Die Beschreibung spricht nur noch vom wiederhergestellten Garten; die Abhängigkeit von F-15 steht unter References.

Korrigierte Anker: Ohne TimescaleDB bekommt der Dienst `readings=None` in `src/backend/app/common/dependencies.py:1789` (der Lauf vom 27.11. nannte `:1787`; die Datei hat seither zwei Zeilen mehr). Die Aggregat-Definition liegt unter `src/backend/app/data_access/timescale/migrations/002_continuous_aggregates.sql:23-35` (die Notiz vom 17.11. nannte den Pfad verkürzt).

Der Block vom 2026-11-27, wie er bis zu diesem Lauf im Frontmatter stand:

```yaml
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
```

**Festlegungen dieses Laufs.**

- **Zeilen ohne zuordenbaren Sensor: auslassen und zählen (drift, proceed).** Established: Der normale Schreibpfad nimmt einen Messwert nur für einen eigenen Sensor an (`observation_service.py:64-74`). Für Verweise in Dokumenten gilt beim Import bereits eine Regel: Ein mandanteninterner Verweis, den das Archiv nicht hält, wird geleert und gezählt, nie behalten (`tenant_import_engine.py:21-26`, `_internal` `:423-431`, Bericht `nulled_references` in `tenant_export_service.py:1239`); `sensor_key` ist als solcher Verweis deklariert (`tenant_export_engine.py:481`). Ein Messwert ohne Sensor lässt sich nicht „leeren“; die Entsprechung ist, die Zeile nicht zu schreiben und sie im Bericht zu zählen. Das ist eine Herleitung der Planung aus der bestehenden Regel, keine Betreiberentscheidung; die Alternative „ganzes Archiv ablehnen“ stand im Lauf vom 27.11. zur Wahl (siehe „Offene Punkte“).
- **Rand-Buckets (drift, proceed).** Established: `sensor_daily` wird aus `sensor_hourly` berechnet (`002_continuous_aggregates.sql:23-35`). Unestablished: wie sich ein `refresh_continuous_aggregate` über das Rohwert-Fenster auf die Stunde und den Tag auswirkt, in die der früheste Rohwert fällt, wenn für sie nur ein Teil der Rohwerte vorliegt; das zeigt erst der Integrationstest zu acceptance-3 (nicht durchgeführt). acceptance-3 legt das erwartete Ergebnis fest (Wert wie vor dem Export), nicht den Weg. [Überholt durch die Entscheidung vom 2026-11-28 und die Messung: Der Import berechnet nichts neu; die Stunden- und Tageswerte liegen in F-34.]
- **Bericht mit und ohne Zeitreihendatenbank (prior-art, proceed).** Established: Heute meldet der Import jeden Zeitreihen-Teil als `not_imported:<part>` mit der Zeilenzahl (`tenant_export_service.py:1240-1242`), ob eine Zeitreihendatenbank da ist oder nicht. acceptance-6 trennt „importiert (mit Zahlen)“ von „übersprungen, keine Zeitreihendatenbank“.
- **Überschneidung mit F-17 (overlap, proceed).** Begründung für `proceed`: Die Phase „Messwerte“ stand bis 2026-11-28 in F-17 Kriterium 5 und ist hierher verschoben, weil F-16 in der entschiedenen Reihenfolge nach F-17 kommt und erst F-16 Messwerte schreibt. acceptance-9 ergänzt die Phasenanzeige aus F-17 um einen Wert; acceptance-7 benutzt den Weg über die Vorprüfung, den F-17 liefert. Beides sind Abhängigkeiten in einer Richtung (F-16 nach F-17), kein doppelt umgesetzter Umfang.
- **Überschneidung mit F-15 (overlap, proceed).** Begründung für `proceed`: F-16 liest die Messwerte aus dem gespeicherten Archiv, begrenzt nur durch die Archivgrenze aus F-15, und meldet einen Fehler über das Detailfeld aus F-15 acceptance-6. F-16 ändert keine Größe und kein Feld, das F-15 definiert.

**Umgesetzte Edits aus dem Lauf vom 2026-11-27** (alle sieben): Prüfsumme des Messwert-Teils (acceptance-2); Regel für nicht zuordenbare `sensor_key` (acceptance-1); Kriterium 6 um AK-47 und Runbook erweitert (acceptance-10); Hooks auf `test_tenant_export_readings_timescale.py`, Kriterium 5 geteilt in Roundtrip (acceptance-7) und Layout (acceptance-2, als Verhalten des Imports statt als Aussage über einen Test); Abhängigkeit von F-15 eingetragen; Rollback-Notiz korrigiert (oben datiert vermerkt); Abschnitt „Betreiberentscheidungen 2026-11-27“ vorhanden. Zusätzlich: altes Kriterium 3 geteilt (acceptance-4, -5), Rand-Buckets in acceptance-3, Bericht in acceptance-6, Mandantentrennung der importierten Messwerte (acceptance-8), Phase „Messwerte“ aus F-17 übernommen (acceptance-9).

**Wertnachweis des Sprints.** `verifies_sprint_value: acceptance-7`. Das Kriterium läuft durch alle vier Features: Hintergrundprüfung und Größenpfad (F-15), Dokumentprüfung eines unveränderten Archivs (F-32), Vorprüfung mit E-Mail-Zuordnung und Start aus dem gespeicherten Archiv (F-17), Messwerte (F-16). Die Größe von rund 500 MiB weist es nicht nach; das bleibt nach Betreiberentscheidung der manuelle Lauf zu F-15 acceptance-1.

**Verhältnis der vier Features (R-19).** F-16 setzt F-15 und F-17 voraus und steht deshalb zuletzt. Die Reihenfolge F-15 → F-32 → F-17 → F-16 trägt.

**Ergebnis:** kein ungelöster Befund; F-16 ist `ready`. Die Regel „auslassen und zählen“ ist eine Planungsfestlegung, die der Betreiber vor dem Start von F-16 bestätigen oder ändern kann.

### Agentenlauf 2026-11-28

Lauf des `feature-consistency-reviewer` (`agent_version: feature-consistency-reviewer@unknown`) am 2026-11-28 gegen den Stand `3a8c33e43`, von der Hauptsitzung gestartet; die Befunde stehen sinngemäß im Frontmatter. Damit ist der im manuellen Durchgang vermerkte Workflow-Health-Befund erledigt. Die Einarbeitung unten stammt vom selben Subagenten wie der manuelle Durchgang; die zitierten Stellen wurden nachgelesen, ein Test lief nicht. Nach dieser Einarbeitung lässt die Hauptsitzung den Agenten erneut laufen.

Der Block des manuellen Durchgangs vom 2026-11-28, wie er bis zu diesem Lauf im Frontmatter stand:

```yaml
consistency_check:
  performed_at: 2026-11-28
  agent_version: manual-2026-11-28
  findings:
    - kind: prior-art
      target: src/backend/app/domain/services/tenant_service.py:2592
      resolution: proceed
      evidence: "_rollback (tenant_export_service.py:1324, Aufruf erase_abandoned_import :1354) führt über das Löschinventar zu _purge_tenant_readings: 'removed = self._observation_repo.delete_by_tenant(tenant_key)' (:2580-2594); Docstring :1331 'every row, edge, object and reading of the tenant'. acceptance-5 braucht einen Test, keinen neuen Pfad."
    - kind: drift
      target: src/backend/app/domain/engines/tenant_export_engine.py:1220
      resolution: proceed
      evidence: "'if is_ignored_part(name): # Listed (above) but never decompressed …; continue' (:1220-1224) steht vor dem sha256-Vergleich (:1225-1228); acceptance-2 verlangt die Prüfsumme des Messwert-Teils vor dem Schreiben."
    - kind: drift
      target: src/backend/app/domain/services/observation_service.py:64
      resolution: proceed
      evidence: "_require_owned_sensor (:64-74) lässt den normalen Schreibpfad nur für einen eigenen Sensor zu; 'sensor_key': _internal('sensors') ist deklariert (tenant_export_engine.py:481); ein Verweis, den das Archiv nicht hält, wird vom Import geleert und gezählt (tenant_import_engine.py:21-26, :423-431). acceptance-1 überträgt die Regel: Zeile auslassen und zählen."
    - kind: drift
      target: spec/req/REQ-056_Mandanten-Lebenszyklus-Kontingente.md:683
      resolution: proceed
      evidence: "AK-47: 'ein Leser des Formats 1 importiert das Archiv, entpackt den Teil nicht und meldet not_imported:…'; §8.3 (:365) 'der Import von Messwerten ist nicht Teil dieser Fassung'; Runbook DE :8, :26, :146. acceptance-10 nennt AK-47, §8.3, §8.4, §16.4 und das Runbook."
    - kind: prior-art
      target: src/backend/tests/integration/test_tenant_export_readings_timescale.py:151
      resolution: proceed
      evidence: "test_the_archive_carries_the_tenants_readings_and_an_import_lists_but_skips_them läuft in CI gegen TimescaleDB (.github/workflows/backend-guards.yml ab :417); das Roundtrip-Modul verdrahtet NullObservationRepository (test_tenant_export_roundtrip.py:358). Die Hooks nennen das Timescale-Modul."
    - kind: prior-art
      target: src/backend/app/data_access/timescale/observation_repository.py:132
      resolution: proceed
      evidence: "resolve_aggregate_tables (:132-144, AGGREGATE_VIEWS :119) löst die Materialisierungstabellen auf und wirft, wenn eine fehlt; iter_tenant_readings (:320), delete_by_tenant (:300); sensor_daily wird aus sensor_hourly berechnet (data_access/timescale/migrations/002_continuous_aggregates.sql:23-35)."
    - kind: overlap
      target: F-17
      resolution: proceed
      evidence: "acceptance-9 ergänzt die Phasenanzeige aus F-17 acceptance-7 um 'Messwerte'; acceptance-7 nutzt den Weg über die Vorprüfung aus F-17. Begründung in den Consistency notes (Re-run 2026-11-28)."
    - kind: overlap
      target: F-15
      resolution: proceed
      evidence: "acceptance-4 ('nur die Archivgrenze gilt') setzt die Größen und /tmp-Werte aus F-15 voraus; acceptance-2 nutzt das Detailfeld aus F-15 acceptance-6. Begründung in den Consistency notes (Re-run 2026-11-28)."
```

**Befunde und Einarbeitung.**

- **Nichts neu berechnen (drift, proceed; Betreiberentscheidung 2026-11-28).** Established: `refresh_continuous_aggregate` arbeitet über einen Zeitbereich, nicht je Mandant; das Repository hält selbst fest, dass Buckets älter als die Rohwert-Aufbewahrung nicht neu berechnet werden können und ein breiteres Neuberechnen die Historie anderer Mandanten löschen würde (`observation_repository.py:245-251`); Rohwerte bleiben 90 Tage (`migrations/003_retention_policies.sql:3`). Die Entscheidung vom 2026-11-17 („hourly/daily only before it, refresh only the raw window“, R13) ist damit ersetzt: Der Import schreibt alle archivierten Stunden- und Tageswerte direkt in die Materialisierungstabellen und stößt kein Neuberechnen an. acceptance-3 verlangt Gleichheit mit dem Archiv für alle Buckets einschließlich der Rand- und der jüngsten Buckets, acceptance-8 sichert die anderen Mandanten (REQ-056 AK-33). Die Toleranz für neu berechnete Zahlen in acceptance-7 entfällt.
- **Policy-Lauf über direkt geschriebene Buckets (drift, revisit-after Integrationstest).** Established: Die Policies decken stündlich die letzten 3 Stunden bis 1 Stunde und täglich die letzten 3 Tage bis 1 Tag ab (`002_continuous_aggregates.sql:16-19`, `:37-40`). Das Repository beschreibt: Ein Bucket wird nur neu berechnet, wenn ein Neuberechnen seinen Bereich abdeckt, und eine Änderung an Rohwerten vermerkt den Bereich als ungültig, sodass der nächste Policy-Lauf ihn aus den Rohwerten neu bildet (`observation_repository.py:245-260`). Daraus folgt für Buckets im Policy-Fenster zur Zeit des Imports: Sie werden aus den importierten Rohwerten neu gebildet. Das ergibt den Archivwert nur, wenn die Rohwerte dieses Fensters vollständig im Archiv stehen; bei 90 Tagen Rohwert-Aufbewahrung und Fenstern von 3 Stunden bzw. 3 Tagen ist das der Fall, solange der Export alle Rohwerte des Mandanten enthält (AK-47, `REQ-056:683`). Buckets außerhalb des Fensters fasst die Policy nicht an. Unestablished: (a) ob ein Policy-Lauf einen direkt geschriebenen Bucket in seinem Fenster unverändert lässt, wenn für ihn keine Rohwerte importiert wurden (etwa ein Tageswert, dessen Rohwerte schon abgelaufen sind, was im 3-Tage-Fenster nicht vorkommen sollte); (b) ob das direkte Schreiben neben den Rohwerten zu doppelten Zeilen in der Abfrage führt, falls die Aggregate in Echtzeit lesen (`002_continuous_aggregates.sql` setzt `materialized_only` nicht; Image `timescale/timescaledb:2.32.1-pg16`, `docker-compose.yml:99`); (c) ob die von den importierten Rohwerten vermerkten ungültigen Bereiche außerhalb des Fensters später durch ein händisches breites Neuberechnen Buckets verändern. Alle drei klärt der Integrationstest zu acceptance-3 gegen TimescaleDB (nicht durchgeführt); (c) steht zusätzlich in den Risiken.
- **Fixture ohne Sensoren (prior-art, proceed).** Established: Der Seed schreibt nur Messwerte, keine Sensor-Dokumente (`test_tenant_export_readings_timescale.py:49`, `:68-85`). Die Hooks zu acceptance-1, -7 und -8 verlangen Sensoren im Seed.
- **Wo die Prüfsumme scheitert (drift, proceed).** Festlegung der Planung: in der Hintergrundprüfung, also vor dem Start; das Archiv wird dort ohnehin gelesen, und der Admin soll kein Archiv starten können, dessen Messwert-Teil beschädigt ist. Das Tabellenlayout kann sich zwischen Vorprüfung und Start ändern und braucht die Zeitreihendatenbank; es wird im Lauf geprüft, vor dem ersten Messwert (acceptance-11, aus acceptance-2 herausgelöst).
- **Voraussetzungen des Wertnachweises (prior-art, proceed).** Zwei ArangoDB-Datenbanken und Fotos ohne EXIF stehen im Hook zu acceptance-7.
- **Überschneidung mit F-17 (overlap, proceed).** Begründung für `proceed`: unverändert wie im manuellen Durchgang (Phase „Messwerte“ ergänzt die Anzeige aus F-17, der Wertnachweis nutzt die Vorprüfung); neu hinzu kommt, dass acceptance-2 das Ergebnis über die Liste aus F-17 zeigt. Alles sind Abhängigkeiten in einer Richtung, F-16 nach F-17.

**Betreiberentscheidung zur Regel für Sensoren.** „Auslassen und zählen“ ist am 2026-11-28 bestätigt und gilt auch für die Stunden- und Tageswerte eines nicht zuordenbaren Sensors (acceptance-1). Der Vorbehalt des manuellen Durchgangs entfällt.

**Nummern.** acceptance-7 bleibt der Wertnachweis (`verifies_sprint_value`). acceptance-8 ist um die Unversehrtheit anderer Mandanten erweitert; acceptance-11 ist neu (aus acceptance-2 herausgelöst).

**Ergebnis:** alle Befunde eingearbeitet; offen ist als Experiment nur das Policy-Verhalten, das der Hook zu acceptance-3 klärt. F-16 ist `ready`, vorbehaltlich des erneuten Agentenlaufs. Mit elf Kriterien liegt das Feature über der Empfehlung der Feature-Spec.

### Stand nach dem zweiten Agentenlauf (2026-11-28)

Zweiter Lauf des `feature-consistency-reviewer` (`feature-consistency-reviewer@unknown`) am 2026-11-28 gegen `22ec65763`, von der Hauptsitzung gestartet; dazu ein Versuch der Hauptsitzung gegen TimescaleDB und drei Betreiberentscheidungen. Die Befunde beider Agentenläufe stehen im Frontmatter (angehängt, nicht ersetzt). Die Einarbeitung stammt vom Subagenten der Planungssitzung; die zitierten Stellen wurden nachgelesen, ein eigener Test lief nicht.

**Teilung (Betreiberentscheidung A).** F-16 behält Rohwerte, Prüfsumme, Rollback der Rohwerte, Bericht und Phase. Stunden- und Tageswerte, Mandantentrennung, Tabellenlayout und der Rundlauf als Wertnachweis liegen in F-34 (`tenant-readings-aggregates-import.md`). Zuordnung der alten Kriterien (Stand `22ec65763`): 1 → 1 und 2 (Rohwerte) sowie F-34 acceptance-1 (Buckets nicht zuordenbarer Sensoren), 2 → 3, 3 → F-34 acceptance-1 und -2, 4 → 1, 5 → 4 und F-34 acceptance-5, 6 → 5 und F-34 acceptance-1, 7 → F-34 acceptance-6 (Wertnachweis), 8 → F-34 acceptance-3, 9 → 6, 10 → 7 und F-34 acceptance-7, 11 → F-34 acceptance-4. `verifies_sprint_value` ist hier `null`.

**Messung der Hauptsitzung gegen TimescaleDB 2.32.1-pg16** (dasselbe Image wie `docker-compose.yml:99`), 2026-11-28; Befehle sinngemäß, Ergebnisse wie übermittelt:

- Abfrage von `timescaledb_information.continuous_aggregates`: Die Aggregate sind `materialized_only = true`; Materialisierungstabellen `_timescaledb_internal._materialized_hypertable_2` (hourly) und `_3` (daily); Spalten hourly: `bucket, tenant_key, sensor_key, sensor_type, avg_value, min_value, max_value, sample_count`.
- `INSERT` in die Materialisierungstabelle: „Direktes INSERT in die Materialisierungstabelle wird angenommen und ist sofort über die Sicht `sensor_hourly` sichtbar“; auch ein `INSERT` über die Sicht selbst wurde angenommen.
- `refresh_continuous_aggregate` ohne vorgemerkte Änderung: lässt direkt geschriebene Buckets unverändert („already up-to-date“).
- Rohwerte in den Zeitraum eines Buckets schreiben, dann neu berechnen: „Schreibt der Import Rohwerte in den Zeitraum eines Buckets, merkt TimescaleDB den Bereich vor; das nächste Neuberechnen darüber bildet die Buckets ALLER Mandanten in diesem Bereich aus den Rohwerten neu.“ Gemessen: Mandant A bekam 2 Rohwerte in eine Stunde, in der A (6 Stichproben) und B (3 Stichproben, keine Rohwerte) direkt geschriebene Buckets hatten; nach dem Neuberechnen: A = Mittel der 2 Rohwerte (`sample_count` 2), B gelöscht. Ebenso für einen 300 Tage alten Bucket nach einem Rohwert-Insert und `refresh(NULL, NULL)`.
- Nie aufgefrischte Datenbank: Das erste `refresh(NULL, NULL)` löscht alle direkt geschriebenen Buckets (Wassermarke am Anfang).
- Die Policies decken nur 3 h bis 1 h (stündlich) und 3 d bis 1 d (täglich) ab; vorgemerkte Bereiche außerhalb bleiben liegen, bis jemand breiter auffrischt.

Damit sind die Punkte (a) und (b) aus dem Abschnitt „Agentenlauf 2026-11-28“ geklärt: (a) ein direkt geschriebener Bucket ohne vorgemerkte Änderung bleibt; (b) keine Doppelzählung, weil die Aggregate nur Materialisiertes lesen. Punkt (c) ist bestätigt und der Grund für die Vorgabe „keine Rohwerte älter als die Aufbewahrung“.

**Vorgabe der Hauptsitzung (aus der Messung).** Rohwerte, die älter sind als die Rohwert-Aufbewahrung der Zielinstallation, werden nicht eingespielt, sondern gezählt und im Bericht genannt (acceptance-2). Established: Die Frist setzt die Aufbewahrungs-Policy (`migrations/003_retention_policies.sql:3`, 90 Tage). Grund: Solche Rohwerte entfielen beim nächsten Aufräumlauf ohnehin, und ihr Einspielen merkt Bereiche vor, in denen andere Mandanten keine Rohwerte mehr haben. Ihre Stunden- und Tageswerte kommen aus dem Archiv (F-34). Unestablished: ob es neben der Policy eine Einstellung für die Frist gibt (eine Suche nach einer Sensor-Aufbewahrung in `config/settings.py` fand keine); der Hook verlangt, dass der Import die wirksame Policy liest.

**Ergebnis:** eingearbeitet; F-16 ist `ready`, vorbehaltlich des dritten Agentenlaufs. Sieben Kriterien.

### Stand nach dem dritten Agentenlauf (2026-11-28)

Dritter Lauf des `feature-consistency-reviewer` (`feature-consistency-reviewer@unknown`) am 2026-11-28 gegen `b3c7f6eba`, von der Hauptsitzung gestartet; dazu weitere Messungen der Hauptsitzung gegen TimescaleDB und zwei Betreiberentscheidungen (D, E). Die Einarbeitung stammt vom Subagenten der Planungssitzung; die zitierten Stellen wurden nachgelesen, ein eigener Test lief nicht.

**Weitere Messungen der Hauptsitzung gegen TimescaleDB 2.32.1-pg16**, 2026-11-28; Befehle sinngemäß, Ergebnisse wie übermittelt:

- **Ebene Stunden → Tage.** Auf einer einmal voll aufgefrischten Datenbank wurde für einen 900 Tage alten Tag ein Stundenwert von Mandant A direkt eingefügt, dazu direkte Tageswerte für A (avg 22, 40 Stichproben) und B (avg 11, 30 Stichproben; B ohne Stundenwerte). Nach `refresh_continuous_aggregate('sensor_daily', NULL, NULL)`: A = avg 20, 4 Stichproben (aus seinem Stundenwert neu gebildet), B gelöscht. Das direkte Einfügen eines Stundenwerts merkt den Tag also für die Tageswerte aller Mandanten vor.
- **Begrenztes Neuberechnen.** Auf einer frischen Datenbank mit direkten Buckets für A und B (300 Tage alt und 20 Tage alt): Rohwerte für A und B in die 20-Tage-Stunde eingefügt, dann `refresh_continuous_aggregate('sensor_hourly', <diese Stunde>, <+1 h>)` → A = 50/2, B = 12/3 (beide aus ihren Rohwerten), die 300 Tage alten Buckets beider unverändert. Ein begrenztes Neuberechnen über einen Bereich, in dem alle Mandanten ihre Rohwerte haben, ist für andere unschädlich.
- **Frische Installation.** Dieselbe Datenbank danach `refresh(NULL, NULL)` → die 300 Tage alten, direkt geschriebenen Stundenwerte beider Mandanten gelöscht (nie voll aufgefrischt, also gelten sie als nie materialisiert). Nicht gemessen: ob Policy-Läufe allein das auslösen (die Jobs 1000/1001 existieren; der Lauf per `run_job` gelang im Versuch nicht).

**Schichtung nach Aufbewahrungsfristen (Vorgabe der Hauptsitzung).** Established: Die Zielinstallation hält Rohwerte 90 Tage, Stundenwerte 2 Jahre, Tageswerte 5 Jahre (`data_access/timescale/migrations/003_retention_policies.sql:3`, `:6`, `:9`). Was älter ist als die Frist seiner Ebene, wird nicht eingespielt, sondern gezählt; die Fristen liest der Import aus den wirksamen Policies. Der Schnitt liegt jeweils auf einer Tagesgrenze mit Abstand zur Frist, damit kein halb gedeckter Bucket entsteht und ein gleichzeitiger Aufbewahrungslauf keine eben eingespielten Zeilen trifft. Daraus folgt: In jedem Zeitraum, den der Import neu berechnen lässt, haben alle Mandanten ihre Quelldaten noch (Rohwerte innerhalb der Rohwert-Frist, Stundenwerte innerhalb der Stundenwert-Frist); nach der Messung „Begrenztes Neuberechnen“ ist das für sie unschädlich.

- **Gezieltes Neuberechnen schon hier (Betreiberentscheidung D; Abweichung von der Vorgabe, begründet).** Die Vorgabe der Hauptsitzung ordnet das Neuberechnen F-34 zu. Die Planung legt den Teil, der die Rohwerte betrifft, in F-16: Der Import schreibt hier Rohwerte, und jeder Rohwert merkt seinen Zeitraum vor (Messung). Bliebe das Neuberechnen bis F-34 aus, hätte ein nach F-16 importierter Garten für den Rohwert-Zeitraum keine Stunden- und Tageswerte (die Policies decken nur 3 Stunden bzw. 3 Tage, `002_continuous_aggregates.sql:16-19`, `:37-40`), und die Vormerkungen blieben dauerhaft offen. Dieselbe Vorgabe verlangt das Neuberechnen am Ende eines Rollbacks, sobald Rohwerte geschrieben waren; auch das liegt in F-16. acceptance-4 und -5 prüfen es mit dem starken Test: Ein volles Neuberechnen danach ändert nichts, bei keinem Mandanten. F-34 fügt das direkte Schreiben der älteren Werte und das Neuberechnen der Tageswerte über den Stundenwert-Zeitraum hinzu. Widerspricht die Hauptsitzung, wandern acceptance-4 und der zweite Halbsatz von acceptance-5 nach F-34.
- **Stichtag (Vorgabe der Hauptsitzung, präzisiert).** Der Schnitt liegt auf einer Tagesgrenze mit Abstand zur Frist. Die Planung ergänzt: auch nach dem ersten Rohwert des Archivs. Sonst wäre der erste Tag nur teilweise mit Rohwerten gedeckt, und sein Stunden- und Tageswert würde aus einem Teil der Rohwerte neu gebildet statt aus dem Archiv übernommen.
- **Zwischenstand bis F-34 (Vorgabe 5).** Der Bericht nennt die archivierten Stunden- und Tageswerte als nicht eingespielt, mit Zahl (acceptance-6); die Phase „Messwerte“ umfasst Schreiben und Neuberechnen (acceptance-7) und später auch die Schritte aus F-34.
- **Frontmatter bereinigt.** Das überholte `revisit-after` zum Policy-Verhalten ist `proceed` mit Verweis auf die Messungen; die Kriteriennummern früherer Stände in den Befunden nennen den heutigen Ort.

**Ergebnis:** eingearbeitet; F-16 ist `ready`, vorbehaltlich des nächsten Agentenlaufs. Acht Kriterien, eines über dem angestrebten Rahmen, weil das Neuberechnen des Rohwert-Zeitraums hier liegt.

### Stand nach dem vierten Agentenlauf (2026-11-28)

Vierter Lauf des `feature-consistency-reviewer` (`feature-consistency-reviewer@unknown`) am 2026-11-28 gegen `9c779f351`, von der Hauptsitzung gestartet; dazu eine weitere Messung der Hauptsitzung gegen TimescaleDB und die Betreiberentscheidung F. Die Einarbeitung stammt vom Subagenten der Planungssitzung; die zitierten Stellen wurden nachgelesen, ein eigener Test lief nicht.

- **Löschlücke (drift, proceed; Betreiberentscheidung F).** Established: Das Löschen der Rohwerte eines Sensors oder Mandanten entfernt auch seine Buckets (`_purge_aggregates`, `observation_repository.py:242-276`), berechnet aber nichts neu; der Kommentar dort hält fest, dass die Vormerkung des gelöschten Bereichs liegen bleibt (`:259-262`). Gemessen (Hauptsitzung, 2026-11-28): Ein späteres Neuberechnen über einen solchen Bereich bildet die Buckets aller Mandanten aus den Rohwerten neu und löscht die, für die keine mehr da sind. Dieselbe Löschung nutzen der Rollback eines Imports (`tenant_export_service.py:1354`) und der Sweep abgebrochener Importe (`_sweep_abandoned_import`, `:1429-1460`; `erase_abandoned_import`, `tenant_service.py:487`). Entschieden: Jedes Löschen von Rohwerten berechnet seinen Zeitraum unmittelbar gezielt neu, erst Stunden-, dann Tageswerte, an einer Stelle im Datenzugriff. Das ist unschädlich, solange die Rohwerte der anderen Mandanten dort noch vorhanden sind (gemessen für Stundenwerte). acceptance-9 ist das eigene Kriterium; acceptance-5 nennt Rollback und Sweep ausdrücklich.
- **Grenze der Frist.** Unestablished: ob am Rand der Rohwert-Aufbewahrung ein Mandant noch Rohwerte hat und ein anderer im selben Zeitraum nicht mehr; die Aufbewahrung entfernt Rohwerte nicht je Mandant, sondern je Zeitabschnitt der Tabelle, was dafür spricht, dass es nicht vorkommt. Der Hook zu acceptance-9 prüft den Randfall.
- **Begrenztes Neuberechnen der Tageswerte ist hergeleitet, nicht gemessen.** Gemessen wurde das begrenzte Neuberechnen der Stundenwerte aus Rohwerten. F-16 wird vor F-34 gebaut und berechnet als erstes Feature auch Tageswerte begrenzt neu; der Hook zu acceptance-4 ist die Messung.
- **Stichtag.** „Tagesgrenze“ heißt die Grenze des Tages-Buckets, also Tagesbeginn in UTC (`002_continuous_aggregates.sql:26`). Dass auch ein junger Garten die Rohwerte seines ersten, angebrochenen Tages verliert, ist gewollt: Sonst würde der Stunden- und Tageswert dieses Tages aus einem Teil der Rohwerte gebildet. Der Bericht zählt sie, das Runbook nennt es (acceptance-2, -8).

**Ergebnis:** eingearbeitet; F-16 ist `ready`, vorbehaltlich des nächsten Agentenlaufs. Neun Kriterien; die Hauptsitzung hat bis zu zehn zugelassen, weil die Löschlücke hier mit behoben wird.

### Stand nach dem fünften Agentenlauf (2026-11-28)

Fünfter Lauf des `feature-consistency-reviewer` (`feature-consistency-reviewer@unknown`) am 2026-11-28, von der Hauptsitzung gestartet, und ihre fünfte Messreihe gegen TimescaleDB 2.32.1-pg16 (vollständig in `tenant-readings-aggregates-import.md`). Kern der Messung: Die Rohwert-Aufbewahrung hinterlässt selbst Vormerkungen (R2), und ein Neuberechnen von `sensor_hourly` über einen solchen Tag löscht die Stundenwerte aller Mandanten dort (R3); ein Neuberechnen nur von `sensor_daily` über einen Zeitraum, in dem die Stundenwerte aller stehen, ist unschädlich (R4). Einarbeitung durch den Subagenten der Planungssitzung; kein eigener Test.

- **Kein volles Neuberechnen als Prüfung (drift, proceed).** acceptance-4, -5 und -9 verlangten bisher, dass ein Neuberechnen über den ganzen Zeitraum nichts ändert. Nach R3 ist das in jeder Installation falsch, die älter ist als die Rohwert-Frist: Ein solches Neuberechnen löscht die ältere Historie aller Mandanten, unabhängig vom Import. Geprüft wird jetzt mit einem Neuberechnen innerhalb der Fristen: Stundenwerte über den Rohwert-Zeitraum, Tageswerte über den Stundenwert-Zeitraum der Installation.
- **Was F-16 neu berechnen lässt (Vorgabe der Hauptsitzung).** Der Import: `sensor_hourly` und danach `sensor_daily` über den eingespielten Rohwert-Zeitraum, nie davor. Die Löschwege (acceptance-9, auch Rollback und Sweep): `sensor_hourly` über den Zeitraum der gelöschten Rohwerte innerhalb der Rohwert-Frist, `sensor_daily` über den Zeitraum der gelöschten Stundenwerte innerhalb der Stundenwert-Frist. Established: `_purge_aggregates` löscht Stundenwerte direkt aus der Materialisierungstabelle (`observation_repository.py:265-275`). Unestablished: dass ein direktes Löschen eines Stundenwerts den Tag für die Tageswerte vormerkt wie das gemessene direkte Einfügen; der Hook zu acceptance-9 prüft es.
- **Guard aus #3172.** Das Issue trägt die Runbook-Warnung und einen Guard gegen ein Neuberechnen jenseits der Frist; es ist nicht Teil von Sprint 5. Die Aufrufe aus F-16 liegen immer innerhalb der Frist ihrer Ebene, sodass der Guard sie zuließe (Hooks zu acceptance-4 und -9).
- **Tageswerte.** Das begrenzte Neuberechnen der Tageswerte ist jetzt gemessen (R4); der Vermerk „hergeleitet“ aus dem vorigen Abschnitt ist für diesen Fall erledigt.

**Ergebnis:** eingearbeitet; F-16 ist `ready`, vorbehaltlich des nächsten Agentenlaufs. Neun Kriterien.

## Risks

- **Neuberechnen über den Rohwert-Zeitraum.** Es bildet die Stunden- und Tageswerte aller Mandanten in diesem Zeitraum aus ihren Quelldaten neu. Das ist unschädlich, solange alle ihre Rohwerte dort noch haben (gemessen); der Stichtag mit Abstand zur Frist stellt das sicher. Jenseits der Rohwert-Frist wird `sensor_hourly` nie neu berechnet: Dort liegen die Vormerkungen der Aufbewahrung, und ein Neuberechnen löschte die Stundenwerte aller Mandanten (gemessen).
- **Vormerkungen jenseits der Frist bleiben.** Die der Aufbewahrung und die aus früheren Löschungen räumt niemand ab; solange niemand `sensor_hourly` jenseits der Rohwert-Frist neu berechnet, schaden sie nicht. Das Risiko eines solchen Neuberechnens von Hand besteht für alle Mandanten und ist Issue #3172 (Runbook-Warnung, Guard), nicht Teil von Sprint 5.
- **Löschen wird langsamer.** Das Löschen eines Sensors oder Mandanten wartet künftig auf das Neuberechnen von bis zu 90 Tagen Stundenwerten und bis zu zwei Jahren Tageswerten.
- Ein Archiv, das kurz vor dem Import exportiert wurde, verliert kaum Rohwerte; liegt der Export länger zurück, fallen die ältesten Rohwerte vor den Stichtag und werden nur gezählt.
- Große Messwert-Importe verlängern den Lauf; das Lebenszeichen muss während des Schreibens und des Neuberechnens gesetzt werden, sonst beendet der Stale-Sweep den Import nach sechs Stunden (`tenant_export_service.py:168`).
- Zwischen F-16 und F-34 fehlen einem importierten Garten die Stunden- und Tageswerte vor dem Stichtag; der Bericht sagt es.

## References

- Issue #3140 (Rest von #2138, MT-042), roadmap item R-19
- `project/requirements/tenant-export-import-remainder.md` (R3, R9, R14)
- Setzt F-15 voraus (Archivgröße, `/tmp`, Detailfeld), F-17 (Vorprüfung für acceptance-3) und F-33 (Importliste für acceptance-6); F-34 setzt dieses Feature voraus

## Betreiberentscheidungen 2026-11-27

- Es gibt nur **eine** Installation; Mandanten werden nicht zwischen Installationen verschoben. Die Datenschutz-Befunde zum Archiv laufen in einer eigenen Lane.
- Der Test mit einem Archiv von etwa 500 MiB läuft **nur manuell** (`workflow_dispatch`).
- Ein Speicherlimit des Workers von rund 2 GiB ist akzeptabel.
- Sprint 5 enthält nur R-19; Reihenfolge der Umsetzung F-15 → F-32 → F-17 → F-16 (F-16 zuletzt).

## Betreiberentscheidungen 2026-11-28

- **Messwerte ohne zuordenbaren Sensor: auslassen und zählen** (bestätigt). Das gilt auch für die Stunden- und Tageswerte eines solchen Sensors (acceptance-1).
- **Archivierte Stunden- und Tageswerte werden direkt geschrieben, nichts wird neu berechnet** (ersetzt die Entscheidung vom 2026-11-17 zu R13). Grund: Das Neuberechnen läuft über einen Zeitbereich, nicht je Mandant; reicht ein Archiv weiter zurück als die 90 Tage Rohwert-Aufbewahrung, würden Stunden- und Tageswerte anderer Mandanten aus nicht mehr vorhandenen Rohwerten neu gebildet, also gelöscht (acceptance-3, -7, -8).
- **Der Handlauf mit rund 500 MiB (F-15 acceptance-1) ist verpflichtend**; der Wertnachweis acceptance-7 ersetzt ihn nicht.

Dritte Runde am selben Tag:

- **A — F-16 wird geteilt** in „Rohwerte und Bericht“ (dieses Feature) und „Stunden- und Tageswerte“ (F-34); der Wertnachweis des Sprints liegt in F-34.
- **Vorgabe der Hauptsitzung nach der Messung gegen TimescaleDB:** Rohwerte älter als die Rohwert-Aufbewahrung der Zielinstallation werden nicht eingespielt, sondern gezählt (acceptance-2).

Vierte Runde am selben Tag:

- **D — Der Import lässt am Ende gezielt neu berechnen**, genau die eingespielten Zeiträume, erst Stunden-, dann Tageswerte (ersetzt „nichts neu berechnen“). Für die Rohwerte: acceptance-4 und -5.
- **E — Sprintwert:** „samt Sensor-Historie im Rahmen der Aufbewahrungsfristen“.
- Vorgabe der Hauptsitzung: Schichtung nach den Aufbewahrungsfristen der Zielinstallation, Schnitt an einer Tagesgrenze mit Abstand zur Frist (acceptance-2).

Fünfte Runde am selben Tag:

- **F — Die Löschlücke wird in diesem Feature mit behoben.** Jedes Löschen von Rohwerten (Sensor, Mandant, Rückrollen eines Imports, Aufräumen abgebrochener Importe durch den Sweep) berechnet seinen Zeitraum unmittelbar gezielt neu, erst Stunden-, dann Tageswerte, solange die Rohwerte der anderen Mandanten dort noch vorhanden sind. Eine Stelle im Datenzugriff, nicht je Aufrufer (acceptance-5, acceptance-9).

Sechste Runde am selben Tag (Vorgaben der Hauptsitzung nach ihrer fünften Messreihe):

- Jenseits des Rohwert-Stichtags wird `sensor_hourly` nie neu berechnet, weder vom Import noch von den Löschwegen; `sensor_daily` nur innerhalb der Stundenwert-Frist.
- Das Risiko eines Neuberechnens jenseits der Frist ist Issue #3172 und nicht Teil von Sprint 5; die Aufrufe aus F-16 bleiben innerhalb der Frist ihrer Ebene.

## Offene Betreiberentscheidungen (Re-run 2026-11-27)

Der Bericht nennt für F-16 keine blockierende Betreiberentscheidung. Eine Regel ist beim Hochstufen festzulegen:

- **Messwerte, deren `sensor_key` nicht im Archiv steht.** Heute verlangt der normale Schreibpfad einen eigenen Sensor (`observation_service.py:64-74`, `:95-106`); der Import schreibt Messwerte noch gar nicht.
  - **Überspringen und zählen:** Der Import läuft durch; der Bericht nennt die Zahl der ausgelassenen Zeilen.
  - **Ablehnen:** Ein Archiv mit einer unzuordenbaren Zeile scheitert ganz und wird zurückgerollt.
  - **Entschieden 2026-11-28: Überspringen und zählen**, auch für die Stunden- und Tageswerte eines nicht zuordenbaren Sensors (acceptance-1).

## Offene Punkte (Stand 2026-11-28)

Keine offene Betreiberentscheidung blockiert F-16.

- **Neuberechnen des Rohwert-Zeitraums in F-16 statt F-34** ist eine Festlegung der Planung, abweichend von der Vorgabe der Hauptsitzung aus der vierten Runde und in den Consistency notes begründet; mit der Entscheidung F liegt der Mechanismus ohnehin hier.
- **Quelle der Aufbewahrungsfrist.** Der Import liest die wirksame Aufbewahrungs-Policy der Zeitreihendatenbank; ob es zusätzlich eine Einstellung gibt, ist nicht belegt.
- **Wo die Prüfsumme scheitert** (in der Vorprüfung) ist eine Festlegung der Planung, keine Betreiberentscheidung.
