---

ID: NFR-016
Titel: Datenbank-Migrationsstrategie — Versionierung, Tracking, Fehler-Isolation
Kategorie: Betrieb / Datenlebenszyklus Unterkategorie: Schema- & Daten-Migrationen, Seeds, Startup-Resilience Fokus: Beides (Zierpflanze & Nutzpflanze)
Technologie: Python, ArangoDB, AQL, FastAPI, Kubernetes
Status: Genehmigt
Priorität: Hoch
Version: 1.0
Autor: nolte
Datum: 2026-07-04
Tags: [migration, seed, schema-migration, versioning, idempotency, startup-resilience, arangodb]
Abhängigkeiten: [NFR-001, NFR-002, NFR-007, ADR-001, ADR-005]
Betroffene Module: [backend/app/migrations, backend/app/main]
---

# NFR-016: Datenbank-Migrationsstrategie

## Abgrenzung zu bestehenden Specs

| Quelle | Fokus | Definiert |
|---|---|---|
| ADR-001 | ArangoDB als schemalose Primär-DB | **Persistenz-Technologie** |
| docs/adr/005 | YAML-Seed-Jobs beim Startup | **Idempotente Referenzdaten** |
| ADR-005 | Versioniertes Migrations-Framework | **Entscheidung & Architektur** |
| **NFR-016 (dieses Dokument)** | Verbindliche Regeln für Migrationen & Seeds | **Was gelten MUSS** |

NFR-016 macht die in ADR-005 getroffene Entscheidung **normativ**: Es legt fest,
welche Eigenschaften Migrationen und Seeds erfüllen müssen, damit der Startup
robust, reproduzierbar und betriebssicher ist.

---

## 1. Motivation

Am 2026-07-04 crashte der Backend-Pod zweimal in Folge beim Startup, weil je ein
einzelner Migrations-/Seed-Schritt eine Exception warf und — mangels
Fehler-Isolation — den **gesamten** Startup mitriss (`Application startup failed.
Exiting.`, Pod dauerhaft `0/1`). Ursache #1 war ein seit Issue #306 abgeschaffter
Enum-Wert (`harvest`), für den **keine Daten-Migration** existierte; die
Seed-Leselogik validierte die Alt-Dokumente strikt und brach ab, **bevor** sie sie
hätte reparieren können (Henne-Ei). Ohne Tracking, Versionierung und
Fehler-Isolation sind solche Ausfälle systemisch, nicht zufällig.

## 2. Begriffsdefinitionen

- **Migration:** Einmalige Transformation **bestehender** Daten oder Strukturen.
  Läuft **genau einmal** pro Datenbank, versioniert und in `schema_migrations`
  getrackt.
- **Seed:** Idempotenter Upsert von **Referenzdaten** (typischerweise YAML → DB).
  Läuft bei **jedem** Startup und spiegelt stets den aktuellen Quelldatenstand.
- **Baseline:** Die No-op-Migration `v0001`, die den Stand „vor Einführung des
  Frameworks" markiert.

## 3. Verbindliche Anforderungen

### 3.1 Migrationen

- **M-1 Versionierung:** Jede Migration trägt eine nullgepolsterte, streng monotone
  Version (`vNNNN_<slug>.py`). Die History ist **strikt linear**; Lücken vor dem
  Head sind ein Fehler.
- **M-2 Tracking:** Angewandte Migrationen werden in der ArangoDB-Collection
  `schema_migrations` mit `version`, `name`, `checksum`, `applied_at`,
  `duration_ms`, `status` festgehalten. Bereits angewandte Versionen werden nicht
  erneut ausgeführt.
- **M-3 Idempotenz:** Jede Migration MUSS idempotent geschrieben sein (Re-Run =
  No-op), damit der Baseline-Übergang und Wiederholungen sicher sind.
