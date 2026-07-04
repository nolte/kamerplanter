# Tank Management

Tanks manage your water reservoirs, nutrient solution tanks, and irrigation water containers. You record fill levels, document fillings with complete mixing recipes, and schedule maintenance tasks such as water changes and probe calibrations.

---

## Prerequisites

- At least one location set up (tanks are assigned to a location)
- For EC-driven fills: nutrient plans created under **Fertilization**

---

## Understanding Tank Types

Kamerplanter distinguishes five tank types:

| Type | Description | Typical Use |
|------|-------------|-------------|
| **Nutrient** | Ready-mixed nutrient solution | Drip systems, hydroponics |
| **Irrigation** | Treated water, pH-adjusted if needed | Soil and coco grows |
| **Reservoir** | Raw water storage tank | Rainwater collector, RO water |
| **Recirculation** | Return tank in closed systems | NFT, ebb & flow |
| **Stock Solution** | Concentrated A/B tanks | Automated dosing |

!!! danger "Never mix stock solutions directly"
    Concentrated A and B stock solutions must never come into direct contact — only when diluted with water. Kamerplanter warns you when creating stock solution tanks.

!!! info "Hydroponic terms: DWC and NFT"
    **DWC** (Deep Water Culture) is a hydroponic system where the roots hang permanently in an oxygen-enriched nutrient solution — a **Nutrient** tank for this usually needs an air pump (see Equipment below) and regular measurement of dissolved oxygen. **NFT** (Nutrient Film Technique) lets a thin film of nutrient solution flow over the roots and back into a **Recirculation** tank — here the circulation pump matters most.

---

## Creating a New Tank

### Step 1: Navigate to Tank Overview

Click **Locations** in the navigation and open a site. In the **Tanks** tab you see all tanks for that site.

Alternatively: navigate to **Locations → Tanks** for a cross-site overview.

### Step 2: Create a New Tank

Click **Add Tank**.

### Step 3: Configure the Tank

| Field | Description | Example |
|-------|-------------|---------|
| Name | Tank label | "DWC Reservoir Tent A" |
| Type | Tank type (see above) | Nutrient |
| Volume (L) | Tank capacity | 100 |
| Material | Plastic, stainless steel, glass, or IBC container | Plastic |
| Location | Which area is the tank assigned to? | "Grow Tent A" |
| Installation Date | Optional, for maintenance history | 2026-03-01 |
| Notes | Free text, e.g. manufacturer notes | — |

### Equipment (optional)

When creating or editing a tank you can also toggle which equipment it has — it appears as a property chip on the detail page:

| Equipment | Relevance |
|-----------|-----------|
| Lid | Evaporation and light protection |
| Air Pump | Oxygenation, important for DWC |
| Circulation Pump | Circulation, important for NFT/recirculation |
| Heater | Constant water temperature |
| Light-Proof | Prevents algae growth from light exposure |
| UV Sterilizer | Reduces pathogens in the water loop |
| Ozone Generator | Additional disinfection |

### Step 4: Link Sensors (optional)

If you have a sensor for fill level, EC, pH, or other water parameters in the tank, link it via **Add Sensor** (in the Edit tab). Current sensor values then appear in the tank detail view.

!!! tip "Pick a Home Assistant entity via autocomplete"
    In the sensor dialog, an autocomplete field suggests matching Home Assistant entities (including their current state). Selecting one automatically fills in the entity ID and, based on the entity type, suggests a metric type and sensor name. Alternatively, enter the entity ID manually (e.g. `sensor.tank_ec`) or link an MQTT topic.

---

## Recording the Current Tank State

The tank state provides information on current fill level, EC, pH, and water temperature.

### Enter a New Reading

1. Open a tank.
2. Click **Record State** (in the **Readings** tab).
3. Enter the current values:

| Parameter | Description |
|-----------|-------------|
| pH Value | Current pH |
| EC (mS/cm) | Electrical conductivity of the solution |
| TDS (ppm) | Total dissolved solids |
| Water Temperature (°C) | Solution temperature |
| Fill Level (%) or Volume (L) | Current fill |
| Dissolved Oxygen (mg/L) | Oxygen content in the water — essential for root activity in hydroponics, optimal 5–8 mg/L |
| ORP (mV) | Redox potential — an electrochemical measure of water quality, optimal 300–500 mV |

4. Save. The value appears in the state history.

!!! tip "Dissolved oxygen matters most in DWC"
    If dissolved oxygen drops below 6 mg/L, Kamerplanter warns about an increased risk of root rot for nutrient and recirculation tanks. A low ORP (below 250 mV) indicates an increased pathogen risk; values below 650 mV are considered suboptimal for disinfection effectiveness.

!!! tip "Regular measurements"
    The tank detail view shows a chart of EC and pH trends over time. Regular measurements help spot trends early — for example rising EC caused by water evaporation.

---

## Documenting a Tank Fill

Every time the tank is filled — whether a full change, top-up, or correction — the event is recorded as an immutable entry. This lets you trace later exactly what your plants received and when.

### Step 1: Record a Fill

Click **Record Fill** in the tank detail view (in the **Fills** tab).

### Step 2: Select Fill Type

| Type | Description |
|------|-------------|
| **Full Change** | Complete replacement of the solution |
| **Top-Up** | Refilling evaporated water |
| **Correction / Adjustment** | EC or pH correction without full change |

### Step 3: Enter Data

**Basic values:**
- Volume (L) of water added
- Water source (tap water, RO water, rainwater, mixed)
- RO / tap water mixing ratio (if mixed, in %)

