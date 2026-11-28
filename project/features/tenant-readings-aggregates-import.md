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
      evidence: "'Buckets older than the raw retention (90 days) cannot be recomputed at all … a wider refresh would wipe other tenants' history' (:245-251). Messung der Hauptsitzung gegen TimescaleDB 2.32.1-pg16 (2026-11-28) bestätigt es. Entschieden: direkt schreiben, nichts neu berechnen; acceptance-1 bis -3."
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
den Verlauf wie vor dem Export. Die Messwerte anderer Gärten bleiben dabei
unberührt. Das gilt auch, wenn ein Garten in eine neu aufgesetzte Installation
zurückgespielt wird. Damit ist ein Garten aus seinem Archiv vollständig
wiederherstellbar.

## Acceptance criteria

- [ ] **acceptance-1** Nach dem Ende des Imports liefert die Messwert-Abfrage des neuen Mandanten jeden Stunden- und Tageswert des Archivs, der innerhalb der Aufbewahrungsfristen der Zielinstallation liegt: außerhalb der neu berechneten Zeiträume genau den archivierten Wert, innerhalb mit einer relativen Abweichung von höchstens 1e-9.
- [ ] **acceptance-2** Nicht eingespielt und im Importbericht je Grund gezählt werden Stunden- und Tageswerte eines Sensors, der nicht im Archiv steht, Stundenwerte älter als die Stundenwert-Aufbewahrung der Zielinstallation (heute 2 Jahre) und Tageswerte älter als ihre Tageswert-Aufbewahrung (heute 5 Jahre); der Schnitt liegt jeweils auf einer Tagesgrenze, mindestens einen Tag innerhalb der Frist.
- [ ] **acceptance-3** Weder der Import noch ein anschließendes Neuberechnen beider Aggregate über den ganzen Zeitraum ändert einen Rohwert, Stunden- oder Tageswert eines anderen Mandanten oder einen Wert des neuen Mandanten; dasselbe gilt nach einem gescheiterten und zurückgerollten Import, der zudem keinen Stunden- oder Tageswert des neuen Mandanten hinterlässt.
- [ ] **acceptance-4** In einer Zielinstallation, deren Aggregate noch nie über den ganzen Zeitraum neu berechnet wurden, behalten die eingespielten Stunden- und Tageswerte ihre Werte, nachdem die Aggregat-Policies gelaufen sind und nachdem beide Aggregate über den ganzen Zeitraum neu berechnet wurden.
- [ ] **acceptance-5** Passt das Tabellenlayout der Stunden- und Tageswerte nicht zu dem, was der Import erwartet, oder lesen die Aggregate nicht ausschließlich materialisierte Werte (`materialized_only`), endet der Import als fehlgeschlagen, bevor ein Messwert geschrieben ist, und der Garten wird zurückgerollt.
- [ ] **acceptance-6** Ein Garten mit Datensätzen, Fotos, Mitgliedern, Sensoren und Messwerten wird exportiert, das Archiv hochgeladen, vorgeprüft, die Mitglieder per E-Mail zugeordnet und aus der Vorprüfung importiert; ein erneuter Export des neuen Gartens enthält bis auf Schlüssel, Importzeitpunkt und Instanz-ID dieselben Daten einschließlich der Sensor-Historie im Rahmen der Aufbewahrungsfristen (Rohwerte ab dem Stichtag genau, Stunden- und Tageswerte mit einer relativen Abweichung von höchstens 1e-9).
- [ ] **acceptance-7** REQ-056 §8.3, §8.4, AK-47 und ein neues Abnahmekriterium in §16.4 sowie das Runbook (DE + EN) beschreiben den Import der Stunden- und Tageswerte, die Schichtung nach Aufbewahrungsfristen, das gezielte Neuberechnen und den Schritt für die Wiederherstellung in eine neu aufgesetzte Installation.

## Test hooks

