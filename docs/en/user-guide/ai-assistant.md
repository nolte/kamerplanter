# AI Assistant

!!! note "Partially available"
    The AI Assistant is usable as its own page **AI Assistant** (`/ki-assistent`): knowledge questions and a context-free chat already work. The **tip cards**, **tip of the day**, and **"why?" buttons** described further down on this page have already been built as frontend components, but are not yet wired into any plant, planting-run, or task page — they don't appear anywhere yet. The next two sections describe today's state in the present tense; the sections after that describe the **planned behavior** in future tense. <!-- REQ-031 -->

The AI Assistant answers knowledge questions about plant care based on a curated knowledge base — clearly labeled as AI-generated, with source references, and without sending your personal data to a language model.

---

## Asking knowledge questions

Open **AI Assistant** in the menu. Enter your question in the text field — for example "What is VPD and why does it matter?" — and click **Ask** (or submit with Ctrl/Cmd + Enter). The answer appears below, with AI labeling and expandable sources.

These knowledge questions are **purely factual** — they don't relate to your specific plants, only to general plant knowledge from the knowledge base. That's why no consent is required, and the feature is also available in anonymous [Light Mode](light-mode.md) without logging in.

!!! example "Example questions"
    - "What is VPD?"
    - "How do I lower the pH of the nutrient solution?"
    - "What is a pre-harvest interval?"

## Context-aware chat

In full mode (logged in), the **Open chat** button at the top of the page opens a chat panel. Your message is answered word by word as it streams in; every answer appears in the same AI envelope as the knowledge questions. A cancel button stops an answer that's still streaming.

