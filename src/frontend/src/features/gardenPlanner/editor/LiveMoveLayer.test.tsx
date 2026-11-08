import { act, cleanup, fireEvent, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { pointer, px, setupEditor } from './editorTestKit';

// Counts the toolbar's renders: it stands for the editor's heavy chrome (toolbar, panels, lists).
const toolbarRenders = vi.hoisted(() => ({ count: 0 }));
vi.mock('./EditorToolbar', async (importOriginal) => {
  const original = await importOriginal<typeof import('./EditorToolbar')>();
  return {
    ...original,
    EditorToolbar: (props: Parameters<typeof original.EditorToolbar>[0]) => {
      toolbarRenders.count += 1;
      return original.EditorToolbar(props);
    },
  };
});

afterEach(cleanup);

describe('a move re-renders only the live layer (GP-NFR-011, GP-NFR-033)', () => {
  it('follows every pointer move with the ghost and its size, without rendering the editor again', () => {
    const t = setupEditor();
    t.click(11, 11); // the area: a large rect, so its handles show
    expect(screen.queryAllByTestId(/garden-plan-handle-/).length).toBeGreaterThan(0);
    fireEvent.pointerDown(t.canvas(), pointer(px(11, 11))); // the press is the last editor render before the release
    const rendersAtStart = toolbarRenders.count;
    fireEvent.pointerMove(t.canvas(), pointer(px(11, 11.1))); // the move begins - live, too
    const ghostY = () => screen.getAllByTestId('garden-plan-dimension')[0].getAttribute('y');
    const before = ghostY();
    // The handles are hidden while the selection moves.
    expect(screen.queryAllByTestId(/garden-plan-handle-/)).toEqual([]);
    for (let i = 1; i <= 10; i += 1) fireEvent.pointerMove(t.canvas(), pointer(px(11, 11.1 + i * 0.04)));
    expect(toolbarRenders.count).toBe(rendersAtStart);
    expect(ghostY()).not.toBe(before); // the size label moved with the ghost
    expect(t.renderer.dragPreview?.key).toBe('area');
    fireEvent.pointerUp(t.canvas(), pointer(px(11, 11.5)));
    t.rerender();
    expect(toolbarRenders.count).toBeGreaterThan(rendersAtStart); // the release renders the editor once more
    expect(t.state().past).toHaveLength(1);
    expect(screen.queryAllByTestId(/garden-plan-handle-/).length).toBeGreaterThan(0);
  });

  it('measures a gesture from where the canvas was at the press: a layout shift does not make the object jump', () => {
    const t = setupEditor();
    t.click(11, 11);
    fireEvent.pointerDown(t.canvas(), pointer(px(11, 11)));
    // Something opens above the canvas while the pointer is down (a notice, a sheet): the canvas moves 176 px down.
    const canvas = t.canvas();
    const rect = canvas.getBoundingClientRect();
    vi.spyOn(canvas, 'getBoundingClientRect').mockReturnValue({ top: rect.top + 176, y: rect.y + 176, bottom: rect.bottom + 176, left: rect.left, right: rect.right, width: rect.width, height: rect.height, x: rect.x, toJSON: () => ({}) });
    fireEvent.pointerMove(canvas, pointer(px(11, 11.2)));
    fireEvent.pointerUp(canvas, pointer(px(11, 11.5)));
    t.rerender();
    // The area (2, 2) moved by what the last move did - 0.2 m - not by the 4.4 m of the shift.
    expect(t.state().plan!.locations.area.geometry).toMatchObject({ origin: [2, 2.2] });
  });

  it('drops the ghost when the tool is switched in the middle of a move', () => {
    const t = setupEditor();
    t.click(11, 11);
    fireEvent.pointerDown(t.canvas(), pointer(px(11, 11)));
    fireEvent.pointerMove(t.canvas(), pointer(px(11, 11.3)));
    expect(screen.queryAllByTestId('garden-plan-ghost').length).toBeGreaterThan(0);
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-tool-bed')));
    expect(screen.queryAllByTestId('garden-plan-ghost')).toEqual([]);
  });

  /** Puts the canvas `dy` px lower on screen than where jsdom draws it (0, 0). */
  const canvasAt = (canvas: HTMLElement, dy: number) =>
    vi.spyOn(canvas, 'getBoundingClientRect').mockReturnValue({ top: dy, y: dy, bottom: 800 + dy, left: 0, right: 800, width: 800, height: 800, x: 0, toJSON: () => ({}) });

  it('follows a scroll while the pointer is down: the pointer then points at another part of the plan', () => {
    const t = setupEditor();
    t.click(11, 11);
    fireEvent.pointerDown(t.canvas(), pointer(px(11, 11)));
    // The page scrolls 40 px (1 m at 40 px/m): the plan moves up under the pointer that stays where it is.
    document.documentElement.scrollTop = 40;
    const moved = canvasAt(t.canvas(), -40);
    act(() => {
      document.dispatchEvent(new Event('scroll'));
    });
    fireEvent.pointerMove(t.canvas(), pointer(px(11, 11.2)));
    fireEvent.pointerUp(t.canvas(), pointer(px(11, 11.2)));
    moved.mockRestore();
    t.rerender();
    document.documentElement.scrollTop = 0;
    // 0.2 m up by the pointer, 1 m down by the scroll.
    expect(t.state().plan!.locations.area.geometry).toMatchObject({ origin: [2, 1.2] });
  });

  it('does not follow a scroll offset that leaves the canvas where it is on screen (scroll anchoring)', () => {
    const t = setupEditor();
    t.click(11, 11);
    fireEvent.pointerDown(t.canvas(), pointer(px(11, 11)));
    // A notice opens above the canvas and scroll anchoring scrolls the page by its 176 px: the canvas stays put.
    document.documentElement.scrollTop = 176;
    act(() => {
      document.dispatchEvent(new Event('scroll'));
    });
    fireEvent.pointerMove(t.canvas(), pointer(px(11, 11.2)));
    fireEvent.pointerUp(t.canvas(), pointer(px(11, 11.2)));
    t.rerender();
    document.documentElement.scrollTop = 0;
    // Only the 0.2 m of the pointer, not the 4.4 m of the anchoring scroll.
    expect(t.state().plan!.locations.area.geometry).toMatchObject({ origin: [2, 2.2] });
  });

  it('does not follow the page scrolling under a canvas in a fixed box', () => {
    const t = setupEditor();
    t.click(11, 11);
    fireEvent.pointerDown(t.canvas(), pointer(px(11, 11)));
    // An ancestor scrolls 80 px, but the canvas sits in a fixed box: it has not moved on screen.
    const scroller = t.canvas().parentElement!;
    scroller.scrollTop = 80;
    act(() => {
      scroller.dispatchEvent(new Event('scroll'));
    });
    fireEvent.pointerMove(t.canvas(), pointer(px(11, 11.2)));
    fireEvent.pointerUp(t.canvas(), pointer(px(11, 11.2)));
    t.rerender();
    expect(t.state().plan!.locations.area.geometry).toMatchObject({ origin: [2, 2.2] });
  });

  it('ends the press with Escape: its scroll listener does not outlive the gesture', () => {
    const t = setupEditor();
    t.click(11, 11);
    const added = vi.spyOn(window, 'addEventListener');
    const removed = vi.spyOn(window, 'removeEventListener');
    fireEvent.pointerDown(t.canvas(), pointer(px(11, 11)));
    fireEvent.pointerMove(t.canvas(), pointer(px(11, 11.3)));
    const listener = added.mock.calls.find(([type]) => type === 'scroll')?.[1];
    expect(listener).toBeDefined();
    fireEvent.keyDown(t.canvas(), { key: 'Escape' });
    expect(removed.mock.calls.some(([type, fn]) => type === 'scroll' && fn === listener)).toBe(true);
    added.mockRestore();
    removed.mockRestore();
  });
});
