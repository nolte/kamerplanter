# AP-15 / AP-17 / AP-18 — Backend-Refactoring-Cluster (Base-Repository, Pagination, API-/Task-Helper, vectordb)

> Arbeitspakete aus dem Kamerplanter-Code-Review (Fable 5), `../code-review-fable5-2026-07.md`.
> Befund-IDs: **DUP-B1, DUP-B2, DUP-B3, DUP-B6, DUP-B10** (AP-15, Aufwand L) ·
> **DUP-B5, SEC-B5** (AP-17, Aufwand M) · **DUP-B4, INF-D1, INF-D2** (AP-18, Aufwand M).
> Die Frontend-Anteile von AP-17/18 (FE-L6 `fetchAllPages`, FE-L7 `window.confirm`→`ConfirmDialog`)
> sind **nicht** Teil dieses Plans — sie sind unabhängig umsetzbar und werden separat geplant.

AP-15 ist laut Review-Priorisierung (Z. 199) das **Refactoring-Fundament**, das viele spätere
Arbeitspakete verkleinert. Dieser Plan behandelt die drei APs als ein Cluster, weil sie
denselben Code berühren (Repositories, Router) und eine gemeinsame Migrationsreihenfolge
Doppelarbeit vermeidet.

---

## 1. Ziel

Nach Umsetzung gilt:

1. **AP-15:** `BaseArangoRepository` ist generisch (`BaseArangoRepository[TModel]`) und liefert
   typisierte Domain-Models. Die ~40 Sub-Repositories unter
   `src/backend/app/data_access/arango/` verlieren ihre kopierten CRUD-Wrapper
   (geschätzt −500 bis −800 LOC). Multi-Collection-Repos (`ipm_repository.py`,
   `harvest_repository.py`) reimplementieren kein Base-CRUD mehr, sondern komponieren
   typisierte Collection-Views. Der 118× kopierte Get-or-raise-Block in den Services wird
   durch `get_or_raise(key)` ersetzt. Kaskadierende Edge-Löschung läuft über ein erweitertes
   `delete_edges(..., direction=...)`.
2. **AP-17:** Die 39×/43× kopierten `offset`/`limit`-Query-Parameter der Router laufen über
   eine gemeinsame `PaginationParams`-Dependency (FastAPI-Query-Modell). Kein
   `LIMIT {offset}, {limit}` per f-String mehr — `AQLBuilder` und alle Hand-AQL nutzen
   bind_vars (SEC-B5).
3. **AP-18:** Das 30-Router-Idiom `Resp(key=m.key or "", **m.model_dump(exclude={"key"}))`
   wird durch einen generischen `to_response`-Helper ersetzt; die 9 `asyncio.run`-Brücken in
   `app/tasks/` laufen über einen `run_async_task`-Decorator (auf Basis des vorhandenen
   loop-isolierten `run_async`); die `vectordb/`-Infrastruktur-Schicht existiert nur noch
   einmal (gemeinsames Paket für knowledge- und inference-service).

**Verbindliche Leitplanke:** `spec/style-guides/BACKEND.md` — insbesondere §2 (5-Schichten),
§4 (PEP-604/PEP-585-Typing, `type`-Aliases), §9 (Repository-Pattern: Interface-ABC +
`Arango{Entity}Repository`, Rückgabetypen immer Domain-Models), §10 (Exceptions nur aus
`app/common/exceptions.py`, nie `HTTPException` unterhalb des API-Layers), §16 (Tests).
Alle hier vorgeschlagenen Refactorings bleiben innerhalb dieser Muster; das Style-Guide-Beispiel
in §9.2 (händischer `get_by_key`-Wrapper) wird am Ende an die neue generische Base angepasst
(siehe §8, Schritt F).

---

## 2. Ist-Analyse (code-verankert)

### 2.1 DUP-B1 — typisierte CRUD-Wrapper (~40 Repos)

`src/backend/app/data_access/arango/base_repository.py` (135 Zeilen) arbeitet
ausschließlich auf `dict[str, Any]`:

```python
class BaseArangoRepository:
    def get_by_key(self, key: str) -> dict[str, Any] | None: ...
    def get_all(self, offset=0, limit=50, tenant_key=None) -> tuple[list[dict], int]: ...
    def create(self, model: BaseModel) -> dict[str, Any]: ...
    def update(self, key: str, model: BaseModel) -> dict[str, Any]: ...
    def delete(self, key: str) -> bool: ...
    def find_by_field(self, field: str, value: Any) -> list[dict[str, Any]]: ...
```

48 Dateien unter `data_access/arango/` referenzieren `BaseArangoRepository`; die Sub-Repos
wiederholen darüber das immer gleiche Muster (Beispiel `oidc_config_repository.py:14-35`,
identisch in `tenant_repository.py:14-39`, `fertilizer_repository.py:49-59`,
`data_export_repository.py:25-35`, …):

```python
def get_by_key(self, key: OidcProviderConfigKey) -> OidcProviderConfig | None:
    doc = BaseArangoRepository.get_by_key(self, key)
    return OidcProviderConfig(**doc) if doc else None
```

Charakteristisch ist der **explizite unqualifizierte Base-Call**
(`BaseArangoRepository.get_by_key(self, …)`), weil die Subklasse denselben Methodennamen
mit anderem Rückgabetyp überschreibt. Das ist der zentrale Migrations-Constraint (§3.3).

### 2.2 DUP-B2 — Multi-Collection-Repos reimplementieren Base-CRUD

- `ipm_repository.py:56-136`: Disease- und Treatment-CRUD komplett von Hand
  (`self._db.collection(col.DISEASES)`, manuelles `created_at`/`updated_at`,
  f-String-`LIMIT {offset}, {limit}` in Z. 57/99), weil die Base an **eine**
  Collection (`col.PESTS`) gebunden ist.
- `harvest_repository.py:24-53, 57-96, 144-194`: dieselbe Handarbeit für
  `HARVEST_INDICATORS`, `HARVEST_OBSERVATIONS`, `QUALITY_ASSESSMENTS`, `YIELD_METRICS`.
- Gleiches Muster in `fertilizer_repository.py:80-129` (`FERTILIZER_STOCKS`).

### 2.3 DUP-B3 — Ein-Feld-AQL trotz `find_by_field`

- `oidc_config_repository.py:19` und `tenant_repository.py:19`: byte-identisches
  `get_by_slug` (`FOR doc IN @@collection FILTER doc.slug == @slug LIMIT 1 RETURN doc`).
