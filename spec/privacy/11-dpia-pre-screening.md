# SPEC-11 — DSFA-Vorprüfung (Art. 35 DSGVO)

```
Paket: spec/privacy · Version 1.2 · 2026-11-22 · Gemessen gegen: develop 007a4ea90 (Audit 2026-11-22)
(v1.1: develop 24d1c2988; Nachtrag #2839 develop 343afbb97)
Status: technische Vorprüfung (Schwellwertanalyse) der Engineering-Seite. Sie ist KEINE DSFA und
KEINE Rechtsberatung. Sie liefert dem DSB die Fakten, die Methodik und das Risikoinventar, um zu
entscheiden, ob eine DSFA erforderlich ist, und um sie zu erstellen.
Änderung v1.1: §4 ersetzt die Zählregel durch eine begründete Bewertung (DA-08); Evidenz L-16/L-17;
RISK-19/20 neu; Produktionsgate.
Änderungen 1.2: Vorgänge O11–O14 (Aufgaben-Leistungsdaten, Aktorik, Weitergabe per Service-Account/MCP, KI/externe
Dienste); RISK-21…24 neu; RISK-01/09/15 auf Ist-Stand korrigiert (RISK-15: keine GPS-Rundung im Archiv); WP248-Kriterien
1 und 8 neu bewertet; §4.3 je Betriebsmodell fortgeschrieben inkl. „selbst gehostet, gewerblich“ (LEG-48) und Art. 36;
W-10 und Gate-Lücke (DEC-32 nur SaaS, Klassifizierung inert) vermerkt.
```

---

## 1. Basisfakten (VERIFIED_SPEC / VERIFIED_CODE)

- Keine DSFA im Repository; NFR-001 §6.7 verlangt eine für Sensordaten vor Produktivsetzung; ADR-003 nennt die
  DSFA-Frage offen; `docs/de/user-guide/privacy.md` behauptet eine durchgeführte DSFA (Widerspruch W-10).
  **Audit 2026-11-22:** W-10 ist weiterhin offen (`docs/de/user-guide/privacy.md:488–490` „Für solche Daten wurde eine
  DSFA durchgeführt“) — aktive Falschinformation gegenüber Betroffenen (Art. 5 Abs. 1 lit. a), Korrektur PRA-0.05 (P1);
  zusätzlich steht NFR-001 §6.7 (MUSS) gegen das Ergebnis „keine DSFA“ für Hobby in §4.3 (`14`).
- DEC-32 sperrt nur „kommerziellen SaaS-Betrieb“ organisatorisch; gewerbliche Mandanten sind technisch **nicht
  erkennbar**, weil `organization_kind`/`record_keeping` weder setzbar noch gelesen werden (LEG-30, `05`). Der selbst
  hostende Arbeitgeber erhält keinen Hinweis auf DSFA oder § 87 BetrVG (LEG-48).
- Kein Verzeichnis von Verarbeitungstätigkeiten (Art. 30); REQ-025 §8 / NFR-011 §8 verlegen es außerhalb der Software.
  `06` §2 liefert die technische Zuarbeit (PA-01…PA-12).
- REQ-056 O-03, REQ-053 SR-020, GP-FR-146 und das REQ-055-Review (S-018) verweisen auf eine nicht existierende DSFA.
- Rollen der Verantwortlichen: DA-01 (LEG-01). Die Vorprüfung ist aus der Perspektive „Mandant = Verantwortlicher für
  Mitgliederdaten, Betreiber = Auftragsverarbeiter; Betreiber = Verantwortlicher für PA-01/02/07a/08/09/12“ geschrieben.

---

## 2. Verarbeitungsvorgänge im Geltungsbereich

