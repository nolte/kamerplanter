# SPEC-06 — Verarbeitungstätigkeiten, Rechtsgrundlagen und Aufbewahrung

```
Paket: spec/privacy · Version 1.2 · 2026-11-22 · Gemessen gegen: develop 007a4ea90 (Audit 2026-11-22)
(v1.1: develop 24d1c2988; Nachtrag #2839 develop 343afbb97)
Anforderungs-IDs: PRIV-400 … PRIV-449
Hängt ab von: NFR-011 (Aufbewahrungsregeln R-nn), REQ-025 §3, 02 (Inventar), 03/04 (Verhalten),
13 (Rechtsevidenz L-nn), 15 (Entscheidungsanalysen DA-01…DA-04)
Änderung v1.1: Rollenmatrix (§1), Verarbeitungstätigkeitenmatrix (§2), feldgenaue Zuordnung der
Pflichtaufzeichnungen (§3), Evidenzklassen an jeder Rechtsgrundlage, Produktionsgates (§10).
Änderungen 1.2: Verantwortlichkeitsmodell je Betriebsmodell (§1a, LEG-01); PA-04a, PA-13…PA-17 und
Bewertung der Rechtsgrundlagen (§2, §2.1); KI-Cloud-Gate (§2.2, LEG-31), Empfänger-/Unter-AV-Inventar mit
Drittland (§2.3, LEG-33), Wetterkoordinaten DP-002 (§2.4, LEG-49), Mandantenarchiv (§2.5, LEG-13);
Ist-Stand Klassifizierung und Pflichtzeilen nach Mandantenlöschung (§3.3, LEG-30/LEG-47); LIA-2 fortlaufende
Kopie (LEG-07), LIA-4-Lücke (LEG-16); Zweckbindung korrigiert (§6); Art.-13-Lücken der Policy (§7.1, LEG-50);
Aufbewahrungsmatrix vollständig mit R-49…R-62 (§8, LEG-44); Gates (§10); neuer §11 Compliance-Matrix (59 Zeilen).
Nachtrag 2026-11-23 (gemessen gegen develop ce7e858d0): Aufbewahrung R-63 (Journal), R-64 (Restore-Evidence-Reports),
R-65 (Quarantäne verwaister Objekte nach Restore) aus `17-privacy-recovery.md` §3.8/§7.4/§11.5; R-45 durch R-63
ersetzt; R-53 um LEG-68 ergänzt; PA-09 und Backup-Gate auf `17`; Compliance-Matrix Art. 5/17/18/19/21/25/30/32/35 um
`17` und die vorgeschlagenen PRA-0.12, PRA-1.08, PRA-2.21…2.23, PRA-3.11 ergänzt (Status unverändert: nichts davon
ist implementiert).
```

Evidenzklassen: `VERIFIED_CODE` · `VERIFIED_SPEC` · `VERIFIED_LEGAL` (mit L-nn) · `INFERRED` ·
`PROPOSED` · `OPEN_DECISION` · `LEGAL_REVIEW_REQUIRED` (mit LEG-nn). Eine Rechtsgrundlage ohne
L-Verweis ist `INFERRED`. **Art. 17 Abs. 3 DSGVO ist eine Ausnahme vom Löschanspruch, keine
Rechtsgrundlage** — wo NFR-011 „Art. 17(3)“ als Grundlage nennt (R-25), ist das ein zu korrigierender
Spec-Text (§9, E16).

---

## 1. Rollenmatrix — wer bestimmt Zwecke und wesentliche Mittel (LEG-01, DA-01)

Maßstab: EDSA 07/2020 Rn. 40, 54–55, 81 (L-18, `VERIFIED_LEGAL`): Der Verantwortliche bestimmt Zwecke
und **wesentliche Mittel** (welche Daten, wie lange, wer hat Zugriff); nicht wesentliche Mittel darf der
Auftragsverarbeiter festlegen; konvergierende Entscheidungen begründen gemeinsame Verantwortlichkeit.

| PA | Verarbeitungstätigkeit | Zweck bestimmt von | Wesentliche Mittel heute bestimmt von (VERIFIED_CODE) | Nach Umsetzung E08/E09 | Rolle Betreiber (PROPOSED) | Rolle Mandant | Erforderliche Dokumente |
|----|------------------------|--------------------|--------------------------------------------------------|------------------------|-----------------------------|---------------|-------------------------|
| PA-01 | Kontoverwaltung, Authentifizierung, Sitzungen | Betreiber | Betreiber | — | **Verantwortlicher** | — | Datenschutzinformation Plattform (Art. 13) |
| PA-02 | Sicherheits-Audit, Logs, Monitoring | Betreiber | Betreiber | — | **Verantwortlicher** | — | dito; Art.-30-Eintrag Betreiber |
| PA-03 | Mitgliederverwaltung des Mandanten (Einladung, Rollen, Scopes, E-Mail-Sichtbarkeit) | Mandant | Betreiber (Datenfelder, 730 d Audit) | Mandant (E-Mail-Sichtbarkeit), Betreiber (Audit) | Auftragsverarbeiter (Mitgliederdaten); Verantwortlicher (Audit) | **Verantwortlicher** | AVV; Datenschutzinformation Mandant (Art. 13); Art.-30-Eintrag Mandant |
| PA-04 | Pflegeprotokoll mit Zurechnung (`care_events`, Bestätigungen, Plan-Audit) | Mandant (Koordination, Historie) | **Betreiber** (Frist 5 J. fest, Sichtbarkeit fest) → Indiz gegen reine Auftragsverarbeitung | Mandant (`attribution_visibility`, Aufbewahrung innerhalb Grenzen), Betreiber (Grenzen, Verfahren) | Auftragsverarbeiter **nach** E08/E09; bis dahin OPEN_DECISION (Art. 26?) | **Verantwortlicher** | AVV; LIA-1/LIA-2 des Mandanten (Vorlage aus §4); Mustertext Betriebsrat (PRIV-406) |
| PA-05 | Gesetzliche Aufzeichnungen (PflSchG, KCanG) | Mandant (gesetzliche Pflicht trifft ihn) | Betreiber (Collection-weit für alle) | Mandant (`record_keeping`, `organization_kind`) | Auftragsverarbeiter | **Verantwortlicher** | AVV; Art.-30-Eintrag Mandant; Nachweis der Pflicht (Klassifizierung) |
| PA-06 | Tagebuch, Freitext, Fotos | Mandant / Nutzer | Betreiber (Aufbewahrung „Lebensdauer“) | unverändert (Inhalt), Prüfwarteschlange (E07) | Auftragsverarbeiter | **Verantwortlicher** | AVV |
| PA-07a | Betroffenenrechte Konto (Art. 15–21 Selbstbedienung) | Betreiber (Pflicht) | Betreiber | — | **Verantwortlicher** | — | Verfahrensbeschreibung |
| PA-07b | Betroffenenrechte in Mandantendaten (Prüfwarteschlange, Schwärzung) | Mandant (Pflicht) | Betreiber (Verfahren) | Mandant (Entscheidung), Betreiber (Werkzeug) | Auftragsverarbeiter (Unterstützung Art. 28 Abs. 3 lit. e) | **Verantwortlicher** | AVV mit Unterstützungspflichten |
| PA-08 | Speicherung auf dem Endgerät (Cache, Puffer, Web Storage) | Betreiber (Dienstgestaltung) | Betreiber | Nutzer (Schalter), Betreiber (Fristen) | **Anbieter des digitalen Dienstes** (TDDDG) und Verantwortlicher für die Gestaltung | — | Datenschutzinformation Plattform §„Daten auf dem Gerät“ |
| PA-09 | Backups und Wiederherstellung | Betreiber | Betreiber | — | **Verantwortlicher** (eigener Zweck Datensicherheit) | — | Art.-30-Eintrag Betreiber; AVV-Anlage TOM |
| PA-10 | Sensorik/Aktorik (TimescaleDB, Overrides) | Mandant | Betreiber (Fristen) | — (außerhalb dieses Pakets) | Auftragsverarbeiter | **Verantwortlicher** | DSFA Sensorik (NFR-001 §6.7) |
| PA-11 | Mandantenexport/-import (REQ-056) | Mandant | Betreiber (Format) | — | Auftragsverarbeiter | **Verantwortlicher** (Empfänger des Archivs) | AVV; LEG-13 |
| PA-12 | Plattform-Support (Admin-Zugriff auf Mitgliederlisten, Löschvorschau) | Betreiber | Betreiber | — | **Verantwortlicher** | — | Datenschutzinformation Plattform |

**Selbst gehostete Installation:** Betreiber = Mandant; alle Zeilen kollabieren auf einen Verantwortlichen;
AVV entfällt, Art.-30-Einträge bleiben.

**PRIV-409** [PROPOSED, DA-03/DA-04] Ein Organisationsmandant MUSS bei der Anlage klassifiziert werden:
`organization_kind ∈ {association, commercial, community, other}` und `record_keeping ∈ {none,
pflschg_professional, kcang_association, both}`; ohne Angabe ist der Zustand `undeclared`. `undeclared`
verhält sich bei der Aufbewahrung konservativ (wie `legacy`), erzeugt aber **keinen** Tombstone für
`harvested_by_key` (§3.2) und zeigt der Leitung bei jeder Anmeldung einen Hinweis, bis die Angabe erfolgt;
der Betreiber sieht die Zahl `undeclared`-Mandanten (PRIV-110-Endpunkt). Bestehende Mandanten erhalten
`legacy` durch v0110 (`09` §4). Persönliche Mandanten sind `none` (L-07: kein Dokumentationsrecht/-pflicht
im Eigenanbau; INFERRED für Zierpflanzen ohnehin).
**Ist-Stand (Audit 2026-11-22, LEG-30):** [VERIFIED_CODE] nicht gebaut. Die Felder existieren nur im Modell
(`domain/models/tenant.py:35,38`, Kommentar „In no request or response schema yet“ `:31–38`), im Mandantenexport
(`tenant_export_service.py:145`) und in v0110; kein Anlagepfad setzt sie, kein Leser wertet sie aus. Folge: Die
Aufbewahrungsregeln aus §3 und die Klassen-Defaults aus §5 sind inert; Umsetzung PRA-1.02 (Sachverhalt `05`).

**Wesentliche Mittel heute (Audit 2026-11-22, LEG-01):** [VERIFIED_CODE] `attribution_visibility` hat 0 Treffer in
`src/`; Mitglieder-E-Mails sind für alle Mitglieder sichtbar (`api/v1/tenants/schemas.py:219–223`, `router.py:275`);
R-25 ist fest 5 J. (`config/settings.py:125`); der Verantwortlichenkontakt ist global mit dem Platzhalter
`"Kamerplanter Operator"`/`"privacy@kamerplanter.example"` (`config/settings.py:1134–1135`), nicht je Mandant (E13
offen). Die mandanteneigene KI-Provider-Konfiguration wirkt nicht auf das tatsächlich verwendete Modell (§2.2). Das
Projekt selbst hat keine Verarbeitungsrolle (kein Phone-home, keine Hersteller-Telemetrie; nur pseudonyme
Request-Telemetrie `common/request_context.py`). Die Spalte „Nach Umsetzung E08/E09“ oben ist damit weiterhin Soll.

### 1a. Verantwortlichkeitsmodell je Betriebsmodell (LEG-01; PROPOSED, `LEGAL_REVIEW_REQUIRED`)

Empfehlung des Audits 2026-11-22 (Strang F); rechtliche Freigabe über LEG-01 (Q-LAW-05 in `16`), Umsetzung der
Dokumente PRA-3.03. Maßstab L-18 Rn. 40, 54–55, 81; Haushaltsausnahme Art. 2 Abs. 2 lit. c und ErwG 18 als Bezug (L-12).

| Betriebsmodell | Verantwortlicher | Auftragsverarbeiter | Gemeinsame Verantwortung (Art. 26) | Unterauftragsverarbeiter | Pflichtdokumente | Bedingung / Anmerkung |
|---|---|---|---|---|---|---|
| (1) Privater Self-Host (BM-003, Haushalt) | Privatperson; DSGVO nach Art. 2 Abs. 2 lit. c nicht anwendbar, **soweit** nur Haushalt | — | — | externe Dienste in **eigener** Verantwortung bzw. als Dienstleister der Person (die Haushaltsausnahme deckt nicht die Anbieter, ErwG 18) | keine nach DSGVO; Doku-Hinweis: Cloud-LLM, Pl@ntNet und Wetterdienste übermitteln Daten | öffentlich erreichbare Instanz oder Personen außerhalb des Haushalts → (5) |
| (2) Kamerplanter-SaaS (BM-001) | **Betreiber**: PA-01, PA-02, PA-07a, PA-08, PA-09, PA-12, Plattform-Sicherheit, KI-Plattformmodell (solange der Mandant das Modell nicht wählt) | **Betreiber für den Mandanten**: PA-03…PA-06, PA-07b, PA-10, PA-11 — erst nach E08/E09/E13, sonst Indiz für Art. 26 | Option für PA-04, solange der Betreiber Frist und Sichtbarkeit fest bestimmt (LEG-01 Option B) | Resend/SMTP, LLM-Anbieter, Sentry, S3, ggf. Pl@ntNet/Kindwise (falls AV) — §2.3 | Datenschutzinformation Plattform (Art. 13), AVV-Muster mit Unter-AV-Liste und TOM, Art.-30-Verzeichnis (Betreiber + Mandantenvorlage), DSFA gewerblich (`11`), Datenpannenverfahren (LEG-32), Drittlandprüfung | `deployment_allowed` erst nach LEG-01/05/12, LEG-31, LEG-32, LEG-33 (DEC-32-Checkliste, PRA-0.02) |
| (3) Gewerbliche Kunden (BM-001-Mandant `commercial`) | **Kunde** (Arbeitgeber) für Beschäftigtendaten und Inhalte; PflSchG-Pflichten | Betreiber (AVV) | nein (Default) | wie (2), vom Kunden genehmigt (Art. 28 Abs. 2) | AVV, Information der Beschäftigten (Art. 13; PRIV-408), ggf. Betriebsvereinbarung (§ 87 Abs. 1 Nr. 6 BetrVG, L-10; PRIV-406), DSFA des Kunden | `attribution_visibility=leads_and_self` (E08), Klassifizierung (E09), MCP-Freitext nur eigene (PRA-2.10) |
| (4) Gemeinschaftsgärten / Vereine (BM-002 Self-Host oder BM-001-Mandant) | **Verein** (Art. 4 Nr. 7) | Self-Host: Technikwart als Organ, kein AV; Hoster der Infrastruktur (VPS) als AV. SaaS: Betreiber als AV | nein (Default); bei Kooperation mehrerer Vereine auf einem Mandanten prüfen | Self-Host: VPS, Mailer, LLM; SaaS: wie (2) | Mitgliederinformation (Satzung oder Art. 13), Verzeichnis, KCanG-Pflichten bei Anbauvereinigungen (L-05), Datenpannenverfahren des Vereins | `light`-Modus unzulässig (BM-002 §6.1); Einwilligungen der Mitglieder für KI und MCP |
| (5) Geteilte Installationen (mehrere Haushalte, Familie/Freunde, Mehrnutzer-Self-Host ohne Verein) | **Betreiber der Instanz** (natürliche Person), sobald Dritte außerhalb des Haushalts Konten haben (Haushaltsausnahme entfällt); je Mandant ggf. das Mitglied für eigene Inhalte | Betreiber für fremde Mandanten, wenn diese eigene Zwecke verfolgen | **wahrscheinlich Art. 26** zwischen Instanzbetreiber und Mandanten-Leitung (`LEGAL_REVIEW_REQUIRED`) | wie (4) | vereinfachte Information, Vereinbarung nach Art. 26 oder AVV-Light, Verzeichnis | häufigster Graubereich; Doku-Empfehlung „ab dem zweiten Haushalt `full` und Information“ |

Auslegung (Audit 2026-11-22, INFERRED): Solange der Betreiber Frist, Sichtbarkeit und E-Mail-Sichtbarkeit fest
bestimmt, spricht das bei PA-03/PA-04 gegen eine reine Auftragsverarbeitung; die Rolle „A — Mandant
Verantwortlicher, Betreiber AV“ trägt erst, wenn diese Mittel konfigurierbar sind (E08, E09, E13; PRA-1.02, PRA-2.05,
PRA-3.03). Eine gespeicherte, aber inerte Klassifizierung (LEG-30) verhindert zudem, dass der Betreiber seine
Unterstützungspflicht nach Art. 28 Abs. 3 lit. f klassenabhängig erfüllt. Schutzmaßnahme ohne Rechtsfreigabe:
Startverweigerung für den Platzhalter-Verantwortlichen in `full`/`production` (PRA-2.18).

---

## 2. Verarbeitungstätigkeiten-Matrix (Art. 30-Zuarbeit)

Spalten: Zweck · Betroffene · Datenkategorien (`02`) · Empfängerkategorien · Rechtsgrundlage (Evidenz) ·
Erforderlichkeit · Aufbewahrung (R-nn) · Betroffenenrechte (Besonderheiten) · Verantwortlicher ·
Auftragsverarbeiter-Beteiligung.