- `oidc_config_repository.py:38,43`: `list_all` / `list_enabled` — Ein-Feld-Filter + Sort.
- DSGVO-Zwillinge: `data_export_repository.py:37-67` (`list_by_user`, `list_active_by_user`)
  ≈ `processing_restriction_repository.py:66-98` — Unterschiede nur: Filterfeld-Zusatz
  (`status IN ['pending','processing']` vs. `lifted_at == null`) und Sortierfeld.

Das vorhandene `find_by_field(field, value)` kann das nicht ausdrücken: kein `sort`,
kein `limit`, keine Zusatzfilter, kein Einzel-Ergebnis, und es liefert `dict`s.

### 2.4 DUP-B6 — Get-or-raise 118× in Services

`grep -rn "raise NotFoundError" app` → 158 Treffer, davon ~118 im Muster
(`app/domain/services/activity_service.py:22-25`, `tank_service.py:27-32,191-193,216-218`, …):

```python
activity = self._repo.get_by_key(key)
if activity is None:
    raise NotFoundError("Activity", key)
```

`NotFoundError(entity, key)` (`app/common/exceptions.py:22-29`) braucht den Entity-Namen —
den kennt das generische Repo über `self._model_cls.__name__`.

### 2.5 DUP-B10 — kaskadierende Edge-Löschung kopiert

`base_repository.py:127-135` (`delete_edges`) filtert nur `e._from == @from` (outbound)
und gibt hart `return 1` zurück. Deshalb schreiben Repos die Inbound-Variante von Hand:

- `ipm_repository.py:50-52` (`e._to == @id`), `ipm_repository.py:88-91` (dito),
  `ipm_repository.py:131-133` (`e._from == @id OR e._to == @id`),
- `fertilizer_repository.py:67-69` (inbound), `data_export_repository.py:70-71`,
  `processing_restriction_repository.py:100-101`.

### 2.6 DUP-B5 / SEC-B5 — Pagination

- Router: `offset: int = Query(0, ge=0)` 39× / `limit: int = Query(50, ge=1, le=200)` 43×
  unter `app/api/v1/` (Beispiel `app/api/v1/activities/router.py:18-19`).
- `app/common/pagination.py` enthält bereits `PaginatedRequest` (offset/limit mit
  denselben Constraints) und `PaginatedResponse[T]` — **beides aktuell toter Code**
  (keine Verwendung außerhalb des Moduls). FastAPI ist auf 0.139 gepinnt
  (`requirements.txt:69`) → Query-Parameter-Modelle (`Annotated[Model, Query()]`,
  seit 0.115) sind verfügbar.
- f-String-`LIMIT {offset}, {limit}`: 13 Stellen in 8 Repos (`activity_repository.py`,
  `ipm_repository.py:57,99,174,239`, `tank_repository.py`, `harvest_repository.py:25,85`,
  `nutrient_plan_repository.py`, `planting_run_repository.py`, `fertilizer_repository.py:42`,
  `task_repository.py:53,288`). Zusätzlich interpoliert **auch der `AQLBuilder` selbst**
  (`query_builder.py:41`: `f"  LIMIT {self._offset}, {self._limit}"`). Durch `int`-Typisierung
  + `le=200` aktuell nicht ausnutzbar, aber Disziplin-Bruch; `phase_sequence_repository.py:32`
  macht es korrekt mit bind_vars.

### 2.7 DUP-B4 — Response-Mapping-Idiom

`def _to_response` in 30 Routern; das triviale Idiom (`activities/router.py:12-13`):

```python
def _to_response(a: Activity) -> ActivityResponse:
    return ActivityResponse(key=a.key or "", **a.model_dump(exclude={"key"}))
```

Nicht-triviale Varianten existieren und **bleiben bestehen**: `attachments/tenant_router.py:83`
(braucht `tenant_slug`), `plant_instances/tenant_router.py:24` (braucht Service für
berechnete Felder), `ha_publish/tenant_router.py:25` (kein Domain-Model-Mapping).

### 2.8 INF-D2 — `asyncio.run`-Brücke in Tasks

- `app/common/async_bridge.py` stellt bereits ein loop-isoliertes `run_async[T]` bereit
  (fresh Loop im Worker-Thread; sicher unter pytest-asyncio) — genutzt von
  `storage_tasks.py:111`, `reference_contribution_tasks.py`, `pest_image_tasks.py`, u. a.
- **Rohes `asyncio.run`** dagegen 9×: `retention_tasks.py` (4× wortgleiches
  try/`asyncio.run`/log/`raise`-Gerüst, Z. 44-132), `notification_tasks.py:120,175,303`,
  `storage_tasks.py:81`. Das wortgleiche Gerüst (Service holen → `asyncio.run` →
  `logger.info(...completed)` / `logger.exception(...failed)` → `raise`) ist der
  eigentliche Dedup-Kandidat.

### 2.9 INF-D1 — `vectordb/` doppelt

| Datei | knowledge-service | inference-service | Diff |
|---|---|---|---|
| `app/vectordb/connection.py` | 69 Z. | 69 Z. | **nur Docstring** |
| `app/vectordb/schema.py` | 58 Z. | 60 Z. | Migrations-Tabellenname (`schema_migrations` vs. `inference_schema_migrations`) + Kommentare |
| `app/vectordb/repository.py` | 382 Z. | 229 Z. (+ `pest_repository.py` 188 Z.) | **substanziell verschieden** (Hybrid-Fulltext/Umlaut-Logik vs. Embedding-Lookups) |

→ Dedup-Ziel ist die **Infrastruktur-Schicht** (Connection-Pool + Migration-Runner),
nicht die fachlichen Repositories. Constraint: `connection.py` importiert das
service-lokale `app.config.Settings`; die Docker-Build-Contexte sind per Service
(`skaffold.yaml:137` → `src/knowledge-service`, `:214` → `src/inference-service`) —
ein geteiltes Paket außerhalb dieser Verzeichnisse ist ohne Context-Änderung nicht
COPY-bar (siehe §7.3).

---

## 3. AP-15 — Design: `BaseArangoRepository[TModel]`

### 3.1 Zwei-Schichten-Design der Base

Kernidee: die Base bekommt **private Doc-Primitiven** (dict-Ebene, heutiges Verhalten
unverändert) und darüber eine **öffentliche typisierte API** mit den kanonischen Namen.
Das löst den Namenskonflikt aus §2.1: Sub-Repos, die noch nicht migriert sind, rufen die
Doc-Primitiven; migrierte Sub-Repos löschen ihre Wrapper und erben die typisierte API.

