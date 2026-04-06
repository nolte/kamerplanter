# Datenbankschema

Kamerplanter verwendet ArangoDB als primäre Datenbank — ein Multi-Modell-System, das Dokument- und Graphdatenbank kombiniert. Alle Entitäten sind als Dokument-Collections organisiert; Beziehungen werden als Kanten-Collections im Named Graph `kamerplanter_graph` abgebildet.

---

## Überblick

| Kennzahl | Wert |
|----------|------|
| Datenbankname | `kamerplanter` |
| Graph-Name | `kamerplanter_graph` |
| Dokument-Collections | 54 |
| Kanten-Collections | ~75 |
| Primäre Persistenz | ArangoDB 3.11+ |
| Zeitreihendaten | TimescaleDB (optional, REQ-005) |
| Cache / Queue | Redis / Valkey |

---

## Dokument-Collections

### Stammdaten (REQ-001)

| Collection | Beschreibung | Wichtige Felder |
|-----------|-------------|----------------|
| `botanical_families` | Botanische Familien | `name` (unique), `common_name` |
| `species` | Pflanzenarten | `scientific_name` (unique), `common_names`, `frost_sensitivity` |
| `cultivars` | Sorten / Varietäten | `name`, `species_key`, genetische Herkunft |
| `lifecycle_configs` | Lebenszyklusdefinitionen pro Art | `species_key`, `lifecycle_type` |
| `growth_phases` | Einzelne Wachstumsphasen | `name`, `order`, `lifecycle_config_key` |
| `requirement_profiles` | Umgebungsanforderungen je Phase | `vpd_target_kpa`, `temperature_day_c`, `ppfd` |
| `nutrient_profiles` | Nährstoffprofile je Phase | `npk_ratio`, `target_ec_ms`, `target_ph` |
| `phase_transition_rules` | Übergangskriterien zwischen Phasen | `from_phase_key`, `to_phase_key`, `trigger_type`, `gdd_threshold` |
| `phase_histories` | Protokoll vergangener Phasenübergänge | `entered_at`, `exited_at`, `actual_duration_days` |

### Standorte und Infrastruktur (REQ-002, REQ-019)

| Collection | Beschreibung | Wichtige Felder |
|-----------|-------------|----------------|
| `sites` | Gärten, Standorte | `name`, `tenant_key`, `location_type` |
| `locations` | Räume, Beete, Zonen | `name`, `parent_location_key`, `depth`, `path` |
| `location_types` | Typen für Standorthierarchie | `name`, `level` (10 System-Seeds) |
| `slots` | Einzelne Pflanzplätze | `slot_id` (unique), `capacity` |
| `substrates` | Substrattypen/-profile | `substrate_type`, `ph_range`, `ec_capacity` |
| `substrate_batches` | Konkrete Substrat-Batches | `cycles_used`, `ph_history`, `irrigation_strategy` |

### Pflanzinstanzen und Durchläufe (REQ-013)

| Collection | Beschreibung | Wichtige Felder |
|-----------|-------------|----------------|
| `plant_instances` | Einzelne Pflanzen | `instance_id` (unique), `current_phase_key`, `sown_at` |
| `planting_runs` | Pflanzdurchläufe (Gruppen) | `name`, `state`, `tenant_key` |
| `planting_run_entries` | Einträge eines Durchlaufs | `species_key`, `planned_count` |

**Zustände eines Pflanzdurchlaufs:**
```
planned → active → harvesting → completed
                             → cancelled
```

### Bewässerung und Düngung (REQ-004, REQ-014)

