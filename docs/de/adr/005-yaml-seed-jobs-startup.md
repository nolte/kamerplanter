# ADR-005: YAML-basierte Seed-Jobs beim Application-Startup

**Status:** Akzeptiert
**Datum:** 2026-03-17
**Entscheider:** Kamerplanter Development Team

## Kontext

Kamerplanter benötigt umfangreiche Stammdaten (botanische Familien, Arten, Sorten, Düngemittel, Nährstoffpläne, Starter-Kits, Workflows, IPM-Daten, Aktivitäten etc.), die beim ersten Start und bei jedem Update konsistent in der Datenbank vorhanden sein müssen. Es musste entschieden werden:

1. **Datenformat**: In welchem Format werden Seed-Daten gepflegt?
2. **Ausführungszeitpunkt**: Wann und wie werden Seed-Jobs ausgeführt?
3. **Idempotenz**: Wie wird sichergestellt, dass wiederholtes Seeden keine Duplikate erzeugt?
4. **Anreicherungsprozess**: Wie werden neue Stammdaten hinzugefügt und bestehende erweitert?

## Entscheidung

### Deklarative YAML-Dateien als Single Source of Truth

Alle Seed-Daten liegen als YAML-Dateien in `src/backend/app/migrations/seed_data/`. YAML wurde gewählt, weil es human-readable, diff-freundlich (Git) und gut für hierarchische Daten geeignet ist. Jede Domäne hat eine eigene Datei (z.B. `species.yaml`, `plagron.yaml`, `starter_kits.yaml`).

### Startup-Seeding im FastAPI-Lifespan

Seed-Jobs werden beim Application-Startup im FastAPI-Lifespan-Hook (`main.py`) ausgeführt — nicht als separater CLI-Befehl oder Migrations-Schritt. Die Reihenfolge ist festgelegt:

1. `ensure_collections()` — Collections und Graph anlegen
2. `seed_location_types()` — Standort-Typen
3. `run_seed()` — Kern-Stammdaten (Familien, Arten, Sorten, IPM, Workflows)
4. `run_seed_starter_kits()` — Onboarding Starter-Kits
5. `run_seed_adventskalender()` — Saisonale Kits
6. `run_seed_plant_info()` / `run_seed_plant_info_extended()` — Erweiterte Pflanzendaten
7. `run_seed_plagron()` / `run_seed_gardol()` — Produktspezifische Düngepläne
8. `run_seed_nutrient_plans_outdoor()` — Freiland-Nährstoffpläne
9. `run_seed_activities()` — Aktivitätsdefinitionen
10. `run_seed_lifecycles_outdoor()` — Freiland-Lebenszyklen
11. Bedingt: `run_seed_light_mode()` — Nur wenn `KAMERPLANTER_MODE=light`

### Idempotenz durch Lookup-before-Create

Jeder Seed-Job prüft vor dem Anlegen, ob ein Datensatz bereits existiert (per `scientific_name`, `kit_id`, `product_name` o.ä.). Vier Muster werden eingesetzt:

- **Lookup + Create/Update**: Existenz-Check per eindeutigem Feld, dann Insert oder selektives Update definierter Felder
- **Selective Field Update**: Nur vordefinierte `seed_update_fields` werden überschrieben — benutzerdefinierte Änderungen an anderen Feldern bleiben erhalten
- **Backfill Missing**: Vorhandene Einträge zählen, fehlende ergänzen (z.B. Nährstoffplan-Phasen)
- **Exception-based**: Try/Catch für Graph-Edges, die bei Duplikat einen Fehler werfen

### Referenz-Auflösung über Zwischen-Maps

YAML-Dateien verwenden menschenlesbare Namen (`scientific_name`, `product_name`). Beim Seeden werden Zwischen-Maps aufgebaut (`name → _key`), die nachfolgende Schritte nutzen, um Referenzen aufzulösen (z.B. `species_names` in Starter-Kits → `species_keys`).

## Anreicherungsprozess für Seed-Daten

Der Prozess zum Hinzufügen oder Erweitern von Stammdaten folgt einem festen Schema:

