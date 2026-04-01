# Spezifikation: REQ-032 - Druckansichten & Export

```yaml
ID: REQ-032
Titel: Druckansichten & Export
Kategorie: Ausgabe & Dokumentation
Fokus: Beides
Technologie: Python, FastAPI, React, TypeScript, MUI, WeasyPrint/ReportLab
Status: Entwurf
Version: 1.1 (Pflanzen-Infokarten mit QR-Code)
```

## 1. Business Case

**User Story (Nährstoffplan drucken):** "Als Grower möchte ich meinen aktuellen Nährstoffplan als übersichtliches PDF ausdrucken und im Growraum aufhängen können — damit ich beim Anmischen nicht ständig aufs Handy schauen muss."

**User Story (Pflegeablauf drucken):** "Als Gärtnerin mit 30 Zimmerpflanzen möchte ich eine Pflege-Checkliste für die aktuelle Woche ausdrucken können — damit ich sie abhaken kann, während ich durch die Wohnung gehe."

**User Story (Ernteprotokoll):** "Als Anbauer möchte ich ein Ernteprotokoll mit Qualitätsbewertungen als PDF exportieren können — zur Dokumentation und für behördliche Nachweise."

**User Story (Standort-Übersicht):** "Als Betreiber eines Gemeinschaftsgartens möchte ich eine druckbare Übersicht aller Beete mit aktueller Belegung erstellen können — zum Aushang am schwarzen Brett."

**User Story (Gießplan drucken):** "Als Urlaubsvertretung möchte ich einen ausgedruckten Gießplan mit Pflanzennamen, Fotos und Mengenangaben bekommen — damit ich die Pflanzen auch ohne App-Zugang pflegen kann."

**Beschreibung:**
In vielen Praxissituationen — Growraum, Gewächshaus, Garten, Gemeinschaftsflächen — ist ein physischer Ausdruck unverzichtbar. Nutzer brauchen druckoptimierte Darstellungen wichtiger Daten, die als PDF exportiert oder direkt über den Browser gedruckt werden können.

REQ-032 definiert ein **generisches Druckansichten-System** mit vordefinierten Templates für die häufigsten Anwendungsfälle. Die Ausgabe erfolgt entweder als browser-optimierte Druckansicht (CSS `@media print`) oder als serverseitig generiertes PDF.

## 2. Druckbare Inhalte

### 2.1 Nährstoffplan (REQ-004)

| Feld | Beschreibung |
|------|-------------|
| Plan-Name | Name des NutrientPlan |
| Phasen-Tabelle | Phase → EC-Ziel, NPK-Verhältnis, Zusätze |
| Mischanleitungen | Pro Phase: Produkt, Menge pro Liter, Mischreihenfolge |
| Wasser-Konfiguration | Basis-EC, pH-Ziel, RO-Anteil |
| Hinweise | CalMag-Korrektur, Flushing-Protokoll |

**Format:** Tabelle mit klarer Phasentrennung, optimiert für A4 Hochformat.

### 2.2 Pflege-Checkliste (REQ-022)

| Feld | Beschreibung |
|------|-------------|
| Zeitraum | Ausgewählter Tag / Woche |
| Pflanzen-Liste | Name, Standort, fällige Aktionen |
| Checkboxen | Zum Abhaken (☐ Gießen, ☐ Düngen, ☐ Schädlingskontrolle) |
| Hinweise | Pflanzspezifische Anmerkungen (z.B. "Tauchbad", "Regenwasser") |

**Format:** Kompakte Liste mit Checkboxen, optimiert für A4 Hochformat.

### 2.3 Gießplan / Urlaubsvertretung (REQ-004 + REQ-022)

| Feld | Beschreibung |
|------|-------------|
| Pflanzen-Karten | Foto, Name, Standort |
| Gießintervall | Wochentage oder Intervall |
| Wassermenge | ml/L pro Pflanze |
| Besonderheiten | "Von unten gießen", "Nebeln", "Kein Kalk" |
| Dünger | Ob ja/nein, welcher, wie viel |

**Format:** Karten-Layout mit optionalem Foto, optimiert für visuell einfache Orientierung.

### 2.4 Ernteprotokoll (REQ-007)

| Feld | Beschreibung |
|------|-------------|
| Charge | HarvestBatch-ID, Datum, Sorte |
| Menge | Frisch-/Trockengewicht |
| Qualitätsbewertung | Score, visuelle/olfaktorische Bewertung |
| Trichom-Stadium | Falls erfasst |
| Behandlungen | Letzte IPM-Anwendungen + Karenz-Status |
| Notizen | Freitext |

