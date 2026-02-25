import { useState, useCallback } from 'react';

interface PaginationState {
  page: number;
  rowsPerPage: number;
  offset: number;
}

export function usePagination(initialRowsPerPage = 50) {
  const [state, setState] = useState<PaginationState>({
    page: 0,
    rowsPerPage: initialRowsPerPage,
    offset: 0,
  });

  const setPage = useCallback(
    (page: number) => {
      setState((prev) => ({
        ...prev,
        page,
        offset: page * prev.rowsPerPage,
      }));
    },
    [],
  );

  const setRowsPerPage = useCallback((rowsPerPage: number) => {
    setState({ page: 0, rowsPerPage, offset: 0 });
  }, []);

  return {
    ...state,
    setPage,
    setRowsPerPage,
  };
}
