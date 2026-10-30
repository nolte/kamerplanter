# Pre-analysis: #2534 zone editor follow-ups (transient, removed before merge)

Class: bug (non-blocking review findings of PR #2533, frontend, REQ-053 WP 7.6/7.7). Source: issue #2534 (8 numbered items). Authorised under operator autonomy 2026-10-09 / 2026-10-30 (partition 2026-10-29 single). Requirements: the issue body is the decision record (U_gate override: reviewer findings with exact locations).

## Established (develop 7116e1824; locations as the issue states them, to be re-measured by the specialist)
- `src/frontend/src/features/gardenPlanner/zones/ZoneEditor.tsx` (379 lines): `errorKey` returns `noBeds` for `irrigation_zone.no_beds` (l.57) but `pages.…zones.errors.noBeds` does not exist in DE/EN (only `…round.noBeds`, `…noBeds` of other dialogs exist: pages.json en l.6195/6888/7219).
- `ZonePanel.test.tsx` (415 lines), `ZoneLegend.tsx`, `BedZoneInfo.tsx`, `useZoneData.ts`, `zonesApi.ts`, `zonesTestKit.ts`, `ZonePanel.tsx` (225 lines).
- Items: (1) 404 message lost because `setError` and `onChanged(null)` batch and the editor unmounts: show via `notify.error` before `onChanged(null)` or in the panel; (2) partial create (POST ok, PUT failed) leaves a "new" form: switch to `{kind:'edit', key}` after the successful POST or say "zone created, beds not assigned"; exclude `createdKey` in `zoneOfBed`; (3) dead `noBeds` branch: remove (backend raises `no_beds` only for the watering round, which the dialog handles itself); (4) `isTempKey` `/^tmp[0-9a-z]+$/`, report how many unsaved beds a mixed selection skipped; (5) `wrote = true` right after `updateZone`; (6) zone numbers derive from backend sort `name ASC, _key ASC` (renaming renumbers — consistent but surprising), `BedZoneInfo` shows no number, panel title and editor title both `h3`; (7) test gaps (real reload that changes `zones`, PATCH body on second save, PATCH ok + PUT failed, 404 on delete, focus management open / mode switch / return to `garden-plan-zones-open`, mixed selection); (8) from the first review: Suspense error boundary around the lazy panel (ChunkLoadError after a deploy), `nowMs` frozen at mount (day classes wrong after midnight), redundant `layerRefresh` full plan GET on every zone change.

## Design
- D-1 Items 1-5 and 7 as the issue says; keep the existing mode/state machine of ZoneEditor, no new abstraction unless two call sites need it.
- D-2 Item 6: fix the two a11y/UX defects (distinct heading levels; show the zone number in `BedZoneInfo` consistent with legend/overlay). Renumbering on rename stays as is = OPERATOR POINT (changing the backend sort would alter an API ordering; alternative sort by creation is a product decision) — report, do not change.
- D-3 Item 8: error boundary with a retry/reload hint around the lazy zone panel (use the existing lazy-chunk error boundary pattern if the repo has one — grep for ChunkLoadError / ErrorBoundary — else the smallest local one); `nowMs` from a clock that advances (reuse an existing hook/utility if one exists, e.g. a minute tick, else minimal `useNow`); drop the redundant `layerRefresh` full GET per zone change only if the data is provably already refreshed through the zone data hook (measure what refetches; if not provable, keep and report).
- D-4 Tests per item 7; every new test must fail without its fix (cp backup, never git stash).

## Work packages
| id | what | specialist |
|---|---|---|
| P1 | items 1, 2, 3, 4, 5 in ZoneEditor/ZonePanel + tests (item 7 for these) | fullstack-developer |
| P2 | item 6 (headings, BedZoneInfo number) + test gaps of item 7 (reload, focus management, mixed selection) | fullstack-developer |
| P3 | item 8 (error boundary, nowMs, layerRefresh) + tests | fullstack-developer |
Review after: frontend-code-reviewer (+ a usability read of the messages and the partial-create state).

## Risks
- i18n keys DE/EN parity; texts follow "beschreibende Texte" convention (what happened and what to do next).
- Focus management: mobile first, kiosk targets unaffected.
