# Tabellen-Analyse: Darstellung, Filter, Sortierung, Paginierung, Bulk-Aktionen und Export
**Erstellt von:** Frontend-Design-Reviewer (Subagent)
**Datum:** 2026-03-18
**Analysierte Dokumente:**
- `spec/req/` — REQ-001 bis REQ-028 (alle vorliegenden)
- `spec/nfr/NFR-010_UI-Pflegemasken-Listenansichten.md`
- `spec/ui-nfr/UI-NFR-010_Tabellen-Datenansichten.md`
- `spec/ui-nfr/UI-NFR-001_Responsive-Design.md`
- `src/frontend/src/components/common/DataTable.tsx`
- Alle `*ListPage.tsx`-Dateien in `src/frontend/src/pages/`

---

## Zusammenfassung

Die Spezifikationslage zu Tabellen ist zweigeteilt: UI-NFR-010 und NFR-010 definieren gemeinsam ein solides, gut durchdachtes Verhaltensmuster fuer alle Listenansichten. Die DataTable-Komponente setzt grosse Teile davon bereits um. Gleichzeitig enthalten die fachlichen Anforderungsdokumente (REQ-001 bis REQ-028) fast keine konkreten Angaben zu Tabellendarstellung, Filtern oder Spalten — die Specs schweigen dazu weitgehend. Besonders bei domainspezifischen Filtern (Status, Phase, Zeitraum), Bulk-Aktionen und Export-Funktionalitaet klafft eine erhebliche Luecke zwischen implizitem Bedarf und expliziter Spezifikation.

---

## 1. Tabellen-Darstellungen

### 1.1 Explizit geforderte Tabellenansichten

| Entitaet | Quelle | Art der Anforderung |
|----------|--------|---------------------|
| BotanicalFamily, Species, Cultivar | NFR-010 §4.2, REQ-001 | Listenansicht mit DataTable explizit vorgeschrieben |
| Site, Location, Slot, Substrate, Batch | NFR-010 §4.2, REQ-002 | Listenansicht mit DataTable explizit vorgeschrieben |
| PlantInstance, GrowthPhase | NFR-010 §4.2, REQ-003 | Listenansicht mit DataTable explizit vorgeschrieben |
| PlantingRun | NFR-010 §4.3, REQ-013 | Listenansicht gefordert (noch nicht implementiert) |
| Tank, TankFillEvent | NFR-010 §4.3, REQ-014 | Listenansicht gefordert |
| NutrientPlan, FertilizerProduct, FeedingEvent | NFR-010 §4.3, REQ-004 | Listenansicht gefordert |
| Task / Aufgabenliste | REQ-006, NFR-010 §4.3 | Listendarstellung gefordert; implizit auch Board/Kanban |
| WorkflowTemplate | REQ-006, NFR-010 | Listenansicht gefordert |
| HarvestBatch | REQ-007, NFR-010 §4.3 | Listenansicht mit Batch-Tracking |
| DryingBatch, CuringBatch | REQ-008, NFR-010 §4.3 | Listenansicht gefordert (nicht implementiert) |
| Pest, Disease, Treatment | REQ-010, NFR-010 §4.3 | Listenansicht gefordert |
| ImportJob (CSV-Vorschautabelle) | REQ-012 | Zeilenweise Vorschau mit Validierungsstatus pro Zeile — spezifische Tabellenform |
| SensorReading | REQ-005, NFR-010 §4.3 | Zeitreihen-Anzeige (Charts + Tabelle) |
| WateringEvent, WateringLog | REQ-014 | Befuellungshistorie als tabellarische Liste |
| CareReminder / PflegeDashboard | REQ-022 | Karten-Gruppierung nach Dringlichkeit (kein klassisches Tabellenlayout) |
| Membership / Tenant-Mitglieder | REQ-024 | Mitgliederliste mit Rollenzuweisung |
| ImportLog | REQ-012 | Ergebnis-Statistiken als Liste |
| ActivityLog | REQ-023 | Audit-Trail-Tabelle (Token-Aktivitaet, Login-Versuche) |

### 1.2 Implizit geforderte Tabellenansichten (nicht explizit spezifiziert)

Die folgenden Tabellen sind aus dem fachlichen Kontext zwingend erforderlich, ohne in den Specs als Tabellenansicht bezeichnet zu werden:

