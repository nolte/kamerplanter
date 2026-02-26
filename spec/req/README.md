# Kamerplanter - Anforderungsspezifikationen

## Übersicht
Dieses Verzeichnis enthält **16 vollständig ausgearbeitete Anforderungsdokumente** für das Kamerplanter-System — eine Agrotech-Plattform für Pflanzen-Lebenszyklusmanagement (Cannabis, Gemüse, Kräuter) mit Python/FastAPI-Backend und ArangoDB Graph-Datenbank.

### Dokumenten-Struktur
Jedes Dokument folgt einer konsistenten, RAG-optimierten Struktur:
1. **YAML-Header** — Metadaten, Kategorisierung, Technologie-Stack
2. **Business Case** — User Stories, fachliche Beschreibung
3. **ArangoDB-Modellierung** — Collections, Edges, AQL-Queries
4. **Technische Umsetzung** — Python-Code, Logik, Validierung (Pydantic v2, Type Hinting)
5. **Abhängigkeiten** — Querverweise zu anderen Modulen (bidirektional, mit Impact-Level)
6. **Akzeptanzkriterien** — Definition of Done, Testszenarien (GIVEN/WHEN/THEN)

---

## Enthaltene Dokumente

### 🌱 REQ-001: Stammdatenverwaltung (35 KB)
**Fokus:** Botanische Taxonomie, Lebenszyklus-Typen, Photoperiodismus
- Vernalisations-Tracking für Zweijährige
- Dormanz-Trigger für Mehrjährige
- Fruchtfolge-Validierung (3-5 Jahre Historie)
- Mischkultur-Kompatibilität-Matrix

**Highlights:**
- Photoperioden-Berechnung basierend auf GPS-Koordinaten
- Allelopathie-Scores für Companion Planting
- Hardiness Zones Integration (USDA)

---

### 📍 REQ-002: Standort & Substrat (41 KB)
**Fokus:** Räumliche Verwaltung, Substrat-Management, Fruchtfolge-Engine
- Rekursive Hierarchie: Site → Location (beliebig tief) → Slot
- Indoor (Growzelte) + Outdoor (Beete) + Hydro-Systeme
- Substrat-Recycling-Tracker mit Aufbereitungs-Anleitung
- ArangoDB Geo-Indizes für GPS-basierte Standorte

**Highlights:**
- Hydro-spezifisches Monitoring (NFT, DWC, Aeroponik)
- Reservoir-Management mit Nährlösungs-Wechsel-Scheduler
- Nachbarschafts-Graph für Mischkultur-Analysen

---

### 🔄 REQ-003: Phasensteuerung (21 KB)
**Fokus:** State-Machine für Wachstumsphasen, Ressourcen-Profile
- Automatische Phasen-Transitions (zeitbasiert/ereignisgesteuert)
- VPD-Berechnung mit Zielbereich-Validierung
- Photoperioden-Manager (gradueller Übergang 18h → 12h)
- NPK-Auto-Adjust bei Phasenwechsel

**Highlights:**
- VPD-Optimizer für Transpirationssteuerung
- Lichtspektrum-Profile (Blue/Red/Far-Red Ratio)
- Stress-Phasen (Hardening, Drought-Stress)

---

### 💧 REQ-004: Dünge-Logik (57 KB)
**Fokus:** Multi-Part-Fertilizer, EC-Budget-Management, Lifecycle-Nährstoffpläne
- Kritische Misch-Reihenfolge (verhindert Ausfällungen)
- EC-Netto-Rechner (Ziel-EC minus Basis-EC)
- Flushing-Protokolle (Substrat-spezifisch)
- Lifecycle Nutrient Plans (NutrientPlan vs. NutrientProfile)

**Highlights:**
- Step-by-Step Mixing Instructions
- Rezirkulations-Logik für Hydro-Systeme
- Inkompatibilitäten-Check (CalMag + Sulfate)

---