```python
# src/backend/app/data_access/arango/base_repository.py
from typing import Any, ClassVar, Literal

from pydantic import BaseModel

type FilterTriple = tuple[str, str, Any]  # (field, op, value) — op aus AQLBuilder-Whitelist


class BaseArangoRepository[TModel: BaseModel]:
    """Generic, typed ArangoDB CRUD operations for one primary collection."""

    _model_cls: ClassVar[type[BaseModel] | None] = None   # von Subklassen gesetzt
    _entity_name: ClassVar[str | None] = None             # Default: _model_cls.__name__

    def __init__(
        self,
        db: StandardDatabase,
        collection_name: str,
        model_cls: type[TModel] | None = None,   # für Composition (Multi-Collection-Views)
    ) -> None: ...

    # ── Doc-Primitiven (privat, dict-Ebene — heutiger Code, nur umbenannt) ──
    def _get_doc(self, key: str) -> dict[str, Any] | None: ...          # ex get_by_key
    def _list_docs(self, offset=0, limit=50, tenant_key=None) -> tuple[list[dict], int]: ...  # ex get_all
    def _insert_doc(self, model: BaseModel, *, default_now_fields: tuple[str, ...] = ()) -> dict: ...  # ex create
    def _update_doc(self, key: str, model: BaseModel) -> dict[str, Any]: ...  # ex update
    def _delete_doc(self, key: str) -> bool: ...                          # ex delete
    def _find_docs(self, filters: list[FilterTriple], *, sort=None, offset=None, limit=None) -> list[dict]: ...

    # ── Typisierte öffentliche API ──
    def get_by_key(self, key: str) -> TModel | None: ...
    def get_or_raise(self, key: str) -> TModel: ...
    def get_all(
        self,
        offset: int = 0,
        limit: int = 50,
        tenant_key: str | None = None,
    ) -> tuple[list[TModel], int]: ...
    def get_page(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
        filters: list[FilterTriple] | None = None,
        sort: str = "_key",
        sort_direction: Literal["ASC", "DESC"] = "ASC",
    ) -> tuple[list[TModel], int]: ...
    def create(self, model: TModel, *, default_now_fields: tuple[str, ...] = ()) -> TModel: ...
    def update(self, key: str, model: TModel) -> TModel: ...
    def delete(self, key: str) -> bool: ...
    def find_by_field(
        self,
        field: str,
        value: Any,
        *,
        sort: str | None = None,
        sort_direction: Literal["ASC", "DESC"] = "ASC",
        offset: int | None = None,
        limit: int | None = None,
        extra_filters: list[FilterTriple] | None = None,
    ) -> list[TModel]: ...
    def find_one_by_field(
        self,
        field: str,
        value: Any,
        *,
        extra_filters: list[FilterTriple] | None = None,
    ) -> TModel | None: ...

    # ── Edges ──
    def create_edge(self, edge_collection, from_id, to_id, data=None) -> dict[str, Any]: ...  # unverändert
    def get_edges(self, edge_collection, vertex_id, direction="outbound") -> list[dict]: ...  # unverändert
    def delete_edges(
        self,
        edge_collection: str,
        vertex_id: str,
        *,
        direction: Literal["outbound", "inbound", "any"] = "outbound",
        other_id: str | None = None,
    ) -> int: ...
```

Verhaltensdetails:

- `_to_model(doc)`-intern: `self._resolved_model_cls()(**self._from_doc(doc))`. Auflösung:
  Konstruktor-Argument `model_cls` (Composition) gewinnt vor Klassenattribut `_model_cls`;
  ist beides `None`, wirft jede typisierte Methode `TypeError` mit klarer Meldung
  ("repository X has no model_cls — use the _doc primitives or set _model_cls").
  So kann kein halb-migriertes Repo still `dict`s liefern.
- `get_or_raise`: `raise NotFoundError(self._entity_name or self._resolved_model_cls().__name__, key)`
  — exakt die heutige Service-Semantik (§2.4). `_entity_name` erlaubt abweichende
  Anzeige-Namen (z. B. `"MaintenanceSchedule"`).
- `create(..., default_now_fields=("applied_at",))` deckt das Muster
  „`if not data.get('applied_at'): data['applied_at'] = now`" aus
  `ipm_repository.py:146-147,217-218` und `harvest_repository.py:63-64,150-151` ab:
  jedes gelistete Feld wird, falls im Dump fehlend/leer, auf `self._now()` gesetzt.
- `get_all` bleibt **signatur- und verhaltensgleich** zur heutigen Methode (inkl.
  `tenant_key`-Filter und `SORT _key`), nur der Item-Typ ändert sich auf `TModel`.
  Intern delegiert sie an `get_page`. Wichtig für Test-Mocks: die Query-Reihenfolge
  (erst List-Query, dann Count-Query) **muss unverändert bleiben** — bestehende
  Unit-Tests stubben `mock_db.aql.execute.side_effect = [iter([...]), iter([n])]`
  (z. B. `tests/unit/data_access/arango/test_activity_repository.py:41-48`).
- `find_by_field(field, value)` ohne Keyword-Args bleibt verhaltensgleich (Filter `==`,
  kein Sort/Limit) — nur der Rückgabetyp wird typisiert. `find_one_by_field` setzt
  intern `limit=1` und gibt das erste Element oder `None`.
- `delete_edges`: zweiter Parameter heißt neu `vertex_id` (heute `from_id`), bleibt aber
  **positional-kompatibel** (alle heutigen Aufrufer übergeben positional:
  `fertilizer_repository.py:65`). Semantik:
  - `direction="outbound"` → `FILTER e._from == @v` (heutiges Verhalten, Default),
  - `direction="inbound"` → `FILTER e._to == @v`,
  - `direction="any"` → `FILTER e._from == @v OR e._to == @v`,
  - `other_id` (ersetzt heutiges `to_id`) schränkt zusätzlich auf die Gegenseite ein.
  Rückgabewert wird ehrlich: `RETURN OLD._key` zählen statt hart `return 1`.
  Edge-Collection-Name weiterhin aus `collections.py`-Konstanten (kein User-Input),
  Query auf `@@collection`-bind_var umstellen.

### 3.2 `AQLBuilder`-Erweiterungen (`query_builder.py`)

Minimal-invasiv, alle Bestandsaufrufer bleiben gültig:

1. **Operator-Whitelist** in `filter()`: `{"==", "!=", ">", ">=", "<", "<=", "IN", "NOT IN", "LIKE"}`,
   sonst `ValueError` (Injection-Guard, da `op` bisher unvalidiert interpoliert wird).
