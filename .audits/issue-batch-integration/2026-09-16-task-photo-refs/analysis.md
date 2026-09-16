# Gruppe `2026-09-16-task-photo-refs`

Status: freigegeben 2026-09-16 · Umsetzung startet nach Abschluss von Gruppe `write-route-guard`

Gemessen gegen `origin/develop` @ `87c82ae25` (2026-09-16).

## Die Frage, auf die die Research-Phase gescoped war

Wer besitzt die Versöhnung von `photo_refs` mit dem Attachment-Katalog — und was
passiert mit einer Referenz, wenn niemand sie besitzt?

## Die eine logische Änderung

Der Attachment-Katalog wird die einzige Autorität dafür, was ein `photo_refs`-Eintrag
bedeutet, sodass weder die Löschroute noch die Migration eine Referenz auf etwas zeigen
lassen kann, das es nicht gibt.

## Mitglieder

| Issue | Klasse | Aufnehmendes Prädikat | Beleg |
|---|---|---|---|
| **#1437** | `bug`, `backend`, `frontend` | thematische Kopplung | `app/api/v1/tasks/photo_router.py:172-181` — der Löschpfad prunt `photo_refs` bewusst nicht und verweist auf „the readers resolve ids against the catalogue rather than trusting the list" |
| **#1438** | `bug`, `backend` | thematische Kopplung | `app/migrations/migrate_photo_refs.py:55-75` — die Normalisierung würde genau die Schreibweise zerstören, die der Resolver in `attachment_repository.py:498-522` per `storage_key`-Vergleich korrekt auflöst |

Beide Mitglieder ändern dieselbe Capability: die Auflösung von `photo_refs` gegen den
Katalog. Beide sind Ausgründungen aus #1393 / PR #1424.

## Was gemessen wurde

### Die zwei Identitäten

Ein Attachment hat zwei Identitäten, die nichts miteinander zu tun haben:

- `_key` — ein kurzer **numerischer** Schlüssel, den ArangoDB vergibt (`1024799`);
  `BaseArangoRepository._to_doc` entfernt `_key` vor dem Insert, kein Key-Generator
  ist konfiguriert (`migrate_photo_refs.py:59-62`).
- der ULID-Stamm im `storage_key` — `StorageKeyBuilder.build` prägt einen **eigenen**
  ULID, wenn der Aufrufer keinen übergibt, und `AttachmentService.upload` übergibt
  keinen (`:62-65`, `attachment_repository.py:501-505`).

Ein `photo_refs`-Eintrag kann heute beides sein. Der Resolver
(`attachment_repository.py:516-522`) vergleicht deshalb gegen `_key` **und** gegen den
Stamm von `storage_key`. Das funktioniert — solange niemand den Eintrag umschreibt.

### #1438 — die Migration schreibt eine funktionierende Referenz in eine kaputte um