- **acceptance-1** — `src/backend/tests/integration/test_tenant_export_readings_timescale.py` (Timescale service of `.github/workflows/backend-guards.yml`): the target's aggregates are refreshed once before the import (as the fixture does, `:86-87`); the seed has sensor documents; after the import `query_hourly` / `query_daily` (`observation_repository.py:196-228`) return every archived bucket inside the retentions; the test distinguishes by construction of the seed: (a) hourly buckets before the raw cut-off and daily buckets before the hourly cut-off equal the archive exactly (`avg_value`, `min_value`, `max_value`, `sample_count`); (b) hourly buckets of the raw period (rebuilt from the imported raw rows, F-16) and daily buckets of the imported hourly period (rebuilt from the imported hourly rows) equal the archive within 1e-9 relative; the import refreshes `sensor_hourly` over the imported raw period first, then `sensor_daily` over the imported hourly period, and nothing wider — pending
- **acceptance-2** — same module: buckets of an unknown `sensor_key`, hourly buckets older than the hourly retention and daily buckets older than the daily retention are not written and counted per reason in the report; both retentions are read from the target's effective policies (`data_access/timescale/migrations/003_retention_policies.sql:6`, `:9`; a test with changed policies proves they are not hard-coded); each cut is a day boundary at least one day inside the retention — pending
- **acceptance-3** — same module: a second tenant has raw rows, hourly and daily buckets inside the imported periods, and hourly and daily buckets older than the retentions written directly with no source rows; snapshots of the raw table and both materialisation tables for every tenant are taken after the import and again after `CALL refresh_continuous_aggregate('sensor_hourly', NULL, NULL)` and `('sensor_daily', NULL, NULL)`: the second tenant's rows equal their state before the import, the new tenant's rows do not change by the full refresh. Second scenario: induced failure after the buckets were written → zero buckets of the new tenant (rollback through `erase_abandoned_import` → `_purge_aggregates`, `observation_repository.py:242-276`) and the same snapshots are unchanged by a full refresh. Control (measured 2026-11-28): one directly inserted hourly row of the first tenant in a 900-day-old day without the bounded daily refresh makes a full daily refresh delete the second tenant's daily bucket — pending
- **acceptance-4** — same module, second fixture without the initial full refresh: import, then run the aggregate policies (jobs of `002_continuous_aggregates.sql:16-19`, `:37-40`, via `run_job` or by refreshing exactly their windows), then a full refresh of both aggregates; every imported bucket still carries its value. Measured 2026-11-28: on such a database a full refresh deletes directly written buckets; not measured: the policy runs. This test is the experiment that settles it; a possible means, not a requirement, is that the import refreshes a never-refreshed installation once before it writes — pending
- **acceptance-5** — same module: layout pin on `resolve_aggregate_tables()` (`observation_repository.py:132-144`) and the written columns (`bucket, tenant_key, sensor_key, sensor_type, avg_value, min_value, max_value, sample_count`); a missing or changed materialisation table, and an aggregate altered to `materialized_only = false`, each end the import `failed` with no reading written and the tenant rolled back — pending
- **acceptance-6** — same module, extending `test_the_archive_carries_the_tenants_readings_and_an_import_lists_but_skips_them` (`:151`): export → upload → pre-check → e-mail mapping → start from the pre-check → re-export, empty difference including `timeseries/readings.csv` (sensor keys compared through the key mapping; raw rows of the seed lie after the cut-off; aggregate numbers within 1e-9 relative). Needs two ArangoDB databases, as the module provisions (`SOURCE_DB`, `TARGET_DB`, `:50-51`), because an import next to the original fails on own species (runbook `docs/de/deployment/tenant-export-import.md:136-137`); the source photos carry no EXIF block, because the import stores stripped bodies (`_with_stored_bodies`, `tenant_export_service.py:1286-1312`); the seed has sensor documents; the target's aggregates are refreshed once before the import — pending
- **acceptance-7** — `mkdocs build --strict` + spec diff review — pending

