# VPD Optimization

Vapor Pressure Deficit (VPD) describes the difference between the current water vapor pressure in the air and the maximum vapor pressure the air could hold at a given temperature. It is the key parameter governing the plant's transpiration rate — and therefore nutrient uptake, cooling capacity, and fungal disease risk.

---

## Prerequisites

- Thermometer and hygrometer (temperature + relative humidity)
- Known growth phase of the plant
- Ventilation or climate control for adjustment

---

## What Is VPD and Why Does It Matter?

When the air is dry (high VPD), it actively draws water from the leaves — stomata open wide, nutrients are pulled upward, the plant grows rapidly. If the air is too dry, stomata close as a protective response — growth stops.

When the air is too humid (low VPD), little water evaporates — nutrient transport stalls, fungi thrive.

**Optimal VPD = balance between growth and protection.**

---

## Formula (Tetens Approximation)

The saturated vapor pressure at a given temperature (eSat) is calculated as:

```
eSat(T) = 0.6108 × exp(17.27 × T / (T + 237.3))  [kPa]
```

The actual vapor pressure in the air:

```
e_actual = (rH / 100) × eSat(T_air)
```

VPD is the difference, referenced to leaf temperature:

```
VPD = eSat(T_leaf) - e_actual
```

In practice, `T_leaf ≈ T_air - 2 °C` is commonly assumed (leaves cool through transpiration).

!!! note "Simplified calculation"
    For everyday use: VPD ≈ eSat(T_air) × (1 - rH/100). This approximation works well between 18 and 30 °C.

---

## Target Values by Growth Phase

Kamerplanter uses the following target ranges, defined as system constants in the backend:

| Phase | VPD Target Range (kPa) | Humidity (guideline) | Temperature (guideline) |
|-------|-----------------------|---------------------|------------------------|
| Germination | 0.4 – 0.8 | 70 – 80 % | 22 – 26 °C |
| Seedling | 0.4 – 0.8 | 65 – 75 % | 22 – 26 °C |
| Vegetative | 0.8 – 1.2 | 55 – 70 % | 22 – 28 °C |
| Flowering | 1.0 – 1.5 | 40 – 55 % | 22 – 28 °C |
| Ripening / Late Flower | 1.2 – 1.6 | 35 – 50 % | 20 – 26 °C |
| Flushing | 0.8 – 1.2 | 55 – 65 % | 20 – 24 °C |

!!! danger "High humidity during flowering"
    Relative humidity above 60 % during the flowering phase strongly promotes Botrytis (grey mould). Keep humidity consistently below 55 % — especially in the final weeks of flowering.

---

## Calculating VPD — Practical Example

**Scenario:** Grow room, vegetative phase, 25 °C air temperature, 65 % rH

```
eSat(25) = 0.6108 × exp(17.27 × 25 / (25 + 237.3))
         = 0.6108 × exp(1.646)
         = 0.6108 × 5.186
         = 3.168 kPa

e_actual = 0.65 × 3.168 = 2.059 kPa

VPD = 3.168 - 2.059 = 1.109 kPa  ✓ (Target: 0.8–1.2 kPa)
```

!!! tip "VPD calculator"
    Simple VPD charts or apps work well in practice. Kamerplanter displays the calculated VPD on the plant detail page when sensor data is available.

---

## VPD Reference Table (Temperature × Humidity)

VPD values in kPa for various combinations of temperature and relative humidity:

