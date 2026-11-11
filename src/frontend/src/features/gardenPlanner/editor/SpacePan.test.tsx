/**
 * Space + drag in the assembled editor (REQ-053 GP-FR-010, #2892): the canvas takes Space as the pan modifier, shows
 * the grab cursor while it is held, pans in the active tool without touching the selection or the tool, and leaves
 * Space on the controls around the plan alone.
 */
import { cleanup, fireEvent, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { setTool } from '../state/gardenPlanSlice';
import { pointer, px, setupEditor } from './editorTestKit';

afterEach(() => {
  cleanup();
});

const cursorOf = (element: HTMLElement) => window.getComputedStyle(element).cursor;

describe('Space + drag in the editor (GP-FR-010)', () => {
  it('pans in the select tool with the grab cursor; selection and tool stay', () => {
    const t = setupEditor();
    const canvas = t.canvas();
    const geometryBefore = t.state().plan?.locations.b1.geometry;
    canvas.focus();
    expect(cursorOf(canvas)).toBe('default');
    t.after(() => expect(fireEvent.keyDown(canvas, { key: ' ', code: 'Space' })).toBe(false));
    expect(cursorOf(canvas)).toBe('grab');
    // Bed b1 lies at (3, 3)-(5, 5): without Space the press would select it and the drag would move it.
    t.after(() => {
      fireEvent.pointerDown(canvas, pointer(px(4, 4)));
      fireEvent.pointerMove(canvas, pointer(px(6, 4)));
      fireEvent.pointerUp(canvas, pointer(px(6, 4)));
      fireEvent.click(canvas, px(6, 4));
    });
    expect(t.onPan).toHaveBeenCalledWith(80, 0);
    expect(t.selected()).toEqual([]);
    expect(t.state().tool).toBe('select');
    expect(t.state().plan?.locations.b1.geometry).toEqual(geometryBefore);
    t.after(() => fireEvent.keyUp(canvas, { key: ' ', code: 'Space' }));
    expect(cursorOf(canvas)).toBe('default');
    // Space released: the press is the tool's again.
    t.click(4, 4);
    expect(t.selected()).toEqual(['b1']);
  });

  it('pans in the bed tool instead of drawing a bed', () => {
    const t = setupEditor();
    t.after(() => t.store.dispatch(setTool('bed')));
    const canvas = t.canvas();
    const before = Object.keys(t.state().plan!.locations).length;
    t.after(() => fireEvent.keyDown(canvas, { key: ' ', code: 'Space' }));
    t.after(() => {
      fireEvent.pointerDown(canvas, pointer(px(16, 14)));
      fireEvent.pointerMove(canvas, pointer(px(18, 17)));
      fireEvent.pointerUp(canvas, pointer(px(18, 17)));
    });
    t.after(() => fireEvent.keyUp(canvas, { key: ' ', code: 'Space' }));
    expect(t.onPan).toHaveBeenCalled();
    expect(Object.keys(t.state().plan!.locations)).toHaveLength(before);
    expect(t.state().tool).toBe('bed');
  });

  it('leaves Space on a zoom button to the button', () => {
    const t = setupEditor();
    const button = screen.getByTestId('garden-plan-zoom-in');
    button.focus();
    expect(fireEvent.keyDown(button, { key: ' ', code: 'Space' })).toBe(true);
    expect(cursorOf(t.canvas())).toBe('default');
    t.after(() => {
      fireEvent.pointerDown(t.canvas(), pointer(px(4, 4)));
      fireEvent.pointerUp(t.canvas(), pointer(px(4, 4)));
    });
    expect(t.onPan).not.toHaveBeenCalled();
    expect(t.selected()).toEqual(['b1']);
  });
});
