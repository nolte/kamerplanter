# Sensors and Measurement Data

Kamerplanter is designed for four data sources for climate, substrate, and light data: automatic IoT/MQTT sensors, Home Assistant, a weather API for outdoor locations, and manual entry. Home Assistant (automatic polling) and manual entry at the tank are currently the only sources usable in production — the remaining sources are specified but not yet implemented (details below). <!-- REQ-005 v2.7 -->

---

## Prerequisites

- At least one location set up (site or location)
- For automatic data: sensors linked in Home Assistant and Kamerplanter connected to Home Assistant — see [Home Assistant Integration](../guides/home-assistant-integration.md)

---

## The Data Sources at a Glance

The specification defines a four-tier fallback chain. Currently, only **one automatic path (Home Assistant) and manual entry at the tank** are actually implemented — there is no automatic switching between tiers:

```
1. Automatic (IoT/MQTT) — planned
2. Home Assistant REST API — REAL, implemented
3. Weather API (outdoor only) — planned
4. Manual entry — REAL, currently tank only
```

**1. Automatic (IoT/MQTT) — planned**
The sensor data model already has an `mqtt_topic` field reserved for a future direct MQTT connection. This ingestion path is **not yet implemented** — the field currently has no effect and does not need to be filled in.

**2. Home Assistant (automatic)**
A background job polls the current value of every active sensor with a configured HA entity ID every 5 minutes and writes it to the time-series database (source `ha_auto`). This is the only automatic path currently implemented.

