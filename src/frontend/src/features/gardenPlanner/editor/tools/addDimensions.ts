/**
 * "Add with dimensions" (REQ-053 GP-UX-046): the keyboard and touch alternative to drawing. This
 * module turns the dialog's numbers into the geometry and the create operation; the dialog keeps
 * the text. The parent is inferred like for a drawn shape and the live validation (GP-UX-053)
 * decides before anything reaches the plan.
 */
import { roundLength } from '../../model/geometry';
import { newTempKey, type PlanModel } from '../../model/planModel';
import type { GardenObjectType, Geometry, PlanOperation, Point } from '../../model/types';
import type { SelectionRef } from '../../state/gardenPlanSlice';
import type { DrawShape } from './drawMachine';
import { defaultProps } from './objectTypes';
import { inferParentKey, violationOfNew } from './validation';

export type DimensionTarget = 'bed' | 'garden_object';

export interface DimensionValues {
  target: DimensionTarget;
  /** `location_type_key` of a bed. */
  bedTypeKey: string;
  objectType: GardenObjectType;
  name: string;
  shape: DrawShape;
  x: number | null;
  y: number | null;
  width: number | null;
  length: number | null;
  radius: number | null;
  rotation: number | null;
  strokeWidth: number | null;
  /** Polygon and polyline points; `null` = a field that is not a number yet. */
  points: ([number, number] | null)[];
}

/** Which dialog fields a shape needs (the others are hidden). */
export const SHAPE_FIELDS: Record<
  DrawShape,
  readonly ('x' | 'y' | 'width' | 'length' | 'radius' | 'rotation' | 'strokeWidth' | 'points')[]
> = {
  rect: ['x', 'y', 'width', 'length', 'rotation'],
  circle: ['x', 'y', 'radius'],
  polygon: ['points'],
  polyline: ['points', 'strokeWidth'],
};

export type GeometryResult = { geometry: Geometry } | { missing: string };

/** The geometry the values describe, or the first field that is missing or not a number. */
export function geometryOfValues(values: DimensionValues): GeometryResult {
  switch (values.shape) {
    case 'rect': {
      const [x, y, w, l] = [values.x, values.y, values.width, values.length];
      if (x === null) return { missing: 'x' };
      if (y === null) return { missing: 'y' };
      if (w === null) return { missing: 'width' };
      if (l === null) return { missing: 'length' };
      return {
        geometry: {
          kind: 'rect',
          origin: [roundLength(x), roundLength(y)],
          width_m: roundLength(w),
          length_m: roundLength(l),
          rotation_deg: roundLength(values.rotation ?? 0),
        },
      };
    }
    case 'circle': {
      if (values.x === null) return { missing: 'x' };
      if (values.y === null) return { missing: 'y' };
      if (values.radius === null) return { missing: 'radius' };
      return {
        geometry: {
          kind: 'circle',
          origin: [roundLength(values.x), roundLength(values.y)],
          radius_m: roundLength(values.radius),
        },
      };
    }
    default: {
      const points: Point[] = [];
      for (let i = 0; i < values.points.length; i += 1) {
        const p = values.points[i];
        if (p === null) return { missing: `point${i}` };
        points.push([roundLength(p[0]), roundLength(p[1])]);
      }
      if (values.shape === 'polygon')
        return { geometry: { kind: 'polygon', points, rotation_deg: 0 } };
      if (values.strokeWidth === null) return { missing: 'strokeWidth' };
      return { geometry: { kind: 'polyline', points, width_m: roundLength(values.strokeWidth) } };
    }
  }
}

export type AddOutcome =
  { ok: true; ops: PlanOperation[]; selection: SelectionRef } | { ok: false; code: string };

/** The create operation for the values, or the reason the plan would refuse it. */
export function addWithDimensions(
  plan: PlanModel,
  values: DimensionValues,
  fallbackName: string,
): AddOutcome {
  const result = geometryOfValues(values);
  if ('missing' in result) return { ok: false, code: 'geometry.invalid' };
  const { geometry } = result;
  const parentKey = inferParentKey(plan, geometry);
  const violation = violationOfNew(plan, geometry, parentKey);
  if (violation) return { ok: false, code: violation };
  const tempKey = newTempKey();
  if (values.target === 'bed') {
    return {
      ok: true,
      ops: [
        {
          op: 'create_location',
          temp_key: tempKey,
          data: {
            name: values.name.trim() || fallbackName,
            location_type_key: values.bedTypeKey,
            geometry,
            ...(parentKey ? { parent_location_key: parentKey } : {}),
          },
        },
      ],
      selection: { entity: 'location', key: tempKey },
    };
  }
  return {
    ok: true,
    ops: [
      {
        op: 'create_garden_object',
        temp_key: tempKey,
        data: {
          object_type: values.objectType,
          label: values.name.trim(),
          geometry,
          props: defaultProps(values.objectType),
          ...(parentKey ? { parent_location_key: parentKey } : {}),
        },
      },
    ],
    selection: { entity: 'garden_object', key: tempKey },
  };
}
