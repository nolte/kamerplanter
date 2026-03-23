---
name: REQ-001 Stammdatenverwaltung — UI Patterns and Test Insights
description: Key patterns, validation rules, and Stammdaten-Scoping v4.0 test notes for TC-REQ-001
type: project
---

## REQ-001 v4.0 — Output and Coverage

- Output: `spec/e2e-testcases/TC-REQ-001.md`, 78 test cases, IDs TC-001-001 to TC-001-078
- Replaces previous version (62 test cases) with v4.0 Stammdaten-Scoping coverage

## Frontend Pages and Routes

- `/stammdaten/botanical-families` → BotanicalFamilyListPage
- `/stammdaten/botanical-families/:key` → BotanicalFamilyDetailPage (edit + delete + species list)
- `/stammdaten/species` → SpeciesListPage
- `/stammdaten/species/:key` → SpeciesDetailPage (5 tabs: Bearbeiten, Anbauperioden, Sorten, Lebenszyklus-Konfiguration, Workflows)
- `/stammdaten/species/:speciesKey/cultivars/:cultivarKey` → CultivarDetailPage
- `/stammdaten/crop-rotation` → CropRotationPage
- `/stammdaten/companion-planting` → CompanionPlantingPage (see REQ-028 notes)
- `/stammdaten/import` → ImportPage (REQ-012 connection)

## Client-Side Zod Validation Rules

BotanicalFamily (BotanicalFamilyCreateDialog + BotanicalFamilyDetailPage):
- `name`: min(1) + refine `v.endsWith('aceae')` — error: "Muss auf '-aceae' enden"
- `order`: validated BACKEND-ONLY (must end '-ales') — no client-side regex; Zod just validates it's a string
- `typical_growth_forms`: array min(1)
- `pollination_type`: array min(1)
- `soil_ph_min/max`: `z.union([z.number().min(3).max(9), z.literal('')])` — empty string = not set, fully optional

Species (SpeciesCreateDialog + SpeciesDetailPage):
- `scientific_name`: min(1) — binomial/hybrid validation is BACKEND ONLY
- `allelopathy_score`: min(-1).max(1)
- `family_key`: nullable

Cultivar (CultivarCreateDialog):
- `name`: min(1)
- `days_to_maturity`: nullable, z.number().min(1).max(365)
- `traits`: array of strings — BACKEND validates against valid_traits set
- Autoflower fields: NOT in current CultivarCreateDialog schema (spec-forward tests TC-001-040 to TC-001-043)

## Stammdaten-Scoping v4.0 — Key Test Patterns

- tenant_has_access Edge (Species→Tenant): controls which global species a tenant sees
- Cultivar access is TRANSITIVE: tenant with access to Species sees all its Cultivars automatically
- BotanicalFamily is NEVER filtered by tenant (always global)
- TenantSpeciesConfig.hidden = true: hides species from tenant without removing tenant_has_access edge
- Merge-Logik: API response has `has_overlay: bool` indicating if Tenant overlay is active
- Promotion (Szenario 12): KA-Admin can promote origin:'tenant' → origin:'system', tenant_key: null in-place
- TC-001-060 (has_overlay indicator) and TC-001-061 (hidden-Flag) are SPEC-FORWARD — may require Admin UI not yet implemented

## Spec-Forward Test Cases in TC-REQ-001

- TC-001-040 to TC-001-043: Autoflower Cultivar fields (photoperiod_type, autoflower_days_to_flower, autoflower_total_cycle_days) — NOT in current CultivarCreateDialog Zod schema
- TC-001-060: has_overlay Indikator on Species detail — overlay indication may not be visible yet
- TC-001-062: Promotion UI button — may not exist yet in SpeciesDetailPage
- TC-001-063: Platform-Admin write restriction — depends on REQ-024 auth implementation
- TC-001-070 to TC-001-072: ToxicityInfo / AllergenInfo display — may not be shown in current SpeciesDetailPage
- TC-001-073 to TC-001-074: Vermehrungsmethoden display — may not be shown in current SpeciesDetailPage

## Seed-Data Concrete Values for Test Preconditions

9 Base BotanicalFamilies: Solanaceae(heavy,MEDIUM,SENSITIVE,INSECT+SELF), Brassicaceae(heavy,MEDIUM,HARDY,INSECT),
Fabaceae(light,nitrogen_fixing=true,DEEP,MODERATE,INSECT+SELF), Cucurbitaceae(heavy,SHALLOW,SENSITIVE,INSECT),
Apiaceae(medium,DEEP,HARDY,INSECT), Asteraceae(medium,MEDIUM,MODERATE,INSECT+WIND),
Poaceae(medium,SHALLOW,VERY_HARDY,WIND+SELF), Lamiaceae(light,SHALLOW,MODERATE,INSECT),
Cannabaceae(heavy,DEEP,SENSITIVE,WIND)

4 Zierpflanzen BotanicalFamilies: Geraniaceae, Campanulaceae, Balsaminaceae, Primulaceae

Key rotation_after edges for test preconditions:
- Fabaceae→Solanaceae (0.95, nitrogen_fixation)
- Fabaceae→Brassicaceae (0.90, nitrogen_fixation)
- Solanaceae↔Cucurbitaceae shares_pest_risk: Blattläuse/Weiße Fliege, risk_level=medium
- Brassicaceae→Fabaceae (0.85, soil_structure)

## i18n Label Mapping (pages.botanicalFamilies.*)

- create: "Familie erstellen"
- name: "Name", nameHelper: "Botanischer Familienname, muss auf '-aceae' enden (z. B. 'Solanaceae')"
- nitrogenFixing: "Stickstofffixierend"
- soilPhMin: "pH-Minimum", soilPhMax: "pH-Maximum"
- speciesInFamily: "Arten in dieser Familie"
- showAllSpeciesFiltered: "Alle Arten dieser Familie anzeigen"
- noSpeciesInFamily: "Dieser Familie sind noch keine Arten zugeordnet."

## Why: REQ-001 is the foundation spec for all other modules

All REQ-002 through REQ-012 depend on REQ-001 Stammdaten. Changes to BotanicalFamily, Species, or Cultivar
entities cascade to crop rotation (REQ-002), phase transitions (REQ-003), nutrient plans (REQ-004),
IPM pest matching (REQ-010), and companion planting (REQ-028). Test cases here form the baseline
data layer for E2E tests in all other requirement areas.

**How to apply**: When writing or updating tests for REQ-002 through REQ-012, use the seed-data values
from this doc as precondition setup. Assume TC-001-006 (create BotanicalFamily) and TC-001-025 (create Species)
can be used as setup helpers.