### 1. YAML-Datei bearbeiten oder erstellen

Neue Daten werden in der passenden YAML-Datei in `seed_data/` ergänzt. Für neue Domänen wird eine neue Datei angelegt. Die Struktur orientiert sich an den Pydantic-Modellen in `domain/models/`.

### 2. Pydantic-Modell erweitern (falls nötig)

Wenn neue Felder benötigt werden, wird das Pydantic-Modell in `domain/models/` erweitert. Pydantic v2 übernimmt automatisch die Koerzierung von YAML-Strings in Enums, Listen etc.

### 3. Seed-Funktion anpassen

Die zugehörige Seed-Funktion in `migrations/seed_*.py` wird erweitert:

- Neue Felder in `seed_update_fields` aufnehmen (damit bestehende Datensätze aktualisiert werden)
- Neue Referenz-Auflösungen ergänzen (wenn das neue Feld auf andere Entitäten verweist)
- `yaml_loader.load_yaml()` nutzt denselben Mechanismus

### 4. Startup-Reihenfolge beachten

Wenn eine neue Seed-Datei angelegt wird, muss sie in `main.py` in der richtigen Reihenfolge eingehängt werden — Abhängigkeiten (z.B. Arten vor Starter-Kits) bestimmen die Position.

### 5. Anreicherung durch Agenten

Für die initiale Erstellung und Erweiterung von Pflanzendaten steht der `plant-info-document-generator`-Agent zur Verfügung. Dieser recherchiert botanische Daten und erzeugt strukturierte Dokumente, die anschließend in die YAML-Dateien überführt werden.

### 6. Testen

Ein Neustart der Applikation triggert automatisch alle Seed-Jobs. Strukturiertes Logging (`structlog`) protokolliert jede Aktion (created/updated/skipped) mit Identifiern.

## Begründung

### Warum YAML und nicht SQL-Migrations, JSON oder CSV?

- **SQL-Migrations** (Alembic-Stil) passen nicht zu ArangoDB als Dokumentendatenbank
- **JSON** ist weniger lesbar und schlechter diffbar als YAML bei tief verschachtelten Strukturen
- **CSV** kann keine hierarchischen Daten abbilden (verschachtelte Phasen, Dosierungslisten)
- **YAML** ist der natürliche Kompromiss: maschinenlesbar, human-readable, Git-diff-freundlich

### Warum Startup und nicht separate Migrations?

- **Einfachheit**: Kein separater Migrations-Befehl nötig, kein vergessener Schritt beim Deployment
- **Immer konsistent**: Jeder Startup garantiert vollständige Stammdaten
- **Idempotenz**: Wiederholtes Ausführen ist sicher — kein Zustandstracking (keine Migrations-Tabelle) nötig
- **Kubernetes-tauglich**: Pods können jederzeit neu starten; Seed-Jobs sind Teil des Startup-Lifecycle

### Warum kein Transaktions-Rollback?

- ArangoDB-Transaktionen über viele Collections sind komplex und limitiert
- Partielles Seeding ist akzeptabel: Idempotenz garantiert, dass ein Neustart den Rest nachträgt
- Der Startup blockiert bei Fehlern sowieso — ein unvollständiger Seed führt zu einem Pod-Restart

## Konsequenzen

### Positiv

- Stammdaten sind versioniert und reviewbar (Git)
- Einfacher Onboarding-Prozess: `git pull` + Neustart = aktuelle Daten
- Klare Trennung: YAML = Daten, Python = Orchestrierung
- Erweiterbar: Neues Seed-File + Einhängen in `main.py` genügt
- Observable: Structured Logging zeigt exakt, was geseeded wurde

### Negativ

- Startup-Zeit steigt mit wachsender Datenmenge (aktuell ~2-3s, akzeptabel)
- Kein atomares Rollback bei partiellem Fehler (durch Idempotenz kompensiert)
- Reihenfolge der Seed-Jobs muss manuell gepflegt werden (Abhängigkeitsgraph ist implizit)
- `seed_update_fields` muss bei neuen Feldern manuell erweitert werden — sonst werden bestehende Datensätze nicht aktualisiert
