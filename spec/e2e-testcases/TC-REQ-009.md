---
req_id: REQ-009
title: Zentrales Monitoring-Dashboard & Analytics
category: Visualisierung
test_count: 42
coverage_areas:
  - Overview Dashboard (Hauptansicht)
  - Plant Grid Widget (Kanban-Style)
  - VPD Calculator Widget
  - Alert Center
  - Task Queue Widget
  - Harvest Calendar Widget (4-Wochen-Vorschau)
  - Yield Forecasting Widget
  - Climate Dashboard
  - Dashboard-Navigation und Routing
  - Responsive Layout (Mobile/Tablet/Desktop)
  - Dark Mode
  - Widget-Konfiguration
  - WebSocket Live-Updates (sichtbares Verhalten)
  - Auth-Zugriffsschutz
  - Leer-Zustände (Empty States)
generated: 2026-03-21
version: "2.0"
---

# TC-REQ-009 — Zentrales Monitoring-Dashboard & Analytics

> Alle Testfälle beschreiben die Nutzerperspektive im Browser. Keine API-Calls,
> HTTP-Statuscodes oder Datenbankoperationen werden in Testschritten erwähnt.
> Erwartete Ergebnisse beschreiben ausschliesslich sichtbare UI-Zustände.

---

## Abschnitt A — Dashboard-Navigation und Einstiegspunkt

### TC-009-001: Dashboard-Seite aufrufen (authentifizierter Nutzer)

**Requirement**: REQ-009 §1 — Business Case: Overview Dashboard als Hauptansicht
**Priority**: Critical
**Category**: Navigation / Happy Path
**Preconditions**:
- Nutzer ist eingeloggt (gültige Session)
- Mindestens ein Tenant ist vorhanden

**Test Steps**:
1. Nutzer öffnet die Anwendung im Browser (URL: `/`)
2. Nutzer beobachtet, wohin die Weiterleitung führt

**Expected Results**:
- Automatische Weiterleitung auf `/dashboard`
- Seite zeigt Titel "Dashboard" (i18n: `pages.dashboard.title`)
- Begrüssungstext "Willkommen bei Kamerplanter" ist sichtbar
- Abschnitt "Schnellaktionen" mit mindestens 6 Kacheln ist sichtbar
- Seiten-`data-testid="dashboard-page"` ist im DOM vorhanden

**Postconditions**: Nutzer befindet sich auf der Dashboard-Seite `/dashboard`

**Tags**: [req-009, dashboard, navigation, routing, auth]

---

### TC-009-002: Dashboard-Navigation aus der Sidebar heraus

**Requirement**: REQ-009 §1 — Business Case: Information at a Glance
**Priority**: High
**Category**: Navigation
**Preconditions**:
- Nutzer ist eingeloggt
- Nutzer befindet sich auf einer beliebigen anderen Seite (z. B. `/stammdaten/species`)

**Test Steps**:
1. Nutzer klickt in der Sidebar auf den Menüeintrag "Dashboard" (`nav.dashboard`)
2. Nutzer beobachtet die Navigation

**Expected Results**:
- Browser-URL wechselt zu `/dashboard`
- Dashboard-Seite rendert vollständig mit Titel und Schnellaktionen
- Kein Fehlerbildschirm erscheint

**Postconditions**: Nutzer ist auf `/dashboard`

**Tags**: [req-009, dashboard, navigation, sidebar]

---

### TC-009-003: Schnellaktions-Kacheln navigieren zu Zielseiten

**Requirement**: REQ-009 §1 — Business Case: Actionable Insights (jedes Widget führt zu konkreten Handlungen)
**Priority**: High
**Category**: Navigation / Happy Path
**Preconditions**:
- Nutzer ist auf `/dashboard`

**Test Steps**:
1. Nutzer klickt auf die Kachel "Botanische Familien" (`nav.botanicalFamilies`)
2. Nutzer navigiert zurück zum Dashboard (Browser-Zurück oder Sidebar)
3. Nutzer klickt auf die Kachel "Arten" (`nav.species`)
4. Nutzer navigiert zurück
5. Nutzer klickt auf die Kachel "Standorte" (`nav.sites`)
6. Nutzer navigiert zurück
7. Nutzer klickt auf die Kachel "Substrate" (`nav.substrates`)
8. Nutzer navigiert zurück
9. Nutzer klickt auf die Kachel "Pflanzen" (`nav.plantInstances`)
10. Nutzer navigiert zurück
11. Nutzer klickt auf die Kachel "Berechnungen" (`nav.calculations`)

**Expected Results**:
- Klick auf "Botanische Familien" navigiert zu `/stammdaten/botanical-families`
- Klick auf "Arten" navigiert zu `/stammdaten/species`
- Klick auf "Standorte" navigiert zu `/standorte/sites`
- Klick auf "Substrate" navigiert zu `/standorte/substrates`
- Klick auf "Pflanzen" navigiert zu `/pflanzen/plant-instances`
- Klick auf "Berechnungen" navigiert zu `/pflanzen/calculations`
- Jede Zielseite rendert fehlerfrei

**Postconditions**: Alle 6 Schnellaktionskacheln navigieren korrekt

**Tags**: [req-009, dashboard, quickactions, navigation]

---

### TC-009-004: Dashboard-Aufruf ohne Authentifizierung wird abgeblockt

**Requirement**: REQ-009 §4 — Authentifizierung & Autorisierung: Alle Endpunkte erfordern Authentifizierung
**Priority**: Critical
**Category**: Auth / Fehlermeldung
**Preconditions**:
- Nutzer ist NICHT eingeloggt (keine gültige Session)

**Test Steps**:
1. Nutzer ruft direkt `/dashboard` im Browser auf

**Expected Results**:
- Weiterleitung zur Login-Seite oder eine Fehlermeldung "Nicht autorisiert"
- Dashboard-Inhalte sind NICHT sichtbar

**Postconditions**: Nicht-authentifizierter Nutzer sieht kein Dashboard

**Tags**: [req-009, dashboard, auth, security]

---

## Abschnitt B — Overview Dashboard Widgets (Schnellübersicht)

### TC-009-005: Quick Stats — Pflanzenzähler im Overview-Bereich

**Requirement**: REQ-009 §1 — Overview Dashboard: Quick Stats (Pflanzen gesamt, in Blüte, Tage bis Ernte)
**Priority**: High
**Category**: Listenansicht / Happy Path
**Preconditions**:
- Nutzer ist auf `/dashboard`
- System enthält mindestens 3 aktive Pflanzen in verschiedenen Phasen

