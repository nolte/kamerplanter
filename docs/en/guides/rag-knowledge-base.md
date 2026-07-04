# Understanding the RAG Knowledge Base

The AI Assistant in Kamerplanter does not answer from the memory of a general language model — it grounds every response in your own data and a curated knowledge base. This technique is called **Retrieval-Augmented Generation (RAG)**. This page explains how the system is structured and why it works the way it does.

---

## Why RAG?

A language model answering solely from its training has two weaknesses:

1. **Hallucinations** — It invents plausible-sounding but incorrect facts
2. **No context** — It does not know your specific plant, your current measurements, or your care history

RAG solves both problems: before generating every response, the system searches a verified database for relevant information and provides it to the model as a foundation. The model then combines these facts with your specific situation — instead of speculating from memory.

!!! tip "Simply explained"
    Think of RAG as a very well-prepared assistant: before answering your question, they quickly looked up the relevant reference books. They don't make things up — they explain what they found.

---

## The 4-Level Model

Kamerplanter's knowledge base consists of four levels that are combined for every request.

<!-- diagram-source: user-described — 4-level RAG knowledge base feeding the retriever, context builder, and prompt assembler -->
```mermaid
flowchart TB
    subgraph "Level 1: Global Master Data"
        E1[Plant species, cultivars, growth phases,<br/>nutrient profiles, pests, diseases]
    end

    subgraph "Level 2: Thematic Guides"
        E2[31 curated expert knowledge files:<br/>Diagnostics, fertilization, irrigation,<br/>environment, phases, outdoor, general]
    end

    subgraph "Level 3: Tenant Context"
        E3[Active planting run, phase,<br/>measurements EC/pH/VPD,<br/>active IPM events, recent feeding events]
    end

    subgraph "Level 4: Your Plant Data"
        E4[Care history, harvest results,<br/>plant diary entries, confirmations]
    end

    E1 --> RAG[RAG Retriever<br/>pgvector]
    E2 --> RAG
    E3 --> CB[Context Builder<br/>ArangoDB]
    E4 --> CB

    RAG --> PA[Prompt Assembler]
    CB --> PA
    PA --> LLM[Language Model]
    LLM --> Response
```

**Levels 1 and 2** are stored as vectors and retrieved via similarity search.
**Levels 3 and 4** are injected as structured text into every request at runtime.

### Level 1: Global Master Data

The Kamerplanter master data forms the foundation of all recommendations:

- Plant species with taxonomy, care requirements, and characteristics
- Cultivars with specific traits
- Growth phase definitions with VPD targets, light and temperature requirements
- Nutrient profiles per species and phase
- Pest and disease data with symptoms and treatment methods

This data is re-indexed weekly.

### Level 2: Thematic Guides

Thematic guides contain cross-cutting knowledge that cannot be derived from master data — expert knowledge that applies across many plant species and situations. The knowledge base currently includes 31 curated guides in seven categories:

| Category | Example Guides |
|----------|---------------|
| Diagnostics | Nutrient deficiency symptoms, pH/EC deviations, early pest detection, root health |
| Environment | VPD optimization, light fundamentals, temperature control, CO₂ enrichment |
| Fertilization | EC management (hydroponics/soil), organic outdoor fertilization, CalMag correction, mixing order |
| Irrigation | Irrigation strategies by substrate, recognizing overwatering, water quality |
| Phases | Germination, vegetative optimization, flowering management, harvest timing, overwintering |
| Outdoor | Season planning, companion planting, crop rotation, weather reactions |
| General | Beginner's guide, common mistakes to avoid, yield optimization |

!!! note "Reviewed by horticultural experts"
    All guides are reviewed for technical accuracy before inclusion in the knowledge base. The system also includes 100 benchmark questions against which every new version of the knowledge base is tested.

### Level 3: Tenant Context (Real-Time)

For every request, the Context Builder fetches the current state of your grow from the database:

- Active planting runs with current growth phase and phase duration
- Latest measurements: EC, pH, VPD, temperature, humidity
- Active IPM events (pest infestations, diseases, ongoing treatments)
- Last feeding events with quantities and products

### Level 4: Your Plant Data (Real-Time)

With your consent, personal care data also flows into the context:

- Care confirmations (when watered, fertilized, trained)
- Plant diary entries
- Results from past harvests

---

## An Example Flow

Here is how a typical request moves through the system:

!!! example "Example: Yellowing Leaves"

    **Your question:** "My lower leaves are turning yellow — what could be the cause?"

    **Step 1 — Context Builder reads your data:**
    ```
    Species: Cannabis sativa 'Northern Lights'
    Phase: Flowering, Day 21
    EC: 1.2 mS/cm, pH: 5.8, VPD: 1.1 kPa
    Last feeding: 2 days ago (standard nutrient solution)
    ```

    **Step 2 — RAG Retriever finds relevant chunks:**
    - Master data chunk: "Cannabis sativa, Flowering phase, NPK target 5-15-14"
    - Guide chunk: "Nitrogen deficiency: lower leaves yellow, raise EC..."
    - Guide chunk: "Flowering management: N demand drops from week 3, natural N draw-down..."

    **Step 3 — Model combines everything:**
    > "Your Northern Lights is in week 3 of flowering. Yellowing lower leaves can indicate N deficiency, BUT: natural N draw-down in lower leaves during late flower is normal. Your EC is at 1.2 — that's a bit low for week 3 flowering. Recommendation: raise EC to 1.4–1.6, do NOT increase the N ratio (PK phase). If more than 30% of leaves are affected, consider a light N boost."

