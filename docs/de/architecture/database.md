# Datenbankarchitektur

Kamerplanter nutzt polyglotte Persistenz: ArangoDB als primäre Multi-Modell-Datenbank, TimescaleDB für Zeitreihendaten und Redis als Cache und Celery-Broker.

!!! note "Platzhalter"
    Dieser Inhalt wird in einem folgenden Schritt ausgearbeitet.

## ArangoDB

- Named Graph: `kamerplanter_graph`
- 54 Dokument-Collections + 75 Edge-Collections
- Graph-Queries für Begleittflanzen, genetische Herkunft, Fruchtfolge

## TimescaleDB

- Sensordaten mit automatischem Downsampling
- 3 Stufen: 90 Tage roh → 2 Jahre stündlich → 5 Jahre täglich