## Consistency notes

Manual pass performed by: Claude (Subagent der Planungssitzung vom 2026-11-28, im Auftrag des Betreibers nolte)

Manueller, rein lesender Durchgang gegen develop `17e1034d2` beim Anlegen des Features am 2026-11-28; ein eigener Test lief nicht. Der Agent `feature-consistency-reviewer` ist verfügbar, ein Subagent darf ihn aber nicht starten; die Hauptsitzung lässt ihn nach diesem Commit laufen. Das Feature ist aus F-16 abgespalten (Betreiberentscheidung A vom 2026-11-28); die Vorgeschichte seiner Kriterien steht in `tenant-readings-import.md`.

**Messung der Hauptsitzung gegen TimescaleDB 2.32.1-pg16** (dasselbe Image wie `docker-compose.yml:99`), 2026-11-28; Befehle sinngemäß, Ergebnisse wie übermittelt:

- Abfrage von `timescaledb_information.continuous_aggregates`: Die Aggregate sind `materialized_only = true`; Materialisierungstabellen `_timescaledb_internal._materialized_hypertable_2` (hourly) und `_3` (daily); Spalten hourly: `bucket, tenant_key, sensor_key, sensor_type, avg_value, min_value, max_value, sample_count`.
- `INSERT` in die Materialisierungstabelle: „Direktes INSERT in die Materialisierungstabelle wird angenommen und ist sofort über die Sicht `sensor_hourly` sichtbar“; auch ein `INSERT` über die Sicht selbst wurde angenommen.
- `refresh_continuous_aggregate` ohne vorgemerkte Änderung: lässt direkt geschriebene Buckets unverändert („already up-to-date“).
- Rohwerte in den Zeitraum eines Buckets schreiben, dann neu berechnen: „Schreibt der Import Rohwerte in den Zeitraum eines Buckets, merkt TimescaleDB den Bereich vor; das nächste Neuberechnen darüber bildet die Buckets ALLER Mandanten in diesem Bereich aus den Rohwerten neu.“ Gemessen: Mandant A bekam 2 Rohwerte in eine Stunde, in der A (6 Stichproben) und B (3 Stichproben, keine Rohwerte) direkt geschriebene Buckets hatten; nach dem Neuberechnen: A = Mittel der 2 Rohwerte (`sample_count` 2), B gelöscht. Ebenso für einen 300 Tage alten Bucket nach einem Rohwert-Insert und `refresh(NULL, NULL)`.
- Nie aufgefrischte Datenbank: Das erste `refresh(NULL, NULL)` löscht alle direkt geschriebenen Buckets (Wassermarke am Anfang).
- Die Policies decken nur 3 h bis 1 h (stündlich) und 3 d bis 1 d (täglich) ab; vorgemerkte Bereiche außerhalb bleiben liegen, bis jemand breiter auffrischt.

**Was aus der Messung folgt (Vorgaben der Hauptsitzung).**

1. Rohwerte älter als die Rohwert-Aufbewahrung der Zielinstallation werden nicht eingespielt (F-16 acceptance-2). Ihre Stunden- und Tageswerte kommen aus dem Archiv und werden hier direkt geschrieben.
2. Stunden- und Tageswerte werden direkt geschrieben (Betreiberentscheidung 2026-11-28). Innerhalb des Rohwert-Zeitraums stammen die Buckets des importierten Mandanten nach einem Neuberechnen aus seinen importierten Rohwerten; Gleichheit mit dem Archiv gibt es dort nur bei vollständigen Rohwerten, deshalb die Toleranz und die drei Fälle in acceptance-2.
3. Die Mandantentrennung ist nach Import und vollem Neuberechnen prüfbar (acceptance-3) und mit Vorgabe 1 erfüllbar; ohne sie nicht, wie die Messung zeigt.
4. Die Test-Fixture frischt vor dem Import einmal auf und hat Sensoren im Seed (Hooks).
5. Der Import schreibt gezielt in die über `resolve_aggregate_tables` ermittelten Tabellen, nicht über die Sicht.

