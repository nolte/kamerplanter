import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { Activity, BotanicalFamily, Fertilizer, NutrientPlan, Species, Substrate } from '@/api/types';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import type { AppDispatch, RootState } from '@/store/store';
import { fetchActivities } from '@/store/slices/activitiesSlice';
import { fetchBotanicalFamilies } from '@/store/slices/botanicalFamiliesSlice';
import { fetchFertilizers } from '@/store/slices/fertilizersSlice';
import { fetchNutrientPlans } from '@/store/slices/nutrientPlansSlice';
import { fetchSpeciesList } from '@/store/slices/speciesSlice';
import { fetchSubstrates } from '@/store/slices/substratesSlice';

/**
 * The one reader for a seeded reference catalogue (#1560, #1568).
 *
 * **The defect this closes.** Every one of these catalogues already had a store
 * slice that loads it *completely* — `listAllSpecies`, `listAllBotanicalFamilies`,
 * `fetchAllFertilizers`, … — and carries `loading` and `error` while it does. The
 * pickers did not use them. Each dialog and dropdown rebuilt the same load into
 * local state, and rebuilt it wrong in the same two ways every time:
 *
 * 1. It asked for **one page** with an explicit bound (`listSpecies(0, 200)`),
 *    against a catalogue that is 207 rows seeded. Because every filter in those
 *    pickers runs client-side over the array already fetched, the seven rows that
 *    never arrived are not off-screen — the picker answers "no such species".
 * 2. It collapsed *failed* into *empty*, usually as `.catch(() => {})`. A load
 *    that 500s and a catalogue that is genuinely empty then render the identical
 *    "nothing found" message, and the user creates the record without the field.
 *
 * Both follow from the same cause: the loader was duplicated instead of shared.
 * So does a third, which is why this went unseen for two milestones —
 * `scripts/check_seed_catalogue_page_size.py` binds **one** owning module per
 * catalogue (the slice), and a picker in a different module is invisible to it.
 *
 * **The contract this hook gives instead.** Three states that cannot be confused
 * with one another:
 *
 * - `loading` — in flight, and in flight for the *whole* paging sequence. A
 *   complete load is sequential (`fetchAllPages`), so clearing the flag when the
 *   first page lands would present a list that is neither complete nor marked as
 *   loading, which is this class's failure mode rather than an improvement on it.
 * - `failed` — the load rejected. Carries an error for {@link ErrorDisplay} and a
 *   {@link CatalogueReader.reload} to retry with. Never renders as "empty".
 * - `ready` — the complete catalogue arrived. `items` may still be `[]`, and that
 *   is then a *genuine* empty catalogue, which is a different sentence.
 *
 * **Caching.** The rows live in the store slice, so the second picker to ask for
 * the same catalogue in a session renders from cache with no request. The cache
 * predicate is deliberately "the slice holds no rows" rather than a module-level
 * "already fetched" flag: that flag would survive a tenant switch, and these
 * catalogues are a global/tenant union (#324). An empty catalogue therefore
 * re-requests on the next mount, which is the harmless direction — and a *failed*
 * load leaves the slice empty too, so the next open retries by itself.
 *
 * **Status is per-consumer, not read off the slice.** `slice.loading` is also
 * toggled by the slice's single-entity fetch (`fetchSubstrate`, …), so a detail
 * page loading one row would otherwise flip an unrelated picker into its
 * spinner. This hook derives its status from its own dispatch instead, and takes
 * only the rows from the store.
 *
 * @example
 * const families = useCatalogue('botanicalFamilies', { enabled: open });
 * if (families.status === 'failed') return <ErrorDisplay error={families.error!} onRetry={families.reload} />;
 */

/** Rows a catalogue name resolves to. */
interface CatalogueItems {
  activities: Activity;
  botanicalFamilies: BotanicalFamily;
  fertilizers: Fertilizer;
  nutrientPlans: NutrientPlan;
  species: Species;
  substrates: Substrate;
}

/** Name of a catalogue this hook can read. */
export type CatalogueName = keyof CatalogueItems;

/** Row type of one catalogue. */
export type CatalogueItem<K extends CatalogueName> = CatalogueItems[K];

/**
 * The three states, which is the whole point: a consumer that renders `ready`
 * and `failed` the same way is the defect this replaces.
 */
export type CatalogueStatus = 'loading' | 'ready' | 'failed';

/** What {@link useCatalogue} returns. */
export interface CatalogueReader<T> {
  /** The complete catalogue once `status` is `ready`; `[]` before that. */
  items: T[];
  status: CatalogueStatus;
  /**
   * Error for {@link ErrorDisplay} when `status` is `failed`, `null` otherwise.
   * Holds an `errors.*` i18n key or an already user-facing message — never raw
   * English fallback prose (FE-L5).
   */
  error: string | null;
  /** `true` only when the catalogue arrived and is genuinely empty. */
  isEmpty: boolean;
  /** Retry a failed load, or refresh a loaded one. */
  reload: () => void;
}

/**
 * How each catalogue is read: where its rows live in the store, and the thunk
 * that loads it completely.
 *
 * Every `fetch` here is a slice thunk whose endpoint is the *complete* loader.
 * That is the invariant `check_seed_catalogue_page_size.py` enforces from the
 * other side, so a catalogue added here without one fails the gate rather than
 * shipping short.
 */
