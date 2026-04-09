---
id: UI-NFR-018
Titel: Herkunftskennzeichnung von Stammdaten
Kategorie: UI-Verhalten
Unterkategorie: Datenherkunft, Schreibschutz, Chips
Version: 1.0
Letzte Aktualisierung: 2026-04-06
Status: Entwurf
Abhängigkeiten: [REQ-001, REQ-002, REQ-006, REQ-010, REQ-004, REQ-024, UI-NFR-006, UI-NFR-010, UI-NFR-017]
Tags: [herkunft, origin, is_system, seed, chip, badge, schreibschutz, stammdaten, system-kennzeichnung]
---

# UI-NFR-018: Herkunftskennzeichnung von Stammdaten

## 1. Zielsetzung

Stammdaten in Kamerplanter stammen aus verschiedenen Quellen: vorinstallierte Seed-Daten (`system`), externe Anreicherung (`enrichment`), CSV-Import (`import`) oder manuelle Tenant-Eingabe (`tenant`). Der Nutzer MUSS jederzeit erkennen koennen, woher ein Datensatz stammt, ob er schreibgeschuetzt ist und ob er geloescht werden kann.

## 2. User Story

**Als** Nutzer der Kamerplanter-Anwendung
**moechte ich** auf einen Blick erkennen, welche Stammdaten vom System bereitgestellt werden und welche ich selbst erstellt habe
**um** zu verstehen, warum bestimmte Eintraege nicht bearbeitbar oder loeschbar sind, und um System-Referenzdaten von eigenen Daten zu unterscheiden.

## 3. Betroffene Entitaeten

### 3.1 Entitaeten mit `is_system: bool`

| Entitaet | Collection | Seed-Daten | Loeschbar wenn `is_system=true` | Editierbar wenn `is_system=true` |
|----------|-----------|------------|-------------------------------|--------------------------------|
| WorkflowTemplate | `workflow_templates` | 4 Workflows | Nein | Nein (nur Tenant-Kopie) |
| TaskTemplate | `task_templates` | Via Workflows | Nein | Nein (nur Tenant-Kopie) |
| PhaseSequence | `phase_sequences` | Ja | Nein | Nein |
| PhaseDefinition | `phase_definitions` | Ja | Nein | Nein |
| LocationType | `location_types` | 10 Typen | Nein (HTTP 403) | Nein |
| Activity | `activities` | Ja | Nein | Nein |

### 3.2 Entitaeten mit `origin: Literal['system', 'enrichment', 'import', 'tenant']`

| Entitaet | Collection | Globale Daten | Tenant-eigene Daten | Editierbar bei `origin != 'tenant'` |
|----------|-----------|--------------|--------------------|------------------------------------|
| Species | `species` | Ja (`origin: 'system'`) | Ja (`origin: 'tenant'`) | Nein (nur Overlay via `tenant_species_config`) |
| Cultivar | `cultivars` | Ja (`origin: 'system'`) | Ja (`origin: 'tenant'`) | Nein (nur Overlay via `tenant_cultivar_config`) |
| Pest | `pests` | Ja (`origin: 'system'`) | Ja (`origin: 'tenant'`) | Nein |
| Disease | `diseases` | Ja (`origin: 'system'`) | Ja (`origin: 'tenant'`) | Nein |
| Treatment | `treatments` | Ja (`origin: 'system'`) | Ja (`origin: 'tenant'`) | Nein |
| Fertilizer | `fertilizers` | Ja (`origin: 'system'`) | Ja (`origin: 'tenant'`) | Nein |
| NutrientPlan | `nutrient_plans` | Ja (`origin: 'system'`) | Ja (`origin: 'tenant'`) | Nein |

> **Hinweis:** `origin`-Feld ist in REQ-001 v5.0 und REQ-024 v1.3 spezifiziert, aber noch nicht implementiert. Diese UI-NFR gilt fuer beide Felder (`is_system` und `origin`) und wird wirksam, sobald die jeweiligen Backend-Felder implementiert sind.

---

## 4. Anforderungen

### 4.1 Herkunfts-Chip (Origin-Chip)

