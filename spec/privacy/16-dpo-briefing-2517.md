# SPEC-16 — Briefing für DSB / Rechtsberatung (#2517)

```
Paket: spec/privacy · Version 1.1 · 2026-11-22
Gemessen gegen: develop ef39d1f8e (2026-11-22; nach #2968 und den Datenschutzmigrationen v0109–v0111)
Zweck: Die in #2517 gesammelten Rechtsfragen als EIN Briefing (Betreiberentscheidung 2026-11-14, Pkt. 1).
Keine Rechtsberatung. #2517 bleibt offen, bis die Antwort vorliegt; jede Antwort wird als LEG-Entscheidung
in decision-log §B eingetragen (Status decided) und vom Betreiber durchgesetzt.
Änderungen 1.1 (Neumessung): §1 Routen korrigiert (`GET /care-events`, `GET /locations/{key}/history`) und
CSV-Download ergänzt; §2 Plan-Audit-Marker umgesetzt (v0109, DEC-16), `anon2_` weiterhin nicht gebaut, Frage 3
neu (LEG-15); §4 Schlüsselfelder aus v0111 ergänzt; §6 Dateiname wird bei Löschung geleert (v0109, PRIV-211).
§3 und §5: Ist-Stand unverändert, Belege ergänzt. Keine neue Frage aus #2517 oder den verknüpften Issues; keine neue LEG-Zeile.
```

## 0. Wie dieses Briefing zu lesen ist

Jede Frage aus #2517 ist genau einem oder mehreren Einträgen der Rechtsregistry (`decision-log.md` §B, LEG-nn)
zugeordnet. Die Registry trägt Optionen, Empfehlung, Gate und Durchsetzungspunkt; dieses Dokument ergänzt je
Frage den **Ist-Stand im Code** (gemessen, mit Datei), den **ausgelieferten Default** und die **konkrete Frage**,
die beantwortet werden muss. Quellenbelege (Wortlaut, URL, Prüfdatum) stehen im Rechtsevidenzregister `13`
(L-nn); was dort `UNVERIFIED_AT_SOURCE` ist, wird hier nicht als Rechtsaussage verwendet.

Drei Fragenkomplexe hatte die Registry noch nicht; sie sind mit diesem Dokument als **LEG-20**, **LEG-21** und
**LEG-22** angelegt (Beetfotos, §6).

| # | Komplex | Fragen aus #2517 | LEG |
|---|---------|------------------|-----|
| 1 | Sichtbarkeit der durchführenden Person im Pflegeprotokoll | Beschreibung Pkt. 1; Nachtrag 2026-11-07 Pkt. 2 | LEG-02, LEG-05 |
| 2 | Gelöschte Mitglieder im Pflegeprotokoll | Beschreibung Pkt. 2; Frage 3 aus LEG-15 (Plan-Audit-Marker, seit v1.1) | LEG-15, LEG-06 |
| 3 | Freitexte gelöschter Mitglieder | Beschreibung Pkt. 3–4; Kommentar 2026-10-20 (`bed_templates.name`) | LEG-08 |
| 4 | Zweckänderung durch das M4-Backfill; `pest_control` bei Mandantenlöschung | Nachtrag 2026-11-07 Pkt. 1, 4, 5 | LEG-07 |
| 5 | Gerätespeicher (Offline) | Kommentar 2026-11-09 Pkt. 1–5 | LEG-09, LEG-10, LEG-12 |
| 6 | Beetfotos und Plan-Unterlagen | aus #2643 verschoben (2026-11-14) Pkt. 1–3 | **LEG-20, LEG-21, LEG-22** |

## 1. Sichtbarkeit der durchführenden Person (LEG-02, LEG-05)