2. **bind_vars für LIMIT** (SEC-B5): `build_list()` erzeugt
   `LIMIT @__offset, @__limit` und legt beide in `_bind_vars` ab (reservierte Namen mit
   `__`-Präfix kollidieren nicht mit `v0…vN`).
3. `sort()` validiert `direction` gegen `{"ASC", "DESC"}` und `field` gegen
   `^[A-Za-z_][A-Za-z0-9_.]*$` (Feldnamen kommen heute schon nur aus Code, Guard trotzdem).

### 3.3 Migrationsstrategie (inkrementell, Repo für Repo, jederzeit grün)

**Schritt 0 — mechanische Basis-Umbenennung (ein PR, reine Umbenennung):**
Base-Methoden auf Doc-Primitiven umbenennen und alle expliziten Base-Calls mitziehen.
Die Aufrufform ist grep-bar eindeutig:

| alt (in ~40 Repos) | neu |
|---|---|
| `BaseArangoRepository.get_by_key(self, ` | `self._get_doc(` |
| `BaseArangoRepository.get_all(self, ` | `self._list_docs(` |
| `BaseArangoRepository.create(self, ` | `self._insert_doc(` |
| `BaseArangoRepository.update(self, ` | `self._update_doc(` |
| `BaseArangoRepository.delete(self, ` | `self._delete_doc(` |

Verifikation: `grep -rn "BaseArangoRepository\.\(get\|create\|update\|delete\|find\)" app/`
muss leer sein; danach prüfen, ob irgendein Service/Router die Base-Methoden **ohne**
Subklassen-Wrapper nutzt (also heute dicts erwartet):
`grep`-Sweep über `app/domain/services/` auf `.get_all(`/`.get_by_key(`-Aufrufe an Repos
ohne eigene Wrapper — diese Stellen im selben PR auf die Doc-Primitiven bzw. (besser)
gleich auf die typisierte API des jeweiligen Repos umstellen. Kein Verhaltens-Diff;
kompletter pytest-Lauf muss ohne Teständerung grün sein (Solitary-Tests mocken nur
`StandardDatabase`, keine Base-Methodennamen).

**Schritt 1 — typisierte API + Erweiterungen auf der Base (ein PR):**
Generics, `_model_cls`, `get_by_key`/`get_all`/`get_page`/`create`/`update`/`delete`/
`get_or_raise`/`find_by_field`/`find_one_by_field`, `delete_edges(direction)`,
`AQLBuilder`-Erweiterungen (§3.2). Neue Unit-Tests
`tests/unit/data_access/arango/test_base_repository.py` (existiert noch nicht) decken die
neue API gegen `MagicMock`-DB ab. Noch **kein** Sub-Repo migriert → Null-Risiko-PR.

**Schritt 2..n — Sub-Repos in Batches migrieren (pro Batch ein PR):**
Pro Repo: `class ArangoXRepository(IXRepository, BaseArangoRepository[X])`,
`_model_cls = X`, triviale Wrapper löschen, nicht-triviale Methoden (Edge-Kaskaden,
Zusatzlogik) rufen `super().delete(key)` etc. Interface-ABCs (`domain/interfaces/`)
bekommen dort, wo Services `get_or_raise` nutzen sollen, die abstrakte Methode
`def get_or_raise(self, key: str) -> X: ...` ergänzt (Style-Guide §9.1).
Empfohlene Batches (aufsteigendes Risiko):

1. **Pilot (2 Repos):** `activity_repository` (hat Solitary-Tests) +
   `oidc_config_repository` (DUP-B3-Showcase: `get_by_slug` → `find_one_by_field("slug", slug)`,
   `list_all` → `find_by_field`… bzw. `get_page(sort="slug")`, `list_enabled` →
   `find_by_field("enabled", True, sort="slug")`). Pilot validiert Design + Testansatz.
2. **Ein-Collection-Repos ohne Edges** (~15 Stück: `tenant`, `consent`, `notification_*`,
   `phase_sequence`, `system_settings`, …). `tenant_repository.get_by_slug` fällt weg
   (identisch zu oidc) — `list_by_owner` → `find_by_field("owner_user_key", owner, sort="created_at")`.
3. **DSGVO-Zwillinge:** `data_export_repository`, `processing_restriction_repository`,
   `erasure_repository`. `list_by_user` → `find_by_field("user_key", u, sort="requested_at", sort_direction="DESC")`;
   `list_active_by_user` → `find_by_field("user_key", u, extra_filters=[("status", "IN", ["pending", "processing"])])`
   bzw. `[("lifted_at", "==", None)]`. Edge-Cleanup in `delete` →
   `self.delete_edges(col.REQUESTED_EXPORT, export_id, direction="inbound")`.
   Beide Repos haben Solitary-Tests (Regressionsnetz vorhanden).
4. **Repos mit Edge-Kaskaden:** `fertilizer`, `species`, `plant_instance`, `substrate`, ….
   Inbound-Schleifen (`fertilizer_repository.py:67-69`) → `delete_edges(..., direction="inbound")`.
5. **Multi-Collection-Repos (DUP-B2) via Composition:** `ipm_repository`, `harvest_repository`.
   Im `__init__` typisierte Views bauen:

   ```python
   class ArangoIpmRepository(IIpmRepository, BaseArangoRepository[Pest]):
       _model_cls = Pest

       def __init__(self, db: StandardDatabase) -> None:
           super().__init__(db, col.PESTS)
           self._diseases = BaseArangoRepository[Disease](db, col.DISEASES, Disease)
           self._treatments = BaseArangoRepository[Treatment](db, col.TREATMENTS, Treatment)
           self._inspections = BaseArangoRepository[Inspection](db, col.INSPECTIONS, Inspection)
           self._applications = BaseArangoRepository[TreatmentApplication](
               db, col.TREATMENT_APPLICATIONS, TreatmentApplication
           )
   ```

   Damit werden `get_all_diseases` → `self._diseases.get_all(offset, limit)`,
   `create_disease` → `self._diseases.create(disease)`,
   `delete_disease` → `delete_edges(col.TARGETS_DISEASE, disease_id, direction="inbound")`
   + `self._diseases.delete(key)`,
   `get_inspections_for_plant` → `self._inspections.get_page(offset=…, limit=…,
   filters=[("plant_key", "==", plant_key)], sort="inspected_at", sort_direction="DESC")`,
   `create_inspection` → `self._inspections.create(inspection, default_now_fields=("inspected_at",))`
   + bestehende Edge-Erzeugung. Analog `harvest_repository` (Indicators/Observations/
   Quality/Yield) und `fertilizer_repository` (Stocks). Die IPM-/Harvest-Interfaces
   (`domain/interfaces/ipm_repository.py`, `harvest_repository.py`) bleiben unverändert —
   die Öffentlichkeit des Repos ändert sich nicht, nur die Implementierung.

