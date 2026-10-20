/** Shared rendering helpers of the editor component tests (WP 2.6): store, editor and pointer helpers. */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { configureStore } from '@reduxjs/toolkit';
import { Provider } from 'react-redux';
import { vi, type Mock } from 'vitest';
import { ThemeContextProvider } from '@/theme';
import { HeadlessPlanRenderer } from '../renderer/HeadlessPlanRenderer';
import { TEST_LABELS } from '../renderer/rendererTestKit';
import type { Viewport } from '../renderer';
import type { PlanModel } from '../model/planModel';
import { gardenPlanSlice, loadGardenPlan, type GardenPlanState } from '../state/gardenPlanSlice';
import { GardenPlanEditor } from './GardenPlanEditor';
import { testPlan } from './tools/toolTestKit';

/** 40 px per metre, model (0, 20) at the top-left: the area is 400 px wide, a 2 m bed 80 px. */
export const VIEWPORT: Viewport = { originM: [0, 20], pxPerM: 40, widthPx: 800, heightPx: 800 };

export const px = (x: number, y: number): { clientX: number; clientY: number } => ({
  clientX: x * 40,
  clientY: (20 - y) * 40,
});

export const pointer = (extra: Record<string, unknown> = {}) => ({
  pointerId: 1,
  pointerType: 'mouse',
  button: 0,
  ...extra,
});

/** Makes MUI's `useMediaQuery` answer `true` for max-width queries (a phone) and for `(pointer: coarse)`. */
export function stubPhone(): () => void {
  const original = window.matchMedia;
  window.matchMedia = ((query: string) => ({
    matches: query.includes('max-width') || query.includes('coarse'),
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

interface SetupOptions {
  plan?: PlanModel;
  onPan?: Mock<(dxPx: number, dyPx: number) => void>;
  onZoom?: Mock<(factor: number, centerPx: [number, number]) => void>;
  onOpenLocation?: Mock<(locationKey: string) => void>;
  onOpenCare?: Mock<(locationKey: string) => void>;
  viewport?: Viewport;
}

export function setupEditor(options: SetupOptions = {}) {
  const plan = options.plan ?? testPlan();
  const onPan = options.onPan ?? vi.fn<(dxPx: number, dyPx: number) => void>();
  const onZoom = options.onZoom;
  const onOpenLocation = options.onOpenLocation;
  const onOpenCare = options.onOpenCare;
  const store = configureStore({ reducer: { gardenPlan: gardenPlanSlice.reducer } });
  store.dispatch(loadGardenPlan.pending('r1', 'site_1'));
  store.dispatch(loadGardenPlan.fulfilled(plan, 'r1', 'site_1'));
  const renderer = new HeadlessPlanRenderer();
  const state = (): GardenPlanState => store.getState().gardenPlan;
  const tree = () => (
    <Provider store={store}>
      <ThemeContextProvider>
        <GardenPlanEditor
          plan={state().plan!}
          viewport={options.viewport ?? VIEWPORT}
          renderer={renderer}
          labels={TEST_LABELS}
          onPan={onPan}
          onZoom={onZoom}
          onOpenLocation={onOpenLocation}
          onOpenCare={onOpenCare}
        />
      </ThemeContextProvider>
    </Provider>
  );
  const view = render(tree());
  const rerender = () => view.rerender(tree());
  const canvas = () => screen.getByTestId('garden-plan-canvas');
  /** Run an interaction, then bring the editor up to date with the store. */
  const after = <T,>(run: () => T): T => {
    const result = run();
    act(() => rerender());
    return result;
  };
  const click = (x: number, y: number, mods: Record<string, unknown> = {}) =>
    after(() => {
      fireEvent.pointerDown(canvas(), pointer({ ...px(x, y), ...mods }));
      fireEvent.pointerUp(canvas(), pointer({ ...px(x, y), ...mods }));
    });
  const selected = () => state().selection.map((ref) => ref.key);
  return { store, state, view, rerender, canvas, after, click, selected, renderer, onPan, onZoom };
}

/** Type into a panel field and leave it: the value is committed on blur. */
export function typeAndBlur(element: HTMLElement, value: string): void {
  fireEvent.change(element, { target: { value } });
  fireEvent.blur(element);
}
