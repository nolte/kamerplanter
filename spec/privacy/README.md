# Kamerplanter — DSGVO-Datenschutzarchitektur und Umsetzungsspezifikation

```
Ablageort: spec/privacy/ (DEC-01) · Sprache: Deutsch (DEC-23); Issue-Titel, Code und GitHub-Texte englisch
Version: 1.2 · 2026-11-22 · Gemessen gegen: develop 007a4ea90 (Audit 2026-11-22)
Vorgänger: 1.1 · 2026-11-09 · gemessen gegen develop 24d1c2988; Nachtrag #2839 (develop 343afbb97)
Änderungen 1.2: Audit 2026-11-22 vollständig in die Fachdokumente übernommen (Befunde LEG-23…LEG-61 in
decision-log §D, Maßnahmen PRA-0.01…PRA-3.10 in 12, Fragen in 16, Widersprüche W-30…W-53 in 14); neuer Abschnitt
„Stand nach Audit 2026-11-22“; Dokumentenindex, Umsetzungsreihenfolge und Ist-Aussagen auf den gemessenen Stand
gebracht; angrenzende Dokumente, Duplikate, fehlende Dokumente und Spezifikationen, Zuständigkeiten aufgenommen
Status: umsetzungsreif für die in 12 §4 als READY/READY_WITH_GUARDS geführten Anforderungen; produktive
Verarbeitung gegateter Maßnahmen erst nach registrierter Rechtsentscheidung (decision-log §B); kommerzieller
SaaS-Betrieb (BM-001) und gewerbliche Mandanten mit Beschäftigten nicht freigabefähig (Stand nach Audit, unten)
Verantwortlich: Engineering (Erstellung) · DSB / Rechtsberatung (LEG §B, Fragen in 16) · Betreiber (DEC, Gates, PRA-0.01…0.04)
```

## Zweck

Das Paket ist die maßgebliche technische Grundlage für Datenschutz durch Technikgestaltung in Kamerplanter als
mandantenfähiger, gegebenenfalls kommerziell betriebener Anwendung. Es trennt **verifizierte Repository-Fakten**,
**verifizierte Rechtsquellen**, **Vorschläge** und **offene Rechtsentscheidungen** und erlaubt, freigegebene
Funktionen umzusetzen, ohne Datenschutzverhalten zu erfinden oder Rechtsentscheidungen stillschweigend zu treffen.
Es baut auf REQ-025, NFR-011, REQ-023/024/049, REQ-053 und UI-NFR-012 auf und ändert sie nie stillschweigend
(Änderungsvorschläge: `06` §9, Epic E16).

## Dokumenthierarchie

