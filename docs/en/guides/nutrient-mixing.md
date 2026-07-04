# Nutrient Mixing

A correctly mixed nutrient solution is the foundation for healthy plant growth. Kamerplanter automatically calculates EC budgets, scales manufacturer recipes, and validates the mixing order — preventing precipitation and wasted nutrients.

!!! info "Two terms up front: Fertigation and Drain-to-Waste"
    **Fertigation** ("Fertilizer" + "Irrigation") means automated delivery of nutrient solution through irrigation — usually via a drip system and pump, instead of watering by hand with a can. In Kamerplanter, fertigation is one of the [delivery methods](../user-guide/fertilization.md#delivery-channels-multi-channel-delivery) alongside drench, foliar, and top-dress.

    **Drain-to-Waste** is an irrigation strategy without recirculation. You deliberately water with a surplus (usually 10–30 % more than the substrate can hold), so runoff water drains from the bottom of the pot. This runoff is discarded rather than reused — unlike recirculating systems such as NFT (Nutrient Film Technique) or ebb & flow. The advantage: salt buildup in the substrate is prevented, because excess nutrients are flushed out rather than reused. More on this in the [Runoff Analysis](#runoff-analysis) section below.

!!! danger "Mixing order matters"
    Always add CalMag (calcium-magnesium supplement) **first** to the water before adding any other fertilizer — especially before sulfates and phosphates. Wrong order causes calcium sulfate precipitation (CaSO₄) and renders the solution ineffective.

---

## Prerequisites

- EC meter (electrical conductivity meter)
- pH meter or test kit
- Known EC values for your water source (tap water or RO water)
- Fertilizers added in Kamerplanter under **Fertilization → Fertilizers**

---

## The EC Budget Model

Kamerplanter calculates how much electrical conductivity the fertilizers may still contribute — the EC budget:

```
EC_net = EC_target - EC_base_water
```

| Variable | Meaning | Example |
|----------|---------|---------|
| `EC_target` | Desired final EC of the nutrient solution | 1.8 mS/cm |
| `EC_base_water` | EC of the water used | 0.4 mS/cm |
| `EC_net` | Remaining budget for fertilizers | 1.4 mS/cm |

!!! tip "RO water for maximum control"
    Reverse osmosis (RO) water typically has EC < 0.05 mS/cm, freeing the full EC budget for nutrients. Hard tap water with high Ca/Mg content significantly reduces the available budget.

---

## The 3-Stage EC Budget Pipeline

Kamerplanter applies a structured 3-stage calculation:

### Stage 1 — Water Mix (EC_mix)

When blending RO and tap water, Kamerplanter first calculates the EC of the blend:

```
EC_mix = EC_tap × (1 - RO_fraction) + EC_RO × RO_fraction
```

**Example:** 50 % RO (EC 0.02) + 50 % tap water (EC 0.50):
```
EC_mix = 0.50 × 0.50 + 0.02 × 0.50 = 0.26 mS/cm
```

### Stage 2 — EC Allocation (Budget Segments)

The net EC budget is divided into segments in this order:

| Segment | Priority | Description |
|---------|---------|-------------|
| Silica | 1 (first deduction) | Optional silicate is pre-calculated |
| CalMag | 2 | Calcium-magnesium solution (essential for coco/hydro) |
| pH Reserve | 3 | Buffer for pH adjuster (0.02–0.05 mS depending on water hardness) |
| Base Nutrients | 4 | Remaining budget distributed to base nutrients |

!!! tip "Where to find these values in the nutrient calculator"
    In the mixing protocol (**Fertilization → Nutrient Calculations → Mixing Protocol**) you enter your water's carbonate hardness as **alkalinity** (ppm CaCO₃). Kamerplanter automatically calculates the pH reserve from it and shows it together with the net EC budget (`ec_net`) and the recipe's validity (`valid`) in the result. Details on how to use it: [Fertilization — Alkalinity and pH Reserve](../user-guide/fertilization.md#alkalinity-and-ph-reserve).

### Stage 3 — Recipe Scaling

When manufacturer recipes (ml/L per fertilizer) are stored in Kamerplanter, the system scales proportionally:

```
k = EC_net / EC_full_recipe
dose_i = k × recipe_dose_i
```

Without recipe data: the EC budget is distributed equally across all base fertilizers.

---

## Mixing Order — Step by Step

The mixing sequence is critical. Kamerplanter automatically generates a numbered mixing guide:

```
1. Fill container with [X] liters of water
2. Add silica — stir vigorously, wait 5 minutes
3. Add CalMag — mix thoroughly
4. Add base nutrient A — stir
5. Add base nutrient B — stir
6. Adjust pH to target — stir, wait 5 minutes
7. Verify final EC reading
```

!!! warning "Why silica before CalMag?"
    Silicate ions (SiO₄²⁻) form poorly soluble calcium silicate (CaSiO₃) with calcium ions (Ca²⁺). Therefore silica must go into the water before CalMag — otherwise the active ingredient precipitates out.

---

## Incompatibilities and Safety Validation

Kamerplanter automatically checks the following combinations:

| Combination | Risk | Severity |
|-------------|------|---------|
| CalMag + Sulfates (e.g. Epsom) | Gypsum precipitation (CaSO₄) | Critical |
| CalMag + Phosphates | Calcium phosphate precipitation | Critical |
| Silica + CalMag (wrong order) | CaSiO₃ precipitation | Critical |
| Iron chelate + pH > 7 | Chelate destabilizes | Warning |
| Foliar-only + fertigation products | Wrong application method | Note |

!!! danger "Act on critical warnings immediately"
    If a red warning appears in the mixing guide, stop immediately and check the fertilizer combination. A precipitated solution cannot be recovered — complete remixing is required.

---

## EC Target Values by Phase and Substrate {#ec-target-substrate}

Kamerplanter validates the calculated final EC against phase- and substrate-specific maximum values:

<!-- Source: src/backend/app/domain/engines/ec_budget_engine.py EC_MAX_TABLE (REQ-004-A §4.2) -->

| Substrate | Seedling (mS) | Vegetative (mS) | Flowering (mS) | Flushing (mS) |
|-----------|--------------|----------------|----------------|---------------|
| Hydroponics | 0.8 – 1.2 | 1.6 – 2.4 | 1.8 – 2.8 | 0.0 – 0.3 |
| Coco | 0.8 – 1.0 | 1.6 – 2.0 | 1.8 – 2.4 | 0.0 – 0.3 |
| Soil | 0.4 – 0.6 | 0.8 – 1.4 | 1.0 – 1.6 | 0.0 – 0.3 |

!!! tip "Fresh coco: automatic CalMag boost"
    For freshly set-up coco batches (0 cycles used), Kamerplanter automatically increases the CalMag dose by 20 %, since unused coco absorbs calcium and magnesium from the solution (cation exchange).

---

## EC Temperature Correction (EC@25)

The electrical conductivity of a reading depends on water temperature — the same nutrient solution shows a higher EC in warmer water than in cooler water. To keep measurements taken at different temperatures comparable, Kamerplanter can optionally correct to the 25 °C reference temperature:

```
EC@25 = EC_measured / (1 + 0.02 × (T − 25))
```

If you enter both your measured EC value and the water temperature in the [EC Budget Calculator](../user-guide/fertilization.md#water-mixer-and-ec-budget-calculator), Kamerplanter automatically computes this corrected value and shows it in addition to the raw reading.

!!! example "Example"
    You measure 1.9 mS/cm at a water temperature of 30 °C. Corrected to 25 °C: `EC@25 = 1.9 / (1 + 0.02 × 5) = 1.9 / 1.1 ≈ 1.73 mS/cm`. The uncorrected value would make the nutrient solution look stronger than it actually is at the reference temperature.

---

## Setting pH

After mixing all nutrients, measure and correct the pH:

| Substrate | Target pH Range | Note |
|-----------|----------------|------|
| Hydroponics | 5.5 – 6.0 | Optimum nutrient availability |
| Coco | 5.8 – 6.2 | Slightly higher than hydro |
| Soil | 6.0 – 6.8 | Consider microbial activity |
| Living Soil | 6.2 – 7.0 | pH buffered by soil biology |

Kamerplanter instructs whether pH Up (potassium hydroxide) or pH Down (phosphoric acid) is needed.

!!! warning "Always adjust pH last"
    pH corrections must be performed as the final step — after all nutrients have been mixed in. Nutrients change the pH and may require a second adjustment.

---

## Runoff Analysis {#runoff-analysis}

In drain-to-waste operation (coco, rockwool), runoff analysis provides important feedback:

| Measurement | Target Range | Deviation → Action |
|-------------|-------------|-------------------|
| Runoff EC − Input EC | ±0.3 mS/cm | > +0.5: salt buildup → flush |
| Runoff pH − Input pH | ±0.5 | > ±0.5: check substrate buffering |
| Runoff volume / Input | 10 – 30 % | < 10 %: increase water volume |

!!! example "Typical flush signal"
    Runoff EC = 2.8 mS, input EC = 2.0 mS → delta = +0.8 mS (exceeds threshold of 0.5). Kamerplanter recommends 1–2 flush cycles with clean water (EC < 0.3 mS, pH 6.0).

---

## Pre-Harvest Flushing {#flush-substrate}

Kamerplanter automatically calculates a flushing schedule via the [Flushing Calculator](../user-guide/fertilization.md#calculating-a-flush). Recommended flush duration depends on substrate:

<!-- Source: src/backend/app/domain/engines/nutrient_engine.py FlushingProtocol.FLUSH_DURATIONS -->

| Substrate | Recommended Flush Duration |
|-----------|--------------------------|
| Hydroponics | 7 – 14 days |
| Coco | 10 – 21 days |
| Rockwool | 7 – 14 days |
| Soil | 14 – 30 days |

**Flushing protocol (3-phase reduction):**

| Time segment (% of flush period) | Target EC | Action |
|-----------------------------------|---------|--------|
| First 30 % | 50 % of original EC | Reduced nutrient solution |
| Middle 30 % | 25 % of original EC | Quarter-strength |
| Final 40 % | 0.0 mS/cm | Plain water only |

---

## Water Temperature

Water temperature affects solubility and biological effectiveness:

| Temperature | Assessment |
|------------|-----------|
| < 5 °C | Too cold — poor dissolution, precipitation risk |
| 5 – 18 °C | Suboptimal — stir longer |
| 18 – 22 °C | Optimal |
| 22 – 30 °C | Acceptable — biological products may degrade faster |
| > 35 °C | Not suitable for biological fertilizers |

---

## Frequently Asked Questions

??? question "My solution is white / cloudy after mixing — what happened?"
    Cloudiness indicates precipitation. Most common cause: CalMag was added after a sulfate or phosphate. Discard the solution, rinse the container with warm water, correct the mixing order, and start fresh.

??? question "Can I add all fertilizers at the same time?"
    No. CalMag and sulfate/phosphate must not come into contact simultaneously — this immediately causes precipitation. Always add step by step and stir between additions.

??? question "How often should I measure EC and pH of the finished solution?"
    Always immediately after mixing. For tank/reservoir systems, check daily — EC rises as water evaporates and pH drifts due to plant metabolism.

??? question "What does 'not tank-safe' mean for a fertilizer?"
    Fertilizers that are not tank-safe must not be stored in a reservoir over extended periods — they decompose or precipitate. They must be mixed fresh before each application.

---

## See Also

- [Fertilization Logic](../user-guide/fertilization.md)
- [Watering Log](../user-guide/watering-log.md) — runoff analysis per entry
- [Tank Management](../user-guide/tanks.md)
- [VPD Optimization](vpd-optimization.md)
