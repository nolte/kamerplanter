/**
 * Focus retention of the editor (REQ-053 §17.3, GP-NFR-070, WCAG 2.2 SC 2.4.3, #2886): a focused control that becomes
 * unavailable keeps the focus (M-1: "Save" after a save, undo/redo at an end of the history, zoom-out at the fit zoom,
 * "Finish" of a drawing), and a focused header control that moves into the overflow hands it to "⋮" (M-2).
 */
import { useState } from 'react';
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { configureStore } from '@reduxjs/toolkit';
import { Provider } from 'react-redux';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ThemeContextProvider } from '@/theme';
import { bed, planResponse } from '@/test/gardenPlanFixtures';
import * as api from '../api/gardenPlan';
import { normalizePlan } from '../model/planModel';
import type { Geometry, PlanBatchResponse } from '../model/types';
import { applyAction, gardenPlanSlice, loadGardenPlan } from '../state/gardenPlanSlice';
import { EditorHeaderBar } from './EditorHeaderBar';
import { EditorToolbar } from './EditorToolbar';
import { TouchBar } from './TouchBar';
import { ZoomOverlay } from './ZoomOverlay';
import { setupEditor } from './editorTestKit';
import type { AutoSave } from './useAutoSave';

vi.mock('../api/gardenPlan', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../api/gardenPlan')>()),
  getGardenPlan: vi.fn(),
  applyPlanBatch: vi.fn(),
}));

const applyPlanBatch = vi.mocked(api.applyPlanBatch);

const rect = (x: number): Geometry => ({ kind: 'rect', origin: [x, 3], width_m: 2, length_m: 2, rotation_deg: 0 });

function plan() {
  return normalizePlan(planResponse({ locations: [bed('b1', 3, 3)], slots: [], plants: [] }));
}

function ok(): PlanBatchResponse {
  return { plan_revision: 43, key_map: {}, updated: [], deleted: [], derived: {} };
}

beforeEach(() => {
  vi.resetAllMocks();
});
afterEach(() => {
  cleanup();
  window.localStorage.clear();
});

const unavailable = (element: HTMLElement) => expect(element).toHaveAttribute('aria-disabled', 'true');

/**
 * The browser's "focus fixup" (HTML § 6.6.4): a focused element that turns `disabled` loses the focus to the body.
 * jsdom does not run it, so the test does before it asks where the focus is - otherwise a `disabled` regression
 * would pass here and still drop the focus in every real browser.
 */
function expectFocusKept(element: HTMLElement) {
  const active = document.activeElement;
  if (active instanceof HTMLElement && active.matches(':disabled')) act(() => active.blur());
  expect(element).toHaveFocus();
}

