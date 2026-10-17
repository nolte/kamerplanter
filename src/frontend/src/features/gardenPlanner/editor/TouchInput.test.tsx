import { act, cleanup, createEvent, fireEvent, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import type { PlanModel } from '../model/planModel';
import { px, setupEditor, stubPhone } from './editorTestKit';
import { testPlan } from './tools/toolTestKit';

let restore: (() => void) | null = null;
beforeEach(() => {
  restore = stubPhone();
  vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] });
});
afterEach(() => {
  vi.useRealTimers();
  restore?.();
  cleanup();
});

type T = ReturnType<typeof setupEditor>;
type Touch = { id: number; at: number; width?: number; height?: number; primary?: boolean };

/** A touch event with a chosen `timeStamp` (the phantom filter reads it, a real clock would make tests flaky). */
function touchEvent(
  t: T,
  type: 'pointerDown' | 'pointerMove' | 'pointerUp' | 'pointerCancel',
  point: [number, number],
  { id, at, width, height, primary }: Touch,
) {
  const event = createEvent[type](t.canvas(), {
    pointerId: id,
    pointerType: 'touch',
    button: 0,
    ...px(...point),
    ...(width !== undefined ? { width } : {}),
    ...(height !== undefined ? { height } : {}),
  });
  Object.defineProperty(event, 'timeStamp', { value: at });
  if (primary) Object.defineProperty(event, 'isPrimary', { value: true });
  if (width !== undefined) Object.defineProperty(event, 'width', { value: width });
  if (height !== undefined) Object.defineProperty(event, 'height', { value: height });
  act(() => {
    fireEvent(t.canvas(), event);
  });
}

const advance = (ms: number) =>
  act(() => {
    vi.advanceTimersByTime(ms);
  });

describe('gesture table: one finger (GP-UX-040)', () => {
  it('a tap selects the bed and the sheet opens above the toolbar', () => {
    const t = setupEditor();
    touchEvent(t, 'pointerDown', [4, 4], { id: 1, at: 1000 });
    touchEvent(t, 'pointerUp', [4, 4], { id: 1, at: 1050 });
    act(() => t.rerender());
    expect(t.selected()).toEqual(['b1']);
    const sheet = screen.getByTestId('garden-plan-sheet');
    expect(within(sheet).getByTestId('garden-plan-panel')).toHaveAttribute('data-layout', 'sheet');
    expect(t.state().past).toHaveLength(0);
  });

  it('a drag from an object before the hold time pans the plan and moves nothing', () => {
    const t = setupEditor();
    touchEvent(t, 'pointerDown', [4, 4], { id: 1, at: 1000 });
    touchEvent(t, 'pointerMove', [4.5, 4.5], { id: 1, at: 1100 });
    touchEvent(t, 'pointerMove', [5, 5], { id: 1, at: 1200 });
    touchEvent(t, 'pointerUp', [5, 5], { id: 1, at: 1300 });
    expect(t.onPan).toHaveBeenCalled();
    const total = t.onPan.mock.calls.reduce(
      (sum: number[], [dx, dy]: number[]) => [sum[0] + dx, sum[1] + dy],
      [0, 0],
    );
    expect(total[0]).toBeCloseTo(40, 0); // 1 m at 40 px/m to the right
    act(() => t.rerender());
    expect(t.state().plan!.locations.b1.geometry).toMatchObject({ origin: [3, 3] });
    expect(t.state().past).toHaveLength(0);
  });

  it('after 500 ms the press is armed (ring, vibration) and the drag moves the object as ONE step', () => {
    const vibrate = vi.fn();
    Object.defineProperty(navigator, 'vibrate', { value: vibrate, configurable: true });
    const t = setupEditor();
    touchEvent(t, 'pointerDown', [4, 4], { id: 1, at: 1000 });
    act(() => t.rerender());
    expect(screen.getByTestId('garden-plan-press-ring')).toHaveAttribute('data-armed', 'false');
    advance(500);
    expect(screen.getByTestId('garden-plan-press-ring')).toHaveAttribute('data-armed', 'true');
    expect(vibrate).toHaveBeenCalled();
    touchEvent(t, 'pointerMove', [4.5, 4.5], { id: 1, at: 1600 });
    touchEvent(t, 'pointerMove', [5, 5], { id: 1, at: 1700 });
    touchEvent(t, 'pointerUp', [5, 5], { id: 1, at: 1800 });
    act(() => t.rerender());
    expect(t.state().plan!.locations.b1.geometry).toMatchObject({ origin: [4, 4] });
    expect(t.state().past).toHaveLength(1);
    expect(screen.queryByTestId('garden-plan-press-ring')).toBeNull();
    expect(t.onPan).not.toHaveBeenCalled();
  });

  it('lifting the finger early cancels the long press timer', () => {
    const t = setupEditor();
    touchEvent(t, 'pointerDown', [4, 4], { id: 1, at: 1000 });
    touchEvent(t, 'pointerUp', [4, 4], { id: 1, at: 1100 });
    advance(600);
    act(() => t.rerender());
    expect(screen.queryByTestId('garden-plan-press-ring')).toBeNull();
  });

  it('a drag on empty ground pans; a tap there clears the selection', () => {
    const t = setupEditor();
    touchEvent(t, 'pointerDown', [4, 4], { id: 1, at: 1000 });
    touchEvent(t, 'pointerUp', [4, 4], { id: 1, at: 1050 });
    act(() => t.rerender());
    touchEvent(t, 'pointerDown', [18, 18], { id: 2, at: 2000 });
    touchEvent(t, 'pointerMove', [17, 18], { id: 2, at: 2100 });
    touchEvent(t, 'pointerUp', [17, 18], { id: 2, at: 2200 });
    expect(t.onPan).toHaveBeenCalled();
    expect(t.selected()).toEqual(['b1']);
    touchEvent(t, 'pointerDown', [18, 18], { id: 3, at: 3000 });
    touchEvent(t, 'pointerUp', [18, 18], { id: 3, at: 3050 });
    expect(t.selected()).toEqual([]);
  });
});

