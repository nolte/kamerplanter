# Onboarding Wizard

The onboarding wizard guides you through the initial setup of Kamerplanter. In just a few steps you set your experience level, choose a starter kit, and have your first plants in the system — without filling out a single form manually.

---

## What is a Starter Kit?

A starter kit is a pre-configured growing scenario. It bundles all the master data you need for a specific use case: plant species, cultivars, predefined growth phases, and matching nutrient plan templates.

Kamerplanter ships with nine starter kits:

| Starter Kit | Difficulty | Environment |
|-------------|:----------:|:-----------:|
| Windowsill Herbs | Beginner | Windowsill |
| Houseplant Starter | Beginner | Indoors |
| Pet-Friendly Houseplants | Beginner | Indoors |
| Balcony Tomatoes | Beginner | Balcony |
| Vegetable Bed | Intermediate | Outdoors |
| Succulents & Cacti | Beginner | Indoors |
| Mediterranean Herbs | Beginner | Outdoors / Balcony |
| Balcony Chillis | Intermediate | Balcony |
| Indoor Grow Tent | Advanced | Grow Tent |

!!! tip "Tip"
    You can launch the wizard again at any time — for example to add a second scenario or change your experience level. The link is in **Account Settings** under **Restart Onboarding Wizard**.

---

## The Five Steps at a Glance

```mermaid
flowchart LR
    A["Step 1\nExperience Level"] --> B["Step 2\nEnvironment & Goals"]
    B --> C["Step 3\nChoose Starter Kit"]
    C --> D["Step 4\nPlants & Favourites"]
    D --> E["Step 5\nSummary"]
    E --> F["Dashboard"]

    style A fill:#4CAF50,color:#fff
    style B fill:#4CAF50,color:#fff
    style C fill:#4CAF50,color:#fff
    style D fill:#4CAF50,color:#fff
    style E fill:#4CAF50,color:#fff
    style F fill:#388E3C,color:#fff
```

---

## Step 1: Choose Your Experience Level

You choose one of three levels that determines which fields and menu items are visible throughout the entire app.

| Level | Visible Features | Best For |
|-------|-----------------|----------|
| **Beginner** | Core features: plants, locations, tasks, phases | Getting started with Kamerplanter |
| **Intermediate** | Also: fertilization, tank management, sensors | Experienced plant growers |
| **Expert** | Everything: IPM, EC budgets, calibration, imports | Professional cultivation |

!!! note "Note"
    You can change your experience level at any time in **Account Settings** under **Experience Level**. You can also reveal individual fields without switching the entire level.

---

## Step 2: Environment & Goals

You briefly describe where and what you want to grow. This helps the wizard suggest matching starter kits.

- **Location type:** Windowsill, indoors, balcony, outdoor bed, greenhouse, or grow tent
- **Location name:** For example "Kitchen Window" or "South Balcony" — this name appears throughout the app

**For Intermediate and Expert users:** You can optionally enter your water quality — the EC value and pH of your tap water. This later improves the automatic calculation of nutrient solutions. You can also add these values at any time in the location settings.

---

## Step 3: Choose a Starter Kit

You see all starter kits that match your environment. Each card shows:

- **Name and short description** of the scenario
- **Difficulty level** (Beginner / Intermediate / Advanced)
- **Included plant species** with preview images
- **Toxicity warning** if any plants may be harmful to pets or children

!!! warning "Toxicity Warning"
    Starter kits that contain plants with toxicity notes are clearly marked. Read the warning before selecting such a kit.

Choose the kit that suits you best. You cannot automatically switch it after the wizard, but you can always add more plants manually.

---

## Step 4: Plants & Favourites

This step has two parts.

### Part 4a: Select Plants and Set Favourites

You see all plant species from your chosen starter kit. You can:

- **Set the plant count:** How many plants should the system create?
- **Mark favourite plants:** Click the heart icon next to a plant to mark it as a favourite

Favourites are personal shortcuts: filtered catalogues, recommendations, and later your shopping list are all oriented around your favourites.

### Part 4b: Nutrient Plan Favourites (Optional)

If you set favourites in Part 4a, the system shows you matching nutrient plans for your selected plants. You can mark one or more plans as favourites too.

!!! tip "The Fertilizer Cascade"
    When you mark a nutrient plan as a favourite, all fertilizer products it contains are automatically saved as favourites too. This means your personal fertilizer overview is immediately filtered to the products you actually need — no manual clicking required.

You can add or remove favourites at any time in the respective detail views (species, nutrient plan, fertilizer).

---

## Step 5: Summary

Before the wizard finishes, you see an overview of all entities Kamerplanter will create automatically:

- Your new location
- The created plant instances with automatically generated names (e.g. TOMATO-001, TOMATO-002)
- The planting run that groups all plants together
- Set favourites (plants, nutrient plans, fertilizers)
- First automatically generated tasks from the starter kit template

Click **Finish** to create everything. The wizard takes you directly to your dashboard.

---

## Light Mode: Onboarding Without Login

If Kamerplanter is running in Light Mode (e.g. on a Raspberry Pi or home server), the onboarding wizard starts directly when you first open the app — without a login screen, without registration.

!!! note "What is Light Mode?"
    Light Mode is an operating option for local single-user instances. It hides login, tenant management, and GDPR settings. Learn more on the [Light Mode](light-mode.md) page.

---

## Frequently Asked Questions

??? question "Can I skip the starter kit and set everything up manually?"
    Yes. On the "Choose Starter Kit" step there is an **Own Setup** option — this skips the automatic entity creation and lets you set up everything through the regular menus. This option is especially prominent if no kit matches your garden.

??? question "What happens if I no longer like the chosen kit after the wizard?"
    You can add more plants, locations, and nutrient plans at any time manually. The automatically created entities can be renamed, edited, or deleted just like any other entity in the app.

??? question "Do I have to set favourites in the wizard?"
    No. The favourite selection in Step 4 is optional. You can skip it entirely and set favourites later directly in the detail views.

??? question "Where do I find my favourites after the wizard?"
    Favourite species appear with a heart icon in the species overview. Favourite nutrient plans and fertilizers are marked with a heart icon in their respective catalogues. The filtered "Favourites only" view is available via the filter button in those lists.

??? question "Can I run the wizard more than once?"
    Yes. Via **Account Settings → Restart Onboarding Wizard** you can launch the wizard again. Each run can create an additional scenario without changing your existing plants.

---

## See Also

- [Master Data](plant-management.md) — Create plant species and cultivars manually
- [Locations & Substrates](locations-substrates.md) — Adjust your location after the wizard
- [Planting Runs](planting-runs.md) — Manage the created planting run
- [Fertilization](fertilization.md) — Nutrient plans and favourites in detail
- [Light Mode](light-mode.md) — Running Kamerplanter without login
