# SPEC-11 — DSFA-Vorprüfung (Art. 35 DSGVO)

```
Package: spec/privacy · Version 1.0 · 2026-11-09 · gemessen gegen develop 24d1c2988
Status: technische Vorprüfung, erstellt von der Engineering-Seite. Sie ist KEINE DSFA und KEINE
Rechtsberatung. Sie liefert dem DSB / der Rechtsberatung die Fakten und das Risikoinventar, die nötig sind, um
zu entscheiden, ob eine vollständige DSFA erforderlich ist, und um eine solche zu schreiben.
```

---

## 1. Basisfakten (verifiziert)

- Im Repository existiert keine DSFA. NFR-001 §6.7 verlangt eine **für Sensordaten**, bevor
  die Sensorerfassung produktiv geht; ADR-003 (Sensor-Aufbewahrung) nennt die DSFA-Frage offen; die
  Endnutzer-Doku `docs/de/user-guide/privacy.md` besagt, dass eine DSFA „wurde durchgeführt" —
  ein Widerspruch, der zu korrigieren ist (`06` §9).
- Ein Verzeichnis von Verarbeitungstätigkeiten (Art. 30) existiert nicht; REQ-025 §8 und NFR-011 §8 verlegen es
  außerhalb der Software.
- REQ-056 O-03 (Mandantenarchiv), REQ-053 SR-020 („berechtigtes Interesse oder DSFA") und
  GP-FR-146 (GeoJSON, „eigene DSFA") sowie das REQ-055-Review (S-018 Muster bei Buchungszeiten)
  verweisen jeweils auf eine DSFA, die nicht existiert.
- Die Rollen der Verantwortlichen (LEG-01) sind unentschieden; die folgende Vorprüfung ist aus der
  Perspektive des **Plattformbetreibers als Auftragsverarbeiter und des Mandanten als Verantwortlichem für
  Mitgliederdaten** geschrieben und vermerkt, wo der Betreiber selbst Verantwortlicher ist.

---

## 2. Verarbeitungsvorgänge im Geltungsbereich

| # | Operation | Data subjects | Data | Where |
|---|-----------|---------------|------|-------|
| O1 | Historische Aktivitätserfassung (Pflegelog, Bestätigungen, Ernten, Behandlungen, Plan-Audit) mit Zuordnung von Ausführenden/Erstellern und Zeitstempeln | Mitglieder (Beschäftigte, Ehrenamtliche, Vereinsmitglieder, Haushaltsmitglieder), in Labels genannte Dritte | wer hat was wann wo getan; Freitext | `care_events`, gesetzliche Zeilen, `garden_plan_audit`, Aufgaben |
| O2 | Zugriff von Lead/Management auf Mitgliederaktivität (Filter nach Person, CSV-Export mit Namen, Beethistorie) | Mitglieder | Aktivität je Person | `GET /care-events`, CSV, Beethistorie |
| O3 | Potenzial zur Beschäftigtenüberwachung in gewerblichen Mandanten | Beschäftigte | O1 + O2 | dasselbe |
| O4 | Freitextinhalte, die Personen nennen (Tagebuch, Notizen, Labels, Namen, Beschriftungen, Audit-Zusammenfassungen) | Mitglieder, Dritte, Personen auf Fotos | Namen, Beschreibungen, Fotos | ~25 Felder (`02` §3) |
| O5 | Lange Aufbewahrung (5 J. Pflegeereignisse, 3–5 J. gesetzlich, 730 d Security-Audit, pseudonymisierte Zeilen, die das Konto überdauern) | ehemalige Mitglieder, gelöschte Konten | pseudonymisierte Zuordnung, Freitext | Aufbewahrungs-Beats |
| O6 | Geteilte Geräte und Offline-Speicherung (IndexedDB-Queue mit Notizen/Fotos, Plan-Cache, localStorage-Schlüssel mit `user_key`/E-Mail) | die Nutzer/innen des Geräts | ungesendete Notizen/Fotos, Schlüssel | Browser |
| O7 | Mandantenübergreifende Verarbeitung (eine Installation, viele Verantwortliche; Plattformbetreiber mit Admin-Zugriff auf Mitgliederlisten und Security-Audit; Mandantenarchive, die die Installation verlassen) | alle Nutzer/innen | Verzeichnisdaten, GPS von Standorten | Plattform-Mandant, `/admin/platform/*`, REQ-056-Export |
| O8 | Abgeleitete Datensätze und Weitergabe (Backfill kopiert Ausführende aus gesetzlichen Zeilen; Plan-Audit kopiert Namen; Vorlagen kopieren Namen in Beete; Import-Snapshots) | Mitglieder | Kopien von Zuordnung und Inhalt | v0104, Konsistenz-Job, `place_template`, Audit |
| O9 | Sensordaten, die Anwesenheit offenbaren können (CO₂, Bewegung, manuelle Overrides) — der Vorgang, den NFR-001 §6.7 bereits markiert | Haushaltsmitglieder, Beschäftigte | Zeitreihen, Overrides | TimescaleDB, `manual_overrides` |
| O10 | Standortdaten (Standort-GPS = Wohnadresse bei persönlichen Gärten; vor dem Verlassen auf 2 Dezimalstellen gerundet) | Kontoinhaber/innen | Koordinaten | `sites.gps_coordinates`, Wetteraufrufe, Art.-15-Bundle, Mandantenarchiv |

Besondere Kategorien (Art. 9): konstruktionsbedingt keine. Gesundheitsbezogene Rückschlüsse sind nur
indirekt möglich (ein Tagebucheintrag kann eine Krankheit erwähnen; die Mitgliedschaft in einer
Cannabis-Anbauvereinigung kann selbst als sensibler Kontext gelten — **[rechtlich]** für den DSB). Kinder:
von den Specs nicht behandelt (keine Altersschranke) — **[rechtlich]** Hinweis für den DSB.

---

## 3. Risikoregister

Eintrittswahrscheinlichkeit / Auswirkung auf einer 3-Stufen-Skala (niedrig / mittel / hoch), wie die Engineering-Seite sie
sieht; der DSB kalibriert.

| R | Threat scenario | Subjects | Likelihood | Impact | Existing controls [verifiziert] | Required controls (this package) | Residual |
|---|-----------------|----------|------------|--------|-------------------------------|----------------------------------|----------|
| RISK-01 | **Aktivitätsprofiling von Mitgliedern**: Ein Lead oder ein beliebiges Mitglied rekonstruiert aus den Zeitstempeln der Ausführenden, wann eine Person im Garten war (Anwesenheitsmuster) | Mitglieder, bes. in Gemeinschaftsgärten | mittel (Daten sind für alle Mitglieder sichtbar) | mittel (Privatleben, Anwesenheit) | Filter nach anderer Person nur für Lead/Management (SR-020); kein Statistik-Endpunkt; CSV auf 50 000 Zeilen begrenzt | `attribution_visibility = leads_and_self` (PRIV-300); CSV-Namen nur für Leads + auditiert (PRIV-307/308); Guard gegen Aggregation je Person (PRIV-403); Unterdrückung ehemaliger Mitglieder (PRIV-112) | niedrig–mittel (Leads sehen weiterhin alles; durch Koordination gerechtfertigt) |
| RISK-02 | **Leistungsbewertung von Beschäftigten** durch einen Arbeitgeber mittels Filter/Export | Beschäftigte | mittel in gewerblichen Mandanten | hoch (arbeitsrechtliche Folgen; §26 BDSG / Art. 88; Mitbestimmung) | keine spezifischen | PRIV-403…407; Transparenztext für Betriebsräte; Standardempfehlung `leads_and_self` für Organisations-Mandanten (LEG-05) | mittel — die Plattform kann die Nutzung eines exportierten CSV außerhalb der Plattform nicht verhindern; gemindert durch Audit und Beschränkung |
| RISK-03 | **Gelöschte Person weiterhin identifizierbar** durch Freitext („Maren hat gegossen"), Fotobeschriftungen, Dateinamen, Vorlagen-/Beetnamen, Audit-Zusammenfassungen, alte getippte Namen | gelöschte Konten | hoch (heute sicher bei jeder Zeile, die die Person nennt) | mittel–hoch (Art. 17 nicht erfüllt; Reputationsrisiko für den Betreiber) | Marker an Kontofeldern; manuelle Schwärzung von Pflegeereignissen nur durch Leads, ohne Liste | Prüfwarteschlange mit Namens-Token-Markierung (PRIV-221), generische Schwärzung (PRIV-228), `original_filename` geleert (PRIV-211), alte nicht verschlüsselte Namen aufgelistet (PRIV-233), SLA-Metrik (PRIV-226) | niedrig–mittel — hängt davon ab, dass Leads handeln; LEG-08 zur Hinlänglichkeit |
| RISK-04 | **Pseudonym gelangt in nicht gesetzliche Speicher** (Tombstone ins Pflegelog kopiert, 5 J. verknüpfbar, filterbar) | gelöschte Konten | mittel (ist passiert: #2770) | mittel | keine | PRIV-204…207, Migration v0107, Konsistenz-Beat | niedrig |
| RISK-05 | **Ehemaliges Mitglied bleibt unbegrenzt namentlich genannt** in einem verlassenen Mandanten (und kann diese Zeilen nicht per Art. 15 exportieren, weil das Manifest nur aktuelle Mandanten liest) | ehemalige Mitglieder | hoch (heute sicher) | mittel | Security-Audit des Austritts | PRIV-112 Unterdrückung, PRIV-115 Information, PRIV-116 Entfernung der Zuordnung (P2); LEG-06(b) zu Art. 15 | niedrig–mittel |
| RISK-06 | **Gesetzliche Aufbewahrung ohne Rechtspflicht angewendet** (Ernte-/Behandlungszeilen eines Hobby-Mandanten 3–5 J. nach der Löschung pseudonymisiert behalten; der Export der Person findet sie) | gelöschte Konten in Hobby-Mandanten | hoch (heute sicher) | mittel | Tombstone (pseudonymisiert, nicht namentlich) | Profil `record_keeping` (PRIV-122/401), Reklassifizierungs-Job | niedrig; LEG-03 entscheidet |
| RISK-07 | **Gesetzliche Aufzeichnung geschwächt** (Name der anwendenden Person bei Löschung geleert, obwohl §11(2) PflSchG ihn verlangen kann) | der Mandant (Compliance), Kontrolleure | mittel | mittel (regulatorisch für den Mandanten) | Verknüpfbarkeit des Tombstones | Entscheidung LEG-04; Alternative mit versiegeltem Namen | offen |
| RISK-08 | **Geschlossenes Konto wird noch bis zu 90 Tage angezeigt** | Personen, die die Löschung beantragt haben | hoch (sicher) | niedrig–mittel (die Person erwartet zu verschwinden) | `is_active=false` | PRIV-104 | niedrig |
| RISK-09 | **Geteiltes Gerät legt ungesendete Notizen/Fotos und die Identität der vorherigen Nutzerin / des vorherigen Nutzers offen**; anderswo gelöschtes Konto hinterlässt Daten bis zu 365 d; `localStorage` behält `user_key`/E-Mail; Logout-Bereinigung wird nicht abgewartet | Nutzer/innen geteilter Tablets/Telefone (Gemeinschaftsgärten, Beschäftigte) | hoch (geteilte Geräte sind in Gärten die Regel) | mittel (Notizen, Fotos, Identität) | Namespace je Nutzer+Mandant; Dialog bei explizitem Logout; TTL 15 min für den Cache; Doku-Hinweis | PRIV-511…526 (kürzere Standardwerte, Quarantäne, `account.closed`, abgewartete Bereinigung, Schlüsselhygiene, Modus für geteilte Geräte, Geräteseite) | niedrig–mittel; LEG-09/10 |
| RISK-10 | **Backup-Wiederherstellung erzeugt gelöschte Personen neu** (kein Replay-Verfahren; Aufbewahrung der Dumps undefiniert) | gelöschte Konten | heute niedrig (keine Backups laufen) → hoch, sobald aktiviert | hoch (vollständige Re-Identifizierung) | keine | Ledger + Mirror + Replay bei Wiederherstellung (PRIV-707…713), bevor Backups aktiviert werden | nach Umsetzung niedrig; LEG-11 |
| RISK-11 | **Überschreitung durch den Plattformbetreiber**: Admin-Routen liefern mandantenübergreifend Mitglieder-E-Mails und Security-Audit; eine REQ-023-Zeile nennt sogar „Backup-System → Cross-Tenant Read-Access" | alle Nutzer/innen | niedrig (Routen abgesichert; Prinzip P4 gilt im Code) | hoch | `require_platform_admin`; keine Domänendaten-Routen | PRIV-311 (keine neuen Lesezugriffe); Operations-Endpunkt nur mit Zählungen; REQ-023 §5b.1 mit REQ-049 P4 in Einklang bringen (`06` §9) | niedrig |
| RISK-12 | **Offenlegung des Mitgliederverzeichnisses**: Jedes Mitglied sieht die E-Mail jedes Mitglieds | Mitglieder | hoch (sicher) | niedrig–mittel (Spam, unerwünschte Kontaktaufnahme; Adressen von Beschäftigten) | — | PRIV-305 (E-Mail nur für `management`); LEG-14 | niedrig |
| RISK-13 | **Zweckausweitung durch Ableitung**: gesetzliche Ausführende ins Pflegelog kopiert; Namen in Beete/Audit kopiert; Vorlagen-Austauschdateien (GP-API-070) tragen Vorlagennamen | Mitglieder | mittel | niedrig–mittel | GP-NFR-051 (Plan-Exporte ohne `*_by`); Vorlagen-Export „ohne Personenbezüge" laut Spec | Lineage-Registry (PRIV-031/606), `carry_account_reference`, Prüfvorschläge; LEG-07 | niedrig |
| RISK-14 | **Anwesenheitsrückschluss aus Sensoren und Overrides** (NFR-001 §6.7) | Haushaltsmitglieder | mittel | mittel–hoch (Privatleben) | Sensor-Aufbewahrungsstufen; `OUTDOOR_OPEN` als nicht personenbezogen eingestuft; DP-002-Rundung | außerhalb des Umfangs dieses Pakets, außer `manual_overrides.created_by/reason` (Marker, Prüfung); die Sensor-DSFA des DSB bleibt fällig | offen (bereits vorhanden) |
| RISK-15 | **Standortdaten verlassen die Installation** (Mandantenarchiv mit GPS; Art.-15-Bundle mit GPS; Wetteraufrufe gerundet) | Kontoinhaber/innen | niedrig–mittel | mittel (Wohnadresse) | Rundung DP-002; Archiv 72 h; Step-up | LEG-13; hier keine Änderung vorgeschlagen | mittel (bereits vorhanden) |
| RISK-16 | **Unvollständige Datenschutzoperationen bleiben unbemerkt** (`partially_completed`-Löschungen nur in Logs sichtbar; abweichende Eskalationsschwellen) | gelöschte Konten | mittel | mittel | Retry/Backoff; Fehlerlogs bei Versuch 1 und 5 | Metriken + Operations-Endpunkt + Stale-Alert (PRIV-110, PRIV-607) | niedrig |
| RISK-17 | **Dritte werden ohne Information genannt** (`performed_by_label`, Fotos von Personen) | Nicht-Nutzer/innen | mittel | niedrig–mittel | UI-Hinweis „keine vollständigen Namen" (SR-006); Label ≤ 80 | Prüffeld; Art.-14-Text für Mandanten (PRIV-408); LEG-12 | niedrig–mittel |
| RISK-18 | **Cannabis-Kontext**: Mitgliedschaft in einer Anbauvereinigung und Ernteaufzeichnungen können kontextbedingt sensibel sein | Vereinsmitglieder | niedrig–mittel | hoch (Stigma, rechtlich) | gesetzliche Aufbewahrung; Mandantenisolation | `record_keeping = kcang_association` macht die Klasse explizit; DSB soll Art.-9-Analogie bewerten | offen |

---

## 4. Ist eine vollständige DSFA wahrscheinlich erforderlich?

Kriterien (WP 248 rev.01, DSK-„Muss-Liste"): Eine DSFA ist erforderlich, wenn zwei oder mehr der neun
Kriterien zutreffen oder wenn die Verarbeitung auf der Liste einer Aufsichtsbehörde steht.

| Criterion | Applies? | Why |
|-----------|----------|-----|
| Bewertung oder Scoring (einschl. Profiling der Arbeitsleistung) | **ja, potenziell** (O2/O3 in gewerblichen Mandanten) | Aktivitätsfilter und Export je Person machen Leistungsbewertung möglich |
| Systematische Überwachung | teilweise (O1 fortlaufende Aktivitätsprotokollierung; O9 Sensoren mit Anwesenheitsrückschluss) | |
| Sensible Daten oder Daten höchstpersönlicher Natur | teilweise (O9 Anwesenheitsmuster; RISK-18 Cannabis-Kontext; O10 Wohnadresse) | |
| Große Reichweite | **nein** heute (einzelne Installation, kleine Mandanten); ändert sich mit gewerblichem SaaS | |
| Abgleich/Zusammenführung von Datensätzen | teilweise (O8 abgeleitete Datensätze über Collections hinweg; mandantenübergreifend) | |
| Schutzbedürftige betroffene Personen | **ja** (Beschäftigte in gewerblichen Mandanten — WP 248 nennt Beschäftigte ausdrücklich) | |
| Innovative Nutzung / neue Technologie | nein (KI-Features sind einwilligungsgesteuert und außerhalb dieses Umfangs) | |
| Verhindert die Ausübung eines Rechts oder die Nutzung eines Dienstes | nein | |
| DSK-Muss-Liste: „Verarbeitung von Beschäftigtendaten zur Verhaltens-/Leistungskontrolle"? | **vom DSB zu prüfen** — das Pflegelog ist nicht dafür gebaut, aber dafür geeignet (der Test nach §87(1) Nr. 6 BetrVG) | |

**Engineering-Einschätzung**: Für eine **selbst betriebene Hobby- oder Haushaltsinstallation** ist eine vollständige
DSFA wahrscheinlich **nicht** erforderlich (höchstens ein Kriterium; geringer Umfang). Für den **gewerblichen SaaS-
Betrieb mit Organisations-Mandanten, die Personal beschäftigen**, treffen plausibel mindestens zwei Kriterien
zu (Beschäftigtendaten + Bewertungspotenzial; dazu systematische Überwachung/Anwesenheitsrückschluss,
sobald Sensoren genutzt werden) — eine vollständige DSFA ist **wahrscheinlich erforderlich**, bevor dieses Betriebsmodell
startet, und die Sensor-DSFA, die NFR-001 §6.7 bereits verlangt, sollte darin aufgehen.
Diese Aussage ist kein rechtliches Ergebnis (LEG-12).

---

## 5. Eingaben, die die DSFA aus diesem Paket braucht

| DPIA section | Source |
|--------------|--------|
| Systematische Beschreibung der Verarbeitung | `01` §3/§6, `02` §3 |
| Erforderlichkeit und Verhältnismäßigkeit | `06` §4 LIA-1…3, `05` §3 Matrix |
| Rechtsgrundlagen und Aufbewahrung | `06` §2 |
| Risiken und Maßnahmen | §3 oben; Kontrollen aus `03`, `04`, `07` |
| Umgang mit Rechten betroffener Personen | `03` §2, REQ-025 (bestehend) |
| Auftragsverarbeiter / Empfänger | REQ-025 §9 (Sentry, Wetter, OAuth), REQ-056-Archiv, LEG-01 |
| Restrisiko und Konsultation (Art. 36) | DSB |

---

## 6. Offene Rechtsfragen für den DSB (Querverweis)

LEG-01 Rollen der Verantwortlichen · LEG-02 LIA Zuordnung · LEG-03 gesetzliche Anwendbarkeit · LEG-04
Lesbarkeit des Namens der anwendenden Person · LEG-05 Grundlage für Beschäftigtendaten, BetrVG · LEG-06 Frist
für ehemalige Mitglieder und Umfang von Art. 15 · LEG-07 Zweckvereinbarkeit des Backfills · LEG-08 Prüfmodell
für Freitext und SLA · LEG-09 TDDDG-Einordnung und Offline-Opt-in · LEG-10 Geräte-Aufbewahrung und
Karenz für tote Sitzungen · LEG-11 Backups und Replay-Ledger · LEG-12 DSFA-Schwelle, RoPA, Texte nach Art.
13/14 · LEG-13 Mandantenarchiv · LEG-14 Sichtbarkeit der Mitglieder-E-Mail · LEG-15 Verknüpfbarkeit von
Tombstones · LEG-16 berechtigtes Interesse Sentry (bereits vorhanden) · LEG-17 KCanG-Paragraf.
Details und Standardwerte: `decision-log.md`.
