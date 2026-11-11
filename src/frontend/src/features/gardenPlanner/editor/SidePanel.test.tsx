/**
 * The side panel of the plan editor (REQ-053 §17.3, GP-UX-068/069, AC-5/AC-6/AC-17, WP 10.5): no reserved width while
 * collapsed, the switch with `aria-expanded`/`aria-controls`, the WAI-ARIA tabs with a roving tabindex, the state
 * rule through the editor, the form per width (docked from lg up, drawer at md, bottom sheet below md), the skip link,
 * the view settings in "Ansicht" and the layer switches with the legend in "Ebenen".
 *
 * jsdom lays nothing out: the width is set through `matchMedia` (MUI's `up`/`down` queries are answered for a chosen
 * window width), and the canvas area's size is stubbed where the fit reserve is checked.
 */
import { act, cleanup, fireEvent, screen, waitFor, within } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { server } from '@/test/mocks/server';
import { openPanelTab, setupEditor } from './editorTestKit';
import { PANEL_GAP_PX, PANEL_WIDTH_PX } from './layout';
import type { CanvasAreaSize } from './useCanvasArea';

/** Answers MUI's breakpoint queries as a window `width` px wide would; the pointer stays fine. */
function stubWidth(width: number): () => void {
  const original = window.matchMedia;
  window.matchMedia = ((query: string) => {
    const max = /max-width:\s*([\d.]+)px/.exec(query);
    const min = /min-width:\s*([\d.]+)px/.exec(query);
    const matches =
      (max === null || width <= Number(max[1])) && (min === null || width >= Number(min[1])) && (max !== null || min !== null);
    return {
      matches,
      media: query,
      onchange: null,
      addListener: () => undefined,
      removeListener: () => undefined,
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
      dispatchEvent: () => false,
    };
  }) as typeof window.matchMedia;
  return () => {
    window.matchMedia = original;
  };
}

const restores: (() => void)[] = [];

beforeEach(() => {
  server.use(http.get('/api/v1/t/:tenant/sites/:key/irrigation-zones', () => HttpResponse.json([])));
});
afterEach(() => {
  cleanup();
  while (restores.length > 0) restores.pop()?.();
  window.localStorage.clear();
});

const toggle = () => screen.getByTestId('garden-plan-panel-toggle');
const panel = () => screen.queryByTestId('garden-plan-side-panel');
const tab = (name: string) => screen.getByTestId(`garden-plan-side-panel-tab-${name}`);
const selectedTab = () => panel()?.getAttribute('data-tab') ?? null;

describe('collapsed panel (GP-UX-068, AC-5)', () => {
  it('reserves no width: the canvas row holds only the tool rail and the canvas area', () => {
    setupEditor();
    expect(panel()).toBeNull();
    expect(screen.queryByTestId('garden-plan-side-panel-dock')).toBeNull();
    const row = screen.getByTestId('garden-plan-canvas-area').parentElement!;
    expect(row.children).toHaveLength(2);
    expect(row.children[1]).toBe(screen.getByTestId('garden-plan-canvas-area'));
    // The switch says it is collapsed and names what it controls.
    expect(toggle()).toHaveAttribute('aria-expanded', 'false');
    expect(toggle()).toHaveAttribute('aria-controls', 'garden-plan-properties-panel');
    expect(toggle()).toHaveAccessibleName('Side panel');
  });

  it('opens docked beside the canvas from lg up, with the switch pointing at it', () => {
    setupEditor();
    fireEvent.click(toggle());
    expect(toggle()).toHaveAttribute('aria-expanded', 'true');
    const dock = screen.getByTestId('garden-plan-side-panel-dock');
    expect(dock).toHaveStyle({ width: `${PANEL_WIDTH_PX}px` });
    expect(screen.getByTestId('garden-plan-canvas-area').parentElement).toContainElement(dock);
    expect(panel()).toHaveAttribute('id', 'garden-plan-properties-panel');
    expect(panel()).toHaveAttribute('data-variant', 'docked');
  });

  it('has no accessibility violations collapsed and open on each tab', async () => {
    const t = setupEditor();
    await expectNoA11yViolations(t.view.container);
    for (const name of ['view', 'layers', 'properties']) {
      openPanelTab(name as 'view' | 'layers' | 'properties');
      await expectNoA11yViolations(screen.getByTestId('garden-plan-side-panel'));
    }
  });
});

