/**
 * #3017 (W-01, L-06, N-18) — DataTable rows that lead to a detail page carry a real link, and clickable
 * cards without a URL carry a role.
 *
 * Before: `onRowClick={() => navigate(...)}` on a focusable `<tr>`/`<div>` — no role, no name, no URL, so
 * Ctrl-, Cmd- and middle-click did nothing and a screen reader announced nothing actionable.
 */
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import DataTable from '@/components/common/DataTable';
import { expectNoA11yViolations } from '../a11y/expectNoA11yViolations';

interface Row {
  id: string;
  name: string;
  value: number;
}

const columns = [
  { id: 'name', label: 'Name', render: (r: Row) => r.name },
  { id: 'value', label: 'Value', render: (r: Row) => r.value },
];
const rows: Row[] = [
  { id: '1', name: 'Alice', value: 30 },
  { id: '2', name: 'Bob', value: 10 },
];

function Where() {
  return <div data-testid="where">{useLocation().pathname}</div>;
}

function renderLinked(extra: { mobile?: boolean } = {}) {
  return render(
    <MemoryRouter initialEntries={['/list']}>
      <Routes>
        <Route
          path="/list"
          element={
            <DataTable
              columns={columns}
              rows={rows}
              getRowKey={(r) => r.id}
              getRowHref={(r) => `/items/${r.id}`}
              ariaLabel="Items"
              mobileCardRenderer={extra.mobile ? (r: Row) => <span>card-{r.name}</span> : undefined}
            />
          }
        />
        <Route path="*" element={<Where />} />
      </Routes>
    </MemoryRouter>,
  );
}

/** This dom-testing-library has no `fireEvent.auxClick`; dispatch the event the browser sends. */
function auxClick(el: Element, button: number) {
  fireEvent(el, new MouseEvent('auxclick', { bubbles: true, cancelable: true, button }));
}

function stubMatchMedia(matches: boolean) {
  window.matchMedia = (query: string) =>
    ({
      matches,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }) as unknown as MediaQueryList;
}

describe('DataTable row links (#3017)', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    // @ts-expect-error - remove the per-test matchMedia stub
    delete window.matchMedia;
  });

  it('gives each linked row a real link named by its first cell', () => {
    renderLinked();
    const link = screen.getByRole('link', { name: 'Alice' });
    expect(link).toHaveAttribute('href', '/items/1');
    // The link is the row's one tab stop; the row itself is not a second one.
    expect(screen.getAllByTestId('data-table-row')[0]).not.toHaveAttribute('tabindex');
  });

  it('follows the link with Enter from the keyboard', async () => {
    const user = userEvent.setup();
    renderLinked();
    await user.tab();
    expect(screen.getByRole('link', { name: 'Alice' })).toHaveFocus();
    await user.keyboard('{Enter}');
    expect(screen.getByTestId('where')).toHaveTextContent('/items/1');
  });

  it('follows the row URL on a plain click anywhere on the row', async () => {
    const user = userEvent.setup();
    renderLinked();
    await user.click(screen.getByText('10'));
    expect(screen.getByTestId('where')).toHaveTextContent('/items/2');
  });

  it('opens the row in a new tab on Ctrl-click and middle-click instead of navigating', () => {
    const open = vi.spyOn(window, 'open').mockImplementation(() => null);
    renderLinked();
    const valueCell = screen.getByText('30');
    fireEvent.click(valueCell, { ctrlKey: true });
    fireEvent.click(valueCell, { metaKey: true });
    fireEvent(valueCell, new MouseEvent('auxclick', { bubbles: true, button: 1 }));
    expect(open).toHaveBeenCalledTimes(3);
    expect(open).toHaveBeenCalledWith('/items/1', '_blank', 'noopener');
    // Still on the list: none of the three navigated in place.
    expect(screen.queryByTestId('where')).toBeNull();
  });

  describe('a nested control owns its own clicks (#3069 SCR-001)', () => {
    const onInnerButton = vi.fn();
    const nestedColumns = [
      { id: 'name', label: 'Name', render: (r: Row) => r.name },
      {
        id: 'other',
        label: 'Other',
        render: (r: Row) => (
          <span>
            <a href={`/runs/${r.id}`} onClick={(e) => e.stopPropagation()}>
              run-{r.name}
            </a>
            <button type="button" onClick={(e) => { e.stopPropagation(); onInnerButton(); }}>
              act-{r.name}
            </button>
          </span>
        ),
      },
    ];

    function renderNested(mobile = false) {
      return render(
        <MemoryRouter initialEntries={['/list']}>
          <Routes>
            <Route
              path="/list"
              element={
                <DataTable
                  columns={nestedColumns}
                  rows={rows}
                  getRowKey={(r) => r.id}
                  getRowHref={(r) => `/items/${r.id}`}
                  ariaLabel="Items"
                  mobileCardRenderer={
                    mobile
                      ? (r: Row) => (
                          <span>
                            card-{r.name} {nestedColumns[1].render(r)}
                          </span>
                        )
                      : undefined
                  }
                />
              }
            />
            <Route path="*" element={<Where />} />
          </Routes>
        </MemoryRouter>,
      );
    }

    it('does not open the row URL on a middle click on an inner link or button', () => {
      const open = vi.spyOn(window, 'open').mockImplementation(() => null);
      renderNested();
      auxClick(screen.getByText('run-Alice'), 1);
      auxClick(screen.getByText('act-Alice'), 1);
      fireEvent.click(screen.getByText('run-Alice'), { ctrlKey: true });
      expect(open).not.toHaveBeenCalled();
      expect(screen.queryByTestId('where')).toBeNull();
    });

    it('still opens the row URL on a middle click elsewhere on the row', () => {
      const open = vi.spyOn(window, 'open').mockImplementation(() => null);
      renderNested();
      // The cell around the inner controls is plain row surface.
      auxClick(screen.getByText('run-Bob').closest('td')!, 1);
      expect(open).toHaveBeenCalledWith('/items/2', '_blank', 'noopener');
    });

    it('does not open the card URL on a middle click on an inner link or button of a mobile card', () => {
      stubMatchMedia(true);
      const open = vi.spyOn(window, 'open').mockImplementation(() => null);
      renderNested(true);
      auxClick(screen.getByText('run-Bob'), 1);
      auxClick(screen.getByText('act-Bob'), 1);
      expect(open).not.toHaveBeenCalled();
      // The card's own surface still opens its URL.
      auxClick(screen.getByText(/card-Bob/), 1);
      expect(open).toHaveBeenCalledWith('/items/2', '_blank', 'noopener');
    });
  });

  it('renders a linked mobile card as a link that Enter follows', async () => {
    stubMatchMedia(true);
    const user = userEvent.setup();
    renderLinked({ mobile: true });
    const card = screen.getByRole('link', { name: 'card-Bob' });
    card.focus();
    await user.keyboard('{Enter}');
    expect(screen.getByTestId('where')).toHaveTextContent('/items/2');
  });

  it('has no serious accessibility violations with links in the rows', async () => {
    const { container } = renderLinked();
    await expectNoA11yViolations(container, { minImpact: 'serious' });
  });
});