| rH \ T | 18 °C | 20 °C | 22 °C | 24 °C | 26 °C | 28 °C | 30 °C |
|--------|-------|-------|-------|-------|-------|-------|-------|
| 40 % | 1.24 | 1.42 | 1.62 | 1.84 | 2.08 | 2.35 | 2.55 |
| 50 % | 1.03 | 1.18 | 1.35 | 1.54 | 1.74 | 1.96 | 2.13 |
| 55 % | 0.93 | 1.07 | 1.22 | 1.38 | 1.56 | 1.76 | 1.91 |
| 60 % | 0.82 | 0.95 | 1.08 | 1.23 | 1.39 | 1.57 | 1.70 |
| 65 % | 0.72 | 0.83 | 0.95 | 1.08 | 1.22 | 1.37 | 1.49 |
| 70 % | 0.62 | 0.71 | 0.81 | 0.92 | 1.04 | 1.18 | 1.28 |
| 75 % | 0.52 | 0.59 | 0.68 | 0.77 | 0.87 | 0.98 | 1.06 |
| 80 % | 0.41 | 0.47 | 0.54 | 0.62 | 0.70 | 0.79 | 0.85 |

*Values rounded. Calculated with Tetens approximation, T_leaf = T_air.*

---

## Common VPD Problems and Solutions

### VPD Too Low (Plant Barely Transpires)

**Symptoms:** Poor growth, nutrient deficiency despite feeding, mould spots, soft or thin leaves.

**Causes and solutions:**

| Cause | Solution |
|-------|----------|
| Too high humidity | Increase ventilation, use dehumidifier |
| Temperature too low | Heating, raise daytime temperature to 22–26 °C |
| Overcrowded grow space | Reduce plant density, improve air circulation |

### VPD Too High (Plant Closes Stomata)

**Symptoms:** Wilting despite adequate watering, heat stress, leaf tips browning, stunted growth.

**Causes and solutions:**

| Cause | Solution |
|-------|----------|
| Air too dry | Humidifier, wet towels, water reservoirs |
| Temperature too high | Cooling, ventilation, check lighting schedule |
| Lighting too intense | Reduce light intensity or increase distance |

---

## VPD and Watering Frequency

VPD directly affects how quickly the plant takes up water. At high VPD (>1.5 kPa), the transpiration rate can rise sharply — substrates dry out faster.

**Rules of thumb:**
- VPD < 0.8 kPa: Extend watering interval
- VPD 0.8–1.5 kPa: Normal watering frequency
- VPD > 1.5 kPa: Increase watering frequency, monitor for heat stress

!!! tip "Use substrate as a buffer"
    Coco and rockwool dry out particularly fast at high VPD. Soil substrates buffer better. Adjust watering frequency accordingly or use an automated watering schedule.

---

## Configuring VPD in Kamerplanter

Kamerplanter allows you to adjust phase-specific VPD target values per requirement profile:

1. Navigate to **Master Data > [Species] > Lifecycle > [Phase] > Requirement Profile**.
2. Adjust `vpd_target_kpa` and the min/max boundaries.
3. When sensor data is available, Kamerplanter compares the measured value against the target range and shows warnings in the dashboard.

!!! example "Custom VPD targets for sensitive cultivars"
    Tropical plants like chili or basil are more sensitive to high VPD. Set the vegetative target range tighter to 0.7–1.0 kPa for these species.

---

## Frequently Asked Questions

??? question "Do I need to calculate VPD every day?"
    No. Once you know optimal temperature–humidity combinations for your growth phase (e.g. 25 °C / 60 % for vegetative), set those as targets on your controller. Kamerplanter will alert you via sensor-based warnings if conditions drift outside the target range.

??? question "Leaf temperature vs. air temperature — which do I measure?"
    Standard hygrometers measure air temperature and humidity. That is sufficient for practical use. Leaf temperature is typically 1–3 °C below air temperature. For highest accuracy, an infrared thermometer can be aimed directly at the leaf.

??? question "Different VPD at night than during the day — is that normal?"
    Yes. At night, temperature drops, which lowers VPD at the same humidity level. A slightly lower nighttime VPD (0.6–0.8 kPa) is normal and harmless, as long as absolute humidity does not rise too high.

---

## See Also

- [Phase Control](../user-guide/growth-phases.md)
- [GDD Calculation](gdd-calculation.md)
- [Environment Control](../user-guide/environment-control.md)
- [Sensors](../user-guide/sensors.md)
