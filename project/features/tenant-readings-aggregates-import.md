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
  agent_version: manual-2026-11-28
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
---

## Description

Nach F-16 stellt der Import die Rohwerte der Sensoren wieder her, aber nicht
die Stunden- und Tageswerte. Die Diagramme eines wiederhergestellten Gartens
zeigen deshalb nur die letzten Wochen; die Stundenwerte (bis zwei Jahre) und
Tageswerte (bis fünf Jahre) aus dem Archiv fehlen.

Nach dieser Änderung stellt der Import auch die Stunden- und Tageswerte
wieder her, sodass die Diagramme den Verlauf zeigen wie vor dem Export. Der
Import schreibt die archivierten Werte unverändert und berechnet keinen neu;
die Messwerte anderer Gärten bleiben dabei unberührt, auch wenn das Archiv
weiter zurückreicht als die Aufbewahrung der Rohwerte. Damit ist ein Garten
aus seinem Archiv vollständig wiederherstellbar.

## Acceptance criteria

- [ ] **acceptance-1** Unmittelbar nach dem Import liefert die Messwert-Abfrage des neuen Mandanten für jeden Stunden- und Tageswert des Archivs genau den archivierten Wert, auch für Zeiträume ohne Rohwerte; Stunden- und Tageswerte eines Sensors, der nicht im Archiv steht, werden nicht geschrieben, und der Importbericht nennt die Zahl der importierten und der ausgelassenen Werte.
- [ ] **acceptance-2** Nach einem Neuberechnen der Aggregate über den ganzen Zeitraum tragen die Stunden- und Tageswerte des neuen Mandanten außerhalb des importierten Rohwert-Zeitraums unverändert den archivierten Wert; im Rohwert-Zeitraum tragen sie ihn mit einer relativen Abweichung von höchstens 1e-9, wenn die Rohwerte des Zeitabschnitts vollständig importiert wurden, und sonst (am Rand des Rohwert-Zeitraums) den Wert aus den vorhandenen Rohwerten.
- [ ] **acceptance-3** Nach dem Import und einem anschließenden Neuberechnen beider Aggregate über den ganzen Zeitraum ist kein Rohwert und kein Stunden- oder Tageswert eines anderen Mandanten verändert, auch nicht bei einem Mandanten, der nur noch Stunden- und Tageswerte älter als die Rohwert-Aufbewahrung hat.
- [ ] **acceptance-4** Passt das Tabellenlayout der Stunden- und Tageswerte nicht zu dem, was der Import erwartet (etwa nach einem TimescaleDB-Upgrade), endet der Import als fehlgeschlagen, bevor ein Messwert geschrieben ist, und der Garten wird zurückgerollt.
- [ ] **acceptance-5** Ein Import, der nach dem Schreiben von Stunden- und Tageswerten fehlschlägt, hinterlässt keinen Stunden- oder Tageswert des neuen Mandanten.
- [ ] **acceptance-6** Ein Garten mit Datensätzen, Fotos, Mitgliedern, Sensoren und Messwerten wird exportiert, das Archiv hochgeladen, vorgeprüft, die Mitglieder per E-Mail zugeordnet und aus der Vorprüfung importiert; ein erneuter Export des neuen Gartens enthält bis auf Schlüssel, Importzeitpunkt und Instanz-ID dieselben Daten einschließlich aller Rohwerte innerhalb der Aufbewahrungsfrist und aller Stunden- und Tageswerte.
- [ ] **acceptance-7** REQ-056 §8.3, §8.4, AK-47 und ein neues Abnahmekriterium in §16.4 sowie das Runbook (DE + EN) beschreiben den Import der Stunden- und Tageswerte, dass sie direkt geschrieben werden, und warnen davor, die Aggregate nach einem Import von Hand über einen breiten Zeitraum neu zu berechnen.

## Test hooks

