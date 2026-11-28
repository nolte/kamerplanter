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
      evidence: "'Buckets older than the raw retention (90 days) cannot be recomputed at all … a wider refresh would wipe other tenants' history' (:245-251); Rohwerte 90 Tage (migrations/003_retention_policies.sql:3). Ein Neuberechnen über das Rohwert-Fenster des Archivs träfe andere Mandanten. Betreiberentscheidung 2026-11-28: alle archivierten Buckets direkt schreiben, nichts neu berechnen (acceptance-3, -8)."
    - kind: drift
      target: src/backend/app/data_access/timescale/migrations/002_continuous_aggregates.sql:16
      resolution: revisit-after Integrationstest zu acceptance-3 (Policy-Lauf nach dem Import)
      evidence: "Policies: sensor_hourly start_offset 3 hours / end_offset 1 hour / stündlich (:16-19), sensor_daily 3 days / 1 day / täglich (:37-40). Was ein Policy-Lauf mit einem direkt geschriebenen Bucket in seinem Fenster tut, ist aus dem Repository nur teilweise belegt (Consistency notes)."
    - kind: prior-art
      target: src/backend/tests/integration/test_tenant_export_readings_timescale.py:49
      resolution: proceed
      evidence: "Die Fixture schreibt Messwerte unter SHARED_SENSOR ohne Sensor-Dokument (:49, :68-85); unter 'auslassen und zählen' würde jede Zeile übersprungen. Die Hooks zu acceptance-1, -7 und -8 verlangen eigene Sensoren im Seed."
    - kind: drift
      target: project/features/tenant-readings-import.md
      resolution: proceed
      evidence: "Offen war, ob eine falsche Prüfsumme des Messwert-Teils in der Vorprüfung (F-17) oder erst nach dem Start scheitert. Festgelegt: in der Hintergrundprüfung (acceptance-2); das Tabellenlayout prüft der Lauf (acceptance-11)."
    - kind: prior-art
      target: docs/de/deployment/tenant-export-import.md:136
      resolution: proceed
      evidence: "Ein Import neben dem Original scheitert an eigenen Arten (:136-137); der Wertnachweis braucht zwei ArangoDB-Datenbanken und Fotos ohne EXIF in der Quelle (_with_stored_bodies, tenant_export_service.py:1286-1312). Im Hook zu acceptance-7 benannt."
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
---

## Description

Ein Mandanten-Archiv enthält die Sensor-Historie schon heute: Rohwerte der
letzten 90 Tage sowie Stunden- (2 Jahre) und Tageswerte (5 Jahre). Beim Import
wird sie aber übersprungen; ein wiederhergestellter Garten startet ohne
Messverlauf.

Nach dieser Änderung stellt der Import die Rohwerte mit her und ordnet sie den
Sensoren des neuen Mandanten zu. Rohwerte, die älter sind als die
Aufbewahrungsfrist der Installation, spielt er nicht ein; der Importbericht
nennt ihre Zahl. Auf einer Installation ohne Zeitreihendatenbank gelingt der
Import weiterhin und meldet, dass die Messwerte übersprungen wurden. Schlägt
ein Import fehl, bleiben keine Messwerte zurück. Während die Messwerte
geschrieben werden, zeigt die Importliste das als eigene Phase.

Die Stunden- und Tageswerte stellt F-34 wieder her.

## Acceptance criteria

- [ ] **acceptance-1** Der Import stellt die Rohwerte des Archivs wieder her, zugeordnet zu den Sensoren des neuen Mandanten, vollständig auch bei mehr als 1 000 000 Messwert-Zeilen; für Messwerte gilt nur die Größengrenze des Archivs.
- [ ] **acceptance-2** Nicht eingespielt und im Importbericht je Grund gezählt werden Rohwerte eines Sensors, der nicht im Archiv steht, und Rohwerte, die älter sind als die Rohwert-Aufbewahrung der Zielinstallation (heute 90 Tage).
- [ ] **acceptance-3** Stimmt die Prüfsumme des Messwert-Teils nicht, scheitert schon die Hintergrundprüfung: Die Vorprüfung endet als fehlgeschlagen und lässt sich nicht starten.
- [ ] **acceptance-4** Ein Import, der nach dem Schreiben von Rohwerten fehlschlägt, hinterlässt keinen Rohwert des neuen Mandanten.
- [ ] **acceptance-5** Der Importbericht nennt die Zahl der importierten Rohwerte; ohne Zeitreihendatenbank gelingt der Import und der Bericht sagt ausdrücklich, dass die Messwerte übersprungen wurden.
- [ ] **acceptance-6** Während ein Import Messwerte schreibt, zeigt die Importliste die Phase „Messwerte“.
- [ ] **acceptance-7** REQ-056 §8.3, §8.4, AK-47 und ein neues Abnahmekriterium in §16.4 sowie das Runbook (DE + EN) beschreiben den Import der Rohwerte, die beiden Regeln für nicht eingespielte Rohwerte und das Verhalten ohne Zeitreihendatenbank.

## Test hooks

