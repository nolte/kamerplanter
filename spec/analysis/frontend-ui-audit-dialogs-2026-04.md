# Frontend UI Audit — Dialogs & Wizards (April 2026)

**Companion Report to:** `spec/analysis/frontend-ui-audit-2026-04.md`
**Audit Scope:** 51 Create/Edit Dialog and Wizard files
**Audit Date:** 2026-04-25
**Auditor:** Claude Code (read-only walkthrough, no code changes)
**Spec Basis:** UI-NFR-008 v1.3, UI-NFR-001 v2.0, UI-NFR-004, UI-NFR-002, UI-NFR-007, UI-NFR-011

---

## Executive Summary

The 51 dialog and wizard files were audited in full read-only mode against the UI-NFR specifications. The majority of dialogs follow the mobile-first `fullScreen` pattern and use `react-hook-form` with `zodResolver` as the mandated form pattern. However, three systemic issues affect most dialogs: (1) missing `aria-labelledby` on the Dialog root element (affects ~60% of files), (2) missing `data-testid` on the Dialog root element (affects ~55% of files), and (3) Unicode escape sequences for special characters in violation of R-049 (affects at least 9 files). Additionally, the two most complex dialogs in the `duengung` module (`ChannelFertilizerDialog` and `DeliveryChannelDialog`) bypass the mandatory `react-hook-form + Zod` pattern in favour of raw `useState` chains, which constitutes a medium-severity conformance violation. A further issue isolated to `AdoptPlantsDialog` is the display of a raw `current_phase` enum value in a Chip component without `t()` wrapping. Positive highlights include consistently good `helperText` coverage on numeric Fachbegriff fields (EC, pH, VPD, PPFD), widespread use of `FormActions` for Double-Submit-Schutz, and several dialogs (`ProfileEditDialog`, `PlantingRunEditDialog`, `TankCreateDialog`, `TankFillCreateDialog`) achieving a high level of conformance.

---

## Overview Table (51 Files)

