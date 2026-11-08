/**
 * REQ-053 WP 9.14 (#2754, GP-FR-025): Ctrl/Cmd+D duplicates the selection - the same action as the panel button
 * and the item menu, which names the key.
 *
 * Pinned: one duplicate per press, one undo step, the copy selected; the browser's own Ctrl+D (bookmark) is kept
 * closed only while something duplicable is selected; a text field keeps the key; the copy carries no slots or
 * plants (§32.4 Pkt. 8); the menu entry shows the shortcut and declares it (`aria-keyshortcuts`).
 */
import { cleanup, fireEvent, screen, within } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { pointer, px, setupEditor } from './editorTestKit';

afterEach(() => cleanup());

const press = (t: ReturnType<typeof setupEditor>, target: HTMLElement, mods: Record<string, boolean>) =>
  t.after(() => fireEvent.keyDown(target, { key: 'd', ...mods }));

describe('Ctrl/Cmd+D (GP-FR-025)', () => {
  it('duplicates the selected bed as one undo step and selects the copy', () => {
    const t = setupEditor();
    t.click(4, 4);
    const slots = Object.keys(t.state().plan!.slots).length;

    const notPrevented = press(t, t.canvas(), { ctrlKey: true });

    expect(notPrevented).toBe(false); // the browser's "bookmark this page" stays closed
    expect(t.state().past).toHaveLength(1);
    expect(t.state().past[0].label).toBe('pages.gardenPlan.editor.actions.duplicate');
    const [copyKey] = t.selected();
    expect(copyKey).not.toBe('b1');
    expect(t.state().plan!.locations[copyKey].name).toBe('Bed 1 (copy)');
    expect(Object.keys(t.state().plan!.slots)).toHaveLength(slots); // no slot copy (§32.4 Pkt. 8)
  });

  it('works with Cmd on a Mac, and a second press duplicates the copy', () => {
    const t = setupEditor();
    t.click(4, 4);

    press(t, t.canvas(), { metaKey: true });
    press(t, t.canvas(), { metaKey: true });

    expect(t.state().past).toHaveLength(2);
    expect(Object.values(t.state().plan!.locations).filter((l) => l.name.startsWith('Bed 1'))).toHaveLength(3);
  });

  it('duplicates a garden object as well', () => {
    const t = setupEditor();
    t.click(9, 9);

    press(t, t.canvas(), { ctrlKey: true });

    expect(Object.values(t.state().plan!.gardenObjects).filter((o) => o.object_type === 'tree')).toHaveLength(2);
  });

  it('leaves the key to the browser with nothing selected', () => {
    const t = setupEditor();

    const notPrevented = press(t, t.canvas(), { ctrlKey: true });

    expect(notPrevented).toBe(true);
    expect(t.state().past).toHaveLength(0);
  });

  it('leaves the key to a text field and to Ctrl+Shift+D / Alt combinations', () => {
    const t = setupEditor();
    t.click(4, 4);

    press(t, screen.getByTestId('garden-plan-panel-name'), { ctrlKey: true });
    press(t, t.canvas(), { ctrlKey: true, shiftKey: true });
    press(t, t.canvas(), { ctrlKey: true, altKey: true });

    expect(t.state().past).toHaveLength(0);
  });

  it('names the shortcut in the item menu entry', () => {
    const t = setupEditor();
    t.after(() => {
      fireEvent.pointerDown(t.canvas(), pointer({ ...px(4, 4), button: 2 }));
      fireEvent.contextMenu(t.canvas(), { ...px(4, 4) });
    });

    const entry = within(screen.getByRole('menu')).getByRole('menuitem', { name: 'Duplicate' });
    expect(entry).toHaveTextContent('Ctrl/Cmd + D');
    expect(entry).toHaveAttribute('aria-keyshortcuts', 'Control+D Meta+D');
  });

  it('is listed in the keyboard help', () => {
    const t = setupEditor();
    t.after(() => fireEvent.click(screen.getByRole('button', { name: /Keyboard help/ })));

    const help = screen.getByTestId('garden-plan-keyboard-help');
    expect(help).toHaveTextContent('Ctrl + D / Cmd + D');
    expect(help).toHaveTextContent('Duplicate the selection, offset by one grid step.');
  });
});
