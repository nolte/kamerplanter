# Hydroponics Setup: Setting Up NFT & DWC

This journey walks you through the initial setup of a soilless hydroponic system in Kamerplanter — from the location through the tank and nutrient solution to sensors and environment control. It chains together existing Kamerplanter pages only; it does not describe any new features. Where a feature is only partially built or not yet implemented, this page says so honestly.

<!-- Target audience: ZG-006 Hydroponics / Vertical Farming Operator -->

---

## Who Is This Journey For?

For anyone running an NFT or DWC system — in a basement, grow tent, or as a small urban farm — who wants to keep an eye on [EC](../reference/glossary.md#electrical-conductivity-ec), pH, and fill level.

## Prerequisites

- A tenant in Kamerplanter (created automatically during onboarding)
- For automatic sensor data: a working Home Assistant integration — see [Home Assistant Integration](home-assistant-integration.md)

---

## What Are NFT and DWC?

Both systems work without a solid substrate — the plant roots are in direct contact with the nutrient solution:

- **DWC** (Deep Water Culture) — the roots hang permanently in an oxygen-enriched nutrient solution. An air pump with an air stone is essential here, since standing water without aeration quickly leads to root rot.
- **NFT** (Nutrient Film Technique) — a thin film of nutrient solution continuously flows over the roots in a sloped channel and returns to a recirculation tank. Here the circulation pump is the critical component: if it fails, the roots dry out within a few hours.

The flow through this journey is identical for both systems — the differences lie mainly in the tank equipment (Step 2).

---

## Step 1: Prepare the Location and Substrate

First, set up a [location](../user-guide/locations-substrates.md) for your system — for example, a location of type "Grow Tent", "Room", or "Shelf", depending on where your setup lives.

Even though NFT and DWC do without a classic substrate, Kamerplanter still manages them through [substrate management](../user-guide/locations-substrates.md#managing-substrates) — using two substrate types specifically designed for this:

- **No Substrate** — for fully soilless systems such as pure DWC setups
- **Hydro Solution** — for systems where the nutrient solution itself is treated as the "medium"

If you use propagation cubes or slabs for germination instead (e.g. to move seedlings into the NFT system later), use the **Rockwool Plug** or **Rockwool Slab** types for that. Clay pebbles are also available as a substrate type, in case you support individual plants in net pots with clay pebbles.

---

## Step 2: Configure Your Tank(s)

Next, set up the tanks for your system in [Tank Management](../user-guide/tanks.md). Kamerplanter distinguishes five tank types — three of them are especially relevant for hydroponics, see [Understanding Tank Types](../user-guide/tanks.md#understanding-tank-types):

| Your system | Tank type | Key equipment |
|-------------|-----------|----------------|
| DWC | Nutrient | Air pump (oxygenation) |
| NFT | Recirculation | Circulation pump (circulation) |
| Both (reservoir) | Reservoir | Lid, optionally light-proof (against algae) |

When creating the tank, enter the volume, material, and matching equipment — the equipment chips then appear on the tank detail page. Then link your EC, pH, and fill-level sensors via **Add Sensor** directly on the tank (more on this in Step 4).

!!! danger "Never mix stock solutions directly"
    If you use concentrated A/B stock solutions for automated dosing, set them up as separate tanks of type **Stock Solution**. These must never come into direct contact with each other — only when diluted with water. Kamerplanter warns you when you create these tanks.

---

## Step 3: Mixing the Nutrient Solution — EC Budget and Mixing Order

Once the tank is set up, it's time for the nutrient solution itself. [Nutrient Mixing](nutrient-mixing.md) explains step by step how Kamerplanter calculates an EC budget — based on your target EC and the EC of your mixing water. It also scales manufacturer recipes proportionally and guides you through the correct mixing order (silica before CalMag before base nutrients — otherwise precipitation is a risk).

For hydroponic systems without substrate buffering, EC targets are tighter than for soil or coco — the matching ranges by growth phase are in [EC Target Values by Phase and Substrate](nutrient-mixing.md#ec-target-substrate).

!!! tip "Recirculation needs more attention than drain-to-waste"
    In a recirculating system (NFT, DWC), the nutrient solution concentrates over time through evaporation — EC creeps upward without new nutrients being added. Plan for regular check measurements instead of relying solely on the last fill (see [Recording the Current Tank State](../user-guide/tanks.md#recording-the-current-tank-state)).

---

## Step 4: Setting Up Sensors for EC, pH, and Fill Level

With the tank set up and the solution mixed, it's time for ongoing monitoring. [Sensors and Measurement Data](../user-guide/sensors.md) explains how to [link sensors to a location](../user-guide/sensors.md#linking-sensors-to-a-location) and which [metric types](../user-guide/sensors.md#metric-types-in-the-form) are available. For a hydroponic system, these are especially relevant:

| Metric type | What it's for |
|-------------|----------------|
| `ec_ms` | Nutrient concentration of the solution |
| `ph` | Nutrient availability |
| `water_temp_celsius` | Root zone temperature |
| `dissolved_oxygen_mgl` | Oxygen supply to the roots (especially critical for DWC) |
| `orp_mv` | Redox potential as a water quality indicator |
| `fill_level_percent` | Fill level — early warning before a tank runs empty |

!!! info "Current state: Home Assistant or manual entry at the tank"
    Of the four data sources envisioned in the specification, two are actually usable today: automatic polling via **Home Assistant** (every 5 minutes) and **manual entry** directly at the tank — see [Recording the Current Tank State](../user-guide/tanks.md#recording-the-current-tank-state). A direct MQTT connection without Home Assistant in between is planned in the data model, but not yet implemented. If you already run ESPHome- or Shelly-based probes, the easiest way to connect them is via Home Assistant, then select them in the sensor or tank form using the HA entity autocomplete.

---

## Step 5: Environment Control — Actuators and Automation (Outlook)

The final building block of a fully automated setup is the closed control loop: a sensor measures, a rule evaluates, an actuator switches — for example a circulation pump, a CO₂ doser, or a humidifier.

!!! warning "Not yet implemented"
    [Environment Control & Actuators](../user-guide/actuator-control.md) is fully specified but not yet implemented in code. Currently, only the Home Assistant communication layer for **reading** sensor data exists (Step 4) — the rule engine, schedules, hysteresis, and automatic sending of actuator commands are still missing.

    Until then, control pumps, humidifiers, and dosing devices directly via Home Assistant or by hand, and log important events (water changes, calibration) manually via [Tank Maintenance Scheduling](../user-guide/tanks.md#scheduling-maintenance-tasks).

---

## Where This Journey Hits Its Limits: Yield and Cost

For semi-professional or commercial operations, metrics like yield per watt, yield per liter, or production cost per head of lettuce are often at least as important as pure climate and nutrient control.

!!! warning "Resource and cost analytics not yet available"
    Kamerplanter currently documents harvests with weight and a quality rating (see [Harvest Management](../user-guide/harvest.md)), but there is **no** automatic calculation yet for yield per watt, yield per liter, or production cost per unit (electricity, nutrient, water, and substrate costs). <!-- ZG-006: yield/cost analytics, resource dashboard planned, not scheduled -->
    For a cost or yield metric per crop, you currently have to calculate it yourself — for example using the harvest weights recorded in Kamerplanter and your own consumption data outside the app.

---

## Frequently Asked Questions

??? question "Do I absolutely need Home Assistant for a hydroponics setup?"
    No. You can always enter EC, pH, water temperature, fill level, and the other tank values manually — see [Recording the Current Tank State](../user-guide/tanks.md#recording-the-current-tank-state). Home Assistant becomes worthwhile once you have several tanks or a larger system and manual entry becomes too much effort.

??? question "How do I keep my NFT channel from drying out if the pump fails?"
    Kamerplanter cannot yet automatically detect a failed pump and react (see Step 5). Until environment control is implemented, set up your own safeguard in Home Assistant (e.g. a notification on pump power loss) and add a check task in Kamerplanter.

??? question "What do I do about rising EC from evaporation?"
    Measure regularly and log the values at the tank. If EC rises above the target range, dilute with fresh water or reverse-osmosis (RO) water — details on the mixing logic are in [Nutrient Mixing](nutrient-mixing.md).

---

## See Also

- [Locations & Substrates](../user-guide/locations-substrates.md)
- [Tank Management](../user-guide/tanks.md)
- [Nutrient Mixing](nutrient-mixing.md)
- [Sensors and Measurement Data](../user-guide/sensors.md)
- [Environment Control & Actuators](../user-guide/actuator-control.md)
- [Home Assistant Integration](home-assistant-integration.md)
- [Glossary](../reference/glossary.md)