| # | File | Status | fullScreen | RHF+Zod | autoFocus | aria-labelledby | data-testid (Dialog) | Notable Issues |
|---|------|--------|-----------|---------|-----------|-----------------|---------------------|----------------|
| 1 | components/common/ConfirmDialog.tsx | 🟢 | ✓ | N/A | ✓ (cancel) | ✓ | ✓ | Minor: no spinner on loading state |
| 2 | components/print/PlantLabelDialog.tsx | 🟢 | ✓ | N/A | — | ✓ (useId) | ✓ | Good Info-Icon pattern |
| 3 | pages/aufgaben/TaskCreateDialog.tsx | 🟡 | ✓ | ✓ | ✓ | ✗ | ✗ | D-001, D-002, D-004 (DeleteIcon) |
| 4 | pages/aufgaben/TaskTemplateDialog.tsx | 🟡 | ✓ | ✓ | ✓ | ✓ | ✗ | D-001 |
| 5 | pages/aufgaben/WorkflowCreateDialog.tsx | 🟡 | ✓ | ✓ | ✓ | ✗ | ✗ | D-001, D-002 |
| 6 | pages/aufgaben/WorkflowInstantiateDialog.tsx | 🟡 | ✓ | N/A | — | ✗ | ✗ | D-001, D-002, D-007 (hardcoded strings) |
| 7 | pages/aufgaben/WorkflowPhaseDialog.tsx | 🟡 | ✓ | ✓ | edit-only | ✓ | ✗ | D-001, D-003 (line 405), D-009 |
| 8 | pages/duengung/ChannelFertilizerDialog.tsx | 🔴 | ✓ | ✗ (useState) | ✗ | ✗ | ✗ | D-001, D-002, D-004, D-006 |
| 9 | pages/duengung/DeliveryChannelDialog.tsx | 🔴 | ✓ | ✗ (useState) | ✗ | ✗ | ✗ | D-001, D-002, D-003 (line 371), D-006 |
| 10 | pages/duengung/FeedingEventCreateDialog.tsx | 🟡 | ✓ | ✓ | ✗ | ✗ | ✗ | D-001, D-002, D-004 (DeleteIcon), D-009 |
| 11 | pages/duengung/FertilizerCreateDialog.tsx | 🟡 | ✓ | ✓ | ✓ | ✗ | ✗ | D-001, D-002 |
| 12 | pages/duengung/NutrientPlanAssignDialog.tsx | 🟢 | ✓ | N/A | — | ✗ | ✓ | D-002; otherwise exemplary pick-list |
| 13 | pages/duengung/NutrientPlanCreateDialog.tsx | 🟡 | ✓ | ✓ | ✓ | ✗ | ✗ | D-001, D-002 |
| 14 | pages/duengung/PhaseEntryDialog.tsx | 🟡 | ✓ | ✓ | ✗ | ✗ | ✗ | D-001, D-002, D-008 (NPK fields), D-009 |
| 15 | pages/durchlaeufe/AdoptPlantsDialog.tsx | 🟡 | ✓ | N/A | — | ✗ | ✓ | D-002, D-005 (raw enum in Chip) |
| 16 | pages/durchlaeufe/BatchPhaseTransitionDialog.tsx | 🟡 | ✓ | N/A | — | ✗ | ✓ | D-002 |
| 17 | pages/durchlaeufe/PlantingRunCreateDialog.tsx | 🟡 | ✓ | ✓ | ✗ | ✗ | ✗ | D-001, D-002, D-003 (lines 161, 399), D-009 |
| 18 | pages/durchlaeufe/PlantingRunEditDialog.tsx | 🟢 | ✓ | ✓ | ✓ | ✗ | ✓ | D-002, D-003 (line 159) |
| 19 | pages/durchlaeufe/WateringConfirmDialog.tsx | 🟡 | ✓ | ✓ | ✗ | ✗ | ✓ | D-002, D-008 (EC/pH no HelpTooltip), D-009 |
| 20 | pages/ernte/HarvestCreateDialog.tsx | 🟡 | ✓ | ✓ | ✓ | ✗ | ✗ | D-001, D-002 |
| 21 | pages/ernte/ObservationCreateDialog.tsx | 🟡 | ✓ | ✓ | ✓ | ✗ | ✗ | D-001, D-002, D-003 (line 127) |
| 22 | pages/giessprotokoll/WateringLogCreateDialog.tsx | 🟡 | ✓ | ✓ | ✓ | ✗ | ✗ | D-001, D-002; good responsive grid layout |
| 23 | pages/onboarding/OnboardingWizard.tsx | 🟢 | N/A (page) | Redux+manual | — | N/A | ✓ | D-010 (wizard-specific); good mobile/desktop split |
| 24 | pages/pflanzen/GrowthPhaseDialog.tsx | 🟡 | ✓ | ✓ | — | ✗ | ✓ (generic) | D-002, D-011 (generic data-testid) |
| 25 | pages/pflanzen/PhaseTransitionDialog.tsx | 🟡 | ✓ | ✗ (useState) | ✗ | ✗ | ✓ | D-002, D-009; manual state acceptable (non-standard form) |
| 26 | pages/pflanzen/PlantInstanceCreateDialog.tsx | 🟡 | ✓ | ✓ | ✗ | ✗ | ✗ | D-001, D-002, D-003 (lines 162, 284, 351, 353), D-009 |
| 27 | pages/pflanzen/PlantTagDialog.tsx | 🟢 | ✓ | N/A | — | ✗ | ✓ | D-002; url truncation acceptable (secondary) |
| 28 | pages/pflanzen/ProfileEditDialog.tsx | 🟢 | ✓ | ✓ | ✓ | ✗ | ✓ | D-002, D-003 (labels line 159: `μ`, `²`, `₂`) |
| 29 | pages/pflanzenschutz/DiseaseCreateDialog.tsx | 🟡 | ✓ | ✓ | ✗ | ✗ | ✗ | D-001, D-002, D-009 |
| 30 | pages/pflanzenschutz/PestCreateDialog.tsx | 🟡 | ✓ | ✓ | ✓ | ✗ | ✗ | D-001, D-002, D-003 (`°C` lines 142, 148) |
| 31 | pages/pflanzenschutz/TreatmentCreateDialog.tsx | 🟡 | ✓ | ✓ | ✓ | ✗ | ✗ | D-001, D-002 |
| 32 | pages/pflege/components/CareConfirmDialog.tsx | 🟡 | ✓ | ✗ (useState) | ✗ | ✗ | ✗ | D-001, D-002, D-004 (DeleteIcon), D-009; manual state acceptable (confirm dialog, not a create form) |
| 33 | pages/pflege/components/CareProfileEditDialog.tsx | 🟢 | ✓ | ✗ (useState) | — | ✗ | ✓ | D-002, D-004 (no aria-label on ExpandMore/ExpandLess); Slider/Switch UI justified |
| 34 | pages/phasen/PhaseDefinitionDialog.tsx | 🟢 | ✓ | ✓ | ✓ | ✓ | ✗ | D-001 only |
| 35 | pages/phasen/PhaseSequenceEntryDialog.tsx | 🟢 | ✓ | ✓ | — | ✓ | ✗ | D-001 only |
| 36 | pages/stammdaten/ActivityCreateDialog.tsx | 🟡 | ✓ | ✓ | ✓ | ✗ | ✓ (generic) | D-002, D-011 (generic `data-testid="create-dialog"`) |
| 37 | pages/stammdaten/BotanicalFamilyCreateDialog.tsx | 🟡 | ✓ | ✓ | ✓ | ✗ | ✓ (generic) | D-002, D-011 (generic `data-testid="create-dialog"`), F-011 (hardcoded Zod message) |
| 38 | pages/stammdaten/CultivarCreateDialog.tsx | 🟡 | ✓ | ✓ | ✓ | ✗ | ✓ (generic) | D-002, D-011 (generic `data-testid="create-dialog"`) |
| 39 | pages/stammdaten/SpeciesCreateDialog.tsx | 🟡 | ✓ | ✓ | ✗ | ✗ | ✓ (generic) | D-002, D-003 (`—` option labels), D-009, D-011 (generic) |
| 40 | pages/standorte/BatchCreateDialog.tsx | 🟡 | ✓ | ✓ | — | ✗ | ✗ | D-001, D-002 |
| 41 | pages/standorte/LocationCreateDialog.tsx | 🟡 | ✓ | ✓ | — | ✗ | ✗ | D-001, D-002; no intro text |
| 42 | pages/standorte/MaintenanceLogDialog.tsx | 🟡 | ✓ | ✓ | — | ✗ | ✗ | D-001, D-002; no intro text, no autoFocus |
| 43 | pages/standorte/MaintenanceScheduleDialog.tsx | 🟡 | ✓ | ✓ | — | ✗ | ✗ | D-001, D-002; no intro text |
| 44 | pages/standorte/SensorCreateDialog.tsx | 🟡 | ✓ | ✓ | — | ✗ | ✗ | D-001, D-002; D-008 (metric Fachbegriffe ph/ec/vpd/ppfd lack HelpTooltip) |
| 45 | pages/standorte/SiteCreateDialog.tsx | 🟡 | ✓ | ✓ | ✓ | ✗ | ✗ | D-001, D-002; ExpertiseFieldWrapper present |
| 46 | pages/standorte/SlotCreateDialog.tsx | 🟡 | ✓ | ✓ | — | ✗ | ✗ | D-001, D-002; no intro text, no autoFocus |
| 47 | pages/standorte/SubstrateCreateDialog.tsx | 🟡 | ✓ | ✓ | ✓ | ✗ | ✗ | D-001, D-002 |
| 48 | pages/standorte/SubstrateMixDialog.tsx | 🟡 | ✓ | ✗ (useState) | — | ✗ | ✗ | D-001, D-002, D-004 (DeleteIcon row), D-006; manual state partly justified (Slider-based mix UI) |
| 49 | pages/standorte/TankCreateDialog.tsx | 🟢 | ✓ | ✓ | ✓ | ✗ | ✓ | D-002; D-003 (`—` in MenuItem line 173) |
| 50 | pages/standorte/TankFillCreateDialog.tsx | 🟢 | ✓ | ✓ | ✓ | ✗ | ✓ | D-002; D-003 (`—` in option line 155) |
| 51 | pages/standorte/TankStateCreateDialog.tsx | 🟢 | ✓ | ✓ | ✓ | ✗ | ✓ | D-002; pH/EC/TDS/ORP lack HelpTooltip (D-008) |
| 52 | pages/standorte/WateringEventCreateDialog.tsx | 🟡 | ✓ | ✓ | — | ✗ | ✗ | D-001, D-002, D-004 (DeleteIcon), D-009 |

