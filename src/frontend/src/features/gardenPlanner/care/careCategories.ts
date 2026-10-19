/**
 * Which care categories a bed offers and which short form each one asks for (REQ-053 §12.1, F-03,
 * GP-FR-084). Pure functions: the dialogs and their tests share them.
 */
import type { GrowingMediumKind } from '../bed/types';
import type { CareUnit } from './careTypes';

/** Every category a bed task or a care log line may take, before the context narrows it (§12.1). */
export const BED_CARE_CATEGORIES = [
  'watering',
  'feeding',
  'mulching',
  'weeding',
  'soil_loosening',
  'pruning',
  'thinning',
  'sowing',
  'pricking_out',
  'transplant',
  'harvest',
  'observation',
  'pest_control',
  'soil_amendment',
  'liming',
  'hilling',
  'tillage',
  'flush',
  'ec_check',
  'ph_adjustment',
  'covering',
  'uncovering',
  'ventilating',
  'rainfall',
  'pollinating',
  'maintenance',
] as const;

/** The care log also knows a free note; it is not a task category (`note`, §20.10). */
export const NOTE_CATEGORY = 'note';

/** `flush`, `ec_check`, `ph_adjustment`: beds with a substrate, not native soil (W-007). */
const SUBSTRATE_ONLY = new Set(['flush', 'ec_check', 'ph_adjustment']);
/** `hilling`, `tillage`, `liming`: soil beds (F-03). */
const SOIL_ONLY = new Set(['hilling', 'tillage', 'liming']);
/** Pot and substrate beds do not have soil to work. */
const NOT_SOIL: ReadonlySet<GrowingMediumKind> = new Set(['potting_mix', 'mineral_substrate']);
/** `ventilating` only where there is a cover to open (F-03). */
const COVERED_TYPES = new Set(['greenhouse', 'greenhouse_bed', 'cold_frame', 'tent']);
/**
 * The care log is not the proof of a plant protection treatment (PflSchG section 11, E-16); those
 * go through the IPM form, so the log without a task does not offer them.
 */
const NOT_LOGGABLE = new Set(['pest_control', 'ipm']);

export interface CareContext {
  /** `soil_profile.growing_medium_kind` of the bed; unknown keeps every category on offer. */
  growingMedium?: GrowingMediumKind | null;
  /** `location_type_key` of the bed (`greenhouse_bed`, `cold_frame`, `tent`, `raised_bed` ...). */
  locationTypeKey?: string | null;
}

/** Whether `category` suits the bed (F-03); an unknown medium or type hides nothing. */
export function categoryFitsContext(category: string, context: CareContext): boolean {
  const medium = context.growingMedium ?? null;
  if (SUBSTRATE_ONLY.has(category)) return medium !== 'native_soil';
  if (SOIL_ONLY.has(category)) return medium === null || !NOT_SOIL.has(medium);
  if (category === 'ventilating') {
    return context.locationTypeKey == null || COVERED_TYPES.has(context.locationTypeKey);
  }
  return true;
}

/** The categories the dialog offers; `forLog` adds the free note and drops the treatments. */
export function categoriesFor(context: CareContext, mode: 'task' | 'log'): string[] {
  const fitting: string[] = BED_CARE_CATEGORIES.filter(
    (category) => categoryFitsContext(category, context) && (mode === 'task' || !NOT_LOGGABLE.has(category)),
  );
  return mode === 'log' ? [...fitting, NOTE_CATEGORY] : fitting;
}

/** The short form a category asks for (GP-FR-084); everything else is a note. */
export type FormKind = 'watering' | 'rainfall' | 'feeding' | 'amendment' | 'mulching' | 'cover' | 'harvest' | 'note';

export function formKindOf(category: string): FormKind {
  switch (category) {
    case 'watering':
    case 'flush':
      return 'watering';
    case 'rainfall':
      return 'rainfall';
    case 'feeding':
      return 'feeding';
    case 'soil_amendment':
    case 'liming':
      return 'amendment';
    case 'mulching':
      return 'mulching';
    case 'covering':
    case 'uncovering':
      return 'cover';
    case 'harvest':
      return 'harvest';
    default:
      return 'note';
  }
}

/** Units each form kind offers; the first is the default. */
export const UNITS_BY_KIND: Record<FormKind, readonly CareUnit[]> = {
  watering: ['l', 'ml', 'l_per_m2'],
  rainfall: ['l_per_m2'],
  feeding: ['ml', 'l', 'g', 'kg', 'l_per_m2', 'g_per_m2'],
  amendment: ['g_per_m2', 'kg', 'l'],
  mulching: ['cm'],
  cover: [],
  harvest: ['g', 'kg'],
  note: [],
};

/** Suggestions for the material field (free text stays possible); codes are translated in the UI. */
export const MATERIALS_BY_KIND: Partial<Record<FormKind, readonly string[]>> = {
  amendment: ['compost', 'manure', 'horn_shavings'],
  mulching: ['straw', 'grass_clippings', 'bark_mulch', 'wood_chips', 'leaves', 'cardboard', 'compost'],
  cover: ['fleece', 'net', 'foil', 'frost_cover'],
};

/** Water sources of the watering form (`WaterSource`); written into `material` of the care line. */
export const WATER_SOURCES = ['tap', 'rainwater', 'well', 'tank', 'osmose', 'distilled', 'mixed'] as const;

/** What a task is bound to: the bed itself, one plant, or something else (a tank, a run ...). */
export function taskTarget(task: { entity_type: string | null }): 'bed' | 'plant' | 'other' {
  if (task.entity_type === 'location') return 'bed';
  if (task.entity_type === 'plant_instance') return 'plant';
  return 'other';
}
