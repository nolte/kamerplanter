# Database Schema

Kamerplanter uses ArangoDB as its primary database — a multi-model system combining document and graph database capabilities. All entities are organized as document collections; relationships are modeled as edge collections in the named graph `kamerplanter_graph`.

---

## Overview

| Metric | Value |
|--------|-------|
| Database name | `kamerplanter` |
| Graph name | `kamerplanter_graph` |
| Document collections | 54 |
| Edge collections | ~75 |
| Primary persistence | ArangoDB 3.11+ |
| Time-series data | TimescaleDB (optional, REQ-005) |
| Cache / Queue | Redis / Valkey |

---

## Document Collections

### Master Data (REQ-001)

| Collection | Description | Key fields |
|-----------|-------------|-----------|
| `botanical_families` | Plant families | `name` (unique), `common_name` |
| `species` | Plant species | `scientific_name` (unique), `common_names`, `frost_sensitivity`, `propagation_configs[]` |
| `cultivars` | Cultivars / varieties | `name`, `species_key`, genetic lineage |
| `lifecycle_configs` | Lifecycle definitions per species | `species_key`, `lifecycle_type` |
| `growth_phases` | Individual growth phases | `name`, `order`, `lifecycle_config_key` |
| `requirement_profiles` | Environmental requirements per phase | `vpd_target_kpa`, `temperature_day_c`, `ppfd` |
| `nutrient_profiles` | Nutrient profiles per phase | `npk_ratio`, `target_ec_ms`, `target_ph` |
| `phase_transition_rules` | Transition criteria between phases | `from_phase_key`, `to_phase_key`, `trigger_type`, `gdd_threshold` |
| `phase_histories` | Log of past phase transitions | `entered_at`, `exited_at`, `actual_duration_days` |

#### Species — field `propagation_configs`

The `propagation_configs` object-array field is the canonical model for a species' propagation. Each `PropagationConfig` entry describes one propagation method together with its own timing, wood stage, difficulty and notes — replacing the former flat `propagation_methods`/`propagation_months`/`propagation_notes` fields. Subfields:

- `method` (required) — one `PropagationMethod` enum value: `seed` · `cutting` · `leaf_cutting` · `division` · `rhizome_division` · `bulb` · `bulbil` · `tuber` · `offset` · `runner` · `grafting` · `layering` · `air_layering` · `water_propagation` · `tissue_culture` · `spore` · `self_seeding`.
- `months` (`list[int]`, range 1–12) — months in which this method is most suitable, deduplicated and sorted ascending on the server side, independent of the other configs. The species-level sowing windows for generative propagation remain in the separate `direct_sow_months`, `indoor_start_months` and `transplant_months` fields.
- `wood_stage` (`WoodStage \| null`) — `softwood` / `semi_hardwood` / `hardwood` / `herbaceous`; only meaningful for cutting-type methods.
- `difficulty` (`PropagationDifficulty \| null`) — `easy` / `moderate` / `difficult`.
- `notes` (`string \| null`, max. 1,000 characters) — free-text expert knowledge for this method: typical failure points, species-specific substrate or temperature requirements, acclimatisation steps.

The array is optional in `SpeciesCreate` (default: empty list) and always present in `SpeciesResponse` (empty list when not populated). It is maintained for most species in the seed data.
<!-- REQ-017 -->

> **Note (deprecated flat fields):** The flat fields `propagation_methods`/`propagation_months`/`propagation_notes` are **deprecated** in favour of `propagation_configs`. Legacy flat values are still accepted and adapted on import — one config per method, all sharing the flat `propagation_months`, with `propagation_notes` attached to the first method only. New data uses `propagation_configs`.

#### Species — field `toxicity` / `allergen_info`

The `toxicity` object field captures a species' toxicity separately for cats, dogs and children (`is_toxic_cats`/`is_toxic_dogs`/`is_toxic_children`), the affected plant parts (`toxic_parts`), the responsible compounds (`toxic_compounds`) and the severity (`severity`: `none`/`mild`/`moderate`/`severe`). `allergen_info` adds contact- and pollen-allergen flags. The flat passthrough field `toxicity_severity` (`low`/`moderate`/`high`) is preserved from historical data and is **not** mapped onto `toxicity.severity`. All fields are optional (`null` when not maintained).

#### Species — field `seed_profile`