**Test Steps**:
1. Nutzer öffnet `/dashboard`
2. Nutzer betrachtet den Bereich "Statistiken" (`pages.dashboard.stats`)

**Expected Results**:
- Kennzahl "Pflanzen gesamt" zeigt die korrekte Gesamtanzahl an
- Kennzahl "In Blüte" zeigt die Anzahl der Pflanzen in der Blütephase an
- Kennzahl "Bereit zur Ernte" ist sichtbar (ggf. 0, wenn keine erntefähig)
- Alle Zahlen sind als lesbare Text-Elemente dargestellt (keine leeren Felder)

**Postconditions**: Statistik-Kacheln zeigen aktuelle Werte

**Tags**: [req-009, dashboard, overview, stats, plants]

---

### TC-009-006: Quick Stats — Leer-Zustand ohne Pflanzen

**Requirement**: REQ-009 §1 — Overview Dashboard: Quick Stats
**Priority**: Medium
**Category**: Leer-Zustand / Edge Case
**Preconditions**:
- Nutzer ist auf `/dashboard`
- Im System sind KEINE Pflanzen vorhanden (leere Datenbank oder frischer Tenant)

**Test Steps**:
1. Nutzer öffnet `/dashboard`
2. Nutzer betrachtet den Statistik-Bereich

**Expected Results**:
- Pflanzenzähler zeigt "0" an (kein Absturz, keine leere Seite)
- "In Blüte" zeigt "0" an
- "Bereit zur Ernte" zeigt "0" an
- Kein Fehlerbanner oder unbehandelter JS-Fehler ist sichtbar

**Postconditions**: Dashboard rendert stabil auch ohne Daten

**Tags**: [req-009, dashboard, empty-state, edge-case]

---

### TC-009-007: Task Queue Widget — Top-5-Aufgaben anzeigen

**Requirement**: REQ-009 §1 — Overview Dashboard: Task Queue (Top 5 fällige/überfällige Tasks)
**Priority**: High
**Category**: Listenansicht / Happy Path
**Preconditions**:
- Nutzer ist auf `/dashboard`
- Im System existieren mindestens 3 fällige oder überfällige Aufgaben

**Test Steps**:
1. Nutzer öffnet `/dashboard`
2. Nutzer sucht das Widget "Aufgaben" oder "Task Queue"

**Expected Results**:
- Das Widget listet maximal 5 Aufgaben auf
- Jede Aufgabe zeigt mindestens: Name/Beschreibung und Fälligkeitsdatum
- Überfällige Aufgaben sind visuell hervorgehoben (z. B. rote Farbe oder Icon)
- Ein Klick auf eine Aufgabe navigiert zur Aufgaben-Detailseite oder Aufgabenliste

**Postconditions**: Task Queue zeigt fällige Aufgaben

**Tags**: [req-009, dashboard, tasks, task-queue, widget]

---

### TC-009-008: Task Queue Widget — Leer-Zustand ohne fällige Aufgaben

**Requirement**: REQ-009 §1 — Overview Dashboard: Task Queue
**Priority**: Medium
**Category**: Leer-Zustand
**Preconditions**:
- Nutzer ist auf `/dashboard`
- Keine Aufgaben sind fällig oder überfällig

**Test Steps**:
1. Nutzer öffnet `/dashboard`
2. Nutzer betrachtet das Task-Queue-Widget

**Expected Results**:
- Widget zeigt eine leere Zustand-Nachricht (z. B. "Keine fälligen Aufgaben") anstatt eines leeren Bereichs
- Kein Fehler oder leeres Widget-Gerüst ohne Inhalt

**Postconditions**: Task Queue rendert stabil ohne Daten

**Tags**: [req-009, dashboard, tasks, empty-state]

---

## Abschnitt C — Plant Grid Widget (Kanban-Style)

### TC-009-009: Plant Grid — Pflanzen nach Phase farbkodiert

**Requirement**: REQ-009 §1 — Overview Dashboard: Plant Status Grid (Farbe = Phase)
**Priority**: High
**Category**: Listenansicht / Happy Path
**Preconditions**:
- Nutzer ist auf `/dashboard`
- System enthält Pflanzen in verschiedenen Phasen: Keimling, Vegetativ, Blüte, Reifung

**Test Steps**:
1. Nutzer öffnet `/dashboard` und navigiert zum Plant Grid Widget
2. Nutzer betrachtet die Farbgebung der Pflanzenkarten

**Expected Results**:
- Pflanzen in Phase "Keimling" erscheinen mit hellgrüner Karte
- Pflanzen in Phase "Vegetativ" erscheinen mit grüner Karte
- Pflanzen in Phase "Blüte" erscheinen mit violetter/lila Karte
- Pflanzen in Phase "Reifung" erscheinen mit oranger Karte
- Jede Karte zeigt: Pflanzenname, Phasenname, Standort (Location + Slot)

**Postconditions**: Plant Grid zeigt farbkodierte Pflanzenkarten

**Tags**: [req-009, plant-grid, phase, color-coding, widget]

---

### TC-009-010: Plant Grid — Health Score Sortierung (Critical zuerst)

**Requirement**: REQ-009 §2 — AQL Plant Grid Widget: `SORT health_score ASC, tasks_due DESC`
**Priority**: High
**Category**: Listenansicht / Happy Path
**Preconditions**:
- Nutzer ist auf `/dashboard`
- System enthält:
  - 1 Pflanze mit kritischem Alert (Health Score 0)
  - 2 Pflanzen mit Warning-Alert (Health Score 50)
  - 7 gesunde Pflanzen (Health Score 100)

**Test Steps**:
1. Nutzer öffnet `/dashboard` und betrachtet das Plant Grid Widget

**Expected Results**:
- Pflanzen mit rotem Icon (kritisch) erscheinen ganz oben im Grid
- Pflanzen mit gelbem Icon (Warnung) erscheinen vor gesunden Pflanzen
- Pflanzen ohne Alert erscheinen am Ende
- Die kritische Pflanze trägt ein rotes Warn-Icon ("🔴" oder äquivalentes Icon)
- Warning-Pflanzen tragen ein gelbes Icon ("🟡" oder äquivalentes Icon)
- Gesunde Pflanzen ohne offene Aufgaben tragen ein grünes Haken-Icon

**Postconditions**: Plant Grid sortiert Pflanzen nach Handlungsbedarf