| PA | Zweck | Betroffene | Datenkategorien | Empfänger | Rechtsgrundlage | Erforderlichkeit | Aufbewahrung | Rechte | Verantw. | AV |
|----|-------|------------|-----------------|-----------|-----------------|------------------|--------------|--------|----------|----|
| PA-01 | Konto, Login, Sitzung | Kontoinhaber | IDN, PRO, AUTH | keine (OAuth-Provider bei Föderation: REQ-025 §9) | Art. 6 Abs. 1 lit. b (Nutzungsvertrag) — INFERRED; IP-Sicherheit lit. f (VERIFIED_SPEC REQ-023) | Login ohne Konto unmöglich | R-01…R-11 | Art. 15–21 Selbstbedienung (VERIFIED_CODE) | Betreiber | — |
| PA-02 | Sicherheit, Nachweis von Zugriffsänderungen | alle Konten | AUD | Plattform-Admin | lit. c (Art. 32) / lit. f — VERIFIED_SPEC NFR-011 R-38 | Nachweis von Rollenänderungen | R-38 730 d; neue Aktionen R-44 | Auskunft (im Bundle), keine Löschung vor Fristende (Tombstone) | Betreiber | — |
| PA-03 | Mitgliederverwaltung | Mitglieder, Eingeladene | IDN (E-Mail), Rolle | Mitglieder des Mandanten (Verzeichnis), Admin | lit. b (Mitgliedschafts-/Arbeitsverhältnis, Satzung) — INFERRED; E-Mail-Sichtbarkeit für alle: Erforderlichkeit zweifelhaft (LEG-14) | Rollen nötig; E-Mail nur für `management` nötig (PRIV-305) | mit Mitgliedschaft; Einladungen R-12 | Austritt jederzeit; Audit bleibt 730 d | Mandant | Betreiber |
| PA-04 | Koordination gemeinsamer Arbeit, Beethistorie | Mitglieder, in Labels genannte Dritte | ATTR, TXT, MED, Zeit/Ort | Mitglieder (nach `attribution_visibility`), Leads/Management (Filter/Export) | Inhalt: lit. b (Dienst/Mitgliedschaft) — INFERRED; Zurechnung für Dritte sichtbar: lit. f mit LIA-1 (§4.1) — PROPOSED, LEG-02; Backfill-Kopie: Art. 6 Abs. 4 LIA-2 — LEG-07 | Inhalt ja; Zurechnung für Koordination ja, für Historie nein (§4.1) | R-25 5 J. (Zurechnung → Marker spätestens dann; Unterdrückung ehemaliger Mitglieder PRIV-112) | Widerspruch Art. 21 → PRIV-116 (P2); Berichtigung eigener Zeilen (VERIFIED_CODE); Löschung → Marker + Prüfung | Mandant | Betreiber |
| PA-04a (neu, Audit 2026-11-22) | Aufgabenverwaltung: Leistungsdaten je Person (`actual_duration_minutes`, `quality_rating`, `difficulty_rating`, `started_at`, roher `assigned_to_user_key`) | Mitglieder, Beschäftigte | ATTR, Zeit | alle Mitglieder | **keine dokumentierte Grundlage** — für Koordination nicht erforderlich (Art. 5 Abs. 1 lit. b/c); LEG-28 | nein über Zuständigkeit/Erledigung hinaus | keine Frist (Vorschlag 90 d, Q-DSB-21) | Auskunft/Löschung nicht geregelt | Mandant | Betreiber |
| PA-05 | Gesetzliche Aufzeichnung | Anwendende, Erntende | ATTR, Fach | Behörde auf Verlangen | **lit. c nur für die in §3.2 zugeordneten Felder und nur bei `pflschg_professional`/`kcang_association`** (L-01, L-05 VERIFIED_LEGAL); sonst lit. b/f | je Feld (§3.2) | R-16/R-17/R-18 mit Fristbeginn nach PRIV-412 | Löschung: Ausnahme Art. 17 Abs. 3 lit. b nur für Pflichtfelder (LEGAL_REVIEW_REQUIRED LEG-04) | Mandant | Betreiber |
| PA-06 | Pflanzenakte, Freitext, Fotos | Mitglieder, Dritte, abgebildete Personen | TXT, MED | Mitglieder | lit. b — INFERRED; Fotos Dritter: lit. f + Art. 14 (RISK-17) | Freitext ist Zweck des Tagebuchs | Lebensdauer der Pflanze/des Mandanten; Vorschlag R-47 für geschlossene Aufgaben/Kommentare | Löschung → Marker + Prüfwarteschlange (DA-05) | Mandant | Betreiber |
| PA-07a | Betroffenenrechte Konto | Kontoinhaber | CONS, AUD | — | lit. c (Art. 12–22) | — | R-04, R-05, R-06, R-13 | — | Betreiber | — |
| PA-07b | Betroffenenrechte Mandantendaten | gelöschte Mitglieder, Leads | AUD (`privacy_review_items`) | Leads/Management | lit. c (Art. 17, Art. 5 Abs. 2) | Nachweis der Erledigung | R-43 3 J. | — | Mandant | Betreiber (Werkzeug) |
| PA-08 | Offline-Funktion auf dem Gerät | Gerätenutzer | DEV | — (lokal) | TDDDG § 25 Abs. 2 Nr. 2 (L-11) **nur mit ausdrücklichem Einschalten** (DEC-29) — LEG-09; DSGVO lit. b | nur mit Schalter | R-41/R-42 (Fristen `07` §6) — LEG-10 | Löschung lokal; Widerruf → Quarantäne/Löschung (`07` §7) | Betreiber (Gestaltung) / Nutzer | — |
| PA-09 | Backup/Wiederherstellung | alle | alle Kopien | Backup-Speicher (S3) | lit. f (Datensicherheit, Art. 32) — INFERRED | ja | ≤ 35 d Dumps (DEC-26) | Löschung wird nach Restore erneut angewendet (`09` §6; Detail [`17`](17-privacy-recovery.md) §5, §6) — LEG-11; Journal-Frist R-63, Evidence-Reports R-64 | Betreiber | S3-Anbieter als Unter-AV |
| PA-10 | Sensorik | Haushaltsmitglieder, Beschäftigte | SENS, LOC | Mitglieder | lit. b (VERIFIED_SPEC NFR-011 R-14) | — | R-14/R-15 (nicht klassifizierungsabhängig umgesetzt) | — | Mandant | Betreiber |
| PA-11 | Mandantenexport/-import | Mitglieder | alle Mandantendaten inkl. GPS | Mandant (Download) | lit. b (Portabilität des Mandanten) — INFERRED, LEG-13 | — | R-05 72 h | — | Mandant | Betreiber |
| PA-12 | Support/Administration | alle | IDN, AUD | Plattform-Admin | lit. f — INFERRED | Mitgliederlisten für INV-1, Löschvorschau | — | — | Betreiber | — |
| PA-13 (neu) | KI-Assistent (Tipps, Tagestipp, „Warum?“, Chat, Wissensfrage) | Kontoinhaber, Mitglieder (Freitext) | Stammwerte, `cultivar_hint`, Chat-Freitext; keine Konto-IDs | LLM-Anbieter über den Knowledge-Service (§2.3) | lit. a (`ai_cloud_processing`, REQ-031 §7.1) für Cloud-Modelle; lokal (Ollama) lit. b — PROPOSED; Gate-Defekt §2.2 (LEG-31) | optional | `ai_conversations` 90 d, `ai_audit_log` 30 d (R-59) | Widerruf der Einwilligung | Betreiber (Plattformmodell) / Mandant (eigener Provider) | LLM-Anbieter (Unter-AV, Cloud) |
| PA-14 (neu) | Pflanzenerkennung, Schädlings-/Krankheitsdiagnose | Kontoinhaber; abgebildete Dritte | Foto (EXIF entfernt), IP der Instanz; Nutzerfoto wird nicht persistiert, nur `image_hash` (`domain/models/identification.py:3–5, 37, 44`) | Pl@ntNet, Kindwise; Cloud-LLM bei Diagnose | lit. a (`plant_identification`, `pest_detection_cloud`; Diagnose per Cloud-LLM `ai_cloud_processing`, §2.2) — VERIFIED_CODE Consent-Guard; geprüft wird die Einwilligung der handelnden, nicht der hochladenden Person (LEG-40) | optional | Anbieterfrist (Register §2.3) | Widerruf | Betreiber | Rolle offen (Q-LAW-07) |
| PA-15 (neu) | Benachrichtigung, E-Mail, Web-Push, Apprise | Kontoinhaber, Eingeladene | E-Mail, Name, Mailinhalt; Push-Endpunkt; Apprise-Text im Klartext | Resend/SMTP, Push-Dienste, vom Nutzer/Mandanten gewählte Apprise-Ziele | lit. b — INFERRED | ja (Konto, Einladung, Export-Hinweis) | Benachrichtigungen R-48 (PROPOSED, nicht durchgesetzt) | — | Betreiber / Mandant (Apprise) | Resend/SMTP-Relay (Unter-AV) |
| PA-16 (neu) | Wetter- und Klimadaten für Standorte | Kontoinhaber (Wohnadresse bei privaten Gärten) | exakte Koordinaten (§2.4) | OpenWeatherMap, Open-Meteo, Bright Sky, NASA POWER (USA) | lit. b bzw. lit. f — INFERRED; LIA fehlt (Q-DSB-18); DP-002 nicht umgesetzt (LEG-49) | Raster ~1–10 km genügt | beim Dienst (Empfänger) | — | Betreiber | — (Empfänger, eigener Verantwortlicher) |
| PA-17 (neu) | MCP/Agenten und Service-Accounts (Weitergabe an KI-Clients, Home Assistant, Drittsysteme) | Mitglieder, Dritte in Freitext/Fotos | Tagebuch, Pflegeprotokoll, Aufgaben, Fotos (heute unmarkiert, LEG-51) | Agent/LLM des Schlüsselinhabers, HA-Recorder | lit. b/f für Offenlegung an Berechtigte; Weitergabe verantwortet das Mitglied (Q-LAW-10) | nur eigene/markierte Inhalte (PRA-2.10) | `mcp_audit_log` 90 d (R-60); beim Drittsystem ohne Frist (LEG-48) | — | Mandant / Mitglied | — |

**Ist-Stand-Korrekturen (Audit 2026-11-22):** PA-04 — die Backfill-Kopie ist **fortlaufend** (§4.2, LEG-07); PA-05 —
die lit.-c-Aufbewahrung gilt im Code für **alle** Mandanten (§3.3, LEG-30); PA-08 — Speicherung ohne Schalter, SW-Cache
unprojiziert (`07` §1, LEG-09/LEG-27); PA-09 — Backup per Default aus, Spiegel und Replay fehlen (`09` §6, LEG-11);
PA-10 — `control_events.triggered_by_user` ohne Frist, Löschung, Auskunft (LEG-29, Sachverhalt `02`); PA-11 —
`sites.gps_coordinates` ungerundet im Archiv, Plattform-Admin-Export (§2.5, LEG-13/LEG-53). PA-13…PA-17 nach PRA-1.03.

### 2.1 Bewertung der Rechtsgrundlagen und Zweckbindung (Audit 2026-11-22, Strang E)

| PA | Bewertung | Einwilligung als Universallösung? | LIA dokumentiert? | Zweckbindungsrisiko |
|---|---|---|---|---|
| PA-01 | tragfähig | nein | — (IP: REQ-023) | gering |
| PA-02 | tragfähig für Audit; Log-Frist fehlt (R-51) | Fehlertracking-Zuordnung per Einwilligung — zusätzlich, nicht ersetzend (vertretbar) | LIA-4 nur Verweis (LEG-16, §4.4) | gering–mittel (stabile Pseudonyme in Logs) |
| PA-03 | tragfähig; E-Mail an alle nicht erforderlich (LEG-14) | nein | — | gering |
| PA-04 | lit. b nur mit Leistungsbeschreibung in Nutzungsbedingungen/Satzung/Arbeitsvertrag (heute nicht belegt); Zurechnung 5 J. nicht von LIA-1 gedeckt (LEG-02); Backfill fortlaufend (LEG-07); Beschäftigte → Art. 88/§ 26 BDSG (LEG-05) | nein (Option C zu Recht verworfen) | Vorlage, nicht je Mandant | **hoch** in Betrieben |
| PA-04a | keine dokumentierte Grundlage; Datenminimierung verletzt; widerspricht PRIV-407 im Bestand (LEG-28) | — | nein | **hoch** |
| PA-05 | Konzept (feldgenau, nur bei Pflicht) richtig; Code wendet lit.-c-Aufbewahrung auf alle an; Fristbeginn falsch (PRIV-412) | nein | — | mittel (Kopie LEG-07; Aufbewahrung ohne Zugriff LEG-47) |
| PA-06 | tragfähig, Prüfweg fehlt (LEG-08, LEG-20) | nein | nein | mittel |
| PA-07a/b | tragfähig | nein | — | gering |
| PA-08 | TDDDG § 25 + lit. b (`07` §2) | Schalter (DEC-29), kein Einwilligungsdialog — korrekt | — | mittel |
| PA-09 | lit. f | nein | nein | — |
| PA-10 | Aktorik-Personenbezug ohne Frist/Löschung (LEG-29); Sensor-DSFA offen | nein | nein | mittel–hoch (Anwesenheit) |
| PA-11 | LEG-13 | nein | — | mittel |
| PA-12 | tragfähig, LIA fehlt | nein | nein | gering |
| PA-13/PA-14 | Einwilligung sachgerecht (optional, zweckgebunden, Consent-Guard) — aber Gate am falschen Provider (§2.2) | **nein** — nur für optionale Funktionen (positiv) | — | gering (bei funktionierendem Gate) |

**Gesamturteil (Audit 2026-11-22):** Kein Missbrauch der Einwilligung als Universallösung (nur optionale KI-, Diagnose-
und Fehlertracking-Zwecke, `domain/guards/consent_guard.py:47–51`). Gesetzliche und betriebliche Aufbewahrung sind in
der Spec sauber getrennt (§3.2, PRIV-410), im Code nicht (Klassifizierung ohne Leser, LEG-30). Neue Zwecke entstehen
durch den fortlaufenden Kopierjob (LEG-07) und die Aufgaben-Leistungsfelder (LEG-28, ohne Grundlage). Offene
Rechtsfragen: Q-DSB-01 (LEG-02), Q-DSB-05 (LEG-07), Q-DSB-18 (LEG-16/LEG-49), Q-DSB-21 (LEG-28/29) in `16`.

### 2.2 KI-Cloud-Gate am falschen Provider (LEG-31) — Sachverhalt

[VERIFIED_CODE, Hauptsession-Verifikation Audit 2026-11-22] Für **Tipps, Tagestipp, „Warum?“, Chat-Stream und
Diagnose** leitet das Backend `uses_cloud` aus dem Provider-Datensatz **des Mandanten** ab; davon hängen die
Mandantensperre `ai_allow_cloud_providers` (REQ-031 SEC-001) und die Pflicht-Einwilligung `ai_cloud_processing`
(REQ-031 §7.1) ab. Der LLM-Aufruf läuft aber über den Knowledge-Service ohne Provider-Angabe, und der KS nutzt sein per
Umgebung gesetztes Modell (`LLM_PROVIDER`, Default `ollama`, wahlweise `anthropic`/`openai_compatible`).

| Pfad | Beleg | Status |
|---|---|---|
| `refresh_tips` | `domain/services/ai_assistant_service.py:245`; KS-Aufruf ohne Provider `_run_ask(question, …)` `:250` | `CONFIRMED` |
| `refresh_daily_tip` | `ai_assistant_service.py:350` | `CONFIRMED` |
| `explain` („Warum?“) | `ai_assistant_service.py:463` | `CONFIRMED` |
| `stream_chat` | `ai_assistant_service.py:768` | `CONFIRMED` |
| Provider-Ermittlung | `_resolve_provider` `ai_assistant_service.py:125–165` (Mandanten-Datensatz; ohne Datensatz `("", "ollama", False)` → **keine** Einwilligungsprüfung) | `CONFIRMED` |
| Diagnose | `domain/services/diagnose_service.py:293–312` `_resolve_cloud`, Aufruf `:118` (gleiches Muster; ohne Datensatz `("ollama", False)`) | `CONFIRMED` |
| `/ask` (`ask_knowledge`) | ab `ai_assistant_service.py:524`, `_platform_provider()` `:572`, prüft `ai_cloud_processing` korrekt (Bereich `:524–577`) | `NOT_REPRODUCIBLE` (korrekt); Rest: `_platform_provider` ist ebenfalls nur ein Datensatz, nicht mit dem KS abgeglichen |

Folgen: (1) KS auf Anthropic/OpenAI, Mandant ohne Datensatz → keine Einwilligungsprüfung, Sperre greift nicht, Daten
gehen an einen US-Anbieter; (2) bei `ai_allow_cloud_providers = false` ersetzt das Backend nur den Datensatz, der KS
antwortet trotzdem mit dem Cloud-Modell; (3) UI-Indikator „Cloud-Verarbeitung“ und `ai_audit_log.uses_cloud_provider`
können „lokal“ melden. Der KS-Payload enthält nur `question/top_k/doc_language/prompt_language/context`
(`data_access/external/knowledge_service_adapter.py:188–213`).
Rechtliche Einordnung (Audit 2026-11-22): Art. 6 Abs. 1 lit. a/Art. 7 (erklärte Einwilligung nicht eingeholt),
Art. 44 ff. (Übermittlung ohne dokumentierte Grundlage; Eignung als Art. 49 Abs. 1 lit. a offen, Q-DSB-19), Art. 5
Abs. 1 lit. a/Art. 13 Abs. 1 lit. f (Indikator). Risiko niedrig bei `LLM_PROVIDER=ollama`, mittel bis hoch sonst;
**P1, bedingt P0** bei Produktionsinstanz mit Cloud-LLM (nicht prüfbar, PRA-0.01). Abhilfe: PRA-0.09 (KS meldet
`provider_type`/`uses_cloud`, fail-closed „Cloud“, zentrale Prüfung vor jedem `self._ks.ask`).

