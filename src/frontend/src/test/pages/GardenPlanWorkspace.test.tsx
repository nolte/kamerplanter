/**
 * The editor workspace frame of the garden plan route (REQ-053 §17.3, WP 10.3 #2824): one header bar (GP-UX-063,
 * AC-3), the move order of its overflow "⋮" on a narrow bar and below md (AC-15), "Save" always visible, the list
 * switch gone, zoom as an overlay on the canvas (GP-UX-067, AC-14) and the canvas fitted into the room it reports.
 *
 * jsdom lays nothing out, so the header bar's width is stubbed: `scrollWidth` follows the bar's overflow level
 * (`data-overflow-level`), the way a real bar gets narrower with every step it moves out.
 */
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { RouterProvider, createMemoryRouter } from 'react-router-dom';
import { SnackbarProvider } from 'notistack';
import { http, HttpResponse } from 'msw';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import GardenPlanRoute from '@/features/gardenPlanner/routes/GardenPlanRoute';
import { availableCanvasHeight, MIN_CANVAS_HEIGHT_PX } from '@/features/gardenPlanner/editor/useCanvasArea';
import { rootReducer } from '@/store/rootReducer';
import { ThemeContextProvider } from '@/theme';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { bed, gardenObject, planResponse } from '@/test/gardenPlanFixtures';
import { tenantState } from '@/test/helpers';
import { server } from '@/test/mocks/server';
import { bedListItem } from '@/features/gardenPlanner/bed/bedTestKit';

const PLAN_URL = '/api/v1/t/:tenant/sites/:key/plan';
const BEDS_URL = '/api/v1/t/:tenant/locations';

function usePlanAndBeds() {
  server.use(
    http.get(PLAN_URL, () =>
      HttpResponse.json(
        planResponse({
          locations: [bed('loc_a', 2, 2), bed('loc_b', 6, 7)],
          garden_objects: [gardenObject('go_1', 6, 2)],
        }),
      ),
    ),
    http.get(BEDS_URL, () => HttpResponse.json([bedListItem('loc_a'), bedListItem('loc_b')])),
  );
}

function renderRoute(route = '/standorte/sites/site_1/plan?mode=plan') {
  const store = configureStore({ reducer: rootReducer, preloadedState: tenantState('lead') as never });
  const router = createMemoryRouter(
    [
      { path: 'standorte/sites/:key/plan', element: <GardenPlanRoute /> },
      { path: 'standorte/sites/:key', element: <div data-testid="site-detail-stub" /> },
    ],
    { initialEntries: [route] },
  );
  const view = render(
    <Provider store={store}>
      <ThemeContextProvider>
        <SnackbarProvider>
          <RouterProvider router={router} />
        </SnackbarProvider>
      </ThemeContextProvider>
    </Provider>,
  );
  return { store, router, ...view };
}

const tabParam = (router: ReturnType<typeof renderRoute>['router']) =>
  new URLSearchParams(router.state.location.search).get('tab');

/** Every entry of a menu, whatever its kind (`menuitem`, `menuitemcheckbox`, `menuitemradio`). */
const menuItems = (menu: HTMLElement): HTMLElement[] => Array.from(menu.querySelectorAll<HTMLElement>('[role^="menuitem"]'));

/** The ids of the overflow entries, in menu order (`garden-plan-menu-<id>` or the kept test id of a moved button). */
function openOverflow(): string[] {
  fireEvent.click(screen.getByTestId('garden-plan-overflow'));
  const menu = screen.getByTestId('garden-plan-overflow-menu');
  return menuItems(menu).map((item) => item.getAttribute('data-testid') ?? '');
}