**Status Legend:** 🟢 Conformant (0–1 minor gap) / 🟡 Yellow (2–4 moderate gaps, no critical) / 🔴 Red (critical gap or multiple high-severity issues)

**File count by status:** 🟢 13 / 🟡 33 / 🔴 2

---

## Findings

### D-001 — Missing `data-testid` on Dialog Root Element

**Severity:** High (blocks Selenium E2E automation)
**Affected files:** ~30 dialogs (see Appendix A for complete list)

**Description:** UI-NFR-002 R-019 requires `data-testid` on all interactive containers for test automation. MUI `<Dialog>` components in approximately 30 files have no `data-testid` attribute on the root `<Dialog>` element. Dialogs that accept the `data-testid` prop pass it to the underlying `<div role="dialog">`, making this the correct attachment point.

**Pattern observed:**
```tsx
// MISSING — no data-testid
<Dialog fullScreen={fullScreen} open={open} onClose={onClose} maxWidth="sm" fullWidth>

// CORRECT (as seen in TankCreateDialog, TankFillCreateDialog, etc.)
<Dialog fullScreen={fullScreen} open={open} onClose={onClose} maxWidth="sm" fullWidth data-testid="tank-create-dialog">
```

**Cross-reference:** Extends F-004 from the main audit report.

---