**Schritt S — Services auf `get_or_raise` umstellen (DUP-B6, pro Domänen-Batch):**
Nach Migration eines Repos die zugehörigen Service-Blöcke ersetzen:

```python
# vorher (activity_service.py:22-25)
activity = self._repo.get_by_key(key)
if activity is None:
    raise NotFoundError("Activity", key)
# nachher
activity = self._repo.get_or_raise(key)
```

Nur Blöcke ersetzen, deren Entity-String dem Modellnamen entspricht (sonst
`_entity_name` am Repo setzen). Folgen weitere Prüfungen (z. B.
`verify_tenant_ownership(tank, tenant_key, "Tank")`, `tank_service.py:30-31`), bleiben
diese unverändert im Service — `get_or_raise` ersetzt **nur** den None-Check.
API-Verhalten (404-Payload) ist identisch, da dieselbe Exception mit denselben
Argumenten fliegt.

### 3.4 Testplan AP-15

1. **Regressionsnetz:** kompletter Backend-Lauf (`pytest`, 821 Tests) nach jedem PR;
   Schritt 0 und 1 dürfen **keine** Testdatei anfassen.
2. **Neue Base-Tests** (`tests/unit/data_access/arango/test_base_repository.py`):
   - typisierte Rückgaben (`get_by_key` → Model, `None`-Pfad),
   - `get_or_raise` wirft `NotFoundError` mit `entity == model_cls.__name__`,
   - `find_by_field` mit `sort`/`limit`/`extra_filters`: erzeugte AQL + bind_vars
     asserten (inkl. `LIMIT @__offset, @__limit`),
   - `delete_edges` je `direction` (outbound/inbound/any, mit/ohne `other_id`),
   - `create(default_now_fields=…)` setzt fehlende Timestamps,
   - `TypeError` bei fehlendem `model_cls`,
   - `AQLBuilder`: Operator-Whitelist, LIMIT-bind_vars, Count-Query unverändert.
3. **Bestehende Repo-Solitary-Tests** (16 Dateien unter `tests/unit/data_access/arango/`)
   bleiben die Verhaltensspezifikation: Sie mocken `StandardDatabase` und asserten
   AQL/bind_vars bzw. Query-Reihenfolge. Wo die Migration die erzeugte AQL ändert
   (f-String-LIMIT → bind_vars, `@@collection`), werden die Assertions im selben PR
   angepasst — die **fachlichen** Assertions (Modelle, Totals, Filterwerte) bleiben.
4. **Integrationstest** `tests/integration/test_arango_integration.py` (gegen echte DB)
   nach Batch 5 einmal vollständig ausführen (deckt echte AQL-Syntax ab, die Mocks
   nicht validieren).
5. **API-Contract-Absicherung:** `tests/api/`-Suite (Router bis Service) unverändert grün —
   insbesondere `test_error_handling.py` (404-Payload nach DUP-B6-Umstellung).

### 3.5 Akzeptanzkriterien AP-15

- [ ] `BaseArangoRepository` ist `class BaseArangoRepository[TModel: BaseModel]` mit den
      Signaturen aus §3.1; `mypy`-/`ruff`-clean, PEP-604/585-konform.
- [ ] `grep -rn "BaseArangoRepository\.[a-z_]*(self" app/` → 0 Treffer.
- [ ] Kein Sub-Repo enthält mehr einen trivialen `get_by_key`/`create`/`update`/`delete`/
      `get_all`-Wrapper (Review-Kriterium: Wrapper nur noch, wenn er Zusatzlogik trägt).
- [ ] `ipm_repository.py` und `harvest_repository.py` enthalten keine handgeschriebenen
      `insert`/`update`/`LIMIT`-CRUD-Blöcke mehr (Z.-Bereiche aus §2.2 ersetzt).
- [ ] `get_by_slug` existiert nur noch als `find_one_by_field`-Einzeiler; die
      DSGVO-Listen-Queries laufen über `find_by_field`.
- [ ] `grep -rn "if .* is None:\s*$" -A1 app/domain/services | grep "raise NotFoundError" | wc -l`
      ist von ~118 auf < 15 gefallen (Rest: Fälle mit abweichender Semantik, im PR begründet).
- [ ] `delete_edges` unterstützt `direction`; die Inbound-Kopien aus §2.5 sind entfernt.
- [ ] Alle 821 Backend-Tests grün; `data_access/arango/` netto um ≥ 400 LOC kleiner.

### 3.6 Risiken & Gegenmaßnahmen AP-15

| Risiko | Schwere | Gegenmaßnahme |
|---|---|---|
| **Breaking Change an 40 Repos**: verpasster Call-Site bei Schritt 0 → Laufzeitfehler statt Compile-Fehler | Hoch | Schritt 0 rein mechanisch + grep-Verifikation; typisierte API wirft sofort `TypeError` bei fehlendem `model_cls` (fail fast statt stiller dicts); Batches klein halten (≤ 8 Repos/PR) |
| Semantik-Drift bei `update` (Arango-`update` merged; `exclude_none` löscht nie Felder) | Mittel | Bewusst **nicht** anfassen — bekannte Bestands-Semantik, Verhalten 1:1 in `_update_doc` übernehmen; als Folge-Finding notieren |
| Test-Mocks brechen, weil Query-Reihenfolge/-Text sich ändert | Mittel | List-vor-Count-Reihenfolge vertraglich festschreiben (Base-Test); AQL-Text-Änderungen nur in den Batch-PRs, die die betroffenen Assertions mit anpassen |
| `find_by_field`-Verallgemeinerung erzeugt subtly andere AQL (z. B. fehlendes `LIMIT 1`) | Mittel | `find_one_by_field` erzwingt `limit=1`; Basis-Tests asserten AQL wortgenau |
| Pydantic-Modelle mit Alias-/Extra-Feld-Eigenheiten (`_key`-Alias) | Niedrig | `_from_doc` bleibt unverändert; Pilot-Batch prüft repräsentativ |
| Interfaces (`I*Repository`) und Base laufen auseinander | Niedrig | `get_or_raise` je Interface nur ergänzen, wenn ein Service es nutzt; Style-Guide §9.1 |

---

## 4. AP-17 — `PaginationParams`-Dependency + LIMIT-bind_vars

