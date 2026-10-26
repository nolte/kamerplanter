import { act, cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { configureStore } from '@reduxjs/toolkit';
import { Provider } from 'react-redux';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ThemeContextProvider } from '@/theme';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { HeadlessPlanRenderer } from '../renderer/HeadlessPlanRenderer';
import type { Viewport } from '../renderer';
import { gardenPlanSlice, loadGardenPlan, type GardenPlanState } from '../state/gardenPlanSlice';
import type { PlanModel } from '../model/planModel';
import { testPlan } from './tools/toolTestKit';
import { GardenPlanEditor } from './GardenPlanEditor';
import { TEST_LABELS } from '../renderer/rendererTestKit';

/** 40 px per metre, model (0, 20) at the top-left: the area is 400 px wide (all handles), a 2 m bed 80 px. */
const VIEWPORT: Viewport = { originM: [0, 20], pxPerM: 40, widthPx: 800, heightPx: 800 };
const px = (x: number, y: number): { clientX: number; clientY: number } => ({
  clientX: x * 40,
  clientY: (20 - y) * 40,
});
const pointer = (extra: Record<string, unknown> = {}) => ({
  pointerId: 1,
  pointerType: 'mouse',
  button: 0,
  ...extra,
});

function setup(plan: PlanModel = testPlan(), onPan = vi.fn()) {
  const store = configureStore({ reducer: { gardenPlan: gardenPlanSlice.reducer } });
  store.dispatch(loadGardenPlan.pending('r1', 'site_1'));
  store.dispatch(loadGardenPlan.fulfilled(plan, 'r1', 'site_1'));
  const renderer = new HeadlessPlanRenderer();
  const view = render(
    <Provider store={store}>
      <ThemeContextProvider>
        <GardenPlanEditor
          plan={plan}
          viewport={VIEWPORT}
          renderer={renderer}
          labels={TEST_LABELS}
          onPan={onPan}
        />
      </ThemeContextProvider>
    </Provider>,
  );
  const state = (): GardenPlanState => store.getState().gardenPlan;
  const canvas = () => screen.getByTestId('garden-plan-canvas');

  // The editor draws from the store; re-render it with the plan the store holds now.
  const rerender = () =>
    view.rerender(
      <Provider store={store}>
        <ThemeContextProvider>
          <GardenPlanEditor
            plan={state().plan!}
            viewport={VIEWPORT}
            renderer={renderer}
            labels={TEST_LABELS}
            onPan={onPan}
          />
        </ThemeContextProvider>
      </Provider>,
    );
  const click = (x: number, y: number, mods: Record<string, unknown> = {}) => {
    fireEvent.pointerDown(canvas(), pointer({ ...px(x, y), ...mods }));
    fireEvent.pointerUp(canvas(), pointer({ ...px(x, y), ...mods }));
    rerender();
  };
  const drag = (path: [number, number][], mods: Record<string, unknown> = {}) => {
    fireEvent.pointerDown(canvas(), pointer({ ...px(...path[0]), ...mods }));
    for (const point of path.slice(1))
      fireEvent.pointerMove(canvas(), pointer({ ...px(...point), ...mods }));
    fireEvent.pointerUp(canvas(), pointer({ ...px(...path[path.length - 1]), ...mods }));
    rerender();
  };
  const key = (name: string, mods: Record<string, unknown> = {}) => {
    fireEvent.keyDown(canvas(), { key: name, ...mods });
    rerender();
  };
  const selected = () => state().selection.map((ref) => ref.key);
  return { store, state, canvas, click, drag, key, selected, rerender, view, onPan, renderer };
}

afterEach(() => cleanup());

describe('toolbar', () => {
  it('offers the tools with 44 px targets, named, and marks the active one', () => {
    setup();
    const toolbar = screen.getByRole('toolbar', { name: 'Garden plan tools' });
    for (const tool of ['select', 'pan', 'bed', 'garden_object']) {
      const button = within(toolbar).getByTestId(`garden-plan-tool-${tool}`);
      expect(button).toHaveStyle({ minHeight: '44px', minWidth: '44px' });
    }
    expect(screen.getByTestId('garden-plan-tool-select')).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByRole('button', { name: 'Draw bed' })).toBeInTheDocument();
  });

  it('switches the tool and shows the shape choices of a draw tool only', () => {
    const { state } = setup();
    expect(screen.queryByTestId('garden-plan-shape-rect')).toBeNull();
    fireEvent.click(screen.getByTestId('garden-plan-tool-bed'));
    expect(state().tool).toBe('bed');
    expect(screen.getByTestId('garden-plan-shape-polygon')).toBeInTheDocument();
    // A bed is an area: only garden objects may be lines.
    expect(screen.queryByTestId('garden-plan-shape-polyline')).toBeNull();
    fireEvent.click(screen.getByTestId('garden-plan-tool-garden_object'));
    expect(screen.getByTestId('garden-plan-shape-polyline')).toBeInTheDocument();
  });

  it('has no accessibility violations (toolbar, plan region, delete dialog)', async () => {
    const view = setup();
    await expectNoA11yViolations(view.view.container);
    view.click(4, 4);
    fireEvent.click(screen.getByTestId('garden-plan-delete-button'));
    expect(await screen.findByTestId('confirm-dialog')).toBeInTheDocument();
    await expectNoA11yViolations(document.body);
  });
});