### 2.3 Empfänger und Unterauftragsverarbeiter mit Drittlandbezug (LEG-33)

[VERIFIED_CODE für Code-Pfad, Aktivierung und Datenkategorie; Rolle PROPOSED; Sitz/Region **nicht verifiziert**, Prüfung
in PRA-1.03] Heute fehlen KI/LLM, Erkennung, E-Mail, Push/Apprise, NASA POWER und Bright Sky in REQ-025 §9 und in §2;
eine Drittlandprüfung (Art. 44 ff.) gibt es für keinen Dienst. Das maschinenlesbare Register mit Guard über
`data_access/external/` und `src/knowledge-service/app/llm/` ist PRA-1.03; diese Tabelle ist sein fachlicher Inhalt.

| Dienst | Code | Aktivierung | Personenbezogene Daten | Konfigurationsebene (REQ-049 P5) | Rolle (PROPOSED) | Drittland (zu prüfen) | Consent-Gate |
|---|---|---|---|---|---|---|---|
| Resend | `data_access/external/resend_email_adapter.py:27` | `EMAIL_ADAPTER=resend` | E-Mail, Name, Mailinhalt (Verifizierung, Einladung, Export-Hinweis) | Betreiber | Unter-AV bzw. AV des Betreibers | USA (Region prüfen) | nein (funktional) |
| SMTP-Relay | `smtp_email_adapter.py` | `EMAIL_ADAPTER=smtp` | wie Resend | Betreiber | AV, falls fremd gehostet | abhängig | nein |
| LLM über Knowledge-Service (Anthropic / OpenAI-kompatibel / Ollama) | `src/knowledge-service/app/llm/*` | `LLM_PROVIDER` | Prompt: Stammwerte, `cultivar_hint`, Freitext (Chat, Wissensfrage) | Betreiber (faktisch; Mandanten-Provider wirkungslos, §2.2) | Unter-AV (Cloud) / keiner (Ollama lokal) | USA bei Anthropic/OpenAI | ja, aber am falschen Provider (LEG-31) |
| Pl@ntNet | `plantnet_adapter.py` | `PLANTNET_API_KEY` | Pflanzenfoto (EXIF entfernt, `identification_service.py:99–118`), IP der Instanz | Betreiber | eigener Verantwortlicher oder AV (Q-LAW-07) | FR (EU) | ja (`plant_identification`) |
| Kindwise (plant.id / crop.health) | `kindwise_pest_adapter.py` | Adapter-Konfiguration | Foto | Betreiber | wie Pl@ntNet | CZ (EU) | ja (`pest_detection_cloud`) |
| OpenWeatherMap | `openweathermap_weather_adapter.py` | `openweathermap_enabled`, API-Key | **exakte** Koordinaten | Betreiber oder Mandant | Empfänger (eigener Verantwortlicher) | UK u. a. (prüfen) | nein (lit. b) |
| Open-Meteo | `open_meteo_weather_adapter.py` | Default | exakte Koordinaten | Betreiber | Empfänger | CH/EU | nein |
| Bright Sky (DWD-Daten) | `dwd_weather_adapter.py` | Default | exakte Koordinaten | Betreiber | Empfänger | DE | nein |
| NASA POWER | `nasa_power_weather_adapter.py` | `nasa_power_climate_enabled` | exakte Koordinaten | Betreiber | Empfänger | **USA** | nein |
| Web-Push-Dienste (FCM, Mozilla, Apple) | `pwa_notification_channel.py` | VAPID-Keys | Push-Endpunkt, Metadaten; Payload Ende-zu-Ende verschlüsselt (`:214–218`) | Nutzer (Abo) | eigener Verantwortlicher des Browseranbieters | USA | nein (Opt-in je Gerät) |
| Apprise-Ziele (Telegram, Slack, Discord …) | `apprise_notification_channel.py` | vom Nutzer oder Mandanten konfiguriert | Titel und Text der Benachrichtigung im Klartext | Mandant/Nutzer | vom Mandanten/Nutzer gewählter Empfänger | je Dienst | nein; SSRF-Filter (`url_safety`) |
| Sentry / GlitchTip | `observability/error_tracking.py` | `SENTRY_DSN` (Helm-Default `""`, `values.yaml:832`) | bereinigte Ereignisse, Pseudonym bei Einwilligung | Betreiber | Unter-AV bzw. AV | je Hosting | Zuordnung ja (`error_tracking`) |
| S3-Backup | `helm/kamerplanter/values.yaml:593` | `backup.enabled` | Vollkopie | Betreiber | Unter-AV | je Anbieter | — |
| OAuth-Provider (Google, GitHub, Apple, OIDC) | Authlib | Konfiguration | Identität beim Login | Betreiber | eigener Verantwortlicher | USA (Google, GitHub, Apple) | nein (funktional) |
| Home Assistant | REQ-005/REQ-018 | Betreiber-Token | Sensorwerte | Betreiber | Teil der eigenen Infrastruktur | — | — |
| GBIF, Perenual, iNaturalist, iDigBio, Wikimedia | `gbif_adapter.py`, `perenual_adapter.py`, `*_media_client.py` | Admin-Jobs | keine (Artnamen, Katalogbilder) | Betreiber | nicht einschlägig | — | — |
| GHCR, Renovate, Cloudflare | CI und Bild-Pipeline | — | keine Endnutzerdaten zur Laufzeit | — | nicht einschlägig | — | — |
| Kamerplanter-Projekt (Hersteller) | — | — | **keine** (keine Telemetrie, kein Update-Check) | — | keine Verarbeitungsrolle | — | — |

Normen: Art. 13 Abs. 1 lit. e/f, Art. 28 Abs. 2/4, Art. 30 Abs. 1 lit. d/e, Art. 44–46, 49 (L-12 als Bezug; Kapitel-V-
Instrumente L-25, V-12). Offene Fragen: Rollen externer Dienste (Q-LAW-07), Art. 49 für KI-Cloud (Q-DSB-19).

### 2.4 Wetterkoordinaten: DP-002 nicht umgesetzt (LEG-49)

[VERIFIED_CODE] REQ-025 §9 DP-002 (MUSS) sagt zu, Koordinaten würden vor der Übermittlung an Wetter-APIs auf zwei
Nachkommastellen (~1 km) gerundet. Kein Adapter und kein Aufrufer rundet: `open_meteo_weather_adapter.py:58–72`,
`openweathermap_weather_adapter.py:110–122`, `dwd_weather_adapter.py:150–165` (`api.brightsky.dev`),
`nasa_power_weather_adapter.py:99–106, 156–161`; Aufrufer `domain/services/weather_source_resolver.py:171–199`,
`weather_source_service.py:376–380`, `climate_normal_fetcher.py`; `domain/models/site.py:845–854` prüft nur den
Wertebereich; `grep "round("` in den Wetteradaptern findet nur Messwerte; kein Test zu DP-002. Folge: OpenWeatherMap,
Open-Meteo, Bright Sky und NASA POWER (USA) erhalten bei privaten Gärten die Wohnadresse; dasselbe gilt für
`sites.gps_coordinates` im Mandantenarchiv (§2.5). Bewertung: Art. 5 Abs. 1 lit. c, Art. 25 Abs. 1 (eigene
MUSS-Zusage nicht eingehalten); Art. 44 ff. für NASA POWER; personenbeziehbar über Installation und IP (INFERRED).
**P2**, Abhilfe PRA-2.14 (`coarsen_coordinates(lat, lon, decimals=2)` vor jedem `fetch_*`, schutzverstärkend, ohne
Rechtsfreigabe). LIA für die Übermittlung an Wetterdienste fehlt (Q-DSB-18).

### 2.5 Mandantenarchiv und Plattform-Export (LEG-13; Teilfrage LEG-53)

[VERIFIED_CODE] Export durch Leitung mit `management` **oder Plattform-Admin** (`domain/services/tenant_export_service.py:282–283`,
Route `POST /admin/platform/tenants/{key}/exports`); Step-up `tenant_export` (`:336`); Audit `TENANT_EXPORT_REQUESTED` mit
`via` (`:370–376`); E-Mail-Hinweis an alle Mitglieder mit `management` (`:380, 388–414`), bei `orphaned`-Mandanten an
niemanden (`:393–397`). Download nur durch die anfordernde Person; Ablauf nach R-05 (72 h). `members.jsonl` mit Schlüssel,
Anzeigename, Rolle, Scopes, `joined_at`, ohne E-Mail (`tenant_export_engine.py:192–198`); Geheimnisse, KI-Konversationen,
API-Keys und Einladungen ausgeschlossen (`:194–215`); `sites.gps_coordinates` **ungerundet**. Status technisch
`PARTIALLY_CONFIRMED`, rechtlich `LEGAL_REVIEW_REQUIRED` (Art. 28 Abs. 3 lit. a/g; Art. 44 erst bei Weitergabe durch den
Mandanten; Art. 20 bei Übergabe an fremde Installation, Q-LAW-09). Der Plattform-Admin-Export widerspricht REQ-049 P4
(W-30, LEG-53; Sachverhalt `05`) und braucht in BM-001 eine Weisungsgrundlage (Q-LAW-08). Schutzverstärkend sofort:
Pflichtfeld `reason`/`instruction_ref` im Audit, Hinweis an alle aktiven Mitglieder (PRA-2.11). RISK-15 in `11` ist
korrigiert (keine Rundung im Archiv). **P2.**

---

## 3. Gesetzliche Aufzeichnungspflichten — feldgenau (LEG-03, LEG-04, LEG-17; DA-03)

### 3.1 Anwendbarkeit je Mandant

**PRIV-400** Das System DARF NICHT annehmen, dass jeder Mandant an PflSchG § 11 oder KCanG § 26 gebunden
ist. [VERIFIED_CODE] Heute gelten `LEGAL_RETENTION_RULES` für jeden Mandanten. [VERIFIED_LEGAL L-02]
Beruflicher Anwender ist, wer „im Zuge ihrer beruflichen Tätigkeit“ anwendet; [L-05] § 26 trifft nur
Anbauvereinigungen; [L-07] der private Eigenanbau kennt keine Dokumentationspflicht.

**PRIV-401** [DEC-11 aktualisiert] `Tenant.settings.record_keeping` bestimmt die Klasse **je Feld** (§3.2):
`pflschg_professional` / `kcang_association` / `both` → Pflichtfelder unter lit. c; `none` → keine
Statutory-Klasse; `legacy` (nur Bestand, v0110) → heutiges Verhalten; `undeclared` → PRIV-409. Der Wechsel
auf `none` löst den Reklassifizierungs-Job aus (`09` §4), der hinter dem Flag `PRIVACY_RECORD_KEEPING_RECLASSIFY`
steht (Gate §10).

**PRIV-402** Wechselt `record_keeping` von gesetzlich auf `none`, MÜSSEN pseudonymisierte Zeilen neu
klassifiziert werden (Tombstone → Marker, `notes` → Prüfung), auditiert (`TENANT_RECORD_KEEPING_CHANGED`);
die Rückrichtung gilt nur für neue Zeilen. Solange das Flag aus ist, wird der Wechsel gespeichert, der Job
aber nicht ausgeführt (Zustand `reclassification_pending`, Metrik).

### 3.2 Feldgenaue Zuordnung: Vorschrift → Pflichtangabe → Anwendungsfeld → Aufbewahrungsregel

**PRIV-410** Art. 6 Abs. 1 lit. c und die Ausnahme Art. 17 Abs. 3 lit. b DÜRFEN NUR für Felder geltend gemacht
werden, die in dieser Tabelle einer Vorschrift zugeordnet sind. Alle anderen Felder derselben Zeile folgen
den Regeln für `shared_history` (Marker, Prüfung) bzw. den gewöhnlichen Fristen.

| Vorschrift (Evidenz) | Pflichtangabe | Anwendungsfeld (VERIFIED_CODE) | Adressat | Frist / Beginn | Regel |
|---|---|---|---|---|---|
| KCanG § 26 Abs. 1 Nr. 3, Abs. 2 (L-05) | Mengen des angebauten Cannabis in Gramm | `harvest_batches.{Mengenfeld(er), harvest_date, cultivar/strain}`; `yield_metrics` (ohne Nutzerfeld) | Anbauvereinigung | 5 Jahre; Beginn in § 26 nicht geregelt → INFERRED: Entstehung der Aufzeichnung; LEG-17 | R-16 (Pflichtfelder) |
| KCanG § 26 Abs. 1 Nr. 5 lit. b (L-05) | durchschnittlicher THC-Gehalt des **weitergegebenen** Cannabis | **kein Feld [v]** (V-11 erledigt 2026-11-15: kein THC-/Cannabinoid-Feld in `quality_assessments`/`harvest_batches`, keine Weitergabe-Entität) — fällt aus der Pflichtmenge (DA-03) | Anbauvereinigung | 5 Jahre | R-16 nur, falls das Feld den THC-Wert der weitergegebenen Charge belegt |
| KCanG § 26 Abs. 1 Nr. 5–7 (L-05) | Name/Vorname/Geburtsjahr der **Empfänger**, Transportbegleitende | **keine Entität in Kamerplanter** | Anbauvereinigung | 5 Jahre | außerhalb der Anwendung (Hinweis in Doku: Kamerplanter ist kein Weitergabe-Register) |
| KCanG § 26 (L-05) | — | `harvest_batches.harvested_by_key`, `harvester`, `quality_assessments.assessed_by_key/assessed_by` | — | **keine Pflichtangabe** | **PRIV-411**: bei Löschung Marker (nicht Tombstone) in Mandanten mit `kcang_association`; `harvester` geleert; `notes` → Prüfung |
| KCanG § 16 Abs. 3 (L-06) | Selbstauskunft der Mitglieder | keine Entität | Anbauvereinigung | 3 Jahre | außerhalb |
| KCanG § 9, § 10 (L-07) | — | — | privater Eigenanbau | **keine Pflicht** | persönliche Mandanten: `none` |
| PflSchG § 11 Abs. 2 S. 2 (L-01) | Zusammenführung der Aufzeichnungen „unter Angabe des jeweiligen Anwenders“ | `treatment_applications.applied_by_key` (+ lesbarer Bezug: heute `applied_by`, bei Löschung geleert) | Leiter eines gärtnerischen Betriebs (beruflich) | Frist nach Art. 67 VO 1107/2009 (L-03, UNVERIFIED_AT_SOURCE; NFR-011: 3 Jahre VERIFIED_SPEC); **Beginn 1. Januar des Folgejahres** (§ 11 Abs. 3, VERIFIED_LEGAL) | R-17 (Pflichtfeld); **LEG-04**: Pseudonym vs. lesbarer Name |
| VO 1107/2009 Art. 67 Abs. 1 (L-03) / DVO 2023/564 Art. 2 (L-04) | Mittel, Zeitpunkt, Dosis, Fläche, Kultur (VERIFIED_SPEC NFR-011 R-17; Wortlaut nicht verifiziert) | `treatment_applications.{product/treatment_key, applied_at, dosage, location/area, crop/plant}` | berufliche Verwender | wie oben | R-17 (Pflichtfelder) |
| PflSchG § 11 / VO 1107/2009 (L-01/L-03) | — | `treatment_applications.notes` | — | **keine Pflichtangabe** | `notes` → Prüfung bei Löschung |
| PflSchG (Inspektionen) | **kein Fundstellennachweis** im Register für eine Pflicht, Überwachungsaufzeichnungen zu führen (NFR-011 R-18 nennt „PflSchG § 11“; § 11 selbst nennt Inspektionen nicht) | `inspections.*` | — | — | **PRIV-413**: R-18 gilt bis V-04/V-06 als `VERIFIED_SPEC` ohne rechtlichen Beleg; Klassifizierung `shared_history`, sofern LEG-03 keine Vorschrift benennt (LEGAL_REVIEW_REQUIRED) |
| `care_events` mit `category ∈ {pest_control, ipm}` | — | — | — | — | keine Pflichtaufzeichnung (VERIFIED_SPEC REQ-053 §13.2, E-16); der „PflSchG-Vorbehalt“ in R-25 ist eine Aufbewahrungsuntergrenze, keine Rechtsgrundlage (LEG-07) |

**PRIV-412** [PROPOSED, VERIFIED_LEGAL L-01 Abs. 3] Die Aufbewahrungsfrist der PflSchG-Pflichtfelder MUSS ab
dem **1. Januar des auf die Aufzeichnung folgenden Jahres** gerechnet werden, nicht ab `applied_at`.
[VERIFIED_CODE] `LEGAL_RETENTION_RULES` rechnen heute ab `applied_at`/`inspected_at`; `retention_service.
care_event_pflschg_cutoff` entsprechend. Die Korrektur **verlängert** die Aufbewahrung (bis zu 364 Tage) und
ist ohne Rechtsfreigabe umsetzbar (schutzverstärkend für die Pflicht; nicht datenvernichtend). TA-412.

