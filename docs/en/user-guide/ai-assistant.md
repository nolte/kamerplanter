# AI Assistant

!!! warning "Not yet implemented"
    The AI Assistant **interface** described on this page (chat panel, tip cards, diagnosis mode) is planned and not yet available; it is not yet implemented in the frontend. The `KIAssistentPage` currently exists only as a placeholder ("This feature is still in preparation") and is not yet linked in the navigation. This documentation describes the **planned behavior** and uses future tense throughout. The underlying knowledge base is already usable directly via the API today — see the next section. <!-- REQ-031 -->

The AI Assistant will provide context-aware care tips, support diagnosing plant problems, and answer questions about your plants — directly based on your own data.

---

### For technical users: AI answers via the API

This section is aimed at technical users and self-hosters. Even without a finished interface, the underlying knowledge base is already available through two API endpoints:

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/knowledge/search` | Semantic search over the knowledge base (plant knowledge, guides) |
| `POST /api/v1/knowledge/ask` | Ask a question — the system generates an answer from the knowledge base, provided an AI provider is configured |

!!! info "API only / operator configuration"
    There is no chat interface. Both endpoints can be tested directly through the interactive API documentation (`/docs`); a logged-in session is required. See the [API reference](../api/overview.md) for details. The operator also needs to configure an AI provider (see [AI Provider Setup](ai-providers.md)) — without a provider, `/ask` returns an error.

---

## Prerequisites (planned)

- At least one planting run or plant configured
- A configured AI provider (see [AI Provider Setup](ai-providers.md))
- For the chat feature: experience level **Intermediate** or higher (see [Experience Levels](#experience-levels-and-ai-features))

!!! tip "No API key required"
    With Ollama (local), it will be possible to run the AI Assistant entirely on your own hardware — no cloud account needed, no data shared externally.

---

## Planned Features at a Glance

### Tip Cards

Tip cards will appear as compact care recommendations automatically on the detail page of a plant or planting run. The system will analyze the current state and show 2 to 4 prioritized suggestions (title, explanation, recommendation, priority). New cards will be generated daily, and immediately whenever the growth phase transitions, an EC/pH value drifts outside the target range, or a new IPM event is recorded. Cards will be dismissible as done or not relevant.

### Chat Feature

The chat will enable a free-form dialog with the AI Assistant. The system will have full knowledge of the plant's context: current phase, measurements (EC, pH, VPD), fertilization history, and active pest events. Responses will stream word by word. The chat feature will be available from experience level **Intermediate** onwards; beginners will see tip cards only.

!!! example "Example questions that will be possible"
    - "My lower leaves are turning yellow — what could be the cause?"
    - "Should I start the PK boost in week 4 of flowering?"
    - "EC rose from 1.4 to 1.8 today — do I need to flush?"
    - "When is the optimal harvest window for my cultivar?"

### Diagnosis Mode

Diagnosis mode will enable targeted analysis of specific problems: describe a symptom, and the system will analyze it using current measurements, care history, and the internal knowledge base. The result will be a prioritized list of possible causes with concrete action recommendations.

---

## Provider Selection and Privacy (planned)

Once the interface is available, **Settings > AI Provider** will let you choose which system processes requests. Until then, provider selection happens exclusively through operator configuration (see [AI Provider Setup](ai-providers.md)).

| Provider | Data Sharing | API Key | Cost |
|----------|-------------|---------|------|
| Ollama (local) | None | Not needed | Free (own hardware) |
| llama.cpp | None | Not needed | Free (own hardware) |
| OpenAI-compatible | Depends on provider | Depends | Variable |
| Anthropic Claude | Transferred to Anthropic (USA) | Required | Pay-per-token |

!!! warning "Cloud providers and privacy"
    When using a cloud provider, plant data is transmitted to external servers. Once the UI is available, opening chat with a cloud provider for the first time will trigger a consent prompt. If you don't want to share data externally, use Ollama (local).

---

## Experience Levels and AI Features (planned) {#experience-levels-and-ai-features}

Available AI features will adapt to the configured experience level.

| Feature | Beginner | Intermediate | Expert |
|---------|:--------:|:------------:|:------:|
| Tip cards (simplified) | Yes | Yes | Yes |
| Tip cards (technical details) | — | Yes | Yes |
| Chat feature | — | Yes | Yes |
| Diagnosis mode | — | Yes | Yes |
| View recommendation sources | — | — | Yes |
| Technical context data in chat | — | — | Yes |

---

## Behavior Without a Configured AI Provider

Kamerplanter will work without an AI provider. In this case, the system will generate rule-based tip cards from master data and the current phase — without a language model. Quality will be lower, but the system will never be without recommendations.

---

## Frequently Asked Questions

??? question "Are my plant data used to train AI models?"
    No. Kamerplanter will send data only to answer a specific request to the configured provider. Use for model training is contractually excluded (OpenAI API, Anthropic API). With local providers (Ollama, llama.cpp), data never leaves your network.

??? question "How current is the knowledge base already used by `/knowledge/ask`?"
    Master data (species, nutrient profiles, pest data) is re-indexed weekly. Thematic guides are maintained and updated with each Kamerplanter release.

??? question "Can I add custom care guides to the knowledge base?"
    Tenant admins can upload custom guides in YAML format. These are automatically integrated into the RAG knowledge base. The guide [Understanding the RAG Knowledge Base](../guides/rag-knowledge-base.md) explains how.

??? question "When is the chat interface coming?"
    No fixed date has been set. Progress can be tracked in the project's backlog/issue tracker. <!-- REQ-031 -->

---

## See Also

- [AI Provider Setup](ai-providers.md)
- [Understanding the RAG Knowledge Base](../guides/rag-knowledge-base.md)
- [AI Architecture (Developer)](../architecture/ai-architecture.md)
- [Sensors and Measurements](sensors.md)
- [Fertilization Logic](fertilization.md)