| ID | Anforderung | Stufe |
|----|-------------|-------|
| R-001 | Jede Entitaet mit `is_system=true` oder `origin != 'tenant'` MUSS in der Detail-Ansicht einen **Herkunfts-Chip** in der Meta-Zeile (Pattern C gemaess UI-NFR-017) anzeigen. | MUSS |
| R-002 | Jede Entitaet mit `is_system=true` oder `origin != 'tenant'` MUSS in Listenansichten/Tabellen einen **Herkunfts-Chip** als Spalte oder Inline-Badge anzeigen. | MUSS |
| R-003 | Entitaeten mit `origin='tenant'` oder `is_system=false` SOLLEN **keinen** Herkunfts-Chip anzeigen — die Abwesenheit signalisiert "eigener Datensatz". | SOLL |
| R-004 | Der Herkunfts-Chip MUSS `size="small"` verwenden (konsistent mit UI-NFR-017 R-015). | MUSS |
| R-005 | Der Herkunfts-Chip MUSS ein fuehrendes Icon enthalten, um die Herkunft auch ohne Farbe erkennbar zu machen (Barrierefreiheit gemaess UI-NFR-002). | MUSS |

### 4.2 Chip-Varianten

| Origin-Wert | Label (DE) | Label (EN) | Icon | `color` | `variant` |
|-------------|-----------|-----------|------|---------|-----------|
| `system` / `is_system=true` | "System" | "System" | `SettingsIcon` | `"info"` | `"outlined"` |
| `enrichment` | "Angereichert" | "Enriched" | `AutoAwesomeIcon` | `"secondary"` | `"outlined"` |
| `import` | "Importiert" | "Imported" | `FileUploadIcon` | `"default"` | `"outlined"` |
| `tenant` / `is_system=false` | — (kein Chip) | — (no chip) | — | — | — |

| ID | Anforderung | Stufe |
|----|-------------|-------|
| R-006 | Die vier Chip-Varianten MUESSEN die oben definierten Label, Icons und Farbkombinationen verwenden. | MUSS |
| R-007 | Alle Labels MUESSEN ueber i18n-Keys lokalisiert werden: `common.origin.system`, `common.origin.enrichment`, `common.origin.import`. | MUSS |
| R-008 | Fuer Entitaeten die nur `is_system: bool` (kein `origin`-Feld) besitzen, MUSS `is_system=true` wie `origin='system'` behandelt werden (gleicher Chip). | MUSS |

### 4.3 Tooltip mit Erklaerung

| ID | Anforderung | Stufe |
|----|-------------|-------|
| R-009 | Der Herkunfts-Chip MUSS bei Hover/Focus einen Tooltip mit einer erklaerenden Beschreibung anzeigen. | MUSS |
| R-010 | Tooltip-Texte MUESSEN die Herkunft und die daraus resultierenden Einschraenkungen erklaeren. | MUSS |

**Tooltip-Texte:**

| Origin | Tooltip (DE) | Tooltip (EN) |
|--------|-------------|-------------|
| `system` | "Vom System bereitgestellt. Kann nicht bearbeitet oder geloescht werden." | "Provided by the system. Cannot be edited or deleted." |
| `enrichment` | "Automatisch ueber externe Quellen angereichert (REQ-011). Kann nicht direkt bearbeitet werden." | "Automatically enriched from external sources. Cannot be edited directly." |
| `import` | "Ueber CSV-Import hinzugefuegt. Kann bearbeitet und geloescht werden." | "Added via CSV import. Can be edited and deleted." |

> **Hinweis:** `import`-Eintraege sind grundsaetzlich editierbar, da sie vom Nutzer eingebracht wurden. Sie erhalten den Chip nur zur Herkunfts-Transparenz.

### 4.4 Schreibschutz-Anzeige

| ID | Anforderung | Stufe |
|----|-------------|-------|
| R-011 | Bei `origin='system'`, `origin='enrichment'` oder `is_system=true` MUSS der "Bearbeiten"-Button in der Detail-Ansicht **ausgeblendet** werden. | MUSS |
| R-012 | Bei `origin='system'` oder `is_system=true` MUSS der "Loeschen"-Button in der Detail-Ansicht **ausgeblendet** werden. | MUSS |
| R-013 | In Listenansichten MUESSEN Zeilen-Aktionen (Edit-Icon, Delete-Icon) fuer schreibgeschuetzte Eintraege **ausgeblendet** werden. | MUSS |
| R-014 | Anstelle des ausgeblendeten "Bearbeiten"-Buttons KANN ein Hinweistext angezeigt werden, z.B. "Systemdaten koennen nicht bearbeitet werden." als `Typography variant="body2" color="text.secondary"` unterhalb der Meta-Zeile. | KANN |
| R-015 | Fuer WorkflowTemplates und NutrientPlans mit `is_system=true` oder `origin='system'` SOLL ein **"Als Vorlage kopieren"**-Button angeboten werden, der eine editierbare Tenant-Kopie erstellt. | SOLL |

