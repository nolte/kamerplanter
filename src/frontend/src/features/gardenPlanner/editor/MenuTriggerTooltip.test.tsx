/**
 * The tooltip of a menu button in the editor (REQ-053 §17.3, GP-UX-010/066, AC-9/AC-15, #2904): never over its
 * open menu, and not brought back by the focus the closing menu hands back or by the pointer that pressed the
 * button - on the phone the overflow's "More" tooltip covered the bottom sheet's tabs and close button.
 *
 * jsdom knows no `:focus-visible`; the keyboard cases stub it, as a browser reports it after a key press.
 */
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ThemeContextProvider } from '@/theme';
import { EditorHeaderActions } from './EditorHeaderActions';
import { EditorToolbar } from './EditorToolbar';
import { setupEditor } from './editorTestKit';

const restores: (() => void)[] = [];
afterEach(() => {
  cleanup();
  while (restores.length) restores.pop()?.();
  vi.clearAllMocks();
});

/** A browser after a key press: the focused element matches `:focus-visible`. */
function stubFocusVisible(): () => void {
  const original = Element.prototype.matches;
  const spy = vi.spyOn(Element.prototype, 'matches').mockImplementation(function (
    this: Element,
    selector: string,
  ) {
    return selector === ':focus-visible' ? true : original.call(this, selector);
  });
  return () => spy.mockRestore();
}

/** Longer than the tooltip's enter delay (100 ms): a tooltip that would open has opened by then. */
const pastEnterDelay = () => act(() => new Promise<void>((resolve) => setTimeout(resolve, 250)));

const tooltipShown = () => screen.queryByRole('tooltip');

function renderOverflow() {
  const onEntry = vi.fn();
  render(
    <ThemeContextProvider>
      <button type="button" data-testid="elsewhere">
        elsewhere
      </button>
      <EditorHeaderActions actions={[{ id: 'entry', label: 'Entry', onClick: onEntry }]} />
    </ThemeContextProvider>,
  );
  return { button: screen.getByTestId('garden-plan-overflow'), onEntry };
}

describe('the overflow "⋮" tooltip (#2904)', () => {
  it('is not shown while the menu is open, nor by the focus it hands back after Escape', async () => {
    restores.push(stubFocusVisible());
    const { button } = renderOverflow();
    act(() => button.focus());
    expect(await screen.findByRole('tooltip')).toHaveTextContent('More');

    fireEvent.click(button);
    expect(button).toHaveAttribute('aria-expanded', 'true');
    await waitFor(() => expect(tooltipShown()).toBeNull());

    fireEvent.keyDown(screen.getByRole('menu'), { key: 'Escape' });
    await waitFor(() => expect(button).toHaveFocus());
    expect(button).toHaveAttribute('aria-expanded', 'false');
    await pastEnterDelay();
    expect(tooltipShown()).toBeNull();

    // Once the focus left and came back, the button names itself again.
    act(() => screen.getByTestId('elsewhere').focus());
    act(() => button.focus());
    expect(await screen.findByRole('tooltip')).toHaveTextContent('More');
  });

  it('is not shown by the resting pointer after an entry closed the menu, only once the pointer moves', async () => {
    const { button, onEntry } = renderOverflow();
    fireEvent.mouseOver(button);
    expect(await screen.findByRole('tooltip')).toHaveTextContent('More');

    fireEvent.pointerDown(button, { clientX: 10, clientY: 10, pointerType: 'mouse' });
    fireEvent.click(button);
    await waitFor(() => expect(tooltipShown()).toBeNull());
    fireEvent.click(within(screen.getByRole('menu')).getByText('Entry'));
    expect(onEntry).toHaveBeenCalledTimes(1);
    expect(button).toHaveAttribute('aria-expanded', 'false');

    // The backdrop is gone: the pointer that never moved is "over" the button again.
    fireEvent.mouseOver(button);
    fireEvent.pointerMove(button, { clientX: 10, clientY: 10, pointerType: 'mouse' });
    await pastEnterDelay();
    expect(tooltipShown()).toBeNull();

    // A pointer that really moves over the button is a hover of its own.
    fireEvent.pointerMove(button, { clientX: 14, clientY: 11, pointerType: 'mouse' });
    expect(await screen.findByRole('tooltip')).toHaveTextContent('More');
  });

  it('shows again on the next hover after the pointer left the button', async () => {
    const { button } = renderOverflow();
    fireEvent.click(button);
    fireEvent.keyDown(screen.getByRole('menu'), { key: 'Escape' });
    expect(button).toHaveAttribute('aria-expanded', 'false');
    fireEvent.mouseOver(button);
    await pastEnterDelay();
    expect(tooltipShown()).toBeNull();

    fireEvent.pointerLeave(button);
    fireEvent.mouseLeave(button);
    fireEvent.mouseOver(button);
    expect(await screen.findByRole('tooltip')).toHaveTextContent('More');
  });
});

