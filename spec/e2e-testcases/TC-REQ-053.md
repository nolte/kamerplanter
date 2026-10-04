---
req_id: REQ-053
title: Grafische Garten- und Beetplanung (Plan-Editor, Beetverwaltung, Pflanzplanung, Beetpflege, Feldmodus, Druck/Export)
category: Standorte & Pflanzplanung
test_count: 30
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
generated: "2026-10-04"
version: "1.2"
---

# Testfälle REQ-053: Grafische Garten- und Beetplanung

Dieses Dokument enthält End-to-End-Testfälle aus **REQ-053 Grafische Garten- und Beetplanung
v1.2**, ausschließlich aus der Perspektive eines Nutzers im Browser. Keine Endpunkte,
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
032, 035, 036, 039, 040, 044, 047 und 048. Die Kriterien sind dort, wo sie als Integrationstest
(I) formuliert sind, auf ihre sichtbare Wirkung in der Oberfläche reduziert; der Datenvertrag
selbst (Feldwerte, Fehlercodes, Edges) wird in Integrationstests geprüft.

Zusätzlich sind drei Testfälle aus Use Cases abgeleitet, die kein Akzeptanzkriterium trifft:
TC-053-007 (Speichern-Status und Verlassen-Dialog, abgeleitet aus UC-02 / GP-UX-003),
TC-053-029 (Plan drucken, abgeleitet aus UC-11) und TC-053-030 (Plan als JSON sichern,
abgeleitet aus UC-12).

**Nicht** abgedeckt sind die Kriterien GP-ACC-003, 004, 009, 010, 013, 014, 017, 018, 023,
033, 034, 037, 038, 041, 042, 043, 045, 046 und 049 — siehe Abschnitt „Nicht abgedeckte
Akzeptanzkriterien" am Dokumentende für die Begründung je Kriterium. Sie gehören in Unit-,
Integrations- und Benchmark-Tests.

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
- Der Dialog bietet „Neu laden" und „Änderungen als JSON herunterladen" (Kopie der
  eigenen Änderungen)
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
3. Nutzer wählt „brach" und trägt als Begründung „Bodenruhe" ein, bestätigt
4. Nutzer öffnet den Tab „Historie"

**Erwartete Ergebnisse**:
- Der Übergang von „aktiv" nach „geplant" wird nicht angeboten bzw. mit einer verständlichen
  Fehlermeldung abgelehnt
- „brach" wird übernommen; das Status-Badge am Beet zeigt „brach"
- Die Historie enthält einen Eintrag „Statuswechsel" mit der Begründung „Bodenruhe"

**Nachbedingungen**:
- Beet hat Status „brach"

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
- Beet mit Geometrie (z. B. 3,0 × 1,2 m); Spezies Tomate mit Steckbrief vorhanden

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
- Der Import ist in diesem Zuschnitt nicht Teil des Tests (SHOULD, siehe unten)

**Nachbedingungen**:
- Datei heruntergeladen; Plan unverändert

**Tags**: [req-053, export, json, sicherung, desktop, abgeleitet-uc-12, gp-acc-031]

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
| GP-ACC-031 | JSON-Export (Import nicht abgedeckt) | TC-053-030 |
| GP-ACC-032 | Ansicht „Als Liste", Barrierefreiheit | TC-053-009 |
| GP-ACC-035 | Bestandsbeet ohne Geometrie | TC-053-011 |
| GP-ACC-036 | Zelt = Beetansicht, Slot verschieben | TC-053-014 |
| GP-ACC-039 | Nachkultur und überlappendes Zeitfenster | TC-053-017 |
| GP-ACC-040 | „Beet räumen" | TC-053-027 |
| GP-ACC-044 | Ereignis schwärzen (Leitung) | TC-053-028 |
| GP-ACC-047 | Fruchtfolge-Hinweis, „Trotzdem pflanzen" | TC-053-018 |
| GP-ACC-048 | Chip „Gejätet/Gemulcht", Rückgängig 8 s | TC-053-026 |
| (abgeleitet aus UC-02) | Speichern-Status, Verlassen-Dialog | TC-053-007 |
| (abgeleitet aus UC-11) | Plan drucken | TC-053-029 |
| (abgeleitet aus UC-12) | Plan sichern (Export) | TC-053-030 |

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
| GP-ACC-033 | Benchmark Verschieben, Culling | Performance-Benchmark |
| GP-ACC-034 | Benchmark Plan-Abfrage p95 | Performance-Benchmark |
| GP-ACC-037 | Migration Zehrerstufen | Migrationstest |
| GP-ACC-038 | Migration Wiederholungsregeln | Migrationstest |
| GP-ACC-041 | Fremde Mandanten-Referenzen abgelehnt | Sicherheitstest auf API-Ebene |
| GP-ACC-042 | Gärtner darf Batch mit Löschung nicht (Rollen) | API-Rollentest; die sichtbare Löschwirkung ist in TC-053-010 und TC-053-028 teilweise abgedeckt |
| GP-ACC-043 | Layout-Vorschau mit zu vielen Positionen | API-Limit, Antwortzeit |
| GP-ACC-045 | Schutz vor Injektion im Beetnamen (SVG/PDF) | Sicherheitstest auf API-Ebene |
| GP-ACC-046 | Mandantenfilter am Repository | Repository-Test |
| GP-ACC-049 | Migration Spezies-Zehrerstufe | Unit-/Migrationstest |

Teilweise nicht abgedeckt: der Import aus GP-ACC-031 (SHOULD, nicht im MVP) und die
Konfliktfälle der Ersetzungs-/Wiederherstellungsfunktion; die Quoten- und Prüfregeln der Datei
sind kein Browser-Artefakt.

---

**Dokumenten-Ende**
