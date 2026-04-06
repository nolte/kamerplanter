# AI Assistant

The AI Assistant in Kamerplanter provides context-aware care tips, supports diagnosing plant problems, and answers questions about your plants — directly based on your own data.

---

## Prerequisites

- At least one planting run or plant configured
- A configured AI provider (see [AI Provider Setup](ai-providers.md))
- For the chat feature: experience level **Intermediate** or higher (see [Experience Levels](#experience-levels-and-ai-features))

!!! tip "No API key required"
    With Ollama (local), you can run the AI Assistant entirely on your own hardware — no cloud account needed, no data shared externally.

---

## Tip Cards

Tip cards are compact care recommendations that appear automatically on the detail page of your plant or planting run. The system analyzes the current state and provides 2 to 4 prioritized suggestions.

### What tip cards show

Each card displays:

- **Title** — A brief summary of the recommendation
- **Explanation** — What the system detected and why it matters
- **Recommendation** — A concrete action you can take
- **Priority** — Critical, high, medium, or low (color-coded)

!!! info "Screenshot pending"
    This screenshot will be added in a future version.

### When are tip cards refreshed?

The system generates new tip cards daily for all active runs. Cards are also regenerated immediately when:

- The growth phase transitions
- An EC or pH value falls outside the target range
- An IPM event (pest, disease, active treatment) is recorded

!!! note "Caching"
    Tip cards are cached for 4 hours. If you dismiss or mark a card as done, it will not reappear unless the plant's state changes significantly.

### Dismissing or completing a tip card

Click the three-dot menu on a card:

- **Done** — Marks the tip as acted upon and removes it
- **Not relevant** — Hides the card; the system learns from this
- **Details** — Shows the knowledge sources the recommendation is based on

---

## Chat Feature

The chat enables a free-form dialog with the AI Assistant. The system has full knowledge of your plant's context: current phase, measurements (EC, pH, VPD), fertilization history, and active pest events.

!!! info "Availability"
    The chat feature is available from experience level **Intermediate** onwards. Beginners see tip cards only.

### Opening the chat

1. Open the detail page of a plant or planting run
2. Click **AI Chat** (icon in the top toolbar)
3. The chat panel slides open

### Example questions

The system understands natural language questions. Some examples:

!!! example "Questions you can ask"
    - "My lower leaves are turning yellow — what could be the cause?"
    - "Should I start the PK boost in week 4 of flowering?"
    - "EC rose from 1.4 to 1.8 today — do I need to flush?"
    - "When is the optimal harvest window for my cultivar?"
    - "Humidity was 80% today — how high is my mold risk?"
    - "Can I still top the plant or is it too far along?"

### Streaming responses

Responses appear word by word as the model generates them. You don't have to wait for the full response.

### Chat history

All conversations are saved and accessible under **AI Chat > History**. Conversation history is automatically deleted after 90 days (GDPR policy).

!!! warning "Cloud providers and privacy"
    When using OpenAI or Anthropic, your plant data is transmitted to external servers. When you first open chat with a cloud provider, Kamerplanter asks for your consent. If you don't want to share data externally, use Ollama (local).

---

## Diagnosis Mode

Diagnosis mode is designed for targeted analysis of specific problems. You describe a symptom — the system analyzes it using your current measurements, care history, and the internal knowledge base.

### Starting a diagnosis

1. Open the detail page of the affected plant
2. Click **Diagnose** (or open chat and describe the symptom)
3. Describe the problem as precisely as possible

!!! example "Symptoms the system can analyze"
    - Yellow or brown leaves (describe the pattern: top/bottom, uniform/spotty)
    - Deformed or unusually small leaves
    - Signs of pests (webbing, bite marks, small insects)
    - EC drift (rising or falling)
    - Unusually slow growth
    - Root discoloration

### How the system analyzes

The system combines:

1. **Your current state** — Phase, current EC/pH/VPD values, last care events
2. **Species master data** — Known sensitivities, nutrient requirements per phase
3. **Knowledge base** — Curated expert knowledge on symptoms, causes, and remedies

The result is a prioritized list of possible causes with concrete action recommendations.

---

## Provider Selection and Privacy

Under **Settings > AI Provider** you can choose which system processes your requests.

| Provider | Data Sharing | API Key | Cost |
|----------|-------------|---------|------|
| Ollama (local) | None | Not needed | Free (own hardware) |
| llama.cpp | None | Not needed | Free (own hardware) |
| OpenAI | Transferred to OpenAI (USA) | Required | Pay-per-token |
| Anthropic Claude | Transferred to Anthropic (USA) | Required | Pay-per-token |
| OpenAI-compatible | Depends on provider | Depends | Variable |

!!! warning "Cloud providers require GDPR consent"
    When using a cloud provider for the first time, Kamerplanter asks for your consent to data transfer. You can revoke this consent at any time under **Settings > Privacy**.

How to set up a provider is explained on the [AI Provider Setup](ai-providers.md) page.

---

## Experience Levels and AI Features

Available AI features adapt to your configured experience level.

| Feature | Beginner | Intermediate | Expert |
|---------|:--------:|:------------:|:------:|
| Tip cards (simplified) | Yes | Yes | Yes |
| Tip cards (technical details) | — | Yes | Yes |
| Chat feature | — | Yes | Yes |
| Diagnosis mode | — | Yes | Yes |
| View recommendation sources | — | — | Yes |
| Technical context data in chat | — | — | Yes |

You can change your experience level at any time under **Settings > Experience Level**.

---

## When No AI Provider Is Available

Kamerplanter works without an AI provider. In this case, the system generates rule-based tip cards from master data and the current phase — without a language model. The quality is lower, but the system is never without recommendations.

!!! note "Rule-based fallback"
    The fallback activates automatically when no provider is configured or the configured provider is unreachable. Cards generated this way display a "Rule-based" label.

---

## Frequently Asked Questions

??? question "Are my plant data used to train AI models?"
    No. Kamerplanter sends your data only to answer your specific request. Use for model training is contractually excluded (OpenAI API, Anthropic API). With local providers (Ollama, llama.cpp), your data never leaves your network.

??? question "How current is the AI Assistant's knowledge base?"
    Master data (species, nutrient profiles, pest data) is re-indexed weekly. Thematic guides (expert knowledge on diagnosis, fertilization, environment) are maintained and updated with each Kamerplanter release.

??? question "Can I add custom care guides to the knowledge base?"
    Tenant admins can upload custom guides in YAML format. These are automatically integrated into the RAG knowledge base. The guide [Understanding the RAG Knowledge Base](../guides/rag-knowledge-base.md) explains how.

??? question "Why does the AI Assistant sometimes give different answers to the same question?"
    Language models are probabilistic systems — responses vary slightly. The factual basis (your measurements, master data, knowledge base) is always the same, but phrasing and emphasis may differ. For critical decisions (e.g., harvest timing), we recommend asking multiple times and comparing the responses.

??? question "The assistant responds very slowly — what can I do?"
    With local providers (Ollama), speed depends on your hardware. Tips for improvement: (1) Enable GPU acceleration if available. (2) Use a smaller model (e.g., `llama3.2:3b` instead of `gemma3:4b`). (3) For tip cards, speed is less critical since they are generated daily in the background.

---

## See Also

- [AI Provider Setup](ai-providers.md)
- [Understanding the RAG Knowledge Base](../guides/rag-knowledge-base.md)
- [AI Architecture (Developer)](../architecture/ai-architecture.md)
- [Sensors and Measurements](sensors.md)
- [Fertilization Logic](fertilization.md)
