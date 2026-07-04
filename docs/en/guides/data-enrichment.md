<!-- Source: REQ-011 (external master-data enrichment); code: src/backend/app/api/v1/enrichment/, src/backend/app/domain/engines/enrichment_engine.py, src/backend/app/data_access/external/{gbif_adapter,perenual_adapter}.py, src/frontend/src/components/common/OriginChip.tsx, src/frontend/src/hooks/useOriginProtection.ts -->

# External Data Enrichment

Kamerplanter can automatically fill in the botanical master data of a plant species from public databases — for example common names, native habitat, or taxonomic information. This saves you from having to research and enter these details for every species yourself.

Enrichment runs in the background and only fills in **missing** information. Data you have already entered always takes precedence and is never overwritten automatically.

---

## What gets enriched?

Only the botanical **species data** is affected (not your individual plants, locations, or harvest records). The following fields can be filled in by external enrichment, as long as they are still empty for a species:

| Field | Example |
|-------|---------|
| Common names | "Tomato", "Love Apple" |
| Genus | *Solanum* |
| Botanical family | Solanaceae (nightshade family) |
| Growth habit | herbaceous, shrubby, climbing |
| Native habitat | region of origin and site conditions |
| Hardiness zones | e.g. 7a–9b |
| Synonyms | older or alternative scientific names |
| Taxonomic authorship and status | e.g. "L." for Linnaeus, status "ACCEPTED"/"SYNONYM" |
| Short description | brief botanical characterisation |