!!! warning "Requires activation by an administrator"
    Unlike the plain knowledge question, chat uses the context of your garden (tenant) and therefore needs two additional approvals before it will actually answer: the operator of the instance must have AI features enabled, **and** your garden (tenant) must additionally have AI features enabled. If either level is off, opening chat shows the message "The AI features are currently disabled for this garden." There is currently no click-through flow that lets an administrator enable this tenant-level setting themselves — see [For Technical Users / Self-Hosters](#for-technical-users-self-hosters).

If your consent for the assistant to use your plant master values as context is also missing, you'll instead see "This AI feature requires your consent …". How to grant that consent is described under [Granting consent](#granting-consent).

---

## How the AI Assistant is structured (three-stage toggle)

An AI feature only answers when every relevant stage agrees:

| Stage | Who decides | Affects |
|-------|-------------|---------|
| 1. Instance-wide | Platform operator (environment variable) | All AI features across the whole instance |
| 2. Garden (tenant) | Your garden's administrator | All AI features that use your plant context (chat, and tip cards in the future) |
| 3. Your consent | You | Whether your plant data may be sent as context, and whether a cloud provider may be used instead of a local model |

Plain knowledge questions without a plant reference (see above) only need stage 1 — that's why they also work in Light Mode without logging in.

## Granting consent {#granting-consent}

Two consents are relevant to the AI Assistant:

| Consent | Needed for |
|---------|-----------|
| AI access to your plant data | Chat, tip cards, tip of the day, and "why?" explanations — anywhere the answer uses your specific plant context (species, phase, substrate, EC/pH readings) |
| AI processing via cloud provider | Additionally needed only if your instance uses a cloud provider instead of a local model |

Both appear in the **Privacy** area under the **Consents** tab, where you can currently only view them, not grant or revoke them by clicking — that still works only through the API. Details, the wording of the consent texts, and the exact click-through flow are described in [Privacy & GDPR](privacy.md#managing-consents-gdpr-art-7).

---

## Transparency: how to recognize an AI answer

Every answer from the AI Assistant carries visible labeling:

- **AI badge** ("AI-generated") — appears above every answer, with the model and provider name in the tooltip.
- **Sources footer** — an expandable list of the cited knowledge-base entries with a relevance score and language. Expanded by default at the Expert experience level, collapsed otherwise.
- **"Uses your plant data" indicator** — appears only when the answer was generated using your plant context. Clicking it navigates to the privacy settings.
- **"Cloud processing" indicator** — appears only when the answer was processed via an external cloud provider instead of locally.
- **"General information" notice** — appears when your plant is a self-added species/cultivar the knowledge base has no specific information about; the answer then relates to the nearest known genus or family instead.
- **Disclaimer** — below every answer: "AI answers can be inaccurate. Please check the sources for critical decisions."

!!! info "Cloud vs. local"
    Whether a cloud provider (e.g. Anthropic, OpenAI) or a locally run model (Ollama) answers is decided by the platform operator. Local providers send no data externally and need no separate consent; cloud providers additionally require your consent for "AI processing via cloud provider" (see above).

## Data minimization

The AI Assistant **never** sends your name, e-mail address, or free-text notes from your plant diary to the language model. Only master values are transmitted as context: scientific plant name, current phase, substrate, and numeric readings (EC, pH). Diary entries — if included at all — are only sent as an anonymized aggregate (e.g. "last watered 5 days ago"), never as original text. Every AI call is logged internally, but only as a hash of the question and its length — never in plain text.

---

## Planned Features at a Glance

The following features have already been built as components, but are not yet wired into any plant, planting-run, or task page — they aren't visible anywhere yet. These sections describe the planned behavior in future tense.

### Tip Cards

Tip cards will appear as compact care recommendations on the detail page of a plant or planting run. The system will analyze the current state and show 2 to 4 prioritized suggestions (title, explanation, recommendation, priority) — at most 2 for the Beginner experience level, more compact and with collapsed sources. Cards will be dismissible as done or not relevant.

### Tip of the Day

The first time you open the dashboard on a given day, a single tip relevant to you will appear — for example a warning about an unusual reading, a note about an upcoming phase transition, or a general care tip. The tip can be dismissed for the rest of the day.

### "Why?" Buttons

Task cards, care reminders, phase-transition suggestions, and feeding recommendations will get a small "why?" button. Clicking it opens a side panel with a short, AI-generated explanation based on your current plant data.

## Experience Levels and AI Features (planned)

Available AI features will eventually adapt to the configured [experience level](../user-guide/onboarding.md).

| Feature | Beginner | Intermediate | Expert |
|---------|:--------:|:------------:|:------:|
| Knowledge questions | Yes | Yes | Yes |
| Tip cards (simplified, max. 2) | Yes | Yes | Yes |
| Tip of the day | Yes | Yes | Yes |
| "Why?" buttons | Yes | Yes | Yes |
| Chat feature | — | Yes | Yes |
| Sources expanded by default | — | — | Yes |

The sources display (expanded/collapsed) already adapts to your experience level today; the remaining restrictions in this table are not yet implemented — in particular, chat is currently visible at every experience level.

---

## For Technical Users / Self-Hosters {#for-technical-users-self-hosters}

The AI Assistant is unlocked through three levels — details and environment variables are in [Environment Variables — AI Assistant](../reference/environment-variables.md#ki-assistent).

**Stage 1 (operator):** `AI_FEATURES_ENABLED=true` on the backend. If unset, every AI endpoint responds with HTTP 404 — the AI API effectively doesn't exist for the instance.

**Stage 2 (tenant):** The field `tenant.settings.ai_features_enabled` controls whether AI features are active for a specific garden (tenant) (default: `false`). There is currently **neither a UI nor a dedicated API endpoint** for this — the field can only be set through direct access to the tenant document in ArangoDB. Without this step, every tenant-scoped AI feature (chat, and tip cards in the future) stays disabled even when stage 1 is on.

**Stage 3 (consent):** `POST /api/v1/privacy/consents` with `purpose: ai_tenant_data_access` or `purpose: ai_cloud_processing` (see [Privacy & GDPR](privacy.md#for-technical-users-self-hosters)).

The plain knowledge question only needs stage 1 and is reachable as a rate-limited, anonymous endpoint:

| Endpoint | Purpose |
|----------|---------|
| `POST /api/v1/public/ai/ask` | Free-form knowledge question with no plant context (no login, IP rate-limited) |
| `GET /api/v1/public/ai/health` | Checks whether the knowledge base is reachable |

Details for all AI endpoints (including chat, tips, explanations) are in the [API reference](../reference/api-reference.md#ki-assistent).

---

## Behavior Without a Reachable Knowledge Base

If the underlying knowledge base (Knowledge Service) is unreachable, the AI Assistant returns a rule-based answer without a language model instead of an error — the application stays usable, but answer quality is then lower.

---

## Frequently Asked Questions

??? question "Are my plant data used to train AI models?"
    No. Kamerplanter sends data only to answer your specific request. Whether it's used for model training depends on the contractual terms of the provider chosen by the operator — with locally run models (Ollama), your data never leaves your network in the first place.

??? question "Why does chat respond with 'The AI features are currently disabled for this garden'?"
    Stage 1 (operator) is active, but stage 2 (your garden/tenant) isn't yet. This currently can only be fixed by the operator directly — see [For Technical Users / Self-Hosters](#for-technical-users-self-hosters).

??? question "Why does chat show a missing-consent notice?"
    Chat uses your plant context and therefore needs your "AI access to your plant data" consent. How to grant it is described under [Granting consent](#granting-consent).

??? question "Can I run the AI Assistant entirely locally?"
    That's decided by the platform operator when configuring the knowledge base. With a local model (Ollama), no data leaves your own network and no cloud-processing consent is needed. Details for self-hosters: [AI Provider Setup](ai-providers.md).

---

## See Also

- [AI Provider Setup](ai-providers.md)
- [Privacy & GDPR](privacy.md)
- [Understanding the RAG Knowledge Base](../guides/rag-knowledge-base.md)
- [AI Architecture (Developer)](../architecture/ai-architecture.md)
- [API Reference: AI Assistant](../reference/api-reference.md#ki-assistent)
- [Environment Variables: AI Assistant](../reference/environment-variables.md#ki-assistent)