describe('DataTable action cards without a URL (#3017)', () => {
  afterEach(() => {
    // @ts-expect-error - remove the per-test matchMedia stub
    delete window.matchMedia;
  });

  it('leaves a row without a detail page unlinked and falls back to onRowClick (#3047)', async () => {
    const onRowClick = vi.fn();
    render(
      <MemoryRouter>
        <DataTable
          columns={columns}
          rows={rows}
          getRowKey={(r) => r.id}
          getRowHref={(r) => (r.id === '1' ? '/items/1' : null)}
          onRowClick={onRowClick}
          ariaLabel="Items"
        />
      </MemoryRouter>,
    );
    expect(screen.getByRole('link', { name: 'Alice' })).toHaveAttribute('href', '/items/1');
    expect(screen.queryByRole('link', { name: 'Bob' })).toBeNull();
    await userEvent.click(screen.getByText('Bob'));
    expect(onRowClick).toHaveBeenCalledWith(rows[1]);
  });

  it('announces a plain action card as a button', () => {
    stubMatchMedia(true);
    render(
      <DataTable
        columns={columns}
        rows={rows}
        getRowKey={(r) => r.id}
        onRowClick={vi.fn()}
        mobileCardRenderer={(r: Row) => <span>card-{r.name}</span>}
      />,
    );
    expect(screen.getByRole('button', { name: 'card-Alice' })).toBeInTheDocument();
  });

  it('makes a card that holds its own control a group, never a button with nested controls', async () => {
    stubMatchMedia(true);
    const { container } = render(
      <DataTable
        columns={columns}
        rows={rows}
        getRowKey={(r) => r.id}
        onRowClick={vi.fn()}
        mobileCardRenderer={(r: Row) => (
          <span>
            card-{r.name} <button type="button">inner</button>
          </span>
        )}
      />,
    );
    const cards = screen.getAllByTestId('data-table-row');
    expect(cards[0]).toHaveAttribute('role', 'group');
    await expectNoA11yViolations(container, { minImpact: 'serious' });
  });
});
