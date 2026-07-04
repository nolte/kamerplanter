# Integrated Pest Management (IPM)

The Integrated Pest Management (IPM) system follows a three-tier approach: prevention before monitoring, monitoring before intervention. Kamerplanter records inspection results, manages treatments with pre-harvest intervals, and warns you in time before harvest.

---

## Prerequisites

- At least one plant or an active planting run
- For pre-harvest interval tracking: treatments recorded with the product used and application date

---

## The IPM Three-Tier Model

### Tier 1: Prevention

The best pest control measure is the one you never need. Kamerplanter supports preventive measures through:

- **Location hygiene tasks** (automatically generated): cleaning the growing area, disinfecting tools
- **Crop rotation warnings**: alerts when the same plant family is placed too quickly at the same location
- **Climate monitoring**: alert when relative humidity stays persistently above 70 % rH, which promotes mould

!!! tip "Prevention pays off"
    Pests and diseases caught early can be treated with biological agents. Acting too late often means resorting to chemical treatments that trigger weeks of pre-harvest intervals.

### Tier 2: Monitoring (Inspection)

Regular inspections are the most important tool for early detection. Kamerplanter helps with planning and documentation.

### Tier 3: Intervention

When infestation is confirmed, choose the appropriate treatment. Kamerplanter tracks the pre-harvest interval and blocks the harvest if necessary.

---

## Conducting an Inspection

In the interface, an inspection is created exclusively via photo detection: open the affected plant and click **Check for Pests** — this opens the [Pest Detection dialog](pest-detection.md). If the detection suggests an infestation, the dialog offers a **Create Inspection** step: the detected pest, the photo, and an infestation level derived from the detection confidence are carried over automatically.

### Infestation Level Tiers

Every inspection is assigned one of five levels:

| Level | Description |
|-------|-------------|
| None | No signs of pests or disease |
| Low | Isolated signs, no spread |
| Medium | Visible infestation, local spread |
| High | Heavy infestation, widespread |
| Critical | Acute plant damage, immediate action required |

### Common Pests and Diseases

Click on the name of a pest to open the [pest detail page](pest-detail.md) with its fact sheet, reference images, and control measures.

**Common pests:**
- Spider mites (Tetranychus urticae)
- Aphids (Aphididae)
- Thrips (Thysanoptera)
- Fungus gnats (Sciaridae) — especially in coco and soil
- Whiteflies (Aleyrodidae)

**Common diseases:**
- Powdery mildew (various species)
- *Botrytis cinerea* (gray mold / gray rot)
- *Pythium* spp. (root rot, especially in hydroponics)
- *Fusarium* spp. (soil-borne crown and root rot fungus)

