# ADR-009: Versioniertes Datenbank-Migrations-Framework

**Status:** Akzeptiert
**Datum:** 2026-07-04
**Entscheider:** Kamerplanter Development Team

## Kontext

Datenbank-Seeds und einmalige Datenmigrationen wurden bisher als lose Sammlung von Funktionen in `app/migrations/` geführt und einzeln, hartkodiert und ungeordnet beim Application-Startup (`app/main.py`) aufgerufen — rund 18 Aufrufe hintereinander, die bei **jedem** Start erneut liefen. Dabei fehlten:

- **Tracking**, welche Migration auf einer Datenbank bereits ausgeführt wurde
- **Fehler-Isolation** — eine einzelne fehlschlagende Migration riss den gesamten Startup mit
- **Deklarierte Reihenfolge** — die Ausführungsreihenfolge steckte implizit in der Aufrufsequenz
- **Einheitliche Konventionen** für Report-Format und `--dry-run`
- Ein **Versionierungs-/Rollback-Konzept**, das anzeigt, welcher Datenbankstand gerade vorliegt

Diese Lücken führten am 2026-07-04 zu zwei aufeinanderfolgenden Backend-Crashes beim Startup: Einmal an einem seit Issue #306 abgeschafften Enum-Wert (`harvest`), für den keine Daten-Migration existierte, danach an einem blockierten Home-Assistant-Endpoint. In beiden Fällen riss ein einzelner Schritt den kompletten Startup mit.

**Randbedingungen:** ArangoDB ist als primäre Datenbank schemalos und AQL-basiert ([ADR-001](001-arangodb-multi-model.md)) — ein Migrations-Framework im Alembic-/SQL-Stil passt hier nicht. Das bestehende Muster „idempotente YAML-Seed-Jobs bei jedem Startup" (docs/adr/005, [YAML-basierte Seed-Jobs beim Startup](005-yaml-seed-jobs-startup.md)) bleibt gültig und wird von einmaligen Migrationen sauber abgegrenzt, nicht ersetzt. Mehrere Backend-Replicas in Produktion dürfen keine doppelte oder konkurrierende Migrationsausführung auslösen.

## Entscheidung

Wir führen ein **versioniertes, getracktes Migrations-Framework** ein und trennen begrifflich klar zwischen **Migrationen** (einmalig, versioniert) und **Seeds** (idempotent, immer laufend):

| | Migration | Seed |
|---|---|---|
| Zweck | Einmalige Transformation bestehender Daten/Struktur | Laden/Upsert von Referenzdaten |
| Ausführung | Genau einmal pro Datenbank (getrackt) | Bei jedem Startup (idempotent) |
| Fehler-Policy | **Fatal** — Startup bricht ab | Non-fatal — Startup läuft weiter |

**Kernbausteine:**

- **Tracking-Collection `schema_migrations`** — pro angewandter Version ein Dokument mit Versionsnummer, Name, Checksumme des `up()`-Quelltexts, Zeitstempel und Dauer. Weicht die Checksumme einer bereits angewandten Migration ab, wird das als Warnung geloggt — angewandte Migrationen gelten als unveränderlich, Korrekturen erfolgen als **neue** Migration.
- **Concurrency-Lock** — verhindert, dass mehrere gleichzeitig startende Backend-Replicas dieselbe Migration doppelt ausführen.
- **Strikt lineare Versionshistorie** — Migrationen sind fortlaufend nummeriert (`v0001`, `v0002`, …); Lücken vor dem aktuellen Stand sind ein Fehler, Out-of-Order-Anwendung ist ausgeschlossen.
- **Migration-Protokoll** mit `up()`/`down()`: Rollback wird unterstützt, wo sinnvoll; nicht umkehrbare Datentransformationen deklarieren das ehrlich (`reversible = False`) statt eine scheinbare Umkehr vorzutäuschen.
- **Baseline-Migration `v0001`** markiert den Datenbankstand vor Einführung des Frameworks; die fünf bestehenden Migrationen wurden als `v0002`–`v0006` gekapselt.
- **Startup-Reihenfolge:** Erst alle ausstehenden Migrationen (fatal bei Fehler), danach die Seed-Registry (isoliert, non-fatal für Referenzdaten).

### Datenbank-Migrationen — CLI-Referenz

