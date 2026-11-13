/**
 * An area location as the renderers draw it (REQ-053 §9.5, GP-UX-032, GP-UX-071, #2913): a garden, terrace or
 * greenhouse - a location the server marks `is_area` - lies below the beds and paths inside it (hit class "Bereich",
 * rank 3), has its own light look whatever its `bed_status`, is named as an area, and its name gives way to the names
 * of the beds inside it. A location without the mark keeps the bed look and rank (a plan cached before #2913).
 */
import { describe, expect, it } from 'vitest';
import { lightTheme } from '@/theme/theme';
import type { Point } from '../model/types';
import { HeadlessPlanRenderer } from './HeadlessPlanRenderer';
import { planPalette, shapeAriaLabel, shapeStyle } from './planDrawing';
import { shapeEntries } from './planIndex';
import { buildScene } from './scene';
import {
  NO_SELECTION,
  bed,
  gardenObject,
  normalizePlan,
  options,
  planResponse,
  viewportAt,
  type PlanModel,
} from './rendererTestKit';

/** Screen point of model point (x, y) for a viewport at origin (0, 10) and 100 px/m. */
const px = (x: number, y: number): Point => [x * 100, (10 - y) * 100];
const VIEW = viewportAt(0, 10, 100);

/** A 4 x 4 m garden (an area, `bed_status` planned on purpose) holding a bed at (1.4, 1.06) and a path across it. */
function garden(isArea = true): PlanModel {
  return normalizePlan(
    planResponse({
      plan: null,
      locations: [
        bed('garden', 0, 0, {
          name: 'Gemüsegarten',
          location_type_key: 'garden',
          geometry: { kind: 'rect', origin: [0, 0], width_m: 4, length_m: 4, rotation_deg: 0 },
          bbox: [0, 0, 4, 4],
          area_m2: 16,
          bed_status: 'planned',
          ...(isArea ? { is_area: true } : {}),
        }),
        bed('inner', 1.4, 1.06, { name: 'Beet', parent_location_key: 'garden' }),
      ],
      garden_objects: [
        gardenObject('path', 2, 3.5, {
          object_type: 'path',
          props: { object_type: 'path' },
          geometry: { kind: 'rect', origin: [0, 3.2], width_m: 4, length_m: 0.5, rotation_deg: 0 },
          bbox: [0, 3.2, 4, 3.7],
          parent_location_key: 'garden',
        }),
      ],
      area_type_keys: ['garden'],
    }),
  );
}

function render(model: PlanModel) {
  const renderer = new HeadlessPlanRenderer();
  renderer.render(model, VIEW, NO_SELECTION, options());
  return renderer;
}

const entryOf = (model: PlanModel, key: string) => shapeEntries(model).find((entry) => entry.key === key)!;

describe('an area lies below the beds (GP-UX-032)', () => {
  it('is in the hit class "Bereich": a bed inside it and a path across it are hit first', () => {
    const renderer = render(garden());
    // The bed sits at (1.4, 1.06), 1.2 x 2 m.
    expect(renderer.hitTestAll(px(2, 2))).toEqual(['inner', 'garden']);
    expect(renderer.hitTestAll(px(0.5, 3.4))).toEqual(['path', 'garden']);
  });

  it('is selected by a click on its free space', () => {
    expect(render(garden()).hitTest(px(0.5, 0.5))).toBe('garden');
  });

  it('is painted before the beds inside it (the DOM order follows the hit class)', () => {
    const scene = buildScene(garden(), VIEW, NO_SELECTION, {});
    const order = scene.shapes.map((shape) => shape.entry.key);
    expect(order.indexOf('garden')).toBeLessThan(order.indexOf('inner'));
  });

  it('keeps a location without the mark on the bed rank (a plan cached before #2913)', () => {
    expect(entryOf(garden(false), 'garden').layer).toBe(1);
    expect(entryOf(garden(), 'garden').layer).toBe(3);
  });
});

describe('an area looks like an area (§9.5)', () => {
  const palette = planPalette(lightTheme);

  it('has the light area wash and the dotted outline whatever its bed status; a bed keeps its status look', () => {
    const model = garden();
    const area = shapeStyle(entryOf(model, 'garden'), false, false, palette);
    expect(area.fill).toBe(palette.area.fill);
    expect(area.strokeDasharray).toBe(palette.area.dash);
    // Not the planned bed's look, although the area's `bed_status` reads planned.
    expect(area.fill).not.toBe(palette.bed.planned.fill);
    expect(shapeStyle(entryOf(model, 'inner'), false, false, palette).fill).toBe(palette.bed.active.fill);
  });

  it('is named as an area for a screen reader', () => {
    const model = garden();
    const scene = buildScene(model, VIEW, NO_SELECTION, {});
    const shape = scene.shapes.find((item) => item.entry.key === 'garden')!;
    const labels = { ...options().labels, area: ({ name }: { name: string }) => `${name}, area` };
    expect(shapeAriaLabel(shape, labels)).toBe('Gemüsegarten, area');
  });
});

describe('the name of an area gives way to the names of the beds inside it', () => {
  it('draws the bed name where the two meet, and keeps the area name where nothing is in the way', () => {
    // The bed's centre sits 6 cm from the area's: the two labels collide. The larger object would keep its name
    // (GP-UX-047); an area yields instead.
    const view = viewportAt(-1, 6, 100);
    const scene = buildScene(garden(), view, NO_SELECTION, {});
    const label = (key: string) => scene.shapes.find((shape) => shape.entry.key === key)?.label ?? null;
    expect(label('inner')?.text).toBe('Beet');
    expect(label('garden')).toBeNull();

    const alone = normalizePlan(
      planResponse({ plan: null, locations: [garden().locations.garden], garden_objects: [] }),
    );
    expect(buildScene(alone, view, NO_SELECTION, {}).shapes[0].label?.text).toBe('Gemüsegarten');
  });
});
