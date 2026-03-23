# HA-Integration Style Guide — Home Assistant Custom Component

> Verbindlicher Style Guide fuer die Kamerplanter Home Assistant Custom Integration.
> Wird durch **ruff** (Linting), **mypy** (Typsicherheit) und **HA-Validierung** (hassfest) geprueft.

**Scope:** `src/ha-integration/custom_components/kamerplanter/`

---

## 1. Statische Analyse & Tooling

| Tool | Zweck | Status |
|------|-------|--------|
| **Ruff** | Python Linting + Formatting | Geteilt mit Backend-Config |
| **MyPy** | Statische Typanalyse | Geteilt mit Backend-Config |
| **hassfest** | HA-Manifest-Validierung | CI-Integration empfohlen |
| **pytest** | Unit-Tests | Aufzubauen |

### 1.1 Empfohlene Ruff-Konfiguration (HA-spezifisch)

```toml
# In pyproject.toml oder eigene ruff.toml in src/ha-integration/
[tool.ruff]
line-length = 120
target-version = "py312"   # HA 2024.x erfordert Python 3.12+

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "SIM"]
ignore = ["B008"]
```

### 1.2 CI-Pruefung

```bash
ruff check src/ha-integration/
ruff format --check src/ha-integration/
# hassfest (optional, erfordert HA-Umgebung)
python -m homeassistant.scripts.hassfest --integration-path src/ha-integration/custom_components/kamerplanter
```

---

## 2. Verzeichnisstruktur

```
src/ha-integration/
├── custom_components/kamerplanter/
│   ├── __init__.py              # Setup + Service-Handler (~500 Zeilen)
│   ├── api.py                   # REST-Client (KamerplanterApi dataclass)
│   ├── config_flow.py           # ConfigFlow + OptionsFlow
│   ├── coordinator.py           # 5 DataUpdateCoordinators
│   ├── sensor.py                # 30+ Sensor-Entities
│   ├── binary_sensor.py         # 5 Binary-Sensor-Entities
│   ├── button.py                # Refresh-Button
│   ├── calendar.py              # Kalender-Entities
│   ├── todo.py                  # Todo-Listen
│   ├── diagnostics.py           # Diagnostik-Daten
│   ├── const.py                 # Konstanten (DOMAIN, Keys, Defaults)
│   ├── services.yaml            # Service-Definitionen
│   ├── strings.json             # Englische Strings (Fallback)
│   ├── translations/
│   │   ├── en.json              # Englische Uebersetzungen
│   │   └── de.json              # Deutsche Uebersetzungen
│   ├── manifest.json            # Integration-Metadaten
│   ├── brand/                   # Logo/Icon
│   └── www/                     # Custom Lovelace Cards
├── hacs.json                    # HACS-Metadaten
└── Dockerfile.dev               # Entwicklungs-Container
```

### 2.1 Dateizuordnung

| Datei | Verantwortung |
|-------|---------------|
| `__init__.py` | `async_setup_entry`, `async_unload_entry`, Service-Handler |
| `api.py` | HTTP-Kommunikation mit Kamerplanter-Backend |
| `config_flow.py` | Setup-Wizard (URL → Auth → Tenant) |
| `coordinator.py` | Daten-Polling + Enrichment |
| `sensor.py` | Alle `SensorEntity`-Klassen |
| `binary_sensor.py` | Alle `BinarySensorEntity`-Klassen |
| `const.py` | Konstanten, Domain-Name, Config-Keys |

---

## 3. Namenskonventionen

### 3.1 Konstanten (`const.py`)

```python
from typing import Final

DOMAIN: Final = "kamerplanter"

# Config Keys (CONF_ Praefix)
CONF_API_KEY: Final = "api_key"
CONF_TENANT_SLUG: Final = "tenant_slug"
CONF_LIGHT_MODE: Final = "light_mode"

# Polling Defaults (DEFAULT_ / MIN_ Praefix)
DEFAULT_POLL_PLANTS: Final = 300
MIN_POLL_PLANTS: Final = 120

# Platforms
PLATFORMS: Final = ["sensor", "binary_sensor", "calendar", "todo", "button"]

# Events (EVENT_ Praefix)
EVENT_TASK_COMPLETED: Final = "kamerplanter_task_completed"
EVENT_CARE_DUE: Final = "kamerplanter_care_due"

# Services (SERVICE_ Praefix)
SERVICE_REFRESH: Final = "refresh_data"
SERVICE_FILL_TANK: Final = "fill_tank"
```

