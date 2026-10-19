/**
 * Grid, snap, zoom, scale bar, compass and dimension text of the plan editor (REQ-053 WP 2.5):
 * GP-FR-009/011/012/014/015/150/154, GP-ACC-006.
 */
import { useCallback, useState } from 'react';
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { configureStore } from '@reduxjs/toolkit';
import { Provider } from 'react-redux';
import { afterEach, describe, expect, it } from 'vitest';
import { ThemeContextProvider } from '@/theme';
import { useAppSelector } from '@/store/hooks';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { HeadlessPlanRenderer } from '../renderer/HeadlessPlanRenderer';
import type { Viewport } from '../renderer';
import { TEST_LABELS } from '../renderer/rendererTestKit';
import {
  gardenPlanSlice,
  loadGardenPlan,
  selectGardenPlanState,
  type GardenPlanState,
} from '../state/gardenPlanSlice';
import { zoomAround } from '../model/units';
import type { Point } from '../model/types';
import { testPlan } from './tools/toolTestKit';
import { GardenPlanEditor } from './GardenPlanEditor';

const START: Viewport = { originM: [0, 20], pxPerM: 40, widthPx: 800, heightPx: 800 };
const MIN_PX_PER_M = 10;
const px = (x: number, y: number, view: Viewport = START) => ({
  clientX: (x - view.originM[0]) * view.pxPerM,
  clientY: (view.originM[1] - y) * view.pxPerM,
});
const mouse = (extra: Record<string, unknown> = {}) => ({
  pointerId: 1,
  pointerType: 'mouse',
  button: 0,
  ...extra,
});

/** The route's part: a viewport that zooms and fits. */
function Harness({ renderer }: { renderer: HeadlessPlanRenderer }) {
  const { plan } = useAppSelector(selectGardenPlanState);
  const [viewport, setViewport] = useState<Viewport>(START);
  const onZoom = useCallback((pxPerM: number, anchorPx: Point) => {
    setViewport((previous) => ({ ...previous, ...zoomAround(previous, pxPerM, anchorPx, MIN_PX_PER_M) }));
  }, []);
  const onFit = useCallback(() => setViewport(START), []);
  if (!plan) return null;
  return (
    <GardenPlanEditor
      plan={plan}
      viewport={viewport}
      renderer={renderer}
      labels={TEST_LABELS}
      onPan={() => undefined}
      onZoom={onZoom}
      onFit={onFit}
      minPxPerM={MIN_PX_PER_M}
    />
  );
}

function setup() {
  const store = configureStore({ reducer: { gardenPlan: gardenPlanSlice.reducer } });
  const plan = testPlan();
  store.dispatch(loadGardenPlan.pending('r1', 'site_1'));
  store.dispatch(loadGardenPlan.fulfilled(plan, 'r1', 'site_1'));
  const view = render(
    <Provider store={store}>
      <ThemeContextProvider>
        <Harness renderer={new HeadlessPlanRenderer()} />
      </ThemeContextProvider>
    </Provider>,
  );
  const state = (): GardenPlanState => store.getState().gardenPlan;
  const canvas = () => screen.getByTestId('garden-plan-canvas');
  const originOf = (key: string) =>
    (state().plan!.locations[key].geometry as { origin: Point }).origin;
  const drag = (path: [number, number][], mods: Record<string, unknown> = {}) => {
    fireEvent.pointerDown(canvas(), mouse({ ...px(...path[0]), ...mods }));
    for (const point of path.slice(1)) {
      fireEvent.pointerMove(canvas(), mouse({ ...px(...point), ...mods }));
    }
    fireEvent.pointerUp(canvas(), mouse({ ...px(...path[path.length - 1]), ...mods }));
  };
  return { store, state, canvas, originOf, drag, view };
}

afterEach(() => {
  cleanup();
  window.localStorage.clear();
});