**Ist-Stand.** Jedes Pflegeereignis trägt `performed_by_user_key`; die ungefilterte Liste des Mandanten
(`GET /care-events`, optional `?location_key=`, `api/v1/care_events/tenant_router.py:45`) und die Beet-Historie
(`GET /locations/{key}/history`, `api/v1/locations/tenant_router.py:818`) zeigen jedem Mitglied den Anzeigenamen
der durchführenden Person (nie den Kontoschlüssel). Dieselbe Liste lädt jedes Mitglied mit `format=csv` als Datei
mit bis zu 50 000 Zeilen herunter, Spalten `performed_by` und `performed_for` eingeschlossen
(`domain/engines/care_event_csv_engine.py:22`). Der Personenfilter ist eingeschränkt (SR-020/E-16,
`check_performed_by_filter`, `domain/services/care_event_service.py:151`), das Datum nicht: die Einschränkung
entfernt die Abkürzung, nicht die Daten (`05` §1).
Seit 2026-11-14 gilt für eine Pflege-Bestätigung **eine Regel: immer die aufrufende Person** — REST,
Benachrichtigung, Aufgabenwarteschlange (`care_reminder_service.record_care_task_completion`,
`domain/services/care_reminder_service.py:1290`, Aufrufer `TaskService`, `task_service.py:1853`; #2961/#2968, seit
#2968 auf jedem abschließenden oder überspringenden Weg) und MCP (`mcp_server/tools/care.py:84`,
`ctx.principal.account_key`). Die Bestätigung selbst hat keine eigene Aufbewahrung; die 5 Jahre gelten für das
abgeleitete Pflegeereignis (R-25, `retention_care_event_retention_years = 5`, `config/settings.py:125`;
Widerspruch W-19 in `14` aufgelöst).

**Ausgelieferter Default.** Sichtbar für alle Mitglieder; Einstellung `attribution_visibility` je Mandantenklasse
ist spezifiziert (DEC-10, DA-04), nicht gebaut.

**Fragen.**
1. Trägt Art. 6 Abs. 1 lit. f (berechtigtes Interesse der Gruppe an nachvollziehbarer Pflege) die Sichtbarkeit
   der durchführenden Person für **alle** Mitglieder, oder nur für Leitung + die Person selbst (LEG-02, LIA-1)?
2. In gewerblichen Mandanten ist „wer hat bestätigt“ ein Aufzeichnen von Beschäftigtentätigkeit, 5 Jahre lang
   je Person filterbar (Leitung/`management`). Braucht das eine Grundlage nach § 26 BDSG / Art. 88 DSGVO
   (nach EuGH C-34/21, L-09/L-10) und eine Mitbestimmung nach § 87 Abs. 1 Nr. 6 BetrVG? Welche Pflichten hat die
   Plattform gegenüber dem Arbeitgeber-Mandanten (LEG-05)?
3. Bestätigt die DSB die Regel „immer die aufrufende Person“ (DEC-09)? Die Sichtbarkeitsentscheidung (Frage 1)
   ändert nur, wer es sieht, nicht, was gespeichert wird.

## 2. Gelöschte Mitglieder (LEG-15, LEG-06)

**Ist-Stand.** Bei Kontolöschung erhalten die fünf Kontoverweise eines Pflegeereignisses (`performed_by_user_key`,
`performed_for_user_key`, `created_by`, `voided_by`, `redacted_by`) den Sammelmarker `_anonymized`
(`domain/engines/erasure_engine.py:162–235`), der **alle** gelöschten Mitglieder eines Mandanten bündelt; ein
Filter auf `_anonymized` wird mit 422 abgewiesen (`care_event_service.py:164`, `04` §2). Ein Pseudonym
(Tombstone `anon_<16 hex>`, instanzweit, `ErasureEngine.compute_tombstone_hash`, `erasure_engine.py:1236`) erhalten
die Pflichtaufzeichnungen, darunter `treatment_applications.applied_by_key` und `harvest_batches.harvested_by_key`
(`erasure_engine.py:84`, `:109`).
Seit 2026-11-15 (Betreiberfreigabe DEC-16/DEC-28) gilt: Das Plan-Audit `garden_plan_audit.user_key` erhält bei
Löschung den Marker statt des Pseudonyms (`erasure_engine.py:269`). Migration `v0109_privacy_tombstone_copies`
setzt davor geschriebene Pseudonyme dort und ins Pflegeprotokoll kopierte Pseudonyme
(`care_events.performed_by_user_key`, `created_by`) auf den Marker; Pseudonyme in übrigen Feldern außerhalb der
Allowlist zählt sie nur, ohne sie zu ändern, und der nur lesende Beat `privacy.consistency` zählt sie seither
täglich (`migrations/versions/v0109_privacy_tombstone_copies.py`, Schritte 1–3; `09` §3).
**Nicht gebaut** ist das mandantengebundene Pseudonym `anon2_` für neue Zeilen (DEC-25, PRIV-238): Die Leser
erkennen die Form (`domain/models/privacy.py:25`), kein Pfad schreibt sie.