**PRIV-413** `treatment_applications` gilt bis zur Erledigung von V-04/V-06 als **Hilfsdokumentation**: Die
Anwendung DARF NICHT behaupten, die Zeile sei eine vollständige Aufzeichnung nach DVO 2023/564 (Doku-Text
„unterstützt die Aufzeichnung“ statt „ist der Nachweis“); REQ-053 §13.2 („`treatment_applications` bleibt der
Nachweis“) ist entsprechend zu präzisieren (E16, W-13).

**PRIV-411** [PROPOSED, DA-03] In Mandanten mit `kcang_association` (ohne `pflschg_professional`) erhält
`harvested_by_key`/`assessed_by_key` bei Kontolöschung den **Marker**, nicht den Tombstone; die Mengen-/Datums-
felder bleiben 5 Jahre. **Gate:** Änderung gegenüber Bestand (REQ-025 §3.1.3 Regel 2) → Flag
`PRIVACY_RECORD_KEEPING_RECLASSIFY`, bis LEG-03/LEG-17 entschieden; bis dahin gilt für `kcang_association`
der Bestand (Tombstone).

### 3.3 Ist-Stand und Pflichtzeilen nach Mandantenlöschung (Audit 2026-11-22; LEG-30, LEG-47)

[VERIFIED_CODE] PRIV-400/401/409 sind nicht umgesetzt (§1, LEG-30): Kontolöschung behält die Pflichtzeilen
pseudonymisiert (`erasure_engine.py:84–122`), Mandantenlöschung behält `treatment_applications`, `inspections`,
`harvest_batches` (+ `quality_assessments`) 3–5 J. pseudonymisiert (`domain/engines/tenant_erasure_engine.py:44–57`
`_R16/_R17/_R18`, `:189–209`) — für **jeden** Mandanten, auch Eigenanbau und Hobby (RISK-06; L-02, L-07). Die
`care_events`-Kopien inkl. `pest_control` werden gelöscht (`:111–117`); das ist unbedenklich, solange
`treatment_applications` der Nachweis bleibt (LEG-07 Frage 3, Auslegung).

**LEG-47 (P2):** Nach der Mandantenlöschung hat der Pflichtige (Mandant; PflSchG § 11, KCanG § 26) **keinen Zugang**
mehr zu den zurückbehaltenen Zeilen; keine Admin-Route erlaubt die Vorlage an eine Behörde. Der Zweck der lit.-c-
Aufbewahrung (Vorlage auf Verlangen) ist nicht mehr erreichbar; die Daten liegen beim Betreiber ohne eigenen Zweck.
Art. 17 Abs. 3 lit. b greift nur, soweit die Aufbewahrung zur Pflichterfüllung **erforderlich** ist; für `none` fehlt die
Grundlage ganz (Auslegung, Audit 2026-11-22). Im AV-Modell ist offen, ob die Pflicht des Mandanten eine
Speicherpflicht des AV nach Art. 28 Abs. 3 lit. g begründet (Q-LAW-04).

**PRIV-415** [PROPOSED, PRA-2.09] Der Löschdialog für Mandanten MUSS einen Pflichtexport anbieten und dessen
Bestätigung verlangen („Aufzeichnungen nach § 11 PflSchG / § 26 KCanG wurden exportiert“; REQ-056-Archiv enthält die
Zeilen). Danach DÜRFEN Pflichtzeilen nur für `pflschg_professional`/`kcang_association` aufbewahrt werden, mit
dokumentiertem, auditiertem Herausgabeprozess; für `none` werden sie sofort gelöscht (Logik von
`PRIVACY_RECORD_KEEPING_RECLASSIFY`). **Gate:** datenvernichtend → `processing_allowed` nein bis LEG-03 (§10).

---

## 4. Interessenabwägungen (Art. 6 Abs. 1 lit. f) — dreistufig (Prüfschema nach EDSA 1/2024, L-22 INFERRED)

Jede LIA hält fest: (1) berechtigter Zweck, (2) Erforderlichkeit, (3) Abwägung einschließlich vernünftiger
Erwartungen und Schutzmaßnahmen. Alle LIAs sind **Vorlagen für den Verantwortlichen** (DA-01: der Mandant);
die Rechtsberatung prüft sie (LEG-02, LEG-06, LEG-07).

### 4.1 LIA-1 — Sichtbarkeit der Zurechnung für andere Mitglieder (aktuelle Mitglieder)

1. **Zweck**: Koordination gemeinsamer Arbeit (wer hat gegossen/behandelt), Korrektur eigener Zeilen,
   Rechenschaft innerhalb von Gemeinschaftsgarten oder Betrieb. Die agronomische Historie braucht *was/wann*,
   nicht *wer* (PRIV-004).
2. **Erforderlichkeit**: Für Koordination während der aktiven Mitgliedschaft; nicht für die Historie; für
   Rechenschaft zeitlich begrenzt. Mildere Mittel: `leads_and_self`, Unterdrückung nach Austritt, Marker nach R-25.
3. **Abwägung**: vernünftige Erwartung (Aushang im Garten) vs. Profiling-Risiko (Anwesenheitsmuster,
   Leistungsbewertung in Betrieben — DSK-Liste Nr. 8, L-17). Schutzmaßnahmen: keine Aggregation (PRIV-403),
   Filter nur Lead/Management (SR-020, VERIFIED_CODE), `attribution_visibility` (PRIV-300) mit Klassen-
   Defaults (DA-04), Namensunterdrückung ehemaliger Mitglieder (PRIV-112), Widerspruch (PRIV-116), kein Name
   in Exporten für Nicht-Leads (PRIV-307), Transparenz (PRIV-115, PRIV-408).
   **Ergebnis (PROPOSED)**: trägt für aktuelle Mitglieder unter den Maßnahmen; trägt **nicht** für die
   fünfjährige Aufbewahrung des Namens → Marker/Unterdrückung. LEG-02.

### 4.2 LIA-2 — Übernahme der Zurechnung aus gesetzlichen Zeilen ins Pflegeprotokoll (Art. 6 Abs. 4)

1. **Zweck**: vollständige Beethistorie einschließlich Ernten/Behandlungen vor Einführung des Protokolls.
2. **Erforderlichkeit**: Das Ereignis ist nötig, die Zurechnung nicht (Historie); sie wird jedoch nicht neu
   erhoben, sondern aus einem vom Mitglied selbst gesetzten `performed_by` übernommen.
3. **Vereinbarkeitsprüfung (Art. 6 Abs. 4 lit. a–e, Bezug)**: Zusammenhang (gleicher Mandant, gleiche Tätigkeit),
   Erhebungskontext (Mitglied trug „ich habe“ ein), Art der Daten (nicht sensibel), Folgen (längere Frist,
   Filter, CSV), Garantien (Allowlist, keine Pseudonyme, LIA-1-Maßnahmen). **Ergebnis (PROPOSED)**: vereinbar;
   **Alternative** ohne Zurechnung per Schalter `PRIVACY_BACKFILL_COPIES_PERFORMER` (DA-02). LEG-07.
4. **Ist-Stand (Audit 2026-11-22, VERIFIED_CODE):** Der Mapper kopiert nur die Kontoreferenz (`ACCOUNT_FIELDS`
   `domain/engines/care_event_backfill_mapper.py:71–77`, `account_of` `:183–191` Tombstone → Marker, `map_document`
   `:271–306`); Freitexte und `notes` werden nicht kopiert (`migrations/versions/v0104_care_events_backfill.py:19–21`).
   Die Kopie ist **keine einmalige Migration (M4), sondern fortlaufend**: der tägliche Konsistenzjob ruft denselben
   Mapper (`domain/services/care_event_consistency_service.py:129`, Fenster 7 d `config/settings.py:1287`). Der Schalter
   `PRIVACY_BACKFILL_COPIES_PERFORMER` existiert nicht (0 Treffer in `app/` und `helm/`). Damit ist die Zweckänderung
   eine Dauer-Zweckänderung; ein Schalter muss Migration **und** Konsistenzjob abdecken (PRA-2.08, Lesestelle
   `account_of`), sonst wirkt eine Entscheidung nur auf Altdaten.
5. **Würdigung (Audit 2026-11-22, Auslegung):** Für Vereinbarkeit sprechen der enge Zusammenhang (gleiche Tatsache,
   gleicher Mandant; Art. 6 Abs. 4 lit. a/b). Dagegen sprechen die Eignung des Ziels (Personenfilter, CSV) zur
   Leistungs- und Verhaltensbewertung (lit. d) und die längere Zielfrist (5 J. statt 3 J. ab 1.1. des Folgejahres,
   § 11 Abs. 3 PflSchG, L-01). In Beschäftigtenkontexten ist Vereinbarkeit daher fraglich; für Hobby-Mandanten ist die
   Quelle selbst lit. b, die Kopie unkritisch. Rechtsgrundlage der Kopie bleibt `LEGAL_REVIEW_REQUIRED` (LEG-07,
   Q-DSB-05); fehlende Information nach Art. 13 Abs. 3 über den Fluss „Pflichtaufzeichnung → Pflegeprotokoll“ ist in
   die Art.-13-Vorlage aufzunehmen (PRA-2.18). Für `commercial` keine Kopie (PRA-2.08). **P2.**

### 4.3 LIA-3 — Name ehemaliger Mitglieder für N Tage

1. Übergabe-Zweck; 2. kurz (Saisonübergabe); 3. abnehmende Erwartung; Maßnahmen: N ≤ 365, Default 90, kein
Filter/Export, Transparenz. LEG-06.

### 4.4 LIA-4 — Sentry

[VERIFIED_SPEC REQ-025 §9] „rechtlich zu bestätigen“; LEG-16.
**Ist-Stand (Audit 2026-11-22):** LIA-4 ist **nicht ausgeführt** — dieser Abschnitt ist nur ein Verweis
(technisch und rechtlich `LEGAL_REVIEW_REQUIRED`, **P3**). Die zugesagten Schutzmaßnahmen sind belegt [VERIFIED_CODE]:
ohne `SENTRY_DSN` kein Betrieb (`observability/error_tracking.py:647–648`, Helm-Default `""` `values.yaml:832`);
`send_default_pii=False` (`:675`); `before_send=scrub_event` (`:685`, `:523–560`) bereinigt Request-Daten, verwirft den
SDK-`user`, setzt nur das Pseudonym bei Einwilligung `error_tracking` (`:113`), redigiert `extra/tags/contexts`, Routen,
Frames und Texte; `scrub_breadcrumb`; `traces_sample_rate=0.0`; gleiches Modul in Knowledge- und Inference-Service;
Frontend `Sentry.init` nur nach Einwilligung, `beforeSend` nach Widerruf `null`
(`src/frontend/src/test/observability/errorTracking.test.ts:308–315`). Restrisiko: Freitext in Exception-Meldungen, den
die musterbasierte Redaktion nicht erkennt. Fehlend: ausformulierte LIA (Zweck, Erforderlichkeit, Abwägung,
Maßnahmen), Registereintrag mit Region (§2.3), Aufbewahrungsfrist beim Tracker (R-52). Bei Sentry SaaS gelten Art. 28 und
Art. 44 ff. — im Repo nicht belegbar; EU-Hosting oder selbst gehostetes GlitchTip vermeidet die Drittlandfrage.
Umsetzung PRA-3.05 (vierstufige LIA hier), Rechtsfrage Q-DSB-18.

---

## 5. Beschäftigte, Auftragnehmende, Ehrenamtliche, Vereins- und Haushaltsmitglieder (LEG-05; DA-04)

Rechtsrahmen je Gruppe, Default der Sichtbarkeit und organisatorische Pflichten des Mandanten: Tabelle in
DA-04 Pkt. 7 (normativ hier übernommen). Technische Einschränkungen:

- **PRIV-403** Kein Endpunkt, Export oder keine UI DARF Aktivität je Person aggregieren (Zähler, Zeitreihen,
  Ranglisten); Guard TA-309.
- **PRIV-404** `attribution_visibility = leads_and_self` MUSS verfügbar sein und ist Default für
  `organization_kind ∈ {commercial}` und für Auftragnehmende; `all_members` für `association`, `community`,
  `personal` (DA-04).
- **PRIV-405** Personenfilter und Namensexport werden auditiert (`ATTRIBUTION_FILTER_USED`,
  `ATTRIBUTION_EXPORTED`); `management` sieht Zähler je Akteur (90 d).
- **PRIV-406** Doku-Abschnitt „Für Betriebe und Vereine“ mit Mustertext für Betriebsrat/Information (E16).
- **PRIV-407** Keine Dauer-/Geschwindigkeitsmessung über `performed_at` hinaus. **Ist-Stand (Audit 2026-11-22):**
  im Bestand verletzt — Aufgaben speichern und zeigen Start, Ist-Dauer und Bewertungen je Person (`task.py:181–205`,
  `task_service.py:1469–1475, 1720–1730`; LEG-28, Sachverhalt `02`, Abhilfe PRA-2.06).
- **PRIV-414** [PROPOSED] Der Hinweistext zu `attribution_visibility` (PRIV-301) MUSS die Evidenz nennen:
  „§ 26 BDSG gilt nur für Beschäftigte i. S. v. § 26 Abs. 8; für Vereinsmitglieder gilt er nicht“ (L-09).

---

## 6. Zweckbindung (Art. 5 Abs. 1 lit. b) — Prüfung der Flüsse

| Fluss | Ursprünglicher Zweck | Zweitnutzung | Bewertung |
|-------|----------------------|--------------|-----------|
| `treatment_applications.applied_by_key` → `care_events.performed_by_user_key` | Pflichtaufzeichnung (PA-05) | Beethistorie, Filter, CSV (PA-04) | LIA-2 (LEG-07); Pseudonyme nie (PRIV-205); Schalter DA-02 — **fortlaufend** per Konsistenzjob, Schalter fehlt (§4.2 Pkt. 4) |
| `care_events.performed_by_user_key` (Erledigung) → `harvest_batches.harvested_by_key` | Protokoll | Ernteaufzeichnung | gleiche Tatsache; `harvested_by_key` ist **keine** KCanG-Pflichtangabe (§3.2) → kein lit.-c-Zweck entsteht |
| `bed_templates.name` → `locations.name` → `garden_plan_audit.summary` → Exporte | Plan | Export/Druck | Inhalt; Datenlinie (PRIV-230) |
| `users.display_name` → Darstellungen | Identifikation | Aktivitätsanzeige | LIA-1 |
| `security_audit_log` | Art. 32 | — | keine Zweitnutzung (REQ-049) |
| Gerätecache | Offline-Lesen | — | IndexedDB minimiert (VERIFIED_CODE `storedProjection`, `planCache.ts:345–367`); **SW-API-Cache `kp:{user}:{tenant}` unprojiziert** mit Mitgliedername und Beet-Notizen (Audit 2026-11-22, LEG-27, `07` §1) |
| Aufgaben (Zuständige, Start, Dauer, Bewertung) | Koordination | faktisch Leistungsbewertung je Person | keine Grundlage (PA-04a, LEG-28); PRA-2.06 |
| Gartenkoordinaten → Wetterdienste | Wetter/Klima am Standort | — | Übermittlung ungerundet (§2.4, LEG-49); PRA-2.14 |
| Prompts (Stammwerte, `cultivar_hint`, Chat-Freitext) → Knowledge-Service → LLM | KI-Funktion | — | Einwilligung am falschen Provider geprüft (§2.2, LEG-31) |
| Tagebuch/Pflegeprotokoll/Fotos → MCP-Agent, Service-Account → Drittsystem | Offenlegung an Berechtigte | Weiterverarbeitung in fremden Historien (HA-Recorder, Chat-Verläufe) ohne Frist | PA-17; LEG-48, LEG-51; PRA-2.10, PRA-3.04 |

---

## 7. Informationspflichten (Art. 13/14)

**PRIV-408** Die Datenschutzinformation des Betreibers (Plattform) und die **Vorlage** für die Information des
Mandanten (Art. 13 gegenüber Mitgliedern, Art. 14 gegenüber in Labels genannten Dritten und abgebildeten Personen)
MÜSSEN enthalten: Pflegeprotokoll und Zurechnung, Sichtbarkeitsregel des Mandanten, Unterdrückung ehemaliger
Mitglieder, Prüfwarteschlange, Gerätespeicher (REQ-025 §10), Backups (≤ 35 d, Replay), Rechtsgrundlagen je PA
(§2). Wortlaute: LEG-12 (E16).

### 7.1 Ist-Stand der öffentlichen Datenschutzauskunft (Audit 2026-11-22, LEG-50)