describe('selection (GP-FR-020, GP-FR-156)', () => {
  it('click selects, Shift extends, a click on empty ground clears', () => {
    const t = setup();
    t.click(4, 4);
    expect(t.selected()).toEqual(['b1']);
    t.click(15, 3, { shiftKey: true });
    expect(t.selected()).toEqual(['b1', 'solo']);
    t.click(19, 19);
    expect(t.selected()).toEqual([]);
  });

  it('a repeated click walks down the stack under the pointer (GP-UX-033) and the state keeps it', () => {
    const t = setup();
    t.click(4, 4);
    expect(t.selected()).toEqual(['b1']);
    expect(t.state().stack).toMatchObject({ keys: ['b1', 'area'], index: 0 });
    t.click(4, 4);
    expect(t.selected()).toEqual(['area']);
    t.click(4, 4);
    expect(t.selected()).toEqual(['b1']);
  });

  it('Alt+click picks the object below the selected one', () => {
    const t = setup();
    t.click(4, 4);
    t.click(4, 4, { altKey: true });
    expect(t.selected()).toEqual(['area']);
  });

  it('a frame selects what it fully contains; Ctrl+A everything but locked objects', () => {
    const t = setup();
    t.drag([
      [13, 1],
      [17, 5],
      [17, 11],
    ]);
    expect(t.selected()).toEqual(['solo']);
    expect(screen.queryByTestId('garden-plan-marquee')).toBeNull();
    t.key('a', { ctrlKey: true });
    expect(t.selected().sort()).toEqual(['area', 'b1', 'b2', 'solo', 't1']);
    expect(t.selected()).not.toContain('lock');
  });

  it('Escape clears the selection', () => {
    const t = setup();
    t.click(4, 4);
    t.key('Escape');
    expect(t.selected()).toEqual([]);
  });

  it('shows the frame while it is dragged', () => {
    const t = setup();
    fireEvent.pointerDown(t.canvas(), pointer(px(13, 1)));
    fireEvent.pointerMove(t.canvas(), pointer(px(17, 5)));
    expect(screen.getByTestId('garden-plan-marquee')).toBeInTheDocument();
    fireEvent.keyDown(t.canvas(), { key: 'Escape' });
    expect(screen.queryByTestId('garden-plan-marquee')).toBeNull();
  });
});

