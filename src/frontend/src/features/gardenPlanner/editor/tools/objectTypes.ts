/**
 * The garden object types a user can pick for a new object (REQ-053 §9.5, GP-UX-046), with the
 * props the server requires per type. The draw tools and the "add with dimensions" dialog share
 * this list, so a drawn trellis or lamp is valid on the wire without a second dialog.
 */
import type { GardenObjectType } from '../../model/types';

export const OBJECT_TYPES: readonly GardenObjectType[] = [
  'path',
  'lawn',
  'tree',
  'shrub',
  'building',
  'wall',
  'fence',
  'trellis',
  'water_source',
  'compost',
  'storage',
  'window',
  'door',
  'furniture',
  'lamp',
  'other',
];

/**
 * Props a new object of `type` needs to be accepted: the required ones of the closed list (a tree
 * needs a crown, a trellis a height, a lamp a kind and a height, a water source a kind). The
 * optional ones stay unset - the panel fills them in later.
 */
export function defaultProps(type: GardenObjectType): Record<string, unknown> {
  switch (type) {
    case 'tree':
      return { crown_radius_m: 1 };
    case 'trellis':
      return { height_m: 1.8 };
    case 'water_source':
      return { water_source_kind: 'tap' };
    case 'lamp':
      return { kind: 'ceiling', height_m: 2.5 };
    default:
      return {};
  }
}
