import { useState, useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';

export interface SortState {
  column: string;
  direction: 'asc' | 'desc';
}

export interface TableState {
  search: string;
  setSearch: (v: string) => void;
  sort: SortState | null;
  setSort: (column: string) => void;
  page: number;
  setPage: (p: number) => void;
  pageSize: number;
  setPageSize: (s: number) => void;
  resetAll: () => void;
}

export interface TableStateConfig {
  defaultSort?: SortState;
  defaultPageSize?: number;
  pageSizeStorageKey?: string;
}

function getStoredPageSize(key: string | undefined, fallback: number): number {
  if (!key) return fallback;
  try {
    const stored = localStorage.getItem(key);
    if (stored) {
      const parsed = parseInt(stored, 10);
      if (!isNaN(parsed) && parsed > 0) return parsed;
    }
  } catch {
    // localStorage unavailable
  }
  return fallback;
}

function storePageSize(key: string | undefined, size: number): void {
  if (!key) return;
  try {
    localStorage.setItem(key, String(size));
  } catch {
    // localStorage unavailable
  }
}

export function useTableLocalState(config: TableStateConfig = {}): TableState {
  const { defaultSort = null, defaultPageSize = 25, pageSizeStorageKey } = config;

  const [search, setSearchRaw] = useState('');
  const [sort, setSortRaw] = useState<SortState | null>(defaultSort);
  const [page, setPage] = useState(0);
  const [pageSize, setPageSizeRaw] = useState(() =>
    getStoredPageSize(pageSizeStorageKey, defaultPageSize),
  );

  const setSearch = useCallback((v: string) => {
    setSearchRaw(v);
    setPage(0);
  }, []);

  const setSort = useCallback((column: string) => {
    setSortRaw((prev) => {
      if (prev?.column === column) {
        return prev.direction === 'asc'
          ? { column, direction: 'desc' }
          : null;
      }
      return { column, direction: 'asc' };
    });
    setPage(0);
  }, []);

  const setPageSize = useCallback(
    (s: number) => {
      setPageSizeRaw(s);
      storePageSize(pageSizeStorageKey, s);
      setPage(0);
    },
    [pageSizeStorageKey],
  );

  const resetAll = useCallback(() => {
    setSearchRaw('');
    setSortRaw(defaultSort);
    setPage(0);
    setPageSizeRaw(getStoredPageSize(pageSizeStorageKey, defaultPageSize));
  }, [defaultSort, defaultPageSize, pageSizeStorageKey]);

  return useMemo(
    () => ({ search, setSearch, sort, setSort, page, setPage, pageSize, setPageSize, resetAll }),
    [search, setSearch, sort, setSort, page, pageSize, setPageSize, resetAll],
  );
}

export function useTableUrlState(config: TableStateConfig = {}): TableState {
  const { defaultSort = null, defaultPageSize = 25, pageSizeStorageKey } = config;
  const [searchParams, setSearchParams] = useSearchParams();

  const search = searchParams.get('q') ?? '';
  const sortColumn = searchParams.get('sort');
  const sortDir = searchParams.get('dir') as 'asc' | 'desc' | null;
  const sort = useMemo<SortState | null>(
    () =>
      sortColumn && (sortDir === 'asc' || sortDir === 'desc')
        ? { column: sortColumn, direction: sortDir }
        : defaultSort,
    [sortColumn, sortDir, defaultSort],
  );

  const pageParam = searchParams.get('page');
  const page = pageParam ? Math.max(0, parseInt(pageParam, 10) - 1) : 0;

  const pageSizeParam = searchParams.get('pageSize');
  const pageSize = pageSizeParam
    ? parseInt(pageSizeParam, 10)
    : getStoredPageSize(pageSizeStorageKey, defaultPageSize);

  const updateParams = useCallback(
    (updates: Record<string, string | null>) => {
      setSearchParams(
        (prev) => {
          const next = new URLSearchParams(prev);
          for (const [k, v] of Object.entries(updates)) {
            if (v === null) {
              next.delete(k);
            } else {
              next.set(k, v);
            }
          }
          return next;
        },
        { replace: true },
      );
    },
    [setSearchParams],
  );

  const setSearch = useCallback(
    (v: string) => {
      updateParams({
        q: v || null,
        page: null, // reset page on search
      });
    },
    [updateParams],
  );

  const setSort = useCallback(
    (column: string) => {
      if (sort?.column === column) {
        if (sort.direction === 'asc') {
          updateParams({ sort: column, dir: 'desc', page: null });
        } else {
          // Remove sort (back to default or no sort)
          if (defaultSort) {
            updateParams({ sort: defaultSort.column, dir: defaultSort.direction, page: null });
          } else {
            updateParams({ sort: null, dir: null, page: null });
          }
        }
      } else {
        updateParams({ sort: column, dir: 'asc', page: null });
      }
    },
    [sort, defaultSort, updateParams],
  );

  const setPage = useCallback(
    (p: number) => {
      updateParams({ page: p > 0 ? String(p + 1) : null });
    },
    [updateParams],
  );

  const setPageSize = useCallback(
    (s: number) => {
      storePageSize(pageSizeStorageKey, s);
      updateParams({ pageSize: String(s), page: null });
    },
    [pageSizeStorageKey, updateParams],
  );

  const resetAll = useCallback(() => {
    setSearchParams({}, { replace: true });
  }, [setSearchParams]);

  return useMemo(
    () => ({ search, setSearch, sort, setSort, page, setPage, pageSize, setPageSize, resetAll }),
    [search, setSearch, sort, setSort, page, setPage, pageSize, setPageSize, resetAll],
  );
}