const CATALOGUES: {
  [K in CatalogueName]: {
    select: (state: RootState) => CatalogueItems[K][];
    fetch: (dispatch: AppDispatch) => Promise<unknown>;
  };
} = {
  activities: {
    select: (state) => state.activities.items,
    fetch: (dispatch) => dispatch(fetchActivities()).unwrap(),
  },
  botanicalFamilies: {
    select: (state) => state.botanicalFamilies.items,
    fetch: (dispatch) => dispatch(fetchBotanicalFamilies()).unwrap(),
  },
  fertilizers: {
    select: (state) => state.fertilizers.fertilizers,
    fetch: (dispatch) => dispatch(fetchFertilizers()).unwrap(),
  },
  nutrientPlans: {
    select: (state) => state.nutrientPlans.plans,
    fetch: (dispatch) => dispatch(fetchNutrientPlans()).unwrap(),
  },
  species: {
    select: (state) => state.species.items,
    fetch: (dispatch) => dispatch(fetchSpeciesList()).unwrap(),
  },
  substrates: {
    select: (state) => state.substrates.items,
    fetch: (dispatch) => dispatch(fetchSubstrates()).unwrap(),
  },
};

/**
 * Loads in flight per catalogue, so two pickers mounting in the same tick issue
 * one request between them and both learn its outcome.
 *
 * Module-level on purpose: it is the request, not a React value, that must be
 * shared. The entry is removed as soon as the promise settles, so nothing here
 * outlives the load — in particular, nothing survives a tenant switch.
 */
const inFlight = new Map<CatalogueName, Promise<unknown>>();

/**
 * Joins the load already running for this catalogue, or starts one.
 *
 * @param name The catalogue.
 * @param start Starts a load.
 * @param forced Set by a retry: it must reach the network rather than inherit
 *   the outcome of a load that may already be failing.
 */
function joinOrStart(
  name: CatalogueName,
  start: () => Promise<unknown>,
  forced = false,
): Promise<unknown> {
  const running = inFlight.get(name);
  if (running && !forced) return running;
  const started = start();
  inFlight.set(name, started);
  const forget = () => {
    if (inFlight.get(name) === started) inFlight.delete(name);
  };
  started.then(forget, forget);
  return started;
}

/**
 * Turns a rejected load into the string `ErrorDisplay` renders.
 *
 * Falls back to the `errors.loadFailed` key rather than to the raw message,
 * because an unrecognised message is English backend prose and a German form is
 * no place for it (NFR-003, FE-L5).
 */
function errorMessage(error: unknown): string {
  const message = error instanceof Error ? error.message : null;
  return message && message.length > 0 && message.length < 200 ? message : 'errors.loadFailed';
}

/** Options for {@link useCatalogue}. */
export interface UseCatalogueOptions {
  /**
   * Whether to load at all. Pass the dialog's `open` flag so a picker inside a
   * closed dialog costs nothing; the hook reports `loading` while disabled so a
   * consumer never renders "empty" for a catalogue it has not asked for.
   */
  enabled?: boolean;
}

/**
 * Reads a seeded reference catalogue completely, with pending / failed / empty
 * kept apart.
 *
 * @param name Which catalogue.
 * @param options See {@link UseCatalogueOptions}.
 * @returns The reader; the object is `useMemo`-stabilised (FRONTEND.md §6.1).
 */
export function useCatalogue<K extends CatalogueName>(
  name: K,
  options?: UseCatalogueOptions,
): CatalogueReader<CatalogueItem<K>> {
  const enabled = options?.enabled ?? true;
  const dispatch = useAppDispatch();
  const items = useAppSelector(CATALOGUES[name].select) as CatalogueItem<K>[];
  const hasItems = items.length > 0;

  // Bumped by `reload`; re-runs the effect even when nothing else changed, which
  // is the only way a retry after a failure reaches the network again.
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState<{ status: CatalogueStatus; error: string | null }>(() => ({
    status: hasItems ? 'ready' : 'loading',
    error: null,
  }));

  // The `attempt` value whose forced load this hook has already started. Without
  // it a successful reload would re-enter the effect (the slice now holds rows),
  // see a forced attempt again, and request forever.
  const startedAttempt = useRef<number | null>(null);

  useEffect(() => {
    if (!enabled) return;
    const forced = attempt > 0 && startedAttempt.current !== attempt;
    startedAttempt.current = attempt;
    let ignore = false;
    // Declared inside the effect and invoked, never called at the top level of
    // the effect body, so `react-hooks/set-state-in-effect` stays clean without
    // an eslint-disable (same shape as `useAquaponicSystems`).
    const run = async () => {
      // Cached: the slice already holds the complete catalogue, and no retry
      // asked for a fresh one.
      if (hasItems && !forced) {
        setState({ status: 'ready', error: null });
        return;
      }
      setState({ status: 'loading', error: null });
      try {
        await joinOrStart(name, () => CATALOGUES[name].fetch(dispatch), forced);
        if (!ignore) setState({ status: 'ready', error: null });
      } catch (error) {
        // The ignore guard is the half that was missing at every call site: a
        // dialog closed and reopened started a second sequence whose late
        // answer overwrote the live one (#1568).
        if (!ignore) setState({ status: 'failed', error: errorMessage(error) });
      }
    };
    void run();
    return () => {
      ignore = true;
    };
  }, [name, enabled, hasItems, attempt, dispatch]);

  const reload = useCallback(() => {
    setAttempt((previous) => previous + 1);
  }, []);

  return useMemo(
    () => ({
      items,
      status: state.status,
      error: state.error,
      isEmpty: state.status === 'ready' && items.length === 0,
      reload,
    }),
    [items, state.status, state.error, reload],
  );
}
