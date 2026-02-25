# Agrotech Software - Vollständige Anforderungsspezifikationen

## Übersicht
Dieses Paket enthält **10 vollständig ausgearbeitete Anforderungsdokumente** für die "Pflanzen Pflege & Ernte Helfer App" - ein umfassendes Agrotech-System mit Python-Backend und Neo4j Graph-Datenbank.

## Version 2.0 - Vollständige Spezifikationen

### Dokumenten-Struktur
Jedes Dokument folgt einer konsistenten, RAG-optimierten Struktur:
1. **YAML-Header** - Metadaten, Kategorisierung, Technologie-Stack
2. **Business Case** - User Stories, fachliche Beschreibung
3. **GraphDB-Modellierung** - Nodes, Edges, Cypher-Queries
4. **Technische Umsetzung** - Python-Code, Logik, Validierung (Type Hinting)
5. **Abhängigkeiten** - Querverweise zu anderen Modulen
6. **Akzeptanzkriterien** - Definition of Done, Testszenarien

---

## Enthaltene Dokumente

### 🌱 REQ-001: Stammdatenverwaltung (19 KB)
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

### 📍 REQ-002: Standort & Substrat (23 KB)
**Fokus:** Räumliche Verwaltung, Substrat-Management, Fruchtfolge-Engine
- Hierarchie: Site → Location → Slot
- Indoor (Growzelte) + Outdoor (Beete) + Hydro-Systeme
- Substrat-Recycling-Tracker mit Aufbereitungs-Anleitung
- PostGIS-Integration für GPS-basierte Standorte

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
- Lichtspe ktrum-Profile (Blue/Red/Far-Red Ratio)
- Stress-Phasen (Hardening, Drought-Stress)

---

### 💧 REQ-004: Dünge-Logik (6.5 KB)
**Fokus:** Multi-Part-Fertilizer, EC-Budget-Management
- Misch-Reihenfolge (verhindert Ausfällungen)
- EC-Netto-Rechner (Ziel-EC minus Basis-EC)
- Flushing-Protokolle (Substrat-spezifisch)
- Inkompatibilitäten-Check (CalMag + Sulfate)

**Highlights:**
- Step-by-Step Mixing Instructions
- Rezirkulations-Logik für Hydro-Systeme

---

### 🌡️ REQ-005: Hybrid-Sensorik (2.5 KB)
**Fokus:** Home Assistant Integration, Manual Fallback
- Dreistufiges Monitoring (Auto / Semi-Auto / Manuell)
- Sensor-Fallback-Manager (Auto-Task bei Ausfall >24h)
- Multi-Parameter-Tracking (Temp, RLF, pH, EC, PPFD, CO2)

**Highlights:**
- Graceful Degradation ohne Hardware
- Datenquellen-Kennzeichnung (Auto vs. Manual)

---

### ✅ REQ-006: Aufgabenplanung (3.4 KB)
**Fokus:** Workflow-Templates, HST-Validierung
- System-Templates vs. User-Blueprints
- Phase-Trigger + Zeit-Trigger + Dependency-Chains
- HST-Validator (verhindert Topping in Blüte)

**Highlights:**
- Foto-Upload bei kritischen Tasks
- Gantt-Chart für 4-Wochen-Vorschau

---

### 🌾 REQ-007: Erntemanagement (3.3 KB)
**Fokus:** Gattungsspezifische Reife-Indikatoren
- Factory-Pattern (TrichomeIndicator vs. FoliageIndicator)
- Flushing-Trigger (14 Tage vor Ernte)
- Batch-Tracking mit QR-Codes (Seed-to-Shelf)

**Highlights:**
- Quality-Scoring (Optik, Aroma, Potenz)
- Dunkelphase-Protokoll (48h vor Ernte)

---

### 🍷 REQ-008: Post-Harvest (3.0 KB)
**Fokus:** Trocknung, Curing, Lagerung
- Spezies-spezifische Protokolle (Cannabis, Zwiebel, Kräuter)
- Burping-Scheduler für Fermentierung
- Gewichts-Tracking (Ziel-Trockenheit)

**Highlights:**
- Schimmel-Prävention (RLF-Alerts)
- Schalenhärtung für Zwiebeln/Kürbis

---

### 📊 REQ-009: Dashboard (2.8 KB)
**Fokus:** Multi-Widget-Dashboard, Mobile-First
- Live-Grid aller Slots mit Phase-Indikatoren
- VPD-Ampel, Task-Queue, Alert-Center
- WebSocket-Updates für Real-Time-Daten

**Highlights:**
- QR-Scanner für Slot-Identifikation
- Offline-Modus mit Sync
- Dark-Mode (Growzelt-freundlich)

---

### 🔗 REQ-011: Externe Stammdatenanreicherung (18 KB)
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

## Technologie-Stack

### Backend
- **Python 3.11+** mit Type Hinting (Pydantic)
- **Neo4j 5.x** (Graph Database)
- **FastAPI** (REST API)
- **Celery** (Task Scheduling)
- **TimescaleDB** (Zeitreihen für Sensorik)

### Optionale Integrationen
- **Home Assistant** (MQTT/REST API)
- **PostGIS** (GPS-Koordinaten)
- **Computer Vision** (Schädlings-/Reife-Erkennung)

---

## Nutzung für RAG-Systeme

### Optimierungen
✅ Konsistente YAML-Header für Metadaten-Extraktion
✅ Fachterminologie-Dichte für präzises Retrieval
✅ Cypher-Beispiele für Graph-Query-Generation
✅ Python-Code-Snippets für Implementierungs-Guidance

### Empfohlene Embedding-Strategie
- **Chunk-Size:** 512-1024 Tokens
- **Overlap:** 128 Tokens
- **Metadaten-Filter:** Kategorie, Fokus, Technologie
- **Keywords pro Dokument:** 15-25 botanische/technische Begriffe

---

## Zusammenfassung

| Metrik | Wert |
|--------|------|
| Gesamt-Dokumente | 17 (11 unique requirements) |
| Gesamt-Größe | ~170 KB (Markdown) |
| Anforderungsdokumente | 11 (REQ-001 bis REQ-011) |
| Graph-Nodes definiert | ~60 |
| Graph-Edges definiert | ~80 |
| Python-Code-Beispiele | ~50 |
| Cypher-Queries | ~35 |
| Akzeptanzkriterien | ~150 |

**Vollständigkeits-Matrix:**
- ✅ REQ-001: Stammdatenverwaltung (19 KB)
- ✅ REQ-002: Standort & Substrat (23 KB)
- ✅ REQ-003: Phasensteuerung (21 KB)
- ✅ REQ-004: Dünge-Logik (35 KB)
- ✅ REQ-005: Hybrid-Sensorik (7 KB)
- ✅ REQ-006: Aufgabenplanung (7.5 KB)
- ✅ REQ-007: Erntemanagement (9 KB)
- ✅ REQ-008: Post-Harvest (8 KB)
- ✅ REQ-009: Dashboard (4.5 KB)
- ✅ REQ-010: IPM-System (16 KB)
- ✅ REQ-011: Externe Stammdatenanreicherung (18 KB)

---

## Autoren & Lizenz
Erstellt von: Claude (Anthropic)
Datum: 25. Februar 2026
Version: 2.0 (Erweitert)

**Verwendung:** Diese Spezifikationen dienen als Grundlage für ein RAG-gestütztes Entwicklungssystem.
