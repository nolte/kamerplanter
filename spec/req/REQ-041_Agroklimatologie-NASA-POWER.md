# Spezifikation: REQ-041 - Agroklimatologie-Wetterquelle (NASA POWER)

```yaml
ID: REQ-041
Titel: Agroklimatologie-Wetter- & Klimadatenquelle (NASA POWER)
Kategorie: Monitoring
Fokus: Backend
Technologie: Python 3.14+, FastAPI, ArangoDB, Celery, REST-API (NASA POWER)
Status: Entwurf
Version: 1.0
Abhängigkeit: REQ-005 (Hybrid-Sensorik/Wetter), REQ-002 (Standort), REQ-037 (Evapotranspiration — Strahlungsinput), REQ-039 (Klimazonen — Klimanormale), REQ-047 (Saison-/Überwinterungs-Automatik — Klimanormale als Saison-Fallback)
```

## Versionshistorie

| Version | Datum | Änderung |
|---------|-------|----------|
| 1.0 | 2026-06-19 | Initialer Entwurf — Integration NASA POWER (inspiriert von `agroclimatology`, awesome-agriculture) |

## 1. Business Case

**User Story (global):** "Als Gärtner mit einem Freiland-Standort außerhalb des deutschsprachigen Raums möchte ich verlässliche tägliche Wetter- und Strahlungsdaten erhalten, damit die Bewässerungs- und Düngeempfehlungen auch dort funktionieren, wo der DWD keine Daten liefert."

**User Story (Strahlung):** "Als ambitionierter Outdoor-Gärtner möchte ich, dass das System die tatsächlich eingestrahlte Solarenergie kennt, damit die Verdunstungsberechnung (ET₀) realistisch wird und meine Gießintervalle nicht nur auf Niederschlag, sondern auch auf Sonneneinstrahlung basieren."

**User Story (Klima):** "Als Nutzer, der einen neuen Standort anlegt, möchte ich, dass das System die langjährigen klimatischen Normale (Temperatur, Niederschlag, Strahlung) meines Standorts kennt, damit Hardiness-Zone, Aussaatfenster und Überwinterungsempfehlungen automatisch abgeleitet werden — auch ohne dass ich diese Werte selbst kenne."

**Beschreibung:**

Die bestehende Wetter-Integration aus **REQ-005** (Abschnitt *Wetter-Integration (Freiland)*) liefert über das Adapter-Pattern bereits Vorhersagedaten von **DWD Open Data**, **OpenWeatherMap** und **Open-Meteo**. Diese Quellen sind exzellent für **kurzfristige Vorhersagen** (Frost, Regen, Sturm) — aber:

- **DWD** deckt nur die **DACH-Region** ab und ist für globale Standorte unbrauchbar.
- Keine der drei bestehenden Quellen liefert **gemessene Solarstrahlung** (Globalstrahlung) als belastbaren Tageswert — ein zentraler Eingang für die **Evapotranspirations-Berechnung (REQ-037, ET₀ nach Penman-Monteith / FAO-56)**.
- Keine Quelle liefert **langjährige Klimanormale** (Climatology), die als Eingang für die automatische **Klimazonen-/Hardiness-Ableitung (REQ-039)** dienen.

Diese Spezifikation ergänzt die REQ-005-Adapter-Registry um einen **vierten Wetter-Adapter** `NasaPowerWeatherAdapter`, der das **NASA POWER** (Prediction of Worldwide Energy Resources) Web-Resource anbindet. POWER ist:

- **global** (Rasterdaten ~0,5° × 0,625°, weltweite Abdeckung),
- **kostenlos und ohne API-Key** nutzbar,
- liefert **gemessene/satellitengestützte Solarstrahlung** sowie meteorologische Tagesparameter,
- bietet **Klimanormale** (langjährige Monatsmittel) über einen separaten Endpunkt.

**Rolle in der Quellen-Hierarchie (Ergänzung, kein Ersatz):**