### D-002 — Missing `aria-labelledby` on Dialog Root Element

**Severity:** High (WCAG 2.1 Level AA violation — UI-NFR-002 R-009)
**Affected files:** ~40 dialogs (see Appendix A)

**Description:** MUI Dialog with a visible title should have `aria-labelledby` on the `<Dialog>` element pointing to the `<DialogTitle>` element's `id`. Without this link, screen readers cannot announce the dialog name when focus moves into the dialog. The MUI Dialog component does not automatically wire this; the developer must set both `aria-labelledby="<id>"` on `<Dialog>` and `id="<id>"` on `<DialogTitle>`.

Only 4 dialogs in the entire corpus do this correctly:
- `TaskTemplateDialog.tsx` (`aria-labelledby="task-template-dialog-title"`)
- `PhaseDefinitionDialog.tsx` (`aria-labelledby="phase-definition-dialog-title"`)
- `PhaseSequenceEntryDialog.tsx` (`aria-labelledby="phase-sequence-entry-dialog-title"`)
- `WorkflowPhaseDialog.tsx` (`aria-labelledby` present)

**Pattern required:**
```tsx
<Dialog aria-labelledby="my-dialog-title" ...>
  <DialogTitle id="my-dialog-title">...</DialogTitle>
```

---

### D-003 — Unicode Escape Sequences in Dialog Files (R-049 violation)

**Severity:** Medium (code maintainability, NFR-003 style compliance)
**Affected files:** 9 dialogs

**Description:** UI-NFR-008 R-049 requires literal UTF-8 characters rather than JavaScript Unicode escapes (`—`, `²`, etc.) in source code. The main audit report already identified this as F-006 across 53 files; this finding extends the count to dialog files specifically.

**Confirmed occurrences:**

| File | Line(s) | Escape(s) | Should be |
|------|---------|-----------|-----------|
| WorkflowPhaseDialog.tsx | 405 | `'—'` | `'—'` |
| DeliveryChannelDialog.tsx | 371 | `{'²'}` | `{'²' → '²'}` |
| PlantingRunCreateDialog.tsx | 161, 399 | `'—'` | `'—'` |
| PlantingRunEditDialog.tsx | 159 | `'—'` | `'—'` |
| PlantInstanceCreateDialog.tsx | 162, 284, 351, 353 | `'—'` | `'—'` |
| ObservationCreateDialog.tsx | 127 | `'—'` | `'—'` |
| PestCreateDialog.tsx | 142, 148 | `'°C'` | `'°C'` |
| ProfileEditDialog.tsx | 159 | `'μ'`, `'²'`, `'₂'` | `'μ'`, `'²'`, `'₂'` |
| SpeciesCreateDialog.tsx | 177, 310, etc. | `'—'` | `'—'` |
| TankCreateDialog.tsx | 173 | `'—'` | `'—'` |
| TankFillCreateDialog.tsx | 155 | `'—'` | `'—'` |

