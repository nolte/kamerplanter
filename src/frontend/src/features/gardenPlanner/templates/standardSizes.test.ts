import { describe, expect, it } from 'vitest';
import type { BedTemplate } from '../model/types';
import { standardSizeOf, standardSizeTemplates } from './standardSizes';

const template = (patch: Partial<BedTemplate>): BedTemplate => ({
  key: 'sys_a',
  name: 'A',
  location_type_key: 'bed',
  default_geometry: { kind: 'rect', origin: [0, 0], width_m: 2, length_m: 1, rotation_deg: 0 },
  height_m: null,
  recurring_task_templates: [],
  is_system: true,
  ...patch,
});

describe('standard sizes (GP-FR-045)', () => {
  it('reads a rectangle as width and length and prefills the height', () => {
    expect(standardSizeOf(template({ location_type_key: 'raised_bed', height_m: 0.8 }))).toEqual({
      shape: 'rect',
      width: 2,
      length: 1,
      radius: null,
      bedTypeKey: 'raised_bed',
      heightM: 0.8,
    });
  });

  it('reads a planter as a circle by its radius', () => {
    expect(
      standardSizeOf(
        template({ default_geometry: { kind: 'circle', origin: [0, 0], radius_m: 0.2 } }),
      ),
    ).toMatchObject({ shape: 'circle', radius: 0.2, width: null, heightM: null });
  });

  it('offers system templates with a numeric shape only', () => {
    const polygon = template({
      key: 'sys_p',
      default_geometry: {
        kind: 'polygon',
        points: [
          [0, 0],
          [1, 0],
          [1, 1],
        ],
        rotation_deg: 0,
      },
    });
    const own = template({ key: 'own', is_system: false });
    const system = template({ key: 'sys_r' });
    expect(standardSizeTemplates([polygon, own, system]).map((item) => item.key)).toEqual([
      'sys_r',
    ]);
  });
});