describe('state rule through the editor (GP-UX-068, AC-17)', () => {
  it('a selection opens it on the properties, the deselect collapses it again', () => {
    const t = setupEditor();
    t.click(4, 4);
    expect(t.selected()).toEqual(['b1']);
    expect(selectedTab()).toBe('properties');
    expect(tab('properties')).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByTestId('garden-plan-panel-form')).toBeInTheDocument();
    t.click(18, 18);
    expect(t.selected()).toEqual([]);
    expect(panel()).toBeNull();
  });

  it('a panel the user opened stays open over selecting and deselecting; first it shows "Ansicht"', () => {
    const t = setupEditor();
    fireEvent.click(toggle());
    expect(selectedTab()).toBe('view');
    t.click(4, 4);
    expect(selectedTab()).toBe('properties');
    t.click(18, 18);
    expect(panel()).not.toBeNull();
    expect(screen.getByTestId('garden-plan-panel-empty')).toBeInTheDocument();
  });

  it('a panel the user closed stays closed until the user opens it or a new selection is made', () => {
    const t = setupEditor();
    t.click(4, 4);
    fireEvent.click(screen.getByTestId('garden-plan-panel-close'));
    expect(panel()).toBeNull();
    // The docked panel only collapses: the selection stays, the focus goes back to the switch.
    expect(t.selected()).toEqual(['b1']);
    expect(toggle()).toHaveFocus();
    act(() => t.rerender());
    expect(panel()).toBeNull();
    t.click(15, 3); // another bed: a new selection
    expect(t.selected()).toEqual(['solo']);
    expect(selectedTab()).toBe('properties');
  });

  it('opened without a selection it shows the tab used last', () => {
    setupEditor();
    openPanelTab('layers');
    fireEvent.click(toggle());
    expect(panel()).toBeNull();
    fireEvent.click(toggle());
    expect(selectedTab()).toBe('layers');
  });

  it('the overflow entry "Manage irrigation zones" opens the panel on "Zonen" (test id kept)', async () => {
    setupEditor();
    fireEvent.click(screen.getByTestId('garden-plan-overflow'));
    fireEvent.click(screen.getByTestId('garden-plan-zones-open'));
    expect(selectedTab()).toBe('zones');
    expect(await screen.findByTestId('garden-plan-zone-panel')).toBeInTheDocument();
  });
});

describe('panel tabs: WAI-ARIA "Tabs" (GP-UX-068, AC-5)', () => {
  it('has one tab stop, arrows and Home/End move and select, and every tab controls its tab panel', () => {
    setupEditor();
    fireEvent.click(toggle());
    const list = screen.getByRole('tablist', { name: 'Side panel sections' });
    const tabs = within(list).getAllByRole('tab');
    expect(tabs.map((element) => element.textContent)).toEqual(['Properties', 'View', 'Layers', 'Zones']);
    for (const element of tabs) {
      const target = document.getElementById(element.getAttribute('aria-controls') ?? '');
      expect(target).toHaveAttribute('role', 'tabpanel');
      expect(target).toHaveAttribute('aria-labelledby', element.id);
    }
    // Roving tabindex: only the selected tab ("View" on the first open) is a tab stop.
    expect(tabs.filter((element) => element.tabIndex === 0)).toEqual([tab('view')]);
    act(() => tab('view').focus());
    fireEvent.keyDown(tab('view'), { key: 'ArrowRight' });
    expect(tab('layers')).toHaveFocus();
    expect(tab('layers')).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByTestId('garden-plan-side-panel-tabpanel-layers')).toBeVisible();
    expect(screen.getByTestId('garden-plan-side-panel-tabpanel-view')).not.toBeVisible();
    fireEvent.keyDown(tab('layers'), { key: 'Home' });
    expect(tab('properties')).toHaveFocus();
    expect(tab('properties')).toHaveAttribute('aria-selected', 'true');
    fireEvent.keyDown(tab('properties'), { key: 'ArrowLeft' });
    expect(tab('zones')).toHaveFocus();
    fireEvent.keyDown(tab('zones'), { key: 'End' });
    expect(tab('zones')).toHaveAttribute('aria-selected', 'true');
    expect(within(list).getAllByRole('tab').filter((element) => element.tabIndex === 0)).toEqual([tab('zones')]);
  });

  it('keeps the arrow keys away from the plan: a selected bed does not move', () => {
    const t = setupEditor();
    t.click(4, 4);
    const before = t.state().plan!.locations.b1.geometry;
    act(() => tab('properties').focus());
    t.after(() => fireEvent.keyDown(tab('properties'), { key: 'ArrowRight' }));
    expect(t.state().plan!.locations.b1.geometry).toEqual(before);
    expect(t.state().pending).toHaveLength(0);
  });
});

