import { type ReactNode, useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import TablePagination from '@mui/material/TablePagination';
import TableSortLabel from '@mui/material/TableSortLabel';
import Paper from '@mui/material/Paper';
import TextField from '@mui/material/TextField';
import InputAdornment from '@mui/material/InputAdornment';
import Chip from '@mui/material/Chip';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import SearchIcon from '@mui/icons-material/Search';
import SearchOffIcon from '@mui/icons-material/SearchOff';
import LoadingSkeleton from './LoadingSkeleton';
import EmptyState from './EmptyState';
import { useDebounce } from '@/hooks/useDebounce';
import type { TableState } from '@/hooks/useTableState';

export interface Column<T> {
  id: string;
  label: string;
  render: (row: T) => ReactNode;
  width?: number | string;
  align?: 'left' | 'right' | 'center';
  sortable?: boolean;
  sortKey?: string;
  sortFn?: (a: T, b: T) => number;
  searchable?: boolean;
  searchValue?: (row: T) => string;
  hideBelowBreakpoint?: 'md' | 'lg';
}

interface DataTableProps<T> {
  columns: Column<T>[];
  rows: T[];
  loading?: boolean;
  total?: number;
  page?: number;
  rowsPerPage?: number;
  onPageChange?: (page: number) => void;
  onRowsPerPageChange?: (rowsPerPage: number) => void;
  onRowClick?: (row: T) => void;
  emptyMessage?: string;
  emptyActionLabel?: string;
  onEmptyAction?: () => void;
  emptyIllustration?: string;
  getRowKey: (row: T) => string;
  tableState?: TableState;
  variant?: 'full' | 'simple';
  searchable?: boolean;
  ariaLabel?: string;
  stickyHeader?: boolean;
  mobileCardRenderer?: (row: T) => ReactNode;
  mobileBreakpoint?: 'sm' | 'md';
}

function defaultSearchExtractor<T>(row: T, col: Column<T>): string {
  if (col.searchValue) return col.searchValue(row);
  const rendered = col.render(row);
  if (typeof rendered === 'string') return rendered;
  if (typeof rendered === 'number') return String(rendered);
  return '';
}

function defaultComparator<T>(a: T, b: T, col: Column<T>): number {
  const aVal = defaultSearchExtractor(a, col);
  const bVal = defaultSearchExtractor(b, col);
  const aNum = Number(aVal);
  const bNum = Number(bVal);
  if (!isNaN(aNum) && !isNaN(bNum)) return aNum - bNum;
  return aVal.localeCompare(bVal, undefined, { sensitivity: 'base' });
}

export default function DataTable<T>({
  columns,
  rows,
  loading,
  total,
  page = 0,
  rowsPerPage = 50,
  onPageChange,
  onRowsPerPageChange,
  onRowClick,
  emptyMessage,
  emptyActionLabel,
  onEmptyAction,
  emptyIllustration,
  getRowKey,
  tableState,
  variant = 'full',
  searchable,
  ariaLabel,
  stickyHeader = true,
  mobileCardRenderer,
  mobileBreakpoint = 'sm',
}: DataTableProps<T>) {
  const { t } = useTranslation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down(mobileBreakpoint));
  const containerRef = useRef<HTMLDivElement>(null);
  const [scrollShadow, setScrollShadow] = useState<'none' | 'left' | 'right' | 'both'>('none');

  // Local search input state for debouncing
  const [searchInput, setSearchInput] = useState(tableState?.search ?? '');
  const debouncedSearch = useDebounce(searchInput, 300);

  // Sync debounced search to tableState
  useEffect(() => {
    if (tableState && debouncedSearch !== tableState.search) {
      tableState.setSearch(debouncedSearch);
    }
  }, [debouncedSearch]); // eslint-disable-line react-hooks/exhaustive-deps

  // Sync external search changes back to input
  useEffect(() => {
    if (tableState && tableState.search !== searchInput && tableState.search !== debouncedSearch) {
      setSearchInput(tableState.search);
    }
  }, [tableState?.search]); // eslint-disable-line react-hooks/exhaustive-deps

  // Scroll shadow detection
  const updateScrollShadow = useCallback(() => {
    const el = containerRef.current;
    if (!el) return;
    const { scrollLeft, scrollWidth, clientWidth } = el;
    const hasLeft = scrollLeft > 0;
    const hasRight = scrollLeft + clientWidth < scrollWidth - 1;
    if (hasLeft && hasRight) setScrollShadow('both');
    else if (hasLeft) setScrollShadow('left');
    else if (hasRight) setScrollShadow('right');
    else setScrollShadow('none');
  }, []);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    updateScrollShadow();
    el.addEventListener('scroll', updateScrollShadow);
    window.addEventListener('resize', updateScrollShadow);
    return () => {
      el.removeEventListener('scroll', updateScrollShadow);
      window.removeEventListener('resize', updateScrollShadow);
    };
  }, [updateScrollShadow]);

  // Processing pipeline when tableState is active
  const processedData = useMemo(() => {
    if (!tableState) return { rows, totalFiltered: rows.length };

    let filtered = rows;

    // 1. Search filter
    if (tableState.search) {
      const lower = tableState.search.toLowerCase();
      filtered = filtered.filter((row) =>
        columns.some((col) => {
          if (col.searchable === false) return false;
          return defaultSearchExtractor(row, col).toLowerCase().includes(lower);
        }),
      );
    }

    // 2. Sort
    if (tableState.sort) {
      const sortCol = columns.find(
        (c) => c.id === tableState.sort!.column || c.sortKey === tableState.sort!.column,
      );
      if (sortCol) {
        const dir = tableState.sort.direction === 'asc' ? 1 : -1;
        filtered = [...filtered].sort((a, b) => {
          if (sortCol.sortFn) return sortCol.sortFn(a, b) * dir;
          return defaultComparator(a, b, sortCol) * dir;
        });
      }
    }

    const totalFiltered = filtered.length;

    // 3. Pagination
    const start = tableState.page * tableState.pageSize;
    const paged = filtered.slice(start, start + tableState.pageSize);

    return { rows: paged, totalFiltered };
  }, [rows, tableState, columns]);

  const showToolbar =
    variant === 'full' && tableState && (searchable !== false);
  const hasActiveSearch = !!tableState?.search;

  if (loading) {
    return <LoadingSkeleton variant="table" />;
  }

  // Empty state: no source data at all (before any filtering)
  if (rows.length === 0 && !hasActiveSearch) {
    return (
      <EmptyState
        message={emptyMessage}
        actionLabel={emptyActionLabel}
        onAction={onEmptyAction}
        illustration={emptyIllustration}
      />
    );
  }

  const scrollShadowSx = {
    position: 'relative' as const,
    '&::before, &::after': {
      content: '""',
      position: 'absolute',
      top: 0,
      bottom: 0,
      width: 16,
      pointerEvents: 'none',
      zIndex: 1,
      transition: 'opacity 0.2s',
    },
    '&::before': {
      left: 0,
      background: 'linear-gradient(to right, rgba(0,0,0,0.08), transparent)',
      opacity: scrollShadow === 'left' || scrollShadow === 'both' ? 1 : 0,
    },
    '&::after': {
      right: 0,
      background: 'linear-gradient(to left, rgba(0,0,0,0.08), transparent)',
      opacity: scrollShadow === 'right' || scrollShadow === 'both' ? 1 : 0,
    },
  };

  const displayRows = tableState ? processedData.rows : rows;
  const totalCount = tableState ? processedData.totalFiltered : (total ?? rows.length);

  // Column labels for sort chip
  const sortColumnLabel = tableState?.sort
    ? columns.find((c) => c.id === tableState.sort!.column)?.label ?? tableState.sort.column
    : '';

  return (
    <Paper variant="outlined" data-testid="data-table">
      {/* Toolbar */}
      {showToolbar && (
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: 1,
            px: 2,
            py: 1.5,
            borderBottom: 1,
            borderColor: 'divider',
          }}
        >
          <TextField
            size="small"
            placeholder={t('table.searchPlaceholder')}
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            slotProps={{
              input: {
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon fontSize="small" />
                  </InputAdornment>
                ),
              },
            }}
            sx={{ minWidth: 200, maxWidth: 300 }}
            data-testid="table-search-input"
          />
          {tableState.search && (
            <Chip
              label={`${t('common.search')}: "${tableState.search}"`}
              onDelete={() => {
                setSearchInput('');
                tableState.setSearch('');
              }}
              size="small"
              data-testid="search-chip"
            />
          )}
          {tableState.sort && (
            <Chip
              label={`${t('table.sortedBy')}: ${sortColumnLabel}`}
              onDelete={() => tableState.resetAll()}
              size="small"
              data-testid="sort-chip"
            />
          )}
          {(hasActiveSearch || tableState.sort) && (
            <Button
              size="small"
              onClick={() => {
                setSearchInput('');
                tableState.resetAll();
              }}
              data-testid="reset-filters-button"
            >
              {t('table.resetFilters')}
            </Button>
          )}
        </Box>
      )}

      {/* Mobile card view */}
      {isMobile && mobileCardRenderer ? (
        <Box
          sx={{ display: 'flex', flexDirection: 'column', gap: 1, p: 1 }}
          data-testid="data-table-cards"
        >
          {displayRows.map((row) => (
            <Box
              key={getRowKey(row)}
              onClick={() => onRowClick?.(row)}
              onKeyDown={
                onRowClick
                  ? (e) => { if (e.key === 'Enter') onRowClick(row); }
                  : undefined
              }
              tabIndex={onRowClick ? 0 : undefined}
              sx={{
                ...(onRowClick && {
                  cursor: 'pointer',
                  '&:focus-visible': {
                    outline: '2px solid',
                    outlineColor: 'primary.main',
                    outlineOffset: -2,
                  },
                }),
              }}
              data-testid="data-table-row"
            >
              {mobileCardRenderer(row)}
            </Box>
          ))}
        </Box>
      ) : (
        /* Desktop table view */
        <Box sx={scrollShadowSx}>
          <TableContainer ref={containerRef}>
            <Table
              size="small"
              stickyHeader={stickyHeader}
              aria-label={ariaLabel}
            >
              <TableHead>
                <TableRow>
                  {columns.map((col) => {
                    const isSortable = tableState && col.sortable !== false && col.id !== 'actions';
                    const isSorted = tableState?.sort?.column === col.id;
                    const responsiveSx = col.hideBelowBreakpoint
                      ? { display: { xs: 'none', [col.hideBelowBreakpoint]: 'table-cell' } }
                      : undefined;

                    return (
                      <TableCell
                        key={col.id}
                        width={col.width}
                        align={col.align}
                        sx={{
                          ...responsiveSx,
                          ...(stickyHeader && {
                            borderBottom: 2,
                            borderColor: 'divider',
                          }),
                        }}
                        sortDirection={isSorted ? tableState!.sort!.direction : false}
                        aria-sort={
                          isSorted
                            ? tableState!.sort!.direction === 'asc'
                              ? 'ascending'
                              : 'descending'
                            : undefined
                        }
                      >
                        {isSortable ? (
                          <TableSortLabel
                            active={isSorted}
                            direction={isSorted ? tableState!.sort!.direction : 'asc'}
                            onClick={() => tableState!.setSort(col.id)}
                          >
                            {col.label}
                          </TableSortLabel>
                        ) : (
                          col.label
                        )}
                      </TableCell>
                    );
                  })}
                </TableRow>
              </TableHead>
              <TableBody>
                {displayRows.map((row) => (
                  <TableRow
                    key={getRowKey(row)}
                    hover
                    onClick={() => onRowClick?.(row)}
                    onKeyDown={
                      onRowClick
                        ? (e) => {
                            if (e.key === 'Enter') onRowClick(row);
                          }
                        : undefined
                    }
                    tabIndex={onRowClick ? 0 : undefined}
                    sx={{
                      ...(onRowClick && {
                        cursor: 'pointer',
                        '&:focus-visible': {
                          outline: '2px solid',
                          outlineColor: 'primary.main',
                          outlineOffset: -2,
                        },
                      }),
                    }}
                    data-testid="data-table-row"
                  >
                    {columns.map((col) => {
                      const responsiveSx = col.hideBelowBreakpoint
                        ? { display: { xs: 'none', [col.hideBelowBreakpoint]: 'table-cell' } }
                        : undefined;
                      return (
                        <TableCell key={col.id} align={col.align} sx={responsiveSx}>
                          {col.render(row)}
                        </TableCell>
                      );
                    })}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )}

      {/* No search results state */}
      {tableState && processedData.totalFiltered === 0 && rows.length > 0 && (
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            py: 6,
            gap: 1,
          }}
          data-testid="no-search-results"
        >
          <SearchOffIcon sx={{ fontSize: 48, color: 'text.disabled' }} />
          <Typography color="text.secondary">
            {t('table.noSearchResults')}
          </Typography>
          <Button
            size="small"
            onClick={() => {
              setSearchInput('');
              tableState.resetAll();
            }}
          >
            {t('table.resetFilters')}
          </Button>
        </Box>
      )}

      {/* Pagination */}
      {tableState && variant === 'full' && processedData.totalFiltered > 0 && (
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
          }}
        >
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ pl: 2 }}
            data-testid="showing-count"
          >
            {t('table.showing', {
              from: tableState.page * tableState.pageSize + 1,
              to: Math.min(
                (tableState.page + 1) * tableState.pageSize,
                totalCount,
              ),
              total: totalCount,
            })}
          </Typography>
          <TablePagination
            component="div"
            count={totalCount}
            page={tableState.page}
            onPageChange={(_, newPage) => tableState.setPage(newPage)}
            rowsPerPage={tableState.pageSize}
            onRowsPerPageChange={(e) =>
              tableState.setPageSize(parseInt(e.target.value, 10))
            }
            labelRowsPerPage={t('common.rowsPerPage')}
            rowsPerPageOptions={[10, 25, 50, 100]}
          />
        </Box>
      )}

      {/* Legacy pagination (server-side) */}
      {!tableState &&
        total !== undefined &&
        onPageChange &&
        onRowsPerPageChange && (
          <TablePagination
            component="div"
            count={total}
            page={page}
            onPageChange={(_, newPage) => onPageChange(newPage)}
            rowsPerPage={rowsPerPage}
            onRowsPerPageChange={(e) =>
              onRowsPerPageChange(parseInt(e.target.value, 10))
            }
            labelRowsPerPage={t('common.rowsPerPage')}
            rowsPerPageOptions={[10, 25, 50, 100]}
          />
        )}
    </Paper>
  );
}
