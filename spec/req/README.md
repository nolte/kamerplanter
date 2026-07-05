# Kamerplanter - Anforderungsspezifikationen

## Übersicht
Dieses Verzeichnis enthält **18 vollständig ausgearbeitete Anforderungsdokumente** für das Kamerplanter-System — eine Agrotech-Plattform für Pflanzen-Lebenszyklusmanagement (Cannabis, Gemüse, Kräuter) mit Python/FastAPI-Backend und ArangoDB Graph-Datenbank.

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

### 📍 REQ-002: Standortverwaltung
**Fokus:** Räumliche Verwaltung, Fruchtfolge-Engine, Hydro-Monitoring
- Rekursive Hierarchie: Site → Location (beliebig tief) → Slot
- Indoor (Growzelte) + Outdoor (Beete) + Hydro-Systeme
- LocationType-Stammdaten (CRUD, 10 Seed-Einträge)
- ArangoDB Geo-Indizes für GPS-basierte Standorte

**Highlights:**
- Hydro-spezifisches Monitoring (NFT, DWC, Aeroponik)
- Nachbarschafts-Graph für Mischkultur-Analysen
- Lichtzeiten-Verwaltung mit SunCalculator

### 🪴 REQ-019: Substratverwaltung
**Fokus:** Substrat-Definitionen, Chargen-Tracking, Wiederverwendung
- Substrat-Typen: Erde, Coco, Steinwolle, Living Soil, Hydro
- Batch-Tracking mit pH/EC-Verlauf über Anbauzyklen
- Wiederverwendbarkeits-Check und Aufbereitungs-Anleitungen

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

### 🌿 REQ-017: Vermehrungsmanagement
**Fokus:** Stecklinge, Aussaat, Veredelung, Mutterpflanzen, Genetische Abstammung
- Mutterpflanzen-Verwaltung mit Gesundheitsbewertung und Retirement-Empfehlung
- 6 Vermehrungsmethoden: Steckling, Aussaat, Teilung, Absenker, Veredelung, Gewebekultur
- Wiederverwendbare Bewurzelungsprotokolle mit Erfolgsraten-Tracking
- Genetischer Abstammungsgraph (Lineage) über beliebig viele Generationen
- Veredelungs-Kompatibilitätsprüfung auf Gattungs-/Familienebene

**Highlights:**
- PropagationBatch → PlantingRun-Übergabe
- Phänotyp-Dokumentation für Selektion
- Generationswarnung bei genetischer Drift (>10 Klon-Generationen)

---

### ⚡ REQ-018: Umgebungssteuerung & Aktorik
**Fokus:** Aktive Steuerung (Licht, Klima, Bewässerung), Home Assistant, Automatisierungsregeln
- 11 Aktor-Typen: Licht, Abluft, Umluft, Heizung, Kühlung, Befeuchter, Entfeuchter, CO₂-Doser, Bewässerungsventil, Pumpe, Generic Switch
- Drei Protokolle: Home Assistant (REST API), MQTT (direkt), Manuell (Fallback-Tasks)
- Regelbasierte Steuerung mit Hysterese (Oszillationsschutz)
- Phasengebundene Profile mit graduellem Übergang (z.B. 18h→12h über 7 Tage)
- Prioritätssystem: Override > Safety > Rule > Schedule

**Highlights:**
- Home Assistant bidirektional (Service-Calls + State-Sync)
- Graceful Degradation: HA-Ausfall → automatische Fallback-Tasks (REQ-006)
- Energieverbrauch-Schätzung pro Location
- Compound-Regeln (AND/OR) und Dry-Run-Tests

---

### 🌿 REQ-028: Mischkultur & Companion Planting
**Fokus:** Companion-Planting-Empfehlungen, Kompatibilitäts-Validierung, Mischkultur-Beratung
- Graph-basierte Empfehlungs-Engine (Species-Level + Family-Level Fallback mit 20% Abschlag)
- 7 Effekt-Typen: pest_repellent, growth_enhancer, soil_improver, nutrient_fixer, pollinator_attractor, space_optimizer, general
- Seed-Daten: 25+ compatible_with-Paare, 15+ incompatible_with-Paare aus 185 plant-info Dokumenten
- Run-Kompatibilitäts-Validierung (N×N/2 Paarprüfung) + Slot-Nachbarschafts-Check