- **acceptance-1** — `src/backend/tests/integration/test_tenant_export_readings_timescale.py` (Timescale service of `.github/workflows/backend-guards.yml`): the seed gains sensor documents of the source tenant (today the readings hang on `SHARED_SENSOR` without one, `:49`, `:68-85`); raw rows arrive under the new sensor keys; an archive with more than `MAX_ROWS` reading rows (`tenant_export_engine.py:1012`) imports every row, streamed from the stored archive — pending
- **acceptance-2** — `src/backend/tests/integration/test_tenant_export_readings_timescale.py`: raw rows of a `sensor_key` that is not a sensor of the archive, and raw rows older than the target's raw retention, are not written and counted separately in the report; the retention is read from the target's effective retention policy (`data_access/timescale/migrations/003_retention_policies.sql:3` sets 90 days), a test with a changed policy proves it is not hard-coded — pending
- **acceptance-3** — `src/backend/tests/unit/domain/services/test_tenant_export_service.py`: a readings part with a wrong SHA-256 ends the background check `failed`/`IMPORT_CHECKSUM_MISMATCH` (today the part is skipped before the comparison, `tenant_export_engine.py:1220-1228`) and a start is refused — pending
- **acceptance-4** — `src/backend/tests/integration/test_tenant_export_readings_timescale.py`: induced failure after the raw rows were written → zero raw rows of the new tenant (rollback through `erase_abandoned_import`, `tenant_export_service.py:1354`) — pending
- **acceptance-5** — unit test with `readings=None` (the wiring without TimescaleDB, `src/backend/app/common/dependencies.py:1789`): the report says skipped for lack of a time-series database; integration test: the report carries the raw count — pending
- **acceptance-6** — service test (phase on the record while readings are written) + vitest of the import list from F-33 (phase label DE/EN) — pending
- **acceptance-7** — `mkdocs build --strict` + spec diff review — pending

## Consistency notes

Manual pass performed by: Claude (Subagent der Planungssitzung vom 2026-11-28, im Auftrag des Betreibers nolte) — betrifft den Abschnitt „Re-run 2026-11-28“; die älteren Läufe stammen vom `feature-consistency-reviewer`.

Geltend sind Beschreibung, Kriterien, Hooks und der jüngste Abschnitt dieser Notizen („Stand nach dem zweiten Agentenlauf“). Alle älteren Abschnitte sind Verlauf: Ihre Kriteriennummern, Feature-Zuschnitte und Aussagen geben den Stand ihres Laufs wieder.

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

## Risks

- **Vorgemerkte Bereiche.** Jeder importierte Rohwert merkt seinen Zeitbereich für das Neuberechnen vor (Messung 2026-11-28). Innerhalb der Aufbewahrungsfrist haben alle Mandanten ihre Rohwerte noch, ein Neuberechnen ist dort unschädlich. Was mit liegen gebliebenen Vormerkungen geschieht, wenn die Rohwerte später ablaufen, steht in F-34 (Risiken und offene Punkte).
- Ein Archiv, das kurz vor dem Import exportiert wurde, verliert keine Rohwerte; liegt der Export länger zurück, fallen die ältesten Rohwerte unter acceptance-2 und werden nur gezählt.
- Große Messwert-Importe verlängern den Lauf; das Lebenszeichen muss während des Schreibens gesetzt werden, sonst beendet der Stale-Sweep den Import nach sechs Stunden (`tenant_export_service.py:168`).
- Ohne konfiguriertes Löschinventar bleibt ein fehlgeschlagener Import `cleanup_pending`, bis der stündliche Sweep den halben Mandanten samt Messwerten entfernt hat (`tenant_export_service.py:1324-1362`); acceptance-4 gilt für den Normalfall mit Löschinventar.

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

## Offene Betreiberentscheidungen (Re-run 2026-11-27)

Der Bericht nennt für F-16 keine blockierende Betreiberentscheidung. Eine Regel ist beim Hochstufen festzulegen:

- **Messwerte, deren `sensor_key` nicht im Archiv steht.** Heute verlangt der normale Schreibpfad einen eigenen Sensor (`observation_service.py:64-74`, `:95-106`); der Import schreibt Messwerte noch gar nicht.
  - **Überspringen und zählen:** Der Import läuft durch; der Bericht nennt die Zahl der ausgelassenen Zeilen.
  - **Ablehnen:** Ein Archiv mit einer unzuordenbaren Zeile scheitert ganz und wird zurückgerollt.
  - **Entschieden 2026-11-28: Überspringen und zählen**, auch für die Stunden- und Tageswerte eines nicht zuordenbaren Sensors (acceptance-1).

## Offene Punkte (Stand 2026-11-28)

Keine offene Betreiberentscheidung blockiert F-16.

- **Quelle der Aufbewahrungsfrist.** Der Import liest die wirksame Aufbewahrungs-Policy der Zeitreihendatenbank; ob es zusätzlich eine Einstellung gibt, ist nicht belegt. Blockiert niemanden.
- **Wo die Prüfsumme scheitert** (in der Vorprüfung) ist eine Festlegung der Planung, keine Betreiberentscheidung.