| Entitaet | Impliziert durch | Fehlt in Spec |
|----------|-----------------|---------------|
| Fruchtfolge-Matrix (Beet x Jahr) | REQ-002 ("Tabellarische Uebersicht pro Beet x Jahr mit Farbcode") | Tabellenformat genannt, Spalten/Zeilen nicht spezifiziert |
| Karenz-Uebersicht (aktive Sperrzeiten) | REQ-007, REQ-010 | Keine UI-Spezifikation vorhanden |
| Widerstandsmanagement (Wirkstoff-Rotation) | REQ-010 (ResistanceManager) | Keine Tabellenspezifikation |
| Sensor-Rohdaten-Tabelle | REQ-005, REQ-009 | Charts spezifiziert, Rohdaten-Tabelle fehlt |
| Service-Account-Liste | REQ-023 v1.7 | Neue Entitaet ohne Tabellenspezifikation |
| Duty-Rotation-Plan | REQ-024 v1.2 | Rotations-Kalender/Tabelle nicht spezifiziert |
| Einladungsliste (offene Einladungen) | REQ-024 | Nicht spezifiziert |
| Yield-Analytics-Tabelle | REQ-009 Dashboard | Nur als Widget erwaehnt, kein Tabellenlayout |
| Stecklingshistorie (Mutterpflanze) | REQ-017 | Nicht spezifiziert |
| OverwinteringProfile-Liste | REQ-022 | Nicht spezifiziert |

---

## 2. Filter-Funktionalitaet

### 2.1 Explizit spezifizierte Filter

**In UI-NFR-010 definierte allgemeine Filterregeln:**

| Regel | Anforderung | Stufe |
|-------|------------|-------|
| R-006 | Globales Suchfeld ueber alle sichtbaren Spalten | MUSS |
| R-007 | Suche mit Debouncing >= 300ms | MUSS |
| R-008 | Spaltenspezifische Filter (z.B. Status-Dropdown) | KANN |
| R-009 | Aktive Filter visuell als Chip mit Loesch-Button | MUSS |
| R-010 | "Alle Filter zuruecksetzen"-Button bei aktiven Filtern | MUSS |

**In NFR-010 §3.3a definierte Suchfeldregel:**

Die Volltextsuche durchsucht alle textuellen Spalten; Suchbegriff wird als URL-Parameter `?search=...` abgebildet; Ergebnisanzahl bei aktiver Suche anzeigen ("3 von 42 Ergebnissen"); X-Icon zum Loeschen.

**Domainspezifische Filter, die REQ-Dokumente implizieren:**

| Filter | Quelle | Beschreibung |
|--------|--------|-------------|
| Phase (vegetativ, bluehand, etc.) | REQ-003, REQ-009 | Pflanzinstanzen nach Wachstumsphase filtern — hochfrequente Aktion |
| Status (pending, completed, etc.) | REQ-006 | Aufgaben nach Status filtern — "Meine Aufgaben" vs. "Alle" |
| Zugewiesener Nutzer | REQ-006 | Filter "assigned_to_user_key" explizit erwaehnt: "Filter: Meine Aufgaben vs. Alle Aufgaben" |
| Zeitraum (Datum von/bis) | REQ-007, REQ-014, REQ-005 | Ernte-/Befuellungs-/Sensorereignisse im Zeitraum |
| Standort / Site | REQ-002, REQ-013 | Pflanzen/Runs nach Standort filtern |
| Befallsdruck (none/low/.../critical) | REQ-010 | IPM-Inspektionen nach pressure_level |
| Import-Status (valid/invalid/duplicate) | REQ-012 | CSV-Vorschautabelle: zeilenweiser Validierungsstatus als Filter |
| Substrattyp | REQ-019 | Substrat-Listenansicht nach type filtern |
| Behandlungstyp (cultural/biological/chemical) | REQ-010 | Behandlungen nach Kategorie |
| Karenz-Status (aktiv/abgelaufen) | REQ-007, REQ-010 | Karenzzeiten-Uebersicht |
| Dormant / Pending / Completed | REQ-006 | Aufgaben nach Workflow-Phase und Status |
| Tenant-Rolle (admin/grower/viewer) | REQ-024 | Mitgliederverwaltung |

**Kritische Feststellung:** Kein einziges REQ-Dokument spezifiziert explizit, *welche* spaltenspezifischen Filter fuer *welche* Entitaet bereitgestellt werden sollen. Die allgemeine Filterregel in UI-NFR-010 (R-008: KANN) laesst dies als optionale Erweiterung offen, ohne den konkreten Bedarf pro Entitaet zu benennen.

### 2.2 Freitext-Suche — aktueller Implementierungsstand

Die DataTable-Komponente implementiert Volltextsuche client-seitig ueber alle als `searchable` markierten Spalten mit 300ms Debouncing. URL-Persistenz ist ueber `useTableUrlState` umgesetzt. Die Suche erfolgt derzeit **ausschliesslich client-seitig** — bei grossen Datenststaenden (>1.000 Eintraege) kein Problem, da die gesamte Liste vom Redux-Store gehalten wird. Serverseitige Suche ist als API-Parameter `search` in NFR-010 §3.3a spezifiziert, aber noch nicht flaechendeckend implementiert.

