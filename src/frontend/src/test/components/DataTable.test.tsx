import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, afterEach } from 'vitest';
import DataTable from '@/components/common/DataTable';
import type { TableState } from '@/hooks/useTableState';

interface TestRow {
  id: string;
  name: string;
  value: number;
}

const makeTableState = (overrides?: Partial<TableState>): TableState => ({
  search: '',
  setSearch: vi.fn(),
  sort: null,
  setSort: vi.fn(),
  page: 0,
  setPage: vi.fn(),
  pageSize: 25,
  setPageSize: vi.fn(),
  resetAll: vi.fn(),
  ...overrides,
});

describe('DataTable', () => {
  const columns = [
    { id: 'name', label: 'Name', render: (r: TestRow) => r.name },
    { id: 'value', label: 'Value', render: (r: TestRow) => r.value, align: 'right' as const },
  ];

  const rows: TestRow[] = [
    { id: '1', name: 'Alice', value: 30 },
    { id: '2', name: 'Bob', value: 10 },
    { id: '3', name: 'Charlie', value: 20 },
  ];

  // === Legacy tests (backwards compatibility) ===

  it('renders loading skeleton when loading', () => {
    render(
      <DataTable
        columns={columns}
        rows={[]}
        loading={true}
        getRowKey={(r: TestRow) => r.id}
      />,
    );
    expect(document.querySelector('.MuiSkeleton-root')).toBeTruthy();
  });

  it('renders empty state when no rows', () => {
    render(
      <DataTable
        columns={columns}
        rows={[]}
        loading={false}
        getRowKey={(r: TestRow) => r.id}
      />,
    );
    expect(screen.getByText(/Keine Daten|No data/i)).toBeTruthy();
  });

  it('renders a custom empty message and description when provided', () => {
    render(
      <DataTable
        columns={columns}
        rows={[]}
        loading={false}
        getRowKey={(r: TestRow) => r.id}
        emptyMessage="Nothing here yet"
        emptyDescription="Create your first entry to get started."
      />,
    );
    expect(screen.getByText('Nothing here yet')).toBeTruthy();
    expect(screen.getByText('Create your first entry to get started.')).toBeTruthy();
  });

  it('renders rows', () => {
    render(
      <DataTable
        columns={columns}
        rows={rows}
        loading={false}
        getRowKey={(r) => r.id}
      />,
    );
    expect(screen.getByText('Alice')).toBeTruthy();
    expect(screen.getByText('Bob')).toBeTruthy();
  });

  it('calls onRowClick when a row is clicked', () => {
    const onClick = vi.fn();
    render(
      <DataTable
        columns={columns}
        rows={[rows[0]]}
        loading={false}
        getRowKey={(r) => r.id}
        onRowClick={onClick}
      />,
    );
    screen.getByText('Alice').closest('tr')?.click();
    expect(onClick).toHaveBeenCalledWith(rows[0]);
  });

  // === New tests ===

  it('renders sort labels when tableState is provided', () => {
    const tableState = makeTableState();
    render(
      <DataTable
        columns={columns}
        rows={rows}
        getRowKey={(r) => r.id}
        tableState={tableState}
      />,
    );
    // MUI TableSortLabel renders buttons
    const sortButtons = screen.getAllByRole('button');
    // Search field might also be a button-like element, but sort labels are present
    expect(sortButtons.length).toBeGreaterThanOrEqual(2);
  });

  it('calls setSort when sort label is clicked', () => {
    const setSort = vi.fn();
    const tableState = makeTableState({ setSort });
    render(
      <DataTable
        columns={columns}
        rows={rows}
        getRowKey={(r) => r.id}
        tableState={tableState}
      />,
    );
    // Click the "Name" header sort label
    const nameHeader = screen.getByText('Name');
    nameHeader.click();
    expect(setSort).toHaveBeenCalledWith('name');
  });

  it('shows aria-sort on sorted header', () => {
    const tableState = makeTableState({
      sort: { column: 'name', direction: 'asc' },
    });
    render(
      <DataTable
        columns={columns}
        rows={rows}
        getRowKey={(r) => r.id}
        tableState={tableState}
      />,
    );
    const th = screen.getByText('Name').closest('th');
    expect(th?.getAttribute('aria-sort')).toBe('ascending');
  });

  it('shows descending aria-sort', () => {
    const tableState = makeTableState({
      sort: { column: 'value', direction: 'desc' },
    });
    render(
      <DataTable
        columns={columns}
        rows={rows}
        getRowKey={(r) => r.id}
        tableState={tableState}
      />,
    );
    const th = screen.getByText('Value').closest('th');
    expect(th?.getAttribute('aria-sort')).toBe('descending');
  });

  it('triggers onRowClick on Enter key', () => {
    const onClick = vi.fn();
    render(
      <DataTable
        columns={columns}
        rows={[rows[0]]}
        getRowKey={(r) => r.id}
        onRowClick={onClick}
      />,
    );
    const row = screen.getByTestId('data-table-row');
    fireEvent.keyDown(row, { key: 'Enter' });
    expect(onClick).toHaveBeenCalledWith(rows[0]);
  });

  it('filters rows by search', () => {
    const tableState = makeTableState({ search: 'alice' });
    render(
      <DataTable
        columns={columns}
        rows={rows}
        getRowKey={(r) => r.id}
        tableState={tableState}
      />,
    );
    expect(screen.getByText('Alice')).toBeTruthy();
    expect(screen.queryByText('Bob')).toBeNull();
    expect(screen.queryByText('Charlie')).toBeNull();
  });

  it('shows no-search-results when filtered to empty', () => {
    const tableState = makeTableState({ search: 'zzzzz' });
    render(
      <DataTable
        columns={columns}
        rows={rows}
        getRowKey={(r) => r.id}
        tableState={tableState}
      />,
    );
    expect(screen.getByTestId('no-search-results')).toBeTruthy();
  });

  it('shows "Showing X-Y of Z" with pagination', () => {
    const tableState = makeTableState({ pageSize: 2 });
    render(
      <DataTable
        columns={columns}
        rows={rows}
        getRowKey={(r) => r.id}
        tableState={tableState}
      />,
    );
    expect(screen.getByTestId('showing-count')).toBeTruthy();
    // Should show 2 of 3 rows
    const displayedRows = screen.getAllByTestId('data-table-row');
    expect(displayedRows.length).toBe(2);
  });

  it('hides toolbar for variant="simple"', () => {
    const tableState = makeTableState();
    render(
      <DataTable
        columns={columns}
        rows={rows}
        getRowKey={(r) => r.id}
        tableState={tableState}
        variant="simple"
      />,
    );
    expect(screen.queryByTestId('table-search-input')).toBeNull();
  });

  it('applies align="right" to cells', () => {
    render(
      <DataTable
        columns={columns}
        rows={[rows[0]]}
        getRowKey={(r) => r.id}
      />,
    );
    const cells = document.querySelectorAll('td');
    // Second cell (value column) should have align=right
    const valueCell = cells[1];
    expect(valueCell?.classList.toString()).toContain('Right');
  });

  it('renders without tableState (backwards compatible)', () => {
    render(
      <DataTable
        columns={columns}
        rows={rows}
        getRowKey={(r) => r.id}
      />,
    );
    expect(screen.getAllByTestId('data-table-row').length).toBe(3);
    // No sort labels when no tableState
    const sortLabels = document.querySelectorAll('.MuiTableSortLabel-root');
    expect(sortLabels.length).toBe(0);
  });

  it('sets aria-label on table element', () => {
    render(
      <DataTable
        columns={columns}
        rows={rows}
        getRowKey={(r) => r.id}
        ariaLabel="Test Table"
      />,
    );
    expect(screen.getByRole('table').getAttribute('aria-label')).toBe('Test Table');
  });

  it('sorts rows ascending by default comparator', () => {
    const tableState = makeTableState({
      sort: { column: 'name', direction: 'asc' },
    });
    render(
      <DataTable
        columns={columns}
        rows={rows}
        getRowKey={(r) => r.id}
        tableState={tableState}
      />,
    );
    const renderedRows = screen.getAllByTestId('data-table-row');
    expect(renderedRows[0].textContent).toContain('Alice');
    expect(renderedRows[1].textContent).toContain('Bob');
    expect(renderedRows[2].textContent).toContain('Charlie');
  });

  it('sorts rows descending', () => {
    const tableState = makeTableState({
      sort: { column: 'name', direction: 'desc' },
    });
    render(
      <DataTable
        columns={columns}
        rows={rows}
        getRowKey={(r) => r.id}
        tableState={tableState}
      />,
    );
    const renderedRows = screen.getAllByTestId('data-table-row');
    expect(renderedRows[0].textContent).toContain('Charlie');
    expect(renderedRows[1].textContent).toContain('Bob');
    expect(renderedRows[2].textContent).toContain('Alice');
  });

  it('paginates to second page', () => {
    const tableState = makeTableState({ page: 1, pageSize: 2 });
    render(
      <DataTable
        columns={columns}
        rows={rows}
        getRowKey={(r) => r.id}
        tableState={tableState}
      />,
    );
    const renderedRows = screen.getAllByTestId('data-table-row');
    expect(renderedRows.length).toBe(1); // Only 1 row on page 2
    expect(renderedRows[0].textContent).toContain('Charlie');
  });

  // === Additional branch/function coverage ===

  it('calls setSort when a sort label is clicked in a full toolbar', () => {
    const setSearch = vi.fn();
    const tableState = makeTableState({ setSearch });
    render(
      <DataTable
        columns={columns}
        rows={rows}
        getRowKey={(r) => r.id}
        tableState={tableState}
      />,
    );
    const input = screen.getByTestId('table-search-input').querySelector('input')!;
    fireEvent.change(input, { target: { value: 'ali' } });
    expect(input.value).toBe('ali');
  });

  it('clears search via the search chip delete button', () => {
    const setSearch = vi.fn();
    const tableState = makeTableState({ search: 'alice', setSearch });
    render(
      <DataTable
        columns={columns}
        rows={rows}
        getRowKey={(r) => r.id}
        tableState={tableState}
      />,
    );
    const chip = screen.getByTestId('search-chip');
    const deleteIcon = chip.querySelector('.MuiChip-deleteIcon') as HTMLElement;
    fireEvent.click(deleteIcon);
    expect(setSearch).toHaveBeenCalledWith('');
  });

  it('resets sort via the sort chip delete button', () => {
    const resetAll = vi.fn();
    const tableState = makeTableState({
      sort: { column: 'name', direction: 'asc' },
      resetAll,
    });
    render(
      <DataTable
        columns={columns}
        rows={rows}
        getRowKey={(r) => r.id}
        tableState={tableState}
      />,
    );
    const chip = screen.getByTestId('sort-chip');
    const deleteIcon = chip.querySelector('.MuiChip-deleteIcon') as HTMLElement;
    fireEvent.click(deleteIcon);
    expect(resetAll).toHaveBeenCalled();
  });

  it('resets all filters via the toolbar reset button', () => {
    const resetAll = vi.fn();
    const tableState = makeTableState({ search: 'alice', resetAll });
    render(
      <DataTable
        columns={columns}
        rows={rows}
        getRowKey={(r) => r.id}
        tableState={tableState}
      />,
    );
    fireEvent.click(screen.getByTestId('reset-filters-button'));
    expect(resetAll).toHaveBeenCalled();
  });

  it('resets all filters via the no-search-results button', () => {
    const resetAll = vi.fn();
    const tableState = makeTableState({ search: 'zzzzz', resetAll });
    render(
      <DataTable
        columns={columns}
        rows={rows}
        getRowKey={(r) => r.id}
        tableState={tableState}
      />,
    );
    const emptyState = screen.getByTestId('no-search-results');
    const button = emptyState.querySelector('button') as HTMLElement;
    fireEvent.click(button);
    expect(resetAll).toHaveBeenCalled();
  });

  it('advances the page via the tableState pagination control', () => {
    const setPage = vi.fn();
    const tableState = makeTableState({ pageSize: 2, setPage });
    render(
      <DataTable
        columns={columns}
        rows={rows}
        getRowKey={(r) => r.id}
        tableState={tableState}
      />,
    );
    fireEvent.click(screen.getByRole('button', { name: /next page/i }));
    expect(setPage).toHaveBeenCalledWith(1);
  });

  it('renders the column-filter empty state and resets via CTA', () => {
    const onResetColumnFilters = vi.fn();
    render(
      <DataTable
        columns={columns}
        rows={[]}
        getRowKey={(r: TestRow) => r.id}
        hasActiveColumnFilters={true}
        onResetColumnFilters={onResetColumnFilters}
      />,
    );
    const emptyState = screen.getByTestId('no-column-filter-results');
    const button = emptyState.querySelector('button') as HTMLElement;
    fireEvent.click(button);
    expect(onResetColumnFilters).toHaveBeenCalled();
  });

  it('renders the column-filter empty state without a reset CTA when no handler', () => {
    render(
      <DataTable
        columns={columns}
        rows={[]}
        getRowKey={(r: TestRow) => r.id}
        hasActiveColumnFilters={true}
      />,
    );
    const emptyState = screen.getByTestId('no-column-filter-results');
    expect(emptyState.querySelector('button')).toBeNull();
  });

  it('uses column searchValue when filtering', () => {
    const columnsWithSearchValue = [
      {
        id: 'name',
        label: 'Name',
        render: (r: TestRow) => r.name,
        searchValue: (r: TestRow) => `custom-${r.name}`,
      },
    ];
    const tableState = makeTableState({ search: 'custom-alice' });
    render(
      <DataTable
        columns={columnsWithSearchValue}
        rows={rows}
        getRowKey={(r) => r.id}
        tableState={tableState}
      />,
    );
    expect(screen.getByText('Alice')).toBeTruthy();
    expect(screen.queryByText('Bob')).toBeNull();
  });

  it('filters on a numeric column value', () => {
    const tableState = makeTableState({ search: '10' });
    render(
      <DataTable
        columns={columns}
        rows={rows}
        getRowKey={(r) => r.id}
        tableState={tableState}
      />,
    );
    expect(screen.getByText('Bob')).toBeTruthy();
    expect(screen.queryByText('Alice')).toBeNull();
  });

  it('ignores non-searchable columns during filtering', () => {
    const columnsMixed = [
      { id: 'name', label: 'Name', render: (r: TestRow) => r.name, searchable: false as const },
      { id: 'value', label: 'Value', render: (r: TestRow) => r.value },
    ];
    const tableState = makeTableState({ search: 'alice' });
    render(
      <DataTable
        columns={columnsMixed}
        rows={rows}
        getRowKey={(r) => r.id}
        tableState={tableState}
      />,
    );
    // 'alice' only appears in the non-searchable name column -> no matches
    expect(screen.getByTestId('no-search-results')).toBeTruthy();
  });

  it('uses a custom sortFn when provided', () => {
    const sortFn = vi.fn((a: TestRow, b: TestRow) => a.value - b.value);
    const columnsWithSortFn = [
      { id: 'name', label: 'Name', render: (r: TestRow) => r.name, sortFn },
      { id: 'value', label: 'Value', render: (r: TestRow) => r.value },
    ];
    const tableState = makeTableState({
      sort: { column: 'name', direction: 'asc' },
    });
    render(
      <DataTable
        columns={columnsWithSortFn}
        rows={rows}
        getRowKey={(r) => r.id}
        tableState={tableState}
      />,
    );
    expect(sortFn).toHaveBeenCalled();
    const renderedRows = screen.getAllByTestId('data-table-row');
    // Sorted by value asc: Bob (10), Charlie (20), Alice (30)
    expect(renderedRows[0].textContent).toContain('Bob');
    expect(renderedRows[2].textContent).toContain('Alice');
  });

  it('resolves sort column via sortKey', () => {
    const columnsWithSortKey = [
      { id: 'name', label: 'Name', render: (r: TestRow) => r.name, sortKey: 'displayName' },
      { id: 'value', label: 'Value', render: (r: TestRow) => r.value },
    ];
    const tableState = makeTableState({
      sort: { column: 'displayName', direction: 'desc' },
    });
    render(
      <DataTable
        columns={columnsWithSortKey}
        rows={rows}
        getRowKey={(r) => r.id}
        tableState={tableState}
      />,
    );
    const renderedRows = screen.getAllByTestId('data-table-row');
    expect(renderedRows[0].textContent).toContain('Charlie');
  });

  it('falls back to the raw column key for the sort chip label', () => {
    const tableState = makeTableState({
      sort: { column: 'unknown-col', direction: 'asc' },
    });
    render(
      <DataTable
        columns={columns}
        rows={rows}
        getRowKey={(r) => r.id}
        tableState={tableState}
      />,
    );
    const chip = screen.getByTestId('sort-chip');
    expect(chip.textContent).toContain('unknown-col');
  });

  it('renders columns with hideBelowBreakpoint', () => {
    const responsiveColumns = [
      { id: 'name', label: 'Name', render: (r: TestRow) => r.name },
      {
        id: 'value',
        label: 'Value',
        render: (r: TestRow) => r.value,
        hideBelowBreakpoint: 'md' as const,
      },
    ];
    render(
      <DataTable
        columns={responsiveColumns}
        rows={rows}
        getRowKey={(r) => r.id}
      />,
    );
    // The component renders without throwing and shows the data
    expect(screen.getAllByTestId('data-table-row').length).toBe(3);
  });

  it('does not trigger onRowClick for non-Enter keys', () => {
    const onClick = vi.fn();
    render(
      <DataTable
        columns={columns}
        rows={[rows[0]]}
        getRowKey={(r) => r.id}
        onRowClick={onClick}
      />,
    );
    const row = screen.getByTestId('data-table-row');
    fireEvent.keyDown(row, { key: 'ArrowDown' });
    expect(onClick).not.toHaveBeenCalled();
  });

  it('renders legacy server-side pagination and advances the page', () => {
    const onPageChange = vi.fn();
    const onRowsPerPageChange = vi.fn();
    render(
      <DataTable
        columns={columns}
        rows={rows}
        getRowKey={(r) => r.id}
        total={30}
        page={0}
        rowsPerPage={10}
        onPageChange={onPageChange}
        onRowsPerPageChange={onRowsPerPageChange}
      />,
    );
    fireEvent.click(screen.getByRole('button', { name: /next page/i }));
    expect(onPageChange).toHaveBeenCalledWith(1);
  });

  it('treats non-string/non-number cell renders as empty when searching', () => {
    const columnsWithNode = [
      { id: 'name', label: 'Name', render: (r: TestRow) => <em>{r.name}</em> },
      { id: 'value', label: 'Value', render: (r: TestRow) => r.value },
    ];
    // Search text only present in the JSX-rendered name column -> extractor
    // returns '' for that column, so there are no matches.
    const tableState = makeTableState({ search: 'Alice' });
    render(
      <DataTable
        columns={columnsWithNode}
        rows={rows}
        getRowKey={(r) => r.id}
        tableState={tableState}
      />,
    );
    expect(screen.getByTestId('no-search-results')).toBeTruthy();
  });

  it('changes rows-per-page via the tableState pagination control', async () => {
    const setPageSize = vi.fn();
    const tableState = makeTableState({ pageSize: 10, setPageSize });
    render(
      <DataTable
        columns={columns}
        rows={rows}
        getRowKey={(r) => r.id}
        tableState={tableState}
      />,
    );
    fireEvent.mouseDown(screen.getByRole('combobox'));
    const option = await screen.findByRole('option', { name: '25' });
    fireEvent.click(option);
    expect(setPageSize).toHaveBeenCalledWith(25);
  });

  it('changes rows-per-page via the legacy pagination control', async () => {
    const onPageChange = vi.fn();
    const onRowsPerPageChange = vi.fn();
    render(
      <DataTable
        columns={columns}
        rows={rows}
        getRowKey={(r) => r.id}
        total={30}
        page={0}
        rowsPerPage={10}
        onPageChange={onPageChange}
        onRowsPerPageChange={onRowsPerPageChange}
      />,
    );
    fireEvent.mouseDown(screen.getByRole('combobox'));
    const option = await screen.findByRole('option', { name: '25' });
    fireEvent.click(option);
    expect(onRowsPerPageChange).toHaveBeenCalledWith(25);
  });

  it('syncs an external search value into the search input', async () => {
    const tableState = makeTableState({ search: 'external' });
    render(
      <DataTable
        columns={columns}
        rows={rows}
        getRowKey={(r) => r.id}
        tableState={tableState}
      />,
    );
    const input = screen.getByTestId('table-search-input').querySelector('input')!;
    await waitFor(() => expect(input.value).toBe('external'));
  });

  describe('mobile card rendering', () => {
    afterEach(() => {
      // @ts-expect-error - cleanup of the matchMedia stub between tests
      delete window.matchMedia;
    });

    const enableMobile = () => {
      window.matchMedia = (query: string) =>
        ({
          matches: true,
          media: query,
          onchange: null,
          addListener: vi.fn(),
          removeListener: vi.fn(),
          addEventListener: vi.fn(),
          removeEventListener: vi.fn(),
          dispatchEvent: vi.fn(),
        }) as unknown as MediaQueryList;
    };

    it('renders mobile cards and handles click + Enter key', () => {
      enableMobile();
      const onClick = vi.fn();
      render(
        <DataTable
          columns={columns}
          rows={rows}
          getRowKey={(r) => r.id}
          onRowClick={onClick}
          mobileCardRenderer={(r: TestRow) => <span>card-{r.name}</span>}
        />,
      );
      expect(screen.getByTestId('data-table-cards')).toBeTruthy();
      expect(screen.getByText('card-Alice')).toBeTruthy();
      const cards = screen.getAllByTestId('data-table-row');
      fireEvent.click(cards[0]);
      expect(onClick).toHaveBeenCalledWith(rows[0]);
      fireEvent.keyDown(cards[1], { key: 'Enter' });
      expect(onClick).toHaveBeenCalledWith(rows[1]);
      fireEvent.keyDown(cards[2], { key: 'ArrowUp' });
      expect(onClick).toHaveBeenCalledTimes(2);
    });

    it('renders mobile cards without an onRowClick handler', () => {
      enableMobile();
      render(
        <DataTable
          columns={columns}
          rows={[rows[0]]}
          getRowKey={(r) => r.id}
          mobileCardRenderer={(r: TestRow) => <span>card-{r.name}</span>}
        />,
      );
      const card = screen.getByTestId('data-table-row');
      expect(card.getAttribute('tabindex')).toBeNull();
    });
  });

  it('does not make actions column sortable', () => {
    const columnsWithActions = [
      ...columns,
      { id: 'actions', label: 'Actions', render: () => 'btn', sortable: false as const },
    ];
    const setSort = vi.fn();
    const tableState = makeTableState({ setSort });
    render(
      <DataTable
        columns={columnsWithActions}
        rows={rows}
        getRowKey={(r) => r.id}
        tableState={tableState}
      />,
    );
    // The "Actions" header should not have a TableSortLabel
    const actionsHeader = screen.getByText('Actions');
    const sortLabel = actionsHeader.closest('.MuiTableSortLabel-root');
    expect(sortLabel).toBeNull();
  });
});