NASA POWER ist **kein Echtzeit-Nowcast-Ersatz** für DWD/Open-Meteo. POWER-Tagesdaten haben eine **Latenz von mehreren Tagen bis Wochen** (Near-Real-Time-Aufbereitung der Satelliten-/Reanalyse-Produkte) und eine grobe räumliche Auflösung. POWER positioniert sich daher zweifach:

1. **Strahlungs- und Backfill-Quelle für Freiland-Standorte ohne bessere Abdeckung** (insbesondere außerhalb der DWD-Region): liefert Solarstrahlung + Tageswerte für die rückblickende ET₀-Bilanzierung.
2. **Klimanormale-Quelle** für jeden GPS-Standort: einmalige bzw. seltene Abfrage langjähriger Mittel zur Standort-Charakterisierung.

Für aktuelle Frost-/Regen-/Sturmwarnungen (REQ-005 Benachrichtigungs-Tabelle) bleibt POWER **explizit nachrangig**: Wo DWD oder Open-Meteo verfügbar sind, gewinnen diese in der Quellen-Priorisierung.

### Projekt-Steckbrief

| Eigenschaft | `agroclimatology` (Vorbild) | NASA POWER API (eigentliche Datenquelle) |
|-------------|-----------------------------|-------------------------------------------|
| URL | <https://github.com/brycejohnston/agroclimatology> | <https://power.larc.nasa.gov/> (API: <https://power.larc.nasa.gov/docs/services/api/>) |
| Typ | Ruby-Client-Gem für die NASA-POWER-Web-Resource | Öffentliche REST-API (NASA Langley Research Center) |
| Sprache | **Ruby** (95,8 %) | sprachneutral (REST/JSON) |
| Lizenz | MIT (Code) | Daten: **frei nutzbar, keine Restriktionen** (de facto CC BY 4.0 / Public Domain US-Recht); **Zitationsbitte** der NASA POWER Project |
| API-Key | — (nutzt die offene POWER-API) | **kein API-Key erforderlich** |
| Abdeckung | global (über POWER) | **global** (Rasterprodukt, weltweit) |
| Reifegrad | gering — letzte Veröffentlichung **06/2016**, 4 Releases, nicht aktiv gepflegt; nur Solarstrahlung im Funktionsumfang | **produktiv & aktiv gepflegt** (NASA-Service), Datenreihe ab 1981-01-01 |
| Parameter-Fokus | 3 Strahlungsparameter (TOA-Insolation, horizontale Globalstrahlung, langwellige Abstrahlung) | Solarstrahlung + T2M, Niederschlag, Wind, Feuchte, Luftdruck u.v.m. (bis 20 Parameter/Abfrage) |

**Caveat zur Wiederverwendung:** Der `agroclimatology`-Client ist in **Ruby** geschrieben, seit 2016 nicht mehr gepflegt und nur auf Solarstrahlung beschränkt. Er ist daher **nicht direkt einsetzbar** — Kamerplanter ist ein Python-Stack. Übernommen wird ausschließlich das **Konzept** (Agroklimatologie als Datenquelle) und das **Wissen um die POWER-Endpunkte/Parameter**. Der eigentliche Adapter wird als **eigener Python-Adapter** gegen das REQ-005-`WeatherAdapter`-ABC neu implementiert.

## 2. Datenmodell-Erweiterung (ArangoDB)

### 2.1 Einreihung in `WeatherForecast` (bestehend, REQ-005)

NASA-POWER-Tagesdaten werden in die **bestehende** Collection `weather_forecasts` (`:WeatherForecast`, REQ-005 §2) geschrieben. Es entsteht **keine** neue Collection für die Tagesdaten. Belegung der bestehenden Felder:

| `WeatherForecast`-Feld | Belegung durch NASA POWER |
|------------------------|---------------------------|
| `source` | `"nasa-power"` (neuer Quellen-String, reiht sich neben `"dwd"`, `"openweathermap"`, `"open-meteo"`) |
| `forecast_date` | Tagesdatum des POWER-Records (UTC, `YYYY-MM-DD`) |
| `temp_min_c` / `temp_max_c` | `T2M_MIN` / `T2M_MAX` |
| `precipitation_mm` | `PRECTOTCORR` |
| `wind_speed_kmh` | `WS2M` (m/s → km/h) |
| `wind_gust_kmh` | `null` (POWER liefert keine Böen — Feld bleibt `Optional`) |
| `humidity_percent` | `RH2M` |
| `weather_code` | `null` bzw. abgeleiteter neutraler Wert (POWER liefert keinen WMO-Code) |
| `fetched_at` | Abrufzeitpunkt (Server-UTC) |

