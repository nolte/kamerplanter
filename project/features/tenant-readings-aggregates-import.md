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
      resolution: revisit-after Integrationstest zu acceptance-4 (Policy-Läufe auf einer nie voll aufgefrischten Datenbank)
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
      resolution: revisit-after Integrationstest zu acceptance-4 (Altlast im Zielzeitraum) und Prüfung, ob TimescaleDB offene Vormerkungen lesbar macht
      evidence: "Altlasten: Vormerkungen aus Löschungen vor F-16 bleiben liegen (':259-262' beschreibt sie als harmlos). Das Vorab-Neuberechnen dieses Features würde in einem solchen Bereich die Buckets anderer Mandanten löschen, deren Rohwerte abgelaufen sind (Messung 300-Tage-Bucket). Im Repository liest nichts den Vormerk-Katalog von TimescaleDB (Suche nach 'invalidation', 'watermark', '_timescaledb_catalog' in src/backend, scripts, helm: nur dieser Kommentar)."

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
verloren. Die wiederhergestellten Werte bleiben auch dann erhalten, wenn das
Archiv weiter zurückreicht, als die Installation alt ist. Damit ist ein Garten
aus seinem Archiv im Rahmen der Aufbewahrungsfristen vollständig
wiederherstellbar.

## Acceptance criteria

- [ ] **acceptance-1** Nach dem Ende des Imports liefert die Messwert-Abfrage des neuen Mandanten jeden Stunden- und Tageswert des Archivs innerhalb der Aufbewahrungsfristen der Zielinstallation genau einmal: Stundenwerte vor dem Rohwert-Stichtag und Tageswerte zwischen dem Tageswert- und dem Stundenwert-Stichtag genau wie im Archiv; Stundenwerte ab dem Rohwert-Stichtag und Tageswerte ab dem Stundenwert-Stichtag gebildet aus den eingespielten Quelldaten, gleich dem Archiv bis auf eine relative Abweichung von 1e-9.
- [ ] **acceptance-2** Nicht eingespielt und im Importbericht je Grund gezählt werden Stunden- und Tageswerte eines Sensors, der nicht im Archiv steht, Stundenwerte vor dem Stundenwert-Stichtag und Tageswerte vor dem Tageswert-Stichtag; jeder Stichtag ist ein Tagesbeginn in UTC, mindestens einen Tag innerhalb der jeweiligen Aufbewahrung der Zielinstallation (heute 2 Jahre für Stunden-, 5 Jahre für Tageswerte).
- [ ] **acceptance-3** Durch den Import geht kein Rohwert, Stunden- oder Tageswert eines anderen Mandanten verloren: Außerhalb der vom Import neu berechneten Zeiträume sind seine Werte unverändert, innerhalb entsprechen sie seinen eigenen Quelldaten (unverändert bis auf 1e-9, wenn sie das vorher schon taten); ein anschließendes Neuberechnen beider Aggregate über den ganzen Zeitraum ändert keinen Wert irgendeines Mandanten. Dasselbe gilt nach einem gescheiterten und zurückgerollten Import, der zudem keinen Stunden- oder Tageswert des neuen Mandanten hinterlässt.
- [ ] **acceptance-4** In einer Zielinstallation, deren Aggregate bisher nur die Policy-Läufe gesehen haben, behalten die eingespielten Stunden- und Tageswerte ihre Werte, nachdem die Policies erneut gelaufen sind und nachdem beide Aggregate über den ganzen Zeitraum neu berechnet wurden — auch für Zeiträume, die weiter zurückliegen, als die Installation alt ist —, und kein Wert eines anderen Mandanten geht dabei verloren.
- [ ] **acceptance-5** Passt das Tabellenlayout der Stunden- und Tageswerte nicht zu dem, was der Import erwartet, oder lesen die Aggregate nicht ausschließlich materialisierte Werte (`materialized_only`), endet der Import als fehlgeschlagen, bevor ein Messwert geschrieben ist, und der Garten wird zurückgerollt.
- [ ] **acceptance-6** Ein Garten mit Datensätzen, Fotos, Mitgliedern, Sensoren und Messwerten, dessen Stunden- und Tageswerte vollständig berechnet sind, wird exportiert, das Archiv hochgeladen, vorgeprüft, die Mitglieder per E-Mail zugeordnet und aus der Vorprüfung importiert; ein erneuter Export des neuen Gartens enthält bis auf Schlüssel, Importzeitpunkt und Instanz-ID dieselben Daten einschließlich der Sensor-Historie im Rahmen der Aufbewahrungsfristen (Rohwerte ab dem Stichtag genau, Stunden- und Tageswerte mit einer relativen Abweichung von höchstens 1e-9).
- [ ] **acceptance-7** REQ-056 §8.3, §8.4, AK-47 und ein neues Abnahmekriterium in §16.4 sowie das Runbook (DE + EN) beschreiben den Import der Stunden- und Tageswerte, die Schichtung nach Aufbewahrungsfristen, das Neuberechnen vor und nach dem Schreiben und den Prüfschritt des Betreibers vor dem ersten Import in eine Installation, in der früher Sensoren oder Gärten gelöscht wurden.