| Collection | Beschreibung | Wichtige Felder |
|-----------|-------------|----------------|
| `tanks` | Wassertanks | `name` (unique), `capacity_liters`, `tenant_key` |
| `tank_states` | Messzeitpunkt-Snapshots eines Tanks | `ec_ms`, `ph`, `volume_liters`, `recorded_at` |
| `tank_fill_events` | Befüllereignisse | `filled_at`, `water_mix_ratio_ro_percent` |
| `fertilizers` | Dünger-Stammdaten | `product_name`, `brand` (unique je Paar), `mixing_priority` |
| `fertilizer_stocks` | Lagerbestände | `quantity_g`, `expiry_date` |
| `nutrient_plans` | Nährlösungspläne | `name`, `watering_schedule`, `is_template` |
| `nutrient_plan_phase_entries` | Phasenbezogene Plandaten | `phase_name`, `target_ec_ms`, `fertilizer_doses` |
| `feeding_events` | Einzelne Gabe-Ereignisse | `plant_key`, `timestamp`, `ec_ms`, `ph` |
| `watering_events` | Bewässerungsereignisse | `watered_at`, `volume_liters` |
| `watering_logs` | Einheitliches Bewässerungsprotokoll | `logged_at`, `plant_keys[]`, `slot_keys[]` |
| `maintenance_logs` | Wartungsprotokolle für Tanks | `performed_at`, `action` |
| `maintenance_schedules` | Wartungspläne | `interval_days`, `next_due` |

### Pflanzenschutz — IPM (REQ-010)

| Collection | Beschreibung | Wichtige Felder |
|-----------|-------------|----------------|
| `pests` | Schädlings-Stammdaten | `scientific_name` (unique), `common_name` |
| `diseases` | Krankheits-Stammdaten | `scientific_name` (unique) |
| `treatments` | Behandlungsmittel | `name` (unique), `pre_harvest_interval_days` |
| `inspections` | Befallskontrollen | `plant_key`, `inspected_at`, `severity` |
| `treatment_applications` | Durchgeführte Behandlungen | `plant_key`, `treatment_key`, `applied_at` |

### Ernte (REQ-007)

| Collection | Beschreibung | Wichtige Felder |
|-----------|-------------|----------------|
| `harvest_indicators` | Erntereife-Indikatoren je Art | `indicator_type`, `target_value` |
| `harvest_observations` | Beobachtungen zur Reife | `plant_key`, `observed_at` |
| `harvest_batches` | Ernte-Chargen | `batch_id` (unique), `plant_key`, `harvested_at`, `wet_weight_g` |
| `quality_assessments` | Qualitätsbewertungen | `overall_score`, `terpene_profile` |
| `yield_metrics` | Ertragskennzahlen | `dry_weight_g`, `trim_weight_g` |

### Aufgaben und Workflows (REQ-006)

| Collection | Beschreibung | Wichtige Felder |
|-----------|-------------|----------------|
| `workflow_templates` | Wiederverwendbare Workflow-Vorlagen | `name` (unique), `trigger_phase` |
| `task_templates` | Aufgaben-Vorlagen innerhalb Workflows | `title`, `due_offset_days` |
| `tasks` | Konkrete Aufgaben | `plant_key`, `status`, `due_date` |
| `workflow_executions` | Aktive Workflow-Ausführungen | `plant_key`, `started_at` |
| `task_comments` | Kommentare an Aufgaben | `author_key`, `body` |
| `task_audit_entries` | Audit-Trail je Aufgabe | `changed_by`, `change_type` |
| `activities` | Aktivitäts-Stammdaten | `name` (unique) |

### Authentifizierung und Benutzer (REQ-023)

| Collection | Beschreibung | Wichtige Felder |
|-----------|-------------|----------------|
| `users` | Benutzerkonten | `email` (unique), `account_type`, `is_active` |
| `auth_providers` | Verbundene OAuth/OIDC-Provider | `provider`, `provider_user_id` (unique je Paar) |
| `refresh_tokens` | Aktive Sitzungs-Tokens | `token_hash` (unique), `user_key`, `expires_at` |
| `oidc_provider_configs` | OIDC-Provider-Konfigurationen | `slug` (unique), `client_id` |
| `api_keys` | API-Schlüssel für M2M | `key_hash` (unique), `user_key` |

### Mandanten und Mitgliedschaften (REQ-024)

