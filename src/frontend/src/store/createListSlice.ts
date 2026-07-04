import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { ActionReducerMapBuilder, Reducer } from '@reduxjs/toolkit';

/** Standard paginated envelope returned by list endpoints. */
export interface PaginatedResult<T> {
  items: T[];
  total: number;
  offset: number;
  limit: number;
}

/**
 * A list endpoint returns either a paginated envelope or a plain array.
 * The factory normalises both into {@link ListState}.
 */
export type ListResult<T> = PaginatedResult<T> | T[];

/**
 * Paging arguments every list thunk understands. Concrete slices widen this
 * with their own filter fields (e.g. `tankType`, `isTemplate`) via the generic
 * `A` parameter of {@link createListSlice}.
 */
export interface ListPageArg {
  offset?: number;
  limit?: number;
}

/**
 * Shared state shape for every list slice built with {@link createListSlice}.
 *
 * The collection and selection field names are configurable via `IF`/`CF`
 * (defaulting to `items`/`current`). This lets a domain slice keep its
 * historical, domain-named fields (`tanks`/`currentTank`, `plans`/`currentPlan`,
 * `runs`/`currentRun`, …) so existing page selectors (`s.tanks.tanks`) stay
 * valid — the migration is behaviourally neutral for consumers (Code-Review
 * FE-D5, FR-002 §B1).
 *
 * `error` holds either an i18n key (matching `errors.*`) or an already
 * user-facing ApiError message. It never holds raw English fallback prose:
 * `ErrorDisplay` resolves `errors.*` keys to the active locale (Code-Review
 * FE-L5).
 *
 * Pagination fields (`total`/`offset`/`limit`) are optional: `paginated` slices
 * fill them from the envelope; plain-array slices leave them absent.
 */
export type ListState<
  T,
  IF extends string = 'items',
  CF extends string = 'current',
> = { [K in IF]: T[] } & { [K in CF]: T | null } & {
  total?: number;
  offset?: number;
  limit?: number;
  loading: boolean;
  error: string | null;
};

export interface ListSliceConfig<
  T,
  A extends object = ListPageArg,
  IF extends string = 'items',
  CF extends string = 'current',
> {
  /** Slice name; also the action-type prefix (e.g. `species/fetchAll`). */
  name: string;
  /**
   * Loads the list page. Receives the raw dispatched thunk argument (paging
   * plus any slice-specific filters) and resolves a paginated envelope or a
   * plain array.
   */
  list: (arg: A) => Promise<ListResult<T>>;
  /** Loads a single entity by key; omit for list-only slices. */
  getOne?: (key: string) => Promise<T>;
  /** State field holding the collection. Default `items`. */
  itemsField?: IF;
  /** State field holding the single selection. Default `current`. */
  currentField?: CF;
  /**
   * Whether the endpoint returns a paginated envelope whose `total`/`offset`/
   * `limit` should be stored. Default `true`. Domain slices whose endpoints
   * return a plain array set this to `false`, keeping their state shape free of
   * pagination fields.
   */
  paginated?: boolean;
  /**
   * Whether `getOne` toggles `loading` (pending) and stores `error` (rejected).
   * Default `true`. Domain slices that historically only reacted to the
   * fulfilled action pass `false` to stay behaviourally neutral.
   */
  singleFetchTogglesStatus?: boolean;
  /** i18n key stored in `error` when a rejected action carries no message. */
  errorKey?: string;
  /** Extension point for entity-specific thunks/cases. */
  extraCases?: (builder: ActionReducerMapBuilder<ListState<T, IF, CF>>) => void;
}

const DEFAULT_ERROR_KEY = 'errors.loadFailed';

/**
 * Concrete, Immer-friendly working shape used inside the reducer. The dynamic
 * collection/selection fields are reached through the string index signature;
 * the static fields keep their precise types. The slice is exposed to consumers
 * as the precise {@link ListState} (see the `reducer` cast in the return), so
 * `s.tanks.tanks` stays typed as `Tank[]`.
 */
interface DraftListState<T> {
  [field: string]: T[] | T | boolean | string | number | null | undefined;
  loading: boolean;
  error: string | null;
  total?: number;
  offset?: number;
  limit?: number;
}