> **Hinweis Begriffsschärfe:** Obwohl die Collection `WeatherForecast` heißt, liefert POWER **vergangenheitsbezogene Tageswerte** (keine echte Vorhersage). Der Quellen-String `"nasa-power"` und das neue Feld `data_kind` (s.u.) machen diese Provenance explizit. Konsumenten (REQ-022 Gieß-Logik, REQ-037 ET₀) MÜSSEN die Provenance respektieren und POWER-Records **nicht** als Zukunftsvorhersage für Warnungen interpretieren.

**Zusatzfelder auf `:WeatherForecast` (additiv, abwärtskompatibel — Default für Altdaten):**

- `solar_radiation_mj_m2: Optional[float]` — Globalstrahlung (`ALLSKY_SFC_SW_DWN`) in MJ/m²/Tag. Primärer Eingang für REQ-037 ET₀. Bei DWD/OWM/Open-Meteo i.d.R. `null`.
- `data_kind: Literal['forecast', 'observed', 'reanalysis'] = 'forecast'` — Provenance-Klassifizierung. NASA POWER → `'reanalysis'`; bestehende Quellen → `'forecast'`. Steuert die Eignung als Warn-Trigger (nur `'forecast'` triggert REQ-005-Frühwarnungen).

### 2.2 Neue Collection `:ClimateNormal` (Klimanormale)

Langjährige Monatsmittel werden in einer **neuen** Doc-Collection `climate_normals` abgelegt. Sie werden selten aktualisiert (POWER-Climatology ändert sich nur mit neuen Daten-Releases) und dienen REQ-039 (Klimazonen) sowie REQ-022/REQ-047 (Überwinterung/Aussaatfenster). **REQ-047** nutzt `monthly_temp_min_c` und `coldest_month_min_c` als **Stufe-2-Signal** (klimatologischer Saison-Fallback) der SeasonState-Engine, wenn ein Standort keine Live-Wetterdaten hat.

- **`:ClimateNormal`** — Langjähriges klimatisches Mittel pro Standort
  - Collection: `climate_normals`
  - Properties:
    - `climate_normal_id: str`
    - `site_key: str` (Referenz auf Site, REQ-002)
    - `source: str` (`"nasa-power"`)
    - `period_start_year: int` (z.B. 1991)
    - `period_end_year: int` (z.B. 2020)
    - `monthly_temp_avg_c: list[float]` (12 Werte, Jan–Dez; `T2M`)
    - `monthly_temp_min_c: list[float]` (12 Werte; `T2M_MIN`)
    - `monthly_precip_mm: list[float]` (12 Werte; `PRECTOTCORR`, Monatssumme)
    - `monthly_solar_mj_m2: list[float]` (12 Werte; `ALLSKY_SFC_SW_DWN`, Tagesmittel je Monat)
    - `annual_temp_avg_c: float`
    - `annual_precip_mm: float`
    - `coldest_month_min_c: float` (Eingang für Hardiness-Zonen-Ableitung, REQ-039; Saison-Fallback-Signal für REQ-047 SeasonState — markiert den kältesten Monat für die `winter_dormancy→pre_spring`-Bedingung)
    - `fetched_at: datetime`

### 2.3 Edges

```
Edge Collection          _from              _to                     Attribut
─────────────────────────────────────────────────────────────────────────────
has_forecast             sites              weather_forecasts        // bestehend (REQ-005, G-010) — auch für source="nasa-power"
has_climate_normal       sites              climate_normals          // NEU — Standort ↔ Klimanormale
```

## 3. Technische Umsetzung (Python)