**Tags**: [req-009, plant-grid, health-score, sorting, priority]

---

### TC-009-011: Plant Grid — Pflanze mit offenen Aufgaben zeigt Task-Icon

**Requirement**: REQ-009 §2 — AQL Plant Grid Widget: `status_icon` für `tasks_due > 0`
**Priority**: Medium
**Category**: Listenansicht
**Preconditions**:
- Nutzer ist auf `/dashboard`
- Eine Pflanze hat 2 fällige Aufgaben, aber keinen Alert

**Test Steps**:
1. Nutzer betrachtet das Plant Grid Widget

**Expected Results**:
- Die Pflanze mit offenen Aufgaben zeigt ein Aufgaben-Icon (z. B. Clipboard-Icon oder "📋")
- Die Anzahl fälliger Aufgaben (z. B. "2 Aufgaben") ist sichtbar oder per Tooltip zugänglich

**Postconditions**: Task-Indikator ist auf der Pflanzenkarte sichtbar

**Tags**: [req-009, plant-grid, tasks, icon]

---

### TC-009-012: Plant Grid — Klick auf Pflanzenkarte navigiert zur Detailseite

**Requirement**: REQ-009 §1 — Actionable Insights: jedes Widget führt zu konkreten Handlungen
**Priority**: High
**Category**: Navigation
**Preconditions**:
- Nutzer ist auf `/dashboard`
- Plant Grid Widget zeigt mindestens eine Pflanzenkarte

**Test Steps**:
1. Nutzer klickt auf eine Pflanzenkarte im Plant Grid Widget

**Expected Results**:
- Browser navigiert zur Detailseite der geklickten Pflanze (z. B. `/pflanzen/plant-instances/{id}`)
- Detailseite der Pflanze rendert ohne Fehler

**Postconditions**: Nutzer befindet sich auf der Pflanzdetailseite

**Tags**: [req-009, plant-grid, navigation, detail]

---

## Abschnitt D — VPD Calculator Widget

### TC-009-013: VPD Widget — Optimaler VPD-Bereich (grüne Anzeige)

**Requirement**: REQ-009 §1 — Climate Dashboard: VPD Calculator & Heatmap; §6 Szenario 2
**Priority**: High
**Category**: Detailansicht / Happy Path
**Preconditions**:
- Nutzer ist auf `/dashboard`
- VPD-Widget ist vorhanden
- Aktuelle Sensorwerte: Temperatur = 24 °C, Luftfeuchte = 60 %
- Ziel-VPD: 1,0 kPa, Toleranz: ±0,2 kPa
- Berechneter VPD ≈ 0,77 kPa (innerhalb Toleranz)

**Test Steps**:
1. Nutzer öffnet `/dashboard` und sucht das VPD-Widget

**Expected Results**:
- VPD-Widget zeigt den aktuellen VPD-Wert in kPa an (z. B. "0,77 kPa")
- Statusanzeige ist grün ("OPTIMAL" oder gleichbedeutend)
- Zielbereich wird als Bereich angezeigt (z. B. "Ziel: 0,8–1,2 kPa")
- Empfehlung lautet sinngemäss "Keine Änderung nötig"

**Postconditions**: VPD-Widget zeigt optimalen Zustand grün an

**Tags**: [req-009, vpd, climate, widget, optimal]

---

### TC-009-014: VPD Widget — VPD zu niedrig (rote Warnanzeige)

**Requirement**: REQ-009 §3 — VPDWidget.vpd_status: `LOW` wenn VPD < target - tolerance; §6 Szenario 2
**Priority**: High
**Category**: Fehlermeldung / Zustandswechsel
**Preconditions**:
- VPD-Widget vorhanden
- Aktuelle Werte führen zu VPD = 0,50 kPa (deutlich unter Minimum 0,80 kPa)

**Test Steps**:
1. Nutzer öffnet `/dashboard` und betrachtet das VPD-Widget

**Expected Results**:
- VPD-Wert "0,50 kPa" ist sichtbar
- Statusanzeige ist rot gefärbt (Status: "LOW" oder "ZU NIEDRIG")
- Empfehlungstext erscheint (sinngemäss: "Erhöhe Temperatur oder senke Luftfeuchte")
- Zielbereich-Indikator zeigt an, dass der aktuelle Wert ausserhalb liegt

**Postconditions**: VPD-Widget signalisiert Handlungsbedarf

**Tags**: [req-009, vpd, climate, widget, warning, low]

---

### TC-009-015: VPD Widget — VPD zu hoch (rote Warnanzeige)

**Requirement**: REQ-009 §3 — VPDWidget.vpd_status: `HIGH` wenn VPD > target + tolerance
**Priority**: High
**Category**: Fehlermeldung / Zustandswechsel
**Preconditions**:
- VPD-Widget vorhanden
- Aktuelle Werte führen zu VPD = 1,80 kPa (über Maximum 1,20 kPa)

**Test Steps**:
1. Nutzer öffnet `/dashboard` und betrachtet das VPD-Widget

**Expected Results**:
- VPD-Wert "1,80 kPa" ist sichtbar
- Statusanzeige ist rot gefärbt (Status: "HIGH" oder "ZU HOCH")
- Empfehlungstext erscheint (sinngemäss: "Senke Temperatur oder erhöhe Luftfeuchte")

**Postconditions**: VPD-Widget signalisiert zu hohe Transpirationsbelastung

**Tags**: [req-009, vpd, climate, widget, warning, high]

---

### TC-009-016: VPD Widget — Manueller VPD-Rechner (Interactive Widget)

**Requirement**: REQ-009 §1 — Interactive-Widgets: VPD Calculator (Input: Temp/RLF → Output: VPD)
**Priority**: Medium
**Category**: Happy Path / Formvalidierung
**Preconditions**:
- Nutzer ist auf `/dashboard`
- VPD-Widget zeigt den interaktiven Rechner-Modus

**Test Steps**:
1. Nutzer gibt im Temperaturfeld "26" ein
2. Nutzer gibt im Luftfeuchte-Feld "55" ein
3. Nutzer beobachtet die Berechnung

**Expected Results**:
- VPD wird in Echtzeit berechnet und angezeigt (Wert ca. 1,25 kPa bei T=26°C, RH=55%)
- Berechneter Wert aktualisiert sich ohne Seitenneuladen
- Einheitenangabe "kPa" ist sichtbar
- Wenn aktiviert: Empfehlungstext passt sich an das Ergebnis an

