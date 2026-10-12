# Messung: `tenant_key`-Index für die Task-Queue (#1534, Slice 1)

| Feld | Wert |
|---|---|
| Datum | 2026-10-12 |
| Stand | `develop` @ `959a3dc1b` (Worktree `chore/1534-task-queue-index-measure`) |
| Methode | Messung, kein Index im Produktcode. Wegwerf-Container `arangodb:3.12.12` (dieselbe Version wie `helm/kamerplanter/values.yaml`, Digest `sha256:4bc086d5…`), Einzelserver, RocksDB, keine Ressourcenlimits; Host 8 Kerne / 30 GiB. Datenbank per `ensure_collections` (Produktions-Bootstrap) angelegt, synthetisches Volumen geseedet, `explain` + Laufzeit + Schreibkosten pro Index-Variante gemessen. |
| Skript | `src/backend/scripts/measure_task_queue_indexes.py` (reproduzierbar, siehe §8) |
| Ergebnis | **Index ja: persistent `["tenant_key", "status"]`.** `due_date` als drittes Feld bringt für die Queries, wie sie heute geschrieben sind, **nichts** (§4). |

## 1. Kurzfassung

- **Heute** nimmt jede Queue-Abfrage den Einzelfeld-Index `status` und filtert den Mandanten danach. Gemessen: Ein Mandant mit **262 Tasks** liest bei jedem Queue-Aufruf **alle 62 389 `pending`-Tasks der Installation** (113 424 Tasks, 300 Mandanten) und braucht dafür **~134 ms** — so viel wie der größte Mandant. Die Kosten wachsen mit der *Installation*, nicht mit dem Mandanten; genau die Vermutung aus #1534, jetzt gemessen.
- **Mit `["tenant_key","status"]`** liest derselbe Mandant **139 Index-Einträge** und braucht **~1,6 ms** (Faktor ~80). Der große Mandant (20 000 Tasks) halbiert sich auf ~78 ms; sein Rest ist eigene Größe (10 828 pending) plus Orphan-Guard und Sort, kein Index-Problem mehr.
- **`["tenant_key","status","due_date"]`** liefert **dieselben Scan-Zahlen** wie die Zwei-Feld-Variante: Der Sort bleibt ein `SortNode`, die Overdue-Range wird nicht über den Index aufgelöst. Grund: Die Queries sortieren und filtern auf `DATE_TIMESTAMP(doc.due_date)` (ein Ausdruck, kein Feld), haben einen `doc._key`-Tie-Breaker, und zwischen Index-Scan und `SORT` sitzt der Orphan-Guard (`LET _plant = DOCUMENT(...) FILTER ...`). Nur eine **hypothetische, umgeschriebene** Query ohne Guard, mit Roh-Feld-Sort und ohne Tie-Breaker nutzt das dritte Feld (200 statt 10 828 gelesen, 0,9 statt 29 ms) — das ist eine Query-Änderung mit Semantikfolgen, nicht Gegenstand dieses Issues.
- **Bei ≈ 1 M Tasks** (3 406 Mandanten) wächst die Baseline linear mit: **1,4 s** pro Queue-Query für einen 277-Task-Mandanten (zwei Queries pro Queue-Aufruf), mit `["tenant_key","status"]` **2,0 ms** (§6).
- **Schreibkosten**: von Lauf-zu-Lauf-Streuung nicht trennbar (Single-Insert ~1 ms in allen Varianten; Bulk-Durchsatz streut bis ~25 %, nicht monoton über die Varianten). Index-Aufbau: 0,27 s / 0,61 s auf 113 k, 1,97 s / 3,55 s auf 970 k Tasks (zwei / drei Felder).

## 2. Gemessene Queries (vom Builder erzeugt, nicht abgeschrieben)

Das Skript ruft die echten Methoden von `ArangoTaskRepository` gegen die geseedete Datenbank auf und zeichnet das AQL auf, das sie senden. Die Queue (`TaskService.get_task_queue` ohne `plant_key`) ruft `get_pending_tasks(0, QUEUE_LIMIT=200, …)` → `get_all_tasks` → **zwei** Queries (Fenster + Count). `get_tasks_window` ist die Listen-Route (`GET /t/{slug}/tasks`).