### 3.1 `NasaPowerWeatherAdapter` gegen das `WeatherAdapter`-ABC

> **Registry-Ownership (REQ-046):** Das `WeatherAdapter`-ABC und die `WeatherAdapterRegistry` sind seit REQ-046 dort beheimatet (SSOT der Wetter-Datenquellen-Schicht) — nicht mehr in REQ-005. REQ-041 **definiert keine eigene Registry**, sondern registriert `NasaPowerWeatherAdapter` in der REQ-046-Registry. REQ-041 bleibt SSOT für den POWER-Adapter selbst, `:ClimateNormal` und `solar_radiation_mj_m2`.

Der Adapter implementiert das in **REQ-046** beheimatete `WeatherAdapter`-ABC (Adapter-Pattern analog REQ-011) und registriert sich in derselben `WeatherAdapterRegistry`. Er ergänzt eine zweite Methode für den Klimanormale-Pfad.

```python
from abc import abstractmethod
from datetime import date, datetime, timedelta

import httpx

from app.domain.interfaces.weather_adapter import WeatherAdapter  # REQ-046-ABC
from app.domain.models.weather import WeatherForecast
from app.domain.models.climate import ClimateNormal


class NasaPowerWeatherAdapter(WeatherAdapter):
    """Wetter-/Klima-Adapter für die NASA POWER Web-Resource.

    Liefert satellitengestützte Tageswerte (Reanalyse) inkl. Globalstrahlung
    sowie langjährige Klimanormale. KEIN Echtzeit-Nowcast — ergänzt DWD/Open-Meteo,
    ersetzt sie nicht. POWER-Tagesdaten haben mehrere Tage Latenz.

    Inspiriert vom (Ruby-)Projekt `agroclimatology` (awesome-agriculture);
    eigenständige Python-Reimplementierung — der Ruby-Client ist nicht nutzbar.
    """

    source_name = "nasa-power"
    base_url = "https://power.larc.nasa.gov/api/temporal"

    # POWER → WeatherForecast-Parameter-Mapping (s. §3.2)
    DAILY_PARAMETERS = [
        "T2M_MIN", "T2M_MAX", "PRECTOTCORR",
        "WS2M", "RH2M", "ALLSKY_SFC_SW_DWN",
    ]
    # Latenz: POWER-Tagesdaten sind erst nach mehreren Tagen verfügbar.
    DATA_LATENCY_DAYS = 7

    def __init__(self, http_client: httpx.AsyncClient, timeout_s: float = 30.0) -> None:
        self._client = http_client
        self._timeout = timeout_s

    async def fetch_daily(
        self, latitude: float, longitude: float, days_back: int = 14
    ) -> list[WeatherForecast]:
        """Holt die letzten `days_back` Tageswerte (rückblickend, wegen Latenz).

        Anders als die echten Forecast-Adapter (DWD/Open-Meteo) liefert dieser
        Adapter Vergangenheitswerte: relevant für die ET₀-Rückbilanzierung
        (REQ-037) und als Backfill für Standorte ohne bessere Abdeckung.
        """
        end = date.today() - timedelta(days=self.DATA_LATENCY_DAYS)
        start = end - timedelta(days=days_back)
        params = {
            "parameters": ",".join(self.DAILY_PARAMETERS),
            "community": "AG",  # Agroclimatology-Community
            "latitude": latitude,
            "longitude": longitude,
            "start": start.strftime("%Y%m%d"),
            "end": end.strftime("%Y%m%d"),
            "format": "JSON",
        }
        resp = await self._client.get(
            f"{self.base_url}/daily/point", params=params, timeout=self._timeout
        )
        resp.raise_for_status()
        return self._map_daily(resp.json(), latitude, longitude)

    async def fetch_climate_normals(
        self, latitude: float, longitude: float
    ) -> ClimateNormal:
        """Holt langjährige Klimanormale (Climatology-Endpunkt)."""
        params = {
            "parameters": "T2M,T2M_MIN,PRECTOTCORR,ALLSKY_SFC_SW_DWN",
            "community": "AG",
            "latitude": latitude,
            "longitude": longitude,
            "format": "JSON",
        }
        resp = await self._client.get(
            f"{self.base_url}/climatology/point", params=params, timeout=self._timeout
        )
        resp.raise_for_status()
        return self._map_climatology(resp.json(), latitude, longitude)

    @staticmethod
    def _ws_ms_to_kmh(ws_ms: float) -> float:
        return round(ws_ms * 3.6, 1)

    def _map_daily(self, payload: dict, lat: float, lon: float) -> list[WeatherForecast]:
        """Mappt das POWER-JSON (parameter→{YYYYMMDD: value}) auf WeatherForecast.

        POWER markiert fehlende Werte mit -999; diese werden zu None.
        """
        params = payload["properties"]["parameter"]
        out: list[WeatherForecast] = []

        def clean(v: float | None) -> float | None:
            return None if v is None or v == -999 else v

        for day_key in params["T2M_MIN"]:
            fc_date = datetime.strptime(day_key, "%Y%m%d").date()
            ws = clean(params["WS2M"].get(day_key))
            out.append(
                WeatherForecast(
                    forecast_date=fc_date,
                    temp_min_c=clean(params["T2M_MIN"].get(day_key)),
                    temp_max_c=clean(params["T2M_MAX"].get(day_key)),
                    precipitation_mm=clean(params["PRECTOTCORR"].get(day_key)),
                    wind_speed_kmh=self._ws_ms_to_kmh(ws) if ws is not None else None,
                    wind_gust_kmh=None,
                    humidity_percent=clean(params["RH2M"].get(day_key)),
                    weather_code=None,
                    solar_radiation_mj_m2=clean(params["ALLSKY_SFC_SW_DWN"].get(day_key)),
                    data_kind="reanalysis",
                    source=self.source_name,
                    fetched_at=datetime.utcnow(),
                )
            )
        return out
```