---

## 3. Sortierung

### 3.1 Spezifizierte Sortierregeln (UI-NFR-010 §2.1)

| Regel | Anforderung | Implementiert? |
|-------|------------|---------------|
| R-001 | Jede Datenspalte per Klick auf Header sortierbar | Ja — ueber `col.sortable !== false` |
| R-002 | Sortierrichtung visuell anzeigen (Pfeil) | Ja — MUI TableSortLabel |
| R-003 | Erneuter Klick kehrt Richtung um | Ja |
| R-004 | Standard-Sortierung kontextuell sinnvoll | Ja — `defaultSort` per Seite konfigurierbar |
| R-005 | cursor: pointer und Hover-Effekt | Ja — MUI TableSortLabel Standard |

**Aus NFR-010 §3.3:**
- Standard-Sortierung: Name aufsteigend (oder Erstellungsdatum absteigend, falls kein Name-Feld)
- Sortierung erfolgt server-seitig (API-Parameter `sort_by`, `sort_order`) — **aber:** aktuelle Implementierung ist client-seitig

### 3.2 Fehlende Sortier-Spezifikation

Kein REQ-Dokument benennt, **welche Spalten** fuer welche Entitaet besonders relevant fuer die Sortierung sind. Aus fachlicher Sicht kritisch fehlende Sortieroptionen:

| Entitaet | Fachlich relevante Sortierkriterien | Spec-Referenz |
|----------|-------------------------------------|---------------|
| PlantInstance | Phase, Pflanzdatum, Frist bis Ernte | REQ-003, REQ-009 |
| Task | Faelligkeit (due_date), Prioritaet, Status | REQ-006 |
| HarvestBatch | Erntedatum, Qualitaet (Grade), Gewicht | REQ-007 |
| FeedingEvent | Datum, EC-Ist-Wert | REQ-004 |
| TankFillEvent | Befuellungsdatum, Typ (full_change/top_up) | REQ-014 |
| IPM-Inspection | Datum, Befallsdruck | REQ-010 |
| ImportJob | Status, Datum, Fehleranzahl | REQ-012 |

---

## 4. Paginierung

### 4.1 Spezifizierte Paginierungsregeln (UI-NFR-010 §2.3 und NFR-010 §3.2)

| Regel | Anforderung | Stufe | Implementiert? |
|-------|------------|-------|---------------|
| R-011 | Paginierung bei >50 Eintraegen | MUSS | Ja |
| R-012 | Eintraege pro Seite einstellbar: 10, 25, 50, 100 | MUSS | Ja |
| R-013 | Anzeige "Zeigt 1-50 von 234 Eintraegen" | MUSS | Ja |
| R-014 | Gewahlte Seitengroesse in localStorage persistieren | SOLL | Nein — fehlt |
| R-015 | Filter-/Sortierwechsel setzt Pagination auf Seite 1 zurueck | MUSS | Ja — via useTableState |
| NFR-010 §3.2 | Standard: 50 Eintraege pro Seite | MUSS | Ja (Default in DataTable) |

**Fehlend (R-014):** Die Seitengroesse wird aktuell nicht in localStorage persistiert. Bei jedem Seitenaufruf wird der Default von 50 verwendet. Fuer Nutzer, die regelmaessig mit 100 Eintraegen arbeiten, ist das eine Reibungsquelle.

### 4.2 Server-seitige vs. Client-seitige Paginierung

NFR-010 §3.2 fordert "server-seitige Pagination mit konfigurierbaren Seitengroessen". Die aktuelle Implementierung in DataTable unterstuetzt **beide Modi**:

1. **Client-seitig (via `tableState`):** Alle Daten werden geladen, Paginierung/Suche/Sortierung erfolgt client-seitig. Dieser Modus wird von allen aktuellen ListPages verwendet (z.B. PlantInstanceListPage, HarvestBatchListPage).

2. **Server-seitig (Legacy-Props):** `total`, `onPageChange`, `onRowsPerPageChange` ermoglichen Server-Paginierung. Dieser Modus ist implementiert, wird aber von keiner aktuellen ListPage genutzt.

**Bewertung:** Fuer die aktuellen Datenmengen (Hunderte bis wenige Tausend Eintraege) ist client-seitige Paginierung ausreichend. Bei REQ-005 (Sensordaten — potenziell Millionen von Rohdaten-Zeilen) oder REQ-023 (Audit-Trail-Tabellen) wird echter Server-Paginierung notwendig.

---

## 5. Spalten-Konfiguration

### 5.1 Was die Specs dazu sagen

Weder UI-NFR-010 noch NFR-010 noch irgendein REQ-Dokument fordert, dass Nutzer Spalten ein-/ausblenden koennen. Dies ist eine **vollstaendige Spec-Luecke**.

