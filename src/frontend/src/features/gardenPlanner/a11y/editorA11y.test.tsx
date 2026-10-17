/**
 * Keyboard operation, list view and live region of the plan editor (REQ-053 WP 2.7:
 * GP-ACC-008, GP-ACC-032, GP-NFR-020/022/023/068/070, GP-UX-045). No pointer anywhere in here.
 * It lives outside `editor/` because it composes the editor with the real `SvgPlanRenderer`,
 * which `editor/` may not import (GP-NFR-009).
 */
import { act, cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { configureStore } from '@reduxjs/toolkit';
import { Provider, useSelector } from 'react-redux';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ThemeContextProvider } from '@/theme';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { SvgPlanRenderer } from '../renderer/SvgPlanRenderer';
import type { Viewport } from '../renderer';
import { TEST_LABELS } from '../renderer/rendererTestKit';
import {
  gardenPlanSlice,
  loadGardenPlan,
  selectGardenPlanState,
  setSelection,
} from '../state/gardenPlanSlice';
import { GardenPlanEditor } from '../editor/GardenPlanEditor';
import { testPlan } from '../editor/tools/toolTestKit';

const VIEWPORT: Viewport = { originM: [0, 20], pxPerM: 40, widthPx: 800, heightPx: 800 };

function Harness({
  renderer,
  onPan,
}: {
  renderer: SvgPlanRenderer;
  onPan: (x: number, y: number) => void;
}) {
  const state = useSelector(selectGardenPlanState);
  if (!state.plan) return null;
  return (
    <GardenPlanEditor
      plan={state.plan}
      viewport={VIEWPORT}
      renderer={renderer}
      labels={TEST_LABELS}
      fieldMode={false}
      onPan={onPan}
    />
  );
}

function setup() {
  const store = configureStore({ reducer: { gardenPlan: gardenPlanSlice.reducer } });
  store.dispatch(loadGardenPlan.pending('r1', 'site_1'));
  store.dispatch(loadGardenPlan.fulfilled(testPlan(), 'r1', 'site_1'));
  const onPan = vi.fn();
  render(
    <Provider store={store}>
      <ThemeContextProvider>
        <Harness renderer={new SvgPlanRenderer()} onPan={onPan} />
      </ThemeContextProvider>
    </Provider>,
  );
  const select = (key: string, entity: 'location' | 'garden_object' = 'location') =>
    act(() => void store.dispatch(setSelection([{ entity, key }])));
  const canvas = () => screen.getByTestId('garden-plan-canvas');
  const live = () => screen.getByTestId('garden-plan-live-region');
  const settle = () => act(() => void vi.advanceTimersByTime(1000));
  const plan = () => store.getState().gardenPlan.plan!;
  return { store, onPan, select, canvas, live, settle, plan };
}

beforeEach(() => {
  vi.useFakeTimers();
  window.localStorage.clear();
});
afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

describe('arrow keys (GP-ACC-008)', () => {
  it('moves the selected bed three grid steps and announces the coordinate once', () => {
    const t = setup();
    t.select('solo');
    for (let i = 0; i < 3; i += 1) fireEvent.keyDown(t.canvas(), { key: 'ArrowRight' });
    // The default grid of the test plan is 0.1 m.
    expect(t.plan().locations.solo.bbox?.[0]).toBeCloseTo(14.3, 6);
    expect(t.live().textContent).toBe(''); // still settling: not every step is spoken
    t.settle();
    expect(t.live().textContent).toBe('Solo moved to x 14.3 m, y 2 m.');
    expect(t.live()).toHaveAttribute('aria-live', 'polite');
  });

  it('moves up with ArrowUp (model y points up) and ten steps with Shift', () => {
    const t = setup();
    t.select('solo');
    fireEvent.keyDown(t.canvas(), { key: 'ArrowUp', shiftKey: true });
    expect(t.plan().locations.solo.bbox?.[1]).toBeCloseTo(3, 6);
    expect(t.plan().locations.solo.bbox?.[0]).toBe(14);
  });

  it('scrolls the view when nothing is selected, and does not touch the plan', () => {
    const t = setup();
    fireEvent.keyDown(t.canvas(), { key: 'ArrowRight' });
    fireEvent.keyDown(t.canvas(), { key: 'ArrowDown' });
    expect(t.onPan).toHaveBeenNthCalledWith(1, -40, 0);
    expect(t.onPan).toHaveBeenNthCalledWith(2, 0, -40);
    expect(t.store.getState().gardenPlan.past).toHaveLength(0);
  });

  it('tells the user a locked bed cannot move instead of moving it', () => {
    const t = setup();
    t.select('lock');
    fireEvent.keyDown(t.canvas(), { key: 'ArrowLeft' });
    expect(screen.getByTestId('garden-plan-notice')).toHaveTextContent(/Locked objects cannot/);
    expect(t.plan().locations.lock.bbox?.[0]).toBe(14);
  });

  it('leaves arrow keys typed in a field alone', () => {
    const t = setup();
    t.select('solo');
    const input = document.createElement('input');
    t.canvas().appendChild(input);
    fireEvent.keyDown(input, { key: 'ArrowRight' });
    expect(t.plan().locations.solo.bbox?.[0]).toBe(14);
  });
});

