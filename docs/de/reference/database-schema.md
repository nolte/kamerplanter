# Datenbankschema

Überblick über ArangoDB Collections und Graph-Kanten in Kamerplanter.

!!! note "Platzhalter"
    Dieser Inhalt wird in einem folgenden Schritt ausgearbeitet.

## Kerndaten

| Collection | Typ | Beschreibung |
|-----------|-----|-------------|
| `botanical_families` | Dokument | Botanische Familien |
| `species` | Dokument | Pflanzenarten |
| `cultivars` | Dokument | Sorten |
| `plant_instances` | Dokument | Einzelne Pflanzen |
| `planting_runs` | Dokument | Pflanzdurchläufe |
| `tanks` | Dokument | Wassertanks |
| `locations` | Dokument | Standorte |

## Graph-Kanten (Auswahl)

| Edge Collection | Von | Nach | Bedeutung |
|----------------|-----|------|----------|
| `belongs_to_family` | species | botanical_families | Art → Familie |
| `has_cultivar` | species | cultivars | Art → Sorte |
| `compatible_with` | species | species | Mischkultur-Kompatibilität |
| `descended_from` | cultivars | cultivars | Genetische Herkunft |
| `CONTAINS` | locations | locations | Standort-Hierarchie |
