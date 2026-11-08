import { cleanup, fireEvent, screen } from '@testing-library/react';
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
});
