# AP-01 (P0): Datetime-Härtung der Sicherheits-Gates

> Arbeitspaket aus dem Kamerplanter-Code-Review (Fable 5). Priorität **P0**.
> Befund-IDs: **DOM-1** (Karenz-Gate), **DOM-2** (Resistance-Manager & HST-Validator).
> Betroffene Domäne: IPM / Pflanzenschutz.

---

## 1. Ziel & betroffene Anforderung

### Ziel
Die drei Sicherheits-Gates der IPM-Domäne vergleichen `datetime`-Werte, bei denen ein
tz-aware-Wert (aus der DB geparst) auf einen naiven `datetime.now()` trifft. Python wirft
dabei `TypeError: can't compare offset-naive and offset-aware datetimes`. Da dieser Fehler
in keinem Handler abgefangen wird, liefert die API **HTTP 500** statt des fachlich
korrekten **HTTP 422** (Vertragsverletzung / fachliche Blockade).

Nach diesem Arbeitspaket gilt:
- Alle Datetime-Vergleiche in den Gates sind konsistent tz-aware (UTC).
- Das Karenz-Gate blockiert eine unzulässige Ernte deterministisch mit `422`
  (`KarenzViolationError`), niemals mit `500`.
- Resistance-Manager und HST-Validator rechnen ausschließlich in UTC — auch wenn die
  Prozess-Lokalzeit vom Server abweicht.

### Betroffene Anforderung
- **REQ-010 (IPM-System)** — `spec/req/REQ-010_IPM-System.md`
  - Zeile 206 ff.: „Karenzzeit-Prüfung vor Ernte"
  - Zeile 543 ff.: „5. Karenzzeit-Validator" (`SafetyIntervalValidator.can_harvest`)
  - Zeile 775: Akzeptanzkriterium „Karenzzeit-Enforcement: Harvest-Tasks werden blockiert,
    wenn aktive Karenzzeiten bestehen"
  - Zeile 839 ff.: „Szenario 2: Karenzzeit-Blockierung"
- Der `422`-Vertrag ist in `src/backend/app/common/exceptions.py` verankert:
  `KarenzViolationError` (Z. 148), `ResistanceWarningError` (Z. 164),
  `HSTViolationError` (Z. 180) — alle mit `status_code=422`.

---

## 2. Root-Cause-Analyse

### 2.1 Persistenz von `applied_at` — immer tz-aware ISO-String

`applied_at` wird beim Anlegen einer `TreatmentApplication` gesetzt:

`src/backend/app/data_access/arango/ipm_repository.py:214-218`
```python
now = self._now()          # -> "2026-07-03T…+00:00"  (tz-aware ISO)
data["created_at"] = now
data["updated_at"] = now
if not data.get("applied_at"):
    data["applied_at"] = now
```

`_now()` liefert **tz-aware UTC** als ISO-String:

`src/backend/app/data_access/arango/base_repository.py:23-24`
```python
def _now(self) -> str:
    return datetime.now(UTC).isoformat()   # endet auf "+00:00"
```

Ebenso wird ein vom Client mitgegebenes `applied_at` über
`model_dump(..., mode="json")` (`base_repository.py:26-28`) als ISO-String serialisiert.
Die AQL-Query `get_active_karenz_periods` (`ipm_repository.py:271-289`) gibt `applied_at`
unverändert als String zurück. **Ergebnis: `applied_at` erreicht die Engines als
tz-aware ISO-String** (Offset `+00:00`), sofern der Datensatz vom aktuellen Code
geschrieben wurde.

### 2.2 Der naive Gegenpart entsteht in den Services/Engines

**Karenz-Gate (DOM-1):**

`src/backend/app/domain/engines/safety_interval_engine.py:26-32`
```python
for period in active_karenz_periods:
    applied_at = period["applied_at"]
    if isinstance(applied_at, str):
        applied_at = datetime.fromisoformat(applied_at)   # -> tz-AWARE (aus "+00:00")
    safety_days = period["safety_interval_days"]
    safe_date = applied_at + timedelta(days=safety_days)  # bleibt tz-aware
    if safe_date > planned_harvest_date:                  # <-- Vergleich
```