Die DataTable-Komponente bietet `hideBelowBreakpoint` pro Spalte (responsive Ausblendung), aber keine nutzergesteuerte Spalten-Konfiguration.

### 5.2 Aktuell implementierte responsive Spaltensteuerung

Die Spalte `hideBelowBreakpoint` in der Column-Definition blendet Spalten unterhalb bestimmter Breakpoints automatisch aus. Genutzt wird dies in:

- `HarvestBatchListPage.tsx`: `plantKey` und `harvestType` mit `hideBelowBreakpoint: 'md'`

Fuer weitere Listenansichten fehlt diese Breakpoint-Konfiguration ganz oder teilweise — Tabellen werden auf Tablet/Mobile mit unveraendertem Spaltenset dargestellt und koennen dadurch ueberladen wirken.

### 5.3 Bewertung

Nutzergesteuerte Spalten-Konfiguration (Spalten ein-/ausblenden, Reihenfolge aendern) ist ein haeufig genutztes Feature in daten-intensiven Anwendungen, aber fuer diese Anwendungsdomaene (Gaertner, Grower) nicht kritisch. REQ-021 (Erfahrungsstufen) loest einen Teil des Problems bereits durch das Ausblenden komplexer Felder im Einsteiger-Modus. Eine explizite Spalten-Konfiguration pro Nutzer ist ein sinnvolles mittelfristiges Feature, das aber keiner sofortigen Umsetzung bedarf.

---

## 6. Responsive Tabellen

### 6.1 Spezifizierte Responsive-Regeln (UI-NFR-010 §2.5)

| Regel | Anforderung | Stufe | Implementiert? |
|-------|------------|-------|---------------|
| R-019 | Desktop (>1024px): vollstaendige Tabelle mit allen Spalten | MUSS | Ja |
| R-020 | Tablet (<=1024px): weniger wichtige Spalten ausblenden, Prioritaet pro Tabelle definieren | SOLL | Teilweise — nur HarvestBatchListPage nutzt hideBelowBreakpoint |
| R-021 | Mobile (<=768px): Kartenansicht ODER horizontaler Scroll mit Indikator | MUSS | Ja — mobileCardRenderer vorhanden |
| R-022 | Horizontales Scrollen durch visuellen Hinweis erkennbar (Schatten am Rand) | MUSS | Ja — scrollShadow-Logik implementiert |

**Feststellung zu R-020:** Die Mehrheit der ListPages definiert keine `hideBelowBreakpoint`-Konfiguration fuer ihre Spalten. Damit fehlt die systematische Tablet-Optimierung. Die Tabellen werden zwischen Breakpoint 'sm' (Mobile-Card) und dem vollen Desktop-Layout nicht graduell angepasst — es gibt einen harten Schnitt ohne Zwischenstufe.

### 6.2 Mobile-Card-Implementierung

Der `mobileCardRenderer`-Prop ist in den meisten ListPages implementiert:
- `PlantInstanceListPage`: Vollstaendige MobileCard mit Species, Cultivar, Phase, Standort
- `HarvestBatchListPage`: MobileCard mit Datum, Typ, Qualitaet, Gewicht
- `WorkflowTemplateListPage`: MobileCard vorhanden (nicht vollstaendig gelesen, aber Import bestaetigt)
- `WateringEventListPage`: MobileCard vorhanden

**Nicht geprueft / potenziell fehlend:**
- `FeedingEventListPage`, `WateringLogListPage`, `TankListPage`, `SubstrateListPage` — kein vollstaendiger Code-Review durchgefuehrt, aber Muster ist konsistent uebernommen.

### 6.3 Fehlende Tablet-Optimierung — konkrete Luecken

| ListPage | Problem | Empfehlung |
|----------|---------|-----------|
| PlantInstanceListPage | 6 Spalten auf Tablet unveraendert | `removedOn`, `instanceId` auf md ausblenden |
| WorkflowTemplateListPage | Spalten-Set nicht geprueft, wahrscheinlich unveraendert | Kategorie/Beschreibung auf sm ausblenden |
| FertilizerListPage | Vermutlich viele Spalten (EC, NPK-Werte) | Technische Details auf md ausblenden |
| TankListPage | Technische Parameter (Volumen, EC, pH) | Nicht-kritische Parameter auf md ausblenden |
| PestListPage, DiseaseListPage | Taxonomische Details | Wissenschaftlicher Name auf sm ausblenden |

---

## 7. Bulk-Aktionen

### 7.1 Explizit geforderte Bulk-Aktionen (REQ-006)

REQ-006 §"Batch-Operationen" ist das einzige REQ-Dokument mit expliziten Bulk-Aktionen:

```
POST /tasks/batch/status — Mehrere Tasks gleichzeitig starten, abschliessen oder ueberspringen
POST /tasks/batch/delete — Mehrere Tasks gleichzeitig loeschen (nur pending/skipped)
POST /tasks/batch/assign — Mehrere Tasks einem Nutzer zuweisen
```

Diese API-Endpunkte sind laut CLAUDE.md implementiert. Die Frontend-Entsprechung (Checkbox-Selektion + Aktionsleiste) ist in der DataTable-Komponente als KANN-Anforderung (UI-NFR-010 R-025 bis R-028) spezifiziert, aber **in keiner ListPage implementiert**. Die DataTable-Komponente selbst unterstuetzt die Checkbox-Selektion noch nicht — weder die Komponente noch eine der Pages nutzt dieses Feature.

### 7.2 Implizit geforderte Bulk-Aktionen aus anderen REQs

| Entitaet | Bulk-Aktion | Quelle | Frontend-Spec vorhanden? |
|----------|------------|--------|--------------------------|
| PlantInstance | Batch-Phasenuebergang (alle Pflanzen eines Runs auf naechste Phase) | REQ-013 §"Batch-Phasenuebergang" | Nein — kein UI fuer Tabellen-Checkbox-Flow |
| PlantInstance | Batch-Entfernung (Run abschliessen, alle als entfernt markieren) | REQ-013 | Nein |
| HarvestBatch | Batch-Ernte aus PlantingRun | REQ-013 §"Batch-Ernte" | Nein |
| Task | Bulk-Status-Aenderung (start/complete/skip) | REQ-006 | Nein — API vorhanden, UI fehlt |
| Task | Bulk-Loeschen | REQ-006 | Nein |
| Task | Bulk-Zuweisung | REQ-006 | Nein |
| PlantInstance | Import-Bestaetigungs-Selektion (welche Zeilen importieren) | REQ-012 | Teilweise — per "Alle bestaetigen" |

**Bewertung:** Die Batch-API fuer Tasks ist vollstaendig implementiert. Das Frontend nutzt diese Endpoints nicht. Die Spezifikation spricht die UI-Seite nur in UI-NFR-010 R-025 bis R-028 als KANN-Anforderung an — die Umsetzung ist damit technisch optional, fachlich aber dringend fuer die Aufgabenverwaltung (REQ-006) und den PlantingRun-Workflow (REQ-013).

### 7.3 Spezifikation fuer die Bulk-Aktions-Toolbar (UI-NFR-010 §2.7)

| Regel | Anforderung |
|-------|------------|
| R-025 | Checkbox-Spalte zur Mehrfachauswahl — KANN |
| R-026 | "Alle auswaehlen"-Checkbox im Header bei aktiver Mehrfachauswahl — MUSS |
| R-027 | Aktionsleiste mit Anzahl ausgewaehlter Eintraege und Massenaktionen — MUSS (wenn Selektion aktiv) |
| R-028 | Destruktive Massenaktionen benoetigen Bestaedigungsdialog — MUSS |

Die DataTable-Komponente muss um Checkbox-Support erweitert werden.

---

## 8. Export

### 8.1 Was die Specs dazu sagen

**In keinem REQ-Dokument und in keiner NFR/UI-NFR wird ein Daten-Export (CSV, PDF, Excel) explizit gefordert.** Dies ist eine vollstaendige Spec-Luecke.

Einzige Ausnahmen:
- REQ-012 spezifiziert Download-Templates fuer den CSV-Import ("GET /import/templates/species-template.csv") — das ist aber ein Import-Template, kein Daten-Export.
- REQ-006 erwaehnt "Import/Export als JSON" fuer Workflow-Blueprints (User-Blueprints). Das ist Export eines einzelnen Datensatzes, keine Tabellen-Massenexport.

### 8.2 Fachlicher Bedarf (implizit)

Obwohl nicht spezifiziert, besteht fachlicher Bedarf in folgenden Szenarien:

| Szenario | Betroffene Entitaet | Exportformat |
|----------|--------------------|--------------|
| Ernteauswertung fuer Behoerden (CanG-Dokumentation) | HarvestBatch | CSV / PDF |
| IPM-Behandlungsprotokoll mit Karenzzeiten | TreatmentApplication | PDF |
| Aufgabenhistorie fuer Qualitaetssicherung | Task | CSV |
| Seed-to-Shelf-Rückverfolgbarkeit | HarvestBatch + PlantInstance | PDF |
| Duengeprotokoll (EC/pH-Verlauf) | FeedingEvent, TankState | CSV |
| Sensorwerte-Rohdaten | SensorReading (REQ-005) | CSV |