The `seed_profile` object field bundles genuine seed/germination metadata for seed-propagated species: germination temperature range (`germination_temp_min_c`/`_max_c`), sowing depth (`sowing_depth_cm`), days to germination (`days_to_germination`), seed viability in years (`seed_viability_years`), light/dark germination (`light_germination`: `light`/`dark`/`indifferent`), pretreatment (`pretreatment`: `cold_stratification`/`warm_stratification`/`scarification`/`presoak`), thousand-seed weight (`thousand_seed_weight_g`) and sowing density (`sowing_density_per_m2`). All fields are optional; purely vegetatively propagated species leave the object empty (`null`).

---

### Locations and Infrastructure (REQ-002, REQ-019)

| Collection | Description | Key fields |
|-----------|-------------|-----------|
| `sites` | Gardens, locations | `name`, `tenant_key`, `location_type` |
| `locations` | Rooms, beds, zones | `name`, `parent_location_key`, `depth`, `path` |
| `location_types` | Types for location hierarchy | `name`, `level` (10 system seeds) |
| `slots` | Individual plant spots | `slot_id` (unique), `capacity` |
| `substrates` | Substrate types / profiles | `substrate_type`, `ph_range`, `ec_capacity` |
| `substrate_batches` | Concrete substrate batches | `cycles_used`, `ph_history`, `irrigation_strategy` |

### Plant Instances and Runs (REQ-013)

| Collection | Description | Key fields |
|-----------|-------------|-----------|
| `plant_instances` | Individual plants | `instance_id` (unique), `current_phase_key`, `sown_at`, `mother_key` (pup ancestry, REQ-017) |
| `planting_runs` | Planting runs (groups) | `name`, `state`, `tenant_key` |
| `planting_run_entries` | Entries within a run | `species_key`, `planned_count` |

**Planting run states:**
```
planned → active → harvesting → completed
                             → cancelled
```

### Irrigation and Fertilization (REQ-004, REQ-014)

| Collection | Description | Key fields |
|-----------|-------------|-----------|
| `tanks` | Water tanks | `name` (unique), `capacity_liters`, `tenant_key` |
| `tank_states` | Point-in-time tank snapshots | `ec_ms`, `ph`, `volume_liters`, `recorded_at` |
| `tank_fill_events` | Tank fill events | `filled_at`, `water_mix_ratio_ro_percent` |
| `fertilizers` | Fertilizer master data | `product_name`, `brand` (unique per pair), `mixing_priority` |
| `fertilizer_stocks` | Inventory levels | `quantity_g`, `expiry_date` |
| `nutrient_plans` | Nutrient solution plans | `name`, `watering_schedule`, `is_template` |
| `nutrient_plan_phase_entries` | Phase-specific plan data | `phase_name`, `target_ec_ms`, `fertilizer_doses` |
| `feeding_events` | Individual feeding events | `plant_key`, `timestamp`, `ec_ms`, `ph` |
| `watering_events` | Watering events | `watered_at`, `volume_liters` |
| `watering_logs` | Unified watering log | `logged_at`, `plant_keys[]`, `slot_keys[]` |
| `maintenance_logs` | Tank maintenance records | `performed_at`, `action` |
| `maintenance_schedules` | Maintenance plans | `interval_days`, `next_due` |

### Pest Management — IPM (REQ-010)

| Collection | Description | Key fields |
|-----------|-------------|-----------|
| `pests` | Pest master data | `scientific_name` (unique), `common_name` |
| `diseases` | Disease master data | `scientific_name` (unique) |
| `treatments` | Treatment agents | `name` (unique), `pre_harvest_interval_days` |
| `inspections` | Pest inspection records | `plant_key`, `inspected_at`, `severity` |
| `treatment_applications` | Applied treatments | `plant_key`, `treatment_key`, `applied_at` |

### Harvest (REQ-007)

| Collection | Description | Key fields |
|-----------|-------------|-----------|
| `harvest_indicators` | Harvest readiness indicators per species | `indicator_type`, `target_value` |
| `harvest_observations` | Maturity observations | `plant_key`, `observed_at` |
| `harvest_batches` | Harvest batches | `batch_id` (optional, `null` allowed; unique only for values that are set), `plant_key`, `harvested_at`, `wet_weight_g` |
| `quality_assessments` | Quality evaluations | `overall_score`, `terpene_profile` |
| `yield_metrics` | Yield metrics | `dry_weight_g`, `trim_weight_g` |

### Tasks and Workflows (REQ-006)

