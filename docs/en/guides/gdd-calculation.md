# GDD Calculation

Growing Degree Days (GDD) measure the accumulated heat a plant has experienced since sowing. They allow more reliable predictions of harvest time and phase transitions than calendar days alone, because plants respond to accumulated warmth — not to calendar dates.

---

## Prerequisites

- A plant instance with a sowing date
- Daily temperature readings (entered manually or via sensor)
- Known base temperature for the plant species (can be stored in master data)

---

## The GDD Formula

Kamerplanter uses the standard daily average method:

```
GDD_day = max(0, (T_max + T_min) / 2 - T_base)
```

| Parameter | Meaning | Typical value |
|-----------|---------|--------------|
| `T_max` | Daily maximum temperature (°C) | measured or day average |
| `T_min` | Daily minimum temperature (°C) | measured or day average |
| `T_base` | Plant base temperature (°C) | 10 °C (most vegetables), 0 °C (wheat) |

Accumulated GDD since sowing is the sum of all daily values:

```
GDD_accumulated = Σ GDD_day  (from day 1 to today)
```

!!! note "Negative values are ignored"
    If the daily average temperature falls below the base temperature, the result is 0 — not a negative number. The plant accumulates no heat on cold days.

---

## Base Temperatures for Common Plants

| Plant | T_base (°C) | Note |
|-------|-------------|------|
| Tomato | 10 | Harvest ~1000–1400 GDD |
| Pepper / Chili | 10 | Harvest ~1200–1600 GDD |
| Cucumber | 10 | Harvest ~600–800 GDD |
| Lettuce | 4 | Fast — ~500 GDD |
| Corn | 10 | Maturity ~1300–1600 GDD |
| Cannabis (short-day) | 10 | Flowering varies greatly by cultivar |
| Basil | 10 | First harvest after ~300 GDD |
| Carrot | 4 | Harvest after ~1000–1200 GDD |

!!! tip "Store base temperature in master data"
    Enter the base temperature for a species directly in master data under the "Growth Requirements" tab. Kamerplanter will use this value automatically in all GDD calculations for plants of that species.

---

## Example Calculation

**Scenario:** Tomato, T_base = 10 °C, 5 days after sowing

| Day | T_max (°C) | T_min (°C) | Daily average | GDD_day | GDD accumulated |
|-----|-----------|-----------|--------------|---------|-----------------|
| 1 | 22 | 14 | 18.0 | 8.0 | 8.0 |
| 2 | 25 | 16 | 20.5 | 10.5 | 18.5 |
| 3 | 18 | 8 | 13.0 | 3.0 | 21.5 |
| 4 | 11 | 6 | 8.5 | 0.0 | 21.5 |
| 5 | 24 | 15 | 19.5 | 9.5 | 31.0 |

On day 4, the daily average (8.5 °C) was below the base temperature (10 °C), so no GDD were accumulated.

---

## GDD and Phase Transitions in Kamerplanter

Kamerplanter can evaluate GDD-based phase transition rules. When a plant reaches a defined GDD threshold, a transition prompt is automatically triggered.

### Configuring a GDD Transition Rule

1. Open the master data for the desired plant species.
2. Navigate to **Lifecycle > Transition Criteria**.
3. For the desired phase transition, select the type **GDD-based**.
4. Enter the threshold value in GDD.

!!! example "Example: Tomato Vegetative → Flowering"
    Enter 400 GDD as the threshold for the transition from the vegetative phase to the flowering phase. Once the plant reaches this value, a transition prompt appears in the dashboard.

---

## GDD vs. Calendar Days

| Criterion | Calendar Days | GDD |
|-----------|--------------|-----|
| Simplicity | Very simple | Requires temperature data |
| Accuracy during warm/cold periods | Low | High |
| Comparability across years | Limited | Comparable |
| Best for | Rough planning | Harvest and phase forecasting |

!!! tip "Combination recommended"
    For precise harvest timing, combine both methods: calendar time as a rough frame, GDD as the fine indicator for maturity.

---

## Upper-Capped GDD (Optional Method)

Some plants do not accumulate additional maturity at very high temperatures — growth slows above a maximum temperature. The extended formula:

```
T_eff = min(T_max_cap, max(T_base, daily_average))
GDD_day = T_eff - T_base
```

| Parameter | Meaning |
|-----------|---------|
| `T_max_cap` | Upper temperature cap (e.g. 30 °C) |
| `T_eff` | Effective temperature after capping |

!!! note "Simplified method in Kamerplanter"
    Kamerplanter uses the standard daily average method without upper temperature capping. The extended method is on the roadmap for future versions.

---

## Background: Why GDD Are Better than Calendar Days

Plants are not calendars. Their development is driven by accumulated heat energy. A warm spring can advance tomato development by 2–3 weeks compared to a cold year. Expressed in GDD, those two years are directly comparable.

!!! example "Practical example from outdoor growing"
    In a warm year (April average 16 °C), a tomato reaches the flowering phase in 4 weeks. In the cooler following year (April average 12 °C), it takes 7 weeks. In GDD, both events occur at approximately 400 GDD.

---

## Frequently Asked Questions

??? question "Which base temperature should I use for cannabis?"
    Most cannabis strains use T_base = 10 °C. Some indoor growers use 15 °C since plants never experience temperatures below that. Consistency matters more than the absolute value — use the same T_base for all plants of one species.

??? question "Do I need to record temperatures every day?"
    For indoor growing with stable temperature, a single daily average is sufficient. For outdoor growing, a min/max thermometer is recommended. In future versions, Kamerplanter will be able to retrieve weather data automatically via DWD/Open-Meteo integration (REQ-005).

??? question "GDD value seems unrealistically high — what went wrong?"
    Check that the base temperature is correctly set in master data. If it was accidentally set to 0 °C, all ambient warmth is summed up without a meaningful floor.

---

## See Also

- [Phase Control](../user-guide/growth-phases.md)
- [VPD Optimization](vpd-optimization.md)
- [Plant Management](../user-guide/plant-management.md)
