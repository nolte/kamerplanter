# ADR-003: Sensor-Retention für Perennials — DSGVO-Speicherbegrenzung vs. fachlicher Saison-Vergleich

## Status

**Accepted** — *Entschieden: 2026-04-27, durch nolte*
*Erstellt: 2026-04-27*

## Context

NFR-011 R-14 (Sensordaten-Retention) und REQ-003 §1 (Dauerkulturen-Modus) verfolgen gegensätzliche Ziele:

```
NFR-011 R-14 (DSGVO-getrieben):
  Stufe 1: Rohdaten     →  90 Tage volle Auflösung
  Stufe 2: Stündlich    →  90d–2 Jahre
  Stufe 3: Täglich      →  2–5 Jahre
  Danach:               →  Hard-Delete

REQ-003 §1 (fachlich):
  „Saison-Vergleich: Ertrag und Performance über Jahre hinweg vergleichbar"
  → Ein 20-jähriger Apfelbaum braucht idealerweise 20 Saisons Daten
  → 5-Jahres-Grenze ist zu kurz für aussagekräftige Trendanalysen
```

### Warum die heutige `ClimateEvent`-Ausnahme nicht reicht

NFR-011 §2.2 hat bereits eine Ausnahme: **Klimatische Extremwert-Events** (Frost, Hitzewelle, Sturm) werden als `ClimateEvent`-Dokumente in ArangoDB dauerhaft archiviert. Das adressiert aber nur **Ausreißer**, nicht die normalen Wachstumsbedingungen:

```
Was die Ausnahme abdeckt:
  ✅ "Spätfrost am 12.5.2024 hat Apfelblüte beschädigt"
  ✅ "Hitzewelle 38°C über 5 Tage im Juli 2024"

Was sie NICHT abdeckt — aber Ertragsprognose braucht:
  ❌ Mittlere VPD-Kurve über die Vegetationsperiode
  ❌ DLI-Akkumulation pro Saison
  ❌ Durchschnittstemperatur in Blütephase
  ❌ Bewässerungs-Reaktion auf Bodenfeuchte-Trends
  ❌ Vergleich „Saison 2024 vs. Saison 2025 mittlere Bedingungen"
```

### Die Spannung: Sensordaten sind gestuft personenbezogen

NFR-011 §2.2 weist auf SEC-K-005 hin: Sensordaten **können** Rückschlüsse auf Anwesenheit erlauben.

```
Indoor-Sensoren (Wohnzimmer, Schlafzimmer):
  CO2-Kurve   → erkennt Anwesenheit, Schlaf, Aktivität
  Bewegung    → direkter Personenbezug
  Manuelle Overrides → wer war wann zuhause?
  → INDIREKT PERSONENBEZOGEN, DSGVO Art. 5 strikt anwendbar

Outdoor-Sensoren (Hochbeet im Garten, Apfelbaum):
  Temperatur, RH, Bodenfeuchte
  → Standort-bezogen, kein Personenbezug
  → DSGVO Art. 5(1)(e) Speicherbegrenzung greift nicht
    (kein personenbezogenes Datum mehr)
```

Die heutige R-14 behandelt **alle** Sensordaten gleich — auch Outdoor-Wetterdaten am Apfelbaum, obwohl die rein agro-meteorologisch sind.

### Compliance-Constraints

- **DSGVO Art. 5(1)(e)** Speicherbegrenzung — nur **personenbezogene** Daten
- **DSGVO Art. 5(1)(c)** Datenminimierung — auch nicht-personenbezogene Aggregate sollten zweckgebunden sein
- **DSFA-Schwelle** (Art. 35): Sensor-basiertes Anwesenheitsmuster KÖNNTE eine DSFA auslösen, je nach Granularität
- **NFR-011 §1.2** zitiert Art. 5(1)(e) als Grundlage

### Betroffene Specs

- **NFR-011** §2.2 R-14, §4 RetentionSettings
- **REQ-003** §2 SeasonalCycle, §1 Dauerkulturen-Modus
- **REQ-002** Standortverwaltung — `location_type` (Indoor/Outdoor-Klassifizierung)
- **REQ-005** Sensor-Architektur

## Decision

**Hybrid-Ansatz: Saison-Aggregation als Default + Opt-in Roh-Retention für Outdoor-Standorte.**

