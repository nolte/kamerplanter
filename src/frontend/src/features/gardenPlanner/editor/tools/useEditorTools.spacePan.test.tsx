/**
 * Space + drag pans in every tool (REQ-053 GP-FR-010, #2892), through the real `useEditorTools` hook on a surface
 * that carries its container props the way the editor's canvas does.
 */
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi, type Mock } from 'vitest';
import { HeadlessPlanRenderer } from '../../renderer/HeadlessPlanRenderer';
import { NO_SELECTION, options as renderOptions } from '../../renderer/rendererTestKit';
import type { PlanOperation, Point } from '../../model/types';
import type { PlanTool, SelectionRef, SelectionStack } from '../../state/gardenPlanSlice';
import type { ActionLabel } from './machineTypes';
import { testPlan, VIEWPORT } from './toolTestKit';
import { useEditorTools } from './useEditorTools';

interface Spies {
  onSelect: Mock<(selection: SelectionRef[]) => void>;
  onStack: Mock<(stack: SelectionStack | null) => void>;
  onCommit: Mock<(ops: PlanOperation[], label: ActionLabel) => void>;
  onPan: Mock<(dxPx: number, dyPx: number) => void>;
  onTool: Mock<(tool: PlanTool) => void>;
  onNotice: Mock<(code: string | null) => void>;
  onRequestDelete: Mock<() => void>;
}

const plan = testPlan();
const renderer = new HeadlessPlanRenderer();
renderer.render(plan, VIEWPORT, NO_SELECTION, renderOptions());

function Surface({ tool, spies }: { tool: PlanTool; spies: Spies }) {
  const tools = useEditorTools({
    tool,
    drawShape: 'rect',
    angleStepDeg: 15,
    plan,
    viewport: VIEWPORT,
    renderer,
    selection: [],
    stack: null,
    newBedName: (n) => `Bed ${n}`,
    ...spies,
  });
  return (
    <div
      data-testid="surface"
      tabIndex={0}
      data-pan-modifier={String(tools.panModifier)}
      {...tools.containerProps}
    >
      <button type="button" data-testid="zoom-button">
        +
      </button>
      <div role="menuitem" tabIndex={-1} data-testid="menu-item">
        Lock
      </div>
      <input data-testid="field" />
      <textarea data-testid="area" />
      <div data-testid="editable" contentEditable suppressContentEditableWarning />
      <svg>
        <g data-plan-key="b1" role="button" tabIndex={-1} data-testid="plan-object" />
      </svg>
      <span data-testid="label">Bed 1</span>
    </div>
  );
}

/** Model metres to client pixels: 20 px per metre, model (0, 20) at the top-left; the surface sits at (0, 0). */
const px = ([x, y]: Point) => ({ clientX: x * 20, clientY: (20 - y) * 20 });
const mouse = (point: Point, extra: Record<string, unknown> = {}) => ({
  pointerId: 1,
  pointerType: 'mouse',
  button: 0,
  ...px(point),
  ...extra,
});

let spies: Spies;
beforeEach(() => {
  spies = {
    onSelect: vi.fn(),
    onStack: vi.fn(),
    onCommit: vi.fn(),
    onPan: vi.fn(),
    onTool: vi.fn(),
    onNotice: vi.fn(),
    onRequestDelete: vi.fn(),
  };
});
afterEach(() => {
  cleanup();
});

const surface = () => screen.getByTestId('surface');
const modifierShown = () => surface().getAttribute('data-pan-modifier') === 'true';
/** `fireEvent` answers `false` when a handler called `preventDefault`. */
const pressSpace = (target: Element, extra: Record<string, unknown> = {}) =>
  fireEvent.keyDown(target, { key: ' ', code: 'Space', ...extra });
const releaseSpace = (target: Element = surface()) =>
  fireEvent.keyUp(target, { key: ' ', code: 'Space' });

function drag(from: Point, to: Point, extra: Record<string, unknown> = {}) {
  fireEvent.pointerDown(surface(), mouse(from, extra));
  fireEvent.pointerMove(surface(), mouse(to, extra));
  fireEvent.pointerUp(surface(), mouse(to, extra));
}