describe('selection above the sheet (GP-UX-052)', () => {
  it('pans the view so the selected bed lies above the sheet', () => {
    const t = setupEditor();
    // Only 100 px are free above the dock; the bed is at 600..680 px.
    const rect = { top: 100, bottom: 100, left: 0, right: 0, width: 0, height: 0, x: 0, y: 100 };
    vi.spyOn(screen.getByTestId('garden-plan-dock'), 'getBoundingClientRect').mockReturnValue({
      ...rect,
      toJSON: () => ({}),
    });
    touchEvent(t, 'pointerDown', [4, 4], { id: 1, at: 1000 });
    touchEvent(t, 'pointerUp', [4, 4], { id: 1, at: 1050 });
    act(() => t.rerender());
    expect(t.onPan).toHaveBeenCalledWith(0, 16 - 600);
  });

  it('leaves the view alone when the bed is visible already', () => {
    const t = setupEditor();
    touchEvent(t, 'pointerDown', [4, 4], { id: 1, at: 1000 });
    touchEvent(t, 'pointerUp', [4, 4], { id: 1, at: 1050 });
    act(() => t.rerender());
    expect(t.onPan).not.toHaveBeenCalled();
  });
});

describe('two fingers (GP-UX-040)', () => {
  it('pan with the midpoint and zoom with the spread', () => {
    const onZoom = vi.fn<(pxPerM: number, anchorPx: [number, number]) => void>();
    const t = setupEditor({ onZoom });
    touchEvent(t, 'pointerDown', [4, 10], { id: 1, at: 1000 });
    touchEvent(t, 'pointerDown', [6, 10], { id: 2, at: 1200 });
    touchEvent(t, 'pointerMove', [3, 10], { id: 1, at: 1300 });
    touchEvent(t, 'pointerMove', [7, 10], { id: 2, at: 1300 });
    // Each finger moved on its own: 2 m -> 3 m -> 4 m apart, the factors multiply to 2. The editor
    // hands the route the new absolute zoom (the viewport of this harness stays at 40 px/m).
    const factor = onZoom.mock.calls.reduce((product, [pxPerM]) => product * (pxPerM / 40), 1);
    expect(factor).toBeCloseTo(2, 5);
    t.onPan.mockClear();
    touchEvent(t, 'pointerMove', [3, 11], { id: 1, at: 1400 });
    touchEvent(t, 'pointerMove', [7, 11], { id: 2, at: 1400 });
    // Both fingers moved up by 1 m: 40 px.
    expect(t.onPan).toHaveBeenCalled();
    const dy = t.onPan.mock.calls.reduce((sum: number, [, y]: number[]) => sum + y, 0);
    expect(dy).toBeCloseTo(-40, 0);
    touchEvent(t, 'pointerUp', [3, 11], { id: 1, at: 1500 });
    touchEvent(t, 'pointerUp', [7, 11], { id: 2, at: 1500 });
    act(() => t.rerender());
    expect(t.state().past).toHaveLength(0);
  });

  it('a second finger ends a begun move without changing the plan', () => {
    const t = setupEditor();
    touchEvent(t, 'pointerDown', [4, 4], { id: 1, at: 1000 });
    advance(500);
    touchEvent(t, 'pointerMove', [5, 5], { id: 1, at: 1600 });
    touchEvent(t, 'pointerDown', [10, 10], { id: 2, at: 1700 });
    touchEvent(t, 'pointerUp', [5, 5], { id: 1, at: 1800 });
    touchEvent(t, 'pointerUp', [10, 10], { id: 2, at: 1800 });
    act(() => t.rerender());
    expect(t.state().plan!.locations.b1.geometry).toMatchObject({ origin: [3, 3] });
    expect(t.state().past).toHaveLength(0);
  });
});

