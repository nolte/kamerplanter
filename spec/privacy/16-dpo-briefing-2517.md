# SPEC-16 — Briefing für DSB / Rechtsberatung (#2517)

```
Paket: spec/privacy · Version 1.0 · 2026-11-14
Gemessen gegen: develop ff18c1574 (nach #2961, #2966, #2967); #2968 (Batch-Abschluss) offen
Zweck: Die in #2517 gesammelten Rechtsfragen als EIN Briefing (Betreiberentscheidung 2026-11-14, Pkt. 1).
Keine Rechtsberatung. #2517 bleibt offen, bis die Antwort vorliegt; jede Antwort wird als LEG-Entscheidung
in decision-log §B eingetragen (Status decided) und vom Betreiber durchgesetzt.
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
| 2 | Gelöschte Mitglieder im Pflegeprotokoll | Beschreibung Pkt. 2 | LEG-15, LEG-06 |
| 3 | Freitexte gelöschter Mitglieder | Beschreibung Pkt. 3–4; Kommentar 2026-10-20 (`bed_templates.name`) | LEG-08 |
| 4 | Zweckänderung durch das M4-Backfill; `pest_control` bei Mandantenlöschung | Nachtrag 2026-11-07 Pkt. 1, 4, 5 | LEG-07 |
| 5 | Gerätespeicher (Offline) | Kommentar 2026-11-09 Pkt. 1–5 | LEG-09, LEG-10, LEG-12 |
| 6 | Beetfotos und Plan-Unterlagen | aus #2643 verschoben (2026-11-14) Pkt. 1–3 | **LEG-20, LEG-21, LEG-22** |

## 1. Sichtbarkeit der durchführenden Person (LEG-02, LEG-05)

**Ist-Stand.** Jedes Pflegeereignis trägt `performed_by_user_key`; die ungefilterte Liste
(`GET /locations/{key}/care-events`) zeigt es jedem Mitglied des Mandanten. Der Personenfilter ist eingeschränkt
(SR-020/E-16), das Datum nicht: die Einschränkung entfernt die Abkürzung, nicht die Daten (`05` §1).
Seit 2026-11-14 gilt für eine Pflege-Bestätigung **eine Regel: immer die aufrufende Person** — REST,
Benachrichtigung, Aufgabenwarteschlange (`care_reminder_service.record_care_task_completion`, Aufrufer
`TaskService`, #2961/#2968) und MCP (`mcp_server/tools/care.py`, `ctx.principal.account_key`). Die Bestätigung
selbst hat keine eigene Aufbewahrung; die 5 Jahre gelten für das abgeleitete Pflegeereignis (R-25; Widerspruch
W-19 in `14` aufgelöst).

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

**Ist-Stand.** Bei Kontolöschung werden Verweise auf die Person durch ein Pseudonym ersetzt; Altbestand trägt den
Sammelmarker `_anonymized`, der **alle** gelöschten Mitglieder eines Mandanten bündelt; ein Filter auf
`_anonymized` wird abgewiesen (`04` §2). Neue Zeilen sollen ein mandantengebundenes Pseudonym erhalten (DEC-25)
und das Plan-Audit einen Marker (DEC-16) — spezifiziert, nicht gebaut (Migrationen v0109–v0111, `09`).

**Fragen.**
1. Ist ein deterministisches, mandantengebundenes Pseudonym über 5 Jahre (Art.-15-Suche nach der eigenen
   Person bleibt möglich) verhältnismäßig, oder muss es zufällig sein (LEG-15, L-14/L-15)?
2. Ab welcher Frist nach Ende der Mitgliedschaft wird der Anzeigename ehemaliger Mitglieder unterdrückt
   (Vorschlag 90 Tage, LEG-06 a)?

## 3. Freitexte gelöschter Mitglieder (LEG-08)

**Ist-Stand.** Freitexte bleiben nach der Löschung im gemeinsamen Mandanten; die Leitung schwärzt reaktiv
(`POST /care-events/{key}/redact`, GP-FR-109) und erhält **keine Liste** der betroffenen Zeilen. Die Schwärzung
ersetzt `FREE_TEXT_FIELDS = (summary, reason, observed_outcome, product_label, performed_by_label)`
(`domain/models/care_event.py`) — **`care_events.material` gehört nicht dazu**. Ebenfalls Freitext mit möglichem
Personenbezug: `bed_templates.name` (z. B. „Omas Hochbeet“, bis 200 Zeichen); er bleibt nach Löschung der
Urheberin im Mandanten, wird beim Platzieren in `Location.name` kopiert und landet in `garden_plan_audit`.
Spezifiziert ist eine Prüfwarteschlange mit vollständiger Entdeckung (DEC-06/DEC-27), nicht gebaut.

**Fragen.**
1. Genügt „behalten + Prüfung durch die Leitung“ (Art. 17 Abs. 3, Abwägung nach Art. 6 Abs. 1 lit. f), oder
   müssen Freitexte gelöschter Mitglieder automatisch geschwärzt werden?
2. Dürfen Leads über die Schwärzung entscheiden, ist eine Frist von 30 Tagen angemessen, und soll nach Ablauf
   automatisch geschwärzt werden (Schalter `PRIVACY_REVIEW_AUTO_REDACT_ON_SLA`, Default aus)?
3. Gilt dieselbe Abwägung für `bed_templates.name` / den kopierten Beetnamen und für `care_events.material`, oder
   müssen beide in den Schwärzungsumfang?

## 4. Zweckänderung durch das M4-Backfill; `pest_control` bei Mandantenlöschung (LEG-07)

**Ist-Stand.** Das Backfill v0104 (`care_event_backfill_mapper.py`) kopiert `applied_by_key` / `harvested_by_key`
aus Aufzeichnungen nach Art. 6 Abs. 1 lit. c (PflSchG § 11, KCanG; NFR-011 R-16/R-17) ins Pflegeprotokoll, wo sie
der Beet-Historie und dem Personenfilter dienen. Die Kopie läuft bereits; ein Schalter
`PRIVACY_BACKFILL_COPIES_PERFORMER` ist spezifiziert (E01). Bewässerungs-/Düngeereignisse werden ohne
Kontoverweis kopiert (Personenbezug nur über den Mandanten). Bei Mandantenlöschung werden `pest_control`-Zeilen des
Pflegeprotokolls gelöscht; der § 11-Nachweis ist die `treatment_applications`-Zeile (`tenant_erasure_engine.py`).

**Fragen.**
1. Ist die Weiterverarbeitung der kopierten durchführenden Person mit dem ursprünglichen Zweck vereinbar
   (Art. 5 Abs. 1 lit. b, Art. 6 Abs. 4), und decken Datenschutzhinweis und Verzeichnis sie ab?
2. Gering: Gilt dasselbe für die kopierten Bewässerungs-/Düngeereignisse ohne Kontoverweis?
3. Ist das Löschen der `pest_control`-Zeilen bei Mandantenlöschung haltbar, solange `treatment_applications` der
   einzige § 11-Nachweis bleibt?

## 5. Gerätespeicher (LEG-09, LEG-10, LEG-12)

**Ist-Stand.** IndexedDB `kp-plan-cache`, `kp-write-queue` und Cache Storage `kp:{user}:{tenant}`, `kp-sw-state`
sowie App-Shell-Caches; der Schreibpuffer hält offene Einträge 365 Tage, fehlgeschlagene/kollidierende 90 Tage.
`07` schlägt Opt-in für alle (DEC-29), Quarantäne 14 Tage, Fristen 90/30 Tage und einen Shared-Device-Modus vor
(DEC-12); gebaut ist der Bestand.

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
Löschumfang `user_diary_attachments` (`erasure_engine.STORAGE_CLEANUP_RULES`): bei Kontolöschung bleibt die Datei
für die übrigen Mitglieder, `created_by` wird `_anonymized`, EXIF wird entfernt. Die Regel begründet das mit
NFR-011 R-16/R-17/R-18 (CanG/PflSchG) — für Gartenfotos trifft das nicht zu; tragfähig wäre allenfalls Art. 6
Abs. 1 lit. f. Der Art.-15/20-Export enthält Metadaten und Verweise, die Bilddateien sind „in der App
verfügbar“. Ein Foto entfernen kann nur die Leitung; eine abgebildete Person ohne Konto hat keinen eigenen Weg.

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
