import { describe, it, expect, vi } from 'vitest';
import { act, fireEvent, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import DataTable, { type Column } from '@/components/common/DataTable';
import type { TableState } from '@/hooks/useTableState';
import i18n from '@/i18n';
import { renderWithProviders } from '@/test/helpers';

/**
 * #3020 — `Column.helpTerm` (UI-NFR-011 §6.2): a domain-term column carries the
 * glossary trigger in its header. `TableSortLabel` is itself a button, so the
 * trigger has to sit beside it — and activating it must never sort.
 */

interface Row {
  id: string;
  ec: number;
}

const makeTableState = (setSort = vi.fn()): TableState => ({
  search: '',
  setSearch: vi.fn(),
  sort: null,
  setSort,
  page: 0,
  setPage: vi.fn(),
  pageSize: 25,
  setPageSize: vi.fn(),
  resetAll: vi.fn(),
});

const columns: Column<Row>[] = [
  { id: 'id', label: 'Id', render: (r) => r.id },
  { id: 'ec', label: 'EC (mS/cm)', helpTerm: 'ec', render: (r) => r.ec, align: 'right' },
];

const rows: Row[] = [
  { id: 'a', ec: 1.2 },
  { id: 'b', ec: 0.8 },
];

function renderTable(setSort = vi.fn()) {
  renderWithProviders(
    <DataTable
      columns={columns}
      rows={rows}
      getRowKey={(r) => r.id}
      tableState={makeTableState(setSort)}
      searchable={false}
    />,
  );
  return setSort;
}

function headerHelp(): HTMLElement {
  const button = screen.getByTestId('help-tooltip-icon-ec').closest('button');
  if (!button) throw new Error('no help button in the EC header');
  return button;
}

describe('DataTable column helpTerm (#3020)', () => {
  it('renders a named help trigger inside the column header, beside the sort control', () => {
    renderTable();
    const header = screen.getByRole('columnheader', { name: /EC \(mS\/cm\)/ });
    const help = headerHelp();
    expect(header.contains(help)).toBe(true);
    expect(help).toHaveAccessibleName(i18n.t('glossary.ec.short'));
    // Not nested in the sort button: a button inside a button is invalid and
    // its activation would bubble into the sort handler.
    expect(screen.getByTestId('sort-ec').contains(help)).toBe(false);
    // Columns without helpTerm render no trigger.
    expect(screen.queryAllByTestId(/^help-tooltip-icon-/)).toHaveLength(1);
  });

  it('does not sort when the help trigger is clicked, but opens the tooltip', async () => {
    const setSort = renderTable();
    await act(async () => {
      fireEvent.click(headerHelp());
    });
    expect(setSort).not.toHaveBeenCalled();
    const tooltip = await screen.findByRole('tooltip');
    expect(within(tooltip).getByText(i18n.t('glossary.ec.short'))).toBeTruthy();
  });

  it('is reachable by keyboard right after the sort control and does not sort on Enter/Space', async () => {
    const user = userEvent.setup();
    const setSort = renderTable();
    screen.getByTestId('sort-ec').focus();
    await user.tab();
    expect(document.activeElement).toBe(headerHelp());
    await user.keyboard('{Enter}');
    await user.keyboard(' ');
    expect(setSort).not.toHaveBeenCalled();
  });

  it('keeps sorting on the label itself', async () => {
    const user = userEvent.setup();
    const setSort = renderTable();
    await user.click(screen.getByTestId('sort-ec'));
    expect(setSort).toHaveBeenCalledWith('ec');
  });
});
