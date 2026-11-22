/** The "record soil analysis" form (REQ-053 GP-FR-122): validation and the wire body - nothing is converted. */
import { describe, expect, it } from 'vitest';
import {
  buildSoilAnalysisBody,
  contentClassAllowed,
  emptyRow,
  emptySoilAnalysisForm,
  hasErrors,
  methodsFor,
  validateSoilAnalysis,
  withParameter,
  type SoilAnalysisFormState,
} from './soilAnalysisForm';

const NOW = new Date('2026-06-15T10:00:00Z');

function form(overrides: Partial<SoilAnalysisFormState> = {}): SoilAnalysisFormState {
  return { ...emptySoilAnalysisForm(NOW), performedAt: '2026-06-01T09:00', ...overrides };
}

describe('soil analysis form', () => {
  it('asks for the method of a pH and an EC but not of a nutrient value', () => {
    const state = form({
      rows: [
        { ...emptyRow(1, 'ph'), value: '6.4' },
        { ...emptyRow(2, 'ec'), value: '0.8' },
        { ...emptyRow(3, 'p'), value: '12' },
      ],
    });
    const errors = validateSoilAnalysis(state, NOW);
    expect(errors.rows).toEqual({ 1: { method: 'required' }, 2: { method: 'required' } });
    expect(hasErrors(errors)).toBe(true);
  });

  it('refuses a missing value, a non-number and a value outside the physical range', () => {
    const state = form({
      rows: [
        { ...emptyRow(1, 'ph'), value: '', method: 'cacl2' },
        { ...emptyRow(2, 'ph'), value: 'abc', method: 'cacl2' },
        { ...emptyRow(3, 'ph'), value: '15', method: 'cacl2' },
        { ...emptyRow(4, 'humus'), value: '101' },
        { ...emptyRow(5, 'k'), value: '-1' },
      ],
    });
    expect(validateSoilAnalysis(state, NOW).rows).toEqual({
      1: { value: 'required' },
      2: { value: 'number' },
      3: { value: 'range' },
      4: { value: 'range' },
      5: { value: 'range' },
    });
  });

  it('refuses a future instant and a depth outside 0-1000 cm', () => {
    const errors = validateSoilAnalysis(
      form({ performedAt: '2026-07-01T09:00', depth: '1200', rows: [{ ...emptyRow(1, 'humus'), value: '3' }] }),
      NOW,
    );
    expect(errors.performedAt).toBe('future');
    expect(errors.depth).toBe('range');
  });

  it('takes a lab report up to five years old and refuses an older one (GP-FR-122)', () => {
    const rows = [{ ...emptyRow(1, 'humus'), value: '3' }];
    expect(validateSoilAnalysis(form({ performedAt: '2023-03-01T09:00', rows }), NOW).performedAt).toBeUndefined();
    expect(validateSoilAnalysis(form({ performedAt: '2021-06-01T09:00', rows }), NOW).performedAt).toBe('tooOld');
  });

  it('sends every value as typed with its own unit and method, and the depth on each', () => {
    const state = form({
      source: 'lab',
      depth: '30',
      rows: [
        { ...emptyRow(1, 'ph'), value: '6,4', method: 'cacl2' },
        { ...withParameter(emptyRow(2), 'ec'), value: '0.8', unit: 'dS/m', method: 'ratio_1_5' },
        { ...emptyRow(3, 'humus'), value: '3.2' },
      ],
    });
    expect(hasErrors(validateSoilAnalysis(state, NOW))).toBe(false);
    const body = buildSoilAnalysisBody('loc_b03', state, 'Soil analysis');
    expect(body).toMatchObject({ location_key: 'loc_b03', category: 'soil_analysis', summary: 'Soil analysis' });
    expect(body.measurements).toEqual([
      { parameter: 'ph', value: 6.4, unit: 'pH', source: 'lab', sample_depth_cm: 30, ph_method: 'cacl2' },
      { parameter: 'ec', value: 0.8, unit: 'dS/m', source: 'lab', sample_depth_cm: 30, ec_method: 'ratio_1_5' },
      { parameter: 'humus', value: 3.2, unit: '%', source: 'lab', sample_depth_cm: 30 },
    ]);
  });

  it('keeps a content class only for a lab value of P, K or Mg by CAL - it is never computed', () => {
    const cal = { ...emptyRow(1, 'p'), value: '12', method: 'cal', contentClass: 'C' };
    expect(contentClassAllowed(cal, 'lab')).toBe(true);
    expect(contentClassAllowed(cal, 'test_kit')).toBe(false);
    expect(contentClassAllowed({ ...cal, method: 'quick_test' }, 'lab')).toBe(false);
    expect(contentClassAllowed({ ...cal, parameter: 'humus' }, 'lab')).toBe(false);

    const lab = buildSoilAnalysisBody('b', form({ source: 'lab', rows: [cal] }), 's').measurements[0];
    expect(lab).toMatchObject({ extraction_method: 'cal', content_class: 'C' });
    const kit = buildSoilAnalysisBody('b', form({ source: 'test_kit', rows: [cal] }), 's').measurements[0];
    expect(kit.content_class).toBeUndefined();
  });

  it('offers the method list of the parameter and resets unit and method when the parameter changes', () => {
    expect(methodsFor('ph')).toEqual(['cacl2', 'h2o', 'probe_unknown']);
    expect(methodsFor('ec')).toContain('saturated_paste');
    expect(methodsFor('mg')).toContain('cal');
    const switched = withParameter({ ...emptyRow(1, 'ph'), value: '6', method: 'cacl2' }, 'ec');
    expect(switched).toMatchObject({ parameter: 'ec', unit: 'mS/cm', method: '', value: '6' });
  });
});