describe('phantom touch filter (GP-UX-041)', () => {
  it('ignores a palm-sized contact patch', () => {
    const t = setupEditor();
    touchEvent(t, 'pointerDown', [4, 4], { id: 1, at: 1000, width: 120, height: 120 });
    touchEvent(t, 'pointerUp', [4, 4], { id: 1, at: 1050 });
    act(() => t.rerender());
    expect(t.selected()).toEqual([]);
  });

  it('forgets a finger whose end was never reported when a primary pointer arrives', () => {
    const t = setupEditor();
    touchEvent(t, 'pointerDown', [15, 3], { id: 1, at: 1000 });
    // No pointerup for finger 1 (lost). A new primary touch 10 ms later is a fresh single touch.
    touchEvent(t, 'pointerDown', [4, 4], { id: 2, at: 1010, primary: true });
    touchEvent(t, 'pointerUp', [4, 4], { id: 2, at: 1060 });
    act(() => t.rerender());
    expect(t.selected()).toEqual(['b1']);
  });

  it('ignores a second pointer within 50 ms of the first (no pan/zoom starts)', () => {
    const onZoom = vi.fn<(pxPerM: number, anchorPx: [number, number]) => void>();
    const t = setupEditor({ onZoom });
    touchEvent(t, 'pointerDown', [4, 10], { id: 1, at: 1000 });
    touchEvent(t, 'pointerDown', [6, 10], { id: 2, at: 1030 });
    touchEvent(t, 'pointerMove', [2, 10], { id: 2, at: 1100 });
    touchEvent(t, 'pointerMove', [8, 10], { id: 2, at: 1150 });
    expect(onZoom).not.toHaveBeenCalled();
    touchEvent(t, 'pointerUp', [8, 10], { id: 2, at: 1200 });
    touchEvent(t, 'pointerUp', [4, 10], { id: 1, at: 1250 });
  });
});

function densePlan(): PlanModel {
  const plan = testPlan();
  return {
    ...plan,
    slots: {
      ...plan.slots,
      s3: {
        key: 's3',
        slot_id: 'B1_3',
        location_key: 'b1',
        plan_geometry: { origin: [3.75, 3.5] },
      },
    },
    plants: {
      ...plan.plants,
      p3: { key: 'p3', instance_id: 'BAS-1', species_key: 'sp_basil', slot_key: 's3' },
    },
  };
}

describe('dense plants (GP-UX-034)', () => {
  it('lists the plants nearby instead of guessing one', () => {
    const t = setupEditor({ plan: densePlan() });
    // Between two markers that are 10 px apart: both are under the fingertip.
    touchEvent(t, 'pointerDown', [3.625, 3.5], { id: 1, at: 1000 });
    touchEvent(t, 'pointerUp', [3.625, 3.5], { id: 1, at: 1050 });
    act(() => t.rerender());
    expect(t.selected()).toEqual([]);
    const list = screen.getByTestId('garden-plan-panel-stack');
    expect(within(list).getByText(/Plants nearby \(\d+\)/)).toBeInTheDocument();
    const item = within(list).getAllByRole('button')[0];
    expect(item).toHaveStyle({ minHeight: '64px' });
    act(() => {
      fireEvent.click(item);
    });
    act(() => t.rerender());
    expect(t.selected()).toHaveLength(1);
  });
});