---

### D-004 — Missing `aria-label` on Icon-Only Buttons

**Severity:** High (WCAG 2.1 Level AA — UI-NFR-002 R-006)
**Affected files:** TaskCreateDialog, FeedingEventCreateDialog, CareConfirmDialog, SubstrateMixDialog, WateringEventCreateDialog

**Description:** `<IconButton>` containing only a `<DeleteIcon>` or `<AddIcon>` with no visible text label must have an `aria-label` to be accessible. Without it, screen readers announce the element as an unlabelled button.

**Pattern required:**
```tsx
// MISSING aria-label
<IconButton size="small" onClick={() => handleRemove(index)}>
  <DeleteIcon fontSize="small" />
</IconButton>

// CORRECT
<IconButton
  size="small"
  onClick={() => handleRemove(index)}
  aria-label={t('common.remove')}
  data-testid={`remove-item-${index}`}
>
  <DeleteIcon fontSize="small" />
</IconButton>
```

---

### D-005 — Raw Enum Value Displayed in Chip (i18n violation)

**Severity:** High (UI-NFR-007 R-001)
**Affected file:** `pages/durchlaeufe/AdoptPlantsDialog.tsx`

**Description:** The plant phase is rendered as a raw backend string in a `<Chip>` label:
```tsx
<Chip label={plant.current_phase} size="small" />
```
This displays e.g. `"vegetative"` or `"flowering"` in lowercase English even when the UI is in German. The correct pattern is:
```tsx
<Chip label={t(`enums.phase.${plant.current_phase}`, { defaultValue: plant.current_phase })} size="small" />
```

---

### D-006 — `react-hook-form + Zod` Not Used (UI-NFR-008 R-001)

**Severity:** High (mandatory pattern)
**Affected files:** `ChannelFertilizerDialog.tsx`, `DeliveryChannelDialog.tsx`

**Description:** These two dialogs use plain `useState` chains for form state management instead of the mandatory `react-hook-form + zodResolver` pattern (UI-NFR-008 §2.1). Both dialogs are complex enough (4+ fields with validation requirements) that the deviation cannot be justified by dialog simplicity.

`SubstrateMixDialog.tsx` and `CareProfileEditDialog.tsx` also use manual state, but these have a stronger justification: they are primarily Slider-based / toggle-based interaction UIs where the "form submit" pattern is not the dominant interaction model.

`CareConfirmDialog.tsx` and `PhaseTransitionDialog.tsx` use manual state, which is acceptable for confirm/action dialogs where the schema is trivial.

---

### D-007 — Hardcoded Strings in `WorkflowInstantiateDialog`

**Severity:** High (UI-NFR-007 R-001)
**Affected file:** `pages/aufgaben/WorkflowInstantiateDialog.tsx`

**Description:** Two hardcoded English strings found in `defaultValue` fallback positions:
1. `defaultValue: 'failed'` — used as the default `status` value in a Zod schema or form init
2. A full English fallback sentence: `defaultValue: 'Workflow instantiation failed for all plants.'`

Both must be replaced with i18n keys.

---

### D-008 — Missing HelpTooltip on Fachbegriff Fields in Dialogs

**Severity:** Medium (UI-NFR-008 R-042/R-046, UI-NFR-011)
**Affected files:** Multiple (see below)

**Description:** Fields carrying specialist terms (EC, pH, VPD, PPFD, NPK, TDS, ORP, PPFD) that lack any `HelpTooltip` or sufficient `helperText` explanation. While `helperText` with value ranges is present on most EC/pH fields (addressing the main audit finding F-003 for dialogs), a subset of fields in specialized dialogs remain undocumented.