### 🌡️ REQ-005: Hybrid-Sensorik (45 KB)
**Fokus:** Home Assistant Integration, MQTT, Manual Fallback
- Dreistufiges Monitoring (Auto / Semi-Auto / Manuell)
- Sensor-Fallback-Manager (Auto-Task bei Ausfall >6h)
- Multi-Parameter-Tracking (Temp, RLF, pH, EC, PPFD, CO2)
- TimescaleDB-Integration für Zeitreihen

**Highlights:**
- Graceful Degradation ohne Hardware
- Datenquellen-Kennzeichnung (Auto vs. Manual)
- Plausibilitätsprüfung und Interpolation

---

### ✅ REQ-006: Aufgabenplanung (45 KB)
**Fokus:** Workflow-Templates, HST-Validierung, Dependency-Chains
- System-Templates vs. User-Blueprints
- Phase-Trigger + Zeit-Trigger + Conditional-Trigger
- HST-Validator (verhindert Topping in Blüte)
- Task-Scoring und Priorisierung

**Highlights:**
- Foto-Upload bei kritischen Tasks
- Gantt-Chart für 4-Wochen-Vorschau
- Celery-Integration für Erinnerungen

---

### 🌾 REQ-007: Erntemanagement (47 KB)
**Fokus:** Gattungsspezifische Reife-Indikatoren
- Factory-Pattern (TrichomeIndicator vs. FoliageIndicator)
- Flushing-Trigger (14 Tage vor Ernte)
- Batch-Tracking mit QR-Codes (Seed-to-Shelf)

**Highlights:**
- Quality-Scoring (Optik, Aroma, Potenz)
- Dunkelphase-Protokoll (48h vor Ernte)

---

### 🍷 REQ-008: Post-Harvest (45 KB)
**Fokus:** Trocknung, Curing, Lagerung
- Spezies-spezifische Protokolle (Cannabis, Zwiebel, Kräuter)
- Burping-Scheduler für Fermentierung
- Gewichts-Tracking (Ziel-Trockenheit)

**Highlights:**
- Schimmel-Prävention (RLF-Alerts)
- Schalenhärtung für Zwiebeln/Kürbis

---

### 📊 REQ-009: Dashboard (41 KB)
**Fokus:** Multi-Widget-Dashboard, Mobile-First
- Live-Grid aller Slots mit Phase-Indikatoren
- VPD-Ampel, Task-Queue, Alert-Center
- WebSocket-Updates für Real-Time-Daten

**Highlights:**
- QR-Scanner für Slot-Identifikation
- Offline-Modus mit Sync
- Dark-Mode (Growzelt-freundlich)

---

### 🐛 REQ-010: IPM-System (16 KB)
**Fokus:** Integriertes Pest Management
- Mehrstufiger IPM-Ansatz (Prävention → Monitoring → Intervention)
- Resistenzmanagement (Wirkstoff-Rotation)
- Nützlingseinsatz-Kalkulation
- Karenzzeit-Enforcement

**Highlights:**
- Dynamische Inspektions-Frequenz (Befallsdruck-abhängig)
- Chemie-Inkompatibilitäts-Check
- Standort-Befallshistorie (3 Jahre)

---

### 🔗 REQ-011: Externe Stammdatenanreicherung (31 KB)
**Fokus:** API-Adapter, Multi-Source-Sync, Datenprovenienz
- Adapter-Pattern für modulare Quellen-Anbindung (Perenual, OpenFarm, GBIF, Trefle, Otreeba)
- Periodische Synchronisation via Celery-Beat (täglich inkrementell, wöchentlich full)
- Lokale Hoheit: manuelle Daten werden nie automatisch überschrieben
- Checksum-basiertes Überspringen unveränderter Daten

**Highlights:**
- Taxonomie-Normalisierung via GBIF (Synonym-Auflösung)
- Cannabis-Sorten-Import via Otreeba
- Accept/Reject-Workflow für vorgeschlagene Anreicherungen
- Sync-Historie und Health-Checks

---

