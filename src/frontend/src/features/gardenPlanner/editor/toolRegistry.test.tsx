/**
 * The tool registry drives the places that compared tool names before (REQ-053 GP-UX-001/071, #2913): the rail's
 * buttons, the canvas machine, the cursor and the touch bar's sections. The four tools of before and the boundary mode
 * keep their behaviour; the measure tool gets the crosshair and the point actions from its kind alone.
 */
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ThemeContextProvider } from '@/theme';
import type { PlanTool } from '../state/gardenPlanSlice';
import { TouchBar } from './TouchBar';
import { behaviourOf, canvasKindOf, cursorOf, RAIL_TOOLS, TOOL_DEFS } from './toolRegistry';

afterEach(() => cleanup());

const ALL_TOOLS = Object.keys(TOOL_DEFS) as PlanTool[];

describe('the tool registry', () => {
  it('lists the rail in GP-UX-001 order: the four tools of before, then Messen; the boundary is no rail tool', () => {
    expect(RAIL_TOOLS.map((entry) => entry.tool)).toEqual(['select', 'pan', 'bed', 'garden_object', 'measure']);
    expect(RAIL_TOOLS.length).toBeLessThanOrEqual(8);
  });

  it('hands each tool to its machine; the boundary mode draws until the plan has a boundary (#2890)', () => {
    expect(ALL_TOOLS.map((tool) => [tool, canvasKindOf(tool, false)])).toEqual([
      ['select', 'select'],
      ['pan', 'pan'],
      ['bed', 'draw'],
      ['garden_object', 'draw'],
      ['measure', 'measure'],
      ['boundary', 'draw'],
    ]);
    expect(canvasKindOf('boundary', true)).toBe('boundary');
    expect(canvasKindOf('bed', true)).toBe('draw');
  });

  it('gives the canvas its cursor by the kind: grab to pan, a crosshair to draw and to measure', () => {
    const cursor = (tool: PlanTool, hasBoundary = false) => cursorOf(behaviourOf(canvasKindOf(tool, hasBoundary)), false);
    expect(ALL_TOOLS.map((tool) => [tool, cursor(tool)])).toEqual([
      ['select', 'default'],
      ['pan', 'grab'],
      ['bed', 'crosshair'],
      ['garden_object', 'crosshair'],
      ['measure', 'crosshair'],
      ['boundary', 'crosshair'],
    ]);
    // The boundary that exists is reshaped by its handles: no crosshair. Space pans in every tool (GP-FR-010).
    expect(cursor('boundary', true)).toBe('default');
    expect(cursorOf(behaviourOf('measure'), true)).toBe('grab');
  });

  it('keeps the bed a surface and the boundary a rect or polygon (§9.5)', () => {
    expect(TOOL_DEFS.bed.draw?.shapes).not.toContain('polyline');
    expect(TOOL_DEFS.garden_object.draw?.shapes).toContain('polyline');
    expect(TOOL_DEFS.boundary.draw?.shapes).toEqual(['rect', 'polygon']);
    expect(TOOL_DEFS.measure.draw).toBeUndefined();
  });
});

describe('the touch bar reads its sections from the registry', () => {
  function renderTouchBar(tool: PlanTool, extra: Partial<Parameters<typeof TouchBar>[0]> = {}) {
    return render(
      <ThemeContextProvider>
        <TouchBar
          tool={tool}
          drawShape="polygon"
          draftPoints={0}
          onPlacePoint={vi.fn()}
          onUndoPoint={vi.fn()}
          onFinish={vi.fn()}
          onCancel={vi.fn()}
          multiSelect={false}
          onMultiSelect={vi.fn()}
          {...extra}
        />
      </ThemeContextProvider>,
    );
  }

  it.each([
    ['select', false, true],
    ['pan', false, false],
    ['bed', true, false],
    ['garden_object', true, false],
    ['measure', true, false],
    ['boundary', false, false],
  ] as const)('%s: point actions %s, multi-select %s', (tool, points, multi) => {
    renderTouchBar(tool);
    expect(screen.queryByTestId('garden-plan-touch-place') !== null).toBe(points);
    expect(screen.queryByTestId('garden-plan-touch-multi') !== null).toBe(multi);
    // A tool with neither section and nothing leading shows no bar at all.
    expect(screen.queryByTestId('garden-plan-touchbar') !== null).toBe(points || multi);
  });

  it('finishes a measurement only while it is finishable, and its "cancel" clears it', () => {
    renderTouchBar('measure', { draftPoints: 2, measureFinishable: false });
    expect(screen.getByTestId('garden-plan-touch-finish')).toHaveAttribute('aria-disabled', 'true');
    expect(screen.getByTestId('garden-plan-touch-cancel')).toHaveTextContent('Clear');
    cleanup();
    renderTouchBar('measure', { draftPoints: 2, measureFinishable: true });
    expect(screen.getByTestId('garden-plan-touch-finish')).not.toHaveAttribute('aria-disabled');
  });
});