describe('tab contents (GP-UX-068, AC-6)', () => {
  it('"Ansicht" carries grid step, grid, snap, unit and the compass', () => {
    setupEditor();
    openPanelTab('view');
    const view = screen.getByTestId('garden-plan-side-panel-tabpanel-view');
    for (const id of ['grid-step', 'grid-toggle', 'snap-toggle', 'unit-m', 'unit-cm', 'compass']) {
      expect(within(view).getByTestId(`garden-plan-${id}`)).toBeInTheDocument();
    }
    expect(within(view).getByTestId('garden-plan-view-bar')).toBeInTheDocument();
    // Nothing of it stands above the plan any more.
    expect(screen.getAllByTestId('garden-plan-grid-step')).toHaveLength(1);
  });

  it('"Ebenen" labels every layer switch with visible text and shows the legend, which can be hidden', () => {
    setupEditor();
    openPanelTab('layers');
    const layers = screen.getByTestId('garden-plan-side-panel-tabpanel-layers');
    const zones = within(layers).getByTestId('garden-plan-layer-zones');
    expect(zones).toHaveTextContent('Show irrigation zones');
    expect(zones).toHaveAccessibleName('Show irrigation zones');
    for (const button of within(layers).getAllByRole('button')) {
      expect(button.textContent?.trim()).not.toBe('');
    }
    expect(within(layers).queryByTestId('garden-plan-layer-legend')).toBeNull();
    fireEvent.click(zones);
    expect(zones).toHaveAttribute('aria-pressed', 'true');
    expect(within(layers).getByTestId('garden-plan-layer-legend')).toBeInTheDocument();
    fireEvent.click(within(layers).getByTestId('garden-plan-legend-toggle'));
    expect(within(layers).queryByTestId('garden-plan-layer-legend')).toBeNull();
  });
});

