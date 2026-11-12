/**
 * The measurement drawn on the canvas (REQ-053 GP-UX-071, #2913): a segment too short on screen for its own length
 * label leaves it off, so it never overprints its neighbour or the total; a long segment keeps its label.
 */
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { ThemeContextProvider } from '@/theme';
import type { Point } from '../model/types';
import { MeasureOverlay } from './MeasureOverlay';
import { measureFinish, measureView, INITIAL_MEASURE_STATE, measureDown, measureUp } from './tools/measureMachine';
import { at, makeEnv, testPlan } from './tools/toolTestKit';

afterEach(() => cleanup());

/** 40 px per metre, model (0, 20) at the top-left - the editor's test viewport. */
const toScreen = ([x, y]: Point): Point => [x * 40, (20 - y) * 40];

function finished(points: Point[]) {
  const env = makeEnv(testPlan(), { snapPoint: (point) => point });
  const state = points.reduce((current, point) => {
    const sample = at(env, point);
    return measureUp(measureDown(current, sample, env), sample, env);
  }, INITIAL_MEASURE_STATE);
  return measureView(measureFinish(state))!;
}

function renderOverlay(points: Point[]) {
  render(
    <ThemeContextProvider>
      <svg>
        <MeasureOverlay measure={finished(points)} toScreen={toScreen} unit="m" widthPx={800} />
      </svg>
    </ThemeContextProvider>,
  );
  return screen.queryAllByTestId('garden-plan-measure-segment').map((node) => node.textContent);
}

describe('segment labels of a measurement', () => {
  it('leaves out the label of a segment too short for it, and keeps the total', () => {
    // 0.5 m = 20 px on screen: "0.50 m" needs about 45 px plus room.
    const labels = renderOverlay([
      [2, 14],
      [2.5, 14],
      [2.5, 19],
    ]);
    expect(labels).toEqual(['5.00 m']);
    expect(screen.getByTestId('garden-plan-measure-total')).toHaveTextContent('Total 5.50 m');
  });

  it('draws the label of every segment long enough for it', () => {
    const labels = renderOverlay([
      [2, 14],
      [4, 14],
      [4, 19],
    ]);
    expect(labels).toEqual(['2.00 m', '5.00 m']);
  });
});