!!! note "Not to be confused with reference images"
    This page covers the **textual** master data. The photos shown to you as comparison images on the species page come from a separate image acquisition pipeline and are described under [Reference Images in the Species View](../user-guide/plant-management.md#reference-images-in-the-species-view). Both features partly share a source (GBIF, Global Biodiversity Information Facility) but run independently of each other.

## Where does the data come from?

| Source | Provides | Requirement |
|--------|----------|-------------|
| **GBIF** (Global Biodiversity Information Facility) | Taxonomy, synonyms, common names, native habitat, short description | None — public API, no key required |
| **Perenual** | Additional care data (including growth habit, hardiness zones) | The operator needs a free API key |

If no key is configured for a source (for example Perenual on a freshly installed instance), that source simply provides no data — the rest of the system keeps working unaffected.

## Automatic sync

A sync with the external sources runs **automatically in the background** — you don't need to do anything:

- **Daily**, the system checks which species are not yet enriched from a source and runs a sync for those.
- **Weekly**, a full sync of all species runs additionally, so that updates to already-enriched species are picked up as well. Unchanged data is skipped.

## How existing values are handled

For every field, the rule **"local data takes precedence"** applies:

- If the field was **empty** for a species, the system adopts the external value automatically.
- If a value was **already set**, the external value is only stored as a suggestion and is **not** adopted automatically — your existing value stays unchanged.

!!! tip "Origin marker in the interface"
    Kamerplanter marks automatically adopted fields in the master data views with the origin marker **"Enriched"** (a sparkle-star icon). This marker is read-only, so that the externally sourced data is not accidentally overwritten — unlike data you imported or entered yourself, you cannot edit it directly.

## Privacy

External data enrichment only processes botanical reference data (scientific species names) — no personal data of yours. Nevertheless, the feature is treated as an **optional, revocable consent** because it sends requests to third-party APIs (GBIF, Perenual). Details and how to manage the consent: [Privacy (GDPR, General Data Protection Regulation)](../user-guide/privacy.md#managing-consents-gdpr-art-7).

---

## For Technical Users / Self-Hosters

!!! note "Audience: operators and developers"
    The following sections are for people who run or administer their own Kamerplanter instance. None of these steps are needed for everyday use in the garden — enrichment runs automatically in the background.

### Setting up the Perenual key

GBIF works without any configuration. For Perenual you need a free API key, which you configure as an environment variable. Details and example values: [Environment Variables Reference](../reference/environment-variables.md#external-data-enrichment-req-011).

### Checking source status

```bash
curl -H "Authorization: Bearer <JWT>" \
  http://localhost:8000/api/v1/enrichment/sources | python3 -m json.tool
```

The health check shows whether a source is currently reachable:

```bash
curl -H "Authorization: Bearer <JWT>" \
  http://localhost:8000/api/v1/enrichment/health | python3 -m json.tool
```

### Triggering a sync manually

Instead of waiting for the next scheduled run, you can trigger a sync immediately — for example after adding several new species:

```bash
curl -X POST -H "Authorization: Bearer <JWT>" \
  http://localhost:8000/api/v1/enrichment/sources/gbif/sync
```

For a full sync of all species (not just those not yet enriched), set the `full_sync` parameter:

```bash
curl -X POST -H "Authorization: Bearer <JWT>" -H "Content-Type: application/json" \
  -d '{"full_sync": true}' \
  http://localhost:8000/api/v1/enrichment/sources/perenual/sync
```

The call starts the sync asynchronously and immediately returns the status of the started run. The following call shows the history of previous runs (including errors):

```bash
curl -H "Authorization: Bearer <JWT>" \
  http://localhost:8000/api/v1/enrichment/sources/gbif/history | python3 -m json.tool
```

### Reviewing, accepting or rejecting suggested values

For a given species, the following call shows all enrichments, including automatically adopted fields and still-open suggestions:

```bash
curl -H "Authorization: Bearer <JWT>" \
  http://localhost:8000/api/v1/enrichment/species/{species_key}/enrichments | python3 -m json.tool
```

Adopt an open suggestion (overwriting the current local value) or reject it:

```bash
# Accept a suggestion
curl -X POST -H "Authorization: Bearer <JWT>" -H "Content-Type: application/json" \
  -d '{"fields": ["hardiness_zones"]}' \
  http://localhost:8000/api/v1/enrichment/species/{species_key}/enrichments/perenual/accept

# Reject a suggestion
curl -X POST -H "Authorization: Bearer <JWT>" -H "Content-Type: application/json" \
  -d '{"fields": ["hardiness_zones"]}' \
  http://localhost:8000/api/v1/enrichment/species/{species_key}/enrichments/perenual/reject
```

### Searching external sources without importing

To check what data a source returns for a search term before importing anything:

```bash
curl -X POST -H "Authorization: Bearer <JWT>" -H "Content-Type: application/json" \
  -d '{"source_key": "gbif", "query": "Solanum lycopersicum"}' \
  http://localhost:8000/api/v1/enrichment/search | python3 -m json.tool
```

This call does not change any master data — it is preview-only.

!!! warning "All endpoints require authentication"
    All enrichment endpoints require a valid JWT access token. These are global resources (no tenant URL, `/api/v1/enrichment/...`), since botanical species data is shared across tenants.

---

## Frequently Asked Questions

??? question "Why don't I see enrichment for some species?"
    Possible reasons: the species has not been synced yet (the daily run processes not-yet-enriched species incrementally), the scientific name could not be matched to a unique species in the external source, or no API key is configured for Perenual on this instance.

??? question "Can I undo a value that was already adopted?"
    An automatically adopted value can be viewed like any other field with this origin, but not edited directly. To correct an incorrect value, contact the operator of your instance — technical details are in the [For Technical Users / Self-Hosters](#for-technical-users-self-hosters) section.

??? question "Does enrichment affect my own plants or harvests?"
    No. Enrichment only affects the botanical species data (the shared knowledge base), not your individual plants, locations, tasks, or harvest records.

??? question "What happens if an external source is unreachable?"
    A single failed source sync does not affect the other sources and does not change your existing master data. The next scheduled run will try again.

## See Also

- [Plant Master Data](../user-guide/plant-management.md) — managing species, cultivars, and botanical families
- [Identify a Plant by Photo](../user-guide/plant-identification.md) — a related but independent species-identification feature
- [Privacy (GDPR)](../user-guide/privacy.md) — managing consents
- [Environment Variables Reference](../reference/environment-variables.md#external-data-enrichment-req-011) — configuration for operators
