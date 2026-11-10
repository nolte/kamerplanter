# SPEC-11 — DSFA-Vorprüfung (Art. 35 DSGVO)

```
Paket: spec/privacy · Version 1.1 · 2026-11-09 · gemessen gegen develop 24d1c2988; Nachtrag #2839 (develop 343afbb97)
Status: technische Vorprüfung (Schwellwertanalyse) der Engineering-Seite. Sie ist KEINE DSFA und
KEINE Rechtsberatung. Sie liefert dem DSB die Fakten, die Methodik und das Risikoinventar, um zu
entscheiden, ob eine DSFA erforderlich ist, und um sie zu erstellen.
Änderung v1.1: §4 ersetzt die Zählregel durch eine begründete Bewertung (DA-08); Evidenz L-16/L-17;
RISK-19/20 neu; Produktionsgate.
```

---

## 1. Basisfakten (VERIFIED_SPEC / VERIFIED_CODE)

- Keine DSFA im Repository; NFR-001 §6.7 verlangt eine für Sensordaten vor Produktivsetzung; ADR-003 nennt die
  DSFA-Frage offen; `docs/de/user-guide/privacy.md` behauptet eine durchgeführte DSFA (Widerspruch W-10).
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
| O10 | Standortdaten (GPS = Wohnadresse bei persönlichen Gärten) | Kontoinhaber | Koordinaten | `sites.gps_coordinates`, Export, Archiv | PA-11 |

Besondere Kategorien (Art. 9): konstruktionsbedingt keine; Cannabis-Kontext (RISK-18) und Tagebuchfreitext können
indirekt sensible Inhalte tragen (LEGAL_REVIEW_REQUIRED). Kinder: keine Altersprüfung (LEGAL_REVIEW_REQUIRED).

---

## 3. Risikoregister

Skala niedrig/mittel/hoch, Einschätzung der Engineering-Seite; der DSB kalibriert.

