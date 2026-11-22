/**
 * The mini-map component (REQ-053 GP-UX-014, #2536): it does not redraw its up to 500 boxes when the editor
 * re-renders for a pointer move, and a click inside its border lands on the pixel under the pointer.
 */
import { useState } from 'react';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ThemeContextProvider } from '@/theme';
import type { Point } from '../model/types';
import type { Viewport } from '../renderer';
import { MiniMap } from './MiniMap';
import * as miniMap from './miniMap';
import { testPlan } from './tools/toolTestKit';

vi.mock('./miniMap', async (importOriginal) => {
  const original = await importOriginal<typeof import('./miniMap')>();
  return { ...original, toMiniMap: vi.fn(original.toMiniMap) };
});

afterEach(() => cleanup());

const PLAN = testPlan();
const EXTENT: [number, number, number, number] = [0, 0, 20, 20];
const VIEW: Viewport = { originM: [4, 12], pxPerM: 160, widthPx: 400, heightPx: 400 };

/** A parent that re-renders on demand with the same mini-map props, as the editor does on a pointer move. */
function Host({ onJump }: { onJump: (target: Point) => void }) {
  const [tick, setTick] = useState(0);
  return (
    <ThemeContextProvider>
      <button type="button" data-testid="tick" onClick={() => setTick(tick + 1)}>
        {tick}
      </button>
      <MiniMap plan={PLAN} extent={EXTENT} viewport={VIEW} onJump={onJump} />
    </ThemeContextProvider>
  );
}

describe('MiniMap', () => {
  it('does not redraw when its parent re-renders with the same plan and view', () => {
    render(<Host onJump={() => undefined} />);
    const toMiniMap = vi.mocked(miniMap.toMiniMap);
    toMiniMap.mockClear();
    fireEvent.click(screen.getByTestId('tick'));
    fireEvent.click(screen.getByTestId('tick'));
    expect(screen.getByTestId('tick')).toHaveTextContent('2');
    expect(toMiniMap).not.toHaveBeenCalled();
  });

  it('measures a click from inside its 1 px border, not from the border box', () => {
    const onJump = vi.fn();
    render(<Host onJump={onJump} />);
    const map = screen.getByTestId('garden-plan-minimap');
    map.getBoundingClientRect = () =>
      ({ left: 100, top: 50, right: 222, bottom: 172, width: 122, height: 122, x: 100, y: 50 }) as DOMRect;
    Object.defineProperty(map, 'clientLeft', { value: 1 });
    Object.defineProperty(map, 'clientTop', { value: 1 });
    // content pixel (60, 60) = the middle of the 20 x 20 m extent: the border box starts one pixel earlier
    fireEvent.click(map, { clientX: 100 + 1 + 60, clientY: 50 + 1 + 60 });
    expect(onJump).toHaveBeenCalledTimes(1);
    const [x, y] = onJump.mock.calls[0][0] as Point;
    expect(x).toBeCloseTo(10, 6);
    expect(y).toBeCloseTo(10, 6);
  });
});