Drei verschränkte Mechanismen:

### A — SeasonalCycle als Aggregat-Speicher

Der bestehende `seasonal_cycles`-Knoten (REQ-003 §2) wird um **Sensor-Aggregat-Felder** pro Saison erweitert. Diese Aggregate werden **dauerhaft** aufbewahrt — sie enthalten keine Rohdaten und keine Anwesenheitsmuster, sondern saisonale Kennzahlen für die Trendanalyse.

```python
class SeasonalCycle(BaseModel):
    plant_instance_key: str
    season_year: int
    season_number: int
    # ... bestehende Felder ...

    # NEU (ADR-003): Sensor-Aggregate pro Saison
    sensor_aggregates: dict = Field(default_factory=dict)
    # Format:
    # {
    #   "temperature_c":    {"avg": 18.4, "min": -3.2, "max": 35.7, "p10": 12.1, "p90": 27.3, "samples": 8760},
    #   "humidity_rh":      {"avg": 65.2, ...},
    #   "vpd_kpa":          {"avg": 0.95, "min": 0.4, "max": 2.1, "samples": 8760},
    #   "soil_moisture_pct":{"avg": 32.5, ...},
    #   "dli_mol_m2":       {"sum": 5840.0, "avg_per_day": 16.0, "samples": 365}
    # }

    aggregate_computed_at: Optional[datetime] = None
    aggregate_source_retention_horizon: str = "5y"  # Bis wann waren Rohdaten verfügbar
```

Die Aggregate werden als Celery-Task **am Ende jeder Saison** berechnet (Trigger: SeasonalCycle.ended_at gesetzt) aus den dann noch verfügbaren Sensor-Daten (Stufe 2 oder 3). Ergebnis ist deterministisch — derselbe Datensatz erzeugt immer dieselben Aggregate.

**Retention der Aggregate:** Dauerhaft, **solange die zugehörige PlantInstance existiert**. Bei User-Löschung werden Aggregate anonymisiert (siehe Subproblem C).

### B — Standort-Klassifizierung (`location_type`)

REQ-002 hat bereits `location_type` (Indoor/Outdoor/Greenhouse/etc.). Die Sensor-Retention nutzt diese Klassifizierung als **DSGVO-Risikogruppe**:

```python
class LocationDataClassification(str, Enum):
    """ADR-003: Risikogruppe für Sensor-Daten an einem Standort."""

    OUTDOOR_OPEN = "outdoor_open"       # Garten, Hochbeet, Freiland — kein Personenbezug
    GREENHOUSE = "greenhouse"           # Gewächshaus — meist arbeitsbezogen, kaum Anwesenheit
    INDOOR_PUBLIC = "indoor_public"     # Verkaufsraum, Kindergarten — Mehrpersonen, anonym
    INDOOR_PRIVATE = "indoor_private"   # Wohnzimmer, Schlafzimmer — Anwesenheits-erkennend
    UNKNOWN = "unknown"                 # Default — zur Sicherheit als private behandelt
```

Auf Location wird ein neues Feld `data_classification` ergänzt. Default für neue Locations: `UNKNOWN` (= maximaler Schutz). Tenant-Admin kann es bewusst auf `OUTDOOR_OPEN` setzen, was die Retention verlängert.

### C — Differenzierte Roh-Retention nach Klassifizierung

```
data_classification         Stufe 1 (Roh)    Stufe 2 (Stunde)   Stufe 3 (Tag)   Aggregate (Saison)
────────────────────────────────────────────────────────────────────────────────────────────────
INDOOR_PRIVATE (Default)    90d              2y                  5y              ∞ (anonymisiert)
INDOOR_PUBLIC               90d              2y                  5y              ∞ (anonymisiert)
GREENHOUSE                  90d              2y                  10y (opt-in)    ∞ (anonymisiert)
OUTDOOR_OPEN                90d              5y                  20y (opt-in)    ∞
UNKNOWN                     wie INDOOR_PRIVATE                   (Maximum-Schutz)
```

**Verlängerte Retention ist Opt-in:** Tenant-Admin muss explizit zustimmen, dass für `OUTDOOR_OPEN` und `GREENHOUSE` längere Stufe-3-Aufbewahrung aktiviert wird. Default ist die DSGVO-konservative 5-Jahres-Grenze.