`planned_harvest_date` kommt naiv herein:

`src/backend/app/domain/services/ipm_service.py:260-266`
```python
def check_harvest_safety(self, plant_key, planned_date=None):
    …
    if planned_date is None:
        planned_date = datetime.now()   # NAIV (from datetime import datetime, Z. 1)
    return self._safety.can_harvest(karenz_periods, planned_date)
```

`src/backend/app/domain/services/harvest_service.py:105-111`
```python
def create_harvest_batch(self, plant_key, batch):
    batch.plant_key = plant_key
    harvest_date = batch.harvest_date or datetime.now()   # NAIV bei Default
    can_harvest, blocking = self._ipm.check_harvest_safety(plant_key, harvest_date)
```

→ In `safety_interval_engine.py:32` trifft **tz-aware `safe_date`** auf **naives
`planned_harvest_date`** ⇒ `TypeError`. Gleiche Stelle in
`earliest_safe_harvest_date` ist nur intern-vergleichend (aware vs. aware) und harmlos,
aber der Rückgabewert ist tz-aware und wird von naiven Aufrufern weiterverglichen.

**Resistance-Manager (DOM-2):**

`src/backend/app/domain/engines/resistance_engine.py:32-38` und `74-80`
```python
cutoff = datetime.now() - timedelta(days=ROTATION_WINDOW_DAYS)  # NAIV
for app in recent_applications:
    applied_at = app["applied_at"]
    if isinstance(applied_at, str):
        applied_at = datetime.fromisoformat(applied_at)          # tz-AWARE
    if applied_at < cutoff:                                       # <-- TypeError
```

Hinweis: `get_recent_applications` (`ipm_repository.py:290`) filtert bereits per AQL mit
`datetime.now(UTC)`-Cutoff, d.h. im Normalpfad ist die Liste vorgefiltert — der zweite
Cutoff-Vergleich in der Engine ist dennoch erreichbar (z.B. direkter Engine-Aufruf,
`suggest_alternatives`, oder Test-Fixtures) und crasht.

**HST-Validator (DOM-2), zusätzlich Lokalzeit-Fehler:**

`src/backend/app/domain/engines/hst_validator.py:211,219-221,228-229`
```python
now = datetime.now()                       # NAIV **und Lokalzeit**
…
for task in recent_hst_tasks:
    completed_at = task.get("completed_at")
    if isinstance(completed_at, str):
        completed_at = datetime.fromisoformat(completed_at)   # tz-AWARE
    if latest is None or completed_at > latest:               # aware vs. None ok
        latest = completed_at
…
recovery_end = latest + timedelta(days=recovery_days)   # tz-aware
recovered = now >= recovery_end                          # <-- naiv >= aware = TypeError
days_remaining = max(0, (recovery_end - now).days)       # <-- ebenfalls
```

Doppelter Defekt: (a) `now` ist naiv → `TypeError` gegen aware `recovery_end`;
(b) selbst wenn beide naiv wären, ist `datetime.now()` **Lokalzeit**, während
`completed_at` in UTC persistiert ist → die Recovery-Fenster würden um den
UTC-Offset (z.B. 2 h im Sommer) verschoben berechnet.

### 2.3 Warum 500 statt 422
`TypeError` ist kein `KamerplanterError`. Der zentrale Handler
(`common/error_handlers.py`) mappt nur `KamerplanterError`-Subklassen auf ihren
`status_code`; ein unerwarteter `TypeError` fällt auf den generischen 500-Pfad. Das
fachliche Gate-Ergebnis (`KarenzViolationError` → 422) wird also **nie erreicht**, weil
der Vergleich vorher abbricht.

---

## 3. Lösungsdesign

### Entscheidung: zentraler Helper `ensure_aware_utc()` + durchgängig `datetime.now(UTC)`

Zwei sich ergänzende Maßnahmen:

