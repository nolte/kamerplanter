# SPEC-16 — Briefing für DSB / Rechtsberatung (#2517)

```
Paket: spec/privacy · Version 1.2 · 2026-11-22
Gemessen gegen: develop 007a4ea90 (Audit 2026-11-22); v1.1 gegen ef39d1f8e
Zweck: Die in #2517 gesammelten Rechtsfragen und die Rechtsfragen des Audits 2026-11-22 als EIN Briefing
(Betreiberentscheidung 2026-11-14, Pkt. 1; PRA-3.01). Keine Rechtsberatung. #2517 bleibt offen, bis die Antwort
vorliegt; jede Antwort wird als LEG-Entscheidung in decision-log §B eingetragen (Status decided) und vom Betreiber
über die genannte PRA-Aufgabe durchgesetzt.
Änderungen 1.1 (Neumessung): §1 Routen korrigiert (`GET /care-events`, `GET /locations/{key}/history`) und
CSV-Download ergänzt; §2 Plan-Audit-Marker umgesetzt (v0109, DEC-16), `anon2_` weiterhin nicht gebaut, Frage 3
neu (LEG-15); §4 Schlüsselfelder aus v0111 ergänzt; §6 Dateiname wird bei Löschung geleert (v0109, PRIV-211).
Änderungen 1.2 (Audit 2026-11-22): alle Belege auf 007a4ea90 gemessen; §0 um Frage-IDs (Q-DSB-01…21,
Q-LAW-01…17), Ebenen Rechtspflicht/Auslegung/offene Frage und erweiterte Übersicht ergänzt; §1–§6 um die
Audit-Ergänzungen und 13 Folgefragen erweitert (bestehende Fragen unverändert, mit Frage-ID); §5 Fristen-Beleg
korrigiert (`retention.ts:13`, `:15` statt `queue.ts:450`), SW-API-Cache hält Rohantworten (LEG-27); neue
Komplexe §7–§17 (LEG-11, -13, -16, -23…-25, -28…-33, -35, -38, -40…-42, -47…-53); bisheriger §7 „Was mit der
Antwort geschieht“ ist jetzt §18 und nennt je Frage die PRA-Aufgabe und das Gate.
Änderungen 1.2 (Nachtrag 2026-11-23, gemessen gegen develop ce7e858d0): §8 Ist-Stand nachgeführt (SSE
`values.yaml:607–608`, LEG-24-Belege auf die Schreibpfade, LEG-62…LEG-70) und auf `17-privacy-recovery.md` bezogen;
Q-DSB-15 und Q-DSB-16 präzisiert; neue Fragen Q-DSB-22…Q-DSB-26 und Q-LAW-18, Q-LAW-19 (§8 Frage 4–10); §0 Übersicht
und Zählung, §18 Tabellen erweitert.
```

## 0. Wie dieses Briefing zu lesen ist

Jede Frage ist genau einem oder mehreren Einträgen der Rechtsregistry zugeordnet: LEG-01…LEG-22 in
[`decision-log.md`](decision-log.md) §B, die Audit-Befunde LEG-23…LEG-61 und die Befunde aus `17` LEG-62…LEG-70 in
[`decision-log.md`](decision-log.md) §D.
Die Registry trägt Optionen, Empfehlung, Gate und Durchsetzungspunkt; dieses Dokument ergänzt je Frage den
**Ist-Stand im Code** (gemessen, mit Pfad:Zeile), den **ausgelieferten Default**, die **Norm** und die **konkrete
Frage**. Was mit einer Antwort umgesetzt wird, steht als PRA-Aufgabe in
[`12-implementation-roadmap.md`](12-implementation-roadmap.md); §18 fasst das je Frage zusammen.
Quellenbelege (Wortlaut, URL, Prüfdatum) stehen im Rechtsevidenzregister
[`13-legal-evidence-register.md`](13-legal-evidence-register.md) (L-nn); was dort `UNVERIFIED_AT_SOURCE` ist, wird
hier nicht als Rechtsaussage verwendet. DSGVO-Artikel sind nur **Bezug** (L-12, `UNVERIFIED_AT_SOURCE`, V-07),
nie Wortlaut. EuGH C-34/21 (L-13, V-08) und die BAG-Linie zur „Eignung“ (V-05) sind nicht an der Quelle
verifiziert; die EDSA-Leitlinien 9/2022 (Datenpannen) stehen nur als L-24 `UNVERIFIED_AT_SOURCE` im Register (V-13).

**Pfade.** Backend-Pfade ohne Präfix beginnen mit `src/backend/app/`; Frontend-Pfade (`main.tsx`, `sw.ts`, `pwa/`,
`features/`, `store/`, `pages/`, `layouts/`, `lib/`) mit `src/frontend/src/`. Pfade mit `src/`, `scripts/`, `helm/`,
`docs/` oder `spec/` sind repo-relativ. Zeilen gemessen am SHA `007a4ea90`.

**Frage-IDs.** Die Fragen aus #2517 behalten ihre Nummer je Abschnitt („§1 Frage 2“). Seit v1.2 trägt jede Frage
zusätzlich eine stabile ID: `Q-DSB-nn` richtet sich an den externen DSB (Bewertung im Rahmen bestehender Leitlinien,
Freigabe von Fristen und Texten), `Q-LAW-nn` an die Rechtsberatung (Auslegung ohne gesicherte Leitlinie,
Vertragsgestaltung). Fragen an Product Owner, Betreiber und gewerbliche Kunden (`Q-PO`, `Q-OP`, `Q-CUS`) stehen als
offene Punkte in [`12-implementation-roadmap.md`](12-implementation-roadmap.md); wo eine von ihnen die Rechtsfrage
berührt, ist sie hier nur genannt.

**Drei Ebenen je Komplex.** Die neuen Komplexe (§7–§17) und die Audit-Ergänzungen in §1–§6 trennen:

| Ebene | Bedeutung | Wer entscheidet |
|---|---|---|
| **Rechtspflicht** | folgt aus dem Normtext, nicht aus einer Abwägung | Gesetz |
| **Auslegung** (`INFERRED`) | vertretbare Anwendung auf den Ist-Stand; Leitlinien (L-14…L-22) stützen, binden nicht | DSB/Rechtsberatung bestätigt |
| **Offene Frage** (`LEGAL_REVIEW_REQUIRED`) | ohne externen Rat nicht entscheidbar | DSB / Rechtsberatung |

Ein technischer Befund `CONFIRMED` bestätigt den beschriebenen Ist-Stand, **keinen Rechtsverstoß**.

Drei Fragenkomplexe hatte die Registry vor v1.0 nicht; sie sind mit diesem Dokument als **LEG-20**, **LEG-21** und
**LEG-22** angelegt (Beetfotos, §6). Die Komplexe §7–§17 stammen aus dem Audit 2026-11-22.

| # | Komplex | Herkunft | LEG | Fragen |
|---|---------|----------|-----|--------|
| 1 | Sichtbarkeit der durchführenden Person im Pflegeprotokoll | #2517 Beschreibung Pkt. 1; Nachtrag 2026-11-07 Pkt. 2; Audit | LEG-02, LEG-05 (LEG-19) | Q-DSB-01 |
| 2 | Gelöschte und ehemalige Mitglieder im Pflegeprotokoll | #2517 Beschreibung Pkt. 2; LEG-15 Frage 3 (v1.1); Audit | LEG-15, LEG-06, LEG-54 | Q-DSB-02, Q-DSB-03 |
| 3 | Freitexte gelöschter Mitglieder | #2517 Beschreibung Pkt. 3–4; Kommentar 2026-10-20; Audit | LEG-08, LEG-34 | Q-DSB-04, Q-LAW-06, Q-LAW-11 |
| 4 | Zweckänderung durch das M4-Backfill; `pest_control` bei Mandantenlöschung | #2517 Nachtrag 2026-11-07 Pkt. 1, 4, 5; Audit | LEG-07 | Q-DSB-05 |
| 5 | Gerätespeicher (Offline) | #2517 Kommentar 2026-11-09 Pkt. 1–5; Audit | LEG-09, LEG-10, LEG-12, LEG-27, LEG-37 | Q-DSB-06, Q-DSB-07, Q-LAW-16, Q-LAW-17 |
| 6 | Beetfotos und Plan-Unterlagen | aus #2643 verschoben (2026-11-14) Pkt. 1–3; Audit | **LEG-20, LEG-21, LEG-22**, LEG-55 | Q-DSB-09…11, Q-LAW-12 |
| 7 | Einschränkung, Widerspruch und Legal Hold | Audit | LEG-23, LEG-35 | Q-DSB-14 |
| 8 | Backups, Restore und Widerrufe | Audit; Nachtrag 2026-11-23 (`17`) | LEG-11, LEG-24, LEG-25, LEG-26, LEG-62…LEG-70 | Q-DSB-15, Q-DSB-16, Q-DSB-22…26, Q-LAW-14, Q-LAW-18, Q-LAW-19 |
| 9 | Beschäftigtendaten: Leistungsdaten, Aktorik-Protokoll, Mandantenklassifizierung | Audit (vertieft §1 Frage 2) | LEG-05, LEG-28, LEG-29, LEG-30 | Q-LAW-01…03, Q-DSB-21 |
| 10 | KI-Cloud-Verarbeitung und MCP | Audit | LEG-31, LEG-51, LEG-52 | Q-DSB-19, Q-LAW-10 |
| 11 | Rollenmodell, Empfänger, Drittland, Unterauftragsverarbeiter, Plattform-Export | Audit | LEG-01, LEG-13, LEG-33, LEG-53 | Q-LAW-05, Q-LAW-07…09 |
| 12 | Datenschutzverletzungen | Audit | LEG-32 | Q-DSB-20, Q-LAW-15 |
| 13 | Transparenz: Art. 13, Art. 15 Abs. 1, Identität beim Export | Audit | LEG-41, LEG-50, LEG-38 | Q-DSB-13, Q-LAW-13 |
| 14 | Fotos fremder Personen an Erkennungsdienste | Audit | LEG-40, LEG-57 | Q-DSB-12 |
| 15 | Pflichtzeilen nach Mandantenlöschung | Audit (Gegenfrage zu §4 Frage 3) | LEG-47 | Q-LAW-04 |
| 16 | GPS an Wetterdienste; Fehlertracking (LIA) | Audit | LEG-49, LEG-16 | Q-DSB-18 |
| 17 | Verschlüsselung ruhender Daten; DSFA je Betriebsmodell | Audit (vertieft §5 Frage 4) | LEG-42, LEG-12, LEG-48 | Q-DSB-17, Q-DSB-08 |

Zählung: 26 DSB-Fragen und 19 Fragen an die Rechtsberatung (45; Nachtrag 2026-11-23: +5 DSB, +2 Recht in §8). Davon greifen 14 eine Frage aus #2517 auf
(Q-DSB-01…11 ganz oder teilweise; Q-LAW-01, Q-LAW-03, Q-LAW-12 als Teilaspekt); sie werden in §1–§6 nicht neu
gestellt, sondern um die Audit-Erkenntnis ergänzt.

## 1. Sichtbarkeit der durchführenden Person (LEG-02, LEG-05)

