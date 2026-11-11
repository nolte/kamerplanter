---
req_id: REQ-053
title: Grafische Garten- und Beetplanung (Plan-Editor, Beetverwaltung, Pflanzplanung, Beetpflege, Feldmodus, Druck/Export)
category: Standorte & Pflanzplanung
test_count: 108
coverage_areas:
  - Gartengrenze und Beete zeichnen (Raster, Snap, Maße)
  - Verschieben, Drehen, Undo/Redo, Tastaturbedienung
  - Speichern-Status, Konflikt-Dialog, Listenansicht (Barrierefreiheit)
  - Beetliste, Beetstatus, Löschen mit aktiven Pflanzen, Bestandsbeete ohne Geometrie
  - Zelt als Beet (einheitliche Beetansicht Indoor/Outdoor)
  - Bepflanzen (Reihenlayout, Durchlauf starten, Nachkultur, Fruchtfolge-Hinweis)
  - Position korrigieren, Beet räumen
  - Pflegeaufgaben erledigen, Pflegehistorie (Filter, Zeitstrahl, Korrektur, Schwärzung)
  - Feldmodus Smartphone 390 × 844 (Erledigt in zwei Tipps, Schnellprotokoll mit Rückgängig)
  - Plan drucken (PDF) und JSON-Export
  - v1.3 — Stapelauswahl, Touch-Zeichnen, Eltern-Kind, Maßeingabe, Zoom/LOD, Tastaturfokus
  - v1.3 — Pflanzeninfo beim Überfahren, grafische Pflanzenzustände, Standortmerkmale, Eignungs-Ampel
  - v1.3 — Wiederherstellung per Import, Saison-Kopie, Indoor-Grundriss (SHOULD)
  - Welle 7 — Bewässerungszonen, Gießrunde, Ebene „zuletzt gegossen“, Beetvorlagen und Standardgrößen
  - Welle 7 — Objekt-Snap, Ausrichten/Verteilen, Mehrfach duplizieren, Auto-Save, Mini-Map
  - Welle 7 — Pflanzenzustand-Filter, Teilexport/Import-Ziel, frühere Stände, Sonnenfenster im Feldmodus
  - Welle 8 Teil A — Bodenanalyse, Flächendosis, Bodenverbesserung, Nährstoff-Hinweis ohne Zahl, Historie als CSV, Rotationsmatrix, Folgekultur, Vorschläge
  - Welle 8 Teil B — Mischkultur-Ebene, Standortmerkmale, Erreichbarkeit, Beet-Fotos, CSV-Beetliste/-Import, Frost-Grund im Pflanzenzustand
  - Welle 9 — Renderer-Messung D-01 (Drag-/Zoom-Frametime, große Pläne, Desktop und Mobile CPU 4×)
  - Welle 9 Teil A — Offline: Service Worker, Plan ohne Verbindung, Puffer und Sync, Konflikt, Abmelden leert den Zwischenspeicher
  - Welle 9 Teil B — PNG-Export, Vorlagen-Austausch, Parzellenseite im PDF, Standort-Flags, nächste Wasserquelle, Strg+D, Konva-Umschaltung
  - Welle 10 Teil A — Editor-Arbeitsfläche (Tabs mit URL-Zustand, Seitenpanel, drei Breiten), Objekteigenschaften, Indoor-Plan (Leerzustand, Fenster-Vorschlag, Pflanzplätze)
generated: "2026-10-11"
version: "1.13"
---

# Testfälle REQ-053: Grafische Garten- und Beetplanung

Dieses Dokument enthält End-to-End-Testfälle aus **REQ-053 Grafische Garten- und Beetplanung
v1.3**, ausschließlich aus der Perspektive eines Nutzers im Browser. Keine Endpunkte,
HTTP-Statuscodes, Collection-Namen oder Datenbankabfragen erscheinen in den Testschritten. Alle
Aussagen beschreiben, was der Nutzer sieht, anklickt, antippt, eintippt und auf dem Bildschirm
erwartet. `data-testid`-Werte aus GP-UX-012 stehen in Klammern ausschließlich als Lokator-Hinweis.

Die UI-Sprache ist **Deutsch** (Standard-Locale). UI-Texte in Anführungszeichen sind Platzhalter
aus REQ-053 und werden bei der Umsetzung gegen die tatsächlichen i18n-Texte abgeglichen.

Jeder Testfall nennt das **Gerät**:

- **Desktop** — Viewport ≥ md (z. B. 1440 × 900), Planungsmodus mit Werkzeugleiste, Canvas und
  Eigenschaftenpanel
- **Smartphone 390 × 844** — Feldmodus (Standard auf xs), Touch-Bedienung

Beispiel-Beträge der Akzeptanzkriterien (z. B. Garten 10 × 10 m, Raster 10 cm) gelten als
Testdaten-Vorgabe.

## Geltungsbereich

Abgedeckt sind die browser-beobachtbaren Akzeptanzkriterien GP-ACC-001, 002, 005, 006, 007, 008,
011, 012, 015, 016, 019, 020, 021, 022, 024, 025, 026, 027, 028, 029, 030, 031 (nur Export),
032, 035, 036, 039, 040, 044, 047, 048, 051 und 052. Die Kriterien sind dort, wo sie als Integrationstest
(I) formuliert sind, auf ihre sichtbare Wirkung in der Oberfläche reduziert; der Datenvertrag
selbst (Feldwerte, Fehlercodes, Edges) wird in Integrationstests geprüft.

Zusätzlich sind drei Testfälle aus Use Cases abgeleitet, die kein Akzeptanzkriterium trifft:
TC-053-007 (Speichern-Status und Verlassen-Dialog, abgeleitet aus UC-02 / GP-UX-003),
TC-053-029 (Plan drucken, abgeleitet aus UC-11) und TC-053-030 (Plan als JSON sichern,
abgeleitet aus UC-12). Die Fälle TC-053-031 bis TC-053-044 sind aus den Anforderungen der Version 1.3 abgeleitet (GP-ACC-051 und GP-ACC-052 sind direkt zugeordnet). Die Fälle TC-053-045 bis TC-053-055 sind aus den SHOULD-Zeilen der Welle 7 abgeleitet (Abschnitt 7). Die Fälle TC-053-056 bis TC-053-059 sind aus den SHOULD-Zeilen der Welle 7, Teil B abgeleitet (Abschnitt 8); TC-053-060 aus GP-NFR-071.

**Nicht** abgedeckt sind die Kriterien GP-ACC-003, 004, 009, 010, 013, 014, 017, 018, 023,
033, 034, 037, 038, 041, 042, 043, 045, 046, 049, 050 sowie 053, 054, 055, 056 und 057 — siehe
Abschnitt „Nicht abgedeckte Akzeptanzkriterien" am Dokumentende für die Begründung je
Kriterium. Sie gehören in Unit-, Integrations- und Benchmark-Tests.

**Version 1.4 (2026-10-16, Nachtrag zu REQ-053 v1.4 nach dem Spec-Readiness-Review) — was sich
für die Tests ändert:**

- **E-01 (Site-Anker statt `tenant_key`-Stempel):** Testdaten für Beete, Pflanzpositionen und
  Gartenobjekte tragen kein `tenant_key`; die Mandantenzugehörigkeit kommt über den Garten
  (Site). Für die Browser-Fälle ändert sich nichts Sichtbares; GP-ACC-046 bleibt Service-/
  Integrationstest (Zeile in der Tabelle unten).
- **E-05 (`light_requirement` vs. `shade_tolerance`):** TC-053-037 (Eignungs-Ampel) prüft den
  Anspruch der Art gegen das Beet; die Zelle „Beet eine Stufe schattiger, Toleranz unbekannt"
  zeigt **gelb** mit der Begründung „Toleranz unbekannt" (GP-FR-160). Die Matrix selbst wird im
  Unit-Test GP-ACC-053 geprüft, nicht im Browser.
- **Neue Akzeptanzkriterien GP-ACC-053…057** (Unit/Integration): Eignungs-Matrix mit
  gemeinsamen Testvektoren, disjunkte Reihenzuweisung bei Mischkultur, Fruchtfolge standardmäßig
  aus für Pflanzgefäß/Zelt/Regal, Plan-Rahmen > 1 000 m abgelehnt, mandantenweite Historie mit
  90-Tage-Standard — alle ohne eigenen Browser-Fall; die sichtbare Wirkung von GP-ACC-054 ist in
  TC-053-015 (Reihenlayout), die von GP-ACC-055 in TC-053-014 (Zelt) und TC-053-018
  (Fruchtfolge-Hinweis) teilweise enthalten.
- **Wortlaut Konflikt-Dialog (TC-053-008):** die zweite Schaltfläche heißt einheitlich
  „Meine Änderungen als Kopie behalten (JSON herunterladen)" (GP-UX-017, GP-ACC-011, UI-NFR-022).
- `test_count` bleibt 44; die Abdeckungs-Matrix und die Tabelle der nicht abgedeckten Kriterien
  sind um GP-ACC-053…057 ergänzt.

