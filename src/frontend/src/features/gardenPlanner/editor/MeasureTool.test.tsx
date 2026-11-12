/**
 * The measure tool in the editor (REQ-053 GP-UX-071, #2913): the fifth button of the rail, a measurement on the
 * canvas with its lengths in the user's unit, the status text that announces the total, the touch path below md -
 * and nothing that reaches the plan, its pending operations or the undo history.
 */
import { cleanup, fireEvent, screen, within } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { openPanelTab, pointer, px, setupEditor, stubPhone } from './editorTestKit';

const restores: (() => void)[] = [];
afterEach(() => {
  cleanup();
  while (restores.length) restores.pop()?.();
  // The length unit is a stored view setting: the cm test must not leak into the next one.
  localStorage.clear();
});

function measureSetup() {
  const t = setupEditor();
  t.after(() => fireEvent.click(screen.getByTestId('garden-plan-tool-measure')));
  const hover = (x: number, y: number) => t.after(() => fireEvent.pointerMove(t.canvas(), pointer(px(x, y))));
  const status = () => screen.getByTestId('garden-plan-measure-status');
  const total = () => screen.queryByTestId('garden-plan-measure-total');
  return { ...t, hover, status, total };
}

describe('the measure tool on the rail (GP-UX-071)', () => {
  it('is a tool of the store, pressed on the rail, with a crosshair cursor', () => {
    const t = measureSetup();
    expect(t.state().tool).toBe('measure');
    expect(screen.getByTestId('garden-plan-tool-measure')).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByTestId('garden-plan-tool-measure')).toHaveAccessibleName('Measure');
    expect(t.canvas()).toHaveStyle({ cursor: 'crosshair' });
    // No draw options: measuring creates nothing, so there is no shape or type choice.
    expect(screen.queryByTestId('garden-plan-shape-rect')).toBeNull();
    expect(t.status()).toHaveTextContent('Click the start of the distance');
  });

  it('measures a distance: live line while moving, the length fixed by the second click, announced as text', () => {
    const t = measureSetup();
    t.click(1, 14);
    expect(t.status()).toHaveTextContent('Start point set');
    t.hover(4, 18);
    // The live line shows its length on the canvas; the status speaks of fixed points only.
    expect(t.total()).toHaveTextContent('5.00 m');
    expect(t.status()).not.toHaveTextContent('5.00 m');
    t.click(4, 18);
    expect(t.status()).toHaveTextContent('Measured: 5.00 m (1 segment)');
    expect(t.status()).toHaveAttribute('role', 'status');
    expect(t.status()).toHaveAttribute('aria-live', 'polite');
  });

  it('continues as a polyline with a length per segment and the total; Enter finishes, Esc clears', () => {
    const t = measureSetup();
    t.click(1, 14);
    t.click(4, 18);
    t.click(4, 12);
    const segments = screen.getAllByTestId('garden-plan-measure-segment').map((node) => node.textContent);
    expect(segments).toEqual(['5.00 m', '6.00 m']);
    expect(t.status()).toHaveTextContent('Measured: 11.00 m (2 segments)');

    t.after(() => fireEvent.keyDown(t.canvas(), { key: 'Enter' }));
    expect(screen.getByTestId('garden-plan-measure')).toHaveAttribute('data-done', 'true');
    expect(t.status()).toHaveTextContent('Measurement done: 11.00 m (2 segments)');
    expect(t.total()).toHaveTextContent('Total 11.00 m');

    // The measurement stays until Esc; the tool stays on.
    t.after(() => fireEvent.keyDown(t.canvas(), { key: 'Escape' }));
    expect(screen.queryByTestId('garden-plan-measure')).toBeNull();
    expect(t.state().tool).toBe('measure');
    expect(t.status()).toHaveTextContent('Click the start of the distance');
  });

  it('takes the last point back with Backspace, and a double click finishes', () => {
    const t = measureSetup();
    t.click(1, 14);
    t.click(4, 18);
    t.click(4, 12);
    t.after(() => fireEvent.keyDown(t.canvas(), { key: 'Backspace' }));
    expect(t.status()).toHaveTextContent('Measured: 5.00 m (1 segment)');
    // The second click of a double click lands on the last point.
    t.click(4, 18);
    expect(screen.getByTestId('garden-plan-measure')).toHaveAttribute('data-done', 'true');
  });

  it('snaps its points like drawing: to the grid, and to an object corner before the grid', () => {
    const t = measureSetup();
    // Off the 10 cm grid by a few centimetres: the points land on it.
    t.click(1.03, 14.02);
    t.click(4.02, 17.97);
    expect(t.status()).toHaveTextContent('Measured: 5.00 m');
    t.after(() => fireEvent.keyDown(t.canvas(), { key: 'Escape' }));
    // Near the corner (14, 4) of the bed "solo": the corner wins over the grid point (14.1, 4.1).
    t.click(14.12, 4.13);
    t.click(13, 4);
    expect(t.status()).toHaveTextContent('Measured: 1.00 m');
  });

  it('shows its lengths in the user unit (cm)', () => {
    const t = measureSetup();
    openPanelTab('view');
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-unit-cm')));
    t.click(1, 14);
    t.click(4, 18);
    expect(t.status()).toHaveTextContent('Measured: 500 cm');
  });

  it('is transient: no operation, nothing pending, no undo step', () => {
    const t = measureSetup();
    const plan = t.state().plan;
    t.click(1, 14);
    t.click(4, 18);
    t.after(() => fireEvent.keyDown(t.canvas(), { key: 'Enter' }));
    expect(t.state().pending).toHaveLength(0);
    expect(t.state().past).toHaveLength(0);
    expect(t.state().plan).toBe(plan);
  });

  it('ends with a tool change, and the measurement is gone when the tool comes back', () => {
    const t = measureSetup();
    t.click(1, 14);
    t.click(4, 18);
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-tool-select')));
    expect(screen.queryByTestId('garden-plan-measure-status')).toBeNull();
    expect(screen.queryByTestId('garden-plan-measure')).toBeNull();
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-tool-measure')));
    expect(screen.queryByTestId('garden-plan-measure')).toBeNull();
  });

  it('has no accessibility violations with a measurement on the plan', async () => {
    const t = measureSetup();
    t.click(1, 14);
    t.click(4, 18);
    await expectNoA11yViolations(document.body, { minImpact: 'serious' });
  });
});

