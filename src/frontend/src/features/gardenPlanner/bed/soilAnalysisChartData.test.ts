/** The chart's view of the soil series (GP-FR-122): one line per method, never merged; changes marked. */
import { describe, expect, it } from 'vitest';
import { parameterHistory } from './soilAnalysisChartData';
import { soilAnalyses } from './soilAnalysisTestKit';

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

  it('answers null for a parameter without values', () => {
    expect(parameterHistory(soilAnalyses({ series: [] }), 'humus')).toBeNull();
  });
});
