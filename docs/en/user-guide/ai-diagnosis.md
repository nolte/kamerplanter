# AI Diagnosis

With AI Diagnosis you describe your plant's symptoms through a short, guided assistant — instead of writing a free-form chat question, you pick from a curated catalogue. You receive the **three most likely causes** with confidence, an explanation, and recommended actions, each linked to the matching entry in the [Pest Management (IPM)](pest-management.md) system.

!!! note "Partially available"
    AI Diagnosis is usable as its own page **AI Diagnosis** (`/diagnose`): you select symptoms from a curated catalogue, optionally add a note, and get an AI-generated top-3 assessment linked to the pest management system. Currently **not** implemented are a link to a specific plant or planting run, a photo upload directly inside the assistant, and a saved diagnosis history — every session is stateless and is not retained after the answer. There's also no dedicated menu entry yet. The following sections describe today's state in the present tense. <!-- REQ-036 -->

!!! warning "An assessment — not a definitive diagnosis"
    Every answer is an AI-generated assessment based on the symptoms you selected, not a definitive diagnosis. Please verify the finding yourself before starting any treatment. AI Diagnosis **never** triggers a treatment automatically, and any existing pre-harvest interval gate (the legally required waiting period between treatment and harvest) remains active regardless.

!!! note "Full mode and consent required"
    AI Diagnosis is only available to signed-in users. In **[Light Mode](light-mode.md)** (anonymous access) the feature is unavailable. In addition, the analysis — just like the [AI Assistant](ai-assistant.md) — needs all three approval levels (operator, your garden/tenant, your consent "AI access to your plant data"). If any of these is missing, you can still fill out the assistant up to the last step, but the analysis itself then fails with a generic error message (see [When the analysis fails](#when-the-analysis-fails)).

---

## Prerequisites

- Signed-in user account (not Light Mode)
- AI features must be enabled instance-wide and for your garden (tenant)
- Your consent "AI access to your plant data" (`ai_tenant_data_access`) must be granted — see [AI Assistant: Granting consent](ai-assistant.md#granting-consent) for details

---

## What the AI Diagnosis Does

AI Diagnosis is a **structured, symptom-based** path to an assessment — you describe what you see on your plant instead of formulating an open question. That lowers the jargon barrier and gives the AI a clearly scoped input format.

!!! info "How this differs from photo-based recognition"
    AI Diagnosis is **text-based**: you select symptoms, not images. That makes it different from Kamerplanter's photo-based features:

    - [Identify Plant by Photo](plant-identification.md) determines the **species** of an unknown plant from a photo.
    - [Pest Detection by Photo](pest-detection.md) detects pests and typical damage patterns from a photo of an already-known plant.

    The context step of AI Diagnosis (see below) includes a hint pointing to the existing photo recognition feature, in case a photo could provide additional context — but AI Diagnosis itself does not accept or evaluate a photo.

---

## Getting Started

You currently reach AI Diagnosis directly at the address `/diagnose` in your browser — there's no dedicated entry in the side menu yet.

The assistant guides you through three steps: **Symptoms**, **Context**, and **Result**. A progress indicator at the top shows which step you're on.

### Step 1: Select Symptoms

The catalogue contains over 30 curated symptoms, grouped by category (for example "Leaf discoloration", "Visible pests", or "Growth anomaly"). Check every symptom that applies to your plant — multiple selections are possible.

!!! tip "Preview possible causes"
    Next to many symptoms, a small info icon shows a short hint about common causes when tapped or hovered — that helps you pick the right symptoms even before you submit.

Once you've selected at least one symptom, the **Next** button becomes active.

### Step 2: Add Context (Optional)

In this step you can optionally leave a note in the free-text field (up to 2,000 characters) — for example about location, watering habits, or when the symptom first appeared.

!!! note "Your note is not sent verbatim"
    For privacy reasons, your free text is **not** forwarded to the language model. The AI only receives the neutral hint that you added a note — your text itself stays with you.

Below that you'll find a hint with a link to the existing photo recognition feature, in case a photo could provide additional context (see [How this differs from photo-based recognition](#what-the-ai-diagnosis-does) above).

Click **Start Diagnosis** to trigger the analysis — or **Back** to change your symptom selection.

### Step 3: Read the Result

After a few seconds, the **three most likely causes** appear, sorted by descending confidence.

---

## Understanding the Result

Each of the three diagnosis cards shows:

- **Rank and name** of the suspected cause, supplemented with the scientific name when botanically nameable
- **Confidence** as a percentage, color-coded (green = high, blue = medium, orange = low)
- **Explanation** of why the AI arrived at this assessment
- **Recommended actions** as a bulleted list

If the system finds a match in the pest master data, the card additionally links directly to the matching [pest detail page](pest-detail.md) and to suggested treatments. If a suggested treatment carries a pre-harvest interval (the legally required waiting period between treatment and harvest, see [Glossary](../reference/glossary.md#pre-harvest-interval-phi)), that's clearly marked on the treatment chip with a warning icon and the number of days.

The answer is also embedded in the shared envelope used for all AI answers — AI labeling, expandable source references from the knowledge base, and indicators showing whether your plant data or a cloud provider were used. Details are described under [AI Assistant: Transparency](ai-assistant.md#transparency-how-to-recognize-an-ai-answer).

Use the **New Diagnosis** button to restart the assistant with an empty symptom selection.

### When the Analysis Fails {#when-the-analysis-fails}

If the analysis fails, the assistant shows a generic error message regardless of the exact cause — whether AI features aren't enabled, your consent is missing, the knowledge base is unreachable, or the AI didn't produce a usable result. In that case, first check the three approval levels under [AI Assistant](ai-assistant.md#how-the-ai-assistant-is-structured-three-stage-toggle) and try again afterward.

---

## From Diagnosis to Treatment

If a diagnosis points to a known pest, you can go directly via the **View pest details** link to the [pest detail page](pest-detail.md) and create a pest inspection from there in the [Pest Management (IPM)](pest-management.md) system. If a suggested treatment carries a pre-harvest interval, it's honored on the [treatment detail page](treatment-detail.md) — the system never triggers a treatment automatically; the decision is always yours.

---

## Frequently Asked Questions

??? question "Why can't I find AI Diagnosis in the side menu?"
    The feature doesn't have its own menu entry yet. You reach it directly at the address `/diagnose`.

??? question "Can I attach a photo to the diagnosis?"
    Not directly inside the assistant. The context step includes a link to the existing photo recognition features — use [Pest Detection by Photo](pest-detection.md) for pest detection, or [Identify Plant by Photo](plant-identification.md) for pure species identification.

??? question "Is this the same as the planned photo diagnosis for diseases and nutrient deficiencies?"
    No. AI Diagnosis is symptom- and text-based and usable today. A complementary, photo-based condition diagnosis specifically for diseases and nutrient deficiencies is planned as its own feature — the API already exists but is not yet wired into a user interface — see [My Plant Doesn't Look Well — What Now?](plant-health-troubleshooting.md#planned-extension-photo-diagnosis-for-diseases-and-deficiencies).

??? question "Why do I always get a generic error message when something goes wrong?"
    The assistant doesn't yet distinguish between the possible failure causes (missing approval, missing consent, an unreachable knowledge base, or an unusable AI result) — the same generic message appears in all cases. If in doubt, check the [AI Assistant's approval levels](ai-assistant.md#how-the-ai-assistant-is-structured-three-stage-toggle).

??? question "Is my diagnosis saved so I can find it again later?"
    No. Every session is stateless: only an anonymized, hashed entry is written to the internal AI audit log (without the plain text of your symptoms or notes), but there is no diagnosis history you could review later.

---

## See Also

- [Pest Management (IPM)](pest-management.md) — inspections, treatments, pre-harvest intervals
- [Pest Detail Page](pest-detail.md) — profile, reference images, countermeasures
- [Treatment Detail Page](treatment-detail.md) — details on suggested treatments
- [My Plant Doesn't Look Well — What Now?](plant-health-troubleshooting.md) — symptom lookup table as a first assessment
- [Pest Detection by Photo](pest-detection.md) — image-based pest detection
- [Identify Plant by Photo](plant-identification.md) — species identification for unknown plants
- [AI Assistant](ai-assistant.md) — approval levels, consents, and transparency labeling
- [Privacy & GDPR](privacy.md) — consents and data subject rights