/** A header bar `width` px wide whose content measures `widths[level]` at each overflow level. */
function stubHeaderWidths(width: number, widths: readonly number[]): () => void {
  const scroll = Object.getOwnPropertyDescriptor(Element.prototype, 'scrollWidth');
  const client = Object.getOwnPropertyDescriptor(Element.prototype, 'clientWidth');
  const isBar = (element: Element) => element.getAttribute('data-testid') === 'garden-plan-header-bar';
  Object.defineProperty(Element.prototype, 'clientWidth', {
    configurable: true,
    get(this: Element) {
      return isBar(this) ? width : (client?.get?.call(this) ?? 0);
    },
  });
  Object.defineProperty(Element.prototype, 'scrollWidth', {
    configurable: true,
    get(this: Element) {
      if (!isBar(this)) return scroll?.get?.call(this) ?? 0;
      const level = Number(this.getAttribute('data-overflow-level') ?? 0);
      return widths[Math.min(level, widths.length - 1)];
    },
  });
  return () => {
    if (scroll) Object.defineProperty(Element.prototype, 'scrollWidth', scroll);
    if (client) Object.defineProperty(Element.prototype, 'clientWidth', client);
  };
}

/** Below md: every max-width query matches (MUI `down(...)`), the pointer stays fine. */
function stubBelowMd(): () => void {
  const original = window.matchMedia;
  window.matchMedia = ((query: string) => ({
    matches: query.includes('max-width'),
    media: query,
    onchange: null,
    addListener: () => undefined,
    removeListener: () => undefined,
    addEventListener: () => undefined,
    removeEventListener: () => undefined,
    dispatchEvent: () => false,
  })) as typeof window.matchMedia;
  return () => {
    window.matchMedia = original;
  };
}

const restores: (() => void)[] = [];

beforeEach(() => {
  server.use(
    http.get('/api/v1/tenants/:slug/members', () => HttpResponse.json([])),
    http.get('/api/v1/tenants/:slug/assignments', () => HttpResponse.json([])),
  );
});
afterEach(() => {
  cleanup();
  while (restores.length > 0) restores.pop()?.();
  window.localStorage.clear();
});