**Format:** Formular-Layout, behördentauglich, A4 Hochformat.

### 2.5 Standort-Übersicht / Beetplan (REQ-002)

| Feld | Beschreibung |
|------|-------------|
| Standort-Hierarchie | Zone → Bereich → Beet/Slot |
| Belegung | Aktuelle Pflanzen pro Slot |
| Phasen-Status | Aktuelle Wachstumsphase |
| Fruchtfolge-Info | Vorkultur, Familiengruppe |

**Format:** Tabellarisch oder visueller Grundriss, A4 Querformat.

### 2.6 Pflanzen-Steckbrief (REQ-001)

| Feld | Beschreibung |
|------|-------------|
| Stammdaten | Art, Sorte, Familie |
| Foto | Falls vorhanden |
| Pflegeanforderungen | Licht, Temperatur, Luftfeuchtigkeit |
| Phasen-Zeitplan | Aussaat → Ernte mit Monatsangaben |
| NPK-Bedarf | Pro Phase |
| Mischkultur | Gute/schlechte Nachbarn |

**Format:** Einzelseite pro Pflanze, A4 Hochformat.

### 2.7 Pflanzen-Infokarte / Pflanzenetikett (REQ-001 + REQ-013)

**User Story (Topf-Etikett):** "Als Zimmerpflanzen-Besitzerin möchte ich kleine Karten ausdrucken, die ich in den Topf stecken kann — mit Name, Art und einem QR-Code, der direkt zur Pflanze in der App führt."

**User Story (Growraum-Beschriftung):** "Als Grower möchte ich für jeden Slot im Zelt eine Infokarte drucken mit Sortenname, Pflanzdatum und QR-Code — damit ich beim Rundgang sofort weiß, was wo steht und schnell zur Pflanze in der App springen kann."

**User Story (Gemeinschaftsgarten):** "Als Betreiber eines Gemeinschaftsgartens möchte ich wetterfeste Beetstecker drucken mit Pflanzenname, Gattung und Pflanz-Datum — und einem QR-Code, über den Mitglieder die Pflegehinweise aufrufen können."

**User Story (Sammelausdruck):** "Als Gärtnerin mit 40 Pflanzen möchte ich mehrere Infokarten auf einmal drucken — z.B. alle Pflanzen eines Standorts auf einem A4-Blatt zum Ausschneiden."

| Feld | Sichtbarkeit | Beschreibung |
|------|-------------|-------------|
| QR-Code | Immer | Deep-Link zur PlantInstance oder Species in der App (`/t/{slug}/plants/{key}`) |
| Pflanzenname | Konfigurierbar | Anzeigename / Sortename |
| Wissenschaftlicher Name | Konfigurierbar | Botanischer Name (kursiv) |
| Gattung / Familie | Konfigurierbar | Taxonomische Einordnung |
| Pflanzdatum | Konfigurierbar | Datum der Pflanzung / des Starts |
| Aktuelle Phase | Konfigurierbar | Vegetativ, Blüte, etc. |
| Standort | Konfigurierbar | Raum / Zone / Slot |
| Sorte (Cultivar) | Konfigurierbar | Sortenname falls vorhanden |
| Kurzhinweis | Konfigurierbar | Freitext (z.B. "Nicht direkte Sonne", "Kalkfrei gießen") |

**Konfigurierbar** bedeutet: Der Nutzer kann vor dem Druck wählen, welche Felder auf der Karte erscheinen sollen (Checkbox-Dialog oder Preset).

**Format-Optionen:**
- **Einzelkarte:** Eine Karte pro Seite (A6 oder A7, konfigurierbar)
- **Sammelausdruck:** Mehrere Karten pro A4-Blatt (Raster-Layout, z.B. 2×4 oder 3×3), optimiert zum Ausschneiden mit Schnittmarken
- **QR-Code-Größe:** Min. 20×20mm für zuverlässiges Scannen, auch auf kleineren Karten

**QR-Code-Inhalt:**
- URL zur PlantInstance: `{app_base_url}/t/{tenant_slug}/plants/{plant_key}`
- Alternativ zur Species (bei Steckbrief ohne konkrete Pflanze): `{app_base_url}/species/{species_key}`
- Die `app_base_url` wird aus der Backend-Konfiguration gelesen (Umgebungsvariable `APP_BASE_URL`)

