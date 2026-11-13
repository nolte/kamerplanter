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
  it('lists the rail in GP-UX-001 order: select, pan, Bereich before Beet, garden object, Pflanze setzen, Messen, Text; no boundary', () => {
    expect(RAIL_TOOLS.map((entry) => entry.tool)).toEqual([
      'select',
      'pan',
      'area',
      'bed',
      'garden_object',
      'plant',
      'measure',
      'text',
    ]);
    // Text is the eighth and last tool of GP-UX-071: the cap of GP-UX-001 is reached, not passed (#2913).
    expect(RAIL_TOOLS).toHaveLength(8);
  });

  it('hands each tool to its machine; the boundary mode draws until the plan has a boundary (#2890)', () => {
    expect(ALL_TOOLS.map((tool) => [tool, canvasKindOf(tool, false)])).toEqual([
      ['select', 'select'],
      ['pan', 'pan'],
      ['area', 'draw'],
      ['bed', 'draw'],
      ['garden_object', 'draw'],
      ['plant', 'plant'],
      ['measure', 'measure'],
      ['text', 'text'],
      ['boundary', 'draw'],
    ]);
    expect(canvasKindOf('boundary', true)).toBe('boundary');
    expect(canvasKindOf('bed', true)).toBe('draw');
  });

  it('gives the canvas its cursor by the kind: grab to pan, a crosshair to draw and to measure, a hand to plant', () => {
    const cursor = (tool: PlanTool, hasBoundary = false) => cursorOf(behaviourOf(canvasKindOf(tool, hasBoundary)), false);
    expect(ALL_TOOLS.map((tool) => [tool, cursor(tool)])).toEqual([
      ['select', 'default'],
      ['pan', 'grab'],
      ['area', 'crosshair'],
      ['bed', 'crosshair'],
      ['garden_object', 'crosshair'],
      ['plant', 'pointer'],
      ['measure', 'crosshair'],
      // The caption's anchor is aimed like a drawn corner: crosshair and snap marker (GP-UX-071).
      ['text', 'crosshair'],
      ['boundary', 'crosshair'],
    ]);
    expect(behaviourOf('text').snapMarker).toBe(true);
    // The boundary that exists is reshaped by its handles: no crosshair. Space pans in every tool (GP-FR-010).
    expect(cursor('boundary', true)).toBe('default');
    expect(cursorOf(behaviourOf('measure'), true)).toBe('grab');
  });

  it('keeps the bed a surface and the boundary a rect or polygon (§9.5)', () => {
    expect(TOOL_DEFS.bed.draw?.shapes).not.toContain('polyline');
    expect(TOOL_DEFS.garden_object.draw?.shapes).toContain('polyline');
    expect(TOOL_DEFS.boundary.draw?.shapes).toEqual(['rect', 'polygon']);
    // An area is a rect or a polygon (§9.5 "Bereich"): no circle, no line (#2913).
    expect(TOOL_DEFS.area.draw).toEqual({ target: 'area', shapes: ['rect', 'polygon'] });
    expect(TOOL_DEFS.area.menu).toBe(true);
    expect(TOOL_DEFS.measure.draw).toBeUndefined();
    // The text tool is no draw tool: one click, then the dialog - no shapes to pick, no sub-menu.
    expect(TOOL_DEFS.text.draw).toBeUndefined();
    expect(TOOL_DEFS.text.menu).toBeUndefined();
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
    ['area', true, false],
    ['bed', true, false],
    ['garden_object', true, false],
    // "Pflanze setzen" is a tap on a spot: no points to set, no multi-select - the bar offers nothing misleading.
    ['plant', false, false],
    ['measure', true, false],
    // Text: "set point" alone (its anchor at the crosshair) - see the next test.
    ['text', true, false],
    ['boundary', false, false],
  ] as const)('%s: point actions %s, multi-select %s', (tool, points, multi) => {
    renderTouchBar(tool);
    expect(screen.queryByTestId('garden-plan-touch-place') !== null).toBe(points);
    expect(screen.queryByTestId('garden-plan-touch-multi') !== null).toBe(multi);
    // A tool with neither section and nothing leading shows no bar at all.
    expect(screen.queryByTestId('garden-plan-touchbar') !== null).toBe(points || multi);
  });

  it('offers the text tool "set point" alone: one anchor, nothing to undo, finish or cancel (GP-UX-071)', () => {
    const onPlacePoint = vi.fn();
    renderTouchBar('text', { onPlacePoint });
    screen.getByTestId('garden-plan-touch-place').click();
    expect(onPlacePoint).toHaveBeenCalledTimes(1);
    expect(screen.queryByTestId('garden-plan-touch-undo')).toBeNull();
    expect(screen.queryByTestId('garden-plan-touch-finish')).toBeNull();
    expect(screen.queryByTestId('garden-plan-touch-cancel')).toBeNull();
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