**Schreiben in die Materialisierungstabellen (prior-art, proceed).** Established: `resolve_aggregate_tables` ermittelt Schema und Tabelle je Aggregat und wirft, wenn eine fehlt (`observation_repository.py:132-144`); die Löschung eines Mandanten schreibt dort bereits gezielt (`_purge_aggregates`, `:242-276`). Der Import nutzt dieselbe Auflösung.

**Kommentar zur Sicht (drift, proceed).** Established: Der Kommentar nennt das Aggregat eine nur lesbare Sicht, die ein `DELETE` ablehnt (`:121-123`). Gemessen wurde, dass ein `INSERT` über die Sicht angenommen wird. Der Kommentar spricht nur vom Löschen und ist damit nicht widerlegt; für den Import gilt trotzdem: Er schreibt in die ermittelten Tabellen, damit Schreiben und Löschen denselben Weg nehmen und das Layout an einer Stelle festgehalten ist (acceptance-4).

**Tageswerte aus Stundenwerten.** Established: `sensor_daily` wird aus `sensor_hourly` gebildet (`data_access/timescale/migrations/002_continuous_aggregates.sql:23-35`). Unestablished: wie ein Neuberechnen einen Tageswert bildet, dessen Stundenwerte teils direkt geschrieben, teils aus Rohwerten neu gebildet sind; gemessen wurden nur Stundenwerte. Der Hook zu acceptance-2 prüft die drei Fälle für beide Aggregate und klärt es.

**Spec schließt den Import aus (drift, proceed).** Established: REQ-056 §8.3 (`:365`) und AK-47 (`:683`); Runbook DE `:8`, `:26`, `:146`. acceptance-7 zieht nach; F-16 acceptance-8 trägt den Teil für die Rohwerte.

**Überschneidung mit F-16 (overlap, proceed).** Begründung für `proceed`: F-16 liest und prüft den Messwert-Teil, bildet die Sensor-Zuordnung, schreibt die Rohwerte und zählt im Bericht; F-34 schreibt mit derselben Zuordnung die Stunden- und Tageswerte und ergänzt den Bericht um ihre Zahlen. Die Regel „Sensor nicht im Archiv: auslassen und zählen“ gilt in beiden, je für die eigene Reihe. Der Rollback der Rohwerte ist F-16 acceptance-5, der der Buckets acceptance-5 hier; beide laufen über denselben bestehenden Pfad.

**Überschneidung mit F-17 (overlap, proceed).** Begründung für `proceed`: acceptance-6 benutzt Vorprüfung, Bestätigung, Zuordnung und Start aus F-17 als Weg, ohne sie zu ändern. Das ist eine Abhängigkeit in einer Richtung.

**Wertnachweis des Sprints.** `verifies_sprint_value: acceptance-6`. F-34 ist das letzte Feature der Kette; der Rundlauf geht durch alle sechs: Hintergrundprüfung und Größenpfad (F-15), Dokumentprüfung eines unveränderten Archivs (F-32), Vorprüfung, Zuordnung und Start (F-17), der Eintrag in der Liste (F-33), Rohwerte (F-16), Stunden- und Tageswerte (F-34). Die Größe von rund 500 MiB weist er nicht nach; dafür ist der Handlauf zu F-15 acceptance-1 verpflichtend.

**Ergebnis:** kein ungelöster Befund in den Kriterien; F-34 ist `ready`, vorbehaltlich des Agentenlaufs. Zwei Punkte sind nicht belegt und stehen unter „Offene Punkte“.

### Stand nach dem dritten Agentenlauf (2026-11-28)

