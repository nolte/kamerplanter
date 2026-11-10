/**
 * The vertical tool rail of the plan editor (REQ-053 §17.3, GP-UX-001/066/069, AC-3/AC-4/AC-9; WP 10.4 #2825):
 * the tools of GP-UX-001 (at most 8 on the top level), their sub-menus, the selection group that exists only with
 * a selection, the roving tabindex of the WAI-ARIA tool bar, and the touch path below md.
 */
import { act, cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ThemeContextProvider } from '@/theme';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { EditorToolbar, type ToolbarSelectionGroup } from './EditorToolbar';
import { chooseToolMenuEntry, setupEditor, stubPhone } from './editorTestKit';
import type { ToolbarOrientation } from './useRovingToolbar';

const restores: (() => void)[] = [];
afterEach(() => {
  cleanup();
  while (restores.length) restores.pop()?.();
  vi.clearAllMocks();
});

const group = (): ToolbarSelectionGroup => ({
  angleStep: 15,
  onAngleStep: vi.fn(),
  onDelete: vi.fn(),
  align: { canAlign: true, canDistribute: false, onAlign: vi.fn(), onDistribute: vi.fn() },
});

function renderBar(
  options: {
    orientation?: ToolbarOrientation;
    selectionGroup?: ToolbarSelectionGroup | null;
    tool?: 'select' | 'bed';
  } = {},
) {
  const onTool = vi.fn();
  const onTemplate = vi.fn();
  const onAddWithDimensions = vi.fn();
  render(
    <ThemeContextProvider>
      <button type="button" data-testid="before">
        before
      </button>
      <EditorToolbar
        orientation={options.orientation ?? 'vertical'}
        tool={options.tool ?? 'select'}
        onTool={onTool}
        drawShape="rect"
        onDrawShape={vi.fn()}
        draftPoints={0}
        onFinishDraw={vi.fn()}
        onCancelDraw={vi.fn()}
        vertexPicked={false}
        canDeleteVertex={false}
        onDeleteVertex={vi.fn()}
        onInsertVertex={vi.fn()}
        templateActive={false}
        onTemplate={onTemplate}
        onAddWithDimensions={onAddWithDimensions}
        selectionGroup={options.selectionGroup ?? null}
      />
    </ThemeContextProvider>,
  );
  const bar = screen.getByRole('toolbar', { name: 'Garden plan tools' });
  return { bar, onTool, onTemplate, onAddWithDimensions };
}

/** The top-level tools: the toggles of the group "Tool" (the sub-menu buttons are no tools). */
const topLevelTools = (bar: HTMLElement) =>
  within(within(bar).getByRole('group', { name: 'Tool' })).getAllByRole('button', { pressed: undefined }).filter(
    (button) => button.hasAttribute('aria-pressed'),
  );

const tabStops = (bar: HTMLElement) =>
  Array.from(bar.querySelectorAll<HTMLButtonElement>('button')).filter((button) => button.tabIndex === 0);

