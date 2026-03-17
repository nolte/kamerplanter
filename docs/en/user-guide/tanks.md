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
| **Nutrient Solution** | Ready-mixed solution | Drip systems, hydroponics |
| **Irrigation Water** | Treated water, pH-adjusted if needed | Soil and coco grows |
| **Reservoir** | Raw water storage tank | Rainwater collector, RO water |
| **Recirculation** | Return tank in closed systems | NFT, ebb & flow |
| **Stock Solution** | Concentrated A/B tanks | Automated dosing |

!!! danger "Never mix stock solutions directly"
    Concentrated A and B stock solutions must never come into direct contact — only when diluted with water. Kamerplanter warns you when creating stock solution tanks.

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
| Type | Tank type (see above) | Nutrient Solution |
| Volume (L) | Tank capacity | 100 |
| Location | Which area is the tank assigned to? | "Grow Tent A" |
| Irrigation System | Which system does the tank feed? | Drip system |

### Step 4: Link Sensors (optional)

If you have a sensor for fill level, EC, or pH in the tank, link it via **Add Sensor Link**. Current sensor values then appear in the tank detail view.

---

## Recording the Current Tank State

The tank state provides information on current fill level, EC, pH, and water temperature.

### Enter a New Reading

1. Open a tank.
2. Click **Record State** (in the **State** tab).
3. Enter the current values:

| Parameter | Description |
|-----------|-------------|
| Fill Level (%) or Volume (L) | Current fill |
| EC (mS/cm) | Electrical conductivity of the solution |
| pH Value | Current pH |
| Water Temperature (°C) | Solution temperature |

4. Save. The value appears in the state history.

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
Link an existing mixing recipe from your nutrient plans. This automatically imports all nutrients and dosages.

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

## Scheduling Maintenance Tasks

Tanks need regular maintenance. Kamerplanter schedules these tasks automatically and reminds you in time.

### Available Maintenance Types

| Maintenance Type | Recommended Interval | Description |
|-----------------|---------------------|-------------|
| **Water Change** | 7–14 days (DWC), 14 days (drip) | Full replacement of nutrient solution |
| **Cleaning** | On visible algae growth, after harvest | Clean tank interior and lines |
| **Disinfection** | Between growing cycles | Sterile cleaning with H₂O₂ or enzymes |
| **EC Probe Calibration** | 7–14 days (recirculation), 14 days (nutrient tank) | Calibrate EC probe with reference solution |
| **pH Probe Calibration** | Same as EC probe | Calibrate pH probe with buffer solutions |
| **Filter Change** | Manufacturer recommendation | Pre-filter, inline filter, UV lamps |
| **Pump Inspection** | Monthly | Check circulation pump and pressure pump |

### Setting Up a Maintenance Schedule

1. Open the tank and switch to the **Maintenance** tab.
2. Click **Add Maintenance Schedule**.
3. Select the maintenance type and interval.
4. The system creates tasks automatically at the set interval.

### Recording Completed Maintenance

When you have carried out maintenance:

1. Click **Record Maintenance** or tick the corresponding task.
2. Enter date, duration, and any observations.
3. The next maintenance date is calculated automatically.

---

## Tank Alerts

Kamerplanter generates automatic alerts when:

- Fill level drops below 20 % of volume (alert: "Tank almost empty")
- EC value is outside the target range for the current phase
- pH value is outside the target range (hydroponics: 5.5–6.5)
- A probe calibration is overdue
- A water change is overdue

These alerts appear in the tank detail view and on the dashboard.

---

## Frequently Asked Questions

??? question "How many tanks can I set up?"
    There is no limit. You can create as many tanks as you physically have.

??? question "Do I have to record every watering as a tank fill?"
    No. Tank fills are for filling and changing the tank. Individual watering sessions are recorded as **feeding events** — either via a planting run or directly under **Fertilization → Feeding Events**.

??? question "How do I calibrate a pH probe properly?"
    Rinse the probe with distilled water first. Immerse it in a buffer solution with a known pH (e.g. pH 7.0). If the displayed value deviates, adjust the calibration offset accordingly. Repeat with a second buffer solution (e.g. pH 4.0). Record the calibration as a maintenance entry.

??? question "What is the difference between tank EC and plant substrate EC?"
    Tank EC shows the concentration of the stock solution. Substrate runoff EC shows how much salt has accumulated in the root zone. Both values matter, but they measure different things.

---

## See Also

- [Fertilization](fertilization.md)
- [Locations and Substrates](locations-substrates.md)
- [Guides: Mixing Nutrient Solutions](../guides/nutrient-mixing.md)
