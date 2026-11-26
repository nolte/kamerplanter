import { type KeyboardEvent, type ReactNode, useState, useRef, useEffect, useCallback, useMemo } from 'react';
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
import HelpTooltip from './HelpTooltip';
import { useDebounce } from '@/hooks/useDebounce';
import type { TableState } from '@/hooks/useTableState';
import { LinkedCard, LinkedTableRow, RowCellLink } from './DataTableRowLink';
import { compareText } from '@/utils/formatting';

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
  /**
   * Several values the search matches one by one (e.g. a name in every language,
   * #2936): a query must sit inside ONE of them, never across two. Wins over
   * `searchValue` for the search; sorting still uses `sortFn` / `searchValue`.
   */
  searchValues?: (row: T) => readonly string[];
  hideBelowBreakpoint?: 'md' | 'lg';
  /**
   * Glossary key of the domain term this column shows (e.g. "ec", "ppfd") — renders the shared
   * `HelpTooltip` trigger next to the header label (#3020, UI-NFR-011 §6.2). The trigger is a sibling
   * of the sort control, not inside it, so a click or Enter on it never sorts.
   */
  helpTerm?: string;
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
  /**
   * The detail URL a row leads to (#3017). Prefer it over `onRowClick` for navigation: the row then
   * carries a real link (named by its first visible cell) that keyboard and screen-reader users can
   * reach, and Ctrl/Cmd/Shift/middle click open it in a new tab. Wins over `onRowClick` when both are set.
   * `null` for a row that has no detail page (#3047): that row falls back to `onRowClick`, if any.
   */
  getRowHref?: (row: T) => string | null;
  emptyMessage?: string;
  /** Optional secondary sentence shown below `emptyMessage` (e.g. how to create the first entry). */
  emptyDescription?: string;
  emptyActionLabel?: string;
  onEmptyAction?: () => void;
  emptyIllustration?: string;
  getRowKey: (row: T) => string;
  tableState?: TableState;
  variant?: 'full' | 'simple';
  searchable?: boolean;
  ariaLabel?: string;
  /**
   * Stable, English identifier of the *section* this table renders (e.g.
   * `plant-tasks-active`). Emitted as `data-table-section` on the component
   * root, which is the only element both layouts share — the desktop `<Table>`
   * does not exist in the card layout, and `ariaLabel` (translated, and only
   * set on the `<Table>`) can neither be relied upon nor reaches the cards.
   *
   * The root keeps its `data-testid="data-table"`, so two tables on the same
   * page are told apart with
   * `[data-testid='data-table'][data-table-section='<id>']` in either layout
   * without breaking any selector that exists today.
   */
  sectionTestId?: string;
  stickyHeader?: boolean;
  mobileCardRenderer?: (row: T) => ReactNode;
  mobileBreakpoint?: 'sm' | 'md';
  /**
   * When `true` the DataTable knows that external column-filters are active and
   * that an empty `rows` array means "no matches" rather than "no data at all".
   * This swaps the generic EmptyState for the same "no results" view used by
   * the built-in text search so the user gets a meaningful empty state with a
   * "reset filters" CTA instead of the "create your first entry" illustration.
   */
  hasActiveColumnFilters?: boolean;
  /** Called when the user clicks the "reset filters" CTA in the column-filter
   *  empty state. Typically clears both the DataTable search and column filters. */
  onResetColumnFilters?: () => void;
}

/**
 * Puts a column's help trigger next to its header label (#3020). `TableSortLabel` is itself a
 * button, and a button inside a button is invalid HTML whose inner control screen readers flatten
 * away — so the trigger sits beside it, and `HelpTooltip` already swallows its own activation.
 */
function HeaderLabelWithHelp({ helpTerm, children }: { helpTerm?: string; children: ReactNode }) {
  if (!helpTerm) return <>{children}</>;
  return (
    <Box component="span" sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.25 }}>
      {children}
      <HelpTooltip term={helpTerm} iconOnly placement="bottom" />
    </Box>
  );
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
  return compareText(aVal, bVal, { sensitivity: 'base' });
}

/**
 * Keyboard activation for a clickable row/card (WCAG 2.1.1): Enter and Space
 * activate it, but only when the row itself has focus — a key pressed on a
 * nested control (row action button, link) must not also trigger the row.
 */
function activateRowOnKey(e: KeyboardEvent<HTMLElement>, activate: () => void): void {
  if (e.target !== e.currentTarget || e.repeat) return;
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();
    activate();
  }
}

const NESTED_FOCUSABLE = 'a[href], button, input, select, textarea, [tabindex]';

/**
 * A clickable card without a URL (it opens a dialog or panel) is announced as a button (#3017, W-01).
 * A button's children are presentational, so a card that holds its own link or control (diary entry,
 * garden bed) would turn into an invalid nested-interactive button; such a card becomes a named `group`
 * instead — still a role, and its inner controls stay reachable.
 */