- **acceptance-1** — `src/backend/tests/integration/test_tenant_export_readings_timescale.py` (Timescale service of `.github/workflows/backend-guards.yml`): the aggregates are refreshed once before the import (as the fixture does, `:86-87`; on a never-refreshed database the first full refresh deletes directly written buckets, measured 2026-11-28); the seed has sensor documents; after the import, with no refresh, `query_hourly` / `query_daily` (`observation_repository.py:196-228`) return every archived bucket with exactly the archived `avg_value`, `min_value`, `max_value`, `sample_count`, including buckets older than the raw retention; buckets of an unknown `sensor_key` are skipped and counted; the import issues no `refresh_continuous_aggregate` — pending
- **acceptance-2** — same module: after `CALL refresh_continuous_aggregate('sensor_hourly', NULL, NULL)` and `('sensor_daily', NULL, NULL)` the test distinguishes three cases by construction of the seed: (a) a bucket older than the raw retention (no raw imported) equals the archive exactly; (b) an hour with all its raw rows imported equals the archive within 1e-9 relative and has the archived `sample_count`; (c) an hour at the edge of the raw period, for which only part of the raw rows was imported, carries the average and `sample_count` of the raw rows present (measured: 2 raw rows replace a bucket of 6 samples) — pending
- **acceptance-3** — same module: a second tenant has raw rows inside the retention, and hourly and daily buckets older than the retention written directly into the materialisation tables with no raw rows; an archive of the first tenant reaching back beyond the retention is imported; after a full refresh of both aggregates every raw row and bucket of the second tenant is unchanged (REQ-056 AK-33). Control: with raw rows older than the retention written for the first tenant, the same refresh deletes the second tenant's old buckets (measured 2026-11-28), which is why F-16 acceptance-2 does not import them — pending
- **acceptance-4** — same module: layout pin on `resolve_aggregate_tables()` (`observation_repository.py:132-144`) and the written columns (`bucket, tenant_key, sensor_key, sensor_type, avg_value, min_value, max_value, sample_count`); a missing or changed materialisation table ends the import `failed` with no reading written and the tenant rolled back — pending
- **acceptance-5** — same module: induced failure after the buckets were written → zero buckets of the new tenant in both materialisation tables (rollback through `erase_abandoned_import` → `_purge_aggregates`, `observation_repository.py:242-276`) — pending
- **acceptance-6** — same module, extending `test_the_archive_carries_the_tenants_readings_and_an_import_lists_but_skips_them` (`:151`): export → upload → pre-check → e-mail mapping → start from the pre-check → re-export, empty difference including `timeseries/readings.csv` (sensor keys compared through the key mapping; raw rows of the seed lie inside the retention). Needs two ArangoDB databases, as the module provisions (`SOURCE_DB`, `TARGET_DB`, `:50-51`), because an import next to the original fails on own species (runbook `docs/de/deployment/tenant-export-import.md:136-137`); the source photos carry no EXIF block, because the import stores stripped bodies (`_with_stored_bodies`, `tenant_export_service.py:1286-1312`); the seed has sensor documents; the target's aggregates are refreshed once before the import — pending
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

**Spec schließt den Import aus (drift, proceed).** Established: REQ-056 §8.3 (`:365`) und AK-47 (`:683`); Runbook DE `:8`, `:26`, `:146`. acceptance-7 zieht nach; F-16 acceptance-7 trägt den Teil für die Rohwerte.

**Überschneidung mit F-16 (overlap, proceed).** Begründung für `proceed`: F-16 liest und prüft den Messwert-Teil, bildet die Sensor-Zuordnung, schreibt die Rohwerte und zählt im Bericht; F-34 schreibt mit derselben Zuordnung die Stunden- und Tageswerte und ergänzt den Bericht um ihre Zahlen. Die Regel „Sensor nicht im Archiv: auslassen und zählen“ gilt in beiden, je für die eigene Reihe. Der Rollback der Rohwerte ist F-16 acceptance-4, der der Buckets acceptance-5 hier; beide laufen über denselben bestehenden Pfad.

**Überschneidung mit F-17 (overlap, proceed).** Begründung für `proceed`: acceptance-6 benutzt Vorprüfung, Bestätigung, Zuordnung und Start aus F-17 als Weg, ohne sie zu ändern. Das ist eine Abhängigkeit in einer Richtung.

**Wertnachweis des Sprints.** `verifies_sprint_value: acceptance-6`. F-34 ist das letzte Feature der Kette; der Rundlauf geht durch alle sechs: Hintergrundprüfung und Größenpfad (F-15), Dokumentprüfung eines unveränderten Archivs (F-32), Vorprüfung, Zuordnung und Start (F-17), der Eintrag in der Liste (F-33), Rohwerte (F-16), Stunden- und Tageswerte (F-34). Die Größe von rund 500 MiB weist er nicht nach; dafür ist der Handlauf zu F-15 acceptance-1 verpflichtend.

**Ergebnis:** kein ungelöster Befund in den Kriterien; F-34 ist `ready`, vorbehaltlich des Agentenlaufs. Zwei Punkte sind nicht belegt und stehen unter „Offene Punkte“.

## Risks

