# AP-02 / AP-03 / AP-13: Backend-Gap-Schließung (Export-Dispatch, Entry-Partial-Update, E-Mail-Digest)

> Arbeitspakete aus dem Kamerplanter-Code-Review (Fable 5, `spec/analysis/code-review-fable5-2026-07.md`).
> Befund-IDs: **GAP-B5 + INF-L3** (AP-2), **GAP-B9** (AP-3), **GAP-B8** (AP-13).
> Betroffene Anforderungen: **REQ-025/NFR-011** (DSGVO-Export & Retention), **REQ-013** (Pflanzdurchlauf), **REQ-030** (Notifications).
> Alle Pfade relativ zu `src/backend/`, sofern nicht anders angegeben.

---

# AP-2 (GAP-B5, INF-L3): DSGVO-Export an Celery dispatchen + Retention-Task-Härtung

## 1. Ziel & betroffene Anforderung

### Ziel
Ein DSGVO-Datenexport (Art. 15/20) wird nach `POST /api/v1/privacy/exports` tatsächlich asynchron
verarbeitet. Heute legt `PrivacyService.request_data_export` nur den `DataExportRequest` mit
`status="pending"` an — der Celery-Task `retention.process_data_export` existiert, wird aber **nie
dispatcht**. Export-Requests bleiben dauerhaft `pending` (Art.-15-Risiko: Betroffenenrecht wird
faktisch nicht bedient).

Nach diesem Arbeitspaket gilt:
- Jeder neu angelegte Export-Request dispatcht `retention.process_data_export` (Worker flippt
  `pending → processing`; der weitere Ausbau des Manifest-Builds ist separat, siehe §3.4).
- Ein fehlgeschlagener Dispatch (Broker down) lässt die API-Anfrage **nicht** mit 500 scheitern;
  ein stündlicher Beat-Safety-Net-Task re-dispatcht liegengebliebene `pending`-Exports.
- Die Retention-Tasks haben `autoretry_for` + Backoff (INF-L3), statt beim ersten transienten
  Fehler hart zu failen.