**Postconditions**: Manuell eingegebene Werte ergeben korrekte VPD-Anzeige

**Tags**: [req-009, vpd, calculator, interactive, widget]

---

### TC-009-017: VPD Widget — Keine Sensordaten verfügbar (Leer-Zustand)

**Requirement**: REQ-009 §2 — AQL VPD: `LET temp_c = FIRST(...)` kann null zurückgeben
**Priority**: Medium
**Category**: Leer-Zustand / Edge Case
**Preconditions**:
- VPD-Widget vorhanden
- Keine Sensordaten der letzten 15 Minuten verfügbar

**Test Steps**:
1. Nutzer öffnet `/dashboard` und betrachtet das VPD-Widget

**Expected Results**:
- Widget zeigt eine Meldung wie "Keine aktuellen Sensordaten verfügbar" oder "--"
- Kein Absturz oder leeres Gerüst ohne Erklärung
- Manuelle Eingabefelder (wenn vorhanden) sind weiterhin nutzbar

**Postconditions**: VPD-Widget rendert stabil ohne Sensor-Daten

**Tags**: [req-009, vpd, empty-state, sensor, edge-case]

---

## Abschnitt E — Alert Center

### TC-009-018: Alert Center — Kritischen Alert anzeigen

**Requirement**: REQ-009 §1 — Overview Dashboard: Alert Center (kritische Warnungen prominent); §6 Szenario 7
**Priority**: Critical
**Category**: Fehlermeldung / Listenansicht
**Preconditions**:
- Nutzer ist auf `/dashboard`
- Mindestens 1 unbestätigter kritischer Alert existiert (Severity: `critical`)

**Test Steps**:
1. Nutzer öffnet `/dashboard`
2. Nutzer sucht das Alert-Center-Widget

**Expected Results**:
- Kritische Alerts erscheinen oben im Alert-Feed
- Kritische Alerts sind rot hervorgehoben
- Jeder Alert zeigt: Nachricht/Beschreibung, Zeitstempel, Quelle
- Ein Badge oder Zähler zeigt die Anzahl unbestätigter Alerts an (z. B. rote Zahl)

**Postconditions**: Kritischer Alert ist prominent sichtbar

**Tags**: [req-009, alerts, critical, alert-center, widget]

---

### TC-009-019: Alert Center — Alert bestätigen (Acknowledge)

**Requirement**: REQ-009 §2 — Alert-Modell: `acknowledged: bool`; `acknowledged_at: Optional[datetime]`
**Priority**: High
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer ist auf `/dashboard`
- Alert-Center zeigt mindestens 1 unbestätigten Alert

**Test Steps**:
1. Nutzer klickt auf den "Bestätigen"- oder "Erledigt"-Button eines Alerts
2. Nutzer beobachtet die Änderung im Widget

**Expected Results**:
- Der Alert verschwindet aus dem "unbestätigt"-Bereich oder wird visuell als bestätigt markiert
- Die Alert-Zähler-Badge aktualisiert sich (Zahl verringert sich um 1)
- Bestätigungszeit wird ggf. angezeigt
- Kein Seitenneuladen notwendig

**Postconditions**: Alert ist als bestätigt markiert und aus dem aktiven Feed entfernt

**Tags**: [req-009, alerts, acknowledge, state-change, widget]

---

### TC-009-020: Alert Center — Actionable Alert führt zu Zielseite

**Requirement**: REQ-009 §2 — Alert-Modell: `actionable: bool`, `action_url: Optional[str]`
**Priority**: Medium
**Category**: Navigation
**Preconditions**:
- Alert-Center zeigt einen Alert mit hinterlegtem Aktionslink

**Test Steps**:
1. Nutzer klickt auf den Aktions-Button oder Link eines "actionable" Alerts

**Expected Results**:
- Browser navigiert zur verlinkten Seite (z. B. zur betroffenen Pflanze oder Aufgabe)
- Zielseite rendert ohne Fehler

**Postconditions**: Nutzer befindet sich auf der verlinkten Zielseite

**Tags**: [req-009, alerts, actionable, navigation]

---

### TC-009-021: Alert Center — Leer-Zustand (keine Alerts)

**Requirement**: REQ-009 §1 — Alert Center
**Priority**: Low
**Category**: Leer-Zustand
**Preconditions**:
- Keine unbestätigten Alerts vorhanden

**Test Steps**:
1. Nutzer öffnet `/dashboard` und betrachtet das Alert-Center-Widget

**Expected Results**:
- Widget zeigt einen positiven Leer-Zustand (z. B. "Alles in Ordnung – keine Alerts")
- Kein Fehler oder leeres Widget-Gerüst

**Postconditions**: Alert Center zeigt stabilen Leer-Zustand

**Tags**: [req-009, alerts, empty-state]

---

## Abschnitt F — Harvest Calendar Widget (4-Wochen-Vorschau)

### TC-009-022: Harvest Calendar — Pflanzen nach Erntewochen gruppiert

**Requirement**: REQ-009 §6 Szenario 4 — Harvest Calendar 4-Wochen-Vorschau mit Wochen-Gruppierung
**Priority**: High
**Category**: Listenansicht / Happy Path
**Preconditions**:
- Nutzer ist auf `/dashboard`
- System enthält Pflanzen mit Ernte-Schätzungen:
  - Pflanze A: morgen fällig
  - Pflanze B: in 3 Tagen
  - Pflanze C: in 10 Tagen
  - Pflanze D: in 20 Tagen
  - Pflanze E: überfällig (vor 2 Tagen)

**Test Steps**:
1. Nutzer öffnet `/dashboard` und sucht das Harvest-Calendar-Widget

**Expected Results**:
- Gruppenbezeichnung "Überfällig" (oder "Overdue") enthält Pflanze E, mit roter Hervorhebung
- Gruppe "Diese Woche" (oder "This Week") enthält Pflanzen A und B
- Gruppe "Nächste Woche" (oder "Next Week") enthält Pflanze C
- Gruppe "Woche 3" enthält Pflanze D
- Gruppen sind chronologisch sortiert (Überfällig → Diese Woche → Nächste Woche → ...)
- Pflanze E trägt einen visuellen Dringlichkeitsindikator (rot)

**Postconditions**: Ernte-Kalender gruppiert Pflanzen korrekt nach Ernte-Nähe

**Tags**: [req-009, harvest-calendar, widget, grouping, urgency]

---

### TC-009-023: Harvest Calendar — Ernte-Datum-Schätzung mit HarvestObservation

