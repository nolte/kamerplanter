/**
 * The garden boundary / flat outline in the editor (REQ-053 UC-01, GP-FR-019/032, GP-API-002, V-03/V-19; #2890):
 * drawn as a rect or a polygon from the overflow, edited by its handles while unlocked, locked again by a save, and
 * refused - not clipped - where it would leave a bed or an object outside. Driven through the real editor.
 */
import { act, cleanup, fireEvent, screen, within } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { normalizePlan } from '../model/planModel';
import type { Geometry, PlanOperation } from '../model/types';
import { saveGardenPlan, undo } from '../state/gardenPlanSlice';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { bed, planResponse } from '@/test/gardenPlanFixtures';
import { chooseOverflowEntry, pointer, px, setupEditor, stubPhone } from './editorTestKit';
import { testPlan } from './tools/toolTestKit';

afterEach(() => cleanup());

const BOUNDARY_ENTRY = 'garden-plan-menu-boundary';

/** A site without a plan (no boundary, nothing placed): what the indoor "Grundriss zeichnen" opens on. */
function emptyPlan() {
  return normalizePlan(planResponse({ plan: null, locations: [], garden_objects: [], slots: [], plants: [] }));
}

/** A 20 x 20 m polygon boundary, north at 30 deg, with one bed (2,2) 1.2 x 2 m inside. */
function polygonPlan() {
  return normalizePlan(
    planResponse({
      plan: {
        boundary: { kind: 'polygon', points: [[0, 0], [20, 0], [20, 20], [0, 20]], rotation_deg: 0 },
        north_angle_deg: 30,
        default_grid_m: 0.1,
        adjacency_factor: 1.5,
        plan_revision: 3,
      },
      plan_revision: 3,
      locations: [bed('b1', 2, 2)],
      garden_objects: [],
      slots: [],
      plants: [],
    }),
  );
}

type Editor = ReturnType<typeof setupEditor>;

function drag(t: Editor, path: [number, number][]): void {
  t.after(() => {
    fireEvent.pointerDown(t.canvas(), pointer(px(...path[0])));
    for (const point of path.slice(1)) fireEvent.pointerMove(t.canvas(), pointer(px(...point)));
    fireEvent.pointerUp(t.canvas(), pointer(px(...path[path.length - 1])));
  });
}

function pendingOps(t: Editor): PlanOperation[] {
  return t.state().pending.map((item) => item.op);
}

function boundaryOf(t: Editor): Geometry | null | undefined {
  return t.state().plan?.settings?.boundary;
}

function mode(): string | null {
  return screen.queryByTestId('garden-plan-boundary-mode')?.getAttribute('data-mode') ?? null;
}