Dritter Lauf des `feature-consistency-reviewer` (`feature-consistency-reviewer@unknown`) am 2026-11-28 gegen `b3c7f6eba`, von der Hauptsitzung gestartet; dazu weitere Messungen der Hauptsitzung gegen TimescaleDB und zwei Betreiberentscheidungen (D, E). Die Einarbeitung stammt vom Subagenten der Planungssitzung; die zitierten Stellen wurden nachgelesen, ein eigener Test lief nicht.

Die Abschnitte dieser Notizen oberhalb geben den Stand vor der Entscheidung D wieder („nichts neu berechnen“); geltend sind Beschreibung, Kriterien, Hooks und dieser Abschnitt.

**Weitere Messungen der Hauptsitzung gegen TimescaleDB 2.32.1-pg16**, 2026-11-28; Befehle sinngemäß, Ergebnisse wie übermittelt:

- **Ebene Stunden → Tage.** Auf einer einmal voll aufgefrischten Datenbank wurde für einen 900 Tage alten Tag ein Stundenwert von Mandant A direkt eingefügt, dazu direkte Tageswerte für A (avg 22, 40 Stichproben) und B (avg 11, 30 Stichproben; B ohne Stundenwerte). Nach `refresh_continuous_aggregate('sensor_daily', NULL, NULL)`: A = avg 20, 4 Stichproben (aus seinem Stundenwert neu gebildet), B gelöscht. Das direkte Einfügen eines Stundenwerts merkt den Tag also für die Tageswerte aller Mandanten vor.
- **Begrenztes Neuberechnen.** Auf einer frischen Datenbank mit direkten Buckets für A und B (300 Tage alt und 20 Tage alt): Rohwerte für A und B in die 20-Tage-Stunde eingefügt, dann `refresh_continuous_aggregate('sensor_hourly', <diese Stunde>, <+1 h>)` → A = 50/2, B = 12/3 (beide aus ihren Rohwerten), die 300 Tage alten Buckets beider unverändert. Ein begrenztes Neuberechnen über einen Bereich, in dem alle Mandanten ihre Rohwerte haben, ist für andere unschädlich.
- **Frische Installation.** Dieselbe Datenbank danach `refresh(NULL, NULL)` → die 300 Tage alten, direkt geschriebenen Stundenwerte beider Mandanten gelöscht (nie voll aufgefrischt, also gelten sie als nie materialisiert). Nicht gemessen: ob Policy-Läufe allein das auslösen (die Jobs 1000/1001 existieren; der Lauf per `run_job` gelang im Versuch nicht).

**Schichtung nach Aufbewahrungsfristen (Vorgabe der Hauptsitzung).** Established: Die Zielinstallation hält Rohwerte 90 Tage, Stundenwerte 2 Jahre, Tageswerte 5 Jahre (`data_access/timescale/migrations/003_retention_policies.sql:3`, `:6`, `:9`). Was älter ist als die Frist seiner Ebene, wird nicht eingespielt, sondern gezählt; die Fristen liest der Import aus den wirksamen Policies. Der Schnitt liegt jeweils auf einer Tagesgrenze mit Abstand zur Frist, damit kein halb gedeckter Bucket entsteht und ein gleichzeitiger Aufbewahrungslauf keine eben eingespielten Zeilen trifft. Daraus folgt: In jedem Zeitraum, den der Import neu berechnen lässt, haben alle Mandanten ihre Quelldaten noch (Rohwerte innerhalb der Rohwert-Frist, Stundenwerte innerhalb der Stundenwert-Frist); nach der Messung „Begrenztes Neuberechnen“ ist das für sie unschädlich.

**Ablauf des Imports (Betreiberentscheidung D, Vorgabe der Hauptsitzung).** Der Import schreibt die archivierten Stunden- und Tageswerte direkt und lässt dann gezielt neu berechnen: `sensor_hourly` über den eingespielten Rohwert-Zeitraum, danach `sensor_daily` über den eingespielten Stundenwert-Zeitraum, nichts darüber hinaus. Das Neuberechnen der Stundenwerte über den Rohwert-Zeitraum liefert schon F-16 (dort begründet); F-34 fügt das direkte Schreiben und das Neuberechnen der Tageswerte hinzu. Welche Werte danach woher stammen:

| Zeitraum | Stundenwerte | Tageswerte |
|---|---|---|
| ab dem Rohwert-Stichtag | aus den eingespielten Rohwerten (bis 1e-9) | aus den Stundenwerten (bis 1e-9) |
| davor, innerhalb der Stundenwert-Frist | direkt aus dem Archiv (genau) | aus den eingespielten Stundenwerten (bis 1e-9) |
| davor, innerhalb der Tageswert-Frist | nicht eingespielt, gezählt | direkt aus dem Archiv (genau) |
| älter | nicht eingespielt, gezählt | nicht eingespielt, gezählt |

Established für die zweite Spalte: Die Messung „Ebene Stunden → Tage“ zeigt, dass ein direkt eingefügter Stundenwert den Tag für die Tageswerte aller Mandanten vormerkt; deshalb das Neuberechnen der Tageswerte über genau diesen Zeitraum, in dem alle Mandanten ihre Stundenwerte noch haben. Unestablished: dass ein begrenztes Neuberechnen der Tageswerte für andere Mandanten ebenso unschädlich ist wie das gemessene der Stundenwerte; der Hook zu acceptance-3 prüft es.

- **Vormerkungen (drift, proceed).** Die Risikonotiz des vorigen Stands („besteht in dieser Form schon heute“) war falsch und ist ersetzt. Established durch die Messungen: Ohne Vormerkung lässt ein Neuberechnen direkt geschriebene Buckets unberührt. Vormerkungen entstehen heute durch das Löschen von Rohwerten (`delete_by_sensor`, `observation_repository.py:278`; `delete_by_tenant`, `:300`), also auch durch den Rollback eines gescheiterten Imports. acceptance-3 verlangt deshalb auch nach einem Rollback, dass ein volles Neuberechnen nichts ändert.
- **`materialized_only` (drift, proceed).** Gemessen ist `true`; die Migration setzt es nicht ausdrücklich (`002_continuous_aggregates.sql:3`, `:24`). Bei `false` gälte die Sichtbarkeit direkt geschriebener Werte nicht; acceptance-5 lehnt dann ab.
- **Frische Installation (drift, revisit-after Integrationstest).** acceptance-4 legt das Ergebnis fest; wie es erreicht wird, ist Sache der Umsetzung. Unestablished: das Verhalten der Policy-Läufe auf einer nie voll aufgefrischten Datenbank; der Hook zu acceptance-4 ist das Experiment.
- **Der offene Punkt „Vormerkungen nach dem Import abbauen?“** des vorigen Stands ist mit der Entscheidung D beantwortet.
- **Phase „Messwerte“.** Sie umfasst auch das Schreiben und Neuberechnen aus diesem Feature (F-16 acceptance-7); der Eintrag „nicht eingespielt“ für Stunden- und Tageswerte im Bericht aus F-16 acceptance-6 wird hier durch die Zahlen ersetzt.

**Ergebnis:** Die Kriterien entscheiden unter den Messungen eindeutig; offen ist als unbelegt nur das Policy-Verhalten auf einer frischen Installation, mit Test-Hook. F-34 ist `ready`, vorbehaltlich des nächsten Agentenlaufs. Sieben Kriterien.

## Risks