## Test hooks

- **acceptance-1** — `src/backend/tests/integration/test_tenant_export_readings_timescale.py` (Timescale service of `.github/workflows/backend-guards.yml`): the seed has sensor documents and a fully refreshed source; after the import `query_hourly` / `query_daily` (`observation_repository.py:196-228`) return every archived bucket inside the retentions exactly once (no bucket twice: F-16 builds the hourly buckets of the raw period from raw rows, F-34 writes no archived hourly bucket there, and no archived daily bucket from the hourly cut-off on); by construction of the seed the test checks the four layers: hourly before the raw cut-off and daily between the daily and the hourly cut-off equal the archive exactly (`avg_value`, `min_value`, `max_value`, `sample_count`); hourly from the raw cut-off on and daily from the hourly cut-off on equal the archive within 1e-9 relative; order of work pinned: recompute the periods to be written, write, then refresh `sensor_hourly` over the imported raw period (F-16) and `sensor_daily` over the imported hourly period, nothing wider — pending
- **acceptance-2** — same module: buckets of an unknown `sensor_key`, hourly buckets before the hourly cut-off and daily buckets before the daily cut-off are not written and counted per reason in the report; both retentions are read from the target's effective policies (`data_access/timescale/migrations/003_retention_policies.sql:6`, `:9`; a test with changed policies proves they are not hard-coded); each cut-off is the start of a UTC day at least one day inside the retention — pending
- **acceptance-3** — same module: a second tenant has raw rows, hourly and daily buckets inside the imported periods, built from its own source rows, and hourly and daily buckets older than the retentions written directly with no source rows; snapshots of the raw table and both materialisation tables for every tenant are taken before the import, after it, and after `CALL refresh_continuous_aggregate('sensor_hourly', NULL, NULL)` and `('sensor_daily', NULL, NULL)`: no row of the second tenant is missing; its buckets inside the recomputed periods equal what its own source rows yield (within 1e-9 of their state before); its other rows are identical; the full refresh changes nothing for any tenant. Second scenario: induced failure after the buckets were written → zero buckets of the new tenant (rollback through `erase_abandoned_import` → `_purge_aggregates`, `observation_repository.py:242-276`, with the recompute of F-16 acceptance-9) and the same holds. Control (measured 2026-11-28): one directly inserted hourly row in a 900-day-old day without the bounded daily refresh makes a full daily refresh delete the second tenant's daily bucket — pending
- **acceptance-4** — same module, second fixture reproducing the measured course I–IV: raw rows of a third tenant in the last hours and days, only the two policy windows refreshed (3 h … 1 h hourly, 3 d … 1 d daily, `002_continuous_aggregates.sql:16-19`, `:37-40`), never a full refresh; a second tenant with source rows; then the import of an archive reaching back 900 days; then the policy windows again, then a full refresh of both aggregates: every imported bucket keeps its value and no value of the second or third tenant is lost. Variants that settle what is not measured: (a) the bounded recompute before the write, instead of the measured full one; (b) a target with no raw row at all in the archive's raw period; (c) a completely empty time-series database; (d) a legacy mark: raw rows of the second tenant deleted without recompute, as before F-16, in a period whose raw rows have meanwhile expired — the test records whether the second tenant's buckets survive the import — pending
- **acceptance-5** — same module: layout pin on `resolve_aggregate_tables()` (`observation_repository.py:132-144`) and the written columns (`bucket, tenant_key, sensor_key, sensor_type, avg_value, min_value, max_value, sample_count`); a missing or changed materialisation table, and an aggregate altered to `materialized_only = false`, each end the import `failed` with no reading written and the tenant rolled back — pending
- **acceptance-6** — same module, extending `test_the_archive_carries_the_tenants_readings_and_an_import_lists_but_skips_them` (`:151`): export → upload → pre-check → e-mail mapping → start from the pre-check → re-export, empty difference including `timeseries/readings.csv` (sensor keys compared through the key mapping; raw rows of the seed lie after the cut-off; aggregate numbers within 1e-9 relative). The source is fully refreshed before the export, because in operation the newest hour and day are not materialised yet and would show as a difference. Needs two ArangoDB databases, as the module provisions (`SOURCE_DB`, `TARGET_DB`, `:50-51`), because an import next to the original fails on own species (runbook `docs/de/deployment/tenant-export-import.md:136-137`); the source photos carry no EXIF block, because the import stores stripped bodies (`_with_stored_bodies`, `tenant_export_service.py:1286-1312`) — pending
- **acceptance-7** — `mkdocs build --strict` + spec diff review — pending