describe('drawing the boundary (UC-01, GP-FR-019)', () => {
  it('draws a rect from the overflow: one set_boundary, then the new boundary is unlocked with its handles', () => {
    const t = setupEditor({ plan: emptyPlan(), connected: true });
    fireEvent.click(screen.getByTestId('garden-plan-overflow'));
    expect(screen.getByTestId(BOUNDARY_ENTRY)).toHaveTextContent('Draw garden boundary');
    t.after(() => fireEvent.click(screen.getByTestId(BOUNDARY_ENTRY)));

    expect(t.state().tool).toBe('boundary');
    expect(mode()).toBe('draw');
    // The boundary is a rect or a polygon (§9.5): no circle, no line; no top-level tool is pressed (GP-UX-001).
    expect(screen.getByTestId('garden-plan-shape-rect')).toBeInTheDocument();
    expect(screen.getByTestId('garden-plan-shape-polygon')).toBeInTheDocument();
    expect(screen.queryByTestId('garden-plan-shape-circle')).toBeNull();
    expect(screen.queryByTestId('garden-plan-shape-polyline')).toBeNull();
    for (const tool of ['select', 'pan', 'bed', 'garden_object', 'measure']) {
      expect(screen.getByTestId(`garden-plan-tool-${tool}`)).toHaveAttribute('aria-pressed', 'false');
    }

    drag(t, [
      [2, 2],
      [7, 6],
      [12, 10],
    ]);

    expect(pendingOps(t)).toEqual([
      {
        op: 'set_boundary',
        boundary: { kind: 'rect', origin: [2, 2], width_m: 10, length_m: 8, rotation_deg: 0 },
      },
    ]);
    expect(t.state().past.map((entry) => entry.label)).toEqual(['pages.gardenPlan.editor.actions.drawBoundary']);
    // Unlocked until the save (GP-FR-032): the mode now edits, the handles of the new rect are drawn.
    expect(t.state().tool).toBe('boundary');
    expect(mode()).toBe('edit');
    expect(screen.getByTestId('garden-plan-handles')).toBeInTheDocument();
    expect(screen.getByTestId('garden-plan-handle-ne')).toBeInTheDocument();
  });

  it('draws a polygon point by point and closes it with "Done"', () => {
    const t = setupEditor({ plan: emptyPlan(), connected: true });
    t.after(() => chooseOverflowEntry(BOUNDARY_ENTRY));
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-shape-polygon')));
    for (const [x, y] of [
      [2, 2],
      [14, 2],
      [14, 12],
      [2, 12],
    ] as const) {
      t.click(x, y);
    }
    expect(pendingOps(t)).toEqual([]);
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-draw-finish')));

    expect(pendingOps(t)).toEqual([
      {
        op: 'set_boundary',
        boundary: {
          kind: 'polygon',
          points: [
            [2, 2],
            [14, 2],
            [14, 12],
            [2, 12],
          ],
          rotation_deg: 0,
        },
      },
    ]);
    expect(mode()).toBe('edit');
  });

  it('refuses a boundary that would leave a placed bed outside (V-03/V-19): drawn red, a notice, nothing pending', () => {
    const plan = normalizePlan(
      planResponse({ plan: null, locations: [bed('far', 14, 2)], garden_objects: [], slots: [], plants: [] }),
    );
    const t = setupEditor({ plan, connected: true });
    t.after(() => chooseOverflowEntry(BOUNDARY_ENTRY));
    t.after(() => {
      fireEvent.pointerDown(t.canvas(), pointer(px(1, 1)));
      fireEvent.pointerMove(t.canvas(), pointer(px(10, 10)));
    });
    expect(screen.getByTestId('garden-plan-ghost')).toHaveAttribute('data-invalid', 'true');
    t.after(() => fireEvent.pointerUp(t.canvas(), pointer(px(10, 10))));

    expect(pendingOps(t)).toEqual([]);
    expect(boundaryOf(t)).toBeUndefined();
    expect(screen.getByTestId('garden-plan-notice')).toHaveTextContent(
      'The boundary would leave beds or objects outside and was not applied.',
    );
    expect(mode()).toBe('draw');
  });

  it('undoes the unsaved boundary in one step and is back to drawing', () => {
    const t = setupEditor({ plan: emptyPlan(), connected: true });
    t.after(() => chooseOverflowEntry(BOUNDARY_ENTRY));
    drag(t, [
      [2, 2],
      [12, 10],
    ]);
    expect(mode()).toBe('edit');
    t.after(() => t.store.dispatch(undo()));
    expect(pendingOps(t)).toEqual([]);
    expect(boundaryOf(t) ?? null).toBeNull();
    expect(mode()).toBe('draw');
  });

  it('is reachable below md: the overflow entry, and "Set point" in the TouchBar while drawing', () => {
    const restore = stubPhone();
    try {
      const t = setupEditor({ plan: emptyPlan(), connected: true });
      t.after(() => chooseOverflowEntry(BOUNDARY_ENTRY));
      const touchBar = screen.getByTestId('garden-plan-touchbar');
      expect(within(touchBar).getByTestId('garden-plan-touch-place')).toBeInTheDocument();
      expect(mode()).toBe('draw');
    } finally {
      restore();
    }
  });
});