describe('moving is one undo step (GP-FR-155, GP-FR-151)', () => {
  it('a drag is one history entry and one operation; undo takes it back', () => {
    const t = setup();
    t.drag([
      [4, 4],
      [4.5, 4.5],
      [5, 5],
    ]);
    expect(t.state().past).toHaveLength(1);
    expect(t.state().pending).toHaveLength(1);
    expect(t.state().plan!.locations.b1.geometry).toMatchObject({ origin: [4, 4] });
    act(() => {
      t.store.dispatch({ type: 'gardenPlan/undo' });
    });
    expect(t.state().plan!.locations.b1.geometry).toMatchObject({ origin: [3, 3] });
    expect(t.state().pending).toHaveLength(0);
  });

  it('moving an area carries its children: one operation each, still one undo step', () => {
    const t = setup();
    t.drag([
      [11, 11],
      [12, 11],
      [13, 11],
    ]);
    expect(t.state().past).toHaveLength(1);
    expect(t.state().pending).toHaveLength(4);
    const { locations, gardenObjects } = t.state().plan!;
    expect(locations.area.geometry).toMatchObject({ origin: [4, 2] });
    expect(locations.b1.geometry).toMatchObject({ origin: [5, 3] });
    expect(locations.b2.geometry).toMatchObject({ origin: [8, 3] });
    expect(gardenObjects.t1.geometry).toMatchObject({ origin: [11, 9] });
    act(() => {
      t.store.dispatch({ type: 'gardenPlan/undo' });
    });
    expect(t.state().plan!.locations.b1.geometry).toMatchObject({ origin: [3, 3] });
    expect(t.state().plan!.gardenObjects.t1.geometry).toMatchObject({ origin: [9, 9] });
  });

  it('a locked bed does not move and the user is told why', () => {
    const t = setup();
    t.drag([
      [15, 9],
      [15, 10],
      [15, 11],
    ]);
    expect(t.state().past).toHaveLength(0);
    expect(t.state().plan!.locations.lock.geometry).toMatchObject({ origin: [14, 8] });
    expect(screen.getByTestId('garden-plan-notice')).toHaveTextContent(
      /Locked objects cannot be changed/,
    );
  });

  it('a move that leaves the area snaps back with a message, and nothing is queued', () => {
    const t = setup();
    t.drag([
      [4, 4],
      [8, 4],
      [12, 4],
    ]);
    expect(t.state().past).toHaveLength(0);
    expect(screen.getByTestId('garden-plan-notice')).toHaveTextContent(/sticks out of its area/);
  });

  it('Escape in the middle of a drag leaves everything as it was', () => {
    const t = setup();
    fireEvent.pointerDown(t.canvas(), pointer(px(4, 4)));
    fireEvent.pointerMove(t.canvas(), pointer(px(5, 5)));
    expect(screen.getAllByTestId('garden-plan-ghost').length).toBeGreaterThan(0);
    fireEvent.keyDown(t.canvas(), { key: 'Escape' });
    fireEvent.pointerUp(t.canvas(), pointer(px(5, 5)));
    t.rerender();
    expect(t.state().past).toHaveLength(0);
    expect(screen.queryByTestId('garden-plan-ghost')).toBeNull();
  });

  it('previews the dragged object through the renderer and clears it on release', () => {
    const t = setup();
    fireEvent.pointerDown(t.canvas(), pointer(px(4, 4)));
    fireEvent.pointerMove(t.canvas(), pointer(px(5, 4)));
    expect(t.renderer.dragPreview).toMatchObject({ key: 'b1', dxPx: 40 });
    fireEvent.pointerUp(t.canvas(), pointer(px(5, 4)));
    expect(t.renderer.dragPreview).toBeNull();
  });

  it('ignores a second pointer while one gesture is running', () => {
    const t = setup();
    fireEvent.pointerDown(t.canvas(), pointer(px(4, 4)));
    fireEvent.pointerDown(t.canvas(), pointer({ ...px(15, 3), pointerId: 2 }));
    fireEvent.pointerMove(t.canvas(), pointer({ ...px(15, 5), pointerId: 2 }));
    fireEvent.pointerUp(t.canvas(), pointer({ ...px(15, 5), pointerId: 2 }));
    expect(t.state().past).toHaveLength(0);
    fireEvent.pointerUp(t.canvas(), pointer(px(4, 4)));
  });

  it('works the same for pen input (a finger needs the long press, see the touch tests)', () => {
    const t = setup();
    t.drag(
      [
        [4, 4],
        [4.5, 4.5],
        [5, 5],
      ],
      { pointerType: 'pen' },
    );
    expect(t.state().past).toHaveLength(1);
  });
});

describe('handles (GP-FR-022, GP-UX-048)', () => {
  it('shows eight handles and the rotate handle on a large selected rect, and resizes by dragging one', () => {
    const t = setup();
    t.click(11, 11); // the area only
    expect(t.selected()).toEqual(['area']);
    for (const id of ['nw', 'n', 'ne', 'e', 'se', 's', 'sw', 'w', 'rotate']) {
      expect(screen.getByTestId(`garden-plan-handle-${id}`)).toBeInTheDocument();
    }
    t.drag([
      [12, 7],
      [13, 7],
      [14, 7],
    ]);
    expect(t.state().plan!.locations.area.geometry).toMatchObject({ width_m: 12, length_m: 10 });
    expect(t.state().past).toHaveLength(1);
  });

  it('shows no handles for a locked object and only a hint for one too small on screen', () => {
    const t = setup();
    t.click(15, 9);
    expect(t.selected()).toEqual(['lock']);
    expect(screen.queryByTestId('garden-plan-handles')).toBeNull();
    t.click(4, 4); // b1 is 80 px
    expect(screen.getByTestId('garden-plan-too-small')).toBeInTheDocument();
  });

  it('refuses a resize that strands the children', () => {
    const t = setup();
    t.click(11, 11);
    t.drag([
      [12, 7],
      [8, 7],
      [5, 7],
    ]);
    expect(t.state().past).toHaveLength(0);
    expect(screen.getByTestId('garden-plan-notice')).toBeInTheDocument();
  });
});