[VERIFIED_CODE] `GET /privacy/policy` (ohne Authentifizierung; `PrivacyPolicyInfo` `domain/models/privacy.py:850–857`,
`domain/services/privacy_service.py:165–166, 2155–2201`) liefert Zwecke, Fristen (`retention_summary`), Verantwortlichen
und Rechte (nur Art. 15, 16, 17, 18, 20, 21). Es fehlen die Pflichtangaben nach Art. 13 Abs. 1 lit. a–f, Abs. 2 lit. b–d:
Empfänger und Empfängerkategorien (§2.3), Drittlandübermittlung, Beschwerderecht (Art. 77), DSB-Kontakt; ob das
Widerrufsrecht (Art. 7 Abs. 3) in den Zwecken steht, ist nicht verifiziert. Der Verantwortliche ist der Platzhalter
`privacy@kamerplanter.example` (`config/settings.py:1134–1135`; `docs/de/reference/environment-variables.md:95–96`
„Pflicht: Nein“); der Start wird — anders als bei unsicheren Secrets — nicht verweigert. Policy-Version `1.0`, gültig ab
`2026-04-27`, ist fest kodiert. Fotos fehlen als Kategorie (LEG-22), die Backup-Frist fehlt (PRIV-708). Der Text selbst
hängt an LEG-12 (E16 `BLOCKED_LEGAL`); die technische Hülle kann die Pflichtfelder schon tragen. Ob der Endpunkt „die“
Datenschutzinformation oder nur Zuarbeit ist, entscheidet der Betreiber; zeigt die UI ihn als solche, gelten die
Pflichtinhalte. **P2.**

**PRIV-416** [PROPOSED, PRA-2.18] `PrivacyPolicyInfo` MUSS um `recipients[]`, `third_country_transfers[]`,
`supervisory_authority_complaint`, `dpo_contact?` und `consent_withdrawal` erweitert werden, gespeist aus dem Register
§2.3 (PRA-1.03); die Policy-Version kommt aus einer versionierten Quelle. In `full` und `production` MUSS der Start
verweigert werden, wenn der Verantwortlichenkontakt auf `.example` endet (wertfreie Meldung). Art.-13-Hinweis und
Art.-15-Metainformationen (LEG-41) kommen aus derselben Quelle.

Weitere Zusagen gegenüber Betroffenen, die das Audit widerlegt hat (Korrektur PRA-0.05): Einschränkung „wirkt“
(`docs/de/user-guide/privacy.md:153`, LEG-23), „DSFA durchgeführt“ (`:488–490`, W-10, `11` §1), Gerätecache „ohne
Namen und Notizen“ (`:426`, LEG-27, `07` §1).

---

## 8. Aufbewahrungsmatrix (vollständig; Ist-Stand am SHA `007a4ea90`)

Die Matrix führt **jeden** personenbezogenen Speicher mit Frist, Grundlage, Durchsetzung und Konfiguration (Audit
2026-11-22, Strang D Lieferung (b), 36 Zeilen vollständig übernommen; LEG-44 geschlossen auf Spec-Ebene, Umsetzung
PRA-3.06). Neue Zeilen R-49…R-62 schließen die Lücken für Nebenspeicher; sie sind zugleich der Scope von Restore-Replay
und Residue-Scan (`09` §6). Nachtrag 2026-11-23: R-63…R-65 sind die Fristen der Recovery-Bausteine aus [`17`](17-privacy-recovery.md); R-45 ist
durch R-63 ersetzt. Legende Grundlage: **RP** Rechtspflicht (gesetzliche Mindestfrist), **BE**
betrieblich/Zweck (Höchstfrist aus Art. 5 Abs. 1 lit. e), **RE** Rechenschaft (Art. 5 Abs. 2). „≥/≤“ = Untergrenze
(`ge`)/Obergrenze (`le`) in `config/settings.py` (Ceilings/Floors `:103–127, 1147–1290`). Beat-Tasks R-01…R-26:
`tasks/__init__.py:461–604`.

| # | Speicher / Daten | Frist | Grundlage (Evidenz) | Durchsetzung (Ist, Beleg) | Konfiguration (Env · Default · ≥/≤) | Status / Befund |
|---|---|---|---|---|---|---|
| R-01 | `users` soft-deleted (geschlossene Konten) | 90 d nach Antrag | BE, lit. c (Art. 17) — INFERRED | `retention.execute_scheduled_erasures` 04:00 (`privacy_service.py:2568`) | `RETENTION_SOFT_DELETE_RETENTION_DAYS` · 90 · ≥1/≤90 | VERIFIED_CODE |
| R-01b | Mandanten-Löschfrist | 90 d Gnade | BE (REQ-024 AK-52/AK-65) | `tenant_tasks.resume_tenant_erasures` 04:30 | `RETENTION_TENANT_ERASURE_GRACE_DAYS` · 90 · ≥0/≤90 | VERIFIED_CODE |
| R-02 | unbestätigte Konten | 7 d | BE | `auth_tasks.cleanup_unverified_accounts` 03:10; lokale Konten nur mit `RETENTION_UNVERIFIED_LOCAL_REAP_ENABLED` | `RETENTION_UNVERIFIED_ACCOUNT_DAYS` · 7 · ≥1/≤7; Reap · `false` | VERIFIED_CODE (lokale Konten per Default nicht entfernt) |
| R-03 | `refresh_tokens.ip_address` | 7 d → gekürzt | BE, lit. f — VERIFIED_SPEC REQ-023 | `auth_tasks.anonymize_old_ips` 03:20 (`tasks/auth_tasks.py:134–156`) | `RETENTION_IP_ANONYMIZATION_DAYS` · 7 · ≥1/≤7 | VERIFIED_CODE |
| R-04/04a | Einwilligungen / deren IP | 3 J. nach Widerruf / IP 7 d | RE, Art. 7 Abs. 1 — VERIFIED_SPEC | `retention.purge_expired_consent_records` 04:35; `retention.anonymize_consent_ips` 04:40 | `RETENTION_CONSENT_RETENTION_YEARS` · 3 · ≥1/≤3; `RETENTION_CONSENT_IP_ANONYMIZATION_DAYS` · 7 · ≥1/≤7 | VERIFIED_CODE |
| R-05 | persönlicher Export, Mandantenarchiv | 72 h | BE | `retention.expire_data_exports` stündlich :20 (`retention_tasks.py:205–224`, `tenant_export_service.py:1384`) | `RETENTION_EXPORT_FILE_RETENTION_HOURS` · 72 · ≥1/≤72 | VERIFIED_CODE; S3-Versionierung hebelt aus (R-56) |
| R-06 | `erasure_requests` | sofort pseudonymisiert, Löschung nach 3 J. | RE, Art. 5 Abs. 2 — INFERRED | `retention.purge_expired_erasure_records` 04:30 | `RETENTION_ERASURE_AUDIT_RETENTION_YEARS` · 3 · ≥1/≤3 | VERIFIED_CODE (Docstring „one year“ falsch, W-11) |
| R-06a | `tenant_erasure_records` | bis Ende R-16…R-18, max. 5 J. | RE | `retention.purge_expired_tenant_erasure_records` 04:50 | fest `TENANT_ERASURE_RECORD_CAP_YEARS=5` (`retention_service.py`) | VERIFIED_CODE |
| R-07/07a/07b | `email_change_requests` | 24 h / 7 d | BE | `retention.expire_email_change_requests` stündlich :15 | `…EMAIL_CHANGE_RETENTION_HOURS` · 24 · ≤24; `…REVERT_DAYS` · 7 · ≤7 | VERIFIED_CODE |
| R-10 | OAuth-State (Valkey) | 5 min | BE | Valkey-TTL | — | VERIFIED_CODE; Persistenz siehe R-49 |
| R-11 | `refresh_tokens` | bis Ablauf (30 d) | BE | `auth_tasks.cleanup_expired_tokens` stündlich :10 + TTL-Index | `REFRESH_TOKEN_EXPIRE_DAYS` · 30 | VERIFIED_CODE |
| R-12 | Einladungen | 30 d nach Ablauf | BE | `tenant_tasks.cleanup_expired_invitations` 02:00 | `RETENTION_INVITATION_RETENTION_DAYS` · 30 · ≤30 | VERIFIED_CODE |
| R-14 | TimescaleDB-Sensordaten | 90 d roh, 2 J. stündlich, 5 J. täglich (flach) | BE, lit. b — VERIFIED_SPEC NFR-011 | TimescaleDB-Jobs `timescale/migrations/003_retention_policies.sql:3–9` (kein Celery) | Literale in SQL; `SENSOR_*` ohne Leser; **nur mit `TIMESCALEDB_ENABLED=true`** (Default `false`, `config/settings.py:645`) — im Light-/Default-Betrieb werden keine Zeitreihen gespeichert | `PARTIALLY_CONFIRMED`: Differenzierung nach `data_classification` und ADR-003-Stufen fehlen; `sensor_daily` wird ab Tag 0 materialisiert; Endnutzerdoku `docs/de/guides/data-retention.md:123–150` zeigt Downsampling ohne TimescaleDB-Vorbehalt und behauptet „Tagesmittel 2–5 Jahre“ (LEG-44) |
| R-15 | Aktor-Logs | — | — | kein eigener Speicher | — | VERIFIED_CODE; aber `control_events` → R-62 |
| R-16 | Ernte-Pflichtfelder (§3.2) | ≥ 5 J. ab `harvest_date` | **RP** lit. c nur `kcang_association` (L-05) | `retention.purge_expired_legal_retention_rows` 04:45 | `RETENTION_HARVEST_DATA_MIN_RETENTION_YEARS` · 5 · ≥5 (kein Ceiling) | VERIFIED_CODE Collection-weit für **alle** Mandanten (§3.3, LEG-30) → PRIV-410/411; nach Mandantenlöschung ohne Zugriffsweg (LEG-47) |
| R-17 | PflSchG-Pflichtfelder | 3 J. (VERIFIED_SPEC) ab **1.1. Folgejahr** (L-01) | **RP** lit. c nur `pflschg_professional` | wie R-16 | `…TREATMENT…` · 3 · ≥3 | VERIFIED_CODE ab `applied_at` → PRIV-412 Korrektur; LEG-30, LEG-47 |
| R-18 | Inspektionen | 3 J. ab `inspected_at` | **ohne Beleg** (PRIV-413) | wie R-16 | `…INSPECTION…` · 3 · ≥3 | LEGAL_REVIEW_REQUIRED; LEG-30, LEG-47 |
| R-19…R-21, R-24, R-27…R-37, R-39 | (NFR-011) | — | — | nicht implementiert (Collections fehlen oder Funktion nicht gebaut) | — | VERIFIED_CODE (keine Daten) |
| R-25 | `care_events` | 5 J. → anonymisiert | Inhalt lit. b, Zurechnung lit. f (DA-02); „Art. 17(3)“ in NFR-011 ist zu korrigieren | `retention.anonymize_expired_care_events` 04:55 | `RETENTION_CARE_EVENT_RETENTION_YEARS` · 5 · ≥5/≤5 (fest, LEG-01) | VERIFIED_CODE; `material`, `measurements[].source/.extraction_method` nicht erfasst (LEG-08, `04`) |
| R-26 | `garden_plan_audit` inkl. Plan-Snapshots (bis 20 je Site) | 365 d | lit. f — INFERRED | `retention.purge_expired_garden_plan_audit` 05:00 | `RETENTION_GARDEN_PLAN_AUDIT_RETENTION_DAYS` · 365 · ≤365 | VERIFIED_CODE; Akteur → Marker (DEC-16); Snapshots halten Freitext und setzen ihn per Restore zurück (LEG-34, `04`) |
| R-38 | `security_audit_log` | 730 d | RE, Art. 32 — VERIFIED_SPEC | `security_audit.purge_expired` 02:55 | fest 730 (`security_audit_service.py:40`) | VERIFIED_CODE |
| R-40 | Export-/Importanträge | 30 d nach Ende | BE/RE | wie R-05 (`tenant_export_service.py:170–171, 1406–1407`) | Konstante `REQUEST_RETENTION` (keine Einstellung) | VERIFIED_CODE; NFR-011 führt R-40 fälschlich als „nicht implementiert“ (LEG-58, PRA-3.10) |
| R-41/R-42 | Browser: Lesecache / Schreibpuffer | Ist: 15 min nutzbar (physisch bis Start/Lesen/Schreiben) / **365 d** pending, **90 d** failed/conflict, hart kodiert (`features/gardenPlanner/offline/retention.ts:13,15`); Soll 90/30/14 d (PRIV-511, PROPOSED) | TDDDG § 25 Abs. 2 Nr. 2 (L-11) mit Schalter; DSGVO lit. b | im Client (`07` §6) | keine `OFFLINE_*`-Einstellung | `CONFIRMED` (Ist-Stand), LEG-09/LEG-10; SW-Cache und `notices` ohne physische Frist (LEG-36, LEG-56) |
| R-43 | `privacy_review_items` | 3 J. nach Entscheidung | Art. 5 Abs. 2 | — | — | PROPOSED (nicht gebaut) |
| R-44 | Datenschutzaktionen im Security-Audit | 730 d | Art. 5 Abs. 2 | — | — | PROPOSED |
| R-45 | ~~**Löschungs-Spiegel** (`erasure_mirror`: Tombstone-Liste, keine Rohschlüssel; DEC-26)~~ | ~~wie R-06 (3 J.)~~ | — | **nicht implementiert** (`erasure_mirror` 0 Treffer in `src`, `helm`, `docs`) | — | **ersetzt durch R-63** (Nachtrag 2026-11-23, `17` §3.8; Vorschlag DEC-36): ein Journal-Ereignis wird nur gebraucht, solange ein Backup existiert, das vor ihm entstand; der Löschnachweis über 3 J. liegt dauerhaft in `erasure_requests` (R-06) bzw. `tenant_erasure_records` (R-06a), die das Replay nach einem Restore neu erzeugt; drei Jahre Pseudonyme in einem WORM-Speicher wären nicht erforderlich (Art. 5 Abs. 1 lit. c, e); das Umschreiben gefilterter Journal-Objekte ist mit Object Lock unvereinbar |
| R-46 | Gieß-/Dünge-/Tankprotokolle | 5 J. (an R-25 angleichen) | lit. b | **kein Task** | — | PROPOSED, nicht durchgesetzt |
| R-47 | geschlossene Aufgaben/Kommentare | 2 J. | lit. b | **kein Task** | — | PROPOSED, DSB |
| R-48 | Benachrichtigungen | 90 d gelesen / 180 d ungelesen | lit. b | **kein Task** | — | PROPOSED, DSB |
| R-49 (neu) | Valkey: Rate-Limit-Schlüssel, OAuth-State (R-10), Glossar-Cache; **AOF-Persistenz** | TTL je Schlüssel; AOF-Inhalte bis Rewrite auf Disk | BE | Valkey-TTL; `glossary.cleanup_expired_cache` 02:45; AOF `values.yaml:3253–3261` | — | PROPOSED: Betreiberfrist für AOF/Snapshots dokumentieren; Valkey ohne Auth (LEG-59, `01`) |
| R-50 (neu) | Celery-Broker/Queues | bis Konsum (kein Result-Backend, `tasks/__init__.py:347–394`) | BE | — | Argumente nur Schlüssel (`user_key`, `tenant_key`), keine E-Mails (z. B. `api/v1/plant_instances/photo_router.py:215`) | VERIFIED_CODE; Persistenz über R-49 |
| R-51 (neu) | Anwendungs- und Zugriffsprotokolle | ≤ 30 d (Vorschlag; bisher nur NFR-011-Änderungsverlauf v1.13) | BE | Betreiber-Log-Pipeline (Loki `retention_period`, containerd `max-size`); Inhalt pseudonymisiert (`common/log_privacy.py`, `config/logging.py:33–80`, `src/frontend/nginx.conf:18–48`) | nicht im Repo | PROPOSED; Betreibernachweis PRA-3.09 |
| R-52 (neu) | Fehlertracker (Sentry/GlitchTip, optional) | ≤ 90 d Events (Vorschlag) | BE, lit. f (§4.4) | `before_send`-Redaktion (`observability/error_tracking.py:523–560`) | `SENTRY_DSN`; Frist beim Anbieter/Betreiber nicht dokumentiert | PROPOSED; LEG-16 |
| R-53 (neu) | ArangoDB-Backups (Helm) | Soll ≤ 35 d (DEC-26); Ist `retentionDays` 30 | lit. f (Art. 32) — INFERRED | rclone-Purge im CronJob (`values.yaml:1418–1430`); `backup.enabled: false` (`:567–612`) | `backup.retentionDays` · 30 · **keine** Unter-/Obergrenze, `0`, negative und nicht-numerische Werte = unbegrenzt; bei Upload-Fehler bricht `set -eu` vor der Retention ab; `backup.enabled: false` beendet auch die Löschung vorhandener Dumps (`values.yaml:1325`, LEG-68) | `CONFIRMED` Lücke, LEG-11, LEG-68; Interimssperre PRA-0.10; Soll zusätzlich Bucket-`Expiration` = `retentionDays + 1` unabhängig vom CronJob (`17` §7.2, PRIV-854) |
| R-54 (neu) | Backups Docker-Compose/Light | Ist unbegrenzt; Soll ≤ 35 d | lit. f | — | ohne Verschlüsselung, Passwort in der Kommandozeile | LEG-43, PRA-3.07 |
| R-55 (neu) | TimescaleDB-, local-fs- und Valkey-Snapshots | Soll ≤ 35 d (PRIV-713) | BE | Betreiber, nicht im Chart | — | PROPOSED |
| R-56 (neu) | nicht-aktuelle S3-Objektversionen (Fotos, Underlays, Exportarchive) | Soll: Lifecycle ≤ Backup-Frist | BE, Art. 17 | — | empfohlene Bucket-Versionierung ohne Lifecycle ⇒ **unbefristet** | LEG-26, PRA-0.10 |
| R-57 (neu) | verwaiste Objekte im Objektspeicher | Soll: Löschung nach Trockenlauf; Warnung > 30 d | BE | Waisen-Sweeps 03:40/03:50/04:00, Reconcile 04:10 nur Bericht (`storage_tasks.*`) | `STORAGE_RECONCILE_DELETE_ENABLED` · `false` (`config/settings.py:1386`) | LEG-60, PRA-3.06; nach einem Restore gilt R-65 |
| R-58 (neu) | Referenzindex pgvector `vectordb` (`user_contributed`, `contributed_by`, `tenant_key`) | an Konto/Mandant gebunden | BE | gelöscht in Phase 0.5 der Erasure (`domain/interfaces/reference_index_store.py:6–8, 54–75`) | nicht im Chart-Backup; Snapshot-Frist Betreiber (R-55) | VERIFIED_CODE |
| R-59 (neu) | `ai_conversations` / `ai_audit_log` | 90 d / 30 d | BE | `ai.cleanup_expired_conversations` 02:30, `ai.cleanup_expired_audit_log` 02:35 | fest `_CONVERSATION_TTL` (`ai_assistant_service.py:57`), `_AUDIT_RETENTION_DAYS` (`ai_tasks.py`) — keine Settings | VERIFIED_CODE (bisher ohne R-ID) |
| R-60 (neu) | `mcp_audit_log` / MCP-Idempotenz | 90 d / 24 h | BE/RE | `mcp.cleanup_expired_audit_log` 02:50, `mcp.cleanup_expired_idempotency` stündlich | `MCP_AUDIT_RETENTION_DAYS` · 90 (kein Ceiling); `MCP_IDEMPOTENCY_TTL_HOURS` · 24 | VERIFIED_CODE (bisher ohne R-ID) |
| R-61 (neu) | `client_event_tombstones` | 395 d | BE (Replay-Schutz) | Arango-TTL-Index (`collections.py:2386–2398`); Mandantenlöschung entfernt sie (`tenant_erasure_engine.py:236`) | fest `CLIENT_EVENT_TOMBSTONE_DAYS` (`client_event.py:46`) | VERIFIED_CODE (bisher ohne R-ID) |
| R-62 (neu) | `control_events.triggered_by_user` | Ist **keine** Frist; Vorschlag 90 d (Q-DSB-21) | BE | — (`domain/models/actuator.py:227`) | — | PROPOSED; LEG-29, PRA-2.07 |
| R-63 (neu, Nachtrag 2026-11-23) | Privacy Recovery Journal (Journal-Store außerhalb der DB: Ereignisse der Klassen E/H/C/A/D/O mit Pseudonymen `jsub_`/`jten_`/`jrec_`, Tombstone nur in `SUBJECT_ERASURE_COMPLETED`, keine Nutzdaten) | `L_eff + 14 d`, höchstens **90 d**, mit `L_eff = backup.retentionDays + noncurrentVersionDays + 2 d`; Default 30 + 7 + 2 + 14 = **53 d**; Outbox `privacy_journal_outbox` in der DB bis Bestätigung + 7 d | RE/BE: Durchsetzung von Art. 17, 7 Abs. 3, 18, 21 und Art. 32 Abs. 1 lit. b nach Restore — INFERRED; Frist und Zulässigkeit `LEGAL_REVIEW_REQUIRED` (Q-DSB-15, Q-DSB-22, Q-LAW-19) | **nicht implementiert**; Soll: Segmentablauf über Object-Lock-`retain-until` und Lifecycle-Expiration (kein Umschreiben), Purge-Beat für die Outbox (`17` §3.8, PRIV-808) | Soll `privacy.journal.retentionDays`, Render-Check `≥ L_eff + 14` und `≤ 90` (PRIV-855); ein Legal Hold verlängert das Journal **nicht** | PROPOSED; ersetzt R-45; LEG-11, LEG-44; PRA-1.04, PRA-0.10 |
| R-64 (neu, Nachtrag 2026-11-23) | Restore-Evidence-Reports (je Restore: Backup-Prüfung, Journalbereich, Zähler je Datenbereich, Residue-Scan, Stichproben, Freigaben) | 3 J. | RE, Art. 5 Abs. 2, Art. 32 Abs. 1 lit. d — INFERRED | **nicht implementiert**; Soll: Ablage außerhalb der DB (`privacy/evidence/<restore_id>.json` bzw. Volume), **ohne** Pseudonyme und Personendaten, Regex-Prüfung TA-760 (`17` §11.5, PRIV-870) | — | PROPOSED; PRA-1.05, PRA-3.09 |
| R-65 (neu, Nachtrag 2026-11-23) | Quarantäne verwaister Objekte nach Restore (Präfix `quarantine/<restore_id>/`, nicht auslieferbar) | 30 d, dann physisch löschen | BE, Art. 5 Abs. 1 lit. e; Schutz legitimer Uploads nach dem Backup-Stand — INFERRED | **nicht implementiert**; Soll: Object-Storage-Reconciler verschiebt statt löscht; Wiederaufnahme in den Katalog nur durch Plattform-Admin, nie für Objekte eines nach T0 gelöschten Subjekts (`17` §7.4, PRIV-853) | — | PROPOSED; LEG-60; PRA-1.08, PRA-3.06 |
| — | Vektordaten des Knowledge-Service | — | — | nur statische YAML-Chunks (`src/knowledge-service/app/ingestor.py:29–49`), wöchentlicher Reingest | — | keine personenbezogenen Daten |
| — | Replikate | — | — | `arangodb`/`vectordb`/`timescaledb` mit genau 1 Replik erzwungen (`values.yaml:291–302`, Render-Fail) | — | keine Kopien |

