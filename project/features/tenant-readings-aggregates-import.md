---
id: F-34
title: Stunden- und Tageswerte der Sensor-Historie beim Import wiederherstellen
status: ready
roadmap_item: R-19
sprint: 5
created: 2026-11-28
ended: null
verifies_sprint_value: acceptance-6
consistency_check:
  performed_at: 2026-11-28
  agent_version: feature-consistency-reviewer@unknown
  findings:
    - kind: prior-art
      target: src/backend/app/data_access/timescale/observation_repository.py:132
      resolution: proceed
      evidence: "resolve_aggregate_tables (:132-144, AGGREGATE_VIEWS :119) löst die Materialisierungstabellen auf und wirft, wenn eine fehlt; _purge_aggregates (:242-276) löscht dort bereits gezielt je Mandant. Der Import schreibt in dieselben Tabellen."
    - kind: drift
      target: src/backend/app/data_access/timescale/observation_repository.py:245
      resolution: proceed
      evidence: "'Buckets older than the raw retention (90 days) cannot be recomputed at all … a wider refresh would wipe other tenants' history' (:245-251). Messung der Hauptsitzung gegen TimescaleDB 2.32.1-pg16 (2026-11-28) bestätigt es. Damals entschieden: direkt schreiben, nichts neu berechnen. Seit den Entscheidungen D und F: direkt schreiben, davor und danach gezielt neu berechnen (acceptance-1, -3, -4)."
    - kind: drift
      target: src/backend/app/data_access/timescale/observation_repository.py:121
      resolution: proceed
      evidence: "Kommentar: 'A continuous aggregate is a read-only view: DELETE FROM sensor_hourly is refused' (:121-123); gemessen wurde, dass ein INSERT über die Sicht angenommen wird. Der Import schreibt gezielt in die über resolve_aggregate_tables ermittelten Tabellen (Consistency notes)."
    - kind: drift
      target: spec/req/REQ-056_Mandanten-Lebenszyklus-Kontingente.md:683
      resolution: proceed
      evidence: "AK-47 und §8.3 (:365) schließen den Import von Messwerten aus; Runbook DE :8, :26, :146. acceptance-7 zieht nach."
    - kind: prior-art
      target: src/backend/tests/integration/test_tenant_export_readings_timescale.py:151
      resolution: proceed
      evidence: "Das Modul läuft in CI gegen TimescaleDB und zwei ArangoDB-Datenbanken (SOURCE_DB, TARGET_DB, :50-51); die Fixture frischt vor den Tests auf (:86-87), schaltet die Jobs ab (:64-67) und hat keine Sensor-Dokumente (:49, :68-85)."
    - kind: overlap
      target: F-16
      resolution: proceed
      evidence: "Abgespalten aus F-16 (Betreiberentscheidung A, 2026-11-28). F-16 liest den Messwert-Teil, ordnet Sensoren zu und schreibt Rohwerte; F-34 schreibt die Stunden- und Tageswerte und trägt den Rundlauf. Begründung in den Consistency notes."
    - kind: overlap
      target: F-17
      resolution: proceed
      evidence: "acceptance-6 läuft über Vorprüfung, Zuordnung und Start aus F-17. Begründung in den Consistency notes."
    - kind: drift
      target: project/features/tenant-readings-aggregates-import.md
      resolution: proceed
      evidence: "Dritter Agentenlauf (2026-11-28): nicht ready bis Messung und Entscheidung. Beides liegt vor: Messungen der Hauptsitzung zu Stunden → Tage, begrenztem Neuberechnen und frischer Installation; Betreiberentscheidung D (gezielt neu berechnen). Kriterien neu gefasst."
    - kind: drift
      target: src/backend/app/data_access/timescale/migrations/003_retention_policies.sql:6
      resolution: proceed
      evidence: "Stundenwerte 2 Jahre (:6), Tageswerte 5 Jahre (:9). Vorgabe der Hauptsitzung: Was älter ist als die Frist seiner Ebene, wird gezählt, nicht eingespielt; Schnitt an einer Tagesgrenze mit Abstand (acceptance-2)."
    - kind: drift
      target: src/backend/app/data_access/timescale/observation_repository.py:278
      resolution: proceed
      evidence: "Dritter Lauf: Die Risikonotiz 'besteht in dieser Form schon heute' war falsch. Ohne Vormerkung lässt ein Neuberechnen Buckets unberührt; Vormerkungen entstehen heute durch das Löschen von Rohwerten (delete_by_sensor :278, delete_by_tenant :300), auch durch den Rollback eines gescheiterten Imports. Korrigiert; Rollback in acceptance-3."
    - kind: drift
      target: src/backend/app/data_access/timescale/migrations/002_continuous_aggregates.sql:3
      resolution: proceed
      evidence: "Dritter Lauf: Die Sichtbarkeit direkt geschriebener Buckets gilt nur bei materialized_only = true (gemessen; die Migration setzt es nicht ausdrücklich, :3, :24). In acceptance-5 aufgenommen."
    - kind: drift
      target: project/features/tenant-readings-aggregates-import.md
      resolution: proceed
      evidence: "Gemessen: Auf einer nie voll aufgefrischten Datenbank löscht refresh(NULL, NULL) direkt geschriebene Buckets. Nicht gemessen: ob Policy-Läufe allein das auslösen (run_job gelang im Versuch nicht). acceptance-4 legt das Ergebnis fest, der Hook ist das Experiment."
    - kind: drift
      target: project/features/tenant-readings-aggregates-import.md
      resolution: proceed
      evidence: "Vierter Agentenlauf (2026-11-28): nicht ready bis zu einer Messung. Sie liegt vor (Abschnitte I bis VI der Hauptsitzung): Zeiträume vor dem ersten Neuberechnen einer Installation gelten als nie materialisiert, ein volles Neuberechnen löscht dort direkt geschriebene Werte; nach einem Neuberechnen mit vorhandenem Rohwert überleben danach direkt geschriebene Werte. Mittel für acceptance-4 festgelegt: vorab genau die Zeiträume neu berechnen, die der Import beschreibt."
    - kind: drift
      target: project/features/tenant-readings-aggregates-import.md
      resolution: proceed
      evidence: "Vierter Agentenlauf: acceptance-1 nennt jetzt die Stichtage statt 'außerhalb der neu berechneten Zeiträume'; acceptance-3 sagt für andere Mandanten zu, was gilt (kein Wert geht verloren, Werte entsprechen ihren Quelldaten); acceptance-6 gilt für eine vollständig neu berechnete Quelle; überholte Nummern und 'Manual pass' bereinigt."
    - kind: drift
      target: src/backend/app/data_access/timescale/observation_repository.py:259
      resolution: proceed
      evidence: "Altlasten: Vormerkungen aus Löschungen vor F-16 bleiben liegen (':259-262' beschreibt sie als harmlos). Das Vorab-Neuberechnen dieses Features würde in einem solchen Bereich die Buckets anderer Mandanten löschen, deren Rohwerte abgelaufen sind (Messung 300-Tage-Bucket). Im Repository liest nichts den Vormerk-Katalog von TimescaleDB (Suche nach 'invalidation', 'watermark', '_timescaledb_catalog' in src/backend, scripts, helm: nur dieser Kommentar)."

    - kind: drift
      target: project/features/tenant-readings-aggregates-import.md
      resolution: proceed
      evidence: "Nachtrag der Hauptsitzung (2026-11-28) nach ihrer Katalog-Messung: Offene Vormerkungen sind lesbar (_timescaledb_catalog.continuous_aggs_hypertable_invalidation_log, …materialization_invalidation_log, …invalidation_threshold). Die Altlasten-Erkennung ist Kriterium (acceptance-8), die Katalogtabellen gehören zur Layout-Prüfung (acceptance-5). Semantik einzelner Einträge offen."
    - kind: drift
      target: src/backend/app/data_access/timescale/migrations/003_retention_policies.sql:3
      resolution: proceed
      evidence: "Fünfter Agentenlauf und fünfte Messreihe der Hauptsitzung (2026-11-28): Die Rohwert-Aufbewahrung hinterlässt selbst Vormerkungen (R2); ein Neuberechnen von sensor_hourly jenseits der Rohwert-Frist löscht die Stundenwerte aller Mandanten (R3); nur sensor_daily über einen Zeitraum mit den Stundenwerten aller ist unschädlich (R4). Das Vorab-Neuberechnen und acceptance-8 (Abbruch bei alter Vormerkung) sind gestrichen: Es bräche jeden Import in einer Installation ab, die älter ist als 90 Tage. Die beiden revisit-after-Befunde darüber sind damit erledigt (Policy-Läufe: gemessen III; Katalog-Einträge: erklärt durch R2/R3). acceptance-3 und -4 neu gefasst; das bestehende Risiko ist Issue #3172."
