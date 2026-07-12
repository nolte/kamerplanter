# Terminology Glossary

The terminology glossary explains terms like VPD, EC, or the pre-harvest interval right inside the application — short, tailored to your experience level, and without leaving the app to check the documentation. The explanations come from the [AI Assistant's](ai-assistant.md) curated knowledge base and also work without logging in. <!-- REQ-035 -->

---

## Prerequisites

- Your instance operator must have AI features enabled instance-wide. If not, the glossary page is just as unreachable as the [AI Assistant](ai-assistant.md) — details under [For Technical Users / Self-Hosters](#for-technical-users-self-hosters).
- Logging in is **not** required: the glossary is purely factual knowledge with no reference to your specific plants, so it also works in anonymous [Light Mode](light-mode.md).
- If your garden (tenant) uses a cloud provider instead of a local model as its default, you additionally need your "AI processing via cloud provider" consent — see [Granting consent](ai-assistant.md#granting-consent). This doesn't apply in Light Mode, since it always processes locally.

## Browsing the glossary

### Step 1: Open the glossary

Open **Glossary** in the menu. You'll see an overview of all curated terms, grouped by categories such as **Environment & climate**, **Fertilisation**, **Watering**, **Growth phases**, **Outdoor & garden**, and **Plant protection**.

### Step 2: Select a term

Tap a term to open its full explanation. The explanation appears in the same AI envelope as the AI Assistant — with AI labeling, model name, and an expandable source list. Clicking **Back to overview** returns you to the term list.

!!! tip "Follow related terms directly"
    Below every explanation you'll find clickable chips for related terms — for example "VPD" leads to "leaf temperature" and "transpiration". Clicking one opens the next explanation directly, so you can work your way from term to term without jumping back to the overview.

## Explanations adapt to your experience level

The explanation you see is tailored to your configured [experience level](onboarding.md) (Beginner, Intermediate, Expert). As a beginner you get a simple explanation in everyday language without exact numbers; as an expert you get the same explanation with concrete value ranges — for example target EC values per growth phase or substrate-dependent notes. If you change your experience level in the account settings, explanations fetched afterward will reflect it.

!!! example "Example: the term \"EC\""
    - **Beginner:** "EC measures how many nutrients are in the water."
    - **Expert:** "Vegetative: 1.0–1.4 mS/cm, flowering: 1.4–1.8 mS/cm, depending on substrate (hydro vs. soil)."

## When the knowledge base has no matching hit

Not every term has a sufficiently relevant hit in the knowledge base. In that case, the glossary honestly shows you an editorially maintained short definition instead of an AI-generated answer, labeled "Short definition (no knowledge-base match)". This way you're never given a fabricated or unreliable answer.

## The inline question-mark icon

!!! note "Partially available: question-mark icons on other pages"
    The question-mark icon that opens the same explanation as a compact popover right next to a term has already been built as a component and works correctly wherever it's wired in. Right now, though, it doesn't yet appear on any plant, dashboard, or substrate page — rolling it out across existing views is a separate, follow-up piece of work. Until then, you can reach the same explanations through the glossary overview above. <!-- REQ-035 -->

Once the icon is wired into a page, here's how it works: clicking the small question mark next to a term opens a compact popover with the same explanation as the glossary overview — including related terms, back navigation within the popover, and its own close button. You never have to leave the page for it.

## Light Mode & anonymous use

The glossary is one of the few features that works entirely without a user account: neither the term list nor the individual explanations require a tenant or personal reference, so no consent is needed and the feature is available in [Light Mode](light-mode.md) just as it is in full mode. Light Mode always processes locally — an external cloud provider is never used. To keep the glossary usable for everyone, the number of requests per minute for anonymous use is limited; if you open many terms in quick succession, you may briefly see an error message — just wait a moment and try again.

---

## For Technical Users / Self-Hosters {#for-technical-users-self-hosters}

The glossary uses the same instance-wide AI toggle as the [AI Assistant](ai-assistant.md#for-technical-users-self-hosters) (`AI_FEATURES_ENABLED=true`), but **not** the additional garden-level toggle (stage 2) — it needs no tenant-level AI activation because it doesn't use any plant data. Details on the environment variable are in [Environment Variables — AI Assistant](../reference/environment-variables.md#ki-assistent).

If your garden (tenant) uses a cloud provider as its default provider, the regular "AI processing via cloud provider" consent check (`ai_cloud_processing`) still applies before a request reaches the cloud provider — see [Privacy & GDPR](privacy.md#for-technical-users-self-hosters). If consent is missing or the associated user can't be determined unambiguously, the request is rejected outright rather than silently redirected to a local model.

Like the AI Assistant, every glossary call is logged without any plant or account data included in the request sent to the knowledge base.

---

## Frequently Asked Questions

??? question "Do I need to be logged in to use the glossary?"
    No. The glossary works in both full mode and anonymous Light Mode without logging in — provided the operator has enabled AI features instance-wide.

??? question "Why do I sometimes see 'Short definition (no knowledge-base match)' instead of a detailed explanation?"
    That means the knowledge base didn't find a sufficiently relevant match for this term. Instead of making up an unreliable AI answer, the glossary then shows you a short, editorially reviewed definition.

??? question "Why does the explanation change when I switch my experience level?"
    The explanation is generated to match your configured experience level — beginners get everyday language, experts get concrete value ranges. This applies to explanations fetched after the level change.

??? question "Why don't I see the question-mark icon next to terms on other pages yet?"
    Rolling it out to existing pages (plant detail page, dashboard, substrate editor, and more) isn't finished yet. Until then, you can find the same explanations via the [glossary overview](#browsing-the-glossary).

## See Also

- [AI Assistant](ai-assistant.md)
- [Experience levels in the onboarding wizard](onboarding.md)
- [Light Mode](light-mode.md)
- [Privacy & GDPR](privacy.md)
- [Static terminology reference (documentation)](../reference/glossary.md)