**Version 1.5 (2026-10-31, WP 7.25 / #2491)** — elf neue Fälle TC-053-045 bis TC-053-055 aus
GP-FR-110, GP-FR-117, GP-UX-031, GP-FR-044, GP-FR-045, GP-FR-012, GP-FR-029, GP-FR-025, GP-UX-004 und
GP-UX-014 (Abschnitt 7); `test_count` 44 → 55, die Abdeckungs-Matrix ist um die abgeleiteten Zeilen
ergänzt. TC-053-047 („Regen — übersprungen“) beschreibt das geforderte Verhalten; die Oberfläche bietet
die Aktion noch nicht an (Platzhalter-Bündel #2466).

**Version 1.6 (2026-10-31, WP 7.26 / #2492)** — vier neue Fälle TC-053-056 bis TC-053-059 aus GP-UX-061,
GP-FR-169, GP-FR-172, GP-FR-148/170 und GP-FR-158/159 mit GP-UX-057 (Abschnitt 8); `test_count` 55 → 59, die
Abdeckungs-Matrix ist um die abgeleiteten Zeilen ergänzt. TC-053-042 und TC-053-044 bleiben unverändert.

**Version 1.8 (2026-11-03, WP 8.29 / #2672)** — ein neuer Fall TC-053-060 (Messprofil Interaktion, GP-NFR-071, Abschnitt 8);
`test_count` 59 → 60, die Abdeckungs-Matrix ist um die abgeleitete Zeile ergänzt. Die Grenzwerte sind beratend.

**Version 1.7 (2026-10-31, WP 7.27 / #2493)** — keine neuen Fälle (`test_count` bleibt 59). Die Zuordnung der
Welle-7-Zeilen GP-FR/GP-API/GP-UX (SHOULD) zu Tests steht in der generierten Matrix
`spec/e2e-testcases/GP-REQ-wave7-matrix.md` (`scripts/gp_acc_matrix.py`). Zwei Fälle bleiben bewusst ohne
Automatisierung, weil die Oberfläche fehlt: TC-053-047 („Regen — übersprungen“ — keine Aktion im Gießrunden-Dialog,
keine Route) und TC-053-027 („Beet räumen“ — kein Knopf ruft die Route auf). GP-ACC-033 ist in der Tabelle der
nicht abgedeckten Kriterien um die Benchmark-Tests ergänzt; die E2E-Datei des Feldmodus zählt nicht mehr dafür.

**Version 1.9 (2026-11-06, WP 8.30 / #2673 und WP 8.31 / #2674)** — 22 neue Fälle TC-053-061 bis TC-053-082 aus den
Welle-8-Zeilen GP-FR-104, 122, 123, 124, 125, 133, 135, 086 (Teil A, Abschnitt 9) sowie GP-FR-051, 134, 145, 161–163,
166, 168, 174, 175, GP-UX-057 und §11.4 (Teil B, Abschnitt 10); `test_count` 60 → 82, die Abdeckungs-Matrix ist um die
abgeleiteten Zeilen ergänzt. Bereits abgedeckte Teile werden nicht wiederholt: Düngen mit Flächenmenge in l/m² steht in
TC-053-020, die Sonnenfenster-Chips im Feldmodus in TC-053-059, Sonne/Schatten-Kacheln in TC-053-036, die
Eignungs-Ampel (Licht) in TC-053-037, Pflanzenzustand und Info-Blase in TC-053-034/035/056, JSON-Export in
TC-053-030/057. GP-FR-105 (Konsistenz-Job), GP-FR-165 und GP-FR-167 haben keinen Browser-Weg und stehen am Dokumentende
unter „Nicht abgedeckte Welle-8-Zeilen“.

**Version 1.10 (2026-11-08, WP 9.6 / #2746)** — ein neuer Fall TC-053-083 (Renderer-Messung D-01, GP-NFR-033/034,
Abschnitt 11); `test_count` 82 → 83, die Abdeckungs-Matrix ist um die abgeleitete Zeile ergänzt. Die Grenzwerte sind
beratend; der Fall liefert die Messwerte für die Go/No-Go-Entscheidung zu WP 9.7.

**Version 1.11 (2026-11-09, WP 9.15 / #2755)** — sieben neue Fälle TC-053-084 bis TC-053-090: Teil A Offline
(Abschnitt 12, aus GP-UX-024 und UI-NFR-012); `test_count` 83 → 90, die Abdeckungs-Matrix ist um die abgeleiteten
Zeilen ergänzt. Bewusst nicht abgedeckte Teile stehen am Dokumentende unter „Nicht abgedeckte Welle-9-Teile“.

**Version 1.12 (2026-11-09, WP 9.16 / #2756)** — sieben neue Fälle TC-053-091 bis TC-053-097: Teil B Export, Vorlagen,
Standort, Editor und Renderer (Abschnitt 13, aus GP-FR-144, 173, 176, 165, 167, 025/026 und GP-NFR-033/D-01);
`test_count` 90 → 97, die Abdeckungs-Matrix ist um die abgeleiteten Zeilen ergänzt. TC-053-047 („Regen —
übersprungen“) ist seit WP 9.13 in der Oberfläche und jetzt automatisiert (`tests/e2e/test_req053_wave9_export.py`).
GP-FR-165 und GP-FR-167 sind aus den nicht abgedeckten Welle-8-Zeilen in Abschnitt 13 gewandert.

**Version 1.13 (2026-11-11, WP 10.13 / #2834)** — elf neue Fälle TC-053-098 bis TC-053-108: Welle 10 Teil A,
Editor-Arbeitsfläche und Indoor-Plan (Abschnitt 14, aus den Akzeptanzkriterien AC-1…AC-11 der Arbeitsfläche §17.3 mit
AC-12, AC-15, AC-16, AC-17 sowie GP-FR-180…183); `test_count` 97 → 108. TC-053-103 (AC-2) ist **blockiert durch #2868**
und hat keinen ausführbaren Test. Bereits abgedeckte Teile werden nicht wiederholt, sondern verwiesen: der
Verlassen-Dialog (AC-8) in TC-053-007, die Hervorhebung aus der Beetliste (AC-7) in TC-053-012, die bestehenden
Touch-Fälle (AC-9) in TC-053-032 und TC-053-033, der ursprüngliche Indoor-Grundriss in TC-053-044. Die Zuordnung je
Kriterium steht am Anfang von Abschnitt 14, die Abdeckungs-Matrix ist um die abgeleiteten Zeilen ergänzt, nicht
abgedeckte Teile stehen am Dokumentende unter „Nicht abgedeckte Welle-10-Teile“.

## Hinweis zur Zustandsherstellung

Mehrere Testfälle brauchen Vorbedingungen, die nicht über die Oberfläche herstellbar sind
(Beet mit 60 Pflegeereignissen über zwei Jahre, Beet mit Vorjahreskultur, Bestandsbeet ohne
Geometrie, Zelt mit 9 Slots aus der Migration, zweiter Nutzer mit überholter Plan-Version).
Jeder Testfall hält ausdrücklich fest, wie der Zustand herzustellen ist: über Seed-Daten oder
über eine zweite Browser-Sitzung. Testdaten-Mandant: Demo-Mandant mit einer Outdoor-Site
(Garten 10 × 10 m, Raster 10 cm), Rolle Leitung, sofern nicht anders genannt.

---

## 1. Garten und Editor

### TC-053-001: Leerer Plan erklärt den ersten Schritt, Gartengrenze zeichnen und speichern

**Requirement**: REQ-053 §6 UC-01, §9.2, GP-UX-010 — GP-ACC-001
**Gerät**: Desktop
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer ist eingeloggt (Rolle Gärtner oder Leitung)
- Eine Outdoor-Site ohne Plan existiert

**Testschritte**:
1. Nutzer öffnet die Site und wählt „Plan" (`garden-plan-page`)
2. Nutzer liest den Leerzustand des Canvas
3. Nutzer zeichnet mit dem Bereichs-/Grenzwerkzeug ein Rechteck von 10 × 10 m
4. Nutzer setzt die Nordrichtung auf 0°
5. Nutzer klickt „Speichern" (`save-plan-button`)
6. Nutzer lädt die Seite neu

**Erwartete Ergebnisse**:
- Der Leerzustand erklärt in zwei Sätzen, was zuerst zu tun ist („Zeichne die Umrisse deines
  Gartens. Du kannst sie später jederzeit anpassen.")
- Nach dem Speichern zeigt die Kopfzeile „Gespeichert"
- Die Gartengrenze erscheint als gestrichelte Außenlinie, mit Schloss-Symbol (gesperrt)
- Die Gesamtfläche wird als 100 m² angezeigt
- Nach dem Neuladen steht die Grenze unverändert an derselben Stelle

**Nachbedingungen**:
- Die Site hat einen gespeicherten Plan mit Grenze und Nordrichtung

**Tags**: [req-053, garden-plan, boundary, speichern, desktop, gp-acc-001]

---

### TC-053-002: Beet mit Rechteck-Werkzeug zeichnen — Snap auf 2,0 × 1,0 m

**Requirement**: REQ-053 §9.2, §9.4 GP-FR-019, UC-02 — GP-ACC-002
**Gerät**: Desktop
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Plan einer Site mit Gartengrenze 10 × 10 m und Raster 10 cm ist geöffnet
- Zoom steht auf 100 %

**Testschritte**:
1. Nutzer wählt das Werkzeug „Beet" (`plan-tool-bed`)
2. Nutzer zieht auf dem Canvas ein Rechteck auf, das nach dem Einrasten 2,0 × 1,0 m misst
3. Nutzer trägt im Eigenschaftenpanel den Namen „Beet 1" ein
   (`plan-properties-panel`, `form-field-name`)
4. Nutzer klickt „Speichern"

**Erwartete Ergebnisse**:
- Während des Ziehens zeigt eine Live-Anzeige Position und Maße
- Das Panel zeigt Breite 2,0 m, Länge 1,0 m und Fläche 2,0 m²
- Das Beet wird im Seitenverhältnis 2 : 1 dargestellt und mit Name und Status-Badge beschriftet
- Nach dem Speichern zeigt die Kopfzeile „Gespeichert"; nach einem Neuladen ist das Beet
  unverändert vorhanden

**Nachbedingungen**:
- Ein Beet „Beet 1" mit 2 m² Fläche existiert im Plan und in der Beetliste

**Tags**: [req-053, garden-plan, bed, zeichnen, snap, desktop, gp-acc-002]

---

### TC-053-003: Beet per Maus verschieben — Rastereinrastung und Alt-Taste

**Requirement**: REQ-053 §9.2 Raster, §9.4 GP-FR-021, GP-UX-007 — GP-ACC-006
**Gerät**: Desktop
**Priority**: High
**Category**: Interaktion
**Preconditions**:
- Gespeicherter Plan mit Raster 10 cm und einem Beet „Beet 1"

**Testschritte**:
1. Nutzer wählt „Beet 1" aus und zieht es mit der Maus um 23 cm nach rechts; er lässt los
2. Nutzer liest die x-Position im Eigenschaftenpanel
3. Nutzer macht die Verschiebung mit „Rückgängig" ungeschehen
4. Nutzer zieht das Beet erneut um 23 cm nach rechts und hält dabei die Alt-Taste gedrückt

**Erwartete Ergebnisse**:
- Während des Ziehens sind ein Geisterobjekt und eine Snap-Hilfslinie sichtbar; Position und Maß
  laufen live mit
- Ohne Alt liegt die neue x-Position um 0,20 m weiter rechts (auf einem Vielfachen von 0,10 m)
- Mit Alt liegt die neue x-Position genau 0,23 m weiter rechts (kein Einrasten)
- Esc während des Ziehens bricht die Verschiebung ab und das Beet bleibt an seiner Stelle

**Nachbedingungen**:
- Beet steht an der zuletzt abgelegten Position; Kopfzeile zeigt „Ungespeicherte Änderungen"

**Tags**: [req-053, garden-plan, drag, snap, raster, desktop, gp-acc-006]

---

### TC-053-004: Undo und Redo einer Verschiebung per Tastatur

**Requirement**: REQ-053 §9.4 GP-FR-026, GP-UX-003 — GP-ACC-007
**Gerät**: Desktop
**Priority**: High
**Category**: Interaktion
**Preconditions**:
- Gespeicherter Plan mit einem Beet; das Beet ist ausgewählt

**Testschritte**:
1. Nutzer verschiebt das Beet mit der Maus an eine andere Stelle
2. Nutzer prüft den Speichern-Status in der Kopfzeile
3. Nutzer drückt `Ctrl+Z`
4. Nutzer drückt `Ctrl+Shift+Z`

**Erwartete Ergebnisse**:
- Nach Schritt 1 zeigt die Kopfzeile „Ungespeicherte Änderungen (1)"
- Nach `Ctrl+Z` steht das Beet wieder an der ursprünglichen Position und die Kopfzeile zeigt
  „Ungespeicherte Änderungen (0)"
- Nach `Ctrl+Shift+Z` steht das Beet wieder an der verschobenen Position
- Die Schaltflächen „Rückgängig" / „Wiederholen" in der Kopfzeile spiegeln den Zustand
  (Rückgängig inaktiv, wenn der Stapel leer ist)

**Nachbedingungen**:
- Beet steht an der verschobenen Position; nicht gespeichert

**Tags**: [req-053, garden-plan, undo, redo, tastatur, desktop, gp-acc-007]

---

### TC-053-005: Beet ausschließlich mit der Tastatur verschieben, Ansage für Screenreader

**Requirement**: REQ-053 §9.4 GP-FR-021, GP-UX-009, §24 — GP-ACC-008
**Gerät**: Desktop (nur Tastatur)
**Priority**: High
**Category**: Barrierefreiheit
**Preconditions**:
- Gespeicherter Plan mit Raster 10 cm und einem Beet
- Es wird kein Zeigegerät benutzt

**Testschritte**:
1. Nutzer erreicht das Beet mit der Tabulator-Taste (Fokusrahmen sichtbar) und wählt es aus
2. Nutzer drückt dreimal Pfeil-rechts
3. Nutzer drückt einmal `Shift` + Pfeil-runter
4. Nutzer drückt `R`
5. Nutzer drückt `Esc`

**Erwartete Ergebnisse**:
- Das Beet liegt nach Schritt 2 um 3 Rasterschritte (30 cm) weiter rechts
- Eine unsichtbare Live-Region (aria-live) sagt die neue Position an; der Text enthält die
  Koordinate
- Nach Schritt 3 hat sich das Beet um 10 Rasterschritte nach unten bewegt
- `R` dreht das Beet um 15°; die Rotation steht im Panel
- `Esc` hebt die Auswahl auf

**Nachbedingungen**:
- Beet ist verschoben und gedreht; Kopfzeile zeigt „Ungespeicherte Änderungen"

**Tags**: [req-053, garden-plan, a11y, tastatur, aria-live, desktop, gp-acc-008]

---

### TC-053-006: Beet mit Pflanzpositionen verschieben und drehen — Positionen wandern mit

**Requirement**: REQ-053 §9.2a, §6 UC-03 — GP-ACC-005
**Gerät**: Desktop
**Priority**: High
**Category**: Interaktion
**Preconditions**:
- Beet mit 12 Pflanzpositionen im Reihenlayout, gespeichert (Seed-Daten oder TC-053-015)

**Testschritte**:
1. Nutzer öffnet die Gartenübersicht und merkt sich die Lage einer Pflanzposition im Beet
2. Nutzer verschiebt das Beet um 1 m und trägt im Panel die Rotation 90° ein
3. Nutzer speichert
4. Nutzer öffnet die Beetansicht (`bed-plan-tab`)

**Erwartete Ergebnisse**:
- Alle 12 Positionen bleiben im Beet an derselben Stelle relativ zum Beetrahmen und drehen
  mit
- Die Beetansicht zeigt die 12 Positionen weiterhin unverändert im Beet-Rahmen (nicht gedreht)
- Die Pflanzen stehen weiterhin an ihren Positionen; keine Position geht verloren oder verschiebt
  sich im Beet

**Nachbedingungen**:
- Beet an neuer Stelle mit Rotation 90°

**Tags**: [req-053, garden-plan, bed, rotation, slots, desktop, gp-acc-005]

---

### TC-053-007: Speichern-Status und Verlassen-Dialog bei ungespeicherten Änderungen

**Requirement**: abgeleitet aus UC-02 / GP-UX-003 (Speichern-Status, Guard-Dialog)
**Gerät**: Desktop
**Priority**: Medium
**Category**: Navigation
**Preconditions**:
- Plan geöffnet, gespeichert, mit einem Beet

**Testschritte**:
1. Nutzer verschiebt das Beet
2. Nutzer drückt `Ctrl+S`
3. Nutzer verschiebt das Beet erneut und klickt dann in der Hauptnavigation auf einen anderen
   Menüpunkt
4. Nutzer wählt im Dialog „Abbrechen"
5. Nutzer klickt erneut auf den Menüpunkt und bestätigt „Verwerfen"

**Erwartete Ergebnisse**:
- Es gibt keinen Auto-Save: die Kopfzeile zeigt nach Schritt 1 „Ungespeicherte Änderungen (1)",
  nach `Ctrl+S` kurz „Speichert…" und dann „Gespeichert"
- Beim Verlassen mit ungespeicherter Änderung erscheint ein Dialog, der nachfragt
- „Abbrechen" lässt den Nutzer im Plan; die Änderung bleibt erhalten
- „Verwerfen" navigiert weg; beim erneuten Öffnen des Plans steht das Beet an der zuletzt
  gespeicherten Position

**Nachbedingungen**:
- Zuletzt gespeicherter Stand ist unverändert

**Tags**: [req-053, garden-plan, speichern, guard-dialog, desktop, abgeleitet-uc-02]

---

### TC-053-008: Konflikt bei paralleler Bearbeitung — Dialog „Neu laden"

**Requirement**: REQ-053 GP-FR-026, GP-UX-017 — GP-ACC-011
**Gerät**: Desktop (zwei Browser-Sitzungen A und B desselben Mandanten)
**Priority**: High
**Category**: Fehlerbehandlung
**Preconditions**:
- Zwei Nutzer bzw. zwei Sitzungen haben denselben Plan zum selben Stand geöffnet
- Sitzung B hat vorher mehrere Änderungen gemacht (Undo-Stapel nicht leer)

**Testschritte**:
1. In Sitzung A verschiebt der Nutzer ein Beet und speichert
2. In Sitzung B verschiebt der Nutzer ein anderes Beet und klickt „Speichern"
3. In Sitzung B liest der Nutzer den Dialog (`plan-conflict-dialog`)
4. Nutzer wählt „Neu laden"

**Erwartete Ergebnisse**:
- Die Kopfzeile in Sitzung B zeigt „Konflikt"
- Der Dialog bietet „Neu laden" und „Meine Änderungen als Kopie behalten (JSON herunterladen)"
  (Kopie der eigenen Änderungen; Wortlaut nach GP-UX-017)
- Nach „Neu laden" zeigt Sitzung B den Plan mit der Verschiebung aus Sitzung A
- Die eigene Änderung aus Sitzung B ist verworfen, der Undo-Stapel ist leer
  („Rückgängig" inaktiv)

**Nachbedingungen**:
- Plan in B entspricht dem gespeicherten Stand aus A

**Tags**: [req-053, garden-plan, konflikt, mehrbenutzer, desktop, gp-acc-011]

---

### TC-053-009: Ansicht „Als Liste" — alle Objekte erreichbar, keine Barrierefreiheits-Verstöße

**Requirement**: REQ-053 §24, GP-UX-009 — GP-ACC-032
**Gerät**: Desktop
**Priority**: High
**Category**: Barrierefreiheit
**Preconditions**:
- Plan mit Gartengrenze, 3 Beeten und 2 Gartenobjekten (Weg, Baum)

**Testschritte**:
1. Nutzer öffnet den Plan
2. Nutzer aktiviert die Ansicht „Als Liste"
3. Nutzer geht die Liste mit der Tastatur durch und wählt einen Eintrag
4. Nutzer wechselt zurück zur Kartenansicht

**Erwartete Ergebnisse**:
- Die Liste enthält alle Objekte mit Name, Typ, Position und Maßen
- Die Auswahl eines Listeneintrags markiert das Objekt auf dem Plan (und umgekehrt)
- Die Fokusreihenfolge ist logisch, ohne Fokusfalle; Tooltips/Beschriftungen sind vorhanden
- Eine automatisierte Barrierefreiheitsprüfung meldet für Editor und Liste keine Verstöße
  (WCAG 2.1 AA)

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-053, garden-plan, a11y, liste, desktop, gp-acc-032]

---

## 2. Beetverwaltung

### TC-053-010: Beet mit aktiven Pflanzen löschen — Bestätigung mit Anzahl, Löschen wird verweigert

**Requirement**: REQ-053 §10.1 GP-FR-024, §22 — GP-ACC-012
**Gerät**: Desktop
**Priority**: High
**Category**: Negativ
**Preconditions**:
- Beet „Beet 2" mit 2 aktiven Pflanzen existiert

**Testschritte**:
1. Nutzer wählt „Beet 2" und drückt `Entf` (oder wählt „Löschen" im Kontextmenü)
2. Nutzer liest den Dialog und bestätigt das Löschen
3. Nutzer betrachtet Plan und Beetliste

**Erwartete Ergebnisse**:
- Der Dialog fordert eine Bestätigung und nennt die Anzahl der aktiven Pflanzen (2)
- Nach der Bestätigung erscheint eine Fehlermeldung, dass ein Beet mit aktiven Pflanzen nicht
  gelöscht werden kann; die Meldung nennt „2" aktive Pflanzen
- Das Beet ist weiterhin im Plan und in der Beetliste vorhanden, mit unveränderten Pflanzen

**Nachbedingungen**:
- Beet und Pflanzen unverändert

**Tags**: [req-053, bed, loeschen, validierung, desktop, gp-acc-012]

---

### TC-053-011: Bestandsbeet ohne Geometrie bleibt in der Liste, Geometrie nachtragen

**Requirement**: REQ-053 §20.3, §3.3 — GP-ACC-035
**Gerät**: Desktop
**Priority**: Medium
**Category**: Bestandsdaten
**Preconditions**:
- Seed-Daten: ein Beet, das vor REQ-053 ohne Geometrie angelegt wurde, in einer Site mit Plan
- Seed-Daten: ein Bestandsbeet mit Maßen 2,0 × 1,0 m ohne Zeichnung

**Testschritte**:
1. Nutzer öffnet die Beetliste der Site
2. Nutzer öffnet den Plan
3. Nutzer wählt das Beet ohne Geometrie in der Liste aus und vergibt im Panel Position und
   Maße (3,0 × 1,0 m)
4. Nutzer speichert

**Erwartete Ergebnisse**:
- Das Beet ohne Geometrie ist in der Beetliste vorhanden, mit einem Hinweis „nicht gezeichnet"
  o. ä.; es wird nicht auf dem Plan gerendert
- Das Bestandsbeet mit Maßen erscheint auf dem Plan als Rechteck mit diesen Maßen
- Nach dem Speichern erscheint das Beet auf dem Plan; die Fläche zeigt 3,0 m² (neu berechnet)

**Nachbedingungen**:
- Beide Beete sind in Liste und Plan vorhanden

**Tags**: [req-053, bed, bestandsdaten, geometrie, desktop, gp-acc-035]

---

### TC-053-012: Klick auf Beetliste-Zeile hebt das Beet auf dem Plan hervor

**Requirement**: REQ-053 §10.1 GP-FR-042 — GP-ACC-016
**Gerät**: Desktop
**Priority**: Medium
**Category**: Navigation
**Preconditions**:
- Site mit 3 Beeten, eines liegt außerhalb des aktuell sichtbaren Ausschnitts (Plan herangezoomt)

**Testschritte**:
1. Nutzer öffnet die Beetliste und betrachtet die Spalten
2. Nutzer klickt auf die Zeile des Beets, das außerhalb des Ausschnitts liegt

**Erwartete Ergebnisse**:
- Die Liste zeigt Name, Typ, Fläche, Status, aktive Pflanzen, offene Aufgaben und nächste
  Fälligkeit
- Das Beet ist auf dem Plan selektiert (Auswahlrahmen sichtbar)
- Der Plan scrollt/zoomt so, dass das gesamte Beet im sichtbaren Ausschnitt liegt

**Nachbedingungen**:
- Beet ausgewählt

**Tags**: [req-053, bed, beetliste, hervorhebung, desktop, gp-acc-016]

---

### TC-053-013: Beetstatus ändern — nur erlaubte Übergänge, Begründung

**Requirement**: REQ-053 §7.4, §10.1 GP-FR-046 — GP-ACC-015
**Gerät**: Desktop
**Priority**: High
**Category**: Zustandsübergang
**Preconditions**:
- Beet mit Status „aktiv"

**Testschritte**:
1. Nutzer öffnet die Beetansicht und die Statusauswahl
2. Nutzer prüft, ob „geplant" auswählbar ist
3. Nutzer wählt „aufgelöst" und trägt als Begründung „Beet wird 2027 versetzt" ein, bestätigt
4. Nutzer öffnet den Tab „Historie"

**Erwartete Ergebnisse**:
- Der Übergang von „aktiv" nach „geplant" wird nicht angeboten bzw. mit einer verständlichen
  Fehlermeldung abgelehnt
- „aufgelöst" wird übernommen; das Beet verschwindet aus dem Plan und ist über den Historie-Filter „Archivierte anzeigen" sichtbar; ein Saisonzustand „brach" ist **kein** wählbarer Status (er wird aus Pflanzungen und Rotationsplan abgeleitet)
- Die Historie enthält einen Eintrag „Statuswechsel" mit der Begründung „Beet wird 2027 versetzt"

**Nachbedingungen**:
- Beet hat Status „aufgelöst"

**Tags**: [req-053, bed, status, zustandsuebergang, historie, desktop, gp-acc-015]

---

### TC-053-014: Zelt (Indoor) in derselben Beetansicht wie Outdoor-Beet — Slot verschieben

**Requirement**: REQ-053 §9.2a — GP-ACC-036
**Gerät**: Desktop
**Priority**: High
**Category**: Konsistenz
**Preconditions**:
- Indoor-Site mit einem Zelt 1,2 × 1,2 m und 9 Pflanzpositionen (3 × 3), Seed-Daten
- Außerdem existiert ein Outdoor-Beet zum Vergleich

**Testschritte**:
1. Nutzer öffnet die Beetansicht des Zelts (`bed-detail-page`, `bed-plan-tab`)
2. Nutzer notiert Tabs, Werkzeuge und Historie-Bereich
3. Nutzer zieht die mittlere Pflanzposition um 10 cm nach rechts
4. Nutzer öffnet zum Vergleich die Beetansicht des Outdoor-Beets

**Erwartete Ergebnisse**:
- Das Zelt zeigt 9 Positionen in einem 3 × 3-Raster und einen Rahmen 1,2 × 1,2 m
- Die mittlere Position steht nach dem Ziehen 10 cm weiter rechts
- Ansicht, Tabs (Pflanzung · Pflege · Boden · Historie), Werkzeuge und Historie sind mit
  der Beetansicht des Outdoor-Beets identisch (derselbe `data-testid`-Satz, kein Zelt-Sonderpfad)

**Nachbedingungen**:
- Pflanzposition im Zelt verschoben

**Tags**: [req-053, tent, indoor, bed-plan, konsistenz, desktop, gp-acc-036]

---

## 3. Pflanzplanung

### TC-053-015: „Bepflanzen" im Reihenlayout — Vorschau und Durchlauf anlegen

**Requirement**: REQ-053 §11.1, §6 UC-05 — GP-ACC-019
**Gerät**: Desktop
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Beet mit Geometrie (z. B. 3,0 × 1,6 m — mit dem Standard-Randabstand passen in 1,2 m Tiefe nur
  eine Reihe und damit keine 6 Tomaten); Spezies Tomate mit Steckbrief vorhanden

**Testschritte**:
1. Nutzer wählt das Beet und „Bepflanzen" (Kontextmenü oder Beetansicht)
2. Nutzer wählt Spezies „Tomate", Anzahl 6, Layout „Reihen", Pflanzabstand 60 cm,
   Reihenabstand 80 cm
3. Nutzer betrachtet die Vorschau auf dem Beet
4. Nutzer entfernt in der Vorschau eine Position und fügt sie wieder hinzu
5. Nutzer klickt „Durchlauf anlegen"
6. Nutzer öffnet im Tab „Pflanzung" die geplanten Pflanzungen

**Erwartete Ergebnisse**:
- Der Dialog zeigt Fachbegriffe (Pflanzabstand, Reihenabstand, Randabstand) mit Glossar-Erklärung
- Die Vorschau zeigt 6 Positionen in Reihen mit den gewählten Abständen, alle innerhalb des Beets
  mit Randabstand
- Nach „Durchlauf anlegen" listet das Beet 6 geplante Positionen (gestricheltes Icon, Initiale
  „T", geplantes Datum)
- Der Durchlauf hat den Status „geplant"; es wurden noch keine Pflanzen angelegt

**Nachbedingungen**:
- Durchlauf „geplant" mit 6 reservierten Positionen

**Tags**: [req-053, planting, run, layout, rows, desktop, gp-acc-019]

---

### TC-053-016: Geplanten Durchlauf starten — Pflanzen entstehen an den geplanten Positionen

**Requirement**: REQ-053 §6 UC-06, §11.2 GP-FR-066 — GP-ACC-020
**Gerät**: Desktop
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Durchlauf mit 6 geplanten Positionen aus TC-053-015

**Testschritte**:
1. Nutzer öffnet den geplanten Durchlauf und wählt „Durchlauf starten" / „Pflanzen erzeugen"
   mit Zuweisung auf die geplanten Positionen
2. Nutzer öffnet den Tab „Pflanzung" der Beetansicht

**Erwartete Ergebnisse**:
- Es entstehen 6 Pflanzen; jede steht an genau einer der zuvor geplanten Positionen,
  in der geplanten Reihenfolge
- Die Liste „geplant" ist leer; „aktiv" zeigt 6 Pflanzen mit vollem Icon und Phasenfarbe
- Der Durchlauf hat den Status „aktiv"
- Ein Klick auf eine Pflanze öffnet deren Detailseite

**Nachbedingungen**:
- 6 aktive Pflanzen im Beet

**Tags**: [req-053, planting, run, create-plants, desktop, gp-acc-020]

---

### TC-053-017: Nachkultur im selben Slot — überlappendes Zeitfenster wird abgelehnt

**Requirement**: REQ-053 §11.2 GP-FR-065 — GP-ACC-039, GP-ACC-021
**Gerät**: Desktop
**Priority**: High
**Category**: Negativ
**Preconditions**:
- Beet mit einer geplanten Position, reserviert für Durchlauf A vom 15.05.2026 bis 30.09.2026

**Testschritte**:
1. Nutzer legt für dieselbe Position einen Durchlauf B mit Beginn 05.10.2026 an („Feldsalat")
2. Nutzer legt für dieselbe Position einen Durchlauf C mit Beginn 01.08.2026 an

**Erwartete Ergebnisse**:
- Durchlauf B wird akzeptiert (Nachkultur); die Position zeigt beide Reservierungen mit Datum
- Durchlauf C wird abgelehnt mit einer Meldung, dass die Position im Zeitraum 01.08.2026 bis
  30.09.2026 bereits belegt ist; es wird nichts gespeichert
- Es ist erkennbar, welcher Durchlauf den Konflikt verursacht

**Nachbedingungen**:
- Durchläufe A und B bestehen; C existiert nicht

**Tags**: [req-053, planting, zeitfenster, nachkultur, konflikt, desktop, gp-acc-039, gp-acc-021]

---

### TC-053-018: Fruchtfolge-Hinweis beim Bepflanzen — „Trotzdem pflanzen" verlangt Begründung

**Requirement**: REQ-053 §11.1, §16.2 — GP-ACC-047
**Gerät**: Desktop
**Priority**: High
**Category**: Fachregel
**Preconditions**:
- Beet, in dem 2025 Kohlgewächse (Brassicaceae) standen; Anbaupause für Kohl beträgt 4 Jahre
- Aktuelles Jahr 2026 (Seed-Daten für das Vorjahr)

**Testschritte**:
1. Nutzer öffnet „Bepflanzen" für das Beet und wählt Spezies „Blumenkohl"
2. Nutzer liest den Hinweis oberhalb der Layoutwahl
3. Nutzer wählt „Trotzdem pflanzen" und bestätigt ohne Begründung
4. Nutzer trägt eine Begründung ein und legt den Durchlauf an
5. Nutzer betrachtet das Beet in Plan und Beetansicht

**Erwartete Ergebnisse**:
- Der Dialog zeigt vor der Layout-Wahl einen Fruchtfolge-Hinweis mit Grund (Vorjahr: Kohl,
  Anbaupause 4 Jahre) und Stärke der Warnung; der Hinweis ist kein Blocker
- Ohne Begründung wird „Trotzdem pflanzen" nicht übernommen (Pflichtfeld-Meldung)
- Mit Begründung wird der Durchlauf angelegt; die Begründung ist am Durchlauf einsehbar
- Das Beet trägt danach ein Badge (Fruchtfolge-Abweichung)

**Nachbedingungen**:
- Durchlauf mit Begründung angelegt

**Tags**: [req-053, planting, fruchtfolge, warnung, begruendung, desktop, gp-acc-047]

---

### TC-053-019: Position korrigieren im Feldmodus per Long-Press-Drag

**Requirement**: REQ-053 §11.2 GP-FR-068, §18 UC-07 — GP-ACC-022
**Gerät**: Smartphone 390 × 844
**Priority**: High
**Category**: Interaktion
**Preconditions**:
- Beet mit aktiver Pflanze auf Position (0,30; 0,90) im Beet-Rahmen
- Nutzer im Feldmodus, Beet-Sheet geöffnet

**Testschritte**:
1. Nutzer tippt die Pflanze an und wählt „Position korrigieren"
2. Nutzer zieht die Pflanze per Long-Press-Drag (500 ms halten, dann ziehen) auf die Position
   (0,60; 0,90)
3. Nutzer öffnet den Tab/Bereich „Historie" des Beets
4. Nutzer tippt in einer Zone-Pflanze (Seed-Daten) auf „Position korrigieren"

**Erwartete Ergebnisse**:
- Ohne Long-Press wird die Pflanze nicht verschoben, sondern die Ansicht gepannt
- Die Pflanze steht nach dem Ziehen an der neuen Position; die Änderung wird sofort gespeichert,
  ohne „Ungespeicherte Änderungen"
- Die Historie enthält einen Eintrag „Position korrigiert" mit dem Namen der Pflanze
- Als Alternative zum Ziehen steht ein Stepper (±10 cm) zur Verfügung
- Für Pflanzen in einer Zone erscheint der Hinweis, dass sie keine Einzelposition haben

**Nachbedingungen**:
- Pflanze an neuer Position

**Tags**: [req-053, feldmodus, position-korrigieren, mobile, touch, gp-acc-022]

---

## 4. Beetpflege und Historie

### TC-053-020: Düngeaufgabe erledigen mit Produkt und Menge — Historie zeigt Eintrag

**Requirement**: REQ-053 §12.3, §13 — GP-ACC-024
**Gerät**: Desktop
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Beet 2,0 m² mit offener Aufgabe „Düngen" und zwei aktiven Pflanzen; Düngerprodukt vorhanden

**Testschritte**:
1. Nutzer öffnet in der Beetansicht den Tab „Pflege" und klickt bei der Aufgabe „Erledigt"
2. Nutzer wählt das Düngerprodukt, trägt 2 l/m² ein und wählt beide Pflanzen
3. Nutzer bestätigt
4. Nutzer öffnet den Tab „Historie"

**Erwartete Ergebnisse**:
- Die Aufgabe verschwindet aus den offenen Aufgaben
- In der Historie steht ein Eintrag „Düngen" mit Datum, dem Produkt, der Gesamtmenge (4 l für
  2,0 m² bei 2 l/m²), dem ausführenden Nutzer und den beiden Pflanzen
  (`care-event-row-<key>`)
- Schlägt das Speichern fehl (Fehler z. B. simuliert), bleibt die Aufgabe offen und in der
  Historie entsteht kein Eintrag

**Nachbedingungen**:
- Aufgabe erledigt; ein Pflegeereignis „Düngen"

**Tags**: [req-053, pflege, task, duengen, historie, desktop, gp-acc-024]

---

### TC-053-021: Erledigt-Zeitpunkt in der Zukunft oder weit in der Vergangenheit wird abgelehnt

**Requirement**: REQ-053 §13.3, §22 — GP-ACC-025
**Gerät**: Desktop
**Priority**: Medium
**Category**: Validierung
**Preconditions**:
- Beet mit offener Aufgabe

**Testschritte**:
1. Nutzer klickt bei der Aufgabe „Erledigt" und trägt als Zeitpunkt „jetzt + 10 Minuten" ein
2. Nutzer bestätigt
3. Nutzer trägt als Zeitpunkt „vor 400 Tagen" ein und bestätigt

**Erwartete Ergebnisse**:
- In beiden Fällen erscheint eine feldbezogene Fehlermeldung (Zeitpunkt in der Zukunft bzw.
  zu weit zurückliegend); das Feld ist rot markiert
- Die Aufgabe bleibt offen; es entsteht kein Eintrag in der Historie

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-053, pflege, validierung, zeitpunkt, desktop, gp-acc-025]

---

### TC-053-022: Pflegeereignis korrigieren — Original bleibt unveränderbar

**Requirement**: REQ-053 §13.2/13.3 — GP-ACC-026
**Gerät**: Desktop
**Priority**: Medium
**Category**: Zustandsübergang
**Preconditions**:
- Pflegeereignis „Düngen" mit Menge 2 l/m² in der Historie des Beets

**Testschritte**:
1. Nutzer öffnet das Ereignis in der Historie und sucht eine Bearbeiten-Funktion
2. Nutzer wählt „Korrigieren" und trägt Menge 3 l/m² ein
3. Nutzer betrachtet die Historie
4. Nutzer aktiviert den Filter „Korrigierte Einträge anzeigen"

**Erwartete Ergebnisse**:
- Das Ereignis lässt sich nicht direkt überschreiben; angeboten wird „Korrigieren"
- Die Historie zeigt standardmäßig nur den korrigierten Eintrag (3 l/m²)
- Mit dem Filter erscheinen beide Einträge; der ursprüngliche ist als „ersetzt" gekennzeichnet

**Nachbedingungen**:
- Korrigierter Eintrag ersetzt den ursprünglichen in der Standardansicht

**Tags**: [req-053, historie, korrektur, unveraenderbar, desktop, gp-acc-026]

---

### TC-053-023: Historie filtern nach Kategorie, paginiert, mit Zeitstrahl

**Requirement**: REQ-053 §13.3, §6 UC-10 — GP-ACC-027
**Gerät**: Desktop
**Priority**: Medium
**Category**: Filter
**Preconditions**:
- Beet mit 60 Pflegeereignissen über 2 Jahre (Seed-Daten), davon mehr als 50 „Gießen"

**Testschritte**:
1. Nutzer öffnet den Tab „Historie" des Beets
2. Nutzer filtert nach Kategorie „Gießen"
3. Nutzer blättert zur nächsten Seite
4. Nutzer betrachtet den Zeitstrahl

**Erwartete Ergebnisse**:
- Es erscheinen nur Gieß-Ereignisse, neueste zuerst, 50 je Seite; die zweite Seite zeigt den Rest
- Der Zeitstrahl zeigt je Jahr die Pflanzenfamilien der Pflanzungen
- Ohne Filter erscheinen alle Kategorien

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-053, historie, filter, pagination, zeitstrahl, desktop, gp-acc-027]

---

### TC-053-024: Fruchtfolge-Verlauf eines Beets in der Historie

**Requirement**: REQ-053 §16.2 — GP-ACC-028
**Gerät**: Desktop
**Priority**: Medium
**Category**: Anzeige
**Preconditions**:
- Beet mit Pflanzen 2024 (Nachtschattengewächse/Tomate) und 2025 (Hülsenfrüchte/Erbse), Seed-Daten

**Testschritte**:
1. Nutzer öffnet die Beetansicht und den Tab „Historie"
2. Nutzer betrachtet den Fruchtfolge-Verlauf der letzten Jahre
3. Nutzer schaltet in der Gartenübersicht den Jahr-Umschalter auf 2024

**Erwartete Ergebnisse**:
- Jedes Jahr zeigt die Pflanzenfamilie (2024 Solanaceae, 2025 Fabaceae) und deren Zehrerstufe
- Die Gartenübersicht färbt das Beet nach der Familie des gewählten Jahres; die Legende erklärt
  die Farben und die Farbe ist nie das einzige Merkmal (Beschriftung)
- Die Info-Blase des Beets zeigt „Vorjahr: …"

**Nachbedingungen**:
- Kein Status geändert

**Tags**: [req-053, fruchtfolge, historie, jahr-umschalter, desktop, gp-acc-028]

---

### TC-053-025: Aufgabe im Feldmodus mit zwei Tipps erledigen

**Requirement**: REQ-053 §18.1 Schritt 5, GP-UX-023 — GP-ACC-029
**Gerät**: Smartphone 390 × 844
**Priority**: Critical
**Category**: Happy Path
**Preconditions**:
- Nutzer im Feldmodus; Beet mit offener Aufgabe „Gießen" (zugewiesen an den Nutzer)

**Testschritte**:
1. Nutzer sieht die Liste „Meine Beete · heute fällig" und tippt das Beet an (Tipp 0: Auswahl)
2. Nutzer tippt im Sheet „Erledigt" (Tipp 1)
3. Nutzer tippt im Schnell-Dialog ohne weitere Eingabe „Fertig" (Tipp 2)
4. Nutzer öffnet die Historie des Beets

**Erwartete Ergebnisse**:
- Der Button „Erledigt" misst mindestens 64 × 64 px, Schrift ≥ 16 px
- Nach dem ersten Tipp ist der Button bis zur Rückmeldung gesperrt (Doppeltipp erzeugt keine
  zweite Erledigung)
- Nach „Fertig" ist die Aufgabe erledigt; sie verschwindet aus der Liste
- Die Historie enthält einen Eintrag „Gießen" ohne Mengenangabe
- Es sind genau zwei Tipps nach der Beetauswahl nötig

**Nachbedingungen**:
- Aufgabe erledigt, Pflegeereignis „Gießen" ohne Menge

**Tags**: [req-053, feldmodus, aufgabe, erledigt, mobile, touch, gp-acc-029]

---

### TC-053-026: Schnellprotokoll „Gejätet/Gemulcht" mit Rückgängig innerhalb von 8 Sekunden

**Requirement**: REQ-053 §18.2 GP-UX-029 — GP-ACC-048
**Gerät**: Smartphone 390 × 844
**Priority**: High
**Category**: Interaktion
**Preconditions**:
- Nutzer im Feldmodus, Beet-Sheet geöffnet

**Testschritte**:
1. Nutzer tippt den Chip „Gejätet/Gemulcht"
2. Nutzer liest die Snackbar und tippt „Rückgängig" innerhalb von 8 Sekunden
3. Nutzer öffnet die Historie
4. Nutzer tippt den Chip erneut und wartet 8 Sekunden ohne Eingabe

**Erwartete Ergebnisse**:
- Nach dem ersten Tipp erscheint sofort ein Eintrag „Jäten/Mulchen" in der Historie
- Die Snackbar „Rückgängig" bleibt 8 Sekunden sichtbar
- Nach „Rückgängig" ist der Eintrag in der Historie als zurückgenommen gekennzeichnet bzw. aus der
  Standardansicht verschwunden
- Wird nicht zurückgegangen, bleibt der Eintrag bestehen und die Snackbar verschwindet

**Nachbedingungen**:
- Ein zurückgenommener und ein gültiger Eintrag „Jäten/Mulchen"

**Tags**: [req-053, feldmodus, schnellprotokoll, rueckgaengig, mobile, gp-acc-048]

---

### TC-053-027: Beet räumen am Saisonende

**Requirement**: REQ-053 §10.1 GP-FR-055 — GP-ACC-040
**Gerät**: Desktop
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Beet mit 2 aktiven Durchläufen und 12 Pflanzen

**Testschritte**:
1. Nutzer öffnet das Beet und wählt „Beet räumen"
2. Nutzer wählt als Beendigungsart „abgestorben" und bestätigt
3. Nutzer betrachtet Beetansicht und Historie
4. Nutzer klickt „Bepflanzen" und legt einen neuen Durchlauf im Zonen-Layout an

**Erwartete Ergebnisse**:
- Der Dialog nennt die Anzahl der betroffenen Pflanzen (12) und Durchläufe (2)
- Alle 12 Pflanzen erscheinen nicht mehr als aktiv, sondern in der Historie mit Datum heute;
  beide Durchläufe sind „abgeschlossen"
- Die Historie enthält einen Eintrag „Beet geräumt"
- Der neue Durchlauf lässt sich im selben Beet anlegen, ohne Fehlermeldung wegen der früheren
  Positionen

**Nachbedingungen**:
- Beet ohne aktive Pflanzen; neuer Durchlauf geplant

**Tags**: [req-053, bed, beet-raeumen, saisonende, desktop, gp-acc-040]

---

### TC-053-028: Schwärzen eines Pflegeereignisses durch die Leitung

**Requirement**: REQ-053 §21.8, §26 — GP-ACC-044
**Gerät**: Desktop
**Priority**: Medium
**Category**: Datenschutz
**Preconditions**:
- Pflegeereignis mit Notiz „Nachbarin Frau Müller hat gegossen" und zwei Fotos, bereits durch
  eine Korrektur ersetzt
- Zwei Sitzungen: Gärtner und Leitung

**Testschritte**:
1. Als Gärtner öffnet der Nutzer das Ereignis und sucht die Funktion „Schwärzen"
2. Als Leitung öffnet der Nutzer dasselbe Ereignis und wählt „Schwärzen" mit Begründung
3. Nutzer betrachtet Ereignis und Vorgänger-Version in der Historie

**Erwartete Ergebnisse**:
- Der Gärtner sieht die Funktion „Schwärzen" nicht bzw. kann sie nicht ausführen
- Nach dem Schwärzen steht in beiden Versionen als Notiz „[redacted]" und die Fotos sind
  entfernt
- Die Begründung und der ausführende Nutzer sind erkennbar; der Vorgang ist nicht umkehrbar
  (Hinweis im Bestätigungsdialog)

**Nachbedingungen**:
- Ereignisse geschwärzt, Fotos gelöscht

**Tags**: [req-053, historie, datenschutz, redact, rolle-leitung, desktop, gp-acc-044]

---

## 5. Druck und Export

### TC-053-029: Plan drucken — PDF-Vorschau mit Maßstab, Nordpfeil und Legende

**Requirement**: abgeleitet aus UC-11 (Plan drucken); §23 GP-FR-142 — GP-ACC-030
**Gerät**: Desktop
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Plan mit Grenze 10 × 6 m und 3 Beeten (darunter ein Beet 2 × 1 m), Beschriftungen aktiv

**Testschritte**:
1. Nutzer klickt in der Kopfzeile „Drucken"
2. Nutzer betrachtet die Vorschau mit den Standardeinstellungen
3. Nutzer lädt das PDF herunter und öffnet es
4. Nutzer misst das Beet 2 × 1 m im PDF (Sichtprüfung am Lineal oder Maßstabsleiste)

**Erwartete Ergebnisse**:
- Die Vorschau erscheint innerhalb weniger Sekunden; voreingestellt sind „A4 quer" und
  automatischer Maßstab; der gewählte Maßstab (1:50) ist vor dem Download sichtbar
- Das PDF enthält Maßstabsleiste, Nordpfeil, Legende, Titelblock (Garten, Datum, Revision)
  und Beetbeschriftungen
- Das Beet 2 × 1 m misst im PDF etwa 40 × 20 mm
- Es sind standardmäßig keine Mitgliedernamen oder Notizen enthalten; „Zuweisungen anzeigen" ist
  eine ausdrückliche Option

**Nachbedingungen**:
- Datei heruntergeladen

**Tags**: [req-053, druck, pdf, massstab, desktop, abgeleitet-uc-11, gp-acc-030]

---

### TC-053-030: Plan als JSON sichern (Download-Sichtprüfung)

**Requirement**: abgeleitet aus UC-12 (Plan sichern); §23 GP-FR-140, GP-FR-147 — GP-ACC-031 (nur Export)
**Gerät**: Desktop
**Priority**: Medium
**Category**: Export
**Preconditions**:
- Nutzer mit Rolle Leitung
- Plan mit 5 Beeten, 20 Pflanzpositionen und 3 Gartenobjekten

**Testschritte**:
1. Nutzer wählt „Exportieren" → „JSON"
2. Nutzer öffnet die heruntergeladene Datei in einem Texteditor
3. Nutzer meldet sich als Gärtner an und prüft das Exportangebot

**Erwartete Ergebnisse**:
- Der Browser lädt eine JSON-Datei herunter
- Die Datei enthält Namen, Typen, Maße und Geometrien aller 5 Beete, der Positionen und der 3
  Gartenobjekte sowie Bodenprofile
- Die Datei enthält keine Pflanzen, Aufgaben, Ereignisse oder Fotos
- Die Wiederherstellung per Import wird in TC-053-041 geprüft

**Nachbedingungen**:
- Datei heruntergeladen; Plan unverändert

**Tags**: [req-053, export, json, sicherung, desktop, abgeleitet-uc-12, gp-acc-031]

---

## 6. Neu in v1.3 (Editor-Regeln, Pflanzeninfo, Standortmerkmale, Import)

Die folgenden Testfälle decken die Erweiterungen aus Version 1.3 ab. TC-053-037 setzt die geklärte Semantik von `Species.shade_tolerance` voraus, TC-053-042 und TC-053-044 gehören zu SHOULD-Anforderungen und laufen erst mit deren Umsetzung.

### TC-053-031: Überlappende Objekte — Stapelauswahl und Hit-Priorität

**Requirement**: REQ-053 §9.7 GP-UX-032, GP-UX-033 (abgeleitet)
**Gerät**: Desktop
**Priority**: High
**Category**: Interaktion
**Preconditions**:
- Plan mit einem Bereich „Nutzgarten“, darin ein Beet „Hochbeet 3“ mit 6 Pflanzen (Seed-Daten)

**Testschritte**:
1. Nutzer klickt auf eine Pflanze im Beet
2. Nutzer klickt auf eine freie Stelle des Beets zwischen den Pflanzen
3. Nutzer klickt auf eine Stelle im Bereich außerhalb des Beets
4. Nutzer klickt erneut an derselben Stelle auf dem Beet und hält dabei `Alt`
5. Nutzer öffnet im Panel die Liste „Objekte an dieser Stelle“

**Erwartete Ergebnisse**:
- Schritt 1 wählt die Pflanze, nicht das Beet
- Schritt 2 wählt das Beet
- Schritt 3 wählt den Bereich
- Schritt 4 wählt das nächste Objekt unter dem Beet (den Bereich)
- Die Liste nennt Pflanze, Beet und Bereich in dieser Reihenfolge; ein Klick auf einen Eintrag wählt das Objekt

**Nachbedingungen**:
- Bereich ausgewählt; nichts geändert

**Tags**: [req-053, auswahl, hit-prioritaet, stapel, desktop, gp-ux-032]

---

### TC-053-032: Touch: Beet zeichnen mit Aktionsleiste und Mehrfachauswahl

**Requirement**: REQ-053 §9.7 GP-UX-036, GP-UX-037, GP-UX-038 (abgeleitet)
**Gerät**: Smartphone 390 × 844
**Priority**: High
**Category**: Touch-Bedienung
**Preconditions**:
- Plan mit Gartengrenze und zwei Beeten; Nutzer wechselt über „Bearbeiten“ in den Editiermodus

**Testschritte**:
1. Nutzer wählt das Werkzeug „Beet“ und die Form Polygon
2. Nutzer tippt viermal „Punkt setzen“ an verschiedenen Stellen
3. Nutzer tippt „Rückgängig“ und setzt den vierten Punkt neu
4. Nutzer tippt „Fertig“
5. Nutzer wählt das Polygon und tippt „Punkt löschen“ bei einem Eckpunkt
6. Nutzer schaltet „Mehrfachauswahl“ ein und tippt die beiden anderen Beete an

**Erwartete Ergebnisse**:
- Die Aktionsleiste „Punkt setzen · Rückgängig · Fertig · Abbrechen“ ist sichtbar, jede Schaltfläche ist ≥ 48 px
- Es ist kein Long-Press nötig
- Nach „Fertig“ steht ein Beet mit Namensfeld im Panel
- Nach „Punkt löschen“ hat das Polygon einen Punkt weniger; bei nur drei Punkten ist die Schaltfläche inaktiv
- Im Mehrfachauswahl-Modus fügt jeder Tipp hinzu oder entfernt wieder; das Panel zeigt „3 Objekte ausgewählt“

**Nachbedingungen**:
- Neues Beet nicht gespeichert (Planungsmodus)

**Tags**: [req-053, touch, zeichnen, mehrfachauswahl, smartphone, gp-ux-036]

---

### TC-053-033: Touch: dichte Pflanzen — Auswahlliste „Pflanzen in der Nähe“

**Requirement**: REQ-053 §9.7 GP-UX-034, GP-UX-035 (abgeleitet)
**Gerät**: Smartphone 390 × 844
**Priority**: High
**Category**: Touch-Bedienung
**Preconditions**:
- Beet 1,2 × 2,4 m mit 40 Radieschen im Abstand 5 cm (Seed-Daten), Feldmodus

**Testschritte**:
1. Nutzer öffnet die Beetansicht und zoomt auf „An Fläche anpassen“
2. Nutzer tippt auf die Pflanzenreihe
3. Nutzer tippt in der Liste auf einen Eintrag
4. Nutzer tippt „Nächste Pflanze“

**Erwartete Ergebnisse**:
- Statt einer geratenen Einzelpflanze öffnet sich die Liste „Pflanzen in der Nähe“ als Bottom Sheet
- Die Einträge nennen Art und Slot-Nummer und sind ≥ 64 px hoch
- Der Tipp auf einen Eintrag wählt genau diese Pflanze und zeigt ihre Pflanzen-Info
- „Nächste Pflanze“ springt in Reihenfolge der Reihe weiter

**Nachbedingungen**:
- Eine Pflanze ausgewählt; nichts geändert

**Tags**: [req-053, touch, pflanzenauswahl, smartphone, gp-ux-034]

---

### TC-053-034: Pflanzen-Info beim Überfahren, ohne Nachladen

**Requirement**: REQ-053 §11.4 GP-FR-190, GP-FR-191, GP-UX-058 — GP-ACC-051
**Gerät**: Desktop
**Priority**: High
**Category**: Pflanzeninfo
**Preconditions**:
- Beet mit 40 Pflanzen, eine Tomate in der Blüte mit zwei überfälligen Aufgaben (Seed-Daten)
- Der Browser protokolliert Netzwerkaufrufe (Entwicklerwerkzeuge)

**Testschritte**:
1. Nutzer bewegt den Zeiger auf die Tomate und wartet 300 ms
2. Nutzer bewegt den Zeiger in die Info-Blase
3. Nutzer drückt `Esc`
4. Nutzer setzt den Tastaturfokus mit den Pfeiltasten auf eine andere Pflanze
5. Nutzer zieht ein Objekt (Drag) über den Plan

**Erwartete Ergebnisse**:
- Die Info-Blase erscheint nach 300 ms mit Art, Sorte, Phase samt Fortschritt („{n} d / {m} d“), Alter, Position, nächster Aufgabe und „2 Aufgaben überfällig“
- Zwischen Überfahren und Anzeige findet kein Netzwerkaufruf statt
- Die Blase bleibt sichtbar, solange der Zeiger auf ihr liegt, und verschwindet mit `Esc`
- Der Tastaturfokus zeigt dieselbe Information; der Screenreader liest sie vor
- Während des Drags erscheint keine Blase

**Nachbedingungen**:
- Nichts geändert

**Tags**: [req-053, pflanzeninfo, mouseover, a11y, desktop, gp-acc-051]

---

### TC-053-035: Pflanzenzustände am Marker — Ring, Stil, Badge, Legende, Graustufen

**Requirement**: REQ-053 §11.4 GP-FR-192, GP-UX-059, GP-UX-060, GP-UX-062 — GP-ACC-052
**Gerät**: Desktop
**Priority**: High
**Category**: Pflanzenzustand
**Preconditions**:
- Beet mit fünf Pflanzen in den Zuständen geplant, gesät, aktiv, in Ernte und ausgefallen (Seed-Daten); die aktive Pflanze hat zusätzlich einen offenen Befund und eine überfällige Aufgabe

**Testschritte**:
1. Nutzer öffnet die Beetansicht und prüft die fünf Marker
2. Nutzer öffnet die Legende
3. Nutzer schaltet in den Entwicklerwerkzeugen die Graustufen-Darstellung und die Simulation Rot-Grün-Schwäche ein
4. Nutzer wechselt in den Dark Mode

**Erwartete Ergebnisse**:
- Geplant ist gestrichelt und blass, gesät zeigt das Saatmuster, aktiv einen durchgezogenen Ring in der Phasenfarbe, in Ernte das Erntesymbol, ausgefallen ein graues Kreuz mit „Nachpflanzen“
- Die aktive Pflanze trägt genau ein Badge (Warndreieck für den Befund, nicht der rote Punkt für die überfällige Aufgabe)
- Die Legende erklärt Ringfarben, Ringstile und alle Badges
- Alle fünf Zustände bleiben in Graustufen und bei simulierter Rot-Grün-Schwäche unterscheidbar
- Im Dark Mode bleiben die Kanäle gut erkennbar (Kontrast)

**Nachbedingungen**:
- Nichts geändert

**Tags**: [req-053, pflanzenzustand, legende, a11y, desktop, gp-acc-052]

---

### TC-053-036: Sonne/Schatten am Beet erfassen — Kacheln und Stapel-Zuweisung

**Requirement**: REQ-053 §10.2 GP-FR-157 (abgeleitet)
**Gerät**: Desktop
**Priority**: High
**Category**: Standortmerkmale
**Preconditions**:
- Plan mit 30 Parzellen-Beeten (Seed-Daten), Sonne jeweils „Unbekannt“

**Testschritte**:
1. Nutzer wählt ein Beet und öffnet im Panel „Sonne/Schatten“
2. Nutzer liest die Hilfetexte der Kacheln und wählt „Halbschatten“
3. Nutzer wählt mit Rahmenauswahl 10 Parzellen und wählt „Sonne für alle gewählten Beete setzen“ → „Volle Sonne“
4. Nutzer öffnet ein beliebiges dieser Beete

**Erwartete Ergebnisse**:
- Es gibt fünf Kacheln mit Icon und Text: Volle Sonne, Halbschatten, Schatten, Tiefschatten, Unbekannt (Standard)
- Jede Kachel erklärt ihre Definition, z. B. mehr als 6 Stunden direktes Licht
- Nach der Stapel-Zuweisung zeigen alle 10 Beete „Volle Sonne“, die übrigen bleiben unverändert
- Die Beet-Zusammenfassung nennt die Sonneneinstrahlung

**Nachbedingungen**:
- Änderungen ungespeichert (Planungsmodus)

**Tags**: [req-053, standortmerkmale, sonne, schatten, desktop, gp-fr-157]

---

### TC-053-037: Eignungs-Ampel beim Bepflanzen — nicht blockierend

**Requirement**: REQ-053 §10.2 GP-FR-160 (abgeleitet); Semantik geklärt (O-16/E-05, v1.4): `light_requirement` = Anspruch, `shade_tolerance` = Toleranz, Mapping in GP-FR-160
**Gerät**: Desktop
**Priority**: Medium
**Category**: Standortmerkmale
**Preconditions**:
- Beet mit „Schatten“, Beet mit „Unbekannt“; Art Tomate (Vollsonne) im Steckbrief

**Testschritte**:
1. Nutzer wählt das Schattenbeet und öffnet „Bepflanzen“ mit Tomate
2. Nutzer legt den Durchlauf an
3. Nutzer wiederholt den Vorgang im Beet mit „Unbekannt“

**Erwartete Ergebnisse**:
- Der Dialog zeigt eine Ampel „schlecht geeignet“ mit Klartext („Beet: Schatten — Tomate braucht Vollsonne“)
- Der Durchlauf lässt sich trotzdem anlegen; es gibt keine Sperre
- Im Beet mit „Unbekannt“ erscheint kein Hinweis

**Nachbedingungen**:
- Durchläufe angelegt

**Tags**: [req-053, site-fit, eignung, desktop, gp-fr-160]

---

### TC-053-038: Bereich verschieben und löschen — Kinder wandern mit, Dialog nennt die Anzahl

**Requirement**: REQ-053 §9.7 GP-FR-151, GP-FR-153, GP-UX-043 (abgeleitet)
**Gerät**: Desktop
**Priority**: High
**Category**: Eltern-Kind
**Preconditions**:
- Bereich „Nutzgarten“ mit 3 Beeten, davon eines mit 6 Pflanzen und 2 offenen Aufgaben, plus 1 Weg (Seed-Daten)

**Testschritte**:
1. Nutzer wählt den Bereich und verschiebt ihn um 2 m
2. Nutzer drückt `Ctrl+Z`
3. Nutzer wählt den Bereich und drückt `Entf`
4. Nutzer bricht ab

**Erwartete Ergebnisse**:
- Alle enthaltenen Beete und der Weg wandern mit; ein Schritt rückgängig stellt alles wieder her
- Der Löschdialog nennt „3 Beete, 1 Objekt, 6 Pflanzen, 2 Aufgaben“; der Fokus liegt auf „Abbrechen“
- Nach „Abbrechen“ bleibt alles unverändert

**Nachbedingungen**:
- Bereich unverändert an Ursprungsposition

**Tags**: [req-053, eltern-kind, loeschen, undo, desktop, gp-fr-151]

---

### TC-053-039: Beet per Maßeingabe anlegen und Objekt mit Tastatur platzieren

**Requirement**: REQ-053 §9.7 GP-UX-046, GP-UX-044 (abgeleitet)
**Gerät**: Desktop
**Priority**: Medium
**Category**: Eingabe
**Preconditions**:
- Plan mit Gartengrenze

**Testschritte**:
1. Nutzer öffnet „Hinzufügen mit Maßen“
2. Nutzer wählt Hochbeet, Breite 1,2 m, Länge 2,4 m, Name „Hochbeet 4“, Position x 3,0 / y 2,0
3. Nutzer bestätigt
4. Nutzer drückt die Pfeiltaste nach rechts, ohne zuvor ein Objekt zu wählen
5. Nutzer wählt das Beet und drückt die Pfeiltaste nach rechts

**Erwartete Ergebnisse**:
- Das Beet erscheint mit den angegebenen Maßen und Position, ohne dass mit der Maus gezeichnet wurde
- Ohne Auswahl scrollt die Pfeiltaste den Plan
- Mit Auswahl verschiebt die Pfeiltaste das Beet um einen Rasterschritt; die Statuszeile nennt den Modus

**Nachbedingungen**:
- Beet ungespeichert

**Tags**: [req-053, hinzufuegen-mit-massen, tastatur, desktop, gp-ux-046]

---

### TC-053-040: Zoom und Beschriftung in der Übersicht — Beetnamen bleiben lesbar

**Requirement**: REQ-053 §9.7 GP-FR-150, GP-NFR-067, GP-UX-047 (abgeleitet)
**Gerät**: Desktop
**Priority**: Medium
**Category**: Darstellung
**Preconditions**:
- Plan 28 × 20 m mit 12 Beeten und je 20 Pflanzen, darunter ein sehr schmales Beet (Seed-Daten)

**Testschritte**:
1. Nutzer wählt „An Fläche anpassen“
2. Nutzer zoomt schrittweise hinein
3. Nutzer wählt das schmale Beet

**Erwartete Ergebnisse**:
- In der Übersicht tragen Beete ab 60 px Breite ihren Namen in gleichbleibender Schriftgröße; zu schmale zeigen das Typ-Icon
- Pflanzen erscheinen erst bei genug Abstand, davor als Cluster mit Zähler („{n} Pflanzen · {m} mit Handlungsbedarf“)
- Beim Hineinzoomen erscheinen Namen und Pflanzen, die Schrift springt nicht
- Maßangaben stehen nur beim ausgewählten Beet

**Nachbedingungen**:
- Nichts geändert

**Tags**: [req-053, zoom, lod, beschriftung, desktop, gp-nfr-067]

---

### TC-053-041: Plan aus JSON-Sicherung wiederherstellen — Prüfbericht und Snapshot

**Requirement**: REQ-053 §23.1 GP-FR-170 (O-18, MVP), GP-FR-147
**Gerät**: Desktop
**Priority**: High
**Category**: Import
**Preconditions**:
- Leitung; JSON-Sicherung eines Plans mit 5 Beeten; der aktuelle Plan wurde danach um ein Beet geändert und ein Beet gelöscht

**Testschritte**:
1. Nutzer öffnet „Importieren“ und wählt die Sicherungsdatei
2. Nutzer prüft den Prüfbericht
3. Nutzer wählt den Modus „Ersetzen“ und tippt zur Bestätigung den Garten-Namen
4. Nutzer bestätigt
5. Nutzer meldet sich als Gärtner an und sucht „Importieren“

**Erwartete Ergebnisse**:
- Der Prüfbericht zeigt vor dem Import Zähler (neu/geändert/entfernt), Warnungen und verworfene Verweise; es wird noch nichts geändert
- „Ersetzen“ verlangt die Eingabe des Garten-Namens und nennt den Sicherungs-Snapshot
- Danach entspricht der Plan der Sicherung (5 Beete)
- Der Gärtner sieht keinen Import-Eintrag

**Nachbedingungen**:
- Plan wiederhergestellt; Snapshot vorhanden

**Tags**: [req-053, import, wiederherstellung, snapshot, desktop, gp-fr-170]

---

### TC-053-042: Neue Saison aus Vorjahr — Struktur ohne Pflanzen

**Requirement**: REQ-053 §23.1 GP-FR-171 (SHOULD, abgeleitet)
**Gerät**: Desktop
**Priority**: Medium
**Category**: Saison
**Preconditions**:
- Plan mit 4 Beeten und Vorjahrespflanzungen (historisch); Leitung

**Testschritte**:
1. Nutzer wählt „Neue Saison aus Vorjahr“
2. Nutzer bestätigt
3. Nutzer öffnet ein Beet und die Historie

**Erwartete Ergebnisse**:
- Beete, Positionen und Zonen sind übernommen; es gibt keine aktiven Pflanzen
- Die Historie des Beets zeigt die Vorjahreskultur; Fruchtfolge-Hinweise beim Bepflanzen nutzen sie
- Der Nutzer kann ein Beet bepflanzen

**Nachbedingungen**:
- Neue Saison ohne Pflanzen

**Tags**: [req-053, saison-kopie, historie, desktop, gp-fr-171]

---

### TC-053-043: Tastaturnavigation durch den Plan — ein Tab-Stopp, Skip-Link

**Requirement**: REQ-053 §9.7 GP-NFR-068, GP-NFR-069, GP-NFR-070 (abgeleitet)
**Gerät**: Desktop
**Priority**: High
**Category**: Barrierefreiheit
**Preconditions**:
- Plan mit 12 Beeten, 200 Pflanzen; nur Tastatur und Screenreader

**Testschritte**:
1. Nutzer drückt `Tab`, bis die Zeichenfläche den Fokus hat
2. Nutzer drückt `Tab` weiter
3. Nutzer navigiert mit den Pfeiltasten zu einem Beet und drückt `Enter`
4. Nutzer drückt `Esc`
5. Nutzer löscht das Beet über das Panel, bestätigt und prüft den Fokus

**Erwartete Ergebnisse**:
- Die Zeichenfläche ist genau ein Tab-Stopp; der nächste `Tab` führt zum Panel, nicht durch 200 Pflanzen
- Ein Skip-Link „Zur Objektliste“ ist erreichbar
- `Enter` betritt das Beet, nun sind die Pflanzen fokussierbar; `Esc` führt zurück
- Nach dem Löschen liegt der Fokus auf einem Nachbarobjekt, nicht auf der Seite insgesamt
- Der Screenreader nennt Art, Phase und Handlungsbedarf jedes fokussierten Markers

**Nachbedingungen**:
- Beet gelöscht (nicht gespeichert)

**Tags**: [req-053, tastatur, roving-tabindex, screenreader, desktop, gp-nfr-068]

---

### TC-053-044: Wohnungs-Grundriss mit Fenster (SHOULD, Indoor)

**Requirement**: REQ-053 §9.8 GP-FR-180, GP-FR-181, GP-FR-033 (SHOULD, abgeleitet)
**Gerät**: Desktop
**Priority**: Low
**Category**: Indoor
**Preconditions**:
- Indoor-Site „Wohnung“ ohne Plan; Foto eines Grundrisses vorhanden

**Testschritte**:
1. Nutzer öffnet den Plan; der Leerzustand bietet das Foto als Vorlage an
2. Nutzer lädt das Foto und legt zwei Punkte mit bekannter Distanz 4,0 m fest
3. Nutzer zeichnet den Raum als Polygon und fügt ein Fenster in der Südwand hinzu
4. Nutzer legt eine Fensterbank als Möbel an und stellt einen Topf als Pflanzposition darauf

**Erwartete Ergebnisse**:
- Der Leerzustand erklärt: „Zeichne die Umrisse deiner Wohnung oder lade ein Foto als Vorlage“
- Nach der Eichung stimmen angezeigte Maße mit der Vorlage
- Das Fenster trägt die abgeleitete Himmelsrichtung Süden
- Der Topf ist bepflanzbar wie ein Beet-Slot; die Vorlage ist im Export nicht enthalten

**Nachbedingungen**:
- Plan ungespeichert; Vorlage nur Darstellung

**Tags**: [req-053, indoor, wohnung, fenster, unterlage, desktop, gp-fr-180]

---

## 7. Neu in Welle 7 (Bewässerung, Vorlagen, Editor-Werkzeuge)

Die Fälle TC-053-045 bis TC-053-055 sind aus den Anforderungen GP-FR-110, GP-FR-117, GP-UX-031,
GP-FR-044, GP-FR-045, GP-FR-012, GP-FR-029, GP-FR-025, GP-UX-004 und GP-UX-014 abgeleitet (WP 7.25).
Keine dieser Zeilen hat ein eigenes Akzeptanzkriterium; die Matrix führt sie als „abgeleitet“.

### TC-053-045: Bewässerungszone anlegen — Beete aus der Mehrfachauswahl, Ebene „Zonen“

**Requirement**: REQ-053 §14 GP-FR-110 (SHOULD, abgeleitet)
**Gerät**: Desktop
**Priority**: Medium
**Category**: Bewässerung
**Preconditions**:
- Plan mit drei Beeten „Beet A“, „Beet B“, „Beet C“ nebeneinander, noch keine Zone; Rolle Gärtner oder Leitung

**Testschritte**:
1. Nutzer wählt mit `Strg+A` alle Beete auf dem Plan aus
2. Nutzer öffnet „Bewässerungszonen verwalten“ und wählt „Neue Zone“
3. Nutzer gibt einen Namen ein und wählt „Auswahl vom Plan übernehmen“
4. Nutzer entfernt den Haken bei „Beet C“ und wählt „Zone speichern“
5. Nutzer schaltet die Ebene „Bewässerungszonen anzeigen“ ein
6. Nutzer wählt „Beet A“, dann „Beet C“ und liest die Beet-Info im Eigenschaftenpanel

**Erwartete Ergebnisse**:
- „Auswahl vom Plan übernehmen“ hakt alle drei ausgewählten Beete an
- Nach dem Speichern zeigt der Bereich den Stand der gespeicherten Zone; gespeichert sind genau „Beet A“ und „Beet B“
- Die Ebene schraffiert und umrandet genau „Beet A“ und „Beet B“, „Beet C“ bleibt ohne Schraffur
- Die Beet-Info von „Beet A“ lautet „Bewässerungszone: 1. <Name>“; die von „Beet C“ nennt keine Zone

**Nachbedingungen**:
- Eine Zone mit zwei Beeten ist gespeichert

**Tags**: [req-053, bewaesserung, zone, mehrfachauswahl, ebene, desktop, gp-fr-110]

---

### TC-053-046: Gießrunde einer Zone — Menge nach Beetfläche verteilt und als verteilt gekennzeichnet

**Requirement**: REQ-053 §14 GP-FR-117 (SHOULD, abgeleitet); Gießdienst ZG-004
**Gerät**: Desktop
**Priority**: Medium
**Category**: Bewässerung
**Preconditions**:
- Zone mit „Beet A“ (2 m²) und „Beet B“ (3 m²), noch kein Gießen erfasst (Zustand per API hergestellt)

**Testschritte**:
1. Nutzer öffnet „Bewässerungszonen verwalten“ und die Zone
2. Nutzer wählt „Gießrunde protokollieren“
3. Nutzer gibt 10 Liter ein, lässt „Nach Beetfläche“ gewählt und schreibt eine Übergabenotiz
4. Nutzer wählt „Gießrunde speichern“ und schließt das Ergebnis

**Erwartete Ergebnisse**:
- Vor der Runde zeigt der Stand der Zone „Noch kein Gießen erfasst.“
- Der Dialog erklärt: „Die Menge wird auf die Beete verteilt und nicht gemessen. Das Protokoll kennzeichnet das so.“
- Das Ergebnis nennt „Beet A: 4 Liter“ und „Beet B: 6 Liter“ und den Hinweis „Nach Fläche verteilt: Diese Mengen sind verteilt, nicht gemessen.“
- Jedes Beet hat genau einen Gieß-Eintrag mit seinem Anteil, gekennzeichnet als „nach Fläche verteilt“ (nicht gemessen), mit der Übergabenotiz
- Der Stand der Zone kennzeichnet das letzte Gießen als „Nach Fläche verteilt“

**Nachbedingungen**:
- Zwei Gieß-Einträge (verteilt) gespeichert

**Tags**: [req-053, bewaesserung, giessrunde, verteilt, desktop, gp-fr-117]

---

### TC-053-047: Gießrunde „Regen — übersprungen“

**Requirement**: REQ-053 §14 GP-FR-117 (SHOULD, abgeleitet); F-05
**Gerät**: Desktop
**Priority**: Low
**Category**: Bewässerung
**Preconditions**:
- Zone mit zwei Beeten; Gießdienst an einem Regentag

**Testschritte**:
1. Nutzer öffnet die Gießrunde der Zone
2. Nutzer wählt „Regen — übersprungen“ und bestätigt

**Erwartete Ergebnisse**:
- Die Runde ist als übersprungen protokolliert, ohne Gießmenge und ohne dass ein Beet als gegossen gilt
- Der Stand der Zone und die Ebene „zuletzt gegossen“ bleiben unverändert

**Nachbedingungen**:
- Übersprungene Runde protokolliert

**Automatisierung**: `tests/e2e/test_req053_wave9_export.py::test_tc_053_047_rain_skipped_logs_rain_without_amount_and_keeps_tasks_open`
(seit Version 1.12; die Aktion kam mit WP 9.13). Der Fall prüft zusätzlich: je Beet genau ein Regen-Eintrag ohne Menge
mit der Notiz der Runde, kein Gieß-Eintrag, eine offene Gieß-Aufgabe bleibt offen.

**Tags**: [req-053, bewaesserung, giessrunde, regen, desktop, gp-fr-117]

---

### TC-053-048: Ebene „zuletzt gegossen“ — Tage seit dem letzten Gießen je Beet

**Requirement**: REQ-053 §18 GP-UX-031 (SHOULD, abgeleitet); Klassen nach Entscheidung in #2466
**Gerät**: Desktop
**Priority**: Medium
**Category**: Bewässerung
**Preconditions**:
- Plan mit drei Beeten; „Beet A“ heute gegossen, „Beet B“ vor fünf Tagen, „Beet C“ nie (Zustand per API hergestellt)

**Testschritte**:
1. Nutzer öffnet den Plan bei 100 % und schaltet die Ebene „Zuletzt gegossen anzeigen“ ein
2. Nutzer liest die Legende
3. Nutzer wählt „Beet B“, dann „Beet C“ und liest die Beet-Info

**Erwartete Ergebnisse**:
- Die Ebene ist zu Beginn ausgeschaltet
- „Beet A“ trägt das Muster „0 bis 1 Tag seit“ und die Beschriftung „0 Tage seit“ (bzw. „1 Tag seit“ kurz nach Mitternacht UTC), „Beet B“ das Muster „4 bis 7 Tage seit“ mit „5 Tage seit“
- „Beet C“ bleibt ohne Schraffur
- Die Legende nennt die Klassen, „Ohne Schraffur: kein Gießen erfasst.“ und „Ob ein Beet Wasser braucht, sagt der Plan nicht.“
- Die Beet-Info von „Beet B“ lautet „Zuletzt gegossen: 5 Tage seit“, die von „Beet C“ „Kein Gießen erfasst.“

**Nachbedingungen**:
- Keine Änderung am Plan

**Tags**: [req-053, bewaesserung, ebene, zuletzt-gegossen, desktop, gp-ux-031]

---

### TC-053-049: Beet aus Vorlage platzieren — gedreht, sofort gespeichert

**Requirement**: REQ-053 §10.1 GP-FR-044 (SHOULD, abgeleitet)
**Gerät**: Desktop
**Priority**: Medium
**Category**: Vorlagen
**Preconditions**:
- Plan mit Gartengrenze, ohne Beet; System-Vorlage „Beet 2 × 1 m“ vorhanden

**Testschritte**:
1. Nutzer wählt in der Werkzeugleiste „Aus Vorlage“ und in der Liste „Beet 2 × 1 m“
2. Nutzer wählt einmal „Drehen“
3. Nutzer wählt „In die Bildmitte setzen“

**Erwartete Ergebnisse**:
- Nach der Wahl lautet der Hinweis „Klicke auf den Plan, um das Beet zu setzen. Alt hält den Rasterfang an, Esc beendet.“
- Die Schaltfläche zeigt „Drehen (aktuell 90°)“
- Die Meldung „Das Beet wurde aus der Vorlage angelegt und ist gespeichert. Zum Zurücknehmen lösche das Beet.“ erscheint; es bleibt keine Änderung offen
- Das gespeicherte Beet ist eine Kopie der Vorlage: Beettyp, 2,0 × 1,0 m, um 90° gedreht, Verweis auf die Vorlage, Ursprung auf dem 10-cm-Raster; es ist auf dem Plan ausgewählt

**Nachbedingungen**:
- Ein Beet aus der Vorlage gespeichert

**Tags**: [req-053, vorlagen, platzieren, desktop, gp-fr-044]

---

### TC-053-050: Standardgröße im Dialog „Hinzufügen mit Maßen“

**Requirement**: REQ-053 §10.1 GP-FR-045 (SHOULD, abgeleitet)
**Gerät**: Desktop
**Priority**: Medium
**Category**: Vorlagen
**Preconditions**:
- Plan mit Gartengrenze

**Testschritte**:
1. Nutzer öffnet „Hinzufügen mit Maßen“
2. Nutzer wählt die Standardgröße „Hochbeet 2 × 1 × 0,8 m“
3. Nutzer gibt den Namen „Hochbeet Standard“ und die Position x 3 / y 6 ein, bestätigt und speichert

**Erwartete Ergebnisse**:
- Die Schnellwahl füllt Breite 2, Länge 1, Höhe 0,8 und den Beettyp Hochbeet
- Nach dem Bestätigen ist das Beet eine ungespeicherte Änderung; nach dem Speichern steht es mit 2,0 × 1,0 m, Höhe 0,8 m und Beettyp Hochbeet an (3,0 | 6,0)

**Nachbedingungen**:
- Hochbeet gespeichert

**Tags**: [req-053, vorlagen, standardgroesse, hinzufuegen-mit-massen, desktop, gp-fr-045]

---

### TC-053-051: Objekt-Snap an der Ecke eines Nachbarbeets, `Alt` schaltet ab

**Requirement**: REQ-053 §9.4 GP-FR-012 (Objekt-Snap SHOULD, abgeleitet); GP-FR-154
**Gerät**: Desktop
**Priority**: Medium
**Category**: Editor
**Preconditions**:
- „Beet A“ mit rechter Kante bei x = 3,53 m (bewusst neben dem Raster), „Beet B“ bei x = 5,5 m auf gleicher Höhe; Zoom 100 %

**Testschritte**:
1. Nutzer zieht „Beet B“ um 1,95 m nach links, bis es fast an „Beet A“ stößt
2. Nutzer macht den Schritt rückgängig und zieht dieselbe Strecke mit gehaltener `Alt`-Taste
3. Nutzer macht den Schritt rückgängig, zieht ohne `Alt` und speichert

**Erwartete Ergebnisse**:
- Während des Ziehens zeigt eine Markierung das Einrasten an einer Ecke
- „Beet B“ rastet an der Ecke von „Beet A“ ein (x = 3,53 m) — eine Position, die das Raster allein nicht ergibt
- Mit `Alt` rastet nichts ein (x = 3,55 m)
- Gespeichert ist die eingerastete Position

**Nachbedingungen**:
- „Beet B“ liegt an „Beet A“ an

**Tags**: [req-053, snap, objekt-snap, alt, desktop, gp-fr-012]

---

### TC-053-052: Ausrichten und gleichmäßig verteilen

**Requirement**: REQ-053 §9.4 GP-FR-029 (SHOULD, abgeleitet)
**Gerät**: Desktop
**Priority**: Medium
**Category**: Editor
**Preconditions**:
- Drei versetzte Beete: A (1,0 | 2,0, 2 m breit), B (4,5 | 3,0, 2 m breit), C (7,0 | 2,5, 1 m breit)

**Testschritte**:
1. Nutzer wählt mit `Strg+A` alle Beete aus
2. Nutzer wählt „Ausrichten“ → „Unten ausrichten“
3. Nutzer wählt „Ausrichten“ → „Horizontal gleichmäßig verteilen“ und speichert

**Erwartete Ergebnisse**:
- Nach dem Ausrichten liegen alle Unterkanten auf y = 2,0 m; „Beet A“ bewegt sich nicht
- Beim Verteilen bleiben die äußeren Beete stehen, „Beet B“ rückt auf x = 4,0 m (Abstände je 1,0 m)
- Jede Aktion ist ein Schritt; gespeichert sind die neuen Positionen

**Nachbedingungen**:
- Drei Beete ausgerichtet und verteilt

**Tags**: [req-053, ausrichten, verteilen, mehrfachauswahl, desktop, gp-fr-029]

---

### TC-053-053: Mehrfach duplizieren mit Namensschema

**Requirement**: REQ-053 §9.4 GP-FR-025 (Mehrfach duplizieren SHOULD, abgeleitet); F-10
**Gerät**: Desktop
**Priority**: Medium
**Category**: Editor
**Preconditions**:
- „Beet 1“ (1,0 × 1,0 m) bei (1,0 | 4,5)

**Testschritte**:
1. Nutzer wählt „Beet 1“ und im Menü „Mehr“ den Eintrag „Mehrfach duplizieren“
2. Nutzer gibt Anzahl 3, Namensschema „Parzelle {n}“ und Abstand 0,5 ein und wählt „Duplizieren“
3. Nutzer drückt `Strg+Z`, danach `Strg+Umschalt+Z`, und speichert

**Erwartete Ergebnisse**:
- Der Dialog nennt vorab „Die Kopien heißen: Parzelle 1 … Parzelle 3“
- Drei Kopien erscheinen rechts neben „Beet 1“; ein einziges `Strg+Z` nimmt alle drei zurück, `Strg+Umschalt+Z` bringt alle drei wieder
- Gespeichert sind „Parzelle 1“ bis „Parzelle 3“ mit 1,0 × 1,0 m bei x = 2,5 / 4,0 / 5,5 m

**Nachbedingungen**:
- Vier Beete gespeichert

**Tags**: [req-053, duplizieren, mehrfach, namensschema, undo, desktop, gp-fr-025]

---

### TC-053-054: Automatisch speichern — pausiert bei Konflikt

**Requirement**: REQ-053 §17 GP-UX-004 (SHOULD, abgeleitet); GP-ACC-011 (Konflikt-Dialog)
**Gerät**: Desktop
**Priority**: Medium
**Category**: Speichern
**Preconditions**:
- Plan mit „Beet A“ und „Beet B“; während des Tests speichert eine zweite Sitzung eine Änderung an „Beet B“ (per API hergestellt)

**Testschritte**:
1. Nutzer schaltet „Automatisch speichern“ ein
2. Nutzer verschiebt „Beet A“ per Pfeiltaste und wartet, ohne zu speichern
3. Eine zweite Sitzung speichert „Beet B“ an neuer Position
4. Nutzer verschiebt „Beet A“ erneut
5. Nutzer wählt im Konflikt-Dialog „Neu laden“ und verschiebt „Beet A“ noch einmal

**Erwartete Ergebnisse**:
- Die erste Verschiebung wird ohne Klick gespeichert
- Bei der zweiten öffnet sich der Konflikt-Dialog; die Statuszeile lautet „Konflikt – Plan wurde zwischenzeitlich geändert“ und darunter steht „Automatisches Speichern pausiert, solange der Konflikt offen ist.“
- Die Änderung der zweiten Sitzung bleibt erhalten; die abgelehnte Verschiebung wird nicht gespeichert
- Nach „Neu laden“ ist der Hinweis weg, die Einstellung bleibt an, und die nächste Verschiebung wird wieder automatisch gespeichert

**Nachbedingungen**:
- Plan gespeichert, keine offene Änderung

**Tags**: [req-053, auto-save, konflikt, speichern, desktop, gp-ux-004]

---

### TC-053-055: Mini-Map — nur beim Hineinzoomen, folgt der Ansicht, Klick springt

**Requirement**: REQ-053 §17 GP-UX-014 (SHOULD, abgeleitet)
**Gerät**: Desktop
**Priority**: Low
**Category**: Navigation
**Preconditions**:
- Plan 10 × 10 m mit zwei Beeten in gegenüberliegenden Ecken

**Testschritte**:
1. Nutzer öffnet den Plan (eingepasst, ganzer Garten sichtbar)
2. Nutzer zoomt auf 400 %
3. Nutzer verschiebt die Ansicht dreimal mit `Umschalt+Pfeil rechts`
4. Nutzer klickt in die Mitte der Mini-Map

**Erwartete Ergebnisse**:
- Solange der ganze Garten sichtbar ist, gibt es keine Mini-Map
- Bei 400 % erscheint rechts unten die Mini-Map (120 × 120 px) mit dem Rechteck des sichtbaren Ausschnitts
- Das Rechteck wandert mit der Ansicht nach rechts
- Der Klick zentriert die Ansicht auf die angeklickte Stelle

**Nachbedingungen**:
- Keine Änderung am Plan

**Tags**: [req-053, mini-map, navigation, zoom, desktop, gp-ux-014]

---

## 8. Neu in Welle 7, Teil B (Pflanzenzustand, Teilexport, frühere Stände, Sonnenfenster im Feld)

Die Fälle TC-053-056 bis TC-053-059 sind aus den Anforderungen GP-UX-061, GP-FR-169, GP-FR-172,
GP-FR-148/170 und GP-FR-158/159 mit GP-UX-057 abgeleitet (WP 7.26). Die neue Saison (GP-FR-171) und die
Unterlage mit Eichung (GP-FR-033) sind bereits als TC-053-042 und TC-053-044 beschrieben; sie bekommen
keinen neuen Fall. Keine dieser Zeilen hat ein eigenes Akzeptanzkriterium; die Matrix führt sie als
„abgeleitet“.

### TC-053-056: Ebenen „Pflanzenzustand“ und „Sonnenfenster“, Filter „Nur Pflanzen mit Handlungsbedarf“

**Requirement**: REQ-053 §8 GP-UX-061, GP-FR-031, GP-FR-169 (SHOULD, abgeleitet)
**Gerät**: Desktop
**Priority**: Medium
**Category**: Ebenen
**Preconditions**:
- Plan mit einem Beet „Beet 1“ (2 × 1 m) und drei Tomaten; eine davon hat eine überfällige Aufgabe
- Für „Beet 1“ ist als Sonnenfenster „Morgens“ erfasst; Ebenen im Ausgangszustand (alle aus außer Raster)

**Testschritte**:
1. Nutzer öffnet den Plan und betrachtet die Schaltfläche „Nur Pflanzen mit Handlungsbedarf zeigen“
2. Nutzer schaltet die Ebene „Pflanzenzustand anzeigen“ ein
3. Nutzer schaltet „Nur Pflanzen mit Handlungsbedarf zeigen“ ein
4. Nutzer schaltet die Ebene „Pflanzenzustand anzeigen“ wieder aus
5. Nutzer schaltet die Ebene „Sonnenfenster anzeigen“ ein

**Erwartete Ergebnisse**:
- Solange die Ebene „Pflanzenzustand“ aus ist, ist der Filter nicht bedienbar und sagt, warum
- Mit der Ebene trägt jede Tomate ihren Ring, genau die Pflanze mit der überfälligen Aufgabe ein Zeichen; die Legende erklärt den Pflanzenzustand
- Mit dem Filter bleibt nur die Pflanze mit dem Zeichen sichtbar, die beiden anderen verschwinden
- Ohne die Ebene sind wieder alle drei Pflanzen als einfache Marker zu sehen; der Filter ist wieder nicht bedienbar
- Die Ebene „Sonnenfenster“ legt über „Beet 1“ das Muster für „Morgens“

**Nachbedingungen**:
- Keine Änderung am Plan; die Ebenen-Wahl gilt nur für diesen Browser

**Tags**: [req-053, ebenen, pflanzenzustand, filter, sonnenfenster, desktop, gp-ux-061, gp-fr-169]

---

### TC-053-057: Nur die Auswahl sichern und in einen anderen Standort einspielen

**Requirement**: REQ-053 §23.1 GP-FR-172 (SHOULD, abgeleitet), GP-UX-050, GP-UX-051
**Gerät**: Desktop
**Priority**: Medium
**Category**: Export/Import
**Preconditions**:
- Standort A mit „Beet A“ (zwei Pflanzplätze), „Beet B“ und „Beet C“ nebeneinander; Standort B mit Gartengrenze, ohne Beete; Leitung

**Testschritte**:
1. Nutzer zieht im Plan von Standort A einen Auswahlrahmen um „Beet A“ und „Beet B“
2. Nutzer öffnet „Export & Import“ → „Plan exportieren …“, wählt „JSON-Sicherung“ und „Nur die Auswahl“ und lädt herunter
3. Nutzer öffnet den Plan von Standort B, dann „Sicherung einspielen …“ und wählt die Datei
4. Nutzer liest den Prüfbericht und geht weiter
5. Nutzer wählt „Hinzufügen“ und als Ziel „Aus einem anderen Standort“, prüft erneut und spielt ein

**Erwartete Ergebnisse**:
- Der Auswahlrahmen wählt genau „Beet A“ und „Beet B“
- Die Vorschau nennt 2 Standorte, 0 Gartenobjekte und 2 Pflanzplätze; der Hinweis nennt die 2 ausgewählten Beete
- Der Prüfbericht nennt 2 Standorte und 2 Pflanzplätze, die angelegt werden, und keine Probleme
- Nach dem Einspielen meldet der Dialog die angelegten 2 Standorte und 2 Pflanzplätze
- Standort B zeigt „Beet A“ und „Beet B“ (mit den zwei Pflanzplätzen) als eigene, neue Beete; Standort A ist unverändert

**Nachbedingungen**:
- Standort B enthält zwei Beete

**Tags**: [req-053, export, import, teilexport, ziel, desktop, gp-fr-172]

---

### TC-053-058: Früheren Stand wiederherstellen

**Requirement**: REQ-053 §23.1 GP-FR-148, GP-FR-170 (abgeleitet)
**Gerät**: Desktop
**Priority**: Medium
**Category**: Import
**Preconditions**:
- Plan mit „Beet A“, „Beet B“, „Beet C“; danach kam „Beet D“ hinzu, und eine Sicherung des Stands ohne „Beet D“ wurde per „Ersetzen“ eingespielt — es gibt genau einen früheren Stand (mit vier Beeten); Leitung

**Testschritte**:
1. Nutzer öffnet „Export & Import“ → „Sicherung einspielen …“ → „Früheren Stand wiederherstellen …“
2. Nutzer wählt den Stand mit vier Standorten
3. Nutzer liest den Bericht und tippt zur Bestätigung den Namen des Standorts
4. Nutzer wählt „Diesen Stand wiederherstellen“

**Erwartete Ergebnisse**:
- Die Liste nennt den Stand mit seinen Zählern (4 Standorte)
- Vor dem Schreiben zeigt der Bericht, was angelegt (4) und gelöscht (3) würde, und der Hinweis sagt, dass der jetzige Plan vorher selbst als Stand gespeichert wird
- „Diesen Stand wiederherstellen“ ist erst mit dem richtigen Namen bedienbar
- Danach meldet der Dialog den Erfolg samt gespeichertem Vorstand; der Plan zeigt wieder „Beet A“ bis „Beet D“
- Es gibt nun zwei frühere Stände

**Nachbedingungen**:
- Plan wiederhergestellt; der überschriebene Stand liegt als neuer früherer Stand vor

**Tags**: [req-053, snapshot, wiederherstellung, import, desktop, gp-fr-148, gp-fr-170]

---

### TC-053-059: Sonnenfenster im Feldmodus mit Chips erfassen

**Requirement**: REQ-053 §19 GP-FR-158, GP-FR-159, GP-UX-057 (SHOULD, abgeleitet)
**Gerät**: Smartphone 390 × 844
**Priority**: Medium
**Category**: Standortmerkmale
**Preconditions**:
- Plan mit einem Beet „Beet 1“, für das noch kein Sonnenfenster erfasst ist; Rolle Gärtner oder Leitung

**Testschritte**:
1. Nutzer öffnet den Feldmodus und tippt auf „Beet 1“
2. Nutzer tippt im Abschnitt „Sonne am Beet“ auf den Chip „Nachmittags“
3. Nutzer gibt „6,5“ als Sonnenstunden im Sommer ein und bestätigt mit der Eingabetaste
4. Nutzer öffnet den Feldmodus neu und tippt wieder auf „Beet 1“

**Erwartete Ergebnisse**:
- Vorher ist „Nicht bekannt“ gewählt; jeder Chip ist mindestens 64 × 64 px groß
- Ein Tipp genügt: „Nachmittags“ ist gewählt und ohne Speichern-Schaltfläche gespeichert
- Die Stunden werden als 6,5 gespeichert
- Nach dem Neuladen sind „Nachmittags“ und „6,5“ wieder zu sehen

**Nachbedingungen**:
- Sonnenprofil von „Beet 1“: Nachmittags, 6,5 Stunden

**Tags**: [req-053, feldmodus, sonnenfenster, chips, smartphone, gp-fr-158, gp-ux-057]

---

### TC-053-060: Messprofil Interaktion — INP für Auswahl, Drag-Start und Zoom, Pinch-Frametime, Feldmodus bei 4-facher CPU-Drosselung

**Requirement**: REQ-053 §9.7 GP-NFR-071 (SHOULD, abgeleitet)
**Gerät**: Desktop und Smartphone 390 × 844
**Priority**: Low
**Category**: Performance
**Preconditions**:
- Plan mit einem Beet „Beet 1“; Chrome mit Event-Timing-Schnittstelle; für das Low-End-Profil eine Sitzung, die die CDP-Drosselung zulässt

**Testschritte**:
1. Nutzer wählt das Beet mit einem Klick, beginnt einen Drag und zoomt per Schaltfläche und mit Strg + Mausrad; die Messung liest je Szenario die längste Interaktion
2. Nutzer öffnet den Plan auf dem Smartphone im Planungsmodus und spreizt zwei Finger
3. Nutzer öffnet den Feldmodus mit auf das Vierfache gedrosselter CPU und tippt auf das Beet

**Erwartete Ergebnisse**:
- Je Szenario liegt ein Messwert vor (INP in ms oder „unter 16“); eine fehlende Messung ist ein Fehler
- Beratend (kein Gate): INP ≤ 200 ms, Pinch-Frametime (95. Perzentil) ≤ 33 ms; eine Überschreitung wird als Warnung berichtet
- Ist die Drosselung in der Sitzung nicht verfügbar, steht das als benannte Lücke im Bericht, die Messung läuft ungedrosselt

**Nachbedingungen**:
- Keine; der Bericht liegt als Tabelle in der Testausgabe und als JSON bei den Screenshots

**Tags**: [req-053, performance, inp, pinch, feldmodus, desktop, smartphone, gp-nfr-071]

---

## 9. Neu in Welle 8, Teil A (Welle 8 Teil A — Boden, Dosierung, Nährstoff-Hinweis, Historie als CSV, Rotation, Vorschläge)

Die Fälle TC-053-061 bis TC-053-071 sind aus den Zeilen GP-FR-104, 122, 123, 124, 125, 133, 135 und 086 abgeleitet
(WP 8.30, #2673) und für das E2E-Modul „Welle 8 Teil A“ gedacht. Keine dieser SHOULD-Zeilen hat ein eigenes
Akzeptanzkriterium; die Matrix führt sie als „abgeleitet“. Die Texte in Anführungszeichen sind mit den deutschen
Oberflächentexten (`src/frontend/src/i18n/locales/de/`) abgeglichen. Der Nährstoff-Hinweis (GP-FR-125) ist ausgeliefert ohne belegte Schwelle und zeigt
deshalb im Normalzustand nichts (§15.3, „Inert-Gefahr“); TC-053-065 prüft diesen Zustand, TC-053-066 die Gegenprobe mit
einer in der Testumgebung aktivierten Schwelle (derzeit nicht automatisierbar, siehe dort). Vorschläge (GP-FR-086) haben in Welle 8 keinen Erzeuger; die
Testdaten legen sie als Seed-Daten an (Aufgabe über die API, Vorschlags-Markierung direkt in der Datenbank).

### TC-053-061: Bodenanalyse erfassen — Verlauf pH/EC/Humus je Methode

**Requirement**: REQ-053 §15.1, §15.2 GP-FR-122 (SHOULD, abgeleitet)
**Gerät**: Desktop
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Bodenbeet „Beet 1“ (3,6 m²) ohne Bodenanalyse; Rolle Gärtner oder Leitung
- Das Beet ist gespeichert; der Tab „Boden“ ist erreichbar (Stand TC-053-014 für die Tab-Struktur)

**Testschritte**:
1. Nutzer öffnet die Beetansicht, den Tab „Boden“ und wählt „Bodenanalyse erfassen“
2. Nutzer trägt pH 6,4, Methode „CaCl₂-Lösung“, „Probe genommen am“ vor 300 Tagen ein und wählt „Analyse speichern“
   (der Dialog nimmt höchstens 365 Tage zurück)
3. Nutzer erfasst eine zweite Analyse: pH 6,8, Methode „CaCl₂-Lösung“, Datum heute, über „Weiteren Wert hinzufügen“ Humus 3 %
4. Nutzer erfasst eine dritte Analyse: pH 7,2, Methode „Wasser“, Datum heute
5. Nutzer betrachtet das Verlaufsdiagramm und schaltet „Als Tabelle anzeigen“ ein

**Erwartete Ergebnisse**:
- Der Dialog bietet Messgröße, Wert, Einheit, Methode, Entnahmetiefe und Herkunft an; die Fingerprobe zur Bodenart bleibt erhalten
- Das Diagramm „Verlauf pH-Wert“ zeigt für „CaCl₂-Lösung“ eine Linie mit zwei Punkten und für „Wasser“ eine eigene Linie mit einem Punkt;
  die Werte der beiden Methoden werden **nicht** ineinander umgerechnet
- Der Wechsel der Methode ist im Diagramm gekennzeichnet (Marke „Methodenwechsel“, nicht nur Farbe)
- Die Tabellen-Ansicht nennt dieselben drei Werte mit Datum und Methode (Alternative für Screenreader)
- Das Profil im Tab „Boden“ zeigt den zuletzt gemessenen Stand (heute: pH 7,2 „Wasser“, Humus 3 %); nach dem Neuladen ist
  der Verlauf unverändert

**Nachbedingungen**:
- Drei Bodenanalysen am Beet; Profil trägt den jüngsten Stand

**Tags**: [req-053, welle-8, boden, bodenanalyse, verlauf, diagramm, desktop, gp-fr-122]

---

### TC-053-062: Bodenanalyse — Gehaltsklasse nur vom Labor, ältere Analyse überschreibt nicht, Zukunftsdatum abgelehnt

**Requirement**: REQ-053 §15.1, §15.2 GP-FR-122; §22 V-11 (SHOULD, abgeleitet); Review-Akzeptanz Bodenanalyse (WP 8.7)
**Gerät**: Desktop
**Priority**: Medium
**Category**: Validierung
**Preconditions**:
- Bodenbeet „Beet 1“ mit einer Analyse von heute (pH 6,8, Methode „CaCl2“), wie nach TC-053-061

**Testschritte**:
1. Nutzer öffnet „Bodenanalyse erfassen“ und wählt als Messgröße „Phosphor (P)“, Methode „CAL“, Herkunft „Testset“
2. Nutzer prüft, ob eine „Gehaltsklasse“ (A–E) auswählbar ist; danach wechselt er die Herkunft auf „Labor“
3. Nutzer erfasst eine Analyse pH 5,9, Methode „CaCl₂-Lösung“, Datum vor 200 Tagen, und speichert
4. Nutzer erfasst eine Analyse mit Datum „morgen“
5. Nutzer erfasst einen EC-Wert ohne Angabe der Messmethode

**Erwartete Ergebnisse**:
- Bei Herkunft „Testset“ gibt es kein Feld „Gehaltsklasse“; erst bei „Labor“ und „CAL“ ist sie wählbar und wird nur übernommen,
  nicht berechnet
- Die ältere Analyse erscheint im Verlauf an ihrer Stelle in der Zeitachse; das Profil zeigt weiter den Stand von heute (pH 6,8)
- Das Datum „morgen“ wird mit der Feldmeldung „Der Zeitpunkt liegt in der Zukunft.“ abgelehnt; der Dialog bleibt offen,
  es entsteht kein Eintrag
- Der EC-Wert ohne Methode wird nicht gespeichert: Die Methode ist für EC Pflicht, die Feldmeldung lautet „Wähle die
  Messmethode – ohne sie ist der Wert nicht lesbar.“; es entsteht kein Eintrag und kein Hinweis „Salzgehalt prüfen“

**Nachbedingungen**:
- Zusätzlich die ältere Analyse im Verlauf; Profil unverändert

**Tags**: [req-053, welle-8, boden, bodenanalyse, validierung, desktop, gp-fr-122]

---

### TC-053-063: Düngen mit Flächendosis — Gesamtmenge live berechnet, ohne Fläche gesperrt

**Requirement**: REQ-053 §15.2 GP-FR-123, §12.3 (SHOULD, abgeleitet); Review-Akzeptanz Flächendosierung (WP 8.9). Ergänzt TC-053-020 (l/m²-Fall)
**Gerät**: Desktop
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Beet „Beet 1“ mit Fläche 3,6 m² und eine offene Aufgabe „Düngen“; ein Düngerprodukt mit Datenblatt-Rate 80 g/m²
- Beet „Beet 2“ ohne Fläche (Bestandsbeet ohne Geometrie, TC-053-011) mit offener Aufgabe „Düngen“

**Testschritte**:
1. Nutzer öffnet im Tab „Pflege“ von „Beet 1“ bei der Aufgabe „Erledigt“ und wählt das Düngerprodukt
2. Nutzer liest die vorbelegte Dosis und die Gesamtmenge
3. Nutzer ändert die Dosis auf 100 g/m², danach wieder auf 80 g/m², und bestätigt
4. Nutzer wechselt die Einheit auf „Liter pro m²“, trägt 3 ein und prüft die Gesamtmenge, ohne zu bestätigen
5. Nutzer trägt Dosis 0 ein und wählt „Erledigt“
6. Nutzer öffnet im Tab „Historie“ den Eintrag „Düngen“
7. Nutzer öffnet bei „Beet 2“ denselben Dialog und prüft die Einheiten

**Erwartete Ergebnisse**:
- Die Dosis ist mit 80 „Gramm pro m²“ vorbelegt („Menge pro m² aus dem Datenblatt des Produkts.“); die Gesamtmenge zeigt
  „Gesamtmenge für 3,6 m²: 288 g“ und ändert sich beim Tippen sofort (100 g/m² → 360 g)
- Bei 3 „Liter pro m²“ zeigt die Gesamtmenge „10,8 L“
- Dosis 0 wird beim Speichern mit der Feldmeldung „Eine Menge pro m² muss größer als 0 sein.“ abgelehnt; der Dialog bleibt
  offen und es entsteht kein Eintrag
- Der Historien-Eintrag nennt Produkt und Dosis („80 Gramm pro m²“); die Gesamtmenge 288 g steht am gespeicherten Eintrag
  (die Historienzeile zeigt nur die Dosis)
- Bei „Beet 2“ sind die Einheiten „Gramm pro m²“ und „Liter pro m²“ deaktiviert, der Hinweis lautet „Das Beet hat keine
  Fläche. …“; die Gesamtmenge entfällt
- Die Näherungsangabe beginnt mit „Näherung: ≈ … kg N/ha“; es erscheint keine Warnung vor einer Saisonsumme

**Nachbedingungen**:
- Ein Pflegeereignis „Düngen“ mit 80 g/m² und 288 g Gesamtmenge an „Beet 1“

**Tags**: [req-053, welle-8, pflege, duengen, flaechendosierung, desktop, gp-fr-123]

---

### TC-053-064: Bodenverbesserung erfassen — Kompost, Mulch, Kalk mit Hinweistext

**Requirement**: REQ-053 §12.1, §15.2 GP-FR-124 (SHOULD, abgeleitet)
**Gerät**: Desktop
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Bodenbeet „Beet 1“ (3,6 m²) mit offener Aufgabe „Bodenverbesserung“ und einer weiteren „Kalkung“; Rolle Gärtner oder Leitung

**Testschritte**:
1. Nutzer öffnet bei der Aufgabe „Bodenverbesserung“ den Dialog „Erledigt“ und öffnet die Materialauswahl
2. Nutzer wählt „Kompost“, trägt 3 „Liter“ ein und bestätigt
3. Nutzer erfasst über „Pflege protokollieren“ (Kategorie „Mulchen“) eine Mulchschicht mit Material „Rindenmulch“
4. Nutzer öffnet bei der Aufgabe „Kalkung“ den Dialog und liest den Hinweis
5. Nutzer wählt das Material „Kalk“, trägt eine Menge ein und bestätigt
6. Nutzer öffnet den Tab „Historie“

**Erwartete Ergebnisse**:
- Die Materialliste der Bodenverbesserung enthält Kompost, Mist, Hornspäne, Gesteinsmehl, Pflanzenkohle, Sand, Perlite,
  Kaffeesatz, Gründüngung, Schwefel, Kalk, Holzasche und „Sonstiges“ (Freitext bleibt möglich); die Mulch-Materialien
  (Stroh, Grasschnitt, Rindenmulch, Holzhäcksel, Laub, Pappe, Kompost) bietet die Kategorie „Mulchen“ an, die Kalkung
  Kalk, Holzasche und „Sonstiges“
- Der Kalkungs-Dialog trägt den Hinweis „Kalk und Holzasche heben den pH-Wert. Bringe sie nicht aus, wenn der Boden schon
  über dem Ziel-pH liegt, und nicht bei säureliebenden Pflanzen … Eine Kalkmenge berechnet die App nicht.“ als reinen Text;
  das Mengenfeld bleibt leer, es wird keine Menge vorgeschlagen
- Die Historie enthält die drei Einträge „Bodenverbesserung“ (Kompost), „Mulchen“ (Rindenmulch) und „Kalkung“ (Kalk) mit
  Material, Menge und Datum
- Die offenen Aufgaben „Bodenverbesserung“ und „Kalkung“ sind erledigt

**Nachbedingungen**:
- Drei Pflegeereignisse in der Historie

**Tags**: [req-053, welle-8, pflege, bodenverbesserung, kompost, kalkung, desktop, gp-fr-124]

---

### TC-053-065: Nährstoff-Hinweis im Ausgangszustand — keine Zahl, keine Düngemenge, keine Kalkmenge

**Requirement**: REQ-053 §15.2 GP-FR-125, §15.3 (SHOULD, abgeleitet); Review-Akzeptanz Nährstoff-Hinweis (WP 8.10, 8.8)
**Gerät**: Desktop
**Priority**: High
**Category**: Negativ
**Preconditions**:
- Bodenbeet „Beet 1“ mit aktiver Tomate (Starkzehrer im Steckbrief), Vorjahr Erbse, letzte Düngung vor 120 Tagen
- Bodenprofil: Füllung „Gewachsener Boden“, Bodenart bekannt (z. B. Lehm), Ziel-pH 6,5 laut Labor – ohne diese Angaben
  zeigt der Tab „Boden“ nur die Begründung, warum er den Kalkbedarf nicht einschätzt, und der begründete Hinweis erscheint nie
- Laborklasse Phosphor „D“ (Quelle Labor, Methode CAL) und eine Analyse mit niedrigem pH in der Historie
- Ausgelieferte Konfiguration: keine Schwelle mit Quelle aktiv

**Testschritte**:
1. Nutzer öffnet die Beetansicht und betrachtet den Beetkopf
2. Nutzer öffnet den Tab „Boden“ und liest den Hinweis zur Kalkung
3. Nutzer sucht im Beetkopf, in der Beet-Zusammenfassung und im Tab „Boden“ nach einer Düngemenge oder Kalkmenge

**Erwartete Ergebnisse**:
- Der Beetkopf zeigt keinen Chip „Düngebedarf wahrscheinlich“ und keinen Chip „Düngung prüfen“ (die Einschätzung bleibt ohne belegte Schwelle unbestimmt)
- Es erscheint keine Zahl, die wie ein Messwert oder eine Empfehlung wirkt (weder g/m², kg/ha noch Liter)
- Der Hinweis zur Kalkung ist, falls vorhanden, nur ein Text (z. B. „Kalkung wahrscheinlich sinnvoll.“ oder eine
  „Kalkbedarf: …“-Begründung) ohne Mengenangabe
- Ein Hinweis auf Kompost oder Phosphordünger wird nicht gegeben, weil die Laborklasse Phosphor „D“ vorliegt; Kompost als Bodenverbesserung (TC-053-064) bleibt weiter erfassbar
- Der Hinweis „Salzgehalt prüfen“ fehlt, weil keine Schwelle aktiv ist

**Nachbedingungen**:
- Nichts geändert

**Tags**: [req-053, welle-8, naehrstoff-hinweis, ohne-zahl, kalkbedarf, inert, desktop, gp-fr-125]

---

### TC-053-066: Nährstoff-Hinweis mit aktivierter Testschwelle — Chip und Begründung, nie eine Menge

**Requirement**: REQ-053 §15.3 GP-FR-125 (SHOULD, abgeleitet); Gegenprobe zu TC-053-065
**Automatisierung**: übersprungen (`pytest.skip` mit Grund). Die Schwellen sind Code-Konstanten (`DEFAULT_CONFIG` in
`src/backend/app/domain/engines/nutrient_hint_engine.py`; `NutrientHintService` wird in
`src/backend/app/common/dependencies.py` ohne Konfiguration gebaut); es gibt keine Umgebungsvariable und keine
Einstellung, über die der E2E-Stack eine Testschwelle mit Quelle aktivieren kann.
**Gerät**: Desktop
**Priority**: High
**Category**: Fachregel
**Preconditions**:
- Testumgebung, in der für die Düngeregel eine Testschwelle mit Quelle aktiv ist (Starkzehrer: Hinweis nach 30 Tagen, Prüfung nach 14 Tagen)
- „Beet 1“ mit Tomate (Starkzehrer), letzte Düngung vor 45 Tagen; „Beet 2“ mit Tomate, letzte Düngung vor 20 Tagen; „Beet 3“ mit Tomate, letzte Düngung vor 5 Tagen; „Beet 4“ mit Bohne (Stickstoff-Fixierer) und Rindenmulch nach der letzten Düngung
- Ein Beet mit Boden-EC über der Testschwelle, gemessen mit der passenden Methode

**Testschritte**:
1. Nutzer öffnet nacheinander die Beetansichten von „Beet 1“ bis „Beet 4“ und liest jeweils den Beetkopf
2. Nutzer öffnet den Chip von „Beet 1“ und liest die Begründung
3. Nutzer öffnet das Beet mit der hohen Boden-EC

**Erwartete Ergebnisse**:
- „Beet 1“ trägt den Chip „Düngebedarf wahrscheinlich“, „Beet 2“ den Chip „Düngung prüfen“, „Beet 3“ keinen Chip
- Die Begründung nennt Gründe im Klartext (z. B. „letzte Düngung lange her“) und den Satz „Eine Düngemenge nennt die App nicht.“; der Hinweis ist nie als Messwert beschriftet und enthält keine Zahl mit Mengeneinheit
- „Beet 4“ zeigt die Begründung „Rindenmulch kann Stickstoff binden“ ohne Mengenangabe
- Das Beet mit hoher Boden-EC zeigt einen eigenen Chip „Salzgehalt prüfen“ mit Begründung; der Code erscheint nicht zusätzlich in der Begründungsliste des Nährstoff-Chips

**Nachbedingungen**:
- Nichts geändert

**Tags**: [req-053, welle-8, naehrstoff-hinweis, chip, ohne-zahl, gegenprobe, desktop, gp-fr-125]

---

### TC-053-067: Historie als CSV herunterladen — Inhalt, Härtung, Gesamtseite

**Requirement**: REQ-053 §13 GP-FR-104, SR-016 (SHOULD, abgeleitet). Ergänzt TC-053-023 (Filter der Historie)
**Gerät**: Desktop
**Priority**: High
**Category**: Export
**Preconditions**:
- Beet „Beet 1“ mit mehreren Pflegeereignissen „Gießen“, darunter eines mit dem Text „=1+1“ und eines mit dem Text
  „@Hinweis“, sowie einem Ereignis „Düngung“, ausgeführt von einer Person mit Anzeigename (z. B. „Anna Beispiel“)
- Zweites Beet „Beet 2“ mit eigenen Ereignissen; Rolle Leitung

**Testschritte**:
1. Nutzer öffnet den Tab „Historie“ von „Beet 1“, filtert auf die Kategorie „Gießen“ und wählt „CSV exportieren“ →
   „CSV (Komma)“
2. Nutzer öffnet die heruntergeladene Datei in einem Tabellenprogramm und in einem Texteditor
3. Nutzer öffnet die Seite „Historie aller Beete“ und lädt von dort ebenfalls „CSV exportieren“ → „CSV (Komma)“ herunter

**Erwartete Ergebnisse**:
- Der Browser lädt eine Datei mit Endung „.csv“ herunter; sie enthält eine Kopfzeile und nur die Ereignisse von „Beet 1“ der gewählten Kategorie
- Die Datei ist UTF-8 mit Byte-Order-Mark; Umlaute werden im Tabellenprogramm richtig angezeigt
- Zellen, die mit „=“, „+“, „-“, „@“ beginnen, beginnen in der Datei mit einem vorangestellten Hochkomma; das Tabellenprogramm rechnet nichts aus
- Die Spalte der ausführenden Person (`performed_by`) zeigt den Anzeigenamen der Person, nie einen Kontoschlüssel
- Die CSV der Seite „Historie aller Beete“ enthält auch die Ereignisse von „Beet 2“

**Nachbedingungen**:
- Nichts geändert

**Tags**: [req-053, welle-8, historie, csv, export, formelhaertung, desktop, gp-fr-104]

---

### TC-053-068: Rotationsmatrix — Beet × Jahr, Familie als Liste, Nacherfassung aus der Zelle

**Requirement**: REQ-053 §16 GP-FR-135 (SHOULD, abgeleitet). Ergänzt TC-053-024 (Verlauf je Beet)
**Gerät**: Desktop und Smartphone 390 × 844
**Priority**: High
**Category**: Anzeige
**Preconditions**:
- Site mit drei Beeten mit Fruchtfolge: „Beet 1“ 2025 Vorkultur Feldsalat und Hauptkultur Tomate (Nachtschatten, Starkzehrer), 2026 Erbse (Hülsenfrüchte); „Beet 2“ 2025 Kohl; „Beet 3“ mit ausgeschalteter Fruchtfolge (Pflanzgefäß)
- Abweichung der Automatisierung: Das Produkt kennt keine Rolle „Vorkultur“ – eine Vorkultur ist ein zweiter Eintrag
  desselben Jahres mit der Saison „Frühjahr“, die Hauptkultur trägt „Hauptsaison“; die Zelle unterscheidet beide über
  diese Saison-Beschriftung. Feldsalat fehlt im Seed-Katalog, der Test nutzt Salat (Lactuca sativa). Die Erbse des
  laufenden Jahres ist eine echte Pflanzung (Nacherfassen nimmt nur vergangene Jahre). Jahre relativ zum laufenden Jahr.
- „Beet 2“ hat für 2024 keine Angabe; ein Fruchtfolgeplan enthält für 2027 „Beet 1“: Möhre

**Testschritte**:
1. Nutzer öffnet die Rotationsmatrix der Site
2. Nutzer liest Spaltenköpfe, Zellen und Legende und schaltet die Darstellung in den Entwicklerwerkzeugen auf Graustufen
3. Nutzer tippt die leere Zelle „Beet 2 / 2024“
4. Nutzer wählt im Dialog „Was stand hier 2024?“ die „Pflanzenfamilie“ Kürbisgewächse (Cucurbitaceae) und wählt „Speichern“
5. Nutzer tippt eine Zelle von „Beet 1“ und wählt den Sprung zum Beet
6. Nutzer öffnet dieselbe Matrix auf dem Smartphone

**Erwartete Ergebnisse**:
- Zeilen sind die Beete, Spalten die Jahre (mindestens die Anbaupause, hier fünf Jahre); die Kopfzeile bleibt beim Scrollen sichtbar
- „Beet 1 / 2025“ nennt als Liste beide Einträge (Feldsalat als Vorkultur, Tomate als Hauptkultur) mit Familie, Zehrerstufe als Text und Kürzel/Muster; die Zelle für 2027 zeigt die geplante Möhre
- „Beet 3“ ist als ohne Fruchtfolge gekennzeichnet (z. B. „Von der Fruchtfolge-Prüfung ausgenommen“)
- In Graustufen bleiben die Familien über Kürzel oder Muster unterscheidbar
- Nach dem Bestätigen zeigt „Beet 2 / 2024“ die Kürbisgewächse; die Historie von „Beet 2“ führt 2024 ebenfalls auf (selbe Aussage wie die Matrix)
- Der Sprung öffnet die Beetansicht von „Beet 1“
- Auf dem Smartphone ist die Tabelle horizontal scrollbar, ohne dass die Seite selbst seitlich wandert

**Nachbedingungen**:
- Nacherfassung für „Beet 2“ im Jahr 2024

**Tags**: [req-053, welle-8, fruchtfolge, rotationsmatrix, nacherfassung, desktop, smartphone, gp-fr-135]

---

### TC-053-069: Folgekultur-Empfehlung unter dem Zeitstrahl und Schalter „Fruchtfolge für dieses Beet“

**Requirement**: REQ-053 §16 GP-FR-133 (SHOULD, abgeleitet); Schalter aus WP 8.14 (GP-FR-137 UI)
**Gerät**: Desktop
**Priority**: Medium
**Category**: Fachregel
**Preconditions**:
- „Beet 1“: Vorjahr Tomate (Starkzehrer); Steckbriefe von Kohlrabi (Mittelzehrer), Salat (Schwachzehrer) und einer Art ohne gespeicherte Zehrerstufe liegen vor
- „Beet 2“ ohne Historie

**Testschritte**:
1. Nutzer öffnet den Tab „Historie“ von „Beet 1“ und betrachtet den Bereich unter dem Zeitstrahl
2. Nutzer öffnet den Tab „Historie“ von „Beet 2“
3. Nutzer stellt im Tab „Boden“ von „Beet 1“ im Abschnitt „Fruchtfolge für dieses Beet“ die „Fruchtfolge-Prüfung“ auf
   „Eingeschaltet“ und schaltet zusätzlich „Dauerkultur (von der Fruchtfolge ausgenommen)“ ein
4. Nutzer lädt die Seite neu

**Erwartete Ergebnisse**:
- Unter dem Zeitstrahl steht die „Folgekultur-Empfehlung“ mit „Nach <Vorjahr> (Starkzehrer) passt als Nächstes:
  Mittelzehrer.“ und einer Liste geeigneter Familien/Arten dieser Stufe; sie nennt keine Düngemengen
- Die Art ohne gespeicherte Zehrerstufe erscheint nicht in der Liste und wird nicht mit einer erfundenen Stufe gezeigt
- „Beet 2“ zeigt keine Empfehlung, sondern den Hinweis „Es ist noch kein Jahr erfasst. …“
- Beide Schalter gleichzeitig an werden mit „Eine Dauerkultur kann die Fruchtfolge-Prüfung nicht eingeschaltet haben. …
  Es wurde nichts geändert.“ abgelehnt und nicht gespeichert
- Nach dem Neuladen steht der zuletzt gültige Schalterzustand

**Nachbedingungen**:
- Schalter „Fruchtfolge“ am Beet im gültigen Zustand

**Tags**: [req-053, welle-8, fruchtfolge, folgekultur, empfehlung, desktop, gp-fr-133]

---

### TC-053-070: Vorgeschlagene Aufgabe annehmen

**Requirement**: REQ-053 §12 GP-FR-086, GP-API-040 (SHOULD, abgeleitet)
**Gerät**: Desktop
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- Seed-Daten: „Beet 1“ mit einer vorgeschlagenen Aufgabe „Gießen“ und dem Grund „ET0-Bedarf 4,2 L/m² seit 3 Tagen“; „Beet 2“ ohne Vorschlag; Rolle Gärtner oder Leitung
- Es gibt in Welle 8 keinen Erzeuger für Vorschläge, deshalb die Seed-Daten

**Testschritte**:
1. Nutzer öffnet den Tab „Pflege“ von „Beet 2“
2. Nutzer öffnet den Tab „Pflege“ von „Beet 1“ und liest den Abschnitt „Vorschläge“
3. Nutzer klickt bei dem Vorschlag auf „Annehmen“
4. Nutzer betrachtet die offenen Aufgaben und die Historie

**Erwartete Ergebnisse**:
- Bei „Beet 2“ gibt es keinen Abschnitt „Vorschläge“
- Bei „Beet 1“ erscheint der Abschnitt „Vorschläge (1)“ mit der Aufgabe, dem Grund im Klartext („Grund: …“) und den
  Schaltflächen „Annehmen“ und „Verwerfen“
- Nach „Annehmen“ verschwindet der Eintrag aus „Vorschläge“; die Aufgabe „Gießen“ steht als normale offene Aufgabe in der Liste
- In der Historie entsteht durch das Annehmen kein Pflegeereignis (erst das Erledigen schreibt eines)
- Nach dem Neuladen bleibt die Aufgabe offen und der Abschnitt „Vorschläge“ ist leer bzw. ausgeblendet

**Nachbedingungen**:
- Die Aufgabe ist eine reguläre offene Aufgabe

**Tags**: [req-053, welle-8, aufgaben, vorschlag, annehmen, desktop, gp-fr-086]

---

### TC-053-071: Vorgeschlagene Aufgabe verwerfen — und Rolle „Betrachter“

**Requirement**: REQ-053 §12 GP-FR-086, GP-API-040 (SHOULD, abgeleitet). Variante zu TC-053-070
**Gerät**: Desktop
**Priority**: Medium
**Category**: Negativ
**Preconditions**:
- Seed-Daten: „Beet 1“ mit zwei vorgeschlagenen Aufgaben „Gießen“ und „Düngen“, jeweils mit Grund; ein zweiter Nutzer mit der Rolle Betrachter

**Testschritte**:
1. Als Betrachter öffnet der Nutzer den Tab „Pflege“ von „Beet 1“
2. Als Gärtner klickt der Nutzer bei „Düngen“ auf „Verwerfen“
3. Nutzer betrachtet die offenen Aufgaben, den Abschnitt „Vorschläge“ und die Historie
4. Nutzer aktiviert in der Aufgabenliste den Filter für erledigte/abgebrochene Aufgaben

**Erwartete Ergebnisse**:
- Der Betrachter sieht die Vorschläge lesend, aber keine Schaltflächen „Annehmen“ und „Verwerfen“
- Nach „Verwerfen“ ist „Düngen“ aus dem Abschnitt „Vorschläge“ verschwunden und taucht nicht als offene Aufgabe auf; „Gießen“ bleibt unberührt im Abschnitt
- In der Historie entsteht kein Pflegeereignis
- Die verworfene Aufgabe erscheint nur im Filter der abgebrochenen Aufgaben, mit dem Vermerk, dass sie verworfen wurde
  (Stand Welle 8: der Pflege-Tab hat keinen solchen Filter; der Zustand „übersprungen“ ist nur am Server ablesbar)

**Nachbedingungen**:
- „Düngen“ verworfen; „Gießen“ weiter als Vorschlag

**Tags**: [req-053, welle-8, aufgaben, vorschlag, verwerfen, rollen, desktop, gp-fr-086]

---

## 10. Neu in Welle 8, Teil B (Welle 8 Teil B — Mischkultur, Standortmerkmale, Erreichbarkeit, Fotos, CSV, Frost-Grund)

Die Fälle TC-053-072 bis TC-053-082 sind aus den Zeilen GP-FR-051, 134, 145, 161, 162, 163, 166, 168, 174, 175, GP-UX-057
und §11.4 abgeleitet (WP 8.31, #2674) und für das E2E-Modul „Welle 8 Teil B“ gedacht. Keine dieser Zeilen hat ein
eigenes Akzeptanzkriterium; die Matrix führt sie als „abgeleitet“. Die Texte in Anführungszeichen sind Platzhalter.
Berührungsziele im Feldmodus messen mindestens 64 × 64 px (wie TC-053-025 und TC-053-059).

### TC-053-072: Ebene „Mischkultur“ — grüne, rote und graue Verbindungen mit Grund und Score

**Requirement**: REQ-053 §16 GP-FR-134 (SHOULD, abgeleitet); REQ-028 §7.3
**Gerät**: Desktop
**Priority**: High
**Category**: Ebenen
**Preconditions**:
- Plan mit vier Beeten nebeneinander: Beet A (Tomate), Beet B (Basilikum, verträglich mit Tomate), Beet C (Fenchel, unverträglich mit Tomate), Beet D (eine Art ohne Angabe zur Verträglichkeit); alle Beete grenzen aneinander
- Ebenen im Ausgangszustand

**Testschritte**:
1. Nutzer öffnet den Plan und das Ebenen-Menü
2. Nutzer schaltet die Ebene „Mischkultur“ ein
3. Nutzer bewegt den Zeiger auf die Verbindung Tomate–Basilikum, dann auf Tomate–Fenchel (Touch: Tipp)
4. Nutzer öffnet die Legende
5. Nutzer zoomt so weit heraus, dass die Pflanzen nur noch als Cluster erscheinen
6. Nutzer schaltet die Ebene wieder aus
7. Nutzer öffnet für Tomate den Dialog „Bepflanzen“ neben Fenchel und liest den Mischkultur-Hinweis (Vergleich)

**Erwartete Ergebnisse**:
- Vor dem Einschalten sind keine Verbindungslinien sichtbar
- Mit der Ebene verbindet eine grüne Linie (durchgezogen) Tomate und Basilikum, eine rote (gestrichelt) Tomate und Fenchel, eine graue (gepunktet) Verbindungen zur Art ohne Angabe; der Status ist nie nur an der Farbe erkennbar
- Hover bzw. Tipp zeigt Grund und Score der Verbindung im Klartext
- Die Legende erklärt Farbe und Linienstil der drei Zustände
- In der Cluster-Stufe zeichnet die Ebene keine Linien, ohne eine Fehlermeldung
- Ohne die Ebene verschwinden die Linien wieder
- Der Dialog „Bepflanzen“ nennt für Tomate/Fenchel denselben Befund (unverträglich) wie die rote Linie

**Nachbedingungen**:
- Keine Änderung am Plan; die Ebenen-Wahl gilt nur für diesen Browser

**Tags**: [req-053, welle-8, ebenen, mischkultur, overlay, legende, desktop, gp-fr-134]

---

### TC-053-073: Standortmerkmale am Beet erfassen — Mikroklima, Wind, Hang und abgeleitete Ausrichtung

**Requirement**: REQ-053 §10.2 GP-FR-162, GP-FR-163, GP-FR-168 (SHOULD/COULD, abgeleitet). Ergänzt TC-053-036 (Sonne/Schatten)
**Gerät**: Desktop
**Priority**: Medium
**Category**: Standortmerkmale
**Preconditions**:
- Plan mit „Beet 1“ (Hochbeet 2 × 1 m) und einem Weg; Rolle Gärtner oder Leitung
- Vor dem Test hat „Beet 1“ keine Standortmerkmale außer Sonne „Unbekannt“

**Testschritte**:
1. Nutzer wählt „Beet 1“ und öffnet im Eigenschaftenpanel den Abschnitt „Standort“
2. Nutzer wählt als Frostrisiko „Hoch“ und schaltet „Kaltluftsenke“ ein
3. Nutzer wählt als Windlage „Windig“
4. Nutzer trägt Hangneigung 8° und Exposition 200° ein und liest die Ausrichtung
5. Nutzer wählt als Zugangsseiten „Beidseitig“
6. Nutzer speichert, lädt die Seite neu und öffnet die Beet-Zusammenfassung
7. Nutzer setzt das Frostrisiko wieder auf „Normal“ und speichert

**Erwartete Ergebnisse**:
- Jede Auswahl hat einen erklärenden Hilfetext (Glossar); Frostrisiko, Windlage und Zugangsseiten sind Auswahlfelder, kein Freitext
- Die Ausrichtung wird aus der Exposition abgeleitet und nur angezeigt (200° → Süd-Südwest bzw. „Süd“, je nach Achtteilung der Oberfläche); sie ist nicht mehr manuell pflegbar, solange die Exposition gesetzt ist
- Es wird keine Hangneigung vom Standort vererbt: ohne eigene Eingabe bleibt das Feld leer
- Nach dem Neuladen zeigen Panel und Beet-Zusammenfassung dieselben Werte; Drainage/Wasserregime stehen zusätzlich in der Zusammenfassung
- Das Frostrisiko „Hoch“ erscheint in der Zusammenfassung mit Schneeflocke und Text; nach dem Zurücksetzen ist es wieder „Normal“

**Nachbedingungen**:
- Standortmerkmale gespeichert (Frostrisiko wieder „Normal“)

**Tags**: [req-053, welle-8, standortmerkmale, mikroklima, wind, hang, desktop, gp-fr-162, gp-fr-163, gp-fr-168]

---

### TC-053-074: Eignungs-Ampel um Frost, Wind und Drainage — nicht blockierend, unbekannt ohne Hinweis

**Requirement**: REQ-053 §10.2 GP-FR-161 (SHOULD, abgeleitet). Erweitert TC-053-037 (Licht)
**Gerät**: Desktop
**Priority**: Medium
**Category**: Standortmerkmale
**Preconditions**:
- Art Tomate (frostempfindlich, braucht Stützen) im Steckbrief
- „Beet F“: Frostrisiko „Hoch“; „Beet W“: Windlage „Windig“; „Beet N“: Drainage „Staunass“ und eine Art ohne Staunässe-Toleranz; „Beet U“: alle Merkmale „Unbekannt“; „Beet G“: Frostrisiko „Normal“, windgeschützt, gut drainiert

**Testschritte**:
1. Nutzer öffnet für „Beet F“ den Dialog „Bepflanzen“ mit Tomate und liest die Ampel
2. Nutzer legt den Durchlauf an
3. Nutzer öffnet in „Beet W“ den Dialog mit Tomate
4. Nutzer öffnet in „Beet N“ den Dialog mit der Art ohne Staunässe-Toleranz
5. Nutzer öffnet „Bepflanzen“ in „Beet U“ und „Beet G“

**Erwartete Ergebnisse**:
- „Beet F“ zeigt einen Hinweis mit Klartext zum Frostrisiko („Beet: Frostgefährdet — Tomate ist frostempfindlich“); er blockiert nicht, der Durchlauf lässt sich anlegen
- „Beet W“ weist darauf hin, dass die Pflanze Stützen braucht, wenn das Beet windig ist
- „Beet N“ weist auf das Risiko von Staunässe hin
- In „Beet U“ erscheint für diese Merkmale kein Hinweis; in „Beet G“ ebenfalls nicht
- Die Hinweise treten zusätzlich zur Lichtampel auf; die Lichtampel bleibt wie in TC-053-037

**Nachbedingungen**:
- Durchlauf in „Beet F“ angelegt

**Tags**: [req-053, welle-8, site-fit, frost, wind, drainage, eignung, desktop, gp-fr-161]

---

### TC-053-075: Feldmodus-Kurzbefragung — Chips „Feucht/Normal/Trocken“ und „Windig“ bei 390 px

**Requirement**: REQ-053 §18, §10.2 GP-UX-057, GP-FR-162/163 (SHOULD, abgeleitet). Ergänzt TC-053-059 (Sonnenfenster-Chips)
**Gerät**: Smartphone 390 × 844
**Priority**: High
**Category**: Standortmerkmale
**Preconditions**:
- Beet „Beet 1“ ohne Angabe zum Wasserregime und zur Windlage; Rolle Gärtner oder Leitung; Feldmodus

**Testschritte**:
1. Nutzer öffnet den Feldmodus und tippt auf „Beet 1“
2. Nutzer tippt im Abschnitt „Boden“ den Chip „Trocken“
3. Nutzer tippt den Chip „Windig“
4. Nutzer tippt nochmals „Windig“ und dann „Normal“
5. Nutzer öffnet den Feldmodus neu und tippt wieder auf „Beet 1“
6. Nutzer misst die Größe der Chips

**Erwartete Ergebnisse**:
- Der Beet-Sheet enthält die Chip-Gruppen Sonne (TC-053-059), „Feucht / Normal / Trocken“ und „Windig“, kein Formular mit weiteren Feldern
- Vor der Wahl ist keiner der drei Wasser-Chips gewählt
- Ein Tipp genügt: „Trocken“ ist gewählt und ohne Speichern-Schaltfläche gespeichert; „Windig“ ist an
- Das zweite Tippen auf „Windig“ schaltet den Chip wieder aus; „Normal“ ersetzt „Trocken“
- Nach dem Neuladen sind „Normal“ gewählt und „Windig“ aus
- Jeder Chip misst mindestens 64 × 64 px; die Seite scrollt nicht seitlich

**Nachbedingungen**:
- Wasserregime „Normal“, Windlage nicht windig

**Tags**: [req-053, welle-8, feldmodus, chips, standortmerkmale, smartphone, 390px, touch, gp-ux-057]

---

### TC-053-076: Erreichbarkeits-Hinweis — nur Hinweis, nie Fehler

**Requirement**: REQ-053 §10.2 GP-FR-166 (SHOULD, abgeleitet)
**Gerät**: Desktop
**Priority**: Medium
**Category**: Fachregel
**Preconditions**:
- Plan mit vier Beeten: „Breit“ (1,3 × 3,0 m, kein angrenzender Weg), „Breit mit Weg“ (1,3 × 3,0 m, an beiden Längsseiten ein Weg), „Grenzwert“ (1,2 × 3,0 m, kein Weg), „Schmal einseitig“ (0,7 × 3,0 m, Zugangsseiten „Einseitig“, kein Weg)
- Standardschwellen (1,2 m beidseitig, 0,6 m einseitig)

**Testschritte**:
1. Nutzer wählt „Breit“ und betrachtet Beet-Zusammenfassung und Badge am Beet
2. Nutzer wiederholt die Prüfung bei „Breit mit Weg“, „Grenzwert“ und „Schmal einseitig“
3. Nutzer verbreitert „Grenzwert“ per Maßeingabe auf 1,3 m und speichert
4. Nutzer vergrößert „Breit“ weiter auf 2,0 m

**Erwartete Ergebnisse**:
- „Breit“ zeigt in der Zusammenfassung und am Badge den Hinweis, dass die Beetmitte von den Rändern schwer erreichbar ist (Platzhalter „Beet zu breit zum Erreichen“); er enthält die Schwelle
- „Breit mit Weg“ zeigt keinen Hinweis (beidseitiger Zugang über die Wege)
- „Grenzwert“ zeigt keinen Hinweis (genau 1,2 m gilt noch nicht als überschritten)
- „Schmal einseitig“ zeigt den Hinweis (0,7 m über der Schwelle 0,6 m für einseitigen Zugang)
- Nach Schritt 3 zeigt „Grenzwert“ den Hinweis
- Der Hinweis ist nie rot als Fehler dargestellt, verhindert weder das Speichern noch das Bepflanzen und trägt ein Icon plus Text

**Nachbedingungen**:
- „Grenzwert“ ist 1,3 m breit; „Breit“ 2,0 m

**Tags**: [req-053, welle-8, erreichbarkeit, hinweis, standortmerkmale, desktop, gp-fr-166]

---

### TC-053-077: Beet-Fotos am Desktop — Galerie, Titelbild, Entfernen

**Requirement**: REQ-053 §10.1 GP-FR-051 (SHOULD, abgeleitet); Muster Galerie REQ-034/REQ-052
**Gerät**: Desktop
**Priority**: High
**Category**: Happy Path
**Preconditions**:
- „Beet 1“ ohne Fotos; zwei Bilddateien (JPG, je unter 5 MB) und eine Textdatei „notiz.txt“; Rolle Gärtner oder Leitung

**Testschritte**:
1. Nutzer öffnet die Beetansicht und den Tab „Fotos“
2. Nutzer lädt beide Bilder hoch
3. Nutzer versucht, „notiz.txt“ hochzuladen
4. Nutzer setzt das zweite Bild als Titelbild
5. Nutzer betrachtet den Beetkopf und die Beet-Zusammenfassung im Plan
6. Nutzer entfernt das Titelbild und bestätigt
7. Nutzer exportiert den Plan als JSON (Weg aus TC-053-030) und öffnet die Datei

**Erwartete Ergebnisse**:
- Der leere Tab erklärt, dass noch keine Fotos vorliegen, und bietet das Hochladen an
- Nach dem Hochladen zeigt die Galerie beide Bilder als Vorschau; das erste ist automatisch bzw. nach Wahl Titelbild
- Die Textdatei wird mit einer verständlichen Meldung zu den erlaubten Dateitypen abgelehnt
- Nach Schritt 4 erscheint das zweite Bild als Titelbild im Beetkopf und im Beet-Sheet der Zusammenfassung
- Nach dem Entfernen und Bestätigen ist das Bild aus der Galerie verschwunden; das verbleibende Bild bleibt erhalten, der Beetkopf zeigt kein Titelbild bzw. das verbleibende
- Die JSON-Sicherung des Plans enthält keine Fotos

**Nachbedingungen**:
- Ein Foto am Beet

**Tags**: [req-053, welle-8, fotos, galerie, titelbild, beet, desktop, gp-fr-051]

---

### TC-053-078: Foto vom Beet im Feldmodus — Touch-Ziel mindestens 64 px

**Requirement**: REQ-053 §18.1 Schritt 7 GP-FR-051 (SHOULD, abgeleitet); Berührungsziele GP-UX-023
**Gerät**: Smartphone 390 × 844
**Priority**: High
**Category**: Touch-Bedienung
**Preconditions**:
- Feldmodus, Beet „Beet 1“ mit einer Pflanze; Kamera bzw. Dateiauswahl des Browsers steht zur Verfügung (im Test eine Bilddatei)

**Testschritte**:
1. Nutzer öffnet den Feldmodus und tippt auf „Beet 1“
2. Nutzer misst die Aktion „Foto vom Beet“ im Beet-Sheet
3. Nutzer tippt „Foto vom Beet“ und wählt ein Bild
4. Nutzer tippt eine Pflanze an und prüft, ob dort ebenfalls ein Foto angeboten wird
5. Nutzer öffnet am Desktop den Tab „Fotos“ von „Beet 1“

**Erwartete Ergebnisse**:
- Die Aktion „Foto vom Beet“ ist im Beet-Sheet ohne Scrollen auffindbar und misst mindestens 64 × 64 px
- Nach der Bildwahl erscheint eine Bestätigung („Foto gespeichert“); die Aktion ist bis dahin gesperrt, ein Doppeltipp lädt das Bild nicht doppelt hoch
- Die Pflanze bietet weiterhin ihre eigene Foto-Aktion; das Beet-Foto liegt nicht an der Pflanze
- Das Bild erscheint im Tab „Fotos“ des Beets und ist bei fehlendem Titelbild das Titelbild im Beet-Sheet

**Nachbedingungen**:
- Ein Foto am Beet

**Tags**: [req-053, welle-8, fotos, feldmodus, smartphone, 390px, touch, 64px, gp-fr-051]

---

### TC-053-079: CSV-Beetliste exportieren — Standardspalten, Spaltenauswahl, Excel-Variante

**Requirement**: REQ-053 §23 GP-FR-145, GP-FR-175, GP-FR-174 (Excel-Variante) (SHOULD, abgeleitet). Ergänzt TC-053-030 (JSON-Sicherung)
**Gerät**: Desktop
**Priority**: High
**Category**: Export
**Preconditions**:
- Site mit drei Beeten (Bodenart, Zone, aktive Pflanzen, Status unterschiedlich), eines davon heißt „=SUMME(A1)“; Sonne und Frostrisiko erfasst; Rolle Leitung

**Testschritte**:
1. Nutzer öffnet „Export & Import“ → „Beetliste exportieren (CSV)“
2. Nutzer lässt die Spaltenauswahl unverändert und lädt herunter
3. Nutzer öffnet den Dialog erneut, wählt zusätzlich „Sonne“ und „Frostrisiko“ und lädt die Datei herunter
4. Nutzer wählt „Excel-Variante“ und lädt herunter
5. Nutzer öffnet die Dateien im Texteditor

**Erwartete Ergebnisse**:
- Voreingestellt sind die Spalten Name, Typ, Fläche, Status, Bodenart, Zone und aktive Pflanzen; die Zuweisung ist nicht angekreuzt (TC-053-080)
- Datei 1 enthält genau diese Spalten und drei Zeilen
- Datei 2 enthält zusätzlich die Spalten Sonne und Frostrisiko
- Die Excel-Variante trennt die Spalten mit Semikolon und beginnt mit Byte-Order-Mark; Umlaute sind im Tabellenprogramm korrekt
- Der Beetname „=SUMME(A1)“ steht in der Datei mit vorangestelltem Hochkomma
- Es gibt keinen Fehler und keinen Download bei leerer Spaltenauswahl: der Dialog verlangt mindestens eine Spalte

**Nachbedingungen**:
- Nichts geändert

**Tags**: [req-053, welle-8, export, csv, beetliste, spaltenauswahl, excel, desktop, gp-fr-145, gp-fr-175]

---

### TC-053-080: CSV-Beetliste — Zuweisung nur mit Opt-in, ohne Opt-in keine Namen

**Requirement**: REQ-053 §23 GP-FR-175, SR-024 (SHOULD, abgeleitet); Datenschutz
**Gerät**: Desktop
**Priority**: High
**Category**: Datenschutz
**Preconditions**:
- Site mit „Beet 1“, das der Person „Anna Beispiel“ zugewiesen ist (Zuständigkeit), und „Beet 2“ ohne Zuweisung; Rolle Leitung

**Testschritte**:
1. Nutzer öffnet „Export & Import“ → „Beetliste exportieren (CSV)“ und liest die Spaltenauswahl
2. Nutzer lädt ohne Änderung herunter und sucht in der Datei nach „Anna“
3. Nutzer schaltet „Zuweisung (enthält Namen von Personen)“ ein und liest den Hinweis
4. Nutzer lädt herunter und öffnet die Datei
5. Nutzer öffnet den Dialog erneut

**Erwartete Ergebnisse**:
- Die Option „Zuweisung“ ist standardmäßig aus und mit einem Datenschutz-Hinweis versehen
- Die Datei ohne Opt-in enthält weder eine Spalte für Zuständige noch den Namen „Anna Beispiel“
- Nach dem Einschalten benennt ein Hinweis, dass Personennamen in der Datei stehen
- Die zweite Datei enthält eine Spalte „Zuweisung“ mit „Anna Beispiel“ bei „Beet 1“ und einem leeren Feld bei „Beet 2“
- Beim erneuten Öffnen ist die Option wieder aus (der Opt-in wird nicht gemerkt)

**Nachbedingungen**:
- Nichts geändert

**Tags**: [req-053, welle-8, export, csv, datenschutz, opt-in, zuweisung, desktop, gp-fr-175]

---

### TC-053-081: CSV-Beetliste importieren — Prüfbericht mit Zeilenfehlern, Bestätigung, Sprung in den Editor

**Requirement**: REQ-053 §23 GP-FR-174 (SHOULD, abgeleitet)
**Gerät**: Desktop
**Priority**: High
**Category**: Import
**Preconditions**:
- Standort B mit Gartengrenze und ohne Beete; Rolle Leitung; ein zweiter Nutzer mit Rolle Gärtner
- CSV-Datei (UTF-8, Semikolon) mit Spalten `Name;Typ;Breite_m;Länge_m;Sonne`: vier gültige Zeilen („Hochbeet A“, „Hochbeet B“, „Kräuterbeet“, „=Beet4“), eine Zeile mit Breite „abc“ und eine Zeile ohne Namen

**Testschritte**:
1. Nutzer öffnet den Plan von Standort B, dann „Sicherung einspielen …“ und wählt als Dateityp CSV
2. Nutzer wählt die Datei und liest den Prüfbericht
3. Nutzer bricht ab und prüft den Plan
4. Nutzer wiederholt den Import, bestätigt den Bericht und fährt fort
5. Nutzer betrachtet den Plan
6. Als Gärtner öffnet der Nutzer „Sicherung einspielen …“

**Erwartete Ergebnisse**:
- Der Prüfbericht nennt 4 Beete, die angelegt werden, und listet die beiden Fehlerzeilen mit Zeilennummer und Grund (Breite keine Zahl; Name fehlt)
- Nach dem Abbrechen steht der Plan unverändert (keine Beete); die Vorschau hat nichts geschrieben
- Nach der Bestätigung meldet der Dialog 4 angelegte Beete; die Fehlerzeilen wurden nicht angelegt
- Der Plan zeigt die vier Beete mit den Maßen aus der Datei in einer Reihe nebeneinander ohne Überlappung; ein Hinweis fordert auf, sie im Editor anzuordnen, und führt dorthin
- Der Name „=Beet4“ erscheint ohne führendes „=“ bzw. als Text, nicht als Formel
- Als Gärtner ist der CSV-Import nicht verfügbar oder wird mit verständlicher Meldung abgelehnt (nur Leitung)

**Nachbedingungen**:
- Standort B enthält 4 neue Beete ohne Layout-Anordnung

**Tags**: [req-053, welle-8, import, csv, beetliste, pruefbericht, desktop, gp-fr-174]

---

### TC-053-082: Frost-Grund im Pflanzenzustand — nur bei Frostrisiko „Hoch“ und vorhergesagtem Frost

**Requirement**: REQ-053 §11.4, GP-FR-162, GP-UX-060 (SHOULD, abgeleitet). Ergänzt TC-053-034/035 (Info-Blase, Zustände)
**Gerät**: Desktop
**Priority**: High
**Category**: Pflanzenzustand
**Preconditions**:
- Standort mit gespeicherter Wettervorhersage, die im Vorhersagehorizont Frost enthält (Seed-Daten)
- „Beet A“: Frostrisiko „Hoch“, eine Tomate ohne weitere Auffälligkeit; „Beet B“: Frostrisiko „Normal“, eine Tomate; „Beet C“: Frostrisiko „Niedrig“, eine Tomate; „Beet D“: Frostrisiko „Hoch“, eine Tomate mit offenem Befund
- Zweiter Standort, an dem keine Frostvorhersage vorliegt, mit „Beet E“ (Frostrisiko „Hoch“) und einer Tomate

**Testschritte**:
1. Nutzer öffnet die Beetansicht von „Beet A“ und bewegt den Zeiger auf die Tomate
2. Nutzer prüft die Tomaten in „Beet B“ und „Beet C“
3. Nutzer prüft die Tomate in „Beet D“
4. Nutzer öffnet am zweiten Standort „Beet E“ und prüft die Tomate
5. Nutzer öffnet die Benachrichtigungen und liest die Frühwarnung des ersten Standorts

**Erwartete Ergebnisse**:
- Die Tomate in „Beet A“ trägt das Badge mit der Schneeflocke; die Info-Blase nennt im Bereich „Handlungsbedarf“ die Frostgefahr im Klartext
- Die Tomaten in „Beet B“ und „Beet C“ tragen kein Frost-Badge und keinen Frost-Grund
- „Beet D“ zeigt genau ein Badge, das Warndreieck für den Befund (Priorität Befund vor Frost); die Frostgefahr steht trotzdem in der Info-Blase
- In „Beet E“ erscheint trotz Frostrisiko „Hoch“ kein Frost-Grund, weil keine Vorhersage vorliegt
- Die Frühwarnung nennt „Beet A“ und „Beet D“, nicht „Beet C“ (Frostrisiko „Niedrig“ wird ausgelassen); sie nennt keine neue Temperaturschwelle

**Nachbedingungen**:
- Nichts geändert

**Tags**: [req-053, welle-8, pflanzenzustand, frost, schneeflocke, badge, fruehwarnung, desktop, gp-fr-162]

---

## 11. Neu in Welle 9 (Renderer-Messung)

Der Fall TC-053-083 ist aus GP-NFR-033/034 und der Entscheidung D-01 abgeleitet (WP 9.6, #2746). Er prüft keine
Funktion, sondern misst: das Ergebnis ist ein Bericht (`.audits/req-053/renderer-measurement-<Datum>.md`), aus dem
sich das Go/No-Go für den zweiten Renderer (WP 9.7) ergibt.

### TC-053-083: Renderer-Messung D-01 — Drag- und Zoom-Frametime auf großen Plänen, Desktop und Mobile bei 4-facher CPU-Drosselung

**Requirement**: REQ-053 §25.2 GP-NFR-033, GP-NFR-034, §19.4 D-01 (MUST, abgeleitet)
**Gerät**: Desktop und Smartphone 390 × 844 (Planungsmodus)
**Priority**: Medium
**Category**: Performance
**Preconditions**:
- Plan „large“: 250 Beete (1,2 × 2 m) mit je 20 Positionen, auf jeder eine Pflanze (5 000 Pflanzen)
- Plan „3 000 Objekte“: 30 Beete (3,3 × 3 m, rechts ein pflanzenfreier Streifen von 0,3 m als Griff für den Drag) mit je 100 Pflanzen, so dicht angeordnet, dass auf dem Desktop in der Gesamtansicht jede Pflanze einzeln gezeichnet wird (30 + 3 000 = 3 030 sichtbare Objekte); auf dem Smartphone zeigt die Gesamtansicht nur Beete und Cluster
- Chrome; für das Mobile-Profil eine Sitzung, die die CDP-Drosselung zulässt

**Testschritte**:
1. Nutzer öffnet einen der beiden Pläne in der Gesamtansicht; die Messung zählt die gezeichneten Objekte
2. Nutzer zoomt mit Strg + Mausrad zehn Rasten hinein und zehn heraus; die Messung liest die Frametime je Hälfte
3. Nutzer zieht ein Beet nahe der Bildmitte hin und zurück; die Messung liest die Frametime; danach macht er die Verschiebung rückgängig
4. Dasselbe auf dem Smartphone mit vierfach gedrosselter CPU

**Erwartete Ergebnisse**:
- Je Fall, Profil und Geste liegt ein 95.-Perzentil der Frametime vor; eine fehlende Messung ist ein Fehler
- In der Gesamtansicht sind alle Beete gezeichnet; der Plan „3 000 Objekte“ zeigt auf dem Desktop mindestens 3 000 Objekte
- Zoom ändert die Zoomstufe in beide Richtungen, der Drag verschiebt das Beet (sonst ist die Messung ungültig)
- Beratend (kein Gate): Frametime ≤ 16 ms (Desktop) bzw. ≤ 33 ms (Smartphone); D-01-Schwelle > 3 000 sichtbare Objekte oder Drag-Frametime > 16 ms; eine Überschreitung wird als Warnung berichtet
- Ist die Drosselung in der Sitzung nicht verfügbar, steht das als benannte Lücke im Bericht

**Nachbedingungen**:
- Nichts gespeichert; die Messwerte liegen als JSON bei den Screenshots und als JUnit-Eigenschaft `renderer_record`

**Tags**: [req-053, welle-9, performance, renderer, frametime, d-01, desktop, smartphone, gp-nfr-033, gp-nfr-034]

---

## 12. Neu in Welle 9, Teil A (Offline: Service Worker, Plan ohne Verbindung, Puffer und Sync, Konflikt, Abmelden)

Die Fälle TC-053-084 bis TC-053-090 sind aus REQ-053 GP-UX-024 und UI-NFR-012 R-001/R-002, R-007…R-010, R-021,
R-025, R-028, R-032, R-055 bis R-060 abgeleitet (WP 9.15, #2755); automatisiert in
`tests/e2e/test_req053_wave9_offline.py`. „Ohne Verbindung“ heißt: die Seite ist über die Entwicklerwerkzeuge des
Browsers offline geschaltet, und der Browser meldet selbst „offline“. Der Service Worker existiert nur in einem
sicheren Kontext; die Testumgebung liefert die App über unverschlüsseltes HTTP aus und startet den Browser für die
Fälle mit Service Worker deshalb mit diesem Ursprung als „sicher“ behandelt. Feldmodus-Fälle laufen auf dem
Smartphone (390 × 844), die übrigen auf dem Desktop.

### TC-053-084: Service Worker aktiv und steuernd, Manifest ausgeliefert

**Requirement**: UI-NFR-012 R-001, R-002, R-007, R-059; REQ-053 WP 9.1 (abgeleitet)
**Gerät**: Desktop
**Priority**: High
**Category**: Offline
**Preconditions**:
- Garten mit einem Beet

**Testschritte**:
1. Nutzer öffnet den Gartenplan
2. Nutzer lädt die Seite neu

**Erwartete Ergebnisse**:
- Für den ganzen Ursprung ist genau ein Service Worker unter `/sw.js` registriert und aktiviert; nach dem Neuladen steuert er die Seite
- Das Dokument verweist auf `/manifest.json`; der Browser liest es ohne Fehler, mit Name, Kurzname, Startadresse, Anzeige „standalone“, Theme- und Hintergrundfarbe sowie Symbolen in 192 und 512 px
- `/sw.js` und `/manifest.json` werden mit „nicht speichern“ ausgeliefert (kein Browser-Cache für das Worker-Skript)

**Nachbedingungen**:
- Keine

**Tags**: [req-053, welle-9, offline, service-worker, manifest, desktop, ui-nfr-012]

---

### TC-053-085: App-Shell lädt ohne Verbindung aus dem Service Worker

**Requirement**: UI-NFR-012 R-007, R-008, R-010, §5.1.5; REQ-053 WP 9.1 (abgeleitet)
**Gerät**: Desktop
**Priority**: High
**Category**: Offline
**Preconditions**:
- Gartenplan einmal mit Verbindung geöffnet und neu geladen (der Service Worker steuert die Seite)

**Testschritte**:
1. Nutzer verliert die Verbindung
2. Nutzer lädt die Seite neu

**Erwartete Ergebnisse**:
- Statt der Fehlerseite des Browsers erscheint die App: im Vollmodus die Anmeldemaske (eine Sitzung lässt sich ohne Verbindung nicht wiederherstellen, R-050 nicht in Welle 9), im Light-Modus der App-Rahmen mit der Verbindungsanzeige
- Die Seite kam vom Service Worker, der Browser meldet weiterhin „offline“, der Service Worker steuert die Seite

**Nachbedingungen**:
- Keine

**Tags**: [req-053, welle-9, offline, app-shell, service-worker, desktop, ui-nfr-012]

---

### TC-053-086: Zuletzt geladener Plan ohne Verbindung lesbar — „Stand von …“, schreibgeschützt

**Requirement**: REQ-053 GP-UX-024 (Teil 1); UI-NFR-012 R-057; WP 9.2 (abgeleitet)
**Gerät**: Desktop
**Priority**: High
**Category**: Offline
**Preconditions**:
- Garten mit den Beeten „Beet A“ und „Beet B“

**Testschritte**:
1. Nutzer öffnet den Gartenplan mit Verbindung
2. Nutzer wechselt mit „Zurück zum Standort“ zur Standortseite
3. Nutzer verliert die Verbindung und geht mit „Zurück“ des Browsers zum Plan
4. Die Verbindung kommt zurück

**Erwartete Ergebnisse**:
- Nach Schritt 3 zeigt der Plan beide Beete schreibgeschützt, mit dem Hinweis „Ohne Verbindung: Du siehst den Stand von <Uhrzeit>.“
- Der Sperrhinweis nennt den Grund („Ohne Verbindung kannst du den Plan nur ansehen …“); „Export & Import“ wird nicht angeboten
- Nach Schritt 4 ersetzt der Editor die Ansicht, der Stand-Hinweis verschwindet

**Nachbedingungen**:
- Nichts geändert

**Tags**: [req-053, welle-9, offline, plan-cache, schreibgeschuetzt, desktop, gp-ux-024]

---

### TC-053-087: Feldmodus ohne Verbindung — „Erledigt“ und Notiz gepuffert, mit Verbindung übertragen

**Requirement**: REQ-053 GP-UX-024 (Teil 2); UI-NFR-012 R-021, R-025, R-058, §5.3.4; WP 9.4 (abgeleitet)
**Gerät**: Smartphone 390 × 844
**Priority**: High
**Category**: Offline
**Preconditions**:
- „Beet 1“ mit einer offenen Gieß-Aufgabe; das Beet-Sheet wurde einmal mit Verbindung geöffnet

**Testschritte**:
1. Nutzer verliert die Verbindung und öffnet das Sheet von „Beet 1“
2. Nutzer tippt bei der Aufgabe „Erledigt“, dann „Fertig“
3. Nutzer tippt den Chip „Notiz“, schreibt eine Notiz und speichert
4. Die Verbindung kommt zurück

**Erwartete Ergebnisse**:
- Das Sheet zeigt den „Stand von …“-Hinweis und erklärt, dass „Erledigt“, Notizen und Fotos auf dem Gerät gespeichert werden
- Die Aufgabe zeigt „Wartet auf Übertragung“ und bietet kein zweites „Erledigt“; die App-Leiste zeigt „2 nicht übertragen“; am Server ist noch nichts angekommen
- Nach Schritt 4 meldet die App „2 Einträge übertragen.“, die Anzeige „nicht übertragen“ verschwindet
- Am Server ist die Aufgabe erledigt (genau ein Pflegeeintrag), die Notiz genau einmal gespeichert; beide tragen den Zeitpunkt der Erfassung ohne Verbindung, nicht den der Übertragung

**Nachbedingungen**:
- Aufgabe erledigt, Notiz gespeichert

**Tags**: [req-053, welle-9, offline, puffer, sync, feldmodus, smartphone, gp-ux-024]

---

### TC-053-088: Feldmodus ohne Verbindung — Beet-Foto gepuffert, landet mit Verbindung in der Galerie

**Requirement**: UI-NFR-012 R-058, R-060 (c); REQ-053 GP-FR-051; WP 9.4 (abgeleitet)
**Gerät**: Smartphone 390 × 844 (nur Vollmodus: Ablage für Anhänge)
**Priority**: Medium
**Category**: Offline
**Preconditions**:
- „Beet 1“ ohne Foto; das Beet-Sheet wurde einmal mit Verbindung geöffnet

**Testschritte**:
1. Nutzer verliert die Verbindung und öffnet das Sheet von „Beet 1“
2. Nutzer tippt „Foto vom Beet“, wählt ein Bild und lädt es hoch
3. Die Verbindung kommt zurück

**Erwartete Ergebnisse**:
- Die App meldet „Foto auf dem Gerät gespeichert …“; die App-Leiste zeigt „1 nicht übertragen“; die Galerie am Server ist leer
- Nach Schritt 3 meldet die App „1 Eintrag übertragen.“; die Galerie des Beets enthält genau ein Foto, und es ist das Titelbild

**Nachbedingungen**:
- Ein Foto am Beet

**Tags**: [req-053, welle-9, offline, puffer, foto, feldmodus, smartphone, gp-fr-051]

---

### TC-053-089: Gepuffertes „Erledigt“ einer inzwischen geschlossenen Aufgabe — Konflikt-Dialog

**Requirement**: UI-NFR-012 R-028, R-032; REQ-053 WP 9.3, WP 9.4 (abgeleitet)
**Gerät**: Smartphone 390 × 844
**Priority**: High
**Category**: Offline
**Preconditions**:
- „Beet 1“ mit einer offenen Gieß-Aufgabe; das Beet-Sheet wurde einmal mit Verbindung geöffnet

**Testschritte**:
1. Nutzer verliert die Verbindung, öffnet das Sheet und erledigt die Aufgabe („Erledigt“, „Fertig“)
2. Auf einem zweiten Gerät wird dieselbe Aufgabe erledigt
3. Die Verbindung kommt zurück
4. Nutzer wählt im Konflikt-Dialog beim Eintrag „Verwerfen“

**Erwartete Ergebnisse**:
- Nach Schritt 3 öffnet sich der Konflikt-Dialog von selbst mit genau einem Eintrag, der die Aufgabe nennt und den Grund „Die Aufgabe ist inzwischen schon erledigt oder übersprungen.“
- Nach Schritt 4 verschwindet der Eintrag und die Anzeige „nicht übertragen“
- Am Server ist die Aufgabe genau einmal erledigt — vom zweiten Gerät, nicht ein zweites Mal aus dem Puffer

**Nachbedingungen**:
- Aufgabe erledigt (vom zweiten Gerät)

**Tags**: [req-053, welle-9, offline, konflikt, feldmodus, smartphone, ui-nfr-012]

---

### TC-053-090: Abmelden leert den Lese-Zwischenspeicher und den Namensraum des Kontos

**Requirement**: UI-NFR-012 R-055, R-056 (a); REQ-053 SR-019, WP 9.1/9.2 (abgeleitet)
**Gerät**: Desktop (nur Vollmodus: der Light-Modus hat kein Abmelden)
**Priority**: High
**Category**: Offline / Datenschutz
**Preconditions**:
- Ein eigenes, frisch registriertes Konto (ein Abmelden beendet alle Zugangs-Token des Kontos)
- Der Service Worker steuert die Seite, der Plan wurde gelesen (liegt im Plan-Zwischenspeicher), der Tab hat seinen Namensraum (Konto und Mandant) beim Service Worker angemeldet

**Testschritte**:
1. Nutzer öffnet das Konto-Menü und wählt „Abmelden“

**Erwartete Ergebnisse**:
- Die Anmeldemaske erscheint
- Der Plan-Zwischenspeicher des Browsers ist gelöscht, der Service Worker kennt keinen Namensraum des Kontos mehr, kein kontobezogener Zwischenspeicher ist übrig
- Die öffentlichen Zwischenspeicher der App-Shell bleiben (sie enthalten keine Kontodaten)

**Nachbedingungen**:
- Abgemeldet

**Tags**: [req-053, welle-9, offline, abmelden, datenschutz, desktop, sr-019, ui-nfr-012]

---

## 13. Neu in Welle 9, Teil B (PNG, Vorlagen-Austausch, Parzellenseite, Standort-Flags, Wasserquelle, Strg+D, Renderer)

Die Fälle TC-053-091 bis TC-053-097 sind aus GP-FR-144, GP-FR-173, GP-API-070/071, GP-FR-176, GP-FR-165, GP-FR-167,
GP-FR-025/026 und GP-NFR-033 mit D-01 abgeleitet (WP 9.16, #2756); automatisiert in
`tests/e2e/test_req053_wave9_export.py`, zusammen mit TC-053-047 („Regen — übersprungen“, Abschnitt 7). Alle Fälle
laufen auf dem Desktop (PNG und CSV bietet der Export-Dialog nur abseits des Smartphones an, GP-UX-050).

### TC-053-091: Plan als PNG — Faktor × angepasste Ansicht, 2× vorgewählt, ohne Wasserzeichen

**Requirement**: REQ-053 GP-FR-144; Platzhalter 9 der Welle 9; WP 9.8 (abgeleitet)
**Gerät**: Desktop
**Priority**: Medium
**Category**: Druck und Export
**Preconditions**:
- Garten 20 × 10 m mit zwei Beeten innerhalb der Grenze

**Testschritte**:
1. Nutzer öffnet „Export & Import“ → „Plan exportieren …“ und wählt PNG
2. Nutzer lädt herunter
3. Nutzer öffnet den Dialog erneut, wählt 1× und lädt herunter

**Erwartete Ergebnisse**:
- Der Dialog steht auf 2×, das Wasserzeichen ist aus, die Größenzeile lautet „Das Bild wird 2400 × 1310 Pixel groß und zeigt den ganzen Plan.“
- Die Datei heißt `garden-plan-<Standort>-<JJJJMMTT>.png`, ist ein PNG und misst 2400 × 1310 Pixel
- Bei 1× lauten Größenzeile und Datei 1200 × 655 Pixel — genau die halbe Breite

**Nachbedingungen**:
- Zwei PNG-Dateien heruntergeladen

**Tags**: [req-053, welle-9, export, png, desktop, gp-fr-144]

---

### TC-053-092: Beetvorlage exportieren und wieder importieren — ohne Kennungen, Namensvorschlag, Kopie

**Requirement**: REQ-053 GP-FR-173, GP-API-070, GP-API-071; WP 9.9 (abgeleitet)
**Gerät**: Desktop
**Priority**: Medium
**Category**: Vorlagen
**Preconditions**:
- Eigene Vorlage „Kräuterbeet <Kennung>“ (Hochbeet 1,6 × 0,8 m, 0,4 m hoch, Reihen 25 cm, Abstand 20 cm); ein Garten

**Testschritte**:
1. Nutzer wählt im Vorlagen-Werkzeug die Vorlage und wählt „Exportieren“
2. Nutzer wählt „Importieren“ und dieselbe Datei
3. Nutzer übernimmt den vorgeschlagenen Namen und wählt „Erneut prüfen“
4. Nutzer wählt „Importieren“

**Erwartete Ergebnisse**:
- Nach Schritt 1: Hinweis „Die Vorlage ist als JSON-Datei heruntergeladen – ohne Mandanten-Kennung, Autor und Notizen.“; die Datei enthält nur die Austauschfelder (Format, Name, Typ, Geometrie, Höhe, Layout, Bodenvorgaben), keine Kennung des Mandanten
- Nach Schritt 2: der vergebene Name wird abgelehnt („Eine Vorlage mit diesem Namen gibt es schon …“), das Namensfeld schlägt einen freien Namen vor
- Nach Schritt 3: der Prüfbericht nennt den neuen Namen
- Nach Schritt 4: Hinweis „Die Vorlage ist importiert und ausgewählt.“; die Auswahl zeigt die neue Vorlage; die Vorlagenliste enthält sie neben dem Original, mit gleicher Form, Höhe und gleichem Raster

**Nachbedingungen**:
- Eine zweite Vorlage mit dem vorgeschlagenen Namen

**Tags**: [req-053, welle-9, vorlagen, export, import, desktop, gp-fr-173]

---

### TC-053-093: PDF mit Parzellenliste nur mit Opt-in, Zuweisungen nur mit eigenem Opt-in

**Requirement**: REQ-053 GP-FR-176, SR-024; Platzhalter 8 der Welle 9; WP 9.10 (abgeleitet)
**Gerät**: Desktop
**Priority**: Medium
**Category**: Druck und Export
**Preconditions**:
- Garten mit zwei Beeten

**Testschritte**:
1. Nutzer exportiert den Plan als PDF, ohne etwas umzustellen
2. Nutzer exportiert erneut mit „Parzellenliste als Zusatzseite“
3. Nutzer exportiert erneut mit Parzellenliste und „Zuweisungen in die Parzellenliste aufnehmen“

**Erwartete Ergebnisse**:
- Schritt 1: Parzellenliste aus, kein Schalter für Zuweisungen; Datenschutzzeile „Der Export enthält keine Namen von Mitgliedern …“; das PDF enthält die Seite „Gartenplan: <Standort>“ und keine „Parzellenliste: <Standort>“
- Schritt 2: der Zuweisungs-Schalter erscheint, aus; das PDF enthält beide Seiten; es wurden keine Namen angefordert
- Schritt 3: die Datenschutzzeile nennt die Namen der zugewiesenen Mitglieder; das PDF enthält die Parzellenseite; nur dieser Export hat Zuweisungen angefordert

**Nachbedingungen**:
- Drei PDF-Dateien heruntergeladen

**Tags**: [req-053, welle-9, export, pdf, parzellenliste, datenschutz, desktop, gp-fr-176]

---

### TC-053-094: Standort-Flags „Wurzelkonkurrenz“ und „Allelopathie-Risiko“ im Panel und als Chip im Beetkopf

**Requirement**: REQ-053 GP-FR-165; WP 9.11 (abgeleitet)
**Gerät**: Desktop
**Priority**: Low
**Category**: Standortmerkmale
**Preconditions**:
- Beet ohne Standortmerkmale

**Testschritte**:
1. Nutzer öffnet die Beetansicht, „Merkmale ändern“, kreuzt beide Flags an und speichert
2. Nutzer entfernt „Allelopathie-Risiko“ und speichert
3. Nutzer entfernt „Wurzelkonkurrenz“ und speichert

**Erwartete Ergebnisse**:
- Die Gruppe „Konkurrenz am Standort“ hat zwei Kontrollkästchen, einen Hinweis („Steht das Beet unter oder neben Bäumen …“) und kein Freitextfeld
- Nach Schritt 1 ist im Kopf ein neutraler Chip „Wurzelkonkurrenz/Allelopathie-Risiko am Standort gemeldet“; beide Flags sind gespeichert
- Nach Schritt 2 nennt der Chip nur „Wurzelkonkurrenz“; nach Schritt 3 ist kein Flag gespeichert und kein Chip zu sehen

**Nachbedingungen**:
- Beet ohne Flags

**Tags**: [req-053, welle-9, standortmerkmale, flags, desktop, gp-fr-165]

---

### TC-053-095: Nächste Wasserquelle in Beetliste, Beetkopf und CSV — ohne Geometrie keine Angabe

**Requirement**: REQ-053 GP-FR-167; WP 9.12 (abgeleitet)
**Gerät**: Desktop
**Priority**: Low
**Category**: Bewässerung
**Preconditions**:
- Garten 10 × 10 m mit „Beet Nah“ (1…3 × 1…2 m), „Beet Fern“ (6…8 × 6…7 m), einem Wasserhahn bei (5,5 | 1,5) m und „Beet Alt“ ohne Geometrie

**Testschritte**:
1. Nutzer öffnet den Plan und liest die Beetliste
2. Nutzer exportiert die Beetliste als CSV mit der Spalte `nearest_water_source_m`
3. Nutzer öffnet die Beetansicht von „Beet Nah“, dann von „Beet Alt“

**Erwartete Ergebnisse**:
- Die Spalte „Wasserquelle“ zeigt „2,5 m“, „4,53 m“ und „—“ (Abstand Kante zu Kante in Luftlinie)
- Die CSV enthält 2.5, 4.528 und eine leere Zelle — nie „0“
- Der Kopf von „Beet Nah“ zeigt „Nächste Wasserquelle“ mit „2,5 m Luftlinie von der Beetkante“; der Kopf von „Beet Alt“ zeigt keine Angabe

**Nachbedingungen**:
- Keine

**Tags**: [req-053, welle-9, bewaesserung, wasserquelle, beetliste, csv, desktop, gp-fr-167]

---

### TC-053-096: Strg+D dupliziert das gewählte Beet um einen Rasterschritt nach rechts unten

**Requirement**: REQ-053 GP-FR-025, GP-FR-026, V-05; WP 9.14 (abgeleitet)
**Gerät**: Desktop
**Priority**: Medium
**Category**: Editor
**Preconditions**:
- Garten 10 × 10 m (Raster 10 cm) mit „Beet K“ 2 × 1 m bei (2 | 4), ohne Pflanzpositionen

**Testschritte**:
1. Nutzer wählt „Beet K“ mit der Tastatur und drückt Strg+D
2. Nutzer schiebt die Kopie mit Umschalt+Pfeil-unten zehn Rasterschritte nach unten
3. Nutzer speichert

**Erwartete Ergebnisse**:
- Nach Schritt 1: eine ungespeicherte Änderung, zwei Beete gezeichnet, die Kopie ist gewählt und liegt bei (2,1 | 3,9) — ein Rasterschritt nach rechts unten; der Browser öffnet keinen Lesezeichen-Dialog
- Die Kopie überlappt ihr Original noch; zwei Beete derselben Fläche dürfen sich nicht überlappen (V-05), daher Schritt 2
- Nach Schritt 3 liegt „Beet K (Kopie)“ bei (2,1 | 2,9) mit gleicher Größe und gleichem Typ neben dem unveränderten Original

**Nachbedingungen**:
- Zwei Beete gespeichert

**Tags**: [req-053, welle-9, editor, duplizieren, tastatur, desktop, gp-fr-025]

---

### TC-053-097: Renderer-Umschaltung — ab 3 000 Objekten zeichnet Konva, darunter SVG

**Requirement**: REQ-053 GP-NFR-033, GP-NFR-034, D-01; WP 9.7 (abgeleitet)
**Gerät**: Desktop
**Priority**: Medium
**Category**: Performance
**Preconditions**:
- Zwei Gärten mit je 30 Beeten: einer mit 99 Pflanzpositionen je Beet (30 + 2 970 = 3 000 Objekte), einer mit 98 (2 970 Objekte)

**Testschritte**:
1. Nutzer öffnet den ersten Plan
2. Nutzer öffnet den zweiten Plan

**Erwartete Ergebnisse**:
- Der erste Plan wird vom Konva-Renderer auf einer Zeichenfläche gezeichnet
- Der zweite Plan wird als SVG gezeichnet, ohne Zeichenfläche

**Nachbedingungen**:
- Keine

**Tags**: [req-053, welle-9, renderer, konva, performance, desktop, gp-nfr-033, d-01]

---

## 14. Neu in Welle 10, Teil A (Editor-Arbeitsfläche, drei Breiten, Objekteigenschaften, Indoor-Plan)

Die Fälle TC-053-098 bis TC-053-108 sind aus den Akzeptanzkriterien der Editor-Arbeitsfläche (REQ-053 §17.3, AC-1…AC-11,
dazu AC-12, AC-15, AC-16 und AC-17) und aus den Indoor-Zeilen GP-FR-180…183 (§9.8) abgeleitet (WP 10.13, #2834);
automatisiert in `tests/e2e/test_req053_wave10_workspace.py`. Jeder Fall legt seine eigene Site über die Anwendung an
(Indoor-Site, Fenster, Pflanzplätze), sodass kein Fall einen Plan berührt, den ein anderer liest.

Die Fälle zu den drei Breiten setzen das Browserfenster selbst auf genau die genannte Größe (CSS-Pixel des Viewports):
Desktop 1366 × 768 (≥ lg, Panel angedockt), Tablet 820 × 1180 (md, Panel als Drawer), Smartphone 390 × 844 (unter md,
`TouchBar` und Bottom Sheet). Maßgeblich sind die Breakpoints des App-Themes (`theme/tokens.ts`): md ab 768 px, lg ab
1024 px — 1024 × 768 ist damit bereits lg mit angedocktem Panel. Gemessen wird bei 100 % Browser-Zoom im echten
App-Shell (App-Bar, Brotkrumen, Seitentitel); den Warnhinweis des Light-Modus hat der Nutzer vorher geschlossen (er
erscheint nur im Light-Modus auf einem nicht privaten Host und gehört nicht zur App-Shell aus §17.3).

**Zuordnung der Kriterien.** Wo ein Kriterium schon durch einen bestehenden Fall abgedeckt ist, steht hier der Verweis
statt eines zweiten Falls.

| Kriterium | Testfälle | Bemerkung |
|-----------|-----------|-----------|
| AC-1 | TC-053-101 | Zeichenfläche ≥ 60 % der Höhe bei 1366 × 768, Kopfleiste auf einer Zeile |
| AC-2 | TC-053-103 | **blockiert durch #2868** — die Werkzeuge Fläche, Pflanze setzen, Messen und Beschriftung sind nicht gebaut; kein ausführbarer Test |
| AC-3 | TC-053-101 | E2E-Teil: genau eine Kopfleiste, Werkzeuge in einer vertikalen Leiste; „Seitenkopf ohne eigene Aktionen“ prüft vitest |
| AC-4 | TC-053-100 | Teil: Drehen, Ausrichten, Löschen nur bei Auswahl; „Als Vorlage speichern“ nur bei genau einem Beet prüft vitest |
| AC-5 | TC-053-100, TC-053-101 | keine reservierte Breite, Umschalter mit `aria-expanded`/`aria-controls`, Panel-Tabs per Tastatur |
| AC-6 | TC-053-100 | Ebenen-Schalter mit sichtbarer Textbeschriftung neben der Legende |
| AC-7 | TC-053-098; TC-053-012 | Deep-Link, „Zurück“, Zeile → Plan mit Auswahl; die Hervorhebung im Ausschnitt bleibt TC-053-012 |
| AC-8 | TC-053-099; TC-053-007 | kein Dialog beim Tab-Wechsel, Änderung bleibt; der Verlassen-Dialog selbst bleibt TC-053-007 |
| AC-9 | TC-053-104; TC-053-032, TC-053-033 | `TouchBar`, Bottom Sheet, Touch-Ziele ≥ 48 px; die bestehenden Touch-Fälle bleiben unverändert |
| AC-10 | — | CI-Kriterium: alle Unit- und E2E-Suiten grün; die Fälle dieses Abschnitts nutzen nur bestehende oder in UI-NFR-022 §2.5.1 registrierte Kennungen |
| AC-11 | — | Dokumentkriterium, erfüllt mit REQ-053 v1.16 (WP 10.1, #2822); kein Browser-Artefakt |
| AC-12 | TC-053-098 | unbekannter `tab`-Wert, Feldmodus ohne Tab-Leiste |
| AC-13 | TC-053-108 | Teil: Tab „Pflanzplätze“ bei URL-Wert `beds`; „Beete lädt nach Speichern neu“ prüft vitest und Welle 9 (#2813) |
| AC-14 | TC-053-101 | Teil: Zoom-Steuerung liegt innerhalb der Zeichenfläche |
| AC-15 | TC-053-104 | Teil: Tabs und Panel-Umschalter im Überlauf, Einträge ≥ 48 px mit Text, Undo/Redo in der `TouchBar` |
| AC-16 | TC-053-099 | Auswahl und Zoomstufe; der Ausschnitt (Pan) prüft vitest |
| AC-17 | TC-053-100 | Zustandsregel GP-UX-068 vollständig |
| GP-FR-180 | TC-053-105, TC-053-106; TC-053-044 | Eigenschaften, Legende, Zeichnen über das Werkzeug „Gartenobjekt“ |
| GP-FR-181 | TC-053-107; TC-053-105, TC-053-106 | Vorschlag mit Bestätigung; abgeleitete Himmelsrichtung im Panel |
| GP-FR-182 | TC-053-106, TC-053-108 | Leerzustand, Route, keine Frost-Ebene |
| GP-FR-183 | TC-053-108 | Teil: Tab und Liste „Pflanzplätze“; die Raum-Hierarchie (COULD) ist nicht gebaut |

### TC-053-098: Tabs Plan · Liste · Beete — Deep-Link, „Zurück“, unbekannter Wert, Feldmodus ohne Tabs

**Requirement**: REQ-053 §17.3 GP-UX-064 — AC-7, AC-12
**Gerät**: Desktop
**Priority**: High
**Category**: Navigation
**Preconditions**:
- Garten 10 × 10 m mit zwei Beeten „Beet A“ und „Beet B“

**Testschritte**:
1. Nutzer öffnet den Plan über einen Link mit `?tab=beds`
2. Nutzer wählt den Tab „Liste“, danach den Tab „Plan“
3. Nutzer geht mit „Zurück“ des Browsers zweimal zurück
4. Nutzer wählt im Tab „Beete“ die Zeile von Beet B mit der Tastatur (Enter)
5. Nutzer öffnet den Plan über einen Link mit `?tab=xyz`
6. Nutzer öffnet den Plan über einen Link mit `?mode=field&tab=beds`

**Erwartete Ergebnisse**:
- Nach Schritt 1 ist „Beete“ der aktive Tab (`garden-plan-tab-beds`), die Beetliste zeigt Beet A und Beet B, die
  Zeichenfläche ist ausgeblendet
- Jeder Tab-Wechsel steht in der URL (`tab=list`, dann `tab=plan`)
- „Zurück“ führt zuerst zum Tab „Liste“, dann zum Tab „Beete“ — ohne Ungespeichert-Dialog
- Nach Schritt 4 ist der Tab „Plan“ aktiv und Beet B auf dem Plan ausgewählt
- Mit `?tab=xyz` zeigt die Route den Tab „Plan“
- Im Feldmodus gibt es keine Tab-Leiste; der Feldmodus zeigt seine eigene Beetliste

**Nachbedingungen**:
- Keine Änderung gespeichert

**Tags**: [req-053, welle-10, arbeitsflaeche, tabs, url-zustand, desktop, ac-7, ac-12, gp-ux-064]

---

### TC-053-099: Tab-Wechsel verliert nichts — ungespeicherte Änderung, Auswahl und Zoom bleiben, kein Dialog

**Requirement**: REQ-053 §17.3 GP-UX-065 — AC-8, AC-16 (Verlassen-Dialog: TC-053-007)
**Gerät**: Desktop
**Priority**: High
**Category**: Navigation
**Preconditions**:
- Garten 10 × 10 m mit einem Beet „Beet A“, Plan gespeichert

**Testschritte**:
1. Nutzer wählt Beet A mit der Tastatur und verschiebt es mit Pfeil rechts um einen Rasterschritt, ohne zu speichern
2. Nutzer wechselt zum Tab „Liste“, dann zum Tab „Beete“, dann zurück zum Tab „Plan“
3. Nutzer klickt in der Hauptnavigation auf „Dashboard“ und wählt im Dialog „Abbrechen“

**Erwartete Ergebnisse**:
- Nach jedem Tab-Wechsel zeigt die Kopfzeile „Ungespeicherte Änderungen (1)“; kein Ungespeichert-Dialog erscheint
- Zurück im Tab „Plan“ ist Beet A weiterhin ausgewählt, die Zoomstufe ist unverändert, und das Beet steht an der
  verschobenen Position
- Beim Verlassen der Route erscheint der Ungespeichert-Dialog; „Abbrechen“ lässt den Nutzer im Plan, die Änderung
  bleibt erhalten

**Nachbedingungen**:
- Gespeicherter Stand unverändert (die Änderung bleibt ungespeichert)

**Tags**: [req-053, welle-10, arbeitsflaeche, tabs, guard-dialog, desktop, ac-8, ac-16, gp-ux-065]

---

### TC-053-100: Seitenpanel — keine reservierte Breite, Umschalter, Zustandsregel, Panel-Tabs per Tastatur

**Requirement**: REQ-053 §17.3 GP-UX-068, GP-UX-066 — AC-4 (Teil), AC-5, AC-6, AC-17
**Gerät**: Desktop (≥ lg, Panel angedockt)
**Priority**: High
**Category**: Bedienung
**Preconditions**:
- Garten 10 × 10 m mit einem Beet „Beet A“

**Testschritte**:
1. Nutzer öffnet den Plan, ohne etwas auszuwählen
2. Nutzer wählt Beet A mit der Tastatur
3. Nutzer hebt die Auswahl mit Esc auf
4. Nutzer öffnet das Panel mit dem Umschalter in der Kopfleiste
5. Nutzer wählt den Panel-Tab „Ebenen“
6. Nutzer wählt Beet A und hebt die Auswahl mit Esc wieder auf
7. Nutzer schließt das Panel mit dem Umschalter und öffnet es wieder
8. Nutzer drückt im aktiven Panel-Tab Pfeil rechts, dann Pos1, dann Ende

**Erwartete Ergebnisse**:
- Nach Schritt 1: kein Seitenpanel, die Zeichenfläche reicht bis an den rechten Rand der Kopfleiste; der Umschalter
  trägt `aria-expanded="false"` und `aria-controls`; Drehen, Ausrichten und Löschen (Auswahlgruppe) sind nicht da
- Nach Schritt 2: das Panel öffnet auf „Eigenschaften“, der Umschalter trägt `aria-expanded="true"` und zeigt mit
  `aria-controls` auf das Panel; die Auswahlgruppe ist da
- Nach Schritt 3: das Panel klappt ein — die Auswahl hatte es geöffnet
- Nach Schritt 4: das Panel öffnet auf „Ansicht“ (erstes Öffnen ohne Auswahl)
- Nach Schritt 5: jeder Ebenen-Schalter trägt eine sichtbare Textbeschriftung; die Legende steht im selben Tab
- Nach Schritt 6: das Panel wechselt auf „Eigenschaften“ und bleibt nach Esc offen (der Nutzer hatte es geöffnet)
- Nach Schritt 7: das Panel ist zu; wieder geöffnet zeigt es „Ebenen“, den zuletzt benutzten Tab
- Nach Schritt 8: die Panel-Tabs folgen dem WAI-ARIA-Muster „Tabs“ (`role="tab"`, `aria-selected`, `aria-controls` auf
  ein `tabpanel` mit `aria-labelledby`, nur der aktive Tab ist Tab-Stopp); Pfeil rechts wählt den nächsten Tab
  („Zonen“), Pos1 „Eigenschaften“, Ende wieder „Zonen“

**Nachbedingungen**:
- Keine Änderung am Plan

**Tags**: [req-053, welle-10, arbeitsflaeche, seitenpanel, a11y, desktop, ac-4, ac-5, ac-6, ac-17, gp-ux-068]

---

### TC-053-101: Desktop 1366 × 768 — Zeichenfläche ≥ 60 % der Höhe, eine Kopfleiste, Werkzeuge links, Panel angedockt

**Requirement**: REQ-053 §17.3 GP-UX-063, GP-UX-066, GP-UX-067, GP-UX-069 — AC-1, AC-3 (E2E-Teil), AC-5 (Breite),
AC-14 (Teil)
**Gerät**: Desktop 1366 × 768
**Priority**: High
**Category**: Layout
**Preconditions**:
- Garten 10 × 10 m mit einem Beet „Beet A“

**Testschritte**:
1. Nutzer öffnet den Plan bei 1366 × 768, ohne etwas auszuwählen
2. Nutzer betrachtet Zeichenfläche, Kopfleiste und Werkzeug-Leiste
3. Nutzer wählt Beet A mit der Tastatur

**Erwartete Ergebnisse**:
- Die Zeichenfläche (`garden-plan-canvas`) ist mindestens 60 % der Viewport-Höhe hoch (≥ 460,8 px)
- Es gibt genau eine Editor-Kopfleiste, und alle ihre Bedienelemente liegen auf einer Zeile
- Die Werkzeuge stehen in einer vertikalen Leiste links der Zeichenfläche; eine `TouchBar` gibt es nicht
- Die Zoom-Steuerung liegt innerhalb der Zeichenfläche
- Ohne Auswahl reserviert das Panel keine Breite; die Seite scrollt nicht horizontal
- Nach Schritt 3 steht das Panel angedockt rechts neben der Zeichenfläche, ganz im Viewport
- Screenshot-Checkpoints ohne und mit Auswahl

**Nachbedingungen**:
- Keine Änderung am Plan

**Tags**: [req-053, welle-10, arbeitsflaeche, layout, desktop-1366, ac-1, ac-3, ac-5, ac-14, gp-ux-067, gp-ux-069]

---

### TC-053-102: Tablet 820 × 1180 — Panel als Drawer über der Zeichenfläche, Werkzeuge links, kein horizontales Scrollen

**Requirement**: REQ-053 §17.3 GP-UX-069, GP-UX-068
**Gerät**: Tablet 820 × 1180 (md, 768–1023 px)
**Priority**: Medium
**Category**: Layout
**Preconditions**:
- Garten 10 × 10 m mit einem Beet „Beet A“

**Testschritte**:
1. Nutzer öffnet den Plan bei 820 × 1180
2. Nutzer öffnet das Seitenpanel mit dem Umschalter (in der Kopfleiste oder im Überlauf)

**Erwartete Ergebnisse**:
- Die Werkzeuge stehen in der vertikalen Leiste links der Zeichenfläche; die Kopfleiste liegt auf einer Zeile
- Das Panel öffnet als Drawer, der über dem rechten Rand der Zeichenfläche liegt; die Zeichenfläche wird dabei nicht
  schmaler
- Die Seite scrollt weder vor noch nach dem Öffnen horizontal
- Screenshot-Checkpoints ohne und mit Panel

**Nachbedingungen**:
- Keine Änderung am Plan

**Hinweis**: Dieser Fall prüft das Layout der Breite md. Er ist **nicht** der Nachweis von AC-2 („jede
Editor-Funktion erreichbar“), siehe TC-053-103.

**Tags**: [req-053, welle-10, arbeitsflaeche, layout, tablet-820, drawer, gp-ux-069]

---

### TC-053-103: Jede Editor-Funktion bei 1024 × 768 erreichbar, ohne horizontales Scrollen (blockiert durch #2868)

**Requirement**: REQ-053 §17.3 GP-UX-069, GP-UX-001 — AC-2
**Status**: **blockiert durch #2868** — die Werkzeuge Fläche, Pflanze setzen, Messen und Beschriftung aus GP-UX-001
sind im Code getypt, aber nicht gebaut. Für diesen Fall gibt es **keinen ausführbaren Test**: ein Test, der den
heutigen Stand der Werkzeug-Leiste als AC-2 erfüllt festschriebe, würde das Kriterium falsch bestätigen.
**Gerät**: 1024 × 768 (nach den Theme-Breakpoints bereits lg, Panel angedockt)
**Priority**: High
**Category**: Layout
**Preconditions**:
- Garten 10 × 10 m mit einem Beet „Beet A“; #2868 ist umgesetzt

**Testschritte**:
1. Nutzer öffnet den Plan bei 1024 × 768
2. Nutzer erreicht nacheinander jedes Werkzeug aus GP-UX-001 (Auswahl, Hand/Pan, Beet, Bereich, Gartenobjekt mit
   Untermenü, Pflanze setzen, Messen, Text/Label) samt der Untermenü-Einträge
3. Nutzer erreicht jeden der vier Panel-Tabs und jeden Eintrag des Überlaufs „⋮“

**Erwartete Ergebnisse**:
- Jede genannte Funktion ist erreichbar und bedienbar
- Die Seitenbreite übersteigt zu keinem Zeitpunkt die Viewport-Breite (kein horizontales Scrollen)
- Screenshot-Checkpoint mit der vollständigen Werkzeug-Leiste

**Nachbedingungen**:
- Keine Änderung am Plan

**Tags**: [req-053, welle-10, arbeitsflaeche, layout, tablet-1024, blockiert, ac-2, gp-ux-001, gp-ux-069]

---

### TC-053-104: Smartphone 390 × 844 — TouchBar, Werkzeug-Leiste unten, Bottom Sheet, Kopfleiste mit Überlauf

**Requirement**: REQ-053 §17.3 GP-UX-063, GP-UX-069, GP-UX-052, §9.7 — AC-9, AC-15 (Teil)
**Gerät**: Smartphone 390 × 844, Planungsmodus (`?mode=plan`)
**Priority**: High
**Category**: Layout
**Preconditions**:
- Garten 10 × 10 m mit einem Beet „Beet A“

**Testschritte**:
1. Nutzer öffnet den Plan im Planungsmodus bei 390 × 844
2. Nutzer öffnet den Überlauf „⋮“ und wählt „Liste“, danach über den Überlauf wieder „Plan“
3. Nutzer wählt Beet A mit der Tastatur

**Erwartete Ergebnisse**:
- `TouchBar` und Werkzeug-Leiste stehen unten, unter der Zeichenfläche; die Werkzeug-Leiste ist waagerecht
- Undo/Redo stehen in der `TouchBar`
- Die Kopfleiste liegt auf einer Zeile; die Tabs Plan · Liste · Beete und der Panel-Umschalter stehen nicht in ihr,
  sondern im Überlauf — jeder dieser Einträge ist mindestens 48 px hoch und mit Text beschriftet
- Jede Schaltfläche in `TouchBar` und Werkzeug-Leiste ist mindestens 48 × 48 px groß
- Nach Schritt 3 öffnet das Panel als Bottom Sheet über den Leisten
- Die Seite scrollt nicht horizontal
- Screenshot-Checkpoints ohne Auswahl, mit offenem Überlauf und mit Bottom Sheet

**Nachbedingungen**:
- Keine Änderung am Plan

**Tags**: [req-053, welle-10, arbeitsflaeche, layout, smartphone-390, touchbar, bottom-sheet, ac-9, ac-15, gp-ux-069]

---

### TC-053-105: Objekteigenschaften — Fenster und Lampe bearbeiten und speichern, Objekt-Legende, „Außerhalb des Grundstücks“

**Requirement**: REQ-053 §9.8 GP-FR-180, §9.5 (`off_site`, V-03); WP 10.6 (abgeleitet)
**Gerät**: Desktop
**Priority**: Medium
**Category**: Indoor
**Preconditions**:
- Indoor-Site „Wohnung“, Grundriss 6 × 4 m, Nordrichtung 0°
- Ein Fenster als Linie an der Südwand (innen an der Wand), eine Deckenleuchte (60 × 60 cm, Montagehöhe 2,5 m) im
  Raum, ein Balkonkasten (Möbel), der über die Grenze ragt und als „Außerhalb des Grundstücks“ markiert ist

**Testschritte**:
1. Nutzer wählt das Fenster, trägt die Brüstungshöhe 0,9 m ein und wählt die Verglasung „Doppel- oder
   Mehrfachverglasung“
2. Nutzer wählt die Lampe, stellt die Art auf „Pflanzenlampe“, die Montagehöhe auf 1,8 m, die Referenz-PPFD auf 400
   und schaltet „Außerhalb des Grundstücks“ ein
3. Nutzer speichert
4. Nutzer wählt den Balkonkasten und schaltet „Außerhalb des Grundstücks“ aus
5. Nutzer öffnet den Panel-Tab „Ebenen“

**Erwartete Ergebnisse**:
- Das Fenster zeigt die Himmelsrichtung „Süd, 180°“ nur lesend
- Nach dem Speichern trägt das Fenster Brüstungshöhe 0,9 m und Doppelverglasung, die Lampe „Pflanzenlampe“, 1,8 m,
  400 µmol/m²/s und „außerhalb des Grundstücks“
- Das Ausschalten beim Balkonkasten wird abgelehnt: ein Hinweis sagt, dass das Objekt aus der Grenze ragt; der
  Schalter bleibt an, es entsteht keine ungespeicherte Änderung
- Die Objekt-Legende im Tab „Ebenen“ nennt Fenster, Lampe und Möbel

**Nachbedingungen**:
- Fenster und Lampe mit den neuen Eigenschaften gespeichert; Balkonkasten unverändert

**Tags**: [req-053, welle-10, indoor, objekteigenschaften, fenster, lampe, off-site, desktop, gp-fr-180]

---

### TC-053-106: Indoor-Plan ohne Inhalt — Leerzustand, „Grundriss zeichnen“, Fenster einzeichnen

**Requirement**: REQ-053 §9.8 GP-FR-182, GP-UX-049, GP-FR-180, GP-FR-181 (Himmelsrichtung), GP-UX-064 (Tabname)
**Gerät**: Desktop
**Priority**: High
**Category**: Indoor
**Preconditions**:
- Eine Indoor-Site ohne Plan; zum Vergleich eine Outdoor-Site ohne Plan

**Testschritte**:
1. Nutzer öffnet den Plan der Outdoor-Site
2. Nutzer öffnet den Plan der Indoor-Site
3. Nutzer wählt „Grundriss zeichnen“
4. Nutzer wählt das Werkzeug „Gartenobjekt“, den Typ „Fenster“ und die Form „Linie“, setzt zwei Punkte von rechts
   nach links (6,0 | 5,0 m → 3,0 | 5,0 m) und wählt „Fertig“
5. Nutzer speichert

**Erwartete Ergebnisse**:
- Die Outdoor-Site zeigt den Garten-Leerzustand mit „Erstes Beet anlegen“
- Die Indoor-Site zeigt den Indoor-Leerzustand: „Zeichne die Umrisse deiner Wohnung oder lade ein Foto als Vorlage“,
  mit den Handlungen „Grundriss zeichnen“ und „Foto als Vorlage laden“ und ohne „Erstes Beet anlegen“
- Nach Schritt 3 erscheint der Editor; der Tab für die Beetliste heißt „Pflanzplätze“
- Nach Schritt 4 ist das Fenster ausgewählt; das Panel zeigt die Himmelsrichtung „Süd, 180°“ und den Hinweis, dass die
  Außenseite aus der Zeichenrichtung angenommen wurde (der Plan hat keinen Umriss)
- Nach dem Speichern hält der Plan genau ein Gartenobjekt: das Fenster als Linie mit den gesetzten Endpunkten

**Nachbedingungen**:
- Der Indoor-Plan enthält ein Fenster

**Tags**: [req-053, welle-10, indoor, leerzustand, zeichnen, fenster, desktop, gp-fr-182, gp-ux-049, gp-fr-180]

---

### TC-053-107: „Aus Fenster vorschlagen“ — Vorschau, Abbrechen ändert nichts, Bestätigen ändert nur das Sonnenfenster

**Requirement**: REQ-053 §9.8 GP-FR-181; G-W10 c („nie automatisch überschreiben“); WP 10.7 (abgeleitet)
**Gerät**: Desktop
**Priority**: High
**Category**: Indoor
**Preconditions**:
- Indoor-Site, Grundriss 6 × 4 m, Nordrichtung 0°, ohne GPS-Koordinaten
- Ein Fenster als Linie an der Südwand; ein Zelt 1,2 × 1,2 m, 25 cm vom Fenster entfernt
- Am Zelt: Sonnenklasse „Halbschatten“, Sonnenstunden im Sommer 4, Sonnenfenster unbekannt

**Testschritte**:
1. Nutzer wählt das Zelt und wählt „Aus Fenster vorschlagen“
2. Nutzer liest die Vorschau und wählt „Abbrechen“
3. Nutzer wählt erneut „Aus Fenster vorschlagen“ und dann „Übernehmen“
4. Nutzer speichert

**Erwartete Ergebnisse**:
- Die Vorschau nennt „Vorschlag: Mittags“ und „Eingetragen ist: Unbekannt“, listet das Fenster mit der Richtung Süd und
  weist darauf hin, dass ohne GPS-Koordinaten die Nordhalbkugel angenommen wird
- Nach „Abbrechen“ ist der Dialog zu, es gibt keine ungespeicherte Änderung, und der gespeicherte Stand des Zelts ist
  unverändert
- Nach „Übernehmen“ zeigt die Kopfzeile eine ungespeicherte Änderung
- Nach dem Speichern trägt das Zelt das Sonnenfenster „Mittags“; Sonnenstunden (4), Laubschatten (aus) und die
  Sonnenklasse „Halbschatten“ sind unverändert

**Nachbedingungen**:
- Sonnenfenster des Zelts „Mittags“

**Tags**: [req-053, welle-10, indoor, fenster, sonnenfenster, vorschlag, desktop, gp-fr-181]

---

### TC-053-108: Indoor-Plan — Tab und Liste „Pflanzplätze“ mit Zelt und Regal, keine Frost-Ebene

**Requirement**: REQ-053 §9.8 GP-FR-183, GP-FR-182, §17.3 GP-UX-064 — AC-13 (Teil)
**Gerät**: Desktop
**Priority**: Medium
**Category**: Indoor
**Preconditions**:
- Indoor-Site mit einem Zelt, einem Regal und einem Zimmer (das Zimmer trägt keine Pflanzplätze)
- Zum Vergleich ein Garten mit einem Hochbeet

**Testschritte**:
1. Nutzer öffnet den Indoor-Plan und liest die Tabs
2. Nutzer wählt den Tab für die Beetliste
3. Nutzer wechselt zum Tab „Plan“ und öffnet den Panel-Tab „Ebenen“
4. Nutzer öffnet den Garten und wiederholt Schritt 1 und 3

**Erwartete Ergebnisse**:
- Im Indoor-Plan heißt der Tab „Pflanzplätze“; gewählt steht in der URL `tab=beds`
- Die Liste ist mit „Pflanzplätze“ überschrieben und enthält genau das Zelt und das Regal, nicht das Zimmer
- Der Tab „Ebenen“ des Indoor-Plans bietet die Ebene „Sonne“, aber keine Ebene „Frost“
- Im Garten heißt derselbe Tab „Beete“, und der Tab „Ebenen“ bietet die Ebene „Frost“

**Nachbedingungen**:
- Keine Änderung

**Tags**: [req-053, welle-10, indoor, pflanzplaetze, beetliste, ebenen, desktop, gp-fr-183, gp-fr-182, ac-13]

---

## Abdeckungs-Matrix

| GP-ACC | Kriterium (Kurzform) | Testfälle |
|--------|----------------------|-----------|
| GP-ACC-001 | Gartengrenze 10 × 10 m zeichnen und speichern | TC-053-001 |
| GP-ACC-002 | Beet-Rechteck nach Snap 2 × 1 m, Verhältnis 2:1 | TC-053-002 |
| GP-ACC-005 | Beet verschieben/drehen, Positionen wandern mit | TC-053-006 |
| GP-ACC-006 | Raster-Einrastung, Alt-Taste ohne Einrasten | TC-053-003 |
| GP-ACC-007 | Undo/Redo per Tastatur | TC-053-004 |
| GP-ACC-008 | Tastatursteuerung, Live-Region | TC-053-005 |
| GP-ACC-011 | Konflikt-Dialog „Neu laden" | TC-053-008 |
| GP-ACC-012 | Beet mit aktiven Pflanzen nicht löschbar | TC-053-010 |
| GP-ACC-015 | Beetstatus-Übergänge, Begründung, Historie | TC-053-013 |
| GP-ACC-016 | Beetliste-Zeile hebt Beet hervor | TC-053-012 |
| GP-ACC-019 | Durchlauf mit 6 geplanten Positionen | TC-053-015 |
| GP-ACC-020 | Pflanzen entstehen an geplanten Positionen | TC-053-016 |
| GP-ACC-021 | Doppelreservierung abgelehnt | TC-053-017 |
| GP-ACC-022 | Position korrigieren (Feldmodus) | TC-053-019 |
| GP-ACC-024 | Düngeaufgabe erledigen, Historie | TC-053-020 |
| GP-ACC-025 | Zeitpunkt Zukunft/zu alt abgelehnt | TC-053-021 |
| GP-ACC-026 | Ereignis korrigieren, Original unveränderbar | TC-053-022 |
| GP-ACC-027 | Historie-Filter, Pagination, Zeitstrahl | TC-053-023 |
| GP-ACC-028 | Fruchtfolge-Verlauf je Jahr | TC-053-024 |
| GP-ACC-029 | Erledigt in zwei Tipps, ≥ 64 px | TC-053-025 |
| GP-ACC-030 | PDF maßstäblich mit Leiste/Nordpfeil/Legende | TC-053-029 |
| GP-ACC-031 | JSON-Export und Wiederherstellung (Weg „Ersetzen“) | TC-053-030, TC-053-041 |
| GP-ACC-032 | Ansicht „Als Liste", Barrierefreiheit | TC-053-009 |
| GP-ACC-035 | Bestandsbeet ohne Geometrie | TC-053-011 |
| GP-ACC-036 | Zelt = Beetansicht, Slot verschieben | TC-053-014 |
| GP-ACC-039 | Nachkultur und überlappendes Zeitfenster | TC-053-017 |
| GP-ACC-040 | „Beet räumen" | TC-053-027 |
| GP-ACC-044 | Ereignis schwärzen (Leitung) | TC-053-028 |
| GP-ACC-047 | Fruchtfolge-Hinweis, „Trotzdem pflanzen" | TC-053-018 |
| GP-ACC-048 | Chip „Gejätet/Gemulcht", Rückgängig 8 s | TC-053-026 |
| GP-ACC-051 | Pflanzen-Info beim Überfahren ohne Nachladen | TC-053-034 |
| GP-ACC-052 | Pflanzenzustände auch in Graustufen/Rot-Grün unterscheidbar | TC-053-035 |
| (abgeleitet aus GP-UX-032/033) | Hit-Priorität, Stapelauswahl | TC-053-031 |
| (abgeleitet aus GP-UX-034–038) | Touch-Zeichnen, dichte Pflanzen, Mehrfachauswahl | TC-053-032, TC-053-033 |
| (abgeleitet aus GP-FR-157/160) | Sonne/Schatten erfassen, Eignungs-Ampel | TC-053-036, TC-053-037 |
| (abgeleitet aus GP-FR-151/153) | Eltern-Kind, Löschdialog | TC-053-038 |
| (abgeleitet aus GP-UX-044/046) | Maßeingabe, Tastatur | TC-053-039 |
| (abgeleitet aus GP-FR-150, GP-NFR-067) | Zoom und Beschriftung | TC-053-040 |
| (abgeleitet aus GP-FR-170) | Wiederherstellung per Import | TC-053-041 |
| (abgeleitet aus GP-FR-171) | Saison-Kopie (SHOULD) | TC-053-042 |
| (abgeleitet aus GP-NFR-068–070) | Fokusmodell | TC-053-043 |
| (abgeleitet aus §9.8) | Indoor-Grundriss (SHOULD) | TC-053-044 |
| (abgeleitet aus UC-02) | Speichern-Status, Verlassen-Dialog | TC-053-007 |
| (abgeleitet aus UC-11) | Plan drucken | TC-053-029 |
| (abgeleitet aus UC-12) | Plan sichern (Export) | TC-053-030 |
| (abgeleitet aus GP-FR-110) | Zone anlegen, Beete aus der Mehrfachauswahl, Ebene „Zonen“ | TC-053-045 |
| (abgeleitet aus GP-FR-117) | Gießrunde nach Fläche verteilt, als verteilt gekennzeichnet; „Regen — übersprungen“ | TC-053-046, TC-053-047 |
| (abgeleitet aus GP-UX-031) | Ebene „zuletzt gegossen“ | TC-053-048 |
| (abgeleitet aus GP-FR-044/045) | Beet aus Vorlage, Standardgrößen | TC-053-049, TC-053-050 |
| (abgeleitet aus GP-FR-012) | Objekt-Snap, `Alt` schaltet ab | TC-053-051 |
| (abgeleitet aus GP-FR-029) | Ausrichten und verteilen | TC-053-052 |
| (abgeleitet aus GP-FR-025) | Mehrfach duplizieren mit Namensschema | TC-053-053 |
| (abgeleitet aus GP-UX-004) | Auto-Save, Pause bei Konflikt | TC-053-054 |
| (abgeleitet aus GP-UX-014) | Mini-Map | TC-053-055 |
| (abgeleitet aus GP-UX-061, GP-FR-169) | Ebenen „Pflanzenzustand“ und „Sonnenfenster“, Filter „Nur Pflanzen mit Handlungsbedarf“ | TC-053-056 |
| (abgeleitet aus GP-FR-172) | Teilexport der Auswahl, Import in einen anderen Standort | TC-053-057 |
| (abgeleitet aus GP-FR-148/170) | Früheren Stand wiederherstellen | TC-053-058 |
| (abgeleitet aus GP-FR-158/159, GP-UX-057) | Sonnenfenster im Feldmodus | TC-053-059 |
| (abgeleitet aus GP-NFR-071) | Messprofil Interaktion: INP, Pinch-Frametime, Feldmodus bei 4× CPU (beratend) | TC-053-060 |
| (abgeleitet aus GP-FR-122) | Welle 8 Teil A: Bodenanalyse erfassen, Verlauf je Methode; Validierung | TC-053-061, TC-053-062 |
| (abgeleitet aus GP-FR-123) | Welle 8 Teil A: Flächendosis, Gesamtmenge live (ergänzt TC-053-020) | TC-053-063 |
| (abgeleitet aus GP-FR-124) | Welle 8 Teil A: Bodenverbesserung, Kalkung mit Hinweistext | TC-053-064 |
| (abgeleitet aus GP-FR-125) | Welle 8 Teil A: Nährstoff-Hinweis ohne Zahl (Ausgangszustand, Gegenprobe) | TC-053-065, TC-053-066 |
| (abgeleitet aus GP-FR-104) | Welle 8 Teil A: Historie als CSV | TC-053-067 |
| (abgeleitet aus GP-FR-135) | Welle 8 Teil A: Rotationsmatrix, Nacherfassung aus der Zelle | TC-053-068 |
| (abgeleitet aus GP-FR-133) | Welle 8 Teil A: Folgekultur-Empfehlung, Fruchtfolge-Schalter | TC-053-069 |
| (abgeleitet aus GP-FR-086) | Welle 8 Teil A: Vorschlag annehmen / verwerfen | TC-053-070, TC-053-071 |
| (abgeleitet aus GP-FR-134) | Welle 8 Teil B: Ebene „Mischkultur“ | TC-053-072 |
| (abgeleitet aus GP-FR-162/163/168) | Welle 8 Teil B: Standortmerkmale (Mikroklima, Wind, Hang, Ausrichtung) | TC-053-073 |
| (abgeleitet aus GP-FR-161) | Welle 8 Teil B: Eignungs-Ampel Frost/Wind/Drainage | TC-053-074 |
| (abgeleitet aus GP-UX-057) | Welle 8 Teil B: Feldmodus-Chips „Feucht/Normal/Trocken“, „Windig“ (Sonne: TC-053-059) | TC-053-075 |
| (abgeleitet aus GP-FR-166) | Welle 8 Teil B: Erreichbarkeits-Hinweis | TC-053-076 |
| (abgeleitet aus GP-FR-051) | Welle 8 Teil B: Beet-Fotos Desktop und Feldmodus (Aktion ≥ 64 px) | TC-053-077, TC-053-078 |
| (abgeleitet aus GP-FR-145/175) | Welle 8 Teil B: CSV-Beetliste, Spaltenauswahl, Opt-in Zuweisung | TC-053-079, TC-053-080 |
| (abgeleitet aus GP-FR-174) | Welle 8 Teil B: CSV-Beetlisten-Import mit Prüfbericht | TC-053-081 |
| (abgeleitet aus §11.4, GP-FR-162) | Welle 8 Teil B: Frost-Grund im Pflanzenzustand | TC-053-082 |
| (abgeleitet aus GP-NFR-033/034, D-01) | Welle 9: Renderer-Messung, Drag-/Zoom-Frametime, Desktop und Mobile CPU 4× (beratend) | TC-053-083 |
| (abgeleitet aus UI-NFR-012 R-001/R-002/R-007/R-059) | Welle 9 Teil A: Service Worker aktiv, Manifest | TC-053-084 |
| (abgeleitet aus UI-NFR-012 R-007/R-010, §5.1.5) | Welle 9 Teil A: App-Shell ohne Verbindung | TC-053-085 |
| (abgeleitet aus GP-UX-024, UI-NFR-012 R-057) | Welle 9 Teil A: Plan ohne Verbindung lesbar, „Stand von …“ | TC-053-086 |
| (abgeleitet aus GP-UX-024, UI-NFR-012 R-021/R-025/R-058) | Welle 9 Teil A: „Erledigt“, Notiz und Foto gepuffert und übertragen | TC-053-087, TC-053-088 |
| (abgeleitet aus UI-NFR-012 R-028/R-032) | Welle 9 Teil A: Konflikt-Dialog bei inzwischen geschlossener Aufgabe | TC-053-089 |
| (abgeleitet aus UI-NFR-012 R-055/R-056, SR-019) | Welle 9 Teil A: Abmelden leert Zwischenspeicher und Namensraum | TC-053-090 |
| (abgeleitet aus GP-FR-144) | Welle 9 Teil B: PNG-Export, Faktor × Ansicht | TC-053-091 |
| (abgeleitet aus GP-FR-173, GP-API-070/071) | Welle 9 Teil B: Vorlage exportieren und importieren | TC-053-092 |
| (abgeleitet aus GP-FR-176, SR-024) | Welle 9 Teil B: Parzellenseite im PDF mit Opt-in | TC-053-093 |
| (abgeleitet aus GP-FR-165) | Welle 9 Teil B: Standort-Flags im Panel und als Chip | TC-053-094 |
| (abgeleitet aus GP-FR-167) | Welle 9 Teil B: Nächste Wasserquelle in Beetliste, Kopf und CSV | TC-053-095 |
| (abgeleitet aus GP-FR-025/026, V-05) | Welle 9 Teil B: Strg+D dupliziert (ohne Slot-Kopie, siehe unten) | TC-053-096 |
| (abgeleitet aus GP-NFR-033, D-01) | Welle 9 Teil B: Renderer-Umschaltung SVG/Konva bei 3 000 Objekten | TC-053-097 |
| (abgeleitet aus AC-7, AC-12, GP-UX-064) | Welle 10 Teil A: Tabs mit URL-Zustand, Deep-Link, „Zurück“, Feldmodus ohne Tabs | TC-053-098 |
| (abgeleitet aus AC-8, AC-16, GP-UX-065) | Welle 10 Teil A: Tab-Wechsel behält Änderung, Auswahl und Zoom, kein Dialog (Verlassen: TC-053-007) | TC-053-099 |
| (abgeleitet aus AC-4, AC-5, AC-6, AC-17, GP-UX-068) | Welle 10 Teil A: Seitenpanel, Zustandsregel, Panel-Tabs per Tastatur | TC-053-100 |
| (abgeleitet aus AC-1, AC-3, AC-14, GP-UX-067/069) | Welle 10 Teil A: Desktop 1366 × 768, Zeichenfläche ≥ 60 %, Panel angedockt | TC-053-101 |
| (abgeleitet aus GP-UX-069) | Welle 10 Teil A: Tablet 820 × 1180 (md), Panel als Drawer | TC-053-102 |
| (abgeleitet aus AC-2, GP-UX-001/069) | Welle 10 Teil A: jede Editor-Funktion bei 1024 px — **blockiert durch #2868**, kein Test | TC-053-103 |
| (abgeleitet aus AC-9, AC-15, GP-UX-063/069) | Welle 10 Teil A: Smartphone 390 × 844, `TouchBar`, Bottom Sheet, Überlauf | TC-053-104 |
| (abgeleitet aus GP-FR-180, §9.5) | Welle 10 Teil A: Fenster- und Lampen-Eigenschaften, Objekt-Legende, „Außerhalb des Grundstücks“ | TC-053-105 |
| (abgeleitet aus GP-FR-182, GP-UX-049, GP-FR-180) | Welle 10 Teil A: Indoor-Leerzustand, Grundriss zeichnen, Fenster einzeichnen | TC-053-106 |
| (abgeleitet aus GP-FR-181) | Welle 10 Teil A: Fenster-Vorschlag mit Vorschau, Abbrechen, Bestätigen | TC-053-107 |
| (abgeleitet aus GP-FR-183, GP-FR-182, AC-13) | Welle 10 Teil A: Tab und Liste „Pflanzplätze“, keine Frost-Ebene | TC-053-108 |

## Nicht abgedeckte Akzeptanzkriterien

Diese Kriterien haben keinen browser-beobachtbaren Weg in diesem Zuschnitt und gehören anderen
Testebenen:

| GP-ACC | Kriterium (Kurzform) | Grund |
|--------|----------------------|-------|
| GP-ACC-003 | Flächenberechnung des Polygons (Unit) | reine Berechnungsfunktion (Unit-Test) |
| GP-ACC-004 | Selbstschnitt-Erkennung (Unit) | Unit-Test der Validierung; im Browser nur indirekt über die Fehlermarkierung (GP-UX-017) |
| GP-ACC-009 | Objekt außerhalb des Gartens im Batch abgelehnt | API-Fehlervertrag; Integrationstest |
| GP-ACC-010 | Gleichzeitige Batches, Revisionskonflikt | API-Vertrag; die sichtbare Wirkung ist in TC-053-008 abgedeckt |
| GP-ACC-013 | Obergrenze 501 Operationen je Batch | API-Limit, nicht über die Oberfläche herstellbar |
| GP-ACC-014 | Mandantenisolation Plan/Batch | Sicherheitstest auf API-Ebene |
| GP-ACC-017 | Layout-Berechnung 3 Reihen × 10 Positionen, Parität Backend/Frontend | Unit-Test mit Testvektoren |
| GP-ACC-018 | Layout im Dreieckbeet innerhalb des Polygons | Unit-Test |
| GP-ACC-023 | Nachbarschaftskanten zwischen Slots | Graph-Datenvertrag, nicht sichtbar |
| GP-ACC-033 | Benchmark Verschieben, Culling | Performance-Benchmark: `applyOperation.benchmark.test.ts` (Median ≤ 1 ms, Benchmark-Lauf), `SvgPlanRenderer.test.tsx` (DOM-Budget auf dem Plan „groß“, immer an), `test_plan_calculators_benchmark.py`; nach der Label-Platzierung (#2490) erneut grün |
| GP-ACC-034 | Benchmark Plan-Abfrage p95 | Performance-Benchmark |
| GP-ACC-037 | Migration Zehrerstufen | Migrationstest |
| GP-ACC-038 | Migration Wiederholungsregeln | Migrationstest |
| GP-ACC-041 | Fremde Mandanten-Referenzen abgelehnt | Sicherheitstest auf API-Ebene |
| GP-ACC-042 | Gärtner darf Batch mit Löschung nicht (Rollen) | API-Rollentest; die sichtbare Löschwirkung ist in TC-053-010 und TC-053-028 teilweise abgedeckt |
| GP-ACC-043 | Layout-Vorschau mit zu vielen Positionen | API-Limit, Antwortzeit |
| GP-ACC-045 | Schutz vor Injektion im Beetnamen (SVG/PDF) | Sicherheitstest auf API-Ebene |
| GP-ACC-046 | Site-Anker-Prädikat im Service; kein `tenant_key` auf Location/Slot/GardenObject (revidiert v1.4, E-01) | Service-/Integrationstest |
| GP-ACC-049 | Migration Spezies-Zehrerstufe | Unit-/Migrationstest |
| GP-ACC-050 | Pflanzenzustand als reine Funktion, Frontend-Port identisch | Unit-Test (Calculator, Port-Gleichheit) |
| GP-ACC-053 | Eignungs-Matrix `site_fit` mit gemeinsamen Testvektoren, inkl. „Toleranz unbekannt" (v1.4, E-05) | Unit-Test (Calculator, Port-Gleichheit); sichtbare Ampel in TC-053-037 |
| GP-ACC-054 | Disjunkte `row_assignment` bei Mischkultur, Slots tragen den richtigen Entry (v1.4) | Integrationstest (Datenvertrag `run_planned_at`); Reihenlayout sichtbar in TC-053-015 |
| GP-ACC-055 | Fruchtfolge standardmäßig aus für Pflanzgefäß/Zelt/Regal, je Beet einschaltbar (v1.4) | Integrationstest (`validate-planting`); Hinweis-Anzeige in TC-053-018 |
| GP-ACC-056 | Plan-Rahmen mit Punkt > 1 000 m abgelehnt (v1.4) | API-Fehlervertrag; Integrationstest |
| GP-ACC-057 | Mandantenweite Historie: nur eigener Mandant, 90 Tage, paginiert (v1.4) | Sicherheits-/Integrationstest auf API-Ebene; Filter-Anzeige in TC-053-023 |

## Nicht abgedeckte Welle-8-Zeilen

| Zeile | Grund |
|-------|-------|
| GP-FR-105 | Täglicher Konsistenz-Job (Celery): läuft ohne Nutzeraktion, kein Auslöser und keine eigene Oberfläche. Beobachtbar wäre nur das nachträgliche Auftauchen von Einträgen mit der Auslöser-Art „Nacherfassung“ in der Historie; das gehört in einen Integrationstest mit Job-Aufruf. |
| GP-FR-165 | COULD, in Welle 8 ohne Oberfläche; seit Welle 9 abgedeckt durch TC-053-094. |
| GP-FR-167 | COULD, in Welle 8 ohne Oberfläche; seit Welle 9 abgedeckt durch TC-053-095. |
| Mengen-Obergrenzen (500 Kanten je Antwort, 500 Zeilen je CSV-Import, 50 000 Zeilen je Historien-CSV, Quote 1 MiB) | API-Grenzen, über die Oberfläche nicht herstellbar; Integrationstest. |

Teilweise nicht abgedeckt: der Import aus GP-ACC-031 ist über TC-053-041 für den Weg „Ersetzen“ abgedeckt; die Konfliktfälle der Ersetzungs-/Wiederherstellungsfunktion sowie die Quoten- und
Prüfregeln der Datei sind kein Browser-Artefakt.

## Nicht abgedeckte Welle-9-Teile

| Teil | Grund |
|------|-------|
| GP-FR-025: Slots beim Duplizieren mitkopieren | Bewusst nicht gebaut: die abschließende Batch-Operationsliste hat kein `create_slot` (§32.4 Pkt. 8, entschieden); ein Duplikat beginnt ohne Pflanzpositionen. Der Satz „bei Beeten werden Slots mitkopiert“ widerspricht dieser Entscheidung, die Betreiberentscheidung steht aus (`GP-REQ-wave7-gaps.json`). TC-053-096 legt ein Beet ohne Positionen an und sagt über Slots nichts aus. |
| GP-FR-176: Mitgliedernamen in der Tabelle der Parzellenseite | Das E2E-Image hat keine Textextraktion für den PDF-Inhalt (der Seiteninhalt sind Glyphen-Nummern einer Teilschrift); TC-053-093 liest die Lesezeichen (Überschriften) und die Anfrage des Dialogs. Die Spalte selbst prüfen die Tests der Druck-Engine serverseitig. |
| GP-FR-165: Flag-Hinweis im Dialog „Bepflanzen“ | Der Hinweis erscheint erst mit einer gewählten Art; TC-053-094 deckt Panel und Chip ab, die das Issue nennt. |
| Gefüllter kontobezogener API-Zwischenspeicher des Service Workers (`kp:{Konto}:{Mandant}`) | Das Backend antwortet auf jede `/api/v1/`-Lesung mit `Cache-Control: no-store` (MT-044), und der Service Worker respektiert das (G-W9 c) — die Positivliste wird nie in den Zwischenspeicher geschrieben; die Offline-Lesung kommt aus IndexedDB (TC-053-086). TC-053-090 prüft deshalb den beim Service Worker angemeldeten Namensraum, nicht einen gefüllten Zwischenspeicher. |


## Nicht abgedeckte Welle-10-Teile (Teil A)

| Teil | Grund |
|------|-------|
| AC-2: jede Editor-Funktion bei 1024 × 768 | **Blockiert durch #2868**: die Werkzeuge Fläche, Pflanze setzen, Messen und Beschriftung aus GP-UX-001 sind getypt, aber nicht gebaut. TC-053-103 beschreibt den Fall ohne ausführbaren Test; TC-053-102 prüft bei 820 px (md) nur das Layout (Drawer, kein horizontales Scrollen) und nicht die Vollständigkeit der Werkzeuge. |
| AC-3: Seitenkopf der Route ohne eigene Aktionen | vitest (`EditorWorkspace`/`GardenPlanRoute`); TC-053-101 prüft die eine Kopfleiste und die vertikale Werkzeug-Leiste. |
| AC-4: „Als Vorlage speichern“ nur bei genau einem ausgewählten Beet | vitest; TC-053-100 prüft die Auswahlgruppe (nur bei Auswahl). |
| AC-10, AC-11 | AC-10 ist ein CI-Kriterium (alle Suiten grün), AC-11 ein Dokumentkriterium (REQ-053 v1.16); keines hat ein eigenes Browser-Artefakt. |
| AC-13: Tab „Beete“ lädt nach dem Speichern neu | vitest und der Welle-9-Fall der Beetliste (#2813); TC-053-108 prüft nur die Benennung „Pflanzplätze“. |
| AC-14: Höhe der Zeichenfläche mit und ohne Mini-Map gleich | vitest; TC-053-101 prüft nur, dass die Zoom-Steuerung innerhalb der Zeichenfläche liegt. |
| AC-16: Ausschnitt (Pan) nach dem Tab-Wechsel | vitest; TC-053-099 prüft Auswahl und Zoomstufe. |
| GP-FR-183: Raum-Hierarchie Wohnung → Raum → Fensterbank/Regal → Topf | COULD, nicht gebaut; TC-053-108 prüft Tab und Liste „Pflanzplätze“. |
| GP-FR-180: Tür und Rankhilfe im Panel | Gleiches Muster wie Fenster und Lampe (WP 10.6, PATCH-Roundtrip je Typ als vitest); TC-053-105 automatisiert Fenster, Lampe und den Schalter „Außerhalb des Grundstücks“. |

---

**Dokumenten-Ende**