### 4.5 Tabellen-Darstellung

| ID | Anforderung | Stufe |
|----|-------------|-------|
| R-016 | Tabellen mit gemischten System- und Tenant-Daten MUESSEN einen **Filter "Herkunft"** anbieten (Chip-Filter gemaess UI-NFR-010 R-041). | MUSS |
| R-017 | Die Filter-Optionen MUESSEN die vorhandenen Origin-Werte als Auswahlmoeglichkeiten enthalten: "System", "Angereichert", "Importiert", "Eigene". | MUSS |
| R-018 | Der Standard-Filter SOLL "Alle" sein (kein Filter aktiv). | SOLL |
| R-019 | In der Tabellen-Spalte MUSS der Herkunfts-Chip identisch zur Detail-Ansicht dargestellt werden (gleiche Icons, Farben, Labels). | MUSS |
| R-020 | Die Herkunfts-Spalte SOLL als **sekundaere Spalte** klassifiziert werden (gemaess UI-NFR-010 Abschnitt 8.1: auf kleinen Bildschirmen ausblendbar). | SOLL |

### 4.6 Sortierung

| ID | Anforderung | Stufe |
|----|-------------|-------|
| R-021 | In Listenansichten SOLLEN System-Eintraege **nach** Tenant-eigenen Eintraegen sortiert werden, sofern keine andere Sortierung aktiv ist. | SOLL |
| R-022 | Die Standard-Sortierreihenfolge nach Herkunft SOLL sein: `tenant` → `import` → `enrichment` → `system`. | SOLL |

---

## 5. Wiederverwendbare Komponente

### 5.1 `OriginChip`-Komponente

Es MUSS eine zentrale, wiederverwendbare Komponente `OriginChip` erstellt werden, die in allen betroffenen Seiten eingesetzt wird:

```tsx
// src/frontend/src/components/common/OriginChip.tsx

interface OriginChipProps {
  /** origin-Feld der Entitaet (system/enrichment/import/tenant) */
  origin?: 'system' | 'enrichment' | 'import' | 'tenant';
  /** Fallback fuer Entitaeten die nur is_system haben */
  isSystem?: boolean;
}
```

| ID | Anforderung | Stufe |
|----|-------------|-------|
| R-023 | Die `OriginChip`-Komponente MUSS als einzelne wiederverwendbare Komponente implementiert werden. | MUSS |
| R-024 | Die Komponente MUSS sowohl `origin`-String als auch `isSystem`-Boolean als Props akzeptieren. | MUSS |
| R-025 | Bei `origin='tenant'` oder `isSystem=false` (und kein `origin` gegeben) MUSS die Komponente `null` rendern. | MUSS |

### 5.2 `useOriginProtection`-Hook

Es SOLL ein Hook bereitgestellt werden, der die Schreibschutz-Logik kapselt:

```tsx
// src/frontend/src/hooks/useOriginProtection.ts

interface OriginProtection {
  /** true wenn der Datensatz nicht bearbeitet werden darf */
  isReadOnly: boolean;
  /** true wenn der Datensatz nicht geloescht werden darf */
  isDeletionProtected: boolean;
  /** true wenn "Als Vorlage kopieren" angeboten werden soll */
  canCopyAsTemplate: boolean;
  /** Tooltip-Text fuer den Origin-Chip */
  tooltipText: string;
}
```

| ID | Anforderung | Stufe |
|----|-------------|-------|
| R-026 | Der Hook SOLL die Schreibschutz-Logik zentral kapseln, damit alle Seiten konsistent reagieren. | SOLL |
| R-027 | Die Logik MUSS sein: `isReadOnly = origin in ['system', 'enrichment'] oder is_system=true`. `import`-Eintraege sind editierbar. | MUSS |
| R-028 | Die Logik MUSS sein: `isDeletionProtected = origin in ['system'] oder is_system=true`. `enrichment`- und `import`-Eintraege sind loeschbar. | MUSS |