describe('M-1: a focused control that becomes unavailable keeps the focus (GP-NFR-070)', () => {
  function moved() {
    const t = setupEditor({ plan: plan() });
    t.after(() => act(() => void t.store.dispatch(applyAction([{ op: 'update_geometry', entity: 'location', key: 'b1', geometry: rect(4) }], 'pages.gardenPlan.editor.actions.move'))));
    return t;
  }

  it('"Save" right after a successful save stays focused, aria-disabled, and a second press sends nothing', async () => {
    const t = moved();
    applyPlanBatch.mockResolvedValue(ok());
    const save = screen.getByTestId('garden-plan-save');
    act(() => save.focus());
    await act(async () => {
      fireEvent.click(save);
    });
    t.rerender();
    expect(t.state().pending).toHaveLength(0);
    expectFocusKept(screen.getByTestId('garden-plan-save'));
    unavailable(screen.getByTestId('garden-plan-save'));
    await act(async () => {
      fireEvent.click(screen.getByTestId('garden-plan-save'));
    });
    expect(applyPlanBatch).toHaveBeenCalledTimes(1);
  });

  it('undo at the start of the history stays focused and does nothing more', () => {
    const t = moved();
    const undoButton = screen.getByTestId('garden-plan-undo');
    act(() => undoButton.focus());
    t.after(() => fireEvent.click(undoButton));
    expect(t.state().past).toHaveLength(0);
    expectFocusKept(undoButton);
    unavailable(undoButton);
    t.after(() => fireEvent.click(undoButton));
    expect(t.state().future).toHaveLength(1);
  });

  it('redo at the end of the history stays focused and does nothing more', () => {
    const t = moved();
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-undo')));
    const redoButton = screen.getByTestId('garden-plan-redo');
    act(() => redoButton.focus());
    t.after(() => fireEvent.click(redoButton));
    expect(t.state().future).toHaveLength(0);
    expectFocusKept(redoButton);
    unavailable(redoButton);
    t.after(() => fireEvent.click(redoButton));
    expect(t.state().past).toHaveLength(1);
  });

  it('zoom-out at the fit zoom stays focused; a further press does not zoom', () => {
    const onZoomOut = vi.fn();
    function Harness() {
      const [pxPerM, setPxPerM] = useState(20);
      return (
        <ZoomOverlay
          pxPerM={pxPerM}
          minPxPerM={10}
          onZoomIn={() => setPxPerM((value) => value * 2)}
          onZoomOut={() => {
            onZoomOut();
            setPxPerM((value) => Math.max(10, value / 2));
          }}
          onFit={() => setPxPerM(10)}
        />
      );
    }
    render(<Harness />);
    const zoomOut = screen.getByTestId('garden-plan-zoom-out');
    act(() => zoomOut.focus());
    fireEvent.click(zoomOut);
    expect(onZoomOut).toHaveBeenCalledTimes(1);
    expectFocusKept(zoomOut);
    unavailable(zoomOut);
    fireEvent.click(zoomOut);
    expect(onZoomOut).toHaveBeenCalledTimes(1);
  });

  describe('"Finish" of a drawing', () => {
    function renderToolbar(draftPoints: number, onFinishDraw = vi.fn()) {
      const props = {
        orientation: 'vertical' as const,
        tool: 'bed' as const,
        onTool: vi.fn(),
        drawShape: 'polygon' as const,
        onDrawShape: vi.fn(),
        onFinishDraw,
        onCancelDraw: vi.fn(),
        vertexPicked: false,
        canDeleteVertex: false,
        onDeleteVertex: vi.fn(),
        onInsertVertex: vi.fn(),
        selectionGroup: null,
      };
      const view = render(<EditorToolbar {...props} draftPoints={draftPoints} />);
      return { rerender: (points: number) => view.rerender(<EditorToolbar {...props} draftPoints={points} />) };
    }

    it('keeps the focus when a point goes and the shape is no longer finishable; a press then does nothing', () => {
      const onFinishDraw = vi.fn();
      const t = renderToolbar(3, onFinishDraw);
      const finish = screen.getByTestId('garden-plan-draw-finish');
      act(() => finish.focus());
      t.rerender(2);
      expectFocusKept(finish);
      unavailable(finish);
      fireEvent.click(finish);
      expect(onFinishDraw).not.toHaveBeenCalled();
    });

    it('stays an item of the tool bar: the arrow keys reach it while it is unavailable', () => {
      renderToolbar(1);
      const finish = screen.getByTestId('garden-plan-draw-finish');
      unavailable(finish);
      const lastShape = screen.getByTestId('garden-plan-shape-polygon');
      act(() => lastShape.focus());
      fireEvent.keyDown(lastShape, { key: 'ArrowDown' });
      expectFocusKept(finish);
    });

    it('a finished shape hands the focus to the plan, its defined successor', () => {
      const t = setupEditor();
      fireEvent.click(screen.getByTestId('garden-plan-tool-garden_object'));
      fireEvent.click(screen.getByTestId('garden-plan-shape-polyline'));
      t.click(16, 14);
      t.click(19, 14);
      const finish = screen.getByTestId('garden-plan-draw-finish');
      act(() => finish.focus());
      t.after(() => fireEvent.click(finish));
      expect(t.canvas()).toHaveFocus();
    });
  });
});

describe('touch bar (below md): a focused draw action that becomes unavailable keeps the focus', () => {
  it('"undo point" with the last point taken back stays focused, and a further press does nothing', () => {
    const onUndoPoint = vi.fn();
    const props = {
      tool: 'bed' as const,
      drawShape: 'polygon' as const,
      onPlacePoint: vi.fn(),
      onUndoPoint,
      onFinish: vi.fn(),
      onCancel: vi.fn(),
      multiSelect: false,
      onMultiSelect: vi.fn(),
    };
    const view = render(<TouchBar {...props} draftPoints={1} />);
    const undoPoint = screen.getByTestId('garden-plan-touch-undo');
    act(() => undoPoint.focus());
    fireEvent.click(undoPoint);
    expect(onUndoPoint).toHaveBeenCalledTimes(1);
    view.rerender(<TouchBar {...props} draftPoints={0} />);
    expectFocusKept(undoPoint);
    unavailable(undoPoint);
    unavailable(screen.getByTestId('garden-plan-touch-finish'));
    fireEvent.click(undoPoint);
    expect(onUndoPoint).toHaveBeenCalledTimes(1);
  });
});