**Prioritaet:** Fuer den Cannabis-Anbauverein-Kontext ist die PDF-Exportmoeglichkeit fuer Ernte- und Behandlungsprotokolle ein potenzielle Compliance-Anforderung (CanG). Ohne explizite Spezifikation kann dies aber nicht als Fehler gewertet werden — es ist ein blinder Fleck der Specs.

---

## 9. Detailanalyse: Was in der DataTable-Komponente fehlt

Die DataTable-Komponente (`src/frontend/src/components/common/DataTable.tsx`) ist gut implementiert und erfuellt die meisten UI-NFR-010-Anforderungen. Folgende Punkte fehlen noch:

| Feature | UI-NFR-010 | Fehlt in Komponente | Prioritaet |
|---------|------------|---------------------|-----------|
| Checkbox-Selektion fuer Bulk-Aktionen | R-025 bis R-028 | Komplett fehlend — kein Checkbox-Prop | Hoch (REQ-006 Batch-API braucht das) |
| Spaltenspezifische Filter (Status-Dropdown, Datums-Picker) | R-008 | Fehlend — nur Volltextsuche | Mittel |
| LocalStorage-Persistenz der Seitengroesse | R-014 | Fehlend | Niedrig |
| ARIA-caption oder aria-label (Tabelle selbst) | R-036 | `ariaLabel`-Prop vorhanden, wird aber nicht als `<caption>` umgesetzt | Niedrig |

---

## 10. CSV-Import-Vorschautabelle (REQ-012) — Sonderfall

REQ-012 beschreibt eine spezifische Tabellenform fuer die Import-Vorschau, die besondere Anforderungen stellt:

```json
"preview_data": [
  {
    "row_number": 1,
    "status": "valid",        // valid | invalid | duplicate
    "data": { ... },
    "errors": [],
    "is_duplicate": false
  }
]
```

**Besondere Tabellenanforderungen fuer die Vorschautabelle:**

| Anforderung | Begruendung | Spec vorhanden? |
|-------------|------------|-----------------|
| Zeilenstatus-Spalte mit Ampel-Icon (valid/invalid/duplicate) | Nutzer muss auf einen Blick sehen, welche Zeilen problematisch sind | Implizit in REQ-012 |
| Filter nach Zeilenstatus (nur Fehler anzeigen) | Bei 150 Zeilen moechte der Nutzer gezielt die 8 fehlerhaften sehen | Nicht spezifiziert |
| Feldspeziifsche Fehler-Hervorhebung in der Zelle | Zeile ist invalid, aber welches Feld? | Nicht spezifiziert |
| Einzelne Zeilen aus dem Import ausschliessen (Checkbox) | "Diese Zeile ueberspringen" — Duplikat-Zeile nicht importieren | Implizit in REQ-012 ("fehlerhafte Zeilen koennen... uebersprungen werden") |
| Gesamtstatistik oberhalb der Tabelle | "142 gueltig, 5 invalid, 3 Duplikate" | In REQ-012 Datenmodell vorhanden (`valid_rows`, `invalid_rows`) |

**Bewertung:** Die Import-Vorschautabelle ist ein Sonderfall, der die normale DataTable-Komponente ergaenzen muss. Sie braucht zusaetzliche Statusspalten, zeilenbasierte Hervorhebungen (rote Hintergrundfarbe fuer invalid) und Checkbox-Selektion fuer "Zeile ueberspringen". Diese Spezifikation ist in REQ-012 nicht vollstaendig ausgearbeitet.

---

## 11. Dashboard-Tabellen und Listen (REQ-009)

REQ-009 beschreibt eine "Task List (Sortierbar)" als Status-Widget und eine "Alert Feed (Real-Time)"-Liste. Diese sind keine klassischen CRUD-Tabellen, sondern Live-Listen mit WebSocket-Updates. Spezifiziert ist:

- Plant Status Grid: Kanban-Style (keine Tabelle)
- Task Queue: "Top 5 faellige/ueberfaellige Tasks" — Mini-Liste, nicht vollstaendige Tabelle
- Alert Center: Real-Time-Feed

Fuer diese Dashboard-Widgets gelten die Tabellenregeln aus UI-NFR-010 nur eingeschraenkt. Es fehlt jedoch eine klare Abgrenzung in den Specs, wann ein Widget eine vollstaendige Tabellenfunktionalitaet (Sortierung, Filter, Pagination) benoetigt und wann es als reines Anzeigewidget fungiert.

---

## 12. Zusammenfassung der Spec-Luecken

### 12.1 Kritische Luecken (blockieren konkrete Implementierung)

