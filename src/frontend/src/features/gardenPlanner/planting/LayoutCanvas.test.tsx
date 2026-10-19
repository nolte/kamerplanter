/**
 * The bed canvas of the planting dialog (REQ-053 GP-FR-072/068): the yellow ring, the layer shapes that
 * keep entries apart without colour, tapping to add and dragging to move.
 */
import { act, cleanup, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import LayoutCanvas from './LayoutCanvas';
import { BED_GEOMETRY } from './plantingTestKit';

beforeEach(() => {
  vi.spyOn(Element.prototype, 'getBoundingClientRect').mockImplementation(
    () => ({ left: 0, top: 0, width: 400, height: 400, right: 400, bottom: 400, x: 0, y: 0, toJSON: () => ({}) }),
  );
});
afterEach(() => {
  vi.useRealTimers();
  cleanup();
  vi.restoreAllMocks();
});

function pointer(target: Element, type: string, x: number, y: number) {
  act(() => {
    target.dispatchEvent(new MouseEvent(type, { clientX: x, clientY: y, bubbles: true }));
  });
}

describe('LayoutCanvas', () => {
  it('rings only the flagged positions', () => {
    render(
      <LayoutCanvas
        bed={BED_GEOMETRY}
        label="Bed"
        layers={[
          { id: 'a', shape: 'circle', color: '#080', positions: [[0.2, 0.2], [0.25, 0.2], [1, 1]], flagged: [0, 1] },
        ]}
      />,
    );
    expect(screen.getAllByTestId('layout-canvas-ring')).toHaveLength(2);
  });

  it('draws a different marker shape per layer, so colour is not the only cue', () => {
    const { container } = render(
      <LayoutCanvas
        bed={BED_GEOMETRY}
        label="Bed"
        layers={[
          { id: 'a', shape: 'circle', color: '#080', positions: [[0.2, 0.2]] },
          { id: 'b', shape: 'square', color: '#008', positions: [[0.5, 0.5]] },
          { id: 'c', shape: 'triangle', color: '#800', positions: [[0.8, 0.8]] },
        ]}
      />,
    );
    expect(container.querySelectorAll('[data-layer="a"] circle')).toHaveLength(1);
    expect(container.querySelectorAll('[data-layer="b"] path')).toHaveLength(1);
    expect(container.querySelectorAll('[data-layer="c"] path')).toHaveLength(1);
    expect(container.querySelector('[data-layer="b"] path')?.getAttribute('d')).not.toBe(
      container.querySelector('[data-layer="c"] path')?.getAttribute('d'),
    );
  });

  it('adds a point where the bed is tapped, in the bed frame, rounded to a centimetre', () => {
    const added: [number, number][] = [];
    render(<LayoutCanvas bed={BED_GEOMETRY} label="Bed" layers={[]} onAdd={(point) => added.push(point)} />);
    pointer(screen.getByTestId('layout-canvas'), 'pointerup', 200, 200);
    expect(added).toEqual([[0.6, 1]]);
  });

  it('moves a point of the interactive layer by dragging and adds none at the end of the drag', () => {
    vi.useFakeTimers();
    const moves: [string, number, [number, number]][] = [];
    const added: [number, number][] = [];
    render(
      <LayoutCanvas
        bed={BED_GEOMETRY}
        label="Bed"
        layers={[{ id: 'plant', shape: 'circle', color: '#080', positions: [[0.6, 1]] }]}
        interactiveLayerId="plant"
        onAdd={(point) => added.push(point)}
        onMove={(layer, index, point) => moves.push([layer, index, point])}
      />,
    );
    const handle = screen.getByTestId('layout-canvas-point-0');
    pointer(handle, 'pointerdown', 200, 200);
    pointer(handle, 'pointermove', 100, 300);
    pointer(handle, 'pointerup', 100, 300);

    expect(moves[moves.length - 1]).toEqual(['plant', 0, [0.24, 0.44]]);
    expect(added).toEqual([]);
    vi.runAllTimers();
  });

  it('is named for assistive technology and has no violations', async () => {
    render(
      <LayoutCanvas
        bed={BED_GEOMETRY}
        label="Preview of the bed"
        layers={[{ id: 'a', shape: 'circle', color: '#080', positions: [[0.2, 0.2]] }]}
      />,
    );
    expect(screen.getByRole('img', { name: 'Preview of the bed' })).toBeInTheDocument();
    await expectNoA11yViolations(screen.getByTestId('layout-canvas').parentElement as HTMLElement);
  });
});