**Requirement**: REQ-009 §2 — Harvest Calendar AQL: Wenn `latest_obs.days_to_harvest_estimate` vorhanden, wird es bevorzugt
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Eine Pflanze hat eine HarvestObservation der letzten 7 Tage mit Tage-Schätzung

**Test Steps**:
1. Nutzer betrachtet das Harvest Calendar Widget

**Expected Results**:
- Die Pflanze erscheint mit dem aus der HarvestObservation berechneten Datum, nicht mit der generischen Phasen-Schätzung
- Die Anzeige ist kohärent (kein doppeltes Datum oder widersprüchliche Werte)

**Postconditions**: Verfeinerte Ernte-Schätzung wird im UI verwendet

**Tags**: [req-009, harvest-calendar, estimate, harvest-observation]

---

### TC-009-024: Harvest Calendar — Leer-Zustand ohne Ernte-Prognosen

**Requirement**: REQ-009 §1 — Harvest & Yield Dashboard: Harvest Calendar
**Priority**: Low
**Category**: Leer-Zustand
**Preconditions**:
- Keine Pflanzen mit Erntetermin innerhalb der nächsten 4 Wochen

**Test Steps**:
1. Nutzer betrachtet das Harvest Calendar Widget

**Expected Results**:
- Widget zeigt Leer-Zustand (z. B. "Keine Ernten in den nächsten 4 Wochen geplant")
- Kein Fehler oder leeres Widget

**Postconditions**: Harvest Calendar ist stabil ohne Daten

**Tags**: [req-009, harvest-calendar, empty-state]

---

## Abschnitt G — Yield Forecasting Widget

### TC-009-025: Yield Forecast — Hohe Konfidenz mit 10+ historischen Grows

**Requirement**: REQ-009 §6 Szenario 5 — Yield Forecast: sample_size >= 10 → confidence = 'high'
**Priority**: High
**Category**: Detailansicht / Happy Path
**Preconditions**:
- Nutzer ist auf `/dashboard`
- System enthält eine Pflanze in der Blütephase (Tag 35)
- Mindestens 10 historische Erntedaten für gleiche Art und Substrat vorhanden
- Historischer Durchschnitt: 80 g, Standardabweichung: 15 g

**Test Steps**:
1. Nutzer öffnet `/dashboard` und sucht das Yield-Forecast-Widget

**Expected Results**:
- Prognose zeigt "80 g" (oder ähnlichen Wert) an
- Konfidenzbereich "[65 g – 95 g]" ist sichtbar
- Konfidenz-Label lautet "Hoch" (oder "high")
- Anzahl der Vergleichs-Grows (z. B. "basierend auf 10 ähnlichen Grows") ist sichtbar

**Postconditions**: Yield Forecast mit hoher Konfidenz wird korrekt dargestellt

**Tags**: [req-009, yield-forecast, confidence, widget, high-confidence]

---

### TC-009-026: Yield Forecast — Niedrige Konfidenz mit weniger als 5 historischen Grows

**Requirement**: REQ-009 §3 — YieldForecast: `confidence = 'low'` wenn `sample_size < 5`
**Priority**: Medium
**Category**: Detailansicht / Edge Case
**Preconditions**:
- System enthält eine Pflanze, aber weniger als 5 vergleichbare historische Grows

**Test Steps**:
1. Nutzer betrachtet das Yield-Forecast-Widget für diese Pflanze

**Expected Results**:
- Prognose zeigt einen Schätzwert (oder "--" wenn keine Daten)
- Konfidenz-Label lautet "Niedrig" (oder "low")
- Hinweis auf geringe Datenbasis ist sichtbar (z. B. "Basierend auf weniger als 5 Grows — Schätzung ungenau")

**Postconditions**: Niedrige Konfidenz ist deutlich kommuniziert

**Tags**: [req-009, yield-forecast, confidence, low-confidence, edge-case]

---

### TC-009-027: Yield Forecast — Keine historischen Daten verfügbar

**Requirement**: REQ-009 §3 — YieldForecast: Rückgabe leeres Dict wenn keine Daten
**Priority**: Medium
**Category**: Leer-Zustand
**Preconditions**:
- Keine historischen Yield-Daten für die aktuelle Pflanze und Art

**Test Steps**:
1. Nutzer betrachtet das Yield-Forecast-Widget

**Expected Results**:
- Widget zeigt Meldung "Keine historischen Daten für Prognose verfügbar"
- Kein Absturz oder unbeschriftete leere Fläche

**Postconditions**: Widget rendert stabil ohne historische Daten

**Tags**: [req-009, yield-forecast, empty-state, no-data]

---

## Abschnitt H — Klimadaten und Klimastatus

### TC-009-028: Klima-Zusammenfassung — Grüner Status bei optimalen Werten

**Requirement**: REQ-009 §1 — Climate Summary: VPD, Temp, RLF — aktuell vs. Soll; AQL-Logik: status = 'ok' wenn Temp 18–28°C und RH 40–70%
**Priority**: High
**Category**: Detailansicht / Happy Path
**Preconditions**:
- Nutzer ist auf `/dashboard`
- Aktuelle Sensorwerte: Temperatur 22 °C, Luftfeuchte 55 % (optimal)

**Test Steps**:
1. Nutzer öffnet `/dashboard` und betrachtet die Klima-Zusammenfassung

**Expected Results**:
- Temperaturanzeige zeigt "22,0 °C"
- Luftfeuchteanzeige zeigt "55 %"
- VPD-Wert ist berechnet und sichtbar
- Klimastatus-Indikator ist grün oder zeigt "OK"/"Optimal"
- Kein Warnbanner für das Klima

**Postconditions**: Klimabereich zeigt optimale Werte grün an

**Tags**: [req-009, climate, temperature, humidity, vpd, optimal]

---

### TC-009-029: Klima-Zusammenfassung — Gelber Status bei Grenzwert-Überschreitung

**Requirement**: REQ-009 §2 — AQL: `status = 'warning'` wenn `temp < 18 OR temp > 28 OR rh < 40 OR rh > 70`
**Priority**: High
**Category**: Zustandswechsel / Fehlermeldung
**Preconditions**:
- Aktuelle Sensorwerte: Temperatur 30 °C (über Maximum) oder Luftfeuchte 35 % (unter Minimum)

**Test Steps**:
1. Nutzer öffnet `/dashboard` und betrachtet die Klima-Zusammenfassung