### 2.8 Kalender-Übersicht (REQ-015)

| Feld | Beschreibung |
|------|-------------|
| Zeitraum | Monat oder Woche |
| Termine | Tasks, Phasenwechsel, Erntezeitpunkte |
| Farbcodierung | Nach Kategorie |

**Format:** Kalender-Raster, A4 Querformat.

## 3. Ausgabeformate

### 3.1 Browser-Druckansicht (Frontend)

- CSS `@media print` Stylesheets für alle druckbaren Seiten
- Navigations-Elemente, Footer, Sidebar werden ausgeblendet
- Seitenumbrüche an logischen Stellen (`page-break-before`, `page-break-inside: avoid`)
- Druckbare Farben (kein dunkler Hintergrund, kontrastreiche Schrift)
- MUI-Komponente `PrintButton` löst `window.print()` aus

### 3.2 PDF-Export (Backend)

- Endpunkt: `GET /api/v1/t/{tenant_slug}/print/{template_type}/{entity_id}`
- Query-Parameter: `format=pdf` (default), `orientation=portrait|landscape`, `locale=de|en`
- Response: `application/pdf` mit `Content-Disposition: attachment`
- Serverseitige Generierung via HTML-Template → PDF-Rendering
- Gleiche Datenquellen wie die entsprechenden Frontend-Ansichten

### 3.3 CSV-Export (optional)

- Tabellarische Daten (Nährstoffpläne, Ernteprotokolle) zusätzlich als CSV
- Endpunkt: gleicher Print-Endpoint mit `format=csv`
- UTF-8 mit BOM für Excel-Kompatibilität

## 4. Datenmodell

Kein eigenes Datenmodell erforderlich — die Druckansichten greifen auf bestehende Daten aus den referenzierten REQs zu. Die Template-Definitionen sind reine Darstellungslogik.

### 4.1 Print-Template-Registry (Backend)

```python
class PrintTemplateType(str, Enum):
    NUTRIENT_PLAN = "nutrient_plan"        # REQ-004
    CARE_CHECKLIST = "care_checklist"       # REQ-022
    WATERING_PLAN = "watering_plan"         # REQ-004 + REQ-022
    HARVEST_REPORT = "harvest_report"       # REQ-007
    LOCATION_OVERVIEW = "location_overview" # REQ-002
    PLANT_FACTSHEET = "plant_factsheet"     # REQ-001
    PLANT_LABEL = "plant_label"             # REQ-001 + REQ-013
    CALENDAR_VIEW = "calendar_view"         # REQ-015
```

## 5. API-Endpunkte

| Methode | Pfad | Beschreibung |
|---------|------|-------------|
| `GET` | `/api/v1/t/{slug}/print/nutrient-plan/{plan_id}` | Nährstoffplan als PDF |
| `GET` | `/api/v1/t/{slug}/print/care-checklist` | Pflege-Checkliste (Query: `date`, `week`) |
| `GET` | `/api/v1/t/{slug}/print/watering-plan` | Gießplan für Urlaubsvertretung |
| `GET` | `/api/v1/t/{slug}/print/harvest-report/{batch_id}` | Ernteprotokoll |
| `GET` | `/api/v1/t/{slug}/print/location-overview/{location_id}` | Standort-/Beetplan |
| `GET` | `/api/v1/t/{slug}/print/plant-factsheet/{species_id}` | Pflanzen-Steckbrief |
| `GET` | `/api/v1/t/{slug}/print/plant-labels` | Pflanzen-Infokarten (Query: `plant_keys`, `fields`, `layout`) |
| `GET` | `/api/v1/t/{slug}/print/calendar` | Kalenderansicht (Query: `month`, `week`) |
| `GET` | `/api/v1/print/templates` | Verfügbare Print-Templates auflisten |

**Query-Parameter (alle Endpunkte):**
- `format`: `pdf` (default) | `csv` (nur bei tabellarischen Templates)
- `locale`: `de` (default) | `en`

**Zusätzliche Query-Parameter für `/print/plant-labels`:**
- `plant_keys`: Komma-separierte Liste von PlantInstance-Keys (Pflicht, min. 1)
- `fields`: Komma-separierte Liste der anzuzeigenden Felder (default: `name,scientific_name,planted_date,qr_code`). Mögliche Werte: `name`, `scientific_name`, `family`, `planted_date`, `current_phase`, `location`, `cultivar`, `note`
- `layout`: `single` (eine Karte pro Seite A6) | `grid_2x4` (8 Karten pro A4, default) | `grid_3x3` (9 Karten pro A4)
- `qr_size_mm`: QR-Code-Seitenlänge in mm (default: `25`, min: `20`, max: `60`)
- Der QR-Code ist immer enthalten und kann nicht abgewählt werden