| # | Dokument | Inhalt | IDs |
|---|----------|--------|-----|
| 01 | [`01-privacy-architecture.md`](01-privacy-architecture.md) | Vokabular, Komponenten, Datenflüsse, Vertrauensgrenzen, Identitätstrennung, Prinzipien | PRIV-001…012 (Bereich 001–029) |
| 02 | [`02-personal-data-inventory.md`](02-personal-data-inventory.md) | feldgenaues Inventar mit Lebenszyklus; Ableitungswege (§5/§5a); nicht existierende Felder | PRIV-030…031 |
| 03 | [`03-account-and-membership-lifecycle.md`](03-account-and-membership-lifecycle.md) | Kontolöschung, Mitgliedschaftsende, Mandantenlöschung, Wiedereintritt, Offline, Pflichtaufzeichnungen, Teilausfall | PRIV-100…134 |
| 04 | [`04-anonymization-and-redaction.md`](04-anonymization-and-redaction.md) | Identifikationsklassen, Marker/Tombstone (zwei Generationen), Zustandsautomat der Freitextprüfung, generische Schwärzung, Verifikation | PRIV-200…239 |
| 05 | [`05-access-and-visibility.md`](05-access-and-visibility.md) | Sichtbarkeitsmatrix, Mandanten- vs. Plattformzugriff, Defaults je Mandantenklasse, Zweckberechtigungen | PRIV-300…316 |
| 06 | [`06-retention-and-legal-basis.md`](06-retention-and-legal-basis.md) | Rollenmatrix (PA-nn), Verarbeitungstätigkeiten-Matrix, **feldgenaue Pflichtaufzeichnungen**, LIAs, Beschäftigte/Ehrenamt, Aufbewahrung, Produktionsgates, **Compliance-Matrix** (Audit 2026-11-22) | PRIV-400…414 |
| 07 | [`07-offline-privacy.md`](07-offline-privacy.md) | Gerätespeicher, TDDDG/DSGVO getrennt, **Opt-in und Übergang**, Fristen, Widerruf, Shared-Device-Szenarien | PRIV-500…533 |
| 08 | [`08-api-and-data-model.md`](08-api-and-data-model.md) | Registry, `PersonRef`, Laufzeit-Provenienz, Collections (`erasure_mirror`), Defaults ohne Modell-Default, Routen, **Feature-Flags** | PRIV-600…610 |
| 09 | [`09-migrations-and-backfills.md`](09-migrations-and-backfills.md) | Migrationsphasen, v0109–v0111, Reklassifizierung (Flag), **Löschungs-Spiegel und Restore-Replay**, Re-Keying, Geräte-Migration | PRIV-700…718 |
| 10 | [`10-testing-and-acceptance.md`](10-testing-and-acceptance.md) | TA-Matrix, Negativtests „kann nicht wieder auftauchen“, Gates; Abnahmetests der PRA-Aufgaben | TA-001…TA-810 ff. |
| 11 | [`11-dpia-pre-screening.md`](11-dpia-pre-screening.md) | Verarbeitungsvorgänge, Risikoregister, **begründete Art.-35-Bewertung je Betriebsmodell** (inkl. „selbst gehostet, gewerblich“, LEG-48) | RISK-01 ff. |
| 12 | [`12-implementation-roadmap.md`](12-implementation-roadmap.md) | Epics E01…E18, Defaults je Klasse, **Readiness-Tabelle** (§4, inkl. Readiness je Betriebsmodell), **Remediation-Aufgaben des Audits** in vier Phasen, offene Punkte für Product Owner, Betreiber und gewerbliche Kunden | PRA-0.01…PRA-3.10; Q-PO/Q-OP/Q-CUS-nn |
| 13 | [`13-legal-evidence-register.md`](13-legal-evidence-register.md) | **Rechtsevidenzregister** L-nn mit Wortlaut, URL, Fassung, Prüfdatum; Verifikationsaufträge V-nn | L-01 ff., V-01 ff. |
| 14 | [`14-contradiction-register.md`](14-contradiction-register.md) | **Widerspruchsregister** mit Auflösung, Test und gemessenem Stand (Audit 2026-11-22) | W-01…W-53 |
| 15 | [`15-decision-analyses.md`](15-decision-analyses.md) | **Entscheidungsanalysen** DA-01…DA-08 (Rollen, Rechtsgrundlagen, KCanG/PflSchG, Beschäftigte, Freitext, Pseudonymisierung, Offline/TDDDG, DSFA) | — |
| 16 | [`16-dpo-briefing-2517.md`](16-dpo-briefing-2517.md) | **Briefing für DSB/Rechtsberatung** (#2517): Fragen je Komplex mit Ist-Stand, Default und LEG-Zuordnung; Nachtrag mit den Rechtsfragen des Audits | LEG-20…22; Q-DSB-nn, Q-LAW-nn |
| — | [`decision-log.md`](decision-log.md) | **Entscheidungsregistry**: DEC-01…34 (§A), Rechtsfragen LEG-01…22 mit Scope, PA, Owner, Gate, Durchsetzungspunkt, Prüfdatum und Audit-Prüfstatus (§B), Betreiberentscheidungen (§C), **Register der Audit-Befunde LEG-23…LEG-61** (§D) | DEC-nn, LEG-nn |

Lesereihenfolge: `01` → `15` (Analysen) → `06` (Recht) → `03`/`04`/`05` (Verhalten) → `07` → `08`/`09` → `10` → `12`.
`02`, `13`, `14` sind Nachschlagewerke; `11` und das Decision-Log sind die Übergabe an DSB und Betreiber.

## Evidenzklassifizierung (DEC-33)

| Klasse | Bedeutung | Verwendung |
|--------|-----------|------------|
| `VERIFIED_CODE` | am Commit im Code gelesen (`path:symbol`) | Fakten zur Implementierung |
| `VERIFIED_SPEC` | in REQ/NFR/UI-NFR wörtlich belegt | dokumentierte Anforderungen |
| `VERIFIED_LEGAL` | Wortlaut aus der Primärquelle (`13` L-nn, mit URL, Fassung, Prüfdatum) | Rechtsaussagen |
| `INFERRED` | technisch/rechtlich begründet, nicht direkt verifiziert | Auslegungen; nie allein Basis einer MUSS-Anforderung |
| `PROPOSED` | empfohlenes Zielverhalten | neue Anforderungen |
| `OPEN_DECISION` | braucht eine autorisierte (Betreiber-)Entscheidung | DEC |
| `LEGAL_REVIEW_REQUIRED` | braucht qualifizierte Rechtsprüfung | LEG |

Dokumente aus v1.0 verwenden die Kurzmarker `[verifiziert]` (= VERIFIED_CODE/VERIFIED_SPEC je Bezug), `[Vorschlag]`
(= PROPOSED), `[rechtlich]` (= LEGAL_REVIEW_REQUIRED), `[?]` (= INFERRED/unverifiziert). Eine Rechtsquelle, die aus
der Umgebung nicht abrufbar war, ist `UNVERIFIED_AT_SOURCE` mit Verifikationsauftrag V-nn; sie trägt keine
MUSS-Anforderung. **EUR-Lex und Curia waren am 2026-11-09 nicht abrufbar** (HTTP 202/JS-Weiterleitung); DSGVO-Artikel
werden daher nur als Bezug genannt, deutsche Gesetze (gesetze-im-internet.de) und EDSA/WP29/DSK-PDFs sind verifiziert.

## Rechtliches Freigabemodell und Produktionsgates (DEC-32)

- **Registry**: jede Rechtsfrage ist eine LEG-Zeile mit Scope, betroffenen Verarbeitungstätigkeiten (PA-nn, `06` §2),
  Owner, erforderlicher Evidenz, Status, Prüfdatum, Neubewertungsauslöser, Produktionsgate und technischem
  Durchsetzungspunkt (Feature-Flag, Setting, Helm-Precheck; `08` §8a).
- **Drei Gates**: `engineering_allowed` (Code/Tests/Flag aus) · `deployment_allowed` (ausgerollt, inaktiv) ·
  `processing_allowed` (aktiv). Einschränkende/schutzverstärkende Maßnahmen sind freigegeben; ausweitende oder
  datenvernichtende Maßnahmen stehen hinter Flags, bis die LEG entschieden ist; Bestandsverarbeitung mit offener LEG
  ist `provisorisch` mit Prüfdatum.
- **Kommerzieller SaaS-Betrieb mit gewerblichen Mandanten** ist `deployment_allowed = nein`, bis LEG-01 (AVV,
  Rollen), LEG-05 (Beschäftigte) und LEG-12 (DSFA-Entscheidung) vorliegen.

## Rückverfolgbarkeit

```
REQ-025 / NFR-011 / REQ-053 …  ──(baut auf / schlägt versionierte Änderungen vor: 06 §9, 14, E16)──▶
PRIV-nnn (normativ, mit Evidenzklasse, Komponente, Begründung)
   ├── Akzeptanz: TA-nnn (10; Testart, Assertion, Pfad)
   ├── Umsetzung: E01…E18 (12; Abhängigkeiten, Gate, Flag)
   ├── Entscheidung: DEC-nn / LEG-nn (decision-log; Owner, Gate, Prüfdatum)
   ├── Evidenz: L-nn / V-nn (13)
   └── Widerspruch: W-nn (14)
```

Regeln: Eine Anforderung ohne TA ist nicht umsetzungsreif; eine Rechtsaussage ohne L-nn ist `INFERRED`; ein
Widerspruch wird in allen betroffenen Dokumenten zugleich aufgelöst und mit Test versehen; die Code-Inventare
(`ErasureEngine.*`, `DataExportEngine.*`) bleiben die einzige Quelle der Listen, das Paket ergänzt abgesicherte
Klassifizierung (`08` §2, TA-001/030/606).

## Umsetzungsreihenfolge

P0: E01-Rest (#2770 wurde durch #2839 geschlossen; „Principal auf Queue/MCP“ ist seit #2961 erledigt — Audit
2026-11-22, W-53; offen: Tombstone-Filter PRIV-207, Schalter `PRIVACY_BACKFILL_COPIES_PERFORMER`) → E03 → E02 → E04.
P1: E05 → E10 → E09 → E07 → E08 → E06. P2: E11 → E13 → E12 → E14. P3: E15, E18, E16, E17. Readiness je Epic: `12` §4.
Die Remediation-Aufgaben des Audits (PRA-0.01…PRA-3.10) ordnen sich in diese Epics ein und legen davor eine Phase 0
(Prüfaufgaben am Produktionsbetrieb, Korrektur von Falschaussagen, kleine schutzverstärkende Fixes); maßgeblich ist `12`.

Aus dem Paket umgesetzt sind am gemessenen Stand: DEC-09 (#2961), v0109 mit Plan-Audit-Marker (DEC-16) und
Minimal-Beat `privacy.consistency` (DEC-14/DEC-28, #2975), v0110 Bestandsklassifizierung (#2977, ohne Anlagepfad),
v0111 Schlüsselfelder für Durchführende (#2978, ohne Schreiber), PRIV-211 (`original_filename`), PRIV-201
(eine Definition von Marker und Tombstone). Alles Übrige ist offen (decision-log §A/§D, `12` §4). Das Paket selbst
ändert kein Anwendungsverhalten und legt keine GitHub-Issues an.

## Stand nach Audit 2026-11-22

Das Paket wurde am 2026-11-22 vollständig gegen die Implementierung geprüft (gemessen gegen develop `007a4ea90`,
nur lesend; Code nicht ausgeführt). **Das Audit selbst ist nicht eingecheckt**; jede Aussage, jeder Befund, jede
Maßnahme und jede Frage steht mit Evidenz im fachlich zuständigen Dokument dieses Pakets (Zuordnung unten). Die
Herkunft wird als „Audit 2026-11-22“ mit der jeweiligen ID angegeben. Keine Rechtsberatung. Pfade: Backend-Pfade ohne
Präfix liegen unter `src/backend/app/`, Frontend-Pfade ohne Präfix unter `src/frontend/src/`; Zeilen am SHA `007a4ea90`.

**Umfang.** Alle 18 Dateien des Pakets; 44 datenschutzrelevante Dokumente außerhalb (unten); Backend (Modelle,
Engines, Services, Router, Celery-Tasks, Migrationen v0093–v0114), Frontend (PWA, Service Worker, IndexedDB,
Offline-Puffer), Knowledge-Service, MCP-Server, Helm-Chart, Betreiber- und Nutzerdoku; 14 Arbeitsstränge (W01–W14) in
sechs Prüfsträngen (A Löschung/Freitext, B Offline, C Betroffenenrechte/Bilder, D TOM/Aufbewahrung/Backup,
E Inventar/Rechtsgrundlage/Beschäftigte/DSFA, F Governance/Vorfälle/KI). **Nicht prüfbar:** Produktionskonfiguration
(tatsächliches `LLM_PROVIDER`, `EMAIL_ADAPTER`, Sentry-Region, `STORAGE_STRIP_EXIF`), laufende Backups und
Bucket-Versionierung, Log-Aufbewahrung im Cluster, Verträge (AVV), organisatorische Meldewege, Gerätezustände im
Browser (nur Codepfad-Analyse). **Methode:** jede Aussage an der Fundstelle gelesen, im Code nachverfolgt und mit
einem Status-Token bewertet (`CONFIRMED`, `PARTIALLY_CONFIRMED`, `NOT_REPRODUCIBLE`, `ALREADY_FIXED`,
`DOCUMENTATION_GAP`, `LEGAL_REVIEW_REQUIRED`, `NEW_FINDING`); tragende Befunde (u. a. LEG-10, LEG-11, LEG-15, LEG-23,
LEG-29, LEG-30, LEG-31) zusätzlich nachgeprüft — daraus die Korrektur, dass LEG-31 nicht für `/ask` gilt.

### Gesamturteil

Das Paket ist methodisch stark — Evidenzklassen, Entscheidungsregister, Widerspruchsregister und Produktionsgates sind
vorhanden und meist korrekt; jede Aussage ließ sich auf eine ID zurückführen. **Es beschrieb aber an vielen Stellen
einen Soll- als Ist-Zustand, und mehrere zentrale Schutzmechanismen existieren nur als Datenmodell oder Text:**
Einschränkung und Widerspruch werden gespeichert, aber nie durchgesetzt (LEG-23); die Mandantenklassifizierung für
Beschäftigtenumgebungen wird nie gelesen (LEG-30); der zugesagte Löschungs-Spiegel für Backups fehlt vollständig
(LEG-11, DEC-26); das Offline-Opt-in ist nicht gebaut (LEG-09, DEC-29). In v1.2 sind diese Stellen auf den gemessenen
Stand gebracht; das Soll steht als PRIV-Anforderung bzw. PRA-Aufgabe.

**Belegte Stärken:** Authentifizierung und Mandantentrennung (JWT 15 min / Refresh 30 d mit Rotation und
Replay-Erkennung, HttpOnly-Cookie, bcrypt, Lockout, Step-up, API-Keys mit IP-Allowlist, `require_permission`,
Ownership-Prädikate mit leerer Restliste); robuste Serverseite der Offline-Synchronisation (gepufferte Einträge
gelöschter Konten → 401, ehemaliger Mitglieder → 403, idempotent über `client_event_id`); Zurechnungsregel „immer der
Aufrufer“ auf allen vier Bestätigungswegen mit Guard; Log-Redaktion, IP-Anonymisierung nach 7 Tagen, Retention-Beats
mit Ober- und Untergrenzen; Plan-Audit-Marker (DEC-16, v0109) und Leeren von `original_filename` (PRIV-211);
Erkennungsbilder werden nicht gespeichert (nur gekürzter Hash, `domain/models/identification.py:3-5`).

**Strukturelle Schwächen:** (1) Sollzustand als Ist-Zustand gegenüber Betroffenen (Art. 18, „DSFA durchgeführt“,
Sensor-Downsampling, Offline-Projektion, „Angemeldet bleiben“) — PRA-0.05, W-10, W-34…W-37. (2) Schutz als Datenfeld
ohne Leser (Einschränkungen, Klassifizierung, `anon2_`) — Processing-Hold-Guard und wirksame Klassifizierung,
Zielarchitektur in [`01`](01-privacy-architecture.md). (3) Kein Feld-Register: über 50 Freitextfelder,
Personenschlüssel in Neben-Collections und externe Empfänger nicht zentral klassifiziert, daher übersehen Guards
Felder wie `triggered_by_user` — PRA-1.01. (4) Löschung endet an der Datenbank: Backups, Bucket-Versionen,
Plan-Snapshots und Gerätespeicher sind nicht in die Löschpropagation einbezogen — PRA-1.04/1.05, PRA-2.02,
PRA-2.15/2.16.

### Readiness je Betriebsmodell

| Betriebsmodell | Einschätzung (Audit 2026-11-22) |
|---|---|
| Privater Self-Host (eine Person / ein Haushalt, BM-003) | betreibbar; Phase 0 (Korrektur der Falschaussagen, SW-Cache, KI-Gate) empfohlen |
| Gemeinschaftsgarten / Verein, selbst gehostet (BM-002) | betreibbar nach Phase 0 und den P1-Aufgaben zu Zurechnung, Freitexten und Art. 18/21 |
| Gewerblich, selbst gehostet (Beschäftigte) | **nicht freigabefähig**, solange LEG-28/29/30 und LEG-05 offen sind |
| Kamerplanter-SaaS (BM-001) | **nicht freigabefähig** — kein Rollenmodell/AVV, kein Empfängerregister, kein Datenpannen-Verfahren, keine Löschpropagation bei Restore; deckt sich mit dem Gate `deployment_allowed = nein` (DEC-32) |

Readiness je Epic und je Betriebsmodell mit Bedingungen: [`12`](12-implementation-roadmap.md) §4.

### Kennzahlen

| Kennzahl | Wert | Wo im Paket |
|---|---|---|
| Inventarisierte Dokumente | 62 (18 im Paket, 44 außerhalb) + 4 erwartete, fehlende | unten |
| Revalidierte bestehende LEG | 16 (LEG-01, -02, -05, -06, -07, -08, -09, -10, -11, -12, -13, -15, -16, -20, -21, -22) | decision-log §B |
| … technisch `CONFIRMED` / `PARTIALLY_CONFIRMED` / `DOCUMENTATION_GAP` / nur rechtlich offen | 8 / 5 / 2 / 1 (LEG-16); `ALREADY_FIXED` 0 vollständig, 1 Teil (Plan-Audit-Marker in LEG-15); rechtlich offen alle 16 | decision-log §B |
| Weitere geprüfte Spec-Aussagen | 137: 96 `CONFIRMED` (17 davon „Ist richtig beschrieben, Anforderung nicht umgesetzt“), 14 `PARTIALLY_CONFIRMED`, 1 `NOT_REPRODUCIBLE`, 6 `ALREADY_FIXED`, 13 `DOCUMENTATION_GAP`, 6 `NEW_FINDING`, 1 ungeprüft | Fachdokumente (Ist-Stand je PRIV) |
| Neue Befunde | 39 (LEG-23…LEG-61): P0 0 · P1 11 · P2 20 · P3 8; bedingte Eskalation auf P0 bei LEG-31 und LEG-32 | decision-log §D |
| Remediation-Aufgaben | 48: P0 4 · P1 22 · P2 18 · P3 4; 20 mit Rechtsfreigabe | `12` (PRA-0.01…PRA-3.10) |
| Offene Fragen | 88 (Product Owner 23, Betreiber 15, DSB 21, Rechtsberatung 17, gewerbliche Kunden 12) | DSB/Recht: `16`; übrige: `12` |
| Punkte für externen Rechtsrat | 38 | `13`, `16` |
| Compliance-Matrix | 59 Zeilen: erfüllt 3 · teilweise 23 · nicht erfüllt 16 · Rechtsprüfung offen 16 · nicht anwendbar 1 | `06` |
| Widerspruchsregister | W-01…W-29: 17 aufgelöst, 12 offen bzw. festgehalten (W-16, W-21 nicht neu gemessen); neu W-30…W-53 | `14` |

Die vier P0-Aufgaben PRA-0.01…PRA-0.04 sind Prüfaufgaben am Produktionsbetrieb; ihr Ergebnis entscheidet, ob eine
P0-Lage vorliegt (Cloud-LLM in Produktion, BM-001-Freigabe, aktive Backups/Bucket-Versionierung, gewerbliche Mandanten
mit Beschäftigten).

### Größte Risiken

| Risiko | LEG | Warum es zählt |
|---|---|---|
| Art. 18/21 wirkungslos — gespeichert, kein Verarbeitungs- oder Löschpfad liest sie; die Nutzerdoku sagt das Gegenteil | LEG-23 | Betroffenenrecht nur dem Anschein nach erfüllt; falsche Information nach Art. 12 |
| Restore macht Löschungen und Widerrufe rückgängig — kein Spiegel, kein Replay; widerrufene API-Keys, Sitzungen, Einwilligungen kehren zurück | LEG-11, LEG-24, LEG-25, LEG-26 | Art. 17 und Art. 32 hängen davon ab, dass nie aus einem Backup wiederhergestellt wird |
| KI-Cloud-Gate prüft den falschen Provider | LEG-31 | bei einem Cloud-LLM in Produktion Übermittlung ohne Einwilligung (P0-Bedingung) |
| Beschäftigtenschutz inert — Klassifizierung nie gelesen; Aufgaben speichern Dauer, Zeiten, Bewertungen je Person für alle lesbar; `control_events` mit rohem Kontoschlüssel | LEG-05, LEG-28, LEG-29, LEG-30 | Leistungs- und Verhaltenskontrolle in gewerblichen Umgebungen möglich (§ 26 BDSG, § 87 Abs. 1 Nr. 6 BetrVG) |
| Offline-Speicher größer und länger als zugesagt — SW-Cache mit Rohantworten, kein Opt-in, Fristen fest kodiert, Puffer nicht wählbarer Mandanten bis 365 d | LEG-09, LEG-10, LEG-27, LEG-36 | § 25 TDDDG, Art. 5 Abs. 1 lit. c/e; falsche Transparenzangaben |
| Governance-Lücken für SaaS — kein Rollenmodell/AVV, kein Empfänger-/Unterauftragsverarbeiter-Register mit Drittlandprüfung, kein Verfahren nach Art. 33/34 | LEG-01, LEG-32, LEG-33 | Grundpflichten aus Art. 28, 30, 33/34 vor jedem SaaS-Betrieb |

### Die drei wichtigsten Maßnahmen vor einem kommerziellen SaaS-Betrieb

1. **Verantwortlichkeit und Meldewege festlegen** — Rollenmodell mit AVV-Muster und Art.-26-Vorlage (PRA-3.03),
   Empfänger- und Unterauftragsverarbeiter-Register mit Drittlandprüfung (PRA-1.03), Datenpannen-Verfahren nach
   Art. 33/34 mit `SECURITY.md`, Pannenregister und Mandantenbenachrichtigung (PRA-0.11, PRA-3.02). Betrifft LEG-01,
   LEG-32, LEG-33.
2. **Löschung und Widerruf dauerhaft durchsetzen** — Journal mit Outbox (PRA-1.04), Restore-Erkennung mit Startsperre
   und Replay (PRA-1.05), Processing-Hold-Guard für Art. 18/21 und Legal Hold (PRA-1.06). Betrifft LEG-11, LEG-23,
   LEG-24, LEG-25, LEG-26, LEG-35.
3. **Beschäftigtenumgebungen technisch absichern** — Mandantenklassifizierung setzbar und wirksam (PRA-1.02),
   Aufgaben-Leistungsdaten und `control_events` minimieren (PRA-2.06, PRA-2.07), Sichtbarkeit der Zurechnung steuern
   (PRA-2.05), DSFA je Betriebsmodell fortschreiben (PRA-3.04). Betrifft LEG-05, LEG-12, LEG-28, LEG-29, LEG-30, LEG-48.

Nächste Schritte: Phase 0 sofort (PRA-0.01…0.04 am Produktionsbetrieb klären; parallel PRA-0.05, PRA-0.09, PRA-0.07);
neue Rechtsfragen als Nachtrag zum bestehenden Briefing [`16`](16-dpo-briefing-2517.md) statt eines zweiten Pakets
(PRA-3.01); danach Architekturgrundlage Phase 1 (Feld-Register, wirksame Klassifizierung, Empfängerregister, Journal
mit Outbox, Restore-Replay, Processing-Hold-Guard). Befundregister: [`decision-log.md`](decision-log.md) §D;
Maßnahmen und Readiness: [`12`](12-implementation-roadmap.md).

### Wo die Inhalte des Audits stehen

| Audit-Inhalt | Dokument |
|---|---|
| Gesamturteil, Readiness, Kennzahlen, Dokumenteninventar, Duplikate, fehlende Dokumente/Spezifikationen, Zuständigkeiten | dieses README; Readiness zusätzlich `12` §4 |
| Revalidierung der 16 bestehenden LEG (Prüfstatus, PRA) | decision-log §B; fachlicher Ist-Stand in den Fachdokumenten |
| Befunde LEG-23…LEG-61 | Register decision-log §D; Sachverhalt und Evidenz im dort genannten Fachdokument |
| veraltete Entscheidungen | decision-log §A (DEC-Status) und §C |
| Widersprüche (Register-Stand, neue Spec-/Doku-vs-Code-Widersprüche) | `14` |
| Zielarchitektur; Lebenszyklen; Backup/Restore/Journal | `01`; `03`; `09` |
| Remediation-Roadmap PRA-*; Abnahmetests | `12`; `10` |
| rechtliche Bewertung; neue Rechtsquellen | `13`; Fragen in `16` |
| offene Fragen | DSB/Rechtsberatung `16`; Product Owner, Betreiber, gewerbliche Kunden `12` |
| Compliance-Matrix | `06` |

### Angrenzende Dokumente außerhalb des Pakets (44)

Version laut Kopfzeile; „Kopf/Fuß“ = Kopf- und Fußzeile nennen verschiedene Versionen (W-25).

| Dokument | Version | Stand am gemessenen SHA (Bezug) |
|---|---|---|
| `spec/req/REQ-023_Benutzerverwaltung-Authentifizierung.md` | 1.51 | aktiv; W-23 offen |
| `spec/req/REQ-024_Mandantenverwaltung-Gemeinschaftsgaerten.md` | 1.37 | aktiv |
| `spec/req/REQ-025_Datenschutz-Betroffenenrechte.md` | Kopf 1.40 / Fuß 1.5 | §9 unvollständig (LEG-33); DP-002 nicht umgesetzt (LEG-49, W-47); §10 veraltet (W-24, W-36) |
| `spec/req/REQ-031_KI-Assistent-Pflanzenberatung.md` | 2.6 | Provider-Gate-Lücke (LEG-31) |
| `spec/req/REQ-033_MCP-Server.md` | 1.14 | keine Agentensicherheit (LEG-52) |
| `spec/req/REQ-049_Rollenmodell-und-Vokabular.md` | 1.15 | P4 ↔ REQ-056 §8 (W-30, LEG-53) |
| `spec/req/REQ-050_KI-Analyse-Tagebucheintraege.md` | Kopf 1.6 / Fuß 1.5 | §7.2 nur auf der Queue wirksam (LEG-51, W-46) |
| `spec/req/REQ-053_Grafische-Garten-Beetplanung.md` | 1.54 | W-01 offen (GP-FR-109) |
| `spec/req/REQ-055_Plant-Identity-Plant-Social.md` | 1.5, Entwurf | teilweise umgesetzt |
| `spec/req/REQ-056_Mandanten-Lebenszyklus-Kontingente.md` | 1.7 | umgesetzt (#2138); §8 ↔ REQ-049 P4 (W-30) |
| `spec/nfr/NFR-001_Separation-of-Concerns.md` | Kopf 2.6 / Fuß 2.3 | §6.7 DSFA-MUSS nicht erfüllt (W-10) |
| `spec/nfr/NFR-007_Betriebsstabilitaet-Monitoring.md` | Kopf 1.1 / Fuß 1.0 | Alerts „Offen“; kein Datenpannenverfahren (LEG-32) |
| `spec/nfr/NFR-011_Vorratsdatenspeicherung-Aufbewahrungsfristen.md` | Kopf 1.46 / Fuß 1.7 | W-11, W-15, W-17, W-22 offen; R-01/R-26/R-40 veraltet (W-38…W-40) |
| `spec/nfr/NFR-013_Speicheranbindung-Object-Storage.md` | Kopf 1.13 / Fuß 1.3 | EXIF-Strip fail-open (LEG-57) |
| `spec/nfr/NFR-014_Nuclei-Security-Scanning.md`, `spec/nfr/NFR-015_OWASP-ZAP-Security-Scanning.md` | Kopf 1.3 / Fuß 1.1 | advisory |
| `spec/betriebsmodelle/README.md`, `BM-001_Oeffentlicher-Managed-Service.md`, `BM-002_Self-Hosted-Mehrnutzer.md`, `BM-003_Self-Hosted-Einzelnutzer.md` | BM je 1.0 | Grundlage für LEG-01; BM-001 §6.2 nicht umgesetzt (Art.-33-Meldepflicht, Drittland); BM-001 §5 ↔ `06` PA-07b (W-33) |
| `spec/decisions/ADR-002-tenant-species-knowledge-service-export.md`, `ADR-009-active-tenant-header.md` | Accepted / — | aktiv |
| `spec/decisions/ADR-003-sensor-retention-perennials.md` | Accepted | „DSFA-Frage offen“ (W-10) |
| `spec/decisions/ADR-005-versioned-migration-framework.md` und `docs/de/adr/009-versioned-migration-framework.md` | beide akzeptiert | **Duplikat** (unten) |
| `spec/analysis/multi-tenant-saas-readiness-audit-2026-10-04.md`, `it-security-review-req-055.md`, `security-review-req-053.md`, `REQ-034-security-review.md` | — | historisch |
| `spec/analysis/code-security-review.md` | 2026-03-22 | **veraltet** (vor Mandantenfähigkeit und RBAC-Durchsetzung); als historisch zu kennzeichnen |
| `docs/de/user-guide/privacy.md` (+ EN-Spiegel) | — | mehrere Falschaussagen (W-10, W-34, W-41, W-42, W-43) |
| `docs/de/user-guide/ai-assistant.md`, `ai-providers.md`, `ai-diagnosis.md` | — | Indikator und Provider-Wahl wirken für Knowledge-Service-Pfade nicht (LEG-31, W-45) |
| `docs/de/user-guide/plant-identification.md`, `pest-detection.md` | — | aktiv |
| `docs/de/guides/data-retention.md` | — | Sensor ohne TimescaleDB-Vorbehalt (W-35); keine Backup-Frist (PRIV-708) |
| `docs/de/guides/compliance-anbauvereinigung.md` | — | nicht im Detail geprüft |
| `docs/de/deployment/backup-restore.md` | — | ohne Löschungs-Vorbedingung (W-48, LEG-11); Versionierung ohne Lifecycle (LEG-26) |
| `docs/de/deployment/tenant-export-import.md` | — | aktiv |
| `docs/de/deployment/fehler-tracking.md` | — | keine Region- oder AVV-Angabe (LEG-16) |
| `docs/de/reference/environment-variables.md` | — | `PRIVACY_DATA_CONTROLLER_*` Pflicht „Nein“ (W-49, LEG-50) |
| `AUDIENCES.md` | `assumed` | keine Datenschutz- bzw. DSB-Zielgruppe benannt |

### Lücken: fehlende Dokumente

Erwartet, aber im Repository nicht vorhanden — jede Lücke ist einem Befund und einer Maßnahme zugeordnet:

| Fehlendes Dokument | Befund | Maßnahme (`12`) |
|---|---|---|
| `SECURITY.md` (Repo-Root; `.github/` ohne Security-Policy) mit Meldeadresse und Notfall-Kurzrunbook | LEG-32 | PRA-0.11, PRA-3.02 |
| DSFA-Dokument (je Verantwortlichem; Vorprüfung `11` ist keine DSFA) | LEG-12, LEG-48 | PRA-3.04 |
| AVV-Muster mit TOM-Anlage (und Art.-26-Vorlage) | LEG-01 | PRA-3.03 |
| Register der Empfänger und Unterauftragsverarbeiter mit Drittlandprüfung | LEG-33 (LEG-01, LEG-16) | PRA-1.03 |

### Duplikate

| Gegenstand | Fundstellen | Folge | Bezug |
|---|---|---|---|
| Zwei ADR-Serien mit überlappender Nummer, gleicher Inhalt „versioniertes Migrationsframework“, beide akzeptiert | `spec/decisions/ADR-005-versioned-migration-framework.md`; `docs/de/adr/009-versioned-migration-framework.md` | Änderungen landen nur in einer Serie | LEG-61; PRA-3.10 (eine Quelle, die andere verweist) |
| DSFA-Aussage an vier Stellen, inhaltlich verschieden | NFR-001 §6.7; ADR-003; `11` §4.3; Nutzerdoku | kein maßgeblicher Stand | W-10, LEG-12 |
| Liste externer Dienste ohne gemeinsame Quelle (u. a. Resend, Kindwise, NASA POWER, Bright Sky, Web-Push, Apprise fehlen in REQ-025 §9) | REQ-025 §9; BM-001 §6.2; `docs/de/user-guide/ai-providers.md`; ENV-Referenz | jede Liste unvollständig | LEG-33; PRA-1.03 |
| Status E01-Rest in vier Dokumenten, nur eines nachgeführt | `16` §1; `03` §4; `12` E01; README | Planung auf falscher Grundlage | W-53, LEG-61 |

### Lücken: fehlende Spezifikationen

| Lücke | Befund | Zieldokument |
|---|---|---|
| Verfahren für Datenschutzverletzungen (Art. 33/34): Erkennung, Bewertung, 72-h-Meldung, Benachrichtigung, Register nach Art. 33 Abs. 5 | LEG-32 | `01` |
| Register der Empfänger und Unterauftragsverarbeiter mit Drittlandprüfung | LEG-33 | `06` |
| Agentensicherheit für MCP (indirekte Prompt-Injection, `dry_run`-Default) und MCP-Freitextpolitik für Inhalte anderer Mitglieder | LEG-51, LEG-52 | `05` |
| Abschließende Ausnahmeliste zu REQ-049 P4 (Plattform-Export) | LEG-53, W-30 | `05`, E16 |
| Legal-Hold-Mechanismus | LEG-35 | `03` |
| Restore-Semantik für Widerrufe (API-Keys, Sitzungen, Passwort, Consent, Art. 18/21) — DEC-26 deckt nur Löschungen | LEG-24 | `09` |
| Aufbewahrung für Nebenspeicher (Logs 30 d nur im NFR-011-Änderungsverlauf v1.13, Valkey-AOF, vectordb, Volume-Snapshots, S3-Versionen, Sentry) | LEG-44 | `06` |
| Verschlüsselung ruhender Daten (Nachweis) und zweiter Faktor für Plattform-Admins | LEG-42, LEG-45 | `01` |
| DSFA-Vorprüfung „selbst gehostet, gewerblich“ und Weitergabe per Service-Account/MCP; KI/MCP bisher nicht bewertet | LEG-48 | `11` |
| Inventarzeilen für `control_events`, Aufgaben-Leistungsfelder, `calendar_feeds`, Erkennung/Diagnose, `owner_user_key`, Telemetrie, externe Empfänger | LEG-46 | `02` |
| Art.-13-Pflichtangaben im öffentlichen `GET /privacy/policy`; Art.-15-Abs.-1-Angaben (lit. a–h) im Export | LEG-50, LEG-41 | `06`, `01` |
| AVV-Muster mit TOM-Anlage; Rollenmodell je Betriebsmodell in `06` §1 | LEG-01 | `06` |
| Session-Fernwiderruf (vorhanden, `AccountSettingsPage.tsx:656`) als Shared-Device-Abhilfe in `07` §8a und Nutzerdoku | LEG-10 | `07` |

### Unklare Zuständigkeiten

| Thema | Widersprüchliche bzw. fehlende Zuweisung | Bezug |
|---|---|---|
| Betroffenenanfragen in BM-001 | BM-001 §5 „Anbieter“ für alle ↔ `06` PA-07b Mandant für Mandantendaten | LEG-01, W-33 |
| Meldung von Datenschutzverletzungen | nirgends zugewiesen | LEG-32 |
| Tagebuchanalyse durch Agenten | REQ-025 „vollständig beim Nutzer“ ↔ `06`: Mandant ist Verantwortlicher für PA-06 | LEG-51 |
| Freigabe von Unterauftragsverarbeitern (Art. 28 Abs. 2) | niemand benannt | LEG-33 |
| Prüfung von Art.-18/21-Anträgen | kein Betreiber-/Admin-Kanal; der Antrag erreicht niemanden | LEG-23 (PRA-0.06) |
| Pflichtzeilen nach Mandantenlöschung | pseudonymisiert erhalten, der Pflichtige hat keinen Zugriff mehr | LEG-47 |
| Log-Aufbewahrung (30 d) | Betreiberaufgabe ohne Betreiberdoku | LEG-44 |
| DSFA bei gewerblichen Mandanten | Pflicht trifft Mandant/Arbeitgeber; das System kann `commercial` nicht erkennen | LEG-12, LEG-30 |

### Anforderungen ohne Abnahmekriterium

Die Regel „eine Anforderung ohne TA ist nicht umsetzungsreif“ (Rückverfolgbarkeit) ist nicht durchgehend eingehalten:
eine Heuristik fand 76 von 182 definierten PRIV-Kennungen ohne TA-Bezug (teils fehlpositiv, z. B. PRIV-310 → TA-304;
eigene Zählung: 198 verschiedene PRIV-Kennungen inkl. Verweisen, 126 TA-Kennungen in `10` — Größenordnung, keine
exakte Zahl). Ohne testbares Kriterium sind insbesondere PRIV-407 (Guard: kein Endpunkt liefert Dauer oder
Geschwindigkeit je Person; LEG-28), PRIV-406/PRIV-408 (nur `mkdocs build`), PRIV-900…PRIV-902 (Prozessregeln);
außerhalb des Pakets BM-001 Meldepflicht 72 h (LEG-32), NFR-001 §6.7 (W-10), REQ-049 P4 (W-30), REQ-025 DP-002
(W-47). TA-Vergabe und ein Pre-commit-Skript „PRIV ohne TA“ mit Ausnahmeliste: PRA-3.10, `10`.

### Am Code belegte, nicht umgesetzte Zusagen

| Zusage | Ist (Audit 2026-11-22) | Befund / Epic |
|---|---|---|
| REQ-025 §3.7 / AK-11 Dependency `check_processing_restriction` (423) | 0 Treffer | LEG-23 |
| REQ-025 DP-002 Koordinaten auf 2 Nachkommastellen | Adapter ungerundet | LEG-49 |
| PRIV-407 keine Dauer-/Geschwindigkeitsmessung | `domain/models/task.py:181-205`, `task_service.py:1469-1475`, `:1720-1730` | LEG-28 |
| PRIV-409 Klassifizierung Pflicht bei Anlage | nicht gebaut (`domain/models/tenant.py:31-38`) | LEG-30 |
| PRIV-300/301, PRIV-307/308, PRIV-405 Sichtbarkeit und Audit der Zurechnung | `attribution_visibility` 0 Treffer | LEG-05, E08 |
| PRIV-310 MCP ohne rohe `users._key` | `mcp_server/tools/diary.py:507-510`, `ipm.py:463` | E08 |
| PRIV-316 auditierter Lesezugriff auf die Löschvorschau | `api/v1/admin/platform/router.py:544-560` ohne Audit-Zeile | PRA-2.19 |
| PRIV-207, Schalter `PRIVACY_BACKFILL_COPIES_PERFORMER` | Schalter 0 Treffer | E01-Rest, LEG-07 |
| PRIV-213 `material`, Messwert-Strings schwärzbar | `domain/models/care_event.py:83`, `:166`, `:254-256` | LEG-08 |
| PRIV-234 Residue-Scan auch für Kontolöschung | nur `tenant_erasure_executor.py` | LEG-08 |
| PRIV-101/104 Daten im Zustand `closed` eingeschränkt | Namens-Join ohne `is_active` (`care_event_repository.py:657-662`) | E02 |
| PRIV-108, PRIV-707…713, TA-718 Löschungs-Spiegel, Replay, Helm-Precheck | 0 Treffer `erasure_mirror` | LEG-11 |
| PRIV-708 Datenschutzinformation nennt Backup-Frist und Replay | fehlt | LEG-11 |
| PRIV-713 Versionierung/Snapshots ≤ 35 d mit Lifecycle | ohne Lifecycle (`helm/kamerplanter/values.yaml:587-591`) | LEG-26 |
| PRIV-505, PRIV-511…514, PRIV-516, PRIV-519…521, PRIV-523, PRIV-530 Gerätefristen, Hygiene, Logout, Quarantäne, Codes | offen | LEG-10 |
| PRIV-524…526 Shared-Device-Modus | nicht gebaut; Annahme „kein Angemeldet bleiben“ falsch | LEG-10, LEG-37 |
| PRIV-531 Offline-Opt-in | kein Schalter | LEG-09 |
| E03 `anon2_` für neue Zeilen | erkannt, kein Erzeuger | LEG-15 |
| E05/E07/E08/E14/E15 `PersonRef`, `privacy_review_items`, `attribution_visibility`, `erasure_mirror`, `/admin/platform/privacy/operations` | je 0 Treffer (Planstand korrekt) | `12` |
| E09 `tenant.classification_required` | 0 Treffer | LEG-30 |
| v0111 Schreiber für `performed_by_user_key` an `watering_events`/`watering_logs`/`tank_fill_events`/`maintenance_logs` | Felder angelegt, kein Schreiber | E01/E04 |

## Konventionen

RFC-2119 (MUSS, DARF NICHT, SOLLTE, KANN). „Anonymisiert“ nur zeilenbezogen (`04` §1a); sonst „Zurechnung entfernt“
(Marker) oder „pseudonymisiert“ (Tombstone). Fehlercodes nach NFR-006; Service-Methoden, die per Schlüssel laden und
schreiben, nehmen `*, tenant_key: str` (#2107); neue Routen im Isolation-Route-Walk und im Bounded-List-Guard; Enums
additiv mit DE/EN-i18n. Art. 17 Abs. 3 DSGVO ist eine Ausnahme vom Löschanspruch, keine Rechtsgrundlage.

## Pflege

Jedes Dokument trägt Version/Datum und den gemessenen Stand („Gemessen gegen“). LEG-Entscheidung ⇒ Decision-Log,
betroffene PRIV und Flag in derselben Änderung; behobener Audit-Befund ⇒ decision-log §D `fixed` mit PR und Test;
REQ/NFR-Änderungen (E16) zitieren `spec/privacy`; neue Widersprüche zuerst in `14`. Nach jeder gemergten PRA-Aufgabe
wird das Paket nachgezogen (PRA-3.10), damit Ist-Aussagen nicht wieder hinter den Code zurückfallen (LEG-61).