| Collection | Beschreibung | Wichtige Felder |
|-----------|-------------|----------------|
| `tenants` | Mandanten (Gärten, Organisationen) | `slug` (unique), `name` |
| `memberships` | Nutzer-Mandant-Beziehungen | `user_key`, `tenant_key` (unique je Paar), `role` |
| `invitations` | Einladungen zu Mandanten | `token_hash` (unique), `tenant_key`, `expires_at` |
| `location_assignments` | Zuweisungsbasierte Schreibrechte | `membership_key`, `location_key` (unique je Paar) |

**Rollen je Mandant:** `admin`, `grower`, `viewer`

### Pflegeerinnerungen (REQ-022)

| Collection | Beschreibung | Wichtige Felder |
|-----------|-------------|----------------|
| `care_profiles` | Pflegeprofil je Pflanzinstanz | `care_style`, `watering_interval_days` |
| `care_confirmations` | Bestätigte Pflegeereignisse | `reminder_type`, `confirmed_at` |

### Onboarding (REQ-020)

| Collection | Beschreibung | Wichtige Felder |
|-----------|-------------|----------------|
| `starter_kits` | Vorkonfigurierte Starter-Sets | `kit_id` (unique), `difficulty`, `sort_order` |
| `onboarding_states` | Fortschritt des Onboarding-Wizards | `user_key`, `completed_at` |
| `user_preferences` | Nutzerpräferenzen | `expertise_level`, `show_all_fields` |
| `user_favorites` | Favorisierte Arten, Pläne, Dünger | `_from` (user), `_to` (target entity) |

### Sonstiges

| Collection | Beschreibung |
|-----------|-------------|
| `sensors` | Sensor-Definitionen (REQ-005) |
| `import_jobs` | CSV-Import-Aufträge (REQ-012) |
| `calendar_feeds` | iCal-Feed-Konfigurationen (REQ-015) |
| `system_settings` | Systemweite Einstellungen (Singleton) |
| `external_sources` | Externe Datenquellen (GBIF, Perenual) |
| `external_mappings` | Mappings interne ↔ externe IDs |
| `sync_runs` | Protokoll der Anreicherungs-Läufe |

---

## Kanten-Collections (Graph-Beziehungen)

### Stammdaten-Graph

| Kante | Von | Nach | Bedeutung |
|-------|-----|------|----------|
| `belongs_to_family` | `species` | `botanical_families` | Art gehört zur Familie |
| `has_cultivar` | `species` | `cultivars` | Art hat Sorte |
| `has_lifecycle` | `species` | `lifecycle_configs` | Art hat Lebenszyklus |
| `consists_of` | `lifecycle_configs` | `growth_phases` | Lebenszyklus besteht aus Phasen |
| `next_phase` | `growth_phases` | `growth_phases` | Phasenreihenfolge |
| `governed_by` | `growth_phases` | `phase_transition_rules` | Phase hat Übergangsregeln |
| `requires_profile` | `growth_phases` | `requirement_profiles` | Phase hat Umgebungsanforderungen |
| `uses_nutrients` | `growth_phases` | `nutrient_profiles` | Phase hat Nährstoffprofil |
| `compatible_with` | `species` | `species` | Mischkultur-Kompatibilität |
| `incompatible_with` | `species` | `species` | Mischkultur-Unverträglichkeit |
| `rotation_after` | `botanical_families` | `botanical_families` | Fruchtfolge-Empfehlung |

### Standort-Graph

| Kante | Von | Nach | Bedeutung |
|-------|-----|------|----------|
| `contains` | `sites`, `locations` | `locations` | Hierarchische Containment-Beziehung |
| `has_slot` | `locations` | `slots` | Standort hat Pflanzplätze |
| `filled_with` | `slots` | `substrate_batches` | Slot ist mit Substrat befüllt |
| `adjacent_to` | `slots` | `slots` | Benachbarte Pflanzplätze (für Mischkultur) |

### Pflanzinstanz-Graph