describe('the touch path below md (GP-UX-036/069)', () => {
  it('sets points at the crosshair, takes one back, finishes and clears through the TouchBar', () => {
    restores.push(stubPhone());
    const t = setupEditor();
    const dock = screen.getByTestId('garden-plan-dock');
    t.after(() => fireEvent.click(within(dock).getByTestId('garden-plan-tool-measure')));
    const bar = screen.getByTestId('garden-plan-touchbar');
    expect(screen.getByTestId('garden-plan-crosshair')).toBeInTheDocument();
    const status = () => screen.getByTestId('garden-plan-measure-status');
    expect(status()).toHaveTextContent('"Set point"');

    // The crosshair is the canvas centre: (400, 400) px = model (10, 10).
    t.after(() => fireEvent.click(within(bar).getByTestId('garden-plan-touch-place')));
    expect(status()).toHaveTextContent('Start point set');
    const finish = within(bar).getByTestId('garden-plan-touch-finish');
    expect(finish).toHaveAttribute('aria-disabled', 'true');
    // A second point by a tap of the finger, three metres to the right.
    t.after(() => {
      fireEvent.pointerDown(t.canvas(), pointer({ ...px(13, 10), pointerType: 'touch' }));
      fireEvent.pointerUp(t.canvas(), pointer({ ...px(13, 10), pointerType: 'touch' }));
    });
    expect(status()).toHaveTextContent('Measured: 3.00 m');

    t.after(() => fireEvent.click(within(bar).getByTestId('garden-plan-touch-undo')));
    expect(status()).toHaveTextContent('Start point set');
    t.after(() => {
      fireEvent.pointerDown(t.canvas(), pointer({ ...px(13, 10), pointerType: 'touch' }));
      fireEvent.pointerUp(t.canvas(), pointer({ ...px(13, 10), pointerType: 'touch' }));
    });
    t.after(() => fireEvent.click(within(bar).getByTestId('garden-plan-touch-finish')));
    expect(status()).toHaveTextContent('Measurement done: 3.00 m');
    expect(within(bar).getByTestId('garden-plan-touch-finish')).toHaveAttribute('aria-disabled', 'true');

    const clear = within(bar).getByTestId('garden-plan-touch-cancel');
    expect(clear).toHaveTextContent('Clear');
    t.after(() => fireEvent.click(clear));
    expect(screen.queryByTestId('garden-plan-measure')).toBeNull();
    expect(t.state().pending).toHaveLength(0);
  });
});