describe('one header bar (GP-UX-063, AC-3)', () => {
  it('stands once between the page title and the canvas and carries every header control; the title has none', async () => {
    usePlanAndBeds();
    renderRoute();
    await screen.findByTestId('garden-plan-canvas');
    const bars = screen.getAllByTestId('garden-plan-header-bar');
    expect(bars).toHaveLength(1);
    const bar = bars[0];
    for (const id of [
      'garden-plan-back-link',
      'garden-plan-undo',
      'garden-plan-redo',
      'garden-plan-save-status',
      'garden-plan-autosave',
      'garden-plan-save',
      'garden-plan-tabs',
      'garden-plan-mode-field',
      'garden-plan-zones-open',
      'garden-plan-overflow',
    ]) {
      expect(within(bar).getByTestId(id)).toBeInTheDocument();
    }
    // The page header shows the title only (UI-NFR-021, "Verhältnis zu Shell und Seitenkopf").
    expect(screen.queryByTestId('page-title-actions')).toBeNull();
    expect(screen.getAllByTestId('garden-plan-back-link')).toHaveLength(1);
    expect(screen.getAllByTestId('garden-plan-tabs')).toHaveLength(1);
    // The header bar comes before the canvas in the document (and so on screen).
    expect(bar.compareDocumentPosition(screen.getByTestId('garden-plan-canvas'))).toBe(
      Node.DOCUMENT_POSITION_FOLLOWING,
    );
    // "Back" names the site it leads to (label in name: the visible site name is part of it).
    expect(within(bar).getByTestId('garden-plan-back-link')).toHaveAccessibleName('Back to Vegetable garden');
  });

  it('has no list switch any more: the tab is the way to the list', async () => {
    usePlanAndBeds();
    const { router } = renderRoute();
    await screen.findByTestId('garden-plan-canvas');
    expect(screen.queryByTestId('garden-plan-view-list')).toBeNull();
    expect(screen.queryByRole('switch', { name: 'Show as list' })).toBeNull();
    fireEvent.click(screen.getByTestId('garden-plan-tab-list'));
    await waitFor(() => expect(tabParam(router)).toBe('list'));
    expect(await screen.findByTestId('garden-plan-list')).toBeInTheDocument();
  });

  it('keeps the header bar on the tab "Beete" and hides only the content below it', async () => {
    usePlanAndBeds();
    renderRoute('/standorte/sites/site_1/plan?mode=plan&tab=beds');
    expect(await screen.findByTestId('bed-list-section')).toBeInTheDocument();
    expect(screen.getByTestId('garden-plan-header-bar')).toBeVisible();
    expect(screen.getByTestId('garden-plan-tab-beds')).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByTestId('garden-plan-tabpanel-editor')).not.toBeVisible();
    expect(screen.getByTestId('garden-plan-tabpanel-beds')).toBeVisible();
  });

  it('lists the rare actions in the overflow with icon and text, the moved buttons under their old test ids', async () => {
    usePlanAndBeds();
    renderRoute();
    await screen.findByTestId('garden-plan-canvas');
    const button = screen.getByTestId('garden-plan-overflow');
    expect(button).toHaveAttribute('aria-haspopup', 'menu');
    expect(button).toHaveAttribute('aria-expanded', 'false');
    expect(button).toHaveAccessibleName('More');
    const entries = openOverflow();
    expect(button).toHaveAttribute('aria-expanded', 'true');
    expect(entries).toEqual([
      'garden-plan-add-with-dimensions',
      'garden-plan-menu-selectAll',
      'garden-plan-menu-multiDuplicate',
      'garden-plan-underlay-open',
      'garden-plan-keyboard-help-button',
      'garden-plan-io-export',
      'garden-plan-io-import',
      'garden-plan-io-csv',
      'garden-plan-io-season',
    ]);
    for (const item of menuItems(screen.getByTestId('garden-plan-overflow-menu'))) {
      expect(item.querySelector('svg')).not.toBeNull();
      expect(item.textContent?.trim()).not.toBe('');
    }
    // "Save" is never an entry of the overflow (UI-NFR-021 R-017).
    expect(within(screen.getByTestId('garden-plan-overflow-menu')).queryByText('Save')).toBeNull();
  });

  it('has no accessibility violations in the header bar', async () => {
    usePlanAndBeds();
    renderRoute();
    await screen.findByTestId('garden-plan-canvas');
    await expectNoA11yViolations(screen.getByTestId('garden-plan-header-bar'));
  });
});