**Praefixe:**
| Praefix | Zweck | Beispiel |
|---------|-------|----------|
| `CONF_` | Config-Flow/Options Keys | `CONF_API_KEY` |
| `DEFAULT_` | Default-Werte | `DEFAULT_POLL_PLANTS` |
| `MIN_` | Minimum-Werte | `MIN_POLL_PLANTS` |
| `EVENT_` | HA-Event-Namen | `EVENT_TASK_COMPLETED` |
| `SERVICE_` | Service-Namen | `SERVICE_FILL_TANK` |

### 3.2 Entity IDs

```
Format:  {platform}.kp_{resource_slug}_{suffix}
Beispiel: sensor.kp_plant_12345_phase
          binary_sensor.kp_loc_garden_needs_attention
          calendar.kp_phases
          todo.kp_tasks
```

### 3.3 Unique IDs

```
Format:  {entry_id}_kp_{resource_slug}_{suffix}
Beispiel: abc123_kp_plant_12345_phase
```

### 3.4 Slugification

```python
def _slugify_key(key: str) -> str:
    """ArangoDB-Keys: Bindestriche → Unterstriche, lowercase."""
    return key.replace("-", "_").lower()

def _slugify_label(label: str) -> str:
    """Freitext: Transliteration (ae→a, ue→u, ss→ss) + alphanumerisch."""
    # ...
```

---

## 4. API-Client Pattern

### 4.1 Dataclass

```python
@dataclass
class KamerplanterApi:
    base_url: str
    session: ClientSession
    api_key: str | None = None
    tenant_slug: str | None = None

    @property
    def _tenant_prefix(self) -> str:
        if self.tenant_slug:
            return f"/api/v1/t/{self.tenant_slug}"
        return "/api/v1"

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = f"{self.base_url}{self._tenant_prefix}{path}"
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        async with self.session.request(method, url, headers=headers, **kwargs) as resp:
            if resp.status == 401:
                raise KamerplanterAuthError("Invalid credentials")
            resp.raise_for_status()
            return await resp.json()
```

**Regeln:**
- `@dataclass` fuer den API-Client (kein Pydantic)
- Alle Methoden `async`
- Methoden-Benennung: `async_get_{resource}()`, `async_{action}_{resource}()`
- Tenant-Prefix automatisch in `_request()`
- Authorization Header nur wenn `api_key` vorhanden (Light-Modus)

### 4.2 Exception-Hierarchie

```python
class KamerplanterApiError(Exception):
    """Basisklasse fuer alle API-Fehler."""

class KamerplanterAuthError(KamerplanterApiError):
    """401/403 — triggert Re-Auth Flow."""

class KamerplanterConnectionError(KamerplanterApiError):
    """Netzwerk/HTTP-Fehler — triggert Retry."""
```

### 4.3 Fehlerbehandlung in _request

```python
try:
    async with self.session.request(...) as resp:
        if resp.status == 401:
            raise KamerplanterAuthError(...)
        resp.raise_for_status()
        return await resp.json()
except KamerplanterApiError:
    raise                                    # Eigene Errors durchlassen
except ClientResponseError as err:
    raise KamerplanterConnectionError(...) from err
except ClientError as err:
    raise KamerplanterConnectionError(...) from err
```

---

## 5. Coordinator-Pattern

### 5.1 Basisstruktur