describe('snap to grid (GP-FR-012, GP-ACC-006)', () => {
  it('moving a bed by 23 cm lands on a multiple of the 10 cm grid, with Alt on the exact value', () => {
    const t = setup();
    t.drag([[4, 4], [4.1, 4], [4.23, 4]]);
    expect(t.originOf('b1')).toEqual([3.2, 3]);
    t.drag([[5, 4], [5.1, 4], [5.23, 4]], { altKey: true });
    expect(t.originOf('b1')[0]).toBeCloseTo(3.43, 3);
  });

  it('follows the chosen grid step shown in the header', () => {
    const t = setup();
    fireEvent.change(screen.getByTestId('garden-plan-grid-step'), { target: { value: '1' } });
    t.drag([[4, 4], [4.2, 4], [4.6, 4]]);
    expect(t.originOf('b1')).toEqual([4, 3]);
  });

  it('the switch turns snapping off, the value is then only rounded to the millimetre', () => {
    const t = setup();
    fireEvent.click(screen.getByTestId('garden-plan-snap-toggle'));
    t.drag([[4, 4], [4.1, 4], [4.23, 4]]);
    expect(t.originOf('b1')[0]).toBeCloseTo(3.23, 3);
  });

  it('a drawn bed starts and ends on grid points', () => {
    const t = setup();
    const before = new Set(Object.keys(t.state().plan!.locations));
    fireEvent.click(screen.getByTestId('garden-plan-tool-bed'));
    t.drag([[14.13, 12.04], [16.4, 13.97], [17.58, 14.46]]);
    const created = Object.values(t.state().plan!.locations).find((l) => !before.has(l.key));
    const geometry = created?.geometry as { origin: Point; width_m: number; length_m: number } | undefined;
    expect(geometry?.origin).toEqual([14.1, 12]);
    expect(geometry?.width_m).toBeCloseTo(3.5, 3);
  });

  it('shows a marker with guide lines at the snapped point while a draw tool hovers', () => {
    const t = setup();
    fireEvent.click(screen.getByTestId('garden-plan-tool-bed'));
    fireEvent.pointerMove(t.canvas(), mouse(px(14.13, 12.04)));
    expect(screen.getByTestId('garden-plan-snap-marker')).toHaveAttribute('data-kind', 'grid');
    fireEvent.pointerMove(t.canvas(), mouse({ ...px(14.13, 12.04), altKey: true }));
    expect(screen.queryByTestId('garden-plan-snap-marker')).toBeNull();
    fireEvent.pointerMove(t.canvas(), mouse(px(14.13, 12.04)));
    fireEvent.pointerLeave(t.canvas());
    expect(screen.queryByTestId('garden-plan-snap-marker')).toBeNull();
  });
});

describe('grid lines (GP-FR-011)', () => {
  const step = () => Number(screen.getByTestId('garden-plan-grid').getAttribute('data-step-m'));

  it('draws only lines at least 8 px apart: at 40 px/m the 10 cm grid shows 25 cm lines', () => {
    setup();
    expect(step()).toBe(0.25);
    fireEvent.click(screen.getByTestId('garden-plan-zoom-in')); // 50 px/m: 10 cm = 5 px
    expect(step()).toBe(0.25);
    fireEvent.click(screen.getByTestId('garden-plan-zoom-in')); // 100 px/m
    expect(step()).toBe(0.1);
  });

  it('G and the switch hide and show the grid', () => {
    const t = setup();
    fireEvent.keyDown(t.canvas(), { key: 'g' });
    expect(screen.queryByTestId('garden-plan-grid')).toBeNull();
    fireEvent.click(screen.getByTestId('garden-plan-grid-toggle'));
    expect(screen.getByTestId('garden-plan-grid')).toBeInTheDocument();
  });

  it('snapping keeps its raster while the lines of a fine step are not drawn', () => {
    const t = setup();
    fireEvent.change(screen.getByTestId('garden-plan-grid-step'), { target: { value: '0.01' } });
    expect(step()).toBeGreaterThan(0.01);
    t.drag([[4, 4], [4.1, 4], [4.237, 4]]);
    expect(t.originOf('b1')[0]).toBeCloseTo(3.24, 3);
  });
});

