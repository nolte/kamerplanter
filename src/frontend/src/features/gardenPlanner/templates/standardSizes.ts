/**
 * The standard sizes of GP-FR-045 as the quick choice of "add with dimensions": a bed template read as the
 * numbers the dialog fills in (shape, size, bed type, height). Pure; the dialog keeps the text.
 */
import type { BedTemplate } from '../model/types';

export interface StandardSize {
  shape: 'rect' | 'circle';
  /** Rectangle only. */
  width: number | null;
  length: number | null;
  /** Circle only. */
  radius: number | null;
  bedTypeKey: string;
  /** Prefilled height (GP-FR-043); `null` = the template states none. */
  heightM: number | null;
}

/** The dialog values of `template`, or `null` for a polygon (no number fields describe it). */
export function standardSizeOf(template: BedTemplate): StandardSize | null {
  const geometry = template.default_geometry;
  const base = { bedTypeKey: template.location_type_key, heightM: template.height_m ?? null };
  if (geometry.kind === 'rect') {
    return {
      ...base,
      shape: 'rect',
      width: geometry.width_m,
      length: geometry.length_m,
      radius: null,
    };
  }
  if (geometry.kind === 'circle') {
    return { ...base, shape: 'circle', width: null, length: null, radius: geometry.radius_m };
  }
  return null;
}

/** The system templates the dialog offers, in the order the catalogue answered. */
export function standardSizeTemplates(templates: readonly BedTemplate[]): BedTemplate[] {
  return templates.filter((template) => template.is_system && standardSizeOf(template) !== null);
}