| Nr. | Luecke | Betroffene REQs | Auswirkung |
|----|--------|-----------------|-----------|
| L-001 | Domainspezifische Filter (Phase, Status, Zeitraum, Standort) sind fuer keine Entitaet explizit spezifiziert | REQ-003, REQ-006, REQ-007, REQ-010, REQ-014 | Entwickler muessen Filterauswahl ohne Spec-Grundlage treffen — Inkonsistenz wahrscheinlich |
| L-002 | Bulk-Aktionen fuer Tasks sind API-seitig implementiert, aber kein UI-Flow (Checkbox-Selektion) spezifiziert | REQ-006 | Batch-API bleibt ungenutzt |
| L-003 | Tablet-Spaltenprioritaeten sind fuer keine einzelne Listenansicht definiert | UI-NFR-010 R-020 | Tabellen werden auf Tablet unveraendert dargestellt — ueberladen |
| L-004 | CSV-Import-Vorschautabelle: zeilenbasierte Checkbox-Selektion fuer "Zeile ueberspringen" ist nicht spezifiziert | REQ-012 | Die zentrale Interaktion des Import-Workflows ist unklar |

### 12.2 Mittlere Luecken (sollten vor Implementierung geklaert werden)

| Nr. | Luecke | Betroffene REQs | Auswirkung |
|----|--------|-----------------|-----------|
| L-005 | Export-Funktionalitaet (CSV/PDF) fuer Ernte- und Behandlungsprotokolle nicht spezifiziert | REQ-007, REQ-010 | Potenzielle Compliance-Luecke fuer CanG-Anforderungen |
| L-006 | Karenz-Uebersicht als eigene Tabellenansicht nicht spezifiziert | REQ-007, REQ-010 | Nutzer hat keinen Ueberblick ueber aktive Sperrzeiten |
| L-007 | LocalStorage-Persistenz der Seitengroesse fehlt (NFR-010 R-014 SOLL) | UI-NFR-010 | Kleine UX-Reibung bei regelmaessiger Nutzung |
| L-008 | Fruchtfolge-Matrix-Tabelle (Beet x Jahr) — Format erwaehnt, Daten/Spalten nicht spezifiziert | REQ-002 | Visuelle Darstellung unklar |
| L-009 | Server-seitige Suche und Pagination fuer grosse Datenmengen (Sensordaten) nicht ausgearbeitet | REQ-005, NFR-010 §3.3 | Client-seitige Verarbeitung skaliert nicht fuer Millionen Sensor-Rohdaten |

### 12.3 Kleinere Luecken (optionale Qualitaetsverbesserungen)

| Nr. | Luecke | Betroffene REQs |
|----|--------|-----------------|
| L-010 | Nutzergesteuerte Spalten-Konfiguration nicht spezifiziert | UI-NFR-010 |
| L-011 | Zebra-Streifen und Zeilenabstand-Konfiguration (KANN-Anforderungen) nicht per Design-Token definiert | UI-NFR-010 R-039 |
| L-012 | Dashboard-Widget-Tabellen vs. vollstaendige Tabellenansichten: Abgrenzung fehlt | REQ-009 |

---

## 13. Positiv: Gut umgesetzte Aspekte

1. **UI-NFR-010 ist ausfuehrlich und praxisnah** — Die Anforderungsregeln R-001 bis R-040 sind klar, testbar und vollstaendig. Das Wireframe-Beispiel (§3) illustriert das Soll-Verhalten gut.

2. **DataTable-Komponente ist solide** — Volltextsuche mit Debouncing, Client-seitige Sortierung, Scroll-Schatten fuer horizontalen Scroll, Skeleton-Ladezustand, differenzierter Leer-Zustand vs. Keine-Suchergebnisse, Mobile-Card-Modus — all das ist korrekt implementiert.

3. **URL-Persistenz ist implementiert** — `useTableUrlState` bildet Suche, Sortierung und Seite als Query-Parameter ab. Gefilterte Ansichten sind teilbar.

4. **ARIA-Attribute** — `aria-sort` auf sortierten Spaltenheadern und `aria-label` auf der Tabelle sind umgesetzt.

5. **Mobile-Card-Renderer** ist in den wichtigsten ListPages implementiert (PlantInstance, HarvestBatch, WorkflowTemplate) und nutzt die `MobileCard`-Komponente konsequent.

6. **Scroll-Schatten** fuer horizontalen Scroll (UI-NFR-010 R-022) ist elegant mit CSS-Pseudoelementen und einem ResizeObserver umgesetzt.

7. **Sticky Header** (R-023) ist als Default aktiviert (`stickyHeader = true`).

---

## 14. Empfehlungen

### Sofort umsetzbar (Quick Wins)

1. **Tablet-Spaltenprioritaeten definieren:** Fuer die 5 wichtigsten ListPages (PlantInstance, HarvestBatch, WorkflowTemplate, FertilizerList, TaskList) `hideBelowBreakpoint: 'md'` fuer nicht-kritische Spalten ergaenzen. Aufwand: 2-4h pro Seite.