describe('the tool rail (GP-UX-066, AC-3)', () => {
  it('is a vertical tool bar with the tools of GP-UX-001 on its top level, at most 8, each named and 48 px', () => {
    const { bar } = renderBar();
    expect(bar).toHaveAttribute('aria-orientation', 'vertical');
    const tools = topLevelTools(bar);
    expect(tools.map((button) => button.getAttribute('data-testid'))).toEqual([
      'garden-plan-tool-select',
      'garden-plan-tool-pan',
      'garden-plan-tool-bed',
      'garden-plan-tool-garden_object',
    ]);
    expect(tools.length).toBeLessThanOrEqual(8);
    // Hand/Pan is the tool #2820 calls "Verschieben".
    expect(screen.getByTestId('garden-plan-tool-pan')).toHaveTextContent('Pan');
    for (const button of bar.querySelectorAll('button')) {
      expect(button).toHaveStyle({ minHeight: '48px', minWidth: '48px' });
      expect(button).toHaveAccessibleName();
    }
  });

  it('names a verb in every tooltip (GP-UX-010)', async () => {
    renderBar();
    fireEvent.mouseOver(screen.getByTestId('garden-plan-tool-bed'));
    expect(await screen.findByRole('tooltip')).toHaveTextContent('Draw a new bed on the plan');
  });

  it('puts "From template" and "Add with dimensions" into the sub-menus of Bed and Garden object', () => {
    const { onTemplate, onAddWithDimensions } = renderBar();
    const bedMenu = screen.getByTestId('garden-plan-tool-bed-menu');
    expect(bedMenu).toHaveAttribute('aria-haspopup', 'menu');
    expect(bedMenu).toHaveAttribute('aria-expanded', 'false');
    // Not on the top level.
    expect(screen.queryByTestId('garden-plan-tool-template')).toBeNull();
    expect(screen.queryByTestId('garden-plan-add-with-dimensions')).toBeNull();

    fireEvent.click(bedMenu);
    expect(bedMenu).toHaveAttribute('aria-expanded', 'true');
    const menu = screen.getByTestId('garden-plan-tool-bed-submenu');
    expect(within(menu).getByRole('menu', { name: 'Bed tools' })).toBeInTheDocument();
    expect(within(menu).getByTestId('garden-plan-tool-template')).toHaveAttribute('role', 'menuitemcheckbox');
    fireEvent.click(within(menu).getByTestId('garden-plan-tool-template'));
    expect(onTemplate).toHaveBeenCalledTimes(1);

    chooseToolMenuEntry('bed', 'garden-plan-add-with-dimensions');
    expect(onAddWithDimensions).toHaveBeenLastCalledWith('bed');
    chooseToolMenuEntry('garden_object', 'garden-plan-add-with-dimensions-object');
    expect(onAddWithDimensions).toHaveBeenLastCalledWith('garden_object');
  });

  it('renders no selection group without a selection - not even as disabled buttons (AC-4)', () => {
    renderBar({ selectionGroup: null });
    expect(screen.queryByTestId('garden-plan-selection-group')).toBeNull();
    expect(screen.queryByTestId('garden-plan-delete-button')).toBeNull();
    expect(screen.queryByTestId('garden-plan-align-button')).toBeNull();
    expect(screen.queryByTestId('garden-plan-angle-15')).toBeNull();
  });

  it('renders rotate (15/45/90), align and delete with a selection', () => {
    const selection = group();
    renderBar({ selectionGroup: selection });
    const box = screen.getByTestId('garden-plan-selection-group');
    expect(box).toHaveAttribute('role', 'group');
    expect(box).toHaveAccessibleName('Edit selection');
    for (const step of [15, 45, 90]) expect(within(box).getByTestId(`garden-plan-angle-${step}`)).toBeInTheDocument();
    expect(within(box).getByTestId('garden-plan-angle-15')).toHaveAttribute('aria-pressed', 'true');
    fireEvent.click(within(box).getByTestId('garden-plan-angle-90'));
    expect(selection.onAngleStep).toHaveBeenCalledWith(90);
    fireEvent.click(within(box).getByTestId('garden-plan-delete-button'));
    expect(selection.onDelete).toHaveBeenCalledTimes(1);
    expect(within(box).getByTestId('garden-plan-align-button')).toHaveAccessibleName('Align');
  });

  it('has no accessibility violations, with and without a selection and with a sub-menu open', async () => {
    const { bar } = renderBar();
    await expectNoA11yViolations(bar);
    cleanup();
    const second = renderBar({ selectionGroup: group(), tool: 'bed' });
    await expectNoA11yViolations(second.bar);
    fireEvent.click(screen.getByTestId('garden-plan-tool-bed-menu'));
    await expectNoA11yViolations(document.body, { minImpact: 'serious' });
  });
});

describe('keyboard: roving tabindex (GP-UX-066 like GP-NFR-068)', () => {
  it('is one tab stop - the pressed tool - and the arrow keys, Home and End move inside', () => {
    const { bar } = renderBar({ selectionGroup: group() });
    expect(tabStops(bar)).toEqual([screen.getByTestId('garden-plan-tool-select')]);

    const select = screen.getByTestId('garden-plan-tool-select');
    act(() => select.focus());
    fireEvent.keyDown(select, { key: 'ArrowDown' });
    expect(screen.getByTestId('garden-plan-tool-pan')).toHaveFocus();
    expect(tabStops(bar)).toEqual([screen.getByTestId('garden-plan-tool-pan')]);
    fireEvent.keyDown(document.activeElement!, { key: 'ArrowDown' });
    expect(screen.getByTestId('garden-plan-tool-bed')).toHaveFocus();
    fireEvent.keyDown(document.activeElement!, { key: 'ArrowDown' });
    expect(screen.getByTestId('garden-plan-tool-bed-menu')).toHaveFocus();
    fireEvent.keyDown(document.activeElement!, { key: 'ArrowUp' });
    expect(screen.getByTestId('garden-plan-tool-bed')).toHaveFocus();

    fireEvent.keyDown(document.activeElement!, { key: 'End' });
    expect(screen.getByTestId('garden-plan-delete-button')).toHaveFocus();
    // Past the end it wraps to the first.
    fireEvent.keyDown(document.activeElement!, { key: 'ArrowDown' });
    expect(select).toHaveFocus();
    fireEvent.keyDown(select, { key: 'ArrowUp' });
    expect(screen.getByTestId('garden-plan-delete-button')).toHaveFocus();
    fireEvent.keyDown(document.activeElement!, { key: 'Home' });
    expect(select).toHaveFocus();
    // The other axis does nothing on a vertical bar.
    fireEvent.keyDown(select, { key: 'ArrowRight' });
    expect(select).toHaveFocus();
    expect(tabStops(bar)).toHaveLength(1);
  });

  it('keeps the last focused control as the tab stop when the focus comes back', () => {
    const { bar } = renderBar();
    const pan = screen.getByTestId('garden-plan-tool-pan');
    act(() => screen.getByTestId('garden-plan-tool-select').focus());
    fireEvent.keyDown(document.activeElement!, { key: 'ArrowDown' });
    expect(pan).toHaveFocus();
    act(() => screen.getByTestId('before').focus());
    expect(tabStops(bar)).toEqual([pan]);
  });

  it('runs on the left/right arrows where the bar is horizontal (below md)', () => {
    const { bar } = renderBar({ orientation: 'horizontal' });
    expect(bar).toHaveAttribute('aria-orientation', 'horizontal');
    const select = screen.getByTestId('garden-plan-tool-select');
    act(() => select.focus());
    fireEvent.keyDown(select, { key: 'ArrowRight' });
    expect(screen.getByTestId('garden-plan-tool-pan')).toHaveFocus();
    fireEvent.keyDown(document.activeElement!, { key: 'ArrowLeft' });
    expect(select).toHaveFocus();
    fireEvent.keyDown(select, { key: 'ArrowDown' });
    expect(select).toHaveFocus();
  });
});