## Consistency notes

Das Feature ist am 2026-11-28 aus F-16 abgespalten (Betreiberentscheidung A). Der erste Durchgang beim Anlegen war manuell (Subagent der Planungssitzung, weil ein Subagent den Agenten nicht starten darf); seither hat der `feature-consistency-reviewer` (`feature-consistency-reviewer@unknown`) das Feature im dritten und vierten Lauf der Hauptsitzung geprüft. Die Befunde aller Durchgänge stehen im Frontmatter. Dieser Abschnitt gibt den geltenden Stand nach dem vierten Lauf wieder; frühere Fassungen dieser Notizen stehen in der Git-Historie des Zweigs (`b3c7f6eba`, `9c779f351`). Die zitierten Code-Stellen wurden nachgelesen; ein eigener Test lief nicht, alle Messungen stammen von der Hauptsitzung.

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

**Was daraus folgt (Vorgaben der Hauptsitzung).**

1. **Schichtung nach Aufbewahrungsfristen.** Established: Rohwerte 90 Tage, Stundenwerte 2 Jahre, Tageswerte 5 Jahre (`data_access/timescale/migrations/003_retention_policies.sql:3`, `:6`, `:9`). Was älter ist als die Frist seiner Ebene, wird gezählt, nicht eingespielt; die Fristen liest der Import aus den wirksamen Policies; jeder Stichtag ist ein Tagesbeginn in UTC mit Abstand zur Frist (acceptance-2; für Rohwerte F-16 acceptance-2).
2. **Ablauf des Imports.** Erst die Zeiträume neu berechnen, die der Import beschreiben wird (Stundenwerte über den Stundenwert-Zeitraum, Tageswerte über den Tageswert-Zeitraum); dann die archivierten Werte direkt schreiben; dann gezielt neu berechnen: `sensor_hourly` über den eingespielten Rohwert-Zeitraum (liefert F-16), danach `sensor_daily` über den eingespielten Stundenwert-Zeitraum. Der Import schreibt in die über `resolve_aggregate_tables` ermittelten Tabellen (`observation_repository.py:132-144`), nicht über die Sicht.
3. **Woher ein Wert nach dem Import stammt** (acceptance-1):