describe('touch bar (GP-UX-036/037)', () => {
  it('offers the draw actions with 48 px targets and a crosshair in the middle', () => {
    const t = setupEditor();
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-tool-garden_object')));
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-shape-polygon')));
    const bar = screen.getByTestId('garden-plan-touchbar');
    for (const id of ['place', 'undo', 'finish', 'cancel']) {
      expect(within(bar).getByTestId(`garden-plan-touch-${id}`)).toHaveStyle({
        minHeight: '48px',
        minWidth: '48px',
      });
    }
    expect(screen.getByTestId('garden-plan-crosshair')).toBeInTheDocument();
    expect(screen.getByTestId('garden-plan-touch-finish')).toBeDisabled();
  });

  it('sets points at the crosshair, takes one back and finishes a polygon', () => {
    const t = setupEditor();
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-tool-garden_object')));
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-shape-polygon')));
    // The view is not panned here, so the crosshair is at model (10, 10): inside the area.
    const place = () =>
      t.after(() => fireEvent.click(screen.getByTestId('garden-plan-touch-place')));
    place();
    // A second point on the same spot is the same point: nothing is added.
    place();
    expect(screen.getByTestId('garden-plan-touch-undo')).not.toBeDisabled();
    expect(screen.getByTestId('garden-plan-draw-hint')).toHaveTextContent('1 point');
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-touch-undo')));
    expect(screen.getByTestId('garden-plan-touch-undo')).toBeDisabled();
  });

  it('sets the two corners of a rectangle with two taps, the view may pan in between', () => {
    const t = setupEditor();
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-tool-bed')));
    touchEvent(t, 'pointerDown', [15, 12], { id: 1, at: 1000 });
    touchEvent(t, 'pointerUp', [15, 12], { id: 1, at: 1050 });
    act(() => t.rerender());
    expect(t.state().past).toHaveLength(0);
    touchEvent(t, 'pointerDown', [17, 14], { id: 2, at: 2000 });
    touchEvent(t, 'pointerUp', [17, 14], { id: 2, at: 2050 });
    act(() => t.rerender());
    expect(t.state().past).toHaveLength(1);
    expect(t.state().plan!.locations[t.selected()[0]].geometry).toMatchObject({
      kind: 'rect',
      origin: [15, 12],
      width_m: 2,
      length_m: 2,
    });
  });

  it('multi-select: taps add and remove, a frame selects only what lies completely inside', () => {
    const t = setupEditor();
    const toggle = screen.getByTestId('garden-plan-touch-multi');
    t.after(() => fireEvent.click(toggle));
    expect(toggle).toHaveAttribute('aria-pressed', 'true');
    touchEvent(t, 'pointerDown', [4, 4], { id: 1, at: 1000 });
    touchEvent(t, 'pointerUp', [4, 4], { id: 1, at: 1050 });
    act(() => t.rerender());
    touchEvent(t, 'pointerDown', [15, 3], { id: 2, at: 2000 });
    touchEvent(t, 'pointerUp', [15, 3], { id: 2, at: 2050 });
    act(() => t.rerender());
    expect(t.selected()).toEqual(['b1', 'solo']);
    touchEvent(t, 'pointerDown', [4, 4], { id: 3, at: 3000 });
    touchEvent(t, 'pointerUp', [4, 4], { id: 3, at: 3050 });
    act(() => t.rerender());
    expect(t.selected()).toEqual(['solo']);
    // Deselect again, then draw a frame on empty ground around the locked and the free bed.
    touchEvent(t, 'pointerDown', [15, 3], { id: 5, at: 5000 });
    touchEvent(t, 'pointerUp', [15, 3], { id: 5, at: 5050 });
    act(() => t.rerender());
    expect(t.selected()).toEqual([]);
    touchEvent(t, 'pointerDown', [13, 10.5], { id: 4, at: 6000 });
    touchEvent(t, 'pointerMove', [17, 1.5], { id: 4, at: 6100 });
    touchEvent(t, 'pointerUp', [17, 1.5], { id: 4, at: 6200 });
    act(() => t.rerender());
    expect(t.selected()).toEqual(['solo']); // the locked bed is out (GP-UX-037)
  });

  it('closes the sheet with its button', () => {
    const t = setupEditor();
    touchEvent(t, 'pointerDown', [4, 4], { id: 1, at: 1000 });
    touchEvent(t, 'pointerUp', [4, 4], { id: 1, at: 1050 });
    act(() => t.rerender());
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-panel-close')));
    expect(t.selected()).toEqual([]);
    expect(screen.queryByTestId('garden-plan-sheet')).toBeNull();
  });

  it('has no accessibility violations (sheet, touch bar, tool bar)', async () => {
    vi.useRealTimers(); // axe schedules its own timers
    const t = setupEditor();
    touchEvent(t, 'pointerDown', [4, 4], { id: 1, at: 1000 });
    touchEvent(t, 'pointerUp', [4, 4], { id: 1, at: 1050 });
    act(() => t.rerender());
    await expectNoA11yViolations(t.view.container);
  });
});