**Highlights:**
- 4-Schritt-Algorithmus: Species-Level → Family-Fallback → Standort/Saison-Filter → Effekt-Prioritäts-Sortierung
- Mischkultur-Partner-Panel mit Quick-Add im PlantingRun-Create-Dialog
- Expertise-Level-Anpassung (Beginner: Top-3, Expert: alle mit Scores)
- Konsolidiert aus REQ-001 (Datenmodell), REQ-013 (Runs), Outdoor-Garden-Planner Review G-008

---

### 📷 REQ-034: Pflanzenfoto-Galerie
**Fokus:** Eigene Fotos pro Pflanzeninstanz, Galerie-Ansicht, optionaler DINOv2-Datenbeitrag
- Foto-Upload via Webcam / Smartphone-Kamera / Datei-Upload (Wiederverwendung der Bilderkennungs-UX, REQ-029)
- Galerie-Tab auf der Pflanzeninstanz-Detailseite: Thumbnail-Grid, Lightbox, Titelbild, Loeschen
- Aufbauend auf dem Storage-Fundament NFR-013 (neue `category = plant`); Frontend kennt nur `attachment_id` + Stable URI
- Optionaler, einwilligungs- und kuratierungs-gesteuerter Rueckfluss eigener Fotos in den DINOv2-Referenz-Index (REQ-029-A, `source = user_contributed`, no-op bis Bilderkennung-Phase 2)

**Highlights:**
- DSGVO-Klassifizierung als `user_diary_attachments` (Anonymisierung statt Hard-Delete), EXIF-Strip beim Upload
- `PlantInstance.photo_refs` + `cover_photo_ref` (attachment_id-Listen statt roher Storage-URLs)
- Verankert auf NFR-013 v1.2, REQ-013, REQ-025 v1.2, REQ-024

---

## 🌍 Integrations-Anforderungen aus awesome-agriculture (REQ-037 – REQ-041)