Without the thematic guides, the model would only know the master data context and give generic tips. Without your real-time context (EC 1.2, week 3 flower), the model would not know the situation is borderline.

---

## Knowledge Base Quality Assurance

### Expert Review

All guides and master data are reviewed by experienced growers for technical accuracy before inclusion. Particular attention is paid to:

- Correct VPD and EC target values per phase and substrate
- Agreement of symptom descriptions with current literature
- Safety notices (mixing order, pre-harvest intervals)

### Benchmark Evaluation

The system includes 100 benchmark questions whose answers are automatically evaluated with every knowledge base update:

- **Topic Match** — Are the retrieved RAG chunks relevant to the question?
- **LLM-as-Judge** — A second model evaluates factual accuracy and actionability
- **A/B Comparison** — When models or guide versions change: improvement over baseline?

---

## Adding Custom Guides (Admin)

!!! warning "Not yet implemented"
    There is currently no management UI for uploading tenant-specific guides — neither in the frontend nor as a dedicated storage area in the backend. All thematic guides come from the centrally curated YAML files under `spec/knowledge/rag/`, which are mounted into the Knowledge Service container on every deployment. The YAML format below describes how a guide chunk is structured — it already serves as the template for the centrally maintained guides today; a tenant-owned upload feature will only arrive in a future version.

Once this feature is available, tenant admins will be able to add custom thematic guides to the local knowledge base — useful for cultivar-specific specialist knowledge, internal protocols, or guides in other languages.

### YAML Format (Reference)

```yaml
---
title: My Custom Guide Title
category: fertilization   # diagnostics | environment | fertilization | irrigation | phases | outdoor | general
tags: [ec, nutrient, hydroponics]
expertise_level: [intermediate, expert]
applicable_phases: [vegetative, flowering]
chunks:
  - id: my-first-chunk
    title: Section Title
    content: |
      Knowledge goes here as free text. The content is vectorized
      and retrieved for matching queries.

      Tip: Concrete, action-oriented text works better
      than general descriptions.
    metadata:
      nutrient: nitrogen
      substrate: coco
```

!!! note "Quality responsibility"
    Even after the upload feature ships, custom guides will not be automatically reviewed. Incorrect guides can degrade the quality of AI responses.

---

## Reindexing the Knowledge Base (Operator/Developer)

After modifying knowledge YAML files under `spec/knowledge/rag/`, the vectors in the VectorDB (pgvector) must be recomputed. There is **no automatic schedule** for this — the reindex must be triggered manually against the Knowledge Service after every content change.

### Prerequisites

- Knowledge YAML files are mounted in the Knowledge Service container at `/app/knowledge` (automatic with Skaffold deployment)
- The Knowledge Service and its Embedding Service must be running
- `INTERNAL_SERVICE_TOKEN` is set (the endpoint is service-token-protected, see [Error Handling](../api/error-handling.md))

### Workflow: Edit chunk → deploy → reindex → test

```bash
# 1. Edit knowledge YAML files
#    e.g. spec/knowledge/rag/diagnostik/naehrstoffmangel-symptome.yaml

# 2. Redeploy (so the files are available in the Knowledge Service container)
skaffold dev   # or: skaffold run

# 3. Trigger the reindex via the Knowledge Service endpoint
kubectl exec -it deploy/knowledge-service -- \
  curl -sX POST http://localhost:8000/ingest \
  -H "Authorization: Bearer $INTERNAL_SERVICE_TOKEN"

# 4. Run the benchmark (optional, recommended)
cd tools/rag-eval
source ~/.venvs/rag-eval/bin/activate
python eval_rag.py
```

### What happens during reindex?

1. All YAML files under `/app/knowledge` are read
2. Each chunk is vectorized using the embedding model (`multilingual-e5-large`, 1024 dimensions, see [ADR-006](../adr/006-embedding-modell-e5-base-hybrid-search.md))
3. Vectors are upserted into `ai_vector_chunks` (existing chunks are updated by their `source_key`, new ones added)
4. The endpoint returns a summary: number of files, number of chunks

!!! tip "Fast feedback loop"
    For iterative knowledge base improvement, use this cycle:

    1. Run benchmark → identify failures
    2. Add or improve chunks in the YAML files
    3. Deploy and reindex
    4. Re-run benchmark → verify score improvement

    See `tools/rag-eval/README.md` for benchmark tool details.

---

## Frequently Asked Questions

??? question "Can the AI search the internet for additional information?"
    No. The system performs no internet searches. All answers are based exclusively on the local knowledge base (master data, guides) and your own plant data. This is a deliberate design decision to avoid hallucinations and ensure data privacy.

??? question "How current are the thematic guides?"
    Guides are maintained with each Kamerplanter release. The exact status is noted in the version documentation ([Changelog](../changelog/index.md)).

??? question "What happens if no matching guide chunk is found?"
    The system falls back to master data (Level 1) and uses the structured context (Levels 3+4). Response quality is lower in this case, but the system still responds — without hallucinating.

??? question "Can I add custom guides for my tenant?"
    Not yet — this is planned as a future feature (see above). Currently, all thematic guides come from the centrally maintained knowledge base under `spec/knowledge/rag/` and apply equally to all tenants.

---

## See Also

- [AI Assistant](../user-guide/ai-assistant.md)
- [AI Provider Setup](../user-guide/ai-providers.md)
- [AI Architecture (Developer)](../architecture/ai-architecture.md)
- [VPD Optimization](vpd-optimization.md)
- [Nutrient Mixing](nutrient-mixing.md)