Zuordnung der Strang-D-Zeilen (Audit 2026-11-22, Nr. 1–36) zu dieser Matrix: 1 → R-01, 2 → R-02, 3 → R-03, 4 → R-11,
5 → R-04/04a, 6 → R-05, 7 → R-40, 8 → R-06, 9 → R-06a, 10 → R-01b, 11 → R-16/R-17/R-18, 12 → R-07, 13 → R-12,
14 → R-25, 15 → R-26, 16 → R-38, 17 → R-59, 18 → R-60, 19 → R-61, 20 → R-46…R-48, 21 → R-19…R-39 (nicht impl.),
22 → R-14, 23 → R-15, 24 → R-57 (und R-56), 25 → R-41/R-42, 26 → R-49 (mit R-10), 27 → R-50, 28 → R-51, 29 → R-52,
30 → R-53, 31 → R-54, 32 → R-55, 33 → Replikate, 34 → R-45 (ersetzt durch R-63), 35 → Knowledge-Service, 36 → R-58.
Die Backup-Zeile der Fassung 1.1 („— Backup-Dumps ≤ 35 d“) ist R-53/R-54.

---

## 9. Erforderliche Spec-Änderungen (Vorschläge, nicht angewendet; E16)

| Spec | Änderung |
|------|----------|
| NFR-011 | R-16/R-17 **feldgenau** (§3.2) statt Collection-weit; R-17 Fristbeginn 1.1. Folgejahr (L-01); R-18 Fundstelle nachliefern oder Klasse ändern; R-25 Grundlage „lit. b/f; Art. 17 Abs. 3 ist Ausnahme“; R-26 Akteur → Marker; neue Zeilen R-43…R-48; `care_events.material` in R-25; §3.1 Beat-Tabelle |
| REQ-025 | §3.1.3 Regel 2 feldgenau (Tombstone nur für Pflichtfelder gem. Profil); Zurechnungsrollen; Prüfwarteschlange Phase 2.6; §10 Tabelle (Schlüssel, TDDDG, Schalter); „CanG §X“ → § 26 KCanG (L-05) mit dem Hinweis, dass die erntende Person keine Pflichtangabe ist; Footer-Version |
| REQ-053 | §13.2 „`treatment_applications` bleibt der Nachweis“ → „unterstützt die Aufzeichnung“ (PRIV-413); GP-FR-109 Feldsatz + `material`; GP-NFR-055 Plan-Audit Marker; GP-FR-109 vs. E-16 (W-01) |
| REQ-024 / REQ-049 | `organization_kind`, `record_keeping`, `attribution_visibility`; E-Mail nur `management`; `management` darf schwärzen |
| REQ-022 | Bestätigungen ohne Akteur und ohne eigene Aufbewahrung |
| REQ-023 §5b.1 | „Backup-System → Cross-Tenant Read-Access“ mit REQ-049 P4 in Einklang bringen |
| docs `privacy.md`, `compliance-anbauvereinigung.md` | DSFA-Satz entfernen (W-10); KCanG-Hinweis: Kamerplanter ist kein Weitergabe-Register nach § 26 Abs. 1 Nr. 5–7 |
| NFR-011 (Audit 2026-11-22) | R-40 als implementiert führen (LEG-58); Zeilen R-49…R-62 (§8, LEG-44); R-14 Fußnote „nur mit `TIMESCALEDB_ENABLED`“ (PRA-3.06, PRA-3.10) |
| REQ-025 §9 (Audit 2026-11-22) | Dienstliste nach §2.3 (KI/LLM, Erkennung, E-Mail, Push/Apprise, NASA POWER, Bright Sky; LEG-33); DP-002 als nicht umgesetzt kennzeichnen, bis PRA-2.14 gebaut ist (LEG-49) |
| docs `data-retention.md` (Audit 2026-11-22) | Sensor-Downsampling nur mit TimescaleDB; `sensor_daily` ab Tag 0 statt „Tagesmittel 2–5 Jahre“ (LEG-44) |
| docs `environment-variables.md` (Audit 2026-11-22) | `PRIVACY_DATA_CONTROLLER_*` in `full`/`production` Pflicht (PRIV-416, LEG-50) |

---

## 10. Produktionsgates für Verarbeitungen dieses Dokuments

Definitionen (README §„Produktionsgates“): `engineering_allowed` (Code mit Testdaten/Flag aus) ·
`deployment_allowed` (ausrollbar, Flag aus) · `processing_allowed` (Flag an / Verarbeitung aktiv) mit den
Werten `ja` · `nein (bis LEG-nn)` · `provisorisch (Bestand, Prüfdatum)`.

| Maßnahme | Art | Gate | Durchsetzungspunkt |
|----------|-----|------|--------------------|
| Fristbeginn PflSchG 1.1. Folgejahr (PRIV-412) | schutzverstärkend für die Pflicht | ja | Code |
| `harvested_by_key` Tombstone → Marker für `kcang_association` (PRIV-411) | datenvernichtend / Bestandsänderung | nein (bis LEG-03, LEG-17) | Flag `PRIVACY_RECORD_KEEPING_RECLASSIFY` (Default aus) |
| Reklassifizierung `legacy → none` (PRIV-402) | datenvernichtend | nein (bis LEG-03) | dasselbe Flag |
| Backfill kopiert Zurechnung (LIA-2) | Bestand | provisorisch (Prüfdatum = LEG-07) | Schalter `PRIVACY_BACKFILL_COPIES_PERFORMER` (Default = Bestand) — **Ist (Audit 2026-11-22): existiert nicht**; MUSS Migration **und** Konsistenzjob abdecken (Lesestelle `account_of`, PRA-2.08) |
| `attribution_visibility`-Defaults (DA-04) | einschränkend | ja | Code/Setting |
| E-Mail nur `management` (PRIV-305) | einschränkend | ja (Breaking Change dokumentiert) | Code |
| Prüfwarteschlange, Entdeckung (DA-05) | schutzverstärkend | ja | Code |
| Auto-Schwärzung nach SLA (DA-05) | datenvernichtend (fremde Historie) | nein (bis LEG-08) | Flag `PRIVACY_REVIEW_AUTO_REDACT_ON_SLA` (Default aus) |
| Kommerzieller SaaS-Betrieb mit gewerblichen Mandanten | Betriebsmodell | `deployment_allowed` nein (bis LEG-01, LEG-05, LEG-12: AVV, Information, DSFA-Entscheidung) | Betreiber-Checkliste (DEC-32) |
| Selbst gehosteter Betrieb gewerblicher Organisationen (Betreiber = Arbeitgeber) | Betriebsmodell | kein Gate greift (DEC-32 erfasst nur SaaS; LEG-48) → Hinweis/Bestätigung an die Klassifizierung `commercial` koppeln, unabhängig vom Hosting | Code PRA-3.04 nach PRA-1.02; `11` §4.3 |
| Backups aktivieren | Infrastruktur | `deployment_allowed` nein (bis Journal + Restore-Lebenszyklus vorhanden und Drill A–H grün, `17` §14; LEG-11 Prüfdatum) | Helm `backup.enabled` nur mit `privacy.journal.enabled` (v1.1: `privacy.mirror.enabled`; DEC-26), Chart-Vertrag `scripts/ci/assert_chart_contracts.sh` (PRIV-855) — **Ist (Audit 2026-11-22): Precheck fehlt** (`values.yaml:382–387` prüft nur `backup.s3.bucket`); Interim PRA-0.10 und Runbook-Sofortkorrektur PRA-0.12 |
| KI-Funktionen mit Cloud-LLM (`LLM_PROVIDER ≠ ollama`) | Übermittlung, einwilligungspflichtig | `processing_allowed` nein, bis das Gate am tatsächlichen Provider prüft (§2.2, LEG-31); vorher Betriebsprüfung PRA-0.01 | Code PRA-0.09 (fail-closed) |
| Koordinaten vergröbern (DP-002, §2.4) | schutzverstärkend | ja | Code PRA-2.14 |
| Pflichtexport-Bestätigung beim Mandantenlöschen (PRIV-415) | schutzverstärkend | ja | Code PRA-2.09 |
| Löschung der Pflichtzeilen für `none` nach Mandantenlöschung (PRIV-415) | datenvernichtend | nein (bis LEG-03) | Flag `PRIVACY_RECORD_KEEPING_RECLASSIFY` |
| Startverweigerung Platzhalter-Verantwortlicher, Art.-13-Felder (PRIV-416) | schutzverstärkend | ja (`full`/`production`) | Code PRA-2.18 |
| Plattform-Admin-Export nur mit `reason` (§2.5) | einschränkend | ja | Code PRA-2.11 |

---

## 11. Compliance-Matrix (Audit 2026-11-22)

Abgleich je Vorschrift (DSGVO, BDSG, TDDDG, BetrVG, PflSchG, KCanG) zwischen Anforderung, Implementierung, Lücke und
Remediation-Aufgabe; übernommen aus dem Audit 2026-11-22 (Compliance-Matrix, 59 Zeilen), gemessen gegen develop
`007a4ea90`. Die Lücken nennen die Befund-IDs LEG-01…LEG-61 (Register `decision-log.md` §B/§D), die Maßnahmen die
PRA-IDs aus [`12`](12-implementation-roadmap.md); die rechtliche Würdigung steht in den Fachdokumenten und in `13`, die
offenen Fragen in [`16`](16-dpo-briefing-2517.md). Pfade relativ zum Repo-Root; Backend-Pfade ohne Präfix unter
`src/backend/app/`, Frontend-Pfade ohne Präfix unter `src/frontend/src/`. Keine Rechtsberatung. Der Status bewertet den
**Repo-Stand am geprüften SHA**; Dokumentationsteile, die diese Paketfassung 1.2 nachgeführt hat (z. B. `11` für
Nr. 47), ändern den Status erst, wenn auch die Code- bzw. Betriebsanteile der PRA-Aufgabe erledigt sind.

### 11.0 Statuswerte

| Status | Bedeutung |
|---|---|
| erfüllt | Anforderung im Code bzw. Repo umgesetzt; Stränge melden `CONFIRMED` ohne offene Lücke. |
| teilweise | Wesentliche Teile umgesetzt; mindestens eine Lücke aus 02/04 offen. |
| nicht erfüllt | Kein Mechanismus oder keine Dokumentation vorhanden, oder eine Zusage wirkt nicht. |
| nicht anwendbar | Die Verarbeitung, die die Vorschrift voraussetzt, findet nicht statt. |
| Rechtsprüfung offen | Ob und wie die Vorschrift greift, hängt von einer offenen LEG-Frage ab (`LEGAL_REVIEW_REQUIRED`). |

Der Status bewertet den **Repo-Stand am geprüften SHA**. Was nur in einer Installation nachweisbar ist (Verträge,
Prod-Konfiguration, Backups, Alerting), ist nicht prüfbar und steht in der Spalte „Lücke“ als Grenze. Ein Status ist keine
Feststellung eines Rechtsverstoßes.

---

### 11.1 DSGVO