### 📥 REQ-012: Stammdaten-Import (54 KB)
**Fokus:** CSV-Upload, Bulk-Import, Zwei-Phasen-Prozess
- Upload → Preview → Confirm → Import Workflow
- Transparente Zeilenvalidierung mit Fehleranzeige pro Feld
- Konfigurierbare Duplikatbehandlung (skip/update/fail)
- Atomarer Import mit Rollback bei kritischen Fehlern

**Highlights:**
- Unterstützte Entitäten: Species, Cultivar, BotanicalFamily
- Vorschau-Tabelle mit Inline-Korrektur
- Import-Protokollierung mit Ergebnis-Statistiken

---

### 🔄 REQ-013: Pflanzdurchlauf (54 KB)
**Fokus:** Gruppenmanagement, Batch-Operationen, Seed-to-Shelf-Traceability
- Pflanzdurchlauf (PlantingRun) als leichtgewichtiger Gruppierungs-Container
- Batch-Erstellung: N Pflanzen mit auto-generierten IDs anlegen
- Batch-Phasenübergang, Batch-Ernte, Batch-Entfernung
- Individuelle Autonomie: Pflanzen jederzeit aus Gruppe lösbar

**Highlights:**
- 3 Run-Typen: Monokultur, Klon, Mischkultur
- Direkte HarvestBatch-Verknüpfung (REQ-007)
- Detach/Reattach ohne Datenverlust

---

### 🪣 REQ-014: Tankmanagement (33 KB)
**Fokus:** Tank-Verwaltung, Wartungsplanung, Bewässerungsinfrastruktur
- Tank-Typen: Nährstofflösung, Gießwasser, Reservoir, Rezirkulation
- Pflicht-Zuordnung zu Location bei automatischer Bewässerung
- Zustandsüberwachung (pH, EC, Temperatur, Füllstand) mit Alert-System
- Wartungspläne mit automatischer Task-Generierung (REQ-006)
- Ergänzende manuelle Bewässerung per Gießkanne neben automatischem System
- 4 Applikationsmethoden: Fertigation, Drench, Foliar, Top Dress

**Highlights:**
- Lückenlose Befüllungshistorie (TankFillEvent) mit Dünger-Snapshot und Rezept-Verknüpfung
- WateringEvent auf Slot-/Pflanzenebene — dokumentiert was die Pflanze tatsächlich bekommt
- Tank-Kaskaden (Reservoir → Mischtank)
- Standard-Wartungsintervalle je Tank-Typ
- Algenrisiko-Erkennung (Temperatur + Deckel-Status)
- Celery-Beat für tägliche Wartungs-Checks

---

### 📅 REQ-015: Kalenderansicht & Kalender-Integration
**Fokus:** Zentrale Kalenderdarstellung, iCal-Export, externe Kalender-Abonnements
- Tasks (REQ-006) als primäre Kalender-Datenquelle — kein separates Event-Modell
- Optionale Timeline-Events: Phasentransitionen, Düngungen, Wartungen, Befüllungen
- CalendarEvent als virtuelles Aggregat (computed at query time, nicht persistiert)
- CalendarFeed mit Token-basiertem Zugang für externe Kalender-Apps
- Farbkodierung pro Kategorie (11 Kategorien)

**Highlights:**
- FullCalendar React-Komponente (Monat/Woche/Tag/Agenda)
- RFC 5545 iCalendar-Export mit VEVENT, VALARM, CATEGORIES, PRIORITY
- webcal:// Abonnement für Thunderbird, Apple Calendar, Google Calendar
- Feed-Management mit Token-Rotation und Filter-Konfiguration
- Responsive: Mobile → Agenda-Liste, Desktop → Grid mit Filter-Sidebar
- Multi-Source-AQL-Aggregation über 5+ Collections

---