```python
class KamerplanterPlantCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Pollt Pflanzendaten + enriched mit Naehrstoffplan, Dosierungen, Phasen."""

    def __init__(self, hass: HomeAssistant, api: KamerplanterApi, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_plants",
            update_interval=timedelta(seconds=DEFAULT_POLL_PLANTS),
        )
        self.api = api
        self.entry = entry

    async def _async_update_data(self) -> list[dict[str, Any]]:
        try:
            plants = await self.api.async_get_plants()
            # Enrichment: Zusaetzliche Daten pro Pflanze laden
            for plant in plants:
                plant["_nutrient_plan"] = await self.api.async_get_plant_nutrient_plan(plant["key"])
            return plants
        except KamerplanterAuthError as err:
            raise ConfigEntryAuthFailed from err
        except KamerplanterConnectionError as err:
            raise UpdateFailed(f"Connection error: {err}") from err
```

### 5.2 Coordinator-Uebersicht

| Coordinator | Polling-Intervall | Daten |
|------------|-------------------|-------|
| `KamerplanterPlantCoordinator` | 300s | Pflanzen + Naehrstoffplan + Dosierungen + Phasen |
| `KamerplanterLocationCoordinator` | 300s | Standorte + Runs + Tanks |
| `KamerplanterAlertCoordinator` | 60s | Ueberfaellige Aufgaben |
| `KamerplanterRunCoordinator` | 300s | Pflanzdurchlaeufe + Phasen + Naehrstoffplan |
| `KamerplanterTaskCoordinator` | 300s | Offene Aufgaben |

### 5.3 Enrichment-Strategie

```python
# In _async_update_data: Daten anreichern statt separate API-Calls pro Entity
for plant in plants:
    plant["_nutrient_plan"] = await self.api.async_get_plant_nutrient_plan(...)
    plant["_current_dosages"] = await self.api.async_get_plant_current_dosages(...)
    plant["_phase_history"] = await self.api.async_get_plant_phase_timeline(...)
```

**Regeln:**
- Enrichment-Felder mit `_` Praefix: `_nutrient_plan`, `_primary_run`
- Besser **ein** grosser Coordinator-Fetch als viele kleine Entity-Fetches
- Fehler bei Enrichment: loggen + ueberspringen, nicht gesamten Update abbrechen

### 5.4 Fehler-Mapping

| API Exception | HA Exception | Effekt |
|--------------|-------------|--------|
| `KamerplanterAuthError` | `ConfigEntryAuthFailed` | Re-Auth Flow |
| `KamerplanterConnectionError` | `UpdateFailed` | Exponentieller Backoff |

---

## 6. Entity-Pattern

### 6.1 Basis-Entity-Klasse

```python
class KpSensorBase(CoordinatorEntity, RestoreEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        resource_key: str,
        suffix: str,
        device_info: DeviceInfo,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_kp_{_slugify_key(resource_key)}_{suffix}"
        self.entity_id = f"sensor.kp_{_slugify_key(resource_key)}_{suffix}"
        self._attr_device_info = device_info
```

**Mixins:**
- `CoordinatorEntity` — Automatisches Update bei Coordinator-Refresh
- `RestoreEntity` — State-Wiederherstellung nach HA-Neustart
- `SensorEntity` / `BinarySensorEntity` / etc. — Plattform-Basis

### 6.2 State Restoration

```python
async def async_added_to_hass(self) -> None:
    await super().async_added_to_hass()
    last = await self.async_get_last_state()
    if last and last.state not in ("unknown", "unavailable", ""):
        self._attr_native_value = last.state
        self.async_write_ha_state()
    # Sofort aus Coordinator populieren falls Daten vorhanden
    if self.coordinator.data:
        self._handle_coordinator_update()
```

### 6.3 Device Info

```python
def plant_device_info(entry: ConfigEntry, plant: dict) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, f"{entry.entry_id}_plant_{plant['key']}")},
        name=plant.get("display_name", plant["key"]),
        manufacturer="Kamerplanter",
        model="Plant Instance",
        via_device=(DOMAIN, entry.entry_id),  # Hub-Beziehung
    )
```

**Regeln:**
- Identifier-Tuple: `(DOMAIN, "{entry_id}_{type}_{key}")`
- `via_device`: Alle Entities gehoeren zum Server-Hub-Device
- `manufacturer`: Immer `"Kamerplanter"`
- `model`: Beschreibender Typ (Plant Instance, Location, Tank)

---

## 7. Config Flow