describe('zoom (GP-FR-009, GP-FR-150)', () => {
  const level = () => screen.getByTestId('garden-plan-zoom-level').textContent;

  it('the buttons step through the fixed levels and "fit" returns to the start', () => {
    setup();
    expect(level()).toBe('40 %');
    fireEvent.click(screen.getByTestId('garden-plan-zoom-in'));
    expect(level()).toBe('50 %');
    fireEvent.click(screen.getByTestId('garden-plan-zoom-in'));
    expect(level()).toBe('100 %');
    fireEvent.click(screen.getByTestId('garden-plan-zoom-in'));
    expect(level()).toBe('200 %');
    fireEvent.click(screen.getByTestId('garden-plan-zoom-out'));
    fireEvent.click(screen.getByTestId('garden-plan-zoom-out'));
    expect(level()).toBe('50 %');
    fireEvent.click(screen.getByTestId('garden-plan-zoom-fit'));
    expect(level()).toBe('40 %');
  });

  it('never goes below the fit zoom: the zoom-out button is then disabled', () => {
    setup();
    fireEvent.click(screen.getByTestId('garden-plan-zoom-out')); // 40 -> 25
    expect(level()).toBe('25 %');
    fireEvent.click(screen.getByTestId('garden-plan-zoom-out'));
    expect(level()).toBe('10 %');
    expect(screen.getByTestId('garden-plan-zoom-out')).toBeDisabled();
  });

  it('+ and - zoom from the keyboard, 0 fits', () => {
    const t = setup();
    fireEvent.keyDown(t.canvas(), { key: '+' });
    fireEvent.keyDown(t.canvas(), { key: '+' });
    expect(level()).toBe('100 %');
    fireEvent.keyDown(t.canvas(), { key: '-' });
    expect(level()).toBe('50 %');
    fireEvent.keyDown(t.canvas(), { key: '0' });
    expect(level()).toBe('40 %');
  });

  it('a plain wheel leaves the page scrolling', () => {
    const t = setup();
    const wheel = new WheelEvent('wheel', { deltaY: -200, clientX: 200, clientY: 200, cancelable: true, bubbles: true });
    act(() => {
      t.canvas().dispatchEvent(wheel);
    });
    expect(wheel.defaultPrevented).toBe(false);
    expect(level()).toBe('40 %');
  });

  it('Ctrl + wheel zooms stepless around the pointer and keeps the page from scrolling', () => {
    const t = setup();
    const wheel = new WheelEvent('wheel', { deltaY: -200, clientX: 200, clientY: 200, ctrlKey: true, cancelable: true, bubbles: true });
    act(() => {
      t.canvas().dispatchEvent(wheel);
    });
    expect(wheel.defaultPrevented).toBe(true);
    const percent = Number(level()!.replace(' %', ''));
    expect(percent).toBeGreaterThan(40);
    expect(percent).not.toBe(100); // no snapping to a level
  });

  it('zooming keeps the model point under the anchor fixed', () => {
    const next = zoomAround(START, 100, [200, 200], MIN_PX_PER_M);
    expect(next.originM[0] + 200 / next.pxPerM).toBeCloseTo(5, 9);
    expect(next.originM[1] - 200 / next.pxPerM).toBeCloseTo(15, 9);
  });
});

describe('scale bar (GP-FR-009)', () => {
  it('is always visible and follows the zoom', () => {
    setup();
    const bar = () => screen.getByTestId('garden-plan-scale-bar');
    expect(bar()).toHaveAttribute('data-length-m', '1'); // 5 m would be 200 px
    expect(bar()).toHaveAccessibleName('Scale bar: 1 m');
    fireEvent.click(screen.getByTestId('garden-plan-zoom-out')); // 25 px/m
    expect(bar()).toHaveAttribute('data-length-m', '5');
    fireEvent.click(screen.getByTestId('garden-plan-zoom-out')); // 10 px/m
    expect(bar()).toHaveAttribute('data-length-m', '10');
  });
});

describe('dimension text (GP-FR-014)', () => {
  it('names width, length and area of the selected bed, in the chosen unit', () => {
    const t = setup();
    fireEvent.pointerDown(t.canvas(), mouse(px(4, 4)));
    fireEvent.pointerUp(t.canvas(), mouse(px(4, 4)));
    expect(screen.getByTestId('garden-plan-dimension')).toHaveTextContent('2.00 m × 2.00 m · 4.00 m²');
    fireEvent.click(screen.getByTestId('garden-plan-unit-cm'));
    expect(screen.getByTestId('garden-plan-dimension')).toHaveTextContent('200 cm × 200 cm · 4.00 m²');
    expect(window.localStorage.getItem('kp_garden_plan_length_unit')).toBe('cm');
  });

  it('shows the size of what is being drawn', () => {
    const t = setup();
    fireEvent.click(screen.getByTestId('garden-plan-tool-bed'));
    fireEvent.pointerDown(t.canvas(), mouse(px(14, 12)));
    fireEvent.pointerMove(t.canvas(), mouse(px(16.5, 13)));
    expect(screen.getByTestId('garden-plan-dimension')).toHaveTextContent('2.50 m × 1.00 m · 2.50 m²');
    fireEvent.keyDown(t.canvas(), { key: 'Escape' });
  });

  it('shows the diameter and area of a circle', () => {
    const t = setup();
    fireEvent.pointerDown(t.canvas(), mouse(px(9, 9)));
    fireEvent.pointerUp(t.canvas(), mouse(px(9, 9)));
    expect(screen.getByTestId('garden-plan-dimension')).toHaveTextContent('Ø 1.00 m · 0.79 m²');
  });
});