function isPaginated<T>(payload: ListResult<T>): payload is PaginatedResult<T> {
  return !Array.isArray(payload);
}

/**
 * Builds a Redux Toolkit slice for the common "paginated list + optional
 * single fetch" pattern shared by the stammdaten and domain list slices
 * (Code-Review FE-D5, FR-002 §B1).
 *
 * The returned thunks keep the conventional action-type prefixes
 * (`<name>/fetchAll`, `<name>/fetchOne`), so consuming pages and tests need no
 * changes when a hand-written slice is migrated. Re-export the members under
 * the slice's historical names (`fetchTanks`, `fetchTank`, `clearCurrentTank`,
 * …); `clearCurrent` clears whichever field `currentField` names.
 */
export function createListSlice<
  T,
  A extends object = ListPageArg,
  const IF extends string = 'items',
  const CF extends string = 'current',
>(config: ListSliceConfig<T, A, IF, CF>) {
  const errorKey = config.errorKey ?? DEFAULT_ERROR_KEY;
  const itemsField = (config.itemsField ?? 'items') as IF;
  const currentField = (config.currentField ?? 'current') as CF;
  const paginated = config.paginated ?? true;
  const singleFetchTogglesStatus = config.singleFetchTogglesStatus ?? true;

  const fetchList = createAsyncThunk(`${config.name}/fetchAll`, (arg?: A) =>
    config.list(arg as A),
  );

  const { getOne } = config;
  const fetchOne = getOne
    ? createAsyncThunk(`${config.name}/fetchOne`, (key: string) => getOne(key))
    : undefined;

  const base: DraftListState<T> = {
    [itemsField]: [] as T[],
    [currentField]: null,
    loading: false,
    error: null,
  };
  const initialState: DraftListState<T> = paginated
    ? { ...base, total: 0, offset: 0, limit: 50 }
    : base;

  const slice = createSlice({
    name: config.name,
    initialState,
    reducers: {
      clearCurrent(state) {
        state[currentField] = null;
      },
      clearError(state) {
        state.error = null;
      },
    },
    extraReducers: (builder) => {
      builder
        .addCase(fetchList.pending, (state) => {
          state.loading = true;
          state.error = null;
        })
        .addCase(fetchList.fulfilled, (state, action) => {
          state.loading = false;
          // Dynamic field name → write through an untyped record view; Immer
          // tracks mutations on the same draft proxy.
          const draft = state as Record<string, unknown>;
          const payload = action.payload;
          if (paginated && isPaginated(payload)) {
            draft[itemsField] = payload.items;
            state.total = payload.total;
            state.offset = payload.offset;
            state.limit = payload.limit;
          } else {
            draft[itemsField] = isPaginated(payload) ? payload.items : payload;
          }
        })
        .addCase(fetchList.rejected, (state, action) => {
          state.loading = false;
          state.error = action.error.message ?? errorKey;
        });

      if (fetchOne) {
        if (singleFetchTogglesStatus) {
          builder
            .addCase(fetchOne.pending, (state) => {
              state.loading = true;
              state.error = null;
            })
            .addCase(fetchOne.fulfilled, (state, action) => {
              state.loading = false;
              (state as Record<string, unknown>)[currentField] = action.payload;
            })
            .addCase(fetchOne.rejected, (state, action) => {
              state.loading = false;
              state.error = action.error.message ?? errorKey;
            });
        } else {
          builder.addCase(fetchOne.fulfilled, (state, action) => {
            (state as Record<string, unknown>)[currentField] = action.payload;
          });
        }
      }

      config.extraCases?.(
        builder as unknown as ActionReducerMapBuilder<ListState<T, IF, CF>>,
      );
    },
  });

  return {
    slice,
    // The reducer works on the Immer-friendly `DraftListState`; expose it as the
    // precise `ListState` so `RootState` keeps the domain-named, fully-typed
    // fields (`s.tanks.tanks: Tank[]`).
    reducer: slice.reducer as unknown as Reducer<ListState<T, IF, CF>>,
    fetchList,
    fetchOne,
    actions: slice.actions,
  };
}
