import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
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