describe('M-2: a focused header control that moves into the overflow hands the focus to "⋮" (GP-NFR-070)', () => {
  const autoSave: AutoSave = { enabled: true, setEnabled: () => undefined, paused: false };
  const panelToggle = {
    label: 'Panel',
    icon: <span />,
    expanded: true,
    controls: 'panel',
    onToggle: () => undefined,
    testId: 'garden-plan-panel-toggle',
  };

  function renderBar(narrow = false) {
    const store = configureStore({ reducer: { gardenPlan: gardenPlanSlice.reducer } });
    store.dispatch(loadGardenPlan.pending('r1', 'site_1'));
    store.dispatch(loadGardenPlan.fulfilled(plan(), 'r1', 'site_1'));
    const overflowButtonRef = { current: null as HTMLButtonElement | null };
    const tree = (isNarrow: boolean) => (
      <Provider store={store}>
        <ThemeContextProvider>
          <EditorHeaderBar
            autoSave={autoSave}
            narrow={isNarrow}
            undoRedo
            panelToggle={panelToggle}
            overflowItems={[]}
            overflowButtonRef={overflowButtonRef}
          />
        </ThemeContextProvider>
      </Provider>
    );
    const view = render(tree(narrow));
    return { overflowButtonRef, rerender: (isNarrow: boolean) => view.rerender(tree(isNarrow)) };
  }

  it('the bar turning narrow moves the focused panel switch into the overflow and the focus to "⋮"', () => {
    const t = renderBar(false);
    const toggle = screen.getByTestId('garden-plan-panel-toggle');
    act(() => toggle.focus());
    t.rerender(true);
    expect(screen.queryByTestId('garden-plan-panel-toggle')).toBeNull();
    expect(screen.getByTestId('garden-plan-overflow')).toHaveFocus();
    // The route's own ref still points at the same button (dialogs give the focus back to it).
    expect(t.overflowButtonRef.current).toBe(screen.getByTestId('garden-plan-overflow'));
  });

  describe('measured by the bar (a longer line, 200 % zoom)', () => {
    let content = 800;
    const observers: { callback: ResizeObserverCallback; observer: ResizeObserver }[] = [];
    const isBar = (element: Element) => element.getAttribute('data-testid') === 'garden-plan-header-bar';

    beforeEach(() => {
      content = 800;
      observers.length = 0;
      vi.spyOn(HTMLElement.prototype, 'clientWidth', 'get').mockImplementation(function (this: HTMLElement) {
        return isBar(this) ? 800 : 0;
      });
      // The content is too wide while the auto-save switch is in the bar (level 0) and fits from level 1 on.
      vi.spyOn(HTMLElement.prototype, 'scrollWidth', 'get').mockImplementation(function (this: HTMLElement) {
        if (!isBar(this)) return 0;
        return Number(this.getAttribute('data-overflow-level')) >= 1 ? 800 : content;
      });
      vi.stubGlobal(
        'ResizeObserver',
        class {
          constructor(callback: ResizeObserverCallback) {
            observers.push({ callback, observer: this as unknown as ResizeObserver });
          }
          observe() {}
          unobserve() {}
          disconnect() {}
        },
      );
    });
    afterEach(() => {
      vi.restoreAllMocks();
      vi.unstubAllGlobals();
    });

    const grow = () =>
      act(() => {
        content = 900;
        for (const { callback, observer } of observers) callback([], observer);
      });

    it('moves the focused auto-save switch into the overflow and the focus to "⋮"', () => {
      renderBar();
      const header = screen.getByTestId('garden-plan-header-bar');
      expect(header).toHaveAttribute('data-overflow-level', '0');
      const autoSaveSwitch = screen.getByTestId('garden-plan-autosave');
      act(() => autoSaveSwitch.focus());
      grow();
      expect(header).toHaveAttribute('data-overflow-level', '1');
      expect(screen.queryByTestId('garden-plan-autosave')).toBeNull();
      expect(screen.getByTestId('garden-plan-overflow')).toHaveFocus();
    });

    it('leaves the focus alone on a control that stays in the bar', () => {
      renderBar();
      const toggle = screen.getByTestId('garden-plan-panel-toggle');
      act(() => toggle.focus());
      grow();
      expect(screen.getByTestId('garden-plan-header-bar')).toHaveAttribute('data-overflow-level', '1');
      expect(toggle).toHaveFocus();
    });

    it('does not pull the focus back once the user had left the control', async () => {
      renderBar();
      const autoSaveSwitch = screen.getByTestId('garden-plan-autosave');
      act(() => autoSaveSwitch.focus());
      act(() => autoSaveSwitch.blur());
      await act(async () => {
        await new Promise((resolve) => window.setTimeout(resolve, 0));
      });
      grow();
      expect(screen.queryByTestId('garden-plan-autosave')).toBeNull();
      expect(screen.getByTestId('garden-plan-overflow')).not.toHaveFocus();
    });
  });
});