### 4.1 Design

Das vorhandene, ungenutzte `app/common/pagination.py` wird zur Single Source of Truth
(FastAPI ≥ 0.115 Query-Parameter-Modelle):

```python
# app/common/pagination.py
from typing import Annotated

from fastapi import Query
from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    """Standard offset/limit pagination query parameters (DUP-B5)."""

    model_config = {"extra": "forbid"}   # Tippfehler in Query-Params → 422 statt still ignoriert

    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1, le=200)


type Pagination = Annotated[PaginationParams, Query()]
```

(`PaginatedRequest` wird zu `PaginationParams` umbenannt bzw. als Alias beibehalten,
`PaginatedResponse[T]` bleibt für spätere Nutzung.) Router-Umstellung:

```python
# vorher (activities/router.py:16-23)
def list_activities(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ...
# nachher
def list_activities(
    pagination: Pagination,
    ...
) -> list[ActivityResponse]:
    items, _ = service.list_activities(pagination.offset, pagination.limit, ...)
```

OpenAPI-Schema bleibt identisch (gleiche Parameternamen, Typen, Constraints) →
**kein Frontend-Impact**. Vorher per grep inventarisieren, welche der 39/43 Stellen
abweichende Grenzen haben (`grep -rn "limit: int = Query" app/api/v1 | grep -v "le=200"`);
Abweichler behalten entweder ihre Einzel-Parameter oder bekommen eine eigene
Modell-Variante (z. B. `SearchPagination` mit `le=50`) — keine stillen Limit-Änderungen.

`model_config = {"extra": "forbid"}` ist die einzige Verhaltensänderung (unbekannte
Query-Parameter → 422). Falls das API-Contract-Tests bricht: weglassen (dann 1:1
verhaltensgleich).

### 4.2 SEC-B5 — bind_vars

1. `AQLBuilder.build_list()` → `LIMIT @__offset, @__limit` (§3.2, zentraler Fix für alle
   Builder-Nutzer inkl. `BaseArangoRepository._list_docs`).
2. Die 13 f-String-Stellen (§2.6): entfallen größtenteils durch die AP-15-Batches
   (Migration auf `get_page`/`find_by_field`). Verbleibende Hand-AQL (z. B.
   `task_repository.py:53,288`, `fertilizer_repository.py:42` mit Custom-Filtern) werden
   auf `LIMIT @offset, @limit` + bind_vars umgestellt — Vorbild
   `phase_sequence_repository.py:32`.
3. Guard gegen Rückfall: neuer Lint-Test (z. B. in `tests/unit/data_access/`), der die
   Repo-Quellen auf das Muster `re.compile(r"LIMIT \{")` scannt und failt
   (billiger als eine Ruff-Custom-Rule, läuft im normalen pytest).

### 4.3 Reihenfolge, Testplan, Akzeptanz, Risiko

**Reihenfolge:** 4.2(1) zusammen mit AP-15 Schritt 1 (gleiche Datei `query_builder.py`);
4.1 unabhängig davon, ein PR pro Router-Gruppe (oder ein Gesamt-PR, Änderung ist mechanisch);
4.2(2) huckepack auf den jeweiligen AP-15-Batch; 4.2(3) zum Schluss.

**Testplan:**
- `tests/api/`-Suite + vitest-unabhängig: OpenAPI-Snapshot vergleichen
  (`app.openapi()` vor/nach für 3 repräsentative Router — offset/limit-Parameter müssen
  byte-gleich bleiben).
- Neue Tests: Pagination-Modell (422 bei `offset=-1`, `limit=201`, Default-Werte),
  ein Router-Test mit `?offset=10&limit=5` Ende-zu-Ende gegen Service-Mock.
- Bestehende Router-Tests (z. B. `tests/api/test_attachments_router.py`) unverändert grün.

**Akzeptanzkriterien:**
- [ ] `grep -rn "offset: int = Query" app/api/v1 | wc -l` → 0 (bzw. dokumentierte Ausnahmen).
- [ ] `grep -rn "LIMIT {" app/data_access | wc -l` → 0, Guard-Test aktiv.
- [ ] OpenAPI-Parameter für Listen-Endpunkte unverändert (Name/Typ/Constraints).
- [ ] Alle Backend-Tests grün.

**Risiken:** FastAPI-Query-Modell ändert die Doku-Gruppierung im OpenAPI minimal
(Parameter bleiben flach — verifizieren im Pilot-Router); `extra="forbid"` kann Clients
brechen, die Müll-Query-Params senden (→ optional, siehe oben). Insgesamt **niedrig**.

---

## 5. AP-18a — `to_response`-Helper (DUP-B4)

### 5.1 Design

```python
# app/api/mapping.py  (API-Layer-Helper — Domain→Schema-Mapping gehört in die API-Schicht)
from typing import Any

from pydantic import BaseModel


def to_response[TResponse: BaseModel](
    model: BaseModel,
    response_cls: type[TResponse],
    **overrides: Any,
) -> TResponse:
    """Map a domain model onto an API response schema.

    Replaces the copied idiom ``Resp(key=m.key or "", **m.model_dump(exclude={"key"}))``.
    Only fields declared on ``response_cls`` are passed through; ``overrides`` win.
    """
    data = model.model_dump()
    data["key"] = data.get("key") or ""
    data.update(overrides)
    allowed = response_cls.model_fields.keys()
    return response_cls(**{k: v for k, v in data.items() if k in allowed})
```

- Die Filterung auf `model_fields` macht den Helper robust gegen Domain-Felder, die das
  Response-Schema nicht kennt (heute implizit über Pydantics `extra='ignore'` gelöst —
  explizit ist besser als implizit und übersteht ein künftiges `extra='forbid'`).
- `**overrides` deckt die halbtrivialen Fälle (`to_response(a, AttachmentResponse,
  download_url=...)`).
- **Nicht** migriert werden `_to_response`-Funktionen mit echter Logik
  (`plant_instances/tenant_router.py:24` mit Service-Aufruf,
  `ha_publish/tenant_router.py:25` ohne Domain-Model) — dort darf die lokale Funktion
  intern `to_response` nutzen, bleibt aber bestehen.

### 5.2 Migration, Tests, Akzeptanz, Risiko

**Migration:** mechanisch pro Router; lokale `_to_response`-Trivialdefinitionen löschen,
Aufrufe durch `to_response(model, XyzResponse)` ersetzen. Ein PR (30 Router, ~100 Stellen),
optional in 2–3 Tranchen.