## 6. Frontend-Integration

### 6.1 PrintButton-Komponente

```typescript
interface PrintButtonProps {
  templateType: PrintTemplateType;
  entityId?: string;
  queryParams?: Record<string, string>;
  variant?: "icon" | "button";  // Icon für Toolbars, Button für Aktionsbereiche
}
```

- Platzierung: In der Toolbar / Aktionsleiste der jeweiligen Detail- oder Listenansicht
- Zwei Modi:
  - **Browser-Druck**: Öffnet druckoptimierte Ansicht im gleichen Tab, löst `window.print()` aus
  - **PDF-Download**: Ruft Backend-Endpoint auf, startet Download

### 6.2 PlantLabelDialog — Konfigurationsdialog für Pflanzen-Infokarten

Vor dem Druck von Pflanzen-Infokarten öffnet sich ein Konfigurationsdialog:

```typescript
interface PlantLabelDialogProps {
  open: boolean;
  onClose: () => void;
  plantKeys: string[];          // Vorausgewählte Pflanzen (z.B. aus Listenauswahl)
  defaultFields?: string[];     // Vorauswahl der Felder
}
```

**Dialog-Inhalt:**
1. **Pflanzenauswahl** — Liste der ausgewählten Pflanzen mit Möglichkeit, weitere hinzuzufügen/zu entfernen
2. **Feld-Checkboxen** — Welche Informationen auf der Karte erscheinen sollen:
   - ☑ Pflanzenname (default: an)
   - ☑ Wissenschaftlicher Name (default: an)
   - ☐ Gattung / Familie
   - ☑ Pflanzdatum (default: an)
   - ☐ Aktuelle Phase
   - ☐ Standort
   - ☐ Sorte
   - ☐ Kurzhinweis (Freitext-Eingabe pro Pflanze)
   - ☑ QR-Code (immer an, nicht abwählbar)
3. **Layout-Auswahl** — Radio-Buttons: Einzelkarte (A6) | 8 pro Seite (2×4) | 9 pro Seite (3×3)
4. **Vorschau** — Schematische Vorschau einer einzelnen Karte mit den gewählten Feldern
5. **Aktion** — "PDF herunterladen"-Button

**Aufrufstellen:**
- PlantInstance-Detailseite (Einzelkarte)
- PlantInstance-Listenansicht (Mehrfachauswahl über Checkboxen → "Etiketten drucken"-Button in Toolbar)
- Standort-Detailseite (alle Pflanzen eines Standorts)

### 6.3 Druckvorschau

- Optionale Vorschau-Ansicht vor dem Druck
- Auswahl des Formats (PDF / Browser-Druck)
- Anpassung von Optionen (Zeitraum, Detailgrad, mit/ohne Fotos)

## 7. Berechtigungen

- Druckansichten unterliegen den gleichen Berechtigungen wie die zugrundeliegenden Daten (REQ-024 RBAC)
- `viewer`-Rolle kann alle Templates drucken, die sie auch lesen darf
- PDF-Endpunkte erfordern gültiges JWT-Token

## 8. Nicht-Funktionale Anforderungen

- PDF-Generierung < 5 Sekunden für Einzeldokumente
- CSS-Print-Stylesheets für alle druckbaren Seiten
- A4-Format als Standard (konfigurierbar)
- Barrierefreie PDFs (Tagged PDF, Dokumenttitel, Sprachattribut)
- i18n: Alle Templates in DE und EN verfügbar

## 9. Erweiterbarkeit

Das Template-System ist so gestaltet, dass neue druckbare Inhalte mit minimalem Aufwand hinzugefügt werden können:

1. Neuen `PrintTemplateType`-Enum-Wert definieren
2. HTML-Template erstellen
3. Daten-Aggregations-Funktion im zugehörigen Service implementieren
4. Route registrieren

Künftige Template-Kandidaten:
- IPM-Inspektionsprotokoll (REQ-010)
- Substrat-Wartungsplan (REQ-019)
- Vermehrungsprotokoll (REQ-017)
- Einkaufsliste / Materialbedarf
