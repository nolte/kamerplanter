# SPEC-06 — Verarbeitungstätigkeiten, Rechtsgrundlagen und Aufbewahrung

```
Paket: spec/privacy · Version 1.1 · 2026-11-09 · gemessen gegen develop 24d1c2988; Nachtrag #2839 (develop 343afbb97)
Anforderungs-IDs: PRIV-400 … PRIV-449
Hängt ab von: NFR-011 (Aufbewahrungsregeln R-nn), REQ-025 §3, 02 (Inventar), 03/04 (Verhalten),
13 (Rechtsevidenz L-nn), 15 (Entscheidungsanalysen DA-01…DA-04)
Änderung v1.1: Rollenmatrix (§1), Verarbeitungstätigkeitenmatrix (§2), feldgenaue Zuordnung der
Pflichtaufzeichnungen (§3), Evidenzklassen an jeder Rechtsgrundlage, Produktionsgates (§10).
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
| PA-05 | Gesetzliche Aufzeichnung | Anwendende, Erntende | ATTR, Fach | Behörde auf Verlangen | **lit. c nur für die in §3.2 zugeordneten Felder und nur bei `pflschg_professional`/`kcang_association`** (L-01, L-05 VERIFIED_LEGAL); sonst lit. b/f | je Feld (§3.2) | R-16/R-17/R-18 mit Fristbeginn nach PRIV-412 | Löschung: Ausnahme Art. 17 Abs. 3 lit. b nur für Pflichtfelder (LEGAL_REVIEW_REQUIRED LEG-04) | Mandant | Betreiber |
| PA-06 | Pflanzenakte, Freitext, Fotos | Mitglieder, Dritte, abgebildete Personen | TXT, MED | Mitglieder | lit. b — INFERRED; Fotos Dritter: lit. f + Art. 14 (RISK-17) | Freitext ist Zweck des Tagebuchs | Lebensdauer der Pflanze/des Mandanten; Vorschlag R-47 für geschlossene Aufgaben/Kommentare | Löschung → Marker + Prüfwarteschlange (DA-05) | Mandant | Betreiber |
| PA-07a | Betroffenenrechte Konto | Kontoinhaber | CONS, AUD | — | lit. c (Art. 12–22) | — | R-04, R-05, R-06, R-13 | — | Betreiber | — |
| PA-07b | Betroffenenrechte Mandantendaten | gelöschte Mitglieder, Leads | AUD (`privacy_review_items`) | Leads/Management | lit. c (Art. 17, Art. 5 Abs. 2) | Nachweis der Erledigung | R-43 3 J. | — | Mandant | Betreiber (Werkzeug) |
| PA-08 | Offline-Funktion auf dem Gerät | Gerätenutzer | DEV | — (lokal) | TDDDG § 25 Abs. 2 Nr. 2 (L-11) **nur mit ausdrücklichem Einschalten** (DEC-29) — LEG-09; DSGVO lit. b | nur mit Schalter | R-41/R-42 (Fristen `07` §6) — LEG-10 | Löschung lokal; Widerruf → Quarantäne/Löschung (`07` §7) | Betreiber (Gestaltung) / Nutzer | — |
| PA-09 | Backup/Wiederherstellung | alle | alle Kopien | Backup-Speicher (S3) | lit. f (Datensicherheit, Art. 32) — INFERRED | ja | ≤ 35 d Dumps (DEC-26) | Löschung wird nach Restore erneut angewendet (`09` §6) — LEG-11 | Betreiber | S3-Anbieter als Unter-AV |
| PA-10 | Sensorik | Haushaltsmitglieder, Beschäftigte | SENS, LOC | Mitglieder | lit. b (VERIFIED_SPEC NFR-011 R-14) | — | R-14/R-15 (nicht klassifizierungsabhängig umgesetzt) | — | Mandant | Betreiber |
| PA-11 | Mandantenexport/-import | Mitglieder | alle Mandantendaten inkl. GPS | Mandant (Download) | lit. b (Portabilität des Mandanten) — INFERRED, LEG-13 | — | R-05 72 h | — | Mandant | Betreiber |
| PA-12 | Support/Administration | alle | IDN, AUD | Plattform-Admin | lit. f — INFERRED | Mitgliederlisten für INV-1, Löschvorschau | — | — | Betreiber | — |

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
| KCanG § 26 Abs. 1 Nr. 5 lit. b (L-05) | durchschnittlicher THC-Gehalt des **weitergegebenen** Cannabis | `quality_assessments` — **[?]** ob ein THC-Feld existiert (V-11); Weitergabe-Entität existiert nicht | Anbauvereinigung | 5 Jahre | R-16 nur, falls das Feld den THC-Wert der weitergegebenen Charge belegt |
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

### 4.3 LIA-3 — Name ehemaliger Mitglieder für N Tage

1. Übergabe-Zweck; 2. kurz (Saisonübergabe); 3. abnehmende Erwartung; Maßnahmen: N ≤ 365, Default 90, kein
Filter/Export, Transparenz. LEG-06.

### 4.4 LIA-4 — Sentry

[VERIFIED_SPEC REQ-025 §9] „rechtlich zu bestätigen“; unverändert; LEG-16.

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
- **PRIV-407** Keine Dauer-/Geschwindigkeitsmessung über `performed_at` hinaus.
- **PRIV-414** [PROPOSED] Der Hinweistext zu `attribution_visibility` (PRIV-301) MUSS die Evidenz nennen:
  „§ 26 BDSG gilt nur für Beschäftigte i. S. v. § 26 Abs. 8; für Vereinsmitglieder gilt er nicht“ (L-09).

---

## 6. Zweckbindung (Art. 5 Abs. 1 lit. b) — Prüfung der Flüsse

| Fluss | Ursprünglicher Zweck | Zweitnutzung | Bewertung |
|-------|----------------------|--------------|-----------|
| `treatment_applications.applied_by_key` → `care_events.performed_by_user_key` | Pflichtaufzeichnung (PA-05) | Beethistorie, Filter, CSV (PA-04) | LIA-2 (LEG-07); Pseudonyme nie (PRIV-205); Schalter DA-02 |
| `care_events.performed_by_user_key` (Erledigung) → `harvest_batches.harvested_by_key` | Protokoll | Ernteaufzeichnung | gleiche Tatsache; `harvested_by_key` ist **keine** KCanG-Pflichtangabe (§3.2) → kein lit.-c-Zweck entsteht |
| `bed_templates.name` → `locations.name` → `garden_plan_audit.summary` → Exporte | Plan | Export/Druck | Inhalt; Datenlinie (PRIV-230) |
| `users.display_name` → Darstellungen | Identifikation | Aktivitätsanzeige | LIA-1 |
| `security_audit_log` | Art. 32 | — | keine Zweitnutzung (REQ-049) |
| Gerätecache | Offline-Lesen | — | minimiert (VERIFIED_CODE `storedProjection`) |

---

## 7. Informationspflichten (Art. 13/14)

**PRIV-408** Die Datenschutzinformation des Betreibers (Plattform) und die **Vorlage** für die Information des
Mandanten (Art. 13 gegenüber Mitgliedern, Art. 14 gegenüber in Labels genannten Dritten und abgebildeten Personen)
MÜSSEN enthalten: Pflegeprotokoll und Zurechnung, Sichtbarkeitsregel des Mandanten, Unterdrückung ehemaliger
Mitglieder, Prüfwarteschlange, Gerätespeicher (REQ-025 §10), Backups (≤ 35 d, Replay), Rechtsgrundlagen je PA
(§2). Wortlaute: LEG-12 (E16).

---

## 8. Aufbewahrungsmatrix (Kurzform; Evidenz je Zeile)

| # | Kategorie | Frist | Auslöser | Grundlage (Evidenz) | Status |
|---|-----------|-------|----------|---------------------|--------|
| R-01 | geschlossene Konten | 90 d | Antrag | lit. c (Art. 17) — INFERRED | VERIFIED_CODE |
| R-03 | IP in Refresh-Tokens | 7 d | Ausstellung | lit. f — VERIFIED_SPEC REQ-023 | VERIFIED_CODE |
| R-04/04a | Einwilligungen (+IP) | 3 J. nach Widerruf / 7 d | Widerruf | Art. 7 Abs. 1 — VERIFIED_SPEC | VERIFIED_CODE |
| R-06 | `erasure_requests` | 3 J. | Abschluss | Art. 5 Abs. 2 — INFERRED | VERIFIED_CODE (Docstring „one year“ falsch, W-11) |
| R-16 | Ernte-Pflichtfelder (§3.2) | ≥ 5 J. | `harvest_date` | lit. c **nur `kcang_association`** (L-05) | VERIFIED_CODE (Collection-weit → PRIV-410/411) |
| R-17 | PflSchG-Pflichtfelder | 3 J. (VERIFIED_SPEC) ab **1.1. Folgejahr** (L-01) | Aufzeichnung | lit. c nur `pflschg_professional` | PRIV-412 Korrektur |
| R-18 | Inspektionen | 3 J. | `inspected_at` | **ohne Beleg** (PRIV-413) | LEGAL_REVIEW_REQUIRED |
| R-25 | `care_events` | 5 J. | `performed_at` | Inhalt lit. b, Zurechnung lit. f (DA-02); „Art. 17(3)“ in NFR-011 ist zu korrigieren | VERIFIED_CODE |
| R-26 | `garden_plan_audit` | 365 d | `at` | lit. f — INFERRED | VERIFIED_CODE; Akteur → Marker (DEC-16) |
| R-38 | `security_audit_log` | 730 d | `created_at` | Art. 32 — VERIFIED_SPEC | VERIFIED_CODE |
| R-41/R-42 | Gerätecache/-puffer | 15 min / 90 d, 30 d (PROPOSED) | TTL/Erfassung | TDDDG § 25 Abs. 2 Nr. 2 (L-11) mit Schalter | PROPOSED, LEG-09/10 |
| R-43 | `privacy_review_items` | 3 J. nach Entscheidung | Entscheidung | Art. 5 Abs. 2 | PROPOSED |
| R-44 | Datenschutzaktionen im Security-Audit | 730 d | `created_at` | Art. 5 Abs. 2 | PROPOSED |
| R-45 | **Löschungs-Spiegel** (`erasure_mirror`: Tombstone-Liste, keine Rohschlüssel; DEC-26) | wie R-06 (3 J.) | Abschluss | Art. 17 Durchsetzung nach Restore | PROPOSED, LEG-11 |
| R-46 | Gieß-/Dünge-/Tankprotokolle | 5 J. (an R-25 angleichen) | Zeitpunkt | lit. b | PROPOSED |
| R-47 | geschlossene Aufgaben/Kommentare | 2 J. | Abschluss | lit. b | PROPOSED, DSB |
| R-48 | Benachrichtigungen | 90 d gelesen / 180 d ungelesen | `read_at`/`created_at` | lit. b | PROPOSED, DSB |
| — | Backup-Dumps | ≤ 35 d | Erstellung | lit. f (Art. 32) | PROPOSED, LEG-11 |

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
| Backfill kopiert Zurechnung (LIA-2) | Bestand | provisorisch (Prüfdatum = LEG-07) | Schalter `PRIVACY_BACKFILL_COPIES_PERFORMER` (Default = Bestand) |
| `attribution_visibility`-Defaults (DA-04) | einschränkend | ja | Code/Setting |
| E-Mail nur `management` (PRIV-305) | einschränkend | ja (Breaking Change dokumentiert) | Code |
| Prüfwarteschlange, Entdeckung (DA-05) | schutzverstärkend | ja | Code |
| Auto-Schwärzung nach SLA (DA-05) | datenvernichtend (fremde Historie) | nein (bis LEG-08) | Flag `PRIVACY_REVIEW_AUTO_REDACT_ON_SLA` (Default aus) |
| Kommerzieller SaaS-Betrieb mit gewerblichen Mandanten | Betriebsmodell | `deployment_allowed` nein (bis LEG-01, LEG-05, LEG-12: AVV, Information, DSFA-Entscheidung) | Betreiber-Checkliste (DEC-32) |
| Backups aktivieren | Infrastruktur | `deployment_allowed` nein (bis Spiegel + Restore-Replay vorhanden; LEG-11 Prüfdatum) | Helm `backup.enabled` nur mit `privacy.mirror.enabled` (DEC-26) |