describe('compass (GP-FR-015)', () => {
  const dial = () => screen.getByRole('slider', { name: /Compass/ });

  it('shows north at 0 degrees and the input as clockwise azimuth', () => {
    setup();
    expect(dial()).toHaveAttribute('aria-valuenow', '0');
    expect(screen.getByLabelText(/North angle/)).toHaveValue(0);
  });

  it('typing an angle sets it as one undoable plan operation; the stored value stays an azimuth', () => {
    const t = setup();
    const input = screen.getByLabelText(/North angle/);
    fireEvent.change(input, { target: { value: '90' } });
    fireEvent.blur(input);
    expect(t.state().plan!.settings!.north_angle_deg).toBe(90);
    expect(t.state().pending).toHaveLength(1);
    expect(dial()).toHaveAttribute('aria-valuenow', '90');
    act(() => {
      t.store.dispatch({ type: 'gardenPlan/undo' });
    });
    expect(t.state().plan!.settings!.north_angle_deg).toBe(0);
  });

  it('stores 360 as 0 and refuses values outside 0 to 360 with a message', () => {
    const t = setup();
    const input = screen.getByLabelText(/North angle/);
    fireEvent.change(input, { target: { value: '-15' } });
    expect(screen.getByText('Enter an angle from 0 to 360.')).toBeInTheDocument();
    fireEvent.blur(input);
    expect(t.state().plan!.settings!.north_angle_deg).toBe(0);
    expect(t.state().pending).toHaveLength(0);
    fireEvent.change(input, { target: { value: '360' } });
    fireEvent.blur(input);
    expect(t.state().plan!.settings!.north_angle_deg).toBe(0);
  });

  it('arrow keys turn the dial by 1 degree, Shift by 15', () => {
    const t = setup();
    fireEvent.keyDown(dial(), { key: 'ArrowRight' });
    expect(t.state().plan!.settings!.north_angle_deg).toBe(1);
    fireEvent.keyDown(dial(), { key: 'ArrowRight', shiftKey: true });
    expect(t.state().plan!.settings!.north_angle_deg).toBe(16);
    fireEvent.keyDown(dial(), { key: 'Home' });
    expect(t.state().plan!.settings!.north_angle_deg).toBe(0);
  });

  it('dragging the dial to the right sets 90 degrees on release', () => {
    const t = setup();
    fireEvent.pointerDown(dial(), mouse({ clientX: 30, clientY: 0 }));
    fireEvent.pointerMove(dial(), mouse({ clientX: 30, clientY: 0 }));
    expect(t.state().plan!.settings!.north_angle_deg).toBe(0); // not before release
    fireEvent.pointerUp(dial(), mouse({ clientX: 30, clientY: 0 }));
    expect(t.state().plan!.settings!.north_angle_deg).toBe(90);
  });

  it('does not touch rotation_deg of any object', () => {
    const t = setup();
    const before = JSON.stringify(Object.values(t.state().plan!.locations).map((l) => l.geometry));
    fireEvent.keyDown(dial(), { key: 'ArrowRight', shiftKey: true });
    const after = JSON.stringify(Object.values(t.state().plan!.locations).map((l) => l.geometry));
    expect(after).toBe(before);
  });
});

describe('accessibility', () => {
  it('the view bar (grid, zoom, compass) and the canvas have no violations', async () => {
    const t = setup();
    await expectNoA11yViolations(t.view.container);
    fireEvent.click(screen.getByTestId('garden-plan-zoom-in'));
    fireEvent.pointerDown(t.canvas(), mouse(px(4, 4)));
    fireEvent.pointerUp(t.canvas(), mouse(px(4, 4)));
    await expectNoA11yViolations(t.view.container);
  });

  it('every control of the bar has a name and a 44 px target', () => {
    setup();
    for (const id of ['zoom-in', 'zoom-out', 'zoom-fit', 'grid-toggle', 'snap-toggle', 'unit-m']) {
      const button = screen.getByTestId(`garden-plan-${id}`);
      expect(button).toHaveStyle({ minHeight: '44px', minWidth: '44px' });
    }
    expect(screen.getByTestId('garden-plan-zoom-in')).toHaveAccessibleName('Zoom in');
    expect(screen.getByTestId('garden-plan-zoom-fit')).toHaveAccessibleName(/Fit/);
    expect(screen.getByLabelText('Grid step')).toBeInTheDocument();
  });
});