describe('form per width (GP-UX-069)', () => {
  it('md: a non-modal drawer over the canvas, the canvas row keeps its full width', async () => {
    restores.push(stubWidth(900));
    const t = setupEditor();
    // The tool rail stays at md.
    expect(screen.getByTestId('garden-plan-toolbar')).toHaveAttribute('data-orientation', 'vertical');
    t.click(4, 4);
    const drawer = screen.getByTestId('garden-plan-side-panel-drawer');
    expect(within(drawer).getByTestId('garden-plan-side-panel')).toHaveAttribute('data-variant', 'drawer');
    expect(screen.queryByTestId('garden-plan-side-panel-dock')).toBeNull();
    // Not in the canvas row: it lies over it and takes no width from it.
    const row = screen.getByTestId('garden-plan-canvas-area').parentElement!;
    expect(row).not.toContainElement(drawer);
    // Persistent: no dialog, no backdrop, the plan stays usable.
    expect(screen.queryByRole('dialog')).toBeNull();
    expect(document.querySelector('[aria-modal="true"]')).toBeNull();
    fireEvent.click(screen.getByTestId('garden-plan-panel-close'));
    await waitFor(() => expect(panel()).toBeNull());
    expect(t.selected()).toEqual(['b1']);
  });

  it('below md: a bottom sheet in the dock, half or full of the visible height, following visualViewport', () => {
    const viewport = Object.assign(new EventTarget(), { height: 700 });
    const original = Object.getOwnPropertyDescriptor(window, 'visualViewport');
    Object.defineProperty(window, 'visualViewport', { configurable: true, value: viewport });
    restores.push(() => {
      if (original) Object.defineProperty(window, 'visualViewport', original);
      else delete (window as { visualViewport?: unknown }).visualViewport;
    });
    restores.push(stubWidth(390));
    const t = setupEditor();
    t.click(4, 4);
    const sheet = screen.getByTestId('garden-plan-sheet');
    expect(screen.getByTestId('garden-plan-dock')).toContainElement(sheet);
    expect(within(sheet).getByTestId('garden-plan-side-panel')).toHaveAttribute('data-variant', 'sheet');
    expect(sheet).toHaveStyle({ maxHeight: `${Math.round(700 * 0.45)}px` });
    fireEvent.click(screen.getByTestId('garden-plan-sheet-size'));
    expect(screen.getByTestId('garden-plan-sheet')).toHaveStyle({ height: `${Math.round(700 * 0.9)}px` });
    expect(screen.getByTestId('garden-plan-sheet-size')).toHaveAccessibleName('Shrink to half height');
    // The on-screen keyboard shrinks the visible height: the sheet follows (GP-UX-052).
    act(() => {
      viewport.height = 400;
      viewport.dispatchEvent(new Event('resize'));
    });
    expect(screen.getByTestId('garden-plan-sheet')).toHaveStyle({ height: `${Math.round(400 * 0.9)}px` });
    // Grid step and snap are in its tab "Ansicht" (GP-UX-052).
    openPanelTab('view');
    expect(within(screen.getByTestId('garden-plan-sheet')).getByTestId('garden-plan-grid-step')).toBeInTheDocument();
    expect(within(screen.getByTestId('garden-plan-sheet')).getByTestId('garden-plan-snap-toggle')).toBeInTheDocument();
  });

  it('below md every control of the sheet is a 48 px target', () => {
    restores.push(stubWidth(390));
    const t = setupEditor();
    t.click(4, 4);
    const sheet = screen.getByTestId('garden-plan-sheet');
    const heightOf = (element: HTMLElement) => {
      const style = getComputedStyle(element);
      return Math.max(parseFloat(style.minHeight) || 0, parseFloat(style.height) || 0);
    };
    const header = [
      screen.getByTestId('garden-plan-sheet-size'),
      screen.getByTestId('garden-plan-panel-close'),
      ...within(sheet).getAllByRole('tab'),
    ];
    expect(header.filter((element) => heightOf(element) < 48).map((element) => element.textContent)).toEqual([]);
  });
});

describe('the fit while a selection docks the panel (WP 10.5)', () => {
  function stubArea(width: number): void {
    const rect = Element.prototype.getBoundingClientRect;
    const client = Object.getOwnPropertyDescriptor(Element.prototype, 'clientWidth');
    const isArea = (element: Element) => element.getAttribute('data-testid') === 'garden-plan-canvas-area';
    Element.prototype.getBoundingClientRect = function getBoundingClientRect(this: Element) {
      return isArea(this) ? new DOMRect(0, 200, width, 400) : rect.call(this);
    };
    Object.defineProperty(Element.prototype, 'clientWidth', {
      configurable: true,
      get(this: Element) {
        return isArea(this) ? width : (client?.get?.call(this) ?? 0);
      },
    });
    restores.push(() => {
      Element.prototype.getBoundingClientRect = rect;
      if (client) Object.defineProperty(Element.prototype, 'clientWidth', client);
    });
  }

  it('counts the panel a selection docked as room of the plan, but not one the user opened', () => {
    stubArea(900);
    const sizes: CanvasAreaSize[] = [];
    const onCanvasSize = vi.fn((size: CanvasAreaSize) => sizes.push(size));
    const last = () => sizes[sizes.length - 1];
    const t = setupEditor({ onCanvasSize });
    expect(last()?.fitWidthPx).toBe(900);
    t.click(4, 4);
    expect(last()).toMatchObject({ widthPx: 900, fitWidthPx: 900 + PANEL_WIDTH_PX + PANEL_GAP_PX });
    t.click(18, 18);
    expect(last()?.fitWidthPx).toBe(900);
    fireEvent.click(toggle());
    t.click(4, 4);
    expect(last()?.fitWidthPx).toBe(900);
  });
});
