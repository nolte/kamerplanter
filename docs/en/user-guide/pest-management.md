# Integrated Pest Management (IPM)

The IPM system follows a three-tier approach: prevention before monitoring, monitoring before intervention. Kamerplanter records inspection results, manages treatments with pre-harvest intervals, and warns you in time before harvest.

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

### Step 1: Start an Inspection

1. Navigate to **Pest Management (IPM)** in the navigation, or open a plant and switch to the **Pest Management** tab.
2. Click **New Inspection**.

### Step 2: Assess Infestation Level

Rate the infestation level:

| Level | Description |
|-------|-------------|
| None | No signs of pests or disease |
| Low | Isolated signs, no spread |
| Medium | Visible infestation, local spread |
| High | Heavy infestation, widespread |
| Critical | Acute plant damage, immediate action required |

### Step 3: Document Pests or Diseases

If you have found infestation, select from the list:

**Common pests:**
- Spider mites (Tetranychus urticae)
- Aphids (Aphididae)
- Thrips (Thysanoptera)
- Fungus gnats (Sciaridae) — especially in coco and soil
- Whiteflies (Aleyrodidae)

**Common diseases:**
- Powdery mildew (various species)
- Botrytis (grey mould)
- Pythium (root rot, in hydroponics)
- Fusarium (soil fungus)

If the pest or disease is not on the list you can enter it manually.

### Step 4: Add Photos (optional)

Add photos of the affected areas. This helps with monitoring over time and later diagnosis.

### Step 5: Save the Inspection

The inspection is saved in the plant's inspection history and is visible in the calendar.

---

## Recording a Treatment

### Step 1: Add a Treatment

1. Navigate to **Pest Management (IPM) → Treatments**, or click **Initiate Treatment** in an inspection.
2. Click **Add Treatment**.

### Step 2: Select Treatment Agent and Method

| Field | Description | Example |
|-------|-------------|---------|
| Product | Name of the agent used | "Neem oil 2 %", "Spidex (Phytoseiulus)" |
| Type | Cultural, biological, chemical, mechanical | Biological |
| Active Ingredient | Main active substance | "Azadirachtin" |
| Pre-Harvest Interval (days) | Waiting period before harvest | 14 |
| Dosage | Amount and concentration | "5 ml/L" |
| Application Method | Spraying, drenching, spreading, release | Spraying |

### Step 3: Document the Application

Enter the application date and the treated plants. The system calculates the earliest possible harvest date automatically.

!!! danger "The interval starts immediately"
    As soon as you record a treatment with a pre-harvest interval, harvest of the affected plants is blocked until the interval has expired. Kamerplanter displays the earliest possible harvest date prominently.

---

## Understanding and Monitoring Pre-Harvest Intervals

The **pre-harvest interval (PHI)** is the legally required waiting period between the last application of a plant protection product and harvest. It protects consumers from residues in the harvested crop.

**Where can I see active pre-harvest intervals?**

1. In the plant detail view under the **Pest Management** tab — a red notice appears when an interval is active
2. In the task overview — an automatically created task "Harvest possible from [date]"
3. In the calendar — interval expiry shown as an event

**Interval active in error — what to do?**

If you entered a treatment by mistake, open it and correct the application date. If you entered the wrong product, use the comment function to document the error.

---

## Resistance Management

!!! warning "Rotate active ingredients"
    Pests develop resistance when the same active ingredient group is used too often. Kamerplanter warns you when you apply the same product (or the same active ingredient) more than three times within 90 days.

When a warning appears:
1. Open the treatment history of the plant.
2. Switch to a product with a different mode of action.
3. Wait at least 2 treatment cycles before returning to the original product.

---

## Releasing Beneficial Insects

For biological control you can document beneficial organism releases:

1. Navigate to **Pest Management → Beneficials**.
2. Click **Beneficial Released**.
3. Select the organism from the list (e.g. predatory mites for spider mites, parasitic wasps for fungus gnats).
4. Enter release date, quantity, and location.

**Important when using beneficials:**
- Beneficial insects have **no pre-harvest interval** — harvests are possible at any time.
- Avoid chemical sprays after releasing beneficials, as these kill the beneficial organisms too.

---

## Analysing Infestation History at a Location

Under **Pest Management → Infestation History** you see which pests and diseases have occurred in which area. This helps with planning preventive measures for the next cycle.

---

## Frequently Asked Questions

??? question "What is the difference between pre-harvest interval and waiting period?"
    In Kamerplanter, **pre-harvest interval** corresponds to the English term "PHI" — the minimum time between last application and harvest. Both terms describe the same concept.

??? question "Can I record a treatment with no pre-harvest interval?"
    Yes. For treatments with no interval (e.g. beneficial insect release, mechanical removal) enter 0 days. These treatments do not block harvests.

??? question "How do I identify spider mites?"
    Spider mites are barely visible to the naked eye. Typical signs: fine silvery stippling on leaf surfaces, fine webbing on the underside of leaves. A 10× loupe is recommended for a reliable diagnosis.

??? question "I used neem oil without a stated interval — what value do I enter?"
    Neem oil as a biological agent is considered relatively safe, but a waiting period of 7–14 days is recommended. Use the value stated on your product label, or check with the manufacturer.

---

## See Also

- [Harvest](harvest.md)
- [Tasks](tasks.md)
- [Locations and Substrates](locations-substrates.md)