### 3.2 Parameter-Mapping POWER → `WeatherForecast`

| NASA-POWER-Parameter | Bedeutung | POWER-Einheit | Ziel-Feld | Ziel-Einheit | Transformation |
|----------------------|-----------|---------------|-----------|--------------|----------------|
| `T2M_MIN` | Tagesminimum Lufttemperatur (2 m) | °C | `temp_min_c` | °C | identisch |
| `T2M_MAX` | Tagesmaximum Lufttemperatur (2 m) | °C | `temp_max_c` | °C | identisch |
| `PRECTOTCORR` | Korrigierter Tagesniederschlag | mm/Tag | `precipitation_mm` | mm | identisch |
| `WS2M` | Windgeschwindigkeit (2 m) | m/s | `wind_speed_kmh` | km/h | `× 3.6` |
| `RH2M` | Relative Luftfeuchte (2 m) | % | `humidity_percent` | % | identisch |
| `ALLSKY_SFC_SW_DWN` | Globalstrahlung an der Oberfläche (All-Sky) | MJ/m²/Tag | `solar_radiation_mj_m2` | MJ/m²/Tag | identisch (POWER liefert AG-Community in MJ/m²/Tag) |
| `T2M` (Klimatologie) | Mittl. Lufttemperatur | °C | `ClimateNormal.monthly_temp_avg_c[]` | °C | identisch |
| — (POWER liefert keine Böen) | — | — | `wind_gust_kmh` | — | `None` |
| — (POWER liefert keinen WMO-Code) | — | — | `weather_code` | — | `None` |

**Fehlwert-Konvention:** POWER kodiert fehlende Werte als `-999`. Der Adapter mappt `-999` → `None` (siehe `clean()` oben).

### 3.3 Klimanormale-Pfad

`fetch_climate_normals()` ruft den **Climatology-Endpunkt** (`/api/temporal/climatology/point`) auf. Das Ergebnis (12 Monatsmittel je Parameter) wird auf `:ClimateNormal` gemappt und über `has_climate_normal` mit der Site verknüpft. Ableitung für REQ-039:

- `coldest_month_min_c = min(monthly_temp_min_c)` → Eingang für USDA-/Hardiness-Zonen-Ableitung.
- `monthly_precip_mm` + `monthly_temp_avg_c` → Köppen-Geiger-naher Klimatyp (REQ-039).