**Ist-Stand.** Jedes Pflegeereignis trägt `performed_by_user_key`, gestempelt aus dem Token
(`domain/services/care_event_service.py:528`); die ungefilterte Liste des Mandanten (`GET /care-events`, optional
`?location_key=`, `api/v1/care_events/tenant_router.py:45–129`) und die Beet-Historie (`GET /locations/{key}/history`,
`api/v1/locations/tenant_router.py:818–860`) zeigen jedem Mitglied den Anzeigenamen der durchführenden Person (nie den
Kontoschlüssel). Dieselbe Liste lädt jedes Mitglied — auch `viewer`; die Route prüft nur `get_current_tenant` — mit
`format=csv` als Datei, Spalten `performed_by` und `performed_for` eingeschlossen
(`domain/engines/care_event_csv_engine.py:22–40`). Das Default-Fenster von 90 Tagen gilt nur ohne Bereich, Beet oder
Pflanze; mit `from`/`to` reicht die Datei bis 5 Jahre zurück, bis 50 000 Zeilen (`care_event_service.py:405–447`).
Der Personenfilter ist eingeschränkt (SR-020/E-16, `check_performed_by_filter`, `care_event_service.py:151–178`), das
Datum nicht: die Einschränkung entfernt die Abkürzung, nicht die Daten (`05` §1). Weder Filter noch Export werden
protokolliert (keine `ATTRIBUTION_*`-Aktion in `common/enums.py:1990–2025`).
Für eine Pflege-Bestätigung gilt seit 2026-11-14 **eine Regel: immer die aufrufende Person**. Das Audit bestätigt sie
auf allen vier Wegen: REST (`api/v1/care_reminders/router.py:159–170`), Benachrichtigungsaktion
(`api/v1/notifications/tenant_router.py:215–220`), Aufgabenwarteschlange (`domain/services/task_service.py:1840–1855`
→ `care_reminder_service.record_care_task_completion`, `domain/services/care_reminder_service.py:1290–1368`;
#2961/#2968) und MCP (`mcp_server/tools/care.py:77–86`, `ctx.principal.account_key`); gepinnt durch
`src/backend/tests/unit/guards/test_care_confirmation_names_its_performer.py`. Die Bestätigung selbst hat keine eigene
Aufbewahrung; die 5 Jahre gelten für das abgeleitete Pflegeereignis (R-25, `retention_care_event_retention_years = 5`,
`config/settings.py:125`; Widerspruch W-19 in `14` aufgelöst).

**Ausgelieferter Default.** Sichtbar und exportierbar für alle Mitglieder, 5 Jahre; Einstellung
`attribution_visibility` je Mandantenklasse ist spezifiziert (DEC-10, DA-04), nicht gebaut (0 Treffer in `app/`).

**Ergänzung Audit 2026-11-22.** *Auslegung:* Die Trennung „Inhalt lit. b / Sichtbarkeit der Zurechnung lit. f“
(DA-02 Option B, LEG-19) ist methodisch tragfähig; lit. b für den Inhalt setzt voraus, dass Nutzungsbedingungen,
Satzung oder Arbeitsvertrag die Protokollierung als Leistungsbestandteil ausweisen — heute nicht belegt. Der Ist-Stand
(Name 5 Jahre lesbar und an jedes Mitglied exportierbar, ohne Audit) liegt außerhalb dessen, was die eigene LIA-1
(`06` §4) trägt. Der Personenfilter ist eine Abkürzungssperre, keine Zugriffsbeschränkung.

**Fragen.**
1. **Q-DSB-01** — Trägt Art. 6 Abs. 1 lit. f (berechtigtes Interesse der Gruppe an nachvollziehbarer Pflege) die
   Sichtbarkeit der durchführenden Person für **alle** Mitglieder, oder nur für Leitung + die Person selbst
   (LEG-02, LIA-1)?
2. In gewerblichen Mandanten ist „wer hat bestätigt“ ein Aufzeichnen von Beschäftigtentätigkeit, 5 Jahre lang
   je Person filterbar (Leitung/`management`). Braucht das eine Grundlage nach § 26 BDSG / Art. 88 DSGVO
   (nach EuGH C-34/21, L-09/L-10) und eine Mitbestimmung nach § 87 Abs. 1 Nr. 6 BetrVG? Welche Pflichten hat die
   Plattform gegenüber dem Arbeitgeber-Mandanten (LEG-05)? *Vertieft in §9 als Q-LAW-01 und Q-LAW-03.*
3. Bestätigt die DSB die Regel „immer die aufrufende Person“ (DEC-09)? Die Sichtbarkeitsentscheidung (Frage 1)
   ändert nur, wer es sieht, nicht, was gespeichert wird. *Audit: auf allen vier Wegen umgesetzt; keine
   Ergänzung.*
4. **Q-DSB-01 (Ergänzung)** — Ist eine eigene, kürzere Frist für die **Zurechnung** (Vorschlag ≤ 2 Jahre, danach
   Marker bei unverändertem Inhalt; Setting „R-25a“) gegenüber 5 Jahren für den Inhalt angemessen? Hängt ab:
   Wert von R-25a und Default von `attribution_visibility` in PRA-2.05. Ohne Freigabe auslieferbar sind dort die
   Rollenschranke für CSV-Namen (PRIV-307), das Audit von Filter und Export (PRIV-308/405) und die
   Namensunterdrückung (PRIV-112); nur der Fristwert wartet auf die Antwort.

## 2. Gelöschte und ehemalige Mitglieder (LEG-15, LEG-06)

**Ist-Stand.** Bei Kontolöschung erhalten die fünf Kontoverweise eines Pflegeereignisses (`performed_by_user_key`,
`performed_for_user_key`, `created_by`, `voided_by`, `redacted_by`) den Sammelmarker `_anonymized`
(`domain/engines/erasure_engine.py:162–236`), der **alle** gelöschten Mitglieder eines Mandanten bündelt; ein
Filter auf `_anonymized` wird mit 422 abgewiesen (`care_event_service.py:164–170`, `04` §2). Ein Pseudonym
(Tombstone `anon_<16 hex>` = `"anon_" + sha256(user_key + salt)[:16]`, instanzweit, kein HMAC, keine
Mandantenbindung; `ErasureEngine.compute_tombstone_hash`, `erasure_engine.py:1235–1256`) erhalten die
Pflichtaufzeichnungen, darunter `treatment_applications.applied_by_key` und `harvest_batches.harvested_by_key`
(`erasure_engine.py:84–122`), sowie `erasure_requests`, `mcp_audit_log`, `security_audit_log` und `consent_records`
(`:860–932`).
Seit 2026-11-15 (Betreiberfreigabe DEC-16/DEC-28) erhält das Plan-Audit `garden_plan_audit.user_key` bei Löschung
den Marker statt des Pseudonyms (`erasure_engine.py:269–283`). Migration `v0109_privacy_tombstone_copies` setzt davor
geschriebene Pseudonyme dort und ins Pflegeprotokoll kopierte Pseudonyme (`care_events.performed_by_user_key`,
`created_by`) auf den Marker; Pseudonyme in übrigen Feldern außerhalb der Allowlist zählt sie nur, und der nur lesende
Beat `privacy.consistency` zählt sie seither täglich (`migrations/versions/v0109_privacy_tombstone_copies.py`,
Schritte 1–3; `tasks/privacy_consistency.py:18`; `09` §3). Das Audit führt diesen Teil als `ALREADY_FIXED`.
**Nicht gebaut** ist das mandantengebundene Pseudonym `anon2_` für neue Zeilen (DEC-25, PRIV-238): Die Leser erkennen
die Form (`domain/models/privacy.py:19–25`), kein Pfad schreibt sie; der einzige Pfad, der sie behandelt, wandelt sie
beim Import in den Marker (`domain/engines/tenant_import_engine.py:401–404`).

**Ergänzung Audit 2026-11-22 — Verknüpfbarkeit.** Die Mandantenlöschung schreibt denselben Tombstone auch für
**lebende** Konten (`domain/engines/tenant_erasure_engine.py:189–209`, `:451–467`); Mandantenarchive enthalten `anon_`
„wie gespeichert“ (`domain/engines/tenant_export_engine.py:186–215`); der Import übernimmt `anon_` unverändert
(`tenant_import_engine.py:405–406`, LEG-54). Wer zwei Archive besitzt, erkennt „dieselbe gelöschte Person“ über
Mandanten hinweg. Das Salt `ERASURE_TOMBSTONE_SALT` ist die einzige Schranke gegen Rückführung; es wird nicht rotiert
und zusätzlich für `compute_request_key` (`erasure_engine.py:1214–1233`) und die Client-Event-Digests verwendet; die
Kontoschlüssel `users._key` sind numerisch (ArangoDB-Standardgenerator). API-Antworten exponieren `*_by_key` nicht
(`api/v1/harvest/schemas.py:73–88`, `api/v1/ipm/schemas.py:299–363`). *Rechtspflicht:* Pseudonymisierte Daten
bleiben personenbezogen (Art. 4 Nr. 5; L-14, L-15); ein Tombstone ist kein Löschnachweis, sondern weiter zu
schützendes Datum (Art. 32 Abs. 1 lit. a). *Auslegung:* Verknüpfbarkeit innerhalb eines Mandanten trägt den Zweck der
Pflichtaufzeichnung; mandantenübergreifende Verknüpfbarkeit trägt kein genannter Zweck außer der Art.-15-Suche, die
auch mit `(tenant, user)`-Bindung funktioniert (DEC-25). Der Code-Kommentar `erasure_engine.py:857–859` („must no
longer be stored as a personal identifier“) beschreibt das zu stark.

**Ergänzung Audit 2026-11-22 — ehemalige Mitglieder.** Das Ende einer Mitgliedschaft löscht nur Mitgliedschaft,
Kanten und `location_assignments` (`data_access/arango/membership_repository.py:130–142`); der Anzeigename wird live
aus `users/<key>` aufgelöst, ohne Mitgliedschaftsprüfung (`data_access/arango/care_event_repository.py:657–662`); die
Leitung kann unbefristet auf Ex-Mitglieder filtern (`care_event_service.py:151–178`); die Unterdrückung ist nicht
gebaut (`grep RETENTION_FORMER_MEMBER\|former_member` in `src/` → 0). Der Art.-15-Export bindet mandantenbezogene
Quellen an **aktuelle** Mitgliedschaften (`domain/services/privacy_service.py:2343`, `:3564–3573`;
`data_access/arango/personal_data_repository.py:122–131`); Zeilen der Person in verlassenen Mandanten fehlen.
*Rechtspflicht:* Speicherbegrenzung (Art. 5 Abs. 1 lit. e) verlangt eine Frist für die identifizierende Zurechnung an
nicht mehr Beteiligte. *Auslegung:* Art. 15 erfasst alle beim Verantwortlichen verarbeiteten Daten (L-19); die Bindung
an aktuelle Mitgliedschaften ist eine sinnvolle Missbrauchssperre (SCR-001), ein sicherer Pfad wären nur
server-gestempelte Kontofelder (`created_by`, `performed_by_user_key` aus dem Token).

**Ausgelieferter Default.** Tombstone instanzweit; Ex-Mitglieder unbefristet sichtbar und filterbar; Art.-15-Export
ohne verlassene Mandanten.

**Fragen.**
1. **Q-DSB-03** — Ist ein deterministisches, mandantengebundenes Pseudonym über 5 Jahre (Art.-15-Suche nach der
   eigenen Person bleibt möglich) verhältnismäßig, oder muss es zufällig sein (LEG-15, L-14/L-15)?
2. **Q-DSB-02 (a)** — Ab welcher Frist nach Ende der Mitgliedschaft wird der Anzeigename ehemaliger Mitglieder
   unterdrückt (Vorschlag 90 Tage, LEG-06 a)?
3. **Q-DSB-03** — Bestätigt die DSB, dass das Plan-Audit nach der Löschung niemanden mehr verknüpft (Marker statt
   Pseudonym, umgesetzt), obwohl die Zeile als Nachweis einer Planlöschung 365 Tage bleibt (R-26)? Die Änderung ist
   einschränkend; die Frage hält nur fest, dass LEG-15 diesen Teil mit abdeckt.
4. **Q-DSB-02 (b), neu** — Genügt es, verlassene Mandanten aus dem Art.-15-Export auszulassen, oder muss eine
   Teilquelle „nur server-gestempelte Kontofelder“ (`created_by`, `performed_by_user_key`) aufgenommen werden
   (Alternative: dokumentierter `disclosure_gap` im Bündel)? Hängt ab: PRA-2.04; Default bis zur Antwort: Teilquelle
   aufnehmen (Audit-Empfehlung). Wo die Auskunft für Zeilen in einem Mandanten zu erteilen ist, fragt §3 Frage 5
   (Q-LAW-06).
5. **Q-DSB-03 (Ergänzung)** — Ändert die heute bestehende mandantenübergreifende Verknüpfbarkeit (Tombstone auch für
   lebende Konten bei Mandantenlöschung, Archive, Import) und die Mehrfachverwendung des nicht rotierten Salts die
   Verhältnismäßigkeitsbewertung des **Bestands**? Hängt ab: ob der Bestand bleibt (PRIV-202) oder migriert wird;
   PRA-1.07 (`anon2_`, Importregel, Residue-Scan) ist schutzverstärkend und ohne Freigabe auslieferbar. Verwahrung und
   Rotation des Salts klärt der Betreiber (Q-OP-04 in `12`).

## 3. Freitexte gelöschter Mitglieder (LEG-08)

**Ist-Stand.** Freitexte bleiben nach der Löschung im gemeinsamen Mandanten: die Kontolöschung ersetzt dort nur
Kontoverweise (`erasure_engine.py:162–236` Pflegeprotokoll, `:247–268` Gartenobjekte/Beetvorlagen, `:291–333`
Tagebuch/Task-Kommentare; Begründung `:172–174`). Die Leitung schwärzt reaktiv (`POST /care-events/{key}/redact`,
`api/v1/care_events/tenant_router.py:231–255`, GP-FR-109) und erhält **keine Liste** der betroffenen Zeilen
(`grep privacy_review_items\|PRIVACY_REVIEW` → 0); für andere Collections gibt es keinen Schwärzungspfad. Die
Schwärzung ersetzt `FREE_TEXT_FIELDS = (summary, reason, observed_outcome, product_label, performed_by_label)` und
`void_reason` (`domain/models/care_event.py:83`, `data_access/arango/care_event_repository.py:1046–1050`) und die Kopie
`feeding_events.product_label` (`:1052–1059`). **`care_events.material`** (`care_event.py:166`, API bis 200 Zeichen
`:304`) und die Messwert-Strings `measurements[].source`/`.extraction_method` (`:254–256`) berührt weder die
Schwärzung noch die R-25-Bereinigung (`care_event_repository.py:573–595`); `material` steht in CSV
(`care_event_csv_engine.py:37`) und API (`api/v1/care_events/schemas.py:110`) und speist den Nährstoffhinweis
(`domain/engines/task_completion_engine.py:125`). Ebenfalls Freitext mit möglichem Personenbezug:
`bed_templates.name` (z. B. „Omas Hochbeet“, bis 200 Zeichen, `domain/models/bed_template.py:128`); er bleibt nach
Löschung der Urheberin im Mandanten (nur `created_by` wird Marker), wird beim Platzieren in `Location.name` kopiert
(`domain/services/garden_plan_service.py:771`) und landet in `garden_plan_audit.summary`
(`domain/services/garden_plan_import_service.py:1131–1139`).
Spezifiziert ist eine Prüfwarteschlange mit vollständiger Entdeckung (DEC-06/DEC-27), nicht gebaut; der Schalter
`PRIVACY_REVIEW_AUTO_REDACT_ON_SLA` existiert im Code nicht. R-25 (5 Jahre) ist die einzige Freitextfrist; Tagebuch,
Task-Kommentare, Objekt-/Beetnotizen und Vorlagen bleiben bis zur Mandantenlöschung.

**Ergänzung Audit 2026-11-22 — Umfang größer als in v1.1.** Jede Planänderung legt einen vollständigen Planexport als
`snapshot` in `garden_plan_audit` ab (`garden_plan_import_service.py:1146–1149`, bis 20 je Site, 365 Tage, R-26) —
mit Namen und Notizen; `restore_snapshot` (`:420–441`, `api/v1/garden_plan/tenant_router.py:867–890`) spielt
geschwärzte oder gelöschte Texte zurück (LEG-34). Der UI-Begriff `PERFORMED_BY_ANONYMISED` (`care_event.py:427`)
verspricht mehr, als der Datenzustand hergibt (Freitext bleibt). *Rechtspflicht:* Art. 17 Abs. 3 nennt abschließende
Ausnahmen; eine Ausnahme „Historie der Gruppe“ kennt die Norm nicht (W-17 in `14`). Die vollständige Löschung muss
nachweisbar sein (Art. 5 Abs. 2) — ohne Entdeckung nicht erbringbar. Berichtigte oder geschwärzte Daten dürfen nicht
durch einen Restore auf den Altstand zurückfallen (Art. 5 Abs. 1 lit. d, Art. 16). Art. 9 Abs. 1 greift für
tatsächlich eingegebene Gesundheitsdaten unabhängig vom Zweck der App; Hinweise auf Straftaten berühren Art. 10.
*Auslegung:* Freitexte, die die Person benennen oder beschreiben, sind Daten **der Person**; als Grundlage des
Behaltens kommt nur ein Abwägungsergebnis (Art. 17 Abs. 1 lit. c i. V. m. Art. 21) oder die Einordnung als
mandanteneigene Daten in Betracht. „Behalten + fristgebundene Prüfung mit vollständiger Entdeckung“ (DEC-27) kann
verhältnismäßig sein; ohne Liste ist reaktive Schwärzung faktisch unwirksam. Eine automatische Inhaltsanalyse auf
Art.-9-Begriffe verlangt die DSGVO nicht und widerspräche Art. 25.

**Ausgelieferter Default.** Behalten; manuelle Schwärzung nur im Pflegeprotokoll; keine Prüfwarteschlange;
Snapshots ungeschwärzt und wiederherstellbar.

**Fragen.**
1. **Q-DSB-04** — Genügt „behalten + Prüfung durch die Leitung“ (Art. 17 Abs. 3, Abwägung nach Art. 6 Abs. 1 lit. f),
   oder müssen Freitexte gelöschter Mitglieder automatisch geschwärzt werden?
2. **Q-DSB-04** — Dürfen Leads über die Schwärzung entscheiden, ist eine Frist von 30 Tagen angemessen, und soll nach
   Ablauf automatisch geschwärzt werden (Schalter `PRIVACY_REVIEW_AUTO_REDACT_ON_SLA`, Default aus)?
3. **Q-DSB-04** — Gilt dieselbe Abwägung für `bed_templates.name` / den kopierten Beetnamen und für
   `care_events.material`, oder müssen beide in den Schwärzungsumfang? (Produktfolge für den Nährstoffhinweis:
   Q-PO-01 in `12`.)
4. **Q-DSB-04 (Ergänzung)** — Gehören Plan-Snapshots (365 Tage, wiederherstellbar) und die Messwert-Strings in
   denselben Umfang, und auf welche Grundlage stützt sich das Behalten nach Art. 17 Abs. 3 / Art. 21 (W-17)? Hängt ab:
   Feldmenge in PRA-2.01, Snapshot-Schwärzung und Restore-Sperre in PRA-2.02 (beide schutzverstärkend, ohne
   Freigabe); nur die Auto-Schwärzung nach SLA wartet auf die Antwort. Snapshot-Frist: Q-PO-02 in `12`.
5. **Q-LAW-06, neu** — Sind Mandanten bzw. ihre Leitung für Freitexte über Dritte und für Zeilen ehemaliger Mitglieder
   eigenständige oder gemeinsame Verantwortliche (L-18), und wo ist die Auskunft für solche Zeilen zu erteilen? Hängt
   ab: Entscheidungsbefugnis der Leads in der Prüfwarteschlange (PRA-2.01), Art.-15-Teilquelle (PRA-2.04, §2 Frage 4).
6. **Q-LAW-11, neu** — Freitexte einer Cannabis-/Gemüse-/Kräuter-App können Gesundheitsdaten und Hinweise auf
   Straftaten enthalten (Tagebuch bis 5000 Zeichen, KI-Chats, Nachernte-Notizen, Task-Kommentare; über 50
   Freitextfelder). Folgt daraus eine DSFA-Pflicht nach Art. 35 Abs. 3 lit. b, und wie ist die Art.-9-Nähe des
   Cannabiskontexts (RISK-18) zu bewerten? § 22 BDSG behandelt das Paket nicht; er wird erst relevant, wenn eine
   Funktion Art.-9-Daten zielgerichtet verarbeiten soll. Hängt ab: Hinweistexte und Längengrenzen (PRA-2.01),
   DSFA-Abschnitt (PRA-3.04).

## 4. Zweckänderung durch das M4-Backfill; `pest_control` bei Mandantenlöschung (LEG-07)

**Ist-Stand.** Das Backfill v0104 (`ACCOUNT_FIELDS`, `domain/engines/care_event_backfill_mapper.py:71–77`;
`account_of` `:183–191`, Tombstone → Marker; `map_document` `:271–306`) kopiert `applied_by_key` / `harvested_by_key`
aus Aufzeichnungen nach Art. 6 Abs. 1 lit. c (PflSchG § 11, KCanG; NFR-011 R-16/R-17) ins Pflegeprotokoll, wo sie der
Beet-Historie und dem Personenfilter dienen; Freitexte und `notes` werden nicht kopiert
(`migrations/versions/v0104_care_events_backfill.py:19–21`). Die Kopie ist **fortlaufend**: der tägliche Job
`care_events.consistency` ruft denselben Mapper (`domain/services/care_event_consistency_service.py:129`, Fenster
7 Tage `config/settings.py:1287`). Ein Schalter `PRIVACY_BACKFILL_COPIES_PERFORMER` ist spezifiziert (E01), im Code und
in `helm/` nicht vorhanden. Bewässerungs-/Düngeereignisse werden ohne Kontoverweis kopiert (Personenbezug nur über den
Mandanten). Seit v0111 (2026-11-15) tragen `watering_events`, `watering_logs`, `tank_fill_events` und
`maintenance_logs` ein Feld `performed_by_user_key` neben dem Freitext `performed_by`; kein Pfad stempelt es, jeder Wert
ist `null`, und der Mapper liest es nicht (`09` §5, `08` §3.4). Bei Mandantenlöschung werden die
Pflegeprotokollzeilen gelöscht, `pest_control`/`ipm` eingeschlossen (Kategorie `care_event_backfill_mapper.py:83`;
`domain/engines/tenant_erasure_engine.py:111–117`); der § 11-Nachweis ist die pseudonymisiert aufbewahrte
`treatment_applications`-Zeile (`:189`, `:208–209`, Begründungen `:44–57`) — unabhängig von `record_keeping`.

**Ergänzung Audit 2026-11-22.** *Rechtspflicht:* Weiterverarbeitung zu einem anderen Zweck nur bei Vereinbarkeit
(Art. 6 Abs. 4 lit. a–e) oder mit eigener Grundlage; Information über den neuen Zweck (Art. 13 Abs. 3). In beruflichen
Betrieben ist `applied_by_key` Pflichtangabe („unter Angabe des jeweiligen Anwenders“, § 11 Abs. 2 S. 2 PflSchG, L-01);
die Pflichtfrist beträgt 3 Jahre ab 1. Januar des Folgejahres (§ 11 Abs. 3; Fristlänge `VERIFIED_SPEC`, L-03).
*Auslegung:* Für Vereinbarkeit spricht der enge Zusammenhang (gleiche Tatsache, gleicher Mandant, lit. a/b); dagegen
sprechen die Eignung des Ziels (Personenfilter, CSV) zur Leistungs- und Verhaltensbewertung (lit. d) und die längere
Zielfrist (5 Jahre). Da die Kopie über den Konsistenzjob dauerhaft läuft, ist sie keine einmalige Migration, sondern
eine fortlaufende Zweckänderung; ein Schalter muss Migration **und** Konsistenzjob abdecken. In Beschäftigtenkontexten
ist Vereinbarkeit fraglich; für Hobby-Mandanten ist schon die Quelle lit. b, die Kopie unkritisch. Das Löschen der
`pest_control`-Kopie bei Mandantenlöschung hält das Audit für unbedenklich, solange `treatment_applications` der
Nachweis bleibt — das eigentliche Problem liegt in der Gegenrichtung (§15).

**Ausgelieferter Default.** Kopie aktiv für alle Mandanten, fortlaufend; `pest_control`-Zeilen werden mit dem Mandanten
gelöscht.

**Fragen.**
1. **Q-DSB-05** — Ist die Weiterverarbeitung der kopierten durchführenden Person mit dem ursprünglichen Zweck vereinbar
   (Art. 5 Abs. 1 lit. b, Art. 6 Abs. 4), und decken Datenschutzhinweis und Verzeichnis sie ab? *Ergänzung Audit:*
   Gilt das auch für die **fortlaufende** Kopie durch den täglichen Konsistenzjob, und auch in gewerblichen Mandanten
   (Vorschlag: `commercial` → keine Kopie)? Hängt ab: PRA-2.08 (Schalter mit Default = Bestand und `commercial`-Regel
   ohne Freigabe; das Umschalten des globalen Defaults braucht sie).
2. Gering: Gilt dasselbe für die kopierten Bewässerungs-/Düngeereignisse ohne Kontoverweis, und auch dann, wenn
   die neuen Schlüsselfelder (v0111) später gestempelt werden (E13)? *Audit: keine Ergänzung.*
3. **Q-DSB-05** — Ist das Löschen der `pest_control`-Zeilen bei Mandantenlöschung haltbar, solange `treatment_applications`
   der einzige § 11-Nachweis bleibt? *Audit (Auslegung): unbedenklich; erbeten ist eine Bestätigung. Gegenfrage
   Q-LAW-04 in §15.*

## 5. Gerätespeicher (LEG-09, LEG-10, LEG-12, LEG-27, LEG-37)

**Ist-Stand.** IndexedDB `kp-plan-cache`, `kp-write-queue` und Cache Storage `kp:{user}:{tenant}`, `kp-sw-state`
sowie App-Shell-Caches (`pwa/storageWipe.ts:13`, `:23`; `sw.ts:57`). Der Service Worker registriert sich bedingungslos
beim Start (`main.tsx:43`); einzige Sperre ist der Betreiber-Kill-Switch `PWA_CACHING_ENABLED` (Default `true`,
`helm/kamerplanter/values.yaml:1063`; `lib/serviceWorkerRegistration.ts:103–107`). Der Plan-Cache schreibt bei jedem
Online-Lesen (`features/gardenPlanner/offline/planCache.ts:160–167`), der Schreibpuffer ebenso
(`features/gardenPlanner/offline/queue.ts:143–150`); der SW-API-Cache füllt sich, sobald der Store Nutzer und Mandant
kennt (`store/sessionListener.ts:89–96` → `sw.ts:314–319`). Es gibt keinen Schalter (`grep "kp-offline-mode\|offlineMode"`
→ 0). Der Schreibpuffer hält offene Einträge 365 Tage, fehlgeschlagene/kollidierende 90 Tage — hart kodiert
(`features/gardenPlanner/offline/retention.ts:13` `ENTRY_MAX_AGE_DAYS = 365`, `:15` `UNSENDABLE_MAX_AGE_DAYS = 90`;
v1.1 nannte `queue.ts:450`); bereinigt wird nur beim App-Start (`main.tsx:49–55`) und vor dem Sync
(`queue.ts:339–369`). Es gibt keine Quarantäne (kein Zustand `quarantined`, `queueTypes.ts:61`), der Logout-Wipe
wird nicht abgewartet (`layouts/MainLayout.tsx:105–108`). `07` schlägt Opt-in für alle (DEC-29), Quarantäne 14 Tage,
Fristen 90/30 Tage und einen Shared-Device-Modus vor (DEC-12); gebaut ist nichts davon.
Serverseitig korrekt: Einträge gelöschter oder geschlossener Konten werden mit 401 abgewiesen, Einträge ehemaliger
Mitglieder mit 403 (`domain/engines/full_auth_provider.py:70–73`, `common/auth.py:169`, `:237–248`).

**Ergänzung Audit 2026-11-22.** (a) Der SW-API-Cache `kp:{user}:{tenant}` ist nicht leer, wie REQ-025 §10 und die
Nutzerdoku (`docs/de/user-guide/privacy.md:426`) sagen: Er speichert die Rohantworten von `/sites`,
`/sites/{k}/plan` und `/locations/{k}/summary` unverändert (`pwa/apiCache.ts:617–626`, `pwa/cachePolicy.ts:87–91`,
`sw.ts:193–207`, `:232–243`), darunter `plan_updated_by_name` und Beet-`notes`/`description` anderer Mitglieder;
der IndexedDB-Cache nullt dieselben Felder (`planCache.ts:338–356`) — LEG-27. (b) „Angemeldet bleiben“ ist
implementiert (`pages/auth/LoginPage.tsx:39`, `:85`, `:198–205`; `api/v1/auth/router.py:251–269`), entgegen
`07` PRIV-524 — LEG-37. *Rechtspflicht (TDDDG):* Speichern und Auslesen auf dem Endgerät nur mit Einwilligung
(§ 25 Abs. 1), außer kumulativ „unbedingt erforderlich“ **und** Dienst „vom Nutzer ausdrücklich gewünscht“ (Abs. 2
Nr. 2, L-11). *Rechtspflicht (DSGVO, getrennt):* Grundlage der Inhalte Art. 6 Abs. 1 lit. b; Art. 5 Abs. 1 lit. c/e und
Art. 25 Abs. 2 zusätzlich; eine absolute Fernlöschpflicht für Kopien auf fremden Offline-Geräten folgt aus Art. 17
nicht; Nutzerdoku und REQ-025 §10 müssen den Cache-Inhalt zutreffend beschreiben (Art. 12/13). *Auslegung:* App-Shell
ist von Abs. 2 Nr. 2 gedeckt; Lesecache, Puffer und SW-API-Cache dienen der „Offline-Nutzung“, die der bloße Aufruf
nicht ausdrücklich wünscht; „unbedingt erforderlich“ schließt den **Umfang** ein, was LEG-27 zusätzlich belastet.
Ein persistentes Refresh-Cookie nach ausdrücklichem Anhaken ist vertretbar. Für geteilte Geräte verlangen Art. 25/32
mindestens eine **Grundsicherung** (abgewarteter Logout-Wipe, Schlüsselhygiene, Quarantäne bei totem Konto und bei
Login eines anderen Nutzers, Minimierung im SW-Cache); ein reiner Hinweis „immer abmelden“ verlagert das Risiko
vollständig auf den Nutzer. Ein eigener Shared-Device-**Modus** ist keine Rechtspflicht.

**Ausgelieferter Default.** Speicherung bei jedem Online-Lesen ohne Nutzerhandlung; Fristen 365/90 Tage; keine
Quarantäne; SW-API-Cache ohne Projektion.

**Fragen** (je Speicherkategorie, `07` §2):
1. **Q-DSB-06** — Ist die Speicherung „unbedingt erforderlich“ nach § 25 Abs. 2 Nr. 2 TDDDG (vom Nutzer gewünschte
   Offline-Funktion), und genügt ein Opt-in-Schalter als „ausdrücklich gewünscht“ (LEG-09, L-11)? *Ergänzung Audit:*
   Ist der Puffer (entsteht erst bei einer Offline-Erfassung, also einer Nutzerhandlung) anders zu bewerten als der
   Lesecache (entsteht bei jedem Online-Lesen), und muss der Schalter alle drei Lesespeicher und den Puffer erfassen?
   Hängt ab: PRA-2.15 (Opt-in), PRA-0.07 (Projektion, ohne Freigabe).
2. **Q-DSB-07** — Sind 365/90 Tage angemessen, insbesondere auf geteilten Geräten in Gemeinschaftsgärten; soll der
   Betreiber kürzere Fristen setzen können (LEG-10)? *Audit: Werte hart kodiert gemessen; Vorschlag Defaults
   90/30/14 Tage mit Obergrenzen 365/90/30 (PRA-2.15).*
3. **Q-DSB-07** — Art. 17: Genügt es, die Lücke zu dokumentieren (ein auf Gerät A gelöschtes Konto lässt gepufferte
   Einträge auf Gerät B bis Fristablauf), oder ist die Quarantäne beim nächsten Online-Kontakt nötig (LEG-10)?
4. Braucht das Verzeichnis einen Eintrag „Speicherung auf dem Endgerät“, und berührt das die DSFA (LEG-12)?
   *Zusammen mit der fortgeschriebenen Schwellwertprüfung gestellt in §17 Frage 2 (Q-DSB-08).*
5. **Q-DSB-07** — Geteiltes Gerät, gleiches Browserprofil: Einträge sind mit Entwicklerwerkzeugen lesbar. Genügt ein
   dokumentierter Hinweis „immer ausdrücklich abmelden“, oder ist Löschen am Sitzungsende nötig (LEG-10)?
   *Ergänzung Audit:* Bestätigt die DSB die Trennung „Grundsicherung geboten (PRA-0.08, ohne Freigabe) —
   Shared-Device-Modus nur Empfehlung (PRA-2.17)“?
6. **Q-LAW-16, neu** — Bis zur Umsetzung von DEC-29 speichert jede Bestandsinstallation ohne Nutzerhandlung
   (`main.tsx:43`, `planCache.ts:160–167`). Wie hoch ist das Übergangsrisiko nach § 25 TDDDG, im Verhältnis zu
   Art. 6 Abs. 1 lit. b, und ist ein Interim (z. B. Abschalten des Lesecaches über `PWA_CACHING_ENABLED`) vor PRA-2.15
   geboten? Default bis zur Antwort: `processing_allowed = provisorisch` mit Prüfdatum (DA-07).
7. **Q-LAW-17, neu** — Namen und Beet-Notizen **anderer** Mitglieder liegen im SW-Cache eines fremden Geräts (LEG-27).
   Folgt daraus eine Informationspflicht nach Art. 14 gegenüber diesen Mitgliedern, oder genügt der allgemeine
   Hinweis? Die Projektion (PRA-0.07) beseitigt den Großteil; der Informationstext läuft über PRA-2.18.

## 6. Beetfotos und Plan-Unterlagen (LEG-20, LEG-21, LEG-22)

**Ist-Stand.** Beetfotos (Kategorie `location`) und Plan-Unterlagen (`garden_plan_underlay`) liegen im Löschumfang
`user_diary_attachments` (`erasure_engine.STORAGE_CLEANUP_RULES`, `erasure_engine.py:491–530`; Kategorienliste
`data_access/storage/local_fs_adapter.py:577–600`): bei Kontolöschung bleibt die Datei für die übrigen Mitglieder,
`created_by` wird `_anonymized`, EXIF wird entfernt. Seit v0109 (2026-11-15, PRIV-211) leert derselbe Schreibvorgang
auch den ursprünglichen Dateinamen `original_filename`, der oft den Namen der Besitzerin trägt
(`data_access/arango/attachment_repository.py:404–430`); v0109 hat das für bereits anonymisierte Zeilen nachgeholt.
Die Regel begründet das Behalten mit NFR-011 R-16/R-17/R-18 (CanG/PflSchG) — nach Einschätzung des Betreibers trifft das
für Gartenfotos nicht zu; welche Grundlage trägt, ist Frage 1 unten. Der Umfang `user_personal` (Löschen) ist heute leer.
Der Art.-15/20-Export ist reines JSON (`api/v1/privacy/router.py:145–181`) und enthält Metadaten: im eigenen
persönlichen Mandanten mit `_key` und `created_at` (`domain/engines/data_export_engine.py:802–818`), für Fotos aus einem
gemeinsamen Mandanten über die `created_by`-Quelle (`data_export_engine.py:501–506`). Die Bilddateien sind „in der App
verfügbar“, nur über mandantengebundene Routen mit Mitgliedschaft (`api/v1/attachments/tenant_router.py:235–318`).
Das Foto eines anderen oder gelöschten Mitglieds entfernen kann nur die Leitung
(`domain/services/location_photo_service.py:128–135`, `:237–266`); eine abgebildete Person ohne Konto hat keinen
eigenen Weg. `GET /privacy/policy` kennt keine Kategorie für Fotos oder Anhänge (`privacy_service.py:1981–2196`).

**Ergänzung Audit 2026-11-22.** (a) Die Bildunterschrift `caption` (bis 500 Zeichen, `domain/models/attachment.py:84`)
bleibt bei der Anonymisierung stehen (`attachment_repository.py:404–430`). (b) Der EXIF-Nachstrip bei Kontolöschung
läuft nur in aktuellen Mitgliedsmandanten (`privacy_service.py:3302–3368`, `:3532–3551`); die kollektionsweite Regel
erreicht verlassene Mandanten ohne Nachstrip (`erasure_engine.py:358–378`, `data_access/arango/erasure_executor.py:387–421`)
— LEG-55. Der Regeltext verweist auf `STORAGE_KEEP_EXIF_<category>`, das es nicht gibt (nur `storage_strip_exif`,
`config/settings.py:1340`). (c) In der Kontoquelle eines gemeinsamen Mandanten fehlen `_key`, `created_at` und das
Bezugsobjekt (`data_export_engine.py:501–506`): die Person erkennt nicht, **welches** Foto gemeint ist; für verlassene
Mandanten gibt es Metadaten ohne Abrufmöglichkeit. *Rechtspflicht:* Ein Foto, das eine Person zeigt, ist ein Datum
dieser Person; für sie gelten Art. 13/14 und Art. 15/17 wie für Kontoinhaber; abgebildete Dritte sind eine eigene
Betroffenenkategorie im Verzeichnis (Art. 30 Abs. 1 lit. c); Zwecke, Grundlage und Speicherdauer gehören in den
Hinweis (Art. 13 Abs. 1 lit. c, Abs. 2 lit. a). *Auslegung:* Die zitierte Ausnahme R-16…R-18 trägt für Beetfotos und
Unterlagen nicht (deckungsgleich mit der Betreibereinschätzung); die „Anonymisierung“ eines Fotos, das Person oder Haus
zeigt, ist i. d. R. keine Anonymisierung i. S. d. ErwG 26. Der Verweis „in der App“ kann Art. 15 Abs. 3 genügen, solange
Zugang besteht — nicht für verlassene Mandanten; eigene Uploads sind typischerweise „bereitgestellt“ (Art. 20);
Art. 15 Abs. 4 begrenzt die Herausgabe fremder Fotos, nicht eigener Uploads.

**Ausgelieferter Default.** Anonymisieren (Datei bleibt, `caption` bleibt); Export ohne Bilddateien; kein Weg für
Dritte; keine Fotozeile im Hinweis.

**Fragen.**
1. **Q-DSB-09 (LEG-20, Art. 17)** — Genügt Art. 6 Abs. 1 lit. f, um die Beetfotos einer gelöschten Person im gemeinsamen
   Garten zu behalten (das Foto kann die Person oder ihr Zuhause zeigen), oder müssen die eigenen Beetfotos gelöscht
   werden (Umfang `user_personal`)? Ausgeliefert: anonymisieren. *Ergänzung Audit:* Varianten B (löschen) und C
   (Wahlrecht der Person im Löschdialog); `caption` wird bis zur Antwort mitgeleert, die Regelbegründung korrigiert
   (PRA-2.12, ohne Freigabe).
2. **Q-DSB-10 (LEG-21, Art. 15 Abs. 3, Art. 20)** — Erfüllt ein Export mit Metadaten und Verweisen das Recht auf Kopie
   und Datenübertragbarkeit, oder müssen die Bilddateien in den Export? Wie übt eine abgebildete Person ohne Konto
   Art. 15/17 aus (heute nur über die Leitung)?
3. **Q-DSB-11 (LEG-22, Art. 30, Art. 13)** — Sollen Beetfotos eine eigene Kategorie im Verzeichnis und im
   Datenschutzhinweis sein?
4. **Q-LAW-12, neu (Teilaspekt von Frage 1)** — Ist ein Marker statt Löschung bei einem Foto, das die Person oder ihr
   Haus zeigt und nach ErwG 26 i. d. R. personenbezogen bleibt, überhaupt eine Erfüllung von Art. 17? Hängt ab: ob
   Variante B Pflicht oder Option wird (PRA-2.12).
5. **Q-DSB-10 (Ergänzung)** — Sind eigene Uploads „bereitgestellt“ i. S. d. Art. 20, und muss der Export sie auch aus
   verlassenen Mandanten liefern? Hängt ab: Kontoquelle mit `_key`/`created_at` (sofort, ohne Freigabe) und Option
   „mit Dateien“ als ZIP (PRA-2.04; Umfang und Größengrenzen Q-PO-05 in `12`); Prozess für Dritte (PRA-2.04).
6. **Q-DSB-11 (Ergänzung)** — Gilt Art. 14 für abgebildete Dritte, und greift eine Ausnahme nach Art. 14 Abs. 5? Hängt
   ab: Gliederung der Zeile `photos_and_attachments` im Policy-Endpunkt (PRA-2.18).

## 7. Einschränkung, Widerspruch und Legal Hold (LEG-23, LEG-35)

**Ist-Stand** (`VERIFIED_CODE`). `POST /privacy/restrict` und `POST /privacy/object` legen
`processing_restrictions`-Dokumente an und antworten 201 (`api/v1/privacy/router.py:336–381`). Kein
Verarbeitungspfad liest sie: die in REQ-025 §3.7 spezifizierte Dependency `check_processing_restriction` (423)
existiert nicht, `ProcessingRestrictionRepository.list_active_by_user`
(`domain/interfaces/processing_restriction_repository.py:38`) hat keinen Aufrufer; einziger Nutzer des Repositorys ist
`domain/services/privacy_service.py:1810–1888`. `scope` ist Freitext ohne Zuordnung zu einem Zweck
(`api/v1/privacy/schemas.py:265–290`). Der Betreiber erfährt von einem Antrag nichts; es gibt keine Admin-Liste und
keine `GET`-Route für die Person (die UI zeigt nur in derselben Sitzung angelegte Einträge,
`pages/auth/PrivacySettingsPage.tsx:117`, `:232–252`). Lösch-, Anonymisierungs- und Purge-Jobs laufen ohne Prüfung
(R-25, R-26, R-16…R-18, R-06/R-38; `tasks/retention_tasks.py:298–348`). Einen Legal Hold gibt es nicht
(`grep -i "legal.hold\|legal_hold"` in `src/backend/app` und `spec/privacy` → 0). Die Nutzerdoku sagt: „Während einer
Einschränkung werden die betroffenen Daten nicht mehr aktiv verarbeitet“ (`docs/de/user-guide/privacy.md:153`).

**Ausgelieferter Default.** Antrag gespeichert, ohne Wirkung und ohne Empfänger; Löschjobs löschen auch Daten unter
Einschränkung; kein Hold.

**Rechtspflicht.** Eingeschränkte Daten dürfen nur noch gespeichert werden, im Übrigen nur mit Einwilligung oder aus
den Gründen des Art. 18 Abs. 2. Nach Widerspruch keine Verarbeitung mehr, außer bei zwingenden schutzwürdigen Gründen
(Art. 21 Abs. 1 S. 2). Verlangt die Person Einschränkung statt Löschung, weil sie die Daten zur Rechtsverfolgung
braucht (Art. 18 Abs. 1 lit. c), dürfen automatische Löschjobs sie nicht vernichten. Unterrichtung binnen eines Monats
(Art. 12 Abs. 3; L-19); Mitteilung an Empfänger (Art. 19). Eine Zusicherung ohne Wirkung widerspricht Art. 5 Abs. 1
lit. a und Art. 12 Abs. 1. Art. 17 Abs. 3 lit. e erlaubt, Daten wegen Rechtsansprüchen zurückzuhalten.

**Auslegung.** Ein manueller Ablauf „Antrag → Betreiber prüft → Maßnahme“ wäre zulässig — es fehlt der Kanal. Ohne
Hold-Mechanik vernichten automatische Löschjobs auch Beweismittel (PflSchG-/KCanG-Prüfungen, Arbeitsrechtsstreit;
Bedarf gewerblicher Kunden: Q-CUS-01 in `12`).

**Fragen.**
1. **Q-DSB-14 (a)** — Welche realen Verarbeitungen sind durch welche Einschränkungs-/Widerspruchs-Scopes erfasst?
   Vorschlag einer Zweckliste: `attribution_display`, `sensor_analytics`, `ai_processing`, `notifications`,
   `retention`, `all` (`all` → Konto im Lesemodus, 423 auf verarbeitende Routen außer Privacy). Produktseite: Q-PO-07
   in `12`.
2. **Q-DSB-14 (b)** — Wer darf einen Legal Hold setzen (Vorschlag: nur Plattform-Admin auf dokumentierten Antrag),
   mit welchen Scopes (`user | tenant | record`) und wie lange?
3. **Q-DSB-14 (c)** — Darf eine aktive Einschränkung mit `scope ∈ {all, retention}` als Hold wirken, d. h.
   Retention-, Purge- und Anonymisierungsjobs sowie der Erasure-Executor lassen die Daten der Person unverändert und
   eine Kontolöschung bleibt `scheduled` mit `held_reason`?

**Hängt ab.** PRA-0.05 (Doku-Satz auf Ist-Stand) und PRA-0.06 (Betreiberbenachrichtigung, Admin-Liste,
`GET /privacy/restrict`) sind ohne Freigabe auslieferbar; PRA-1.06 (Processing-Hold-Guard, `legal_holds`) wartet für
Zweckliste und Hold-Berechtigung auf die Antwort. Fristüberwachung Art. 12 Abs. 3 und Empfängermitteilung Art. 19:
PRA-2.20 (Umsetzung einer ausdrücklichen Pflicht, ohne Freigabe).

## 8. Backups, Restore und Widerrufe (LEG-11, LEG-24, LEG-25, LEG-26; Nachtrag 2026-11-23: LEG-62…LEG-70)

**Ist-Stand** (`VERIFIED_CODE`; Nachtrag 2026-11-23 nachgeprüft an develop `ce7e858d0`, für Backup relevante Dateien
gegenüber `007a4ea90` unverändert). Der Backup-CronJob existiert und ist aus (`helm/kamerplanter/values.yaml:567–612`,
`backup.enabled: false`, `retentionDays: 30`, SSE `AES256`/`aws:kms` in `:607–608`; Controller `arangodb-backup`
`:1324–1460`, arangodump inkl. Systemcollections). Es gibt keinen Lösch-Spiegel, kein Journal und kein Replay
(`grep erasure_mirror\|privacy.mirror\|mirror.enabled` in `src`, `helm`, `docs` → 0). Der einzige Backup-Precheck prüft
den Bucket (`values.yaml:382–387`); `retentionDays` ist unvalidiert, `0` und jeder negative oder nicht-numerische Wert
bedeuten unbegrenzt (`:1418`); `backup.enabled: false` beendet auch die Löschung vorhandener Dumps (`:1325`, LEG-68). Die
Betriebsdoku leitet zur Aktivierung an (`docs/de/deployment/backup-restore.md:21`, `:25–80`) und endet nach dem Restore
mit „Anwendung starten“ (`:101–160`); bei `celeryWorkers.dedicatedQueues: true` laufen dabei zwei Worker weiter
(`:116–117, 156–157`; LEG-62), Worker und Beat warten nicht auf den Migrationsstand (LEG-70), Valkey behält bei einem
Restore im bestehenden Namespace den Stand nach dem Backup (LEG-69). Zufällige Teilwirkung: `execute_scheduled_erasures`
(`privacy_service.py:2568–2602`) führt nach einem Restore Anträge im Status `scheduled`/`partially_completed` erneut
aus, `resume_tenant_erasures` (`tasks/tenant_tasks.py:31–40`) fällige Mandantenlöschungen; Anträge nach dem Dump und
sofortige Admin-Löschungen gehen verloren. Ein `arangorestore --overwrite true` setzt zudem **Widerrufe** zurück:
API-Keys (nur `revoked: True`, `data_access/arango/api_key_repository.py:70–77`; der Widerruf ist außerdem fail-open,
LEG-66), Refresh-Token-Familien und „alle Sitzungen beenden“ (Schreibpfad
`data_access/arango/refresh_token_repository.py:175–216`, Prüfung `domain/services/auth_service.py:888–893`),
Passwortwechsel (`auth_service.py:1273, 1453ff., 1534`), Einwilligungswiderrufe (`domain/services/privacy_service.py:1955–1977`),
Art.-18/21-Einträge, Mitgliedschaftsentzüge, Mandantensperren; `security_audit_log` liegt in derselben Datenbank
(LEG-24). Das Startgate prüft nur die Länge, nicht die Identität des Tombstone-Salts (`main.py:96–98`; LEG-67). Der
Mandanten-Import (einziger Teil-Restore) prüft nicht gegen abgeschlossene Löschungen
(`domain/engines/tenant_import_engine.py:34–36`; LEG-65, Bezug zu Q-DSB-03). Light/Docker:
`docs/de/deployment/docker-dauerbetrieb.md:205–233` ohne Frist, Verschlüsselung und Replay (LEG-43); der Restore läuft
gegen die laufende Anwendung (`:218–230`; LEG-63); `backend` und `celery-worker` haben kein Anhänge-Volume
(`docker-compose.release.yml:145–146, 194–195, 252–257`; LEG-64). Die empfohlene Bucket-Versionierung ohne
Lifecycle-Regel (`backup-restore.md:14`, `:29`; `values.yaml:587–591`) hält gelöschte Fotos und Exportarchive
unbefristet beim S3-Anbieter (LEG-26). Der Spec-Widerspruch PRIV-709 ↔ PRIV-710/PRIV-E14 (Beat-Sync vor dem Dump,
LEG-25) ist in [`17-privacy-recovery.md`](17-privacy-recovery.md) aufgelöst: Outbox im selben Commit, Relay als
Einzelschreiber (PRIV-802, PRIV-805). Ob Backups in Produktion aktiv sind, ist im Repo nicht prüfbar (PRA-0.03, Q-OP-02
in `12`).

**Ausgelieferter Default.** Backup aus; nach Aktivierung ohne Journal, Replay und Fristobergrenze.

**Vorgeschlagene Mechanik (`17`, Status `spezifiziert`).** Transactional Outbox in derselben Stream-Transaktion, Relay
in einen Journal-Store außerhalb der DB (Object Lock bzw. append-only Volume), domänengetrennte Pseudonyme
`jsub_`/`jten_`/`jrec_`, Journal-Frist R-63; Restore-Lebenszyklus mit fail-closed Gate für Backend, Worker und Beat,
Isolation, Migration vor Replay, Reconciliation je Datenbereich, globale Token-Entwertung nach jedem Restore,
Rückfall nur über `FALLBACK_REVIEW`, Evidence-Report (R-64). Architekturvorschläge DEC-35…DEC-40 (`decision-log.md` §A,
`proposed`).

**Rechtspflicht.** Löschung nach Art. 17 Abs. 1; Speicherbegrenzung (Art. 5 Abs. 1 lit. e); Wiederherstellbarkeit
(Art. 32 Abs. 1 lit. c). Widerruf, Einschränkung und Widerspruch wirken für die Zukunft (Art. 7 Abs. 3, Art. 18 Abs. 2,
Art. 21 Abs. 3) — ein Restore, der sie still zurücksetzt, führt zu Verarbeitung ohne Grundlage; reaktivierte
kompromittierte Zugänge berühren Art. 32 Abs. 1 lit. b.

**Auslegung.** Art. 17, Art. 5 Abs. 1 lit. e und Art. 32 Abs. 1 lit. c stehen in Spannung, nicht im Widerspruch. Der
EDSA akzeptiert, dass eine Löschung im Backup erst mit dem nächsten Zyklus nachvollzogen wird (L-19 Rn. 110); das Paket
leitet daraus kurze Zyklen (≤ 35 Tage) und die erneute Anwendung nach einem Restore ab (DEC-13/DEC-26). Ein deutscher
Primärbeleg fehlt (L-21). Ein Journal, das per Beat-Sync geschrieben wird, wäre zwischen Löschung und Sync wirkungslos
(Art. 25 Abs. 1); das Audit empfiehlt write-through mit Outbox, ausgedehnt auf Widerrufe und Sicherheitsereignisse.
Rechtliche Einordnung je Norm, getrennt nach gesicherter Anforderung, Empfehlung, risikobasierter Auslegung und offener
Frage: `17` §10.

**Fragen.**
1. **Q-LAW-14** — Ist „Dumps ≤ 35 Tage mit Replay nach Restore“ ohne deutschen Primärbeleg vertretbar (LEG-11)? Hängt
   ab: Freigabe der Backup-Aktivierung (`deployment_allowed`, PRA-1.05). Kundenseitige Erwartung längerer
   Backup-Fristen (Q-CUS-06 in `12`): Pflichtdaten liegen in der Primär-DB, nicht im Backup.
2. **Q-DSB-15** — Ist ein pseudonymes Journal außerhalb der Datenbank zulässig, obwohl Tombstones personenbezogen
   bleiben (L-15), und ist die Aufbewahrung angemessen (LEG-11, LEG-25)? *Präzisiert (Nachtrag 2026-11-23):* Gefragt
   ist die Frist **R-63** (wirksame Backup-Lebensdauer + 14 d, höchstens 90 d) statt R-45 (3 Jahre); die Frist selbst
   ist Q-DSB-22. Hängt ab: Bau des Journals (PRA-1.04).
3. **Q-DSB-16** — Zwischen Restore und Replay sind Löschungen und Widerrufe zurückgesetzt. Genügt als Maßnahme ein
   Wartungsmodus mit Startsperre (503 außer Health und Admin-Replay) bis zum abgeschlossenen Replay, ergänzt um eine
   Post-Restore-Basis (`JWT_SECRET_KEY` rotieren, alle Refresh-Tokens widerrufen) (LEG-24, LEG-11)? *Präzisiert
   (Nachtrag 2026-11-23):* gemeint ist das Restore-Gate nach `17` §5.3 (schließt Backend, **Worker und Beat**, auch bei
   `DEBUG`; Gründe u. a. Journal nicht erreichbar, Secret-Fingerabdruck abweichend, Migrationskopf veraltet) mit
   globaler Token-Entwertung nach **jedem** Restore (PRIV-829); `JWT_SECRET_KEY` wird nur im Rückfall rotiert. Hängt
   ab: PRA-1.05.

**Neue Fragen (Nachtrag 2026-11-23, aus `17` §10.3).**

4. **Q-DSB-22 — Journal-Frist.** Genügt für das Journal eine Aufbewahrung „wirksame Backup-Lebensdauer + 14 d,
   höchstens 90 d“ (R-63), wenn der Löschnachweis über 3 Jahre in `erasure_requests` (R-06) liegt, statt 3 Jahre im
   Journal (R-45)?
   *Ist-Stand:* kein Journal (Grep → 0); der Nachweis ist der Tombstone in `erasure_requests`
   (`domain/engines/erasure_engine.py:860–871`, Frist `config/settings.py:108`) bzw. `tenant_erasure_records`; beide
   rollen bei einem Restore zurück und würden durch das Replay neu erzeugt (`17` §3.8).
   *Default:* R-63 mit Default 53 d (30 + 7 + 2 + 14), Segmentablauf statt Umschreiben; Vorschlag DEC-36.
   *Norm:* Art. 5 Abs. 1 lit. c, e und Abs. 2; Art. 17 Abs. 1 (Bezug, L-12); Pseudonyme bleiben personenbezogen (L-15).
   *Abhängige PRA:* PRA-1.04 (Journal), PRA-0.10 (Frist-Check im Chart-Vertrag).
5. **Q-DSB-23 — gewöhnliche Löschungen.** Dürfen gewöhnliche Löschungen von Fachdatensätzen durch Nutzer (Tagebucheintrag,
   Notiz, Aufgabe; außerhalb der Privacy-Routen) nach einem Restore für höchstens die wirksame Backup-Lebensdauer
   zurückkehren, oder müssen sie wie Anhänge journalisiert werden?
   *Ist-Stand:* keine Löschung wird journalisiert; nach einem Restore kehren alle nach dem Backup gelöschten Zeilen
   zurück, Selbstheilung nur für fristbasierte Zeilen (`tasks/retention_tasks.py:134–388`).
   *Default:* nicht journalisiert, außer Anhänge (`ATTACHMENT_DELETED`) und Schwärzungen (`REDACTION_APPLIED`);
   Vorschlag DEC-38; die Alternative `RECORD_DELETED` je Löschung ist ohne Schemaänderung ergänzbar (`17` §3.2).
   *Norm:* Art. 17 Abs. 1; Art. 5 Abs. 1 lit. e; L-19 Rn. 110 (Auslegung „nächster Zyklus“).
   *Abhängige PRA:* PRA-1.04.
6. **Q-DSB-24 — Freigabe mit Journal-Lücke.** Ist eine Freigabe nach Restore **mit** Journal-Lücke (Rückfallbasis) vertretbar,
   und welche Information der Betroffenen bzw. Mandanten ist dann nötig?
   *Ist-Stand:* es gibt kein Gate; das System öffnet nach dem Restore ohne Prüfung (`backup-restore.md:155–160`).
   *Default:* Gate bleibt zu; Freigabe nur über `FALLBACK_REVIEW` mit Pflichtmaßnahmen (globale Token-Entwertung,
   `JWT_SECRET_KEY` rotieren, API-Keys auf Bestätigung, optionale Einwilligungen erneut bestätigen, offene Löschungen
   ausführen, Retention-Nachlauf), Freigabe inkl. DSB, bei BM-001 Information der Mandanten; Report „mit Lücke“, nie
   „vollständig“ (`17` §5.5, PRIV-832).
   *Norm:* Art. 5 Abs. 2; Art. 32 Abs. 1 lit. b, c; Art. 34 (Bezug, L-12).
   *Abhängige PRA:* PRA-1.05.
7. **Q-DSB-25 — Einwilligungen nach dem Backup.** Darf eine nach dem Backup erteilte Einwilligung, deren Nachweis der Restore
   verloren hat, aus dem Journal wiederhergestellt werden, oder ist sie erneut einzuholen?
   *Ist-Stand:* der Nachweis (`granted_at`, `consent_version`, `ip_address`, `user_agent`) liegt nur in
   `consent_records` (`domain/models/privacy.py:116–132`) und rollt mit zurück; das Journal soll nur `purpose` und
   `consent_version` tragen.
   *Default:* erneut einholen (`CONSENT_GRANTED` dient nur der Reihenfolge, `17` §3.6); Vorschlag DEC-39.
   *Norm:* Art. 7 Abs. 1 (Nachweis), Art. 6 Abs. 1 lit. a (Bezug, L-12).
   *Abhängige PRA:* PRA-1.05 (PROCESSING_HOLD_RECONCILIATION), PRA-1.04.
8. **Q-DSB-26 — Art. 19 nach Restore.** Müssen Empfänger (Art. 19) nach einem Restore erneut unterrichtet werden, wenn zwischen
   Restore und Freigabe keine Sendung stattfand, und bei Freigabe mit Lücke?
   *Ist-Stand:* kein Art.-19-Mechanismus und keine Empfängerliste (LEG-33, `06` §11 Nr. 22); nach einem Restore starten
   Beat und Digests (06:05–07:00) sofort und erreichen wiederhergestellte Konten (`tasks/__init__.py:395–615`).
   *Default:* während der Isolation alle externen Abflüsse aus (Benachrichtigungen, KI, Erkennung, Wetter, Aktorik,
   Kalender-Feeds), nach Freigabe keine Sendungen an gelöschte Subjekte; keine erneute Unterrichtung, solange nichts
   gesendet wurde (`17` §5.3, §7.1).
   *Norm:* Art. 19; Art. 17 Abs. 2 (Bezug, L-12).
   *Abhängige PRA:* PRA-1.05, PRA-2.20, PRA-1.03.
9. **Q-LAW-18 — Restore als Verletzung.** Ist ein Restore, der gelöschte Daten wieder verfügbar macht oder widerrufene Zugänge
   reaktiviert (heutiger Zustand ohne Reconciliation), eine Verletzung des Schutzes personenbezogener Daten nach
   Art. 4 Nr. 12 mit Prüfpflicht nach Art. 33/34?
   *Ist-Stand:* genau das tritt heute bei jedem Restore ein (Szenarien S3–S7, `09` §6.5); ein Verfahren für
   Datenschutzverletzungen fehlt (LEG-32, §12). Ob in der Vergangenheit Restores stattfanden, ist nicht prüfbar (PRA-0.03).
   *Default:* ein nicht reconcilierter Restore wird als möglicher Vorfall geprüft (Alarm `PrivacyRecoveryBlocked`,
   Metriken `17` §11.4); Fallakte im Incident-Register.
   *Norm:* Art. 4 Nr. 12, Art. 33, Art. 34 (Bezug, L-12); EDSA-Leitlinien 9/2022 (L-24, `UNVERIFIED_AT_SOURCE`, V-13).
   *Abhängige PRA:* PRA-3.02, PRA-0.03.
10. **Q-LAW-19 — WORM-Journal und Löschantrag.** Kann einem Löschantrag hinsichtlich der Pseudonyme im WORM-Journal (Object Lock
    bis R-63) Art. 17 Abs. 3 lit. b/e oder Art. 11 entgegengehalten werden, und ist Compliance-Mode (nicht
    übersteuerbar) für BM-001 zulässig?
    *Ist-Stand:* kein Journal; geplant ist Object Lock **Governance** (Compliance nur BM-001 nach Antwort), Inhalt nur
    Pseudonyme, Enums und Zeitpunkte (`17` §3.7, §7.2, §7.3).
    *Default:* Governance-Mode, Frist R-63, kein Nutzdateninhalt; das Journal wird nie an Mandanten exportiert.
    *Norm:* Art. 17 Abs. 3 lit. b, e; Art. 11; Art. 5 Abs. 1 lit. e (Bezug, L-12); L-15 (Pseudonyme bleiben
    personenbezogen).
    *Abhängige PRA:* PRA-1.04.

**Hängt ab, ohne Freigabe.** PRA-0.10 (Render-Fehler bei `backup.enabled` ohne Journal, `1 ≤ retentionDays ≤ 35`,
Bucket-Expiration unabhängig vom CronJob, Warnblock und manuelles Runbook, Bucket-Lifecycle-Doku); PRA-0.12
(Runbook-Sofortkorrektur: alle Worker anhalten, Docker-Restore nur gestoppt, Valkey leeren); PRA-2.21 (fail-closed
Widerruf); PRA-2.22 (Salt-Identität, Backup-Manifest); PRA-1.08 (versionsvollständige Objektlöschung); PRA-3.07
(Docker-Backup mit Frist und Verschlüsselung). Diese Maßnahmen schränken ein und brauchen keine Antwort.

## 9. Beschäftigtendaten: Leistungsdaten, Aktorik-Protokoll, Mandantenklassifizierung (LEG-05, LEG-28, LEG-29, LEG-30)

**Ist-Stand** (`VERIFIED_CODE`). (a) **Aufgaben** speichern je Person `started_at`, `completed_at`,
`actual_duration_minutes`, `quality_rating`, `difficulty_rating` und `assigned_to_user_key`
(`domain/models/task.py:181–205`; `domain/services/task_service.py:1469–1475` `start_task`, `:1720–1745`); die
Antwort `TaskResponse` liefert sie (`api/v1/tasks/schemas.py:304–357`) jedem Mitglied ohne Rollenprüfung
(`api/v1/tasks/tenant_router.py:380–426`, `:529–613`, `:739–788`) — entgegen PRIV-407 (`06` §5). (b) **Aktorik:**
`control_events.triggered_by_user` hält den rohen Kontoschlüssel (`domain/models/actuator.py:227`;
`domain/services/actuator_service.py:158–170`, `:718–741`), lesbar für alle Mitglieder
(`api/v1/actuators/tenant_router.py:344–375`); weder Kontolöschung noch Art.-15-Export erfassen ihn (`grep
control_events\|triggered_by_user` in `erasure_engine.py`, `data_export_engine.py` → 0), nur die Mandantenlöschung
(`tenant_erasure_engine.py:143`); der Inventar-Guard sieht das Muster `_by_user` nicht
(`scripts/check_privacy_inventory.py:214–215`, repo-relativ). (c) **Klassifizierung:** `record_keeping` und `organization_kind` sind
gespeichert (v0110), aber „in no request or response schema yet“ (`domain/models/tenant.py:31–38`) und außerhalb von
Modell, Enum und Migration nirgends gelesen; der Import setzt `undeclared` (`domain/services/tenant_export_service.py:145`).
Gewerbliche Mandanten sind technisch nicht erkennbar; das Gate DEC-32 („kommerzieller SaaS-Betrieb nicht
freigegeben“) erfasst den Fall „selbst gehostet, gewerblich“ nicht (LEG-48). Ob gewerbliche Mandanten mit
Beschäftigten produktiv sind, klärt PRA-0.04 (Q-OP-12 in `12`).

**Ausgelieferter Default.** Leistungsfelder und `control_events` für alle Mitglieder lesbar, ohne Frist; keine
Klassen-Defaults, weil keine Klasse gesetzt werden kann.

**Rechtspflicht.** Ein Arbeitgeber-Mandant braucht für Beschäftigtendaten eine Grundlage (Art. 6 Abs. 1, Art. 88).
§ 87 Abs. 1 Nr. 6 BetrVG gibt dem Betriebsrat ein Mitbestimmungsrecht bei technischen Einrichtungen, „die dazu bestimmt
sind, das Verhalten oder die Leistung der Arbeitnehmer zu überwachen“ (L-10); die Pflicht trifft den **Arbeitgeber**,
nicht den Softwareanbieter. Ehrenamtliche und Vereinsmitglieder sind keine Beschäftigten i. S. d. § 26 Abs. 8 BDSG
(L-09). Für `control_events.triggered_by_user` gelten Art. 15 und Art. 17 wie für jedes Personenfeld; heute ohne
Auskunft, Löschung und Frist (Art. 5 Abs. 1 lit. e).

**Auslegung.** Die fortgesetzte Berufung auf § 26 Abs. 1 BDSG als spezifischere Vorschrift i. S. d. Art. 88 ist nach
C-34/21 rechtlich unsicher (`INFERRED`, L-13 nicht verifiziert); in der Praxis wird auf Art. 6 Abs. 1 lit. b/c/f
ausgewichen. Nach der (nicht verifizierten, V-05) BAG-Linie genügt objektive Eignung zur Überwachung; ein Aufgabensystem
mit Zuständigen, Start, Ende, Ist-Dauer und Bewertung je Person, angezeigt für alle, ist danach objektiv geeignet,
ebenso das Schaltprotokoll (Anwesenheit und Arbeitszeit ableitbar). Ein Koordinationsprotokoll („wer hat wann gegossen“)
ist nicht per se unzulässig; unverhältnismäßig machen es Zeit-/Dauer-/Qualitätsdaten je Person, unbeschränkte
Sichtbarkeit unter Kollegen, Exporte ohne Audit und 5 Jahre namentliche Historie. Einwilligung ist im
Beschäftigungskontext kein tragfähiger Ausweg (DA-02 Option C verworfen). Weil die Klassifizierung inert ist, kann der
Betreiber seine Unterstützungspflicht nach Art. 28 Abs. 3 lit. f nicht klassenabhängig erfüllen.

**Fragen.**
1. **Q-LAW-01 (präzisiert §1 Frage 2)** — Ist § 26 Abs. 1 BDSG nach EuGH C-34/21 als spezifischere Vorschrift
   i. S. d. Art. 88 weiter anwendbar, und welche Ersatzgrundlage tragen Arbeitgeber-Mandanten (V-08)? Hängt ab: Text der
   Mandantenvorlage und Grundlage im Verzeichnis (PRA-2.05, PRA-3.01).
2. **Q-LAW-02, neu** — Gilt die BAG-Rechtsprechung zur „Eignung“ (§ 87 Abs. 1 Nr. 6 BetrVG, V-05) auch für Aufgaben-
   und Protokollsysteme **ohne** Auswertungsfunktion, deren Daten aber je Person angezeigt werden (LEG-05, LEG-28)?
   Hängt ab: Mustertext Betriebsrat (PRIV-406) und Hinweis bei `commercial` (PRA-2.06, PRA-3.04).
3. **Q-LAW-03 (präzisiert §1 Frage 2)** — Muss der Anbieter die Sichtbarkeit `leads_and_self` für gewerbliche Mandanten
   **erzwingen**, oder genügt ein Default mit Warnhinweis? Welche Pflichten hat die Plattform gegenüber dem
   Arbeitgeber-Mandanten? Hängt ab: „erzwungen vs. Default“ in PRA-2.05; bis zur Antwort erzwungen (Audit-Empfehlung,
   einschränkend).
4. **Q-DSB-21, neu** — PRA-2.06 und PRA-2.07 liefern einschränkend aus: Leistungsfelder nur für die Person selbst und
   Leads, in `commercial` aus; `control_events` mit Marker bei Löschung, als Art.-15-Quelle und mit Frist; Vorschlag
   für beide **90 Tage**. Bestätigt der DSB diesen Wert (neue R-nn in NFR-011 und `06`)? Fachlicher Zweck der Felder
   und Bedarf eines Personenbezugs in `control_events`: Q-PO-13 und Q-PO-15 in `12`.

**Hängt ab, ohne Freigabe.** PRA-1.02 (Klassifizierung bei Anlage verpflichtend, `POST /tenants` ohne Klasse → 422,
einziger Leser `resolve_tenant_privacy_profile`); PRA-2.06, PRA-2.07 (einschränkend). Betriebsrat, Saisonkräfte und
Personalnutzung der Exporte fragen Q-CUS-08…10 (`12`).

## 10. KI-Cloud-Verarbeitung und MCP (LEG-31, LEG-51, LEG-52)

**Ist-Stand** (`VERIFIED_CODE`). (a) **KI-Cloud-Gate:** Das Gate prüft die Einwilligung `ai_cloud_processing` am
Provider-Datensatz des **Mandanten** (`domain/services/ai_assistant_service.py:125–165`; `:148`
`get_default(ctx.tenant_key, …)`; ohne Datensatz `("", "ollama", False)` → keine Prüfung, `:150–151`; Einwilligung nur
bei `uses_cloud`, `:162–163`). Tipps, Tagestipp, „Warum?“, Chat-Stream und Diagnose
(`ai_assistant_service.py:245–250`, `:350–354`, `:463–467`, `:768–778`, `:798–803`, `:892–906`;
`domain/services/diagnose_service.py:295–313`) rufen aber den Knowledge-Service, der sein **eigenes** `LLM_PROVIDER`
nutzt (`src/knowledge-service/app/config.py:61–64`, Default `ollama`; `app/llm/__init__.py:10–17`); die Anfrage trägt
keinen Provider (`data_access/external/knowledge_service_adapter.py:188–213`). `/ask` ist korrekt. Der Indikator
„Cloud-Verarbeitung“ leitet sich aus dem Mandanten-Datensatz ab, nicht aus dem tatsächlichen Provider. Ob eine
Produktionsinstanz mit `LLM_PROVIDER ≠ ollama` läuft, ist nicht prüfbar (PRA-0.01, Q-OP-01 in `12`); dann eskaliert
LEG-31 auf P0. Belegt ist: Consent-Guard `ai_tenant_data_access` auf allen mandantenbezogenen KI-Routen, der
Knowledge-Service protokolliert keine Fragen. (b) **MCP:** `get_diary_entry` und `get_diary_entry_photos` liefern jeden
Eintrag des Mandanten, auch unmarkierte anderer Mitglieder (`mcp_server/tools/diary.py:451–525`, `:530–600`;
`domain/services/plant_diary_service.py:738–746` nur Mandantenbindung; Einwilligung des Markierenden `:765`); der
Einwilligungstext sagt „nur markierte Einträge“ (`spec/req/REQ-050_KI-Analyse-Tagebucheintraege.md:1043–1048`).
(c) Schreibende MCP-Werkzeuge (18 WRITE, 3 SETUP) laufen mit `dry_run = False` als Default (`mcp_server/base.py:265–279`);
Mandanteninhalte erreichen den Agenten ohne Kennzeichnung als nicht vertrauenswürdig (LEG-52, Art.-32-Thema; keine
Rechtsfrage).

**Ausgelieferter Default.** Knowledge-Service lokal (`ollama`); Gate am Mandanten-Datensatz; MCP liefert alle
Freitexte des Mandanten.

**Rechtspflicht.** Eine als Grundlage erklärte Einwilligung muss vor der Verarbeitung eingeholt sein (Art. 6 Abs. 1
lit. a, Art. 7). Eine Übermittlung in ein Drittland (Anthropic/OpenAI-kompatibel, USA) braucht eine Grundlage nach
Kapitel V (Art. 44 ff.). Der Cloud-Indikator muss zutreffen (Art. 5 Abs. 1 lit. a, Art. 13 Abs. 1 lit. f).

**Auslegung.** Mit Cloud-LLM gehen Prompts (Stammwerte, `cultivar_hint`, Freitext im Chat) ohne die erklärte
Einwilligung an einen US-Anbieter. Die Offenlegung an ein Mitglied, das die Daten ohnehin sieht, ist zulässig (lit. b
bzw. f); die Weitergabe an ein LLM verantwortet das Mitglied, eine Drittlandübermittlung ist möglich. Dass die
MCP-Werkzeuge standardmäßig alle Freitexte maschinell bereitstellen, widerspricht Art. 25 Abs. 2; der Text „nur
markierte Einträge“ erzeugt eine falsche Erwartung.

**Fragen.**
1. **Q-DSB-19** — Reicht die Einwilligung `ai_cloud_processing` als Grundlage der Übermittlung nach Art. 49 Abs. 1
   lit. a, oder sind Standardvertragsklauseln bzw. das Data Privacy Framework nötig (LEG-31)? Hängt ab: Registereintrag
   des LLM-Anbieters (PRA-1.03) und Einwilligungstext; das Gate am tatsächlichen Provider (PRA-0.09, fail-closed) ist
   ohne Freigabe auslieferbar.
2. **Q-LAW-10** — Wie verteilt sich die Verantwortung zwischen Mandant, Mitglied und Betreiber, wenn ein Mitglied über
   MCP Mandantendaten — auch fremde Tagebucheinträge und Fotos — an sein eigenes LLM weiterleitet (LEG-51)? Hängt ab:
   PRA-2.10 — Option A (nur eigene, markierte oder Leitung; ohne Freigabe) oder Option B (Text an Verhalten anpassen;
   braucht Freigabe); Produktentscheidung Q-PO-17, Bedarf gewerblicher Kunden Q-CUS-12 (`12`).

DSFA für KI und MCP in Gemeinschaftsgärten und Betrieben: §17 Frage 2.

## 11. Rollenmodell, Empfänger, Drittland, Unterauftragsverarbeiter, Plattform-Export (LEG-01, LEG-13, LEG-33, LEG-53)

**Ist-Stand** (`VERIFIED_CODE`). (a) **Wesentliche Mittel** bestimmt weiter der Betreiber: `attribution_visibility`
0 Treffer; E-Mail aller Mitglieder für alle sichtbar (`api/v1/tenants/schemas.py:219–223`); R-25 fest 5 Jahre
(`config/settings.py:125`); die mandanteneigene KI-Cloud-Entscheidung wirkt nicht auf das Modell (§10). Der
Verantwortlichenkontakt ist global, mit Platzhalter `"privacy@kamerplanter.example"` (`config/settings.py:1134–1135`),
und je Mandant nicht konfigurierbar (E13). Das Projekt selbst hat keine Verarbeitungsrolle (kein Phone-home).
(b) **Empfänger:** Im Code verdrahtet sind u. a. Resend/SMTP, Pl@ntNet, Kindwise, LLM über den Knowledge-Service
(Anthropic, OpenAI-kompatibel, Ollama), NASA POWER, Bright Sky (DWD), OpenWeatherMap, Open-Meteo, Web-Push,
Apprise-Kanäle, GBIF, Perenual, iNaturalist, iDigBio, Wikimedia, Fehlertracking (Sentry/GlitchTip) und Backup-S3
(`data_access/external/*`, `observability/error_tracking.py`, `helm/kamerplanter/values.yaml:593`). Ein Register mit
Rolle, Region und Übermittlungsgrundlage fehlt; REQ-025 §9 (`spec/req/REQ-025_Datenschutz-Betroffenenrechte.md:1683–1694`)
listet nur einen Teil. Regionen sind nicht verifiziert (V-12/V-13). (c) **Plattform-Export:** Neben Leitung mit
`management` darf der Plattform-Admin ein Vollarchiv fremder Mandanten auslösen (`POST /admin/platform/tenants/{key}/exports`,
`domain/services/tenant_export_service.py:282–283`; Step-up `:336`; Audit `TENANT_EXPORT_REQUESTED` `:370–376`) — im
Widerspruch zu REQ-049 P4 (`spec/req/REQ-049_Rollenmodell-und-Vokabular.md:84–85`; W-30 in `14`). Das Archiv enthält
`members.jsonl` (Schlüssel, Anzeigename, Rolle, `joined_at`, ohne E-Mail) und ungerundete `sites.gps_coordinates`
(`domain/engines/tenant_export_engine.py:192–198`); RISK-15 in `11` nennt eine Rundung, die der Code nicht macht.
Bei verwaisten Mandanten geht der Hinweis an niemanden (`tenant_export_service.py:393–397`). Ein Archiv kann auf einer
anderen Installation importiert werden (`POST /admin/platform/tenant-imports`).

**Ausgelieferter Default.** Rolle „A — Mandant Verantwortlicher, Betreiber AV“ vorgeschlagen (DA-01), aber ohne
konfigurierbare Mittel, AVV-Muster und Register; Plattform-Export ohne Begründungspflicht; Start mit
Platzhalter-Verantwortlichem möglich.

**Rechtspflicht.** Sobald mehr als eine Stelle beteiligt ist, braucht es eine Vereinbarung nach Art. 26 oder einen
Vertrag nach Art. 28 Abs. 3; Genehmigung und Pflichtenweitergabe an Unterauftragsverarbeiter (Art. 28 Abs. 2/4).
Ein AV verarbeitet nur auf dokumentierte Weisung (Art. 28 Abs. 3 lit. a); überschreitet er sie, wird er insoweit
Verantwortlicher (Art. 28 Abs. 10; L-18 Rn. 81). Empfänger und Drittlandübermittlung gehören in Hinweis und Verzeichnis
(Art. 13 Abs. 1 lit. e/f, Art. 30 Abs. 1 lit. d/e); jede Drittlandübermittlung braucht eine Grundlage nach Kapitel V.

**Auslegung.** Solange der Betreiber Frist, Sichtbarkeit und E-Mail-Sichtbarkeit festlegt, spricht EDSA 07/2020 Rn. 40
(L-18) bei PA-03/PA-04 gegen eine reine Auftragsverarbeitung. Privater Self-Host im Haushalt fällt unter die
Haushaltsausnahme (Art. 2 Abs. 2 lit. c), die Anbieter externer Dienste nicht; BM-002 mit Personenidentität von Verein
und Technikwart löst wohl kein Art. 26 aus; geteilte Installationen mehrerer Haushalte verlieren die Haushaltsausnahme
und sind wahrscheinlich Art. 26. Die Rückgabe bei Vertragsende ist als AV-Pflicht vertretbar (Art. 28 Abs. 3 lit. g),
muss aber im AVV stehen; der Download durch den Mandanten selbst ist keine Drittlandfrage, erst die Weitergabe durch ihn.

**Fragen.**
1. **Q-LAW-05** — Welches Rollenmodell gilt je Betriebsmodell (privater Self-Host, BM-001, gewerbliche Kunden, Vereine
   BM-002, geteilte Installationen)? Löst eine geteilte Installation oder eine Vereinskooperation Art. 26 aus, und
   BM-002 bei Personenidentität (LEG-01)? Hängt ab: AVV-Muster, Art.-26-Vorlage (PRA-3.03), Freigabe BM-001 (PRA-0.02,
   Q-PO-23 in `12`).
2. **Q-LAW-07** — Sind Pl@ntNet, Kindwise und die Wetterdienste eigene Verantwortliche oder Auftragsverarbeiter
   (LEG-33)? Hängt ab: AVV-Bedarf und Einträge im Empfänger-/Unter-AV-Register (PRA-1.03; Widerspruchsrecht nach
   Art. 28 Abs. 2 S. 2 erwartet: Q-CUS-11 in `12`).
3. **Q-LAW-08** — Welche AVV-Klausel trägt einen vom Plattform-Admin ausgelösten Vollexport (Rückgabe, Verwaisung,
   dokumentierte Weisung; Art. 28 Abs. 3 lit. a/g) (LEG-53, LEG-13)? Hängt ab: Ausnahmeliste zu REQ-049 P4 (Q-PO-19 in
   `12`) und PRA-2.11; die Pflichtangabe `reason` im Audit ist bis dahin ohne Freigabe auslieferbar.
4. **Q-LAW-09** — Rechtfertigt Art. 20 den Export, wenn ein Verein sein Archiv auf einer fremden Installation
   importiert (LEG-13)? Hängt ab: Hinweise beim Export (PRA-2.11), Importregel für Pseudonyme (PRA-1.07); GPS-Rundung im
   Archiv: Q-PO-20 in `12`.

**Hängt ab, ohne Freigabe.** PRA-2.18 (Startverweigerung mit Platzhalter-Verantwortlichem in `production`; Q-OP-15 in
`12`); die Erfassung des Registers selbst (PRA-1.03).

## 12. Datenschutzverletzungen (LEG-32)

**Ist-Stand** (`VERIFIED_SPEC`/`VERIFIED_CODE`). Es gibt kein Verfahren nach Art. 33/34, kein Pannenregister, keine
Meldeadresse und keine `SECURITY.md` (Root und `.github/`); `helm/` enthält keine `PrometheusRule` und keine
`- alert:`-Regel; NFR-007 führt Alerting als „Offen“ (`spec/nfr/NFR-007_Betriebsstabilitaet-Monitoring.md:95`). Vorhandene Bausteine:
`security_audit_log` (R-38, 730 Tage), `POST /auth/logout-all` (`api/v1/auth/router.py:539–547`), Widerruf von
API-Keys, Sperre von Konto und Mandant (REQ-023 §5a.5). IP-Adressen werden nach 7 Tagen anonymisiert (R-03).
Meldestelle, Bereitschaft und zuständige Aufsichtsbehörde klärt der Betreiber (Q-OP-14 in `12`).

**Ausgelieferter Default.** Nichts; Eindämmung nur mit den genannten Einzelfunktionen.

**Rechtspflicht.** Der Verantwortliche meldet binnen 72 Stunden an die Aufsichtsbehörde, sofern die Verletzung
voraussichtlich zu einem Risiko führt (Art. 33 Abs. 1), und dokumentiert **jede** Verletzung (Abs. 5); bei hohem Risiko
benachrichtigt er die Betroffenen (Art. 34). Der AV meldet dem Verantwortlichen unverzüglich (Art. 33 Abs. 2) und
unterstützt ihn (Art. 28 Abs. 3 lit. f).

**Auslegung.** Für BM-002/BM-003 trifft die Pflicht den Verein bzw. die Privatperson (Haushaltsausnahme nur BM-003);
die Software sollte Werkzeuge mitliefern. Ohne Erkennung (keine Alert-Regeln) ist die 72-Stunden-Frist faktisch nicht
beherrschbar. Audit-Daten, die der Beweissicherung dienen, unterliegen selbst Fristen (R-03, R-38); ein Pannenfall
braucht einen Hold (§7). EDSA-Leitlinien 9/2022 sind nicht im Register (Verifikationsauftrag).

**Fragen.**
1. **Q-DSB-20** — Welchen Inhalt und welche Aufbewahrung braucht das Register `privacy_incidents` (Vorschlag: Felder
   nach Art. 33 Abs. 5, Frist ≥ 3 Jahre), und wie ist die Beweissicherung gegen die Fristen R-03 (IP, 7 Tage) und R-38
   (Sicherheits-Audit, 730 Tage) zu lösen (Hold für `security_audit_log`)? Hängt ab: PRA-3.02.
2. **Q-LAW-15** — Wer meldet in BM-001, wenn eine Verletzung Mandantendaten betrifft (Art. 33 Abs. 2 vs. Abs. 1), und
   welche Rolle hat der Plattformbetreiber gegenüber den Mandanten? Hängt ab: Meldevorlagen und Funktion „Mandanten
   benachrichtigen“ (PRA-3.02); vertragliche Unterstützung und Meldefrist: Q-CUS-07 in `12`.

**Hängt ab, ohne Freigabe.** PRA-0.11 (`SECURITY.md`, Notfall-Kurzrunbook); PRA-3.02 ist Release-Blocker für BM-001
(DEC-32-Checkliste, PRA-0.02); LEG-32 eskaliert auf P0, sobald BM-001 freigegeben werden soll.

## 13. Transparenz: Art. 13, Art. 15 Abs. 1, Identität beim Export (LEG-41, LEG-50, LEG-38)

**Ist-Stand** (`VERIFIED_CODE`). (a) Das Art.-15-Bündel (`domain/engines/data_export_engine.py:1328–1388`) enthält
keine Zwecke, Empfänger, Speicherdauer, Herkunft und Rechte (Art. 15 Abs. 1 lit. a–h) und verweist nicht auf den
Policy-Endpunkt. (b) `GET /privacy/policy` (`PrivacyPolicyInfo`, `domain/models/privacy.py:850–857`;
`privacy_service.py:2155–2201`) nennt als Rechte nur Art. 15, 16, 17, 18, 20, 21, keine Kategorie für Fotos (§6) und den
Platzhalter-Verantwortlichen; die Betriebsdoku führt die Kontaktvariable als „Pflicht: Nein“
(`docs/de/reference/environment-variables.md:95–96`). (c) `GET /privacy/export*` prüft weder API-Key noch Step-up
(`api/v1/privacy/router.py:124–181`; `common/auth.py:62–79`), während die Löschung beides verlangt (`router.py:184–221`,
`:271–295`): ein ungescopter Maschinen-Schlüssel ruft eine Komplettkopie ab. Eine automatisierte Einzelentscheidung
(Art. 22) gibt es nicht (Diagnose beratend); ein Satz dazu im Bündel fehlt.

**Ausgelieferter Default.** Bündel ohne Pflichtangaben; Policy unvollständig; Export per Sitzung oder API-Key.

**Rechtspflicht.** Art. 13: Zwecke, Rechtsgrundlagen, Empfänger, Drittlandübermittlung, Speicherdauer,
Beschwerderecht (Art. 77) und Kontaktdaten sind Pflichtangaben. Art. 15: die Auskunft umfasst die Angaben nach Abs. 1
lit. a–h und eine Kopie (Abs. 3). Der Verantwortliche darf bei begründeten Zweifeln an der Identität zusätzliche
Informationen verlangen (Art. 12 Abs. 6).

**Auslegung.** Ein Verweis auf die allgemeine Datenschutzinformation genügt nach verbreiteter Auslegung nur, wenn die
Angaben dort konkret und für die Person zutreffend sind — der Policy-Endpunkt ist es heute nicht. Ein langlebiger,
ungescopter Maschinen-Schlüssel ist kein angemessener Identitätsnachweis für eine Komplettkopie.

**Fragen.**
1. **Q-DSB-13** — Genügt für Art. 15 Abs. 1 lit. a–h der Verweis auf die Datenschutzinformation, oder muss das Bündel
   einen Abschnitt `processing_information` mit den Angaben je Kategorie enthalten (LEG-41, LEG-50)? Hängt ab:
   PRA-2.18 (eine Quelle für Art.-13-Hinweis und Art.-15-Metainformationen; Texte brauchen Freigabe).
2. **Q-LAW-13** — Ist die Sitzung allein ein angemessener Identitätsnachweis für die Komplettkopie, oder ist ein Step-up
   (`data_export`) nach Art. 12 Abs. 6 geboten (LEG-38)? Hängt ab: Step-up-Tabelle in REQ-023 §3.9 (PRA-2.04); die
   API-Key-Sperre der Export-Routen ist ohne Freigabe auslieferbar.

## 14. Fotos fremder Personen an Erkennungsdienste (LEG-40, LEG-57)

**Ist-Stand** (`VERIFIED_CODE`). Die externe Bewertung eines Pflanzenfotos (`api/v1/plant_instances/photo_router.py:277–311`)
prüft nur die Einwilligung der **handelnden** Person (`assess_quality(..., user_key=user_key)`,
`domain/services/plant_photo_service.py:282–286`, `:314–343`); `_resolve_plant_attachment` prüft nur Mandant und
Kategorie (`:94–118`), nicht den Uploader. Dasselbe Muster in der Erkennung
(`domain/services/identification_service.py:99–118`, `:240–260`). Der EXIF-Strip beim Upload ist fail-open und global
abschaltbar (`domain/engines/storage/exif_stripper.py:100–136`; `config/settings.py:1340`, LEG-57); ob
`STORAGE_STRIP_EXIF` in Produktion je `false` war, klärt Q-OP-03 (`12`). Erkennungsbilder werden nicht gespeichert
(nur gekürzter Hash, `domain/models/identification.py:3–5`).

**Ausgelieferter Default.** Jedes Mitglied kann jedes Foto des Mandanten mit der eigenen Einwilligung
(`plant_identification`) an Pl@ntNet bzw. Kindwise senden.

**Rechtspflicht.** Eine Einwilligung deckt nur die Daten der einwilligenden Person (Art. 6 Abs. 1 lit. a). Für
abgebildete Personen gelten Art. 13/14.

**Auslegung.** Für reine Pflanzenfotos ohne Personenbezug unkritisch. Ein Foto, das ein anderes Mitglied hochgeladen hat
oder Dritte zeigt, trägt die Einwilligung der handelnden Person nicht ohne Weiteres; im Drittlandfall stellt sich
zusätzlich Art. 49 Abs. 1 lit. a.

**Fragen.**
1. **Q-DSB-12** — Wessen Einwilligung trägt die externe Bewertung eines fremden Fotos: genügt die der handelnden Person,
   oder ist die Bewertung auf eigene Uploads bzw. auf Fotos mit Einwilligung des Uploaders zu beschränken (auch für
   Art. 49 Abs. 1 lit. a im Drittlandfall)? Hängt ab: PRA-2.12; bis zur Antwort Beschränkung auf eigene Uploads
   (einschränkend). Fail-closed `strip_exif` vor jedem externen Versand und Upload-Strip `strict=True` (PRA-2.12,
   PRA-2.13) sind ohne Freigabe auslieferbar.

## 15. Pflichtzeilen nach Mandantenlöschung (LEG-47)

**Ist-Stand** (`VERIFIED_CODE`). Bei Mandantenlöschung bleiben `treatment_applications`, `inspections` und
`harvest_batches` pseudonymisiert erhalten (`domain/engines/tenant_erasure_engine.py:44–57` Begründungen `_R16/_R17/_R18`,
`:189–209`) — für **alle** Mandanten, unabhängig von `record_keeping` (das nicht gelesen wird, §9). Der Pflichtige (der
ehemalige Mandant) hat keinen Zugriffsweg; es gibt keine Admin-Route für zurückbehaltene Zeilen. §4 Frage 3 fragt nur
die Gegenrichtung.

**Ausgelieferter Default.** Aufbewahrung pseudonymisiert für R-16/R-17/R-18, ohne Herausgabe.

**Rechtspflicht.** Nach Vertragsende gibt der AV zurück oder löscht, soweit keine Speicherpflicht besteht (Art. 28
Abs. 3 lit. g). Art. 17 Abs. 3 lit. b greift nur, soweit die Aufbewahrung zur Pflichterfüllung **erforderlich** ist.
Pflichten: PflSchG § 11 (berufliche Anwender, L-01/L-02), KCanG § 26 (Anbauvereinigungen, 5 Jahre; die erntende Person
ist keine Pflichtangabe, L-05); privater Eigenanbau ohne Dokumentationspflicht (L-07).

**Auslegung.** Pseudonymisiert aufbewahrte Zeilen ohne Zugriffsweg des Pflichtigen erfüllen den Nachweiszweck nicht;
für Mandanten ohne Pflicht (`none`) fehlt die Grundlage ganz.

**Fragen.**
1. **Q-LAW-04** — Begründet die Aufbewahrungspflicht des Mandanten (PflSchG § 11 / KCanG § 26) eine Speicherpflicht des
   Auftragsverarbeiters nach Vertragsende (Art. 28 Abs. 3 lit. g), oder genügt eine Pflicht-Export-Bestätigung beim
   Löschen mit anschließender Löschung? Hängt ab: PRA-2.09 (sofortige Löschung für `none`, Aufbewahrung nur für
   Pflichtklassen, Herausgabeprozess) — datenvernichtend, daher erst nach Antwort; setzt PRA-1.02 voraus.

## 16. GPS an Wetterdienste; Fehlertracking (LEG-49, LEG-16)

**Ist-Stand** (`VERIFIED_CODE`). (a) **Wetter:** Die Adapter senden die Standortkoordinaten ungerundet an Open-Meteo,
OpenWeatherMap, Bright Sky und NASA POWER (USA) (`data_access/external/open_meteo_weather_adapter.py:58–72`,
`openweathermap_weather_adapter.py:110–122`, `dwd_weather_adapter.py:150–165`, `nasa_power_weather_adapter.py:99–106`,
`:156–161`; Aufrufer `domain/services/weather_source_resolver.py:171–199`, `weather_source_service.py:376–380`);
`domain/models/site.py:845–854` prüft nur den Wertebereich. Die eigene MUSS-Anforderung DP-002 (Rundung,
`spec/req/REQ-025_Datenschutz-Betroffenenrechte.md:1691`, `:1700`) ist nicht umgesetzt; kein Test. (b)
**Fehlertracking:** ohne `SENTRY_DSN` kein Betrieb (`observability/error_tracking.py:647–648`; Helm `SENTRY_DSN: ""`,
`values.yaml:832`); `send_default_pii=False` (`:675`); `before_send=scrub_event` (`:523–560`, `:685`) bereinigt
Request-Daten, verwirft den SDK-`user` und setzt nur das Pseudonym bei Einwilligung `error_tracking`; Frontend-Init nur
nach Einwilligung `browser_error_reports` (seit #3025 ein eigener Zweck; Rechtsgrundlage dort beim Umsetzen konservativ
als Einwilligung nach Art. 6 Abs. 1 lit. a DSGVO und § 25 Abs. 1 TDDDG festgelegt — zu bestätigen, ebenso ob der
Einwilligungsnachweis wie bei jedem Zweck nach NFR-011 R-04 aufbewahrt wird). LIA-4 ist in `06` §4.4 nur ein Verweis. Region und Frist des Trackers sind außerhalb des Repos
(Q-OP-01, Q-OP-09 in `12`).

**Ausgelieferter Default.** Exakte Koordinaten an den konfigurierten Wetterdienst; Fehlertracking aus.

**Rechtspflicht.** Datenminimierung (Art. 5 Abs. 1 lit. c); bei Sentry SaaS gelten Art. 28 und Kapitel V.

**Auslegung.** Exakte Gartenkoordinaten sind über Installation und IP beim Dienst personenbeziehbar; die nicht
umgesetzte Rundung verfehlt die eigene Minimierungszusage. lit. f ist für bereinigte Fehlerereignisse gut vertretbar;
selbst gehostetes GlitchTip oder EU-Hosting vermeidet die Drittlandfrage.

**Fragen.**
1. **Q-DSB-18 (a)** — Bestätigt der DSB eine LIA für die Übermittlung der Koordinaten an Wetterdienste, und welche
   Rundungsstufe ist angemessen (LEG-49)? Hängt ab: Rundungsstufe in PRA-2.14 (`coarsen_coordinates` vor jedem
   Wetteradapter, ohne Freigabe auslieferbar).
2. **Q-DSB-18 (b)** — Trägt Art. 6 Abs. 1 lit. f das Fehlertracking mit den belegten Schutzmaßnahmen, sobald LIA-4
   ausformuliert ist (LEG-16)? Hängt ab: PRA-3.05; danach LEG-16 `decided`.

## 17. Verschlüsselung ruhender Daten; DSFA je Betriebsmodell (LEG-42, LEG-12, LEG-48)

**Ist-Stand.** (a) **Verschlüsselung ruhender Daten** ist weder erzwungen noch als Betreiberanforderung dokumentiert
(`helm/kamerplanter/values.yaml:607–608`, `:3253–3261`; `grep -rni "at rest\|ruhend\|LUKS" docs/de/deployment
spec/stack.md spec/nfr/NFR-002*` → 0); vorhanden sind Feldverschlüsselung (`domain/engines/encryption_engine.py`) und
SSE für S3 (`data_access/storage/s3_adapter.py:106`, `:297`). Volume-Verschlüsselung in Produktion klärt Q-OP-10
(`12`). (b) **DSFA** (`VERIFIED_SPEC`): Es gibt keine DSFA und kein Verzeichnis im Repo; die Nutzerdoku behauptet
weiter eine durchgeführte DSFA (`docs/de/user-guide/privacy.md:488–490`, W-10). Die Vorprüfung
[`11-dpia-pre-screening.md`](11-dpia-pre-screening.md) übersieht Aufgaben-Leistungsdaten (LEG-28), `control_events`
(LEG-29), die Weitergabe per Service-Account/MCP an Drittsysteme und das Modell „selbst gehostet, gewerblich“, für das
kein DEC-32-Gate greift (LEG-48); KI und MCP werden als „innovative Nutzung“ verneint. Die Aussage zu Art. 36 („nicht
erforderlich“) stützt sich auf nicht gebaute Maßnahmen.

**Ausgelieferter Default.** Verschlüsselung Sache des Betreibers, undokumentiert; keine DSFA-Bestätigung bei Anlage
eines gewerblichen Mandanten (Klassifizierung inert, §9).

**Rechtspflicht.** Dem Risiko angemessene TOM nach dem Stand der Technik einschließlich regelmäßiger Wirksamkeitsprüfung
(Art. 32 Abs. 1, lit. d); Verschlüsselung ist dort Beispiel, keine absolute Pflicht. Ohne Verschlüsselung entfällt die
Ausnahme von der Benachrichtigung nach Art. 34 Abs. 3 lit. a. Die DSFA-Pflicht trifft den **Verantwortlichen** — im
AV-Modell den Mandanten, beim Selbsthosting den Betreiber, der zugleich Arbeitgeber ist; der Anbieter liefert die
Eingaben (Art. 28 Abs. 3 lit. f). Die DSK-Muss-Liste nennt die umfangreiche Verarbeitung von Beschäftigtenverhalten,
die zur Bewertung eingesetzt werden **kann** (Nr. 8, L-17). Die Behauptung einer DSFA ohne DSFA ist ein
Transparenzmangel (Art. 5 Abs. 1 lit. a, Art. 12 Abs. 1).

**Auslegung.** Das Fehlen einer Verschlüsselung ruhender Daten verlangt eine dokumentierte Abwägung (Art. 5 Abs. 2).
Die Abkehr von der Zählregel (DA-08) ist leitlinienkonform (L-16). Mit den Aufgaben-Leistungsfeldern ist in
gewerblichen Mandanten Kriterium 1 (Bewertung) objektiv erfüllt, ebenso Kriterium 3 (systematische Überwachung) und
7 (Beschäftigte) → DSFA-Pflicht gewerblich bestätigt und verschärft. KI und MCP in Gemeinschaftsgärten und Betrieben
(Freitext und Fotos Dritter an externe Modelle) berühren WP248-Kriterium 8 (innovative Nutzung).

**Fragen.**
1. **Q-DSB-17** — Wie ist das Fehlen einer erzwungenen Verschlüsselung ruhender Daten im TOM-Verzeichnis zu bewerten:
   genügt eine dokumentierte Abwägung, oder soll das Chart eine verschlüsselte StorageClass verlangen
   (`security.requireEncryptedStorageClass`) (LEG-42)? Hängt ab: PRA-3.07 (ohne Freigabe auslieferbar; die Bewertung
   bestimmt, ob Pflicht oder Option).
2. **Q-DSB-08 (greift §5 Frage 4 auf)** — Bestätigt der DSB die fortgeschriebene Schwellwertprüfung: gewerblich
   „erforderlich“ (Kriterien 1, 3, 7), Verein „empfohlen“ oder — ohne Maßnahmen gegen die unbeschränkte
   Zurechnungssichtbarkeit — „erforderlich“, das neue Modell „selbst gehostet, gewerblich“, eine DSFA für KI und MCP in
   Gemeinschaftsgärten und Betrieben, die Schwelle „umfangreich“ bei Kleinbetrieben und eine Art.-36-Aussage für den
   **Ist-Zustand**; dazu den Verzeichniseintrag „Speicherung auf dem Endgerät“ (LEG-12, LEG-48)? Hängt ab: Inhalt von
   `11` und die auditierte Pflichtbestätigung der Leitung bei `commercial` („DSFA durchgeführt / Betriebsrat beteiligt /
   nicht erforderlich (Begründung)“) in PRA-3.04; die Korrektur von W-10 (PRA-0.05) ist ohne Freigabe auslieferbar.
   Weitergabe per Service-Account an Home Assistant oder Grafana klärt Q-OP-13 (`12`).

## 18. Was mit der Antwort geschieht

| Antwort | Durchsetzung |
|---------|--------------|
| je Frage | LEG-Zeile in `decision-log.md` §B (LEG-01…LEG-22) bzw. Befundzeile in §D (LEG-23…LEG-70) auf `decided` mit Datum, Quelle der Entscheidung und umsetzender PRA-Aufgabe (PRA-3.01) |
| Backup/Restore-Fragen mit vorgeschlagener Architekturentscheidung (Q-DSB-22 → DEC-36, Q-DSB-23 → DEC-38, Q-DSB-25 → DEC-39; Nachtrag 2026-11-23) | zusätzlich DEC-Zeile in `decision-log.md` §A von `proposed` auf `accepted` oder `rejected`; bei `rejected` passt die Hauptsession `17` (Taxonomie §3.3, Frist §3.8, Konfliktregel §3.6) und `06` R-63 an |
| einschränkend (weniger sichtbar, kürzere Frist, mehr löschen) | sofort umsetzbar (`processing_allowed: ja`), PRA-Aufgabe laut [`12`](12-implementation-roadmap.md) |
| ausweitend (mehr Verarbeitung) | erst nach registrierter Entscheidung, hinter Schalter (`08` §8a) |
| datenvernichtend (Reklassifizierung, Löschung statt Pseudonym) | erst nach Antwort und Betreiberfreigabe; Flag mit Default aus |
| Beetfotos löschen statt anonymisieren (LEG-20 B) | Wechsel der Kategorien `location`/`garden_plan_underlay` von `user_diary_attachments` nach `user_personal` in `erasure_engine` und `local_fs_adapter._erasure_scope_categories`; Variante C zusätzlich ein Flag im Erasure-Request (PRA-2.12) |

**Je Frage.** „Ohne Freigabe“ heißt: die Aufgabe wird mit dem genannten Default vorab ausgeliefert; die Antwort legt nur
den Wert fest oder kehrt ihn um. Prüfdatum für alle offenen Punkte: 2027-01-31 (Vorschlag, `decision-log.md` §B).

| Frage | LEG | PRA-Aufgabe | bis zur Antwort | Freigabe nötig für |
|---|---|---|---|---|
| Q-DSB-01 (§1 F1, F4) | LEG-02 (LEG-19) | PRA-2.05 | CSV-Namen nur mit Berechtigung, Audit, R-25a mit Default = Bestand | Wert der Zurechnungsfrist; Default `attribution_visibility` |
| §1 F2, Q-LAW-01, Q-LAW-03 | LEG-05 | PRA-2.05, PRA-3.01 | `leads_and_self` in `commercial` erzwungen | erzwungen vs. Default; Text der Mandantenvorlage |
| §1 F3 | LEG-05 | — | Regel umgesetzt | Bestätigung |
| Q-DSB-02 (§2 F2, F4) | LEG-06 | PRA-2.03, PRA-2.04 | Unterdrückung nach 90 d; Teilquelle verlassene Mandanten | endgültiger Fristwert; Umfang Art. 15 |
| Q-DSB-03 (§2 F1, F3, F5) | LEG-15, LEG-54, LEG-65 (Nachtrag 2026-11-23) | PRA-1.07 | `anon2_`, Importregel, Residue-Scan; Import gleicht gegen abgeschlossene Löschungen ab (`17` §6.4) | Verhältnismäßigkeit des Bestands |
| Q-DSB-04 (§3 F1–F4) | LEG-08, LEG-34 | PRA-2.01, PRA-2.02 | Prüfwarteschlange, Feldmenge inkl. `material`, Snapshots schwärzbar | Auto-Schwärzung nach SLA |
| Q-LAW-06 (§3 F5) | LEG-06, LEG-08 | PRA-2.01, PRA-2.04 | Leads entscheiden in der Warteschlange | Entscheidungsbefugnis; Ort der Auskunft |
| Q-LAW-11 (§3 F6) | LEG-08, LEG-12 | PRA-2.01, PRA-3.04 | Hinweistexte, Längengrenzen | DSFA-Bewertung der Art.-9-Hinweise |
| Q-DSB-05 (§4 F1, F3) | LEG-07 | PRA-2.08 | Schalter mit Default = Bestand, `commercial` → keine Kopie | Umschalten des globalen Defaults |
| §4 F2 | LEG-07 | PRA-2.08 | Bestand | — |
| Q-DSB-06 (§5 F1) | LEG-09, LEG-27 | PRA-2.15, PRA-0.07 | Projektion im SW-Cache | Opt-in als „ausdrücklich gewünscht“ |
| Q-DSB-07 (§5 F2, F3, F5) | LEG-10, LEG-37 | PRA-0.08, PRA-2.15, PRA-2.17 | Logout-Grundsicherung, Quarantäne | Defaults 90/30/14 d |
| Q-LAW-16 (§5 F6) | LEG-09 | PRA-2.15 | `processing_allowed = provisorisch` | Interim vor PRA-2.15 |
| Q-LAW-17 (§5 F7) | LEG-27 | PRA-0.07, PRA-2.18 | Projektion | Informationstext |
| Q-DSB-09, Q-LAW-12 (§6 F1, F4) | LEG-20 | PRA-2.12 | anonymisieren, `caption` leeren, Begründung korrigiert | Variante B/C |
| Q-DSB-10 (§6 F2, F5) | LEG-21 | PRA-2.04 | Kontoquelle mit `_key`/`created_at` | ZIP-Umfang, Dritten-Prozess |
| Q-DSB-11 (§6 F3, F6) | LEG-22 | PRA-2.18 | Fotozeile im Policy-Endpunkt | Gliederung, Art.-14-Text |
| Q-DSB-14 (§7) | LEG-23, LEG-35 | PRA-0.05, PRA-0.06, PRA-1.06 | Doku korrigiert, Antrag erreicht Betreiber | Zweckliste; Hold-Berechtigung und -Dauer |
| Q-LAW-14 (§8 F1) | LEG-11 | PRA-0.10, PRA-1.05 | Render-Fehler ohne Journal, Dumps ≤ 35 d | Backup-Aktivierung (`deployment_allowed`) |
| Q-DSB-15 (§8 F2) | LEG-11, LEG-25 | PRA-1.04 | — | Zulässigkeit des Journals; R-63 (statt R-45) |
| Q-DSB-16 (§8 F3) | LEG-24, LEG-11, LEG-70 | PRA-1.05 | — | Toleranzfenster; Restore-Gate inkl. Worker/Beat (`17` §5.3) |
| Q-DSB-22 (§8 F4) | LEG-11, LEG-44 | PRA-1.04, PRA-0.10 | — (Journal nicht gebaut); Vorschlag R-63 | Journal-Frist R-63; DEC-36 |
| Q-DSB-23 (§8 F5) | LEG-11 | PRA-1.04 | nur Anhänge und Schwärzungen journalisiert | gewöhnliche Löschungen ohne Journal; DEC-38 |
| Q-DSB-24 (§8 F6) | LEG-11, LEG-24 | PRA-1.05 | Gate bleibt zu, kein Rückfall ohne `FALLBACK_REVIEW` | Freigabe mit Lücke; Information Betroffener/Mandanten |
| Q-DSB-25 (§8 F7) | LEG-24 | PRA-1.05, PRA-1.04 | Einwilligung nach dem Backup erneut einholen | Wiederherstellung aus dem Journal; DEC-39 |
| Q-DSB-26 (§8 F8) | LEG-33, LEG-11 | PRA-1.05, PRA-2.20 | externe Abflüsse während der Isolation aus | erneute Mitteilung an Empfänger |
| Q-LAW-18 (§8 F9) | LEG-24, LEG-32 | PRA-3.02, PRA-0.03 | Prüfung als möglicher Vorfall; Alarm `PrivacyRecoveryBlocked` | Einordnung als Verletzung, Meldepflicht |
| Q-LAW-19 (§8 F10) | LEG-11, LEG-15 | PRA-1.04 | Object Lock Governance, nur Pseudonyme | Compliance-Mode BM-001; Ausnahme vom Löschanspruch |
| Q-LAW-02 (§9 F2) | LEG-05, LEG-28 | PRA-2.06, PRA-3.04 | Leistungsfelder eingeschränkt | Mustertext Betriebsrat |
| Q-DSB-21 (§9 F4) | LEG-28, LEG-29 | PRA-2.06, PRA-2.07 | Frist 90 d | Bestätigung des Werts |
| Q-DSB-19 (§10 F1) | LEG-31 | PRA-0.09, PRA-1.03 | Gate am tatsächlichen Provider, fail-closed | Übermittlungsgrundlage, Einwilligungstext |
| Q-LAW-10 (§10 F2) | LEG-51, LEG-52 | PRA-2.10 | Option A | Option B |
| Q-LAW-05 (§11 F1) | LEG-01 | PRA-3.03, PRA-0.02 | `deployment_allowed` BM-001 nein | Rollenmodell, AVV, Art.-26-Vorlage |
| Q-LAW-07 (§11 F2) | LEG-33 | PRA-1.03 | Register erfasst | Rollen, Übermittlungsgrundlagen |
| Q-LAW-08 (§11 F3) | LEG-53, LEG-13 | PRA-2.11, PRA-3.03 | Pflichtangabe `reason` | AVV-Klausel, Ausnahmeliste |
| Q-LAW-09 (§11 F4) | LEG-13 | PRA-2.11, PRA-1.07 | Importregel | Hinweise beim Export |
| Q-DSB-20 (§12 F1) | LEG-32 | PRA-0.11, PRA-3.02 | `SECURITY.md`, Runbook | Registerinhalt, Frist, Hold |
| Q-LAW-15 (§12 F2) | LEG-32 | PRA-3.02 | — | Meldevorlagen, Rolle des Betreibers |
| Q-DSB-13 (§13 F1) | LEG-41, LEG-50 | PRA-2.18 | Startverweigerung mit Platzhalter | Texte gegenüber Betroffenen |
| Q-LAW-13 (§13 F2) | LEG-38 | PRA-2.04 | API-Key-Sperre der Export-Routen | Step-up |
| Q-DSB-12 (§14) | LEG-40 | PRA-2.12, PRA-2.13 | nur eigene Uploads; EXIF fail-closed | Einwilligungsmodell |
| Q-LAW-04 (§15) | LEG-47 | PRA-2.09 (nach PRA-1.02) | Bestand | Löschung für `none`; Speicherpflicht des AV |
| Q-DSB-18 (§16) | LEG-49, LEG-16 | PRA-2.14, PRA-3.05 | Koordinaten vergröbert | Rundungsstufe; LIA-4 |
| Q-DSB-17 (§17 F1) | LEG-42 | PRA-3.07 | Betreiberanforderung dokumentiert | Pflicht oder Option |
| Q-DSB-08 (§17 F2, §5 F4) | LEG-12, LEG-48 | PRA-3.04, PRA-0.05 | W-10 korrigiert | Texte, Schwelle „umfangreich“ |

Vor einer MUSS-Anforderung zusätzlich an der Quelle zu verifizieren (Quellenarbeit, keine Rechtsfrage; `13`): V-04,
V-06 (Art. 67 VO 1107/2009, DVO 2023/564), V-05 (BAG), V-07 (DSGVO-Wortlaute), V-08 (C-34/21), EDSA-Leitlinien 9/2022,
Regionen der Dienste (V-12/V-13, PRA-1.03).