Most critical gaps:
- **`PhaseEntryDialog.tsx`:** N, P, K ratio fields have `helperText={t('pages.profiles.npkHelper')}` only on the N field; P and K fields have no helperText at all.
- **`SensorCreateDialog.tsx`:** The `metric_type` field lists `ph`, `ec_ms`, `vpd_kpa`, `ppfd`, `orp_mv`, `tds_ppm`, `dissolved_oxygen_mgl` without any tooltip explanation of what these metrics mean.
- **`TankStateCreateDialog.tsx`:** TDS, ORP fields use only abbreviated labels without explanation of what these values mean or their typical ranges.
- **`WateringConfirmDialog.tsx`:** EC and pH fields in the feeding details section have `helperText` for units but no deeper explanation.

---

### D-009 — Missing `autoFocus` on First Editable Field

**Severity:** Low-Medium (UI-NFR-008 R-010)
**Affected files:** ~15 dialogs (see below)

**Description:** UI-NFR-008 R-010 mandates `autoFocus` on the first editable field in a dialog. Many dialogs open without focus being placed on any input, requiring the user to click before typing.

Dialogs missing autoFocus entirely:
- FeedingEventCreateDialog, PhaseEntryDialog, DiseaseCreateDialog, PlantingRunCreateDialog
- PlantInstanceCreateDialog, WateringConfirmDialog, WateringEventCreateDialog
- BatchCreateDialog (has pre-generated batch_id — acceptable exception)
- SlotCreateDialog (has pre-generated slot_id — acceptable exception)
- LocationCreateDialog, MaintenanceLogDialog, MaintenanceScheduleDialog

Note: `WorkflowPhaseDialog` has `autoFocus={isEdit}` — correct for edit mode but missing for create mode.

---

### D-010 — OnboardingWizard: Water-Data Fields Outside RHF Pattern

**Severity:** Low (wizard-specific concern)
**Affected file:** `pages/onboarding/OnboardingWizard.tsx`

**Description:** The wizard is a full-page component (not a dialog) and uses Redux Toolkit for wizard state, which is the correct pattern per the implementation. However, the water configuration fields (`tapWaterEc`, `tapWaterPh`, `hasRoSystem`) are managed as isolated `useState` strings rather than being integrated into the sub-step components. This means:
- No Zod validation on EC/pH values before passing to the API
- No `inputMode="decimal"` on the EC/pH text inputs (the fields are plain strings stored in state, not typed number fields)
- The `parseFloat()` calls in `handleComplete` lack input sanitation guards

The wizard itself has excellent patterns: proper `data-testid="onboarding-wizard"`, `aria-label` on the Stepper (`aria-label={t('pages.onboarding.stepperAriaLabel')}`), mobile/desktop adaptive rendering, progress persistence via Redux.

---

### D-011 — Generic `data-testid="create-dialog"` Across Multiple Components

**Severity:** Medium (blocks reliable Selenium identification)
**Affected files:** ActivityCreateDialog, BotanicalFamilyCreateDialog, CultivarCreateDialog, SpeciesCreateDialog, GrowthPhaseDialog

**Description:** Five dialogs share the identical `data-testid="create-dialog"`. If two of these dialogs were ever open simultaneously (unlikely but possible via nested navigation), Selenium would be unable to distinguish them. More importantly, the generic value makes test code brittle since it is not self-documenting.

**Required pattern:** `data-testid="activity-create-dialog"`, `data-testid="botanical-family-create-dialog"`, etc.

---

## Positive Highlights

The following dialogs serve as implementation references for the patterns above:

**Best-in-class: `ProfileEditDialog.tsx`**
- `data-testid` on Dialog root
- `Card`/`CardContent` with `fieldset`/`legend` panel structure (R-037/R-038)
- Intro text (`body2`, `color="text.secondary"`) in both panels
- `FormRow` for responsive two-column field layout
- Full `helperText` on all Fachbegriff fields (PPFD range, VPD range, NPK)
- `autoFocus` on first field

**Best-in-class: `PlantingRunEditDialog.tsx`**
- `Card`/`CardContent` with fieldset+legend (R-037/R-038)
- Intro text in panels
- `autoFocus` on first field
- `data-testid` on Dialog

**Best-in-class: `TankCreateDialog.tsx` and `TankFillCreateDialog.tsx`**
- `data-testid` on Dialog root
- Named section headers (`Typography subtitle2`)
- Equipment section has both heading and `equipmentSectionIntro` intro text
- Suffix adornments on all numeric fields (L, mS/cm, %)
- `autoFocus` on primary input