describe('roving focus across objects (GP-NFR-068)', () => {
  it('has one tab stop among the objects and walks them with Page Down / Page Up', () => {
    const t = setup();
    const stops = t.canvas().querySelectorAll('[data-plan-key][tabindex="0"]');
    expect(stops).toHaveLength(1);
    const objects = Array.from(
      t.canvas().querySelectorAll<HTMLElement>('[data-plan-key][role="button"]'),
    );
    objects[0].focus();
    fireEvent.keyDown(objects[0], { key: 'PageDown' });
    expect(document.activeElement).toBe(objects[1]);
    fireEvent.keyDown(objects[1], { key: 'PageUp' });
    expect(document.activeElement).toBe(objects[0]);
  });
});

describe('single-key shortcuts (WCAG 2.1.4, GP-UX-045)', () => {
  it('opens the key help with ? while the plan has focus', () => {
    const t = setup();
    fireEvent.keyDown(t.canvas(), { key: '?' });
    expect(screen.getByTestId('garden-plan-keyboard-help')).toBeInTheDocument();
  });

  it('can be switched off, and the button still opens the help', () => {
    const t = setup();
    fireEvent.click(screen.getByTestId('garden-plan-keyboard-help-button'));
    const help = screen.getByTestId('garden-plan-keyboard-help');
    fireEvent.click(within(help).getByRole('switch', { name: 'Single-key shortcuts' }));
    expect(window.localStorage.getItem('kamerplanter.gardenPlan.singleKeyShortcuts')).toBe('off');
    fireEvent.click(within(help).getByRole('button', { name: 'Close' }));
    act(() => void vi.advanceTimersByTime(1000));
    expect(screen.queryByTestId('garden-plan-keyboard-help')).toBeNull();
    fireEvent.keyDown(t.canvas(), { key: '?' });
    expect(screen.queryByTestId('garden-plan-keyboard-help')).toBeNull();
  });
});