| Kante | Von | Nach | Bedeutung |
|-------|-----|------|----------|
| `placed_in` | `plant_instances` | `slots` | Pflanze steht in Slot |
| `grown_in` | `plant_instances` | `substrate_batches` | Pflanze wächst in Substrat |
| `current_phase` | `plant_instances` | `growth_phases` | Aktuelle Phase der Pflanze |
| `phase_history_edge` | `plant_instances` | `phase_histories` | Phasenhistorie der Pflanze |
| `follows_plan` | `plant_instances` | `nutrient_plans` | Pflanze folgt Nährlösungsplan |

### Pflanzdurchlauf-Graph

| Kante | Von | Nach | Bedeutung |
|-------|-----|------|----------|
| `run_contains` | `planting_runs` | `plant_instances` | Durchlauf enthält Pflanzen |
| `run_at_location` | `planting_runs` | `locations` | Durchlauf am Standort |
| `run_uses_substrate` | `planting_runs` | `substrate_batches` | Durchlauf verwendet Substrat |
| `has_entry` | `planting_runs` | `planting_run_entries` | Durchlauf hat Einträge |
| `run_follows_plan` | `planting_runs` | `nutrient_plans` | Gießplan-Zuordnung |

### Tank- und Düngungsgraph

| Kante | Von | Nach | Bedeutung |
|-------|-----|------|----------|
| `has_tank` | `locations` | `tanks` | Standort hat Tank |
| `supplies` | `tanks` | `locations` | Tank versorgt Standort |
| `feeds_from` | `tanks` | `tanks` | Tank-zu-Tank-Kaskade |
| `has_state` | `tanks` | `tank_states` | Tank-Zustandsprotokolle |
| `has_fill_event` | `tanks` | `tank_fill_events` | Tank-Befüllereignisse |
| `mixed_into` | `nutrient_plans` | `tank_fill_events` | Nährlösung in Befüllereignis |
| `fert_incompatible` | `fertilizers` | `fertilizers` | Inkompatible Dünger-Paare |
| `has_component` | `fertilizers` | `fertilizers` | Multi-Komponenten-Dünger |
| `has_stock` | `fertilizers` | `fertilizer_stocks` | Lagerbestand |
| `fed_by` | `plant_instances` | `feeding_events` | Pflanze wurde gedüngt |
| `feeding_used` | `feeding_events` | `fertilizers` | Gabe verwendete Dünger |
| `has_phase_entry` | `nutrient_plans` | `nutrient_plan_phase_entries` | Plan hat Phaseneinträge |
| `plan_uses_fertilizer` | `nutrient_plan_phase_entries` | `fertilizers` | Planeintrag verwendet Dünger |

### IPM-Graph

| Kante | Von | Nach | Bedeutung |
|-------|-----|------|----------|
| `inspected_by` | `plant_instances` | `inspections` | Befallskontrollen |
| `detected_pest` | `inspections` | `pests` | Festgestellter Schädling |
| `detected_disease` | `inspections` | `diseases` | Festgestellte Krankheit |
| `applied_to_plant` | `treatment_applications` | `plant_instances` | Behandlung an Pflanze |
| `treatment_uses` | `treatment_applications` | `treatments` | Behandlung verwendet Mittel |
| `targets_pest` | `treatments` | `pests` | Mittel wirkt gegen Schädling |
| `contraindicated_with` | `treatments` | `treatments` | Mittel nicht kombinierbar |
| `vulnerable_in_phase` | `growth_phases` | `pests`, `diseases` | Anfälligkeit je Phase |

### Ernte-Graph

| Kante | Von | Nach | Bedeutung |
|-------|-----|------|----------|
| `has_harvest_indicator` | `species` | `harvest_indicators` | Ernteindikatoren je Art |
| `observed_for_harvest` | `plant_instances` | `harvest_observations` | Reife-Beobachtungen |
| `harvested_as` | `plant_instances` | `harvest_batches` | Pflanze wurde zur Charge |
| `assessed_by_quality` | `harvest_batches` | `quality_assessments` | Qualitätsbewertung |
| `has_yield_metric` | `harvest_batches` | `yield_metrics` | Ertragsmetriken |

