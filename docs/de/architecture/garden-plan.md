# Gartenplan: Geometrie und Schnittstellen

Diese Seite beschreibt, wie der Gartenplan technisch aufgebaut ist: das Koordinatensystem und die Formen, den Stapel-Vertrag zum Speichern, das Sicherungsformat und den Weg zu Zustand und Bewässerungszonen. Sie richtet sich an Entwickler und Betreiber. Wie du den Plan bedienst, steht im [Benutzerhandbuch Gartenplan](../user-guide/garden-plan.md).

!!! info "Quelle der Wahrheit"
    Die Grenzen und Fehlercodes unten stammen aus dem Code (`src/backend/app/domain/models/geometry.py`, `garden_plan.py`, `garden_plan_import.py`, `garden_plan_export.py`). Die Routen mit Beispielen stehen in der [API-Referenz](../reference/api-reference.md#gartenplan-pdf-svg-json-sicherung). <!-- REQ-053 §20-§22 -->

---

## Geometriemodell

### Koordinatensystem

Jede gespeicherte Geometrie ist in **Metern** angegeben, gerundet auf 0,001 m (Millimeter). Pixel entstehen nur bei der Umrechnung vom Modell in die Ansicht und werden nie gespeichert. Die x-Achse zeigt nach rechts, die y-Achse nach oben, Winkel laufen **gegen den Uhrzeigersinn**. Die Nordrichtung des Plans (`north_angle_deg`) ist eine Ausnahme: Sie ist ein Kompass-Azimut im Uhrzeigersinn, 0 heißt „Norden ist +y".

Es gibt zwei Bezugsrahmen:

| Rahmen | Gilt für | Koordinatenbereich |
|--------|----------|--------------------|
| **Planrahmen** | Gartengrenze (`plan.boundary`), Geometrie von Standorten (`Location`) und Gartenobjekten | 0 bis 1000 m je Achse |
| **Beetrahmen** | Geometrie eines Pflanzplatzes (`Slot`) | −1000 bis 1000 m je Achse |

Der Ursprung des Beetrahmens ist der Ankerpunkt des Beets: der Mittelpunkt bei einem runden Beet, der erste Eckpunkt bei einem Vieleck. Darum sind Koordinaten eines Pflanzplatzes legitim negativ. Der Bereich −1000 bis 1000 m im Beetrahmen ist ein Platzhalter bis zur Entscheidung der Spezifikation; er steht so im Code.

### Formen (`kind`)

| `kind` | Felder | Hinweise |
|--------|--------|----------|
| `rect` | `origin`, `width_m`, `length_m`, `rotation_deg` | `origin` ist die untere linke Ecke vor der Drehung; die Drehung pivotiert um `origin` |
| `circle` | `origin`, `radius_m` | `origin` ist der Mittelpunkt; keine Drehung |
| `polygon` | `points` (3 bis 200), `rotation_deg` | Der erste Punkt ist der Anker; der Editor speichert Vielecke mit Drehung 0 |
| `polyline` | `points` (2 bis 200), `width_m` | Offene Linie (Zaun, Mauer, Wegachse); keine Drehung |
| `point` | `origin` | Eine Position (Pflanzplatz, Punktobjekt); keine Drehung |

`rect`, `circle` und `polygon` schließen eine Fläche ein und tragen die vom Server berechnete `area_m2`. Ein `rotation_deg` an Kreis, Linie oder Punkt ist ein Fehler (unbekanntes Feld).

### Wertebereiche (Regel V-01)

- Maße (`width_m`, `length_m`, `radius_m`, `width_m` der Linie): 0,01 bis 1000 m.
- Koordinaten: siehe Tabelle oben, je nach Rahmen.
- `rotation_deg`: von 0 (einschließlich) bis unter 360. Ein Eingabewert, der auf 360,000 rundet, wird zu 0.
- Eckpunkte: Vieleck 3 bis 200, Linie 2 bis 200.
- Der Server wendet die Regel mit Fehlercode `geometry.invalid` an. Bei einem Eckpunkt außerhalb des Bereichs trägt der Eintrag zusätzlich `point_index` (ab 0 gezählt).
- Die Regel V-02 (ein Vieleck darf sich nicht selbst schneiden) sitzt eine Schicht höher im Rechner `geometry_calculator`: Ein sich schneidendes Vieleck wird gelesen und vom Service mit eigenem Fehlercode abgelehnt.

### Rundung

Länge, Koordinate und Winkel werden auf drei Nachkommastellen gerundet, **halbe Werte weg von null**, auf dem exakten Binärwert (`Decimal(value).quantize(0.001, ROUND_HALF_UP)`). In JavaScript entspricht das `Number(value.toFixed(3))`. Das eingebaute `round` von Python würde Gleichstände zur geraden Zahl runden und bei genau darstellbaren Hälften wie 2,0625 abweichen. `-0.0` wird zu `0.0`.

---

## Stapel-Vertrag

`POST /api/v1/t/{slug}/sites/{key}/plan/batch` wendet eine Liste von Plan-Operationen **atomar** an: Entweder werden alle übernommen oder keine. Der Editor sammelt seine Änderungen lokal und schickt sie beim Speichern in einem Stapel.

### Anfrage

```json
{
  "expected_revision": 42,
  "operations": [
    { "op": "create_location", "temp_key": "tmp1",
      "data": { "name": "Beet 6", "location_type_key": "bed",
                "geometry": { "kind": "rect", "origin": [4, 1], "width_m": 2, "length_m": 1, "rotation_deg": 0 } } },
    { "op": "delete", "entity": "garden_object", "key": "go_old" }
  ]
}
```

| Feld | Bedeutung |
|------|-----------|
| `expected_revision` | Die `plan_revision`, bei der der Client seinen Stand geladen hat (optimistische Sperre). Ganzzahl ≥ 0 |
| `operations` | 1 bis 500 Operationen aus der geschlossenen Liste unten |

Die Operationen sind geschlossen:

| `op` | Wirkung |
|------|---------|
| `create_location` | Legt einen Standort (ein Beet, einen Bereich) mit Geometrie an; `temp_key` benennt ihn im Stapel |
| `create_garden_object` | Legt ein Gartenobjekt an (`object_type`, Geometrie, `props`) |
| `update_geometry` | Setzt die Geometrie von `entity` (`location` oder `garden_object`) mit `key` |
| `update_fields` | Ändert Felder; bei einem Standort auch `site_conditions.sun_profile` (nur die gesendeten Schlüssel) |
| `delete` | Löscht `entity` mit `key` samt Nachfahren; **nur Rolle lead** |
| `set_boundary` | Setzt Gartengrenze, `north_angle_deg`, `default_grid_m` (größer als 0 bis höchstens 10 m) und `adjacency_factor` |
| `set_locked` | Sperrt oder entsperrt ein Objekt |
| `set_z_order` | Setzt die Zeichenreihenfolge (−10000 bis 10000) |

### Temporäre Schlüssel

Ein Objekt, das du im Stapel anlegst, bekommt einen `temp_key` (1 bis 40 Zeichen aus Buchstaben, Ziffern, `_` und `-`). Spätere Operationen desselben Stapels und `parent_location_key` dürfen ihn als Schlüssel benutzen. Die Antwort enthält `key_map` (`temp_key` auf vergebenen Schlüssel). Ein `temp_key` gilt nur innerhalb der Anfrage.

### Antwort

`200` mit `plan_revision` (die neue Revision), `key_map`, `updated` und `deleted` (Schlüssellisten) und `derived` je Schlüssel (`area_m2`, `bbox` als `[minX, minY, maxX, maxY]`). Jeder erfolgreiche Stapel erhöht die Revision um eins. Pflanzplätze liegen im Beetrahmen und ändern sich **außerhalb** der Plan-Revision, über eigene Routen.

### Reihenfolge der Prüfungen und Fehlercodes

Der Server prüft in dieser Reihenfolge und bricht beim ersten Fehler ab. Es wird nichts geschrieben.

0. Rolle an der Route: Wer nur die Rolle viewer hat, scheitert schon an der Route (Berechtigung zum Ändern von Standorten) mit einem allgemeinen `403` – vor dem `404` und vor den Größenprüfungen.
1. Standort gehört zum Mandanten (sonst `404`).
2. Größe der Anfrage: mehr als `MAX_OPERATIONS` = 500 Operationen ergibt `422 batch.too_many_operations`. Ein Body über 1 MiB weist der Server schon vor dem Routing mit `413 REQUEST_BODY_TOO_LARGE` ab. Die Prüfung `MAX_BATCH_BODY_BYTES` = 2 MiB (`422 batch.too_complex`) misst die erneut serialisierten Operationen eines Bodys, der bereits unter 1 MiB liegt; über HTTP greift sie praktisch nicht.
3. Verweise: Ein unbekannter oder fremder Schlüssel ergibt `422 reference.not_found` (abwesend und fremd sehen gleich aus).
4. Rolle je Operation: `delete` verlangt die Rolle lead, alles andere mindestens grower. Ein Verstoß (ein grower, dessen Stapel ein `delete` enthält) verwirft den ganzen Stapel mit `403 batch.operation_forbidden` und `op_index`.
5. Form: Pydantic prüft jede Operation (`422 VALIDATION_ERROR`). Mehr als `MAX_BATCH_POINTS` = 20 000 Vieleck- und Linienpunkte zusammen ergibt `422 batch.too_complex`.
6. Fachregeln: `422 VALIDATION_ERROR`, in `details[]` jeweils `code`, `op_index` und gegebenenfalls `point_index`. Codes unter anderem `geometry.invalid`, `geometry.outside_parent`, `bed.overlap`, `boundary.shrinks_below_objects`, `plan.quota_exceeded`. Höchstens 50 Befunde je Antwort. Dauert Prüfung und Transaktion länger als `BATCH_TIME_BUDGET_SECONDS` = 10 s, endet der Stapel mit `422 batch.too_complex`.
7. Revision: `409 plan.revision_conflict` mit `current_revision`, dem Anzeigenamen des letzten Bearbeiters (`changed_by`) und `changed_at`; nie mit einem Konto-Schlüssel.

Außerdem lehnt der Server das Löschen eines Beets mit `409 location.has_active_plants` ab, solange darauf Pflanzen stehen.

Pro Standort sind höchstens `MAX_PLAN_OBJECTS_PER_SITE` = 500 Standorte und Gartenobjekte zusammen, `MAX_PLAN_ZONES` = 500 Bewässerungszonen und `MAX_SLOTS_PER_SITE` = 8 000 Pflanzplätze erlaubt. Eine Überschreitung ergibt `422 plan.quota_exceeded` bzw. `irrigation_zone.quota_exceeded`. Das Speichern ist je Konto auf `RATE_LIMIT_PLAN_BATCH` begrenzt (Standard 10 pro Minute), siehe [Umgebungsvariablen](../reference/environment-variables.md).

Einzelne Beete setzt `POST …/plan/place-template` aus einer Vorlage über denselben Pfad (eine Transaktion, eine Revision). `PUT …/plan/boundary` legt beim ersten Aufruf den Plan an und erhöht danach die Revision.

---

## Sicherung: Export und Import

### Export

`GET …/plan/export` liefert eine JSON-Datei mit `schema_version: "1"`: Planeinstellungen, Standorte mit Geometrie und Bodenprofil, Gartenobjekte, Pflanzplätze und Bewässerungszonen. Sie enthält bewusst keine Pflanzen, Aufgaben, Pflegeereignisse, Fotos oder Anhänge, keine Konto-Verweise und kein `tenant_key`; ein neues Feld erscheint nur, wenn es absichtlich ins Exportmodell aufgenommen wird. Die Unterlage gehört nicht dazu.

Mit `scope` wählst du `site` (alles), `selection` (genau die in `keys` genannten Beete oder Objekte als `object:<key>`) oder `subtree` (die Beete mit allem darunter); `keys` hat höchstens 100 Einträge. Eine Teil-Datei ist dasselbe Schema, nur kleiner: ohne Planeinstellungen und mit `null` für Verweise, die die Datei verlassen.

### Import

`POST …/plan/import` (nur Rolle lead) prüft oder schreibt eine Sicherung:

- `mode`: `replace` ersetzt den Plan des Standorts, `merge` fügt hinzu. `dry_run` schreibt nichts und antwortet mit dem Bericht. `replace` verlangt `confirm_site_name`. `force` hebt nur die Bedingung auf, dass kein Beet eine aktive Pflanze trägt (`409 import.not_empty`); diese Beete bleiben dann bestehen.
- `target`: `same_site`, `other_site` oder `other_tenant`. `offset_m` (`[dx, dy]`, höchstens ±1000 m) gilt nur für `merge`.
- **Schlüssel** der Datei werden nie übernommen; alle Objekte bekommen neue Schlüssel, Verweise werden über eine Schlüsseltabelle umgeschrieben. Verknüpfungen zu Home-Assistant-Entitäten und Aktoren werden nie importiert.
- **Grenzen:** Datei höchstens 5 MiB (`413`, ein Umschlag von 64 KiB kommt hinzu), höchstens 10 Ebenen Standorte untereinander (`import.too_deep`), Zeitbudget 30 s, Bericht mit höchstens 50 Befunden (die Zähler bleiben exakt). Das Importbudget ist ein gemeinsamer Zähler je Mandant (`RATE_LIMIT_PLAN_IMPORT`, Standard 3 pro Minute).
- **Quoten:** Dieselben Obergrenzen wie beim Speichern (`plan.quota_exceeded`).

### Additive Schlüssel und Versionen

`schema_version` ist `"1"`. Neue Felder werden nur **additiv** ergänzt; ein bekannter Eintrag ignoriert unbekannte Felder. Eine Datei mit unbekanntem Schlüssel auf oberster Ebene stammt von einer neueren Version und wird mit `422 import.unknown_keys` abgelehnt; ein fehlender oder nicht unterstützter Wert von `schema_version` ergibt `import.schema_version_missing` bzw. `import.schema_version_unsupported`. Die Frostexposition eines Beets (`frost_exposed`) ist Teil der Datei; fehlt sie, leitet der Import sie aus dem Frostrisiko ab.

### Snapshots

Ein `replace`-Import schreibt den überschriebenen Plan vorher als `import_snapshot` ins Änderungsprotokoll. Ein Standort behält höchstens `MAX_SNAPSHOTS_PER_SITE` = 20 Snapshots; ein neuer entfernt den ältesten in derselben Transaktion. Die Aufbewahrung folgt dem Änderungsprotokoll (365 Tage, `RETENTION_GARDEN_PLAN_AUDIT_RETENTION_DAYS`). `GET …/plan/snapshots` listet nur Zähler, nie den Plan; `POST …/plan/snapshots/{audit_key}/restore` stellt einen Stand wieder her und schreibt den jetzigen vorher selbst als Snapshot. Beide Routen sind nur für die Rolle lead.

---

## Zustand, Zonen und weitere Routen

Hier nur Zeiger; Pfade und Felder stehen in der [API-Referenz](../reference/api-reference.md) und in der OpenAPI-Beschreibung des Backends.

| Zweck | Route | Rolle |
|-------|-------|-------|
| Pflanzenzustand eines Beets | `GET /locations/{key}/plant-states` | alle Mitglieder |
| Bewässerungszonen eines Standorts | `GET`/`POST /sites/{key}/irrigation-zones`, `GET`/`PATCH`/`DELETE /irrigation-zones/{key}` | lesen alle, ändern grower, löschen lead |
| Beete einer Zone ersetzen | `PUT /irrigation-zones/{key}/locations` | grower |
| Stand einer Zone | `GET /irrigation-zones/{key}/status` | alle Mitglieder |
| Gießrunde | `POST /irrigation-zones/{key}/log-watering` | grower |
| Beetvorlagen | `GET`/`POST /bed-templates`, `PATCH`/`DELETE /bed-templates/{key}` | lesen alle, anlegen grower, löschen lead |
| Unterlage | `PUT`/`DELETE /sites/{key}/plan/underlay` | grower |
| Änderungsprotokoll | `GET /sites/{key}/plan/audit` | alle Mitglieder |
| Neue Saison | `POST /sites/{key}/plan/new-season` | lead |
| PDF und SVG | `GET /print/garden-plan/{site_key}`, `GET /sites/{key}/plan/render.svg` | alle Mitglieder |

Die technische Kopplung einer Zone (`actuator_key`, Durchfluss aus einer Home-Assistant-Entität) darf nur ein Konto mit dem Verwaltungsbereich `technical` schreiben.

## Druckansichten (Verweis)

Der maßstäbliche Gartenplan ist der „visuelle Grundriss" der Standort-Übersicht. Wie ihn ein Anwender druckt, steht unter [Plan exportieren und Sicherung einspielen](../user-guide/garden-plan.md#plan-export-import) und in [Druckansichten und Export](../user-guide/print-export.md). Die Spezifikation der Druckansichten verweist für diesen Grundriss auf die Routen oben.

## Siehe auch

- [Benutzerhandbuch: Gartenplan](../user-guide/garden-plan.md)
- [API-Referenz](../reference/api-reference.md#gartenplan-pdf-svg-json-sicherung)
- [Umgebungsvariablen](../reference/environment-variables.md)
- [Backend-Architektur](backend.md)
