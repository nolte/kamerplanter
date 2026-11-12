/**
 * The side panel's content keeps one place in the component tree (REQ-053 §17.3, GP-UX-068/069, AC-5; #2882, #2887).
 *
 * Pinned, through the real editor:
 * - A change of the panel's form across md (docked beside the canvas <-> bottom sheet) keeps the content mounted: an
 *   open "create task" dialog of a garden object with its typed name, the open window suggestion and a typed but not
 *   yet committed object property survive it (#2882, G-W10 b).
 * - The panel tabs activate manually (WAI-ARIA tabs, manual activation): the arrow keys only move the focus, Enter
 *   and Space activate. Arrowing from "Eigenschaften" past "Zonen" neither reads the zones nor loads the zone panel,
 *   and keeps the draft in "Eigenschaften"; a deliberate tab change commits a valid draft on the way out (#2887).
 */
import { act, cleanup, fireEvent, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { gardenObject } from '@/test/gardenPlanFixtures';
import { server } from '@/test/mocks/server';
import { getSite } from '@/api/endpoints/sites';
import type { PlanModel } from '../model/planModel';
import type { Geometry } from '../model/types';
import { setSelection } from '../state/gardenPlanSlice';
import { openPanelTab, setupEditor } from './editorTestKit';
import { testPlan } from './tools/toolTestKit';

vi.mock('@/api/endpoints/sites', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/api/endpoints/sites')>()),
  listLocationTypes: vi.fn(async () => []),
  getSite: vi.fn(),
}));

const ZONES = '/api/v1/t/:tenant/sites/:key/irrigation-zones';
const TASKS = '/api/v1/t/:tenant/tasks';

