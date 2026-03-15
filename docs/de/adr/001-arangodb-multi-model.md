# ADR-001: ArangoDB als Multi-Modell-Datenbank

**Status:** Akzeptiert
**Datum:** 2026-01-15
**Entscheider:** Kamerplanter Development Team

## Kontext

Kamerplanter verwaltet sowohl strukturierte Entitätsdaten (Pflanzen, Nährstoffpläne, Aufgaben) als auch komplexe Graphrelationen (Begleittpflanzen-Kompatibilität, genetische Herkunft, Fruchtfolge). Es wurde eine Datenbank benötigt, die beide Anforderungen erfüllt ohne zwei separate Systeme zu betreiben.

## Entscheidung

ArangoDB 3.11+ wird als primäre Datenbank verwendet. Es unterstützt nativ Dokument-Speicherung und Graph-Traversals in einer einzigen Abfragesprache (AQL — ArangoDB Query Language).

## Begründung

### Bewertete Alternativen

| Kriterium | PostgreSQL + pgvector | Neo4j | ArangoDB |
|-----------|----------------------|-------|----------|
| Dokumentenspeicherung | Gut (JSONB) | Schlecht (Properties only) | Sehr gut |
| Graph-Traversal | Mittel (rekursive CTEs) | Sehr gut (Cypher) | Sehr gut (AQL) |
| Betriebskomplexität | Niedrig | Hoch (Enterprise-Kosten) | Mittel |
| Python-Client | Sehr gut (psycopg3) | Gut | Gut (python-arango) |
| Lizenz | PostgreSQL (open) | Community/Enterprise | Apache 2.0 |

ArangoDB bietet die beste Balance aus Dokumentenspeicherung und nativer Graph-Unterstützung ohne Enterprise-Lizenzkosten.

## Konsequenzen

### Positiv
- Eine Datenbank für alle Datentypen
- Native AQL-Graph-Traversals für Begleittflanzengraph und Herkunftsbaum
- Named Graph `kamerplanter_graph` als zentrale Abstraktionsebene

### Negativ
- AQL ist weniger verbreitet als SQL oder Cypher — geringerer Talent-Pool
- TimescaleDB wird zusätzlich für Zeitreihen-Sensordaten benötigt

### Risiken
- ArangoDB Community Edition hat Einschränkungen bei Cluster-Features — für Single-Node-Betrieb ausreichend

## Referenzen

- [ArangoDB Dokumentation](https://docs.arangodb.com/)
- NFR-001: 5-Schichten-Architektur
