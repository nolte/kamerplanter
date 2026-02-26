// Enums (mirrors src/backend/app/common/enums.py)

export type GrowthHabit = 'herb' | 'shrub' | 'tree' | 'vine' | 'groundcover';
export type RootType = 'fibrous' | 'taproot' | 'tuberous' | 'bulbous';
export type PhotoperiodType = 'short_day' | 'long_day' | 'day_neutral';
export type CycleType = 'annual' | 'biennial' | 'perennial';
export type StressTolerance = 'low' | 'medium' | 'high';
export type TransitionTriggerType = 'time_based' | 'manual' | 'event_based' | 'conditional';
export type SiteType = 'outdoor' | 'greenhouse' | 'indoor';
export type LightType = 'natural' | 'led' | 'hps' | 'cmh' | 'mixed';
export type IrrigationSystem = 'manual' | 'drip' | 'hydro' | 'mist';
export type SubstrateType =
  | 'soil'
  | 'coco'
  | 'rockwool'
  | 'clay_pebbles'
  | 'perlite'
  | 'living_soil'
  | 'hydro_solution';
export type NutrientDemand = 'light' | 'medium' | 'heavy';
export type RootDepth = 'shallow' | 'medium' | 'deep';
export type FrostTolerance = 'sensitive' | 'moderate' | 'hardy' | 'very_hardy';
export type PollinationType = 'insect' | 'wind' | 'self';
export type WaterRetention = 'low' | 'medium' | 'high';
export type BufferCapacity = 'low' | 'medium' | 'high';
export type Orientation = 'north' | 'south' | 'east' | 'west';
export type PlantTrait =
  | 'disease_resistant'
  | 'pest_resistant'
  | 'high_yield'
  | 'compact'
  | 'drought_tolerant'
  | 'cold_hardy'
  | 'heat_tolerant'
  | 'early_maturing'
  | 'long_season'
  | 'ornamental'
  | 'heirloom'
  | 'hybrid'
  | 'f1';

// Pagination

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  offset: number;
  limit: number;
}

// Error response (NFR-006)

export interface ApiErrorResponse {
  error_id: string;
  error_code: string;
  message: string;
  details: ApiErrorDetail[];
  timestamp: string;
  path: string;
  method: string;
}

export interface ApiErrorDetail {
  field: string;
  reason: string;
  code: string;
}

// Botanical Families

export interface PhRange {
  min_ph: number;
  max_ph: number;
}

export interface BotanicalFamily {
  key: string;
  name: string;
  common_name_de: string;
  common_name_en: string;
  order: string | null;
  description: string;
  typical_nutrient_demand: NutrientDemand;
  nitrogen_fixing: boolean;
  typical_root_depth: RootDepth;
  soil_ph_preference: PhRange | null;
  frost_tolerance: FrostTolerance;
  typical_growth_forms: GrowthHabit[];
  common_pests: string[];
  common_diseases: string[];
  pollination_type: PollinationType[];
  rotation_category: string;
  created_at: string | null;
  updated_at: string | null;
}

export interface BotanicalFamilyCreate {
  name: string;
  common_name_de?: string;
  common_name_en?: string;
  order?: string | null;
  description?: string;
  typical_nutrient_demand?: NutrientDemand;
  nitrogen_fixing?: boolean;
  typical_root_depth?: RootDepth;
  soil_ph_preference?: PhRange | null;
  frost_tolerance?: FrostTolerance;
  typical_growth_forms?: GrowthHabit[];
  common_pests?: string[];
  common_diseases?: string[];
  pollination_type?: PollinationType[];
  rotation_category?: string;
}

// Species

export interface Species {
  key: string;
  scientific_name: string;
  common_names: string[];
  family_key: string | null;
  genus: string;
  hardiness_zones: string[];
  native_habitat: string;
  growth_habit: GrowthHabit;
  root_type: RootType;
  allelopathy_score: number;
  base_temp: number;
  synonyms: string[];
  taxonomic_authority: string;
  taxonomic_status: string;
  description: string;
  created_at: string | null;
  updated_at: string | null;
}

export interface SpeciesCreate {
  scientific_name: string;
  common_names?: string[];
  family_key?: string | null;
  genus?: string;
  hardiness_zones?: string[];
  native_habitat?: string;
  growth_habit?: GrowthHabit;
  root_type?: RootType;
  allelopathy_score?: number;
  base_temp?: number;
  synonyms?: string[];
  taxonomic_authority?: string;
  taxonomic_status?: string;
  description?: string;
}

// Cultivars

