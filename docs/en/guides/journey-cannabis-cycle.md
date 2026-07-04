# Cannabis Grow Cycle: From Germination to Cure

This guide walks you through a complete indoor cannabis grow cycle in Kamerplanter — from setting up the planting run to a fully cured result. It doesn't introduce any new functionality; it simply chains together the existing topic pages into one continuous flow, so you don't have to figure out yourself which page is relevant at which stage.

!!! info "Growing as a cultivation association?"
    This page focuses on the horticultural side of the cycle. If you instead operate as a **cultivation association** (cannabis social club) with multiple members, role separation, and documentation obligations, complement this page with [CanG-Compliant Documentation for Cultivation Associations](compliance-anbauvereinigung.md).

---

## The Cycle at a Glance

| Stage | What happens | Relevant page(s) |
|-------|-------------|-------------------|
| 1 | Set up a run with clones or seedlings | [Planting Runs](../user-guide/planting-runs.md) |
| 2 | Guide the plants through the growth phases | [Growth Phases](../user-guide/growth-phases.md) |
| 3 | Mix and dose the nutrient solution | [Fertilization](../user-guide/fertilization.md), [Nutrient Mixing](nutrient-mixing.md) |
| 4 | Keep climate and VPD in the target range | [Sensors](../user-guide/sensors.md), [VPD Optimization](vpd-optimization.md) |
| 5 | Check harvest maturity and observe the pre-harvest interval | [Harvest Management](../user-guide/harvest.md) |
| 6 | Dry and cure | [Post-Harvest: Drying, Curing & Storage](post-harvest.md) |
| 7 | Propagate for the next round | [Propagation Management](../user-guide/propagation.md) |

---

## 1. Set Up the Planting Run

Start by creating a [planting run](../user-guide/planting-runs.md) for your cannabis group — either type **monoculture** (seeds of the same variety) or **clone** (cuttings from a mother plant). The run groups all plants for shared phase transitions and watering schedules, saving you from handling every plant individually once your group gets larger.

In the creation dialog, enter the site, area, and optionally an existing substrate batch. If you choose the "clone" type, you can link the source (mother) plant directly. Kamerplanter then generates all individual plant records with sequential IDs at the click of a button.

**Next up:** Once the plants exist, assign a matching nutrient plan under the **Fertilization & Watering** tab (details in step 3).

## 2. Guide the Plants Through the Growth Phases

Cannabis typically runs on the built-in **indoor standard cycle**: seedling → vegetative → flowering → flush → maturity (harvest allowed). You can see the current phase status in the **Phases** tab of your run, or on each plant's detail page — see [Growth Phases](../user-guide/growth-phases.md).

You can trigger the transition into flowering manually (for example when you switch to a 12/12 photoperiod — the day-length ratio that triggers flowering), or — if GPS coordinates are configured for the location — let it be detected automatically based on day length. Don't rely on the automation alone. Keep checking your plants' phase status regularly, since how often the automatic background check actually runs depends on your installation.

!!! warning "Phase transitions cannot be undone"
    Wait until you're really sure before triggering a transition — once a phase change has happened, it cannot be reversed.

## 3. Plan Fertilization and the Nutrient Solution