### 7.1 Mehrstufiger Setup

```python
class KamerplanterConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Schritt 1: URL eingeben."""
        if user_input is not None:
            # Validierung...
            if is_light_mode:
                return self.async_create_entry(...)   # Direkt fertig
            return await self.async_step_auth()       # Weiter zu Auth
        return self.async_show_form(step_id="user", data_schema=STEP_USER_SCHEMA)

    async def async_step_auth(self, user_input=None):
        """Schritt 2: API-Key eingeben."""
        # ...

    async def async_step_tenant(self, user_input=None):
        """Schritt 3: Tenant auswaehlen (nur bei >1 Tenant)."""
        # ...
```

**Regeln:**
- Schritte: `async_step_{step_id}()`
- Light-Modus: Auth ueberspringen, direkt Entry erstellen
- Tenant-Schritt nur wenn >1 Tenant verfuegbar
- Fehler-Keys in `strings.json`: `config.error.{code}`

### 7.2 Options Flow

```python
class KamerplanterOptionsFlow(OptionsFlow):
    async def async_step_init(self, user_input=None):
        """Polling-Intervalle konfigurieren."""
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional("poll_interval_plants", default=300): vol.All(int, vol.Range(min=120)),
                vol.Optional("poll_interval_alerts", default=60): vol.All(int, vol.Range(min=30)),
            }),
        )
```

---

## 8. Service-Handler

### 8.1 Registrierung

```python
# In __init__.py → async_setup_entry()
hass.services.async_register(DOMAIN, SERVICE_FILL_TANK, _handle_fill_tank)
hass.services.async_register(DOMAIN, SERVICE_CONFIRM_CARE, _handle_confirm_care)
```

### 8.2 Handler-Pattern

```python
async def _handle_fill_tank(call: ServiceCall) -> None:
    """Service-Handler fuer Tank-Befuellung."""
    _LOGGER.debug("fill_tank called: %s", dict(call.data))

    # 1. Entity/Key Resolution
    tank_key = _resolve_tank_key(call.data)
    if not tank_key:
        _LOGGER.error("Could not resolve tank_key from %s", dict(call.data))
        return

    # 2. API-Call
    try:
        result = await api.async_fill_tank(tank_key, payload)
        _LOGGER.info("Tank fill recorded: %s", result.get("fill_event", {}).get("key"))
    except Exception:
        _LOGGER.exception("Failed to fill tank %s", tank_key)
```

**Regeln:**
- Alle Inputs loggen (Debug-Level)
- Entity-ID → Key Resolution mit Fallback-Kette
- Try/Except mit `_LOGGER.exception()` (nie stille Fehler)
- Graceful Return bei fehlenden Daten (kein Raise)

### 8.3 Entity-ID Resolution

```python
def _resolve_tank_key(call_data: dict) -> str | None:
    """Tank-Key aus entity_id oder direktem Parameter aufloesen."""
    # 1. Direkt angegeben
    if "tank_key" in call_data:
        return call_data["tank_key"]
    # 2. State-Attribute der Entity
    entity_id = call_data.get("entity_id")
    if entity_id:
        state = hass.states.get(entity_id)
        if state and (key := state.attributes.get("tank_key")):
            return key
    # 3. Aus Entity-ID Pattern parsen
    # sensor.kp_{tank_slug}_{suffix} → tank_slug
    return None
```

---

## 9. services.yaml

```yaml
fill_tank:
  name: "Tank befuellen"              # Deutsche Labels (Zielmarkt)
  description: "Fuellt einen Tank und erfasst Messwerte"
  fields:
    entity_id:
      name: "Tank-Sensor"
      description: "Entity-ID eines Tank-Sensors"
      required: false
      selector:
        entity:
          integration: kamerplanter
          domain: sensor
    volume_liters:
      name: "Volumen (Liter)"
      required: true
      selector:
        number:
          min: 0.1
          max: 10000
          step: 0.1
          unit_of_measurement: "L"
```

**Regeln:**
- Service-Name: `snake_case` (englisch)
- Labels/Beschreibungen: **Deutsch** (primaerer Zielmarkt)
- `selector` fuer HA UI-Integration
- `entity_id` + direkter Key als Alternative (beide optional)