- **Liegen gebliebene Vormerkungen.** Die importierten Rohwerte merken ihren Zeitbereich vor; die Policies arbeiten nur die letzten Stunden bzw. Tage ab (gemessen). Laufen diese Rohwerte später bei allen Mandanten ab und berechnet danach jemand die Aggregate von Hand über einen breiten Zeitraum neu, werden die Stunden- und Tageswerte aller Mandanten in diesem Bereich aus nicht mehr vorhandenen Rohwerten neu gebildet, also gelöscht. Das ist aus der Messung hergeleitet, nicht selbst gemessen; die Gefahr besteht in dieser Form schon heute (`observation_repository.py:245-251`), der Import vergrößert den betroffenen Bereich auf bis zu 90 Tage. acceptance-3 prüft das Neuberechnen unmittelbar nach dem Import, nicht Monate später; das Runbook warnt (acceptance-7).
- **Frische Installation.** Auf einer nie aufgefrischten Zeitreihendatenbank löscht das erste volle Neuberechnen alle direkt geschriebenen Buckets (gemessen). Eine Wiederherstellung in eine neu aufgesetzte Installation ist genau dieser Fall, falls dort je ein volles Neuberechnen läuft.
- Das Schreiben in die Materialisierungstabellen stützt sich auf TimescaleDB-Interna; ein Upgrade kann es brechen. acceptance-4 macht daraus einen fehlgeschlagenen Import und einen roten Test statt stillen Datenverlusts.
- Am Rand des Rohwert-Zeitraums weichen Stundenwerte nach einem Neuberechnen vom Archiv ab (acceptance-2, Fall c); der Verlauf zeigt dort einen Wert aus weniger Stichproben.
- Aufbewahrungsfristen gelten weiter: Importierte Stundenwerte älter als 2 Jahre und Tageswerte älter als 5 Jahre entfernt die nächste Aufbewahrungs-Policy (`data_access/timescale/migrations/003_retention_policies.sql`).

## References

- Issue #3140 (Rest von #2138, MT-042), roadmap item R-19
- `project/requirements/tenant-export-import-remainder.md` (R4, R9, R13 in der Fassung vom 2026-11-28)
- Setzt F-16 voraus (Messwert-Teil, Sensor-Zuordnung, Bericht) und für acceptance-6 F-17; letztes Feature der Kette in Sprint 5

## Betreiberentscheidungen 2026-11-28

- **Archivierte Stunden- und Tageswerte werden direkt geschrieben, nichts wird neu berechnet** (ersetzt die Entscheidung vom 2026-11-17 zu R13).
- **Messwerte ohne zuordenbaren Sensor: auslassen und zählen**, auch Stunden- und Tageswerte (acceptance-1).
- **A — F-16 wird geteilt**; dieses Feature ist der Teil „Stunden- und Tageswerte“ und trägt den Wertnachweis des Sprints.
- **Der Handlauf mit rund 500 MiB (F-15 acceptance-1) ist verpflichtend**; acceptance-6 ersetzt ihn nicht.
- Vorgaben der Hauptsitzung nach der Messung gegen TimescaleDB: siehe Consistency notes, „Was aus der Messung folgt“.

## Offene Punkte (Stand 2026-11-28)

Keine offene Betreiberentscheidung blockiert die Kriterien von F-34. Zwei Punkte sollte der Betreiber vor dem Start von F-34 kennen:

- **Vormerkungen nach dem Import abbauen?** Mit der Vorgabe „keine Rohwerte älter als die Aufbewahrung“ wäre ein Neuberechnen genau über den importierten Rohwert-Zeitraum direkt nach dem Import für andere Mandanten unschädlich (das prüft acceptance-3) und würde die Vormerkungen abbauen, die sonst liegen bleiben (erstes Risiko). Entschieden ist „nichts neu berechnen“; der Grund dieser Entscheidung, Archive, die weiter zurückreichen als die Rohwerte, trifft den Rohwert-Zeitraum seit der Vorgabe nicht mehr. Unbelegt ist, ob liegen gebliebene Vormerkungen später tatsächlich schaden; das zeigte ein Versuch mit zeitversetzten Daten (nicht durchgeführt). Empfehlung der Planung: Der Betreiber entscheidet, ob der Import am Ende genau diesen Zeitraum neu berechnet. Das änderte acceptance-1 (kein Neuberechnen durch den Import) und acceptance-2 (Fall c träte sofort ein).
- **Wiederherstellung in eine frische Installation.** Ob dort vor dem Import einmal aufgefrischt werden muss, damit ein späteres volles Neuberechnen die importierten Werte nicht löscht, ist nur für das volle Neuberechnen gemessen, nicht für die Policy-Läufe. Der Hook zu acceptance-1 hält die Bedingung für den Test fest; für den Betrieb fehlt die Aussage.
