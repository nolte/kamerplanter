import type { SoilAnalysesResponse } from './soilAnalysisTypes';

/** One series point of the fixtures. */
export const point = (at: string, value: number, unit: string, key: string) => ({
  performed_at: at,
  value,
  unit,
  source: 'lab',
  sample_depth_cm: 30,
  content_class: null,
  event_key: key,
});

/** Fixtures of the soil analysis tests (REQ-053 WP 8.8): pH by two methods with the change marked, EC and humus. */
export function soilAnalyses(overrides: Partial<SoilAnalysesResponse> = {}): SoilAnalysesResponse {
  return {
    location_key: 'loc_b03',
    series: [
      { parameter: 'ec', method: 'ratio_1_5', unit: 'mS/cm', points: [point('2025-09-01T09:00:00Z', 0.4, 'mS/cm', 'ce_1')] },
      { parameter: 'humus', method: 'unknown', unit: '%', points: [point('2025-09-01T09:00:00Z', 3.1, '%', 'ce_1')] },
      { parameter: 'ph', method: 'cacl2', unit: 'pH', points: [point('2026-03-01T09:00:00Z', 6.1, 'pH', 'ce_2')] },
      { parameter: 'ph', method: 'h2o', unit: 'pH', points: [point('2025-09-01T09:00:00Z', 6.8, 'pH', 'ce_1')] },
    ],
    method_changes: [{ parameter: 'ph', at: '2026-03-01T09:00:00Z', from_method: 'h2o', to_method: 'cacl2' }],
    analyses: 2,
    truncated: false,
    liming_hint: { status: 'not_assessable', reason: 'no_target_ph' },
    ...overrides,
  };
}