| R | Bedrohungsszenario | Betroffene | Eintrittsw. | Schwere | Bestehende Maßnahmen [VERIFIED_CODE] | Erforderliche Maßnahmen (Paket) | Restrisiko |
|---|--------------------|------------|-------------|---------|--------------------------------------|----------------------------------|------------|
| RISK-01 | Aktivitätsprofiling (Anwesenheitsmuster aus Zeitstempeln) | Mitglieder | mittel | mittel | Personenfilter nur Lead/Management; kein Statistik-Endpunkt; CSV ≤ 50 000 | `attribution_visibility` (PRIV-300, Klassen-Defaults DA-04); CSV-Namen nur Leads + Audit (PRIV-307/308); Aggregationsverbot (PRIV-403); Unterdrückung ehemaliger Mitglieder (PRIV-112) | niedrig–mittel |
| RISK-02 | Leistungsbewertung Beschäftigter durch Filter/Export (DSK-Liste Nr. 8, L-17) | Beschäftigte | mittel (gewerblich) | hoch | keine spezifischen | PRIV-403…407, 414; Default `leads_and_self` (DA-04); Betriebsrats-Mustertext | mittel (Export außerhalb der Plattform nicht kontrollierbar) |
| RISK-03 | Gelöschte Person über Freitext/Beschriftungen/Dateinamen/Namen identifizierbar | gelöschte Konten | hoch | mittel–hoch | Marker auf Kontofeldern; manuelle Schwärzung nur Pflegeereignisse | Zustandsautomat mit vollständiger Entdeckung (DA-05), generische Schwärzung, `original_filename` geleert, Alt-Namen gelistet, Eskalation/Auto-Schwärzung (Flag) | niedrig–mittel (abhängig von Lead-Entscheidungen bzw. Flag, LEG-08) |
| RISK-04 | Pseudonym in nicht gesetzliche Speicher kopiert (#2770) | gelöschte Konten | mittel (eingetreten; für `care_events` **behoben #2839**) | mittel | `account_of` → Marker, v0107 (VERIFIED_CODE) | PRIV-204…207 für die übrigen Kopierstellen, v0109, Konsistenz-Beat | niedrig |
| RISK-05 | Ehemaliges Mitglied unbegrenzt namentlich; Art.-15-Lücke für verlassene Mandanten | ehemalige Mitglieder | hoch | mittel | Security-Audit | PRIV-112/115/116; LEG-06(b) | niedrig–mittel |
| RISK-06 | Statutory-Aufbewahrung ohne Pflicht (Hobby-Mandanten; erntende Person als Pseudonym 5 J.) | gelöschte Konten | hoch | mittel | Tombstone | Profil + feldgenaue Zuordnung (`06` §3.2), PRIV-409…411 (Flag) | niedrig nach LEG-03/17 |
| RISK-07 | Pflichtaufzeichnung geschwächt (Anwender-Name geleert; Fristbeginn zu früh) | Mandant (Compliance) | mittel | mittel | Tombstone-Verknüpfbarkeit | PRIV-412 (Fristbeginn 1.1. Folgejahr), LEG-04 (Name), PRIV-413 (Hilfsdokumentation) | offen |
| RISK-08 | Geschlossenes Konto 90 d sichtbar | Antragsteller | hoch | niedrig–mittel | `is_active=false` | PRIV-104 | niedrig |
| RISK-09 | Geteiltes Gerät legt Notizen/Fotos/Identität offen; Konto anderswo gelöscht; Keys überleben Logout; Logout-Wipe nicht abgewartet | Nutzer geteilter Geräte | hoch | mittel | Namespace; Logout-Dialog; TTL 15 min | DEC-29 Schalter + Übergang; PRIV-511…526; Szenarienmatrix `07` §8a | niedrig–mittel; LEG-09/10 |
| RISK-10 | Restore erzeugt gelöschte Personen neu | gelöschte Konten | niedrig heute → hoch bei Backups | hoch | keine | Löschungs-Spiegel + Replay (`09` §6, DEC-26); Residue-Scan im Restore; Lücke zwischen Dump und Spiegelverlust dokumentiert | niedrig nach Umsetzung; LEG-11 |
| RISK-11 | Betreiber-Überreichweite (Admin-Verzeichnisse; REQ-023 „Backup → Cross-Tenant Read“) | alle | niedrig | hoch | `require_platform_admin`; P4 | PRIV-311; Zähler-Endpunkt; Spec-Korrektur | niedrig |
| RISK-12 | Mitglieder-E-Mails für alle | Mitglieder | hoch | niedrig–mittel | — | PRIV-305; LEG-14 | niedrig |
| RISK-13 | Zweckausweitung durch Ableitung (Backfill, Audit-Kopien, Vorlagenexport) | Mitglieder | mittel | niedrig–mittel | GP-NFR-051 | Lineage-Registry + Laufzeit-Provenienz (`02` §5a), `carry_account_reference`, Schalter DA-02 | niedrig |
| RISK-14 | Anwesenheitsrückschluss aus Sensoren/Overrides (NFR-001 §6.7) | Haushaltsmitglieder | mittel | mittel–hoch | Aufbewahrungsstufen; DP-002 | außerhalb dieses Pakets; Sensor-DSFA fällig | offen |
| RISK-15 | Standortdaten verlassen die Installation (Archiv, Bundle) | Kontoinhaber | niedrig–mittel | mittel | Rundung; 72 h; Step-up | LEG-13 | mittel |
| RISK-16 | Unvollständige Datenschutzoperationen unbemerkt | gelöschte Konten | mittel | mittel | Retry/Backoff; Logs | Metriken, Endpunkt, Stale-Alert (PRIV-110, 607), Zustandsautomat `ERASURE_COMPLETED` | niedrig |
| RISK-17 | Dritte ohne Information genannt (Labels, Fotos) | Nicht-Nutzer | mittel | niedrig–mittel | UI-Hinweis (SR-006) | Prüffeld; Art.-14-Vorlage (PRIV-408) | niedrig–mittel |
| RISK-18 | Cannabis-Kontext (Anbauvereinigung) als sensibler Kontext | Vereinsmitglieder | niedrig–mittel | hoch | Statutory-Aufbewahrung; Isolation | `kcang_association` macht die Klasse explizit; DSB prüft Art.-9-Nähe | offen |
| **RISK-19** (neu) | Mandantenübergreifende Verknüpfbarkeit eines gelöschten Kontos über den instanzweiten Tombstone (zwei Archive/Mandanten genügen) | gelöschte Konten | niedrig–mittel | mittel | Zugriff nur Leads je Mandant | DEC-25 (mandantengebundene HMAC-Pseudonyme für neue Zeilen); Archiv-Hinweis LEG-13 | niedrig nach DEC-25 |
| **RISK-20** (neu) | Kompromittierung des Tombstone-Salts erlaubt Reidentifikation aller Pseudonyme; Rotation nicht heilend | gelöschte Konten | niedrig | hoch | Secret in Kubernetes | Zugriffsbeschränkung, Secret-Rotation **nicht** möglich (`09` §7) → Betriebsdoku, Monitoring des Secret-Zugriffs | mittel (strukturell) |

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
| 1 Bewertung/Scoring | **teilweise, nur gewerblich**: Das System bewertet nicht, ist aber zur Bewertung einsetzbar (Personenfilter, CSV je Person, Zeitstempel) | VERIFIED_CODE Filter/CSV; DSK Nr. 8 „eingesetzt werden können“ |
| 2 Automatisierte Entscheidung mit Rechtswirkung | nein | keine Automatik mit Rechtsfolge |
| 3 Systematische Überwachung | **teilweise**: fortlaufende Protokollierung aller Pflegehandlungen mit Person und Zeit; Sensoren mit Anwesenheitsbezug (O9) | VERIFIED_CODE |
| 4 Sensible/höchstpersönliche Daten | **teilweise**: Anwesenheitsmuster (O9), Wohnadresse (O10), Cannabis-Kontext (RISK-18) | INFERRED |
| 5 Große Reichweite | nein (heute); bei kommerziellem SaaS zu prüfen | — |
| 6 Abgleich/Zusammenführung | **teilweise**: Ableitungen über Collections (O8), instanzweiter Tombstone (RISK-19) | VERIFIED_CODE |
| 7 Schutzbedürftige Betroffene | **ja bei Beschäftigten** („employees“ ausdrücklich, L-16); nein bei Haushalt/Verein | VERIFIED_LEGAL |
| 8 Innovative Nutzung | nein (KI-Funktionen einwilligungsgesteuert, außerhalb) | — |
| 9 Verhindert Rechtsausübung | nein | — |
| DSK Nr. 8 | **einschlägig, sobald „umfangreich“** in einem Betrieb mit Beschäftigten | L-17 |

### 4.3 Ergebnis je Betriebsmodell

| Betriebsmodell | Kriterien | Bewertung | Maßnahmen (Paket) | Restrisiko | Entscheidung (Engineering-Vorschlag) |
|----------------|-----------|-----------|-------------------|------------|--------------------------------------|
| Selbst gehostet, Haushalt/Hobby (persönliche Mandanten) | keines voll; 3/4 nur mit Sensorik | kein voraussichtlich hohes Risiko | Standardmaßnahmen | niedrig | **keine DSFA**; Sensor-DSFA nach NFR-001 §6.7, wenn CO₂/Bewegung genutzt |
| SaaS, Gemeinschaftsgarten/Verein (Ehrenamt, Mitglieder) | 3 teilweise, 6 teilweise; 7 nein (L-09) | mittleres Risiko; Profiling möglich, aber Transparenz erwartet | LIA-1, `all_members` mit Unterdrückung ehemaliger Mitglieder, Prüfwarteschlange, Information | niedrig–mittel | DSFA **empfohlen**, nicht zwingend; DSB-Rat einholen |
| SaaS, gewerblicher Mandant mit Beschäftigten | 7 ja; 1 und 3 teilweise; DSK Nr. 8 einschlägig bei Umfang | **voraussichtlich hohes Risiko** | `leads_and_self`, Aggregationsverbot, Audit, Betriebsrats-Vorlage, Klassifizierung | mittel (Export außerhalb) | **DSFA erforderlich** vor Aufnahme dieses Betriebsmodells; DSB-Beteiligung (Art. 35 Abs. 2) |
| Jedes Modell mit Sensorik Anwesenheitsbezug | 3 und 4 | hohes Risiko (NFR-001 §6.7) | außerhalb dieses Pakets | — | DSFA erforderlich (bereits spezifiziert) |
| Anbauvereinigung (KCanG) | 4 teilweise (Kontext), 3 | mittel–hoch | `kcang_association`, feldgenaue Pflichtaufzeichnung | mittel | DSFA **empfohlen**; DSB prüft Art.-9-Nähe |

**Art. 36 (vorherige Konsultation):** nach heutiger Einschätzung nicht erforderlich, weil die Maßnahmen das
Restrisiko unter „hoch“ bringen; die Entscheidung trifft der DSB nach der DSFA.

**Diese Vorprüfung ersetzt keine DSFA.** Produktionsgate: `deployment_allowed = nein` für „SaaS mit gewerblichen
Mandanten“ bis zur DSFA-Entscheidung (DEC-32, LEG-12).

---

## 5. Eingaben für die DSFA aus diesem Paket

| DSFA-Abschnitt | Quelle |
|----------------|--------|
| Systematische Beschreibung | `01` §3/§6, `02` §3, `06` §2 (PA) |
| Erforderlichkeit und Verhältnismäßigkeit | `06` §4 LIA-1…3, `05` §3, DA-02/DA-04 |
| Rechtsgrundlagen, Aufbewahrung | `06` §2, §3, §8; `13` |
| Risiken und Maßnahmen | §3; `03`, `04`, `07` |
| Betroffenenrechte | `03` §2, `04` §5 (Zustandsautomat), REQ-025 |
| Auftragsverarbeiter/Empfänger | `06` §1 Rollenmatrix, REQ-025 §9, REQ-056 |
| Restrisiko, Konsultation | DSB |

---

## 6. Offene Rechtsfragen (Querverweis)

LEG-01…LEG-17 (decision-log §B) sowie neu LEG-18 (DVO 2023/564 Inhalt/elektronische Form), LEG-19 (Rechtsgrundlage
lit. b vs. lit. f für den Inhalt des Pflegeprotokolls, DA-02).
