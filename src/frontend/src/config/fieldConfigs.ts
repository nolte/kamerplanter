/**
 * Declarative field visibility configuration per dialog/page.
 * Each field is assigned a minimum ExperienceLevel required to see it.
 */
import type { ExperienceLevel } from '@/api/types';

export interface FieldMeta {
  level: ExperienceLevel;
}

// SpeciesCreateDialog field visibility
// NOTE (v1.1 / F-004): description + growth_habit moved from beginner → intermediate.
// Beginners use QuickAddPlantDialog (search-first), not SpeciesCreateDialog.
export const speciesFieldConfig: Record<string, FieldMeta> = {
  // intermediate (Stammdaten nav is intermediate+)
  common_names: { level: 'intermediate' },
  description: { level: 'intermediate' },
  growth_habit: { level: 'intermediate' },
  scientific_name: { level: 'intermediate' },
  family_key: { level: 'intermediate' },
  genus: { level: 'intermediate' },
  // expert
  root_type: { level: 'expert' },
  allelopathy_score: { level: 'expert' },
  hardiness_zones: { level: 'expert' },
  native_habitat: { level: 'expert' },
  base_temp: { level: 'expert' },
  synonyms: { level: 'expert' },
  taxonomic_authority: { level: 'expert' },
  taxonomic_status: { level: 'expert' },
};

// PlantingRunCreateDialog field visibility
export const plantingRunFieldConfig: Record<string, FieldMeta> = {
  // beginner
  name: { level: 'beginner' },
  entries: { level: 'beginner' },
  planned_start_date: { level: 'beginner' },
  // intermediate
  run_type: { level: 'intermediate' },
  site_key: { level: 'intermediate' },
  location_key: { level: 'intermediate' },
  notes: { level: 'intermediate' },
  // expert
  substrate_batch_key: { level: 'expert' },
  source_plant_key: { level: 'expert' },
};

// SiteCreateDialog field visibility
export const siteFieldConfig: Record<string, FieldMeta> = {
  // beginner
  name: { level: 'beginner' },
  type: { level: 'beginner' },
  // intermediate
  climate_zone: { level: 'intermediate' },
  total_area_m2: { level: 'intermediate' },
  // expert
  timezone: { level: 'expert' },
};

// GrowthPhaseDialog field visibility
export const growthPhaseFieldConfig: Record<string, FieldMeta> = {
  // beginner
  name: { level: 'beginner' },
  duration_days: { level: 'beginner' },
  // intermediate
  photoperiod_hours: { level: 'intermediate' },
  temp_day_celsius: { level: 'intermediate' },
  temp_night_celsius: { level: 'intermediate' },
  // expert
  vpd_min_kpa: { level: 'expert' },
  vpd_max_kpa: { level: 'expert' },
  ec_min_ms: { level: 'expert' },
  ec_max_ms: { level: 'expert' },
  ph_min: { level: 'expert' },
  ph_max: { level: 'expert' },
  humidity_min_percent: { level: 'expert' },
  humidity_max_percent: { level: 'expert' },
  ppfd_min: { level: 'expert' },
  ppfd_max: { level: 'expert' },
};

// FertilizerCreateDialog field visibility
export const fertilizerFieldConfig: Record<string, FieldMeta> = {
  // beginner
  product_name: { level: 'beginner' },
  manufacturer: { level: 'beginner' },
  type: { level: 'beginner' },
  // intermediate
  npk_ratio: { level: 'intermediate' },
  recommended_application: { level: 'intermediate' },
  dosage_ml_per_liter: { level: 'intermediate' },
  // expert
  ec_contribution_per_ml: { level: 'expert' },
  ph_effect: { level: 'expert' },
  mixing_priority: { level: 'expert' },
  tank_safe: { level: 'expert' },
};

// Navigation items: which minimum level is required
export const navItemConfig: Record<string, ExperienceLevel> = {
  // beginner (5 items)
  '/dashboard': 'beginner',
  '/pflege': 'beginner',
  '/pflanzen/plant-instances': 'beginner',
  '/aufgaben/queue': 'beginner',
  '/kalender': 'intermediate',
  // intermediate adds
  '/standorte/sites': 'intermediate',
  '/duengung/fertilizers': 'intermediate',
  '/duengung/plans': 'intermediate',
  '/stammdaten/botanical-families': 'intermediate',
  '/stammdaten/species': 'intermediate',
  // expert (all others)
  '/stammdaten/companion-planting': 'expert',
  '/stammdaten/crop-rotation': 'expert',
  '/standorte/substrates': 'expert',
  '/standorte/tanks': 'expert',
  '/standorte/watering-events': 'expert',
  '/pflanzen/calculations': 'expert',
  '/duengung/feeding-events': 'expert',
  '/duengung/calculations': 'expert',
  '/pflanzenschutz/pests': 'expert',
  '/pflanzenschutz/diseases': 'expert',
  '/pflanzenschutz/treatments': 'expert',
  '/ernte/batches': 'expert',
  '/aufgaben/workflows': 'expert',
  '/durchlaeufe/planting-runs': 'expert',
};

// Section headers: the minimum level where the section appears
export const navSectionConfig: Record<string, ExperienceLevel> = {
  stammdaten: 'intermediate',
  standorte: 'intermediate',
  pflanzen: 'beginner',
  duengung: 'intermediate',
  pflanzenschutz: 'expert',
  ernte: 'expert',
  aufgaben: 'beginner',
  durchlaeufe: 'expert',
};
