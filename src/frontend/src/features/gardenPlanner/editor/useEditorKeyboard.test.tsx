/**
 * Arrow keys of the plan canvas through the real `useEditorKeyboard` hook (REQ-053 GP-FR-010, GP-UX-044, #2892):
 * without anything movable selected they scroll the view, Shift ten times as far; with a selection they move it.
 */
import { renderHook } from '@testing-library/react';
import type { KeyboardEvent as ReactKeyboardEvent } from 'react';
import { describe, expect, it, vi } from 'vitest';
import type { PlanTool, SelectionRef } from '../state/gardenPlanSlice';
import { testPlan } from './tools/toolTestKit';
import { COARSE, SCROLL_STEP_PX, useEditorKeyboard } from './useEditorKeyboard';

function setup(tool: PlanTool = 'select', selection: SelectionRef[] = []) {
  const onPan = vi.fn<(dxPx: number, dyPx: number) => void>();
  const onCommit = vi.fn();
  const { result } = renderHook(() =>
    useEditorKeyboard({
      plan: testPlan(),
      tool,
      selection,
      canvasRef: { current: null },
      singleKeyShortcuts: true,
      stepM: 0.1,
      onCommit,
      onNotice: vi.fn(),
      onPan,
      onHelp: vi.fn(),
    }),
  );
  return { keyboard: result.current, onPan, onCommit };
}

function key(name: string, extra: Partial<KeyboardEvent> & { target?: EventTarget } = {}) {
  const preventDefault = vi.fn();
  const event = {
    key: name,
    shiftKey: false,
    ctrlKey: false,
    metaKey: false,
    altKey: false,
    target: document.body,
    preventDefault,
    ...extra,
  } as unknown as ReactKeyboardEvent<HTMLElement>;
  return { event, preventDefault };
}

describe('arrow keys without a movable selection scroll the view (GP-FR-010)', () => {
  it('scrolls one step per press', () => {
    const t = setup();
    expect(t.keyboard.handleKey(key('ArrowRight').event)).toBe(true);
    expect(t.onPan).toHaveBeenLastCalledWith(-SCROLL_STEP_PX, 0);
    t.keyboard.handleKey(key('ArrowUp').event);
    expect(t.onPan).toHaveBeenLastCalledWith(0, SCROLL_STEP_PX);
  });

  it.each([
    ['ArrowLeft', 400, 0],
    ['ArrowRight', -400, 0],
    ['ArrowUp', 0, 400],
    ['ArrowDown', 0, -400],
  ] as const)('Shift + %s scrolls ten steps', (name, dx, dy) => {
    const t = setup();
    const { event, preventDefault } = key(name, { shiftKey: true });
    expect(t.keyboard.handleKey(event)).toBe(true);
    expect(preventDefault).toHaveBeenCalled();
    expect(COARSE).toBe(10);
    expect(t.onPan).toHaveBeenCalledWith(dx, dy);
    expect(Math.abs(dx + dy)).toBe(SCROLL_STEP_PX * COARSE);
    expect(t.onCommit).not.toHaveBeenCalled();
  });

  it('scrolls ten steps in another tool even with a selection (nothing there is movable)', () => {
    const t = setup('pan', [{ entity: 'location', key: 'b1' }]);
    t.keyboard.handleKey(key('ArrowRight', { shiftKey: true }).event);
    expect(t.onPan).toHaveBeenCalledWith(-400, 0);
    expect(t.onCommit).not.toHaveBeenCalled();
  });

  it('moves a movable selection ten grid steps instead of scrolling', () => {
    const t = setup('select', [{ entity: 'location', key: 'solo' }]);
    t.keyboard.handleKey(key('ArrowRight', { shiftKey: true }).event);
    expect(t.onPan).not.toHaveBeenCalled();
    expect(t.onCommit).toHaveBeenCalledTimes(1);
    const [ops, label] = t.onCommit.mock.calls[0];
    expect(label).toBe('move');
    // `solo` sits at x 14; ten grid steps of 0.1 m take it to x 15.
    expect(ops).toEqual([
      expect.objectContaining({
        op: 'update_geometry',
        key: 'solo',
        geometry: expect.objectContaining({ origin: [15, 2] }),
      }),
    ]);
  });

  it('leaves an arrow typed into a field to the field', () => {
    const t = setup();
    const field = document.createElement('input');
    expect(t.keyboard.handleKey(key('ArrowRight', { shiftKey: true, target: field }).event)).toBe(false);
    expect(t.onPan).not.toHaveBeenCalled();
  });

  it('does not take Space: held down it is the pan modifier of the tools, not a scroll key', () => {
    const t = setup();
    const { event, preventDefault } = key(' ');
    expect(t.keyboard.handleKey(event)).toBe(false);
    expect(preventDefault).not.toHaveBeenCalled();
    expect(t.onPan).not.toHaveBeenCalled();
  });
});