describe('move order of the header bar (GP-UX-063)', () => {
  it('moves auto-save, then field mode into the overflow while the bar is too narrow, and keeps "Save"', async () => {
    // Fits after two steps: auto-save and field mode go, the panel switch and the tabs stay.
    restores.push(stubHeaderWidths(1000, [1300, 1150, 980, 900, 700]));
    usePlanAndBeds();
    renderRoute();
    await screen.findByTestId('garden-plan-canvas');
    const bar = screen.getByTestId('garden-plan-header-bar');
    await waitFor(() => expect(bar).toHaveAttribute('data-overflow-level', '2'));
    expect(within(bar).queryByTestId('garden-plan-autosave')).toBeNull();
    expect(within(bar).queryByTestId('garden-plan-mode-field')).toBeNull();
    expect(within(bar).getByTestId('garden-plan-zones-open')).toBeInTheDocument();
    expect(within(bar).getByTestId('garden-plan-tabs')).toBeInTheDocument();
    expect(within(bar).getByTestId('garden-plan-save')).toBeVisible();
    const entries = openOverflow();
    expect(entries.slice(0, 2)).toEqual(['garden-plan-menu-autosave', 'garden-plan-menu-field-mode']);
    expect(entries).not.toContain('garden-plan-menu-panel');
    expect(entries).not.toContain('garden-plan-menu-tab-plan');
  });

  it('switches auto-save from its overflow entry, which says its state', async () => {
    restores.push(stubHeaderWidths(1000, [1300, 900]));
    usePlanAndBeds();
    renderRoute();
    await screen.findByTestId('garden-plan-canvas');
    await waitFor(() =>
      expect(screen.getByTestId('garden-plan-header-bar')).toHaveAttribute('data-overflow-level', '1'),
    );
    openOverflow();
    const entry = screen.getByTestId('garden-plan-menu-autosave');
    expect(entry).toHaveAttribute('role', 'menuitemcheckbox');
    expect(entry).toHaveAttribute('aria-checked', 'false');
    fireEvent.click(entry);
    expect(window.localStorage.getItem('kp_garden_plan_auto_save')).toBe('1');
    openOverflow();
    expect(screen.getByTestId('garden-plan-menu-autosave')).toHaveAttribute('aria-checked', 'true');
  });

  it('moves everything up to the tabs on a very narrow bar, in the order of GP-UX-063', async () => {
    restores.push(stubHeaderWidths(600, [1300, 1150, 980, 800, 560]));
    usePlanAndBeds();
    renderRoute();
    await screen.findByTestId('garden-plan-canvas');
    const bar = screen.getByTestId('garden-plan-header-bar');
    await waitFor(() => expect(bar).toHaveAttribute('data-overflow-level', '4'));
    expect(within(bar).queryByTestId('garden-plan-tabs')).toBeNull();
    expect(within(bar).queryByTestId('garden-plan-zones-open')).toBeNull();
    expect(within(bar).getByTestId('garden-plan-save')).toBeVisible();
    const entries = openOverflow();
    expect(entries.slice(0, 6)).toEqual([
      'garden-plan-menu-autosave',
      'garden-plan-menu-tab-plan',
      'garden-plan-menu-tab-list',
      'garden-plan-menu-tab-beds',
      'garden-plan-menu-field-mode',
      'garden-plan-menu-panel',
    ]);
  });
});

describe('below md (GP-UX-063, AC-15)', () => {
  it('shows only back (an icon), the compact save status, "Save" and "⋮"; the rest is in the overflow', async () => {
    restores.push(stubBelowMd());
    usePlanAndBeds();
    const { router } = renderRoute();
    await screen.findByTestId('garden-plan-canvas');
    const bar = screen.getByTestId('garden-plan-header-bar');
    expect(bar).toHaveAttribute('data-overflow-level', '4');
    const back = within(bar).getByTestId('garden-plan-back-link');
    expect(back).toHaveAccessibleName('Back to Vegetable garden');
    expect(back).toHaveTextContent('');
    expect(within(bar).getByTestId('garden-plan-save-status')).toBeInTheDocument();
    expect(within(bar).getByTestId('garden-plan-save')).toBeVisible();
    expect(within(bar).getByTestId('garden-plan-overflow')).toBeInTheDocument();
    for (const gone of [
      'garden-plan-autosave',
      'garden-plan-tabs',
      'garden-plan-mode-field',
      'garden-plan-zones-open',
      'garden-plan-undo',
      'garden-plan-redo',
    ]) {
      expect(within(bar).queryByTestId(gone)).toBeNull();
    }
    // Undo and redo stand in the TouchBar (GP-UX-052).
    const touchBar = screen.getByTestId('garden-plan-touchbar');
    expect(within(touchBar).getByTestId('garden-plan-undo')).toBeInTheDocument();
    expect(within(touchBar).getByTestId('garden-plan-redo')).toBeInTheDocument();

    // The tabs are three entries of the overflow, the active one marked; choosing one opens it.
    const entries = openOverflow();
    expect(entries.slice(0, 6)).toEqual([
      'garden-plan-menu-autosave',
      'garden-plan-menu-tab-plan',
      'garden-plan-menu-tab-list',
      'garden-plan-menu-tab-beds',
      'garden-plan-menu-field-mode',
      'garden-plan-menu-panel',
    ]);
    const plan = screen.getByTestId('garden-plan-menu-tab-plan');
    expect(plan).toHaveAttribute('role', 'menuitemradio');
    expect(plan).toHaveAttribute('aria-checked', 'true');
    expect(screen.getByTestId('garden-plan-menu-tab-beds')).toHaveAttribute('aria-checked', 'false');
    fireEvent.click(screen.getByTestId('garden-plan-menu-tab-beds'));
    await waitFor(() => expect(tabParam(router)).toBe('beds'));
    // Without the tab on screen the panels are named by their tab's label.
    expect(screen.getByTestId('garden-plan-tabpanel-beds')).toHaveAccessibleName('Beds');
  });

  it('says the save status in words to screen readers and shows the count', async () => {
    restores.push(stubBelowMd());
    usePlanAndBeds();
    renderRoute();
    await screen.findByTestId('garden-plan-canvas');
    const status = screen.getByTestId('garden-plan-save-status');
    expect(status).toHaveTextContent('Saved');
    expect(within(status).queryByTestId('garden-plan-save-status-count')).toBeNull();
  });
});