Für kontrollierte Betriebs-Eingriffe und zum Anlegen neuer Migrationen existiert ein CLI-Einstiegspunkt:

```bash
python -m app.migrations upgrade      # alle ausstehenden Migrationen anwenden
python -m app.migrations downgrade    # auf eine Zielversion zurückrollen (nur reversible Migrationen)
python -m app.migrations current      # höchste angewandte Version anzeigen
python -m app.migrations history      # alle angewandten Migrationen mit Zeitstempel
python -m app.migrations create <slug> # neue vNNNN_<slug>.py aus Vorlage erzeugen
```

`upgrade` und `downgrade` unterstützen `--dry-run`, um den Plan zu berechnen, ohne zu schreiben — das ist Voraussetzung für kontrollierte Produktions-Ausführung. Der CLI-Befehl ändert nichts an der öffentlichen HTTP-API; er ist ein reines Ops-/Entwickler-Werkzeug.

Aktuell laufen Migrationen weiterhin im FastAPI-`lifespan` beim Start (abgesichert durch den Concurrency-Lock). Mittelfristiges Zielbild ist, sie stattdessen als dediziertes Kubernetes-Job / Helm-`pre-upgrade`-Hook auszuführen, sodass App-Replicas selbst nie migrieren — der CLI-Entrypoint ist dafür bereits die Grundlage.

### Abgelehnte Alternativen

| Option | Warum verworfen |
|---|---|
| Leichtgewichtige Registry ohne Versionierung | Erfüllt den Wunsch nach rollback-fähiger, reproduzierbarer Historie nicht |
| Reine Konventionen/Doku ohne Framework-Code | Löst die realen Startup-Crashes (fehlende Fehler-Isolation, kein Tracking) nicht |
| Bestehendes SQL-Tool (Alembic/yoyo) | An SQLAlchemy/SQL-DDL gebunden — passt nicht zum schemalosen, AQL-basierten ArangoDB |
| Migrationen ausschließlich als externer Job, nie im Startup | Als Zielbild übernommen, aber kein Sofort-Bruch — der Startup-Pfad mit Lock bleibt interim erhalten |

## Konsequenzen

### Positiv

- Ein fehlschlagender Referenzdaten-Seed reißt den Startup nicht mehr mit.
- Einmalige Migrationen laufen genau einmal, getrackt und in definierter Reihenfolge.
- Der Datenbankstand ist über `current`/`history` jederzeit inspizierbar.
- Replica-Races beim parallelen Pod-Start sind durch den Lock ausgeschlossen.
- Neue Migrationen folgen einem einheitlichen, getesteten Muster (`create <slug>`-Scaffolding).

### Negativ

- Zusätzliche Framework-Komplexität und eine neue Collection `schema_migrations`.
- Migrations-Autoren müssen Versionierungs- und Idempotenz-Regeln einhalten.
- Die meisten Datentransformationen bleiben faktisch irreversibel — Rollback ist kein Allheilmittel, sondern eine ehrlich deklarierte Ausnahme.

### Folgemaßnahmen

- Migrationen mittelfristig in ein dediziertes Kubernetes-Job/Helm-Hook auslagern, statt im App-Pod-Lifespan zu laufen.
- Bei jeder Entfernung/Umbenennung eines persistierten Enum-Werts oder Felds ist in derselben Änderung verpflichtend eine Daten-Migration mitzuliefern (direkte Lehre aus Issue #306).

## Verweise

- Canonical-Entscheidung: `spec/decisions/ADR-005-versioned-migration-framework.md` *(Hinweis: eigene Nummerierung im `spec/decisions/`-Verzeichnis, unabhängig von der hiesigen `docs/adr/`-Zählung — dieses Dokument ist die publizierte Fassung von Canonical-ADR-005 unter der nächsten freien Nummer `009`)*
- Normative Anforderung: `spec/nfr/NFR-016_Datenbank-Migrationsstrategie.md`
- [ADR-001](001-arangodb-multi-model.md) — ArangoDB als schemalose Primär-Datenbank
- docs/adr/005 — [YAML-basierte Seed-Jobs beim Startup](005-yaml-seed-jobs-startup.md) (abgegrenztes Seed-Muster)
- Issue #306 — Abschaffung der `harvest`-Phase (auslösender Incident)