describe('list view (GP-NFR-023, GP-ACC-032)', () => {
  it('is reached by the skip link, with the focus on the list', () => {
    const t = setup();
    expect(t.canvas()).toBeInTheDocument();
    fireEvent.click(screen.getByTestId('garden-plan-skip-list'));
    expect(screen.queryByTestId('garden-plan-canvas')).toBeNull();
    expect(document.activeElement).toBe(screen.getByTestId('garden-plan-list'));
    expect(screen.getByTestId('garden-plan-skip-plan')).toBeInTheDocument();
  });

  it('shows every object with name, type, position and size', () => {
    setup();
    fireEvent.click(screen.getByRole('switch', { name: 'Show as list' }));
    const row = screen.getByTestId('garden-plan-list-row-b1');
    expect(row).toHaveTextContent('Bed 1');
    expect(row).toHaveTextContent('x 3 m, y 3 m');
    expect(row).toHaveTextContent('4 m2'); // the label kit prints the area
    expect(screen.getByTestId('garden-plan-list-row-t1')).toHaveTextContent('Tree');
  });

  it('selects, reads the values, moves with buttons and with numbers, and keeps the focus', () => {
    const t = setup();
    fireEvent.click(screen.getByRole('switch', { name: 'Show as list' }));
    fireEvent.click(
      within(screen.getByTestId('garden-plan-list-row-solo')).getByRole('button', { name: /Solo/ }),
    );
    const details = screen.getByTestId('garden-plan-list-details');
    expect(details).toHaveTextContent('Position');
    expect(details).toHaveTextContent('Status');

    fireEvent.click(screen.getByTestId('garden-plan-list-move-right'));
    expect(t.plan().locations.solo.bbox?.[0]).toBeCloseTo(14.1, 6);

    fireEvent.change(screen.getByTestId('garden-plan-list-x'), { target: { value: '10' } });
    fireEvent.change(screen.getByTestId('garden-plan-list-y'), { target: { value: '5' } });
    const input = screen.getByTestId('garden-plan-list-x');
    input.focus();
    fireEvent.click(screen.getByTestId('garden-plan-list-move-to'));
    expect(t.plan().locations.solo.bbox).toEqual([10, 5, 12, 7]);
    // The fields follow the new position and are the same elements: the focus did not vanish.
    expect(screen.getByTestId('garden-plan-list-x')).toBe(input);
    expect(input).toHaveValue(10);
    t.settle();
    expect(t.live().textContent).toBe('Solo moved to x 10 m, y 5 m.');
  });

  it('walks the rows with the arrow keys as one tab stop', () => {
    setup();
    fireEvent.click(screen.getByRole('switch', { name: 'Show as list' }));
    const rowButtons = Array.from(document.querySelectorAll<HTMLElement>('button[data-list-key]'));
    expect(rowButtons.filter((b) => b.tabIndex === 0)).toHaveLength(1);
    rowButtons[0].focus();
    fireEvent.keyDown(rowButtons[0], { key: 'ArrowDown' });
    expect(document.activeElement).toBe(rowButtons[1]);
    fireEvent.keyDown(rowButtons[1], { key: 'End' });
    expect(document.activeElement).toBe(rowButtons[rowButtons.length - 1]);
    fireEvent.keyDown(document.activeElement!, { key: 'Home' });
    expect(document.activeElement).toBe(rowButtons[0]);
  });

  it('deletes through the confirmation and hands the focus to the next row, never the body', () => {
    const t = setup();
    fireEvent.click(screen.getByRole('switch', { name: 'Show as list' }));
    fireEvent.click(
      within(screen.getByTestId('garden-plan-list-row-b1')).getByRole('button', { name: /Bed 1/ }),
    );
    fireEvent.click(screen.getByTestId('garden-plan-list-delete'));
    const dialog = screen.getByTestId('confirm-dialog');
    expect(dialog).toHaveTextContent('Delete "Bed 1"?');
    fireEvent.click(within(dialog).getByTestId('confirm-dialog-confirm'));
    act(() => void vi.advanceTimersByTime(1000));
    expect(t.plan().locations.b1).toBeUndefined();
    expect(document.activeElement).toBe(document.querySelector('button[data-list-key="b2"]'));
    t.settle();
    expect(t.live().textContent).toBe('Bed 1 deleted.');
  });

  it('returns the focus to where it was when the delete is cancelled', () => {
    setup();
    fireEvent.click(screen.getByRole('switch', { name: 'Show as list' }));
    fireEvent.click(
      within(screen.getByTestId('garden-plan-list-row-solo')).getByRole('button', { name: /Solo/ }),
    );
    const del = screen.getByTestId('garden-plan-list-delete');
    del.focus();
    fireEvent.click(del);
    fireEvent.click(screen.getByTestId('confirm-dialog-cancel'));
    act(() => void vi.advanceTimersByTime(1000));
    expect(document.activeElement).toBe(del);
  });

  it('does not offer to move a locked object', () => {
    setup();
    fireEvent.click(screen.getByRole('switch', { name: 'Show as list' }));
    fireEvent.click(
      within(screen.getByTestId('garden-plan-list-row-lock')).getByRole('button', {
        name: /Locked/,
      }),
    );
    expect(screen.getByTestId('garden-plan-list-move-left')).toBeDisabled();
    expect(screen.getByTestId('garden-plan-list-details')).toHaveTextContent(/locked/i);
  });
});

describe('focus after a delete on the plan', () => {
  it('lands on a neighbouring object, not on the body', () => {
    const t = setup();
    t.select('b1');
    t.canvas().focus();
    fireEvent.keyDown(t.canvas(), { key: 'Delete' });
    fireEvent.click(screen.getByTestId('confirm-dialog-confirm'));
    act(() => void vi.advanceTimersByTime(1000));
    expect(t.plan().locations.b1).toBeUndefined();
    expect(document.activeElement).not.toBe(document.body);
    expect(document.activeElement?.getAttribute('data-plan-key')).toBe('b2');
  });
});

describe('announcements do not spam', () => {
  it('says nothing for a selection and one sentence for a finished action', () => {
    const t = setup();
    t.select('solo');
    t.settle();
    expect(t.live().textContent).toBe('');
  });
});

describe('accessibility (GP-ACC-032)', () => {
  it('has no violations on the plan view', async () => {
    const t = setup();
    t.select('solo');
    vi.useRealTimers();
    await expectNoA11yViolations(document.body, { minImpact: 'serious', minElements: 60 });
  });

  it('has no violations on the list view with a row opened', async () => {
    setup();
    fireEvent.click(screen.getByRole('switch', { name: 'Show as list' }));
    fireEvent.click(
      within(screen.getByTestId('garden-plan-list-row-b1')).getByRole('button', { name: /Bed 1/ }),
    );
    vi.useRealTimers();
    await expectNoA11yViolations(document.body, { minImpact: 'serious', minElements: 60 });
  });
});