!!! info "Manual inspection without a photo — API only"
    There is currently no interface for manually creating an inspection without a photo (freely selecting a pest, infestation level, and notes). Saved inspections are also not yet viewable in a dedicated history view in the interface. Both features are already available via the API (see [For Technical Users: API Access](#for-technical-users-api-access)).

---

## Managing Treatment Products (Master Data)

Treatment products (agents/methods) are master data, reusable across all plants:

1. Navigate to **Pest Management (IPM) → Treatments**.
2. Click **Add Treatment**.

| Field | Description | Example |
|-------|-------------|---------|
| Product | Name of the agent | "Neem oil 2 %", "Spidex (Phytoseiulus)" |
| Type | Cultural, biological, chemical, mechanical | Biological |
| Active Ingredient | Main active substance | "Azadirachtin" |
| Pre-Harvest Interval (days) | Waiting period before harvest | 14 |
| Dosage | Amount and concentration | "5 ml/L" |
| Application Method | Spraying, drenching, spreading, release | Spraying |
| Protective Equipment | Recommended protective measures | Gloves, respirator |

Click on the name of a treatment to open the [treatment detail page](treatment-detail.md) with mode of action, dosage, pre-harvest interval, and safety information.

!!! info "Documenting a treatment application on a plant — API only"
    Recording a concrete application of a treatment product on a plant (application date, dosage, affected plant) cannot yet be done in the interface. The corresponding API endpoint is already usable (see [For Technical Users: API Access](#for-technical-users-api-access)). Once an entry has been created via the API, the pre-harvest interval lock takes effect automatically at harvest time (see below).

---

## Understanding and Monitoring Pre-Harvest Intervals

The **pre-harvest interval (PHI)** is the legally required waiting period between the last application of a plant protection product and harvest. It protects consumers from residues in the harvested crop.

**Where can I see an active pre-harvest interval?**

There is currently no dedicated display of active pre-harvest intervals in the plant view. The interval takes effect where it matters: if you try to create a **harvest batch** for a plant with a pre-harvest interval that has not yet expired, the system blocks the harvest with an error and states the earliest possible harvest date (pre-harvest interval lock, HTTP 422). You can also check the current status via the API (see [For Technical Users: API Access](#for-technical-users-api-access)).

!!! danger "The interval starts immediately"
    As soon as a treatment with a pre-harvest interval has been recorded for a plant, harvest of that plant is blocked until the interval has expired — regardless of whether the entry was created via the API or (in future) via an interface.

**Incorrect pre-harvest interval entry — what to do?**

There is currently no editing function for treatment applications that have already been recorded. If you made an entry by mistake, contact your operator/support team to have it corrected.

---

## Resistance Management

!!! warning "Rotate active ingredients"
    Pests develop resistance when the same active ingredient group is used too often. Kamerplanter rejects a new treatment application when you apply the same product (or the same active ingredient) more than three times within 90 days (see [Documenting a treatment application](#managing-treatment-products-master-data)).

When this warning appears:
1. Choose a product with a different mode of action.
2. Wait at least 2 treatment cycles before returning to the original product.

---

## Beneficial Insects

Beneficial organisms (e.g. *Phytoseiulus persimilis* — predatory mite — against spider mites, parasitic wasps against fungus gnats) are stored in Kamerplanter as **master data**: if photo-based pest detection recognizes a beneficial organism instead of a pest, it clearly flags this so it is not treated as a pest by mistake.

!!! warning "Not yet implemented"
    Dedicated documentation of beneficial organism **releases** (release date, quantity, location) will only arrive in a future version. For now, using beneficials can only be recorded indirectly via the [treatment product master data](#managing-treatment-products-master-data) (type "Biological", application method "Release", pre-harvest interval 0 days).

**Important when using beneficials:**
- Beneficial insects have **no pre-harvest interval** — harvests are possible at any time.
- Avoid chemical sprays after releasing beneficials, as these kill the beneficial organisms too.

---

## Analysing Infestation History at a Location

!!! warning "Not yet implemented"
    An analysis of which pests and diseases have occurred in which location area over time will only arrive in a future version. Until then, history can only be traced per plant via the pest detail pages and the IPM API.

---

## Frequently Asked Questions

??? question "What is the difference between pre-harvest interval and waiting period?"
    They describe the same thing: the minimum time that must pass between the last application of a plant protection product and harvest, so that residues have enough time to break down. Kamerplanter uses **pre-harvest interval (PHI)** as the single term throughout the interface and this documentation.

??? question "Can I record a treatment with no pre-harvest interval?"
    Yes. For treatments with no interval (e.g. beneficial insect release, mechanical removal) enter 0 days. These treatments do not block harvests.

??? question "How do I identify spider mites?"
    Spider mites are barely visible to the naked eye. Typical signs: fine silvery stippling on leaf surfaces, fine webbing on the underside of leaves. A 10× loupe is recommended for a reliable diagnosis.

??? question "I used neem oil without a stated interval — what value do I enter?"
    Neem oil as a biological agent is considered relatively safe, but a waiting period of 7–14 days is recommended. Use the value stated on your product label, or check with the manufacturer.

---

## For Technical Users: API Access

Some IPM features are already available as REST endpoints, even though the graphical interface for them is still missing. This section is aimed at technical users and self-hosters who want to connect their own integrations or scripts. An authenticated session (bearer token) is required.

| Endpoint | Purpose |
|----------|---------|
| `POST .../ipm/plants/{plant_key}/inspections` | Manually create an inspection (freely selecting pest, infestation level, and notes) |
| `GET .../ipm/plants/{plant_key}/inspections` | Retrieve a plant's saved inspections |
| `POST .../ipm/plants/{plant_key}/treatment-applications` | Document a treatment application on a plant (triggers the pre-harvest interval lock) |
| `GET .../ipm/plants/{plant_key}/harvest-safety` | Check a plant's current pre-harvest interval status |

---

## See Also

- [My Plant Doesn't Look Well — Symptom Diagnosis](plant-health-troubleshooting.md) — Narrow down a cause from a symptom
- [Pest Detail Page](pest-detail.md) — fact sheet, reference images, IPM control measures, and beneficials per pest
- [Treatment Detail Page](treatment-detail.md) — mode of action, dosage, pre-harvest interval, and safety information for a specific product
- [Pest Detection by Photo](pest-detection.md) — upload a photo and get an automated assessment
- [Harvest](harvest.md)
- [Tasks](tasks.md)
- [Locations and Substrates](locations-substrates.md)