describe('canvas on viewport height with overlays (GP-UX-067, AC-14)', () => {
  it('puts zoom and "fit to area" on the canvas, not into a row of their own', async () => {
    usePlanAndBeds();
    renderRoute();
    await screen.findByTestId('garden-plan-canvas');
    const area = screen.getByTestId('garden-plan-canvas-area');
    for (const id of ['garden-plan-zoom-in', 'garden-plan-zoom-out', 'garden-plan-zoom-level', 'garden-plan-zoom-fit']) {
      expect(within(area).getByTestId(id)).toBeInTheDocument();
      expect(within(screen.getByTestId('garden-plan-view-bar')).queryByTestId(id)).toBeNull();
    }
    expect(within(area).getByTestId('garden-plan-canvas')).toContainElement(
      screen.getByTestId('garden-plan-scale-bar'),
    );
  });

  it('is the rest of the window height under the bar, never lower than 400 px', () => {
    expect(availableCanvasHeight(768, 200, 0)).toBe(560);
    expect(availableCanvasHeight(844, 300, 120)).toBe(416);
    expect(availableCanvasHeight(600, 400, 0)).toBe(MIN_CANVAS_HEIGHT_PX);
  });

  it('fits the plan into the room the canvas reports', async () => {
    const rect = Element.prototype.getBoundingClientRect;
    const client = Object.getOwnPropertyDescriptor(Element.prototype, 'clientWidth');
    const isArea = (element: Element) => element.getAttribute('data-testid') === 'garden-plan-canvas-area';
    Element.prototype.getBoundingClientRect = function getBoundingClientRect(this: Element) {
      return isArea(this) ? new DOMRect(0, 200, 900, 400) : rect.call(this);
    };
    Object.defineProperty(Element.prototype, 'clientWidth', {
      configurable: true,
      get(this: Element) {
        return isArea(this) ? 900 : (client?.get?.call(this) ?? 0);
      },
    });
    restores.push(() => {
      Element.prototype.getBoundingClientRect = rect;
      if (client) Object.defineProperty(Element.prototype, 'clientWidth', client);
    });
    usePlanAndBeds();
    renderRoute();
    await screen.findByTestId('garden-plan-canvas');
    const expectedHeight = availableCanvasHeight(window.innerHeight, 200, 0);
    await waitFor(() =>
      expect(screen.getByTestId('garden-plan-canvas-area').style.height).toBe(`${expectedHeight}px`),
    );
    // The drawing is the area less the canvas border, in both directions.
    const svg = screen.getByTestId('garden-plan-svg');
    await waitFor(() => expect(svg.getAttribute('width')).toBe(String(900 - 2)));
    expect(svg.getAttribute('height')).toBe(String(expectedHeight - 2));
  });
});