describe('drawing (GP-FR-001)', () => {
  it('draws a bed with the rect tool: one operation, selected afterwards, back to the select tool', () => {
    const t = setup();
    fireEvent.click(screen.getByTestId('garden-plan-tool-bed'));
    t.drag([
      [16, 14],
      [17, 15],
      [18.5, 16],
    ]);
    expect(t.state().past).toHaveLength(1);
    expect(t.state().pending).toHaveLength(1);
    const [created] = Object.values(t.state().plan!.locations).filter((l) => l.name === 'Bed 6');
    expect(created.geometry).toMatchObject({
      kind: 'rect',
      origin: [16, 14],
      width_m: 2.5,
      length_m: 2,
    });
    expect(t.selected()).toEqual([created.key]);
    expect(t.state().tool).toBe('select');
  });

  it('draws a polygon point by point, finishes with Enter and cancels with Escape', () => {
    const t = setup();
    fireEvent.click(screen.getByTestId('garden-plan-tool-bed'));
    fireEvent.click(screen.getByTestId('garden-plan-shape-polygon'));
    t.click(16, 14);
    t.click(19, 14);
    expect(screen.getByTestId('garden-plan-draw-finish')).toBeDisabled();
    t.click(19, 17);
    expect(screen.getByTestId('garden-plan-draw-finish')).toBeEnabled();
    expect(screen.getAllByTestId('garden-plan-ghost')).toHaveLength(1);
    t.key('Escape');
    expect(t.state().past).toHaveLength(0);
    expect(screen.queryByTestId('garden-plan-ghost')).toBeNull();

    t.click(16, 14);
    t.click(19, 14);
    t.click(19, 17);
    t.key('Enter');
    expect(t.state().past).toHaveLength(1);
    expect(Object.values(t.state().plan!.locations)).toHaveLength(6);
  });

  it('draws a line as a garden object with the finish button', () => {
    const t = setup();
    fireEvent.click(screen.getByTestId('garden-plan-tool-garden_object'));
    fireEvent.click(screen.getByTestId('garden-plan-shape-polyline'));
    t.click(16, 14);
    t.click(19, 14);
    fireEvent.click(screen.getByTestId('garden-plan-draw-finish'));
    const objects = Object.values(t.state().plan!.gardenObjects);
    expect(objects).toHaveLength(2);
    expect(objects.find((o) => o.geometry.kind === 'polyline')).toBeDefined();
  });

  it('refuses a bed that sticks out of the garden: nothing created, a red outline while dragging', () => {
    const t = setup();
    fireEvent.click(screen.getByTestId('garden-plan-tool-bed'));
    fireEvent.pointerDown(t.canvas(), pointer(px(19, 14)));
    fireEvent.pointerMove(t.canvas(), pointer(px(22, 16)));
    expect(screen.getByTestId('garden-plan-ghost')).toHaveAttribute('data-invalid', 'true');
    fireEvent.pointerUp(t.canvas(), pointer(px(22, 16)));
    t.rerender();
    expect(t.state().past).toHaveLength(0);
    expect(screen.getByTestId('garden-plan-notice')).toBeInTheDocument();
  });
});

describe('drawing hints', () => {
  it('tells what to do next while drawing a polygon and says nothing outside the draw tools', () => {
    const t = setup();
    expect(screen.queryByTestId('garden-plan-draw-hint')).toBeNull();
    fireEvent.click(screen.getByTestId('garden-plan-tool-bed'));
    fireEvent.click(screen.getByTestId('garden-plan-shape-polygon'));
    expect(screen.getByTestId('garden-plan-draw-hint')).toHaveTextContent(/corner points/);
    t.click(16, 14);
    expect(screen.getByTestId('garden-plan-draw-hint')).toHaveTextContent(
      /1 point placed.*Backspace/,
    );
  });
});

describe('pan (GP-FR-010)', () => {
  it('reports the drag distance to the page and changes nothing in the plan', () => {
    const t = setup();
    fireEvent.click(screen.getByTestId('garden-plan-tool-pan'));
    t.drag([
      [4, 4],
      [5, 4],
      [5, 3],
    ]);
    expect(t.onPan).toHaveBeenNthCalledWith(1, 40, 0);
    expect(t.onPan).toHaveBeenNthCalledWith(2, 0, 40);
    expect(t.state().past).toHaveLength(0);
    expect(t.state().selection).toEqual([]);
  });

  it('the middle button pans with any tool', () => {
    const t = setup();
    t.drag(
      [
        [4, 4],
        [5, 4],
      ],
      { button: 1 },
    );
    expect(t.onPan).toHaveBeenCalledWith(40, 0);
    expect(t.state().selection).toEqual([]);
  });
});