### Aufgaben-Graph

| Kante | Von | Nach | Bedeutung |
|-------|-----|------|----------|
| `wf_contains` | `workflow_templates` | `task_templates` | Workflow enthält Aufgabenvorlagen |
| `has_task` | `plant_instances` | `tasks` | Pflanze hat offene Aufgabe |
| `task_blocks` | `tasks` | `tasks` | Aufgabe blockiert Folgeaufgabe |
| `instance_of` | `tasks` | `task_templates` | Aufgabe ist Instanz einer Vorlage |
| `task_assigned_to` | `tasks` | `users` | Aufgabe zugewiesen an Nutzer |
| `task_uses_activity` | `tasks`, `task_templates` | `activities` | Aufgabe ist eine Aktivität |

### Mandanten-Graph

| Kante | Von | Nach | Bedeutung |
|-------|-----|------|----------|
| `has_membership` | `tenants` | `memberships` | Mandant hat Mitgliedschaften |
| `membership_in` | `users` | `memberships` | Nutzer hat Mitgliedschaft |
| `belongs_to_tenant` | `sites`, `plant_instances`, `planting_runs`, `tanks`, `fertilizers`, `nutrient_plans`, `tasks` | `tenants` | Ressource gehört zu Mandant |
| `assigned_to_location` | `location_assignments` | `locations` | Zuweisungsbasierter Standortzugriff |

---

## Indizes

Kamerplanter legt beim Start automatisch folgende Indizes an:

| Collection | Index-Feld | Typ | Eindeutig |
|-----------|-----------|-----|----------|
| `species` | `scientific_name` | Hash | Ja |
| `botanical_families` | `name` | Hash | Ja |
| `slots` | `slot_id` | Hash | Ja |
| `plant_instances` | `instance_id` | Hash | Ja |
| `users` | `email` | Hash | Ja |
| `tenants` | `slug` | Hash | Ja |
| `memberships` | `user_key, tenant_key` | Hash | Ja |
| `fertilizers` | `product_name, brand` | Hash | Ja |
| `harvest_batches` | `batch_id` | Hash | Ja |
| `tanks` | `name` | Hash | Ja |
| `refresh_tokens` | `token_hash` | Hash | Ja |
| `calendar_feeds` | `token` | Hash | Ja |
| `tasks` | `status`, `plant_key` | Hash | Nein |
| `feeding_events` | `plant_key`, `timestamp` | Hash | Nein |

---

## Datenisolierung durch Mandanten

Alle mandantengebundenen Ressourcen tragen ein `tenant_key`-Feld. Der FastAPI-Dependency `require_permission()` prüft beim Zugriff automatisch, ob der anfragende Nutzer Mitglied des entsprechenden Mandanten ist.

**Globale Ressourcen** (ohne Mandantenbindung): `species`, `cultivars`, `botanical_families`, `pests`, `diseases`, `treatments`, `starter_kits`

**Mandantengebundene Ressourcen**: `sites`, `locations`, `plant_instances`, `planting_runs`, `tanks`, `fertilizers`, `nutrient_plans`, `tasks`

---

## Technische Hinweise für Entwickler

- Collections und der Named Graph werden beim Backend-Start durch `ensure_collections()` automatisch erstellt und migriert.
- Neue Collections oder Kanten-Definitionen in `collections.py` eintragen — beim nächsten Start werden sie angelegt.
- AQL-Queries verwenden ausschließlich `FOR ... IN GRAPH kamerplanter_graph` für Graph-Traversals.
- `_key` und `_id` sind ArangoDB-interne Identifikatoren. Anwendungsschlüssel (z. B. `instance_id`) sind separate Felder mit Hash-Index.

---

## Siehe auch

- [API-Referenz](api-reference.md)
- [Umgebungsvariablen](environment-variables.md)
- [Backend-Architektur](../architecture/backend.md)