**Expected Results**:
- Klimastatus-Indikator zeigt gelbe oder orange Farbe ("Achtung"/"Warning")
- Auffällige Messgrösse (Temperatur oder Luftfeuchte) ist farblich hervorgehoben
- Optional: ein erläuternder Hinweistext erscheint

**Postconditions**: Klima-Warnung ist für den Nutzer sichtbar

**Tags**: [req-009, climate, warning, threshold, state-change]

---

### TC-009-030: Klima-Zusammenfassung — Keine Sensordaten (Leer-Zustand)

**Requirement**: REQ-009 §2 — AQL: `current_temp = null` wenn keine Messungen der letzten 15 Minuten
**Priority**: Medium
**Category**: Leer-Zustand
**Preconditions**:
- Keine Sensordaten der letzten 15 Minuten

**Test Steps**:
1. Nutzer betrachtet die Klima-Zusammenfassung

**Expected Results**:
- Fehlende Werte werden als "--" oder "Keine Daten" dargestellt
- Kein Absturz durch null-Wert
- Klima-Status zeigt ggf. "Unbekannt" anstatt eines Zahlenwerts

**Postconditions**: Klima-Widget ist stabil ohne Sensor-Daten

**Tags**: [req-009, climate, empty-state, sensor, null-safety]

---

## Abschnitt I — Responsive Layout und Darstellung

### TC-009-031: Desktop-Layout — Mehrspaltige Widget-Anordnung (>1200 px)

**Requirement**: REQ-009 §1 — Responsiveness: Desktop (>1200px): 3–4 Spalten, alle Widgets sichtbar
**Priority**: High
**Category**: Happy Path / Responsiveness
**Preconditions**:
- Nutzer öffnet `/dashboard` in einem Desktop-Browser mit Viewport-Breite > 1200 px

**Test Steps**:
1. Nutzer öffnet `/dashboard` auf einem Desktop-Bildschirm (Breite > 1200 px)
2. Nutzer betrachtet die Widget-Anordnung

**Expected Results**:
- Widgets sind in 3 oder 4 Spalten angeordnet
- Alle konfigurierten Widgets sind ohne horizontales Scrollen sichtbar
- Kein unerwünschter Zeilenumbruch bei breiten Viewports

**Postconditions**: Desktop-Layout ist korrekt mehrspaltig

**Tags**: [req-009, responsive, desktop, layout]

---

### TC-009-032: Tablet-Layout — Zweispaltige Anordnung (768–1200 px)

**Requirement**: REQ-009 §1 — Responsiveness: Tablet (768–1200px): 2 Spalten, scrollbar
**Priority**: High
**Category**: Responsiveness
**Preconditions**:
- Viewport-Breite zwischen 768 px und 1200 px (Tablet-Format)

**Test Steps**:
1. Nutzer öffnet `/dashboard` mit Tablet-Viewport (z. B. Breite 900 px)
2. Nutzer betrachtet die Widget-Anordnung

**Expected Results**:
- Widgets sind in 2 Spalten angeordnet
- Vertikales Scrollen ermöglicht den Zugriff auf alle Widgets
- Kein Überlappen oder Abschneiden von Widget-Inhalten

**Postconditions**: Tablet-Layout ist korrekt zweispaltig und scrollbar

**Tags**: [req-009, responsive, tablet, layout]

---

### TC-009-033: Mobile-Layout — Einspaltige Stacked-Anordnung (<768 px)

**Requirement**: REQ-009 §1 — Responsiveness: Mobile (<768px): 1 Spalte; §6 Szenario 6
**Priority**: High
**Category**: Responsiveness / Mobile
**Preconditions**:
- Viewport-Breite unter 768 px (Smartphone-Format, z. B. 375 px)

**Test Steps**:
1. Nutzer öffnet `/dashboard` auf einem Smartphone (Viewport-Breite 375 px)
2. Nutzer scrollt durch die Seite

**Expected Results**:
- Alle Widgets sind in einer einzigen Spalte (full-width) gestapelt
- Kein horizontales Scrollen notwendig
- Buttons und interaktive Elemente sind touch-freundlich (ausreichende Grösse)
- Alle Widget-Inhalte sind lesbar ohne Zoom

**Postconditions**: Mobile-Layout ist einspaltig und touch-optimiert

**Tags**: [req-009, responsive, mobile, layout, touch]

---

## Abschnitt J — Dark Mode

### TC-009-034: Dark Mode — Dashboard im Dark Theme

**Requirement**: REQ-009 §6 DoD — Dark-Mode: Automatisch basierend auf System-Preference
**Priority**: Medium
**Category**: Happy Path
**Preconditions**:
- Nutzer hat Dark Mode aktiviert (System-Preference oder App-Toggle)
- Nutzer ist auf `/dashboard`

**Test Steps**:
1. Nutzer öffnet `/dashboard` mit aktiviertem Dark Mode

**Expected Results**:
- Dashboard-Hintergrund ist dunkel (dunkle Farbe, kein weisser Hintergrund)
- Widget-Karten haben dunkles Erscheinungsbild
- Texte und Icons sind in heller Farbe (gute Lesbarkeit auf dunklem Hintergrund)
- Farbkodierungen (grün/gelb/orange/rot) bleiben semantisch korrekt und erkennbar
- Kein weisser Blitz oder ungewünschter Farbübergang beim Laden

**Postconditions**: Dashboard ist vollständig im Dark Mode dargestellt

**Tags**: [req-009, dark-mode, theme, accessibility]

---

### TC-009-035: Dark Mode — Wechsel zwischen Light und Dark Mode

**Requirement**: REQ-009 §6 DoD — Dark-Mode
**Priority**: Low
**Category**: Zustandswechsel
**Preconditions**:
- Nutzer ist auf `/dashboard`
- App bietet Theme-Toggle (Light/Dark) in den Account-Einstellungen oder Header

**Test Steps**:
1. Nutzer aktiviert den Dark-Mode-Toggle
2. Nutzer deaktiviert den Dark-Mode-Toggle (wechselt zurück zu Light)

**Expected Results**:
- Nach Aktivierung: Dashboard wechselt sofort zu dunklem Theme ohne Seitenneuladen
- Nach Deaktivierung: Dashboard wechselt sofort zu hellem Theme
- Widget-Inhalte (Zahlen, Icons, Graphen) bleiben beim Theme-Wechsel konsistent
- Keine Datenverluste oder Seiten-Neuladen beim Theme-Wechsel

