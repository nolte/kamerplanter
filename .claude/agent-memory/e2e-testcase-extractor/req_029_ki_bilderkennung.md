---
name: REQ-029 KI-Bilderkennung — UI Patterns and Test Insights
description: Key insights for extracting E2E test cases from REQ-029 (Plant.id optional integration)
type: project
---

## REQ-029 KI-Bilderkennung — UI Patterns and Key Test Insights

- Spec: `spec/req/REQ-029_KI-Bilderkennung-Pflanzenidentifikation.md` (v1.0, 1615 lines, Entwurf status)
- Output: `spec/e2e-testcases/TC-REQ-029.md` with 58 test cases

**Implementation Status (2026-03-21):** NOT YET IMPLEMENTED. All 58 test cases are spec-forward.

**Feature-Toggle Pattern:**
- `GET /api/v1/t/{slug}/identification/status` returns per-adapter `{configured, healthy, supports_health, rate_limit_per_day}`
- No API key → all camera buttons hidden, app fully functional without feature
- Plant.id key → Artbestimmung + Krankheitsdiagnose; PlantNet key only → Artbestimmung only
- Toggle decision: key configured? → button visible; not configured? → button absent (no disabled state shown)

**Consent Pattern (DSGVO-specific to REQ-029):**
- Consent purpose: `plant_identification` (optional, Art.6(1)(a))
- First click on any camera button → Consent-Dialog with i18n key `pages.identification.consentTitle`
- Accept → dialog opens, Decline → dialog closes, camera button stays visible for retry
- Revoke via Einstellungen → Datenschutz toggle → buttons hidden again
- History remains after revoke (no image data stored — only metadata)

**Confidence Threshold Logic (UI-visible):**
- `CONFIDENCE_AUTO_ACCEPT = 0.85` → item shown without uncertainty warning
- `CONFIDENCE_SHOW_RESULTS = 0.10` → items below this filtered out silently
- Below 0.85 → uncertainty banner: "Die Erkennung ist unsicher. Bitte prüfen Sie die Vorschläge."
- Beginner: confidence values HIDDEN; Intermediate: shown as %; Expert: % + raw decimal + GBIF link + expandable JSON

**File Validation (UI-visible errors):**
- Max size: 5 MB (configurable via `IDENTIFICATION_MAX_IMAGE_SIZE_MB`)
- Accepted formats: JPEG, PNG only (GIF/WebP/HEIC rejected with error message)
- Boundary test: exactly 5 MB accepted (5242880 bytes)

**PlantIdentificationDialog Elements:**
- Title: "Pflanze identifizieren" (`pages.identification.title`)
- Kamera-Button: "Foto aufnehmen" (`takePhoto`)
- Upload-Zone: "Foto hochladen" (`uploadPhoto`) + Drag & Drop on desktop
- Loading state: "Pflanze wird analysiert..." (`analyzing`)
- Organ chips (Intermediate/Expert only): Blatt, Blüte, Frucht, Rinde, Ganze Pflanze, Automatisch erkennen
- Result card: name + confidence bar + reference image + "Diese Pflanze anlegen" or "Art hinzufügen und Pflanze anlegen"
- Manual fallback link: "Pflanze nicht dabei? Manuell suchen" (`manualSearch`)
- Error states: `notAPlant`, `noResults`, `rateLimitReached`, `notConfigured`

**Diagnose Tab (Health Assessment):**
- Only visible when Plant.id configured (PlantNet: no health assessment)
- i18n: `diagnoseTitle`, `diagnoseButton`, `diagnoseAnalyzing`, `diagnoseHealthy`, `diagnoseDiseases`, `diagnoseTreatment`, `diagnoseSeverity`
- IPM match: local Disease/Pest from REQ-010 matched by scientific name → local treatment suggestions shown
- Without IPM match: external treatment text from Plant.id shown

**Rate-Limit UI:**
- Per-user daily limit: 100 (Plant.id free), 500 (PlantNet)
- Burst: 5 requests / 10 seconds
- Rate-limit hit → "Tages-Limit für Bilderkennung erreicht. Morgen wieder verfügbar." (`rateLimitReached`)
- PlantNet auto-fallback when Plant.id rate-limit hit (if both configured)

**Integration Entry Points (4 locations):**
1. Stammdaten-Übersicht → FAB "Pflanze per Foto hinzufügen"
2. PlantInstance-Detail → "Per Foto identifizieren" (only when species not set)
3. IPM-Inspektions-Dialog (REQ-010) → "Foto-Diagnose" button
4. Pflege-Dashboard (REQ-022) → Quick-Action "Pflanze krank?"

**Onboarding-Integration (REQ-020):**
- Optional Schritt 0 appears BEFORE kit selection
- Only for Beginner + Intermediate (not Expert — spec §4.2)
- Only shown when `identification_status.available == true`
- Skip button always available
- Flow: Photo → Consent → Identify → Select result → PlantInstance + CareProfile created within wizard

**Cross-req Dependencies for Test Preconditions:**
- Species in Stammdaten (REQ-001): needed for "species_in_database = true" tests
- Disease/Pest in IPM (REQ-010): needed for Diagnose-IPM-Match tests
- PlantInstance without species: needed for "Per Foto identifizieren" button test
- Consent system (REQ-025): PrivacySettingsPage `/settings/privacy` must show `plant_identification` toggle

**Spec Sections Most Valuable for Test Extraction:**
- §1.2 + §1.3: Workflow diagrams (box-arrow diagrams → happy path journey tests)
- §3.5: IdentificationEngine constants (thresholds, max size — all UI-visible as validation errors)
- §4.1: Dialog element table (exhaustive UI element list)
- §4.2: Integration table (which pages get camera buttons and under what conditions)
- §4.3: Expertise level table (3×7 matrix → Beginner/Intermediate/Expert visibility tests)
- §4.4: i18n keys (exact German strings for test assertions)
- §9 Szenarien 1-10: maps directly to TC-029-020 to TC-029-058

**EXIF-Stripping (not directly testable in browser):**
- Technical measure, no UI element confirms it
- Proxy test: Consent-Dialog text mentions "Das Bild wird dort nicht dauerhaft gespeichert." (§5.4)
- History shows no uploaded images (only metadata + external reference URLs from Plant.id)