describe('Space + drag pans (GP-FR-010)', () => {
  it.each<PlanTool>(['select', 'bed', 'garden_object', 'pan'])(
    'pans with the primary button in the %s tool - no selection, no drawing, no move',
    (tool) => {
      render(<Surface tool={tool} spies={spies} />);
      expect(pressSpace(surface())).toBe(false); // the page does not scroll
      expect(modifierShown()).toBe(true);
      // From the middle of bed b1 (a move in the select tool) to free space (a rectangle in a draw tool).
      drag([4, 4], [16, 16]);
      expect(spies.onPan).toHaveBeenCalledWith(240, -240);
      expect(spies.onSelect).not.toHaveBeenCalled();
      expect(spies.onCommit).not.toHaveBeenCalled();
      expect(spies.onTool).not.toHaveBeenCalled(); // a temporary override: the tool in the store stays
      releaseSpace();
      expect(modifierShown()).toBe(false);
    },
  );

  it('gives the press back to the tool once Space is released', () => {
    render(<Surface tool="select" spies={spies} />);
    pressSpace(surface());
    drag([4, 4], [5, 5]);
    releaseSpace();
    expect(spies.onSelect).not.toHaveBeenCalled();
    fireEvent.pointerDown(surface(), mouse([4, 4]));
    expect(spies.onSelect).toHaveBeenCalledWith([{ entity: 'location', key: 'b1' }]);
  });

  it('draws again in the bed tool once Space is released', () => {
    render(<Surface tool="bed" spies={spies} />);
    pressSpace(surface());
    releaseSpace();
    drag([16, 14], [18, 17]);
    expect(spies.onPan).not.toHaveBeenCalled();
    expect(spies.onCommit).toHaveBeenCalledTimes(1);
  });

  it('keeps the page from scrolling on every key repeat and needs one release', () => {
    render(<Surface tool="select" spies={spies} />);
    expect(pressSpace(surface())).toBe(false);
    expect(pressSpace(surface(), { repeat: true })).toBe(false);
    expect(pressSpace(surface(), { repeat: true })).toBe(false);
    expect(modifierShown()).toBe(true);
    releaseSpace();
    expect(modifierShown()).toBe(false);
    fireEvent.pointerDown(surface(), mouse([4, 4]));
    expect(spies.onSelect).toHaveBeenCalled();
  });

  it('finishes a drag as a pan when Space is released while the button is still down', () => {
    render(<Surface tool="select" spies={spies} />);
    pressSpace(surface());
    fireEvent.pointerDown(surface(), mouse([4, 4]));
    releaseSpace();
    fireEvent.pointerMove(surface(), mouse([6, 4]));
    fireEvent.pointerUp(surface(), mouse([6, 4]));
    expect(spies.onPan).toHaveBeenCalledWith(40, 0);
    expect(spies.onSelect).not.toHaveBeenCalled();
    expect(spies.onCommit).not.toHaveBeenCalled();
  });

  it('forgets a held Space when the window loses the focus (its release never arrives)', () => {
    render(<Surface tool="select" spies={spies} />);
    pressSpace(surface());
    act(() => {
      window.dispatchEvent(new Event('blur'));
    });
    expect(modifierShown()).toBe(false);
    fireEvent.pointerDown(surface(), mouse([4, 4]));
    expect(spies.onSelect).toHaveBeenCalledWith([{ entity: 'location', key: 'b1' }]);
  });

  it('notices the release of Space even when the focus left the canvas meanwhile', () => {
    render(<Surface tool="select" spies={spies} />);
    pressSpace(surface());
    releaseSpace(document.body);
    expect(modifierShown()).toBe(false);
  });

  it('leaves the middle button panning as before', () => {
    render(<Surface tool="bed" spies={spies} />);
    drag([16, 14], [17, 14], { button: 1 });
    expect(spies.onPan).toHaveBeenCalledWith(20, 0);
    expect(spies.onCommit).not.toHaveBeenCalled();
  });

  it('leaves a finger to its own gestures', () => {
    render(<Surface tool="select" spies={spies} />);
    pressSpace(surface());
    fireEvent.pointerDown(surface(), mouse([4, 4], { pointerType: 'touch' }));
    expect(spies.onSelect).toHaveBeenCalledWith([{ entity: 'location', key: 'b1' }]);
  });

  it('is no pan modifier together with Ctrl, Cmd or Alt', () => {
    render(<Surface tool="select" spies={spies} />);
    expect(pressSpace(surface(), { ctrlKey: true })).toBe(true);
    expect(pressSpace(surface(), { altKey: true })).toBe(true);
    expect(modifierShown()).toBe(false);
  });
});

describe('where Space belongs to something else', () => {
  it.each(['field', 'area', 'editable'])('types a space in the %s and pans nothing', (testId) => {
    render(<Surface tool="select" spies={spies} />);
    expect(pressSpace(screen.getByTestId(testId))).toBe(true); // not prevented: the space is typed
    expect(modifierShown()).toBe(false);
    drag([4, 4], [6, 6]);
    expect(spies.onPan).not.toHaveBeenCalled();
    expect(spies.onSelect).toHaveBeenCalled();
  });

  it.each(['zoom-button', 'menu-item'])('leaves Space to the focused %s, which activates it', (testId) => {
    render(<Surface tool="select" spies={spies} />);
    const control = screen.getByTestId(testId);
    control.focus();
    expect(pressSpace(control)).toBe(true); // not swallowed: the browser (or the menu) activates the control
    expect(modifierShown()).toBe(false);
    drag([4, 4], [6, 6]);
    expect(spies.onPan).not.toHaveBeenCalled();
  });

  it('is the pan modifier on a non-interactive part of the canvas', () => {
    render(<Surface tool="select" spies={spies} />);
    expect(pressSpace(screen.getByTestId('label'))).toBe(false);
    expect(modifierShown()).toBe(true);
  });

  it('is the pan modifier on a focused plan object, whose activation then waits for an unused release', () => {
    render(<Surface tool="select" spies={spies} />);
    const object = screen.getByTestId('plan-object');
    const handled: boolean[] = [];
    object.addEventListener('keyup', (event) => handled.push(event.defaultPrevented));
    // Space pressed and released without a drag: the release is free, the object's own handler selects it.
    expect(pressSpace(object)).toBe(false);
    releaseSpace(object);
    // Space that panned: the release is marked handled, the object is not activated by it.
    pressSpace(object);
    drag([4, 4], [6, 6]);
    releaseSpace(object);
    expect(handled).toEqual([false, true]);
    expect(spies.onPan).toHaveBeenCalled();
    expect(spies.onSelect).not.toHaveBeenCalled();
  });
});