| Name | Quelle | AQL (gekürzt um den gemeinsamen Orphan-Guard `G`) |
|---|---|---|
| `queue.window` | `get_pending_tasks` | `FOR doc IN tasks FILTER doc.tenant_key == @tenant_key AND doc.status == @val0 G SORT DATE_TIMESTAMP(doc.due_date) ASC, doc._key ASC LIMIT @offset, @limit RETURN doc` |
| `queue.count` | `get_pending_tasks` | `… FILTER doc.tenant_key == @tenant_key AND doc.status == @val0 G COLLECT WITH COUNT INTO total RETURN total` |
| `queue_category.*` | `… category="care_reminder"` | wie oben, zusätzlich `AND doc.category == @val1` |
| `queue_category_origin.*` | `… origins=["system","pipeline"]` | wie oben, zusätzlich `AND doc.origin IN @origins` |
| `overdue` | `get_overdue_tasks` | `FOR doc IN tasks FILTER doc.tenant_key == @tenant_key AND doc.status == 'pending' AND DATE_TIMESTAMP(doc.due_date) != null AND DATE_TIMESTAMP(doc.due_date) < DATE_TIMESTAMP(@now) SORT DATE_TIMESTAMP(doc.due_date) ASC RETURN doc` |
| `list_all.window` / `.count` | `get_all_tasks(0, 50, None)` | `FOR doc IN tasks FILTER doc.tenant_key == @tenant_key G SORT … LIMIT @offset, @limit` bzw. `… G COLLECT WITH COUNT …` |
| `list_completed.window` | `get_tasks_window(0, 50, {"status": "completed"})` | wie `queue.window` mit `@val0 = "completed"`, `@limit = 50` |

`G` = `LET _plant = doc.entity_type == 'plant_instance' ? DOCUMENT(CONCAT('plant_instances/', doc.entity_key)) : null FILTER doc.entity_type != 'plant_instance' OR (_plant != null AND _plant.removed_on == null)`.

Zusätzlich, ausdrücklich **nicht** vom Code gesendet (Diagnose, `HYPOTHETICAL` im Skript): `queue.window` mit `SORT doc.due_date` (Roh-Feld), dasselbe ohne `doc._key`-Tie-Breaker, und beides ohne `G`. Der vollständige Text jeder Query mit Bind-Variablen steht in der Skript-Ausgabe.

## 3. Seed-Parameter

| Parameter | Wert |
|---|---|
| Tasks gesamt | **113 424** |
| Mandanten | 300: 1 × 20 000 (`tenant-large`), 5 × 3 000, 294 × zufällig 50–500 (Median 261,5) |
| Kleiner Messmandant | Median der kleinen: `tenant-small-00130`, 262 Tasks |
| Status | pending 62 389 · completed 33 994 · skipped 9 065 · in_progress 4 548 · dormant 2 273 · failed 1 155 (Gewichte 55/30/8/4/2/1) |
| Kategorie | care_reminder 40 %, feeding 15 %, maintenance 15 %, observation 10 %, ipm/training/harvest/pruning je 5 % |
| Herkunft | user 65 %, system 30 %, pipeline 5 % |
| `entity_type` | plant_instance 60 % (auf echte `plant_instances`, 3 % davon `removed_on` gesetzt), planting_run 20 %, location 10 %, keiner 10 % |
| `due_date` | offen (pending/in_progress/dormant): jetzt ±45 Tage; abgeschlossen: letzte 365 Tage. Serialisiert über `Task` + `_to_doc` (Produktionsformat) |
| Bootstrap-Indizes auf `tasks` (aus der DB gelesen) | primary `_key`; persistent `plant_key`, `status`, `planting_run_key`; persistent unique sparse `care_dedup_key` (+ Computed Value) |
| Zufalls-Seed | 1534 |

## 4. Lesepfad: Plan und Laufzeit (113 k Tasks)