describe('in the editor (WP 10.4)', () => {
  it('stands as a rail left of the canvas and adds the selection group only while something is selected', () => {
    const t = setupEditor();
    const bar = screen.getByRole('toolbar', { name: 'Garden plan tools' });
    expect(bar).toHaveAttribute('aria-orientation', 'vertical');
    const area = screen.getByTestId('garden-plan-canvas-area');
    // The rail and the canvas share one row; the rail comes first (left, and first in the tab order).
    expect(bar.compareDocumentPosition(area) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(area.parentElement).toBe(bar.parentElement?.parentElement);

    expect(screen.queryByTestId('garden-plan-selection-group')).toBeNull();
    t.click(15, 3);
    expect(t.selected()).toEqual(['solo']);
    expect(within(bar).getByTestId('garden-plan-selection-group')).toBeInTheDocument();
    t.after(() => fireEvent.keyDown(t.canvas(), { key: 'Escape' }));
    expect(t.selected()).toEqual([]);
    expect(screen.queryByTestId('garden-plan-selection-group')).toBeNull();
  });

  it('keeps the arrow keys of the rail away from the plan: they move the focus, not the selection', () => {
    const t = setupEditor();
    t.click(15, 3);
    const before = t.state().plan!.locations.solo.geometry;
    const select = screen.getByTestId('garden-plan-tool-select');
    act(() => select.focus());
    t.after(() => fireEvent.keyDown(select, { key: 'ArrowDown' }));
    expect(screen.getByTestId('garden-plan-tool-pan')).toHaveFocus();
    expect(t.state().plan!.locations.solo.geometry).toEqual(before);
    expect(t.state().pending).toHaveLength(0);
  });

  it('opens "Add with dimensions" for a garden object from the sub-menu of Garden object', () => {
    const t = setupEditor();
    t.after(() => chooseToolMenuEntry('garden_object', 'garden-plan-add-with-dimensions-object'));
    expect(screen.getByTestId('garden-plan-add-dialog')).toBeInTheDocument();
    expect(screen.getByTestId('garden-plan-add-kind-object')).toHaveAttribute('aria-pressed', 'true');
  });

  it('below md the same bar docks at the bottom next to the TouchBar (GP-UX-069, AC-9)', () => {
    restores.push(stubPhone());
    setupEditor();
    const dock = screen.getByTestId('garden-plan-dock');
    const bar = within(dock).getByRole('toolbar', { name: 'Garden plan tools' });
    expect(bar).toHaveAttribute('aria-orientation', 'horizontal');
    expect(within(dock).getByTestId('garden-plan-touchbar')).toBeInTheDocument();
    // One tool bar on the page, not a second layout path.
    expect(screen.getAllByTestId('garden-plan-toolbar')).toHaveLength(1);
    // Every target of the dock is at least 48 px high (a minimum height, or a fixed one for the undo/redo icons).
    const heightOf = (button: HTMLElement) => {
      const style = getComputedStyle(button);
      return Math.max(parseFloat(style.minHeight) || 0, parseFloat(style.height) || 0);
    };
    const small = within(dock)
      .getAllByRole('button')
      .filter((button) => heightOf(button) < 48)
      .map((button) => button.getAttribute('data-testid'));
    expect(small).toEqual([]);
  });
});