1. **Neuer Helper** in `src/backend/app/common/datetimes.py` (neues Modul, da
   `common/` bisher kein Datetime-Utility hat):

   ```python
   from datetime import UTC, datetime


   def now_utc() -> datetime:
       """Aktuelle Zeit als tz-aware UTC-datetime."""
       return datetime.now(UTC)


   def ensure_aware_utc(value: datetime | str | None) -> datetime | None:
       """Normalisiert einen datetime/ISO-String auf tz-aware UTC.

       - None            -> None
       - ISO-String      -> geparst; naive Werte werden als UTC interpretiert
       - naive datetime  -> als UTC interpretiert (Legacy-Daten, siehe §6)
       - aware datetime  -> nach UTC konvertiert
       """
       if value is None:
           return None
       if isinstance(value, str):
           value = datetime.fromisoformat(value)
       if value.tzinfo is None:
           return value.replace(tzinfo=UTC)
       return value.astimezone(UTC)
   ```

2. **Konsistenzregel** — jede Stelle, die einen geparsten `applied_at` / `completed_at`
   oder einen frisch erzeugten „jetzt"-Wert in einen Vergleich gibt, läuft ihn **zuerst**
   durch `ensure_aware_utc()` bzw. verwendet `now_utc()`. Damit sind beide Operanden
   garantiert tz-aware UTC; der `TypeError` ist strukturell ausgeschlossen und die
   HST-Lokalzeit-Verschiebung entfällt.

### Warum Helper statt „einfach überall `.replace(tzinfo=UTC)`"
- Eine Stelle definiert die Interpretation naiver Legacy-Werte (§6) — kein verstreutes,
  divergierendes Verhalten.
- `ensure_aware_utc` kapselt auch das `fromisoformat`-Parsen, sodass die Engines das
  `isinstance(str)`-Boilerplate loswerden und nicht versehentlich naive Strings
  durchreichen.
- `now_utc()` macht die UTC-Absicht an jeder Aufrufstelle sichtbar und ist test-mockbar.

### Konsistenzregel für persistierte Werte
`base_repository._now()` bleibt unverändert (schreibt bereits tz-aware UTC ISO). Neue
Daten sind damit korrekt; der Helper deckt zusätzlich **Alt-Datensätze ohne Offset** ab
(§6). Es findet **keine Datenmigration** statt — die Normalisierung geschieht beim Lesen.

---

## 4. Konkrete Änderungen pro Datei

### 4.1 NEU: `src/backend/app/common/datetimes.py`
Modul mit `now_utc()` und `ensure_aware_utc()` wie in §3 skizziert. Docstrings deutsch
erlaubt? Nein — NFR-003: Source-Code englisch. Docstrings/Bezeichner englisch halten.

### 4.2 `src/backend/app/domain/engines/safety_interval_engine.py`
`can_harvest` (Z. 26-41) und `earliest_safe_harvest_date` (Z. 53-61):

Vorher:
```python
applied_at = period["applied_at"]
if isinstance(applied_at, str):
    applied_at = datetime.fromisoformat(applied_at)
safety_days = period["safety_interval_days"]
safe_date = applied_at + timedelta(days=safety_days)
if safe_date > planned_harvest_date:
```
Nachher:
```python
applied_at = ensure_aware_utc(period["applied_at"])
safety_days = period["safety_interval_days"]
safe_date = applied_at + timedelta(days=safety_days)
if safe_date > ensure_aware_utc(planned_harvest_date):
```
- Import ergänzen: `from app.common.datetimes import ensure_aware_utc`.
- `planned_harvest_date` wird pro Vergleich normalisiert (der Aufrufer kann weiterhin
  naiv liefern; die Engine ist damit robust unabhängig vom Aufrufer).

### 4.3 `src/backend/app/domain/services/ipm_service.py`
`check_harvest_safety` (Z. 260-266):

Vorher:
```python
if planned_date is None:
    planned_date = datetime.now()
```
Nachher:
```python
if planned_date is None:
    planned_date = now_utc()
```
- Import: `from app.common.datetimes import now_utc`. Nicht mehr benötigten
  `datetime`-Import prüfen (bleibt evtl. für Typannotation `datetime | None`).

### 4.4 `src/backend/app/domain/services/harvest_service.py`
`create_harvest_batch` (Z. 105-108):