/** Answers MUI's breakpoint queries as a window `width` px wide would; the pointer stays fine. */
function stubWidth(width: number): () => void {
  const original = window.matchMedia;
  window.matchMedia = ((query: string) => {
    const max = /max-width:\s*([\d.]+)px/.exec(query);
    const min = /min-width:\s*([\d.]+)px/.exec(query);
    const matches =
      (max === null || width <= Number(max[1])) &&
      (min === null || width >= Number(min[1])) &&
      (max !== null || min !== null);
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
let zoneReads = 0;

beforeEach(() => {
  zoneReads = 0;
  vi.mocked(getSite).mockRejectedValue(new Error('offline'));
  server.use(
    http.get(ZONES, () => {
      zoneReads += 1;
      return HttpResponse.json([]);
    }),
    http.get(TASKS, () => HttpResponse.json([])),
  );
});

afterEach(() => {
  cleanup();
  while (restores.length > 0) restores.pop()?.();
  vi.mocked(getSite).mockReset();
  window.localStorage.clear();
});

type Editor = ReturnType<typeof setupEditor>;

/** Resize the window to `width` px: the editor renders again with the new breakpoint answers. */
function resizeTo(t: Editor, width: number): void {
  restores.push(stubWidth(width));
  act(() => t.rerender());
}

const panel = () => screen.getByTestId('garden-plan-side-panel');
const tab = (name: string) => screen.getByTestId(`garden-plan-side-panel-tab-${name}`);

function line(points: [number, number][]): Geometry {
  return { kind: 'polyline', points, width_m: 0.1 };
}

/** The test plan plus a compost heap, a bean trellis, a windowsill bed and a window in the east wall beside it. */
function objectsPlan(): PlanModel {
  const base = testPlan();
  const compost = gardenObject('go_compost', 2, 12, {
    object_type: 'compost',
    label: 'Compost heap',
    geometry: { kind: 'rect', origin: [2, 12], width_m: 1, length_m: 1, rotation_deg: 0 },
    bbox: [2, 12, 3, 13],
    props: { object_type: 'compost' },
  });
  const trellis = gardenObject('go_trellis', 6, 12, {
    object_type: 'trellis',
    label: 'Bean trellis',
    geometry: line([[6, 12], [7, 12]]),
    bbox: [6, 12, 7, 12],
    props: { object_type: 'trellis', height_m: 1.8 },
  });
  const window = gardenObject('w_east', 0, 0, {
    object_type: 'window',
    label: 'Living room',
    geometry: line([[20, 14.5], [20, 15.5]]),
    bbox: null,
    props: { object_type: 'window', sill_height_m: 0.9, glazing: 'double' },
  });
  return {
    ...base,
    locations: {
      ...base.locations,
      sill: {
        ...base.locations.solo,
        key: 'sill',
        name: 'Sill',
        geometry: { kind: 'rect', origin: [18.8, 14], width_m: 1, length_m: 2, rotation_deg: 0 },
        bbox: [18.8, 14, 19.8, 16],
        area_m2: 2,
      },
    },
    gardenObjects: { ...base.gardenObjects, go_compost: compost, go_trellis: trellis, w_east: window },
  };
}

function selectObject(key: string): Editor {
  const t = setupEditor({ plan: objectsPlan() });
  t.after(() => {
    act(() => {
      t.store.dispatch(setSelection([{ entity: 'garden_object', key }]));
    });
  });
  openPanelTab('properties');
  t.rerender();
  return t;
}

describe('the panel content survives a change of the panel form (#2882, GP-UX-069)', () => {
  it('keeps the open "create task" dialog with its typed name over docked -> sheet -> docked', async () => {
    const user = userEvent.setup();
    const t = selectObject('go_compost');
    expect(panel()).toHaveAttribute('data-variant', 'docked');
    await screen.findByTestId('garden-plan-panel-object-tasks');
    await user.click(screen.getByTestId('garden-plan-panel-object-task-add'));
    const dialog = await screen.findByTestId('care-task-dialog');
    const name = within(dialog).getByTestId('care-task-name');
    await user.type(name, 'Turn the heap');

    resizeTo(t, 390);
    expect(panel()).toHaveAttribute('data-variant', 'sheet');
    expect(screen.getByTestId('care-task-dialog')).toBe(dialog);
    expect(screen.getByTestId('care-task-name')).toHaveValue('Turn the heap');

    resizeTo(t, 1366);
    expect(panel()).toHaveAttribute('data-variant', 'docked');
    expect(screen.getByTestId('care-task-dialog')).toBe(dialog);
    expect(screen.getByTestId('care-task-name')).toHaveValue('Turn the heap');
  });

  it('keeps the open window suggestion over docked -> sheet', async () => {
    const t = setupEditor({ plan: objectsPlan() });
    t.click(19.3, 15);
    fireEvent.click(await screen.findByTestId('garden-plan-panel-window-suggest'));
    const dialog = screen.getByTestId('garden-plan-window-suggestion-dialog');

    resizeTo(t, 390);
    expect(panel()).toHaveAttribute('data-variant', 'sheet');
    expect(screen.getByTestId('garden-plan-window-suggestion-dialog')).toBe(dialog);
  });

  it('keeps a typed, not yet committed object property over docked -> sheet', async () => {
    const t = selectObject('go_trellis');
    const height = await screen.findByTestId('garden-plan-panel-trellis-height');
    // Typed, no blur, no Enter: a draft only.
    fireEvent.change(height, { target: { value: '2,4' } });
    const pending = t.state().pending.length;

    resizeTo(t, 390);
    expect(panel()).toHaveAttribute('data-variant', 'sheet');
    expect(screen.getByTestId('garden-plan-panel-trellis-height')).toBe(height);
    expect(height).toHaveValue('2,4');
    expect(t.state().pending).toHaveLength(pending);
  });
});

describe('panel tabs activate manually (#2887, GP-UX-068, AC-5)', () => {
  it('arrowing from "Eigenschaften" past "Zonen" reads no zones and keeps the draft', async () => {
    selectObject('go_trellis');
    const height = await screen.findByTestId('garden-plan-panel-trellis-height');
    // A draft the field refuses: it is never committed on the way out, so only a mounted field still holds it.
    fireEvent.change(height, { target: { value: '2,4x' } });
    act(() => tab('properties').focus());
    for (const next of ['view', 'layers', 'zones', 'properties']) {
      fireEvent.keyDown(document.activeElement!, { key: 'ArrowRight' });
      expect(tab(next)).toHaveFocus();
      expect(panel()).toHaveAttribute('data-tab', 'properties');
    }
    expect(tab('properties')).toHaveAttribute('aria-selected', 'true');
    expect(tab('zones')).toHaveAttribute('aria-selected', 'false');
    expect(screen.queryByTestId('garden-plan-zone-panel')).toBeNull();
    expect(screen.getByTestId('garden-plan-panel-trellis-height')).toBe(height);
    expect(height).toHaveValue('2,4x');
    // Give a stray request the time to arrive before counting.
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 50));
    });
    expect(zoneReads).toBe(0);
  });

  it('Enter and Space activate the focused tab; only then the zones are read', async () => {
    const user = userEvent.setup();
    selectObject('go_trellis');
    act(() => tab('properties').focus());
    fireEvent.keyDown(document.activeElement!, { key: 'End' });
    expect(tab('zones')).toHaveFocus();
    expect(panel()).toHaveAttribute('data-tab', 'properties');
    await user.keyboard('{Enter}');
    expect(panel()).toHaveAttribute('data-tab', 'zones');
    expect(tab('zones')).toHaveAttribute('aria-selected', 'true');
    expect(await screen.findByTestId('garden-plan-zone-panel')).toBeInTheDocument();
    await waitFor(() => expect(zoneReads).toBeGreaterThan(0));

    fireEvent.keyDown(document.activeElement!, { key: 'Home' });
    expect(tab('properties')).toHaveFocus();
    await user.keyboard(' ');
    expect(panel()).toHaveAttribute('data-tab', 'properties');
  });

  it('a deliberate tab change commits a valid draft on the way out (blur), nothing is lost', async () => {
    const user = userEvent.setup();
    const t = selectObject('go_trellis');
    const height = await screen.findByTestId('garden-plan-panel-trellis-height');
    await user.clear(height);
    await user.type(height, '2,4');
    await user.click(tab('view'));
    expect(panel()).toHaveAttribute('data-tab', 'view');
    act(() => t.rerender());
    expect(t.state().plan!.gardenObjects.go_trellis.props).toMatchObject({ height_m: 2.4 });
  });
});
