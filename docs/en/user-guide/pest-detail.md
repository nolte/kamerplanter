# Pest Detail Page

The pest detail page gives you everything you need to know about a specific pest: How do you identify it? Which plants are at risk? And how do you control it safely and effectively — from natural methods to chemical treatment as a last resort?

You reach the detail page via the **pest list** (Navigation: Pest Management → Pests → click a row) or via the **More about this pest** link in the [pest detection dialog](pest-detection.md) after an automated detection has produced a match.

---

## Prerequisites

- Authenticated user account (not Light mode)
- At least one plant or an active planting run (to create an inspection directly from the detail page)

---

## Fact Sheet

The fact sheet at the top of the page summarises the most important information about the pest in a quick-read overview:

| Field | Description |
|-------|-------------|
| **Damage pattern / Symptoms** | What does your plant look like when this pest is active? Typical signs include webbing, suction marks, honeydew (sticky residue), wilting, discolouration, or feeding damage |
| **Affected plant parts** | Leaves, roots, stems, flowers — different pests prefer different areas of the plant |
| **Typical host plants** | Which plant species or families are most commonly affected? Helps you assess whether your plant is at risk |
| **Life cycle** | A brief description of the developmental stages (egg → larva/nymph → adult) and how quickly an infestation can spread |
| **Optimal temperature / humidity** | Under which conditions does the pest multiply fastest? This helps you deliberately adjust the growing environment |
| **Severity** | Low / Medium / High / Critical — an assessment of how quickly you need to act when you discover this pest |

!!! tip "Interpreting severity correctly"
    Severity describes the damage potential of an uncontrolled infestation — not your current infestation level. Even a pest rated "Low" can become a serious problem if neglected.

---

## Reference Image Gallery

Below the fact sheet, the gallery shows curated photos of the pest and of typical damage patterns. Images come from licensed sources and are maintained by the operator of the Kamerplanter instance.

!!! note "Empty at first — grows with the system"
    A freshly set up instance does not yet have any reference images. The operator populates the gallery gradually — starting with the most common pests. If images are missing, you will see the message "No reference images available yet".

**What the images show:**

- **The pest itself** (adult, larvae, eggs) — so you can identify it directly
- **Damage pattern / symptoms** — so you can see what your plant looks like when the pest is already active
- **Typical locations on the plant** — where to look on the leaf, on the underside of leaves, or at shoot tips

!!! tip "Compare several photos"
    Pests can look very different depending on their developmental stage. Zoom into the images to spot even tiny details, and compare the larval and adult stages side by side.

### Contribute your own photos

You can add your own photos for a pest — either by **uploading a file** or by photographing the pest directly with your **camera** (smartphone or webcam). In the gallery, click **"Contribute a photo"**.

- **Instantly visible, private:** Your photos appear in your gallery immediately and are visible only to your garden (tenant). You can delete your own photos at any time (trash icon on the image).
- **Privacy:** Location data (EXIF) is removed automatically on upload; the images are stored securely in object storage.
- **Optionally global:** A platform admin can approve especially good shots for all users — such images then carry the **"Global"** badge.
- **Keep from recognition:** If you identified the pest via [photo recognition](pest-detection.md), you can keep the captured photo straight from the recognition dialog via **"Add this photo to the gallery"**. (Otherwise the recognition photo is not stored for privacy reasons — it only enters the gallery when you explicitly choose to.)

In addition, your **inspection photos** appear in the gallery automatically: photos you took during an [inspection](pest-management.md) where you recorded this pest as detected. They are marked **"From inspection"**, read-only (editable only via the inspection itself) and visible only to your garden.

!!! note "Anonymous mode"
    Contributing your own images is not available in anonymous (light) mode, because there is no personal garden.

---

## Control Measures by IPM Hierarchy

[Integrated pest management (IPM)](pest-management.md) arranges measures according to the principle: prevent first, then monitor, intervene only as a last resort — and always as gently as possible.

The control measures on the detail page are therefore organised into four groups. Always start at the top and only move to the next group if the previous measures prove insufficient.

Below each treatment name there is a short explanation of **how the measure works** — so you grasp not just the name but also the benefit at a glance. Click the **name of a treatment** in the control measures list to open the [treatment detail page](treatment-detail.md), where you will find the full mode of action, dosage, pre-harvest interval, and safety information for that specific product.

### 1. Cultural Measures

These are adjustments to your cultivation and care practices that require no additional product:

- Quarantine new plants (keep them separate for 2 weeks before introducing them to your collection)
- Remove infested plant parts immediately and dispose of them in the household waste (do not compost)
- Adjust the growing environment: change temperature or humidity so that the pest faces less favourable conditions
- Disinfect tools and pots before reuse

### 2. Biological Measures

Biological agents rely on natural active substances or living organisms:

- **Beneficial insects** (e.g. predatory mites against spider mites, parasitic wasps against fungus gnats) — they also appear in the [Suitable Beneficials](#suitable-beneficials) section below
- **Neem oil** (active ingredient azadirachtin) — inhibits feeding and reproduction; more effective against larvae than adults
- **Pyrethrin extracts** (from chrysanthemums) — break down quickly, but are also harmful to beneficial insects; do not apply together with a beneficial release

!!! warning "Biological does not mean harmless"
    Biological products carry a pre-harvest interval (PHI), even if it is usually shorter than for chemical products. Always record the treatment in the [IPM system](pest-management.md) so that Kamerplanter can track the interval.

### 3. Mechanical Measures

Physical methods that require no active ingredient:

- Wash pests off with water (direct a water jet against the undersides of leaves)
- Use yellow or blue sticky traps for monitoring and mass trapping
- Cut off and remove individual leaves or shoots
- Use insect-exclusion netting for outdoor growing

### 4. Chemical Measures (last resort)

Chemical plant protection products are effective but must be used with caution:

!!! danger "Chemical products — last resort only"
    Chemical products can promote resistance, kill beneficial insects, and trigger long pre-harvest intervals. Only use them after cultural, biological, and mechanical measures have proven insufficient.

- Before purchasing, check that the product is approved for your crop and application area (greenhouse, indoor, outdoor)
- Follow the **active ingredient rotation / resistance management** schedule: Kamerplanter warns you when you apply the same active ingredient too frequently (see [IPM system](pest-management.md) for details)
- Always record the treatment with active ingredient and pre-harvest interval in the IPM system

**Pre-harvest interval (PHI)** specifies how many days you must wait after the last treatment before harvesting. Kamerplanter calculates the earliest possible harvest date automatically and displays a warning when the interval is still running.

!!! note "Tooltip in the UI"
    In the user interface, hovering over the term "Pre-harvest interval" shows a tooltip that explains the definition directly — no need to look it up.

---

## Suitable Beneficials {#suitable-beneficials}

Beneficial insects (or beneficial organisms) are natural predators or parasites of the pest. They are the cornerstone of biological control and trigger **no pre-harvest interval**.

!!! warning "No spraying before releasing beneficials"
    Chemical and many biological sprays also kill beneficial organisms. Wait at least 48–72 hours after spraying before releasing beneficials — or choose one approach and stick with it.

The beneficials listed on the detail page are specifically recommended for this pest. Each entry shows:

| Information | Description |
|------------|-------------|
| **Name** | Common name and species name of the beneficial organism |
| **Mode of action** | How does it control the pest? (predation, parasitism, competition) |
| **Operating temperature** | In which temperature range is the beneficial active and able to reproduce? |
| **Sourcing note** | Beneficial organisms are living creatures you can order from specialist retailers or specialist suppliers — the operator can optionally add sourcing notes here |

To document a beneficial release, navigate to **Pest Management → Beneficials** and click **Beneficial Released**.

---

## Prevention & Monitoring

This section at the bottom of the page brings together tips to help you prevent a recurrence and explains what to look out for during routine checks.

### Prevention

- Hygiene routine: regular cleaning of the growing area, disinfection of scissors and tools
- Quarantine for new arrivals
- Climate optimisation: many pests thrive in warm, dry conditions (spider mites) or warm, humid conditions (fungus gnats); adjust the vapour pressure deficit (VPD) and substrate moisture deliberately
- Plan crop rotation when changing pots or beds

### Monitoring

Regular inspections are the best form of early detection. Kamerplanter automatically generates inspection tasks — you can also create a [manual pest inspection](pest-management.md) at any time.

!!! tip "Pest detection scan as a complement"
    [Pest detection by photo](pest-detection.md) is not a substitute for your own visual inspection, but a useful first pointer. Use it alongside your routine checks — especially if you notice something unusual on a leaf.

---

## Create an Inspection Directly

At the top of the detail page you will find a **Create Inspection** button. This opens the inspection form with the current pest already pre-filled — you do not have to select it manually from the pest list.

---

## Frequently Asked Questions

??? question "Where do the reference images in the gallery come from?"
    Reference images are sourced and curated by the operator of the Kamerplanter instance from licensed sources. Images are automatically collected from GBIF and Wikimedia under CC0 and CC-BY licences; the platform admin then reviews them visually and deselects any unsuitable ones. As a regular user, you only see active, reviewed images.

??? question "What is the difference between a chemical and a biological product?"
    **Biological products** contain natural active substances (e.g. azadirachtin from neem seeds) or living organisms (beneficial insects). They generally break down faster and have shorter pre-harvest intervals, but can still affect other beneficial organisms. **Chemical products** are synthetic and often have a broader spectrum of activity, but carry longer pre-harvest intervals and a higher resistance risk.

??? question "Why are some control measures not shown?"
    Not every measure is relevant for every pest. The detail page only shows measures that are stored in the master data for this specific pest. If a group is missing, there simply is no recommendation for that pest in that category.

??? question "The gallery is empty — is that a bug?"
    No. A freshly set up instance does not yet contain any reference images. The operator populates the gallery gradually. You can use all other features of the detail page (fact sheet, control measures, beneficials) immediately.

??? question "Can I upload reference images myself?"
    Adding reference images is reserved for the platform admin. As a regular user, you can save photos of your own plants in the [plant photo gallery](plant-photos.md).

??? question "What exactly is a pre-harvest interval?"
    The **pre-harvest interval (PHI)** is the mandatory waiting period between the last application of a plant protection product and harvest. It protects you and others from residues in the harvested crop. Kamerplanter monitors the interval automatically and blocks the harvest for as long as it is running.

---

## See Also

- [Integrated Pest Management (IPM)](pest-management.md) — create inspections, record treatments, monitor pre-harvest intervals
- [Treatment Detail Page](treatment-detail.md) — mode of action, dosage, pre-harvest interval, and safety information for a specific product
- [Pest Detection by Photo](pest-detection.md) — upload a photo and get an assessment
- [Harvest](harvest.md) — how pre-harvest intervals affect harvesting
- [Actuator Control](actuator-control.md) — optimise growing conditions to prevent pest infestation
