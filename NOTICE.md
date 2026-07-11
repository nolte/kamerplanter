# NOTICE — Third-Party Data Attributions

Kamerplanter integrates external data sources. This file records the
attributions required by those sources' licences and terms of use. The same
attributions are surfaced in the application UI (weather section) where the data
is displayed.

## Weather data sources (REQ-046, REQ-039, REQ-041)

Outdoor and greenhouse sites can draw daily weather data from one or more of the
following public services (user-selectable per site). When a provider's data is
used, its attribution is shown in the UI and applies here:

- **Deutscher Wetterdienst (DWD)** — Open Data under the
  *Geodatennutzungsverordnung (GeoNutzV)*. Attribution: „Datenbasis: Deutscher
  Wetterdienst". Accessed via the free Bright Sky JSON facade
  (`api.brightsky.dev`) of the DWD open-data raw records.
- **Open-Meteo** — data licensed under **CC BY 4.0**. Attribution: „Weather data
  by Open-Meteo.com".
- **OpenWeatherMap** — used in accordance with the OpenWeatherMap terms of use of
  the respective plan. Requires a user-supplied API key.
- **NASA POWER** (Prediction of Worldwide Energy Resources, REQ-041) — freely
  usable; the project displays a citation notice: „Klima-/Strahlungsdaten: NASA
  Prediction of Worldwide Energy Resources (POWER), power.larc.nasa.gov".

Home Assistant, when configured as a weather source, reads only the user's own
Home Assistant instance and introduces no third-party data attribution.

## Evapotranspiration library (REQ-037)

- **aquacrop-eto** (`aquacropeto` on PyPI) — used to compute FAO-56 Penman-Monteith
  and Hargreaves reference evapotranspiration (ET₀). Licensed under the
  **BSD-3-Clause** licence; copyright © 2015 Mark Richards (a maintained fork of
  PyETo). A permissive, MIT-compatible licence — no ShareAlike/copyleft
  obligations on the Kamerplanter codebase. The FAO-56 equations themselves
  (Allen et al., 1998, *Crop evapotranspiration — Guidelines for computing crop
  water requirements*, FAO Irrigation and Drainage Paper 56) are the published
  scientific reference.
