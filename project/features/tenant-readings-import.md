---
id: F-16
title: Sensor-Historie beim Import wiederherstellen
status: ready
roadmap_item: R-19
sprint: 5
created: 2026-11-17
ended: null
verifies_sprint_value: acceptance-7
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
---

## Description

Ein Mandanten-Archiv enthält die Sensor-Historie schon heute: Rohwerte der
letzten 90 Tage sowie Stunden- (2 Jahre) und Tageswerte (5 Jahre). Beim Import
wird sie aber übersprungen; ein wiederhergestellter Garten startet ohne
Messverlauf.

Nach dieser Änderung stellt der Import die Sensor-Historie mit her. Die
Rohwerte werden den Sensoren des neuen Mandanten zugeordnet, die älteren
Stunden- und Tageswerte erscheinen in den Diagrammen wie vor dem Export. Auf
einer Installation ohne Zeitreihendatenbank gelingt der Import weiterhin und
meldet, dass die Messwerte übersprungen wurden. Schlägt ein Import fehl,
bleiben keine Messwerte zurück. Während die Messwerte geschrieben werden,
zeigt die Importliste das als eigene Phase.

## Acceptance criteria

- [ ] **acceptance-1** Der Import stellt die Rohwerte ab dem frühesten Rohwert im Archiv wieder her, zugeordnet zu den Sensoren des neuen Mandanten; eine Zeile, deren Sensor nicht im Archiv steht, wird nicht geschrieben und im Importbericht gezählt.
- [ ] **acceptance-2** Stimmt die Prüfsumme des Messwert-Teils nicht oder passt das Tabellenlayout der Stunden- und Tageswerte nicht zu dem, was der Import erwartet (etwa nach einem TimescaleDB-Upgrade), endet der Import als fehlgeschlagen, bevor ein Messwert geschrieben ist.
- [ ] **acceptance-3** Stunden- und Tageswerte aller Zeiträume, die das Archiv enthält, liefern nach dem Import dieselben Werte wie vor dem Export — auch für die Stunde und den Tag, in die der früheste Rohwert fällt, und auch nachdem die Aggregate für das Rohwert-Fenster neu berechnet wurden.
- [ ] **acceptance-4** Ein Archiv mit mehr als 1 000 000 Messwert-Zeilen wird vollständig importiert; für Messwerte gilt nur die Größengrenze des Archivs.
- [ ] **acceptance-5** Ein Import, der nach dem Schreiben von Messwerten fehlschlägt, hinterlässt keinen Messwert und keinen Stunden- oder Tageswert des neuen Mandanten.
- [ ] **acceptance-6** Der Importbericht nennt die Zahl der importierten Rohwerte, Stunden- und Tageswerte; ohne Zeitreihendatenbank gelingt der Import und der Bericht sagt ausdrücklich, dass die Messwerte übersprungen wurden.
- [ ] **acceptance-7** Ein Garten mit Datensätzen, Fotos, Mitgliedern und Messwerten wird exportiert, das Archiv hochgeladen, vorgeprüft, die Mitglieder per E-Mail zugeordnet und aus der Vorprüfung importiert; ein erneuter Export des neuen Gartens enthält bis auf Schlüssel, Importzeitpunkt und Instanz-ID dieselben Daten einschließlich aller Messwerte (Zahlenwerte der Stunden- und Tageswerte mit einer relativen Abweichung von höchstens 1e-9).
- [ ] **acceptance-8** Rohwerte, Stunden- und Tageswerte eines importierten Sensors sind über die Messwert-Abfrage des neuen Mandanten abrufbar und für keinen anderen Mandanten sichtbar.
- [ ] **acceptance-9** Während ein Import Messwerte schreibt, zeigt die Importliste die Phase „Messwerte“.
- [ ] **acceptance-10** REQ-056 §8.3, §8.4, AK-47 und ein neues Abnahmekriterium in §16.4 sowie das Runbook (DE + EN) beschreiben den Messwert-Import, die Regel für nicht zuordenbare Zeilen und das Verhalten ohne Zeitreihendatenbank.

## Test hooks

