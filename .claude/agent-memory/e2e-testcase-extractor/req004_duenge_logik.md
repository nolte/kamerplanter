---
name: REQ-004 Dünge-Logik — UI Patterns and Key Test Insights
description: Key UI patterns, page structure, and test insights for REQ-004 fertilizer management, nutrient plan, EC-budget, and Multi-Channel Delivery
type: project
---

## REQ-004 Dünge-Logik (v3.4) + REQ-004-A EC-Budget-Kalkulation (v1.1)

**Output**: `spec/e2e-testcases/TC-REQ-004.md`, 88 test cases, IDs TC-004-001 to TC-004-088

## Frontend Pages (src/frontend/src/pages/duengung/)

- FertilizerListPage, FertilizerDetailPage, FertilizerCreateDialog
- NutrientPlanListPage, NutrientPlanDetailPage, NutrientPlanCreateDialog, NutrientPlanAssignDialog
- PhaseEntryDialog, ChannelFertilizerDialog, DeliveryChannelDialog, DeliveryChannelAccordion, DeliveryChannelChips
- FeedingEventListPage, FeedingEventDetailPage, FeedingEventCreateDialog
- NutrientCalculationsPage (Berechnungsseite, zustandslos), DosageCalculatorTab
- FertilizerGanttChart, PhaseGanttChart, FertilizerUsageGantt, PhaseDetailGantt
- WaterMixRecommendationBox

## Key UI Patterns

### Düngemittel-Filterung
- Filterbar nach: fertilizer_type, brand (Teilstring), tank_safe (bool), is_organic (bool)
- Alle Filter AND-verknüpft, als Chip-Gruppe oberhalb der Tabelle
- Filter-Chip: `data-testid="reset-filters-button"` zum Zurücksetzen

### Fertilizer Reverse Lookup
- Auf FertilizerDetailPage: Abschnitt „Verwendet in Nährstoffplänen" mit klickbaren Chips
- Bei nicht verwendeten Düngern: explizit „Keinem Plan zugeordnet" anzeigen

### Foliar-Warnung Blütephase (G-013)
- Phase=flowering, Woche ≥ 2: gelbes ⚠ neben Methoden-Dropdown + expandierbarer Alert-Banner
- Phase=flowering, Woche 1: nur informativer Hinweis (INFO-Severity, blau)
- Ausnahme: FeedingEvent mit verknüpftem TreatmentApplication(is_emergency=true) → Warnung unterdrückt
- Kein Hardblock — Speichern bleibt möglich

### Gantt-Diagramm
- React.lazy geladen (Performance: nur beim Tab-Wechsel)
- Modus A: cycle_restart_from_sequence = null → linearer Zeitstrahl
- Modus B: cycle_restart_from_sequence ≠ null → gestrichelte Zyklus-Grenzlinie + ↻-Symbol
- Optionale Dünger: gestrichelter Rahmen oder reduzierte Opazität
- Hover-Tooltip auf Phasen-Header: vollständige Phase-Details (EC, pH, NPK, alle Dünger, EC-Budget-Status)
- Lücken: leere Spalten grauer Hintergrund
- Überlappungen: gestapelte Balken + roter Rahmen