| Nr. | Vorschrift | Anforderung | Bestehende Implementierung (Pfad) | Lücke | Remediation (PRA) | Status |
|---|---|---|---|---|---|---|
| 1 | Art. 5 Abs. 1 lit. a | Transparenz: Zusagen gegenüber Betroffenen entsprechen dem Verhalten | `GET /privacy/policy` (`domain/services/privacy_service.py:1981–2196`); Nutzerdoku `docs/de/user-guide/privacy.md` | Falsche Zusicherungen: Einschränkung wirkt nicht (`privacy.md:153`, LEG-23); DSFA „durchgeführt“ (`:488–490`, W-10, LEG-12); Cache ohne Namen (`:426`, LEG-27); KI-Indikator aus Mandanten-Datensatz (LEG-31); MCP-Einwilligungstext „nur markierte Einträge“ (LEG-51) | PRA-0.05, PRA-0.09, PRA-2.10 | nicht erfüllt |
| 2 | Art. 5 Abs. 1 lit. b | Zweckbindung | Backfill-Mapper `domain/engines/care_event_backfill_mapper.py:183–191`, Konsistenzjob `domain/services/care_event_consistency_service.py:129` | Fortlaufende Kopie einer Pflichtangabe ins Pflegeprotokoll (LEG-07); Aufgaben-Leistungsfelder ohne dokumentierten Zweck (LEG-28) | PRA-2.08, PRA-2.06, PRA-3.01 | Rechtsprüfung offen |
| 3 | Art. 5 Abs. 1 lit. c | Datenminimierung | Projektion im IndexedDB-Cache (`features/gardenPlanner/offline/planCache.ts:345–367`); Log-Pseudonymisierung (`common/log_privacy.py`); Sentry-Scrub (`observability/error_tracking.py:523–560`) | SW-API-Cache unprojiziert (LEG-27); Leistungsfelder je Person (LEG-28); exakte Koordinaten an Wetterdienste, DP-002 (LEG-49) | PRA-0.07, PRA-2.06, PRA-2.14 | teilweise |
| 4 | Art. 5 Abs. 1 lit. d | Richtigkeit; berichtigte Daten werden nicht durch Altstand ersetzt | Schwärzung `POST /care-events/{key}/redact` (`api/v1/care_events/tenant_router.py:231–255`) | Plan-Snapshot-Restore setzt geschwärzte/berichtigte Texte zurück (`domain/services/garden_plan_import_service.py:420–441`, LEG-34) | PRA-2.02 | teilweise |
| 5 | Art. 5 Abs. 1 lit. e | Speicherbegrenzung | Beat-Tasks R-01…R-26 (`tasks/__init__.py:461–604`); Ceilings/Floors (`config/settings.py:103–127, 1147–1290`); IP-Anonymisierung 7 d (`tasks/auth_tasks.py:134–156`) | Ex-Mitglieder unbefristet sichtbar (LEG-06 a); Freitexte ohne Frist außer R-25 (LEG-08); `control_events` ohne Frist (LEG-29); Gerätefristen 365/90 d (LEG-10); SW-Cache und `notices` ohne physische Frist (LEG-36, LEG-56); Bucket-Versionen (LEG-26); Nebenspeicher (LEG-44); Waisenobjekte (LEG-60); Dumps nach Abschalten des Backups unbefristet (LEG-68); Journal-, Evidence- und Quarantänefristen R-63…R-65 nur spezifiziert (`17` §3.8) | PRA-2.03, PRA-2.01, PRA-2.07, PRA-2.15, PRA-2.16, PRA-0.10, PRA-3.06, PRA-1.08 | teilweise |
| 6 | Art. 5 Abs. 1 lit. f | Integrität und Vertraulichkeit | siehe Nr. 37–44 (Art. 32) | siehe Nr. 38–40, 42–44 | siehe dort | teilweise |
| 7 | Art. 5 Abs. 2 | Rechenschaft: Dokumentation gibt den Ist-Stand wieder; Löschung nachweisbar | Paket `spec/privacy/` (01–16, decision-log); Guards unter `tests/unit/guards/`; `security_audit_log` (R-38) | Paket nicht nachgeführt (LEG-61); NFR-011 R-40 falsch geführt (LEG-58); Inventar unvollständig (LEG-46); kein Residue-Scan bei Kontolöschung (Audit 2026-11-22, Verifikation PRIV-234); Freitext-Löschung nicht nachweisbar (LEG-08); kein Nachweis je Restore (Evidence-Report R-64, `17` §11.5); Löschung gilt vor Journal-Bestätigung als abgeschlossen (PRIV-811) | PRA-3.10, PRA-1.01, PRA-1.07, PRA-2.01, PRA-3.09, PRA-1.05 | teilweise |
| 8 | Art. 6 Abs. 1 lit. b, c, f | Rechtsgrundlage je Verarbeitung, dokumentierte Abwägung | PA-Matrix §2 (PA-01…PA-12); LIA-1/LIA-2 in §4 | Zurechnung 5 J. außerhalb LIA-1 (LEG-02); Aufgaben-Leistungsfelder ohne Grundlage (LEG-28); LIA-4 nur Verweis (LEG-16); LIA für Wetterkoordinaten fehlt (LEG-49); lit. c-Aufbewahrung auch ohne Pflicht (LEG-30) | PRA-2.05, PRA-2.06, PRA-3.05, PRA-2.14, PRA-1.02, PRA-3.01 | Rechtsprüfung offen |
| 9 | Art. 6 Abs. 1 lit. a, Art. 7 | Einwilligung vor Verarbeitung eingeholt, nachweisbar, widerrufbar mit Wirkung | `domain/guards/consent_guard.py:47–51` (403 `consent_required`, sechs Services); Consent-Records (`data_access/arango/consent_repository.py`); Frontend-Sentry nur nach Einwilligung (`test/observability/errorTracking.test.ts:308–315`) | KI-Pfade prüfen `ai_cloud_processing` am Mandanten-Provider, KS nutzt eigenes `LLM_PROVIDER` (`domain/services/ai_assistant_service.py:125–165`, `domain/services/diagnose_service.py:293–312`; LEG-31); Einwilligung der handelnden statt der Uploader-Person (LEG-40); Restore setzt Widerruf zurück (LEG-24) | PRA-0.01, PRA-0.09, PRA-2.12, PRA-1.04, PRA-1.05 | teilweise |
| 10 | Art. 6 Abs. 4 | Vereinbarkeit der Weiterverarbeitung | Mapper kopiert nur Kontoreferenz, keine Freitexte (`migrations/versions/v0104_care_events_backfill.py:19–21`) | Schalter `PRIVACY_BACKFILL_COPIES_PERFORMER` fehlt (0 Treffer); keine Klassendifferenzierung; Information Art. 13 Abs. 3 fehlt (LEG-07) | PRA-2.08, PRA-2.18 | Rechtsprüfung offen |
| 11 | Art. 9 | Besondere Kategorien in Freitext | Consent-Guard für KI-Zwecke; Schwärzung nur `care_events` | Keine Hinweistexte und Längengrenzen an Freitextfeldern (`material`, `observed_outcome`, `nutrient_plans.author`); Tagebuch für alle Mitglieder sichtbar; Art.-9-Nähe Cannabis (RISK-18) (Strang A 5b; LEG-08, LEG-12) | PRA-2.01, PRA-3.04 | Rechtsprüfung offen |
| 12 | Art. 10 | Daten über Straftaten in Freitext | wie Nr. 11 | Hinweise auf KCanG-Überschreitungen möglich, keine Bewertung im Paket außer Strang A | PRA-2.01, PRA-3.04 | Rechtsprüfung offen |
| 13 | Art. 12 Abs. 1–5 | Erleichterte Ausübung, Monatsfrist, Unterrichtung | Selbstbedienung Export/Löschung mit Zustandsautomaten; stündliches Re-Dispatch hängender Aufträge (`privacy_service.py:320–339`); max. 1 aktiver Export (`domain/engines/data_export_engine.py:1424–1434`) | Keine Fristüberwachung (Strang C); Art.-18/21-Anträge erreichen niemanden (LEG-23); eigene Fotos nur über Leitung löschbar (LEG-39); kein Listen-/Download-Weg nach Reload (`privacy.md:12`) | PRA-0.06, PRA-1.06, PRA-2.12, PRA-2.04, PRA-2.20 | teilweise |
| 14 | Art. 12 Abs. 6 | Identitätsprüfung mit angemessenen Mitteln | Step-up und API-Key-Sperre für Löschung (`api/v1/privacy/router.py:184–221, 271–295`; `common/auth.py:82–92`) | Vollexport per ungescoptem API-Key ohne Step-up (`router.py:124–181`, LEG-38) | PRA-2.04 | teilweise |
| 15 | Art. 13 | Informationspflichten bei Erhebung | `PrivacyPolicyInfo` (`domain/models/privacy.py:850–857`), `GET /privacy/policy` mit Rechten und `retention_summary` | Empfänger, Drittland, Art. 77, DSB-Kontakt fehlen; Platzhalter-Verantwortlicher (`config/settings.py:1134–1135`) blockiert Start nicht (LEG-50); keine Fotokategorie (LEG-22); keine Backup-Frist (PRIV-708); Rechtstexte offen (LEG-12) | PRA-2.18, PRA-1.03, PRA-0.05, PRA-3.01 | teilweise |
| 16 | Art. 14 | Information nicht direkt Betroffener (abgebildete Dritte, andere Mitglieder in Freitext und Gerätespeicher) | — | Kein Prozess, keine Information; Ausnahme Art. 14 Abs. 5 ungeprüft (LEG-22, LEG-21, LEG-27) | PRA-2.18, PRA-2.04, PRA-3.01 | Rechtsprüfung offen |
| 17 | Art. 15 | Vollständige Auskunft mit Pflichtangaben und Kopie | `data_export_engine.py` (Kontoquellen, persönlicher Mandant), `api/v1/privacy/router.py:124–181`; Tombstone-Abgleich für gelöschte Mandanten (`data_access/arango/personal_data_repository.py:109–131`) | Verlassene Mandanten fehlen (LEG-06 b); Fotos nur Metadaten, im geteilten Mandanten ohne `_key` (LEG-21); `control_events` fehlt (LEG-29); keine Angaben nach Abs. 1 lit. a–h (LEG-41) | PRA-2.04, PRA-2.07, PRA-2.18 | teilweise |
| 18 | Art. 16 | Berichtigung | Profil (E-Mail mit Step-up), eigene Einträge editierbar (Rechte-Matrix Strang C) | Mitgliedschaftsdaten nur über Leitung; Restore setzt Berichtigungen zurück (LEG-34); Art. 16 ohne eigenen Vorgang (Zielarchitektur [`01`](01-privacy-architecture.md)) | PRA-2.02 | teilweise |
| 19 | Art. 17 Abs. 1, 2 | Wirksame, vollständige Löschung | `domain/engines/erasure_engine.py` (Regeln, Phasen `privacy_service.py:3000–3164`); sofort `is_active=False`, Refresh-Widerruf (`privacy_service.py:983–984`); Mandantenlöschung `domain/engines/tenant_erasure_engine.py` | Freitexte ohne Entdeckung/Prüfung (LEG-08); Beetfotos nur anonymisiert, `caption` bleibt (LEG-20); `control_events` (LEG-29); Snapshots (LEG-34); Selbstlöschung Fotos (LEG-39); EXIF in verlassenen Mandanten (LEG-55); Backups ohne Replay (LEG-11); Bucket-Versionen und Löschung ohne `VersionId` (LEG-26); Gerätekopien ohne Quarantäne (LEG-10); Mandanten-Import ohne Abgleich gegen abgeschlossene Löschungen (LEG-65); Docker-Release ohne Anhänge-Volume für den Worker (LEG-64); Soll-Mechanik `17` §6, §7 | PRA-2.01, PRA-2.12, PRA-2.07, PRA-2.02, PRA-2.13, PRA-0.10, PRA-1.04, PRA-1.05, PRA-1.07, PRA-1.08, PRA-2.15, PRA-2.23 | teilweise |
| 20 | Art. 17 Abs. 3 | Ausnahmen nur soweit erforderlich (lit. b Rechtspflicht, lit. e Rechtsansprüche) | Pflichtzeilen pseudonymisiert erhalten (`erasure_engine.py:84–122`; `tenant_erasure_engine.py:44–57, 189–209`) | Kein Legal Hold (LEG-35); Pflichtzeilen ohne Zugriffsweg des Pflichtigen und auch für Mandanten ohne Pflicht (LEG-47, LEG-30); Regelbegründung R-16…R-18 für Beetfotos unzutreffend (LEG-20); ob einem Löschantrag die Pseudonyme im WORM-Journal (bis R-63) nach Abs. 3 lit. b/e oder Art. 11 entgegengehalten werden können, ist offen (`17` §7.3, Q-LAW-19) | PRA-1.06, PRA-2.09, PRA-1.02, PRA-2.12, PRA-1.04 | Rechtsprüfung offen |
| 21 | Art. 18 | Einschränkung wirkt (nur Speicherung), auch gegen Lösch-/Purge-Jobs | `POST /privacy/restrict` (`api/v1/privacy/router.py:336–381`), Speicherung `privacy_service.py:1810–1888` | Kein Leser, keine Dependency `check_processing_restriction` (REQ-025 AK-11), `scope` Freitext, keine Betreiberbenachrichtigung, kein `GET` (LEG-23); Antrag und Sperre überleben keinen Restore (Soll: Journal-Ereignisse `PROCESSING_RESTRICTION_*`, Hold-Filter im Retention-Nachlauf, `17` §3.3, PRIV-842) | PRA-0.05, PRA-0.06, PRA-1.06, PRA-1.05 | nicht erfüllt |
| 22 | Art. 19 | Mitteilung an Empfänger bei Berichtigung, Löschung, Einschränkung | — | Kein Mechanismus, keine Empfängerliste (Rechte-Matrix Strang C; LEG-33); Vorgangsart `notification_art19` der Zielarchitektur ([`01`](01-privacy-architecture.md)); nach einem Restore können Sendungen an wiederhergestellte Konten erneut entstehen (Soll: externe Abflüsse während der Isolation aus, `17` §5.3; erneute Mitteilung offen, Q-DSB-26) | PRA-2.20, PRA-1.03, PRA-0.06, PRA-1.06, PRA-1.05 | nicht erfüllt |
| 23 | Art. 20 | Übertragbarkeit bereitgestellter Daten, strukturiert und maschinenlesbar | JSON-Bündel (`api/v1/privacy/router.py:145–181`); Mandantenarchiv REQ-056 mit Originalen für `lead ∧ management` (`domain/engines/tenant_export_engine.py:31, 77`) | Eigene Bilddateien nicht im Bündel; verlassene Mandanten fehlen (LEG-21, LEG-06 b) | PRA-2.04 | teilweise |
| 24 | Art. 21 | Widerspruch beendet Verarbeitung (außer zwingende Gründe) | `POST /privacy/object` legt Restriction `objection_pending` an (`privacy_service.py:1863–1888`) | Wirkung null, kein Kanal zum Verantwortlichen (LEG-23); Widerspruch geht bei Restore verloren (Soll: `OBJECTION_RECORDED`, `17` §3.3) | PRA-0.05, PRA-0.06, PRA-1.06, PRA-1.04 | nicht erfüllt |
| 25 | Art. 22 | Keine automatisierte Einzelentscheidung mit Rechtswirkung | Diagnose löst keine Behandlung aus (`pest_detection_service.py:97`); KI beratend | Satz dazu im Art.-15-Bündel fehlt (LEG-41, Hinweis) | PRA-2.18 | nicht anwendbar |
| 26 | Art. 24 | Verantwortung des Verantwortlichen je Betriebsmodell | Kein Phone-home des Projekts (§1, LEG-01) | Rollenmatrix je Betriebsmodell nicht entschieden; wesentliche Mittel fest kodiert (LEG-01) | PRA-3.03, PRA-3.01 | Rechtsprüfung offen |
| 27 | Art. 25 Abs. 1 | Datenschutz durch Technikgestaltung | Consent-Guard, Log-Pseudonymisierung, Upload-EXIF-Strip (`domain/services/attachment_service.py:355–356`), Isolation im Offline-Puffer (`queue.ts:234–236`) | Klassifizierung inert (LEG-30); SW-Cache unprojiziert (LEG-27); Journal-Zeitpunkt (LEG-25); Koordinaten (LEG-49); EXIF fail-open (LEG-57); Import übernimmt `anon_` (LEG-54); MCP-Injection (LEG-52); Widerrufspfad API-Key fail-open (LEG-66); Startgate prüft nur die Länge des Tombstone-Salts (LEG-67); Soll Outbox im selben Commit, Pseudonyme, fail-closed Restore-Gate (`17` §4, §5.3) | PRA-1.02, PRA-0.07, PRA-1.04, PRA-2.14, PRA-2.13, PRA-1.07, PRA-2.10, PRA-2.21, PRA-2.22 | teilweise |
| 28 | Art. 25 Abs. 2 | Datenschutzfreundliche Voreinstellungen | „Angemeldet bleiben“ per Default aus (`pages/auth/LoginPage.tsx:198–205`); `traces_sample_rate=0.0`; `send_default_pii=False` | Offline-Speicher ohne Opt-in (LEG-09); `attribution_visibility` nicht gebaut, Default „alle Mitglieder“ (LEG-02); MCP stellt alle Freitexte bereit (LEG-51); `dry_run` Default `false` (LEG-52) | PRA-2.15, PRA-2.05, PRA-2.10 | teilweise |
| 29 | Art. 26 | Vereinbarung bei gemeinsamer Verantwortung | — | Keine Art.-26-Vorlage; geteilte Installationen „wahrscheinlich Art. 26“ (Strang F; LEG-01) | PRA-3.03, PRA-3.01 | Rechtsprüfung offen |
| 30 | Art. 28 Abs. 3 | AVV mit TOM-Anlage (BM-001) | — | Kein AVV-Muster im Repo; Verträge mit Resend, Sentry, LLM-Anbietern, S3 außerhalb nicht prüfbar (LEG-01) | PRA-3.03 | nicht erfüllt |
| 31 | Art. 28 Abs. 2, 4 | Genehmigte Unterauftragsverarbeiter, Pflichtenweitergabe | Dienste im Code verdrahtet (`data_access/external/*`, `src/knowledge-service/app/llm/*`) | Kein Register der Empfänger/Unter-AV; REQ-025 §9 unvollständig (LEG-33) | PRA-1.03 | nicht erfüllt |
| 32 | Art. 28 Abs. 3 lit. a | Verarbeitung nur auf dokumentierte Weisung | Plattform-Export mit Step-up und Audit `TENANT_EXPORT_REQUESTED` (`domain/services/tenant_export_service.py:282–283, 336, 370–376`) | Plattform-Admin-Export ohne Weisungsgrundlage, Widerspruch REQ-049 P4 ↔ REQ-056 §8, kein `reason` (LEG-53, LEG-13) | PRA-2.11, PRA-3.03 | Rechtsprüfung offen |
| 33 | Art. 28 Abs. 3 lit. f | Unterstützung des Verantwortlichen (DSFA, Rechte, Meldung) | Export/Löschung als Selbstbedienung; Mandantenarchiv REQ-056 | Klassifizierung nicht setzbar (LEG-30); kein DSFA-Baustein (LEG-48); kein Pannenwerkzeug (LEG-32) | PRA-1.02, PRA-3.04, PRA-3.02 | teilweise |
| 34 | Art. 28 Abs. 3 lit. g | Rückgabe oder Löschung nach Vertragsende, außer Speicherpflicht | Mandantenarchiv REQ-056; Mandantenlöschung mit 90-d-Frist (REQ-024 AK-52/AK-65) | Pflichtzeilen bleiben ohne Zugriffsweg (LEG-47) | PRA-2.09 | Rechtsprüfung offen |
| 35 | Art. 29 | Zugriff nur auf Weisung; privilegierte Zugriffe kontrolliert | RBAC fail-closed (`common/auth.py:671–832`); `require_platform_admin` (`:644–668`); Audit von Mutationen (R-38) | Kein Leseaudit der Löschvorschau (PRIV-316, `api/v1/admin/platform/router.py:544–560`); Plattform-Export ohne `reason` (LEG-53) | PRA-2.19, PRA-2.11, PRA-3.09 | teilweise |
| 36 | Art. 30 | Verzeichnis von Verarbeitungstätigkeiten (Verantwortlicher; AV) | PA-Matrix §2; Inventar [`02`](02-personal-data-inventory.md) | Kein Verzeichnisdokument (LEG-12); Inventar unvollständig (LEG-46); Löschfristen für Nebenspeicher fehlen (LEG-44); Empfänger fehlen (LEG-33); Fotokategorie (LEG-22); Zeilen für Journal (R-63), Evidence (R-64), Quarantäne (R-65) nur in diesem Dokument (`17` §10.2) | PRA-1.01, PRA-1.03, PRA-3.06, PRA-3.03, PRA-2.18 | teilweise |
| 37 | Art. 32 Abs. 1 lit. b | Authentisierung, Autorisierung, Mandantentrennung | bcrypt Cost 12 (`domain/engines/password_engine.py:21–25`); Access 15 min, Refresh-Rotation mit Replay-Erkennung (`domain/services/auth_service.py:838–915`); HttpOnly-Cookie + CSRF (`api/v1/auth/router.py:250–267`); Lockout (`auth_service.py:684–692`); Step-up nicht per API-Key (`common/auth.py:82–92`); API-Key-Digest, IP-Allowlist, Rate-Limit (`api_key_controls.py:93–110`); Ownership-Guard `_REMAINING` leer | Mit `DEBUG=true` Start mit Default-Secrets (`main.py:77–110`, Hinweis); Vollständigkeit je Route nicht geprüft | — | erfüllt |
| 38 | Art. 32 Abs. 1 | Zweiter Faktor für privilegierte Konten | — | Kein TOTP/WebAuthn (LEG-45) | PRA-2.19 | nicht erfüllt |
| 39 | Art. 32 Abs. 1 lit. a | Verschlüsselung ruhender Daten und Backups (dokumentierte Abwägung) | Feld-Secrets Fernet (`domain/engines/encryption_engine.py:55–90`); Backup-SSE `AES256` (`helm/kamerplanter/values.yaml:584–587`) | Volume-Verschlüsselung weder erzwungen noch dokumentiert (LEG-42); Docker-Backup ohne Verschlüsselung und Frist, Passwort in Kommandozeile (LEG-43) | PRA-3.07 | nicht erfüllt |
| 40 | Art. 32 Abs. 1 lit. a, b | Schutz interner Verbindungen | NetworkPolicy default-deny im Prod-Release (`values.yaml:2601–2620`) | Valkey ohne Auth, Arango/Valkey/Timescale ohne TLS (`values.yaml:786, 793, 2610–2614`; LEG-59) | PRA-3.08 | nicht erfüllt |
| 41 | Art. 32 Abs. 1 lit. a | Pseudonymisierung in Logs und Fehlertracking | `common/log_privacy.py`, `config/logging.py:33–80`, `src/frontend/nginx.conf:18–48`; `observability/error_tracking.py:675, 685` | Laufzeitwirkung nicht geprüft (statisch `CONFIRMED`); Log-Frist siehe Nr. 5 | — | erfüllt |
| 42 | Art. 32 Abs. 1 lit. c | Wiederherstellbarkeit ohne Rücksetzen von Rechten und Sicherheitszustand | Backup-CronJob (aus, `values.yaml:567–612`); Drill 2026-10-04 (nur Dokumentanzahl) | Kein Journal, kein Replay, kein Precheck, keine Obergrenze 35 d (LEG-11); Restore setzt Widerrufe zurück (LEG-24); Runbook hält bei `dedicatedQueues` zwei Worker nicht an (LEG-62); Docker-Restore gegen laufende Anwendung (LEG-63); API-Key-Widerruf fail-open (LEG-66); Salt-Identität ungeprüft (LEG-67); Valkey behält den Stand nach T0 (LEG-69); Worker/Beat warten nicht auf Migrationen (LEG-70); Soll-Mechanik `17` §5 | PRA-0.03, PRA-0.10, PRA-0.12, PRA-1.04, PRA-1.05, PRA-1.08, PRA-2.21, PRA-2.22 | teilweise |
| 43 | Art. 32 Abs. 1 lit. d | Regelmäßige Überprüfung der Wirksamkeit | Guards im CI (statisch) | Kein Drill mit gelöschtem Konto, keine Tabletop-Übung, keine Evidenzablage; Soll Quartals-Drill Szenarien A–H mit Evidence-Report (`17` §9, §11.5, PRIV-872) | PRA-3.09 | nicht erfüllt |
| 44 | Art. 32 Abs. 1 lit. b | Integrität bei KI-/Agentenzugriff | Prompt-Injection-Schutz im Knowledge-Service (`src/knowledge-service/app/prompt_engine.py:148–190`); MCP-Schlüssel nie mehr als Weboberfläche (`mcp_server/auth.py:91–167`) | Mandanteninhalte unmarkiert an schreibende MCP-Agenten, `dry_run` Default `false` (`mcp_server/base.py:265–279`; LEG-52) | PRA-2.10 | teilweise |
| 45 | Art. 33 | Meldung binnen 72 h; Dokumentation jeder Verletzung | Eindämmungsbausteine: `POST /auth/logout-all` (`api/v1/auth/router.py:539–547`), API-Key-Widerruf, Konto-/Mandantensperre | Kein Verfahren, kein Register, keine `SECURITY.md`, keine Alert-Regeln (`NFR-007:95` „Offen“) (LEG-32) | PRA-0.02, PRA-0.11, PRA-3.02, PRA-3.09 | nicht erfüllt |
| 46 | Art. 34 | Benachrichtigung Betroffener bei hohem Risiko | — | Keine Vorlage, keine Funktion „Mandanten benachrichtigen“ (LEG-32); Ausnahme Abs. 3 lit. a ohne dokumentierte Verschlüsselung nicht nutzbar (LEG-42) | PRA-3.02, PRA-3.07 | nicht erfüllt |
| 47 | Art. 35 (Schwellwertprüfung) | Begründete Vorprüfung je Betriebsmodell | [`11`](11-dpia-pre-screening.md) (Methodik DA-08) | Modell „selbst gehostet, gewerblich“, RISK-21…24, Service-Account/MCP-Weitergabe und KI fehlen (LEG-48, LEG-12); Backup/Restore-Risiken in `11` (RISK-10, Nachtrag 2026-11-23) nachgeführt, Umsetzung offen | PRA-3.04, PRA-1.05 | teilweise |
| 48 | Art. 35 (gewerbliche Mandanten) | DSFA beim Verantwortlichen; Anbieter liefert Baustein und Auslöser | DEC-32 sperrt kommerziellen SaaS-Betrieb organisatorisch | Kein DSFA-Baustein „Beschäftigte“; Klassifizierung nicht erkennbar (LEG-30); Gate greift nicht bei Selbsthosting (LEG-48); Doku behauptet durchgeführte DSFA (W-10); ob BM-001 mit aktivem Backup das Restore-Szenario in die DSFA aufnehmen muss, ist Teil von Q-DSB-08 (`17` §10.2) | PRA-3.04, PRA-1.02, PRA-0.05 | nicht erfüllt |
| 49 | Art. 36 | Vorherige Konsultation bei hohem Restrisiko | Aussage in `11` („nicht erforderlich“) | Aussage stützt sich auf nicht gebaute Maßnahmen (Strang E Lieferung (d)) | PRA-3.04, PRA-3.01 | Rechtsprüfung offen |
| 50 | Art. 44–46 | Übermittlungsgrundlage je Drittlandempfänger dokumentiert | Pl@ntNet/Kindwise mit Einwilligung und EXIF-Strip (`domain/services/identification_service.py:99–118`); Web-Push-Payload verschlüsselt (`pwa_notification_channel.py:214–218`) | Keine Drittlandprüfung (LEG-33); NASA POWER mit exakten Koordinaten (LEG-49); Sentry SaaS unbelegt (LEG-16); Resend-Region offen | PRA-1.03, PRA-2.14, PRA-3.05 | nicht erfüllt |
| 51 | Art. 49 Abs. 1 lit. a | Ausdrückliche Einwilligung als Ausnahme (KI-Cloud) | Einwilligung `ai_cloud_processing` definiert; `/ask` prüft korrekt (`ai_assistant_service.py:524, 572`) | Tipps, Tagestipp, „Warum?“, Chat, Diagnose prüfen am falschen Provider (LEG-31) — wirksam, sofern `LLM_PROVIDER ≠ ollama` (Prod nicht prüfbar, PRA-0.01); Eignung als Art.-49-Grundlage offen (Q-DSB-19) | PRA-0.01, PRA-0.09, PRA-1.03 | nicht erfüllt |