function assignActionCardRole(el: HTMLElement | null): void {
  if (!el) return;
  el.setAttribute('role', el.querySelector(NESTED_FOCUSABLE) ? 'group' : 'button');
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
  getRowHref,
  emptyMessage,
  emptyDescription,
  emptyActionLabel,
  onEmptyAction,
  emptyIllustration,
  getRowKey,
  tableState,
  variant = 'full',
  searchable,
  ariaLabel,
  sectionTestId,
  stickyHeader = true,
  mobileCardRenderer,
  mobileBreakpoint = 'sm',
  hasActiveColumnFilters = false,
  onResetColumnFilters,
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
      // eslint-disable-next-line react-hooks/set-state-in-effect -- sync external search state back to local input
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
    // eslint-disable-next-line react-hooks/set-state-in-effect -- initial DOM measurement for scroll shadows
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
          if (col.searchValues) return col.searchValues(row).some((value) => value.toLowerCase().includes(lower));
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

  // Empty state: external column-filters produced zero matches.
  // Shown when the caller passes hasActiveColumnFilters=true and rows is empty.
  // We show the same "no search results" treatment (icon + reset CTA) rather than
  // the "create your first entry" illustration which would be misleading.
  if (rows.length === 0 && hasActiveColumnFilters) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          py: 6,
          gap: 1,
        }}
        data-testid="no-column-filter-results"
      >
        <SearchOffIcon sx={{ fontSize: 48, color: 'text.disabled' }} />
        <Typography color="text.secondary">{t('table.noFilterResults')}</Typography>
        {onResetColumnFilters && (
          <Button size="small" onClick={onResetColumnFilters}>
            {t('table.resetFilters')}
          </Button>
        )}
      </Box>
    );
  }

  // Empty state: no source data at all (before any filtering)
  if (rows.length === 0 && !hasActiveSearch) {
    return (
      <EmptyState
        message={emptyMessage}
        description={emptyDescription}
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
  // The cell that carries a row's link: the first one visible at every width and not an action column.
  const linkColumnId = columns.find((c) => !c.hideBelowBreakpoint && c.id !== 'actions')?.id;
  const totalCount = tableState ? processedData.totalFiltered : (total ?? rows.length);

  // Column labels for sort chip
  const sortColumnLabel = tableState?.sort
    ? columns.find((c) => c.id === tableState.sort!.column)?.label ?? tableState.sort.column
    : '';

  return (
    <Paper variant="outlined" data-testid="data-table" data-table-section={sectionTestId}>
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
              htmlInput: { 'aria-label': t('table.searchPlaceholder') },
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
          {displayRows.map((row) => {
            const href = getRowHref?.(row) ?? null;
            return href !== null ? (
              <LinkedCard key={getRowKey(row)} href={href} rowKey={getRowKey(row)}>
                {mobileCardRenderer(row)}
              </LinkedCard>
            ) : (
            <Box
              key={getRowKey(row)}
              onClick={() => onRowClick?.(row)}
              onKeyDown={
                onRowClick ? (e) => activateRowOnKey(e, () => onRowClick(row)) : undefined
              }
              tabIndex={onRowClick ? 0 : undefined}
              ref={onRowClick ? assignActionCardRole : undefined}
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
              data-row-key={getRowKey(row)}
            >
              {mobileCardRenderer(row)}
            </Box>
            );
          })}
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
                        <HeaderLabelWithHelp helpTerm={col.helpTerm}>
                          {isSortable ? (
                            // `data-testid` belongs on the label, not on the surrounding
                            // cell: the click handler lives here, and a click that lands on
                            // the cell beside this label never reaches it — DOM events
                            // bubble up, not down. The E2E suite clicked the `<th>` and so
                            // sorted nothing whenever a column was wider than its label,
                            // which stayed invisible because the sort chip is already
                            // rendered by `defaultSort` (#802).
                            <TableSortLabel
                              data-testid={`sort-${col.id}`}
                              active={isSorted}
                              direction={isSorted ? tableState!.sort!.direction : 'asc'}
                              onClick={() => tableState!.setSort(col.id)}
                            >
                              {col.label}
                            </TableSortLabel>
                          ) : (
                            col.label
                          )}
                        </HeaderLabelWithHelp>
                      </TableCell>
                    );
                  })}
                </TableRow>
              </TableHead>
              <TableBody>
                {displayRows.map((row) => {
                  const href = getRowHref?.(row) ?? null;
                  const cells = columns.map((col) => {
                    const responsiveSx = col.hideBelowBreakpoint
                      ? { display: { xs: 'none', [col.hideBelowBreakpoint]: 'table-cell' } }
                      : undefined;
                    return (
                      <TableCell
                        key={col.id}
                        align={col.align}
                        sx={responsiveSx}
                        data-testid={`cell-${col.id}`}
                      >
                        {href !== null && col.id === linkColumnId ? (
                          <RowCellLink href={href}>{col.render(row)}</RowCellLink>
                        ) : (
                          col.render(row)
                        )}
                      </TableCell>
                    );
                  });
                  if (href !== null) {
                    return (
                      <LinkedTableRow key={getRowKey(row)} href={href} rowKey={getRowKey(row)}>
                        {cells}
                      </LinkedTableRow>
                    );
                  }
                  return (
                  <TableRow
                    key={getRowKey(row)}
                    hover
                    onClick={() => onRowClick?.(row)}
                    onKeyDown={
                      onRowClick ? (e) => activateRowOnKey(e, () => onRowClick(row)) : undefined
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
                    data-row-key={getRowKey(row)}
                  >
                    {cells}
                  </TableRow>
                  );
                })}
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
            labelDisplayedRows={({ from, to, count }) =>
              `${from}–${to} ${t('common.of')} ${count !== -1 ? count : `> ${to}`}`
            }
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
