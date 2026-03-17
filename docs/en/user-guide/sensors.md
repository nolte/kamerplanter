# Sensors and Measurement Data

Kamerplanter collects climate data, substrate values, and light data from four different sources. The system works equally well with expensive smart home sensors or with no hardware at all — fully manual entry is completely supported.

---

## Prerequisites

- At least one location set up
- For automatic data: sensors physically installed and connected to Home Assistant or MQTT

---

## The Four Data Sources

Kamerplanter uses the following data sources in a fallback chain. The system automatically switches to the next available source when one fails:

```
Automatic (IoT/MQTT) → Home Assistant REST API → Weather API (outdoor) → Manual Entry
```

**1. Automatic (IoT/MQTT)**
Sensors (e.g. SCD40, AHT20, Xiaomi soil sensor) send data directly via MQTT or through Home Assistant to Kamerplanter. No user action required.

**2. Home Assistant (semi-automatic)**
Home Assistant delivers sensor values via its REST API. This is useful when your sensors are already integrated in Home Assistant.

**3. Weather API (outdoor only)**
For outdoor locations (garden, balcony) Kamerplanter can retrieve climate data from the German Weather Service (DWD), Open-Meteo, or OpenWeatherMap. No sensor required.

**4. Manual Entry**
You enter measurement values yourself. Kamerplanter reminds you with tasks when a measurement is due.

!!! note "Every measurement has a source label"
    The detail view always shows where a value came from: sensor, Home Assistant, weather API, or manual. This lets you see how reliable the value is.

---

## Linking Sensors to a Location

### Step 1: Open Site or Location

Navigate to **Locations** and open the site or location the sensor belongs to.

### Step 2: Add Sensor

Click **Add Sensor** (icon in the site detail page top right or in the Sensors tab).

### Step 3: Configure the Sensor

Fill in the form:

| Field | Description | Example |
|-------|-------------|---------|
| Name | Sensor label | "Temp/RH Grow Tent A" |
| Type | What does the sensor measure? | Temperature + Humidity |
| Data Source | Where does the data come from? | Home Assistant |
| Entity ID (HA) | Home Assistant entity name | `sensor.growtent_a_temperature` |
| MQTT Topic | For MQTT connections | `kamerplanter/growtent/temp` |

### Step 4: Test the Connection

Click **Test Connection**. Kamerplanter attempts to retrieve the current value. If successful, the measurement appears.

---

## Entering Measurements Manually

If you have no sensors or a sensor has failed, you can enter measurements manually.

### Step 1: Navigate to the Plant or Location

Open a plant or location and look for the **Measurements** or **Sensor Data** tab.

### Step 2: Record a Measurement

Click **Add Measurement** and enter the values:

**Climate parameters:**
- Temperature (°C)
- Relative humidity (%)
- VPD — calculated automatically when temperature and humidity are known
- CO2 (ppm) — optional

**Substrate parameters:**
- Soil moisture (%)
- Substrate temperature (°C)
- EC in substrate (mS/cm)
- pH value

**Light parameters:**
- PPFD (µmol/m²/s) — Photosynthetic Photon Flux Density
- DLI (mol/m²/d) — Daily Light Integral (calculated from PPFD × light hours)

!!! tip "Let VPD be calculated automatically"
    You do not need to measure Vapor Pressure Deficit (VPD) yourself. Enter temperature and humidity and Kamerplanter calculates VPD automatically using the Tetens formula.

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

Kamerplanter compares the current VPD against the target for the active growth phase and alerts you on deviation.

**CO2 concentration (ppm)**
Normal indoor air: approximately 400–500 ppm. Plants benefit from 800–1500 ppm (with sufficient light). Above 1500 ppm brings little additional benefit and may cause discomfort for people.

### Substrate Parameters

**Soil Moisture (%)**
Shows how much water is present in the substrate. Too dry causes wilting; too wet promotes root rot.

**EC in Substrate (mS/cm)**
Substrate EC (measured at runoff or with a substrate probe) shows salt concentration in the root zone. Significantly higher runoff EC than input EC signals salt accumulation and is a sign that a flush is needed.

**pH Value**
pH determines nutrient availability. Outside the optimal range (hydroponics: 5.5–6.5; soil: 6.0–7.0) plants cannot absorb nutrients even when enough is present.

### Light Parameters

**PPFD (µmol/m²/s) — Photosynthetic Photon Flux Density**
Indicates how much photosynthetically useful light reaches the plant per second. Rough guidelines:
- Low light plants: 100–300 µmol/m²/s
- Medium light plants: 300–600 µmol/m²/s
- High light plants: 600–1200+ µmol/m²/s

**DLI (mol/m²/d) — Daily Light Integral**
The daily light integral is the total light quantity over a day. It is calculated from PPFD × lighting duration. DLI is especially important for outdoor growers and greenhouses.

---

## Outdoor Sensors: Setting Up a Weather API

If you have no outdoor sensor, you can retrieve climate data from a weather service.

### Step 1: Enter Location Coordinates

Open your site and enter the GPS coordinates (latitude, longitude) under **Expert Settings**.

### Step 2: Select Weather Data Source

Choose the preferred source:
- **Open-Meteo** (recommended): Free, no API key required
- **German Weather Service (DWD)**: Official German weather data
- **OpenWeatherMap**: Global, 1000 free requests/day

### Step 3: Set Refresh Interval

Choose how often weather data is fetched (recommended: hourly).

!!! note "Weather data as a supplement"
    Weather data reflects conditions at the weather measurement station, not exactly in your garden. For deviations (e.g. a shaded spot) adjust values manually.

---

## Sensor Failures and Fallbacks

If a sensor delivers no data for more than 6 hours, Kamerplanter detects the failure automatically:

1. A warning appears in the location detail view
2. Kamerplanter switches to the next available fallback source
3. A task is created: "Check sensor — [sensor name]"

Short outages (under 2 hours) are bridged by interpolating the last known values.

---

## Frequently Asked Questions

??? question "Do I need sensors to use Kamerplanter?"
    No. Kamerplanter works fully with manually entered values. Sensors and smart home integration are optional — they make life easier but are not a prerequisite.

??? question "How do I connect a Xiaomi sensor to Kamerplanter?"
    Xiaomi sensors are most easily connected via Home Assistant. Install the Xiaomi integration in Home Assistant, add the sensor, then link Home Assistant to Kamerplanter using the entity name.

??? question "Can I have multiple sensors for the same location?"
    Yes. You can assign any number of sensors to a location. If, for example, temperature and humidity come from different devices, configure them as separate sensors.

??? question "What does 'Measurement outdated' mean?"
    Kamerplanter shows this notice when the last measurement of a parameter is older than the configured monitoring interval. It is a reminder that a new measurement is due.

---

## See Also

- [Dashboard](dashboard.md)
- [Tasks](tasks.md)
- [Guides: VPD Optimisation](../guides/vpd-optimization.md)
