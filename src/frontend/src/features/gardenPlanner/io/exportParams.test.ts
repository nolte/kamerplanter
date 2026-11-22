/**
 * The export query and the rule that offers the underlay (REQ-053 GP-FR-033, #2895): the PDF asks for
 * `underlay=true` only when it was chosen, the SVG and the JSON backup never carry it.
 */
import { describe, expect, it } from 'vitest';
import { exportParams } from './ioApi';
import { DEFAULT_EXPORT_OPTIONS, underlayOffered, type ExportOptions } from './types';

const UNDERLAY = {
  attachment_key: 'att_1',
  calibration: { p1_px: [0, 0] as [number, number], p2_px: [100, 0] as [number, number], distance_m: 5 },
  origin: [0, 0] as [number, number],
  rotation_deg: 0,
  opacity: 0.5,
};

function pdf(change: Partial<ExportOptions> = {}): ExportOptions {
  return { ...DEFAULT_EXPORT_OPTIONS, format: 'pdf', ...change };
}

describe('exportParams underlay', () => {
  it('is off by default and then not in the query', () => {
    expect(DEFAULT_EXPORT_OPTIONS.underlay).toBe(false);
    expect(exportParams(pdf(), 'de')).not.toHaveProperty('underlay');
  });

  it('asks the PDF for the underlay when it is chosen', () => {
    expect(exportParams(pdf({ underlay: true }), 'de')).toMatchObject({ underlay: 'true', bed_list: 'false' });
  });

  it('never sends it with the SVG or the JSON backup', () => {
    expect(exportParams(pdf({ format: 'svg', underlay: true }), 'de')).not.toHaveProperty('underlay');
    expect(exportParams(pdf({ format: 'json', underlay: true }), 'de')).toEqual({});
  });
});

describe('underlayOffered', () => {
  it('offers the option only for a plan that has an underlay', () => {
    expect(underlayOffered({ underlay: UNDERLAY })).toBe(true);
    expect(underlayOffered({ underlay: null })).toBe(false);
    expect(underlayOffered({})).toBe(false);
    expect(underlayOffered(null)).toBe(false);
    expect(underlayOffered(undefined)).toBe(false);
  });
});
