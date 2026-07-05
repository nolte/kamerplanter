# Spezifikation: REQ-046 - Wetterdienst-Datenquellen & -Konfiguration

```yaml
ID: REQ-046
Titel: Wetterdienst-Datenquellen — öffentliche Dienste vs. Home-Assistant-Sensoren (nutzerkonfigurierbar)
Kategorie: Monitoring / Integration
Fokus: Beides
Technologie: Python 3.14+, FastAPI, httpx, ArangoDB, Celery, Home Assistant REST API, React 19, TypeScript 5.9, MUI 7, Redux Toolkit
Status: Entwurf
Version: 1.0
Abhängigkeit: REQ-005 (Hybrid-Sensorik/Wetter — Basis-Datenmodell), REQ-002 (Standort), REQ-018 (HA-Aktorik/REST — geteilter HA-Client), REQ-023 (Secret-Storage für API-Keys), REQ-024 (Mandanten-Scoping), REQ-037 (ET — Konsument), REQ-039 (Winterhärte — Konsument), REQ-041 (NASA POWER — registriert Adapter hier)
```

## Versionshistorie

| Version | Datum | Änderung |
|---------|-------|----------|
| 1.0 | 2026-07-05 | Initialer Entwurf — konsolidiert die über REQ-005/039/041 verstreute Wetter-Datenquellen-Schicht in eine SSOT. Führt die nutzerseitige Datenquellen-Auswahl (öffentlicher Wetterdienst **vs.** Home-Assistant-Sensoren) samt Konfigurations-UI und den `HomeAssistantWeatherAdapter` (native `weather.*`-Entität **und** Einzel-Sensor-Mapping) ein. Etabliert `WeatherAdapter`-ABC, `WeatherAdapterRegistry` und `Site.weather_source_priority` als hier beheimatete, geteilte Infrastruktur. |

## 1. Business Case

### User Stories

