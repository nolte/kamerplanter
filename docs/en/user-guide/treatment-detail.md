# Treatment Detail Page

The treatment detail page gives you all the information you need to apply a control measure safely and effectively: key facts at a glance, step-by-step instructions, mode of action, safety information, and — as an important regulatory reminder — the **pre-harvest interval (PHI)**.

You can reach the detail page in two ways:

- Via **Pest Management (IPM) → Treatments** — click a row in the treatment list.
- Via the [pest detail page](pest-detail.md) — click the name of a treatment in the **Control Measures** list.

---

## Prerequisites

- Authenticated user account (not Light mode)
- To record a treatment application directly: at least one plant or an active planting run

---

## Key Facts (Fact Sheet)

The fact sheet at the top of the page summarises the essential properties of the treatment in a quick-read overview:

| Field | Description |
|-------|-------------|
| **Type** | Cultural, Biological, Mechanical, or Chemical — follows the IPM hierarchy |
| **Active ingredient** | The active substance in the product (e.g. azadirachtin, pyrethrin, spinosad) |
| **Dosage** | Recommended amount and concentration (e.g. "5 ml/L", "2 g/m²") |
| **Application method** | How is the product applied? (spraying, watering, spreading, incorporation into substrate, release of living organisms) |
| **Pre-harvest interval (days)** | Mandatory waiting time between the last application and harvest — 0 days for beneficial insects and mechanical measures |
| **Protective equipment** | Personal protective equipment recommended or required (e.g. gloves, respirator, safety goggles) |

!!! warning "Pre-harvest interval activates immediately on recording"
    As soon as you record a treatment with a PHI in the IPM system, Kamerplanter automatically blocks the harvest of affected plants. The earliest possible harvest date is displayed in the plant view and in the calendar.

!!! tip "What exactly is a pre-harvest interval (PHI)?"
    The **pre-harvest interval (PHI)** is the legally required minimum waiting period between the last application of a plant protection product and harvest. It protects you and others from residues in the harvested crop. Biological products typically have shorter intervals than chemical ones — beneficial insects have none at all.

---

## Application

This section explains how and when to apply the product. The instructions are based on the recommendation stored in the master data; always read the current product label for your specific product as well.

**Typical information in this section:**

- Optimal application time (e.g. in the evening under dimmed light, in the morning before lighting switches on)
- Number of recommended repeat applications and intervals between them
- Notes on coverage (e.g. do not miss the undersides of leaves)
- Guidance on repeated infestations (observe active ingredient rotation)

!!! note "Multilingual texts"
    All descriptions on this page — name, application instructions, mode of action, and safety information — are displayed in your chosen language. The texts are maintained by the operator of the instance in the seed data.

---

## Mode of Action

This section explains what the product does to the pest or its environment. Understanding the mode of action helps with **resistance management**: rotate to a different active ingredient group when you have used the same mechanism several times in a row.

**Examples of modes of action:**

- **Azadirachtin (neem)**: Inhibits moulting and reproduction of larvae; adults are not killed directly, but stop feeding and starve.
- **Pyrethrins**: Block sodium channels in the nervous system, causing immediate paralysis; break down quickly in UV light.
- **Spinosad**: Over-activates acetylcholine receptors, causing paralysis and death; works primarily on feeding insects.
- **Predatory mites (*Phytoseiulus persimilis*)**: Natural predators that feed on spider mite eggs and adults; no chemical active ingredient, no pre-harvest interval.

!!! warning "Resistance management — active ingredient rotation"
    Do not use the same product or active ingredient group more than three times within 90 days. Kamerplanter warns you automatically as you approach the limit. See the [IPM system for details on resistance management](pest-management.md).

---

## Safety Information

This section brings together all relevant warnings for safe handling.

### Personal Protective Measures

- Wear the protective equipment listed in the fact sheet (gloves, respirator, safety goggles)
- Wash hands and exposed skin thoroughly after handling the product
- Do not eat, drink, or smoke while applying
- Change clothing after applying chemical products

### Protecting Bees and Beneficial Insects

!!! danger "Avoid flowering plants — protect bees"
    Chemical products and many biological ones (especially pyrethrin-based formulations) are hazardous to bees and other pollinating insects. **Never** apply them during flowering or near flowering plants. Prefer the evening or night when bees are not flying.

- **Beneficial insects**: If you have released beneficials, do not apply chemical or pyrethrin-based biological products. Wait at least 48–72 hours after the last spray before releasing beneficials.
- **Water and soil**: Prevent the product from entering water bodies or drains. For outdoor use: observe required buffer distances to water bodies.

### Disposal

- Dispose of unused product and containers according to local regulations (not in household waste)
- Clean application equipment thoroughly after use

---

## Controls

This section lists all pests and diseases for which this treatment is recommended in the master data.

### Pests

Click the name of a pest to navigate to the [pest detail page](pest-detail.md) with its fact sheet, reference images, and all control measures for that pest.

| Pest | Efficacy | Notes |
|------|---------|-------|
| Spider mites | High | Larvae and adults; eggs often less susceptible |
| Aphids | High | All developmental stages |
| Thrips | Medium | Larvae more susceptible than adults |
| Fungus gnats (larvae) | High | Larvae in substrate; adults barely affected |

!!! note "Table is pest-specific"
    The actual table in the user interface shows only the pests that are linked to this treatment in the master data — not the example table above.

### Diseases

If the product also controls fungal or bacterial diseases, they appear here in a separate list (e.g. powdery mildew for copper-based products).

---

## Frequently Asked Questions

??? question "What is the difference between a biological and a chemical product?"
    **Biological products** contain natural active substances (e.g. azadirachtin from neem seeds) or living organisms (beneficial insects). They generally break down faster and have shorter pre-harvest intervals. **Chemical products** are synthetic, often with a broader spectrum of activity, but carry longer intervals and a higher resistance risk. Beneficial insects are a special category: they have no pre-harvest interval.

??? question "Can I use the same product multiple times in a row?"
    Kamerplanter warns you when you apply the same product (or the same active ingredient) more than three times within 90 days. To avoid resistance, rotate to a different active ingredient group. The recommendation is: at least two treatment cycles with a different mechanism before returning to the original product.

??? question "Why is there no pre-harvest interval shown for some products?"
    Some measures carry no interval: beneficial insect releases, mechanical measures (e.g. washing off, removing leaves), and cultural measures (e.g. quarantine). In these cases the interval is set to 0 days, and Kamerplanter does not block any harvest.

??? question "Where do the descriptions on the detail page come from?"
    The texts are maintained by the operator of the Kamerplanter instance in the seed data and are multilingual (German and English). You see the texts in your chosen language.

??? question "I cannot find a product in the list — what can I do?"
    The treatment list only contains products that have been added by the operator. If a product is missing, you can enter it manually as free text when recording a treatment application.

---

## See Also

- [Integrated Pest Management (IPM)](pest-management.md) — record treatments, monitor pre-harvest intervals, resistance management
- [Pest Detail Page](pest-detail.md) — navigate from a control measure back to the pest
- [Pest Detection by Photo](pest-detection.md) — upload a photo and get an assessment
- [Harvest](harvest.md) — how pre-harvest intervals affect harvesting