describe('editing the boundary (GP-FR-022/023)', () => {
  it('moves a polygon point by its handle: one set_boundary that keeps the north angle', () => {
    const t = setupEditor({ plan: polygonPlan(), connected: true });
    fireEvent.click(screen.getByTestId('garden-plan-overflow'));
    expect(screen.getByTestId(BOUNDARY_ENTRY)).toHaveTextContent('Unlock and edit garden boundary');
    t.after(() => fireEvent.click(screen.getByTestId(BOUNDARY_ENTRY)));
    expect(mode()).toBe('edit');
    expect(screen.getByTestId('garden-plan-handle-v2')).toBeInTheDocument();

    drag(t, [
      [20, 20],
      [19, 18.5],
      [18, 17],
    ]);

    expect(pendingOps(t)).toEqual([
      {
        op: 'set_boundary',
        boundary: {
          kind: 'polygon',
          points: [
            [0, 0],
            [20, 0],
            [18, 17],
            [0, 20],
          ],
          rotation_deg: 0,
        },
        north_angle_deg: 30,
      },
    ]);
    expect(t.state().plan?.settings?.north_angle_deg).toBe(30);
    expect(t.state().past.map((entry) => entry.label)).toEqual(['pages.gardenPlan.editor.actions.editBoundary']);
  });

  it('deletes a picked polygon point with "Delete point"', () => {
    const t = setupEditor({ plan: polygonPlan(), connected: true });
    t.after(() => chooseOverflowEntry(BOUNDARY_ENTRY));
    t.click(20, 20); // a click on the handle picks the point
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-vertex-delete')));
    expect(pendingOps(t)).toEqual([
      expect.objectContaining({
        op: 'set_boundary',
        boundary: expect.objectContaining({
          points: [
            [0, 0],
            [20, 0],
            [0, 20],
          ],
        }),
      }),
    ]);
  });

  it('refuses an edit that would leave a bed outside: red ghost, the V-19 notice, the boundary unchanged', () => {
    const t = setupEditor({ connected: true }); // rect boundary 20 x 20 with the area (2..12) and beds inside
    const before = boundaryOf(t);
    t.after(() => chooseOverflowEntry(BOUNDARY_ENTRY));
    t.after(() => {
      fireEvent.pointerDown(t.canvas(), pointer(px(0, 10)));
      fireEvent.pointerMove(t.canvas(), pointer(px(8, 10)));
      fireEvent.pointerMove(t.canvas(), pointer(px(15, 10)));
    });
    expect(screen.getByTestId('garden-plan-ghost')).toHaveAttribute('data-invalid', 'true');
    t.after(() => fireEvent.pointerUp(t.canvas(), pointer(px(15, 10))));

    expect(pendingOps(t)).toEqual([]);
    expect(boundaryOf(t)).toEqual(before);
    expect(screen.getByTestId('garden-plan-notice')).toHaveTextContent('would leave beds or objects outside');
  });

  it('a press off the handles pans the view instead of selecting or moving anything', () => {
    const t = setupEditor({ connected: true });
    t.after(() => chooseOverflowEntry(BOUNDARY_ENTRY));
    drag(t, [
      [4, 4],
      [5, 5],
      [6, 6],
    ]); // starts on bed b1
    expect(t.onPan).toHaveBeenCalled();
    expect(pendingOps(t)).toEqual([]);
    expect(t.selected()).toEqual([]);
  });
});