| Zeitraum | Stundenwerte | Tageswerte |
|---|---|---|
| ab dem Rohwert-Stichtag | aus den eingespielten Rohwerten (bis 1e-9) | aus den Stundenwerten (bis 1e-9) |
| davor, ab dem Stundenwert-Stichtag | direkt aus dem Archiv (genau) | aus den eingespielten Stundenwerten (bis 1e-9) |
| davor, ab dem Tageswert-Stichtag | nicht eingespielt, gezählt | direkt aus dem Archiv (genau) |
| älter | nicht eingespielt, gezählt | nicht eingespielt, gezählt |

**Was belegt ist und was nicht.**

- *Gemessen:* Sichtbarkeit direkt geschriebener Werte bei `materialized_only = true`; Vormerkung durch Rohwerte und durch direkt eingefügte Stundenwerte; Unschädlichkeit eines begrenzten Neuberechnens der Stundenwerte, wo alle Mandanten ihre Rohwerte haben; Verlust direkt geschriebener Werte in nie materialisierten Zeiträumen bei einem vollen Neuberechnen; Überleben nach einem vollen Neuberechnen mit vorhandenem Rohwert.
- *Hergeleitet, nicht gemessen* (Unestablished; jeweils durch den genannten Hook zu klären): dass ein *begrenztes* Neuberechnen genau der Zielzeiträume vor dem Schreiben dieselbe Wirkung hat wie das gemessene volle (Hook acceptance-4, Variante a); dass es auch wirkt, wenn im Zielzeitraum kein Rohwert liegt oder die Zeitreihendatenbank leer ist — die Messung VI zeigt, dass ein Neuberechnen auf leeren Tabellen die Wassermarke nicht bewegt (Varianten b und c); dass das begrenzte Neuberechnen der Tageswerte für andere Mandanten unschädlich ist (misst zuerst F-16 acceptance-4, dann acceptance-3 hier).
- *Altlasten (Unestablished, mit Risiko).* Established: Löschungen von Rohwerten vor F-16 lassen ihre Vormerkung liegen (`observation_repository.py:259-262`); im Repository liest nichts den Vormerk-Katalog von TimescaleDB (Suche nach `invalidation`, `watermark` und `_timescaledb_catalog` in `src/backend`, `scripts` und `helm`: Treffer nur in diesem Kommentar). Ob TimescaleDB offene Vormerkungen eines Zeitraums lesbar macht, ist damit aus dem Repository nicht belegt; das zeigte ein Blick in den Katalog der laufenden Datenbank (nicht durchgeführt). Folge: Liegt im Zielzeitraum eine alte Vormerkung, deren Rohwerte abgelaufen sind, löscht das Vorab-Neuberechnen dort die Buckets anderer Mandanten (Messung 300-Tage-Bucket). acceptance-4 gilt deshalb für eine Installation ohne solche Altlast; Variante d des Hooks hält fest, was mit Altlast geschieht.

**Befunde des vierten Laufs, eingearbeitet.** acceptance-1 nennt die Stichtage und „genau einmal“; acceptance-3 sagt für andere Mandanten zu, was tatsächlich gilt (kein Wert geht verloren; Werte in neu berechneten Zeiträumen entsprechen den eigenen Quelldaten); acceptance-4 beschreibt den realen Fall (nur Policy-Läufe) und nennt das Mittel; acceptance-6 gilt für eine vollständig neu berechnete Quelle, weil im Betrieb die jüngste Stunde und der jüngste Tag noch nicht materialisiert sind.