---

## 6. i18n-Keys

Die folgenden i18n-Keys MUESSEN in DE und EN bereitgestellt werden:

```json
{
  "common": {
    "origin": {
      "system": "System",
      "enrichment": "Angereichert",
      "import": "Importiert",
      "tenant": "Eigene",
      "tooltipSystem": "Vom System bereitgestellt. Kann nicht bearbeitet oder geloescht werden.",
      "tooltipEnrichment": "Automatisch ueber externe Quellen angereichert. Kann nicht direkt bearbeitet werden.",
      "tooltipImport": "Ueber CSV-Import hinzugefuegt. Kann bearbeitet und geloescht werden.",
      "filterLabel": "Herkunft",
      "copyAsTemplate": "Als Vorlage kopieren",
      "readOnlyHint": "Systemdaten koennen nicht bearbeitet werden."
    }
  }
}
```

```json
{
  "common": {
    "origin": {
      "system": "System",
      "enrichment": "Enriched",
      "import": "Imported",
      "tenant": "Custom",
      "tooltipSystem": "Provided by the system. Cannot be edited or deleted.",
      "tooltipEnrichment": "Automatically enriched from external sources. Cannot be edited directly.",
      "tooltipImport": "Added via CSV import. Can be edited and deleted.",
      "filterLabel": "Origin",
      "copyAsTemplate": "Copy as template",
      "readOnlyHint": "System data cannot be edited."
    }
  }
}
```

---

## 7. Seiten-Zuordnung (Pruefmatrix)

Welche Seiten MUESSEN den Origin-Chip und Schreibschutz implementieren:

| Seite | Entitaet | Herkunftsfeld | Origin-Chip | Schreibschutz | Kopier-Button | Filter |
|-------|----------|--------------|-------------|---------------|---------------|--------|
| SpeciesDetailPage | Species | `origin` | Ja | Ja | Nein | — |
| SpeciesListPage | Species | `origin` | Ja (Spalte) | Ja (Zeilen-Aktionen) | — | Ja |
| CultivarDetailPage | Cultivar | `origin` | Ja | Ja | Nein | — |
| FertilizerDetailPage | Fertilizer | `origin` | Ja | Ja | Nein | — |
| FertilizerListPage | Fertilizer | `origin` | Ja (Spalte) | Ja (Zeilen-Aktionen) | — | Ja |
| NutrientPlanDetailPage | NutrientPlan | `origin` | Ja | Ja | Ja | — |
| NutrientPlanListPage | NutrientPlan | `origin` | Ja (Spalte) | Ja (Zeilen-Aktionen) | — | Ja |
| PestDetailPage | Pest | `origin` | Ja | Ja | Nein | — |
| DiseaseDetailPage | Disease | `origin` | Ja | Ja | Nein | — |
| TreatmentDetailPage | Treatment | `origin` | Ja | Ja | Nein | — |
| IpmListPage | Pest/Disease/Treatment | `origin` | Ja (Spalte) | Ja (Zeilen-Aktionen) | — | Ja |
| WorkflowDetailPage | WorkflowTemplate | `is_system` | Ja | Ja | Ja | — |
| WorkflowListPage | WorkflowTemplate | `is_system` | Ja (Spalte) | Ja (Zeilen-Aktionen) | — | Ja |
| PhaseSequenceDetailPage | PhaseSequence | `is_system` | Ja | Ja | Nein | — |
| PhaseSequenceListPage | PhaseSequence | `is_system` | Ja (Spalte) | Ja (Zeilen-Aktionen) | — | Ja |
| PhaseDefinitionListPage | PhaseDefinition | `is_system` | Ja (Spalte) | Ja (Zeilen-Aktionen) | — | Ja |
| LocationTypeListPage | LocationType | `is_system` | Ja (Spalte) | Ja (Zeilen-Aktionen) | — | Ja |
| ActivityListPage | Activity | `is_system` | Ja (Spalte) | Ja (Zeilen-Aktionen) | — | Ja |

---

## 8. Visuelles Referenzbeispiel

### 8.1 Detail-Ansicht (Pattern C)