Bei `OUTDOOR_OPEN` ist die Verlängerung DSGVO-rechtlich unkritisch — keine personenbezogenen Daten. Trotzdem opt-in, weil:
- Verhindert versehentliche Aktivierung in falsch klassifizierten Standorten
- Macht Tenant bewusst, was er an Daten hortet
- Audit-Trail: wer hat wann die Verlängerung aktiviert

Begründung der Stufenwerte:
- `OUTDOOR_OPEN` Stufe 2 = 5 Jahre statt 2: Stundenmittelwerte erlauben mikroklima-Analysen, sind aber aggregiert genug, um keine Anwesenheits-Indikatoren zu enthalten
- `OUTDOOR_OPEN` Stufe 3 = 20 Jahre: Ausreichend für die Lebensdauer einer typischen Obstanlage
- `GREENHOUSE` zwischen Privat und Outdoor: Personen sind anwesend (arbeitend), aber unregelmäßig — verlängerte Stufe 3 ok mit Opt-in

## Alternatives Considered

| Alt | Strategie | Verdikt |
|-----|-----------|---------|
| **A.1** Hybrid (SeasonalCycle-Aggregate + differenzierte Retention) — Empfehlung | Beste DSGVO-Konformität + fachliche Anforderung erfüllt | ✅ Gewählt |
| A.2 | Nur SeasonalCycle-Aggregate, alle Rohdaten weiterhin nach 5J löschen | Einfacher, aber „warum Tag-für-Tag-Daten löschen, wenn Outdoor und unkritisch?" — Datenverlust vermeidbar |
| A.3 | Globale Verlängerung Stufe 3 auf 10 Jahre | DSGVO-Verstoß für Indoor-Sensoren mit Anwesenheits-Indikatoren |
| A.4 | Tenant-konfigurierbar pro Standort, ohne feste Klassifizierung | Zu komplex, Operator kann die Risikobewertung schwer machen — Klassifizierung ist eine bewusste Entscheidungs-Hilfe |
| A.5 | Klimadaten extern beziehen (DWD/OpenWeatherMap) statt selbst speichern | Fachliche Genauigkeit leidet — Mikroklima am Apfelbaum ≠ DWD-Wetterstation 5km entfernt |
| A.6 | Sensor-Daten generell anonymisieren (Hash auf location_key) statt löschen | Pseudonymisierung statt Löschung wäre DSGVO-konform, aber Storage wächst unbegrenzt — Skalierungsproblem |

## Consequences

### Positive

- **DSGVO-konform** für alle Standorttypen — Indoor bleibt bei harter 5J-Grenze, kein Compliance-Risiko
- **Fachlich nutzbar:** SeasonalCycle-Aggregate lösen das Saison-Vergleich-Problem **ohne** Roh-Retention zu verlängern. Selbst Indoor-Pflanzen profitieren.
- **Outdoor-Apfelbaum-Use-Case:** Mit Opt-in 20-Jahre-Stufe-3 sind echte mehrjährige Trendanalysen möglich
- **Klare Verantwortung:** Tenant-Admin entscheidet bewusst, welche Klassifizierung für welchen Standort gilt
- **Audit-tauglich:** `data_classification`-Wechsel werden protokolliert (Folgemaßnahme)

### Negative / Risiken

- **Komplexität wächst:** Vier Retention-Klassen statt einer — Code-Pfade in TimescaleDB-Retention-Policy und Continuous Aggregates
- **Fehlerhafte Klassifizierung:** Wenn Anwender einen Indoor-Sensor als `OUTDOOR_OPEN` markiert (versehentlich oder bewusst), umgeht er die DSGVO-Schutzfrist. Mitigation: Default `UNKNOWN`, UI-Warnung beim Wechsel auf `OUTDOOR_OPEN`, Audit-Log
- **Aggregate-Re-Computation:** Wenn jemand einen historischen Sensor-Eintrag korrigiert (selten), müssen abhängige Saison-Aggregate neu berechnet werden — Konsistenz-Problem
- **DSFA-Frage offen:** CO2 + Bewegung + manuelle Overrides als Indoor-Sensoren könnten DSFA-pflichtig sein, unabhängig von der Retention. Open Question

### Folgemaßnahmen