- **M-4 Fehler-Policy — fatal:** Schlägt eine ausstehende Migration fehl, bricht
  der Startup kontrolliert und mit klarer Log-Ausgabe ab. Migrationen dürfen NICHT
  stillschweigend übersprungen werden.
- **M-5 Dry-Run:** Jede Migration MUSS `--dry-run` unterstützen (Report berechnen,
  nichts schreiben) — Pflicht für kontrollierte Prod-Ausführung.
- **M-6 Reversibilität ehrlich deklarieren:** `down()` wird unterstützt;
  nicht-umkehrbare Transformationen setzen `reversible = False` und werfen
  `IrreversibleMigrationError` statt einer scheinbaren Umkehr.
- **M-7 Checksum-Unveränderlichkeit:** Der Quelltext einer angewandten Migration
  wird nicht mehr geändert; Drift wird beim Start als Warnung geloggt. Korrekturen
  erfolgen als **neue** Migration.
- **M-8 Concurrency:** Bei mehreren Backend-Replicas MUSS ein Lock verhindern, dass
  Migrationen konkurrierend/doppelt laufen.
- **M-9 Pflicht bei Enum-/Schema-Rückbau:** Wird ein persistierter Enum-Wert oder
  ein Feld entfernt/umbenannt, MUSS in derselben Änderung eine Daten-Migration die
  Bestandsdokumente überführen. (Direkte Lehre aus Issue #306.)

### 3.2 Seeds

- **S-1 Idempotenz:** Seeds MÜSSEN idempotent sein (Upsert, kein Duplikat bei
  Re-Run).
- **S-2 Fehler-Isolation:** Referenzdaten-Seeds sind **non-fatal** — ein Fehler
  wird geloggt (`seed_failed`), der Startup fährt fort. Strukturell notwendige
  Seeds (z. B. Location-Types, Auth-Bootstrap) dürfen als `fatal=True` markiert
  werden.
- **S-3 Feld-Drift-Toleranz:** Seed-Loader überspringen unbekannte Quellfelder mit
  Warnung, statt die gesamte Datei zu verwerfen.
- **S-4 Registry:** Seeds werden über eine deklarative, geordnete Registry
  ausgeführt — nicht durch verstreute Inline-Aufrufe in `main.py`.

### 3.3 Ausführung & Ops

- **O-1 Startup-Reihenfolge:** Erst Migrationen (fatal), dann Seeds (isoliert).
- **O-2 CLI:** `python -m app.migrations {upgrade|downgrade|current|history|create}`
  MUSS existieren — für kontrollierte Ops und das Scaffolding neuer Migrationen.
- **O-3 Zielbild:** Migrationen SOLLEN mittelfristig als dediziertes Kubernetes-Job
  / Helm-Hook laufen (nicht in jedem App-Pod-Lifespan); der CLI-Entrypoint ist die
  Grundlage. Bis dahin schützt der Lock (M-8) den Startup-Pfad.

## 4. Akzeptanzkriterien

1. Eine fehlgeschlagene, non-fatale Seed-Datei bricht den Startup NICHT ab; die
   übrigen Seeds und die App starten normal.
2. Eine ausstehende Migration, die fehlschlägt, bricht den Startup mit klarer
   Fehlermeldung ab (fatal).
3. Nach erfolgreichem Startup listet `python -m app.migrations current` die höchste
   angewandte Version; `history` alle mit Zeitstempel.
4. Ein zweiter Startup wendet keine bereits getrackte Migration erneut an
   (Tracking greift).
5. Zwei parallel startende Backend-Pods führen jede Migration **genau einmal** aus
   (Lock greift).
6. Der Entfernungs-Fall aus Issue #306 ist durch `v0006_retire_harvest_phase`
   abgedeckt: Alt-`harvest`-Dokumente werden vor dem ersten Plan-Seed überführt.

## 5. Realisierung

Siehe ADR-005 §Realisierung (Framework, Versionen, Tests, Doku).