describe('the same tooltip on the other menu buttons of the editor', () => {
  it('the sub-menu button of a tool: none over its menu, none from the focus handed back', async () => {
    restores.push(stubFocusVisible());
    render(
      <ThemeContextProvider>
        <EditorToolbar
          orientation="horizontal"
          tool="select"
          onTool={vi.fn()}
          drawShape="rect"
          onDrawShape={vi.fn()}
          draftPoints={0}
          onFinishDraw={vi.fn()}
          onCancelDraw={vi.fn()}
          vertexPicked={false}
          canDeleteVertex={false}
          onDeleteVertex={vi.fn()}
          onInsertVertex={vi.fn()}
          onTemplate={vi.fn()}
          onAddWithDimensions={vi.fn()}
          selectionGroup={{
            angleStep: 15,
            onAngleStep: vi.fn(),
            onDelete: vi.fn(),
            align: { canAlign: true, canDistribute: true, onAlign: vi.fn(), onDistribute: vi.fn() },
          }}
        />
      </ThemeContextProvider>,
    );
    for (const testId of ['garden-plan-tool-bed-menu', 'garden-plan-align-button']) {
      const button = screen.getByTestId(testId);
      act(() => button.focus());
      expect(await screen.findByRole('tooltip')).toBeInTheDocument();
      fireEvent.click(button);
      expect(button).toHaveAttribute('aria-expanded', 'true');
      await waitFor(() => expect(tooltipShown()).toBeNull());
      fireEvent.keyDown(screen.getByRole('menu'), { key: 'Escape' });
      await waitFor(() => expect(button).toHaveFocus());
      await pastEnterDelay();
      expect(tooltipShown()).toBeNull();
      act(() => (document.activeElement as HTMLElement | null)?.blur());
      await waitFor(() => expect(screen.queryByRole('menu')).toBeNull());
    }
  });

  it('the panel\'s "⋯" names its open item menu (aria-expanded) and keeps its tooltip away', async () => {
    const t = setupEditor();
    t.click(15, 3);
    const more = screen.getByTestId('garden-plan-panel-more');
    expect(more).toHaveAttribute('aria-expanded', 'false');
    fireEvent.mouseOver(more);
    expect(await screen.findByRole('tooltip')).toBeInTheDocument();
    fireEvent.click(more);
    expect(more).toHaveAttribute('aria-expanded', 'true');
    const list = document.getElementById(more.getAttribute('aria-controls') ?? '');
    expect(list).toHaveAttribute('role', 'menu');
    await waitFor(() => expect(tooltipShown()).toBeNull());
    fireEvent.keyDown(screen.getByRole('menu'), { key: 'Escape' });
    expect(more).toHaveAttribute('aria-expanded', 'false');
    fireEvent.mouseOver(more);
    await pastEnterDelay();
    expect(tooltipShown()).toBeNull();
  });
});