**Postconditions**: Theme-Wechsel funktioniert ohne Datenverlust

**Tags**: [req-009, dark-mode, theme, toggle, state-change]

---

## Abschnitt K — Authentifizierung und Zugriffsschutz

### TC-009-036: Dashboard-Daten sind Tenant-scoped

**Requirement**: REQ-009 §4 — Authentifizierung & Autorisierung: Dashboard-Daten (Tenant-scoped)
**Priority**: High
**Category**: Auth / Security
**Preconditions**:
- Nutzer A und Nutzer B sind Mitglieder verschiedener Tenants
- Nutzer A hat eigene Pflanzen, Nutzer B hat andere Pflanzen

**Test Steps**:
1. Nutzer A loggt sich ein und öffnet `/dashboard`
2. Nutzer A notiert die angezeigten Pflanzen und Metriken
3. Nutzer A loggt sich aus
4. Nutzer B loggt sich ein und öffnet `/dashboard`

**Expected Results**:
- Nutzer B sieht ausschliesslich die Daten seines eigenen Tenants
- Pflanzen, Alerts und Metriken von Nutzer A sind NICHT in Nutzer Bs Dashboard sichtbar
- Keine Cross-Tenant-Datenlecks in der UI

**Postconditions**: Dashboard-Daten sind korrekt tenant-isoliert

**Tags**: [req-009, dashboard, tenant, auth, security, isolation]

---

### TC-009-037: Viewer-Rolle kann Dashboard sehen, aber keine Konfiguration ändern

**Requirement**: REQ-009 §4 — Zugriffsmatrix: Lesen = Mitglied, Schreiben = Mitglied, Löschen = Mitglied
**Priority**: Medium
**Category**: Auth
**Preconditions**:
- Nutzer hat Viewer-Rolle im Tenant (read-only)

**Test Steps**:
1. Nutzer mit Viewer-Rolle öffnet `/dashboard`
2. Nutzer versucht, Widget-Einstellungen zu ändern oder ein Widget zu verschieben (falls Drag&Drop vorhanden)

**Expected Results**:
- Dashboard-Daten sind für Viewer sichtbar
- Widget-Konfigurations-Buttons sind deaktiviert oder nicht vorhanden
- Eine lesbare Fehlermeldung erscheint, falls eine verbotene Aktion versucht wird

**Postconditions**: Viewer kann Dashboard lesen, aber nicht konfigurieren

**Tags**: [req-009, dashboard, auth, viewer-role, rbac]

---

## Abschnitt L — Dashboard-Konfiguration und Widget-Verwaltung

### TC-009-038: Neues Dashboard erstellen (benutzerdefinierter Name)

**Requirement**: REQ-009 §3 — DashboardConfig.name: `min_length=1, max_length=100`
**Priority**: Medium
**Category**: Happy Path / Formvalidierung
**Preconditions**:
- Nutzer ist auf `/dashboard`
- UI bietet eine "Neues Dashboard erstellen"-Funktion

**Test Steps**:
1. Nutzer öffnet das Formular zum Erstellen eines neuen Dashboards
2. Nutzer gibt den Namen "Mein Klima-Dashboard" ein
3. Nutzer wählt Typ "Klima" (dashboard_type: `climate`)
4. Nutzer klickt "Erstellen"

**Expected Results**:
- Neues Dashboard wird angelegt
- Nutzer wird zum neuen Dashboard weitergeleitet oder es erscheint in der Dashboard-Auswahl
- Dashboardname "Mein Klima-Dashboard" ist sichtbar
- Erfolgsbenachrichtigung (Snackbar) bestätigt die Erstellung

**Postconditions**: Neues Dashboard ist erstellt und sichtbar

**Tags**: [req-009, dashboard, create, configuration]

---

### TC-009-039: Dashboard-Name-Validierung — Leerer Name wird abgelehnt

**Requirement**: REQ-009 §3 — DashboardConfig.name: `min_length=1`
**Priority**: Medium
**Category**: Formvalidierung / Fehlermeldung
**Preconditions**:
- Nutzer öffnet das Dashboard-Erstellungsformular

**Test Steps**:
1. Nutzer lässt das Feld "Name" leer
2. Nutzer klickt "Erstellen"

**Expected Results**:
- Formular wird NICHT abgeschickt
- Validierungsfehler erscheint am Namensfeld (z. B. "Name ist erforderlich")
- Dashboard wird NICHT erstellt

**Postconditions**: Leerer Dashboard-Name wird klient-seitig abgefangen

**Tags**: [req-009, dashboard, form-validation, name, required]

---

### TC-009-040: Dashboard-Name-Validierung — Name mit 100 Zeichen (Grenzwert)

**Requirement**: REQ-009 §3 — DashboardConfig.name: `max_length=100`
**Priority**: Low
**Category**: Formvalidierung / Grenzwert
**Preconditions**:
- Nutzer öffnet das Dashboard-Erstellungsformular

**Test Steps**:
1. Nutzer gibt einen Namen mit genau 100 Zeichen ein
2. Nutzer klickt "Erstellen"
3. Nutzer versucht einen Namen mit 101 Zeichen einzugeben

**Expected Results**:
- 100-Zeichen-Name wird akzeptiert und Dashboard erstellt
- Das Eingabefeld lässt keinen Namen mit 101 Zeichen zu (HTML maxlength oder clientseitige Validierung verhindert es) ODER eine Fehlermeldung erscheint beim Absenden

**Postconditions**: Namens-Grenzwert bei 100 Zeichen wird korrekt behandelt

**Tags**: [req-009, dashboard, form-validation, name, max-length, boundary]

---

### TC-009-041: Widget-Refresh-Intervall — Konfigurierbar zwischen 5 und 3600 Sekunden

**Requirement**: REQ-009 §3 — WidgetConfig.refresh_interval_seconds: `Field(default=30, ge=5, le=3600)`
**Priority**: Low
**Category**: Formvalidierung / Grenzwert
**Preconditions**:
- Nutzer hat Zugriff auf Widget-Einstellungen

**Test Steps**:
1. Nutzer öffnet die Einstellungen eines Widgets
2. Nutzer setzt das Refresh-Intervall auf "4" Sekunden (unter Minimum)
3. Nutzer klickt "Speichern"
4. Nutzer setzt das Intervall auf "3601" Sekunden (über Maximum)
5. Nutzer klickt "Speichern"
6. Nutzer setzt das Intervall auf "60" Sekunden (gültiger Wert)
7. Nutzer klickt "Speichern"

