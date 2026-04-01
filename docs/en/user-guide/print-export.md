# Print Views & Export

Kamerplanter lets you export key care data as print-ready PDFs. Whether it is a nutrient plan for the grow room, a care checklist for your daily rounds or info cards for every pot — printed materials help wherever a smartphone is impractical or unwanted.

---

## Prerequisites

- You are logged in as a member of a tenant (role `viewer`, `grower`, or `admin`)
- For nutrient plan export: at least one nutrient plan created (→ [Fertilization Logic](fertilization.md))
- For the care checklist: at least one plant with an active care profile (→ [Care Reminders](care-reminders.md))
- For plant info cards: at least one plant instance (→ [Planting Runs](planting-runs.md))

---

## Printing a Nutrient Plan

The nutrient plan PDF gives you a complete overview of all phases of your mixing plan: which products to use, how many millilitres per litre of water to measure out, the order in which to mix them, and what EC and pH the finished solution should reach.

### Step 1: Open the Nutrient Plan

1. Navigate to **Fertilization Logic** → **Nutrient Plans** in the menu.
2. Click the name of the plan you want to print.
3. The plan detail page opens.

### Step 2: Generate the PDF

1. Click the **printer icon** in the upper toolbar.
2. The download starts automatically — your browser saves the PDF file.

### Step 3: Choose a Language (Optional)

The PDF is generated in German by default. If you need an English version, append `?locale=en` to the download URL or select "English" in the dialog.

### What Does the Nutrient Plan PDF Contain?

| Section | Content |
|---------|---------|
| Header | Plan name, creation date, tenant |
| Phase table | Phase, target EC, target pH, NPK ratio |
| Mixing instructions | Per phase: product, ml per litre, mixing order |
| Water configuration | Base EC of tap water, RO fraction in % |
| Notes | CalMag correction recommendation, flushing protocol |

!!! tip "Tip: Hang it in the grow room"
    Laminate the PDF and hang it next to your mixing station. All mixing information is within reach without using a smartphone in a humid environment.

!!! warning "Observe mixing safety"
    The PDF shows the mixing order that prevents CalMag precipitation (CalMag always before sulphates). Do not deviate from this order.

---

## Printing a Care Checklist

The care checklist exports all due care tasks for a chosen day as a printable PDF with tick boxes. Ideal for the morning round through a greenhouse, garden or home.

### Step 1: Open the Care Dashboard

1. Navigate to **Care Reminders** → **Dashboard** in the menu.
2. You will see all currently due and overdue tasks.

### Step 2: Export the Checklist

1. Click the **printer icon** in the upper toolbar.
2. Optionally: choose a different date in the dialog that appears (default: today).
3. Click **Create PDF**.
4. The download starts automatically.

### What Does the Care Checklist Contain?

Tasks are grouped by urgency:

| Group | Description |
|-------|-------------|
| Overdue | Tasks that should have been completed before the selected date |
| Due today | Tasks due on the selected date |
| Coming up | Tasks due within the next three days (preview) |

Each row shows the plant name, location, the care action due, and an empty tick box to check off by hand. Space for handwritten notes is provided below each plant entry.

!!! example "Example: Checklist for a holiday stand-in"
    Before going on holiday, print the checklist for each day of your absence (multiple prints with different dates). Staple the sheets together — your stand-in immediately has a clear daily task list.

---

## Printing Plant Info Cards

Plant info cards are compact cards containing a QR code that links directly to the plant in the app. You can choose which information appears on each card and which print layout to use.

### What Is the QR Code on the Card?

Every printed card contains a QR code. Scanning it with a smartphone camera opens the plant's detail page in Kamerplanter directly. This allows you to look up the plant's current phase, when it was last watered, and which tasks are pending — right in the greenhouse or garden.

!!! note "Note: App access required"
    The QR code links to a URL in your Kamerplanter instance. Opening it requires an active login in the app on the scanning device.

### Single Plant: Print One Info Card

1. Open a plant under **Planting Runs** → plant instance → detail view.
2. Click the **QR code icon** in the toolbar.
3. The configuration dialog opens.

