import { z } from 'zod';

export const botanicalFamilySchema = z.object({
  name: z.string().min(1, 'Name is required'),
  typical_nutrient_demand: z.enum(['light', 'medium', 'heavy']).default('medium'),
  common_pests: z.array(z.string()).default([]),
  rotation_category: z.string().default(''),
});

export const speciesSchema = z.object({
  scientific_name: z.string().min(1, 'Scientific name is required'),
  common_names: z.array(z.string()).default([]),
  family_key: z.string().nullable().default(null),
  genus: z.string().default(''),
  growth_habit: z.enum(['herb', 'shrub', 'tree', 'vine', 'groundcover']).default('herb'),
  root_type: z.enum(['fibrous', 'taproot', 'tuberous', 'bulbous']).default('fibrous'),
  hardiness_zones: z.array(z.string()).default([]),
  native_habitat: z.string().default(''),
  allelopathy_score: z.number().min(-1).max(1).default(0),
  base_temp: z.number().default(10),
});

export const cultivarSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  breeder: z.string().nullable().default(null),
  breeding_year: z.number().int().nullable().default(null),
  traits: z.array(z.string()).default([]),
  patent_status: z.string().default(''),
  days_to_maturity: z.number().int().min(1).max(365).nullable().default(null),
  disease_resistances: z.array(z.string()).default([]),
});

export const siteSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  type: z.enum(['outdoor', 'greenhouse', 'indoor', 'windowsill', 'balcony', 'grow_tent']).default('indoor'),
  climate_zone: z.string().default(''),
  total_area_m2: z.number().min(0).default(0),
});

export const locationSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  site_key: z.string().min(1),
  area_m2: z.number().min(0),
  orientation: z.enum(['north', 'south', 'east', 'west']).nullable().default(null),
  light_type: z.enum(['natural', 'led', 'hps', 'cmh', 'mixed']).default('natural'),
  irrigation_system: z.enum(['manual', 'drip', 'hydro', 'mist', 'nft', 'ebb_flow']).default('manual'),
});

export const slotSchema = z.object({
  slot_id: z.string().min(1, 'Slot ID is required'),
  location_key: z.string().min(1),
  capacity_plants: z.number().int().min(1).max(20).default(1),
});

export const substrateSchema = z.object({
  type: z
    .enum(['soil', 'coco', 'clay_pebbles', 'perlite', 'living_soil', 'peat', 'rockwool_slab', 'rockwool_plug', 'vermiculite', 'none', 'orchid_bark', 'pon_mineral', 'sphagnum', 'hydro_solution'])
    .default('soil'),
  brand: z.string().nullable().default(null),
  ph_base: z.number().min(0).max(14).default(6.5),
  ec_base_ms: z.number().min(0).default(0.5),
  water_retention: z.enum(['low', 'medium', 'high']).default('medium'),
  buffer_capacity: z.enum(['low', 'medium', 'high']).default('medium'),
  reusable: z.boolean().default(false),
  max_reuse_cycles: z.number().int().min(1).default(3),
});

export const batchSchema = z.object({
  batch_id: z.string().min(1, 'Batch ID is required'),
  substrate_key: z.string().min(1),
  volume_liters: z.number().min(0),
  mixed_on: z.string().min(1),
});

export const plantInstanceSchema = z.object({
  instance_id: z.string().min(1, 'Instance ID is required'),
  species_key: z.string().min(1, 'Species is required'),
  cultivar_key: z.string().nullable().default(null),
  slot_key: z.string().nullable().default(null),
  substrate_batch_key: z.string().nullable().default(null),
  plant_name: z.string().nullable().default(null),
  planted_on: z.string().min(1),
  current_phase_key: z.string().nullable().default(null),
});

export const growthPhaseSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  display_name: z.string().default(''),
  lifecycle_key: z.string().min(1),
  typical_duration_days: z.number().int().min(1),
  sequence_order: z.number().int().min(0),
  is_terminal: z.boolean().default(false),
  allows_harvest: z.boolean().default(false),
  stress_tolerance: z.enum(['low', 'medium', 'high']).default('medium'),
});

export const lifecycleConfigSchema = z.object({
  cycle_type: z.enum(['annual', 'biennial', 'perennial']).default('annual'),
  typical_lifespan_years: z.number().int().nullable().default(null),
  dormancy_required: z.boolean().default(false),
  vernalization_required: z.boolean().default(false),
  vernalization_min_days: z.number().int().min(1).nullable().default(null),
  photoperiod_type: z.enum(['short_day', 'long_day', 'day_neutral']).default('day_neutral'),
  critical_day_length_hours: z.number().min(0).max(24).nullable().default(null),
});

export const vpdSchema = z.object({
  temp_c: z.number(),
  humidity_percent: z.number().min(0).max(100),
  phase: z.string().default('vegetative'),
});

export const gddSchema = z.object({
  daily_temps: z.array(z.tuple([z.number(), z.number()])),
  base_temp_c: z.number().default(10),
});

export const slotCapacitySchema = z.object({
  area_m2: z.number().positive(),
  plant_spacing_cm: z.number().positive(),
});

export const fertigationParamsSchema = z.object({
  method: z.literal('fertigation'),
  runs_per_day: z.number().int().min(1).max(24).default(1),
  duration_minutes: z.number().min(1).max(120).default(5),
  flow_rate_ml_min: z.number().positive().nullable().default(null),
});

export const drenchParamsSchema = z.object({
  method: z.literal('drench'),
  volume_per_feeding_liters: z.number().positive().max(100).default(1.0),
});

export const foliarParamsSchema = z.object({
  method: z.literal('foliar'),
  volume_per_spray_liters: z.number().positive().max(10).default(0.5),
});

export const topDressParamsSchema = z.object({
  method: z.literal('top_dress'),
  grams_per_plant: z.number().positive().nullable().default(null),
  grams_per_m2: z.number().positive().nullable().default(null),
});

export const methodParamsSchema = z.discriminatedUnion('method', [
  fertigationParamsSchema,
  drenchParamsSchema,
  foliarParamsSchema,
  topDressParamsSchema,
]);

export const deliveryChannelSchema = z.object({
  channel_id: z.string().min(1).max(50),
  label: z.string().max(200).default(''),
  application_method: z.enum(['fertigation', 'drench', 'foliar', 'top_dress']),
  enabled: z.boolean().default(true),
  notes: z.string().nullable().default(null),
  target_ec_ms: z.number().min(0).max(10).nullable().default(null),
  target_ph: z.number().min(0).max(14).nullable().default(null),
  method_params: methodParamsSchema.nullable().default(null),
});

export const feedingEventSchema = z.object({
  plant_key: z.string().min(1, 'Plant key is required'),
  application_method: z
    .enum(['fertigation', 'drench', 'foliar', 'top_dress'])
    .default('fertigation'),
  is_supplemental: z.boolean().default(false),
  volume_applied_liters: z.number().gt(0),
  measured_ec_before: z.number().min(0).nullable().default(null),
  measured_ec_after: z.number().min(0).nullable().default(null),
  measured_ph_before: z.number().min(0).max(14).nullable().default(null),
  measured_ph_after: z.number().min(0).max(14).nullable().default(null),
  runoff_ec: z.number().min(0).nullable().default(null),
  runoff_ph: z.number().min(0).max(14).nullable().default(null),
  runoff_volume_liters: z.number().min(0).nullable().default(null),
  notes: z.string().nullable().default(null),
});