Diese fünf Dokumente leiten konkrete Integrationen ausgewählter Open-Source-Projekte aus
[awesome-agriculture](https://github.com/brycejohnston/awesome-agriculture) ab. Jedes erweitert
bestehende REQs und folgt dem Standard-Template (Business Case, ArangoDB-Modell, Python-Umsetzung,
Frontend, Lizenz/Deployment, Abhängigkeiten, Akzeptanzkriterien). Auswahlkriterium: schließt eine
reale fachliche Lücke **und** ist stack-kompatibel (Python/Self-Hosted, lizenzverträglich).
Lizenz- & Nutzungsentscheidungen (G1–G4): siehe `spec/analysis/awesome-agriculture-lizenz-und-nutzungsanalyse.md`.

### 💧 REQ-037: Evapotranspiration & bedarfsgerechte Bewässerung
**Projekt:** PyETo → Fork `aquacropeto` (PyPI, BSD-3) · **Erweitert:** REQ-004, REQ-005, REQ-022
- ET₀ → ETc = ET₀ × Kc → Netto-Gießbedarf = ETc − effektiver Niederschlag (gedeckelt durch Substrat-WHC)
- Engine `EvapotranspirationCalculator`, Collection `irrigation_demands`, `crop_coefficient_kc`
- **Caveat:** nur Outdoor (Indoor bleibt VPD-/intervallbasiert); 🔴 pyTSEB (GPL-3.0) als Dependency ausgeschlossen

### 🔬 REQ-038: CV-gestützte Pflanzendiagnose
**Projekte:** PlantCV (MPL-2.0) + PlantDoc (CC-BY-4.0) · **Erweitert:** REQ-010, REQ-029/-A, REQ-036, REQ-007
- Self-hosted ONNX-Krankheitsklassifikator + PlantCV-Phänotyp-Pipeline; CV-Treffer → IPM-Treatment-**Vorschlag** (Karenz-Gate bleibt)
- **Caveat (G1):** PlantVillage fallengelassen (Lizenz ungeklärt) → PlantDoc + Eigendaten; Domänen-Gap → Fine-Tuning, kein fertiger Klassifikator; immer „nur Hypothese"-Disclaimer

### 🗺️ REQ-039: Klimazonen- & Winterhärte-Geodaten
**Projekt:** frostline-Schema (MIT) + DWD/Open-Meteo-Daten · **Erweitert:** REQ-001, REQ-002, REQ-022, REQ-005, REQ-015-A
- `HardinessZoneResolver` leitet Zone aus Standort ab → automatisiert Winterhärte-Ampel + Frost-Defaults
- **Caveat:** USDA/PHZM-Daten proprietär/US-only (nicht eingecheckt); DACH-Zone aus DWD (GeoNutzV) + Open-Meteo (CC-BY-4.0)

### 📚 REQ-040: Wissensbasis-Enrichment (OpenFarm & Growstuff) — optional
**Projekte:** OpenFarm (CC0, Server tot → nur Dump) + Growstuff (CC-BY-SA, nur Mapping-Idee) · **Erweitert:** REQ-011, REQ-028, REQ-001, REQ-025
- **G3:** OpenFarm nur als einmaliger statischer CC0-Dump (kein Live-Adapter); Companion-Import in REQ-028-Graph
- **Caveat (G2):** Growstuff-Daten CC-BY-SA → kein Wertimport (Wissensbasis bleibt SA-frei, kein REQ-032-Konflikt)

### 🛰️ REQ-041: Agroklimatologie-Wetterquelle (NASA POWER)
**Projekt:** NASA POWER (CC-BY-4.0, keyless; inspiriert von `agroclimatology`) · **Erweitert:** REQ-005, REQ-037, REQ-039, REQ-002
- 5. Wetter-Adapter `NasaPowerWeatherAdapter`; liefert Solarstrahlung (ET₀-Input REQ-037) + Klimanormale (`ClimateNormal`, REQ-039)
- **Caveat:** Reanalyse/Vergangenheit (keine Frühwarnung) → ergänzt DWD/Open-Meteo, ersetzt sie nicht; Ruby-Client nicht nutzbar

---

## 🌤️ REQ-046: Wetterdienst-Datenquellen & -Konfiguration
**Fokus:** Nutzerkonfigurierbare Wetterquellen je Standort — öffentlicher Dienst **vs.** Home-Assistant-Sensoren · **SSOT** der Wetter-Datenquellen-Schicht · **Erweitert:** REQ-005, REQ-002 · **Konsolidiert:** REQ-041, REQ-039
- Konsolidiert die zuvor über REQ-005/039/041 verstreute Wetter-Adapter-Schicht in **eine** Quelle der Wahrheit: `WeatherAdapter`-ABC, `WeatherAdapterRegistry`, `Site.weather_source_priority` und die konkreten öffentlichen Adapter (DWD / OpenWeatherMap / Open-Meteo) sind hier beheimatet. REQ-041 (`NasaPowerWeatherAdapter`) und REQ-039 (`*ClimateNormalAdapter`) **registrieren** ihre Spezial-Adapter in dieser Registry.
- **Kern-Mehrwert:** nutzerseitige Datenquellen-Wahl pro Standort — neuer `HomeAssistantWeatherAdapter` (native `weather.*`-Entität **oder** Einzel-Sensor-Mapping) plus priorisierbare Fallback-Kette (öffentlich ↔ HA), Konfigurations-UI und „Quelle testen"-Verbindungstest.
- Additive `:WeatherForecast`-Erweiterung (`data_kind`, `is_current_conditions`) + neuer `source`-Provenance-Wert `ha_weather` (Quality-Score 0.9); neue Collection `weather_source_configs` + Edge `has_weather_source_config`.

**Highlights:**
- HA bleibt **strikt optional** — alle Wetterfunktionen laufen mit rein öffentlichen Diensten (Open-Meteo, kein Key); Wetter gilt weiterhin nicht als „Smart-Home-Funktion".
- OpenWeatherMap-API-Key verschlüsselt via Fernet (REQ-023, `api_key_ref` statt Klartext); tenant-scoped Routen (REQ-024); SSRF-Schutz via `validate_ha_url`.
- Attributionspflichten (DWD GeoNutzV, Open-Meteo CC-BY-4.0) → NOTICE + UI.

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
| Anforderungsdokumente | 18 (REQ-001 bis REQ-018) |
| Gesamt-Größe | ~700 KB (Markdown) |
| Graph-Nodes definiert | ~80 |
| Graph-Edges definiert | ~110 |
| Python-Code-Beispiele | ~80 |
| AQL-Queries | ~62 |
| Akzeptanzkriterien | ~245 |

**Vollständigkeits-Matrix:**
- ✅ REQ-001: Stammdatenverwaltung (35 KB)
- ✅ REQ-002: Standortverwaltung
- ✅ REQ-019: Substratverwaltung
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
- ✅ REQ-017: Vermehrungsmanagement
- ✅ REQ-018: Umgebungssteuerung & Aktorik
- ✅ REQ-028: Mischkultur & Companion Planting
- ✅ REQ-034: Pflanzenfoto-Galerie

---

## Autoren & Lizenz
Datum: 26. Februar 2026
Version: 3.0

**Verwendung:** Diese Spezifikationen dienen als Grundlage für ein RAG-gestütztes Entwicklungssystem.
