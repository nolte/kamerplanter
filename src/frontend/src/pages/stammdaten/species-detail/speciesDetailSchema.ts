import { z } from 'zod';
import type { Species } from '@/api/types';

/** Propagation method enum values — mirrors PropagationMethod in api/types.ts. */
export const PROPAGATION_METHODS = [
  'seed',
  'cutting',
  'leaf_cutting',
  'division',
  'rhizome_division',
  'bulb',
  'bulbil',
  'tuber',
  'offset',
  'runner',
  'grafting',
  'layering',
  'air_layering',
  'water_propagation',
  'tissue_culture',
  'spore',
  'self_seeding',
] as const;

/** Wood-stage enum values — mirrors WoodStage in api/types.ts. */
export const WOOD_STAGES = ['softwood', 'semi_hardwood', 'hardwood', 'herbaceous'] as const;

/** Propagation-difficulty enum values — mirrors PropagationDifficulty in api/types.ts. */
export const PROPAGATION_DIFFICULTIES = ['easy', 'moderate', 'difficult'] as const;

/** Growth-habit enum values — mirrors GrowthHabit in api/types.ts (Phase A: 12 values). */
export const GROWTH_HABITS = [
  'herb',
  'shrub',
  'subshrub',
  'tree',
  'vine',
  'groundcover',
  'grass',
  'succulent',
  'bulb_geophyte',
  'fern',
  'aquatic',
  'epiphyte',
] as const;

/** Harvest-pattern enum values — mirrors HarvestPattern in api/types.ts (REQ-007). */
export const HARVEST_PATTERNS = ['single', 'continuous', 'perennial'] as const;

/** Harvested-part enum values — mirrors HarvestedPart in api/types.ts (REQ-007). */
export const HARVESTED_PARTS = [
  'fruit',
  'seed',
  'leaf',
  'root',
  'tuber',
  'bulb',
  'flower_bud',
  'flower',
  'stem',
  'whole_plant',
] as const;

/** Climacteric-class enum values — mirrors ClimactericClass in api/types.ts (REQ-008). */
export const CLIMACTERIC_CLASSES = ['climacteric', 'non_climacteric', 'atypical'] as const;

/** Selectable months 1..12 for the propagation month picker. */
export const MONTHS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12] as const;

export const speciesEditSchema = z.object({
  scientific_name: z.string().min(1),
  common_names: z.array(z.string()),
  family_key: z.string().nullable(),
  genus: z.string(),
  growth_habit: z.enum(GROWTH_HABITS),
  root_type: z.enum(['fibrous', 'taproot', 'tuberous', 'bulbous']),
  // Empty string = "no selection" from the MUI select; normalised to null on submit.
  harvest_pattern: z.enum(HARVEST_PATTERNS).or(z.literal('')).nullable(),
  harvested_part: z.enum(HARVESTED_PARTS).or(z.literal('')).nullable(),
  climacteric: z.enum(CLIMACTERIC_CLASSES).or(z.literal('')).nullable(),
  propagation_configs: z.array(
    z.object({
      method: z.enum(PROPAGATION_METHODS),
      months: z.array(z.number().min(1).max(12)),
      // Empty string = "no selection" from the MUI select; normalised to null on submit.
      wood_stage: z.enum(WOOD_STAGES).or(z.literal('')).nullish(),
      difficulty: z.enum(PROPAGATION_DIFFICULTIES).or(z.literal('')).nullish(),
      notes: z.string().max(1000).nullish(),
    }),
  ),
  hardiness_zones: z.array(z.string()),
  native_habitat: z.string(),
  allelopathy_score: z.number().min(-1).max(1),
  base_temp: z.number(),
  description: z.string(),
  synonyms: z.array(z.string()),
  taxonomic_authority: z.string(),
  taxonomic_status: z.string(),
  container_suitable: z.enum(['yes', 'limited', 'no', '']).nullable(),
  recommended_container_volume_l: z.string(),
  min_container_depth_cm: z.number().min(1).max(200).nullable(),
  mature_height_cm: z.string(),
  mature_width_cm: z.string(),
  spacing_cm: z.string(),
  indoor_suitable: z.enum(['yes', 'limited', 'no', '']).nullable(),
  balcony_suitable: z.enum(['yes', 'limited', 'no', '']).nullable(),
  greenhouse_recommended: z.boolean(),
  support_required: z.boolean(),
  default_nutrient_plan_key: z.string().nullable(),
});

export type SpeciesFormData = z.infer<typeof speciesEditSchema>;

/** Blank form state used as the react-hook-form `defaultValues`. */
export const speciesFormDefaults: SpeciesFormData = {
  scientific_name: '',
  common_names: [],
  family_key: null,
  genus: '',
  growth_habit: 'herb',
  root_type: 'fibrous',
  harvest_pattern: null,
  harvested_part: null,
  climacteric: null,
  propagation_configs: [],
  hardiness_zones: [],
  native_habitat: '',
  allelopathy_score: 0,
  base_temp: 10,
  description: '',
  synonyms: [],
  taxonomic_authority: '',
  taxonomic_status: '',
  container_suitable: null,
  recommended_container_volume_l: '',
  min_container_depth_cm: null,
  mature_height_cm: '',
  mature_width_cm: '',
  spacing_cm: '',
  indoor_suitable: null,
  balcony_suitable: null,
  greenhouse_recommended: false,
  support_required: false,
  default_nutrient_plan_key: null,
};

/** Maps a loaded species onto the edit form shape (used with `reset`). */
export function speciesToFormValues(current: Species): SpeciesFormData {
  return {
    scientific_name: current.scientific_name,
    common_names: current.common_names,
    family_key: current.family_key,
    genus: current.genus,
    growth_habit: current.growth_habit,
    root_type: current.root_type,
    harvest_pattern: current.harvest_pattern ?? null,
    harvested_part: current.harvested_part ?? null,
    climacteric: current.climacteric ?? null,
    propagation_configs: (current.propagation_configs ?? []).map((c) => ({
      method: c.method,
      months: [...(c.months ?? [])].sort((a, b) => a - b),
      wood_stage: c.wood_stage ?? null,
      difficulty: c.difficulty ?? null,
      notes: c.notes ?? '',
    })),
    hardiness_zones: current.hardiness_zones,
    native_habitat: current.native_habitat,
    allelopathy_score: current.allelopathy_score,
    base_temp: current.base_temp,
    description: current.description ?? '',
    synonyms: current.synonyms ?? [],
    taxonomic_authority: current.taxonomic_authority ?? '',
    taxonomic_status: current.taxonomic_status ?? '',
    container_suitable: current.container_suitable ?? null,
    recommended_container_volume_l: current.recommended_container_volume_l ?? '',
    min_container_depth_cm: current.min_container_depth_cm ?? null,
    mature_height_cm: current.mature_height_cm ?? '',
    mature_width_cm: current.mature_width_cm ?? '',
    spacing_cm: current.spacing_cm ?? '',
    indoor_suitable: current.indoor_suitable ?? null,
    balcony_suitable: current.balcony_suitable ?? null,
    greenhouse_recommended: current.greenhouse_recommended ?? false,
    support_required: current.support_required ?? false,
    default_nutrient_plan_key: current.default_nutrient_plan_key ?? null,
  };
}

/** Spacing between form panels (UI-NFR-008 R-039: 24px = spacing.lg) */
export const PANEL_GAP = 4;
/** Form container max width on md+ (UI-NFR-008 R-053). */
export const FORM_MAX_WIDTH = 1280;
/** Reading-column max width for prose textareas (UI-NFR-008 R-054, ~70-80 chars). */
export const READING_COL_MAX = 760;