Create a nutrient plan with dosages per phase for your run ([Fertilization](../user-guide/fertilization.md)) and assign it to the run. Kamerplanter uses it to calculate your [EC](../reference/glossary.md#electrical-conductivity-ec) budget per phase and suggests the right dosage at every watering event.

When actually mixing, the order matters: always stir in CalMag (calcium-magnesium supplement) before sulfates and phosphates, otherwise precipitation can occur. The complete mixing order, including the EC budget pipeline, incompatibilities, and pH adjustment, is explained in [Nutrient Mixing](nutrient-mixing.md).

!!! tip "Advanced calculators"
    From the Advanced experience level onward, the **Water Mixer** and the **EC Budget Calculator** are also available, letting you factor in CalMag/silicate separately and apply the EC temperature correction — see [Water Mixer and EC Budget Calculator](../user-guide/fertilization.md#water-mixer-and-ec-budget-calculator).

## 4. Monitor Climate and VPD

Vapor Pressure Deficit (VPD) is the single most important climate parameter for cannabis — it determines how strongly your plant transpires and takes up nutrients. The target ranges per phase (e.g. 0.8–1.2 kPa vegetative, 1.0–1.5 kPa flowering) and the underlying Tetens formula are explained in [VPD Optimization](vpd-optimization.md).

For Kamerplanter to compare the measured value against the target range and warn you on the dashboard, you need climate sensors at your location — automatic readout currently works via a Home Assistant connection. Details on sensor setup, the available measurement types, and the current implementation status of the other data sources are in [Sensors and Measurement Data](../user-guide/sensors.md).

## 5. Check Harvest Maturity and the [Pre-Harvest Interval](../reference/glossary.md#pre-harvest-interval-phi)

Kamerplanter shows an expected harvest date on the plant detail page, calculated from the planting date plus the planned phase durations. The final call, however, is yours — based on classic maturity indicators such as trichome color and pistil color; see [Harvest Management](../user-guide/harvest.md).

Before you can create a harvest batch, the system automatically checks all ongoing pest management treatments: if a treatment is still within its pre-harvest interval, Kamerplanter blocks the harvest and tells you the earliest possible date. If you've been working with [Integrated Pest Management (IPM)](../user-guide/pest-management.md) all along, this safety net is already active without any extra setup.

## 6. Dry and Cure

After cutting, you document fresh weight, harvest type, and later the quality assessment directly on the harvest batch (see [Harvest Management](../user-guide/harvest.md)). The horticultural guidance for the drying process itself is in [Post-Harvest: Drying, Curing & Storage](post-harvest.md). It covers target temperature, humidity, and duration for the slow-dry method, the burping schedule for jar curing, and the storage conditions afterward.

!!! note "No dedicated drying workflow yet"
    There's currently no structured way to record drying steps with ongoing weight or moisture tracking. You only enter the actual dry weight once, at the end, on the harvest batch, and otherwise follow the reference values in the post-harvest guide manually.

## 7. Propagate for the Next Round

If you want to clone a mother plant that performed well for the next cycle, or document the genetic lineage of your plants in a traceable way, this is described in [Propagation Management](../user-guide/propagation.md).

!!! warning "Not yet implemented"
    The lineage graph described there (mother plant → clone generations, crosses, grafts) is specified but not yet built. If you want to trace where a plant came from today, create the new plant as a standalone plant instance and note its origin (e.g. mother plant, cutting date) in the free-text notes field for now.

---

## Frequently Asked Questions

??? question "Do I have to use all seven stages, or can I skip some?"
    You can use each page independently. This journey page is a signpost, not a mandatory sequence — if you don't have sensors, for example, just skip step 4 and enter climate data as you see fit, or skip it entirely.

??? question "Does this flow also apply to indoor crops other than cannabis?"
    Broadly yes — the phase model, EC budget, and VPD logic work the same way for chili, basil, or other indoor crops. The specific target values (e.g. VPD ranges, NPK profiles) and harvest types differ by species, though.

??? question "What do I do if harvest is blocked because of the pre-harvest interval?"
    Wait until the earliest possible harvest date the system tells you. If in doubt, check under [Integrated Pest Management (IPM)](../user-guide/pest-management.md) whether the recorded treatment and its pre-harvest interval are correct.

---

## See Also

- [Planting Runs](../user-guide/planting-runs.md)
- [Growth Phases](../user-guide/growth-phases.md)
- [Fertilization](../user-guide/fertilization.md)
- [Nutrient Mixing](nutrient-mixing.md)
- [Sensors and Measurement Data](../user-guide/sensors.md)
- [VPD Optimization](vpd-optimization.md)
- [Harvest Management](../user-guide/harvest.md)
- [Post-Harvest: Drying, Curing & Storage](post-harvest.md)
- [Propagation Management](../user-guide/propagation.md)
- [CanG-Compliant Documentation for Cultivation Associations](compliance-anbauvereinigung.md)