Pro Zelle: genutzter Index / gelesene Einträge (`scannedIndex` bzw. `scannedFull`) / `SortNode` vorhanden? / **Server-Median ms** (Client-Wall-Median ms). Median aus 9 warmen Läufen nach 2 verworfenen Aufwärmläufen. Kein Plan enthielt einen `EnumerateCollectionNode`, außer wo „Full Scan" steht.

| Query | Mandant | Baseline (Bootstrap) | `+ [tenant_key, status]` | `+ [tenant_key, status, due_date]` |
|---|---|---|---|---|
| queue.window | groß (20 000) | `status` / 62 389 / Sort / **172,6** (175,6) | `tenant_key+status` / 10 828 / Sort / **78,2** (82,0) | `…+due_date` / 10 828 / Sort / **92,9** (97,0) |
| queue.window | klein (262) | `status` / 62 389 / Sort / **134,0** (136,9) | `tenant_key+status` / 139 / Sort / **1,6** (4,4) | `…+due_date` / 139 / Sort / **1,6** (4,0) |
| queue.count | groß | `status` / 62 389 / – / 151,3 | `tenant_key+status` / 10 828 / – / 70,0 | `…+due_date` / 10 828 / – / 72,9 |
| queue.count | klein | `status` / 62 389 / – / 131,8 | `tenant_key+status` / 139 / – / 1,7 | `…+due_date` / 139 / – / 1,7 |
| queue_category.window | groß | `status` / 62 389 / Sort / 144,5 | `tenant_key+status` / 10 828 / Sort / 53,3 | `…+due_date` / 10 828 / Sort / 55,5 |
| queue_category.window | klein | `status` / 62 389 / Sort / 124,5 | `tenant_key+status` / 139 / Sort / 1,1 | `…+due_date` / 139 / Sort / 1,1 |
| queue_category.count | groß | `status` / 62 389 / – / 137,9 | `tenant_key+status` / 10 828 / – / 33,7 | `…+due_date` / 10 828 / – / 44,2 |
| queue_category.count | klein | `status` / 62 389 / – / 136,1 | `tenant_key+status` / 139 / – / 1,0 | `…+due_date` / 139 / – / 1,3 |
| queue_category_origin.window | groß | `status` / 62 389 / Sort / 133,8 | `tenant_key+status` / 10 828 / Sort / 34,4 | `…+due_date` / 10 828 / Sort / 49,9 |
| queue_category_origin.window | klein | `status` / 62 389 / Sort / 137,8 | `tenant_key+status` / 139 / Sort / 0,9 | `…+due_date` / 139 / Sort / 1,2 |
| queue_category_origin.count | groß | `status` / 62 389 / – / 126,6 | `tenant_key+status` / 10 828 / – / 29,7 | `…+due_date` / 10 828 / – / 47,7 |
| queue_category_origin.count | klein | `status` / 62 389 / – / 129,5 | `tenant_key+status` / 139 / – / 1,2 | `…+due_date` / 139 / – / 1,1 |
| overdue | groß (5 379 Treffer) | `status` / 62 389 / Sort / 114,8 (166,7) | `tenant_key+status` / 10 828 / Sort / 29,7 (80,6) | `…+due_date` / 10 828 / Sort / 21,8 (72,9) |
| overdue | klein (66 Treffer) | `status` / 62 389 / Sort / 106,9 | `tenant_key+status` / 139 / Sort / 0,6 | `…+due_date` / 139 / Sort / 0,6 |
| list_all.window | groß | **Full Scan** / 113 424 / Sort / 123,5 | `tenant_key+status` (Präfix) / 20 000 / Sort / 120,3 | `…+due_date` / 20 000 / Sort / 148,5 |
| list_all.window | klein | **Full Scan** / 113 424 / Sort / 29,1 | `tenant_key+status` (Präfix) / 262 / Sort / 2,0 | `…+due_date` / 262 / Sort / 2,2 |
| list_all.count | groß | **Full Scan** / 113 424 / – / 98,2 | `tenant_key+status` (Präfix) / 20 000 / – / 109,2 | `…+due_date` / 20 000 / – / 131,0 |
| list_all.count | klein | **Full Scan** / 113 424 / – / 26,6 | `tenant_key+status` (Präfix) / 262 / – / 2,0 | `…+due_date` / 262 / – / 3,4 |
| list_completed.window | groß | `status` / 33 994 / Sort / 110,7 | `tenant_key+status` / 6 150 / Sort / 44,5 | `…+due_date` / 6 150 / Sort / 59,5 |
| list_completed.window | klein | `status` / 33 994 / Sort / 74,9 | `tenant_key+status` / 90 / Sort / 1,2 | `…+due_date` / 90 / Sort / 1,5 |

