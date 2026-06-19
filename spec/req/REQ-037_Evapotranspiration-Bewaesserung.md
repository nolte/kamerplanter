# Spezifikation: REQ-037 - Evapotranspiration & bedarfsgerechte Bewässerung

```yaml
ID: REQ-037
Titel: Evapotranspiration (ET₀/ETc) & bedarfsgerechte Bewässerungsberechnung
Kategorie: Bewässerung & Düngung
Fokus: Beides
Technologie: Python 3.14+, PyETo, FastAPI, ArangoDB, Celery, React, TypeScript, MUI
Status: Entwurf
Version: 1.1
Abhängigkeit: REQ-004 (Dünge-Logik), REQ-005 (Hybrid-Sensorik/Wetter), REQ-022 (Pflegeerinnerungen), REQ-002 (Standort), REQ-019 (Substrat)
```

## Versionshistorie

| Version | Datum | Änderung |
|---------|-------|----------|
| 1.0 | 2026-06-19 | Initialer Entwurf — Integration von PyETo (awesome-agriculture). Berechnung der Referenz-Evapotranspiration ET₀ → ETc → Netto-Gießbedarf für Freiland- und Gewächshaus-Standorte. |
| 1.1 | 2026-06-20 | Lizenz-Schärfung: aquacropeto (BSD-3) als Dependency, pyTSEB (GPL-3.0) als Dependency ausgeschlossen |

## 1. Business Case

### User Stories

- **Als Freiland-Gärtner** möchte ich, dass meine Gießerinnerungen den tatsächlichen Wasserbedarf meiner Beete aus Wetter- und Standortdaten berechnen, **damit** ich nicht stur alle 3 Tage gieße, obwohl es geregnet hat oder eine Hitzewelle den Bedarf verdoppelt.
- **Als Gewächshaus-Betreiber** möchte ich pro Kultur und Wachstumsphase einen realistischen Tageswasserbedarf (Liter pro m²) sehen, **damit** ich meine Bewässerung dimensionieren und Wasser sparen kann.
- **Als ambitionierter Hobbygärtner** möchte ich eine Wasserbilanz pro Standort sehen (Verdunstung minus Niederschlag), **damit** ich verstehe, warum das System eine Gießerinnerung verschiebt oder verschärft.
- **Als Experten-Nutzer** möchte ich den Kulturkoeffizienten (Kc) pro Art und Phase überschreiben können, **damit** die Berechnung zu meinen spezifischen Sorten und meinem Mikroklima passt.
- **Als Sparsamer** möchte ich, dass der berechnete Gießbedarf durch die Wasserhaltefähigkeit meines Substrats gedeckelt wird, **damit** mir nicht mehr Wasser empfohlen wird, als der Boden überhaupt speichern kann.

### Was ist PyETo und welche Lücke schließt es?

**PyETo** ist eine kleine, fokussierte Python-Bibliothek zur Berechnung der **Referenz-Evapotranspiration ET₀** (auch potenzielle Evapotranspiration / PET) aus meteorologischen Standarddaten. Sie implementiert drei etablierte agrarwissenschaftliche Verfahren:

- **FAO-56 Penman-Monteith** (Allen et al., 1998) — der internationale Referenzstandard; benötigt Temperatur, Luftfeuchte, Windgeschwindigkeit und Strahlung.
- **Hargreaves** (Hargreaves & Samani, 1982/1985) — robuster Fallback, der nur Min-/Max-Temperatur und extraterrestrische Strahlung (aus Breitengrad + Tag des Jahres) benötigt.
- **Thornthwaite** (1948) — rein temperaturbasiert, monatliche Auflösung (für unsere Zwecke nur als grober Notnagel relevant).

Die **Evapotranspiration** ist die Summe aus Bodenverdunstung und Pflanzentranspiration — also der reale Wasserverlust eines Bestands an die Atmosphäre. Aus ET₀ wird über den **Kulturkoeffizienten Kc** (crop coefficient, pro Art und Wachstumsphase) die **kulturspezifische Evapotranspiration ETc = ET₀ × Kc** berechnet. Der **Netto-Gießbedarf** ergibt sich aus `ETc − effektiver Niederschlag`, begrenzt durch die Wasserhaltefähigkeit des Substrats.

**Geschlossene Lücke:** REQ-004 (Dünge-/Bewässerungs-Logik) und REQ-022 (Pflegeerinnerungen) arbeiten heute mit **festen Gießintervallen** (z. B. `watering_interval_days`) plus saisonalen Multiplikatoren und einer einfachen Regen-Unterdrückung aus REQ-005. Es fehlt eine **physikalisch fundierte Bedarfsberechnung** für Freiland- und Gewächshaus-Kulturen. REQ-037 schließt diese Lücke: Es nutzt die in REQ-005 bereits beschafften `weather_forecasts` als **Input** und speist die berechnete Wasserbilanz **zurück** in die adaptiven Gießerinnerungen (REQ-022) und die Aufgabenplanung (REQ-006).

