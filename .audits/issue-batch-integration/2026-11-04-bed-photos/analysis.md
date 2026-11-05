# Group pre-analysis: 2026-11-04-bed-photos

> Run-scoped artifact. Committed on the integration branch, removed with a fix-forward `git rm` before the bundle merges.

## Scope of this analysis

**Research question:** Can #2661 (bed photo storage and routes) and #2662 (gallery, cover photo, field-mode photo to bed) ship as one bundle, and which existing attachment pattern do they follow?

**The group's single logical change, in one sentence:** A bed can carry photos with a cover photo — stored as tenant attachments of a new category `location` with the same EXIF, holder, erasure and export rules as the other tenant photos — and the bed view, the bed sheet and field mode show and add them.

**Out of scope:** E2E (WP 8.31, #2674); photos in the plan JSON (never, decision bundle item 7); image editing; changes to the attachment pipeline itself.

**Tier:** 2 — one repository; additive enum value, additive model fields, new routes.

## Members

| Issue | Class | Admitting predicate | Evidence |
|---|---|---|---|
| #2661 | feature-request | thematic coupling | bed photos (REQ-053 §10.1 GP-FR-051, Appendix A issue 50) |
| #2662 | feature-request | dependency chain | body "Depends on: WP 8.18 (#2661)" |

Re-check: both OPEN, author `nolte` (trusted), bounded, no asserted cause. Kind "symptom" overturned to **neither** (feature chain).

**Dependency ordering:** #2661 → #2662. **Shared touch surface:** none by file; #2662 consumes #2661's routes. Serial after companion-layer (#2710) because both touch `api/v1/locations/`.

## Mode decision

**Mode:** A — single strand. Acceptance is deterministic; the mandatory reviews (security, GDPR) run on the bundle.

## Structural finding

**Cluster shape:** neither — feature chain. **Process finding:** none.

**Measured observations (origin/develop 05fb261ca):**
- Precedent to mirror: `AttachmentCategory.GARDEN_PLAN_UNDERLAY` (`common/enums.py:1530`, GP-FR-033): EXIF strip, erasure like tenant-record photos, never in the plan JSON. The new value `LOCATION = "location"` follows the same wiring.
- Guards that must stay green and be extended, not bypassed: `tests/unit/guards/test_photo_types_the_pipeline_admits_are_strippable.py`, `test_stored_object_deletes_ask_for_other_holders.py`, `test_tenant_erasure_inventory_is_complete.py`, `test_tenant_export_covers_the_inventory.py`, `test_garden_plan_collections_are_in_the_erasure_cascade.py`.
- `photo_refs` patterns exist on `care_event.py:153/281` (with max length and no repeats) and `ipm.py:161`.
- #2637 (retry of a write conflict before keeping an unreferenced photo) is merged, so the delete path already retries once.
- Decision bundle item 7 (#2643, answered 2026-11-03): category name `location`, upload from grower up, deleting another member's photo is lead-only, photos never in the plan JSON.

## Plan approval

**Authorised by:** `2026-11-04-bed-photos/plan-approval` — approved by the coordinator under the operator's standing authorisation for wave 8 (2026-11-04, decision 3).

**Group requirement artifact:** not applicable — not a class cluster.

## Completeness matrix

| Member | Backend | Frontend | Tests & guards | Privacy | Docs & i18n |
|---|---|---|---|---|---|
| #2661 | enum `LOCATION`; `Location.photo_refs[]` (bounded, no repeats) + `cover_photo_ref` (must be one of `photo_refs`); `domain/services/location_photo_service.py` (`*, tenant_key: str`, ownership via `location_ownership`); routes add/remove/set cover under `api/v1/locations/`; bed delete removes the references and asks other holders before deleting objects | not applicable | foreign attachment -> 422 `reference.not_found`; grower may add, lead-only delete of another member's photo; all attachment guards green; route walk, consumer pin, bounded lists, write-gate ceiling | erasure mapping of the category, Art. 15 export, EXIF strip; plan JSON export carries no photos (test) | API reference DE/EN; enum i18n DE/EN |
| #2662 | not applicable | `bed/BedPhotos*.tsx` (lazy) gallery tab, cover photo in bed header and `field/FieldBedSheet.tsx`, field mode "photo to bed or plant" | vitest + axe; field-mode targets >= 64 px; bundle budget not raised | no photo URL in logs or plan export | user guide DE/EN, i18n DE/EN |

## Risks

- GDPR: photos of a garden can show people or a home; the category must be in the erasure cascade and the export from day one.
- Holder check: an attachment used by two beds (or a bed and a care event) must not be deleted with one of them.
- `api/v1/locations/` collides with #2710 at rebase.

## Open questions for the operator

- none (item 7 of #2643 answered)

## Member results

| Member | Specialist | Check | Actual output |
|---|---|---|---|
| #2661 | fullstack-developer | gate + code-security-reviewer + gdpr-data-protection-reviewer | routes, service, discard paths, orphan sweep `cleanup_orphaned_location_photos` (48 h default), MIME + key-length hardening; tests/api, unit+guards, targeted integration green |
| #2662 | fullstack-developer + frontend-usability-optimizer | vitest + axe, tsc, eslint, knip, bundle budget | gallery tab (lazy), cover in header + field sheet, field-mode bed photo (64 px); 7083 FE tests green, gardenPlanner chunk 60.6/120 KB |

## Deviations

| Member | Kind | What changed |
|---|---|---|
| #2661 | scope addition | review finding SEC-001/GDPR-001: never-linked `location` uploads had no sweep — dedicated beat task added; underlay gap + low items to #2715, legal questions to #2643 |