### 3.4 Celery-Tasks

Reiht sich in die bestehenden REQ-005-Tasks ein, ohne sie zu ersetzen:

- **`fetch_weather_forecasts`** (bestehend, REQ-005): wird so erweitert, dass je Outdoor-Site die **konfigurierte Quellen-Priorität** (`Site.weather_source_priority`, s. §5) durchlaufen wird. NASA POWER wird als Quelle nur gezogen, wenn priorisiert oder wenn höher priorisierte Quellen keine Daten liefern (Fallback/Backfill). POWER-Records werden mit `data_kind="reanalysis"` geschrieben und triggern **keine** Frühwarnungen.
- **`fetch_climate_normals`** (NEU): seltener Beat — **monatlich** (z.B. 1. des Monats, 04:00) bzw. einmalig **on-demand bei Anlage einer Outdoor-Site mit GPS**. Holt/aktualisiert `:ClimateNormal` je Site. Idempotent: vorhandene Normale werden nur bei abgelaufener Caching-Frist (§5) neu abgerufen.
- **`check_frost_warnings`** / **`adjust_watering_reminders`** (bestehend, REQ-005): unverändert — sie filtern bereits implizit auf `data_kind="forecast"`, da POWER-Records nicht als Vorhersage gelten.

### 3.5 Caching & Rate-Limiting

- **Tagesdaten:** Da POWER vergangenheitsbezogen und latenzbehaftet ist, werden bereits geladene `(site_key, forecast_date, source="nasa-power")`-Records **nicht erneut** abgerufen (Upsert auf eindeutigem Schlüssel). Re-Fetch nur für den noch nicht abgedeckten Zeitraum.
- **Klimanormale:** TTL **180 Tage** (Default, konfigurierbar) — Normale ändern sich nur mit neuen POWER-Daten-Releases.
- **Rate-Limit/Fair-Use:** POWER bittet um schonende Nutzung. Der Service drosselt auf max. **1 Request/Sekunde** und bündelt bis zu 14 Tage je Site-Call. Bei HTTP 429/5xx: exponentielles Backoff, Skip der Site im laufenden Lauf (Retry beim nächsten Beat).

## 4. Frontend-Integration

- **Quellen-Auswahl im Standort-Detail (REQ-002):** Für Outdoor-/Greenhouse-Sites mit GPS erscheint im Wetter-Abschnitt eine Quellen-Prioritätsliste (Drag-Reihenfolge), in der `NASA POWER (global, inkl. Strahlung)` als Option auswählbar ist. Tooltip erklärt: *„Globale Abdeckung und Solarstrahlung, aber mehrere Tage Datenverzögerung — als Ergänzung, nicht für Echtzeit-Warnungen.“*
- **Quellen-Anzeige:** Im Wetter-Widget (REQ-009 Dashboard) und in der Tageswert-Liste wird je Eintrag die `source` (z.B. `nasa-power`) als kleines Badge gezeigt; POWER-Records erhalten zusätzlich ein `Reanalyse`-Label (aus `data_kind`), um sie sichtbar von Vorhersagen zu trennen.
- **Solarstrahlung:** Wo `solar_radiation_mj_m2` vorhanden ist, wird der Wert (MJ/m²/Tag) im Tagesdetail angezeigt und im ET₀-Kontext (REQ-037) referenziert.
- **Klimanormale im Standort-Detail:** Neuer Tab/Abschnitt *„Klima am Standort“* mit 12-Monats-Diagramm (Temperaturband min/avg, Niederschlagsbalken, Strahlungslinie) aus `:ClimateNormal`, inkl. abgeleiteter Hardiness-Zone (Verweis REQ-039). i18n DE/EN; Strings unter `pages.siteDetail.climate.*` bzw. `enums.weatherSource.*`.

## 5. Konfiguration, Deployment & Lizenz

**Konfiguration (Environment / Site-Ebene):**

