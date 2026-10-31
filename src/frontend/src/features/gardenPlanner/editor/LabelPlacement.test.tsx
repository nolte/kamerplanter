/**
 * The editor's half of label placement (REQ-053 GP-UX-047/048, #2490): the dimension text stands outside above the
 * edge and clear of the handles, the renderer prints no second one under it, and an object too small for handles
 * offers "zoom in to edit", which zooms until the handles are there.
 */
import { useCallback, useState } from 'react';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { configureStore } from '@reduxjs/toolkit';
import { Provider } from 'react-redux';
import { afterEach, describe, expect, it } from 'vitest';
import { ThemeContextProvider } from '@/theme';
import { useAppSelector } from '@/store/hooks';
import { HeadlessPlanRenderer } from '../renderer/HeadlessPlanRenderer';
import type { Viewport } from '../renderer';
import { TEST_LABELS } from '../renderer/rendererTestKit';
import { gardenPlanSlice, loadGardenPlan, selectGardenPlanState } from '../state/gardenPlanSlice';
import { zoomAround } from '../model/units';
import type { Point } from '../model/types';
import { testPlan } from './tools/toolTestKit';
import { HANDLE_TARGET_PX, HANDLE_VISIBLE_PX } from './tools/handles';
import { GardenPlanEditor } from './GardenPlanEditor';

const START: Viewport = { originM: [0, 20], pxPerM: 40, widthPx: 800, heightPx: 800 };
const mouse = (x: number, y: number, view: Viewport) => ({
  pointerId: 1,
  pointerType: 'mouse',
  button: 0,
  clientX: (x - view.originM[0]) * view.pxPerM,
  clientY: (view.originM[1] - y) * view.pxPerM,
});

function Harness({ renderer, onViewport }: { renderer: HeadlessPlanRenderer; onViewport: (view: Viewport) => void }) {
  const { plan } = useAppSelector(selectGardenPlanState);
  const [viewport, setViewport] = useState<Viewport>(START);
  const onZoom = useCallback(
    (pxPerM: number, anchorPx: Point) => {
      setViewport((previous) => {
        const next = { ...previous, ...zoomAround(previous, pxPerM, anchorPx, 10) };
        onViewport(next);
        return next;
      });
    },
    [onViewport],
  );
  if (!plan) return null;
  return (
    <GardenPlanEditor
      plan={plan}
      viewport={viewport}
      renderer={renderer}
      labels={TEST_LABELS}
      onPan={() => undefined}
      onZoom={onZoom}
      minPxPerM={10}
    />
  );
}

function setup() {
  const store = configureStore({ reducer: { gardenPlan: gardenPlanSlice.reducer } });
  store.dispatch(loadGardenPlan.pending('r1', 'site_1'));
  store.dispatch(loadGardenPlan.fulfilled(testPlan(), 'r1', 'site_1'));
  const renderer = new HeadlessPlanRenderer();
  let current = START;
  render(
    <Provider store={store}>
      <ThemeContextProvider>
        <Harness renderer={renderer} onViewport={(view) => (current = view)} />
      </ThemeContextProvider>
    </Provider>,
  );
  const canvas = () => screen.getByTestId('garden-plan-canvas');
  const click = (x: number, y: number) => {
    fireEvent.pointerDown(canvas(), mouse(x, y, current));
    fireEvent.pointerUp(canvas(), mouse(x, y, current));
  };
  return { renderer, click, viewport: () => current };
}

afterEach(() => {
  cleanup();
  window.localStorage.clear();
});

/** Centre of a handle mark in canvas pixels. */
function handleCentre(id: string): Point {
  const node = screen.getByTestId(`garden-plan-handle-${id}`);
  if (node.tagName.toLowerCase() === 'circle') {
    return [Number(node.getAttribute('cx')), Number(node.getAttribute('cy'))];
  }
  return [
    Number(node.getAttribute('x')) + HANDLE_VISIBLE_PX / 2,
    Number(node.getAttribute('y')) + HANDLE_VISIBLE_PX / 2,
  ];
}

describe('dimension text in the editor (GP-UX-047)', () => {
  it('stands above the edge, past the edge and the rotate handle of the selection', () => {
    const t = setup();
    t.click(11, 11); // the 10 x 10 m area: 400 px, every handle
    const text = screen.getByTestId('garden-plan-dimension');
    const baseline = Number(text.getAttribute('y'));
    const [, topEdge] = handleCentre('n');
    const [, rotate] = handleCentre('rotate');
    expect(Number(text.getAttribute('x'))).toBe(handleCentre('n')[0]); // centred over the edge
    expect(baseline).toBeLessThan(topEdge - HANDLE_VISIBLE_PX / 2); // outside the shape, above its edge handle
    expect(baseline + 12 * 0.25).toBeLessThanOrEqual(rotate - HANDLE_VISIBLE_PX / 2); // and above the rotate handle
  });

  it('is printed once: the renderer leaves the selection dimensions to the overlay', () => {
    const t = setup();
    t.click(11, 11);
    expect(screen.getAllByTestId('garden-plan-dimension')).toHaveLength(1);
    expect(t.renderer.lastScene?.shapes.find((shape) => shape.entry.key === 'area')?.showDimensions).toBe(false);
  });
});

describe('"zoom in to edit" (GP-UX-048)', () => {
  it('zooms an object too small for handles until it has all of them, around its centre', () => {
    const t = setup();
    t.click(4, 4); // Bed 1: 2 m = 80 px < 2 x 48 px
    expect(screen.getByTestId('garden-plan-too-small')).toBeInTheDocument();
    expect(screen.getByTestId('garden-plan-handles')).toHaveAttribute('data-density', 'none');

    fireEvent.click(screen.getByTestId('garden-plan-zoom-to-edit'));

    const view = t.viewport();
    expect(2 * view.pxPerM).toBeGreaterThanOrEqual(3 * HANDLE_TARGET_PX);
    expect(screen.getByTestId('garden-plan-handles')).toHaveAttribute('data-density', 'full');
    expect(screen.queryByTestId('garden-plan-too-small')).toBeNull();
    // the bed's centre (4, 4) stays where it was on screen: 160 / 640 px at 40 px/m
    expect((4 - view.originM[0]) * view.pxPerM).toBeCloseTo(160, 6);
    expect((view.originM[1] - 4) * view.pxPerM).toBeCloseTo(640, 6);
  });

  it('is not offered for an object that has handles', () => {
    const t = setup();
    t.click(11, 11);
    expect(screen.queryByTestId('garden-plan-zoom-to-edit')).toBeNull();
  });
});