### Multi-Channel Delivery (Expert-only für Beginner)
- REQ-021 Integration: Beginner = ausgeblendet, Intermediate = „Erweitert", Expert = voll sichtbar
- ChannelCreateDialog: 4-Step-Wizard (Methode → Parameter → Schedule → Dünger)
- Channel-Chips: Icon + Label + Kurzinfo (z. B. „3x/Tag")
- Accordion für expandierte Channel-Ansicht
- Legacy-Toggle: „Zu Multi-Channel konvertieren" für delivery_channels=[] Entries
- Nach Konvertierung: synthetischer Channel erstellt, Legacy-Felder ausgegraut

### Dosierungsrechner-Tab (NED normalisierte Referenzdosierung)
- Site-Dropdown Pre-Fill wenn Plan einem Run mit Site zugeordnet ist
- Wasser-Info-Box: Tap-EC, RO-EC, empfohlenes Mischverhältnis, effektive Parameter
- Pro Phase: Referenzdosierungen (grau, „Herstellerangabe") + berechnete (hervorgehoben, „Für dein Wasser")
- source-Feld: „reference" (grau), „scaled" (normal), „auto_calmag" (hervorgehoben)
- EC-Budget-Visualisierung: Segmented Bar (Wasser / CalMag / Dünger / pH-Reserve)
- Fallback ohne Site/Wasserprofil: Referenzdosierungen + Hinweis

## EC-Budget-Kalkulation (REQ-004-A)

### 3-Stufen-Pipeline (im UI sichtbar)
1. Stufe 1 — WaterMixCalculator: EC_mix = EC_ro × r/100 + EC_tap × (1 − r/100)
2. Stufe 2 — CalMag-Korrektur: Ca/Mg-Defizit berechnen
3. Stufe 3 — EC-Budget-Skalierung: k = EC_net / EC_rezept, d_i = k × r_i

### EC-Grenzwerte für Validierungen
| Substrat | Seedling | Vegetative | Flowering |
|---------|----------|------------|-----------|
| hydro_solution | 0.8–1.2 | 1.6–2.4 | 1.8–2.8 |
| coco | 0.8–1.0 | 1.6–2.0 | 1.8–2.4 |
| soil | 0.4–0.6 | 0.8–1.4 | 1.0–1.6 |
| living_soil | — | — | — (EC-Budget deaktiviert) |

### Living Soil: EC-Budget deaktiviert
- System zeigt organische Düngungsempfehlung statt EC-Budget

### Warnmeldungen (alle Soft-Warnings, kein Hardblock)
- Basis-EC ≥ Ziel-EC: „Basis-EC überschreitet Ziel-EC. Erhöhen Sie Osmose-Anteil oder senken Sie Ziel-EC."
- Ziel-EC überschreitet EC_max: „Überschreitet empfohlene Obergrenze für Phase/Substrat."
- EC_mix < EC_ro: Fehler „Physikalisch nicht erreichbar."
- Ca/Mg-Ratio < 2.0: Ca-Aufnahmehemmung-Warnung
- Ca/Mg-Ratio > 5.0: Mg-Aufnahmehemmung-Warnung
- RO ≥ 80%: pH-Puffer-Warnung
- Einzeldünger > max_dose: Sicherheitslimit-Warnung

## Multi-Channel Validierungsregeln (für Test-Extraktion)
| Regel | Severity | UI-Verhalten |
|-------|---------|-------------|
| MCD-V01 (Tank-Safe) | CRITICAL | Dünger nicht hinzufügbar |
| MCD-V04 (Foliar EC > 1.0 mS) | INFO | Hinweis, Speichern möglich |
| MCD-V05 (Foliar Blüte Woche ≥ 2) | WARNING | Warnung, Speichern möglich |
| MCD-V07 (Params-Match) | ERROR | Formular-Validierungsfehler |
| MCD-V08 (channel_id unique) | ERROR | Formular-Validierungsfehler |
| MCD-V12 (Max 10 Channels) | ERROR | Button deaktiviert oder Fehler |
| MCD-V20 (Dünger-Duplikat) | WARNING | Validierungsergebnis |

## WateringSchedule Validierungsregeln
- mode=weekdays → weekday_schedule Pflicht, 1-7 Werte, keine Duplikate, 0-6 (Mo-So)
- mode=interval → interval_days Pflicht, Bereich 1-90
- preferred_time → Format HH:MM
- application_method auf Plan-Ebene darf NICHT fertigation sein (nur drench/foliar/top_dress)
- Auf Channel-Ebene ist fertigation ERLAUBT (Abweichung von Plan-Level-Regel)

## Spec-spezifische Hinweise
- REQ-004 Section 4 (Akzeptanzkriterien) = Section 7 im Dokument (nummeriert 7)
- REQ-004-A enthält alle EC-Budget-Mathematik (Formeln, Grenzwerte, Praxisbeispiele)
- Testszenarien 1-11 in §7 (Szenario 10-11 = Gantt-Tests) direkt als Testfälle übernommen
- DoD-Liste in §7 hat 75+ Punkte — vollständig in 88 Testfällen abgedeckt