- Kein API-Key nötig — **keine** Secret-Konfiguration erforderlich (Unterschied zu OpenWeatherMap).
- `NASA_POWER_BASE_URL` (Default `https://power.larc.nasa.gov/api/temporal`) — überschreibbar für Tests/Proxy.
- `NASA_POWER_ENABLED: bool` (Default `true`) — globaler Kill-Switch.
- `NASA_POWER_DAILY_DAYS_BACK: int` (Default `14`), `NASA_POWER_CLIMATE_TTL_DAYS: int` (Default `180`), `NASA_POWER_MAX_RPS: float` (Default `1.0`).
- **Site-Ebene:** Die geordnete Quellenliste je Standort (z.B. `["dwd", "open-meteo", "nasa-power"]` (DACH) bzw. `["nasa-power", "open-meteo"]` (global)) wird über REQ-046 (`:WeatherSourceConfig`, löst die ursprünglich skizzierte `Site.weather_source_priority: list[str]` ab) konfiguriert. Default leitet sich aus GPS ab (innerhalb DACH-Bounding-Box → DWD zuerst).

**Deployment:**

- Reine Backend-Erweiterung — neuer Adapter + ein neuer Celery-Beat + eine neue Collection (`climate_normals`) + Edge (`has_climate_normal`). Migration legt Collection/Edge im `kamerplanter_graph` an.
- **Offline/Caching:** Bei nicht erreichbarer POWER-API degradiert der Lauf graceful (Skip + Retry); vorhandene `:ClimateNormal`/`weather_forecasts`-Daten bleiben nutzbar. Kein Hard-Dependency auf POWER-Verfügbarkeit zur Laufzeit.

**Lizenz / Nutzungsbedingungen:**

- NASA-POWER-Daten sind **frei nutzbar, ohne Zugriffs-/Download-Restriktionen** (de facto CC BY 4.0; NASA-ESDIS-Inhalte sind nach US-Recht weitgehend gemeinfrei).
- Die NASA POWER Project **bittet um Zitation** bei Veröffentlichung. Kamerplanter zeigt im *„Klima am Standort“*-Abschnitt und in der Doku einen Attributions-Hinweis: *„Klima-/Strahlungsdaten: NASA Prediction of Worldwide Energy Resources (POWER), power.larc.nasa.gov“*.
- Der Code-Vorbild-Client `agroclimatology` steht unter **MIT** — es wird jedoch **kein Code** übernommen (Ruby, veraltet), nur das Konzept; daher keine Lizenz-Vererbung in den Kamerplanter-Code.
- **DSGVO (REQ-025):** POWER verarbeitet rein meteorologische Rasterdaten — keine personenbezogenen Daten. Übermittelt werden nur GPS-Koordinaten des Standorts an einen US-Dienst (NASA); dies ist im Verarbeitungsverzeichnis als externe Wetter-Datenquelle zu führen (analog OpenWeatherMap, REQ-005).

## 6. Abhängigkeiten

- **REQ-046 (Wetterdienst-Datenquellen):** SSOT für das `WeatherAdapter`-ABC und die `WeatherAdapterRegistry`, in die sich `NasaPowerWeatherAdapter` registriert, sowie für die Quellen-Priorisierung (`:WeatherSourceConfig`, löst `Site.weather_source_priority` ab) und die additiven `:WeatherForecast`-Felder (`data_kind`, `is_current_conditions`). **Harte Abhängigkeit** (Registry-Ownership von REQ-005 hierher umgehängt).
- **REQ-005 (Hybrid-Sensorik/Wetter):** Liefert das `:WeatherForecast`-Basismodell, die `has_forecast`-Edge, den `source`-Provenance-Enum und die Celery-Tasks (`fetch_weather_forecasts`, `check_frost_warnings`, `adjust_watering_reminders`), in die sich dieser Adapter einreiht. **Harte Abhängigkeit.**
- **REQ-002 (Standortverwaltung):** Liefert `Site.gps_coordinates`, `Site.type` (`outdoor`/`greenhouse`/`indoor`) und `hemisphere`. Die Quellen-Priorität je Standort wird über REQ-046 (`:WeatherSourceConfig`) konfiguriert. **Harte Abhängigkeit.**
- **REQ-037 (Evapotranspiration):** Konsument des neuen Feldes `solar_radiation_mj_m2` als Strahlungseingang der ET₀-Berechnung. **Konsumierende Abhängigkeit** (REQ-041 liefert den Eingang).
- **REQ-039 (Klimazonen):** Konsument von `:ClimateNormal` (insb. `coldest_month_min_c`, `monthly_*`) für die Hardiness-/Köppen-Zonen-Ableitung. **Konsumierende Abhängigkeit.**
- **REQ-022 (Pflegeerinnerungen):** Profitiert mittelbar (Aussaatfenster/Überwinterung über Klimanormale + hemisphere). Keine direkte Code-Kopplung.
- **REQ-024 (Mandantenverwaltung):** `:ClimateNormal` und `weather_forecasts` sind über `site_key` an tenant-gebundene Sites geknüpft — Tenant-Scoping erbt von der Site.