- **acceptance-1** — `src/backend/tests/integration/test_tenant_export_readings_timescale.py` (Timescale service of `.github/workflows/backend-guards.yml`): raw rows arrive under the new sensor keys from the earliest raw timestamp; a row whose `sensor_key` is not a sensor of the archive is not written and counted in the report — pending
- **acceptance-2** — unit test in `src/backend/tests/unit/domain/services/test_tenant_export_service.py`: a readings part with a wrong SHA-256 ends `failed`/`IMPORT_CHECKSUM_MISMATCH` with no reading written; `src/backend/tests/integration/test_tenant_export_readings_timescale.py`: layout pin on `resolve_aggregate_tables()` and the written columns, and a missing or changed materialisation table ends the import `failed` and rolled back — pending
- **acceptance-3** — `src/backend/tests/integration/test_tenant_export_readings_timescale.py`: written hourly/daily buckets survive `refresh_continuous_aggregate` over the raw window; the edge buckets (the hour and the day containing the earliest raw value) equal the archived values — pending
- **acceptance-4** — `src/backend/tests/integration/test_tenant_export_readings_timescale.py`: an archive with more than `MAX_ROWS` reading rows (`tenant_export_engine.py:1012`) imports every row, streamed from the stored archive — pending
- **acceptance-5** — `src/backend/tests/integration/test_tenant_export_readings_timescale.py`: induced failure after the readings were written → zero raw rows and zero buckets of the new tenant (rollback through `erase_abandoned_import`) — pending
- **acceptance-6** — unit test with `readings=None` (the wiring without TimescaleDB, `src/backend/app/common/dependencies.py:1789`): the report says skipped for lack of a time-series database; integration test: the report carries the three counts — pending
- **acceptance-7** — `src/backend/tests/integration/test_tenant_export_readings_timescale.py`, extending `test_the_archive_carries_the_tenants_readings_and_an_import_lists_but_skips_them` (`:151`): export → upload → pre-check → e-mail mapping → start from the pre-check → re-export, empty difference including `timeseries/readings.csv` (sensor keys compared through the key mapping, aggregate floats within 1e-9 relative) — pending
- **acceptance-8** — `src/backend/tests/integration/test_tenant_export_readings_timescale.py`: `query_raw` / `query_hourly` / `query_daily` (`observation_repository.py:177-228`) return the imported series for the new tenant and nothing for a second tenant sharing the old sensor key — pending
- **acceptance-9** — service test (phase on the record while readings are written) + vitest of the import list (phase label DE/EN) — pending
- **acceptance-10** — `mkdocs build --strict` + spec diff review — pending

## Consistency notes

Manual pass performed by: Claude (Subagent der Planungssitzung vom 2026-11-28, im Auftrag des Betreibers nolte) — betrifft den Abschnitt „Re-run 2026-11-28“; die älteren Läufe stammen vom `feature-consistency-reviewer`.

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
- **Rand-Buckets (drift, proceed).** Established: `sensor_daily` wird aus `sensor_hourly` berechnet (`002_continuous_aggregates.sql:23-35`). Unestablished: wie sich ein `refresh_continuous_aggregate` über das Rohwert-Fenster auf die Stunde und den Tag auswirkt, in die der früheste Rohwert fällt, wenn für sie nur ein Teil der Rohwerte vorliegt; das zeigt erst der Integrationstest zu acceptance-3 (nicht durchgeführt). acceptance-3 legt das erwartete Ergebnis fest (Wert wie vor dem Export), nicht den Weg.
- **Bericht mit und ohne Zeitreihendatenbank (prior-art, proceed).** Established: Heute meldet der Import jeden Zeitreihen-Teil als `not_imported:<part>` mit der Zeilenzahl (`tenant_export_service.py:1240-1242`), ob eine Zeitreihendatenbank da ist oder nicht. acceptance-6 trennt „importiert (mit Zahlen)“ von „übersprungen, keine Zeitreihendatenbank“.
- **Überschneidung mit F-17 (overlap, proceed).** Begründung für `proceed`: Die Phase „Messwerte“ stand bis 2026-11-28 in F-17 Kriterium 5 und ist hierher verschoben, weil F-16 in der entschiedenen Reihenfolge nach F-17 kommt und erst F-16 Messwerte schreibt. acceptance-9 ergänzt die Phasenanzeige aus F-17 um einen Wert; acceptance-7 benutzt den Weg über die Vorprüfung, den F-17 liefert. Beides sind Abhängigkeiten in einer Richtung (F-16 nach F-17), kein doppelt umgesetzter Umfang.
- **Überschneidung mit F-15 (overlap, proceed).** Begründung für `proceed`: F-16 liest die Messwerte aus dem gespeicherten Archiv, begrenzt nur durch die Archivgrenze aus F-15, und meldet einen Fehler über das Detailfeld aus F-15 acceptance-6. F-16 ändert keine Größe und kein Feld, das F-15 definiert.

**Umgesetzte Edits aus dem Lauf vom 2026-11-27** (alle sieben): Prüfsumme des Messwert-Teils (acceptance-2); Regel für nicht zuordenbare `sensor_key` (acceptance-1); Kriterium 6 um AK-47 und Runbook erweitert (acceptance-10); Hooks auf `test_tenant_export_readings_timescale.py`, Kriterium 5 geteilt in Roundtrip (acceptance-7) und Layout (acceptance-2, als Verhalten des Imports statt als Aussage über einen Test); Abhängigkeit von F-15 eingetragen; Rollback-Notiz korrigiert (oben datiert vermerkt); Abschnitt „Betreiberentscheidungen 2026-11-27“ vorhanden. Zusätzlich: altes Kriterium 3 geteilt (acceptance-4, -5), Rand-Buckets in acceptance-3, Bericht in acceptance-6, Mandantentrennung der importierten Messwerte (acceptance-8), Phase „Messwerte“ aus F-17 übernommen (acceptance-9).