2. **LocalStorage-Persistenz fuer Seitengroesse:** In `useTableState` eine lokale Persistenz der `pageSize`-Einstellung ergaenzen. Aufwand: 1-2h.

3. **Einfache Status-Filter fuer Aufgaben-Liste:** Fuer die Task-Listenansicht einen Status-Filter (pending / in_progress / completed / dormant) als Chip-Gruppe oberhalb der Tabelle ergaenzen — das ist der haeufigste Anwendungsfall und in REQ-006 explizit erwaehnt ("Meine Aufgaben vs. Alle Aufgaben"). Aufwand: 4-6h.

4. **Phase-Filter fuer PlantInstance-Liste:** Einen Chip-Filter fuer die Wachstumsphase ergaenzen. Die Phasen-Chips sind bereits in der Tabelle als MUI Chip dargestellt — als klickbare Filter umsetzen. Aufwand: 3-4h.

### Mittelfristig (Naechste Entwicklungsphase)

1. **Checkbox-Selektion in DataTable ergaenzen:** Die Checkbox-Logik (Einzelauswahl, Alle-auswaehlen, Aktionsleiste) als optionales Feature in DataTable implementieren. Dann fuer die Task-Listenansicht die Bulk-API-Endpoints nutzen. Aufwand: 1-2 Tage Komponente + 1 Tag Integration.

2. **Spaltenspezifischen Filter-Mechanismus spezifizieren:** Einen UI-NFR-Anhang oder ein eigenes Kapitel in UI-NFR-010 erstellen, das fuer jede wichtige Entitaet die relevanten spaltenspezifischen Filter benennt. Dieser Report kann als Ausgangspunkt dienen.

3. **CSV-Import-Vorschautabelle vollstaendig spezifizieren:** REQ-012 um ein detailliertes UI-Konzept fuer die Vorschautabelle ergaenzen — zeilenbasierte Checkbox-Selektion, Fehler-Hervorhebung, Status-Filter.

### Langfristig / Strategisch

1. **Export-Anforderungen klaeren:** Fuer den Cannabis-Social-Club-Kontext pruefe, ob CanG-Compliance einen PDF-Export von Ernte- und Behandlungsprotokollen erfordert. Falls ja, als eigene Anforderung (REQ-029 oder Anhang zu REQ-007) spezifizieren.

2. **Server-seitige Suche und Pagination fuer Sensordaten:** Wenn REQ-005 (Hybrid-Sensorik) implementiert wird, muss die DataTable-Komponente vollstaendig auf server-seitige Pagination umschaltbar sein. Die Legacy-Props existieren bereits, muessen aber in eine vollstaendige Server-State-Strategie eingebettet werden.

3. **Fruchtfolge-Matrix als eigene Visualisierungskomponente:** Die in REQ-002 erwaehnte "tabellarische Uebersicht pro Beet x Jahr mit Farbcode" ist keine klassische DataTable, sondern eine spezielle Heat-Map/Matrix. Eine dedizierte Komponente ist sinnvoller als eine Erweiterung von DataTable.

---

## Glossar (tabellenspezifisch)

- **Client-seitige Pagination:** Alle Daten werden vom Server geladen; Seiten-/Such-/Sortierlogik laeuft im Browser. Einfach zu implementieren, skaliert nicht bei sehr grossen Datenmengen.
- **Server-seitige Pagination:** Browser laedt nur die aktuell angezeigte Seite. Erfordert API-Parameter (`page`, `pageSize`, `sort_by`, `sort_order`, `search`). Notwendig ab ca. 10.000+ Eintraegen.
- **Sticky Header:** Tabellenzeilen-Kopfzeile bleibt beim Scrollen sichtbar. In DataTable als Default aktiviert (`position: sticky`).
- **hideBelowBreakpoint:** DataTable-Column-Option, die eine Spalte unterhalb eines MUI-Breakpoints (`md` oder `lg`) ausblendet. Genutzt fuer responsive Tablet-Optimierung.
- **Bulk-Aktion / Massenaktion:** Operation, die gleichzeitig auf mehrere ausgewaehlte Tabellenzeilen angewendet wird (z.B. "Alle auswaehlten Tasks als erledigt markieren").
- **tableState / useTableUrlState:** React-Hook, der Suchbegriff, Sortierung und aktuelle Seite als URL-Query-Parameter synchronisiert und die Verarbeitungs-Pipeline (Filter, Sortierung, Pagination) client-seitig ausfuehrt.
- **mobileCardRenderer:** Optionale Prop der DataTable, die auf Mobile-Breakpoints statt der Tabellenzeilen eine Card-Darstellung rendert.

---

**Dokumenten-Ende**

**Version:** 1.0
**Status:** Final
**Erstellt:** 2026-03-18
