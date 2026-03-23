---
name: REQ-020 Onboarding-Wizard — UI Patterns and Key Test Insights
description: Test patterns for the multi-step onboarding wizard (REQ-020 v1.6)
type: project
---

## Key Facts
- Route: `/onboarding`, Component: `OnboardingWizard.tsx`, `data-testid="onboarding-wizard"`
- 53 test cases in `spec/e2e-testcases/TC-REQ-020.md`
- Output path: `spec/e2e-testcases/TC-REQ-020.md`

## Dynamic Step Count (Critical)
- Steps: experience → kit → favorites → site → [plants] → [nutrientPlans] → summary
- `plants` step added ONLY when `experienceLevel !== 'beginner'`
- `nutrientPlans` step added ONLY when `favoriteSpeciesKeys.length > 0` AND plans exist
- Beginner: 5 steps total; Intermediate with favorites: 7 steps

## data-testid Inventory
- `onboarding-wizard` — root container
- `onboarding-step-welcome` — step 1
- `onboarding-step-kit` — step 2
- `onboarding-step-favorites` — step 3
- `onboarding-step-site` — step 4
- `onboarding-step-plant-selection` — step 5
- `onboarding-step-nutrient-plans` — step 6
- `onboarding-step-complete` — summary step
- `experience-beginner`, `experience-intermediate`, `experience-expert` — step 1 cards
- `smart-home-toggle` — only visible when experienceLevel != 'beginner'
- `kit-{kit_id}` — e.g. `kit-fensterbank-kraeuter`
- `favorites-search` — search in step 3
- `favorite-tile-{species.key}` — e.g. `favorite-tile-species/ocimum-basilicum`
- `site-option-new`, `site-option-{site.key}` — step 4 site cards
- `site-name-field`, `site-type-select`
- `onboarding-tap-ec`, `onboarding-tap-ph`, `onboarding-ro-toggle` — water fields (intermediate+ only)
- `plant-config-{species.key}`, `plant-count-minus-{key}`, `plant-count-input-{key}`, `plant-count-plus-{key}`, `plant-phase-select-{key}`
- `onboarding-next`, `onboarding-back`, `onboarding-complete`, `skip-onboarding`
- `onboarding-restart`, `onboarding-go-dashboard` — on completed/skipped card

## Smart-Home Toggle (v1.6)
- Hidden for `beginner`; visible for `intermediate` and `expert`
- Default: off (`smart_home_enabled == false`)
- When activated: hint text changes to "...Live-Messwerte werden verfügbar"
- Persists as `UserPreference.smart_home_enabled`

## Wasserquellen-Abschnitt (v1.1)
- Only visible in site step when `experienceLevel !== 'beginner'`
- Fields: tap_water_ec_ms (0–2.0 mS/cm), tap_water_ph (3–10), has_ro_system (Switch)
- Constraint from frontend inputProps: ec max=2.0, ph max=10.0

## Resume Functionality
- `onboarding_state.wizard_step > 0` → resume from that step
- Restored values: step number, experienceLevel, selectedKitId, siteName, siteType, selectedSiteKey, plant_configs

## Auto-Populate on Kit Selection
- Site type → set from kit.site_type
- Site name → set from i18n `pages.onboarding.siteNameDefault.{site_type}` UNLESS manually changed
- Plant configs → kit.plant_count_suggestion distributed evenly across kit.species_keys
- Favorites → all kit.species_keys pre-selected as favorites

## Completed/Skipped State
- Shows a Card (not the stepper) with "already completed" message
- Buttons: `onboarding-restart` (resets and shows wizard), `onboarding-go-dashboard` (navigates to /dashboard)
- After `handleRestart`: all wizard state reset to defaults

## Moduswechsel Behavior
- Szenario A (Light→Full, Übernahme): onboarding_state.completed=true → no wizard, show completed card
- Szenario B (Light→Full, Ablehnung): onboarding_state.completed=false → wizard auto-starts
- Szenario C/D/E: Admin-UI dependent (REQ-027 not yet implemented, test cases skipped)

## Tenant-Scoped Kit Filtering
- `GET /api/v1/t/{slug}/starter-kits` filters by tenant_has_access
- Kit with 0 available species → hidden from list
- Kit with partial species → shows available count in species_count chip
- Unavailable species in favorites step → greyed out / not interactive

## Seed Kit IDs (for test preconditions)
fensterbank-kraeuter, balkon-tomaten, kleines-gemusebeet, zimmerpflanzen,
zimmerpflanzen-haustierfreundlich, indoor-growzelt, chili-zucht, superhot-chili,
microgreens, balkon-blumen, balkon-blumen-voranzucht

## Toxicity Kits (show warning chip)
zimmerpflanzen (warning/cats+dogs+children), indoor-growzelt (danger/children),
balkon-tomaten+kleines-gemusebeet+balkon-blumen (caution/cats+dogs)

## Abschluss-Flow
1. Click `onboarding-complete` → submitting=true, all buttons disabled
2. Success → SnackBar `pages.onboarding.complete` + navigate to `/pflanzen/plant-instances`
3. Error → SnackBar error + wizard stays on summary step, button re-enabled

## Not Testable via E2E
- "Under 3 minutes" → performance/UX test
- Konfetti-Animation after completion → optional visual feature
- i18n EN-Locale → separate test run
- Moduswechsel C/D/E → requires REQ-027 Admin UI