describe('polygon points (GP-FR-023)', () => {
  it('picks a point on click, deletes it with Del or the button, never below three', () => {
    const t = setup();
    fireEvent.click(screen.getByTestId('garden-plan-tool-garden_object'));
    fireEvent.click(screen.getByTestId('garden-plan-shape-polygon'));
    for (const [x, y] of [
      [15, 12],
      [19, 12],
      [19, 16],
      [15, 16],
    ])
      t.click(x, y);
    t.key('Enter');
    const key = t.selected()[0];
    expect(t.state().plan!.gardenObjects[key].geometry).toMatchObject({ kind: 'polygon' });

    // The polygon is 160 px wide, so its vertex handles are shown. Pick the corner at (19, 16).
    t.click(19, 16);
    expect(screen.getByTestId('garden-plan-vertex-delete')).toBeInTheDocument();
    t.key('Delete');
    const triangle = t.state().plan!.gardenObjects[key].geometry as { points: unknown[] };
    expect(triangle.points).toHaveLength(3);
    expect(t.state().past).toHaveLength(2);

    // A triangle keeps its three points.
    t.click(19, 12);
    fireEvent.click(screen.getByTestId('garden-plan-vertex-delete'));
    expect(
      (t.state().plan!.gardenObjects[key].geometry as { points: unknown[] }).points,
    ).toHaveLength(3);
    expect(screen.getByTestId('garden-plan-notice')).toHaveTextContent(/at least three points/);
  });
});

describe('delete protection (GP-FR-153, GP-UX-043)', () => {
  it('names the children, slots, plants and tasks an area takes along; Cancel has the focus', async () => {
    const t = setup();
    t.click(11, 11);
    t.key('Delete');
    const dialog = await screen.findByTestId('confirm-dialog');
    expect(within(dialog).getByText('Delete "Area"?')).toBeInTheDocument();
    const text = dialog.textContent ?? '';
    expect(text).toContain('2 contained beds');
    expect(text).toContain('1 garden object');
    expect(text).toContain('2 planting positions');
    expect(text).toContain('1 plant');
    expect(text).toContain('3 open tasks');
    expect(text).toContain('cannot be undone');
    expect(within(dialog).getByTestId('confirm-dialog-cancel')).toHaveFocus();
    // Nothing happened yet.
    expect(t.state().past).toHaveLength(0);
  });

  it('Cancel keeps the plan; Delete removes the area and its children in one undo step', async () => {
    const t = setup();
    t.click(11, 11);
    t.key('Delete');
    fireEvent.click(await screen.findByTestId('confirm-dialog-cancel'));
    expect(Object.keys(t.state().plan!.locations)).toHaveLength(5);

    t.key('Delete');
    fireEvent.click(await screen.findByTestId('confirm-dialog-confirm'));
    t.rerender();
    expect(Object.keys(t.state().plan!.locations).sort()).toEqual(['lock', 'solo']);
    expect(Object.keys(t.state().plan!.gardenObjects)).toHaveLength(0);
    expect(t.state().past).toHaveLength(1);
    expect(t.state().pending).toHaveLength(1);
    expect(t.selected()).toEqual([]);
  });

  it('an empty bed says nothing else is affected and the toolbar button asks the same way', async () => {
    const t = setup();
    t.click(15, 3);
    fireEvent.click(screen.getByTestId('garden-plan-delete-button'));
    const dialog = await screen.findByTestId('confirm-dialog');
    expect(dialog.textContent).toContain('no further beds, objects, plants or tasks');
    expect(dialog.textContent).not.toContain('cannot be undone');
  });

  it('a locked object cannot be deleted; the user is told to unlock it', () => {
    const t = setup();
    t.click(15, 9);
    t.key('Delete');
    expect(screen.queryByTestId('confirm-dialog')).toBeNull();
    expect(screen.getByTestId('garden-plan-notice')).toHaveTextContent(/Unlock them first/);
  });

  it('asks about several objects at once with their number', async () => {
    const t = setup();
    t.key('a', { ctrlKey: true });
    t.key('Delete');
    const dialog = await screen.findByTestId('confirm-dialog');
    // The area is the root; b1/b2/t1 are its children.
    expect(dialog.textContent).toMatch(/Delete 2 objects\?/);
  });
});