**Mixing recipe (optional):**
Link an existing mixing recipe from your nutrient plans. This automatically imports all fertilizers and dosages.

**Measurements after filling:**
- Measured EC after mixing
- Measured pH after correction

**Plan target values:**
If a nutrient plan is linked, Kamerplanter shows the target EC next to your actual value. You can see at a glance whether your result matches the plan.

### Step 4: Save

The fill is saved in the fill history. A new tank state record with the measured values is created automatically.

---

## Water Source Defaults

If you have configured the water source on your site (tap water EC, whether an RO system is available, etc.), Kamerplanter pre-fills base EC and mixing ratio automatically:

1. **Explicitly entered** in the fill form (highest priority)
2. **From the nutrient plan** (when a plan is linked)
3. **From the site water profile** (from site configuration)
4. **Manual entry** (when none of the above provides data)

The source of default values is shown in the form, so you always know where the pre-filled values come from.

---

## Operator / API Functions for Tanks

The following four functions are already fully implemented in the backend, but still **lack a user interface** — you can currently only reach them via the REST API. They are documented here so you know they exist, in case you (or your operator) want to use them via the API or a custom script.

!!! info "API only: EC Dilution Calculator"
    `POST /tanks/{key}/ec-dilution` calculates how much RO water you need to add to a tank with too-high EC to reach a target EC. Inputs: current EC, target EC, current volume (default: the tank's nominal volume), and the EC of your dilution water (default 0.02 mS/cm). The response includes the required amount of RO water, the resulting final volume, and whether the dilution is even feasible with the current tank volume.

!!! info "API only: Tank Linking (feeds-from)"
    `POST /tanks/{key}/feeds-from` links a tank to a source tank it is fed from — for example a nutrient tank refilled from a larger RO reservoir. This edge is not yet shown or managed anywhere in the UI.

!!! info "API only: Fill Statistics"
    `GET /tanks/{key}/fills/stats` returns aggregated metrics for a tank's fill history: number of fills by type, total volume, and average EC deviation from target.

!!! info "API only: Live sensor values directly from Home Assistant"
    `GET /tanks/{key}/states/live` queries the live current state for all Home Assistant sensors linked to the tank, without saving a new tank state. A button to fetch live values in the tank detail view is planned but not yet wired to the UI — until then, see current values by regularly recording a new state (see above).

---

## Scheduling Maintenance Tasks

Tanks need regular maintenance. Kamerplanter schedules these tasks automatically and reminds you in time.

### Available Maintenance Types

<!-- Source: src/backend/app/common/enums.py MaintenanceType (6 values) -->

| Maintenance Type | Typical Interval (guideline) | Description |
|-----------------|-------------------------------|-------------|
| **Water Change** | 7–14 days (DWC), 14 days (drip) | Full replacement of nutrient solution |
| **Cleaning** | On visible algae growth, after harvest | Clean tank interior and lines |
| **Sanitization** | Between growing cycles | Sterile cleaning with H₂O₂ or enzymes |
| **Calibration** | 7–14 days (recirculation), 14 days (nutrient tank) | Calibrate the EC or pH probe with reference/buffer solution — note which probe in the notes field |
| **Filter Change** | Manufacturer recommendation | Pre-filter, inline filter, UV lamps |
| **Pump Inspection** | Monthly | Check circulation pump and pressure pump |

### Setting Up a Maintenance Schedule

1. Open the tank and switch to the **Maintenance** tab.
2. Click **Add Maintenance Schedule**.
3. Select the maintenance type, the interval (in days), and how many days beforehand to remind you.
4. Optionally enable **"Auto-create task"** — Kamerplanter then automatically creates a task when due, instead of only warning in the dashboard/tank detail view.

### Recording Completed Maintenance

When you have carried out maintenance:

1. Click **Record Maintenance** or tick the corresponding task.
2. Enter date, duration, and any observations.
3. The next maintenance date is calculated automatically.

---

## Tank Alerts

Kamerplanter generates automatic alerts when:

- Fill level drops below 20 % of volume (alert: "Tank almost empty")
- pH is outside the range typical for the tank type (e.g. nutrient tank: 5.5–6.5, recirculation: 5.5–6.3, irrigation: 5.8–6.8)
- EC exceeds the upper limit for the tank type, or deviates by more than 20 % from the assigned nutrient plan's target EC
- pH has drifted significantly since the last fill
- A maintenance task (water change, calibration, cleaning, …) is overdue

These alerts appear in the tank detail view and on the dashboard.

---

## Frequently Asked Questions

??? question "How many tanks can I set up?"
    There is no limit. You can create as many tanks as you physically have.

??? question "Do I have to record every watering as a tank fill?"
    No. Tank fills are for filling and changing the tank. Individual watering events are recorded in the [Watering Log](watering-log.md) — either via a planting run or directly through the **Watering Log** menu item.

??? question "How do I calibrate a pH probe properly?"
    Rinse the probe with distilled water first. Immerse it in a buffer solution with a known pH (e.g. pH 7.0). If the displayed value deviates, adjust the calibration offset accordingly. Repeat with a second buffer solution (e.g. pH 4.0). Record the calibration as a maintenance entry.

??? question "What is the difference between tank EC and plant substrate EC?"
    Tank EC shows the concentration of the stock solution. Substrate runoff EC shows how much salt has accumulated in the root zone. Both values matter, but they measure different things.

---

## See Also

- [Fertilization](fertilization.md)
- [Watering Log](watering-log.md)
- [Locations and Substrates](locations-substrates.md)
- [Guides: Mixing Nutrient Solutions](../guides/nutrient-mixing.md)