**Fragen.**
1. Ist ein deterministisches, mandantengebundenes Pseudonym über 5 Jahre (Art.-15-Suche nach der eigenen
   Person bleibt möglich) verhältnismäßig, oder muss es zufällig sein (LEG-15, L-14/L-15)?
2. Ab welcher Frist nach Ende der Mitgliedschaft wird der Anzeigename ehemaliger Mitglieder unterdrückt
   (Vorschlag 90 Tage, LEG-06 a)?
3. Bestätigt die DSB, dass das Plan-Audit nach der Löschung niemanden mehr verknüpft (Marker statt Pseudonym,
   umgesetzt), obwohl die Zeile als Nachweis einer Planlöschung 365 Tage bleibt (R-26)? Die Änderung ist
   einschränkend; die Frage hält nur fest, dass LEG-15 diesen Teil mit abdeckt.

## 3. Freitexte gelöschter Mitglieder (LEG-08)

**Ist-Stand.** Freitexte bleiben nach der Löschung im gemeinsamen Mandanten; die Leitung schwärzt reaktiv
(`POST /care-events/{key}/redact`, `api/v1/care_events/tenant_router.py:231`, GP-FR-109) und erhält **keine
Liste** der betroffenen Zeilen. Die Schwärzung ersetzt `FREE_TEXT_FIELDS = (summary, reason, observed_outcome,
product_label, performed_by_label)` (`domain/models/care_event.py:83`) — **`care_events.material` (bis 200 Zeichen,
`care_event.py:304`) gehört nicht dazu** und steht in der CSV-Datei (§1). Ebenfalls Freitext mit möglichem
Personenbezug: `bed_templates.name` (z. B. „Omas Hochbeet“, bis 200 Zeichen, `domain/models/bed_template.py:128`);
er bleibt nach Löschung der Urheberin im Mandanten (nur `created_by` wird Marker), wird beim Platzieren in
`Location.name` kopiert (`domain/services/garden_plan_service.py:771`) und landet in `garden_plan_audit`.
Spezifiziert ist eine Prüfwarteschlange mit vollständiger Entdeckung (DEC-06/DEC-27), nicht gebaut; der Schalter
`PRIVACY_REVIEW_AUTO_REDACT_ON_SLA` existiert im Code nicht.

**Fragen.**
1. Genügt „behalten + Prüfung durch die Leitung“ (Art. 17 Abs. 3, Abwägung nach Art. 6 Abs. 1 lit. f), oder
   müssen Freitexte gelöschter Mitglieder automatisch geschwärzt werden?
2. Dürfen Leads über die Schwärzung entscheiden, ist eine Frist von 30 Tagen angemessen, und soll nach Ablauf
   automatisch geschwärzt werden (Schalter `PRIVACY_REVIEW_AUTO_REDACT_ON_SLA`, Default aus)?
3. Gilt dieselbe Abwägung für `bed_templates.name` / den kopierten Beetnamen und für `care_events.material`, oder
   müssen beide in den Schwärzungsumfang?

## 4. Zweckänderung durch das M4-Backfill; `pest_control` bei Mandantenlöschung (LEG-07)

