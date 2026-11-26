import { afterEach, describe, expect, it, vi } from 'vitest';
import { act, render, screen } from '@testing-library/react';
import i18n from '@/i18n/i18n';
import DataTable from '@/components/common/DataTable';
import type { TableState } from '@/hooks/useTableState';
import { formatFixed } from '@/utils/formatting';

/**
 * #3025 M14 review — cells show numbers in the UI language ("6,5" in German). The
 * comparator must still sort them as numbers, and the search must find "6,5" when the
 * user types "6.5" (and the other way round). The search state is handed in directly,
 * so the input's 300 ms debounce is not involved.
 */
interface Row {
  id: string;
  name: string;
  ph: number;
}

const rows: Row[] = [
  { id: 'a', name: 'Kokos', ph: 10.2 },
  { id: 'b', name: 'Perlit', ph: 6.5 },
  { id: 'c', name: 'Torf', ph: 1234.5 },
];

const columns = [
  { id: 'name', label: 'Name', render: (r: Row) => r.name },
  { id: 'ph', label: 'pH', render: (r: Row) => formatFixed(r.ph, 1), align: 'right' as const },
];

function state(overrides: Partial<TableState>): TableState {
  return {
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
  };
}

function renderTable(overrides: Partial<TableState>) {
  render(<DataTable columns={columns} rows={rows} getRowKey={(r) => r.id} tableState={state(overrides)} />);
}

function namesInOrder(): string[] {
  return screen
    .getAllByRole('row')
    .slice(1)
    .map((row) => row.querySelector('td')?.textContent ?? '');
}

describe('DataTable with numbers in the UI language (#3025)', () => {
  const initial = i18n.language;
  afterEach(async () => {
    await act(async () => {
      await i18n.changeLanguage(initial);
    });
  });

  it.each(['de', 'en'])('sorts a formatted numeric column numerically (%s)', async (language) => {
    await act(async () => {
      await i18n.changeLanguage(language);
    });
    renderTable({ sort: { column: 'ph', direction: 'asc' } });
    // As text, "10,2" < "1.234,5" < "6,5" (de) / "1,234.5" < "10.2" < "6.5" (en) — numerically 6.5 < 10.2 < 1234.5.
    expect(namesInOrder()).toEqual(['Perlit', 'Kokos', 'Torf']);
  });

  it.each([
    ['de', '6.5'],
    ['de', '6,5'],
    ['de', '6,'],
    ['en', '6,5'],
    ['en', '6.5'],
  ])('finds the pH cell in %s for the query %j', async (language, query) => {
    await act(async () => {
      await i18n.changeLanguage(language);
    });
    renderTable({ search: query });
    expect(namesInOrder()).toEqual(['Perlit']);
  });

  it('keeps plain-text search unchanged', async () => {
    await act(async () => {
      await i18n.changeLanguage('de');
    });
    renderTable({ search: 'perl' });
    expect(namesInOrder()).toEqual(['Perlit']);
    renderTable({ search: 'x,y' });
    expect(screen.getAllByTestId('no-search-results').length).toBeGreaterThan(0);
  });
});