### Multiple Plants: Batch Print

1. Navigate to the plant list under **Planting Runs** → **All Plants**.
2. Check the tick boxes next to the plants you want.
3. Click **Print Labels** (QR code icon) in the toolbar.
4. The configuration dialog opens with all selected plants.

### Configuration Dialog

The dialog has four sections:

#### 1. Plant Selection

This shows the selected plants. You can add further plants or remove individual ones from the selection.

#### 2. Choose Fields

Select which information should be printed on each card:

| Field | Default | Description |
|-------|---------|-------------|
| Plant name | On | Display name or cultivar name |
| Scientific name | On | Botanical name in italics |
| Genus / Family | Off | Taxonomic classification |
| Planting date | On | Date the plant was started |
| Current phase | Off | e.g. Vegetative, Flowering |
| Location | Off | Room, zone or slot label |
| Cultivar | Off | Cultivar name if stored |
| Short note | Off | Free text, e.g. "No lime" or "Water from below" |
| QR code | Always on | Cannot be deselected |

#### 3. Choose a Layout

| Layout | Cards per sheet | Recommended for |
|--------|----------------|-----------------|
| Single card (A6) | 1 | Plant stakes, laminated cards |
| 2×4 grid (A4) | 8 | Grow room labelling, everyday use |
| 3×3 grid (A4) | 9 | Many small cards, community gardens |

Grid layouts include crop marks at card edges for precise cutting.

!!! tip "Tip: QR code size"
    The minimum size for reliable scanning is 20 × 20 mm. On the 3×3 grid the QR code is already quite small — test-scan a printed card with your smartphone before cutting all cards apart.

#### 4. Preview and Download

The lower part of the dialog shows a schematic preview of one card with the chosen fields. Click **Download PDF** to start the export.

---

## Practical Tips

!!! tip "Laminate for the greenhouse"
    Cards used permanently in a greenhouse or outdoors should be laminated. A6 and smaller laminating pouches are inexpensive at office supply stores.

!!! tip "Weather-resistant plant stakes"
    Print on slightly heavier paper (120–160 g/m²) and insert the cards into standard plastic or metal plant stake holders available at garden centres.

!!! tip "Use the crop marks"
    Grid layouts print thin crop marks at the card edges. Use a cutting ruler and a craft knife for clean edges — scissors tend to drift slightly on long straight cuts.

---

## Frequently Asked Questions

??? question "Can I change the language of the PDF?"
    Yes. All PDFs are available in German and English. For the nutrient plan PDF and the care checklist you can select the language in the download dialog. For plant info cards, the current app interface language is used.

??? question "Which paper format does the PDF use?"
    All PDFs are optimised for A4 portrait format by default, except for the single card (A6). The paper format is fixed and cannot currently be changed. Select the correct format in your operating system's print dialog.

??? question "The QR code does not work. What can I do?"
    First check that you are logged in to Kamerplanter on your smartphone. The URL in the QR code points to your own Kamerplanter instance — if the app is not reachable (e.g. because you are operating on a local network only), the QR code cannot be opened outside that network.
    If you want to scan on the go or from home, your Kamerplanter instance must be publicly reachable or connected via VPN.

??? question "Can I add custom fields to the info cards?"
    Currently you can choose from eight predefined fields and use a free short-note text field. Fully user-defined fields are planned for a future release.

??? question "Can I also export the nutrient plan as CSV?"
    CSV export is planned. Currently only PDF export is available for nutrient plans. Via the interactive API documentation (`/docs`) you can already retrieve the raw plan data as JSON.

??? question "Are the PDFs accessible?"
    Yes. All generated PDFs include a document title tag, the language attribute, and are structured as tagged PDFs, which improves readability for screen readers.

---

## See Also

- [Fertilization Logic](fertilization.md) — Create and manage nutrient plans
- [Care Reminders](care-reminders.md) — Care profiles and due tasks
- [Planting Runs](planting-runs.md) — Manage plant instances
- [Tank Management](tanks.md) — Mix nutrient solutions