export interface Cultivar {
  key: string;
  name: string;
  species_key: string;
  breeder: string | null;
  breeding_year: number | null;
  traits: PlantTrait[];
  patent_status: string;
  days_to_maturity: number | null;
  disease_resistances: string[];
  created_at: string | null;
  updated_at: string | null;
}

export interface CultivarCreate {
  name: string;
  species_key: string;
  breeder?: string | null;
  breeding_year?: number | null;
  traits?: PlantTrait[];
  patent_status?: string;
  days_to_maturity?: number | null;
  disease_resistances?: string[];
}

// Sites

export interface Site {
  key: string;
  name: string;
  type: SiteType;
  gps_coordinates: [number, number] | null;
  climate_zone: string;
  total_area_m2: number;
  timezone: string;
  created_at: string | null;
  updated_at: string | null;
}

export interface SiteCreate {
  name: string;
  type?: SiteType;
  gps_coordinates?: [number, number] | null;
  climate_zone?: string;
  total_area_m2?: number;
  timezone?: string;
}

// Locations

export interface Location {
  key: string;
  name: string;
  site_key: string;
  area_m2: number;
  orientation: Orientation | null;
  light_type: LightType;
  irrigation_system: IrrigationSystem;
  dimensions: [number, number, number];
  lights_on: string | null;
  lights_off: string | null;
  use_dynamic_sunrise: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface LocationCreate {
  name: string;
  site_key: string;
  area_m2: number;
  orientation?: Orientation | null;
  light_type?: LightType;
  irrigation_system?: IrrigationSystem;
  dimensions?: [number, number, number];
  lights_on?: string | null;
  lights_off?: string | null;
  use_dynamic_sunrise?: boolean;
}

// Slots

export interface Slot {
  key: string;
  slot_id: string;
  location_key: string;
  position: [number, number];
  capacity_plants: number;
  currently_occupied: boolean;
  last_sanitization: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface SlotCreate {
  slot_id: string;
  location_key: string;
  position?: [number, number];
  capacity_plants?: number;
}

// Substrates

export interface Substrate {
  key: string;
  type: SubstrateType;
  brand: string | null;
  ph_base: number;
  ec_base_ms: number;
  water_retention: WaterRetention;
  air_porosity_percent: number;
  composition: Record<string, number>;
  buffer_capacity: BufferCapacity;
  reusable: boolean;
  max_reuse_cycles: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface SubstrateCreate {
  type?: SubstrateType;
  brand?: string | null;
  ph_base?: number;
  ec_base_ms?: number;
  water_retention?: WaterRetention;
  air_porosity_percent?: number;
  composition?: Record<string, number>;
  buffer_capacity?: BufferCapacity;
  reusable?: boolean;
  max_reuse_cycles?: number;
}

// Batches

export interface Batch {
  key: string;
  batch_id: string;
  substrate_key: string;
  volume_liters: number;
  mixed_on: string;
  last_amended: string | null;
  cycles_used: number;
  ph_current: number | null;
  ec_current_ms: number | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface BatchCreate {
  batch_id: string;
  substrate_key: string;
  volume_liters: number;
  mixed_on: string;
}

export interface ReusabilityResponse {
  can_reuse: boolean;
  treatments: string[];
}

// Plant Instances

export interface PlantInstance {
  key: string;
  instance_id: string;
  species_key: string;
  cultivar_key: string | null;
  slot_key: string | null;
  substrate_batch_key: string | null;
  plant_name: string | null;
  planted_on: string;
  removed_on: string | null;
  current_phase: string;
  current_phase_key: string | null;
  current_phase_started_at: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface PlantInstanceCreate {
  instance_id: string;
  species_key: string;
  cultivar_key?: string | null;
  slot_key?: string | null;
  substrate_batch_key?: string | null;
  plant_name?: string | null;
  planted_on: string;
  current_phase?: string;
}

export interface ValidatePlantingResponse {
  valid: boolean;
  warnings: string[];
  benefits: string[];
}

// Phase Control

export interface CurrentPhaseResponse {
  phase: string;
  phase_key: string | null;
  days_in_phase: number;
  next_phase: string | null;
}

export interface PhaseHistoryEntry {
  key: string;
  phase_name: string;
  entered_at: string;
  exited_at: string | null;
  actual_duration_days: number | null;
  transition_reason: string;
  performance_score: number | null;
}

export interface TransitionRequest {
  target_phase_key: string;
  reason?: string;
}

// Growth Phases

export interface GrowthPhase {
  key: string;
  name: string;
  display_name: string;
  lifecycle_key: string;
  typical_duration_days: number;
  sequence_order: number;
  is_terminal: boolean;
  allows_harvest: boolean;
  stress_tolerance: StressTolerance;
  created_at: string | null;
  updated_at: string | null;
}

export interface GrowthPhaseCreate {
  name: string;
  display_name?: string;
  lifecycle_key: string;
  typical_duration_days: number;
  sequence_order: number;
  is_terminal?: boolean;
  allows_harvest?: boolean;
  stress_tolerance?: StressTolerance;
}

// Lifecycle Config

export interface LifecycleConfig {
  key: string;
  species_key: string;
  cycle_type: CycleType;
  typical_lifespan_years: number | null;
  dormancy_required: boolean;
  vernalization_required: boolean;
  vernalization_min_days: number | null;
  photoperiod_type: PhotoperiodType;
  critical_day_length_hours: number | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface LifecycleConfigCreate {
  species_key: string;
  cycle_type?: CycleType;
  typical_lifespan_years?: number | null;
  dormancy_required?: boolean;
  vernalization_required?: boolean;
  vernalization_min_days?: number | null;
  photoperiod_type?: PhotoperiodType;
  critical_day_length_hours?: number | null;
}

// Profiles

export interface RequirementProfile {
  key: string;
  phase_key: string;
  light_ppfd_target: number;
  photoperiod_hours: number;
  light_spectrum: Record<string, number>;
  temperature_day_c: number;
  temperature_night_c: number;
  humidity_day_percent: number;
  humidity_night_percent: number;
  vpd_target_kpa: number;
  co2_ppm: number | null;
  irrigation_frequency_days: number;
  irrigation_volume_ml_per_plant: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface RequirementProfileCreate {
  phase_key: string;
  light_ppfd_target?: number;
  photoperiod_hours?: number;
  light_spectrum?: Record<string, number>;
  temperature_day_c?: number;
  temperature_night_c?: number;
  humidity_day_percent?: number;
  humidity_night_percent?: number;
  vpd_target_kpa?: number;
  co2_ppm?: number | null;
  irrigation_frequency_days?: number;
  irrigation_volume_ml_per_plant?: number;
}

export interface NutrientProfile {
  key: string;
  phase_key: string;
  npk_ratio: [number, number, number];
  target_ec_ms: number;
  target_ph: number;
  calcium_ppm: number | null;
  magnesium_ppm: number | null;
  micro_nutrients: Record<string, number>;
  created_at: string | null;
  updated_at: string | null;
}

export interface NutrientProfileCreate {
  phase_key: string;
  npk_ratio?: [number, number, number];
  target_ec_ms?: number;
  target_ph?: number;
  calcium_ppm?: number | null;
  magnesium_ppm?: number | null;
  micro_nutrients?: Record<string, number>;
}

// Companion Planting

export interface CompatibleSpecies {
  species_key: string;
  scientific_name: string | null;
  score: number;
}

export interface IncompatibleSpecies {
  species_key: string;
  scientific_name: string | null;
  reason: string;
}

export interface CompatibilitySet {
  from_species_key: string;
  to_species_key: string;
  score?: number;
}

export interface IncompatibilitySet {
  from_species_key: string;
  to_species_key: string;
  reason?: string;
}

// Crop Rotation

export interface RotationSuccessor {
  family_key: string;
  name: string | null;
  wait_years: number;
}

export interface RotationSuccessorSet {
  from_family_key: string;
  to_family_key: string;
  wait_years?: number;
}

// Calculations

export interface VPDRequest {
  temp_c: number;
  humidity_percent: number;
  phase?: string;
}

export interface VPDResponse {
  vpd_kpa: number;
  status: string;
  recommendation: string;
}

export interface GDDRequest {
  daily_temps: [number, number][];
  base_temp_c?: number;
}

export interface GDDResponse {
  accumulated_gdd: number;
  days_counted: number;
}

export interface PhotoperiodTransitionRequest {
  current_hours: number;
  target_hours: number;
  transition_days?: number;
  ppfd?: number;
  lights_on_time?: string;
}

export interface PhotoperiodScheduleEntry {
  day: number;
  photoperiod_hours: number;
  lights_on: string;
  lights_off: string;
  dli: number;
}

export interface SunTimesRequest {
  latitude: number;
  longitude: number;
  date: string;
  timezone?: string;
}

export interface SunTimesResponse {
  date: string;
  sunrise: string;
  sunset: string;
  dawn: string;
  dusk: string;
  day_length_hours: number;
}

export interface SlotCapacityRequest {
  area_m2: number;
  plant_spacing_cm: number;
}

export interface SlotCapacityResponse {
  max_capacity: number;
  optimal_range: [number, number];
  plants_per_m2: number;
}
