import { useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';

/**
 * Generic, URL-backed multi-select column filter state.
 *
 * Each filter is serialised as a single comma-separated query parameter
 * (e.g. `?pest_type=insect,arachnid&difficulty=hard,medium`). Loading the page
 * rehydrates the active filters from the URL, so bookmarks, reloads and shared
 * links restore the exact same filter state.
 *
 * The hook deliberately reuses the same `useSearchParams` instance as
 * {@link useTableUrlState}; that table hook's `resetAll()` clears *all* query
 * params, which therefore also removes these filter params — so the existing
 * "Filter zurücksetzen" action transparently resets column filters too.
 *
 * Empty selections drop their param entirely to keep URLs clean.
 */
export interface ColumnFiltersResult {
  /** Currently selected values per filter id (URL-derived). */
  values: Record<string, string[]>;
  /** Replace the selected values for a single filter id. */
  setFilter: (id: string, selected: string[]) => void;
  /** Remove all column filters from the URL. */
  clearAll: () => void;
  /** Total number of selected values across every filter. */
  activeCount: number;
}

/**
 * @param filterIds Stable list of query-param names this hook owns. Only these
 *   params are read and written; unrelated params (search, sort, paging) are
 *   left untouched.
 */
export function useColumnFilters(filterIds: readonly string[]): ColumnFiltersResult {
  const [searchParams, setSearchParams] = useSearchParams();

  // Derive selected values from the URL. `searchParams.toString()` keeps the
  // memo dependency primitive and stable across renders.
  const search = searchParams.toString();
  const values = useMemo<Record<string, string[]>>(() => {
    const params = new URLSearchParams(search);
    const next: Record<string, string[]> = {};
    for (const id of filterIds) {
      const raw = params.get(id);
      next[id] = raw ? raw.split(',').filter(Boolean) : [];
    }
    return next;
    // filterIds is a stable literal array from the caller; `search` captures URL changes.
  }, [search, filterIds]);

  const setFilter = useCallback(
    (id: string, selected: string[]) => {
      setSearchParams(
        (prev) => {
          const next = new URLSearchParams(prev);
          // Always reset paging when a filter changes so users see page 1.
          next.delete('page');
          if (selected.length > 0) {
            next.set(id, selected.join(','));
          } else {
            next.delete(id);
          }
          return next;
        },
        { replace: true },
      );
    },
    [setSearchParams],
  );

  const clearAll = useCallback(() => {
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev);
        for (const id of filterIds) next.delete(id);
        next.delete('page');
        return next;
      },
      { replace: true },
    );
  }, [setSearchParams, filterIds]);

  const activeCount = useMemo(
    () => Object.values(values).reduce((sum, arr) => sum + arr.length, 0),
    [values],
  );

  return useMemo(
    () => ({ values, setFilter, clearAll, activeCount }),
    [values, setFilter, clearAll, activeCount],
  );
}
