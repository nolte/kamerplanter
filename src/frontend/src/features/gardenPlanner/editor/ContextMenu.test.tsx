import { cleanup, fireEvent, screen, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { pointer, px, setupEditor } from './editorTestKit';

afterEach(() => cleanup());

const rightClick = (t: ReturnType<typeof setupEditor>, x: number, y: number, type = 'mouse') =>
  t.after(() => {
    fireEvent.pointerDown(t.canvas(), pointer({ ...px(x, y), pointerType: type, button: 2 }));
    return fireEvent.contextMenu(t.canvas(), { ...px(x, y) });
  });

describe('context menu (GP-FR-027, GP-UX-040)', () => {
  it('opens at a right click on a bed with the actions, and selects the bed', () => {
    const onOpenLocation = vi.fn();
    const t = setupEditor({ onOpenLocation });
    // The right button does not start a gesture: the menu event alone selects.
    const notPrevented = rightClick(t, 4, 4);
    expect(notPrevented).toBe(false); // the browser menu is suppressed
    expect(t.selected()).toEqual(['b1']);
    const menu = screen.getByRole('menu', { name: 'Actions for the selection' });
    for (const name of [
      'Edit',
      'Duplicate',
      'Plant it',
      'Bring to front',
      'Send to back',
      'Lock',
      'Delete',
    ]) {
      expect(within(menu).getByRole('menuitem', { name })).toBeInTheDocument();
    }
    for (const item of within(menu).getAllByRole('menuitem')) {
      expect(item).toHaveStyle({ minHeight: '48px' });
    }
  });

  it('runs the chosen action and closes', () => {
    const t = setupEditor();
    rightClick(t, 4, 4);
    t.after(() => fireEvent.click(screen.getByRole('menuitem', { name: 'Duplicate' })));
    expect(t.state().past).toHaveLength(1);
    expect(screen.queryByRole('menu')).toBeNull();
  });

  it('locks and unlocks from the menu, the entry names the state', () => {
    const t = setupEditor();
    rightClick(t, 4, 4);
    t.after(() => fireEvent.click(screen.getByRole('menuitem', { name: 'Lock' })));
    expect(t.state().plan!.locations.b1.locked).toBe(true);
    rightClick(t, 4, 4);
    expect(screen.getByRole('menuitem', { name: 'Unlock' })).toBeInTheDocument();
  });

  it('delete goes through the confirmation', () => {
    const t = setupEditor();
    rightClick(t, 4, 4);
    t.after(() => fireEvent.click(screen.getByRole('menuitem', { name: 'Delete' })));
    expect(screen.getByTestId('confirm-dialog')).toBeInTheDocument();
    expect(t.state().plan!.locations.b1).toBeDefined();
  });

  it('keeps a multi-selection when the right click lands on a selected object', () => {
    const t = setupEditor();
    t.click(4, 4);
    t.click(15, 3, { shiftKey: true });
    rightClick(t, 4, 4);
    expect(t.selected()).toHaveLength(2);
  });

  it('opens nothing over empty ground', () => {
    const t = setupEditor();
    rightClick(t, 18, 18);
    expect(screen.queryByRole('menu')).toBeNull();
  });

  it('has no menu for a finger: the long press is the move gesture, "⋯" opens the menu', () => {
    const t = setupEditor();
    const notPrevented = rightClick(t, 4, 4, 'touch');
    expect(notPrevented).toBe(false);
    expect(screen.queryByRole('menu')).toBeNull();
    t.click(4, 4);
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-panel-more')));
    expect(screen.getByRole('menu', { name: 'Actions for the selection' })).toBeInTheDocument();
  });

  it('has no accessibility violations while open', async () => {
    const t = setupEditor();
    rightClick(t, 4, 4);
    await expectNoA11yViolations(document.body);
  });
});

describe('overflow menu (GP-UX-052)', () => {
  it('selects everything that can be selected', () => {
    const t = setupEditor();
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-overflow')));
    t.after(() => fireEvent.click(screen.getByRole('menuitem', { name: 'Select all' })));
    // The locked bed is excluded (GP-FR-156).
    expect(t.selected()).not.toContain('lock');
    expect(t.selected()).toContain('b1');
  });
});
