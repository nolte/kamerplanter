---
name: REQ-008 Post-Harvest Test Case Patterns
description: Key testing patterns, coverage gaps, and cross-cutting concerns discovered while extracting TC-REQ-008
type: project
---

## REQ-008 Post-Harvest — Test Extraction Notes (2026-03-21)

**Output file**: `spec/e2e-testcases/TC-REQ-008.md` (68 test cases)

### Key UI Patterns for Post-Harvest (spec-only, not yet implemented)
- Batch detail page has tabbed layout: Trocknung | Curing | Beobachtungen | Trim-Protokoll | Lagerort
- Batch status machine (U-006): fresh→drying→curing→aging→stored→consumed/disposed
- Status badges are color-coded per state (design decision: blue=fresh, yellow=drying, green=stored)
- Snap-Test uses two independent boolean checkboxes: "bricht sauber" + "splittert"

### Cross-Cutting Business Rules Surfacing as UI Constraints
- **Karenz-Gate (REQ-010)**: "Trocknung starten" button is disabled/shows tooltip when Karenz still active
- **DryingProtocol weight validator**: current_weight ≤ initial_weight (client-side Zod rule needed)
- **TrimProtocol weight validator**: post_trim ≤ pre_trim (client-side Zod rule needed)
- **StorageObservation defect validator**: mold defect forces visual_condition = 'critical'

### Species-Specific Content in UI Guides (test data requirements)
- Cannabis: hang_dry, 15-21°C, 45-55% RH, UV=none, opaque glass
- Zwiebel (P-004): 2-phase protocol — Phase 1 UV DESIRED (curing), Phase 2 dark (storage)
- Kartoffel: ABSOLUTE darkness (Solanin), sprouting_inhibition modifiers (P-005)
- Speisepilze: dehydrator 45-55°C, heilpilze max 40°C (critical distinction for UI)
- Sauerkraut: 2-phase fermentation (Leuconostoc 18-22°C → Lactobacillus 15-18°C)

### Threshold Values for Test Data
- Snap-Test: OPTIMAL (breaks cleanly, no splinter), OVERDRIED (breaks + splinters), UNDERDRIED (bends only)
- RH Jar: >65%=CRITICAL, 62-65%=SLIGHTLY_HIGH, 58-62%=OPTIMAL, 55-58%=SLIGHTLY_LOW, <55%=TOO_LOW
- CO2 thresholds: 800=OK, 1200=ELEVATED, 1500=WARNING, 2000=CRITICAL
- a_w thresholds: >0.65=CRITICAL, 0.60-0.65=WARNING, <0.60=OK; Cannabis target: 0.55-0.65
- Drying: >85% weight loss = over_dried warning; ≥95% = ready for curing
- Storage alert: days_remaining < 30 triggers alert

### Spec Sections That Are Ambiguous / Need UI Design Decisions
- Where exactly does the Schimmeltyp-Assistent live? (modal dialog or separate page?)
- Jar-ID QR system: generated on demand or persistent? Print or PDF download?
- Dashboard widget for storage inventory: which page / widget slot?
- Photo upload implementation: direct file upload or URL reference?

**Why**: REQ-008 is not yet implemented in frontend — all test cases describe planned behavior.
**How to apply**: When frontend implementation begins, verify which planned routes/components match these test cases and update IDs accordingly.