- **Als Freiland-Gärtner ohne eigene Sensorik** möchte ich einen **öffentlichen Wetterdienst** (z. B. Open-Meteo, ohne Anmeldung) für meinen Standort auswählen, **damit** Frostwarnungen, Regenvorhersagen und die bedarfsgerechte Bewässerung (REQ-037) sofort funktionieren, ohne dass ich Hardware kaufen muss.
- **Als Smart-Home-Nutzer mit eigener Wetterstation** möchte ich, dass Kamerplanter die **Außensensoren aus meiner Home-Assistant-Installation** (Temperatur, Feuchte, Regenmesser, Wind, Luftdruck) als Wetterquelle für meinen Standort verwendet, **damit** die App meine tatsächlich vor Ort gemessenen Werte nutzt statt einer gerasterten Vorhersage für die nächste Großstadt.
- **Als HA-Nutzer mit einer `weather.*`-Integration** (z. B. Met.no, DWD-HA-Integration) möchte ich diese **eine Entität** als Wetterquelle anbinden, **damit** ich die in HA bereits gepflegte Vorhersage direkt weiterverwende, ohne jeden Einzelwert manuell zu mappen.
- **Als Nutzer, der beides hat**, möchte ich **priorisieren**, welche Quelle Vorrang hat (z. B. „erst meine HA-Sensoren, dann Open-Meteo als Fallback"), **damit** bei einem HA-Ausfall die Freiland-Funktionen nicht ausfallen, sondern nahtlos auf den öffentlichen Dienst zurückfallen.
- **Als unsicherer Einsteiger** möchte ich vor dem Speichern **testen**, ob die gewählte Quelle erreichbar ist und plausible Werte liefert, **damit** ich nicht erst nach Tagen merke, dass die Konfiguration falsch war.

### Beschreibung

REQ-005 (§*Wetter-Integration (Freiland)*) hat das **Datenmodell** (`:WeatherForecast`, `weather_forecasts`, `has_forecast`-Edge, `source`-Provenance, Celery-Tasks, Warn-Tabelle) und die **drei öffentlichen Wetterquellen** DWD / OpenWeatherMap / Open-Meteo bereits konzeptionell etabliert — allerdings nur als Akzeptanzkriterium *„mindestens ein Adapter"* und ohne Konfigurationsschicht. REQ-041 (NASA POWER) und REQ-039 (Winterhärte) referenzieren zusätzlich ein `WeatherAdapter`-ABC, eine `WeatherAdapterRegistry` und `Site.weather_source_priority`, ohne dass eine dieser Komponenten im Code existiert oder einem REQ eindeutig **gehört**.

Diese Spezifikation schließt zwei Lücken:

1. **Die geteilte Adapter-Infrastruktur bekommt ein Zuhause.** REQ-046 ist die **SSOT** für das `WeatherAdapter`-ABC, die `WeatherAdapterRegistry`, die Quellen-Priorisierung (`Site.weather_source_priority`) und die konkrete Implementierung der öffentlichen Adapter DWD / OpenWeatherMap / Open-Meteo. REQ-041 (`NasaPowerWeatherAdapter`) und REQ-039 (`*ClimateNormalAdapter`) **registrieren** ihre Spezial-Adapter in dieser Registry; REQ-005 bleibt SSOT für Sensorik und das Basis-`:WeatherForecast`-Modell.
2. **Die nutzerseitige Datenquellen-Auswahl.** Der Kern dieses Requirements: Der Nutzer wählt und konfiguriert **pro Standort** in der UI, **woher** die Wetterdaten kommen — entweder ein **öffentlicher Wetterdienst** oder **Sensoren aus seiner Home-Assistant-Installation** — und in welcher **Priorität** mehrere Quellen greifen. Dafür kommt der neue **`HomeAssistantWeatherAdapter`** hinzu, der die bestehende HA-REST-Anbindung (`HomeAssistantClient.list_sensor_entities`/`get_state`, REQ-005/REQ-018) erstmals als **Wetterquelle** nutzbar macht — in zwei Betriebsarten (native `weather.*`-Entität **oder** Einzel-Sensor-Mapping).

**Abgrenzung (was dieses Dokument NICHT ist):**

- **Keine** Neudefinition des `:WeatherForecast`-Basismodells oder der Warn-Logik (Frost/Regen/Sturm) — das bleibt REQ-005.
- **Keine** Aktorik/Steuerung — das Schreiben in HA (Service-Calls) ist REQ-018. REQ-046 ist reine **Lese-Seite** (Datenerfassung).
- **Kein** neuer Wetter-*Provider* über die genannten hinaus (NASA POWER = REQ-041, Klimanormale = REQ-039/041).

**HA-Abhängigkeit bleibt strikt optional (Invariante, REQ-005):** Wetterfunktionen müssen mit rein öffentlichen Diensten voll funktionieren. Home Assistant ist eine **wählbare** Quelle, nie Voraussetzung. Wetter gilt weiterhin **nicht** als „Smart-Home-Funktion" und wird unabhängig von `smart_home_enabled` abgerufen; der `HomeAssistantWeatherAdapter` ist die einzige Ausnahme, die den HA-Client nutzt und daher ein gesetztes HA-Token voraussetzt (Degradation auf die nächste priorisierte Quelle, wenn HA fehlt/aus ist).

## 2. Datenmodell (ArangoDB)

### 2.1 Neue Collection `:WeatherSourceConfig` (die Nutzer-Konfiguration)

Die Datenquellen-Wahl je Standort ist ein eigenes Konfigurationsdokument (getrennt vom volatilen `:WeatherForecast`, das die Ergebnisdaten hält).

- **`:WeatherSourceConfig`** — Nutzerkonfiguration der Wetterquellen eines Standorts
  - Collection: `weather_source_configs`
  - Properties:
    - `weather_source_config_id: str`
    - `site_key: str` (Referenz auf Site, REQ-002; 1:1 pro Standort)
    - `tenant_key: str` (Mandanten-Scoping, REQ-024 — erbt von der Site, muss beim Schreiben mit `Site.tenant_key` übereinstimmen)
    - `enabled: bool = True` (Wetter-Datenerfassung für diesen Standort aktiv)
    - `sources: list[WeatherSourceEntry]` (geordnete Prioritätsliste, s. §2.2 — Index 0 = höchste Priorität)
    - `updated_at: datetime`
    - `updated_by: str` (User-Key — Audit)

> **Verhältnis zu `Site.weather_source_priority`:** `Site.weather_source_priority: list[str]` (in REQ-041 als REQ-002-Erweiterung skizziert) wird durch dieses reichere Modell **abgelöst**. Die reine `list[str]`-Prioritätsliste bleibt als **abgeleitete, denormalisierte Sicht** (`[e.source_name for e in sources if e.enabled]`) für Alt-Konsumenten erhalten und wird beim Speichern der Config mitgeführt. Neue Konsumenten lesen `:WeatherSourceConfig`.

### 2.2 Eingebettetes Modell `WeatherSourceEntry`

Ein Eintrag der Prioritätsliste — je nach `kind` ein öffentlicher Dienst oder eine HA-Quelle. Als eingebettetes Dokument (kein eigenes Collection-Doc) im `sources`-Array.

- `source_name: str` — technischer Registry-Schlüssel (`"dwd"`, `"openweathermap"`, `"open-meteo"`, `"nasa-power"`, `"ha-weather"`)
- `kind: Literal['public', 'home_assistant']` — Grobklasse für die UI-Umschaltung
- `enabled: bool = True`
- `config: WeatherSourcePublicConfig | WeatherSourceHaConfig | None` — quellenspezifische Zusatzkonfiguration (diskriminiert über `source_name`/`kind`); `None` für konfigurationsfreie Dienste (Open-Meteo, NASA POWER)

**`WeatherSourcePublicConfig`** (für `kind='public'`):
- `api_key_ref: str | None` — Referenz auf ein verschlüsselt gespeichertes Secret (Fernet, REQ-023), **nicht** der Klartext-Key. Nur für Dienste mit Key-Pflicht (OpenWeatherMap). Für DWD/Open-Meteo `None`.
- `units_hint: str | None` — optionaler Provider-spezifischer Hinweis (z. B. OWM `units=metric`); Default aus Adapter.

**`WeatherSourceHaConfig`** (für `kind='home_assistant'`):
- `mode: Literal['weather_entity', 'sensor_mapping']` — die beiden bestätigten HA-Betriebsarten.
- `weather_entity_id: str | None` — bei `mode='weather_entity'`: eine HA-`weather.*`-Entität (liefert `forecast[]` + aktuelle Bedingungen über `attributes`).
- `sensor_mapping: HaSensorMapping | None` — bei `mode='sensor_mapping'`: Zuordnung einzelner HA-`sensor.*`-Entitäten auf die `:WeatherForecast`-Felder.

**`HaSensorMapping`** (Feld → HA-Entity-ID, alle optional; nicht gemappte Felder bleiben `None`):
- `temp_min_entity: str | None`
- `temp_max_entity: str | None` (bzw. Momentan-Temperatur, wenn kein Min/Max verfügbar)
- `temp_current_entity: str | None`
- `humidity_entity: str | None`
- `precipitation_entity: str | None` (Regenmenge mm)
- `wind_speed_entity: str | None`
- `wind_gust_entity: str | None`
- `pressure_entity: str | None`

### 2.3 Erweiterung von `:WeatherForecast` (REQ-005, additiv)

Die Ergebnisdaten aller Quellen landen weiterhin in der bestehenden Collection `weather_forecasts` (REQ-005 §2). Additive, abwärtskompatible Felder (Defaults für Altdaten):

- `data_kind: Literal['forecast', 'observed', 'reanalysis'] = 'forecast'` — Provenance-Klassifizierung (bereits von REQ-041 eingeführt; hier bekräftigt). HA-Einzel-Sensoren liefern **`'observed'`** (Ist-Werte, keine Vorhersage); HA-`weather.*` liefert `'forecast'`; NASA POWER `'reanalysis'`.
- `is_current_conditions: bool = False` — kennzeichnet einen Momentan-/Ist-Datensatz (HA-Sensor-Ist-Werte) gegenüber einer Tages-Vorhersage.

Der bestehende `source`-Provenance-Enum (REQ-005) wird um den HA-Wetter-Herkunftswert erweitert:

```python
# REQ-005 (bestehend) + REQ-046 (neu: 'ha_weather')
SourceType = Literal[
    'ha_auto', 'mqtt_auto', 'modbus_auto', 'manual',
    'interpolated', 'fallback', 'weather_api',
    'ha_weather',  # NEU (REQ-046): Wetterdaten aus HA-Sensoren/weather.*-Entität
]
```

**Quality-Score-Ergänzung (REQ-005 §Quality-Score):** `ha_weather` = **0.9** (vor Ort gemessen/aus HA übernommen, höher als das gerasterte `weather_api`=0.7, aber unter direkt in Kamerplanter kalibrierten `ha_auto`=1.0, da Zuordnung/Provenance über HA indirekt ist).

### 2.4 Edges

```
Edge Collection            _from     _to                       Attribut
────────────────────────────────────────────────────────────────────────────
has_forecast               sites     weather_forecasts          // bestehend (REQ-005) — für ALLE source-Werte
has_weather_source_config  sites     weather_source_configs     // NEU — Standort ↔ Datenquellen-Konfiguration (1:1)
```

### 2.5 Beispiel-AQL

```aql
// Aktive Quellen-Priorität eines Standorts (höchste zuerst)
FOR cfg IN weather_source_configs
  FILTER cfg.site_key == @site_key AND cfg.tenant_key == @tenant_key AND cfg.enabled
  RETURN (
    FOR s IN cfg.sources FILTER s.enabled RETURN s.source_name
  )
```

## 3. Technische Umsetzung (Python)

Alle neuen Klassen folgen der 5-Layer-Architektur (NFR-001) und dem etablierten Adapter-Muster (ABC in `domain/interfaces/`, Impl in `data_access/external/`, Registrierung via Registry — analog `ExternalSourceAdapter` + `AdapterRegistry`).

### 3.1 `WeatherAdapter`-ABC (hier beheimatet)

```python
# app/domain/interfaces/weather_adapter.py  (NEU — SSOT REQ-046)
from abc import ABC, abstractmethod

from app.domain.models.weather import ClimateNormal, WeatherForecast


class WeatherAdapter(ABC):
    """Abstrakte Basis für alle Wetter-Datenquellen (öffentlich oder HA).

    Implementierungen registrieren sich per @WeatherAdapterRegistry.register.
    - Öffentliche Dienste (DWD/OpenWeatherMap/Open-Meteo/NASA-POWER) sprechen
      HTTP-APIs an.
    - Der HomeAssistantWeatherAdapter liest über den HA-REST-Client.
    """

    #: Eindeutiger Registry-Schlüssel; entspricht WeatherForecast.source.
    source_name: str
    #: Grobklasse zur UI-Umschaltung / Konfig-Diskriminierung.
    kind: str  # 'public' | 'home_assistant'
    #: Braucht dieser Adapter ein Secret (API-Key)?
    requires_api_key: bool = False

    @abstractmethod
    async def fetch_daily(
        self, *, latitude: float, longitude: float, config: object | None = None
    ) -> list[WeatherForecast]:
        """Liefert Tageswerte/Vorhersage. `config` ist der quellenspezifische
        WeatherSourceEntry.config (z. B. HA-Mapping oder OWM-Key-Ref)."""

    async def fetch_climate_normals(
        self, *, latitude: float, longitude: float
    ) -> ClimateNormal | None:
        """Optional — nur Adapter mit Klimanormalen (REQ-041/039) überschreiben."""
        return None

    async def health_check(self, *, config: object | None = None) -> bool:
        """Verbindungstest für die UI ('Quelle testen'). Default: fetch_daily
        an einem Referenzpunkt versuchen; Impl. dürfen leichtgewichtiger prüfen."""
        ...
```

### 3.2 `WeatherAdapterRegistry` (hier beheimatet)

```python
# app/domain/services/weather_adapter_registry.py  (NEU — SSOT REQ-046)
from app.domain.interfaces.weather_adapter import WeatherAdapter


class WeatherAdapterRegistry:
    """Registry aller Wetter-Adapter. Muster analog AdapterRegistry (REQ-011).

    REQ-041 (NasaPowerWeatherAdapter) und REQ-039 (Klimanormale-Adapter)
    registrieren sich hier — sie definieren KEINE eigene Registry.
    """

    _adapters: dict[str, type[WeatherAdapter]] = {}

    @classmethod
    def register(cls, adapter_cls: type[WeatherAdapter]) -> type[WeatherAdapter]:
        cls._adapters[adapter_cls.source_name] = adapter_cls
        return adapter_cls

    @classmethod
    def get(cls, source_name: str) -> type[WeatherAdapter] | None:
        return cls._adapters.get(source_name)

    @classmethod
    def all(cls) -> dict[str, type[WeatherAdapter]]:
        return dict(cls._adapters)

    @classmethod
    def public_sources(cls) -> list[str]:
        return [n for n, a in cls._adapters.items() if a.kind == "public"]
```

### 3.3 Öffentliche Adapter (DWD / OpenWeatherMap / Open-Meteo)

Die drei in REQ-005 nur benannten Adapter werden hier konkret spezifiziert. Sie implementieren `WeatherAdapter` und schreiben `:WeatherForecast` mit `source in {"dwd","openweathermap","open-meteo"}`, `kind="public"`, `data_kind="forecast"`.

```python
# app/data_access/external/open_meteo_weather_adapter.py  (NEU)
import httpx

from app.domain.interfaces.weather_adapter import WeatherAdapter
from app.domain.models.weather import WeatherForecast
from app.domain.services.weather_adapter_registry import WeatherAdapterRegistry


@WeatherAdapterRegistry.register
class OpenMeteoWeatherAdapter(WeatherAdapter):
    """Open-Meteo — kostenlos, ohne API-Key, global. Default-Public-Quelle."""

    source_name = "open-meteo"
    kind = "public"
    requires_api_key = False
    base_url = "https://api.open-meteo.com/v1/forecast"

    def __init__(self, http_client: httpx.AsyncClient, timeout_s: float = 20.0) -> None:
        self._client = http_client
        self._timeout = timeout_s

    async def fetch_daily(self, *, latitude, longitude, config=None) -> list[WeatherForecast]:
        params = {
            "latitude": latitude, "longitude": longitude,
            "daily": "temperature_2m_min,temperature_2m_max,precipitation_sum,"
                     "wind_speed_10m_max,wind_gusts_10m_max,relative_humidity_2m_mean,weather_code",
            "wind_speed_unit": "kmh", "timezone": "auto", "forecast_days": 7,
        }
        resp = await self._client.get(self.base_url, params=params, timeout=self._timeout)
        resp.raise_for_status()
        return self._map(resp.json())
    # _map(...) → WeatherForecast(source="open-meteo", data_kind="forecast", ...)
```

| Adapter | `source_name` | API-Key | Basis-URL | Abdeckung | Attribution |
|---------|---------------|---------|-----------|-----------|-------------|
| `OpenMeteoWeatherAdapter` | `open-meteo` | nein | `api.open-meteo.com` | global | CC BY 4.0 (Open-Meteo) |
| `DwdWeatherAdapter` | `dwd` | nein | DWD Open Data / Brightsky | DACH | DWD GeoNutzV |
| `OpenWeatherMapWeatherAdapter` | `openweathermap` | **ja** (Fernet-Ref) | `api.openweathermap.org` | global | OWM-Nutzungsbedingungen |

DWD wird pragmatisch über die freie Brightsky-JSON-Fassade (`api.brightsky.dev`) der DWD-Open-Data-Rohdaten angebunden (WMO-Codes vorhanden), um das MOSMIX-KMZ-Parsing zu vermeiden; die Attribution bleibt DWD. OpenWeatherMap liest den Key über `api_key_ref` → Secret-Store (§5); kein Klartext-Key im Config-Dokument.

### 3.4 `HomeAssistantWeatherAdapter` (der Kern-Mehrwert)

Nutzt den bestehenden `HomeAssistantClient` (`data_access/external/ha_client.py`) und unterstützt **beide** bestätigten Modi.

```python
# app/data_access/external/home_assistant_weather_adapter.py  (NEU)
from datetime import date, datetime

from app.data_access.external.ha_client import HomeAssistantClient
from app.domain.interfaces.weather_adapter import WeatherAdapter
from app.domain.models.weather import WeatherForecast
from app.domain.services.weather_adapter_registry import WeatherAdapterRegistry


@WeatherAdapterRegistry.register
class HomeAssistantWeatherAdapter(WeatherAdapter):
    """Wetterquelle aus einer Home-Assistant-Installation.

    Modus A (weather_entity): liest eine HA weather.*-Entität; deren
        attributes.forecast[] + aktuelle attributes liefern die Tageswerte.
    Modus B (sensor_mapping): liest einzeln gemappte sensor.*-Entitäten
        (Außentemp/Feuchte/Regen/Wind/Druck) als Ist-Werte (current conditions).

    Setzt ein gültiges HA-Token voraus (REQ-005). Fehlt HA/Token → dieser
    Adapter meldet 'nicht verfügbar', der Resolver fällt auf die nächste
    priorisierte Quelle zurück (Degradation, nie harter Fehler).
    """

    source_name = "ha-weather"
    kind = "home_assistant"
    requires_api_key = False  # nutzt das bestehende HA-Token, kein eigenes Secret

    def __init__(self, ha_client: HomeAssistantClient) -> None:
        self._ha = ha_client

    async def fetch_daily(self, *, latitude, longitude, config=None) -> list[WeatherForecast]:
        ha_cfg = config  # WeatherSourceHaConfig
        if ha_cfg.mode == "weather_entity":
            return self._from_weather_entity(ha_cfg.weather_entity_id)
        return self._from_sensor_mapping(ha_cfg.sensor_mapping)

    def _from_weather_entity(self, entity_id: str) -> list[WeatherForecast]:
        state = self._ha.get_state(entity_id)  # {'state','attributes'}
        attrs = state["attributes"]
        # attrs['forecast'] -> [{'datetime','temperature','templow','precipitation',
        #                        'wind_speed','humidity','condition'}, ...]
        out: list[WeatherForecast] = []
        for fc in attrs.get("forecast", []):
            out.append(WeatherForecast(
                forecast_date=datetime.fromisoformat(fc["datetime"]).date(),
                temp_max_c=fc.get("temperature"),
                temp_min_c=fc.get("templow"),
                precipitation_mm=fc.get("precipitation"),
                wind_speed_kmh=fc.get("wind_speed"),
                humidity_percent=fc.get("humidity"),
                weather_code=self._condition_to_wmo(fc.get("condition")),
                data_kind="forecast", is_current_conditions=False,
                source=self.source_name, fetched_at=datetime.utcnow(),
            ))
        return out

    def _from_sensor_mapping(self, m) -> list[WeatherForecast]:
        # Ein Ist-Datensatz für heute aus den gemappten Sensor-Entitäten.
        def read(entity_id: str | None) -> float | None:
            if not entity_id:
                return None
            s = self._ha.get_state(entity_id).get("state")
            try:
                return float(s)
            except (TypeError, ValueError):
                return None  # 'unavailable'/'unknown' -> None

        return [WeatherForecast(
            forecast_date=date.today(),
            temp_min_c=read(m.temp_min_entity),
            temp_max_c=read(m.temp_max_entity) or read(m.temp_current_entity),
            precipitation_mm=read(m.precipitation_entity),
            wind_speed_kmh=read(m.wind_speed_entity),
            wind_gust_kmh=read(m.wind_gust_entity),
            humidity_percent=read(m.humidity_entity),
            weather_code=None,
            data_kind="observed", is_current_conditions=True,
            source=self.source_name, fetched_at=datetime.utcnow(),
        )]
```

> **Sicherheit (SSRF):** Der HA-Client validiert die HA-Basis-URL bereits via `validate_ha_url` (SEC-B3). Der Wetter-Adapter fügt **keine** neue ausgehende Ziel-URL hinzu — er spricht ausschließlich die konfigurierte, validierte HA-Instanz an. Öffentliche Wetter-Adapter nutzen feste, fest verdrahtete Provider-Basis-URLs (nicht nutzergesteuert), daher keine SSRF-Fläche.

### 3.5 Quellen-Auflösung (`WeatherSourceResolver`)

Der Service, der die konfigurierte Priorität durchläuft — die eigentliche „öffentlich vs. HA"-Fallback-Kette pro Standort.

```python
# app/domain/services/weather_source_resolver.py  (NEU)
class WeatherSourceResolver:
    """Läuft Site.WeatherSourceConfig.sources (priorisiert) durch und liefert
    die erste Quelle, die Daten liefert. Fällt bei Nichtverfügbarkeit
    (HA aus, API 5xx/Timeout, leere Antwort) auf die nächste Quelle zurück.
    """

    async def resolve_daily(self, site, cfg) -> list[WeatherForecast]:
        for entry in [e for e in cfg.sources if e.enabled]:
            adapter = self._build(entry)          # Registry.get(entry.source_name)
            if adapter is None:
                continue
            try:
                fcs = await adapter.fetch_daily(
                    latitude=site.gps_coordinates[0],
                    longitude=site.gps_coordinates[1],
                    config=entry.config,
                )
                if fcs:
                    return fcs                     # erste erfolgreiche Quelle gewinnt
            except (HomeAssistantUnavailable, httpx.HTTPError, httpx.TimeoutException):
                continue                           # → nächste priorisierte Quelle
        return []                                  # keine Quelle lieferte Daten
```

### 3.6 Celery-Task-Einreihung

- **`fetch_weather_forecasts`** (bestehend, REQ-005): wird so erweitert, dass je Outdoor-/Greenhouse-Site mit GPS **die konfigurierte `:WeatherSourceConfig`** über den `WeatherSourceResolver` durchlaufen wird (statt einer fest verdrahteten Quelle). Ergebnis-Records werden geschrieben; `source`/`data_kind` tragen die tatsächlich gezogene Quelle. HA-Sensor-Ist-Werte (`is_current_conditions=True`) triggern **keine** Vorhersage-Frühwarnungen (REQ-005), können aber die Gieß-Logik (REQ-022/037) mit Ist-Regenmenge speisen.
- **`weather_source_health_probe`** (NEU, optional, stündlich): prüft je aktiver HA-Quelle, ob die konfigurierten Entitäten noch existieren/verfügbar sind, und markiert eine Quelle in der UI als „gestört", ohne den Fetch-Lauf zu blockieren.

## 4. Frontend-Integration

Neuer Abschnitt **„Wetterquelle"** im Standort-Detail (`SiteDetailPage.tsx`, REQ-002), sichtbar für Sites mit `type ∈ {outdoor, greenhouse}` und gesetzten GPS-Koordinaten. Mobile-First (Feedback), mit erklärenden Texten und Fachbegriff-Erläuterungen.

### 4.1 Datenquellen-Konfigurator

- **Quellen-Prioritätsliste** (Drag-&-Drop-Reihenfolge, Index 0 = höchste Priorität). Jede Zeile: Quellen-Name + `kind`-Badge (`Öffentlicher Dienst` / `Home Assistant`), Enable-Toggle, Entfernen, Zahnrad für quellenspezifische Konfiguration.
- **„Quelle hinzufügen"**-Dialog mit klarer **Zwei-Wege-Umschaltung** (der Kern-UX des Requirements):
  - **Öffentlicher Wetterdienst** → Provider-Auswahl (Open-Meteo *[empfohlen, keine Anmeldung]*, DWD *[DACH]*, OpenWeatherMap *[global, API-Key nötig]*, NASA POWER *[global, Reanalyse — REQ-041]*). Bei OpenWeatherMap: API-Key-Eingabefeld (maskiert; wird als Secret gespeichert, §5).
  - **Home Assistant** → Modus-Umschaltung:
    - **Eine Wetter-Entität** (`mode='weather_entity'`): Auswahl-Dropdown aller `weather.*`-Entitäten der verbundenen HA-Instanz (geladen über den bestehenden HA-Entity-Picker, vgl. `SensorCreateDialog.tsx`).
    - **Einzelne Sensoren zuordnen** (`mode='sensor_mapping'`): pro Wetterfeld (Temp min/max/aktuell, Feuchte, Regen, Wind, Böen, Druck) je ein optionaler HA-`sensor.*`-Picker. Nicht zugeordnete Felder bleiben leer.
  - HA-Optionen sind **deaktiviert mit Hinweis**, wenn kein HA-Token gesetzt ist (`useHaIntegration()`-Hook / `user.ha_token_set`, REQ-005) — mit Deep-Link zur HA-Kontoeinstellung.
- **„Quelle testen"-Button** je Eintrag → ruft `POST /.../weather-sources/{id}/test` (health_check, §4.3) und zeigt Erreichbarkeit + eine Vorschau der zurückgelieferten Werte, **bevor** gespeichert wird.

### 4.2 Anzeige der Herkunft

- Im **Wetter-Widget** (REQ-009 Dashboard) und in der Tageswert-Liste je Eintrag ein Quellen-Badge (`source`), plus ein `Ist-Wert`- bzw. `Reanalyse`-Label aus `data_kind`/`is_current_conditions`, damit gemessene HA-Ist-Werte sichtbar von Vorhersagen getrennt sind.
- Ist die höchstpriorisierte Quelle gerade „gestört" (Health-Probe) und läuft ein Fallback, zeigt das Widget einen dezenten Hinweis *„Fallback aktiv: <Quelle>"*.

### 4.3 API-Endpunkte (tenant-scoped, REQ-024)

| Methode & Pfad | Zweck |
|----------------|-------|
| `GET /api/v1/t/{tenant_slug}/sites/{site_key}/weather-source` | Aktuelle `:WeatherSourceConfig` lesen |
| `PUT /api/v1/t/{tenant_slug}/sites/{site_key}/weather-source` | Config speichern (Prioritätsliste + Quellen-Configs) |
| `GET /api/v1/t/{tenant_slug}/weather-sources/available` | Verfügbare Quellen (aus Registry + HA-Token-Status) für die UI |
| `POST /api/v1/t/{tenant_slug}/sites/{site_key}/weather-sources/test` | Verbindungstest einer (auch ungespeicherten) Quellenkonfiguration |
| `GET /api/v1/t/{tenant_slug}/ha/weather-entities` | Liste der HA-`weather.*`-Entitäten (für Modus A) |
| `GET /api/v1/t/{tenant_slug}/ha/sensor-entities` | Liste der HA-`sensor.*`-Entitäten (für Modus B; nutzt `list_sensor_entities`) |

### 4.4 i18n

Alle Strings in DE (Default/Fallback) und EN. Namespaces: `pages.siteDetail.weatherSource.*`, `enums.weatherSource.*` (Quellen-Namen), `enums.weatherSourceKind.*` (`public`/`home_assistant`), `enums.haWeatherMode.*` (`weather_entity`/`sensor_mapping`). Custom Hooks mit Objekt-/Array-Return via `useMemo` stabilisieren (Projektkonvention).

## 5. Konfiguration, Deployment & Lizenz

**Environment:**
- `WEATHER_DEFAULT_PUBLIC_SOURCE` (Default `open-meteo`) — Default-Quelle, die neuen Outdoor-Sites automatisch zugeordnet wird (kein Key nötig, sofort nutzbar).
- `OPENWEATHERMAP_ENABLED: bool` (Default `true`), `DWD_ENABLED`, `OPEN_METEO_ENABLED` — pro-Provider-Kill-Switch (ausgegraut in der UI, wenn aus).
- `OPEN_METEO_BASE_URL`, `DWD_BASE_URL`, `OPENWEATHERMAP_BASE_URL` — überschreibbar für Tests/Proxy.
- `WEATHER_FETCH_TIMEOUT_S` (Default `20`), `WEATHER_MAX_RPS_PER_PROVIDER` (Default `1.0`).
- HA-seitig werden die bestehenden HA-Verbindungs-Env/-Secrets (REQ-005/REQ-018) wiederverwendet; **keine** neuen HA-Secrets.

**API-Key-Secret-Storage (OpenWeatherMap):**
- Der Klartext-Key wird **nie** in `:WeatherSourceConfig` abgelegt. Er wird über den bestehenden Fernet-Secret-Mechanismus (REQ-023, `FERNET_KEY`) verschlüsselt persistiert; das Config-Dokument hält nur `api_key_ref`. Lese-/Entschlüssel-Zugriff nur im Backend zur Fetch-Zeit; die API gibt Keys nie im Klartext zurück (maskiert).

**Deployment:**
- Backend: neue Collection `weather_source_configs` + Edge `has_weather_source_config` im `kamerplanter_graph` (idempotente Migration, NFR-016). Additive `:WeatherForecast`-Felder (`data_kind`, `is_current_conditions`) mit Defaults → kein Break auf Alt-Daten.
- Graceful Degradation: Ist eine öffentliche API nicht erreichbar oder HA aus, fällt der `WeatherSourceResolver` auf die nächste Quelle zurück; liefert keine Quelle Daten, bleiben zuletzt gespeicherte `:WeatherForecast`-Records nutzbar. Kein Hard-Dependency auf externe Verfügbarkeit zur Laufzeit.

**Lizenz / Attribution (NOTICE-pflichtig):**
- **DWD Open Data:** GeoNutzV — Namensnennung „Datenbasis: Deutscher Wetterdienst".
- **Open-Meteo:** CC BY 4.0 — „Weather data by Open-Meteo.com".
- **OpenWeatherMap:** Nutzung gemäß OWM-Bedingungen des jeweiligen Plans.
- **NASA POWER:** siehe REQ-041 (Zitationsbitte).
- Attributionen werden im Wetter-Abschnitt der UI und in der Doku angezeigt und in die NOTICE-Datei aufgenommen.

**DSGVO (REQ-025):**
- Öffentliche Wetter-Adapter übermitteln nur **GPS-Koordinaten des Standorts** an den jeweiligen Dienst — keine personenbezogenen Daten; im Verarbeitungsverzeichnis als externe Wetter-Datenquellen zu führen (analog REQ-005/041). OpenWeatherMap/US-Dienste als Drittland-Übermittlung kennzeichnen.
- Die HA-Quelle spricht ausschließlich die **eigene** HA-Instanz des Nutzers an — keine Drittübermittlung.

## 6. Abhängigkeiten

- **REQ-005 (Hybrid-Sensorik/Wetter):** Liefert das `:WeatherForecast`-Basismodell, `weather_forecasts`, `has_forecast`, den `source`-Provenance-Enum, die Celery-Tasks und die Warn-Tabelle. REQ-046 erweitert (nicht ersetzt) diese um `data_kind`/`is_current_conditions`/`ha_weather` und die Konfigurationsschicht. **Harte Abhängigkeit.** *(Rück-Querverweis in REQ-005 §Wetter erforderlich.)*
- **REQ-002 (Standortverwaltung):** Liefert `Site.type`, `gps_coordinates`, `tenant_key`. `Site.weather_source_priority` wird durch `:WeatherSourceConfig` abgelöst (denormalisierte Sicht bleibt). **Harte Abhängigkeit.**
- **REQ-018 (Umgebungssteuerung/HA-Aktorik):** Teilt sich den `HomeAssistantClient` (REST). REQ-046 ist die Lese-Seite (Sensoren als Wetterquelle), REQ-018 die Schreib-Seite (Aktoren). **Geteilte Infrastruktur, keine funktionale Kopplung.**
- **REQ-023 (Auth/Secrets):** Fernet-Secret-Storage für den OpenWeatherMap-API-Key. **Harte Abhängigkeit.**
- **REQ-024 (Mandantenverwaltung):** `:WeatherSourceConfig` ist tenant-scoped (erbt `tenant_key` von der Site); tenant-scoped Routen `/t/{tenant_slug}/`. Cross-Tenant-Edges verboten. **Harte Abhängigkeit.**
- **REQ-041 (NASA POWER):** `NasaPowerWeatherAdapter` **registriert sich in der hier definierten** `WeatherAdapterRegistry`. REQ-041 bleibt SSOT für den POWER-Adapter, `:ClimateNormal` und `solar_radiation_mj_m2`. **Rück-Querverweis in REQ-041 erforderlich** (Registry-Ownership umgehängt nach REQ-046).
- **REQ-039 (Winterhärte):** `*ClimateNormalAdapter` registrieren analog. **Konsument geteilter Infrastruktur.**
- **REQ-037 (Evapotranspiration):** Konsument der beschafften Tageswerte (inkl. HA-Ist-Regenmenge, `solar_radiation_mj_m2` via REQ-041). **Konsumierende Abhängigkeit.**
- **REQ-022 (Pflegeerinnerungen):** Konsument (Regenvorhersage/Ist-Regen für adaptive Gieß-Erinnerungen). **Konsumierende Abhängigkeit.**
- **REQ-009 (Dashboard):** Wetter-Widget zeigt Quelle/`data_kind`-Badge und Fallback-Hinweis. **UI-Abhängigkeit.**

## 7. Akzeptanzkriterien

- [ ] **AC-1 (Registry als SSOT):** `WeatherAdapter`-ABC und `WeatherAdapterRegistry` existieren im Code unter `domain/interfaces/` bzw. `domain/services/`; `NasaPowerWeatherAdapter` (REQ-041) registriert sich nachweislich in **dieser** Registry (keine Zweit-Registry).
- [ ] **AC-2 (Öffentliche Adapter):** `OpenMeteoWeatherAdapter`, `DwdWeatherAdapter` und `OpenWeatherMapWeatherAdapter` sind implementiert, registriert und schreiben `:WeatherForecast` mit korrektem `source` und `data_kind="forecast"`.
- [ ] **AC-3 (HA-Modus A):** Bei `WeatherSourceHaConfig(mode='weather_entity')` liest der `HomeAssistantWeatherAdapter` die `forecast[]`-Attribute einer HA-`weather.*`-Entität und erzeugt daraus Tages-`:WeatherForecast`-Records mit `source="ha_weather"`, `data_kind="forecast"`.
- [ ] **AC-4 (HA-Modus B):** Bei `mode='sensor_mapping'` liest der Adapter die gemappten `sensor.*`-Entitäten und erzeugt genau einen Ist-Datensatz (`is_current_conditions=True`, `data_kind="observed"`); nicht gemappte Felder und `unavailable`/`unknown`-States werden zu `None`.
- [ ] **AC-5 (Nutzerwahl in UI):** Im Standort-Detail kann der Nutzer eine Quelle hinzufügen und dabei explizit zwischen „Öffentlicher Wetterdienst" und „Home Assistant" wählen; die HA-Option ist ohne gesetztes HA-Token deaktiviert und mit erklärendem Hinweis versehen.
- [ ] **AC-6 (Priorität & Fallback):** Bei mehreren aktiven Quellen zieht `fetch_weather_forecasts` sie in konfigurierter Reihenfolge; ist die erste nicht verfügbar (HA aus / API 5xx / Timeout / leere Antwort), wird nahtlos die nächste gezogen — ohne Abbruch des Laufs.
- [ ] **AC-7 (Verbindungstest):** Der „Quelle testen"-Endpunkt liefert für eine gültige Konfiguration Erreichbarkeit + Werte-Vorschau und für eine ungültige einen verständlichen Fehler — ohne die Konfiguration zu speichern.
- [ ] **AC-8 (Secret-Sicherheit):** Ein OpenWeatherMap-API-Key wird verschlüsselt (Fernet, REQ-023) gespeichert; `:WeatherSourceConfig` enthält nur `api_key_ref`; kein Endpunkt gibt den Key im Klartext zurück.
- [ ] **AC-9 (HA optional):** Alle Wetterfunktionen sind mit einer rein öffentlichen Quelle (Open-Meteo, ohne Key) vollständig nutzbar; das Entfernen/Fehlen von HA bricht keine Wetterfunktion.
- [ ] **AC-10 (Provenance & Warnungen):** HA-Ist-Werte (`is_current_conditions=True`) lösen **keine** Vorhersage-Frühwarnungen (REQ-005) aus; das Quellen-/`data_kind`-Badge unterscheidet in der UI sichtbar Vorhersage, Ist-Wert und Reanalyse.
- [ ] **AC-11 (Tenant-Isolation):** `:WeatherSourceConfig` erbt `tenant_key` von der Site; das Schreiben mit abweichendem `tenant_key` oder das Verknüpfen einer fremden Site wird abgewiesen (422/403); Routen sind tenant-scoped.
- [ ] **AC-12 (SSRF/Sicherheit):** Der HA-Adapter spricht nur die via `validate_ha_url` geprüfte HA-Instanz an; öffentliche Adapter nutzen fest verdrahtete Provider-URLs (keine nutzergesteuerte Ziel-URL).
- [ ] **AC-13 (Migration):** `weather_source_configs` + `has_weather_source_config` werden idempotent angelegt; additive `:WeatherForecast`-Felder brechen bestehende Records nicht (Defaults greifen).
- [ ] **AC-14 (i18n):** Alle neuen UI-Strings liegen in DE und EN vor; DE ist Default/Fallback.
- [ ] **AC-15 (Attribution):** DWD/Open-Meteo/OWM-Attributionen werden in der UI angezeigt und in der NOTICE-Datei geführt.
```