**Abgrenzung Indoor vs. Outdoor:** ET₀ ist primär **outdoor-relevant** (und für Gewächshäuser mit Wetterbezug bedingt nutzbar). Für reine **Indoor-Kulturen** ohne Wetterdaten ist die Penman-Monteith-/Hargreaves-Berechnung nicht sinnvoll — dort bleibt die Transpirations-/VPD-basierte Logik aus REQ-005 (`vpd`, Leaf-VPD) bzw. das feste Intervall aus REQ-022 maßgeblich. REQ-037 ist deshalb **nur für `Site.type ∈ {'outdoor', 'greenhouse'}`** aktiv.

### Projekt-Steckbrief

| Eigenschaft | Wert |
|-------------|------|
| Name | PyETo |
| Autor | Mark Richards (GitHub: `woodcrafty`) |
| Repo-URL | https://github.com/woodcrafty/PyETo |
| Doku | https://pyeto.readthedocs.io/ (Release 0.2, 2022-07-29) |
| Lizenz | BSD 3-Clause ("New"/"Revised") |
| Sprache | Python (deklariert: 2.7, 3.4–3.8, PyPy) |
| Typ | Bibliothek (reine Berechnung, keine externen Calls) |
| Methoden | FAO-56 Penman-Monteith, Hargreaves, Thornthwaite |
| Reifegrad / Wartungsstand | **Pre-alpha**, **nicht auf PyPI**, letzter dokumentierter Stand 2022 — klein und stabil, aber nicht aktiv gepflegt |
| Rolle in REQ-037 | **Nur Upstream-Vorlage** (BSD-3-Clause) — keine Dependency, da nicht pip-installierbar; siehe Fork `aquacropeto` |

**Empfohlene Dependency — installierbarer Fork (PyPI `aquacropeto`):**