**Best-in-class: `NutrientPlanAssignDialog.tsx`**
- Exemplary pick-list dialog pattern with search field, favorites toggle, EmptyState, LoadingSkeleton
- `data-testid` on dialog and list items

**Best-in-class: `PhaseDefinitionDialog.tsx` and `PhaseSequenceEntryDialog.tsx`**
- Both have `aria-labelledby` correctly wired
- Section headers with Dividers
- `helperText` on all non-obvious fields
- intro text via `body2`

---

## Appendix A: Files Missing `data-testid` on Dialog Root

The following files have no `data-testid` attribute on the `<Dialog>` element:

1. `pages/aufgaben/TaskCreateDialog.tsx`
2. `pages/aufgaben/WorkflowCreateDialog.tsx`
3. `pages/aufgaben/WorkflowInstantiateDialog.tsx`
4. `pages/aufgaben/WorkflowPhaseDialog.tsx`
5. `pages/duengung/ChannelFertilizerDialog.tsx`
6. `pages/duengung/DeliveryChannelDialog.tsx`
7. `pages/duengung/FeedingEventCreateDialog.tsx`
8. `pages/duengung/FertilizerCreateDialog.tsx`
9. `pages/duengung/NutrientPlanCreateDialog.tsx`
10. `pages/duengung/PhaseEntryDialog.tsx`
11. `pages/durchlaeufe/PlantingRunCreateDialog.tsx`
12. `pages/ernte/HarvestCreateDialog.tsx`
13. `pages/ernte/ObservationCreateDialog.tsx`
14. `pages/giessprotokoll/WateringLogCreateDialog.tsx`
15. `pages/pflanzenschutz/DiseaseCreateDialog.tsx`
16. `pages/pflanzenschutz/PestCreateDialog.tsx`
17. `pages/pflanzenschutz/TreatmentCreateDialog.tsx`
18. `pages/pflege/components/CareConfirmDialog.tsx`
19. `pages/pflanzen/PhaseTransitionDialog.tsx`
20. `pages/pflanzen/PlantInstanceCreateDialog.tsx`
21. `pages/standorte/BatchCreateDialog.tsx`
22. `pages/standorte/LocationCreateDialog.tsx`
23. `pages/standorte/MaintenanceLogDialog.tsx`
24. `pages/standorte/MaintenanceScheduleDialog.tsx`
25. `pages/standorte/SensorCreateDialog.tsx`
26. `pages/standorte/SiteCreateDialog.tsx`
27. `pages/standorte/SlotCreateDialog.tsx`
28. `pages/standorte/SubstrateCreateDialog.tsx`
29. `pages/standorte/SubstrateMixDialog.tsx`
30. `pages/standorte/WateringEventCreateDialog.tsx`

Files with only a generic `data-testid="create-dialog"` (also insufficient — see D-011):
- `pages/stammdaten/ActivityCreateDialog.tsx`
- `pages/stammdaten/BotanicalFamilyCreateDialog.tsx`
- `pages/stammdaten/CultivarCreateDialog.tsx`
- `pages/stammdaten/SpeciesCreateDialog.tsx`
- `pages/pflanzen/GrowthPhaseDialog.tsx`

---

## Appendix B: Files Missing `aria-labelledby`

All dialogs except the following 4 are missing `aria-labelledby`:
- `pages/aufgaben/TaskTemplateDialog.tsx` — has `aria-labelledby="task-template-dialog-title"`
- `pages/aufgaben/WorkflowPhaseDialog.tsx` — has `aria-labelledby`
- `pages/phasen/PhaseDefinitionDialog.tsx` — has `aria-labelledby="phase-definition-dialog-title"`
- `pages/phasen/PhaseSequenceEntryDialog.tsx` — has `aria-labelledby="phase-sequence-entry-dialog-title"`

That means 47 out of 51 files are missing `aria-labelledby`.

---

## Appendix C: Hardcoded / Non-i18n Strings in Dialogs