**Expected Results**:
- Wert "4" wird abgelehnt: Fehlermeldung "Minimum 5 Sekunden" oder ähnlich
- Wert "3601" wird abgelehnt: Fehlermeldung "Maximum 3600 Sekunden" oder ähnlich
- Wert "60" wird akzeptiert und gespeichert; Widget aktualisiert sich fortan alle 60 Sekunden

**Postconditions**: Refresh-Intervall-Grenzen werden korrekt validiert

**Tags**: [req-009, widget, configuration, refresh-interval, boundary, form-validation]

---

## Abschnitt M — WebSocket Live-Updates (sichtbares Verhalten)

### TC-009-042: WebSocket Live-Update — VPD-Wert aktualisiert sich ohne Seitenneuladen

**Requirement**: REQ-009 §1 — Real-Time: WebSocket-Updates ohne Page-Refresh; §6 Szenario 2
**Priority**: High
**Category**: Zustandswechsel / Happy Path
**Preconditions**:
- Nutzer ist auf `/dashboard` mit aktivem VPD-Widget
- Ausgangszustand: Temperatur 24 °C, Luftfeuchte 55 % → VPD ≈ 1,18 kPa (grün)
- Ein Sensor-Update erhöht die Temperatur auf 26 °C → neuer VPD ≈ 1,40 kPa

**Test Steps**:
1. Nutzer öffnet `/dashboard` und beobachtet das VPD-Widget
2. Nutzer wartet bis zu 10 Sekunden ohne die Seite neu zu laden

**Expected Results**:
- Der VPD-Wert im Widget aktualisiert sich automatisch auf den neuen Wert (ca. 1,40 kPa)
- Die Statusfarbe wechselt von grün zu gelb (da ausserhalb des Optimalbereichs)
- Die Empfehlung aktualisiert sich (z. B. "Luftfeuchte erhöhen auf ca. 60 %")
- Kein Seitenneuladen hat stattgefunden (URL und Scroll-Position bleiben erhalten)
- Das Update erscheint innerhalb von 10 Sekunden nach dem Sensor-Ereignis

**Postconditions**: VPD-Widget hat sich live ohne Seitenneuladen aktualisiert

**Tags**: [req-009, websocket, live-update, vpd, real-time, state-change]

---

## Abschnitt N — Ladezeit und Performance (beobachtbar)

### TC-009-043: Dashboard-Ladezeit — Sichtbarer Inhalt innerhalb von 1 Sekunde

**Requirement**: REQ-009 §6 DoD — Sub-Second Ladezeit: Initial Load < 1 s; alle Widgets rendern innerhalb 1 s
**Priority**: High
**Category**: Happy Path / Performance
**Preconditions**:
- Nutzer ist authentifiziert
- Normales Netzwerk (kein gedrosseltes 3G)
- Dashboard enthält bis zu 8 Widgets mit realen Daten

**Test Steps**:
1. Nutzer navigiert zu `/dashboard`
2. Nutzer beobachtet, wann der erste sichtbare Inhalt erscheint

**Expected Results**:
- Erste sichtbare Inhalte (Seitentitel, Schnellaktionskacheln) erscheinen innerhalb von 1 Sekunde
- Widgets zeigen spätestens nach 1 Sekunde Daten oder Lade-Indikatoren (Spinner/Skeleton)
- Keine leere weisse Seite für mehr als 1 Sekunde

**Postconditions**: Dashboard-Seite hat akzeptable Ladezeit

**Tags**: [req-009, performance, load-time, initial-render]

---

## Abdeckungsübersicht

| Spec-Abschnitt | Bereich | Testfälle |
|---|---|---|
| §1 Overview Dashboard | Einstieg, Navigation, Quick Stats, Schnellaktionen | TC-009-001, TC-009-002, TC-009-003, TC-009-005, TC-009-006 |
| §1 Plant Grid (Kanban-Style) | Farbkodierung, Sortierung, Icons, Navigation | TC-009-009, TC-009-010, TC-009-011, TC-009-012 |
| §1 Task Queue | Anzeige, Sortierung, Leer-Zustand | TC-009-007, TC-009-008 |
| §1 Alert Center | Critical/Warning, Acknowledge, Actionable, Leer | TC-009-018, TC-009-019, TC-009-020, TC-009-021 |
| §1 VPD Calculator | Optimal/Low/High, Manuell, Kein Sensor | TC-009-013, TC-009-014, TC-009-015, TC-009-016, TC-009-017 |
| §1 Harvest Calendar | 4-Wochen-Gruppen, Verfeinerung, Leer | TC-009-022, TC-009-023, TC-009-024 |
| §1 Yield Forecasting | Hoch/Niedrig/Keine Konfidenz | TC-009-025, TC-009-026, TC-009-027 |
| §1 Climate Dashboard | Optimal, Warning, Leer-Zustand | TC-009-028, TC-009-029, TC-009-030 |
| §1 Responsiveness | Desktop, Tablet, Mobile | TC-009-031, TC-009-032, TC-009-033 |
| §1 Dark Mode | Darstellung, Wechsel | TC-009-034, TC-009-035 |
| §1 WebSocket Real-Time | Live-Update sichtbar | TC-009-042 |
| §3 Widget-Konfiguration | Refresh-Intervall-Grenzen | TC-009-041 |
| §3 Dashboard-Konfiguration | Erstellen, Namensvalidierung, Grenzwert | TC-009-038, TC-009-039, TC-009-040 |
| §4 Auth & Autorisierung | Unauthentifiziert, Tenant-Isolation, Viewer-Rolle | TC-009-004, TC-009-036, TC-009-037 |
| §6 DoD Performance | Ladezeit <1s | TC-009-043 |

### Nicht abgedeckte Bereiche (Scope-Einschränkung)

Die folgenden Bereiche aus §6 DoD sind in der aktuellen Spec-Version als Future-Features beschrieben
und sind zum Zeitpunkt der Testfall-Erstellung nicht implementiert:

- PDF-Export (Dashboard als Report)
- PWA Offline-Modus mit Sync
- Keyboard Shortcuts
- Color-Blind-Mode (Accessibility)
- Drag & Drop Widget-Neuanordnung (vollständig)
- Yield Forecasting: ML-basierte Empfehlungen
- Multi-Dashboard-Auswahl (Custom Dashboards Liste)

Diese Bereiche erfordern eigene Testfälle sobald die Implementierung vorliegt.