**Ist-Stand.** Das Backfill v0104 (`domain/engines/care_event_backfill_mapper.py:74–75`, `account_of` `:183`)
kopiert `applied_by_key` / `harvested_by_key` aus Aufzeichnungen nach Art. 6 Abs. 1 lit. c (PflSchG § 11, KCanG;
NFR-011 R-16/R-17) ins Pflegeprotokoll, wo sie der Beet-Historie und dem Personenfilter dienen; der tägliche Job
`care_events.consistency` nutzt denselben Mapper. Die Kopie läuft bereits; ein Schalter
`PRIVACY_BACKFILL_COPIES_PERFORMER` ist spezifiziert (E01), im Code nicht vorhanden. Bewässerungs-/Düngeereignisse
werden ohne Kontoverweis kopiert (Personenbezug nur über den Mandanten). Seit v0111 (2026-11-15) tragen
`watering_events`, `watering_logs`, `tank_fill_events` und `maintenance_logs` ein Feld `performed_by_user_key`
neben dem Freitext `performed_by`; kein Pfad stempelt es, jeder Wert ist `null`, und der Mapper liest es nicht
(`09` §5, `08` §3.4). Bei Mandantenlöschung werden die Pflegeprotokollzeilen gelöscht, `pest_control`/`ipm`
eingeschlossen; der § 11-Nachweis ist die pseudonymisiert aufbewahrte `treatment_applications`-Zeile
(`domain/engines/tenant_erasure_engine.py:113–117`).

**Fragen.**
1. Ist die Weiterverarbeitung der kopierten durchführenden Person mit dem ursprünglichen Zweck vereinbar
   (Art. 5 Abs. 1 lit. b, Art. 6 Abs. 4), und decken Datenschutzhinweis und Verzeichnis sie ab?
2. Gering: Gilt dasselbe für die kopierten Bewässerungs-/Düngeereignisse ohne Kontoverweis, und auch dann, wenn
   die neuen Schlüsselfelder (v0111) später gestempelt werden (E13)?
3. Ist das Löschen der `pest_control`-Zeilen bei Mandantenlöschung haltbar, solange `treatment_applications` der
   einzige § 11-Nachweis bleibt?

## 5. Gerätespeicher (LEG-09, LEG-10, LEG-12)

**Ist-Stand.** IndexedDB `kp-plan-cache`, `kp-write-queue` und Cache Storage `kp:{user}:{tenant}`, `kp-sw-state`
sowie App-Shell-Caches (`src/frontend/src/pwa/storageWipe.ts:13`, `:23`; `src/frontend/src/sw.ts:57`); der
Schreibpuffer hält offene Einträge 365 Tage, fehlgeschlagene/kollidierende 90 Tage
(`src/frontend/src/features/gardenPlanner/offline/queue.ts:450`). `07` schlägt Opt-in für alle (DEC-29),
Quarantäne 14 Tage, Fristen 90/30 Tage und einen Shared-Device-Modus vor (DEC-12); gebaut ist der Bestand, seit
v1.0 dieses Briefings unverändert.

**Fragen** (je Speicherkategorie, `07` §2):
1. Ist die Speicherung „unbedingt erforderlich“ nach § 25 Abs. 2 Nr. 2 TDDDG (vom Nutzer gewünschte
   Offline-Funktion), und genügt ein Opt-in-Schalter als „ausdrücklich gewünscht“ (LEG-09, L-11)?
2. Sind 365/90 Tage angemessen, insbesondere auf geteilten Geräten in Gemeinschaftsgärten; soll der Betreiber
   kürzere Fristen setzen können (LEG-10)?
3. Art. 17: Genügt es, die Lücke zu dokumentieren (ein auf Gerät A gelöschtes Konto lässt gepufferte Einträge auf
   Gerät B bis Fristablauf), oder ist die Quarantäne beim nächsten Online-Kontakt nötig (LEG-10)?