**Schreiben in die Materialisierungstabellen (prior-art, proceed).** Established: `resolve_aggregate_tables` ermittelt Schema und Tabelle je Aggregat und wirft, wenn eine fehlt (`observation_repository.py:132-144`); die Löschung eines Mandanten schreibt dort bereits gezielt (`_purge_aggregates`, `:242-276`). Der Kommentar `:121-123` nennt das Aggregat eine nur lesbare Sicht, die ein `DELETE` ablehnt; gemessen wurde, dass ein `INSERT` über die Sicht angenommen wird. Der Import schreibt trotzdem in die ermittelten Tabellen, damit Schreiben und Löschen denselben Weg nehmen und das Layout an einer Stelle festgehalten ist (acceptance-5).

**Spec schließt den Import aus (drift, proceed).** Established: REQ-056 §8.3 (`:365`) und AK-47 (`:683`); Runbook DE `:8`, `:26`, `:146`. acceptance-7 zieht nach; F-16 acceptance-8 trägt den Teil für die Rohwerte.

**Überschneidung mit F-16 (overlap, proceed).** Begründung für `proceed`: F-16 liest und prüft den Messwert-Teil, bildet die Sensor-Zuordnung, schreibt die Rohwerte, lässt ihren Zeitraum neu berechnen und behebt die Löschlücke (F-16 acceptance-4, -5, -9); F-34 schreibt mit derselben Zuordnung die älteren Stunden- und Tageswerte und ergänzt den Bericht um ihre Zahlen (der Eintrag „nicht eingespielt“ aus F-16 acceptance-6 entfällt). Die Regel „Sensor nicht im Archiv: auslassen und zählen“ gilt in beiden, je für die eigene Reihe. Die Phase „Messwerte“ (F-16 acceptance-7) umfasst auch die Schritte dieses Features. Kein Kriterium steht in beiden.

**Überschneidung mit F-17 (overlap, proceed).** Begründung für `proceed`: acceptance-6 benutzt Vorprüfung, Bestätigung, Zuordnung und Start aus F-17 als Weg, ohne sie zu ändern.

**Wertnachweis des Sprints.** `verifies_sprint_value: acceptance-6`. F-34 ist das letzte Feature der Kette; der Rundlauf geht durch alle sechs. Die Größe von rund 500 MiB weist er nicht nach; dafür ist der Handlauf zu F-15 acceptance-1 verpflichtend.

**Ergebnis:** Die Kriterien entscheiden unter den Messungen eindeutig. Unbelegt und mit Hook versehen sind das begrenzte Vorab-Neuberechnen, die leere Zielinstallation und die Altlasten. F-34 ist `ready`, vorbehaltlich des nächsten Agentenlaufs; der Punkt „Altlasten“ unter „Offene Punkte“ sollte vor dem ersten Import in die echte Installation geklärt sein.

## Risks

- **Altlasten in der Zielinstallation.** Wurden dort früher Sensoren oder Gärten gelöscht, liegen Vormerkungen in Zeiträumen, deren Rohwerte inzwischen abgelaufen sind. Das Vorab-Neuberechnen des Imports würde in diesen Zeiträumen die Stunden- und Tageswerte anderer Gärten löschen. Ob der Import solche Vormerkungen erkennen kann, ist unbelegt. Sensoren werden im normalen Betrieb gelöscht; in einer länger laufenden Installation ist mit Altlasten zu rechnen.
- **Leere oder sehr junge Zielinstallation.** Ein Neuberechnen auf leeren Tabellen bewegt die Wassermarke nicht (gemessen). Ob die eingespielten Werte in eine ganz neu aufgesetzte Installation ein späteres volles Neuberechnen überstehen, klärt erst der Hook zu acceptance-4.
- **Neuberechnen der Tageswerte.** Für Stundenwerte aus Rohwerten ist die Unschädlichkeit eines begrenzten Neuberechnens gemessen, für Tageswerte aus Stundenwerten hergeleitet.
- Das Schreiben in die Materialisierungstabellen stützt sich auf TimescaleDB-Interna; ein Upgrade kann es brechen. acceptance-5 macht daraus einen fehlgeschlagenen Import und einen roten Test statt stillen Datenverlusts.
- Das Neuberechnen über bis zu zwei Jahre Stundenwerte und fünf Jahre Tageswerte verlängert den Lauf; das Lebenszeichen muss gesetzt werden (`tenant_export_service.py:168`).
- Was älter ist als die Aufbewahrungsfristen der Zielinstallation, kommt nicht zurück; der Bericht nennt die Zahl.

