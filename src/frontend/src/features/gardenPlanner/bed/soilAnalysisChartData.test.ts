/** The chart's view of the soil series (GP-FR-122): one line per method, never merged; changes marked. */
import { describe, expect, it } from 'vitest';
import { changeLabelPosition, parameterHistory, timeDomain } from './soilAnalysisChartData';
import { point, soilAnalyses } from './soilAnalysisTestKit';

describe('parameterHistory', () => {
  it('keeps one line per method and marks the change in the chart and the table', () => {
    const history = parameterHistory(soilAnalyses(), 'ph')!;
    expect(history.lines.map((line) => [line.method, line.points.map((point) => point.value)])).toEqual([
      ['cacl2', [6.1]],
      ['h2o', [6.8]],
    ]);
    const changeAt = new Date('2026-03-01T09:00:00Z').getTime();
    expect(history.changes).toEqual([changeAt]);
    // The table is oldest first; only the value after the change carries the mark.
    expect(history.rows.map((row) => [row.method, row.value, row.methodChanged])).toEqual([
      ['h2o', 6.8, false],
      ['cacl2', 6.1, true],
    ]);
  });

  it('keeps two units of one method apart, each line and row with its own identity', () => {
    const at = '2026-03-01T09:00:00Z';
    const history = parameterHistory(
      soilAnalyses({
        series: [
          { parameter: 'ec', method: 'sensor', unit: 'mS/cm', points: [point(at, 1.1, 'mS/cm', 'ce_9')] },
          { parameter: 'ec', method: 'sensor', unit: 'uS/cm', points: [point(at, 1100, 'uS/cm', 'ce_9')] },
        ],
        method_changes: [],
      }),
      'ec',
    )!;
    expect(history.lines.map((line) => [line.id, line.unit])).toEqual([
      ['sensor|mS/cm', 'mS/cm'],
      ['sensor|uS/cm', 'uS/cm'],
    ]);
    expect(new Set(history.rows.map((row) => row.key)).size).toBe(2);
  });

  it('answers null for a parameter without values', () => {
    expect(parameterHistory(soilAnalyses({ series: [] }), 'humus')).toBeNull();
  });
});

describe('time axis and the method-change label (#2764 item 4)', () => {
  it('keeps the newest value off the right edge, where the change to a new method usually sits', () => {
    const history = parameterHistory(soilAnalyses(), 'ph')!;
    const [from, to] = timeDomain(history);
    const times = history.rows.map((row) => row.time);
    expect(from).toBeLessThan(Math.min(...times));
    expect(to).toBeGreaterThan(Math.max(...times));
  });

  it('pads a history of a single day by a day on each side', () => {
    const at = '2026-03-01T09:00:00Z';
    const history = parameterHistory(
      soilAnalyses({ series: [{ parameter: 'ph', method: 'h2o', unit: 'pH', points: [point(at, 6.8, 'pH', 'ce_1')] }], method_changes: [] }),
      'ph',
    )!;
    const time = new Date(at).getTime();
    expect(timeDomain(history)).toEqual([time - 86_400_000, time + 86_400_000]);
  });

  it('puts the label of a change in the right half to the left of its line, so it is not cut to "M"', () => {
    const history = parameterHistory(soilAnalyses(), 'ph')!;
    const domain = timeDomain(history);
    expect(changeLabelPosition(history.changes[0], domain)).toBe('insideTopRight');
    expect(changeLabelPosition(domain[0], domain)).toBe('insideTopLeft');
  });
});