Vorher:
```python
harvest_date = batch.harvest_date or datetime.now()
```
Nachher:
```python
harvest_date = ensure_aware_utc(batch.harvest_date) or now_utc()
```
- `ensure_aware_utc` deckt den Fall ab, dass `batch.harvest_date` vom Client naiv kommt.
- Import: `from app.common.datetimes import ensure_aware_utc, now_utc`.

### 4.5 `src/backend/app/domain/engines/resistance_engine.py`
`validate_treatment` (Z. 32-38) und `suggest_alternatives` (Z. 74-80):

Vorher:
```python
cutoff = datetime.now() - timedelta(days=ROTATION_WINDOW_DAYS)
…
applied_at = app["applied_at"]
if isinstance(applied_at, str):
    applied_at = datetime.fromisoformat(applied_at)
if applied_at < cutoff:
```
Nachher:
```python
cutoff = now_utc() - timedelta(days=ROTATION_WINDOW_DAYS)
…
applied_at = ensure_aware_utc(app["applied_at"])
if applied_at < cutoff:
```
- Import: `from app.common.datetimes import ensure_aware_utc, now_utc`.
- Grenzfall `applied_at is None`: `ensure_aware_utc(None)` gibt `None` → Vergleich
  `None < cutoff` würde erneut `TypeError` werfen. Deshalb Guard ergänzen:
  `if applied_at is None or applied_at < cutoff: continue` (siehe §6).

### 4.6 `src/backend/app/domain/engines/hst_validator.py`
`_check_recovery` (Z. 211-230):

Vorher:
```python
now = datetime.now()
…
if isinstance(completed_at, str):
    completed_at = datetime.fromisoformat(completed_at)
…
recovery_end = latest + timedelta(days=recovery_days)
recovered = now >= recovery_end
days_remaining = max(0, (recovery_end - now).days) if not recovered else 0
```
Nachher:
```python
now = now_utc()
…
completed_at = ensure_aware_utc(completed_at)
if completed_at is None:
    continue
…
recovery_end = latest + timedelta(days=recovery_days)
recovered = now >= recovery_end
days_remaining = max(0, (recovery_end - now).days) if not recovered else 0
```
- Import: `from app.common.datetimes import ensure_aware_utc, now_utc`.
- Behebt zugleich den Lokalzeit-Fehler (§2.2b), da `now_utc()` statt lokalem
  `datetime.now()`.
- `completed_at is None`-Guard bleibt (Z. 217 vorhanden), zusätzlich `None` nach
  `ensure_aware_utc` abfangen (redundant, aber defensiv).

### 4.7 Weitere naive `datetime.now()`-Stellen (Sichtprüfung, nicht Teil des Kern-Fixes)
`inspection_scheduler.py:46,66` nutzt ebenfalls naives `datetime.now()`. Vergleicht dort
`last_at` (aus DB, potenziell aware). **Empfehlung:** im selben AP mit-härten
(`now_utc()` + `ensure_aware_utc(last_at)` in `next_inspection_date`), da identisches
Muster und derselbe IPM-Service. Falls Scope-Begrenzung nötig, als Folge-Ticket notieren.
`calendar_service.py:312` behandelt tz bereits defensiv — keine Änderung.

---

## 5. Testplan

### 5.1 Betroffene Testdateien (bestehend)
- `src/backend/tests/unit/domain/engines/test_safety_interval_engine.py`
- `src/backend/tests/unit/domain/engines/test_resistance_engine.py`
- `src/backend/tests/unit/domain/engines/test_hst_validator.py`
- `src/backend/tests/unit/domain/engines/test_hst_validator_with_activities.py`
- API-Ebene: bestehende IPM-/Harvest-API-Tests unter `src/backend/tests/api/` bzw.
  `tests/integration/` (Karenz-Gate End-to-End → 422).

### 5.2 Neue Unit-Testfälle