- **Frische Installation.** Auf einer nie voll aufgefrischten Zeitreihendatenbank löscht ein volles Neuberechnen direkt geschriebene Buckets (gemessen). Ob schon die Policy-Läufe das auslösen, ist nicht gemessen. acceptance-4 verlangt, dass die eingespielten Werte beides überstehen; bis der Test läuft, ist offen, mit welchem Mittel.
- **Neuberechnen der Tageswerte.** Es bildet die Tageswerte aller Mandanten im eingespielten Stundenwert-Zeitraum aus ihren Stundenwerten neu. Für Stundenwerte aus Rohwerten ist die Unschädlichkeit gemessen, für Tageswerte aus Stundenwerten hergeleitet; acceptance-3 prüft es.
- **Vormerkungen aus Löschungen.** Löscht jemand Rohwerte (Sensor, Mandant, Rollback), entsteht eine Vormerkung, die außerhalb der Policy-Fenster liegen bleibt. Für den Rollback des Imports räumt acceptance-3 sie ab; für das Löschen eines Sensors oder Mandanten außerhalb eines Imports ändert dieses Feature nichts.
- Das Schreiben in die Materialisierungstabellen stützt sich auf TimescaleDB-Interna; ein Upgrade kann es brechen. acceptance-5 macht daraus einen fehlgeschlagenen Import und einen roten Test statt stillen Datenverlusts.
- Ein langes Neuberechnen über bis zu zwei Jahre Stundenwerte verlängert den Lauf; das Lebenszeichen muss gesetzt werden (`tenant_export_service.py:168`).
- Was älter ist als die Aufbewahrungsfristen der Zielinstallation, kommt nicht zurück; der Bericht nennt die Zahl.

## References

- Issue #3140 (Rest von #2138, MT-042), roadmap item R-19
- `project/requirements/tenant-export-import-remainder.md` (R4, R9, R13 in der Fassung vom 2026-11-28)
- Setzt F-16 voraus (Messwert-Teil, Sensor-Zuordnung, Rohwerte samt Neuberechnen ihres Zeitraums, Bericht) und für acceptance-6 F-17; letztes Feature der Kette in Sprint 5

## Betreiberentscheidungen 2026-11-28

- **Archivierte Stunden- und Tageswerte werden direkt geschrieben, nichts wird neu berechnet** (ersetzt die Entscheidung vom 2026-11-17 zu R13).
- **Messwerte ohne zuordenbaren Sensor: auslassen und zählen**, auch Stunden- und Tageswerte (acceptance-1).
- **A — F-16 wird geteilt**; dieses Feature ist der Teil „Stunden- und Tageswerte“ und trägt den Wertnachweis des Sprints.
- **Der Handlauf mit rund 500 MiB (F-15 acceptance-1) ist verpflichtend**; acceptance-6 ersetzt ihn nicht.
- Vorgaben der Hauptsitzung nach der Messung gegen TimescaleDB: siehe Consistency notes, „Was aus der Messung folgt“.

Vierte Runde am selben Tag:

- **D — Der Import lässt am Ende gezielt neu berechnen**, genau die eingespielten Zeiträume, erst Stunden-, dann Tageswerte. Ersetzt „nichts neu berechnen“ (erster Punkt dieser Liste).
- **E — Sprintwert:** „samt Sensor-Historie im Rahmen der Aufbewahrungsfristen“; acceptance-6 folgt dem Wortlaut.
- Vorgaben der Hauptsitzung: Schichtung nach Aufbewahrungsfristen, Ablauf des Imports, frische Installation als eigenes Kriterium, `materialized_only` im Layout-Kriterium (Consistency notes, „Stand nach dem dritten Agentenlauf“).

## Offene Punkte (Stand 2026-11-28)

Keine offene Betreiberentscheidung blockiert F-34.

- **Policy-Verhalten auf einer frischen Installation** ist unbelegt und wird durch den Integrationstest zu acceptance-4 geklärt. Das Ergebnis bestimmt das Mittel (etwa ein einmaliges Auffrischen vor dem Schreiben) und den Runbook-Schritt in acceptance-7. Kein Blocker für den Start.
- **Lage der Schnitte** (Tagesgrenze, ein Tag Abstand) ist eine Festlegung der Planung auf Grundlage der Vorgabe „mit Abstand zur Frist“.