**3. Weather API (outdoor only) — planned**
For outdoor locations, Kamerplanter is planned to retrieve climate data from the German Weather Service (DWD), Open-Meteo, or OpenWeatherMap. See the [Outdoor Sensors](#outdoor-sensors-setting-up-a-weather-api) section below.

**4. Manual Entry — currently tank only**

!!! note "Manual measurements currently exist only for tanks"
    A manual entry form for climate values on a plant or location does not exist yet. Currently, you can manually record EC, pH, water temperature, fill level, TDS, dissolved oxygen, and ORP for a **tank** — see [Tank Management](tanks.md#recording-the-current-tank-state). For location sensors (site/location), you can only create a sensor with a Home Assistant connection; without Home Assistant their values stay empty.

!!! note "Every measurement has a source label"
    Every stored value carries a source field (`manual`, `ha_auto`, among others). This lets you see whether a value was entered automatically or by hand.

---

## Linking Sensors to a Location

### Step 1: Open Site or Location

Navigate to **Locations** and open the site or location the sensor belongs to.

### Step 2: Add Sensor

In the **Sensors** section, click **Add Sensor**.

### Step 3: Configure the Sensor

Fill in the form:

| Field | Description | Example |
|-------|-------------|---------|
| Sensor name | Sensor label | "Temp/RH Grow Tent A" |
| Metric type | What does the sensor measure? Choose from a predefined list (see [Metric Types](#metric-types-in-the-form)) | Temperature (°C) |
| Select HA sensor | Autocomplete of the entities available in Home Assistant (only shown when HA is configured and entities are found) | "Grow Tent A Temp (sensor.growtent_a_temperature) — 23.4 °C" |
| HA Entity ID | Free-text field, shown only when no HA entities are found — enter the entity name manually | `sensor.growtent_a_temperature` |
| MQTT topic | Reserved for the future direct MQTT connection (Future, currently has no effect) | `kamerplanter/growtent/temp` |
| Active | Only shown when editing. Deactivated sensors are no longer polled by the Home Assistant job | ✓ |

!!! info "No separate 'data source' field and no connection test"
    There is no separate "data source" selector and no "Test Connection" button. Whether a sensor is automatically fed depends solely on whether an HA entity ID is configured. The first actual value appears only with the next automatic poll (every 5 minutes) or — for tanks — via the live query on the tank detail page.

### HA Entity Autocomplete

If Home Assistant is configured, the dialog automatically loads the available Home Assistant entities when opened. Selecting an entity from the list makes Kamerplanter automatically fill in:

- the suggested sensor name,
- the matching unit of measurement,
- a suggested metric type (if Home Assistant provides a `device_class` from which the metric type can be derived),
- the entity ID itself.

If no Home Assistant entities are found (e.g. because no HA integration is set up or Home Assistant is currently unreachable), the dialog instead shows a free-text **HA Entity ID** field where you enter the entity name manually.

### Metric Types in the Form

The metric type is chosen from a fixed list:

| Metric type | Meaning |
|-------------|---------|
| `temperature_celsius` | Temperature (°C) |
| `humidity_percent` | Relative humidity (%) |
| `vpd_kpa` | VPD — Vapor Pressure Deficit (kPa) |
| `co2_ppm` | CO2 concentration (ppm) |
| `ppfd` | PPFD — Photosynthetic Photon Flux Density (µmol/m²/s) |
| `ph` | pH value |
| `ec_ms` | EC — electrical conductivity (mS/cm) |
| `water_temp_celsius` | Water temperature (°C) |
| `tds_ppm` | TDS — total dissolved solids (ppm) |
| `dissolved_oxygen_mgl` | Dissolved oxygen (mg/L) — relevant for hydroponics/aquaponics |
| `orp_mv` | ORP — Oxidation-Reduction Potential (mV) |
| `fill_level_percent` | Fill level (%) |

!!! note "Soil moisture not yet available as a metric type"
    There is currently no dedicated metric type for substrate/soil moisture. If you want to keep an eye on substrate moisture, the only option today is a manual note on the plant — dedicated tracking is not yet implemented.

The first four metric types (temperature, humidity, VPD, CO2) and PPFD are typical for climate sensors on a site/location. The rest (pH, EC, water temperature, TDS, dissolved oxygen, ORP, fill level) are mainly relevant for tanks — see [Tank Management](tanks.md). The form does not technically enforce this mapping; for example, you can also create an external EC sensor on a location.

---

## Understanding Monitored Parameters

### Climate Parameters

**Temperature (°C)**
Air temperature in the growing area. Optimal ranges depend on phase — typically 22–26 °C in the vegetative phase, 18–24 °C in flowering.

**Relative Humidity (rH, %)**
Too high humidity promotes mould (Botrytis, powdery mildew). Too low humidity increases water stress.

**VPD (kPa) — Vapor Pressure Deficit**
VPD is the most important climate parameter for optimal plant growth. It combines temperature and humidity into a single value describing how strongly the air draws moisture from leaves:

- **VPD too low** (< 0.4 kPa): Plant transpires too little, nutrient uptake reduced, mould risk
- **VPD optimal** (0.8–1.2 kPa): Best growth and nutrient uptake
- **VPD too high** (> 1.6 kPa): Plant closes stomata, nutrient deficiency despite adequate fertilization

Kamerplanter calculates VPD from temperature and humidity (Tetens formula) and compares it against the target for the active growth phase.

**CO2 concentration (ppm)**
Normal indoor air: approximately 400–500 ppm. Plants benefit from 800–1500 ppm (with sufficient light). Above 1500 ppm brings little additional benefit and may cause discomfort for people.

### Water and Nutrient Solution Parameters (Tank)

In practice, these values are recorded at the tank — automatically via Home Assistant or manually (see [Tank Management](tanks.md)):

**EC (mS/cm)**
Electrical conductivity of the nutrient solution shows salt concentration. Significantly higher runoff EC than input EC signals salt accumulation in the substrate and is a sign that a flush is needed.

**pH Value**
pH determines nutrient availability. Outside the optimal range (hydroponics: 5.5–6.5; soil: 6.0–7.0) plants cannot absorb nutrients even when enough is present.

**Water temperature, TDS, dissolved oxygen, ORP**
Additional water quality metrics, especially relevant for hydroponic/aquaponic systems. Dissolved oxygen is important for root health in nutrient-solution systems without substrate (e.g. DWC — Deep Water Culture, see [Tank Management](tanks.md)).

### Light Parameters

**PPFD (µmol/m²/s) — Photosynthetic Photon Flux Density**
Indicates how much photosynthetically useful light reaches the plant per second. Rough guidelines:

- Low light plants: 100–300 µmol/m²/s
- Medium light plants: 300–600 µmol/m²/s
- High light plants: 600–1200+ µmol/m²/s

**DLI (mol/m²/d) — Daily Light Integral**
DLI is not a stand-alone sensor reading; it is calculated from PPFD × lighting duration — among other things as part of photoperiod transition schedules (see [Environment Control & Actuators](actuator-control.md)).

---

## Outdoor Sensors: Setting Up a Weather API

!!! warning "Not yet implemented"
    Weather API integration (DWD, OpenWeatherMap, Open-Meteo) is **specified but not yet implemented**. The following sections describe the planned behavior in future tense. Currently outdoor measurements are only captured via Home Assistant or manual entry at the tank. <!-- REQ-005 v2.7 -->

If you have no outdoor sensor, you will be able to retrieve climate data from a weather service.

### Step 1: Enter Location Coordinates

You will be able to enter GPS coordinates (latitude, longitude) for the site under **Expert Settings**.

### Step 2: Select Weather Data Source

You will be able to choose between the following sources:

- **Open-Meteo** (recommended): Free, no API key required
- **German Weather Service (DWD)**: Official German weather data
- **OpenWeatherMap**: Global, 1000 free requests/day

### Step 3: Set Refresh Interval

You will be able to set how often weather data is fetched (recommended: hourly).

!!! note "Weather data as a supplement"
    Weather data reflects conditions at the weather measurement station, not exactly in your garden. For deviations (e.g. a shaded spot), manual adjustments will still be necessary.

---

## Sensor Failures, Fallback, and Interpolation

!!! warning "Not yet implemented"
    Automatic failure detection for sensors, an automatic switch to a fallback source, and bridging short outages via interpolation are **specified but not yet implemented**. Currently, when a Home Assistant sensor fails, no new value simply appears — there is neither a warning nor an automatically created task nor a substitute value.

The planned behavior is as follows: if a sensor delivers no data for more than 6 hours, Kamerplanter will detect the failure, show a warning, switch to the next available source, and create a "Check sensor" task. Short outages (under 2 hours) are planned to be bridged by interpolating the last known values.

---

## Data Retention

Automatically collected measurements are downsampled in stages and eventually deleted (raw data 90 days, then hourly and daily averages — see [Data Retention & Anonymization](../guides/data-retention.md#retention-matrix-sensor-data)).

---

## Frequently Asked Questions

??? question "Do I need sensors to use Kamerplanter?"
    No. Sensors and Home Assistant integration are optional. At the tank you can manually enter EC, pH, and other values at any time. For location climate data (temperature, humidity, VPD, CO2), you currently do need a Home Assistant connection — a manual entry form for this does not exist yet.

??? question "How do I connect a Xiaomi sensor to Kamerplanter?"
    Xiaomi sensors are connected via Home Assistant. Install the Xiaomi integration in Home Assistant, add the sensor, then select it in the Kamerplanter sensor form using the HA entity autocomplete.

??? question "Can I have multiple sensors for the same location?"
    Yes. You can assign any number of sensors to a location. If, for example, temperature and humidity come from different devices, configure them as separate sensors.

??? question "What does the 'Stale' notice on a tank mean?"
    This notice only appears in the live query on the tank detail page: if the last recorded state is older than 60 minutes, Kamerplanter shows "Stale" (under 5 minutes: "Live", in between: "X min ago"). For location sensors (site/location) this indicator does not currently exist.

---

## See Also

- [My Plant Doesn't Look Well — Symptom Diagnosis](plant-health-troubleshooting.md)
- [Dashboard](dashboard.md)
- [Tasks](tasks.md)
- [Tank Management](tanks.md)
- [Home Assistant Integration](../guides/home-assistant-integration.md)
- [Data Retention & Anonymization](../guides/data-retention.md)
- [Guides: VPD Optimisation](../guides/vpd-optimization.md)