### 🔗 REQ-016: Optionale InvenTree-Integration
**Fokus:** Inventar-Anbindung, Verbrauchstracking, Equipment-Verwaltung
- Optionale Anbindung an InvenTree (Open-Source-Inventarverwaltung, REST-API)
- Bidirektionaler Sync: Stock-Pull (hourly) + Consumption-Push (5-min)
- Equipment als First-Class-Entity (Pumpen, Sensoren, Werkzeuge, Reinigungsmittel)
- Generische Link-Tabelle (`inventree_references`) für lose Kopplung
- ConsumptionTracker: Automatische Verbrauchsbuchungen bei FeedingEvent, TankFillEvent, MaintenanceLog

**Highlights:**
- Graceful Degradation: Kernsystem funktioniert ohne InvenTree
- Drift-Detection bei >20% Bestandsabweichung
- Immutables Transaktions-Log mit Retry-Mechanismus (3× mit Backoff)
- 18 REST-API-Endpunkte (Connection-CRUD, Equipment-CRUD, Referenz-Management, Browse, Sync)

---

## Technologie-Stack

### Backend
- **Python 3.14** mit Type Hinting (Pydantic v2)
- **ArangoDB 3.11+** (Multi-Model: Dokumente + Graph)
- **FastAPI** (REST API)
- **Celery** (Task Scheduling)
- **TimescaleDB 2.13+** (Zeitreihen für Sensorik)
- **Redis 7.2+** (Cache + Celery Broker)

### Frontend
- **React 18** + TypeScript (strict)
- **MUI** (Material UI)
- **Redux Toolkit** (State Management)
- **Vite** (Build Tool)

### Optionale Integrationen
- **Home Assistant** (MQTT/REST API)
- **InvenTree** (Inventar & Verbrauchsmaterial, REST-API)
- **ArangoDB Geo-Index** (GPS-Koordinaten)
- **Flutter 3.16+** (Mobile App)

---

## Nutzung für RAG-Systeme

### Optimierungen
- Konsistente YAML-Header für Metadaten-Extraktion
- Fachterminologie-Dichte für präzises Retrieval
- AQL-Beispiele für Graph-Query-Generation
- Python-Code-Snippets für Implementierungs-Guidance

### Empfohlene Embedding-Strategie
- **Chunk-Size:** 512-1024 Tokens
- **Overlap:** 128 Tokens
- **Metadaten-Filter:** Kategorie, Fokus, Technologie
- **Keywords pro Dokument:** 15-25 botanische/technische Begriffe

---

## Zusammenfassung

| Metrik | Wert |
|--------|------|
| Anforderungsdokumente | 16 (REQ-001 bis REQ-016) |
| Gesamt-Größe | ~611 KB (Markdown) |
| Graph-Nodes definiert | ~71 |
| Graph-Edges definiert | ~91 |
| Python-Code-Beispiele | ~66 |
| AQL-Queries | ~51 |
| Akzeptanzkriterien | ~195 |

**Vollständigkeits-Matrix:**
- ✅ REQ-001: Stammdatenverwaltung (35 KB)
- ✅ REQ-002: Standort & Substrat (41 KB)
- ✅ REQ-003: Phasensteuerung (21 KB)
- ✅ REQ-004: Dünge-Logik (57 KB)
- ✅ REQ-005: Hybrid-Sensorik (45 KB)
- ✅ REQ-006: Aufgabenplanung (45 KB)
- ✅ REQ-007: Erntemanagement (47 KB)
- ✅ REQ-008: Post-Harvest (45 KB)
- ✅ REQ-009: Dashboard (41 KB)
- ✅ REQ-010: IPM-System (16 KB)
- ✅ REQ-011: Externe Stammdatenanreicherung (31 KB)
- ✅ REQ-012: Stammdaten-Import (54 KB)
- ✅ REQ-013: Pflanzdurchlauf (54 KB)
- ✅ REQ-014: Tankmanagement (33 KB)
- ✅ REQ-015: Kalenderansicht & Kalender-Integration
- ✅ REQ-016: Optionale InvenTree-Integration

---

## Autoren & Lizenz
Datum: 26. Februar 2026
Version: 3.0

**Verwendung:** Diese Spezifikationen dienen als Grundlage für ein RAG-gestütztes Entwicklungssystem.