| Collection | Description | Key fields |
|-----------|-------------|-----------|
| `workflow_templates` | Reusable workflow templates | `name` (unique), `trigger_phase` |
| `task_templates` | Task templates within workflows | `title`, `due_offset_days` |
| `tasks` | Concrete tasks | `plant_key`, `status`, `due_date` |
| `workflow_executions` | Active workflow executions | `plant_key`, `started_at` |
| `task_comments` | Task comments | `author_key`, `body` |
| `task_audit_entries` | Audit trail per task | `changed_by`, `change_type` |
| `activities` | Activity master data | `name` (unique) |

### Authentication and Users (REQ-023)

| Collection | Description | Key fields |
|-----------|-------------|-----------|
| `users` | User accounts | `email` (unique), `account_type`, `is_active` |
| `auth_providers` | Linked OAuth/OIDC providers | `provider`, `provider_user_id` (unique per pair) |
| `refresh_tokens` | Active session tokens | `token_hash` (unique), `user_key`, `expires_at` |
| `oidc_provider_configs` | OIDC provider configurations | `slug` (unique), `client_id` |
| `api_keys` | API keys for M2M | `key_hash` (unique), `user_key` |

### Tenants and Memberships (REQ-024)

| Collection | Description | Key fields |
|-----------|-------------|-----------|
| `tenants` | Tenants (gardens, organizations) | `slug` (unique), `name` |
| `memberships` | User-tenant relationships | `user_key`, `tenant_key` (unique per pair), `role` |
| `invitations` | Tenant invitations | `token_hash` (unique), `tenant_key`, `expires_at` |
| `location_assignments` | Assignment-based write access | `membership_key`, `location_key` (unique per pair) |

**Roles per tenant:** `admin`, `grower`, `viewer`

### Care Reminders (REQ-022)

| Collection | Description | Key fields |
|-----------|-------------|-----------|
| `care_profiles` | Care profile per plant instance | `care_style`, `watering_interval_days` |
| `care_confirmations` | Confirmed care events | `reminder_type`, `confirmed_at` |

### Onboarding (REQ-020)

| Collection | Description | Key fields |
|-----------|-------------|-----------|
| `starter_kits` | Pre-configured starter sets | `kit_id` (unique), `difficulty`, `sort_order` |
| `onboarding_states` | Onboarding wizard progress | `user_key`, `completed_at` |
| `user_preferences` | User preferences | `expertise_level`, `show_all_fields` |
| `user_favorites` | Favorited species, plans, fertilizers | `_from` (user), `_to` (target entity) |

### Propagation (REQ-017)

| Collection | Description | Key fields |
|-----------|-------------|-----------|
| `propagation_events` | Propagation events — currently only the automatic pup-clone case (D10) | `method` (`clone`), `parent_plant_keys[]`, `child_plant_keys[]`, `happened_at` |

### Miscellaneous

| Collection | Description |
|-----------|-------------|
| `sensors` | Sensor definitions (REQ-005) |
| `import_jobs` | CSV import jobs (REQ-012) |
| `calendar_feeds` | iCal feed configurations (REQ-015) |
| `system_settings` | System-wide settings (singleton) |
| `external_sources` | External data sources (GBIF, Perenual) |
| `external_mappings` | Internal ↔ external ID mappings |
| `sync_runs` | Enrichment run protocol |

---

## Edge Collections (Graph Relationships)

### Master Data Graph

| Edge | From | To | Meaning |
|------|------|----|---------|
| `belongs_to_family` | `species` | `botanical_families` | Species belongs to family |
| `has_cultivar` | `species` | `cultivars` | Species has cultivar |
| `has_lifecycle` | `species` | `lifecycle_configs` | Species has lifecycle |
| `consists_of` | `lifecycle_configs` | `growth_phases` | Lifecycle consists of phases |
| `next_phase` | `growth_phases` | `growth_phases` | Phase sequence |
| `governed_by` | `growth_phases` | `phase_transition_rules` | Phase has transition rules |
| `requires_profile` | `growth_phases` | `requirement_profiles` | Phase has env. requirements |
| `uses_nutrients` | `growth_phases` | `nutrient_profiles` | Phase has nutrient profile |
| `compatible_with` | `species` | `species` | Companion planting compatibility |
| `incompatible_with` | `species` | `species` | Companion planting incompatibility |
| `rotation_after` | `botanical_families` | `botanical_families` | Crop rotation recommendation |

### Location Graph