---

## Description

Nach F-16 stellt der Import die Rohwerte der Sensoren wieder her und zeigt für
diesen Zeitraum auch Stunden- und Tageswerte. Die älteren Stundenwerte (bis
zwei Jahre) und Tageswerte (bis fünf Jahre) aus dem Archiv fehlen noch; die
Diagramme eines wiederhergestellten Gartens zeigen deshalb nur die letzten
Wochen.

Nach dieser Änderung stellt der Import auch die älteren Stunden- und
Tageswerte wieder her, soweit die Aufbewahrungsfristen der Installation
reichen; was älter ist, nennt der Importbericht mit Zahl. Die Diagramme zeigen
den Verlauf wie vor dem Export. Die Messwerte anderer Gärten gehen dabei nicht
verloren, und die wiederhergestellten Werte sind so dauerhaft wie die eigene
Historie der Installation. Damit ist ein Garten aus seinem Archiv im Rahmen
der Aufbewahrungsfristen vollständig wiederherstellbar.

## Acceptance criteria

- [ ] **acceptance-1** Nach dem Ende des Imports liefert die Messwert-Abfrage des neuen Mandanten jeden Stunden- und Tageswert des Archivs innerhalb der Aufbewahrungsfristen der Zielinstallation genau einmal: Stundenwerte vor dem Rohwert-Stichtag und Tageswerte zwischen dem Tageswert- und dem Stundenwert-Stichtag genau wie im Archiv; Stundenwerte ab dem Rohwert-Stichtag und Tageswerte ab dem Stundenwert-Stichtag gebildet aus den eingespielten Quelldaten, gleich dem Archiv bis auf eine relative Abweichung von 1e-9.
- [ ] **acceptance-2** Nicht eingespielt und im Importbericht je Grund gezählt werden Stunden- und Tageswerte eines Sensors, der nicht im Archiv steht, Stundenwerte vor dem Stundenwert-Stichtag und Tageswerte vor dem Tageswert-Stichtag; jeder Stichtag ist ein Tagesbeginn in UTC, mindestens einen Tag innerhalb der jeweiligen Aufbewahrung der Zielinstallation (heute 2 Jahre für Stunden-, 5 Jahre für Tageswerte).
- [ ] **acceptance-3** Durch den Import geht kein Wert eines anderen Mandanten verloren: Seine Rohwerte, seine Stundenwerte vor dem Rohwert-Stichtag und seine Tageswerte vor dem Stundenwert-Stichtag sind unverändert, seine Tageswerte im eingespielten Stundenwert-Zeitraum entsprechen seinen eigenen Stundenwerten (unverändert bis auf 1e-9, wenn sie das vorher schon taten) — auch bei einem Mandanten, dessen ältere Werte nur noch als Stunden- und Tageswerte bestehen, weil die Aufbewahrung seine Rohwerte entfernt hat. Dasselbe gilt nach einem gescheiterten und zurückgerollten Import, der zudem keinen Stunden- oder Tageswert des neuen Mandanten hinterlässt.
- [ ] **acceptance-4** Die eingespielten Stunden- und Tageswerte vor dem Rohwert-Stichtag sind so dauerhaft wie die eigene Historie der Installation: Sie behalten ihre Werte, nachdem die Aggregat-Policies gelaufen sind, auch in einer Installation, deren Aggregate nie über den ganzen Zeitraum neu berechnet wurden; der Import berechnet Stundenwerte nie vor dem Rohwert-Stichtag und Tageswerte nie vor dem Stundenwert-Stichtag neu.
- [ ] **acceptance-5** Passt das Tabellenlayout der Stunden- und Tageswerte nicht zu dem, was der Import erwartet, oder lesen die Aggregate nicht ausschließlich materialisierte Werte (`materialized_only`), endet der Import als fehlgeschlagen, bevor ein Messwert geschrieben ist, und der Garten wird zurückgerollt.
- [ ] **acceptance-6** Ein Garten mit Datensätzen, Fotos, Mitgliedern, Sensoren und Messwerten, dessen Stunden- und Tageswerte vollständig berechnet sind, wird exportiert, das Archiv hochgeladen, vorgeprüft, die Mitglieder per E-Mail zugeordnet und aus der Vorprüfung importiert; ein erneuter Export des neuen Gartens enthält bis auf Schlüssel, Importzeitpunkt und Instanz-ID dieselben Daten einschließlich der Sensor-Historie im Rahmen der Aufbewahrungsfristen (Rohwerte ab dem Stichtag genau, Stunden- und Tageswerte mit einer relativen Abweichung von höchstens 1e-9).
- [ ] **acceptance-7** REQ-056 §8.3, §8.4, AK-47 und ein neues Abnahmekriterium in §16.4 sowie das Runbook (DE + EN) beschreiben den Import der Stunden- und Tageswerte, die Schichtung nach Aufbewahrungsfristen, welche Zeiträume der Import neu berechnen lässt und welche nie, und dass ältere Stunden- und Tageswerte aller Gärten ein Neuberechnen jenseits der Rohwert-Aufbewahrung nicht überstehen (Verweis auf Issue #3172).

## Test hooks

- **acceptance-1** — `src/backend/tests/integration/test_tenant_export_readings_timescale.py` (Timescale service of `.github/workflows/backend-guards.yml`): the seed has sensor documents and a fully refreshed source; after the import `query_hourly` / `query_daily` (`observation_repository.py:196-228`) return every archived bucket inside the retentions exactly once (no bucket twice: F-16 builds the hourly buckets of the raw period from raw rows, F-34 writes no archived hourly bucket there, and no archived daily bucket from the hourly cut-off on); by construction of the seed the test checks the four layers: hourly before the raw cut-off and daily between the daily and the hourly cut-off equal the archive exactly (`avg_value`, `min_value`, `max_value`, `sample_count`); hourly from the raw cut-off on and daily from the hourly cut-off on equal the archive within 1e-9 relative; order of work pinned: write the archived hourly and daily rows directly, then refresh `sensor_daily` over the imported hourly period (between the hourly and the raw cut-off; the raw period is F-16's) — and nothing else — pending
- **acceptance-2** — same module: buckets of an unknown `sensor_key`, hourly buckets before the hourly cut-off and daily buckets before the daily cut-off are not written and counted per reason in the report; both retentions are read from the target's effective policies (`data_access/timescale/migrations/003_retention_policies.sql:6`, `:9`; a test with changed policies proves they are not hard-coded); each cut-off is the start of a UTC day at least one day inside the retention — pending
- **acceptance-3** — same module: a second tenant built by the measured course R1–R2 (raw rows 200 days ago, the windows over them refreshed as the policies do, then `drop_chunks('sensor_readings', older_than => interval '90 days')`, so its old hourly and daily values stand without raw rows and the retention's pending mark is present), plus raw rows, hourly and daily values inside the raw period; snapshots of the raw table and both materialisation tables for every tenant before and after the import: no row of the second tenant is missing, its raw rows and its hourly rows before the raw cut-off are identical, its daily rows inside the imported hourly period equal what its hourly rows yield (within 1e-9 of their state before), its other daily rows are identical. Second scenario: induced failure after the buckets were written → zero buckets of the new tenant (rollback through `erase_abandoned_import` → `_purge_aggregates`, `observation_repository.py:242-276`, with the bounded recompute of F-16 acceptance-9) and the same holds. Control (measured R3): a refresh of `sensor_hourly` over the second tenant's old day deletes its hourly value, which is why the import never issues one — pending
- **acceptance-4** — same module, second fixture reproducing the measured course I–III: raw rows of a third tenant in the last hours and days, only the two policy windows refreshed (3 h … 1 h hourly, 3 d … 1 d daily, `002_continuous_aggregates.sql:16-19`, `:37-40`), never a full refresh; the second tenant of acceptance-3; then the import of an archive reaching back 900 days; then the policy windows again: every imported bucket keeps its value and no value of the second or third tenant changes. A spy on the refresh calls pins that the import refreshes `sensor_hourly` nowhere before the raw cut-off and `sensor_daily` nowhere before the hourly cut-off, every range inside the retention of its level, so the guard of #3172 would admit each call. Variants that settle what is not measured: a target with no raw row at all, and a completely empty time-series database — pending
- **acceptance-5** — same module: layout pin on `resolve_aggregate_tables()` (`observation_repository.py:132-144`) and the written columns (`bucket, tenant_key, sensor_key, sensor_type, avg_value, min_value, max_value, sample_count`); a missing or changed materialisation table, and an aggregate altered to `materialized_only = false`, each end the import `failed` with no reading written and the tenant rolled back — pending
- **acceptance-6** — same module, extending `test_the_archive_carries_the_tenants_readings_and_an_import_lists_but_skips_them` (`:151`): export → upload → pre-check → e-mail mapping → start from the pre-check → re-export, empty difference including `timeseries/readings.csv` (sensor keys compared through the key mapping; raw rows of the seed lie after the cut-off; aggregate numbers within 1e-9 relative). The source is fully refreshed before the export while all its raw rows still exist, because in operation the newest hour and day are not materialised yet and would show as a difference. Needs two ArangoDB databases, as the module provisions (`SOURCE_DB`, `TARGET_DB`, `:50-51`), because an import next to the original fails on own species (runbook `docs/de/deployment/tenant-export-import.md:136-137`); the source photos carry no EXIF block, because the import stores stripped bodies (`_with_stored_bodies`, `tenant_export_service.py:1286-1312`) — pending
- **acceptance-7** — `mkdocs build --strict` + spec diff review — pending

## Consistency notes

Das Feature ist am 2026-11-28 aus F-16 abgespalten (Betreiberentscheidung A). Der erste Durchgang beim Anlegen war manuell (Subagent der Planungssitzung, weil ein Subagent den Agenten nicht starten darf); seither hat der `feature-consistency-reviewer` (`feature-consistency-reviewer@unknown`) das Feature im dritten, vierten und fünften Lauf der Hauptsitzung geprüft. Die Befunde aller Durchgänge stehen im Frontmatter. Dieser Abschnitt gibt den geltenden Stand nach dem fünften Lauf wieder; frühere Fassungen dieser Notizen stehen in der Git-Historie des Zweigs (`b3c7f6eba`, `9c779f351`, `78a692c2c`, `7be252bbe`). Die zitierten Code-Stellen wurden nachgelesen; ein eigener Test lief nicht, alle Messungen stammen von der Hauptsitzung.

**Messungen der Hauptsitzung gegen TimescaleDB 2.32.1-pg16** (dasselbe Image wie `docker-compose.yml:99`), 2026-11-28; Befehle sinngemäß, Ergebnisse wie übermittelt.

*Erste Reihe:*

- Abfrage von `timescaledb_information.continuous_aggregates`: Die Aggregate sind `materialized_only = true`; Materialisierungstabellen `_timescaledb_internal._materialized_hypertable_2` (hourly) und `_3` (daily); Spalten hourly: `bucket, tenant_key, sensor_key, sensor_type, avg_value, min_value, max_value, sample_count`.
- Ein direktes `INSERT` in die Materialisierungstabelle wird angenommen und ist sofort über die Sicht `sensor_hourly` sichtbar; auch ein `INSERT` über die Sicht selbst wurde angenommen.
- Ein `refresh_continuous_aggregate` ohne vorgemerkte Änderung lässt direkt geschriebene Buckets unverändert („already up-to-date“).
- Schreibt jemand Rohwerte in den Zeitraum eines Buckets, merkt TimescaleDB den Bereich vor; das nächste Neuberechnen darüber bildet die Buckets aller Mandanten in diesem Bereich aus den Rohwerten neu. Gemessen: Mandant A bekam 2 Rohwerte in eine Stunde, in der A (6 Stichproben) und B (3 Stichproben, keine Rohwerte) direkt geschriebene Buckets hatten; danach A = Mittel der 2 Rohwerte (`sample_count` 2), B gelöscht. Ebenso für einen 300 Tage alten Bucket nach einem Rohwert-Insert und `refresh(NULL, NULL)`.
- Die Policies decken nur 3 h bis 1 h (stündlich) und 3 d bis 1 d (täglich) ab; vorgemerkte Bereiche außerhalb bleiben liegen, bis jemand breiter neu berechnet.

*Zweite Reihe:*

- **Ebene Stunden → Tage.** Auf einer einmal voll neu berechneten Datenbank wurde für einen 900 Tage alten Tag ein Stundenwert von Mandant A direkt eingefügt, dazu direkte Tageswerte für A (avg 22, 40 Stichproben) und B (avg 11, 30 Stichproben; B ohne Stundenwerte). Nach `refresh_continuous_aggregate('sensor_daily', NULL, NULL)`: A = avg 20, 4 Stichproben, B gelöscht. Das direkte Einfügen eines Stundenwerts merkt den Tag für die Tageswerte aller Mandanten vor.
- **Begrenztes Neuberechnen.** Direkte Buckets für A und B (300 und 20 Tage alt); Rohwerte für A und B in die 20-Tage-Stunde eingefügt, dann `refresh_continuous_aggregate('sensor_hourly', <diese Stunde>, <+1 h>)` → A = 50/2, B = 12/3 (beide aus ihren Rohwerten), die 300 Tage alten Buckets beider unverändert.

*Dritte Reihe (Installation, die nur Policy-Läufe gesehen hat):*

- **I.** Rohwerte von Mandant C in den letzten Stunden und Tagen; die beiden Policy-Fenster von Hand neu berechnet (Wirkung wie die Jobs): Wassermarke = heute.
- **II./III.** Danach direkt geschrieben: ein 300 Tage alter Stundenwert und ein 900 Tage alter Tageswert von Mandant A. Erneute Policy-Fenster: „already up-to-date“, beide Werte bleiben.
- **IV.** Danach `refresh_continuous_aggregate(…, NULL, NULL)` beider Aggregate: beide Werte gelöscht. Zeiträume vor dem ersten Neuberechnen einer Installation gelten als nie materialisiert; ein volles Neuberechnen bildet sie aus Rohwerten neu, und ohne Rohwerte verschwinden direkt geschriebene Werte. Das betrifft jede reale Installation (das Backend berechnet nie voll neu, nur die Policies laufen) für Archive, die weiter zurückreichen, als die Installation alt ist.
- **VI.** Eigene Datenbank: Ein volles Neuberechnen auf leeren Tabellen bewegt die Wassermarke nicht. Mit einem Rohwert vorhanden setzt ein volles Neuberechnen die Wassermarke auf jetzt; ein danach direkt geschriebener 300 Tage alter Stundenwert überlebt ein weiteres volles Neuberechnen („already up-to-date“).

*Vierte Reihe (Katalog):*

- Offene Vormerkungen stehen in `_timescaledb_catalog.continuous_aggs_hypertable_invalidation_log` (Rohwert-Ebene, noch nicht verteilte Bereiche; Spalten `lowest_modified_value` / `greatest_modified_value` in Mikrosekunden seit Epoch) und in `_timescaledb_catalog.continuous_aggs_materialization_invalidation_log` (je Aggregat über `materialization_id`, gleiche Spalten); dazu `_timescaledb_catalog.continuous_aggs_invalidation_threshold`.
- Ablauf: Rohwerte von B vor 200 Tagen und jetzt, volles Neuberechnen, dann `DELETE` der alten Rohwerte von B (wie eine Sensorlöschung). Direkt danach steht der Bereich im Hypertable-Log; nach einem beliebigen Neuberechnen wandert er ins Materialisierungs-Log des Stundenaggregats und bleibt dort offen. Das Tagesaggregat, nie voll neu berechnet, steht dort als ein offener Bereich von −∞ bis +∞.

*Fünfte Reihe (Aufbewahrung der Rohwerte):*

- **R1.** Mandant B: Rohwerte vor 200 Tagen; die Fenster darüber wurden damals neu berechnet (wie die Policies es tun): B hat einen Stunden- und einen Tageswert.
- **R2.** Die Rohwert-Aufbewahrung entfernt den Chunk (`drop_chunks('sensor_readings', older_than => interval '90 days')`, das, was `add_retention_policy` aus `003_retention_policies.sql:3` ausführt). Danach steht der Chunk-Bereich als offene Vormerkung im Hypertable-Log und wandert beim nächsten Neuberechnen ins Materialisierungs-Log des Stundenaggregats. Die Werte von B stehen noch.
- **R3.** Ein Neuberechnen von `sensor_hourly` über diesen Tag, begrenzt auf den einen Tag oder `(NULL, NULL)`, löscht B's Stundenwert. Damit ist der zuvor unverstandene Eintrag im Stunden-Log erklärt: Es sind die Vormerkungen der Aufbewahrung.
- **R4.** Gegenprobe des sicheren Wegs: Derselbe alte Tag; Mandant A schreibt einen Stundenwert direkt hinein; nur `sensor_daily` wird über diesen Tag neu berechnet, `sensor_hourly` dort nicht. Ergebnis: Stundenwerte von A (30/6) und B (8/2) bleiben; Tageswerte A = 30/6 (aus seinem Stundenwert), B = 8/2 (aus seinem Stundenwert), beide richtig. Anschließende Policy-Fenster ändern nichts (2 Stunden-, 2 Tageswerte).

**Was daraus folgt (Vorgaben der Hauptsitzung nach der fünften Reihe; sie ersetzen die Vorgaben der fünften Runde).**

1. **Jenseits des Rohwert-Stichtags wird `sensor_hourly` nie neu berechnet**, weder vor noch nach dem Schreiben, weder vom Import noch von den Löschwegen aus F-16. In jeder Installation, die älter ist als 90 Tage, liegen dort die Vormerkungen der Aufbewahrung (R2); jedes Neuberechnen löscht die Stundenwerte aller Mandanten (R3).
2. **Gestrichen: das Vorab-Neuberechnen** der Zielzeiträume (Vorgabe der fünften Runde) und **das frühere acceptance-8** (Abbruch bei einer alten Vormerkung, Stand `7be252bbe`). Das Vorab-Neuberechnen wäre genau das Neuberechnen aus R3. Der Abbruch bräche jeden Import in einer Installation ab, die älter ist als 90 Tage, weil dort immer Vormerkungen der Aufbewahrung liegen. Die Katalogtabellen liest der Import nicht mehr; acceptance-5 prüft wieder nur das Layout der Aggregate und `materialized_only`.
3. **`sensor_daily` wird über den eingespielten Stundenwert-Zeitraum neu berechnet**, nicht weiter zurück als die Stundenwert-Frist (sonst dasselbe Problem eine Ebene höher: Die Aufbewahrung der Stundenwerte, `003_retention_policies.sql:6`, hinterlässt dort ihre Vormerkungen). Gemessen unschädlich, solange die Stundenwerte der anderen dort stehen (R4).
4. **Schichtung nach Aufbewahrungsfristen.** Established: Rohwerte 90 Tage, Stundenwerte 2 Jahre, Tageswerte 5 Jahre (`data_access/timescale/migrations/003_retention_policies.sql:3`, `:6`, `:9`). Was älter ist als die Frist seiner Ebene, wird gezählt, nicht eingespielt; die Fristen liest der Import aus den wirksamen Policies; jeder Stichtag ist ein Tagesbeginn in UTC mit Abstand zur Frist (acceptance-2; für Rohwerte F-16 acceptance-2).
5. **Ablauf des Imports.** Rohwerte schreiben und ihren Zeitraum neu berechnen lassen (F-16: `sensor_hourly`, dann `sensor_daily`, nur ab dem Rohwert-Stichtag). Dann die archivierten Stundenwerte vor dem Rohwert-Stichtag und die archivierten Tageswerte vor dem Stundenwert-Stichtag direkt schreiben, in die über `resolve_aggregate_tables` ermittelten Tabellen (`observation_repository.py:132-144`). Dann `sensor_daily` über den Zeitraum zwischen Stundenwert- und Rohwert-Stichtag neu berechnen lassen. Sonst nichts.
6. **Woher ein Wert nach dem Import stammt** (acceptance-1):

| Zeitraum | Stundenwerte | Tageswerte |
|---|---|---|
| ab dem Rohwert-Stichtag | aus den eingespielten Rohwerten (bis 1e-9; F-16) | aus den Stundenwerten (bis 1e-9; F-16) |
| davor, ab dem Stundenwert-Stichtag | direkt aus dem Archiv (genau), nie neu berechnet | aus den eingespielten Stundenwerten (bis 1e-9) |
| davor, ab dem Tageswert-Stichtag | nicht eingespielt, gezählt | direkt aus dem Archiv (genau), nie neu berechnet |
| älter | nicht eingespielt, gezählt | nicht eingespielt, gezählt |

7. **Die nie voll neu berechnete Installation ist kein Sonderfall mehr.** Der Import berechnet dort ebenfalls nichts jenseits der Rohwert-Frist; die eingespielten Werte überstehen die Policy-Läufe (gemessen, III). Ein volles Neuberechnen löschte sie (IV) wie in einer älteren Installation die Historie aller Mandanten (R3); der Import löst keines aus.
8. **Bestehendes Risiko, Issue #3172.** Dass ein Neuberechnen jenseits der Rohwert-Frist die ältere Historie aller Mandanten löscht, gilt unabhängig vom Import. #3172 trägt die Runbook-Warnung und einen Guard im Anwendungscode; es ist nicht Teil von Sprint 5. Die Neuberechnungs-Aufrufe aus F-16 und F-34 liegen immer innerhalb der Frist ihrer Ebene, sodass der Guard sie zuließe (Hook zu acceptance-4).

**Was belegt ist und was nicht.**

- *Gemessen:* Sichtbarkeit direkt geschriebener Werte bei `materialized_only = true`; Vormerkung durch Rohwerte, durch direkt eingefügte Stundenwerte und durch die Aufbewahrung; Verlust der Stundenwerte aller Mandanten bei einem Neuberechnen von `sensor_hourly` jenseits der Rohwert-Frist; Unschädlichkeit eines Neuberechnens nur von `sensor_daily` über einen Tag, an dem die Stundenwerte aller stehen; Überleben direkt geschriebener Werte über Policy-Läufe in einer nie voll neu berechneten Installation.
- *Hergeleitet, nicht gemessen* (Unestablished; durch die genannten Hooks zu klären): dass das Neuberechnen von `sensor_daily` über einen langen Zeitraum (bis zwei Jahre) sich verhält wie das gemessene über einen Tag (Hook acceptance-3); das Verhalten in einer Zielinstallation ohne Rohwerte oder mit leerer Zeitreihendatenbank, wo nach Messung VI die Wassermarke nicht bewegt wird (Varianten im Hook zu acceptance-4); dass das direkte Löschen von Stundenwerten beim Rollback den Tag für die Tageswerte vormerkt wie das direkte Einfügen (F-16 acceptance-9).
- Im Repository liest nichts den Vormerk-Katalog von TimescaleDB (Suche nach `invalidation`, `watermark` und `_timescaledb_catalog` in `src/backend`, `scripts` und `helm`: Treffer nur im Kommentar `observation_repository.py:259-262`); nach der Streichung des früheren acceptance-8 braucht dieses Feature ihn auch nicht.

**Befunde des fünften Laufs, eingearbeitet.** acceptance-3 verspricht nicht mehr, dass ein volles Neuberechnen nichts ändert (nach R3 falsch), sondern nennt Ebene für Ebene, was für andere Mandanten gilt, und schließt den Mandanten ein, dessen Rohwerte die Aufbewahrung entfernt hat; die Fixture dazu ist der gemessene Ablauf R1–R2. acceptance-4 ist nach der Vorgabe neu gefasst.

**Schreiben in die Materialisierungstabellen (prior-art, proceed).** Established: `resolve_aggregate_tables` ermittelt Schema und Tabelle je Aggregat und wirft, wenn eine fehlt (`observation_repository.py:132-144`); die Löschung eines Mandanten schreibt dort bereits gezielt (`_purge_aggregates`, `:242-276`). Der Kommentar `:121-123` nennt das Aggregat eine nur lesbare Sicht, die ein `DELETE` ablehnt; gemessen wurde, dass ein `INSERT` über die Sicht angenommen wird. Der Import schreibt trotzdem in die ermittelten Tabellen, damit Schreiben und Löschen denselben Weg nehmen und das Layout an einer Stelle festgehalten ist (acceptance-5).

**Spec schließt den Import aus (drift, proceed).** Established: REQ-056 §8.3 (`:365`) und AK-47 (`:683`); Runbook DE `:8`, `:26`, `:146`. acceptance-7 zieht nach; F-16 acceptance-8 trägt den Teil für die Rohwerte.

**Überschneidung mit F-16 (overlap, proceed).** Begründung für `proceed`: F-16 liest und prüft den Messwert-Teil, bildet die Sensor-Zuordnung, schreibt die Rohwerte, lässt ihren Zeitraum neu berechnen und behebt die Löschlücke (F-16 acceptance-4, -5, -9); F-34 schreibt mit derselben Zuordnung die älteren Stunden- und Tageswerte, lässt die Tageswerte ihres Zeitraums neu berechnen und ergänzt den Bericht um ihre Zahlen (der Eintrag „nicht eingespielt“ aus F-16 acceptance-6 entfällt). Die Regel „Sensor nicht im Archiv: auslassen und zählen“ gilt in beiden, je für die eigene Reihe. Die Phase „Messwerte“ (F-16 acceptance-7) umfasst auch die Schritte dieses Features. Kein Kriterium steht in beiden.

**Überschneidung mit F-17 (overlap, proceed).** Begründung für `proceed`: acceptance-6 benutzt Vorprüfung, Bestätigung, Zuordnung und Start aus F-17 als Weg, ohne sie zu ändern.

**Wertnachweis des Sprints.** `verifies_sprint_value: acceptance-6`. F-34 ist das letzte Feature der Kette; der Rundlauf geht durch alle sechs. Die Größe von rund 500 MiB weist er nicht nach; dafür ist der Handlauf zu F-15 acceptance-1 verpflichtend.

**Ergebnis:** Der sichere Weg ist gemessen (R4, III); die Kriterien entscheiden unter den Messungen eindeutig. Unbelegt und mit Hook versehen sind das Neuberechnen der Tageswerte über einen langen Zeitraum und die leere Zielinstallation. F-34 ist `ready`, vorbehaltlich des nächsten Agentenlaufs. Sieben Kriterien.

## Risks

- **Neuberechnen jenseits der Rohwert-Frist (bestehendes Risiko, Issue #3172).** Berechnet jemand `sensor_hourly` von Hand über einen Zeitraum neu, dessen Rohwerte die Aufbewahrung entfernt hat, verliert jeder Garten dort seine Stundenwerte, auch die eingespielten (gemessen). Der Import löst das nie aus; Warnung und Guard sind #3172, nicht Teil von Sprint 5.
- **Neuberechnen der Tageswerte über bis zu zwei Jahre.** Gemessen ist ein Tag (R4); für den ganzen eingespielten Stundenwert-Zeitraum ist die Unschädlichkeit hergeleitet. acceptance-3 prüft es. Fehlen einem anderen Mandanten dort Stundenwerte, zu denen er Tageswerte hat, verlöre er diese Tageswerte; die Anwendung erzeugt einen solchen Zustand nicht, solange die Stundenwert-Aufbewahrung nicht greift, und der Stichtag hält Abstand zu ihr.
- **Leere oder sehr junge Zielinstallation.** Ein Neuberechnen auf leeren Tabellen bewegt die Wassermarke nicht (gemessen). Ob die eingespielten Werte in einer ganz neu aufgesetzten Installation die Policy-Läufe überstehen, klärt die Variante im Hook zu acceptance-4.
- Das Schreiben in die Materialisierungstabellen stützt sich auf TimescaleDB-Interna; ein Upgrade kann es brechen. acceptance-5 macht daraus einen fehlgeschlagenen Import und einen roten Test statt stillen Datenverlusts.
- Das Neuberechnen über bis zu zwei Jahre Tageswerte verlängert den Lauf; das Lebenszeichen muss gesetzt werden (`tenant_export_service.py:168`).
- Was älter ist als die Aufbewahrungsfristen der Zielinstallation, kommt nicht zurück; der Bericht nennt die Zahl.

## References

- Issue #3140 (Rest von #2138, MT-042), roadmap item R-19
- `project/requirements/tenant-export-import-remainder.md` (R4, R9, R13 in der Fassung vom 2026-11-28)
- Setzt F-16 voraus (Messwert-Teil, Sensor-Zuordnung, Rohwerte samt Neuberechnen ihres Zeitraums, behobene Löschlücke, Bericht) und für acceptance-6 F-17; letztes Feature der Kette in Sprint 5

## Betreiberentscheidungen 2026-11-28

- **Archivierte Stunden- und Tageswerte werden direkt geschrieben.** Der ursprüngliche Zusatz „nichts wird neu berechnet“ ist durch D ersetzt.
- **Messwerte ohne zuordenbaren Sensor: auslassen und zählen**, auch Stunden- und Tageswerte (acceptance-2).
- **A — F-16 wird geteilt**; dieses Feature ist der Teil „Stunden- und Tageswerte“ und trägt den Wertnachweis des Sprints.
- **D — Der Import lässt am Ende gezielt neu berechnen**, genau die eingespielten Zeiträume, erst Stunden-, dann Tageswerte. Nach der fünften Messreihe heißt das: Stundenwerte nur ab dem Rohwert-Stichtag (F-16), Tageswerte nur ab dem Stundenwert-Stichtag.
- **E — Sprintwert:** „samt Sensor-Historie im Rahmen der Aufbewahrungsfristen“; acceptance-6 folgt dem Wortlaut.
- **F — Die Löschlücke wird in F-16 behoben**: Jedes Löschen von Rohwerten berechnet seinen Zeitraum gezielt neu. Für dieses Feature heißt das: Nach F-16 entstehen keine neuen liegenden Vormerkungen mehr.
- **Der Handlauf mit rund 500 MiB (F-15 acceptance-1) ist verpflichtend**; acceptance-6 ersetzt ihn nicht.
- Vorgaben der Hauptsitzung (Stand nach ihrer fünften Messreihe): Schichtung nach Aufbewahrungsfristen; `sensor_hourly` wird jenseits des Rohwert-Stichtags nie neu berechnet; kein Vorab-Neuberechnen und kein Abbruch bei alter Vormerkung; `materialized_only` im Layout-Kriterium; das bestehende Risiko ist Issue #3172 (Consistency notes).

## Offene Punkte (Stand 2026-11-28)

Keine offene Betreiberentscheidung blockiert F-34.

- **Leere Zielinstallation.** Für eine Installation ohne Rohwerte oder mit leerer Zeitreihendatenbank fehlt die Messung, ob die eingespielten Werte die Policy-Läufe überstehen (Varianten im Hook zu acceptance-4).
- **Neuberechnen der Tageswerte über einen langen Zeitraum** ist für einen Tag gemessen, für bis zu zwei Jahre hergeleitet (Hook zu acceptance-3).
- **Lage der Stichtage** (Tagesbeginn in UTC, ein Tag Abstand) ist eine Festlegung der Planung auf Grundlage der Vorgabe „mit Abstand zur Frist“.
- **Issue #3172** (Warnung und Guard gegen ein Neuberechnen jenseits der Frist) liegt außerhalb von Sprint 5.