`normalize_photo_ref` Regel 4 (`migrate_photo_refs.py:80-110`) reduziert einen
Storage-Key auf seinen ULID-Stamm. Dieser Stamm ist per Konstruktion kein `_key` — er
löst zu **keinem** Attachment auf. Der Modulkopf sagt das seit PR #1424 wörtlich
(`:55-58`: „This module's central premise is false"); der Code darunter ist unverändert.

**Drei Aufrufwege, alle gemessen:**

| Weg | Fundstelle | Zustand |
|---|---|---|
| Versionierte Migration `v0003_normalize_photo_refs` | `app/migrations/versions/v0003_normalize_photo_refs.py:24` ruft `migrate_photo_refs.run(db, dry_run=dry_run)` | **läuft beim Start jeder Installation** über `run_pending_migrations` (`framework/runner.py:190-199`), einmal, ledger-verfolgt (`framework/tracking.py:78`). `reversible = False` |
| Celery-Task `storage_tasks.migrate_photo_refs` | `app/tasks/storage_tasks.py:151-166` | manuell auslösbar, **`dry_run=False` per Default**; in keinem Beat-Schedule (`app/tasks/__init__.py:120` plant nur `cleanup_orphaned_task_photos`) |
| CLI `python -m app.migrations.migrate_photo_refs` | `migrate_photo_refs.py:205-221` | schreibt ohne `--dry-run` |

Die Konsequenz aus Zeile 1: **Auf jeder Installation, die seit v0003 gestartet ist, ist
Regel 4 bereits gelaufen.** Wo Storage-Key-Referenzen existierten, sind sie jetzt
fremde ULIDs, die zu nichts auflösen. Das ist kein zukünftiges Risiko, sondern ein
möglicherweise eingetretener Datenschaden — dessen Umfang niemand gemessen hat.

**Die Tests zertifizieren die falsche Prämisse.**
`tests/unit/migrations/test_migrate_photo_refs.py:20` (`test_s3_url_is_reduced_to_attachment_id`)
und `:23` (`test_storage_key_is_reduced_to_attachment_id`) behaupten als Sollverhalten
genau die Reduktion, die der Modulkopf als falsch bezeichnet. Ein Bearbeiter, der die
Suite grün hält, hält den Defekt am Leben. Das ist die Klasse „Prüfung leistet weniger,
als sie behauptet — auch positiv".

### #1437 — zwei Fehler tragen denselben Code, und der Client muss einen davon parsen

`photo_router.py:180` — `task_service.get_task(key, tenant_key=…)` wirft
`NotFoundError("Task", key)` (`common/exceptions.py:24-31`, `error_code="ENTITY_NOT_FOUND"`).
`:190` und `:203`/`:228` werfen `AttachmentNotFoundError` (`exceptions.py:416-420`),
das von `NotFoundError` erbt und **denselben** `error_code` trägt. Sie unterscheiden sich
nur im `message`-Text.

`PhotoUpload.tsx:198-199` reagiert auf **jedes** 404 mit De-Staging aus der Liste. Der
Kommentar darüber (`:190-197`, „Known limitation") beschreibt die Folge selbst: Ist die
*Aufgabe* verschwunden, wurde nichts gelöscht, der Eintrag verschwindet trotzdem aus
der Liste, und das Attachment verwaist. Das Fenster ist schmal (Aufgabe muss zwischen
Seitenaufruf und Klick verschwinden), aber offen.

Der zweite Fall aus dem Issue: ein Foto, das bereits in `photo_refs` einer
abgeschlossenen Aufgabe steht, wird über diese Route gelöscht (`:174-177`), und die
Referenz dangelt. Die Docstring nennt das ausdrücklich denselben Zustand, den ein
manuelles `DELETE /attachments/{id}` immer erzeugt hat. Es gibt **keine
Reparaturoberfläche**: „the orphan sweep is the general reconciliation and ships
disabled" (`:170-171`).

## Strukturbefund über die Mitglieder hinweg (§E)

**Klassifikation: Symptom-Cluster.** Grundursache: **Dokumentschlüssel und Storage-Key
sind zwei unabhängige Identitäten, und keine Komponente besitzt die Versöhnung von
`photo_refs` mit dem Katalog.** Der Resolver toleriert beide Schreibweisen; die
Migration zerstört eine davon; der Löschpfad hinterlässt Referenzen, die zu nichts
auflösen; und der Client entscheidet aus einem Statuscode, ob er eine Referenz
vergessen darf.

Daraus folgt für den Plan: **nicht** zwei Symptome reparieren (Regel 4 löschen, einen
Error-Code ergänzen), sondern die Versöhnung an **einer** Stelle besitzen lassen und
die zwei Symptome als deren Konsequenzen schließen.

### Prozessbefund

Bereits als **#1456** angelegt (aus Gruppe `2026-09-16-write-route-guard`); diese Gruppe
liefert zwei der vier Fundstellen (`migrate_photo_refs.py:55`, `PhotoUpload.tsx:190`).
Neu hinzu kommt hier eine schärfere Form derselben Klasse: **Tests, die die als falsch
erkannte Prämisse als Sollverhalten festschreiben** (`test_migrate_photo_refs.py:20,23`).
Ein Selbst-Widerruf im Modulkopf und ein grüner Test für das widerrufene Verhalten in
derselben Codebasis — das ist der Zustand, den #1456s Guard röten muss. Wird als
Kommentar an #1456 ergänzt, nicht als eigenes Issue.

## Stufe und Scheiben

**Stufe 3.** Die Gruppe ändert (a) einen veröffentlichten Fehlervertrag (NFR-006-Envelope,
`ENTITY_NOT_FOUND`) und (b) Bestandsdaten über eine irreversible Migration.

**Designentscheidung (das *Wo*, vor dem *Wie*) — vom Operator zu treffen, siehe offene
Fragen.**

**Unabhängig verifizierbare Scheiben**, in Abhängigkeitsreihenfolge:

1. **Scheibe 1 — Regel 4 stilllegen und die Tests umdrehen (#1438, Teil 1).**
   `normalize_photo_ref` lässt einen Storage-Key **unverändert** (Regel 5 statt 4). Die
   beiden Tests `:20` und `:23` werden zuerst so umgeschrieben, dass sie das *richtige*
   Verhalten verlangen — und sind damit gegen den heutigen Code **rot**. `run()`,
   der Celery-Task und die CLI bekommen `dry_run=True` als Default; Schreiben wird eine
   ausdrückliche Entscheidung.
2. **Scheibe 2 — die Versöhnung bekommt einen Besitzer (#1438 Teil 2 + #1437 Reparatur).**
   Eine neue versionierte Migration `v00NN_reconcile_photo_refs` mit genau einer Regel:
   Für jeden `photo_refs`-Eintrag, der zu keinem `_key` des Mandanten auflöst, aber zum
   `storage_key`-Stamm genau eines Attachments desselben Mandanten — schreibe ihn auf
   dessen `_key` um (repariert, was v0003 zerstört hat). Für jeden Eintrag, der zu
   **nichts** auflöst — melde ihn im Report, entferne ihn **nicht** (dieselbe
   Nie-fallenlassen-Regel wie `test_never_drops_values`). Diese Migration ist der eine
   Ort, der „was bedeutet diese Referenz" beantwortet; der Resolver-Ausdruck aus
   `attachment_repository.py:516-522` wird wiederverwendet, nicht dupliziert.
3. **Scheibe 3 — unterscheidbare Fehler (#1437 Signal).** Der Client darf nur de-stagen,
   wenn das *Attachment* fehlt. Form siehe offene Frage 1.

**Verifikationsdurchgang durch einen fremden Kontext:** `code-review` gegen den Kopf des
Integrationsbranches nach Scheibe 3, aus dem Worktree.

## Modus

**Modus A — Einzelstrang.** Kein Mitglied ist herauslösbar im Sinne des Kriteriums:
beide sind `fix`, keines hängt von etwas außerhalb der Gruppe ab, kein ausstehendes
Review kann eines ablehnen. Die drei Scheiben bauen aufeinander auf — Scheibe 2 nutzt
Scheibe 1s Nicht-Umschreiben, Scheibe 3s Frontend-Verhalten setzt Scheibe 2s Garantie
voraus, dass ein nicht auflösbarer Eintrag gemeldet statt vergessen wird. Sub-Branches
würden hier nur Merge-Arbeit herstellen.

## Vollständigkeitsmatrix

Spalten wie in Gruppe `write-route-guard` aus dem Repository abgeleitet.

| Mitglied | Backend-Quellcode | Frontend-Quellcode | Spec | Tests | Doku | Config / Workflows | Generierter Katalog |
|---|---|---|---|---|---|---|---|
| **#1438** | `migrations/migrate_photo_refs.py:80-110` Regel 4 → verbatim; `run():155`, `storage_tasks.py:151`, `main():205` `dry_run=True` Default; neue `versions/v00NN_reconcile_photo_refs.py`; Prüfung: `pytest tests/unit/migrations/` | *nicht zutreffend* — keine UI berührt die Migration | `spec/nfr/NFR-013*.md` — Referenzformen und die Versöhnungsregel benennen; Prüfung: `task precommit` | `test_migrate_photo_refs.py:20,23` **umgedreht** (rot zuerst); neuer Test für die Reconcile-Migration mit beiden Identitäten im Fixture; Mutationsbeweis: Resolver-Ausdruck leeren → Test rot; Prüfung: derselbe pytest-Lauf | `docs/de/deployment/` Migrations-Seite, falls sie v0003 nennt (zu prüfen); sonst *nicht zutreffend* | *nicht zutreffend* — Migrationen laufen über den bestehenden Startpfad | *nicht zutreffend* |
| **#1437** | `common/exceptions.py:416` — unterscheidbares Signal (Form nach Entscheidung 1); `photo_router.py` Docstring `:168-181` ohne den Verweis auf die deaktivierte Reconciliation; Prüfung: `pytest tests/unit/api/ tests/api/` | `PhotoUpload.tsx:198` — De-Staging nur bei fehlendem *Attachment*; `api/client` falls das Signal ein neues Feld ist; Prüfung: `vitest run src/frontend/src/test/components/PhotoUpload.test.tsx` | `spec/nfr/NFR-006*.md` — falls Entscheidung 1 den Envelope erweitert; sonst *nicht zutreffend* mit Verweis auf die Entscheidung | Backend: Test, dass Task-404 und Attachment-404 auf der Route unterscheidbar sind (rot zuerst); Frontend: Test, dass ein Task-404 den Eintrag **behält** und einen Fehler zeigt | *nicht zutreffend* — kein Endnutzerdokument beschreibt Fehlercodes | *nicht zutreffend* | *nicht zutreffend* |

## Risiken

- **Scheibe 2 ist eine irreversible Datenänderung** auf Bestand, dessen Schaden niemand
  gemessen hat. Gegenmaßnahme: die Migration läuft **zuerst als `dry_run`** gegen den
  Dev-Cluster (kind) und der Report wird im Artefakt festgehalten, bevor sie scharf
  geht. Eine Referenz, die zu **mehreren** Attachments per Storage-Stamm passt, wird
  nicht umgeschrieben, sondern gemeldet.
- **Die Ledger-Semantik:** v0003 bleibt im Ledger (`applied`) und wird nicht angefasst;
  eine neue Version repariert. Ein Rückbau von v0003 aus `versions/` würde
  `applied_versions` nicht ändern und nur die Discovery verwirren.
- **Ein Error-Code-Wechsel bricht Clients**, die auf `ENTITY_NOT_FOUND` matchen. Deshalb
  offene Frage 1: additiv statt ersetzend.
- **`dry_run=True` als Default ändert das Verhalten des Celery-Tasks** für jeden, der ihn
  heute manuell auslöst. Das ist gewollt und wird im Task-Docstring gesagt.

## Bewusst außerhalb des Scopes

- Der **Orphan-Sweep** (`cleanup_orphaned_task_photos`, „ships disabled") wird nicht
  aktiviert. Er beantwortet die Gegenfrage — „welches Attachment referenziert niemand"
  — und ist ein eigener Posten mit eigener Risikoabwägung (Löschen von Speicher).
- **Plant-Galerie-Referenzen** (`plant.photo_refs`, `cover_photo_ref`) werden von der
  Reconcile-Migration mit erfasst, weil `PHOTO_REF_COLLECTIONS` alle Träger listet —
  aber der Galerie-Löschpfad (`PlantPhotoService.delete`) wird nicht geändert.
- **#1425** (Galerie-Delete für Grower) teilt nur das Wort „Attachment"; Einzellauf.
- Das Messen des tatsächlichen Schadens auf **Produktion** ist ein Betreiberlauf der
  Migration im `dry_run`, kein Teil dieses PR-Strangs.

## Operator-Entscheidungen (2026-09-16, vor der Umsetzung)

1. **404-Signal: additiv.** `NotFoundError` trägt den Entitätsnamen strukturiert in
   `details[0].entity`; `error_code` bleibt `ENTITY_NOT_FOUND`. Kein Client bricht;
   `PhotoUpload` de-staged nur bei `entity == "attachment"`.
2. **Nicht auflösbare Einträge: melden, nie löschen.** Dieselbe Regel wie
   `test_never_drops_values`. Löschen bleibt dem Orphan-Sweep mit eigener Freigabe.
3. **Dry-Run gegen kind vor dem Scharfschalten: ja.** Der Report der Reconcile-Migration
   wird unter „Ergebnisse je Scheibe" festgehalten, bevor Scheibe 2 als abgeschlossen gilt.

## Ergebnisse je Scheibe

*(wird während der Umsetzung gefüllt — tatsächliche Prüfausgaben, nicht Behauptungen)*

### Scheibe 1 — umgesetzt 2026-09-16

**Rot zuerst** (`78d01441d`, nur Tests, Produktionscode unverändert):

```
FAILED tests/unit/migrations/test_migrate_photo_refs.py::TestNormalizePhotoRef::test_s3_url_is_kept_verbatim
FAILED tests/unit/migrations/test_migrate_photo_refs.py::TestNormalizePhotoRef::test_storage_key_is_kept_verbatim
FAILED tests/unit/migrations/test_migrate_photo_refs.py::TestNormalizePhotoRef::test_thumbnail_storage_key_is_kept_verbatim
FAILED tests/unit/migrations/test_migrate_photo_refs.py::TestNormalizeRefs::test_a_storage_key_entry_is_not_counted_as_changed
FAILED tests/unit/migrations/test_migrate_photo_refs.py::TestCliDryRunDefault::test_no_argument_means_dry_run
FAILED tests/unit/migrations/test_migrate_photo_refs.py::TestCliDryRunDefault::test_write_flag_turns_writing_on
FAILED tests/unit/migrations/test_migrate_photo_refs.py::TestCliDryRunDefault::test_explicit_dry_run_wins_over_write
FAILED tests/unit/migrations/test_migrate_photo_refs.py::TestRun::test_run_writes_nothing_unless_asked_to
FAILED tests/unit/migrations/test_migrate_photo_refs.py::TestRun::test_a_storage_key_document_is_left_alone
FAILED tests/unit/tasks/test_storage_tasks.py::test_migrate_photo_refs_task_defaults_to_dry_run
10 failed, 14 passed
```

**Grün danach:** `tests/unit/migrations/ tests/unit/tasks/` → `946 passed, 32 skipped`.

**Mutationsbeweis der drei `dry_run`-Defaults** (je zurück auf den alten Wert, dann
zurückgesichert per `cp`):

| Mutation | Ergebnis |
|---|---|
| `run(..., dry_run=False)` | `FAILED ...::TestRun::test_run_writes_nothing_unless_asked_to` — `1 failed, 19 passed` |
| Celery `migrate_photo_refs(..., dry_run=False)` | `FAILED ...::test_migrate_photo_refs_task_defaults_to_dry_run` — `1 failed, 3 passed` |
| CLI-Polarität zurück auf `return "--dry-run" in args` | `FAILED ...::TestCliDryRunDefault::test_no_argument_means_dry_run` — `1 failed, 19 passed` |

**Gegenprobe der Superset-Eigenschaft gemessen statt argumentiert.** Die Aussage
„`aql_photo_ref_candidates` enthält immer, was `normalize_photo_ref` antwortet"
(`tests/integration/test_aql_reference_normalisation.py`) überspringt sich ohne
ArangoDB lautlos. Gegen eine eigens gestartete `arangodb:3.12`: `31 passed`; die
gesamte `tests/integration/` → `143 passed`.

**Nicht geändert, weil nachgemessen wahr:** die Prosa in
`PhotoUpload.test.tsx:21`, `api/endpoints/tasks.ts:261` und
`photo_router.py:30` behauptet, der Job schreibe *die URI-Form* auf Ids zurück —
genau die Regel, die bleibt. Korrigiert wurden dagegen zwei Stellen, die nach
der Änderung falsch waren (`normalize_photo_ref` reduziere auf den ULID-Stamm)
und zwei, die schon vorher falsch waren (`migrate_photo_refs` sei „manual" —
`v0003` läuft über `run_pending_migrations` beim Start jeder Installation,
`app/main.py:112`).

### Scheibe 2 — umgesetzt 2026-09-16

Neue Migration **`v0046_reconcile_photo_refs`** (`src/backend/app/migrations/versions/`).
`v0003` bleibt unangetastet im Ledger.

**Rot zuerst** (`05d4774c7`, nur die Testdatei — der Besitzer existiert noch nicht):

```
ImportError while importing test module '.../tests/unit/migrations/versions/test_v0046_reconcile_photo_refs.py'.
tests/unit/migrations/versions/test_v0046_reconcile_photo_refs.py:30: in <module>
    from app.migrations.versions.v0046_reconcile_photo_refs import (
E   ModuleNotFoundError: No module named 'app.migrations.versions.v0046_reconcile_photo_refs'
1 error in 1.07s
```

**Grün danach** (`f9f8a1ca2`):

```
tests/unit/migrations/versions/test_v0046_reconcile_photo_refs.py  18 passed
tests/unit/migrations/versions/ tests/unit/migrations/framework/ tests/unit/data_access/arango/  1022 passed
tests/integration/  149 passed   (gegen arangodb:3.12, eigens gestartet, danach gestoppt)
```

**Mutationsbeweis — drei Schnitte, jeder gegen den gesicherten Stand (`cp`, nicht `git stash`):**

| Mutation | Ergebnis |
|---|---|
| `aql_storage_key_stem` gibt den Ausdruck unreduziert zurück (`return f"{expression}"`) | `9 failed, 9 passed` — u. a. `test_the_stem_v0003_wrote_is_rewritten_onto_the_document_key`, `test_re_running_changes_nothing` |
| Separatoren vertauscht (`SPLIT(…, ".")` / `SPLIT(…, "/")`) | `6 failed, 12 passed` — `repaired=0`, der reparierte Eintrag wird als `unresolved` gemeldet |
| Reparaturregel entfernt (`ReferenceVerdict("repaired", …)` → `"unresolved"`) | `7 failed, 11 passed` — inkl. des reinen `plan_reference`-Tests |

Der erste Schnitt wirkt, weil das Unit-Double den Stamm **nicht kennt**: `_FakeAql`
liest die beiden Trenner per Regex aus dem Query-Text, den die Migration ihm
übergibt. Ein Double mit eigener Kopie der Regel wäre bei Mutation 1 und 2 grün
geblieben — genau die Klasse „Prüfung leistet weniger, als sie behauptet".

**Beim Bauen gemessen, Vorgabe korrigiert:** eine fehlende Trägerkollektion ließ die
Migration mit `AQL 1203 collection or view not found: plant_diary_entries` abbrechen
statt zu melden — auf einer teilbootstrapten oder restaurierten Datenbank wäre das ein
Startup-Abbruch. Jeder Scan hängt jetzt an `db.has_collection(...)` (Vorbild `v0010`).

**Dry-Run gegen den kind-Dev-Cluster** (`kind-kamerplanter`, ArangoDB 3.12.10, über
`kubectl port-forward svc/kamerplanter-arangodb 18529:8529` mit dem Code **dieses**
Worktrees — das Pod-Image ist älter als `v0043` und kennt `aql_storage_key_stem` nicht,
ein Pipe in den Pod hätte also eine zweite Kopie des Ausdrucks gebraucht, was genau die
Grundursache ist). Wörtlich:

```
server version: 3.12.10
2026-09-16 22:00:02 [info     ] reconcile_photo_refs  ambiguous=0 changed=0 dry_run=True repaired=0 scanned=3 unresolved=0
{
  "changed": 0,
  "details": {
    "ambiguous": [],
    "ambiguous_total": 0,
    "per_collection": {
      "plant_diary_entries": {
        "ambiguous": 0,
        "changed": 0,
        "repaired": 0,
        "scanned": 1,
        "unresolved": 0
      },
      "plant_instances": {
        "ambiguous": 0,
        "changed": 0,
        "repaired": 0,
        "scanned": 2,
        "unresolved": 0
      }
    },
    "repaired": 0,
    "unresolved": [],
    "unresolved_total": 0
  },
  "dry_run": true,
  "duration_ms": 0.0,
  "name": "reconcile_photo_refs",
  "precondition_unmet": false,
  "scanned": 3,
  "version": "0046"
}
```

**Der Nullbefund ist nicht vakuös** — die Gegenprobe im selben Lauf, lesend:

```
attachments: 3
 att: {'key': '219600',  'storage_key': 't/system-tenant/plant/2026/07/01KXAJS5WZ2AG6C1GMVYF1PQ14.jpg'}
 att: {'key': '1868160', 'storage_key': 't/system-tenant/diary/2026/08/01KZ94PZEXK8RCYA8XV47SDAGT.jpg'}
 att: {'key': '1903568', 'storage_key': 't/system-tenant/diary/2026/08/01KZ9PFWSPB6Y97DJZ5RAVJK5W.jpg'}
 ref:   {'col': 'plant_instances',     'key': '219579',  'refs': ['219600']}
 cover: {'col': 'plant_instances',     'key': '219579',  'cover': '219600'}
 ref:   {'col': 'plant_diary_entries', 'key': '1903596', 'refs': ['1903568']}
```

Die drei gezählten Träger sind genau diese drei Referenzen, und alle drei stehen
bereits als numerischer `_key` da. Damit ist auch die „Zwei Identitäten"-Prämisse auf
Echtdaten bestätigt: numerische Dokumentschlüssel neben unabhängigen ULID-Storage-Keys.
**Auf dem Dev-Cluster hat `v0003` keinen Schaden hinterlassen** — dort existierte keine
Storage-Key-Referenz, als `v0003` lief. Über Produktionsbestand sagt das nichts; das
bleibt ein Betreiberlauf im `dry_run` (bewusst außerhalb des Scopes).

Im Cluster wurde nichts geschrieben (`dry_run=True`, `changed=0`, ausschließlich
lesende Gegenprobe).

**Prosa nachgezogen:** `migrate_photo_refs.py`-Modulkopf und NFR-013 §2.2 nennen jetzt
`v0046_reconcile_photo_refs` samt beider Regeln und des geteilten
`aql_storage_key_stem`; die Docstring von `photo_router.py` sagt nicht mehr, der
deaktivierte Orphan-Sweep sei die Reconciliation — die Referenz-Versöhnung hat einen
Besitzer, der Sweep beantwortet die Gegenfrage und lässt eine Referenz auf eine
gelöschte Zeile bewusst stehen.