| Edge | From | To | Meaning |
|------|------|----|---------|
| `contains` | `sites`, `locations` | `locations` | Hierarchical containment |
| `has_slot` | `locations` | `slots` | Location has plant spots |
| `filled_with` | `slots` | `substrate_batches` | Slot is filled with substrate |
| `adjacent_to` | `slots` | `slots` | Neighboring spots (companion planting) |

### Plant Instance Graph

| Edge | From | To | Meaning |
|------|------|----|---------|
| `placed_in` | `plant_instances` | `slots` | Plant occupies slot |
| `grown_in` | `plant_instances` | `substrate_batches` | Plant grows in substrate |
| `current_phase` | `plant_instances` | `growth_phases` | Current phase of plant |
| `phase_history_edge` | `plant_instances` | `phase_histories` | Plant's phase history |
| `follows_plan` | `plant_instances` | `nutrient_plans` | Plant follows nutrient plan |
| `descended_from` | `plant_instances` (pup) | `plant_instances` (mother) | Genetic lineage — currently only the automatic pup-clone case for monocarpic plants (REQ-017) |

### Planting Run Graph

| Edge | From | To | Meaning |
|------|------|----|---------|
| `run_contains` | `planting_runs` | `plant_instances` | Run contains plants |
| `run_at_location` | `planting_runs` | `locations` | Run at location |
| `run_uses_substrate` | `planting_runs` | `substrate_batches` | Run uses substrate |
| `has_entry` | `planting_runs` | `planting_run_entries` | Run has entries |
| `run_follows_plan` | `planting_runs` | `nutrient_plans` | Watering schedule assignment |

### Tank and Fertilization Graph

| Edge | From | To | Meaning |
|------|------|----|---------|
| `has_tank` | `locations` | `tanks` | Location has tank |
| `supplies` | `tanks` | `locations` | Tank supplies location |
| `feeds_from` | `tanks` | `tanks` | Tank-to-tank cascade |
| `has_state` | `tanks` | `tank_states` | Tank state snapshots |
| `has_fill_event` | `tanks` | `tank_fill_events` | Tank fill events |
| `mixed_into` | `nutrient_plans` | `tank_fill_events` | Nutrient plan in fill event |
| `fert_incompatible` | `fertilizers` | `fertilizers` | Incompatible fertilizer pairs |
| `has_component` | `fertilizers` | `fertilizers` | Multi-component fertilizer |
| `has_stock` | `fertilizers` | `fertilizer_stocks` | Inventory level |
| `fed_by` | `plant_instances` | `feeding_events` | Plant received feeding |
| `feeding_used` | `feeding_events` | `fertilizers` | Feeding used fertilizer |
| `has_phase_entry` | `nutrient_plans` | `nutrient_plan_phase_entries` | Plan has phase entries |
| `plan_uses_fertilizer` | `nutrient_plan_phase_entries` | `fertilizers` | Plan entry uses fertilizer |

### IPM Graph

| Edge | From | To | Meaning |
|------|------|----|---------|
| `inspected_by` | `plant_instances` | `inspections` | Pest inspections |
| `detected_pest` | `inspections` | `pests` | Pest identified |
| `detected_disease` | `inspections` | `diseases` | Disease identified |
| `applied_to_plant` | `treatment_applications` | `plant_instances` | Treatment applied to plant |
| `treatment_uses` | `treatment_applications` | `treatments` | Treatment uses agent |
| `targets_pest` | `treatments` | `pests` | Agent targets pest |
| `contraindicated_with` | `treatments` | `treatments` | Agents not compatible |
| `vulnerable_in_phase` | `growth_phases` | `pests`, `diseases` | Susceptibility per phase |

### Harvest Graph

| Edge | From | To | Meaning |
|------|------|----|---------|
| `has_harvest_indicator` | `species` | `harvest_indicators` | Harvest indicators per species |
| `observed_for_harvest` | `plant_instances` | `harvest_observations` | Ripeness observations |
| `harvested_as` | `plant_instances` | `harvest_batches` | Plant became a batch |
| `assessed_by_quality` | `harvest_batches` | `quality_assessments` | Quality assessment |
| `has_yield_metric` | `harvest_batches` | `yield_metrics` | Yield metrics |

### Task Graph

