# Pre-analysis: #2518 features must not import from pages/ (transient, removed before merge)

Class: refactor. Source: issue #2518 (decision 2026-10-19 on #2496 item 3). Authorised under operator autonomy 2026-10-09 / 2026-10-30 (partition 2026-10-29 single).

## Established (develop fb4d3ed51)
- Only one features -> pages import exists: `src/frontend/src/features/gardenPlanner/field/FieldBedSheet.tsx:46` `lazy(() => import('@/pages/pflanzen/photos/PlantPhotoUploadDialog'))` (grep over src/features, test files excluded: one hit).
- `PlantPhotoUploadDialog.tsx` imports only shared code (`@/components/identification/ImageCapturePanel`, `@/hooks/useExpertiseLevel`, `@/utils/imageNormalization`, `@/api/...`), so it can move without dragging page code. Its other consumer: `pages/pflanzen/photos/PlantPhotoGallery.tsx:37` (relative import). `pages/pflanzen/diary/DiaryPhotoUploadDialog.tsx:41` mentions it in a comment.
- `src/frontend/eslint.config.js` has `no-restricted-imports` blocks scoped by `files:` (garden editor, GP-NFR-009); no rule forbids features -> pages.
- `src/components/` has no `plants`/`photos` folder (admin, ai, common, dashboard, diagnosis, diary, form, glossary, ha, identification, kiosk, layout, pests, print, privacy, sensors, tanks, tenants, water, weather).

## Design
- D-1 Move `PlantPhotoUploadDialog.tsx` (and its test if one exists) to a shared location under `src/components/` (specialist picks the folder by the existing convention; `git mv` to keep history), update both importers and the comment in DiaryPhotoUploadDialog.tsx. The lazy import in FieldBedSheet must stay lazy (field chunk size, `task bundle:check`).
- D-2 Guard (defect-class G1): an ESLint rule for `src/features/**` forbidding `@/pages/**` and relative paths into `pages/`, message pointing at `src/components`. It must pass on the tree after D-1 and fail on a probe import (prove by adding one temporarily). Dynamic `import()` in `lazy()` may NOT be covered by `no-restricted-imports`: measure; if not covered, add `no-restricted-syntax` on `ImportExpression` with a matching source (or a small guard test); record what was measured.
- D-3 Docs: one line in the frontend layering rules (spec/style-guides/FRONTEND.md) only if a fitting place exists.

## Work packages
| id | what | specialist |
|---|---|---|
| P1 | move + importers + comment (D-1) | fullstack-developer |
| P2 | lint guard (D-2) + docs line (D-3) | fullstack-developer |
Review after: frontend-code-reviewer.

## Risks
- Chunk graph: the dialog stays a lazy chunk; check `task bundle:check` (budget gate blocks automerge).
- Tests may import pages from features; check before the guard applies to `*.test.*` files.
