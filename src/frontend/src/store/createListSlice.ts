import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { ActionReducerMapBuilder } from '@reduxjs/toolkit';

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
 * Shared state shape for every list slice built with {@link createListSlice}.
 *
 * `error` holds either an i18n key (matching `errors.*`) or an already
 * user-facing ApiError message. It never holds raw English fallback prose:
 * `ErrorDisplay` resolves `errors.*` keys to the active locale (Code-Review
 * FE-L5). For plain-array endpoints the pagination fields stay at their
 * initial values.
 */
export interface ListState<T> {
  items: T[];
  total: number;
  offset: number;
  limit: number;
  current: T | null;
  loading: boolean;
  error: string | null;
}

export interface ListSliceConfig<T> {
  /** Slice name; also the action-type prefix (e.g. `species/fetchAll`). */
  name: string;
  /** Loads the list page. May resolve a paginated envelope or a plain array. */
  list: (offset: number, limit: number) => Promise<ListResult<T>>;
  /** Loads a single entity by key; omit for list-only slices. */
  getOne?: (key: string) => Promise<T>;
  /** i18n key stored in `error` when a rejected action carries no message. */
  errorKey?: string;
  /** Extension point for entity-specific thunks/cases. */
  extraCases?: (builder: ActionReducerMapBuilder<ListState<T>>) => void;
}

const DEFAULT_ERROR_KEY = 'errors.loadFailed';

function isPaginated<T>(payload: ListResult<T>): payload is PaginatedResult<T> {
  return !Array.isArray(payload);
}

/**
 * Builds a Redux Toolkit slice for the common "paginated list + optional
 * single fetch" pattern shared by ~13 stammdaten slices (Code-Review FE-D5).
 *
 * The returned thunks keep the conventional action-type prefixes
 * (`<name>/fetchAll`, `<name>/fetchOne`), so consuming pages and tests need no
 * changes when a hand-written slice is migrated. Re-export the members under
 * the slice's historical names.
 */
export function createListSlice<T>(config: ListSliceConfig<T>) {
  const errorKey = config.errorKey ?? DEFAULT_ERROR_KEY;

  const fetchList = createAsyncThunk(
    `${config.name}/fetchAll`,
    async ({ offset = 0, limit = 50 }: { offset?: number; limit?: number } = {}) =>
      config.list(offset, limit),
  );

  const { getOne } = config;
  const fetchOne = getOne
    ? createAsyncThunk(`${config.name}/fetchOne`, async (key: string) => getOne(key))
    : undefined;

  const initialState: ListState<T> = {
    items: [],
    total: 0,
    offset: 0,
    limit: 50,
    current: null,
    loading: false,
    error: null,
  };

  const slice = createSlice({
    name: config.name,
    initialState,
    reducers: {
      clearCurrent(state) {
        state.current = null;
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
          const payload = action.payload;
          if (isPaginated(payload)) {
            state.items = payload.items as (typeof state)['items'];
            state.total = payload.total;
            state.offset = payload.offset;
            state.limit = payload.limit;
          } else {
            state.items = payload as (typeof state)['items'];
          }
        })
        .addCase(fetchList.rejected, (state, action) => {
          state.loading = false;
          state.error = action.error.message ?? errorKey;
        });

      if (fetchOne) {
        builder
          .addCase(fetchOne.pending, (state) => {
            state.loading = true;
            state.error = null;
          })
          .addCase(fetchOne.fulfilled, (state, action) => {
            state.loading = false;
            state.current = action.payload as (typeof state)['current'];
          })
          .addCase(fetchOne.rejected, (state, action) => {
            state.loading = false;
            state.error = action.error.message ?? errorKey;
          });
      }

      config.extraCases?.(builder);
    },
  });

  return {
    slice,
    reducer: slice.reducer,
    fetchList,
    fetchOne,
    actions: slice.actions,
  };
}