## References

- Issue #3140 (Rest von #2138, MT-042), roadmap item R-19
- `project/requirements/tenant-export-import-remainder.md` (R4, R9, R13 in der Fassung vom 2026-11-28)
- Setzt F-16 voraus (Messwert-Teil, Sensor-Zuordnung, Rohwerte samt Neuberechnen ihres Zeitraums, behobene Löschlücke, Bericht) und für acceptance-6 F-17; letztes Feature der Kette in Sprint 5

## Betreiberentscheidungen 2026-11-28

- **Archivierte Stunden- und Tageswerte werden direkt geschrieben.** Der ursprüngliche Zusatz „nichts wird neu berechnet“ ist durch D ersetzt.
- **Messwerte ohne zuordenbaren Sensor: auslassen und zählen**, auch Stunden- und Tageswerte (acceptance-2).
- **A — F-16 wird geteilt**; dieses Feature ist der Teil „Stunden- und Tageswerte“ und trägt den Wertnachweis des Sprints.
- **D — Der Import lässt am Ende gezielt neu berechnen**, genau die eingespielten Zeiträume, erst Stunden-, dann Tageswerte.
- **E — Sprintwert:** „samt Sensor-Historie im Rahmen der Aufbewahrungsfristen“; acceptance-6 folgt dem Wortlaut.
- **F — Die Löschlücke wird in F-16 behoben**: Jedes Löschen von Rohwerten berechnet seinen Zeitraum gezielt neu. Für dieses Feature heißt das: Nach F-16 entstehen keine neuen liegenden Vormerkungen mehr.
- **Der Handlauf mit rund 500 MiB (F-15 acceptance-1) ist verpflichtend**; acceptance-6 ersetzt ihn nicht.
- Vorgaben der Hauptsitzung: Schichtung nach Aufbewahrungsfristen; Neuberechnen der Zielzeiträume vor dem Schreiben als Mittel für acceptance-4; `materialized_only` im Layout-Kriterium (Consistency notes).

## Offene Punkte (Stand 2026-11-28)

Keine offene Betreiberentscheidung blockiert den Start von F-34.

- **Altlasten — vor dem ersten Import in die echte Installation zu klären.** Unbelegt ist, ob TimescaleDB offene Vormerkungen eines Zeitraums lesbar macht. Wenn ja, empfiehlt die Planung ein weiteres Kriterium: Findet der Import im Zielzeitraum eine offene Vormerkung, die älter ist als die Rohwert-Aufbewahrung, bricht er vor jedem Schreiben mit einem eigenen Code ab, und das Runbook sagt dem Betreiber, was zu tun ist. Wenn nein, bleibt ein Prüfschritt des Betreibers im Runbook (acceptance-7) und das Risiko. Die Klärung ist ein Blick in den Katalog einer laufenden TimescaleDB und Variante d des Hooks zu acceptance-4.
- **Leere Zielinstallation.** Das Mittel für acceptance-4 ist für eine Installation mit Rohwerten hergeleitet; für eine leere fehlt die Messung (Varianten b und c des Hooks).
- **Lage der Stichtage** (Tagesbeginn in UTC, ein Tag Abstand) ist eine Festlegung der Planung auf Grundlage der Vorgabe „mit Abstand zur Frist“.