**Regressionstest Karenz-Gate (der HEUTE 500/TypeError auslöst):**
In `test_safety_interval_engine.py`:
```python
from datetime import UTC, datetime, timedelta

def test_can_harvest_tz_aware_applied_at_vs_naive_planned_date(engine):
    """Regression DOM-1: tz-aware applied_at (wie aus der DB) darf gegen
    einen naiven planned_harvest_date nicht mit TypeError crashen."""
    periods = [
        {
            "active_ingredient": "Spinosad",
            # so wie es die AQL-Query liefert: ISO mit +00:00
            "applied_at": (datetime.now(UTC) - timedelta(days=2)).isoformat(),
            "safety_interval_days": 21,
        }
    ]
    naive_planned = datetime.now()  # naiv, wie ipm_service-Default heute
    can, blocking = engine.can_harvest(periods, naive_planned)
    assert can is False
    assert len(blocking) == 1
    assert blocking[0]["active_ingredient"] == "Spinosad"
```
Vor dem Fix: `TypeError`. Nach dem Fix: `can is False`, ein Blocker.

**Regressionstest auf Service-/API-Ebene (500 → 422):**
Neuer Test in der IPM-/Harvest-API-Suite:
```python
def test_create_harvest_batch_blocked_by_active_karenz_returns_422(client, seeded_karenz):
    """Regression DOM-1: aktive Karenz -> 422 KarenzViolationError, nicht 500."""
    resp = client.post(f"/api/v1/…/plants/{plant_key}/harvest-batches", json={...})
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "KARENZ_VIOLATION"  # o.ä. laut exceptions.py
```
Fixture `seeded_karenz`: TreatmentApplication mit `applied_at = now_utc()-2d`,
Treatment mit `safety_interval_days=21`, Harvest ohne explizites Datum (Default-`now`).
Vor dem Fix: 500. Nach dem Fix: 422.

**Resistance-Manager:**
```python
def test_validate_treatment_tz_aware_applications_no_crash():
    mgr = ResistanceManager()
    apps = [
        {"active_ingredient": "AzaMax",
         "applied_at": (datetime.now(UTC) - timedelta(days=5)).isoformat()}
        for _ in range(3)
    ]
    ok, msg = mgr.validate_treatment(apps, "AzaMax")
    assert ok is False           # 3 Anwendungen -> Limit erreicht
```
Plus Grenzfall `applied_at=None` (§6): darf nicht crashen, Eintrag wird übersprungen.

**HST-Validator (crash + Lokalzeit-Korrektheit):**
```python
def test_check_recovery_tz_aware_completed_at_no_crash():
    v = HSTValidator()
    tasks = [{"name": "topping",
              "completed_at": (datetime.now(UTC) - timedelta(days=1)).isoformat()}]
    result = v.validate("watering", "vegetative", tasks, species_name="cannabis")
    # recovery cannabis = 7d -> noch nicht erholt, aber KEIN TypeError
    assert result["recovery_status"]["recovered"] is False
```
Ergänzend ein Test, der belegt, dass ein exakt „recovery_days" alter, tz-aware
`completed_at` unabhängig von der Prozess-Lokalzeit als erholt gilt (Lokalzeit-Fix):
z.B. via `freezegun`/Monkeypatch von `now_utc` in einer Nicht-UTC-Zeitzone.

**Helper-Unit-Tests** (`tests/unit/common/test_datetimes.py`, neu):
- `ensure_aware_utc(None) is None`
- naiver `datetime` → `tzinfo == UTC`
- aware Nicht-UTC → korrekt nach UTC konvertiert
- ISO-String mit und ohne Offset → beide aware UTC

### 5.3 Bestehende Tests
Fixtures in `test_safety_interval_engine.py` nutzen aktuell teils **naive**
`datetime.now()` für `applied_at` (Z. 25 ff.). Diese bleiben grün (Helper interpretiert
naiv als UTC). Prüfen, dass kein Test sich auf das alte `isinstance(str)`-Verhalten
verlässt.

---

## 6. Grenzfälle

1. **Naive Legacy-Daten in der DB.** Frühere Datensätze könnten `applied_at` ohne Offset
   gespeichert haben (z.B. Alt-Seeds, manuelle Importe). `ensure_aware_utc` interpretiert
   naive Werte **als UTC** (`replace(tzinfo=UTC)`). Das ist die pragmatisch korrekte
   Annahme, da der aktuelle Schreibpfad (`_now()`) UTC schreibt. Dokumentieren, dass
   naive Legacy-Werte damit implizit als UTC gelten — kein Datenverlust, keine Migration.