**Tests:** neue Unit-Tests für `to_response` (key-Default, overrides, Feld-Filterung,
Enum-/Alias-Felder anhand eines echten Schemas, z. B. `ActivityResponse`);
`tests/api/`-Router-Tests als Regressionsnetz (Response-JSON darf sich nicht ändern —
bei Bedarf pro Tranche einen Response-Snapshot-Vergleich für 2–3 Endpunkte ergänzen).

**Akzeptanz:**
- [ ] `grep -rn "model_dump(exclude={\"key\"})" app/api | wc -l` → nahe 0 (Rest begründet).
- [ ] Response-Payloads unverändert (Router-Tests grün).

**Risiko — Mittel:** Response-Schemas, die heute *versehentlich* Felder nur deshalb füllen,
weil sie im Domain-Dump vorkommen (z. B. via Alias), könnten durch die `model_fields`-
Filterung anders behandelt werden. Gegenmaßnahme: Tranche 1 = 5 Router mit vorhandenen
API-Tests; JSON-Diff im Test, erst dann Rollout.

---

## 6. AP-18b — `run_async_task`-Decorator (INF-D2)

### 6.1 Design

Aufbauend auf dem vorhandenen loop-isolierten `run_async` (`app/common/async_bridge.py`)
— **nicht** auf rohem `asyncio.run`, dessen Event-Loop-Falle dort dokumentiert ist:

```python
# app/tasks/task_bridge.py
import functools
from collections.abc import Callable, Coroutine
from typing import Any

import structlog

from app.common.async_bridge import run_async
from app.tasks import celery_app

logger = structlog.get_logger(__name__)


def run_async_task(name: str, **task_kwargs: Any):
    """Register an async function as a Celery task with the standard bridge.

    Wraps the coroutine in ``run_async`` (loop-isolated) and applies the
    shared try / log-completed / log-exception / re-raise scaffold that is
    currently copied across retention_tasks.py, notification_tasks.py and
    storage_tasks.py.
    """

    def decorator[**P, R](fn: Callable[P, Coroutine[Any, Any, R]]):
        @celery_app.task(name=name, **task_kwargs)
        @functools.wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                result = run_async(fn(*args, **kwargs))
            except Exception as exc:
                logger.exception(f"{name}.failed", error=str(exc))
                raise
            logger.info(f"{name}.completed")
            return result

        return wrapper

    return decorator
```

Anwendung (Beispiel `retention_tasks.process_data_export`, Z. 34-61):

```python
@run_async_task(name="retention.process_data_export")
async def process_data_export(export_key: str) -> dict:
    from app.common.dependencies import get_privacy_service

    service = get_privacy_service()
    result = await service.process_data_export(export_key)
    logger.info("retention.process_data_export.result",
                export_key=export_key,
                file_size_bytes=result.file_size_bytes if result else None)
    return {"export_key": export_key, "status": result.status if result else "unknown"}
```

Task-spezifische Log-Felder (export_key, Zählstände) wandern in die async-Funktion; der
Decorator trägt nur das gemeinsame Gerüst. Migrationsziele: `retention_tasks.py` (4 Tasks),
`notification_tasks.py:120,175,303`, `storage_tasks.py:81`. Wo eine Task *mehrere*
`asyncio.run`-Aufrufe mischt (z. B. `notification_tasks.py:303` im Loop), wird sie
komplett als eine async-Funktion formuliert oder ihre inneren Aufrufe auf `run_async`
umgestellt — kein rohes `asyncio.run` mehr in `app/tasks/`.

### 6.2 Tests, Akzeptanz, Risiko

**Tests:** vorhandene `tests/unit/tasks/`-Tests bleiben Referenz; sie rufen die Task-Funktion
synchron auf — nach dem Umbau rufen sie das dekorierte Wrapper-Objekt (Celery-Task `.run`
bzw. direkt, da `@celery_app.task` callable bleibt). Neue Unit-Tests für `run_async_task`:
Ergebnis-Durchreichung, Exception → `logger.exception` + Re-Raise, Registrierung unter dem
Task-Namen (`celery_app.tasks["retention.process_data_export"]`).
**Wichtig:** Task-Namen (`name=`) dürfen sich nicht ändern — Beat-Schedule und
`send_task`-Aufrufer referenzieren sie als Strings.

**Akzeptanz:**
- [ ] `grep -rn "asyncio.run(" app/tasks | wc -l` → 0.
- [ ] Alle Task-Namen unverändert (Diff der `celery_app.tasks`-Registry vor/nach).
- [ ] Bestehende Task-Tests grün.

**Risiko — Niedrig:** Verhaltensänderung `asyncio.run` → `run_async` (Worker-Thread).
Im Celery-Prefork-Worker gleichwertig; unter pytest sogar sicherer (dokumentiert in
`async_bridge.py`). Restrisiko: thread-lokale Zustände in Services — im PR per
Integrationslauf der betroffenen Tasks prüfen.

---

## 7. AP-18c — gemeinsames `vectordb`-Paket (INF-D1)

### 7.1 Scope

Dedupliziert wird die **Infrastruktur**: `connection.py` (byte-gleich bis auf Docstring)
und `schema.py` (Diff = Name der Migrations-Tabelle). Die fachlichen Repositories
(`repository.py`, `pest_repository.py`) bleiben pro Service — sie teilen keinen Code (§2.9).

### 7.2 Paket-Design

```
src/libs/kp_vectordb/
├── pyproject.toml            # name = "kp-vectordb", deps: psycopg[binary,pool], structlog
└── kp_vectordb/
    ├── __init__.py
    ├── connection.py         # VectorDbConnection(config: VectorDbConfig)
    └── schema.py             # run_migrations(pool, migrations_dir, *, migrations_table="schema_migrations")
```

- **Settings-Entkopplung:** `connection.py` importiert heute service-lokal
  `app.config.Settings`. Das Paket definiert stattdessen ein schlankes
  `@dataclass(frozen=True) class VectorDbConfig` (host, port, database, username,
  password, pool_min_size, pool_max_size); jeder Service baut es aus seinen Settings
  (`VectorDbConfig(**settings.vectordb_dict())`).
- **Migrations-Tabelle parametrisieren:** `migrations_table`-Argument mit
  Identifier-Validierung (`^[a-z_][a-z0-9_]*$`); knowledge-service nutzt den Default,
  inference-service `"inference_schema_migrations"` — bestehende Tracking-Tabellen
  bleiben unangetastet (keine Daten-Migration nötig).