4. Braucht das Verzeichnis einen Eintrag „Speicherung auf dem Endgerät“, und berührt das die DSFA (LEG-12)?
5. Geteiltes Gerät, gleiches Browserprofil: Einträge sind mit Entwicklerwerkzeugen lesbar. Genügt ein
   dokumentierter Hinweis „immer ausdrücklich abmelden“, oder ist Löschen am Sitzungsende nötig (LEG-10)?

## 6. Beetfotos und Plan-Unterlagen (LEG-20, LEG-21, LEG-22 — neu)

**Ist-Stand.** Beetfotos (Kategorie `location`) und Plan-Unterlagen (`garden_plan_underlay`) liegen im
Löschumfang `user_diary_attachments` (`erasure_engine.STORAGE_CLEANUP_RULES`, `erasure_engine.py:491`;
Kategorienliste `data_access/storage/local_fs_adapter.py:567`): bei Kontolöschung bleibt die Datei für die übrigen
Mitglieder, `created_by` wird `_anonymized`, EXIF wird entfernt. Seit v0109 (2026-11-15, PRIV-211) leert derselbe
Schreibvorgang auch den ursprünglichen Dateinamen `original_filename`, der oft den Namen der Besitzerin trägt
(`data_access/arango/attachment_repository.py:416–427`); v0109 hat das für bereits anonymisierte Zeilen
nachgeholt. Die Regel begründet das Behalten mit NFR-011 R-16/R-17/R-18 (CanG/PflSchG) — nach Einschätzung des
Betreibers trifft das für Gartenfotos nicht zu; welche Grundlage trägt, ist Frage LEG-20 unten. Der Umfang `user_personal` (Löschen) ist heute leer.
Der Art.-15/20-Export enthält Metadaten und Verweise (eigener persönlicher Mandant: `domain/engines/data_export_engine.py:805`; Fotos aus einem gemeinsamen Mandanten über die `created_by`-Quelle: `data_export_engine.py:502`), die Bilddateien
sind „in der App verfügbar“. Das Foto eines anderen oder gelöschten Mitglieds entfernen kann nur die Leitung
(`domain/services/location_photo_service.py:251`); eine abgebildete Person ohne Konto hat keinen eigenen Weg.

**Fragen.**
1. **LEG-20 (Art. 17):** Genügt Art. 6 Abs. 1 lit. f, um die Beetfotos einer gelöschten Person im gemeinsamen
   Garten zu behalten (das Foto kann die Person oder ihr Zuhause zeigen), oder müssen die eigenen Beetfotos
   gelöscht werden (Umfang `user_personal`)? Ausgeliefert: anonymisieren.
2. **LEG-21 (Art. 15 Abs. 3, Art. 20):** Erfüllt ein Export mit Metadaten und Verweisen das Recht auf Kopie und
   Datenübertragbarkeit, oder müssen die Bilddateien in den Export? Wie übt eine abgebildete Person ohne Konto
   Art. 15/17 aus (heute nur über die Leitung)?
3. **LEG-22 (Art. 30, Art. 13):** Sollen Beetfotos eine eigene Kategorie im Verzeichnis und im
   Datenschutzhinweis sein?

## 7. Was mit der Antwort geschieht

| Antwort | Durchsetzung |
|---------|--------------|
| je Frage | LEG-Zeile in `decision-log.md` §B auf `decided` mit Datum und Quelle der Entscheidung |
| einschränkend (weniger sichtbar, kürzere Frist, mehr löschen) | sofort umsetzbar (`processing_allowed: ja`), Epic laut `12` |
| ausweitend (mehr Verarbeitung) | erst nach registrierter Entscheidung, hinter Schalter (`08` §8a) |
| Beetfotos löschen statt anonymisieren (LEG-20 B) | Wechsel der Kategorien `location`/`garden_plan_underlay` von `user_diary_attachments` nach `user_personal` in `erasure_engine` und `local_fs_adapter._erasure_scope_categories` |
