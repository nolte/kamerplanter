/**
 * Per-catalogue revision counter, bumped when a catalogue row is written (#1568).
 *
 * **The defect this closes.** `useCatalogue` caches a seeded reference catalogue
 * for the session, marking the row array a complete load produced. That mark
 * survives a *mutation* of the same data: none of the six detail pages refreshes
 * its list slice after a write. `SpeciesDetailPage` dispatches `fetchSpecies(key)`,
 * whose `fetchOne.fulfilled` writes only `currentField` and leaves `items`
 * untouched and still marked; the other five call a page-local loader or set
 * local state. Delete is worse — every one of the six only navigates away. So a
 * picker mounted afterwards offered the old name, and after a delete a row that
 * no longer exists, until the tab was reloaded.
 *
 * That is a **regression against the state before the shared cache**, where each
 * of those dialogs reloaded on open. The cache is what turns a stale read into a
 * lasting one, so the cache is what has to know.
 *
 * **Why this lives in the API layer and not at the call site.** The obvious fix
 * is an `invalidateCatalogue(...)` next to each `await api.updateSpecies(...)`.
 * That is a guard opted into at the call site, and this repository has paid for
 * that shape repeatedly: #948 repaired two of four routes of the same form and
 * the other two stayed open for months. The measurement here says the same —
 * species alone is written from **five** places, two of which
 * (`GrowingPeriodsSection`, `PlantIdentificationDialog`) are not detail pages at
 * all and would plausibly have been missed.
 *
 * The endpoint module is the one place every writer passes through. Bumping here
 * means a new caller of `updateSpecies` is covered the day it is written, without
 * knowing this module exists. `test_catalogue_writes_bump_the_revision` asserts
 * that property as a class rather than trusting the list above to stay complete.
 *
 * **Why a revision and not a `clear()`.** The mark records *which* revision a load
 * observed, so it can be compared rather than erased. A concurrent load that
 * started before a write therefore cannot mark its (already stale) array as
 * current — it marks the revision it began under, and the comparison fails.
 *
 * **Why the reviewer's `extraCases` shape was not used.** It was the preferred
 * form and it is not constructible here: `createListSlice` creates exactly two
 * thunks, `fetchAll` and `fetchOne`, and there is no mutation thunk anywhere for
 * any of the six catalogues — every write is a direct `await api.update…()`.
 * `extraCases` reacting to mutation thunks would have had nothing to react to.
 * Introducing mutation thunks across six catalogues is a refactor of its own.
 */

/** Catalogues whose completeness can go stale through a write. */
export type CatalogueRevisionName =
  | 'activities'
  | 'botanicalFamilies'
  | 'fertilizers'
  | 'nutrientPlans'
  | 'species'
  | 'substrates';

const revisions = new Map<CatalogueRevisionName, number>();

/**
 * Current revision of a catalogue. Starts at 0 and only ever increases.
 *
 * @param name The catalogue.
 * @returns The revision a completeness mark must match to still be valid.
 */
export function catalogueRevision(name: CatalogueRevisionName): number {
  return revisions.get(name) ?? 0;
}

/**
 * Records that a catalogue's rows changed, invalidating every completeness mark
 * taken before now.
 *
 * Called by the endpoint module's create/update/delete wrappers, never by a page.
 *
 * @param name The catalogue that was written.
 */
export function invalidateCatalogue(name: CatalogueRevisionName): void {
  revisions.set(name, catalogueRevision(name) + 1);
}

/** Every catalogue this module knows about, for {@link invalidateAllCatalogues}. */
const ALL_CATALOGUES: readonly CatalogueRevisionName[] = [
  'activities',
  'botanicalFamilies',
  'fertilizers',
  'nutrientPlans',
  'species',
  'substrates',
];

/**
 * Invalidates every catalogue at once, because the rows themselves no longer
 * belong to the same scope.
 *
 * Called when the active tenant changes. Measured reason (#1568 review, SCR-008):
 * `TenantSwitcher` reloads the document and so discards every cache with the
 * heap, but the **stale-slug recovery** path in `store.ts` does not — it clears
 * the active tenant, reloads the memberships, and `loadMyTenants.fulfilled`
 * re-picks a *different* tenant and persists it, all in place. That path is
 * reachable in operation: it fires when the backend refuses the persisted tenant,
 * which is what an admin revoking a membership while the tab is open produces.
 *
 * These catalogues are a global/tenant union (#324), so a row array marked
 * complete under the old tenant would otherwise be served as the new tenant's
 * complete catalogue — carrying the previous tenant's rows across the boundary.
 * That is why this hangs on the slug setter rather than on any caller: it is the
 * one choke point every tenant change passes through.
 */
export function invalidateAllCatalogues(): void {
  for (const name of ALL_CATALOGUES) invalidateCatalogue(name);
}