- Die veralteten TODO-Kommentare (`privacy_service.py:170`, `:358`) und die falsche
  Klassen-Docstring-Aussage („the actual ``celery.send_task`` calls are intentionally left out")
  sind entfernt bzw. korrigiert.

### Betroffene Anforderung
- **REQ-025 (Datenschutz & Betroffenenrechte)** — Self-Service-Export Art. 15/20:
  `spec/req/REQ-025_Datenschutz.md` (Export-Workflow, 72-h-Download-Fenster).
- **NFR-011 (Retention)** — R-05 (Export-Files 72 h), Celery-getriebene Retention-Pipeline.

## 2. Root-Cause-Analyse

1. **Fehlender Dispatch** — `app/domain/services/privacy_service.py:170`:
   ```python
   # TODO(NFR-011): celery dispatch_async("process_data_export", export_key=created.key)
   return created
   ```
   Der Task ist vollständig vorhanden und registriert:
   `app/tasks/retention_tasks.py:33` (`@celery_app.task(name="retention.process_data_export")`),
   Modul ist in `app/tasks/__init__.py:22` im `include` gelistet. Es gibt aber **keinen** Beat-Eintrag
   und keinen Producer-Aufruf — bestätigt per Grep: kein `send_task(`/`delay(`/`apply_async(` auf
   diesen Task im gesamten `app/`-Baum.

2. **Veralteter TODO** — `privacy_service.py:358-359`:
   ```python
   # TODO(NFR-011): celery beat task `execute_scheduled_erasures`
   # picks up scheduled items and performs hard-delete.
   ```
   Dieser Beat-Task existiert längst: `app/tasks/retention_tasks.py:64` +
   Beat-Eintrag `retention-execute-erasures-daily` in `app/tasks/__init__.py:114-117`
   (`crontab(hour=4, minute=0)`). Der TODO ist reine Irreführung.

3. **Falsche Klassen-Docstring** — `privacy_service.py:71-75`:
   > "the actual ``celery.send_task`` calls are intentionally left out and tracked under NFR-011."
   Für die Erasure-Seite stimmt das nicht mehr (Beat vorhanden); für die Export-Seite wird es mit
   diesem AP falsch.

4. **Fehlende Retries (INF-L3)** — alle vier Tasks in `retention_tasks.py` sind nackte
   `@celery_app.task(name=...)` ohne `bind`/`max_retries`/`autoretry_for`. Projektübliche Muster
   existieren bereits:
   - `app/tasks/storage_tasks.py:77` → `@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)`
   - `app/tasks/pest_image_tasks.py:145-147` → `max_retries=3, autoretry_for=(ConnectionError, TimeoutError)`

5. **Dispatch-Muster im Projekt** (als Vorlage): Services dispatchen per **Lazy-Import + `.delay()`**,
   um Import-Zyklen zu vermeiden und Celery zur Service-Konstruktion optional zu halten:
   - `app/domain/services/attachment_service.py:262-269` (`_dispatch_thumbnails` → `generate_thumbnails.delay(...)`)
   - `app/domain/services/pest_image_service.py:447-453` (Lazy-Import, `task.delay(contribution.key)`)

## 3. Lösungsdesign

### 3.1 Dispatch im Service (Lazy-Import + Fehler-Isolation)

Neue private Methode `PrivacyService._dispatch_export_processing`, aufgerufen am Ende von
`request_data_export`. Ein Broker-Ausfall darf den (bereits persistierten) Export-Request nicht
zerstören — der Request bleibt `pending` und wird vom Safety-Net (§3.2) aufgesammelt. Das weicht
bewusst vom ungeschützten `attachment_service`-Dispatch ab, weil hier ein gesetzliches
Betroffenenrecht hinter dem Call steht (Annahme der Anfrage > sofortige Verarbeitung).

### 3.2 Safety-Net: stündlicher Re-Dispatch liegengebliebener Exports

Neuer Beat-Task `retention.redispatch_stale_pending_exports` (stündlich, `:25`): findet
`DataExportRequest`-Dokumente mit `status == "pending"` und `requested_at < now - 15 min` und
dispatcht sie erneut. Dafür bekommt das Export-Repository eine Query-Methode
`list_stale_pending(cutoff_iso)`. Das macht den Fix selbstheilend gegen Broker-Ausfälle und gegen
den Alt-Bestand (bereits liegengebliebene `pending`-Exports in Prod werden automatisch nachgeholt).

### 3.3 Retry-Härtung (INF-L3)

| Task | Dekorator neu |
|---|---|
| `retention.process_data_export` | `bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=600, retry_jitter=True, max_retries=5` |
| `retention.execute_scheduled_erasures` | `bind=True, autoretry_for=(ConnectionError, TimeoutError), max_retries=3, default_retry_delay=300` |
| `retention.expire_email_change_requests` | `bind=True, autoretry_for=(ConnectionError, TimeoutError), max_retries=3, default_retry_delay=300` |
| `retention.expire_data_exports` | `bind=True, autoretry_for=(ConnectionError, TimeoutError), max_retries=3, default_retry_delay=300` |
| `retention.redispatch_stale_pending_exports` (neu) | `bind=True, autoretry_for=(ConnectionError, TimeoutError), max_retries=3, default_retry_delay=300` |

Begründung der Abstufung: `process_data_export` ist ein Fan-out-Task pro Nutzeranfrage — er darf
breit (auch ArangoDB-Fehler) retryen, da idempotent (Status-Guard `if export.status != "pending"`
in `privacy_service.py:629` macht Doppel-Läufe zu No-Ops). Die Beat-Tasks laufen ohnehin
stündlich/täglich erneut; dort genügt Retry auf transiente Transportfehler (Muster
`pest_image_tasks.py`). Die bestehenden `try/except + logger.exception + raise`-Blöcke bleiben —
`raise` füttert `autoretry_for`.

### 3.4 Scope-Abgrenzung
`PrivacyService.process_data_export` flippt derzeit nur `pending → processing`
(`privacy_service.py:616-646`, „Scaffolded transition"). Der vollständige Daten-Walk + Upload in
den Object-Storage (NFR-013-Adapter existiert inzwischen) ist **nicht** Teil von AP-2 — GAP-B5
adressiert den fehlenden Dispatch. Der Ausbau des Manifest-Builds ist als Folge-AP zu erfassen
(Verweis im Code-Kommentar bleibt bestehen).

## 4. Konkrete Änderungen pro Datei

### 4.1 `app/domain/services/privacy_service.py`

**(a) Klassen-Docstring korrigieren** (Z. 69-75) — vorher:
```python
    """Orchestrates GDPR rights (Art. 15/16/17/18/20/21) for a user.

    Heavy work that belongs to a Celery task (export-file generation,
    hard-delete after 90 days) is wired up here only up to the point where
    the dispatch would happen; the actual ``celery.send_task`` calls are
    intentionally left out and tracked under NFR-011.
    """
```
nachher:
```python
    """Orchestrates GDPR rights (Art. 15/16/17/18/20/21) for a user.

    Heavy work runs in Celery (``app.tasks.retention_tasks``): export
    processing is dispatched by :meth:`request_data_export`, hard-delete
    after the 90-day grace period runs via the daily
    ``retention.execute_scheduled_erasures`` beat task (NFR-011).
    """
```

**(b) Dispatch in `request_data_export`** (Z. 170-171) — vorher:
```python
        # TODO(NFR-011): celery dispatch_async("process_data_export", export_key=created.key)
        return created
```
nachher:
```python
        if created.key:
            self._dispatch_export_processing(created.key)
        return created
```

**(c) Neue private Methode** (direkt unter `request_data_export`):
```python
    def _dispatch_export_processing(self, export_key: str) -> None:
        """Enqueue the export worker (NFR-011).

        Lazy import avoids a hard import cycle (tasks import dependencies
        which import services) and keeps Celery optional at
        service-construction time. A broker outage must not fail the API
        request — the record stays ``pending`` and is re-dispatched by the
        hourly ``retention.redispatch_stale_pending_exports`` beat task.
        """
        try:
            from app.tasks.retention_tasks import process_data_export

            process_data_export.delay(export_key)
            logger.info("privacy_export_dispatch", export_key=export_key)
        except Exception as exc:  # noqa: BLE001 — broker outage is survivable
            logger.error(
                "privacy_export_dispatch_failed",
                export_key=export_key,
                error=str(exc),
            )
```

**(d) Veralteten TODO entfernen** (Z. 358-359) — vorher:
```python
        # TODO(NFR-011): celery beat task `execute_scheduled_erasures`
        # picks up scheduled items and performs hard-delete.
        return created
```
nachher:
```python
        # Hard-delete is performed by the daily beat task
        # ``retention.execute_scheduled_erasures`` (app/tasks/__init__.py).
        return created
```

### 4.2 `app/domain/interfaces/data_export_repository.py`

Neue abstrakte Methode (Signatur analog `expire_old`):
```python
    @abstractmethod
    def list_stale_pending(self, cutoff_iso: str) -> list[DataExportRequest]:
        """Return pending exports requested before ``cutoff_iso`` (re-dispatch candidates)."""
```

### 4.3 `app/data_access/arango/data_export_repository.py`

Implementierung (AQL, Muster der bestehenden Methoden):
```python
    def list_stale_pending(self, cutoff_iso: str) -> list[DataExportRequest]:
        query = """
        FOR doc IN @@collection
          FILTER doc.status == "pending"
          FILTER doc.requested_at != null AND doc.requested_at < @cutoff
          SORT doc.requested_at ASC
          LIMIT 100
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={"@collection": self._collection_name, "cutoff": cutoff_iso},
        )
        return [DataExportRequest(**self._from_doc(doc)) for doc in cursor]
```
(Feld-/Attributnamen an die konkrete Repo-Basisklasse anpassen; `LIMIT 100` als Schutz gegen
pathologische Rückstaus — der Task läuft stündlich.)

### 4.4 `app/tasks/retention_tasks.py`

**(a) Dekoratoren härten** — vorher (exemplarisch Z. 33):
```python
@celery_app.task(name="retention.process_data_export")
def process_data_export(export_key: str) -> dict:
```
nachher:
```python
@celery_app.task(  # type: ignore[misc]
    name="retention.process_data_export",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=5,
)
def process_data_export(self, export_key: str) -> dict:
```
Analog für die drei Beat-Tasks (Tabelle §3.3; `bind=True` ⇒ jeweils `self` als ersten Parameter
ergänzen). Die bestehenden `except Exception as exc: ... raise`-Blöcke bleiben unverändert
(sie triggern `autoretry_for`; ruff-format-Falle beachten: `except`-Tupel immer **mit** `as exc`
schreiben, siehe Risiko §7).

**(b) Neuer Safety-Net-Task** (ans Dateiende, Docstring-Kopf der Datei um den Task ergänzen):
```python
STALE_EXPORT_REDISPATCH_AFTER_MINUTES = 15


@celery_app.task(  # type: ignore[misc]
    name="retention.redispatch_stale_pending_exports",
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    max_retries=3,
    default_retry_delay=300,
)
def redispatch_stale_pending_exports(self) -> dict:
    """Re-enqueue pending exports whose original dispatch was lost.

    Safety net for broker outages during ``PrivacyService.request_data_export``
    and for legacy ``pending`` records created before the dispatch existed.
    Idempotent: the worker skips non-``pending`` exports.
    """
    from datetime import timedelta

    from app.common.dependencies import get_data_export_repo

    repo = get_data_export_repo()
    cutoff = datetime.now(UTC) - timedelta(minutes=STALE_EXPORT_REDISPATCH_AFTER_MINUTES)
    stale = repo.list_stale_pending(cutoff.isoformat())
    for export in stale:
        if export.key:
            process_data_export.delay(export.key)
    if stale:
        logger.info("retention.redispatch_stale_pending_exports", redispatched=len(stale))
    return {"redispatched": len(stale)}
```

### 4.5 `app/tasks/__init__.py`

Neuer Beat-Eintrag im NFR-011-Block (nach Z. 125):
```python
        "retention-redispatch-stale-exports-hourly": {
            "task": "retention.redispatch_stale_pending_exports",
            "schedule": crontab(minute=25),  # every hour at :25
        },
```

## 5. Neue Funktionen / Signaturen (Zusammenfassung)

| Ort | Signatur |
|---|---|
| `PrivacyService` | `def _dispatch_export_processing(self, export_key: str) -> None` |
| `IDataExportRepository` | `def list_stale_pending(self, cutoff_iso: str) -> list[DataExportRequest]` |
| `ArangoDataExportRepository` | dito (AQL-Implementierung) |
| `app/tasks/retention_tasks.py` | `def redispatch_stale_pending_exports(self) -> dict` (Task `retention.redispatch_stale_pending_exports`) |
| alle Retention-Tasks | `bind=True` ⇒ `def <task>(self, ...)` |

## 6. Testplan

**`tests/unit/domain/services/test_privacy_service.py`** (bestehende Datei erweitern; Fake-Repos
vorhanden):
1. `test_request_data_export_dispatches_task` — `app.tasks.retention_tasks.process_data_export.delay`
   per `monkeypatch`/`MagicMock` ersetzen; nach `request_data_export` wurde `.delay(created.key)`
   genau einmal aufgerufen.
2. `test_request_data_export_survives_dispatch_failure` — `.delay` wirft `ConnectionError`; der
   Aufruf liefert trotzdem den erstellten Request (`status == "pending"`), keine Exception.
3. `test_request_data_export_blocked_when_active_exists` — Regressionsschutz (bestehende
   Validierung unverändert).

**`tests/unit/tasks/test_retention_tasks.py`** (bestehende Datei, Mock-Muster
`_mock_dependencies` + `patch("asyncio.run")` wiederverwenden):
4. `TestRedispatchStalePendingExports::test_redispatches_each_stale_export` —
   `get_data_export_repo().list_stale_pending` liefert 2 Fakes mit `key`; assert
   `process_data_export.delay` 2× (Task-Funktion patchen).
5. `TestRedispatchStalePendingExports::test_empty_returns_zero` — leere Liste ⇒
   `{"redispatched": 0}`.
6. `test_process_data_export_has_retry_config` — Registrierungs-Assertions:
   `process_data_export.max_retries == 5`, `Exception in process_data_export.autoretry_for`,
   `retry_backoff` gesetzt (analog `tests/unit/tasks/test_celery_registration.py`-Stil).
7. Bestehende Tests der Datei an `bind=True` anpassen (Aufruf bleibt `process_data_export("export_1")`
   — Celery-Task-Objekte binden `self` selbst; nur falls Tests `.run()`/direkt die Funktion
   aufrufen, `self`-Dummy ergänzen).

**`tests/unit/tasks/test_celery_registration.py`**: neuen Task-Namen
`retention.redispatch_stale_pending_exports` in die Registrierungs-/Beat-Schedule-Assertions
aufnehmen (Beat-Key `retention-redispatch-stale-exports-hourly`).

**Repo-Test** (`tests/unit/data_access/…` falls dort ein Arango-Mock-Muster existiert, sonst
Integrationstest): `list_stale_pending` filtert `status=="pending"` + `requested_at < cutoff`.

## 7. Akzeptanzkriterien

- [ ] `POST /api/v1/privacy/exports` erzeugt einen Request **und** enqueued
      `retention.process_data_export` mit dem Export-Key.
- [ ] Broker-Ausfall beim Dispatch ⇒ API antwortet weiterhin 2xx, Log-Event
      `privacy_export_dispatch_failed`, Request bleibt `pending`.
- [ ] Beat-Schedule enthält `retention-redispatch-stale-exports-hourly`; der Task re-dispatcht
      ausschließlich `pending`-Exports älter als 15 min.
- [ ] Alle Retention-Tasks besitzen `autoretry_for` + Retry-Konfiguration gemäß Tabelle §3.3.
- [ ] Kein `TODO(NFR-011)` mehr in `privacy_service.py`; Klassen-Docstring beschreibt den
      Ist-Zustand.
- [ ] `pytest src/backend/tests/unit/tasks/test_retention_tasks.py tests/unit/domain/services/test_privacy_service.py` grün; ruff clean.

## 8. Risiko

- **Doppel-Dispatch** (Original + Safety-Net im Rennen): unkritisch — der Worker ist idempotent
  (`status != "pending"` ⇒ Skip, `privacy_service.py:629-635`). Restrisiko: zwei Worker greifen
  *gleichzeitig* denselben `pending`-Export; beide flippen auf `processing` — harmlos, solange der
  Task nur den Status setzt. Beim späteren Manifest-Build-AP muss ein Claim (Compare-and-Swap auf
  `status`) ergänzt werden — als Hinweis im Folge-AP notieren.
- **`autoretry_for=(Exception,)`** bei `process_data_export` retryt auch permanente Fehler
  (z. B. Pydantic-Bug) — begrenzt durch `max_retries=5` + Backoff; Log via `logger.exception`
  bleibt erhalten.
- **ruff-format-Falle** (Projekt-Memory): `except (ConnectionError, TimeoutError):` ohne `as`
  wird von ruff format 0.15.12 zu Syntaxfehler zerlegt — in `autoretry_for`-Tupeln irrelevant,
  aber in neuen `except`-Blöcken immer `as exc` verwenden.
- **Alt-Bestand in Prod**: liegengebliebene `pending`-Exports werden nach Deploy binnen 1 h
  automatisch nachgeholt — bewusst, aber im PR-Text erwähnen (plötzliche Task-Welle möglich;
  `LIMIT 100` deckelt).

---

# AP-3 (GAP-B9): `PlantingRun.update_entry` — Partial-Update ohne `species_key`-Placeholder

## 1. Ziel & betroffene Anforderung

### Ziel
`PUT /api/v1/t/{tenant}/planting-runs/{key}/entries/{entry_key}` mit einem Teil-Body (z. B. nur
`{"quantity": 5}`) darf bestehende Felder **nicht** verlieren. Heute überschreibt der Router
fehlende Pflichtfelder still mit Dummies: `species_key="placeholder"`, `quantity=1`,
`id_prefix="XX"` — Datenkorruption im Kern der REQ-013-Gruppenplanung (u. a. bricht danach
`create_plants`/`get_phase_timeline`, weil `species_key` auf eine nicht existente Art zeigt).

Nach diesem Arbeitspaket gilt:
- Partial-Update: nur explizit gesendete Felder werden geändert; nicht gesendete bleiben erhalten.
- Explizites `null` für nullable Felder (`cultivar_key`, `spacing_cm`, `notes`) löscht den Wert.
- Explizites `null` für Pflichtfelder (`species_key`, `quantity`, `id_prefix`) ⇒ **422**.
- Bei geändertem `species_key` wird die `entry_for_species`-Edge nachgezogen (heute wird sie nur
  in `create_entry` angelegt und in `delete_entry` gelöscht — nie aktualisiert).

### Betroffene Anforderung
- **REQ-013 (Pflanzdurchlauf)** — Entry-Verwaltung im Status `planned`; `species_key` ist die
  fachliche Grundlage für Batch-Create, Phase-Timeline und `planned_quantity`.

## 2. Root-Cause-Analyse

`app/api/v1/planting_runs/tenant_router.py:159-176`:
```python
def update_entry(...):
    service.get_run(key, tenant_key=ctx.tenant_key)
    data = body.model_dump(exclude_none=True)
    entry = PlantingRunEntry(
        species_key=data.get("species_key", "placeholder"),
        quantity=data.get("quantity", 1),
        id_prefix=data.get("id_prefix", "XX"),
        **{k: v for k, v in data.items() if k not in ("species_key", "quantity", "id_prefix")},
    )
    updated = service.update_entry(key, entry_key, entry)
```
Drei Ursachen:
1. **Schema erlaubt Partial** (`EntryUpdate`, `app/api/v1/planting_runs/schemas.py:55-61`: alle
   Felder `| None = None`), aber der Router baut daraus ein **vollständiges** `PlantingRunEntry`
   (Pflichtfelder `species_key`, `quantity`, `id_prefix`, `app/domain/models/planting_run.py:18-28`)
   und stopft die Lücken mit Literalen.
2. **Service ersetzt statt merged**: `PlantingRunService.update_entry`
   (`app/domain/services/planting_run_service.py:163-182`) lädt `existing` nur für den 404-Check
   und reicht das Router-Objekt unverändert ans Repo durch.
3. **Repo persistiert die Dummies**: `ArangoPlantingRunRepository.update_entry`
   (`app/data_access/arango/planting_run_repository.py:115-124`) dumpt mit `exclude_none=True`
   und schreibt `species_key="placeholder"` etc. in die Collection. Zusatzbefund: die in
   `create_entry` angelegte Edge `entry_for_species` (Z. ~93: `self.link_entry_to_species(...)`)
   wird bei Species-Wechsel nicht angepasst → Graph-Drift.

**Vergleichsmuster im selben Service**: `update_run` (`planting_run_service.py:107-114`) macht es
richtig — lädt den Bestand, wendet nur `allowed_fields` an. Dieses Muster wird auf
`update_entry` übertragen.

## 3. Lösungsdesign

1. **Router** dumpt mit `exclude_unset=True` (nicht `exclude_none` — sonst ist explizites
   `notes: null` nicht von „nicht gesendet" unterscheidbar) und übergibt das **dict** an den
   Service. Die Signatur des Service wechselt von „fertiges Entry-Objekt" auf „Patch-Dict" —
   analog `update_run(key, data: dict)` und `PlantDiaryService.update_entry(key, data: dict)`.
2. **Service** merged das Patch-Dict auf das geladene `existing`-Entry:
   - `allowed_fields = {"species_key", "cultivar_key", "quantity", "id_prefix", "spacing_cm", "notes"}`
   - `None` für ein Pflichtfeld (`species_key`, `quantity`, `id_prefix`) ⇒
     `ValidationError` (`app/common/exceptions.py:127`, mappt auf 422).
   - Merge über `existing.model_copy(update=...)` + Re-Validierung via
     `PlantingRunEntry.model_validate(...)`, damit Feld-Constraints (`quantity ge=1`,
     `id_prefix`-Pattern) weiterhin greifen.
3. **Repo** `update_entry`:
   - dumpt **ohne** `exclude_none` (damit explizit gelöschte nullable Felder als `null`
     geschrieben werden; ArangoDB-`update` merged sonst und behält den Altwert),
     `_key`/`created_at` werden wie bisher nicht angefasst (`_key` poppen; `created_at` kommt aus
     dem geladenen Bestand mit korrektem Wert mit — unschädlich).
   - zieht bei geändertem `species_key` die `entry_for_species`-Edge nach.
4. Alle weiteren Aufrufer geprüft: `update_entry` des PlantingRun-Repos wird nur vom
   PlantingRun-Service benutzt; der Service nur vom Tenant-Router (Grep §2). Kein weiterer
   Call-Site-Umbau nötig.

## 4. Konkrete Änderungen pro Datei

### 4.1 `app/api/v1/planting_runs/tenant_router.py` (Z. 159-176)

vorher:
```python
    service.get_run(key, tenant_key=ctx.tenant_key)
    data = body.model_dump(exclude_none=True)
    entry = PlantingRunEntry(
        species_key=data.get("species_key", "placeholder"),
        quantity=data.get("quantity", 1),
        id_prefix=data.get("id_prefix", "XX"),
        **{k: v for k, v in data.items() if k not in ("species_key", "quantity", "id_prefix")},
    )
    updated = service.update_entry(key, entry_key, entry)
    return _entry_response(updated)
```
nachher:
```python
    service.get_run(key, tenant_key=ctx.tenant_key)
    data = body.model_dump(exclude_unset=True)
    updated = service.update_entry(key, entry_key, data)
    return _entry_response(updated)
```
(Import `PlantingRunEntry` bleibt — wird von `add_entry`/`create_run` weiter genutzt.)

### 4.2 `app/domain/services/planting_run_service.py` (Z. 163-182)

vorher:
```python
    def update_entry(
        self,
        run_key: PlantingRunKey,
        entry_key: str,
        entry: PlantingRunEntry,
    ) -> PlantingRunEntry:
        run = self.get_run(run_key)
        if run.status != PlantingRunStatus.PLANNED:
            raise InvalidRunStateError("update_entry", run.status.value)
        existing = self._repo.get_entry_by_key(entry_key)
        if existing is None:
            raise NotFoundError("PlantingRunEntry", entry_key)
        updated = self._repo.update_entry(entry_key, entry)
        ...
```
nachher:
```python
    ENTRY_UPDATABLE_FIELDS = {"species_key", "cultivar_key", "quantity", "id_prefix", "spacing_cm", "notes"}
    ENTRY_REQUIRED_FIELDS = {"species_key", "quantity", "id_prefix"}

    def update_entry(
        self,
        run_key: PlantingRunKey,
        entry_key: str,
        data: dict,
    ) -> PlantingRunEntry:
        """Partially update a run entry (REQ-013).

        Only keys present in ``data`` are applied; required fields must not
        be nulled. The merged entry is re-validated against the model.
        """
        run = self.get_run(run_key)
        if run.status != PlantingRunStatus.PLANNED:
            raise InvalidRunStateError("update_entry", run.status.value)
        existing = self._repo.get_entry_by_key(entry_key)
        if existing is None:
            raise NotFoundError("PlantingRunEntry", entry_key)

        patch = {k: v for k, v in data.items() if k in self.ENTRY_UPDATABLE_FIELDS}
        nulled_required = self.ENTRY_REQUIRED_FIELDS & {k for k, v in patch.items() if v is None}
        if nulled_required:
            raise ValidationError(f"Fields cannot be null: {', '.join(sorted(nulled_required))}")

        merged = PlantingRunEntry.model_validate(
            {**existing.model_dump(by_alias=False), **patch}
        )
        updated = self._repo.update_entry(entry_key, merged)
        # Update planned_quantity  (unverändert)
        entries = self._repo.get_entries(run_key)
        run.planned_quantity = sum(e.quantity for e in entries)
        self._repo.update(run_key, run)
        return updated
```
Import ergänzen: `from app.common.exceptions import ValidationError` (neben den vorhandenen
`InvalidRunStateError`/`NotFoundError`-Imports der Datei).

### 4.3 `app/data_access/arango/planting_run_repository.py` (Z. 115-124)

vorher:
```python
    def update_entry(self, entry_key: PlantingRunEntryKey, entry: PlantingRunEntry) -> PlantingRunEntry:
        data = entry.model_dump(by_alias=True, exclude_none=True, mode="json")
        data.pop("_key", None)
        data["updated_at"] = datetime.now(UTC).isoformat()
        result = self._db.collection(col.PLANTING_RUN_ENTRIES).update(
            {"_key": entry_key, **data},
            return_new=True,
        )
        return PlantingRunEntry(**self._from_doc(result["new"]))
```
nachher:
```python
    def update_entry(self, entry_key: PlantingRunEntryKey, entry: PlantingRunEntry) -> PlantingRunEntry:
        # No exclude_none: the service passes a fully merged entry, and
        # explicitly cleared nullable fields (notes, cultivar_key, spacing_cm)
        # must be written as null — Arango's update() would otherwise keep
        # the previous value.
        data = entry.model_dump(by_alias=True, mode="json")
        data.pop("_key", None)
        data["updated_at"] = datetime.now(UTC).isoformat()

        old = self._db.collection(col.PLANTING_RUN_ENTRIES).get(entry_key)
        result = self._db.collection(col.PLANTING_RUN_ENTRIES).update(
            {"_key": entry_key, **data},
            return_new=True,
        )
        # Keep the entry_for_species edge in sync when the species changed.
        if old is not None and old.get("species_key") != entry.species_key:
            entry_id = f"{col.PLANTING_RUN_ENTRIES}/{entry_key}"
            self.delete_edges(col.ENTRY_FOR_SPECIES, from_id=entry_id)
            self.link_entry_to_species(entry_key, entry.species_key)
        return PlantingRunEntry(**self._from_doc(result["new"]))
```

### 4.4 `app/domain/interfaces/planting_run_repository.py` (Z. 42)
Unverändert — die Repo-Signatur (`entry: PlantingRunEntry`) bleibt; nur der **Service**-Vertrag
ändert sich (dict statt Modell). Docstring des Interfaces optional um den Merge-Hinweis ergänzen.

## 5. Neue Funktionen / Signaturen

| Ort | Änderung |
|---|---|
| `PlantingRunService.update_entry` | `def update_entry(self, run_key: PlantingRunKey, entry_key: str, data: dict) -> PlantingRunEntry` (**Breaking** für Aufrufer — einziger Aufrufer ist der Tenant-Router) |
| `PlantingRunService` | Klassenkonstanten `ENTRY_UPDATABLE_FIELDS`, `ENTRY_REQUIRED_FIELDS` |
| Router `update_entry` | `exclude_unset=True`, kein `PlantingRunEntry`-Bau mehr |
| Repo `update_entry` | Edge-Sync `entry_for_species`, Dump ohne `exclude_none` |

## 6. Testplan

**Neu: `tests/unit/domain/services/test_planting_run_entry_update.py`** (Fake-Repo-Muster aus
`tests/unit/domain/services/test_planting_run_detach_snapshot.py` übernehmen):
1. `test_partial_quantity_update_preserves_species` — Bestand
   `species_key="species_tomato", quantity=3, id_prefix="TO"`; Patch `{"quantity": 5}` ⇒
   `species_key` unverändert `"species_tomato"`, `quantity == 5`, `planned_quantity` neu summiert.
2. `test_partial_update_never_writes_placeholder` — Patch `{"notes": "x"}` ⇒ persistiertes Entry
   enthält weder `"placeholder"` noch `id_prefix "XX"` (Regressionstest auf GAP-B9).
3. `test_explicit_null_clears_notes` — Patch `{"notes": None}` ⇒ `notes is None` nach Update.
4. `test_null_required_field_raises_422` — Patch `{"species_key": None}` ⇒ `ValidationError`.
5. `test_invalid_id_prefix_rejected` — Patch `{"id_prefix": "xx"}` ⇒ Pydantic-`ValidationError`
   aus `model_validate` (Pattern `^[A-Z]{2,5}$`).
6. `test_update_entry_rejected_when_run_active` — Status `ACTIVE` ⇒ `InvalidRunStateError`
   (bestehendes Verhalten, Guard bleibt).
7. `test_species_change_relinks_edge` — Fake-Repo zeichnet `delete_edges`/`link_entry_to_species`
   auf; Patch `{"species_key": "species_basil"}` ⇒ Edge einmal gelöscht + neu verlinkt; Patch ohne
   Species-Änderung ⇒ keine Edge-Operation.

**API-Ebene** (falls FastAPI-TestClient-Setup für Tenant-Router vorhanden, sonst Service-Ebene
ausreichend): `PUT .../entries/{k}` mit `{"quantity": 5}` ⇒ 200 und Response enthält
ursprünglichen `species_key`.

**Frontend-Gegencheck** (kein Codechange erwartet): `src/frontend` — prüfen, ob der
Entry-Edit-Dialog bisher immer den vollen Body sendet (dann ist der Fix rein defensiv) und dass
kein Code auf das Placeholder-Verhalten baut.

## 7. Akzeptanzkriterien

- [ ] `PUT .../entries/{entry_key}` mit Teil-Body verändert ausschließlich die gesendeten Felder;
      `"placeholder"` / `1` / `"XX"` tauchen in keinem Persistenzpfad mehr auf
      (`grep -rn '"placeholder"' src/backend/app/api/v1/planting_runs/` leer).
- [ ] Explizites `null` auf `species_key`/`quantity`/`id_prefix` ⇒ HTTP 422 mit sprechender Meldung.
- [ ] Explizites `null` auf `notes`/`cultivar_key`/`spacing_cm` löscht den Wert persistent.
- [ ] Species-Wechsel aktualisiert die `entry_for_species`-Edge (Graph konsistent).
- [ ] `planned_quantity`-Resummierung und `PLANNED`-Status-Guard unverändert grün.
- [ ] Alle neuen + bestehenden Planting-Run-Tests grün; ruff/`tsc` clean.

## 8. Risiko

- **Verhaltensänderung** für API-Clients, die sich (fälschlich) auf das Ersetzen verlassen: Ein
  Client, der bisher `{"quantity": 5}` schickte, bekam `species_key="placeholder"` — das war der
  Bug; kein legitimer Client kann darauf gebaut haben. HA-Integration nutzt diesen Endpoint nicht
  (`ha-integration-sync` bei Bedarf gegenprüfen).
- **`exclude_unset` vs. Pydantic-Defaults**: `EntryUpdate` hat ausschließlich `None`-Defaults —
  `exclude_unset` ist hier korrekt und deterministisch.
- **Edge-Sync im Repo** macht `update_entry` um einen `get` teurer (1 Extra-Read pro Update) —
  vernachlässigbar (Entry-Updates sind selten, nur im Status `planned`).
- **Arango `update` + `null`**: Standardverhalten `keepNull=True` schreibt `null`-Werte — gewollt.
  Kein `keep_none`-Parameter nötig.

---

# AP-13 (GAP-B8): E-Mail-Digest real implementieren

## 1. Ziel & betroffene Anforderung

### Ziel
Der Beat-Task `notifications.send_email_digests` (täglich 07:00 UTC,
`app/tasks/__init__.py:109-112`) ist heute ein No-Op-Placeholder
(`app/tasks/notification_tasks.py:339-360`): er loggt `digests_sent=0` und tut nichts. Nutzer,
die eine tägliche E-Mail-Zusammenfassung wollen, bekommen nie eine.

Nach diesem Arbeitspaket gilt:
- Nutzer mit aktiviertem E-Mail-Digest (`channels.email.enabled == true` **und**
  `channels.email.config.digest == true`) erhalten täglich **eine** Sammel-E-Mail mit allen
  Notifications der letzten 24 h.
- Die Zustellung läuft über den bestehenden `EmailNotificationChannel.send_batch`
  (`app/data_access/external/email_notification_channel.py:92-130`) → `IEmailService`
  (SMTP/Console je `settings.email_adapter`, `app/config/settings.py:165-171`).
- Empfängeradresse: `channels.email.config.email`, Fallback auf `User.email`.
- Der Task ist retry-gehärtet und isoliert Fehler pro Nutzer.

### Betroffene Anforderung
- **REQ-030 (Notifications)** — Kanal „email" ist Teil des FE↔BE-Kanal-Contracts
  (`tests/contracts/test_notification_channels_contract.py`); Digest-Zustellung ist der im
  Task-Docstring zugesagte Delivery-Modus.

## 2. Root-Cause-Analyse

`app/tasks/notification_tasks.py:339-360`:
```python
@celery_app.task(name="notifications.send_email_digests")
def send_email_digests() -> dict:
    ...
    # Email digest delivery requires a dedicated query method on
    # the preference repository (list_users_with_digest_enabled)
    # which will be added when the EmailNotificationChannel is
    # fully implemented. For now, this task is a no-op placeholder.
    digests_sent = 0
    ...
```
Der Kommentar ist doppelt veraltet:
1. `EmailNotificationChannel` **ist** vollständig implementiert (Single + Batch + HTML-Rendering)
   und wird beim Startup registriert (`app/main.py:156-163`, best-effort).
2. Es fehlt tatsächlich nur die Infrastruktur drumherum:
   - `INotificationPreferenceRepository` hat nur `get_by_user`/`upsert`
     (`app/domain/interfaces/notification_preference_repository.py`) — keine Query „wer hat
     Digest an?".
   - `INotificationRepository.list_for_user` hat kein Zeitfenster — der Digest braucht
     „Notifications seit gestern 07:00".
   - Es gibt kein Digest-Flag im Preference-Modell — `ChannelPreference.config: dict`
     (`app/domain/models/notification.py:62-65`) ist aber generisch genug (kein Schema-Change
     nötig, Konvention `config.digest: bool`, analog `config.email: str`, das
     `EmailNotificationChannel.send/send_batch` bereits liest).

## 3. Lösungsdesign

### 3.1 Digest-Semantik (Designentscheidung)
- **Fenster**: alle Notifications des Nutzers mit `created_at >= now - 24 h` (der Task läuft
  täglich 07:00 UTC ⇒ lückenlos, idempotent genug; kein zusätzlicher „digested"-Status nötig).
- **Inhalt**: alle Notifications unabhängig vom Sofort-Zustellweg (der Digest ist eine
  *Zusammenfassung*, kein Ersatz-Retry) — bewusst einfach; Filter „nur nicht per E-Mail
  zugestellte" wäre über `"email" not in n.channels_sent` möglich, wird aber als optionale
  Verfeinerung dokumentiert, nicht eingebaut.
- **Abgrenzung zu `daily_summary`**: `DailySummaryPreference` (06:30-Task
  `notifications.send_daily_summary`) fasst **offene Care-Tasks** zusammen; der E-Mail-Digest
  fasst **gesendete Notifications** zusammen. Beide bleiben getrennt konfigurierbar.
- **Opt-in**: `prefs.channels["email"].enabled == true` **und**
  `prefs.channels["email"].config["digest"] == true`. Default bleibt aus (kein Verhaltens-Change
  für Bestandsnutzer; DSGVO-freundlich).

### 3.2 Bausteine
1. `INotificationPreferenceRepository.list_users_with_digest_enabled()` + AQL-Implementierung.
2. `INotificationRepository.list_for_user_since(user_key, since)` + AQL-Implementierung
   (bestehende `list_for_user`-AQL um `created_at`-Filter variiert).
3. `NotificationService.send_email_digest(user_key, to_email, since) -> dict` — sammelt, ruft den
   registrierten `email`-Channel via `NotificationChannelRegistry` mit `send_batch` auf
   (Wiederverwendung des Batch-HTML-Renderings; Betreff „Kamerplanter: N Benachrichtigungen").
4. Task `send_email_digests` orchestriert: Nutzerliste → Adresse auflösen (Config-Fallback
   `User.email` via `get_user_repo`) → pro Nutzer Service-Methode, Fehler isoliert.

### 3.3 Nicht-Ziele / Follow-ups
- **Frontend-Toggle**: Die Einstellungsseite (NotificationSettings) muss `config.digest` setzen
  können — separates kleines FE-Ticket (der Kanal-Key „email" existiert dort bereits; der
  FE↔BE-Kanal-Contract `CHANNEL_KEYS` ist von diesem AP **nicht** betroffen, es kommt kein neuer
  Kanal hinzu). Bis dahin ist das Flag per API (`PUT /notifications/preferences`) setzbar.
- Kein eigener „Digest-Queue"-Speicher; kein Umbau der Sofort-Zustellung.

## 4. Konkrete Änderungen pro Datei

### 4.1 `app/domain/interfaces/notification_preference_repository.py`

```python
class INotificationPreferenceRepository(ABC):
    @abstractmethod
    def get_by_user(self, user_key: str) -> NotificationPreferences | None: ...

    @abstractmethod
    def upsert(self, preferences: NotificationPreferences) -> NotificationPreferences: ...

    @abstractmethod
    def list_users_with_digest_enabled(self) -> list[NotificationPreferences]:
        """Return preferences of all users with the email digest opted in
        (``channels.email.enabled`` and ``channels.email.config.digest``)."""
```

### 4.2 `app/data_access/arango/notification_preference_repository.py`

```python
    def list_users_with_digest_enabled(self) -> list[NotificationPreferences]:
        query = """
        FOR p IN @@collection
          FILTER p.channels.email.enabled == true
          FILTER p.channels.email.config.digest == true
          RETURN p
        """
        cursor = self._db.aql.execute(
            query, bind_vars={"@collection": NOTIFICATION_PREFERENCES}
        )
        return [NotificationPreferences(**self._from_doc(doc)) for doc in cursor]
```
(`self._db` gemäß `BaseArangoRepository`-Attribut der Datei verwenden — dort heißt der Zugriff wie
in den Schwester-Repos; ggf. `self.db`/`self._db` angleichen.)

### 4.3 `app/domain/interfaces/notification_repository.py`

Neue abstrakte Methode:
```python
    @abstractmethod
    def list_for_user_since(
        self,
        user_key: str,
        since: datetime,
        limit: int = 100,
    ) -> list[Notification]:
        """Return the user's notifications created at/after ``since`` (newest first)."""
```

### 4.4 `app/data_access/arango/notification_repository.py`

AQL analog `list_for_user`, zusätzlich:
```
FILTER doc.user_key == @user_key
FILTER doc.created_at != null AND doc.created_at >= @since
SORT doc.created_at DESC
LIMIT @limit
```
mit `bind_vars={"user_key": ..., "since": since.isoformat(), "limit": limit}`.

### 4.5 `app/domain/services/notification_service.py`

Neue Methode (Abschnitt „Sending", nach `send_care_notifications`):
```python
    async def send_email_digest(
        self,
        user_key: str,
        to_email: str,
        since: datetime,
    ) -> dict:
        """Send one digest email summarising the user's notifications since ``since``.

        Uses the registered ``email`` channel's batch rendering (REQ-030).
        Returns {"status": "sent"|"empty"|"failed", "count": int}.
        """
        notifications = self._notification_repo.list_for_user_since(user_key, since)
        if not notifications:
            return {"status": "empty", "count": 0}

        channel = self._engine._channel_registry.get("email")
        if channel is None:
            logger.warning("email_digest_channel_unavailable", user_key=user_key)
            return {"status": "failed", "count": 0}

        result = await channel.send_batch(notifications, {"email": to_email})
        if not result.success:
            logger.warning(
                "email_digest_send_failed", user_key=user_key, error=result.error
            )
            return {"status": "failed", "count": len(notifications)}

        logger.info("email_digest_sent", user_key=user_key, count=len(notifications))
        return {"status": "sent", "count": len(notifications)}
```
Import ergänzen: `datetime` ist bereits importiert (Z. 4).
Hinweis: Zugriff auf `self._engine._channel_registry` folgt dem bestehenden Muster
(`get_channel_status`, `send_test` — Z. 335/373); kein neues API nötig.

### 4.6 `app/tasks/notification_tasks.py` (Z. 339-360 ersetzen)

vorher: No-Op (siehe §2). nachher:
```python
@celery_app.task(  # type: ignore[misc]
    name="notifications.send_email_digests",
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    max_retries=3,
    default_retry_delay=300,
)
def send_email_digests(self) -> dict:
    """Send the daily email digest (REQ-030).

    Runs daily at 07:00 UTC. For every user who opted in
    (``channels.email.enabled`` + ``channels.email.config.digest``) it
    collects the notifications of the last 24 hours and sends them as a
    single batch email via the registered ``email`` channel.
    """
    from datetime import UTC, datetime, timedelta

    from app.common.dependencies import (
        get_notification_preference_repo,
        get_notification_service,
        get_user_repo,
    )

    preference_repo = get_notification_preference_repo()
    service = get_notification_service()
    user_repo = get_user_repo()

    since = datetime.now(UTC) - timedelta(hours=24)
    candidates = preference_repo.list_users_with_digest_enabled()

    digests_sent = 0
    digests_empty = 0
    digests_failed = 0

    for prefs in candidates:
        user_key = prefs.user_key
        if not user_key:
            continue

        channel_pref = prefs.channels.get("email")
        to_email = (channel_pref.config.get("email") if channel_pref else None) or None
        if not to_email:
            user = user_repo.get_by_key(user_key)
            to_email = user.email if user else None
        if not to_email:
            logger.warning("email_digest_no_address", user_key=user_key)
            digests_failed += 1
            continue

        try:
            result = asyncio.run(service.send_email_digest(user_key, to_email, since))
        except Exception:
            logger.exception("email_digest_user_failed", user_key=user_key)
            digests_failed += 1
            continue

        if result["status"] == "sent":
            digests_sent += 1
        elif result["status"] == "empty":
            digests_empty += 1
        else:
            digests_failed += 1

    logger.info(
        "email_digests_complete",
        candidates=len(candidates),
        digests_sent=digests_sent,
        digests_empty=digests_empty,
        digests_failed=digests_failed,
    )
    return {
        "status": "complete",
        "candidates": len(candidates),
        "digests_sent": digests_sent,
        "digests_empty": digests_empty,
        "digests_failed": digests_failed,
    }
```
(Beat-Eintrag `notifications-email-digests` in `app/tasks/__init__.py:109-112` bleibt unverändert.)

### 4.7 Kein Schema-Change
`ChannelPreference.config: dict` trägt das neue Flag konventionsbasiert
(`{"email": "...", "digest": true}`). Kein Migrations-/Seed-Aufwand; Bestandsdokumente ohne
`digest`-Key matchen den AQL-Filter nicht (Digest aus). Der Konventions-Key ist im
Modell-Docstring von `ChannelPreference` zu dokumentieren (2-Zeilen-Kommentar).

## 5. Neue Funktionen / Signaturen (Zusammenfassung)

| Ort | Signatur |
|---|---|
| `INotificationPreferenceRepository` / Arango-Impl | `def list_users_with_digest_enabled(self) -> list[NotificationPreferences]` |
| `INotificationRepository` / Arango-Impl | `def list_for_user_since(self, user_key: str, since: datetime, limit: int = 100) -> list[Notification]` |
| `NotificationService` | `async def send_email_digest(self, user_key: str, to_email: str, since: datetime) -> dict` |
| Task | `notifications.send_email_digests` — `bind=True`, Retry-Konfiguration, echtes Ergebnis-Dict (`candidates`, `digests_sent`, `digests_empty`, `digests_failed`) |
| Konvention | `NotificationPreferences.channels["email"].config = {"email": str, "digest": bool}` |

## 6. Testplan

**`tests/unit/tasks/test_notification_tasks.py`** — Klasse `TestSendEmailDigests` ersetzen
(der bestehende `test_placeholder_returns_zero` prüft explizit das No-Op-Verhalten und **muss**
angepasst werden). Mock-Muster `_mock_dependencies` der Datei wiederverwenden; zusätzlich
`get_notification_preference_repo` und `get_user_repo` am Mock-Modul bereitstellen:
1. `test_no_candidates_sends_nothing` — leere Kandidatenliste ⇒
   `{"status": "complete", "digests_sent": 0, ...}`; Service nie aufgerufen.
2. `test_sends_one_digest_per_user` — 2 Kandidaten mit `config={"email": "a@x", "digest": True}`;
   `asyncio.run` gepatcht auf `{"status": "sent", "count": 3}` ⇒ `digests_sent == 2`,
   `service.send_email_digest` je Nutzer mit korrekter Adresse + `since`-Fenster (≈ now−24 h).
3. `test_address_fallback_to_user_email` — `config={"digest": True}` ohne `email`-Key;
   `user_repo.get_by_key` liefert `SimpleNamespace(email="fallback@x")` ⇒ Aufruf mit
   `"fallback@x"`.
4. `test_missing_address_counts_failed` — weder Config noch User-E-Mail ⇒ `digests_failed == 1`,
   kein Service-Call.
5. `test_per_user_failure_does_not_abort` — erster Nutzer wirft, zweiter liefert `sent` ⇒
   `digests_sent == 1`, `digests_failed == 1`.
6. `test_empty_window_counts_empty` — Service liefert `{"status": "empty"}` ⇒ `digests_empty == 1`,
   `digests_sent == 0`.

**`tests/unit/domain/services/test_notification_service.py`** (bestehende Datei erweitern):
7. `test_send_email_digest_uses_batch_channel` — Fake-Registry mit Fake-`email`-Channel
   (zeichnet `send_batch(notifications, {"email": to})` auf); Repo liefert 3 Notifications ⇒
   `{"status": "sent", "count": 3}`, `send_batch` einmal.
8. `test_send_email_digest_empty` — Repo liefert `[]` ⇒ `{"status": "empty", "count": 0}`,
   Channel nie berührt.
9. `test_send_email_digest_channel_missing` — Registry ohne `email` ⇒ `{"status": "failed", ...}`
   (kein Raise).
10. `test_send_email_digest_channel_error` — `send_batch` liefert
    `ChannelResult(success=False, error=...)` ⇒ `status == "failed"`.

**Repo-Ebene** (Mock-DB-Muster der bestehenden Arango-Repo-Tests unter `tests/unit/data_access/`,
sonst Integrationstest):
11. `list_users_with_digest_enabled` — AQL-Filter greift nur bei `enabled==true` **und**
    `config.digest==true` (Dokumente ohne `digest`-Key ⇒ nicht enthalten).
12. `list_for_user_since` — filtert `user_key` + `created_at >= since`, sortiert absteigend,
    respektiert `limit`.

**Contract-Regression**: `tests/contracts/test_notification_channels_contract.py` unverändert
grün (kein neuer Kanal-Key).

## 7. Akzeptanzkriterien

- [ ] Nutzer mit `channels.email.enabled=true` + `config.digest=true` erhält täglich 07:00 UTC
      genau **eine** E-Mail mit allen Notifications der letzten 24 h (Batch-HTML-Rendering des
      bestehenden Channels).
- [ ] Nutzer ohne Digest-Opt-in oder ohne auflösbare E-Mail-Adresse erhalten nichts; fehlende
      Adresse wird als `email_digest_no_address` geloggt und gezählt.
- [ ] Fehler bei einem Nutzer brechen den Lauf nicht ab (Isolation pro Nutzer); transiente
      Transportfehler des Gesamt-Tasks werden bis 3× mit 300 s Delay retried.
- [ ] Task-Rückgabe enthält `candidates`, `digests_sent`, `digests_empty`, `digests_failed`;
      Log-Event `email_digests_complete` mit denselben Zählern.
- [ ] `list_users_with_digest_enabled` und `list_for_user_since` sind über die Interfaces
      abstrahiert (5-Schichten-Architektur, NFR-001) und in beiden Arango-Repos implementiert.
- [ ] Kein neuer Kanal-Key; FE↔BE-Kanal-Contract-Test unverändert grün.
- [ ] Alle Tests aus §6 grün; ruff clean.

## 8. Risiko

- **Console-Adapter in Dev**: `settings.email_adapter="console"` — `ConsoleEmailAdapter` muss
  `send_notification_email` unterstützen; falls nicht (Default in `IEmailService` wirft
  `NotImplementedError`, `app/domain/interfaces/email_service.py`), fängt der bestehende
  `try/except` in `EmailNotificationChannel.send_batch` das ab ⇒ `digests_failed` statt Crash.
  Im Zuge des AP prüfen und ggf. eine Log-Implementierung im Console-Adapter ergänzen (3 Zeilen).
- **Doppelzustellung Sofort-E-Mail + Digest**: Wer den `email`-Kanal auch für Sofort-Zustellung
  nutzt, bekommt Inhalte doppelt (einmal einzeln, einmal im Digest). Bewusste v1-Entscheidung
  (Digest = Zusammenfassung); Verfeinerung „nur `'email' not in channels_sent`" als dokumentierte
  Option im Code-Kommentar.
- **Fenster-Lücken/Overlaps**: Beat-Verspätung kann das 24-h-Fenster minimal verschieben
  (Doppelnennung oder Lücke einzelner Notifications am Rand). Für einen Digest akzeptabel;
  Alternative (persistenter `last_digest_at`-Cursor pro Nutzer) als Follow-up notiert.
- **Skalierung**: Ein AQL-Full-Scan über `notification_preferences` (Filter ohne Index) — bei
  aktueller Nutzerzahl unkritisch; bei Wachstum persistenten Index auf
  `channels.email.config.digest` ergänzen (python-arango ≥ 8.3.3: `add_persistent_index`, **nicht**
  `add_hash_index` — bekannte Falle aus #148).
- **Blocking SMTP im Async-Pfad**: `EmailNotificationChannel.send_batch` ruft den synchronen
  `IEmailService` — läuft hier aber im Celery-Worker (eigener `asyncio.run`-Loop), nicht im
  API-Event-Loop ⇒ unkritisch.

---

# Gemeinsame Umsetzungs-Hinweise (alle drei APs)

- **Reihenfolge**: AP-3 (isoliert, klein) → AP-2 → AP-13. Keine gegenseitigen Abhängigkeiten;
  drei getrennte Commits im selben PR oder drei PRs (Empfehlung: ein PR pro AP,
  Conventional-Commits: `fix(privacy): dispatch GDPR export to celery (GAP-B5)`,
  `fix(planting-runs): preserve fields on partial entry update (GAP-B9)`,
  `feat(notifications): implement daily email digest (GAP-B8)`).
- **Qualitäts-Gate**: `ruff check` + `ruff format` (except-Tupel-Falle!), volle Backend-Suite
  (`pytest src/backend/tests`), danach 3-Agent-Kette gemäß Projekt-Feedback (UI-Review entfällt
  mangels FE-Änderung; Tests + Doku-Agent laufen).
- **Doku**: Keine Spec-Änderung nötig — alle drei APs stellen bereits spezifiziertes Verhalten
  her (REQ-025/NFR-011, REQ-013, REQ-030). Der No-Op-/Scaffold-Status war reiner
  Implementierungs-Drift.