| # | Vorgang | Betroffene | Daten | Wo | PA (`06` §2) |
|---|---------|------------|-------|----|--------------|
| O1 | Historische Aktivitätserfassung mit Zurechnung und Zeitstempel | Mitglieder (Beschäftigte, Ehrenamtliche, Vereins-/Haushaltsmitglieder), in Labels genannte Dritte | wer/was/wann/wo; Freitext | `care_events`, Pflichtaufzeichnungen, `garden_plan_audit`, Aufgaben | PA-04, PA-05 |
| O2 | Zugriff Lead/Management auf Mitgliederaktivität (Personenfilter, CSV mit Namen, Beethistorie) | Mitglieder | Aktivität je Person | `GET /care-events`, CSV | PA-04 |
| O3 | Überwachungspotenzial in gewerblichen Mandanten | Beschäftigte | O1 + O2 | dasselbe | PA-04 |
| O4 | Freitext, der Personen nennt; Fotos | Mitglieder, Dritte, Abgebildete | Namen, Beschreibungen, Fotos | ~25 Felder (`02` §3) | PA-06 |
| O5 | Lange Aufbewahrung (5 J. Pflegeereignisse, 3–5 J. Pflichtfelder, 730 d Audit, Pseudonyme über das Konto hinaus) | ehemalige Mitglieder, gelöschte Konten | pseudonymisierte Zurechnung, Freitext | Aufbewahrungs-Beats | PA-04, PA-05 |
| O6 | Geteilte Geräte und Offline-Speicher | Gerätenutzer | ungesendete Notizen/Fotos, Schlüssel | Browser | PA-08 |
| O7 | Mandantenübergreifende Verarbeitung (eine Installation, viele Verantwortliche; Admin-Zugriff auf Verzeichnisse und Audit; Archive) | alle | Verzeichnisdaten, GPS | Plattform, `/admin/platform/*`, REQ-056 | PA-03, PA-11, PA-12 |
| O8 | Abgeleitete Datensätze (Backfill, Plan-Audit-Kopien, Vorlagen → Beete, Import-Snapshots) | Mitglieder | Kopien von Zurechnung und Inhalt | v0104, Konsistenz-Job, `place_template` | PA-04 |
| O9 | Sensordaten mit Anwesenheitsbezug (CO₂, Bewegung, Overrides) — NFR-001 §6.7 | Haushaltsmitglieder, Beschäftigte | Zeitreihen | TimescaleDB, `manual_overrides` | PA-10 |
| O10 | Standortdaten (GPS = Wohnadresse bei persönlichen Gärten) | Kontoinhaber | Koordinaten | `sites.gps_coordinates`, Export, Archiv, **ungerundet an Wetterdienste** (`06` §2.4) | PA-11, PA-16 |
| O11 (neu) | Aufgaben-Leistungsdaten je Person (Zuständige, Start, Ende, Ist-Dauer, Qualitäts-/Schwierigkeitsbewertung), für alle Mitglieder lesbar | Mitglieder, Beschäftigte | `actual_duration_minutes`, `quality_rating`, `difficulty_rating`, `started_at`, roher `assigned_to_user_key` | `task.py:181–205`, `task_service.py:1469–1475, 1720–1730` (LEG-28) | PA-04a |
| O12 (neu) | Aktorik-Schaltprotokoll mit Kontoschlüssel, ohne Löschung, Auskunft, Frist | Haushaltsmitglieder, Beschäftigte | `control_events.triggered_by_user` (Anwesenheit, Arbeitszeit ableitbar) | `domain/models/actuator.py:227` (LEG-29) | PA-10 |
| O13 (neu) | Weitergabe von Pflegeprotokoll, Aufgaben, Tagebuch, Fotos per Service-Account/API-Key/MCP an Home Assistant oder KI-Clients; Personenbezug geht in fremde Historien (HA-Recorder, Chat-Verläufe) ohne Frist über | Mitglieder, Dritte in Freitext/Fotos | Protokolle, Freitext, Fotos; `created_by` roh (`mcp_server/tools/diary.py:510`) | MCP, API-Keys (LEG-48, LEG-51, LEG-52) | PA-17 |
| O14 (neu) | KI-Funktionen und externe Dienste (Cloud-LLM, Erkennung, Wetter) mit möglicher Drittlandübermittlung | Kontoinhaber, Mitglieder, Abgebildete | Prompts mit Freitext, Fotos, Koordinaten | Knowledge-Service, `data_access/external/*` (LEG-31, LEG-33) | PA-13, PA-14, PA-16 |