**Wertnachweis des Sprints.** `verifies_sprint_value: acceptance-7`. Das Kriterium läuft durch alle vier Features: Hintergrundprüfung und Größenpfad (F-15), Dokumentprüfung eines unveränderten Archivs (F-32), Vorprüfung mit E-Mail-Zuordnung und Start aus dem gespeicherten Archiv (F-17), Messwerte (F-16). Die Größe von rund 500 MiB weist es nicht nach; das bleibt nach Betreiberentscheidung der manuelle Lauf zu F-15 acceptance-1.

**Verhältnis der vier Features (R-19).** F-16 setzt F-15 und F-17 voraus und steht deshalb zuletzt. Die Reihenfolge F-15 → F-32 → F-17 → F-16 trägt.

**Ergebnis:** kein ungelöster Befund; F-16 ist `ready`. Die Regel „auslassen und zählen“ ist eine Planungsfestlegung, die der Betreiber vor dem Start von F-16 bestätigen oder ändern kann.

## Risks

- Das Schreiben in die Materialisierungstabellen der Aggregate stützt sich auf TimescaleDB-Interna; ein Upgrade kann es brechen. acceptance-2 macht daraus einen fehlgeschlagenen Import und einen roten Test statt stillen Datenverlusts.
- Ob die Stunde und der Tag, in die der früheste Rohwert fällt, nach dem Import den archivierten Wert behalten, ist ungeprüft; das Neuberechnen aus einem Teil der Rohwerte kann sie verändern. acceptance-3 verlangt den archivierten Wert; der Weg dorthin ist offen und der aufwendigste Teil des Features.
- Große Messwert-Importe verlängern den Lauf; das Lebenszeichen muss während des Schreibens gesetzt werden, sonst beendet der Stale-Sweep den Import nach sechs Stunden (`tenant_export_service.py:168`).
- Ohne konfiguriertes Löschinventar bleibt ein fehlgeschlagener Import `cleanup_pending`, bis der stündliche Sweep den halben Mandanten samt Messwerten entfernt hat (`tenant_export_service.py:1324-1362`); acceptance-5 gilt für den Normalfall mit Löschinventar.

## References

- Issue #3140 (Rest von #2138, MT-042), roadmap item R-19
- `project/requirements/tenant-export-import-remainder.md` (R3, R4, R9, R13, R14)
- Setzt F-15 voraus (Archivgröße, `/tmp`, Detailfeld) und F-17 (Importliste für acceptance-9, Vorprüfung für acceptance-7)

## Betreiberentscheidungen 2026-11-27

- Es gibt nur **eine** Installation; Mandanten werden nicht zwischen Installationen verschoben. Die Datenschutz-Befunde zum Archiv laufen in einer eigenen Lane.
- Der Test mit einem Archiv von etwa 500 MiB läuft **nur manuell** (`workflow_dispatch`).
- Ein Speicherlimit des Workers von rund 2 GiB ist akzeptabel.
- Sprint 5 enthält nur R-19; Reihenfolge der Umsetzung F-15 → F-32 → F-17 → F-16 (F-16 zuletzt).

## Offene Betreiberentscheidungen (Re-run 2026-11-27)

Der Bericht nennt für F-16 keine blockierende Betreiberentscheidung. Eine Regel ist beim Hochstufen festzulegen:

- **Messwerte, deren `sensor_key` nicht im Archiv steht.** Heute verlangt der normale Schreibpfad einen eigenen Sensor (`observation_service.py:64-74`, `:95-106`); der Import schreibt Messwerte noch gar nicht.
  - **Überspringen und zählen:** Der Import läuft durch; der Bericht nennt die Zahl der ausgelassenen Zeilen.
  - **Ablehnen:** Ein Archiv mit einer unzuordenbaren Zeile scheitert ganz und wird zurückgerollt.
  - **Stand 2026-11-28: vom Betreiber nicht entschieden.** Die Planung hat „Überspringen und zählen“ festgelegt (acceptance-1); siehe „Offene Punkte“.

## Offene Punkte (Stand 2026-11-28)

Keine offene Betreiberentscheidung blockiert F-16.

- **Regel für Messwerte ohne zuordenbaren Sensor — Bestätigung erbeten.** Die Planung hat „auslassen und zählen“ festgelegt (acceptance-1), hergeleitet aus der bestehenden Importregel für nicht auflösbare Verweise. Der Betreiber hat dazu nicht entschieden. Wählt er „ablehnen“, ändert sich acceptance-1 (das Archiv scheitert ganz und wird zurückgerollt), und der Konsistenzlauf ist zu wiederholen. Kein Blocker: Ohne Rückmeldung gilt die Festlegung. F-16 wird zuletzt umgesetzt, für einen Widerspruch bleibt bis dahin Zeit.