**Diagnose (hypothetische Umschreibungen von `queue.window`, nicht im Code):**

| Variante der Query | Mandant | Baseline | `+ [tenant_key, status]` | `+ [tenant_key, status, due_date]` |
|---|---|---|---|---|
| `SORT doc.due_date ASC, doc._key ASC` (Roh-Feld) | groß | `status` / 62 389 / Sort / 208,8 | 10 828 / Sort / 90,9 | 10 828 / Sort / 96,4 |
| `SORT doc.due_date ASC` (ohne Tie-Breaker) | groß | `status` / 62 389 / Sort / 211,2 | 10 828 / Sort / 97,3 | 10 828 / Sort / 90,0 |
| ohne Orphan-Guard `G`, Sort wie im Code | groß | `status` / 62 389 / Sort / 136,1 | 10 828 / Sort / 28,9 | 10 828 / Sort / 29,0 |
| ohne `G`, `SORT doc.due_date ASC` | groß | `status` / 62 389 / Sort / 128,0 | 10 828 / Sort / 34,2 | **200 / kein Sort / 0,9** |
| ohne `G`, `SORT doc.due_date ASC` | klein | `status` / 62 389 / Sort / 101,3 | 139 / Sort / 0,8 | 139 / kein Sort / 0,6 |

Lesart:

1. **Der Mandantenfilter ist das Problem, nicht der Sort.** Baseline liest für jeden Mandanten die ganze Installation (62 389 bzw. 113 424); beide Compound-Varianten reduzieren das auf die Größe des Mandanten. Für die 299 von 300 Mandanten, die nicht der große sind, ist das der gesamte Effekt (Faktor 60–130).
2. **`due_date` als drittes Feld hilft keiner heutigen Query.** Das Plan-Merkmal ist eindeutig: identisches `scannedIndex`, `SortNode` bleibt in jeder realen Query. Erst wenn *alle drei* Hürden fallen — Roh-Feld statt `DATE_TIMESTAMP`, kein `_key`-Tie-Breaker, kein `FILTER` zwischen Scan und `SORT` — übernimmt der Index Sort und `LIMIT` (`use-index-for-sort`). Der Orphan-Guard kann dafür nicht einfach hinter das `LIMIT` wandern, ohne die Seitengröße zu verändern (#1503-Argument), und der `DATE_TIMESTAMP`-Sort schützt gegen gemischte Zeitstempel-Formate. In den Laufzeiten ist die Drei-Feld-Variante beim großen Mandanten eher langsamer (größere Index-Einträge), beim kleinen gleich.
3. **Beim großen Mandanten bleiben Restkosten von ~30–80 ms**, getrieben von `G` (`DOCUMENT()`-Lookup pro Zeile vor dem Sort: 78 ms mit, 29 ms ohne Guard) und vom Materialisieren aller 10 828 pending Tasks für den Sort. Das ist eigene Größe, kein Index-Thema; ein Folge-Issue, falls Mandanten dieser Größe real werden.
4. **`get_all_tasks`-Paging (`list_all`)** profitiert über das Präfix `tenant_key` vom Compound: kleine Mandanten 29 → 2 ms. Beim großen Mandanten ist der Index-Pfad (20 000 Lookups) nicht schneller als der Full Scan über 113 k — dort entscheidet die Mandantengröße.
5. **`get_overdue_tasks`** profitiert gleich wie die Queue (107 → 0,6 ms klein); die Range auf `due_date` wird mangels Roh-Feld nicht im Index aufgelöst.

## 5. Schreibkosten

Pro Variante: ein AQL-Bulk-Insert von 10 000 Tasks (Median aus 5 Läufen, nach jedem Lauf zurückgerollt) und 1 000 Einzel-Inserts über `collection.insert` (der `create_task`-Pfad, inkl. Computed Value `care_dedup_key`).

| Variante | Index-Aufbau auf 113 k | Bulk Docs/s (Median ms) | Single-Insert Median / p95 ms |
|---|---|---|---|
| Baseline | – | 20 979 (476,7) | 1,175 / 1,753 |
| `+ [tenant_key, status]` | 0,27 s | 21 092 (474,1) | 1,051 / 1,480 |
| `+ [tenant_key, status, due_date]` | 0,61 s | 21 446 (466,3) | 0,971 / 1,337 |

Ein vorheriger identischer Lauf ergab Baseline 26 989 / zwei Felder 24 445 / drei Felder 23 104 Docs/s und Single-Median 0,88 / 0,89 / 0,99 ms. Die Schreibkosten des zusätzlichen Index liegen damit **innerhalb der Lauf-zu-Lauf-Streuung** (bei 970 k bis ~25 %, nicht monoton, §6); ein messbarer Nachteil für eine Installation, deren Tasks einzeln über die API entstehen, ist nicht erkennbar.

## 6. Skalierung (≈ 1 M Tasks)

Zweiter Lauf mit denselben Parametern, aber 3 400 statt 294 kleinen Mandanten: **970 426 Tasks, 3 406 Mandanten**, davon 533 680 `pending`; großer Mandant unverändert 20 000, kleiner Messmandant `tenant-small-02823` mit 277 Tasks. Median aus 7 warmen Läufen.

| Query | Mandant | Baseline | `+ [tenant_key, status]` | `+ [tenant_key, status, due_date]` |
|---|---|---|---|---|
| queue.window | groß | `status` / 533 680 / **1 505** ms | 10 835 / **104,8** ms | 10 835 / **98,6** ms |
| queue.window | klein (277) | `status` / 533 680 / **1 435** ms | 149 / **2,0** ms | 149 / **1,8** ms |
| queue.count | klein | `status` / 533 680 / 1 506 ms | 149 / 1,8 ms | 149 / 1,7 ms |
| queue_category_origin.window | klein | `status` / 533 680 / 1 469 ms | 149 / 1,3 ms | 149 / 1,1 ms |
| overdue | groß | `status` / 533 680 / 1 523 ms | 10 835 / 31,3 ms | 10 835 / 20,6 ms |
| overdue | klein | `status` / 533 680 / 1 475 ms | 149 / 0,7 ms | 149 / 0,7 ms |
| list_all.window | groß | **Full Scan** / 970 426 / 379 ms | 20 000 / 135,7 ms | 20 000 / 156,5 ms |
| list_all.window | klein | **Full Scan** / 970 426 / 261 ms | 277 / 2,5 ms | 277 / 2,6 ms |
| list_all.count | klein | **Full Scan** / 970 426 / 231 ms | 277 / 2,1 ms | 277 / 2,4 ms |
| list_completed.window | klein | `status` / 291 560 / 767 ms | 74 / 1,1 ms | 74 / 1,2 ms |

(Server-Median; vollständige Tabelle inkl. aller Formen und Diagnosen in der Skript-Ausgabe.)

- **Baseline skaliert linear mit der Installation**: ~8,6× mehr Tasks → Queue eines 277-Task-Mandanten von 134 ms auf **1,4 s**, und das **zweimal pro Queue-Aufruf** (Fenster + Count). Mit dem Index bleibt sie bei ~2 ms, unabhängig von der Installationsgröße.
- Pläne und Scan-Zahlen sind dieselben wie bei 113 k: `due_date` als drittes Feld ändert keinen Plan der realen Queries. In den Laufzeiten des *großen* Mandanten ist es diesmal leicht vorn (queue.window 105 → 99 ms, overdue 31 → 21 ms), bei 113 k teils hinten (queue.window 78 → 93 ms); einzig `overdue` war in beiden Läufen um rund ein Drittel schneller — vermutlich, weil die Index-Reihenfolge den nachgelagerten Sort vorsortiert füttert. Für kleine Mandanten ist der Unterschied < 0,3 ms.
- Schreibkosten bei 970 k: Bulk 25 049 / 18 550 / 21 002 Docs/s, Single-Median 1,02 / 1,03 / 1,26 ms, Index-Aufbau 1,97 s bzw. 3,55 s. Nicht monoton (zwei Felder schlechter als drei) → von Streuung dominiert; als **obere Schranke** kostet der zusätzliche Index bis ~25 % Bulk-Durchsatz und ≤ 0,25 ms je Einzel-Insert.

## 7. Entscheidung

**Index ja — persistent, nicht unique, `["tenant_key", "status"]`.**

- Er beseitigt die einzige Kostenkomponente, die mit der *Installation* statt mit dem Mandanten wächst, für alle gemessenen Formen: Queue (alle drei Filtervarianten, Fenster und Count), `get_overdue_tasks`, `get_all_tasks`/`get_tasks_window` mit und ohne Status (Präfix-Nutzung).
- `due_date` als drittes Feld wird **nicht** empfohlen: Es ändert keinen Plan der heutigen Queries (gleiche Scan-Zahlen, `SortNode` bleibt), die Laufzeitunterschiede beim großen Mandanten wechseln zwischen den Läufen das Vorzeichen (Ausnahme `overdue`, dort −⅓ bei 20–30 ms Ausgangswert), und der Index ist größer (fast doppelte Aufbauzeit). Sollte später die Queue auf einen Roh-Feld-Sort ohne Guard vor dem `LIMIT` umgebaut werden, ist das eine eigene Entscheidung mit eigener Messung; dieses Skript enthält die Diagnose-Form dafür bereits.
- Der bestehende Einzelfeld-Index `status` bleibt (andere, mandantenübergreifende Leser wie Beat-Jobs filtern nur auf Status; nicht Gegenstand dieser Messung).
- Umsetzung in Slice 2 (nach Review): Migration neben `v0045`, Bootstrap in `collections.py` synchron, plus ein Explain-Test, der `IndexNode` auf `["tenant_key","status"]` statt `status` für `queue.window` festhält.

## 8. Reproduzieren und Grenzen

```bash
docker run -d --name kp-perf-arango -p 127.0.0.1:18634:8529 \
  -e ARANGO_ROOT_PASSWORD=<pw> arangodb:3.12.12
cd src/backend
ARANGO_PERF_PASSWORD=<pw> .venv/bin/python scripts/measure_task_queue_indexes.py \
  --url http://127.0.0.1:18634 --json /tmp/task-queue-indexes.json
# ≈ 1 M Tasks: zusätzlich --small-tenants 3400 --runs 7
docker rm -f kp-perf-arango
```

Das Skript legt nur eine Datenbank mit Präfix `perf_` an, verweigert eine bestehende ohne `--recreate` und löscht sie am Ende (außer `--keep`). Seed-Verteilung und Mandantengrößen sind über Parameter einstellbar; die Queries kommen immer aus dem aktuellen Repository-Code.

Grenzen:

- **Synthetisches Volumen.** Verteilungen sind plausibel gewählt, nicht aus einer Installation gemessen. Insbesondere wächst real eher der Anteil `completed` (Pflege-Erinnerungen entstehen täglich); das macht den Baseline-`status`-Index für `pending` *selektiver* und den Effekt kleiner — der Faktor bleibt aber proportional zu „pending der Installation / pending des Mandanten".
- **Einzelserver auf einem Entwickler-Host**, warmer Block-Cache (Datenmenge passt in RAM). Absolute Millisekunden sind nicht übertragbar; Scan-Zahlen und Plan-Form sind es.
- **Single-Insert-Zeiten** sind HTTP-Roundtrip-dominiert und deshalb unempfindlich für einen Index mehr.
- Der aufgezeichnete Overdue-Bind-Parameter `@now` ist der Zeitpunkt der Aufzeichnung; die Seed-Daten sind relativ dazu erzeugt.