---

## 10. Translations

### 10.1 Dateistruktur

```
strings.json          → Englisch (Fallback/Referenz)
translations/en.json  → Englisch
translations/de.json  → Deutsch
```

### 10.2 Key-Struktur

```json
{
  "config": {
    "step": {
      "user": {
        "title": "Connect to Kamerplanter",
        "data": { "url": "URL" }
      },
      "auth": {
        "title": "Authentication",
        "data": { "api_key": "API Key" }
      }
    },
    "error": {
      "cannot_connect": "Cannot connect to Kamerplanter",
      "invalid_auth": "Invalid API key or credentials"
    },
    "abort": {
      "already_configured": "Already configured"
    }
  },
  "options": {
    "step": {
      "init": {
        "title": "Polling Settings",
        "data": { "poll_interval_plants": "Plant polling interval (seconds)" }
      }
    }
  }
}
```

---

## 11. Type Hints

```python
from __future__ import annotations      # PEP 563 (immer in HA-Code)

from typing import Any, Final
from homeassistant.config_entries import ConfigEntry

type KamerplanterConfigEntry = ConfigEntry   # Python 3.12+ Type-Alias

async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
    ...

def _resolve_tank_key(call_data: dict) -> str | None:
    ...
```

**Regeln:**
- `from __future__ import annotations` in **jeder** Datei
- `str | None` Syntax (PEP 604)
- `typing.Final` fuer Konstanten
- `type` Keyword fuer Aliases (Python 3.12+)

---

## 12. Logging

```python
import logging

_LOGGER = logging.getLogger(__name__)

# Standard-Logging (NICHT structlog — HA verwendet stdlib logging)
_LOGGER.debug("fill_tank called: %s", dict(call.data))
_LOGGER.info("Tank fill recorded: %s", key)
_LOGGER.warning("Missing nutrient plan for plant %s", plant_key)
_LOGGER.error("Could not resolve tank_key from %s", data)
_LOGGER.exception("Failed to fill tank %s", tank_key)   # Mit Traceback
```

**Regeln:**
- `_LOGGER = logging.getLogger(__name__)` (HA-Standard)
- **Nicht** structlog verwenden (HA-Inkompatibel)
- `%s` String-Formatierung (lazy evaluation)
- `_LOGGER.exception()` fuer Fehler mit Traceback

---

## 13. Deployment

```bash
# 1. Dateien kopieren
kubectl cp src/ha-integration/custom_components/kamerplanter/ \
  default/homeassistant-0:/config/custom_components/kamerplanter/

# 2. Bytecode-Cache loeschen (PFLICHT)
kubectl exec homeassistant-0 -n default -- \
  rm -rf /config/custom_components/kamerplanter/__pycache__

# 3. Pod neustarten
kubectl delete pod homeassistant-0 -n default
```

**WICHTIG:** `__pycache__` **muss** geloescht werden, sonst laedt HA den alten Bytecode.

---

## 14. manifest.json

```json
{
  "domain": "kamerplanter",
  "name": "Kamerplanter",
  "codeowners": ["@kamerplanter"],
  "config_flow": true,
  "documentation": "https://github.com/...",
  "iot_class": "cloud_polling",
  "requirements": [],
  "version": "0.1.0",
  "homeassistant": "2024.1.0"
}
```

**Regeln:**
- `requirements: []` — Keine externen Python-Dependencies (nur HA-Builtins)
- `iot_class: "cloud_polling"` — Daten werden von externer API gepollt
- `config_flow: true` — Pflicht fuer UI-Setup
- Version: **SemVer**

---

## 15. Zusammenfassung der Pruefkette

```
Code-Aenderung
    │
    ├─→ ruff check           → Import-Ordnung, Naming, Bugs
    ├─→ ruff format --check  → Formatierung (120 Zeichen)
    ├─→ mypy                 → Typsicherheit
    ├─→ hassfest (optional)  → Manifest-Validierung
    └─→ kubectl cp + restart → Deployment zum Testen
```