describe('the boundary is locked (GP-FR-032)', () => {
  it('without the mode it has no handles and a drag on its edge changes nothing', () => {
    const t = setupEditor({ connected: true });
    expect(screen.queryByTestId('garden-plan-handles')).toBeNull();
    drag(t, [
      [20, 10],
      [21, 10],
      [22, 10],
    ]);
    expect(pendingOps(t)).toEqual([]);
    expect(screen.queryByTestId('garden-plan-handles')).toBeNull();
    expect(mode()).toBeNull();
  });

  it('"Lock" ends the mode; the next change takes the unlock again', () => {
    const t = setupEditor({ connected: true });
    t.after(() => chooseOverflowEntry(BOUNDARY_ENTRY));
    expect(screen.getByTestId('garden-plan-handles')).toBeInTheDocument();
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-boundary-done')));
    expect(t.state().tool).toBe('select');
    expect(mode()).toBeNull();
    expect(screen.queryByTestId('garden-plan-handles')).toBeNull();
    fireEvent.click(screen.getByTestId('garden-plan-overflow'));
    expect(screen.getByTestId(BOUNDARY_ENTRY)).toHaveTextContent('Unlock and edit garden boundary');
  });

  it('a save locks the boundary again', () => {
    const t = setupEditor({ connected: true });
    t.after(() => chooseOverflowEntry(BOUNDARY_ENTRY));
    drag(t, [
      [20, 10],
      [21, 10],
      [22, 10],
    ]); // the "e" edge: 22 m wide
    expect(pendingOps(t)).toHaveLength(1);
    expect(mode()).toBe('edit');
    t.after(() => {
      t.store.dispatch(saveGardenPlan.pending('save-1', undefined));
      t.store.dispatch(
        saveGardenPlan.fulfilled(
          { response: { plan_revision: 8, key_map: {}, updated: [], deleted: [], derived: {} } },
          'save-1',
          undefined,
        ),
      );
    });
    expect(t.state().pending).toEqual([]);
    expect(t.state().tool).toBe('select');
    expect(mode()).toBeNull();
    expect(boundaryOf(t)).toMatchObject({ kind: 'rect', width_m: 22 });
  });

  it('a refused save names the boundary finding in the save message (save error mapping)', () => {
    const t = setupEditor({ connected: true });
    t.after(() => chooseOverflowEntry(BOUNDARY_ENTRY));
    drag(t, [
      [20, 10],
      [21, 10],
    ]);
    act(() => {
      t.store.dispatch(saveGardenPlan.pending('save-2', undefined));
      t.store.dispatch(
        saveGardenPlan.rejected(null, 'save-2', undefined, {
          kind: 'rejected',
          status: 422,
          code: 'validation_error',
          findings: [{ opIndex: 0, field: 'boundary', code: 'boundary.shrinks_below_objects' }],
        }),
      );
    });
    t.rerender();
    expect(screen.getByText(/Garden boundary.*would leave beds or objects outside/)).toBeInTheDocument();
    // A refused save is no save: the boundary stays unlocked for the fix.
    expect(mode()).toBe('edit');
  });
});

describe('accessibility', () => {
  it('has no violations with the boundary unlocked (notice, its action, the handles)', async () => {
    const t = setupEditor({ connected: true });
    t.after(() => chooseOverflowEntry(BOUNDARY_ENTRY));
    expect(mode()).toBe('edit');
    await expectNoA11yViolations(t.view.container);
  });
});

describe('the rail stays GP-UX-001 (#2868)', () => {
  // GP-UX-071 (#2913) added "Messen" as the fifth tool; the boundary still is no tool of the rail.
  it('keeps exactly the top-level tools of GP-UX-001; the boundary is an overflow entry, not a tool', () => {
    setupEditor({ plan: testPlan() });
    const tools = screen.getByRole('group', { name: 'Tool' });
    const ids = within(tools)
      .getAllByRole('button')
      .map((button) => button.getAttribute('data-testid'))
      .filter((id): id is string => id !== null && !id.endsWith('-menu'));
    expect(ids).toEqual([
      'garden-plan-tool-select',
      'garden-plan-tool-pan',
      'garden-plan-tool-area',
      'garden-plan-tool-bed',
      'garden-plan-tool-garden_object',
      'garden-plan-tool-measure',
    ]);
  });
});