- **`changeme`-Default entfernen** (SEC-Beifang aus INF-D1): `VectorDbConfig` hat
  **kein** Passwort-Default; die Service-`config.py`s behalten ihre Env-Anbindung,
  der unsichere Default fällt beim Umbau weg (Fail-fast, wenn `VECTORDB_PASSWORD` fehlt —
  in Dev via Skaffold-Env gesetzt).

### 7.3 Build-Integration (der eigentliche Knackpunkt)

Die Docker-Build-Contexte sind heute `src/knowledge-service` bzw. `src/inference-service`
(`skaffold.yaml:137,214`) — ein Paket unter `src/libs/` ist von dort nicht COPY-bar.

**Zielvariante A (empfohlen): Build-Context anheben.**
1. `skaffold.yaml`: für beide Services `context: src` + `docker.dockerfile:
   knowledge-service/Dockerfile` (bzw. inference-service), Dockerfiles anpassen:
   `COPY libs/kp_vectordb ./libs/kp_vectordb` + `COPY knowledge-service/ ./` und
   `pip install ./libs/kp_vectordb`.
2. `requirements.txt`/`pyproject.toml` der Services: Abhängigkeit als lokalen Pfad
   (`kp-vectordb @ file:///…` nur im Image; lokal `pip install -e ../libs/kp_vectordb`
   via `task`-Target/README).
3. **CI nachziehen:** `docker-publish.yml` (und ggf. `ci.yml`-Pfadfilter) auf die neuen
   Contexte umstellen; Pfadfilter um `src/libs/kp_vectordb/**` erweitern, damit ein
   Lib-Change beide Service-Images neu baut. (Erfahrungswert aus dem Projektgedächtnis:
   Prod hängt an `:latest`-Images — nach Merge Publish-Workflow + Rollout prüfen.)

**Fallback-Variante B (falls Context-Umbau zu riskant):** Quelle einmalig unter
`src/libs/kp_vectordb/`, Sync-Kopien in beide Services generiert
(`task vectordb:sync`) + CI-Guard-Test, der `diff -r` zwischen Quelle und Kopien prüft.
Dedupliziert die *Pflege*, nicht die Bytes; keinerlei Build-Änderung. Entscheidung
im PR dokumentieren.

### 7.4 Migration, Tests, Akzeptanz, Risiko

**Reihenfolge:** (1) Paket extrahieren + knowledge-service umstellen (hat die
Referenz-Implementierung), (2) inference-service umstellen (inkl. Tabellenname-Parameter),
(3) alte `app/vectordb/connection.py`/`schema.py` in beiden Services löschen,
`repository.py`-Importe umbiegen (`from kp_vectordb.connection import VectorDbConnection`).

**Tests:** bestehende Service-Tests (`src/knowledge-service/tests`,
`src/inference-service/tests`) grün; neue Paket-Tests für `run_migrations`
(Migrations-Tabellen-Parametrisierung, Identifier-Validierung, Comment-Stripping —
Letzteres existiert in beiden Kopien leicht unterschiedlich kommentiert und wird beim
Zusammenführen einmal sauber getestet). Smoke: Skaffold-Dev-Deploy beider Services,
`/healthz`-Check (Pool-Connect) + einmaliger Migrationslauf gegen die Dev-DB.

**Akzeptanz:**
- [ ] `src/knowledge-service/app/vectordb/` und `src/inference-service/app/vectordb/`
      enthalten keine `connection.py`/`schema.py` mehr (nur noch fachliche Repositories).
- [ ] Beide Images bauen in CI; ein Change unter `src/libs/kp_vectordb/**` triggert beide.
- [ ] Migrations-Historie beider Datenbanken unverändert (gleiche Tracking-Tabellen).
- [ ] Kein `changeme`-Passwort-Default mehr im Code.

**Risiko — Mittel:** Build-/CI-Umbau (Variante A) kann Publish-Pipeline brechen →
zuerst auf Branch mit `act`/Workflow-Dispatch verifizieren; Fallback B existiert.
Laufzeitrisiko der Code-Zusammenführung ist minimal (byte-gleiche Quelle).

---

## 8. Gesamt-Reihenfolge & PR-Schnitt

| # | PR | Inhalt | Abhängigkeit | Aufwand |
|---|----|--------|--------------|---------|
| A | AP-15/0 | Base-Umbenennung auf Doc-Primitiven (mechanisch) | — | S |
| B | AP-15/1 + AP-17/SEC | Generische typisierte Base + `get_or_raise` + `delete_edges(direction)` + `AQLBuilder` (Whitelist, LIMIT-bind_vars) + Base-Tests | A | M |
| C | AP-17/Dependency | `PaginationParams` + Router-Umstellung (39 Stellen) | — (parallel zu B) | S–M |
| D1–D5 | AP-15/Batches 1–5 | Sub-Repo-Migration inkl. Service-`get_or_raise` und f-String-LIMIT-Abbau je Batch | B | je S–M |
| E | AP-18a | `to_response`-Helper + Router-Tranchen | — (parallel) | M |
| F | AP-15/Doku | Style-Guide §9.2 (`BACKEND.md`) auf generische Base aktualisieren; Guard-Test `LIMIT {` | D5 | S |
| G | AP-18b | `run_async_task` + Task-Migration | — (parallel) | S |
| H | AP-18c | `kp_vectordb`-Paket + Build/CI | — (parallel, eigener Reviewer-Fokus) | M |

Parallelisierbar: C, E, G, H berühren disjunkte Dateien zu A/B/D. Innerhalb von
AP-15 gilt strikt A → B → D1 → … → D5 (jeder Batch lässt das Repo vollständig
funktionsfähig und alle Tests grün — abbruchsicher nach jedem PR).

## 9. Globale Regressionssicherung

1. **Jeder PR:** `ruff check` + `ruff format --check`, komplette pytest-Suite (821 Tests),
   `tsc`/vitest unberührt (kein FE-Impact geplant — OpenAPI-Invarianz in C abgesichert).
2. **Schritt-0-/Batch-PRs:** keine Änderungen an `tests/` außer den im Batch begründeten
   AQL-Assertion-Anpassungen; Reviewer-Checkliste: „Testdiff erklärt sich vollständig aus
   AQL-Textänderung, nicht aus Fachlogik".
3. **Nach D5 und H:** Integrationslauf `tests/integration/test_arango_integration.py`
   + Skaffold-Dev-Smoke (Backend, knowledge-service, inference-service).
4. **Messbarkeit:** LOC-Bilanz `data_access/arango/` und Trefferzahlen der Akzeptanz-greps
   im jeweiligen PR-Body dokumentieren (Review-Erwartung: data_access −30–40 %).