2. **DST / Sommerzeit.** Durch konsequentes UTC in Vergleich **und** „jetzt" (`now_utc`)
   gibt es keine DST-Sprünge in den Recovery-/Karenz-Fenstern. Der bisherige
   HST-Lokalzeit-`datetime.now()` hätte um den DST-Offset falsch gerechnet — mit dem Fix
   behoben.
3. **`None`-Werte.** `applied_at`/`completed_at`/`harvest_date` sind laut Modell
   `datetime | None` (`ipm.py:128`, `harvest`/`post_harvest`). `ensure_aware_utc(None)`
   → `None`. Jede Vergleichsstelle braucht davor einen `None`-Guard (Karenz:
   `applied_at` ist über die AQL-Query praktisch nie None, aber defensiv behandeln;
   Resistance: `continue`; HST: bereits `continue` bei None). Nicht ungefiltert in `<`/`>`
   geben.
4. **Gemischte Aware/Naive-Listen.** Falls eine Liste sowohl aware als auch naive Einträge
   enthält (Mix aus neuen + Legacy-Daten), normalisiert der Helper jeden Eintrag einzeln
   → homogen UTC. Interne `latest`-Vergleiche in HST/`earliest_safe_harvest_date` sind
   danach aware-vs-aware und stabil.
5. **Client liefert aware Nicht-UTC** (z.B. `+02:00`). `astimezone(UTC)` konvertiert
   korrekt; kein Fehler, kein Offset-Bug.

---

## 7. Akzeptanzkriterien & Rollout

### Akzeptanzkriterien (Checkliste)
- [ ] Neues Modul `app/common/datetimes.py` mit `now_utc()` und `ensure_aware_utc()`
      inkl. Unit-Tests (`tests/unit/common/test_datetimes.py`).
- [ ] `safety_interval_engine.can_harvest` und `earliest_safe_harvest_date` vergleichen
      ausschließlich tz-aware-UTC-Werte; kein `isinstance(str)`-Boilerplate mehr.
- [ ] `ipm_service.check_harvest_safety` und `harvest_service.create_harvest_batch`
      nutzen `now_utc()` / `ensure_aware_utc()` statt naivem `datetime.now()`.
- [ ] `resistance_engine.validate_treatment` und `suggest_alternatives` UTC-konsistent,
      mit `None`-Guard.
- [ ] `hst_validator._check_recovery` nutzt `now_utc()` (behebt Crash **und**
      Lokalzeit-Fehler).
- [ ] Regressionstest vorhanden, der vor dem Fix `TypeError`/500 und nach dem Fix `422`
      (bzw. `can_harvest is False`) liefert — auf Engine- **und** API-Ebene.
- [ ] Alle bestehenden IPM-/Harvest-/HST-Unit- und API-Tests grün.
- [ ] `ruff` clean, `mypy`/Typprüfung ok, keine neuen `datetime.now()`-ohne-`UTC`-Stellen
      in den vier Kern-Dateien (grep-Check: `grep -rn "datetime.now()" app/domain/engines
      app/domain/services | grep -v now_utc` ⇒ leer für die geänderten Dateien).
- [ ] REQ-010 Szenario 2 („Karenzzeit-Blockierung") reproduzierbar als 422.

### Rollout / Risiko
- **Risiko: niedrig.** Reiner Bugfix ohne Schema-/API-Vertragsänderung; das API-Verhalten
  wird *korrekter* (422 statt 500), keine bisher funktionierende Route ändert ihren
  Erfolgs-Contract.
- **Keine Datenmigration.** Normalisierung erfolgt lesend; bestehende Datensätze bleiben
  unverändert.
- **Abwärtskompatibel.** Aufrufer, die naive `datetime` übergeben, funktionieren weiter
  (Helper normalisiert). Frontend unverändert.
- **Verifikation vor Merge:** kompletter Backend-Testlauf (pytest) + gezielter
  Regressionstest; anschließend manueller Smoke gegen einen Datensatz mit aktiver Karenz
  (Ernte-POST → 422 erwartet).
- **Aufwand:** ~0,5 Personentag (1 neues Modul, 4 Dateien Kern + optional
  `inspection_scheduler.py`, ~6 neue Tests).