| File | Location | String | Fix |
|------|----------|--------|-----|
| `WorkflowInstantiateDialog.tsx` | defaultValue | `'failed'` | i18n key |
| `WorkflowInstantiateDialog.tsx` | defaultValue | `'Workflow instantiation failed for all plants.'` | i18n key |
| `BotanicalFamilyCreateDialog.tsx` | Zod schema `.refine()` | `"Muss auf '-aceae' enden"` | i18n key (extends F-011) |
| `SubstrateMixDialog.tsx` | `TextField label` | `"(DE)"`, `"(EN)"` | Use `t('common.langDE')` / `t('common.langEN')` |
| `CareConfirmDialog.tsx` | `TextField label` | `"ml/L"` | i18n key or `t('units.mlPerLiter')` |

---

## Appendix D: OnboardingWizard Step Files (not in scope list but referenced)

The OnboardingWizard delegates rendering to 7 sub-step files in `pages/onboarding/steps/`. These files were not in the audit scope list but are referenced by the wizard:

- `ExperienceLevelStep.tsx`
- `StarterKitStep.tsx`
- `FavoriteSpeciesStep.tsx`
- `SiteSetupStep.tsx`
- `PlantSelectionStep.tsx`
- `NutrientPlanStep.tsx`
- `SummaryStep.tsx`

These step files should be audited separately if wizard-specific testing is required. The `SiteSetupStep` is the most critical as it hosts the EC/pH water configuration fields that currently bypass RHF validation (D-010).

---

## Appendix E: Dialogs with `autoFocus` Missing or on Wrong Field

| File | Situation |
|------|-----------|
| `WorkflowPhaseDialog.tsx` | `autoFocus={isEdit}` only — create mode gets no focus |
| `FeedingEventCreateDialog.tsx` | No autoFocus anywhere |
| `PhaseEntryDialog.tsx` | No autoFocus |
| `DiseaseCreateDialog.tsx` | No autoFocus (PestCreateDialog has it; Disease does not — inconsistent) |
| `PlantingRunCreateDialog.tsx` | No autoFocus on `name` field |
| `PlantInstanceCreateDialog.tsx` | No autoFocus |
| `WateringConfirmDialog.tsx` | No autoFocus |
| `WateringEventCreateDialog.tsx` | No autoFocus |
| `LocationCreateDialog.tsx` | No autoFocus on `name` field |
| `MaintenanceLogDialog.tsx` | No autoFocus |
| `MaintenanceScheduleDialog.tsx` | No autoFocus |
| `SlotCreateDialog.tsx` | Pre-generated `slot_id` — autoFocus on it is acceptable but unset |
| `BatchCreateDialog.tsx` | Pre-generated `batch_id` — same |

---

## Priority-Ranked Remediation Plan

### Priority 1 — Critical (blocks accessibility / E2E automation)
- **D-002:** Add `aria-labelledby` + `id` pairing to all 47 affected dialogs
- **D-001:** Add specific `data-testid` to all 30 dialogs missing it; rename generic `"create-dialog"` in 5 files (D-011)
- **D-004:** Add `aria-label` to all icon-only buttons (Delete/Add/ExpandMore without visible text)
- **D-005:** Fix raw `current_phase` enum display in `AdoptPlantsDialog`

### Priority 2 — High (spec violations)
- **D-006:** Convert `ChannelFertilizerDialog` and `DeliveryChannelDialog` to RHF+Zod
- **D-007:** Extract hardcoded strings in `WorkflowInstantiateDialog` to i18n keys
- **D-003:** Replace all Unicode escapes with literal UTF-8 characters (9 files)
- **Appendix C:** Fix remaining hardcoded strings (`BotanicalFamilyCreateDialog` Zod message, `SubstrateMixDialog` language labels, `CareConfirmDialog` unit label)

### Priority 3 — Medium (usability)
- **D-009:** Add `autoFocus` to first editable field in 13 dialogs
- **D-008:** Add `helperText` to P and K NPK fields in `PhaseEntryDialog`; add metric explanations in `SensorCreateDialog` and `TankStateCreateDialog`
- **D-010:** Add Zod validation for EC/pH fields in `OnboardingWizard`/`SiteSetupStep`

### Priority 4 — Low (code quality)
- All remaining `Typography subtitle2` section headers should be assessed for R-037/R-038 Card/Paper panel structure where >6 fields are present in a section