| Eigenschaft | Wert |
|-------------|------|
| Name (Projekt) | aquacrop-eto (Fork von PyETo, AquaCrop-Projekt) |
| PyPI-Paketname | **`aquacropeto`** (ohne Bindestrich) → `pip install aquacropeto` |
| Repo-URL | https://github.com/aquacropos/aquacrop-eto |
| Lizenz | BSD 3-Clause (Copyright-Notice „Mark Richards" aus PyETo erhalten) |
| Letztes Release | 2022 — funktionsfähig, aber nicht aktiv weiterentwickelt |
| Status | API-kompatibler Fork von PyETo, identische Kernmethoden (`fao56_penman_monteith`, `hargreaves`) + Hilfsfunktionen zur Schätzung fehlender Wetterparameter |

> **Caveat / Entscheidung:** Das Original-PyETo ist **pre-alpha, nicht pip-installierbar und seit 2022 inaktiv** — für Python 3.14 und einen produktiven Stack ist es ungeeignet. REQ-037 verwendet daher den **API-kompatiblen Fork** als pip-Dependency. Der installierbare Fork heißt auf PyPI **`aquacropeto`** (ohne Bindestrich, `pip install aquacropeto`), Lizenz BSD-3-Clause, gleiche Funktionen `fao56_penman_monteith`, `hargreaves` plus Strahlungs-/Hilfsfunktionen. Im weiteren Dokument steht "PyETo" stellvertretend für diese kompatible Engine. **Vor Produktiveinsatz** ist wegen des letzten Releases (2022) die **Python-3.14-Kompatibilität zu prüfen**; falls inkompatibel, ist der Source **vendored** einzubinden, wobei die **Copyright-Notice „Mark Richards" zu erhalten** ist (BSD-3-Clause-Pflicht). Verifizierte Lizenzbewertung: `spec/analysis/awesome-agriculture-lizenz-und-nutzungsanalyse.md`.
>
> 🔴 **`pyTSEB` (Two-Source Energy Balance, thermisches Remote-Sensing) ist verifiziert GPL-3.0-or-later (starkes Copyleft) und damit als Dependency tabu:** Ein Import würde die MIT-lizenzierte, öffentlich verteilte Kamerplanter-Codebasis auf GPL zwingen (Outbound-Inkompatibilität). pyTSEB wird daher **nicht** als Dependency eingebunden. Falls die TSEB-Methodik je benötigt wird, gibt es nur zwei zulässige Wege: das Konzept eigenständig nachbauen **oder** pyTSEB strikt prozessgetrennt als eigenen Microservice betreiben (kein Code-Import). Siehe `spec/analysis/awesome-agriculture-lizenz-und-nutzungsanalyse.md`.

**Lizenz-Übersicht der ET-Optionen:**

| Paket | Lizenz | Bezugsquelle | Rolle in REQ-037 |
|-------|--------|--------------|------------------|
| **`aquacropeto`** | BSD-3-Clause | PyPI (`pip install aquacropeto`), Release 2022 | **Empfohlene Dependency** — Py-3.14-Kompatibilität vor Produktiveinsatz prüfen, sonst vendored (Copyright „Mark Richards" erhalten) |
| PyETo (Upstream) | BSD-3-Clause | nur GitHub `woodcrafty/PyETo`, pre-alpha, **kein PyPI** | Vorlage / Referenz — keine Dependency |
| `evapotranspiration` | MIT | PyPI, Beta (2020) | Höchstens **Fallback**, falls `aquacropeto` ausfällt |
| **`pyTSEB`** | **GPL-3.0-or-later** | — | 🔴 **MEIDEN als Dependency** (Copyleft, unvereinbar mit MIT-Outbound) — nur eigenständiger Nachbau ODER prozessgetrennter Microservice |

Quelle der Bewertung: `spec/analysis/awesome-agriculture-lizenz-und-nutzungsanalyse.md`.

## 2. Datenmodell-Erweiterung (ArangoDB)

### 2.1 Kulturkoeffizient (Kc) — Erweiterung `GrowthPhase` / `Species`

Der Kc-Wert hängt von Art **und** Wachstumsphase ab. Primär wird er pro `GrowthPhase` gepflegt (feingranular), mit einem Default aus einer art-/typbasierten Kc-Tabelle, falls kein expliziter Wert gesetzt ist.

```python
from pydantic import BaseModel, Field
from typing import Optional

class GrowthPhaseEtExtension(BaseModel):
    """Felder, die REQ-037 zur bestehenden GrowthPhase (REQ-003) ergänzt."""

    crop_coefficient_kc: Optional[float] = Field(
        default=None,
        ge=0.1,
        le=1.5,
        description=(
            "Kulturkoeffizient Kc dieser Phase (FAO-56). "
            "ETc = ET0 * Kc. None => Fallback auf KC_DEFAULTS pro plant_type. "
            "Typisch: Keimung/Initial 0.3-0.5, vegetativ/Entwicklung 0.7-1.0, "
            "Voll-/Bluetephase 1.0-1.2, Reife/Spaetphase 0.6-0.9."
        ),
    )
    kc_source: Optional[str] = Field(
        default=None,
        description="Herkunft des Kc-Werts: 'fao56_default', 'species_table', 'user_override'.",
    )
```

```python
class SpeciesEtExtension(BaseModel):
    """Optionaler Art-Default, falls keine Phase einen Kc setzt."""

    default_crop_coefficient_kc: Optional[float] = Field(
        default=None, ge=0.1, le=1.5,
        description="Art-weiter Kc-Default (mid-season). Niedrigere Prioritaet als GrowthPhase.crop_coefficient_kc.",
    )
```

**Kc-Default-Tabelle (`KC_DEFAULTS`)** — grobe FAO-56-orientierte Richtwerte pro Pflanzentyp, dienen nur als Fallback und sollten pro Art/Phase verfeinert werden:

| `plant_type` | Initial (Keimung) | Mid (Vegetativ/Blüte) | Late (Reife) |
|--------------|-------------------|-----------------------|--------------|
| `vegetable_leafy` (Salat, Kohl) | 0.7 | 1.05 | 0.95 |
| `vegetable_fruit` (Tomate, Gurke) | 0.6 | 1.15 | 0.80 |
| `vegetable_root` (Möhre, Rote Bete) | 0.5 | 1.05 | 0.95 |
| `herb` (Kräuter) | 0.5 | 0.95 | 0.90 |
| `cannabis` | 0.4 | 1.10 | 0.90 |
| `berry` / `shrub` | 0.5 | 1.05 | 0.85 |
| `tree` (Obst) | 0.45 | 0.95 | 0.70 |
| `lawn` / `green_manure` | 0.9 | 1.00 | 0.95 |

> **Caveat:** Kc-Werte sind klima-, sorten- und bestandsdichteabhängig. Die Tabelle ist ein bewusst grober Startpunkt; die zuverlässige Beschaffung präziser Kc-Werte pro Art bleibt eine fachliche Aufgabe (siehe §6/§7). Experten überschreiben pro Phase (`user_override`).

### 2.2 Ergebnis-Collection `irrigation_demands`

Das Berechnungsergebnis pro Standort (und optional pro PlantingRun) und Tag wird als eigenes Dokument persistiert — analog zu `weather_forecasts` (REQ-005), damit Frontend, Gießerinnerungen (REQ-022) und Tasks (REQ-006) es ohne Neuberechnung lesen können.

```python
from datetime import date, datetime
from typing import Literal, Optional

class IrrigationDemand(BaseModel):
    """Tages-Wasserbilanz pro Outdoor-/Gewaechshaus-Standort.

    Collection: irrigation_demands
    """

    demand_id: str
    site_key: str                              # Referenz auf Site (REQ-002)
    planting_run_key: Optional[str] = None     # optional je PlantingRun (REQ-013)
    target_date: date

    # Eingangsgroessen
    et0_mm: float = Field(ge=0, description="Referenz-Evapotranspiration ET0 in mm/Tag.")
    kc_used: float = Field(ge=0.1, le=1.5, description="Effektiv verwendeter Kulturkoeffizient.")
    etc_mm: float = Field(ge=0, description="ETc = ET0 * Kc in mm/Tag.")
    effective_precipitation_mm: float = Field(
        ge=0, description="Effektiver Niederschlag (aus weather_forecasts.precipitation_mm, abzgl. Abfluss/Interzeption)."
    )

    # Wasserbilanz
    net_demand_mm: float = Field(
        description="Netto-Gießbedarf = ETc - effektiver Niederschlag (kann negativ sein = Wasserüberschuss)."
    )
    net_demand_mm_capped: float = Field(
        ge=0, description="Auf Substrat-Wasserhaltefaehigkeit begrenzter, nicht-negativer Netto-Bedarf."
    )
    recommended_volume_liters: Optional[float] = Field(
        default=None, ge=0,
        description="net_demand_mm_capped * bewaesserte Flaeche (m2). 1 mm = 1 L/m2.",
    )

    # Methode & Qualitaet
    et_method: Literal["fao56_penman_monteith", "hargreaves", "thornthwaite"]
    method_reason: str = Field(description="Warum diese Methode (z.B. 'kein Wind/Strahlung -> Hargreaves-Fallback').")
    quality: Literal["high", "medium", "low"]  # high=PM mit allen Params, medium=Hargreaves, low=interpoliert

    weather_source: str                        # uebernommen aus weather_forecasts.source
    computed_at: datetime
```

**Edge** (named graph `kamerplanter_graph`):

```
Edge Collection        _from                _to                   Attribut
─────────────────────────────────────────────────────────────────────────
has_irrigation_demand  sites                irrigation_demands     // wie has_forecast (REQ-005)
demand_for_run         planting_runs        irrigation_demands     // optional, je Run
```

**AQL — jüngste Wasserbilanz je Site:**

```aql
FOR site IN sites
  FILTER site.type IN ['outdoor', 'greenhouse']
  LET latest = FIRST(
    FOR d IN 1..1 OUTBOUND site has_irrigation_demand
      FILTER d.target_date >= DATE_FORMAT(DATE_NOW(), "%yyyy-%mm-%dd")
      SORT d.target_date ASC
      LIMIT 1
      RETURN d
  )
  FILTER latest != null
  RETURN { site: site._key, net_demand_mm: latest.net_demand_mm_capped, method: latest.et_method }
```

## 3. Technische Umsetzung (Python)

### 3.1 Engine `EvapotranspirationCalculator`

Neuer Calculator in der Engine-/Calculator-Schicht (5-Layer: API → Service → **Engine/Calculator** → Repository → ArangoDB). Reine Berechnung, keine I/O, kein DB-Zugriff — deterministisch und damit gut unit-testbar.

```python
import math
from datetime import date
from typing import Literal, Optional

import aquacrop_eto as pyeto   # PyPI-Paket `aquacropeto`, Import-Name `aquacrop_eto`; API-kompatibler PyETo-Fork (siehe Steckbrief)

class EvapotranspirationCalculator:
    """Berechnet ET0 (PyETo), ETc und die Tages-Wasserbilanz.

    Methodenwahl:
      - FAO-56 Penman-Monteith, wenn Strahlung/Wind ableitbar sind (hoechste Genauigkeit).
      - Hargreaves als Fallback, wenn nur temp_min/temp_max vorliegen
        (Wetter-API liefert immer temp_min_c/temp_max_c -> Hargreaves ist immer moeglich).
    """

    def calculate_et0(
        self,
        *,
        latitude_deg: float,
        target_date: date,
        temp_min_c: float,
        temp_max_c: float,
        humidity_percent: Optional[float] = None,
        wind_speed_m_s: Optional[float] = None,
        solar_radiation_mj_m2: Optional[float] = None,
        altitude_m: float = 0.0,
    ) -> tuple[float, Literal["fao56_penman_monteith", "hargreaves"], str]:
        """Returns (et0_mm_per_day, method, reason)."""
        lat_rad = pyeto.deg2rad(latitude_deg)
        day_of_year = target_date.timetuple().tm_yday

        # Extraterrestrische Strahlung (nur aus Breitengrad + Tag des Jahres)
        sol_dec = pyeto.sol_dec(day_of_year)
        sha = pyeto.sunset_hour_angle(lat_rad, sol_dec)
        ird = pyeto.inv_rel_dist_earth_sun(day_of_year)
        et_rad = pyeto.et_rad(lat_rad, sol_dec, sha, ird)

        t_mean_c = (temp_min_c + temp_max_c) / 2.0

        # Bevorzugt: FAO-56 Penman-Monteith, wenn genuegend Parameter vorhanden
        if humidity_percent is not None and wind_speed_m_s is not None:
            # Strahlung: gemessen oder per Hargreaves-Formel aus dem Temperaturhub geschaetzt
            if solar_radiation_mj_m2 is not None:
                sol_rad = solar_radiation_mj_m2
            else:
                sol_rad = pyeto.sol_rad_from_t(et_rad, cs_rad=pyeto.cs_rad(altitude_m, et_rad),
                                               tmin=temp_min_c, tmax=temp_max_c, coastal=False)

            svp = pyeto.svp_from_t(t_mean_c)
            avp = pyeto.avp_from_rhmean(pyeto.svp_from_t(temp_min_c),
                                        pyeto.svp_from_t(temp_max_c), humidity_percent)
            net_rad = pyeto.net_rad(
                pyeto.net_in_sol_rad(sol_rad),
                pyeto.net_out_lw_rad(pyeto.celsius2kelvin(temp_min_c),
                                     pyeto.celsius2kelvin(temp_max_c),
                                     sol_rad, pyeto.cs_rad(altitude_m, et_rad), avp),
            )
            et0 = pyeto.fao56_penman_monteith(
                net_rad=net_rad, t=pyeto.celsius2kelvin(t_mean_c), ws=wind_speed_m_s,
                svp=svp, avp=avp, delta_svp=pyeto.delta_svp(t_mean_c),
                psy=pyeto.psy_const(pyeto.atm_pressure(altitude_m)),
            )
            return max(0.0, et0), "fao56_penman_monteith", "Strahlung & Wind verfuegbar"

        # Fallback: Hargreaves (nur Tmin/Tmax/Tmean + extraterrestrische Strahlung)
        et0 = pyeto.hargreaves(tmin=temp_min_c, tmax=temp_max_c, tmean=t_mean_c, et_rad=et_rad)
        return max(0.0, et0), "hargreaves", "Wind/Feuchte fehlen -> Hargreaves-Fallback"

    def calculate_water_balance(
        self,
        *,
        et0_mm: float,
        kc: float,
        precipitation_mm: float,
        water_holding_capacity_mm: Optional[float] = None,
        irrigated_area_m2: Optional[float] = None,
    ) -> dict:
        """ETc, Netto-Bedarf und (optional) empfohlenes Volumen."""
        etc_mm = et0_mm * kc

        # Effektiver Niederschlag: grobe FAO-Faustregel (Abfluss/Interzeption bei Starkregen).
        eff_precip = precipitation_mm * 0.8 if precipitation_mm > 5 else precipitation_mm

        net_mm = etc_mm - eff_precip
        net_capped = max(0.0, net_mm)

        # Deckelung durch Substrat-Wasserhaltefaehigkeit (REQ-019): mehr Wasser kann der Boden
        # ohnehin nicht halten (Rest versickert).
        if water_holding_capacity_mm is not None:
            net_capped = min(net_capped, water_holding_capacity_mm)

        volume_l = (net_capped * irrigated_area_m2) if irrigated_area_m2 else None  # 1 mm = 1 L/m2

        return {
            "etc_mm": round(etc_mm, 2),
            "effective_precipitation_mm": round(eff_precip, 2),
            "net_demand_mm": round(net_mm, 2),
            "net_demand_mm_capped": round(net_capped, 2),
            "recommended_volume_liters": round(volume_l, 1) if volume_l is not None else None,
        }
```

> **Hinweis zur API:** Die exakten Hilfsfunktionsnamen (`sol_dec`, `et_rad`, `fao56_penman_monteith`, `hargreaves`, `deg2rad` …) stammen aus der PyETo-/`aquacrop-eto`-API. Bei der Implementierung ist die Funktionssignatur gegen die installierte Version zu verifizieren; die Skizze zeigt den Datenfluss, nicht das letzte Argument-Detail.

### 3.2 Kc-Auflösung (Service-Schicht)

Prioritäts-Kaskade für den effektiven Kc je Run/Phase:

1. `GrowthPhase.crop_coefficient_kc` (Phase, `kc_source='user_override'` oder `'species_table'`)
2. `Species.default_crop_coefficient_kc`
3. `KC_DEFAULTS[plant_type][stage]` (Tabelle aus §2.1; `stage` aus aktueller Phase abgeleitet)
4. Konservativer Globaldefault `0.8`

### 3.3 Celery-Task `compute_irrigation_demand`

Läuft **nach** dem REQ-005-Task `fetch_weather_forecasts` (der täglich 06:00 die `weather_forecasts` aktualisiert). Reihenfolge wird über den Beat-Schedule bzw. eine Chain sichergestellt.

```python
@celery_app.task(name="irrigation.compute_irrigation_demand")
def compute_irrigation_demand() -> dict:
    """Taeglich nach Wetter-Update: ET0/ETc/Wasserbilanz je Outdoor-/GH-Site & aktivem Run."""
    calc = EvapotranspirationCalculator()
    written = 0

    for site in irrigation_repo.iter_outdoor_and_greenhouse_sites():  # type in {'outdoor','greenhouse'}
        if not site.gps_coordinates:
            continue  # ohne GPS keine ET0-Berechnung -> ueberspringen, Log-Hinweis
        lat, lon = site.gps_coordinates

        for forecast in weather_repo.get_upcoming_forecasts(site.key, horizon_days=3):
            et0, method, reason = calc.calculate_et0(
                latitude_deg=lat,
                target_date=forecast.forecast_date,
                temp_min_c=forecast.temp_min_c,
                temp_max_c=forecast.temp_max_c,
                humidity_percent=forecast.humidity_percent,
                wind_speed_m_s=(forecast.wind_speed_kmh / 3.6) if forecast.wind_speed_kmh else None,
            )
            for run in planting_run_repo.active_runs_for_site(site.key):
                kc = kc_service.resolve_kc(run)
                whc_mm = substrate_service.water_holding_capacity_mm(run)   # aus REQ-019
                balance = calc.calculate_water_balance(
                    et0_mm=et0, kc=kc,
                    precipitation_mm=forecast.precipitation_mm,
                    water_holding_capacity_mm=whc_mm,
                    irrigated_area_m2=run.irrigated_area_m2,
                )
                irrigation_repo.upsert_demand(IrrigationDemand(
                    demand_id=generate_key(), site_key=site.key, planting_run_key=run.key,
                    target_date=forecast.forecast_date, et0_mm=round(et0, 2), kc_used=kc,
                    etc_mm=balance["etc_mm"], effective_precipitation_mm=balance["effective_precipitation_mm"],
                    net_demand_mm=balance["net_demand_mm"], net_demand_mm_capped=balance["net_demand_mm_capped"],
                    recommended_volume_liters=balance["recommended_volume_liters"],
                    et_method=method, method_reason=reason,
                    quality="high" if method == "fao56_penman_monteith" else "medium",
                    weather_source=forecast.source, computed_at=utcnow(),
                ))
                written += 1

    # Feedback an REQ-022: Gieß-Erinnerungen anhand der heutigen Wasserbilanz schaerfen/lockern
    care_reminder_service.apply_irrigation_demand()
    return {"demands_written": written}
```

**Beat-Schedule (Ergänzung):** `compute-irrigation-demand-daily` um **06:15** (15 Min nach `fetch_weather_forecasts`).

### 3.4 Service-Einbindung in REQ-022 (`CareReminderEngine`)

Die `CareReminderEngine` (REQ-022) erhält einen optionalen Übersteuerungs-Pfad: Existiert für den Standort/Run eine aktuelle `IrrigationDemand`, ersetzt sie die rein intervallbasierte Fälligkeit:

- `net_demand_mm_capped == 0` (genug Regen) → Gieß-Erinnerung **unterdrücken** (Hinweis: "Wasserbilanz gedeckt — heute kein Gießen nötig").
- `net_demand_mm_capped` hoch + Trockenheit → Erinnerung **vorziehen / Volumen-Hinweis** (`recommended_volume_liters`).
- Indoor-Standorte ohne `IrrigationDemand` → unveränderte Intervall-Logik aus REQ-022 (`watering_interval_days`, `winter_watering_multiplier`).

Dies ergänzt die bestehende, einfachere Regen-Unterdrückung aus REQ-005 (`>5mm Regen → Erinnerung verschieben`) um eine quantitative Bilanz.

## 4. Frontend-Integration

- **Standort-Detailseite (REQ-002):** Neues Widget **"Wasserbilanz"** für `outdoor`/`greenhouse`-Sites — zeigt für die nächsten 1–3 Tage: ET₀, ETc, effektiven Niederschlag, Netto-Gießbedarf (mm und L) sowie die verwendete Methode und Qualität (Tooltip "Penman-Monteith (hoch)" / "Hargreaves (geschätzt)").
- **Pflege-Dashboard (REQ-022, `PflegeDashboardPage`):** Gieß-Karten zeigen bei vorhandener Bilanz statt "fällig in X Tagen" den **Bedarf in Litern** und einen Badge "regenbedingt verschoben".
- **Kc-Pflege (Expertenmodus, REQ-021):** In den GrowthPhase-/Species-Editierdialogen erscheint hinter `ExpertiseFieldWrapper` (Stufe `expert`) ein Feld **"Kulturkoeffizient (Kc)"** mit Hinweis auf den FAO-56-Default; leeres Feld = Tabellen-Fallback.
- **MUI:** Wasserbilanz als kompakte `Card` mit `LinearProgress`/Sparkline; Methoden-Qualität als `Chip` (high=grün, medium=gelb, low=grau).

**i18n-Keys (DE/EN, `react-i18next`):**

```
pages.irrigation.waterBalance.title          // "Wasserbilanz" / "Water balance"
pages.irrigation.waterBalance.et0            // "Verdunstung (ET₀)" / "Evapotranspiration (ET₀)"
pages.irrigation.waterBalance.etc            // "Pflanzenbedarf (ETc)" / "Crop demand (ETc)"
pages.irrigation.waterBalance.netDemand      // "Netto-Gießbedarf" / "Net irrigation demand"
pages.irrigation.waterBalance.recommendedLiters
pages.irrigation.method.fao56               // "Penman-Monteith (präzise)"
pages.irrigation.method.hargreaves          // "Hargreaves (geschätzt)"
pages.irrigation.cappedBySubstrate          // Hinweis Deckelung durch Wasserhaltefähigkeit
enums.etMethod.fao56_penman_monteith
enums.etMethod.hargreaves
fields.cropCoefficientKc                     // "Kulturkoeffizient (Kc)"
```

## 5. Konfiguration, Deployment & Lizenz

- **pip-Dependency:** PyPI-Paket **`aquacropeto`** (`pip install aquacropeto`; Import-Name `aquacrop_eto`), der API-kompatible PyETo-Fork. Eintrag in `pyproject.toml` des Backends; Renovate hält die Version aktuell. (Original-PyETo ist **nicht** pip-installierbar und wird **nicht** verwendet.)
  - **Python-3.14-Vorbehalt:** Letztes `aquacropeto`-Release stammt aus 2022. Vor Produktiveinsatz die Lauffähigkeit unter Python 3.14 verifizieren; falls inkompatibel, den BSD-3-Clause-Source **vendored** ins Backend übernehmen und dabei die **Copyright-Notice „Mark Richards" erhalten**.
- **Lizenz-Verträglichkeit:** `aquacropeto` ist BSD 3-Clause — permissiv, kompatibel mit der MIT-lizenzierten Kamerplanter-Codebasis; keine Copyleft-Verpflichtung. Fallback-Option `evapotranspiration` (PyPI, MIT, Beta 2020) ist ebenfalls permissiv. **`pyTSEB` ist verifiziert GPL-3.0-or-later (starkes Copyleft) und als Dependency tabu** — ein Import würde die öffentlich verteilte MIT-Codebasis auf GPL zwingen (Outbound-Inkompatibilität); zulässig nur als eigenständiger Nachbau oder prozessgetrennter Microservice. Verifizierte Bewertung: `spec/analysis/awesome-agriculture-lizenz-und-nutzungsanalyse.md`.
- **Offline-Fähigkeit:** PyETo/`aquacropeto` ist **reine Berechnung** ohne Netzwerk-Calls. Alle Eingaben kommen aus `weather_forecasts` (REQ-005) und `Site`/`Substrate` (REQ-002/019). Damit kein zusätzlicher externer Dienst, kein API-Key, keine Rate-Limits, voll cluster-intern.
- **Konfig-Defaults (Env):**
  - `IRRIGATION_DEMAND_HORIZON_DAYS=3`
  - `IRRIGATION_EFFECTIVE_PRECIP_RUNOFF_FACTOR=0.8` (Abfluss-Faktor bei >5 mm)
  - `IRRIGATION_KC_GLOBAL_DEFAULT=0.8`
  - `IRRIGATION_DEMAND_ENABLED=true`
- **DSGVO (REQ-025):** ET₀-Berechnung verarbeitet **keine Personendaten**. Einziger personenbezogener Aspekt: der **GPS-Standortbezug** der Site (Breitengrad als Eingabe). Dieser ist bereits in REQ-002 (`gps_coordinates`) erfasst und durch dessen Consent-/Retention-Regeln abgedeckt; REQ-037 führt keine neue Personendaten-Kategorie ein. `irrigation_demands` enthält nur abgeleitete physikalische Größen und referenziert die Site per Key.

## 6. Abhängigkeiten

| REQ | Beziehung | Impact |
|-----|-----------|--------|
| REQ-005 (Hybrid-Sensorik/Wetter) | **benötigt** — liest `weather_forecasts` (`temp_min_c`, `temp_max_c`, `precipitation_mm`, `humidity_percent`, `wind_speed_kmh`, `source`); Task läuft nach `fetch_weather_forecasts` | **HOCH** — ohne Wetterdaten keine ET₀-Berechnung |
| REQ-004 (Dünge-/Bewässerungs-Logik) | **erweitert** — ergänzt die Freiland-Bewässerung um physikalische Bedarfsberechnung; ergänzt `WaterMixCalculator`/area-based dosing um Volumen-Empfehlung | **HOCH** |
| REQ-022 (Pflegeerinnerungen) | **erweitert / speist** — `CareReminderEngine` nutzt `IrrigationDemand` zur Schärfung/Unterdrückung der Gieß-Erinnerung (statt nur `watering_interval_days`) | **HOCH** |
| REQ-002 (Standortverwaltung) | **benötigt** — `Site.type ∈ {outdoor, greenhouse}`, `gps_coordinates` (Breitengrad), `total_area_m2`/Slot-`area_m2`, `hemisphere` | **HOCH** |
| REQ-019 (Substratverwaltung) | **benötigt** — `water_holding_capacity_percent` zur Deckelung des Netto-Bedarfs | **MITTEL** |
| REQ-003 (Phasensteuerung) | **erweitert** — `GrowthPhase.crop_coefficient_kc` je Phase | **MITTEL** |
| REQ-013 (Pflanzdurchlauf) | **nutzt** — `IrrigationDemand` optional je aktivem `PlantingRun` (`irrigated_area_m2`) | **MITTEL** |
| REQ-006 (Aufgaben) | **speist** — hoher Netto-Bedarf kann Gieß-Task hoher Priorität auslösen | **NIEDRIG** |
| REQ-021 (UI-Erfahrungsstufen) | **nutzt** — Kc-Feld nur im Expertenmodus (`ExpertiseFieldWrapper`) | **NIEDRIG** |
| REQ-025 (DSGVO) | **berührt** — nur indirekter GPS-Standortbezug, bereits durch REQ-002 abgedeckt; keine neue Datenkategorie | **NIEDRIG** |

**Zukunfts-Option (nicht Teil v1.0):** Satellitengestützte ET-Schätzung (Two-Source Energy Balance aus thermischem Remote-Sensing) für großflächige Outdoor-Betriebe — separater REQ. 🔴 **`pyTSEB` darf dabei nicht als Dependency eingebunden werden:** Es ist verifiziert **GPL-3.0-or-later** und damit unvereinbar mit dem MIT-Outbound der öffentlich verteilten Kamerplanter-Codebasis. Falls die TSEB-Methodik benötigt wird, ist sie **eigenständig nachzubauen** ODER `pyTSEB` **strikt prozessgetrennt als eigener Microservice** (kein Code-Import) zu betreiben. Siehe `spec/analysis/awesome-agriculture-lizenz-und-nutzungsanalyse.md`.

## 7. Akzeptanzkriterien

**Szenario 1 — Penman-Monteith bei vollständigen Wetterdaten**
- **GIVEN** eine `outdoor`-Site mit `gps_coordinates` und ein `weather_forecast` mit Tmin/Tmax, Feuchte und Wind
- **WHEN** `compute_irrigation_demand` läuft
- **THEN** wird ein `IrrigationDemand` mit `et_method = 'fao56_penman_monteith'`, `quality = 'high'` und positivem `etc_mm` geschrieben.

**Szenario 2 — Hargreaves-Fallback bei fehlenden Parametern**
- **GIVEN** ein `weather_forecast` mit nur Tmin/Tmax (kein Wind, keine Feuchte)
- **WHEN** ET₀ berechnet wird
- **THEN** wird `et_method = 'hargreaves'`, `quality = 'medium'` gesetzt und `method_reason` erklärt den Fallback; es wird **keine** Exception geworfen.

**Szenario 3 — Regen deckt Bedarf**
- **GIVEN** `ETc = 3.5 mm` und `precipitation_mm = 12`
- **WHEN** die Wasserbilanz berechnet wird
- **THEN** ist `net_demand_mm < 0` und `net_demand_mm_capped == 0`; die REQ-022-Gieß-Erinnerung wird **unterdrückt**.

**Szenario 4 — Deckelung durch Substrat**
- **GIVEN** `net_demand_mm = 9` und `water_holding_capacity_mm = 6`
- **WHEN** die Bilanz berechnet wird
- **THEN** ist `net_demand_mm_capped == 6` (durch Wasserhaltefähigkeit begrenzt).

**Szenario 5 — Kc-Prioritäts-Kaskade**
- **GIVEN** eine `GrowthPhase` mit `crop_coefficient_kc = 1.1` und ein abweichender `KC_DEFAULTS`-Tabellenwert
- **WHEN** `resolve_kc` aufgerufen wird
- **THEN** wird `1.1` verwendet (`kc_used == 1.1`), nicht der Tabellen-Default.

**Szenario 6 — Indoor wird übersprungen**
- **GIVEN** eine `indoor`-Site
- **WHEN** `compute_irrigation_demand` läuft
- **THEN** wird **kein** `IrrigationDemand` erzeugt; die Gieß-Logik bleibt rein intervallbasiert (REQ-022).

**Szenario 7 — Volumen-Empfehlung**
- **GIVEN** `net_demand_mm_capped = 4` und `irrigated_area_m2 = 5`
- **WHEN** das Volumen berechnet wird
- **THEN** ist `recommended_volume_liters == 20.0` (1 mm = 1 L/m²).

### Definition of Done

- [ ] `aquacropeto` (PyPI; Import `aquacrop_eto`) als pip-Dependency in `pyproject.toml`, Lizenz BSD-3-Clause dokumentiert; Python-3.14-Kompatibilität geprüft (sonst vendored mit erhaltener „Mark Richards"-Copyright-Notice).
- [ ] `EvapotranspirationCalculator` mit `calculate_et0` (PM + Hargreaves-Fallback) und `calculate_water_balance` implementiert und unit-getestet (deterministisch, keine I/O).
- [ ] `IrrigationDemand`-Modell + Collection `irrigation_demands` + Edges `has_irrigation_demand`/`demand_for_run` im named graph.
- [ ] `GrowthPhase.crop_coefficient_kc` + `Species.default_crop_coefficient_kc` + `KC_DEFAULTS`-Tabelle + `resolve_kc`-Kaskade.
- [ ] Celery-Task `compute_irrigation_demand` im Beat-Schedule (06:15, nach Wetter-Update), läuft nur für `outdoor`/`greenhouse` mit GPS.
- [ ] `CareReminderEngine` (REQ-022) nutzt `IrrigationDemand` zur Unterdrückung/Schärfung der Gieß-Erinnerung.
- [ ] Frontend: Wasserbilanz-Widget (Standort + Pflege-Dashboard), Kc-Feld im Expertenmodus, DE/EN-i18n vollständig.
- [ ] Alle 7 Akzeptanz-Szenarien als Tests grün; ruff/ESLint/TypeScript clean.
- [ ] Doku-Hinweis (REQ-005/022 Cross-Refs) ergänzt; Caveats (Kc-Beschaffung, Fallback-Genauigkeit, Indoor-Ausschluss) dokumentiert.