| Edge | From | To | Meaning |
|------|------|----|---------|
| `wf_contains` | `workflow_templates` | `task_templates` | Workflow contains task templates |
| `has_task` | `plant_instances` | `tasks` | Plant has open task |
| `task_blocks` | `tasks` | `tasks` | Task blocks follow-up task |
| `instance_of` | `tasks` | `task_templates` | Task is instance of template |
| `task_assigned_to` | `tasks` | `users` | Task assigned to user |
| `task_uses_activity` | `tasks`, `task_templates` | `activities` | Task is an activity |

### Tenant Graph

| Edge | From | To | Meaning |
|------|------|----|---------|
| `has_membership` | `tenants` | `memberships` | Tenant has memberships |
| `membership_in` | `users` | `memberships` | User has membership |
| `belongs_to_tenant` | `sites`, `plant_instances`, `planting_runs`, `tanks`, `fertilizers`, `nutrient_plans`, `tasks` | `tenants` | Resource belongs to tenant |
| `assigned_to_location` | `location_assignments` | `locations` | Assignment-based location access |

---

## Indexes

Kamerplanter automatically creates the following indexes on startup:

| Collection | Index field | Type | Unique |
|-----------|------------|------|-------|
| `species` | `scientific_name` | Persistent | Yes |
| `botanical_families` | `name` | Persistent | Yes |
| `slots` | `slot_id` | Persistent | Yes |
| `plant_instances` | `instance_id` | Persistent | Yes |
| `users` | `email` | Persistent | Yes |
| `tenants` | `slug` | Persistent | Yes |
| `memberships` | `user_key, tenant_key` | Persistent | Yes |
| `fertilizers` | `product_name, brand` | Persistent | Yes |
| `harvest_batches` | `batch_id` | Persistent (sparse) | Yes |
| `tanks` | `name` | Persistent | Yes |
| `refresh_tokens` | `token_hash` | Persistent | Yes |
| `calendar_feeds` | `token` | Persistent | Yes |
| `tasks` | `status`, `plant_key` | Persistent | No |
| `feeding_events` | `plant_key`, `timestamp` | Persistent | No |

<!-- Quelle: src/backend/app/data_access/arango/collections.py (ensure_indexes) -->

!!! note "Sparse indexes"
    An index marked **sparse** only considers documents in which the field is actually set. For `harvest_batches.batch_id` this is required because the batch ID is an optional field: empty input is normalised to `null`, and any number of batches may exist without a batch ID at the same time, while identifiers that are set must still stay unique. Existing data is migrated by `v0030` (empty strings → `null`, index recreated as `unique + sparse`).

---

## Tenant Data Isolation

All tenant-bound resources carry a `tenant_key` field. On each request the FastAPI dependency `get_current_tenant` resolves the tenant from the `/t/{tenant_slug}/` URL segment and rejects the call if the requesting user holds no active membership there. Writing endpoints additionally require a minimum role (`require_tenant_role`) or an administrative scope (`require_admin_scope`). At the data level the isolation comes from every write path stamping `tenant_key` out of the resolved tenant context, and every query filtering on that field.

!!! note "Fine-grained permission matrix: not yet in force"
    The planned permission matrix (resource type × action × role) exists as a
    backend module but is **not** used by the HTTP endpoints — this spot
    previously described a `require_permission()` dependency that is wired into
    no endpoint. What is enforced today is membership, minimum role and admin
    scope. The matrix's only live consumer is the interface for external AI
    clients. <!-- REQ-024, REQ-033 -->
    <!-- Source: src/backend/app/common/auth.py, src/backend/app/core/permissions.py -->
    <!-- Evidence: .audits/issue-pattern-analysis/2026-08-08-report.md §3.1 -->


**Global resources** (no tenant binding): `species`, `cultivars`, `botanical_families`, `pests`, `diseases`, `treatments`, `starter_kits`

**Tenant-bound resources**: `sites`, `locations`, `plant_instances`, `planting_runs`, `tanks`, `fertilizers`, `nutrient_plans`, `tasks`

---

## Technical Notes for Developers

- Collections and the named graph are automatically created and migrated by `ensure_collections()` at backend startup.
- Add new collections or edge definitions to `collections.py` — they are created on the next startup.
- AQL queries use `FOR ... IN GRAPH kamerplanter_graph` exclusively for graph traversals.
- `_key` and `_id` are ArangoDB-internal identifiers. Application keys (e.g. `instance_id`) are separate fields with hash indexes.

---

## See Also

- [API Reference](api-reference.md)
- [Environment Variables](environment-variables.md)
- [Backend Architecture](../architecture/backend.md)