---

### 11.2 Nationales Recht

| Nr. | Vorschrift | Anforderung | Bestehende Implementierung (Pfad) | Lücke | Remediation (PRA) | Status |
|---|---|---|---|---|---|---|
| 52 | BDSG § 26 (i. V. m. Art. 88 DSGVO) | Grundlage für Beschäftigtendaten des Arbeitgeber-Mandanten | Durchführende-Regel „immer die aufrufende Person“ auf allen vier Bestätigungspfaden (`api/v1/care_reminders/router.py:159–170`, `domain/services/care_reminder_service.py:1290–1368`, `mcp_server/tools/care.py:77–86`; Guard `test_care_confirmation_names_its_performer.py`) | Fortgeltung nach C-34/21 offen (V-08); Leistungsfelder (LEG-28), `control_events` (LEG-29), Klassifizierung inert (LEG-30) (LEG-05) | PRA-2.05, PRA-2.06, PRA-1.02, PRA-3.01 | Rechtsprüfung offen |
| 53 | BDSG § 22 | Ausnahmen zur Verarbeitung besonderer Kategorien | — | Im Paket nicht behandelt; erst relevant, wenn eine Funktion Art.-9-Daten zielgerichtet verarbeiten soll (L-23 in [`13`](13-legal-evidence-register.md)) | PRA-3.01 | Rechtsprüfung offen |
| 54 | TDDDG § 25 Abs. 2 Nr. 2 (App-Shell) | Speicherung unbedingt erforderlich für den gewünschten Dienst | Precache, `kp-static-assets`, `kp-runtime-config` ohne personenbezogene Daten (`sw.ts`); Kill-Switch `PWA_CACHING_ENABLED` (`values.yaml:1063`) | — | — | erfüllt |
| 55 | TDDDG § 25 Abs. 1, Abs. 2 Nr. 2 (Lesecache, Schreibpuffer, SW-API-Cache) | Einwilligung oder ausdrücklich gewünschter Dienst und unbedingte Erforderlichkeit | Namensraum je Nutzer/Mandant, `owned()`, Projektion im IndexedDB-Cache | SW-Registrierung bedingungslos (`main.tsx:43`); kein Schalter `kp-offline-mode` (0 Treffer); SW-API-Cache mit Rohantworten (LEG-09, LEG-27); REQ-025 §10 veraltet | PRA-2.15, PRA-0.07, PRA-0.05 | Rechtsprüfung offen |
| 56 | BetrVG § 87 Abs. 1 Nr. 6 (Eignung) | Mitbestimmung bei technischen Einrichtungen zur Verhaltens-/Leistungsüberwachung (Pflicht des Arbeitgebers) | Personenfilter nur Lead/`management` (`domain/services/care_event_service.py:151–178`) | Objektive Eignung von Aufgaben- und Schaltprotokollen (LEG-28, LEG-29); BAG-Linie nicht verifiziert (V-05) (LEG-05) | PRA-2.06, PRA-2.07, PRA-3.01 | Rechtsprüfung offen |
| 57 | BetrVG § 87 Abs. 1 Nr. 6 (Produktunterstützung) | Anbieter liefert Hinweis, Mustertext und minimierenden Betriebsmodus | — | Kein Mustertext Betriebsrat (PRIV-406), kein Modus „Organisation mit Beschäftigten“, kein Hinweis bei Anlage (LEG-05, LEG-30) | PRA-0.04, PRA-1.02, PRA-3.04 | nicht erfüllt |
| 58 | PflSchG § 11 (i. V. m. Art. 67 VO 1107/2009) | Aufzeichnung beruflicher Verwender „unter Angabe des jeweiligen Anwenders“; Frist ab Folgejahr; nur bei Pflicht | `treatment_applications` pseudonymisiert erhalten (`erasure_engine.py:84–122`; `tenant_erasure_engine.py:44–57`); Anwender-Schlüssel aus Token (`api/v1/ipm/tenant_router.py:175, 213`) | Aufbewahrung für alle Mandanten unabhängig von `record_keeping` (LEG-30, RISK-06); Fristbeginn (PRIV-412, Strang E PA-05); kein Zugriffsweg nach Mandantenlöschung (LEG-47); Inhaltskatalog DVO 2023/564 unverifiziert (L-04) | PRA-1.02, PRA-2.09, PRA-3.01 | teilweise |
| 59 | KCanG § 26 | Fünf Jahre Dokumentation nur für Anbauvereinigungen; erntende Person keine Pflichtangabe | `harvest_batches` pseudonymisiert erhalten (`tenant_erasure_engine.py:189, 208–209`); Ernteschlüssel aus Token (`api/v1/harvest/tenant_router.py:160, 232`) | Aufbewahrung Collection-weit für alle Mandanten, auch Eigenanbau (LEG-30; LEG-17 nicht revalidiert); kein Zugriffsweg nach Mandantenlöschung (LEG-47) | PRA-1.02, PRA-2.09 | teilweise |

---

### 11.3 Zählung

| Status | Anzahl | Zeilen |
|---|---|---|
| erfüllt | 3 | 37, 41, 54 |
| teilweise | 23 | 3, 4, 5, 6, 7, 9, 13, 14, 15, 17, 18, 19, 23, 27, 28, 33, 35, 36, 42, 44, 47, 58, 59 |
| nicht erfüllt | 16 | 1, 21, 22, 24, 30, 31, 38, 39, 40, 43, 45, 46, 48, 50, 51, 57 |
| nicht anwendbar | 1 | 25 |
| Rechtsprüfung offen | 16 | 2, 8, 10, 11, 12, 16, 20, 26, 29, 32, 34, 49, 52, 53, 55, 56 |
| **Summe** | **59** | DSGVO 51, national 8 |

Konsistenz: Jede Lücke nennt eine LEG-ID; jede PRA-Aufgabe ist in `12` definiert. Art. 19 (Nr. 22) und die Überwachung
der Monatsfrist nach Art. 12 Abs. 3 (Nr. 13) deckt PRA-2.20 ab. Nachtrag 2026-11-23: PRA-0.12, PRA-1.08, PRA-2.21,
PRA-2.22, PRA-2.23 und PRA-3.11 sind Vorschläge aus [`17`](17-privacy-recovery.md) §14 und werden in `12` §6 aufgenommen; LEG-62…LEG-70 sind
die Befunde aus `17` §1.6 (Registereintrag `decision-log.md` §D). Die Zählung §11.3 ist unverändert, weil keine
Anforderung aus `17` implementiert ist.