```
┌──────────────────────────────────────────────────────────┐
│  Cannabis SOG                                  [Loeschen]│  ← Loeschen ausgeblendet bei system
│  ⚙ System                                               │  ← Meta-Zeile mit Origin-Chip
│                                                          │
│  ℹ Systemdaten koennen nicht bearbeitet werden.          │  ← Optionaler Hinweistext
│  [Als Vorlage kopieren]                                  │  ← Kopier-Button (WorkflowTemplate)
│                                                          │
│  ┌─ Tabs ─────────────────────────────────────┐          │
│  │ Uebersicht │ Aufgaben │ ...                │          │
└──────────────────────────────────────────────────────────┘
```

### 8.2 Listenansicht (Tabelle)

```
┌──────────────────────────────────────────────────────────┐
│  Filter: [Herkunft ▾]  [Kategorie ▾]  [Suche...]        │
│                                                          │
│  Name                    │ Kategorie │ Herkunft │ Aktion │
│  ────────────────────────┼───────────┼──────────┼────────│
│  Meine Tomaten-Workflow  │ Ernte     │          │ ✏ 🗑   │  ← Tenant: kein Chip, Aktionen sichtbar
│  Cannabis SOG            │ Anbau     │ ⚙ System │        │  ← System: Chip, keine Aktionen
│  General Maintenance     │ Pflege    │ ⚙ System │        │  ← System: Chip, keine Aktionen
│  Importierter Plan       │ Duengung  │ ↑ Import │ ✏ 🗑   │  ← Import: Chip, Aktionen sichtbar
└──────────────────────────────────────────────────────────┘
```

---

## 9. Abgrenzung

- Diese Spezifikation regelt **ausschliesslich** die visuelle Kennzeichnung und UI-seitige Schreibschutz-Anzeige.
- Die **Backend-Validierung** (HTTP 403 bei Loeschen/Editieren von System-Daten) ist in den jeweiligen REQ-Dokumenten spezifiziert.
- Die **Promotion** von Tenant-Daten zu System-Daten (origin: tenant → system) ist eine KA-Admin-Funktion (REQ-024 v1.3) und wird in einer separaten Admin-UI spezifiziert.
- Das `origin`-Feld existiert im Backend noch nicht fuer alle Entitaeten — die UI-Implementierung erfolgt schrittweise parallel zur Backend-Implementierung.

---

## 10. Risiken bei Nicht-Einhaltung

| Risiko | Auswirkung | Schweregrad | Gegenmassnahme |
|--------|-----------|-------------|----------------|
| **Fehlende Herkunftskennzeichnung** | Nutzer versucht System-Daten zu bearbeiten, erhaelt unverstaendlichen Fehler | Hoch | Origin-Chip + Tooltip + ausgeblendete Aktionen |
| **Inkonsistente Chip-Darstellung** | Verwirrung ueber Bedeutung der Chips auf verschiedenen Seiten | Mittel | Zentrale `OriginChip`-Komponente |
| **Keine Filteroption** | Nutzer kann eigene Daten nicht von System-Daten trennen | Mittel | Herkunfts-Filter in allen Listenansichten |
| **Fehlender "Als Vorlage kopieren"-Button** | Nutzer hat keine Moeglichkeit, System-Workflows anzupassen | Hoch | Kopier-Button fuer Templates/Plans |

---

## 11. Definition of Done

- [ ] `OriginChip`-Komponente implementiert mit allen vier Varianten
- [ ] `useOriginProtection`-Hook implementiert
- [ ] i18n-Keys fuer DE und EN vorhanden
- [ ] Origin-Chip in allen 17 Seiten der Pruefmatrix (Abschnitt 7) integriert
- [ ] Schreibschutz (ausgeblendete Buttons) in allen Detail-Seiten aktiv
- [ ] Herkunfts-Filter in allen Listenansichten aktiv
- [ ] Tooltips auf allen Origin-Chips sichtbar
- [ ] "Als Vorlage kopieren" fuer WorkflowTemplate und NutrientPlan implementiert
- [ ] Barrierefreiheit: Icons + Text + Tooltip (nicht nur Farbe) zur Unterscheidung
- [ ] Responsive: Herkunfts-Spalte als sekundaer klassifiziert (ausblendbar auf Mobile)
- [ ] Visueller Abgleich mit UI-NFR-017 Pattern C (Meta-Zeile, Spacing, Groessen)