Besondere Kategorien (Art. 9): konstruktionsbedingt keine; Cannabis-Kontext (RISK-18) und Tagebuchfreitext können
indirekt sensible Inhalte tragen (LEGAL_REVIEW_REQUIRED). Kinder: keine Altersprüfung (LEGAL_REVIEW_REQUIRED).

---

## 3. Risikoregister

Skala niedrig/mittel/hoch, Einschätzung der Engineering-Seite; der DSB kalibriert.

| R | Bedrohungsszenario | Betroffene | Eintrittsw. | Schwere | Bestehende Maßnahmen [VERIFIED_CODE] | Erforderliche Maßnahmen (Paket) | Restrisiko |
|---|--------------------|------------|-------------|---------|--------------------------------------|----------------------------------|------------|
| RISK-01 | Aktivitätsprofiling (Anwesenheitsmuster aus Zeitstempeln) | Mitglieder | mittel | mittel | Personenfilter nur Lead/Management; kein Statistik-Endpunkt (Audit 2026-11-22: `PARTIALLY_CONFIRMED` — Einzeldaten mit Dauer/Bewertung je Aufgabe machen Aggregation clientseitig trivial, RISK-21); CSV ≤ 50 000 | `attribution_visibility` (PRIV-300, Klassen-Defaults DA-04); CSV-Namen nur Leads + Audit (PRIV-307/308); Aggregationsverbot (PRIV-403); Unterdrückung ehemaliger Mitglieder (PRIV-112) | niedrig–mittel |
| RISK-02 | Leistungsbewertung Beschäftigter durch Filter/Export (DSK-Liste Nr. 8, L-17) | Beschäftigte | mittel (gewerblich) | hoch | keine spezifischen | PRIV-403…407, 414; Default `leads_and_self` (DA-04); Betriebsrats-Mustertext | mittel (Export außerhalb der Plattform nicht kontrollierbar) |
| RISK-03 | Gelöschte Person über Freitext/Beschriftungen/Dateinamen/Namen identifizierbar | gelöschte Konten | hoch | mittel–hoch | Marker auf Kontofeldern; manuelle Schwärzung nur Pflegeereignisse | Zustandsautomat mit vollständiger Entdeckung (DA-05), generische Schwärzung, `original_filename` geleert, Alt-Namen gelistet, Eskalation/Auto-Schwärzung (Flag) | niedrig–mittel (abhängig von Lead-Entscheidungen bzw. Flag, LEG-08) |
| RISK-04 | Pseudonym in nicht gesetzliche Speicher kopiert (#2770) | gelöschte Konten | mittel (eingetreten; für `care_events` **behoben #2839**) | mittel | `account_of` → Marker, v0107 (VERIFIED_CODE) | PRIV-204…207 für die übrigen Kopierstellen, v0109, Konsistenz-Beat | niedrig |
| RISK-05 | Ehemaliges Mitglied unbegrenzt namentlich; Art.-15-Lücke für verlassene Mandanten | ehemalige Mitglieder | hoch | mittel | Security-Audit | PRIV-112/115/116; LEG-06(b) | niedrig–mittel |
| RISK-06 | Statutory-Aufbewahrung ohne Pflicht (Hobby-Mandanten; erntende Person als Pseudonym 5 J.) | gelöschte Konten | hoch | mittel | Tombstone | Profil + feldgenaue Zuordnung (`06` §3.2), PRIV-409…411 (Flag) | niedrig nach LEG-03/17 |
| RISK-07 | Pflichtaufzeichnung geschwächt (Anwender-Name geleert; Fristbeginn zu früh) | Mandant (Compliance) | mittel | mittel | Tombstone-Verknüpfbarkeit | PRIV-412 (Fristbeginn 1.1. Folgejahr), LEG-04 (Name), PRIV-413 (Hilfsdokumentation) | offen |
| RISK-08 | Geschlossenes Konto 90 d sichtbar | Antragsteller | hoch | niedrig–mittel | `is_active=false` | PRIV-104 | niedrig |
| RISK-09 | Geteiltes Gerät legt Notizen/Fotos/Identität offen; Konto anderswo gelöscht; Keys überleben Logout; Logout-Wipe nicht abgewartet | Nutzer geteilter Geräte | hoch | mittel | Namespace; Logout-Dialog; TTL 15 min (nur Ausliefern). Audit 2026-11-22: ohne Opt-in, Fristen 365/90 d hart kodiert, SW-Cache unprojiziert und ohne physische Frist, „Angemeldet bleiben“ 30 d möglich (`07` §1, LEG-09/10/27/36/37) | DEC-29 Schalter + Übergang; PRIV-511…526; Szenarienmatrix `07` §8a | niedrig–mittel; LEG-09/10 |
| RISK-10 | Restore erzeugt gelöschte Personen neu | gelöschte Konten | niedrig heute → hoch bei Backups | hoch | keine | Löschungs-Spiegel + Replay (`09` §6, DEC-26); Residue-Scan im Restore; Lücke zwischen Dump und Spiegelverlust dokumentiert | niedrig nach Umsetzung; LEG-11 |
| RISK-11 | Betreiber-Überreichweite (Admin-Verzeichnisse; REQ-023 „Backup → Cross-Tenant Read“) | alle | niedrig | hoch | `require_platform_admin`; P4 | PRIV-311; Zähler-Endpunkt; Spec-Korrektur | niedrig |
| RISK-12 | Mitglieder-E-Mails für alle | Mitglieder | hoch | niedrig–mittel | — | PRIV-305; LEG-14 | niedrig |
| RISK-13 | Zweckausweitung durch Ableitung (Backfill, Audit-Kopien, Vorlagenexport) | Mitglieder | mittel | niedrig–mittel | GP-NFR-051 | Lineage-Registry + Laufzeit-Provenienz (`02` §5a), `carry_account_reference`, Schalter DA-02 | niedrig |
| RISK-14 | Anwesenheitsrückschluss aus Sensoren/Overrides (NFR-001 §6.7) | Haushaltsmitglieder | mittel | mittel–hoch | Aufbewahrungsstufen; DP-002 | außerhalb dieses Pakets; Sensor-DSFA fällig | offen |
| RISK-15 | Standortdaten verlassen die Installation (Archiv, Bundle, **Wetterdienste**) | Kontoinhaber | **mittel** (Wetter: regelmäßig) | mittel | 72 h; Step-up. **Korrektur (Audit 2026-11-22):** keine Rundung — `sites.gps_coordinates` liegt ungerundet im Archiv (`06` §2.5), und DP-002 ist für Wetterdienste nicht umgesetzt (`06` §2.4) | Koordinaten vor Wetterdiensten vergröbern (PRA-2.14); Entscheidung zur Rundung im Archiv (LEG-13); Plattform-Export nur mit `reason` (PRA-2.11) | mittel; niedrig–mittel nach PRA-2.14 |
| RISK-16 | Unvollständige Datenschutzoperationen unbemerkt | gelöschte Konten | mittel | mittel | Retry/Backoff; Logs | Metriken, Endpunkt, Stale-Alert (PRIV-110, 607), Zustandsautomat `ERASURE_COMPLETED` | niedrig |
| RISK-17 | Dritte ohne Information genannt (Labels, Fotos) | Nicht-Nutzer | mittel | niedrig–mittel | UI-Hinweis (SR-006) | Prüffeld; Art.-14-Vorlage (PRIV-408) | niedrig–mittel |
| RISK-18 | Cannabis-Kontext (Anbauvereinigung) als sensibler Kontext | Vereinsmitglieder | niedrig–mittel | hoch | Statutory-Aufbewahrung; Isolation | `kcang_association` macht die Klasse explizit; DSB prüft Art.-9-Nähe | offen |
| **RISK-19** (neu) | Mandantenübergreifende Verknüpfbarkeit eines gelöschten Kontos über den instanzweiten Tombstone (zwei Archive/Mandanten genügen) | gelöschte Konten | niedrig–mittel | mittel | Zugriff nur Leads je Mandant | DEC-25 (mandantengebundene HMAC-Pseudonyme für neue Zeilen); Archiv-Hinweis LEG-13 | niedrig nach DEC-25 |
| **RISK-20** (neu) | Kompromittierung des Tombstone-Salts erlaubt Reidentifikation aller Pseudonyme; Rotation nicht heilend | gelöschte Konten | niedrig | hoch | Secret in Kubernetes | Zugriffsbeschränkung, Secret-Rotation **nicht** möglich (`09` §7) → Betriebsdoku, Monitoring des Secret-Zugriffs | mittel (strukturell) |
| **RISK-21** (neu, Audit 2026-11-22) | Leistungsdaten in Aufgaben (Dauer, Start/Ende, Bewertungen, Zuständige) für alle Mitglieder lesbar → Leistungsbewertung, sozialer Druck (O11, LEG-28) | Beschäftigte, Mitglieder | hoch (gewerblich) | hoch | keine; widerspricht PRIV-407 | nur Person selbst und Leads; in `commercial` aus; Frist 90 d (Q-DSB-21); `assigned_to` als `PersonRef`; Aggregationsverbot TA-309 (PRA-2.06) | mittel nach Maßnahme; **hoch ohne** |
| **RISK-22** (neu) | Aktorikereignisse mit Kontoschlüssel ohne Löschung/Frist/Auskunft (O12, LEG-29) | Haushaltsmitglieder, Beschäftigte | mittel | mittel | keine (`manual_overrides.created_by` → Marker, `control_events` nicht) | Marker bei Kontolöschung, Art.-15-Quelle, Frist 90 d (PRA-2.07; `06` R-62) | niedrig |
| **RISK-23** (neu) | Weitergabe personenbezogener Protokolle an Drittsysteme per Service-Account/MCP; fremde Historien ohne Frist (O13, LEG-48/51) | Mitglieder, Dritte | mittel | mittel | Schlüssel nie mehr als Weboberfläche (`mcp_server/auth.py:91–167`) | MCP-Freitext nur eigene/markierte/Leitung, `untrusted_content`, `read_only`-Default (PRA-2.10); Doku „Für Betriebe“ (PRA-3.04) | mittel (außerhalb der Plattform nicht kontrollierbar) |
| **RISK-24** (neu) | Klassifizierung nicht setzbar → Schutzdefaults (DA-04) und DSFA-Gate wirkungslos (LEG-30) | Beschäftigte | hoch (gewerblich) | hoch | keine (Felder ohne Leser) | Klassifizierung bei Anlage verpflichtend, einziger Leser `resolve_tenant_privacy_profile` (PRA-1.02); Bestätigung „DSFA durchgeführt / Betriebsrat beteiligt / nicht erforderlich“ bei `commercial` (PRA-3.04) | niedrig nach Umsetzung |

---

## 4. Ist eine DSFA erforderlich? — Methodik und Bewertung (DA-08)

### 4.1 Methodik

1. **Rechtlicher Maßstab** (Bezug, L-12): Art. 35 Abs. 1 (voraussichtlich hohes Risiko, insbesondere bei neuen
   Technologien), Abs. 3 lit. a–c (Regelbeispiele), Abs. 4 (Listen der Aufsichtsbehörden), Abs. 2 (Rat des DSB),
   Art. 36 (vorherige Konsultation bei hohem Restrisiko).
2. **Leitlinie WP248 rev.01** (L-16, VERIFIED_LEGAL): neun Kriterien; die Aussage „in most cases … two criteria
   would require a DPIA“ ist **Faustregel**, kein Schwellenwert — die Leitlinie sagt zugleich, dass **ein** Kriterium
   genügen kann und dass mehr Kriterien das Risiko wahrscheinlicher machen. Daher wird je Kriterium begründet, ob und
   wie stark es erfüllt ist, und anschließend der **Gesamtkontext** je Betriebsmodell bewertet.
3. **DSK-Muss-Liste** (L-17, VERIFIED_LEGAL): Abgleich mit Nr. 8 (Verhalten von Beschäftigten, zur Bewertung
   einsetzbar); die Liste ist nicht abschließend.
4. **Kombinationsbetrachtung**: Aktivitätserfassung × Managementzugriff × Beschäftigtenkontext × Freitext × lange
   Aufbewahrung × Offline-Speicher × Mehrmandantenfähigkeit × Datenverknüpfung × Ableitungen.
5. **Ergebnis je Betriebsmodell** mit Maßnahmen, Restrisiko und Entscheidungsbegründung.

### 4.2 Bewertung je Kriterium (WP248)

| Kriterium | Erfüllt? | Begründung (Evidenz) |
|-----------|----------|----------------------|
| 1 Bewertung/Scoring | **gewerblich erfüllt** (Audit 2026-11-22; v1.1: „teilweise“): Das System bewertet nicht selbst, speichert aber Ist-Dauer und Qualitätsbewertung je Person und Aufgabe (O11) und ist über Personenfilter und CSV zur Bewertung einsetzbar | VERIFIED_CODE Filter/CSV, `task.py:181–205`; DSK Nr. 8 „eingesetzt werden können“ |
| 2 Automatisierte Entscheidung mit Rechtswirkung | nein | keine Automatik mit Rechtsfolge |
| 3 Systematische Überwachung | **teilweise**, gewerblich **erfüllt**: fortlaufende Protokollierung aller Pflegehandlungen mit Person und Zeit; Aufgaben-Zeiten (O11); Schaltprotokoll (O12); Sensoren mit Anwesenheitsbezug (O9) | VERIFIED_CODE |
| 4 Sensible/höchstpersönliche Daten | **teilweise**: Anwesenheitsmuster (O9), Wohnadresse (O10), Cannabis-Kontext (RISK-18) | INFERRED |
| 5 Große Reichweite | nein (heute); bei kommerziellem SaaS zu prüfen | — |
| 6 Abgleich/Zusammenführung | **teilweise**: Ableitungen über Collections (O8), instanzweiter Tombstone (RISK-19) | VERIFIED_CODE |
| 7 Schutzbedürftige Betroffene | **ja bei Beschäftigten** („employees“ ausdrücklich, L-16); nein bei Haushalt/Verein | VERIFIED_LEGAL |
| 8 Innovative Nutzung | **zu prüfen** (Audit 2026-11-22; v1.1: „nein, außerhalb“): KI und MCP sind keine Randfunktion — in Gemeinschaftsgärten und Betrieben gehen Freitext und Fotos Dritter an externe Modelle (O13, O14); das Einwilligungs-Gate prüft am falschen Provider (LEG-31) | INFERRED; Q-DSB-08 |
| 9 Verhindert Rechtsausübung | nein | — |
| DSK Nr. 8 | **einschlägig, sobald „umfangreich“** in einem Betrieb mit Beschäftigten | L-17 |

### 4.3 Ergebnis je Betriebsmodell (fortgeschrieben, Audit 2026-11-22)

Fortschreibung nach Strang E Lieferung (d) des Audits 2026-11-22 (LEG-12, LEG-48; Umsetzung PRA-3.04). Die
DSFA-Pflicht trifft den **Verantwortlichen** — im AV-Modell den Mandanten (Arbeitgeber), beim Selbsthosting den
Betreiber, der zugleich Arbeitgeber ist; der Anbieter liefert die Eingaben (Art. 28 Abs. 3 lit. f; Rollen `06` §1a).
Spalte „v1.1“ zeigt die Bewertung der Vorfassung, wo sie abweicht.

| Betriebsmodell | WP248-Kriterien (L-16) | DSK-Liste (L-17) | DSFA erforderlich? (Engineering-Vorschlag) | Vertieft zu prüfende Risiken | Fehlende Informationen | Art. 36? | v1.1 |
|---|---|---|---|---|---|---|---|
| Selbst gehostet, Haushalt/Hobby (persönliche Mandanten) | 3 nur mit Sensorik/Aktorik; sonst keines | — | **nein**; bei Präsenzsensorik oder Aktorik-Protokoll Sensor-DSFA nach NFR-001 §6.7 empfohlen; im Haushalt ggf. Haushaltsausnahme Art. 2 Abs. 2 lit. c (Auslegung) | RISK-14, RISK-22 | ob Bewegungs-/CO₂-Sensoren gebunden sind | nein | „keine DSFA“ (bestätigt) |
| SaaS, Gemeinschaftsgarten/Verein (Ehrenamt, Mitglieder) | 3 teilweise, 6 teilweise, 7 nein (L-09) | Nr. 8 nicht (keine Beschäftigten) | **empfohlen**, nicht zwingend — Bewertung nach Umsetzung von PRIV-307/112 und PRA-2.06; **ohne** diese Maßnahmen tendiert die Kombination (namentliche Zurechnung für alle + Aufgaben-Leistungsdaten + 5 J.) zu „voraussichtlich hoch“; DSB-Rat einholen | RISK-01, RISK-05, RISK-17, RISK-21 (sozialer Druck) | Größe der Vereine; Minderjährige (keine Altersprüfung) | nein | empfohlen |
| SaaS, gewerblicher Mandant mit Beschäftigten | 1 **erfüllt** (O11), 3 erfüllt, 7 erfüllt, 6 teilweise | Nr. 8 einschlägig, sobald „umfangreich“ (`LEGAL_REVIEW_REQUIRED`) | **ja** (Mandant als Verantwortlicher; Anbieter liefert Baustein „Beschäftigte“) vor Aufnahme dieses Betriebsmodells; DSB-Beteiligung (Art. 35 Abs. 2); `deployment_allowed` nein bis LEG-01/05/12 **und** LEG-30 | RISK-02, RISK-21, RISK-22, RISK-23, RISK-24 | Betriebsvereinbarung, Mitarbeiterzahl, Nutzung von Export/Filter | möglich, falls RISK-21 ohne Maßnahme bleibt (Restrisiko hoch); nach Maßnahmen voraussichtlich nein | erforderlich (Kriterium 1 nur „teilweise“) |
| **Selbst gehostet, gewerblich** (Gärtnerei, Betrieb; Betreiber = Arbeitgeber = Verantwortlicher) — neu (LEG-48) | wie SaaS gewerblich | Nr. 8 | **ja**; **kein DEC-32-Gate greift** → Hinweis und Bestätigung müssen an die Klassifizierung `commercial` gekoppelt sein, nicht an das Hosting-Modell (PRA-3.04 nach PRA-1.02); Doku „Für Betriebe“ mit DSFA- und Betriebsrat-Hinweis (PRIV-406) | wie SaaS gewerblich | wie SaaS gewerblich | wie SaaS gewerblich | fehlte |
| Anbauvereinigung (KCanG), SaaS oder selbst gehostet | 4 teilweise (Cannabiskontext), 3, 7 nur für Angestellte der Vereinigung | Nr. 8 für Angestellte | **empfohlen**, bei Angestellten **erforderlich**; DSB prüft Art.-9-Nähe (RISK-18, Q-LAW-11) | RISK-18, RISK-06, RISK-21 | ob Angestellte vorhanden; Mitgliederzahl | offen | empfohlen |
| Jedes Modell mit Präsenzsensorik / Aktorik-Protokoll | 3, 4 | — (Nr. 8 bei Beschäftigten) | **ja** (NFR-001 §6.7, bereits spezifiziert); als eigener Abschnitt mit Bedingung „Präsenzsensorik/Aktorik-Protokoll“ (PRA-3.04 Teil 4) | RISK-14, RISK-22 | gebundene Sensortypen (`metric_type` frei, `ha_entity_id` beliebig) | nach DSFA | erforderlich |
| Jedes Modell mit Weitergabe per Service-Account/MCP oder Cloud-KI (O13, O14) — neu | 8 zu prüfen, 6 teilweise; bei Beschäftigten zusätzlich 7 | — | in die DSFA des jeweiligen Modells aufnehmen (eigener Risikoabschnitt RISK-23, Drittland `06` §2.3); keine eigenständige Pflicht festgestellt | RISK-23; LEG-31 (Gate) | welche Agenten/Drittsysteme angebunden sind | — | fehlte („KI außerhalb“) |

**Würdigung (Audit 2026-11-22, Auslegung):** Die Abkehr von der Zählregel (DA-08) ist leitlinienkonform (L-16). Mit den
Aufgaben-Leistungsfeldern ist Kriterium 1 in gewerblichen Mandanten objektiv erfüllt; Kriterium 3 und 7 ebenso — die
DSFA-Pflicht gewerblich ist **bestätigt und verschärft**. Das Gate ist ohne setzbare Klassifizierung (LEG-30, RISK-24)
technisch nicht durchsetzbar.

**Art. 36 (vorherige Konsultation) — korrigiert:** Die Fassung 1.1 hielt sie „nach heutiger Einschätzung nicht für
erforderlich, weil die Maßnahmen das Restrisiko unter ‚hoch‘ bringen“. Diese Aussage stützt sich auf **nicht gebaute**
Maßnahmen (PRIV-300, PRIV-307, PRIV-403, PRA-2.06, PRA-1.02); für den **Ist-Zustand** ist sie nicht belegt. Einschätzung:
Für gewerbliche Mandanten mit Beschäftigten ist eine Konsultation **möglich**, solange RISK-21 ohne Maßnahme bleibt
(Restrisiko hoch); nach Umsetzung der Maßnahmen voraussichtlich nicht erforderlich. Für alle anderen Modelle nach
heutigem Stand nicht erforderlich. Die Entscheidung trifft der Verantwortliche mit dem DSB nach der DSFA
(`LEGAL_REVIEW_REQUIRED`, Q-DSB-08 in `16`).

**Diese Vorprüfung ersetzt keine DSFA.** Produktionsgate: `deployment_allowed = nein` für „SaaS mit gewerblichen
Mandanten“ bis zur DSFA-Entscheidung (DEC-32, LEG-12). Für „selbst gehostet, gewerblich“ gibt es kein Deployment-Gate
des Projekts; die Schutzwirkung entsteht nur über die Klassifizierung (Hinweis und auditierte Bestätigung „DSFA
durchgeführt / Betriebsrat beteiligt / nicht erforderlich (Begründung)“ bei `commercial`, PRA-3.04).

---

## 5. Eingaben für die DSFA aus diesem Paket

| DSFA-Abschnitt | Quelle |
|----------------|--------|
| Systematische Beschreibung | `01` §3/§6, `02` §3, `06` §2 (PA) |
| Erforderlichkeit und Verhältnismäßigkeit | `06` §4 LIA-1…3, `05` §3, DA-02/DA-04 |
| Rechtsgrundlagen, Aufbewahrung | `06` §2, §3, §8; `13` |
| Risiken und Maßnahmen | §3; `03`, `04`, `07` |
| Betroffenenrechte | `03` §2, `04` §5 (Zustandsautomat), REQ-025 |
| Auftragsverarbeiter/Empfänger | `06` §1 Rollenmatrix, §1a Rollen je Betriebsmodell, §2.3 Empfänger/Drittland, REQ-025 §9, REQ-056 |
| Weitergabe an Drittsysteme, KI | `06` §2.2 (KI-Cloud-Gate), PA-13…PA-17; RISK-23 |
| Restrisiko, Konsultation | DSB |

---

## 6. Offene Rechtsfragen (Querverweis)

LEG-01…LEG-17 (decision-log §B) sowie neu LEG-18 (DVO 2023/564 Inhalt/elektronische Form), LEG-19 (Rechtsgrundlage
lit. b vs. lit. f für den Inhalt des Pflegeprotokolls, DA-02). Aus dem Audit 2026-11-22 (Register `decision-log.md` §D,
Fragen in `16`): LEG-48 und LEG-12 — Bestätigung der fortgeschriebenen Schwellwertprüfung (Verein „empfohlen“ vs.
„erforderlich“), Schwelle „umfangreich“ bei Kleinbetrieben, DSFA für KI und MCP, Art.-36-Aussage, VVT-Eintrag
„Speicherung auf dem Endgerät“ (Q-DSB-08); Art. 9/10 in Freitexten und Art. 35 Abs. 3 lit. b, RISK-18 (Q-LAW-11);
Fristen für Aufgaben-Leistungsfelder und `control_events` (Q-DSB-21).