## 7. Akzeptanzkriterien

- [ ] **AC-1 (Registry):** `NasaPowerWeatherAdapter` implementiert das REQ-005-`WeatherAdapter`-ABC und ist in der `WeatherAdapterRegistry` unter `source_name="nasa-power"` registriert.
- [ ] **AC-2 (Tagesdaten):** Für eine Outdoor-Site mit GPS schreibt `fetch_weather_forecasts` POWER-Tageswerte als `:WeatherForecast`-Records mit `source="nasa-power"`, `data_kind="reanalysis"` und gefülltem `solar_radiation_mj_m2`.
- [ ] **AC-3 (Mapping):** Das Parameter-Mapping (§3.2) bildet `WS2M` korrekt von m/s nach km/h ab und konvertiert POWER-`-999`-Fehlwerte zu `None`.
- [ ] **AC-4 (Klimanormale):** `fetch_climate_normals` erzeugt je Site genau einen aktuellen `:ClimateNormal`-Record (12 Monatswerte je Parameter, `coldest_month_min_c` korrekt als Minimum von `monthly_temp_min_c`), verknüpft über `has_climate_normal`.
- [ ] **AC-5 (Caching):** Bereits geladene `(site_key, forecast_date, "nasa-power")`-Tageswerte werden nicht erneut abgerufen; `:ClimateNormal` wird erst nach Ablauf der TTL (`NASA_POWER_CLIMATE_TTL_DAYS`) neu geholt.
- [ ] **AC-6 (Quellen-Priorität):** Bei `Site.weather_source_priority = ["dwd", "open-meteo", "nasa-power"]` wird POWER nur als Fallback gezogen, wenn DWD und Open-Meteo keine Daten liefern.
- [ ] **AC-7 (Keine Falsch-Warnung):** POWER-Records (`data_kind="reanalysis"`) lösen **keine** Frost-/Regen-/Sturm-Frühwarnungen (REQ-005) aus.
- [ ] **AC-8 (Resilienz):** Bei HTTP 429/5xx oder Timeout der POWER-API bricht der Celery-Lauf nicht ab; betroffene Sites werden übersprungen und beim nächsten Beat erneut versucht; bestehende Daten bleiben verfügbar.
- [ ] **AC-9 (Kein API-Key):** Der Adapter funktioniert ohne jegliche Secret-/API-Key-Konfiguration.
- [ ] **AC-10 (Attribution):** Das Frontend zeigt im Standort-Klima-Abschnitt den NASA-POWER-Attributions-Hinweis; das Quellen-Badge unterscheidet sichtbar `nasa-power` (Reanalyse) von echten Vorhersage-Quellen.
- [ ] **AC-11 (i18n):** Alle neuen UI-Strings liegen in DE und EN vor; DE ist Default/Fallback.
- [ ] **AC-12 (Migration):** Collection `climate_normals` und Edge `has_climate_normal` werden idempotent im `kamerplanter_graph` angelegt; das additive Feld `solar_radiation_mj_m2`/`data_kind` bricht bestehende `:WeatherForecast`-Records nicht (Defaults greifen).
