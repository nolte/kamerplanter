# Unveröffentlicht

Änderungen, die noch nicht in einem Release veröffentlicht wurden.

## Hinzugefügt

### Backend

- **REQ-001** Stammdatenverwaltung: Botanische Familien, Arten, Sorten, Lebenszyklen (ArangoDB)
- **REQ-002** Standortverwaltung: Sites, Locations (rekursive Hierarchie), Slots, Standorttypen
- **REQ-003** Phasensteuerung: Phasen-State-Machine (Keimung → Ernte), GDD/VPD/Photoperiod-Berechnung
- **REQ-004** Dünge-Logik: Düngemittel, Nährstoffpläne, Dosierungen, Mischsicherheit, Spülung, Runoff, EC-Budget, Wasserquelle/CalMag-Korrektur
- **REQ-006** Aufgabenplanung: Workflow-Templates, Tasks, Queue, Abhängigkeiten, HST-Validator
- **REQ-007** Erntemanagement: Ernte-Indikatoren, Beobachtungen, Batches, Qualitätsbewertung, Karenz-Gate
- **REQ-010** IPM-System: Schädlinge, Krankheiten, Behandlungen, Inspektionen, Resistenzmanager
- **REQ-011** Externe Stammdatenanreicherung: GBIF + Perenual Adapter, Enrichment-Engine, Celery-Tasks
- **REQ-012** Stammdaten-Import: CSV-Upload, Validierung, Vorschau, Bestätigung
- **REQ-013** Pflanzdurchlauf: PlantingRun, Batch-Operationen, State-Machine
- **REQ-014** Tankmanagement: Tanks, Tankzustände, Befüllungen, Wartung, Sensoren
- **REQ-015** Kalenderansicht: iCal-Feeds, Aggregation, Token-basierter Zugriff
- **REQ-019** Substratverwaltung: Erweiterte Substrattypen, Lebenszyklus-Manager, Wiederverwendung
- **REQ-020** Onboarding-Wizard: 5-Schritte-Assistent, 9 Starter-Kits, Erfahrungsstufen
- **REQ-022** Pflegeerinnerungen: 9 Pflegeprofile, FAMILY_CARE_MAP, adaptive Intervalle, Celery-Task
- **REQ-023** Authentifizierung: Lokale Konten (bcrypt), JWT (authlib), Refresh-Token-Rotation
- **REQ-024** Mandantenverwaltung: Tenant-Isolation, Mitgliedschaften, Einladungen, RBAC
- **REQ-028** Mischkultur & Companion Planting: Graph-basierte Kompatibilität
- **REQ-031** KI-Assistent: RAG-basierte Wissensdatenbank, LLM-Adapter (Anthropic/Ollama/OpenAI-kompatibel), Hybrid-Search

### Frontend

- Alle REQ-001 bis REQ-024 Frontend-Seiten implementiert
- **REQ-020** Onboarding-Wizard (5-Step MUI Stepper)
- **REQ-021** UI-Erfahrungsstufen: Feldkonfiguration, Navigation-Tiering, ExperienceLevelSwitcher
- **REQ-022** Pflege-Dashboard mit Urgency-Gruppierung
- Light/Dark Theme mit localStorage-Persistenz
- i18n Deutsch/Englisch (react-i18next)

### Infrastruktur

- MkDocs-Dokumentationsinfrastruktur mit Material Theme und DE/EN i18n (NFR-005)
- ADR-001 bis ADR-006: Architektur-Entscheidungen dokumentiert
- Skaffold-basierter Entwicklungsworkflow mit Kubernetes/Helm
- pgvector + Embedding-Service für RAG-Pipeline
- Knowledge-Container für YAML-basierte Wissensbasis
- GitHub Actions CI/CD (Docker Lint/Build, Skaffold Verify)

## In Entwicklung

- REQ-025 (Datenschutz/DSGVO): DSGVO Art. 15–21 Betroffenenrechte — spezifiziert, nicht implementiert
- REQ-027 (Light-Modus): Anonymer Zugang für lokale Instanzen — spezifiziert, nicht implementiert
- OAuth/OIDC: Vollständige Implementierung (Engine aktuell Stub)
- TimescaleDB-Integration: Repository und Migrations vorhanden, Feature-Flag gesteuert