| Spec | Änderung |
|------|----------|
| **NFR-011** §2.2 | R-14 differenziert nach `data_classification`; Stufe 3 wird konfigurierbar pro Klassifikation |
| **NFR-011** §4 | Neue Settings: `SENSOR_RETENTION_OUTDOOR_DAILY_YEARS=20`, `SENSOR_RETENTION_GREENHOUSE_DAILY_YEARS=10`, Default-Verhalten ohne Opt-in: 5y |
| **REQ-002** Location-Modell | `data_classification: LocationDataClassification`-Feld ergänzen, Default `UNKNOWN` |
| **REQ-002** UI | Standort-Bearbeitungs-Dialog zeigt Klassifizierungs-Auswahl mit DSGVO-Hinweis-Tooltip |
| **REQ-003** §2 SeasonalCycle | `sensor_aggregates`-Feld ergänzen + Service-Methode `compute_seasonal_aggregates(season_key)` |
| **REQ-003** §3 | Celery-Task `compute_seasonal_aggregates_task` triggert beim `season.ended_at`-Set |
| **REQ-005** Sensor-Architektur | TimescaleDB-Retention-Policy berücksichtigt `data_classification` der zugehörigen Location |
| **REQ-025** | Bei User-Löschung: SeasonalCycle-Aggregate bleiben, aber `aggregate_computed_by` wird auf `null` anonymisiert (analog R-22) |
| **NFR-011** R-19a (NEU) | Anonymisierungs-Regel für `seasonal_cycles.aggregate_computed_by` bei User-Löschung |

## References

- **Widerspruchsbericht:** `spec/analysis/requirements-contradictions-2026-04-26.md` — W-014
- **NFR-011** §2.2 R-14, §4 RetentionSettings — Sensor-Retention-Stufen
- **NFR-011 §1.2** — DSGVO Art. 5(1)(e) als Grundlage
- **REQ-003** §1 Business Case (Dauerkulturen-Modus, Saison-Vergleich)
- **REQ-003** §2 SeasonalCycle-Modell
- **REQ-002** Location/Standort-Verwaltung
- **REQ-005** Sensor-Architektur
- **DSGVO** Art. 5 (1) (c) Datenminimierung, (e) Speicherbegrenzung
- **DSGVO** Art. 35 DSFA-Schwelle (Open Question 3)
- **SEC-K-005** IT-Security-Review zu Sensor-PII-Risiko

## Resolved Decisions (Workshop 2026-04-27)

| # | Frage | Entscheidung | Begründung |
|---|-------|--------------|-----------|
| 1 | Aggregat-Felder pro Saison | **avg/min/max/p10/p90 für `temperature`, `humidity`, `vpd`, `soil_moisture`; sum + avg_per_day für `dli`**; anpassbar via optionalem `aggregate_config` auf SeasonalCycle | Deckt typische Trendanalysen ab; Quartile (p10/p90) zeigen Verteilung statt nur Extreme; `dli` braucht andere Aggregation (kumulativ statt Durchschnitt) |
| 2 | `UNKNOWN`-Default | **mappt auf `INDOOR_PRIVATE`** | DSGVO-konservativ; Anwender muss bewusst auf `OUTDOOR_OPEN` wechseln |
| 3 | DSFA für `INDOOR_PRIVATE` | **Tenant-spezifische Bewertung; UI-Hinweis-Banner bei `INDOOR_PRIVATE` mit Link zu DSFA-Hilfeseite** | Hobby-Einzelnutzer: Haushaltsausnahme Art. 2(2)(c); Gemeinschaftsgarten/kommerziell: DSFA ggf. erforderlich |
| 4 | Aggregate-Update bei Sensor-Korrektur | **Lazy: Re-Computation bei Drift-Detection** (beim Lesezugriff `aggregate_computed_at` vs. `last_modified_in_window` prüfen) | Konsistenz bei seltenen Korrekturen ohne unnötige Recomputation-Last |
| 5 | Klassifizierungs-Wechsel | **Forward-only** — bestehende Daten behalten Schutzklasse, neue Werte folgen neuer Klassifizierung | Verhindert nachträgliche Schutz-Senkung durch Klassifizierungs-Manipulation |
| 6 | Greenhouse als eigene Klasse | **Ja, eigene Klasse** | Mikroklima + Anwesenheits-Pattern deutlich anders als pure Indoor |
