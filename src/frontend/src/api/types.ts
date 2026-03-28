// Enums (mirrors src/backend/app/common/enums.py)

export type GrowthHabit = 'herb' | 'shrub' | 'tree' | 'vine' | 'groundcover';
export type RootType = 'fibrous' | 'taproot' | 'tuberous' | 'bulbous';
export type PhotoperiodType = 'short_day' | 'long_day' | 'day_neutral';
export type CycleType = 'annual' | 'biennial' | 'perennial';
export type StressTolerance = 'low' | 'medium' | 'high';
export type TransitionTriggerType = 'time_based' | 'manual' | 'event_based' | 'conditional';
export type SiteType = 'outdoor' | 'greenhouse' | 'indoor' | 'windowsill' | 'balcony' | 'grow_tent';
export type LightType = 'natural' | 'led' | 'hps' | 'cmh' | 'mixed';
export type IrrigationSystem = 'manual' | 'drip' | 'hydro' | 'mist' | 'nft' | 'ebb_flow';
export type SubstrateType =
  | 'soil'
  | 'coco'
  | 'clay_pebbles'
  | 'perlite'
  | 'living_soil'
  | 'peat'
  | 'rockwool_slab'
  | 'rockwool_plug'
  | 'vermiculite'
  | 'none'
  | 'orchid_bark'
  | 'pon_mineral'
  | 'sphagnum'
  | 'hydro_solution';
export type NutrientDemand = 'light' | 'medium' | 'heavy';
export type RootDepth = 'shallow' | 'medium' | 'deep';
export type FrostTolerance = 'sensitive' | 'moderate' | 'hardy' | 'very_hardy';
export type Suitability = 'yes' | 'limited' | 'no';
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
export type PlantingRunType = 'monoculture' | 'clone';
export type PlantingRunStatus = 'planned' | 'active' | 'harvesting' | 'completed' | 'cancelled';
export type DiaryEntryType = 'observation' | 'problem' | 'milestone' | 'measurement' | 'photo' | 'note';
export type FertilizerType = 'base' | 'supplement' | 'booster' | 'biological' | 'ph_adjuster' | 'organic' | 'silicate';
export type PhEffect = 'acidic' | 'alkaline' | 'neutral';
export type ApplicationMethod = 'fertigation' | 'drench' | 'foliar' | 'top_dress' | 'any';
export type Bioavailability = 'immediate' | 'slow_release' | 'microbial_dependent';
export type IncompatibilitySeverity = 'critical' | 'warning' | 'minor';
export type PhaseName = 'germination' | 'seedling' | 'vegetative' | 'flowering' | 'flushing' | 'dormancy' | 'harvest';
export type ActivityCategory = 'training_hst' | 'training_lst' | 'pruning' | 'ausgeizen' | 'transplant' | 'harvest_prep' | 'propagation' | 'general';
export type StressLevel = 'none' | 'low' | 'medium' | 'high';

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
  species_count: number;
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

// Watering Guide (embedded on Species/Cultivar)

export interface SeasonalWateringAdjustment {
  months: number[];
  interval_days: number;
  volume_ml_min: number;
  volume_ml_max: number;
  label: string;
}

export interface WateringGuide {
  interval_days: number;
  volume_ml_min: number;
  volume_ml_max: number;
  watering_method: WateringMethod;
  water_quality_hint: string | null;
  practical_tip: string | null;
  seasonal_adjustments: SeasonalWateringAdjustment[];
}

// Species

export interface GrowingPeriod {
  label: string;
  sowing_indoor_weeks_before_last_frost: number | null;
  sowing_outdoor_after_last_frost_days: number | null;
  direct_sow_months: number[];
  growth_months: number[];
  harvest_months: number[];
  bloom_months: number[];
  harvest_from_year: number | null;
  bloom_from_year: number | null;
}

export interface Species {
  key: string;
  scientific_name: string;
  common_names: string[];
  family_key: string | null;
  family_name: string | null;
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
  sowing_indoor_weeks_before_last_frost: number | null;
  sowing_outdoor_after_last_frost_days: number | null;
  direct_sow_months: number[];
  harvest_months: number[];
  bloom_months: number[];
  harvest_from_year: number | null;
  bloom_from_year: number | null;
  frost_sensitivity: FrostTolerance | null;
  plant_category: string | null;
  allows_harvest: boolean;
  growing_periods: GrowingPeriod[];
  container_suitable: Suitability | null;
  recommended_container_volume_l: string | null;
  min_container_depth_cm: number | null;
  mature_height_cm: string | null;
  mature_width_cm: string | null;
  spacing_cm: string | null;
  indoor_suitable: Suitability | null;
  balcony_suitable: Suitability | null;
  greenhouse_recommended: boolean;
  support_required: boolean;
  watering_guide: WateringGuide | null;
  default_nutrient_plan_key: string | null;
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
  sowing_indoor_weeks_before_last_frost?: number | null;
  sowing_outdoor_after_last_frost_days?: number | null;
  direct_sow_months?: number[];
  harvest_months?: number[];
  bloom_months?: number[];
  harvest_from_year?: number | null;
  bloom_from_year?: number | null;
  frost_sensitivity?: FrostTolerance | null;
  plant_category?: string | null;
  allows_harvest?: boolean;
  growing_periods?: GrowingPeriod[];
  container_suitable?: Suitability | null;
  recommended_container_volume_l?: string | null;
  min_container_depth_cm?: number | null;
  mature_height_cm?: string | null;
  mature_width_cm?: string | null;
  spacing_cm?: string | null;
  indoor_suitable?: Suitability | null;
  balcony_suitable?: Suitability | null;
  greenhouse_recommended?: boolean;
  support_required?: boolean;
  watering_guide?: WateringGuide | null;
  default_nutrient_plan_key?: string | null;
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
  phase_watering_overrides: Record<string, number> | null;
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
  phase_watering_overrides?: Record<string, number> | null;
}

// Sites

// Water config types

export interface TapWaterProfile {
  ec_ms: number;
  ph: number;
  alkalinity_ppm: number;
  gh_ppm: number;
  calcium_ppm: number;
  magnesium_ppm: number;
  chlorine_ppm: number;
  chloramine_ppm: number;
  measurement_date: string | null;
  source_note: string | null;
}

export interface RoWaterProfile {
  ec_ms: number;
  ph: number;
}

export interface SiteWaterConfig {
  has_ro_system: boolean;
  tap_water_profile?: TapWaterProfile | null;
  ro_water_profile?: RoWaterProfile | null;
}

export interface WaterSourceWarning {
  code: string;
  message: string;
  severity: string;
}

export interface Site {
  key: string;
  name: string;
  type: SiteType;
  gps_coordinates: [number, number] | null;
  climate_zone: string;
  total_area_m2: number;
  timezone: string;
  water_config?: SiteWaterConfig | null;
  water_config_warnings?: WaterSourceWarning[];
  last_frost_date_avg: string | null;
  first_frost_date_avg: string | null;
  eisheilige_date: string | null;
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
  water_config?: SiteWaterConfig | null;
  last_frost_date_avg?: string | null;
  first_frost_date_avg?: string | null;
  eisheilige_date?: string | null;
}

// Locations

export interface Location {
  key: string;
  name: string;
  site_key: string;
  parent_location_key: string | null;
  location_type_key: string;
  depth: number;
  path: string;
  area_m2: number;
  orientation: Orientation | null;
  light_type: LightType;
  irrigation_system: IrrigationSystem;
  dimensions: [number, number, number];
  lights_on: string | null;
  lights_off: string | null;
  use_dynamic_sunrise: boolean;
  tank_key: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface LocationCreate {
  name: string;
  site_key: string;
  parent_location_key?: string | null;
  location_type_key?: string;
  area_m2: number;
  orientation?: Orientation | null;
  light_type?: LightType;
  irrigation_system?: IrrigationSystem;
  dimensions?: [number, number, number];
  lights_on?: string | null;
  lights_off?: string | null;
  use_dynamic_sunrise?: boolean;
  tank_key?: string | null;
}

export interface LocationTreeNode {
  key: string;
  name: string;
  location_type_key: string;
  depth: number;
  parent_location_key: string | null;
  slot_count: number;
  children: LocationTreeNode[];
}

export interface LocationType {
  key: string;
  name: string;
  name_en: string | null;
  icon: string | null;
  is_indoor: boolean;
  is_system: boolean;
  sort_order: number;
  description: string | null;
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

export interface MixComponent {
  substrate_key: string;
  fraction: number;
}

export interface Substrate {
  key: string;
  type: SubstrateType;
  brand: string | null;
  name_de: string;
  name_en: string;
  is_mix: boolean;
  mix_components: MixComponent[];
  ph_base: number;
  ec_base_ms: number;
  water_retention: WaterRetention;
  air_porosity_percent: number;
  composition: Record<string, number>;
  buffer_capacity: BufferCapacity;
  reusable: boolean;
  max_reuse_cycles: number;
  water_holding_capacity_percent: number | null;
  easily_available_water_percent: number | null;
  cec_meq_per_100g: number | null;
  particle_size_mm: number | null;
  bulk_density_g_per_l: number | null;
  irrigation_strategy: IrrigationStrategy | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface SubstrateMixRequest {
  name_de: string;
  name_en: string;
  components: MixComponent[];
}

export interface SubstrateCreate {
  type?: SubstrateType;
  brand?: string | null;
  name_de?: string;
  name_en?: string;
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
  temperature_c: number | null;
  ph_history: number[];
  ec_history: number[];
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
  site_key: string | null;
  location_key: string | null;
  slot_key: string | null;
  substrate_batch_key: string | null;
  substrate_key: string | null;
  plant_name: string | null;
  planted_on: string;
  removed_on: string | null;
  current_phase: string;
  current_phase_key: string | null;
  current_phase_started_at: string | null;
  container_volume_liters: number | null;
  substrate_type_override: SubstrateType | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface PlantInstanceCreate {
  instance_id: string;
  species_key: string;
  cultivar_key?: string | null;
  site_key?: string | null;
  location_key?: string | null;
  slot_key?: string | null;
  substrate_batch_key?: string | null;
  substrate_key?: string | null;
  plant_name?: string | null;
  planted_on: string;
  current_phase_key?: string | null;
  container_volume_liters?: number | null;
  substrate_type_override?: SubstrateType | null;
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
  force?: boolean;
}

// Growth Phases

export interface GrowthPhase {
  key: string;
  name: string;
  display_name: string;
  description: string;
  lifecycle_key: string;
  typical_duration_days: number;
  sequence_order: number;
  is_terminal: boolean;
  allows_harvest: boolean;
  stress_tolerance: StressTolerance;
  watering_interval_days: number | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface GrowthPhaseCreate {
  name: string;
  display_name?: string;
  description?: string;
  lifecycle_key: string;
  typical_duration_days: number;
  sequence_order: number;
  is_terminal?: boolean;
  allows_harvest?: boolean;
  stress_tolerance?: StressTolerance;
  watering_interval_days?: number | null;
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
  benefit_score: number;
  benefit_reason: string;
}

export interface RotationSuccessorSet {
  from_family_key: string;
  to_family_key: string;
  wait_years?: number;
  benefit_score?: number;
  benefit_reason?: string;
}

// Family Relationships

export interface PestRisk {
  family_key: string;
  name: string | null;
  shared_pests: string[];
  shared_diseases: string[];
  risk_level: string;
}

export interface FamilyCompatible {
  family_key: string;
  name: string | null;
  benefit_type: string;
  compatibility_score: number;
  notes: string;
}

export interface FamilyIncompatible {
  family_key: string;
  name: string | null;
  reason: string;
  severity: string;
}

// Companion Planting Recommendations

export interface CompanionRecommendation {
  species_key: string;
  scientific_name: string | null;
  score: number;
  match_level: 'species' | 'family';
  benefit_type?: string;
}

export interface CompanionRecommendationResponse {
  matches: CompanionRecommendation[];
  match_level: 'species' | 'family';
}

// Vernalization

export interface VernalizationRequest {
  cold_days_accumulated: number;
  required_min_days: number;
}

export interface VernalizationResponse {
  progress_percent: number;
  days_remaining: number;
  is_complete: boolean;
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

// Planting Runs (REQ-013)

export interface PlantingRunEntry {
  key: string;
  run_key: string;
  species_key: string;
  cultivar_key: string | null;
  quantity: number;
  id_prefix: string;
  spacing_cm: number | null;
  notes: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface PlantingRunEntryCreate {
  species_key: string;
  cultivar_key?: string | null;
  quantity: number;
  id_prefix: string;
  spacing_cm?: number | null;
  notes?: string | null;
}

export interface PlantDiaryEntry {
  key: string;
  tenant_key: string;
  plant_key: string;
  entry_type: DiaryEntryType;
  title: string | null;
  text: string;
  photo_refs: string[];
  tags: string[];
  measurements: Record<string, unknown> | null;
  created_by: string;
  created_at: string | null;
  updated_at: string | null;
}

export interface PhaseSummary {
  dominant_phase: string | null;
  dominant_phase_count: number;
  total_plant_count: number;
  all_phases: Record<string, number>;
}

export interface PhaseTimelineEntry {
  phase_key: string;
  phase_name: string;
  display_name: string;
  description?: string;
  sequence_order: number;
  typical_duration_days: number;
  status: 'completed' | 'current' | 'projected';
  actual_entered_at: string | null;
  actual_exited_at: string | null;
  actual_duration_days: number | null;
  projected_start: string | null;
  projected_end: string | null;
}

export interface SpeciesPhaseTimeline {
  species_key: string;
  species_name: string | null;
  lifecycle_key: string;
  plant_count: number;
  phases: PhaseTimelineEntry[];
}

export interface PhaseHistoryDateUpdate {
  entered_at?: string;
  exited_at?: string;
}

export interface PlantingRun {
  key: string;
  name: string;
  run_type: PlantingRunType;
  status: PlantingRunStatus;
  planned_quantity: number;
  actual_quantity: number;
  current_phase_key: string | null;
  current_phase_started_at: string | null;
  lifecycle_config_key: string | null;
  location_key: string | null;
  substrate_batch_key: string | null;
  planned_start_date: string | null;
  started_at: string | null;
  completed_at: string | null;
  source_plant_key: string | null;
  notes: string | null;
  phase_summary?: PhaseSummary | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface PlantingRunCreate {
  name: string;
  run_type: PlantingRunType;
  location_key?: string | null;
  substrate_batch_key?: string | null;
  planned_start_date?: string | null;
  source_plant_key?: string | null;
  notes?: string | null;
  entries?: PlantingRunEntryCreate[];
}

export interface PlantingRunUpdate {
  name?: string;
  location_key?: string | null;
  notes?: string | null;
  planned_start_date?: string | null;
}

export interface BatchCreatePlantsResponse {
  run_key: string;
  created_count: number;
  plant_keys: string[];
  instance_ids: string[];
  slots_assigned: number;
}

export interface AdoptPlantsRequest {
  plant_keys: string[];
}

export interface AdoptPlantsResponse {
  run_key: string;
  adopted_count: number;
  adopted_keys: string[];
  skipped: Array<{ key: string; reason: string }>;
  run_status: string;
  run_phase: string | null;
}

export interface BatchTransitionRequest {
  target_phase_key: string;
  target_phase_name: string;
  exclude_keys?: string[];
}

export interface BatchTransitionResponse {
  run_key: string;
  target_phase: string;
  transitioned_count: number;
  skipped_count: number;
  failed_count: number;
  transitioned_keys: string[];
  skipped_keys: string[];
  failed_keys: string[];
}

export interface BatchRemoveRequest {
  reason?: string;
  target_status?: 'completed' | 'cancelled';
}

export interface BatchRemoveResponse {
  run_key: string;
  removed_count: number;
  removed_keys: string[];
  final_status: string;
}

export interface PlantInRun {
  key: string;
  instance_id: string;
  species_key: string;
  cultivar_key: string | null;
  plant_name: string | null;
  planted_on: string;
  removed_on: string | null;
  current_phase: string;
  detached_at: string | null;
  detach_reason: string | null;
}

// Tank enums (REQ-014)

export type TankType = 'nutrient' | 'irrigation' | 'reservoir' | 'recirculation' | 'stock_solution';
export type FillType = 'full_change' | 'top_up' | 'adjustment';
export type TankMaterial = 'plastic' | 'stainless_steel' | 'glass' | 'ibc';
export type MaintenanceType =
  | 'water_change'
  | 'cleaning'
  | 'sanitization'
  | 'calibration'
  | 'filter_change'
  | 'pump_inspection';
export type MaintenancePriority = 'low' | 'medium' | 'high' | 'critical';
export type MaintenanceStatus = 'ok' | 'due_soon' | 'overdue';

// Tanks (REQ-014)

export interface Tank {
  key: string;
  name: string;
  tank_type: TankType;
  volume_liters: number;
  material: TankMaterial;
  has_lid: boolean;
  has_air_pump: boolean;
  has_circulation_pump: boolean;
  has_heater: boolean;
  is_light_proof: boolean;
  has_uv_sterilizer: boolean;
  has_ozone_generator: boolean;
  installed_on: string | null;
  location_key: string | null;
  notes: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface TankCreate {
  name: string;
  tank_type: TankType;
  volume_liters: number;
  material?: TankMaterial;
  has_lid?: boolean;
  has_air_pump?: boolean;
  has_circulation_pump?: boolean;
  has_heater?: boolean;
  is_light_proof?: boolean;
  has_uv_sterilizer?: boolean;
  has_ozone_generator?: boolean;
  installed_on?: string | null;
  location_key?: string | null;
  notes?: string | null;
}

export interface TankUpdate {
  name?: string;
  tank_type?: TankType;
  volume_liters?: number;
  material?: TankMaterial;
  has_lid?: boolean;
  has_air_pump?: boolean;
  has_circulation_pump?: boolean;
  has_heater?: boolean;
  is_light_proof?: boolean;
  has_uv_sterilizer?: boolean;
  has_ozone_generator?: boolean;
  installed_on?: string | null;
  location_key?: string | null;
  notes?: string | null;
}

export interface TankState {
  key: string;
  tank_key: string;
  recorded_at: string | null;
  fill_level_liters: number | null;
  fill_level_percent: number | null;
  ph: number | null;
  ec_ms: number | null;
  water_temp_celsius: number | null;
  tds_ppm: number | null;
  dissolved_oxygen_mgl: number | null;
  orp_mv: number | null;
  source: string;
  created_at: string | null;
  updated_at: string | null;
}

export interface TankStateCreate {
  fill_level_liters?: number | null;
  fill_level_percent?: number | null;
  ph?: number | null;
  ec_ms?: number | null;
  water_temp_celsius?: number | null;
  tds_ppm?: number | null;
  dissolved_oxygen_mgl?: number | null;
  orp_mv?: number | null;
  source?: string;
}

export interface MaintenanceLog {
  key: string;
  tank_key: string;
  maintenance_type: MaintenanceType;
  performed_at: string | null;
  performed_by: string;
  duration_minutes: number | null;
  products_used: string[];
  notes: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface MaintenanceLogCreate {
  maintenance_type: MaintenanceType;
  performed_by?: string;
  duration_minutes?: number | null;
  products_used?: string[];
  notes?: string | null;
}

export interface MaintenanceSchedule {
  key: string;
  tank_key: string;
  maintenance_type: MaintenanceType;
  interval_days: number;
  reminder_days_before: number;
  is_active: boolean;
  priority: MaintenancePriority;
  auto_create_task: boolean;
  instructions: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface MaintenanceScheduleCreate {
  maintenance_type: MaintenanceType;
  interval_days: number;
  reminder_days_before?: number;
  is_active?: boolean;
  priority?: MaintenancePriority;
  auto_create_task?: boolean;
  instructions?: string | null;
}

export interface MaintenanceScheduleUpdate {
  interval_days?: number;
  reminder_days_before?: number;
  is_active?: boolean;
  priority?: MaintenancePriority;
  auto_create_task?: boolean;
  instructions?: string | null;
}

export interface TankAlert {
  type: string;
  severity: string;
  message: string;
  value: number;
  limit?: number;
  limit_min?: number;
  limit_max?: number;
  factors?: string[];
  temp?: number;
}

// ── TankFillEvent types ──────────────────────────────────────────────

export interface FertilizerSnapshotData {
  product_key?: string | null;
  product_name: string;
  ml_per_liter: number;
}

export interface TankFillEvent {
  key: string;
  tank_key: string;
  filled_at: string | null;
  fill_type: FillType;
  volume_liters: number;
  mixing_result_key: string | null;
  nutrient_plan_key: string | null;
  target_ec_ms: number | null;
  target_ph: number | null;
  measured_ec_ms: number | null;
  measured_ph: number | null;
  water_source: string | null;
  water_mix_ratio_ro_percent: number | null;
  source_tank_key: string | null;
  fertilizers_used: FertilizerSnapshotData[];
  base_water_ec_ms: number | null;
  chlorine_ppm: number | null;
  chloramine_ppm: number | null;
  alkalinity_ppm: number | null;
  is_organic_fertilizers: boolean;
  performed_by: string | null;
  notes: string | null;
  water_defaults_source: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface TankFillEventCreate {
  fill_type: FillType;
  volume_liters: number;
  mixing_result_key?: string | null;
  nutrient_plan_key?: string | null;
  target_ec_ms?: number | null;
  target_ph?: number | null;
  measured_ec_ms?: number | null;
  measured_ph?: number | null;
  water_source?: string | null;
  water_mix_ratio_ro_percent?: number | null;
  source_tank_key?: string | null;
  fertilizers_used?: FertilizerSnapshotData[];
  base_water_ec_ms?: number | null;
  chlorine_ppm?: number | null;
  chloramine_ppm?: number | null;
  alkalinity_ppm?: number | null;
  is_organic_fertilizers?: boolean;
  performed_by?: string | null;
  notes?: string | null;
}

export interface TankFillEventStats {
  fill_type_counts: Record<string, number>;
  total_volume_liters: number;
  total_count: number;
  avg_ec_deviation_ms: number | null;
}

export interface FillEventResult {
  fill_event: TankFillEvent;
  tank_state: TankState | null;
  warnings: string[];
  water_defaults_source: string | null;
}

export interface DueMaintenance {
  tank_key: string;
  tank_name: string | null;
  schedule_key: string | null;
  maintenance_type: MaintenanceType;
  next_due: string;
  days_until: number;
  status: MaintenanceStatus;
  priority: MaintenancePriority;
}

// ── REQ-005 Sensor types ────────────────────────────────────────────

export interface Sensor {
  key: string;
  name: string;
  metric_type: string;
  ha_entity_id: string | null;
  unit_of_measurement: string | null;
  mqtt_topic: string | null;
  tank_key: string | null;
  site_key: string | null;
  location_key: string | null;
  is_active: boolean;
}

export interface SensorCreate {
  name: string;
  metric_type: string;
  ha_entity_id?: string | null;
  unit_of_measurement?: string | null;
  mqtt_topic?: string | null;
  tank_key?: string | null;
}

export interface SensorUpdate {
  name?: string;
  metric_type?: string;
  ha_entity_id?: string | null;
  unit_of_measurement?: string | null;
  mqtt_topic?: string | null;
  is_active?: boolean;
}

export interface LiveValueEntry {
  value: number;
  last_changed: string | null;
  entity_id: string | null;
  unit: string | null;
}

export interface LiveStateResponse {
  values: Record<string, LiveValueEntry>;
  errors: Array<{ entity_id: string; error: string }>;
  source: string;
  message?: string | null;
}

// ── Observations / Sensor Readings (TimescaleDB) ───────────────────

export interface SensorReadingResponse {
  time: string;
  sensor_key: string;
  sensor_type: string;
  value: number;
  unit: string | null;
  source: string;
  quality_score: number | null;
  raw_value: number | null;
  metadata: Record<string, unknown> | null;
}

export interface AggregatedReadingResponse {
  bucket: string;
  sensor_key: string;
  sensor_type: string;
  avg_value: number;
  min_value: number;
  max_value: number;
  sample_count: number;
}

export type SensorReadingItem = SensorReadingResponse | AggregatedReadingResponse;

export interface ReadingsListResponse {
  items: SensorReadingItem[];
  total: number;
  resolution: string;
}

export interface TimeseriesStatusResponse {
  available: boolean;
}

// ── REQ-004 Fertilizer types ────────────────────────────────────────

export interface Fertilizer {
  key: string;
  product_name: string;
  brand: string;
  fertilizer_type: FertilizerType;
  is_organic: boolean;
  tank_safe: boolean;
  recommended_application: ApplicationMethod;
  npk_ratio: [number, number, number];
  ec_contribution_per_ml: number;
  ec_contribution_uncertain: boolean;
  max_dose_ml_per_liter: number | null;
  mixing_priority: number;
  ph_effect: PhEffect;
  bioavailability: Bioavailability;
  shelf_life_days: number | null;
  storage_temp_min: number | null;
  storage_temp_max: number | null;
  notes: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface FertilizerCreate {
  product_name: string;
  brand?: string;
  fertilizer_type: FertilizerType;
  is_organic?: boolean;
  tank_safe?: boolean;
  recommended_application?: ApplicationMethod;
  npk_ratio?: [number, number, number];
  ec_contribution_per_ml?: number;
  ec_contribution_uncertain?: boolean;
  max_dose_ml_per_liter?: number | null;
  mixing_priority?: number;
  ph_effect?: PhEffect;
  bioavailability?: Bioavailability;
  shelf_life_days?: number | null;
  storage_temp_min?: number | null;
  storage_temp_max?: number | null;
  notes?: string | null;
}

export interface FertilizerUpdate {
  product_name?: string;
  brand?: string;
  fertilizer_type?: FertilizerType;
  is_organic?: boolean;
  tank_safe?: boolean;
  recommended_application?: ApplicationMethod;
  npk_ratio?: [number, number, number];
  ec_contribution_per_ml?: number;
  ec_contribution_uncertain?: boolean;
  max_dose_ml_per_liter?: number | null;
  mixing_priority?: number;
  ph_effect?: PhEffect;
  bioavailability?: Bioavailability;
  shelf_life_days?: number | null;
  storage_temp_min?: number | null;
  storage_temp_max?: number | null;
  notes?: string | null;
}

export interface FertilizerStock {
  key: string;
  fertilizer_key: string;
  current_volume_ml: number;
  purchase_date: string | null;
  expiry_date: string | null;
  batch_number: string;
  cost_per_liter: number | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface FertilizerStockCreate {
  current_volume_ml: number;
  purchase_date?: string | null;
  expiry_date?: string | null;
  batch_number?: string;
  cost_per_liter?: number | null;
}

export interface Incompatibility {
  fertilizer_key: string;
  product_name: string | null;
  reason: string;
  severity: IncompatibilitySeverity;
}

export interface FertilizerChannelUsage {
  channel_id: string;
  label: string;
  application_method: string;
  ml_per_liter: number;
}

export interface FertilizerPhaseUsage {
  phase_name: string;
  week_start: number;
  week_end: number;
  channels: FertilizerChannelUsage[];
}

export interface NutrientPlanUsage {
  key: string;
  name: string;
  phase_entries: FertilizerPhaseUsage[];
}

// ── REQ-004 Nutrient Plan types ─────────────────────────────────────

export interface NutrientPlan {
  key: string;
  name: string;
  description: string;
  recommended_substrate_type: SubstrateType | null;
  reference_substrate_type: SubstrateType;
  author: string;
  is_template: boolean;
  version: string;
  tags: string[];
  cloned_from_key: string | null;
  watering_schedule: WateringSchedule | null;
  water_mix_ratio_ro_percent: number | null;
  cycle_restart_from_sequence: number | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface NutrientPlanCreate {
  name: string;
  description?: string;
  recommended_substrate_type?: SubstrateType | null;
  reference_substrate_type?: SubstrateType;
  author?: string;
  is_template?: boolean;
  version?: string;
  tags?: string[];
  watering_schedule?: WateringSchedule | null;
  water_mix_ratio_ro_percent?: number | null;
  cycle_restart_from_sequence?: number | null;
}

export interface NutrientPlanUpdate {
  name?: string;
  description?: string;
  recommended_substrate_type?: SubstrateType | null;
  reference_substrate_type?: SubstrateType;
  author?: string;
  is_template?: boolean;
  version?: string;
  tags?: string[];
  watering_schedule?: WateringSchedule | null;
  water_mix_ratio_ro_percent?: number | null;
  cycle_restart_from_sequence?: number | null;
}

export interface FertilizerDosage {
  fertilizer_key: string;
  ml_per_liter: number;
  optional: boolean;
  mixing_order: number;
}

// ── REQ-004 Multi-Channel Delivery types ──────────────────────────────

export interface FertigationParams {
  method: 'fertigation';
  runs_per_day: number;
  duration_seconds: number;
  flow_rate_ml_min: number | null;
}

export interface DrenchParams {
  method: 'drench';
  volume_per_feeding_liters: number;
}

export interface FoliarParams {
  method: 'foliar';
  volume_per_spray_liters: number;
}

export interface TopDressParams {
  method: 'top_dress';
  grams_per_plant: number | null;
  grams_per_m2: number | null;
}

export type MethodParams = FertigationParams | DrenchParams | FoliarParams | TopDressParams;

export interface DeliveryChannel {
  channel_id: string;
  label: string;
  application_method: ApplicationMethod;
  enabled: boolean;
  notes: string | null;
  schedule: WateringSchedule | null;
  target_ec_ms: number | null;
  target_ph: number | null;
  fertilizer_dosages: FertilizerDosage[];
  method_params: MethodParams | null;
}

export interface DeliveryChannelCreate {
  channel_id: string;
  label?: string;
  application_method: ApplicationMethod;
  enabled?: boolean;
  notes?: string | null;
  schedule?: WateringSchedule | null;
  target_ec_ms?: number | null;
  target_ph?: number | null;
  fertilizer_dosages?: FertilizerDosage[];
  method_params?: MethodParams | null;
}

export interface ChannelValidation {
  channel_id: string;
  label: string;
  issues: string[];
  ec_budget: { target: number; calculated: number; delta: number } | null;
}

export interface NutrientPlanPhaseEntry {
  key: string;
  plan_key: string;
  phase_name: PhaseName;
  sequence_order: number;
  week_start: number;
  week_end: number;
  is_recurring: boolean;
  npk_ratio: [number, number, number];
  calcium_ppm: number | null;
  magnesium_ppm: number | null;
  target_ec_ms: number | null;
  reference_ec_ms: number | null;
  target_calcium_ppm: number | null;
  target_magnesium_ppm: number | null;
  reference_base_ec: number;
  notes: string | null;
  delivery_channels: DeliveryChannel[];
  watering_schedule_override: WateringSchedule | null;
  water_mix_ratio_ro_percent: number | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface PhaseEntryCreate {
  phase_name: PhaseName;
  sequence_order: number;
  week_start: number;
  week_end: number;
  is_recurring?: boolean;
  npk_ratio?: [number, number, number];
  calcium_ppm?: number | null;
  magnesium_ppm?: number | null;
  target_ec_ms?: number | null;
  reference_ec_ms?: number | null;
  target_calcium_ppm?: number | null;
  target_magnesium_ppm?: number | null;
  reference_base_ec?: number;
  notes?: string | null;
  delivery_channels?: DeliveryChannelCreate[];
  watering_schedule_override?: WateringSchedule | null;
  water_mix_ratio_ro_percent?: number | null;
}

export interface PhaseEntryUpdate {
  phase_name?: PhaseName;
  sequence_order?: number;
  week_start?: number;
  week_end?: number;
  is_recurring?: boolean;
  npk_ratio?: [number, number, number];
  calcium_ppm?: number | null;
  magnesium_ppm?: number | null;
  target_ec_ms?: number | null;
  reference_ec_ms?: number | null;
  target_calcium_ppm?: number | null;
  target_magnesium_ppm?: number | null;
  reference_base_ec?: number;
  notes?: string | null;
  delivery_channels?: DeliveryChannelCreate[];
  watering_schedule_override?: WateringSchedule | null;
  water_mix_ratio_ro_percent?: number | null;
}

// ── REQ-004 Feeding Event types ─────────────────────────────────────

// @deprecated — use WateringLogFertilizer
export interface FeedingEventFertilizer {
  fertilizer_key: string;
  ml_applied: number;
}

// @deprecated — use WateringLog
export interface FeedingEvent {
  key: string;
  plant_key: string;
  timestamp: string | null;
  application_method: ApplicationMethod;
  is_supplemental: boolean;
  tank_fill_event_key: string | null;
  volume_applied_liters: number;
  fertilizers_used: FeedingEventFertilizer[];
  measured_ec_before: number | null;
  measured_ec_after: number | null;
  measured_ph_before: number | null;
  measured_ph_after: number | null;
  runoff_ec: number | null;
  runoff_ph: number | null;
  runoff_volume_liters: number | null;
  channel_id: string | null;
  notes: string | null;
  created_at: string | null;
  updated_at: string | null;
}

// @deprecated — use WateringLogCreate
export interface FeedingEventCreate {
  plant_key: string;
  application_method?: ApplicationMethod;
  is_supplemental?: boolean;
  volume_applied_liters: number;
  fertilizers_used?: FeedingEventFertilizer[];
  measured_ec_before?: number | null;
  measured_ec_after?: number | null;
  measured_ph_before?: number | null;
  measured_ph_after?: number | null;
  runoff_ec?: number | null;
  runoff_ph?: number | null;
  runoff_volume_liters?: number | null;
  notes?: string | null;
}

// @deprecated — use WateringLogUpdate
export interface FeedingEventUpdate {
  application_method?: ApplicationMethod;
  is_supplemental?: boolean;
  volume_applied_liters?: number;
  measured_ec_before?: number | null;
  measured_ec_after?: number | null;
  measured_ph_before?: number | null;
  measured_ph_after?: number | null;
  runoff_ec?: number | null;
  runoff_ph?: number | null;
  runoff_volume_liters?: number | null;
  notes?: string | null;
}

// ── WateringLog types (unified, replaces WateringEvent + FeedingEvent) ──

export type WaterSource = 'tank' | 'tap' | 'osmose' | 'rainwater' | 'distilled' | 'well' | 'mixed';

export interface WateringLogFertilizer {
  fertilizer_key: string;
  ml_per_liter: number;
}

export interface ResolvedPlant {
  key: string;
  name: string;
}

export interface ResolvedFertilizer {
  key: string;
  name: string;
  ml_per_liter: number;
}

export interface WateringLog {
  key: string;
  logged_at: string | null;
  application_method: ApplicationMethod;
  is_supplemental: boolean;
  volume_liters: number;
  plant_keys: string[];
  slot_keys: string[];
  tank_fill_event_key: string | null;
  nutrient_plan_key: string | null;
  task_key: string | null;
  channel_id: string | null;
  fertilizers_used: WateringLogFertilizer[];
  ec_before: number | null;
  ec_after: number | null;
  ph_before: number | null;
  ph_after: number | null;
  runoff_ec: number | null;
  runoff_ph: number | null;
  runoff_volume_liters: number | null;
  water_source: WaterSource | null;
  performed_by: string | null;
  notes: string | null;
  created_at: string | null;
  updated_at: string | null;
  resolved_plants: ResolvedPlant[];
  resolved_fertilizers: ResolvedFertilizer[];
}

export interface WateringLogCreate {
  application_method?: ApplicationMethod;
  is_supplemental?: boolean;
  volume_liters: number;
  plant_keys?: string[];
  slot_keys?: string[];
  tank_fill_event_key?: string | null;
  nutrient_plan_key?: string | null;
  channel_id?: string | null;
  fertilizers_used?: WateringLogFertilizer[];
  ec_before?: number | null;
  ec_after?: number | null;
  ph_before?: number | null;
  ph_after?: number | null;
  runoff_ec?: number | null;
  runoff_ph?: number | null;
  runoff_volume_liters?: number | null;
  water_source?: WaterSource | null;
  performed_by?: string | null;
  notes?: string | null;
}

export interface WateringLogUpdate {
  application_method?: ApplicationMethod;
  is_supplemental?: boolean;
  volume_liters?: number;
  ec_before?: number | null;
  ec_after?: number | null;
  ph_before?: number | null;
  ph_after?: number | null;
  runoff_ec?: number | null;
  runoff_ph?: number | null;
  runoff_volume_liters?: number | null;
  water_source?: WaterSource | null;
  performed_by?: string | null;
  notes?: string | null;
}

// ── WateringEvent types (deprecated) ────────────────────────────────
// @deprecated — use WateringLog

// @deprecated — use WateringLogFertilizer
export interface FertilizerSnapshot {
  product_key: string | null;
  product_name: string;
  ml_per_liter: number;
}

// @deprecated — use WateringLog
export interface WateringEvent {
  key: string;
  watered_at: string | null;
  application_method: ApplicationMethod;
  is_supplemental: boolean;
  volume_liters: number;
  plant_keys: string[];
  tank_fill_event_key: string | null;
  nutrient_plan_key: string | null;
  fertilizers_used: FertilizerSnapshot[];
  target_ec: number | null;
  target_ph: number | null;
  measured_ec: number | null;
  measured_ph: number | null;
  runoff_ec: number | null;
  runoff_ph: number | null;
  water_source: WaterSource | null;
  performed_by: string | null;
  channel_id: string | null;
  notes: string | null;
  created_at: string | null;
}

// @deprecated — use WateringLogCreate
export interface WateringEventCreate {
  application_method?: ApplicationMethod;
  is_supplemental?: boolean;
  volume_liters: number;
  plant_keys: string[];
  tank_fill_event_key?: string | null;
  nutrient_plan_key?: string | null;
  fertilizers_used?: FertilizerSnapshot[];
  target_ec?: number | null;
  target_ph?: number | null;
  measured_ec?: number | null;
  measured_ph?: number | null;
  runoff_ec?: number | null;
  runoff_ph?: number | null;
  water_source?: WaterSource | null;
  performed_by?: string | null;
  notes?: string | null;
}

export interface WateringEventWithWarnings {
  event: WateringEvent;
  warnings: Array<{ type: string; message: string }>;
}

export interface WateringMethodStats {
  method: string;
  count: number;
  total_volume: number;
}

export interface WateringStats {
  total_events: number;
  total_volume: number;
  by_method: WateringMethodStats[];
}

// ── REQ-004 Calculation types ───────────────────────────────────────

export interface MixingProtocolRequest {
  target_volume_liters: number;
  target_ec_ms: number;
  target_ph: number;
  base_water_ec: number;
  base_water_ph: number;
  fertilizer_keys: string[];
  substrate_type?: SubstrateType;
}

export interface MixingDosage {
  fertilizer_key: string;
  product_name: string;
  ml_per_liter: number;
  total_ml: number;
  ec_contribution: number;
}

export interface MixingProtocolResponse {
  dosages: MixingDosage[];
  calculated_ec: number;
  ph_adjustment: { needed: boolean; direction: string; delta: number };
  warnings: string[];
  instructions: string[];
}

export interface FlushingRequest {
  current_ec_ms: number;
  days_until_harvest: number;
  substrate_type?: SubstrateType;
}

export interface FlushingScheduleDay {
  day: number;
  absolute_day: number;
  target_ec_ms: number;
  action: string;
  dosage_percent: number;
}

export interface FlushingResponse {
  substrate_type: string;
  recommended_flush_days: number;
  flush_start_day: number;
  current_ec_ms: number;
  schedule: FlushingScheduleDay[];
}

export interface RunoffRequest {
  input_ec_ms: number;
  runoff_ec_ms: number;
  input_ph: number;
  runoff_ph: number;
  input_volume_liters: number;
  runoff_volume_liters: number;
}

export interface RunoffResponse {
  ec_delta: number;
  ec_status: string;
  ec_message: string;
  ph_delta: number;
  ph_status: string;
  ph_message: string;
  runoff_percent: number;
  volume_status: string;
  volume_message: string;
  overall_health: string;
}

export interface MixingSafetyRequest {
  fertilizer_keys: string[];
}

export interface MixingSafetyResponse {
  safe: boolean;
  warnings: string[];
}

// ── REQ-004-A Water mix reverse + EC budget ─────────────────────────

export interface WaterMixReverseRequest {
  tap_profile: {
    ec_ms: number;
    ph: number;
    alkalinity_ppm?: number;
    gh_ppm?: number;
    calcium_ppm?: number;
    magnesium_ppm?: number;
    chlorine_ppm?: number;
    chloramine_ppm?: number;
  };
  ro_profile?: { ec_ms?: number; ph?: number };
  target_base_ec_ms: number;
}

export interface WaterMixReverseResponse {
  ro_percent: number;
  effective_profile: {
    ec_ms: number;
    ph: number;
    alkalinity_ppm: number;
    calcium_ppm: number;
    magnesium_ppm: number;
    chlorine_ppm: number;
    chloramine_ppm: number;
  };
}

export interface EcBudgetFertilizerRequest {
  key: string;
  recipe_ml_per_liter?: number;
}

export interface EcBudgetRequest {
  base_water_ec: number;
  alkalinity_ppm?: number;
  target_ec: number;
  substrate: SubstrateType;
  phase: PhaseName;
  volume_liters: number;
  fertilizer_keys: EcBudgetFertilizerRequest[];
  calmag_key?: string;
  calmag_dose_ml_per_liter?: number;
  silicate_key?: string;
  silicate_dose_ml_per_liter?: number;
  substrate_cycles_used?: number;
  measured_ec?: number;
  measured_temp_celsius?: number;
}

export interface EcSegment {
  label: string;
  ec_contribution: number;
  color_hint: string;
  ml_per_liter: number;
  total_ml: number;
  warning: string | null;
}

export interface EcBudgetResponse {
  ec_mix: number;
  ec_net: number;
  ec_silicate: number;
  ec_calmag: number;
  ec_fertilizers: number;
  ec_ph_reserve: number;
  ec_final: number;
  ec_max: number;
  ec_target: number;
  ec_at_25_corrected: number | null;
  tolerance: number;
  valid: boolean;
  living_soil_bypass: boolean;
  segments: EcSegment[];
  warnings: string[];
  dosage_table: Array<{
    key: string;
    product_name: string;
    ml_per_liter: number;
    total_ml: number;
    ec_contribution: number;
  }>;
  dosage_instructions: string[];
}

export interface PlanValidationResult {
  completeness: { complete: boolean; issues: string[] };
  ec_budgets: Array<{
    entry_key: string;
    phase_name: string;
    valid: boolean;
    target_ec: number;
    calculated_ec: number;
    delta: number;
    message: string;
  }>;
  channel_validations: Array<{
    entry_key: string;
    phase_name: string;
    valid: boolean;
    channel_results: ChannelValidation[];
  }>;
  valid: boolean;
}

// ── REQ-010 IPM types ─────────────────────────────────────────────────

export type PestType = 'insect' | 'mite' | 'nematode' | 'mollusk';
export type PathogenType = 'fungal' | 'bacterial' | 'viral' | 'physiological';
export type TreatmentType = 'cultural' | 'biological' | 'chemical' | 'mechanical';
export type IpmApplicationMethod = 'spray' | 'drench' | 'granular' | 'release' | 'cultural';
export type DetectionDifficulty = 'easy' | 'medium' | 'hard';
export type PressureLevel = 'none' | 'low' | 'medium' | 'high' | 'critical';

export interface Pest {
  key: string;
  scientific_name: string;
  common_name: string;
  pest_type: string;
  lifecycle_days: number | null;
  optimal_temp_min: number | null;
  optimal_temp_max: number | null;
  detection_difficulty: string;
  description: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface PestCreate {
  scientific_name: string;
  common_name: string;
  pest_type?: string;
  lifecycle_days?: number | null;
  optimal_temp_min?: number | null;
  optimal_temp_max?: number | null;
  detection_difficulty?: string;
  description?: string | null;
}

export interface PestUpdate {
  scientific_name?: string;
  common_name?: string;
  pest_type?: string;
  lifecycle_days?: number | null;
  optimal_temp_min?: number | null;
  optimal_temp_max?: number | null;
  detection_difficulty?: string;
  description?: string | null;
}

export interface Disease {
  key: string;
  scientific_name: string;
  common_name: string;
  pathogen_type: string;
  incubation_period_days: number | null;
  environmental_triggers: string[];
  affected_plant_parts: string[];
  description: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface DiseaseCreate {
  scientific_name: string;
  common_name: string;
  pathogen_type: string;
  incubation_period_days?: number | null;
  environmental_triggers?: string[];
  affected_plant_parts?: string[];
  description?: string | null;
}

export interface DiseaseUpdate {
  scientific_name?: string;
  common_name?: string;
  pathogen_type?: string;
  incubation_period_days?: number | null;
  environmental_triggers?: string[];
  affected_plant_parts?: string[];
  description?: string | null;
}

export interface Treatment {
  key: string;
  name: string;
  treatment_type: string;
  active_ingredient: string | null;
  application_method: string;
  safety_interval_days: number;
  dosage_per_liter: number | null;
  protective_equipment: string[];
  description: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface TreatmentCreate {
  name: string;
  treatment_type: string;
  active_ingredient?: string | null;
  application_method?: string;
  safety_interval_days?: number;
  dosage_per_liter?: number | null;
  protective_equipment?: string[];
  description?: string | null;
}

export interface TreatmentUpdate {
  name?: string;
  treatment_type?: string;
  active_ingredient?: string | null;
  application_method?: string;
  safety_interval_days?: number;
  dosage_per_liter?: number | null;
  protective_equipment?: string[];
  description?: string | null;
}

export interface Inspection {
  key: string;
  plant_key: string;
  inspector: string;
  inspected_at: string | null;
  pressure_level: string;
  detected_pest_keys: string[];
  detected_disease_keys: string[];
  symptoms_observed: string[];
  environmental_conditions: Record<string, number> | null;
  photo_refs: string[];
  notes: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface InspectionCreate {
  inspector?: string;
  pressure_level?: string;
  detected_pest_keys?: string[];
  detected_disease_keys?: string[];
  symptoms_observed?: string[];
  environmental_conditions?: Record<string, number> | null;
  photo_refs?: string[];
  notes?: string | null;
}

export interface TreatmentApplication {
  key: string;
  treatment_key: string;
  plant_key: string;
  applied_at: string | null;
  dosage: number | null;
  water_volume_liters: number | null;
  efficacy_rating: string | null;
  applied_by: string;
  notes: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface TreatmentApplicationCreate {
  treatment_key: string;
  dosage?: number | null;
  water_volume_liters?: number | null;
  efficacy_rating?: string | null;
  applied_by?: string;
  notes?: string | null;
}

export interface KarenzPeriod {
  active_ingredient: string | null;
  treatment_name: string | null;
  applied_at: string | null;
  safety_interval_days: number | null;
  safe_date: string | null;
}

export interface HarvestSafety {
  can_harvest: boolean;
  blocking_treatments: Array<Record<string, unknown>>;
}

// ── REQ-007 Harvest enums ─────────────────────────────────────────────

export type HarvestType = 'partial' | 'final' | 'continuous';
export type QualityGrade = 'a_plus' | 'a' | 'b' | 'c' | 'd';
export type HarvestIndicatorType =
  | 'trichome'
  | 'color'
  | 'brix'
  | 'size'
  | 'days_since_flowering'
  | 'aroma'
  | 'texture'
  | 'foliage';
export type RipenessStage = 'immature' | 'approaching' | 'peak' | 'overripe';

// ── REQ-007 Harvest types ─────────────────────────────────────────────

export interface HarvestIndicator {
  key: string;
  indicator_type: HarvestIndicatorType;
  measurement_unit: string;
  measurement_method: string;
  observation_frequency: string;
  reliability_score: number;
  species_key: string | null;
  description: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface HarvestIndicatorCreate {
  indicator_type: HarvestIndicatorType;
  measurement_unit?: string;
  measurement_method?: string;
  observation_frequency?: string;
  reliability_score?: number;
  species_key?: string | null;
  description?: string | null;
}

export interface HarvestObservation {
  key: string;
  plant_key: string;
  observed_at: string | null;
  observer: string;
  indicator_key: string;
  measurements: Record<string, unknown>;
  ripeness_assessment: RipenessStage;
  days_to_harvest_estimate: number | null;
  photo_refs: string[];
  notes: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface HarvestObservationCreate {
  indicator_key?: string;
  observer?: string;
  measurements?: Record<string, unknown>;
  ripeness_assessment?: RipenessStage;
  days_to_harvest_estimate?: number | null;
  photo_refs?: string[];
  notes?: string | null;
}

export interface HarvestBatch {
  key: string;
  batch_id: string;
  plant_key: string;
  harvest_date: string | null;
  harvest_type: HarvestType;
  wet_weight_g: number | null;
  estimated_dry_weight_g: number | null;
  actual_dry_weight_g: number | null;
  quality_grade: QualityGrade | null;
  harvester: string;
  notes: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface HarvestBatchCreate {
  batch_id?: string;
  harvest_type?: HarvestType;
  wet_weight_g?: number | null;
  estimated_dry_weight_g?: number | null;
  harvester?: string;
  notes?: string | null;
}

export interface HarvestBatchUpdate {
  harvest_type?: HarvestType;
  wet_weight_g?: number | null;
  estimated_dry_weight_g?: number | null;
  actual_dry_weight_g?: number | null;
  quality_grade?: QualityGrade | null;
  harvester?: string;
  notes?: string | null;
}

export interface QualityAssessment {
  key: string;
  batch_key: string;
  assessed_at: string | null;
  assessed_by: string;
  appearance_score: number;
  aroma_score: number;
  color_score: number;
  defects: string[];
  overall_score: number;
  grade: QualityGrade | null;
  notes: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface QualityAssessmentCreate {
  assessed_by?: string;
  appearance_score?: number;
  aroma_score?: number;
  color_score?: number;
  defects?: string[];
  notes?: string | null;
}

export interface YieldMetric {
  key: string;
  batch_key: string;
  yield_per_plant_g: number;
  yield_per_m2_g: number;
  total_yield_g: number;
  trim_waste_percent: number;
  usable_yield_g: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface YieldMetricCreate {
  yield_per_plant_g?: number;
  yield_per_m2_g?: number;
  total_yield_g?: number;
  trim_waste_percent?: number;
  usable_yield_g?: number;
}

export interface ReadinessIndicatorBreakdown {
  indicator_key: string;
  stage: string;
  score: number;
  reliability: number;
  weighted_contribution: number;
}

export interface ReadinessAssessment {
  overall_score: number;
  recommendation: string;
  estimated_days: number | null;
  indicators: ReadinessIndicatorBreakdown[];
}

export interface YieldStats {
  species_key: string;
  total_batches: number;
  avg_yield_per_plant_g: number;
  avg_yield_per_m2_g: number;
  total_yield_g: number;
  avg_trim_waste_percent: number;
}

// ── REQ-006 Task & Workflow types ─────────────────────────────────────

export type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'skipped' | 'cancelled';
export type TaskPriority = 'low' | 'medium' | 'high' | 'critical';
export type TaskCategory =
  | 'maintenance'
  | 'watering'
  | 'feeding'
  | 'training'
  | 'pest_control'
  | 'harvest'
  | 'pruning'
  | 'transplant'
  | 'monitoring'
  | 'cleaning'
  | 'care_reminder';
export type TriggerType = 'manual' | 'time_based' | 'event_based' | 'conditional';
export type SkillLevel = 'beginner' | 'intermediate' | 'advanced' | 'expert';
export type DifficultyLevel = 'beginner' | 'intermediate' | 'advanced' | 'expert';

export interface WorkflowTemplate {
  key: string;
  name: string;
  description: string | null;
  created_by: string;
  version: string;
  species_compatible: string[];
  growth_system: string | null;
  difficulty_level: string;
  category: string;
  tags: string[];
  is_system: boolean;
  auto_generated: boolean;
  species_key: string | null;
  species_name: string;
  total_duration_days: number;
  assigned_plant_count: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface WorkflowTemplateCreate {
  name: string;
  description?: string | null;
  created_by?: string;
  version?: string;
  species_compatible?: string[];
  species_key?: string | null;
  growth_system?: string | null;
  difficulty_level?: string;
  category?: string;
  tags?: string[];
  is_system?: boolean;
}

export interface WorkflowTemplateUpdate {
  name?: string;
  description?: string | null;
  version?: string;
  species_compatible?: string[];
  growth_system?: string | null;
  difficulty_level?: string;
  category?: string;
  tags?: string[];
}

export interface ChecklistItem {
  text: string;
  done: boolean;
  order: number;
}

export interface TaskTemplate {
  key: string;
  name: string;
  name_de: string;
  instruction: string;
  instruction_de: string;
  description: string;
  description_de: string;
  rationale: string;
  rationale_de: string;
  category: string;
  trigger_type: string;
  trigger_phase: string | null;
  phase_display_name: string;
  phase_duration_days: number;
  phase_stress_tolerance: string;
  days_offset: number;
  stress_level: string;
  estimated_duration_minutes: number | null;
  requires_photo: boolean;
  timer_duration_seconds: number | null;
  timer_label: string | null;
  tools_required: string[];
  skill_level: string;
  optimal_time_of_day: string | null;
  workflow_template_key: string | null;
  activity_key: string | null;
  sequence_order: number;
  recovery_days: number;
  is_optional: boolean;
  enabled: boolean;
  default_checklist: ChecklistItem[];
  require_all_checklist_items: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface TaskTemplateCreate {
  name: string;
  instruction?: string;
  category?: string;
  trigger_type?: string;
  trigger_phase?: string | null;
  days_offset?: number;
  stress_level?: string;
  estimated_duration_minutes?: number | null;
  requires_photo?: boolean;
  timer_duration_seconds?: number | null;
  timer_label?: string | null;
  tools_required?: string[];
  skill_level?: string;
  optimal_time_of_day?: string | null;
  workflow_template_key?: string | null;
  sequence_order?: number;
  default_checklist?: ChecklistItem[];
  require_all_checklist_items?: boolean;
}

export interface TaskTemplateUpdate {
  name?: string;
  instruction?: string;
  category?: string;
  trigger_type?: string;
  trigger_phase?: string | null;
  days_offset?: number;
  stress_level?: string;
  estimated_duration_minutes?: number | null;
  requires_photo?: boolean;
  timer_duration_seconds?: number | null;
  timer_label?: string | null;
  tools_required?: string[];
  skill_level?: string;
  optimal_time_of_day?: string | null;
  sequence_order?: number;
  default_checklist?: ChecklistItem[];
  require_all_checklist_items?: boolean;
}

export interface TaskItem {
  key: string;
  name: string;
  name_de: string;
  instruction: string;
  instruction_de: string;
  category: string;
  plant_key: string | null;
  due_date: string | null;
  scheduled_time: string | null;
  status: string;
  priority: string;
  skill_level: string;
  stress_level: string;
  estimated_duration_minutes: number | null;
  actual_duration_minutes: number | null;
  requires_photo: boolean;
  photo_refs: string[];
  timer_duration_seconds: number | null;
  timer_label: string | null;
  completion_notes: string | null;
  difficulty_rating: number | null;
  quality_rating: number | null;
  tags: string[];
  checklist: ChecklistItem[];
  assigned_to_user_key: string | null;
  recurrence_rule: string | null;
  recurrence_end_date: string | null;
  parent_recurring_task_key: string | null;
  trigger_phase: string | null;
  trigger_phase_override: string | null;
  reopened_at: string | null;
  reopened_from_status: string | null;
  started_at: string | null;
  completed_at: string | null;
  activity_key: string | null;
  template_key: string | null;
  workflow_execution_key: string | null;
  planting_run_key: string | null;
  watering_event_key: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface TaskItemCreate {
  name: string;
  name_de?: string;
  instruction?: string;
  instruction_de?: string;
  category?: string;
  plant_key?: string | null;
  due_date?: string | null;
  scheduled_time?: string | null;
  priority?: string;
  skill_level?: string;
  stress_level?: string;
  estimated_duration_minutes?: number | null;
  requires_photo?: boolean;
  timer_duration_seconds?: number | null;
  timer_label?: string | null;
  tags?: string[];
  checklist?: ChecklistItem[];
  assigned_to_user_key?: string | null;
  recurrence_rule?: string | null;
  recurrence_end_date?: string | null;
  trigger_phase?: string | null;
}

export interface TaskItemUpdate {
  name?: string;
  instruction?: string;
  category?: string;
  plant_key?: string | null;
  due_date?: string | null;
  scheduled_time?: string | null;
  priority?: string;
  skill_level?: string;
  stress_level?: string;
  estimated_duration_minutes?: number | null;
  requires_photo?: boolean;
  timer_duration_seconds?: number | null;
  timer_label?: string | null;
  tags?: string[];
  checklist?: ChecklistItem[];
  assigned_to_user_key?: string | null;
  recurrence_rule?: string | null;
  recurrence_end_date?: string | null;
  trigger_phase_override?: string | null;
}

export interface PhotoUploadResponse {
  url: string;
  filename: string;
  size_bytes: number;
}

export interface TaskCompleteRequest {
  completion_notes?: string | null;
  actual_duration_minutes?: number | null;
  photo_refs?: string[];
  difficulty_rating?: number | null;
  quality_rating?: number | null;
}

export interface TaskCloneRequest {
  target_plant_key?: string | null;
  due_date_offset_days?: number | null;
}

export interface TaskComment {
  key: string;
  task_key: string;
  comment_text: string;
  created_by: string;
  created_at: string | null;
  updated_at: string | null;
}

export interface TaskAuditEntry {
  key: string;
  task_key: string;
  changed_at: string | null;
  changed_by: string;
  action: string;
  field: string | null;
  old_value: string | null;
  new_value: string | null;
}

export interface BatchResponse {
  succeeded: string[];
  failed: { key: string; error: string }[];
}

export interface WorkflowAddTaskRequest {
  name: string;
  instruction?: string;
  category?: string;
  due_date?: string | null;
  priority?: string;
  trigger_phase?: string | null;
  estimated_duration_minutes?: number | null;
  tags?: string[];
  checklist?: ChecklistItem[];
}

export interface WorkflowExecution {
  key: string;
  workflow_template_key: string;
  plant_key: string;
  started_at: string | null;
  completed_at: string | null;
  completion_percentage: number;
  on_schedule: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface WorkflowInstantiateRequest {
  plant_key: string;
}

export interface HSTValidationResult {
  can_perform: boolean;
  reason: string;
  recovery_status: string;
}

// ── REQ-023 Auth types ──────────────────────────────────────────────

export type AuthProviderType = 'local' | 'google' | 'github' | 'apple' | 'oidc';
export type TenantRole = 'admin' | 'grower' | 'viewer';
export type TenantType = 'personal' | 'organization';
export type InvitationStatus = 'pending' | 'accepted' | 'expired' | 'revoked';
export type InvitationType = 'email' | 'link';

export interface LoginRequest {
  email: string;
  password: string;
  remember_me?: boolean;
}

export interface RegisterRequest {
  email: string;
  password: string;
  display_name: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserProfile {
  key: string;
  email: string;
  display_name: string;
  email_verified: boolean;
  is_active: boolean;
  avatar_url: string | null;
  locale: string;
  timezone: string;
  last_login_at: string | null;
  created_at: string | null;
}

export interface UserProfileUpdate {
  display_name?: string;
  avatar_url?: string | null;
  locale?: string;
  timezone?: string;
}

export interface AuthProviderInfo {
  key: string;
  provider: AuthProviderType;
  provider_email: string | null;
  provider_display_name: string | null;
  linked_at: string | null;
  last_used_at: string | null;
}

export interface SessionInfo {
  key: string;
  user_agent: string | null;
  ip_address: string | null;
  created_at: string | null;
  expires_at: string;
  is_current: boolean;
  is_persistent: boolean;
}

export interface OAuthProviderListItem {
  slug: string;
  display_name: string;
  icon_url: string | null;
}

export interface ApiKeyCreate {
  label: string;
  tenant_scope?: string | null;
}

export interface ApiKeyCreated {
  key: string;
  label: string;
  raw_key: string;
  key_prefix: string;
  tenant_scope: string | null;
  created_at: string | null;
}

export interface ApiKeySummary {
  key: string;
  label: string;
  key_prefix: string;
  tenant_scope: string | null;
  revoked: boolean;
  last_used_at: string | null;
  created_at: string | null;
}

// ── REQ-024 Tenant types ────────────────────────────────────────────

export interface Tenant {
  key: string;
  name: string;
  slug: string;
  tenant_type: TenantType;
  description: string | null;
  avatar_url: string | null;
  owner_key: string;
  max_members: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface TenantWithRole extends Tenant {
  role: TenantRole;
}

export interface TenantCreate {
  name: string;
  description?: string | null;
  tenant_type?: TenantType;
}

export interface TenantUpdate {
  name?: string;
  description?: string | null;
  avatar_url?: string | null;
}

export interface Membership {
  key: string;
  user_key: string;
  tenant_key: string;
  role: TenantRole;
  display_name: string;
  email: string;
  joined_at: string | null;
}

export interface Invitation {
  key: string;
  tenant_key: string;
  email: string | null;
  role: TenantRole;
  invitation_type: InvitationType;
  status: InvitationStatus;
  created_by: string;
  expires_at: string;
  created_at: string | null;
}

export interface InvitationCreate {
  email: string;
  role: TenantRole;
}

export interface InvitationLinkCreate {
  role: TenantRole;
  max_uses?: number;
}

export interface LocationAssignment {
  key: string;
  membership_key: string;
  location_key: string;
  tenant_key: string;
  created_at: string | null;
}

// ── REQ-019 Substrate extensions ────────────────────────────────────

export type IrrigationStrategy = 'infrequent' | 'moderate' | 'frequent' | 'continuous';

// ── REQ-022 Care Reminders ──────────────────────────────────────────

export type CareStyleType =
  | 'tropical'
  | 'succulent'
  | 'orchid'
  | 'calathea'
  | 'herb_tropical'
  | 'mediterranean'
  | 'fern'
  | 'cactus'
  | 'custom';
export type ReminderType =
  | 'watering'
  | 'fertilizing'
  | 'repotting'
  | 'pest_check'
  | 'location_check'
  | 'humidity_check';
export type ConfirmAction = 'confirmed' | 'snoozed' | 'skipped';
export type WateringMethod = 'soak' | 'drench_and_drain' | 'top_water' | 'bottom_water';

export interface CareProfile {
  key: string;
  care_style: CareStyleType;
  watering_interval_days: number;
  winter_watering_multiplier: number;
  watering_method: WateringMethod;
  water_quality_hint: string | null;
  fertilizing_interval_days: number;
  fertilizing_active_months: number[];
  repotting_interval_months: number;
  pest_check_interval_days: number;
  location_check_enabled: boolean;
  location_check_months: number[];
  humidity_check_enabled: boolean;
  humidity_check_interval_days: number;
  adaptive_learning_enabled: boolean;
  auto_create_watering_task: boolean;
  auto_create_fertilizing_task: boolean;
  auto_create_repotting_task: boolean;
  auto_create_pest_check_task: boolean;
  watering_interval_learned: number | null;
  fertilizing_interval_learned: number | null;
  notes: string | null;
  auto_generated: boolean;
  plant_key: string;
  created_at: string | null;
  updated_at: string | null;
}

export interface CareConfirmation {
  key: string;
  plant_key: string;
  care_profile_key: string;
  reminder_type: ReminderType;
  action: ConfirmAction;
  confirmed_at: string;
  snooze_days: number | null;
  watering_log_key: string | null;
  notes: string | null;
  interval_at_time: number | null;
}

export interface CareDashboardEntry {
  plant_key: string;
  plant_name: string;
  species_name: string | null;
  reminder_type: ReminderType;
  urgency: 'overdue' | 'due_today' | 'upcoming' | 'not_due';
  due_date: string | null;
  care_profile_key: string;
  task_key: string | null;
}

// ── REQ-020 Onboarding ──────────────────────────────────────────────

export type ExperienceLevel = 'beginner' | 'intermediate' | 'expert';
export type StarterKitDifficulty = 'beginner' | 'intermediate' | 'advanced';

export interface StarterKit {
  key: string;
  kit_id: string;
  name_i18n: Record<string, string>;
  description_i18n: Record<string, string>;
  difficulty: StarterKitDifficulty;
  icon: string;
  plant_count_suggestion: number;
  site_type: SiteType;
  species_keys: string[];
  cultivar_keys: string[];
  toxicity_warning: boolean;
  workflow_template_keys: string[];
  includes_nutrient_plan: boolean;
  nutrient_plan_keys: string[];
  tags: string[];
  sort_order: number;
}

export interface SpeciesAvailability {
  species_key: string;
  available: boolean;
}

export interface StarterKitWithAvailability extends StarterKit {
  species_availability: SpeciesAvailability[];
}

export interface PlantConfig {
  species_key: string;
  count: number;
  initial_phase: PhaseName;
}

export interface OnboardingState {
  key: string;
  user_key: string;
  completed: boolean;
  skipped: boolean;
  completed_at: string | null;
  selected_kit_id: string | null;
  selected_experience_level: ExperienceLevel | null;
  wizard_step: number;
  created_entities: Record<string, string[]>;
  site_name: string;
  site_type: string | null;
  selected_site_key: string | null;
  plant_count: number | null;
  plant_configs: PlantConfig[];
  favorite_species_keys: string[];
  favorite_nutrient_plan_keys: string[];
}

// ── REQ-020 Favorites ───────────────────────────────────────────────

export interface FavoriteEntry {
  key: string;
  target_key: string;
  target_type: string;
  source: string;
  cascade_from_key: string | null;
  favorited_at: string;
}

export interface NutrientPlanFertilizerInfo {
  key: string;
  product_name: string;
  brand: string | null;
}

export interface NutrientPlanMatch {
  plan_key: string;
  name: string;
  description: string | null;
  substrate_type: string | null;
  fertilizer_count: number;
  fertilizers: NutrientPlanFertilizerInfo[];
}

// ── REQ-021 User Preferences ────────────────────────────────────────

export interface UserPreference {
  key: string;
  user_key: string;
  experience_level: ExperienceLevel;
  onboarding_completed: boolean;
  locale: string;
  theme: string;
  watering_can_liters: number;
  smart_home_enabled: boolean;
}

// ── Watering Schedule types ──────────────────────────────────────────

export type ScheduleMode = 'weekdays' | 'interval';

export interface WateringSchedule {
  schedule_mode: ScheduleMode;
  weekday_schedule: number[];
  interval_days: number | null;
  preferred_time: string | null;
  application_method: string;
  reminder_hours_before: number;
  times_per_day: number;
}

export interface ChannelCalendarEntry {
  channel_id: string;
  label: string;
  application_method: string;
  phase_name: string;
  dates: string[];
  times_per_day: number;
}

export interface WateringScheduleCalendarResponse {
  run_key: string;
  has_schedule: boolean;
  plan_key?: string;
  plan_name?: string;
  schedule?: WateringSchedule;
  dates: string[];
  channel_calendars?: ChannelCalendarEntry[];
  times_per_day?: number;
}

export interface NutrientPlanAssignRequest {
  plan_key: string;
  assigned_by?: string;
}

export interface NutrientPlanAssignResponse {
  run_key: string;
  plan_key: string;
  edge_key: string;
}

// ── REQ-015 Calendar Types ───────────────────────────────────────────

export type CalendarEventCategory =
  | 'training'
  | 'pruning'
  | 'transplanting'
  | 'feeding'
  | 'ipm'
  | 'harvest'
  | 'maintenance'
  | 'phase_transition'
  | 'tank_maintenance'
  | 'watering_forecast'
  | 'custom';
export type CalendarEventSource = 'task' | 'phase_transition' | 'maintenance_log' | 'watering' | 'watering_forecast';

export interface CalendarEvent {
  id: string;
  title: string;
  description: string;
  category: CalendarEventCategory;
  source: CalendarEventSource;
  color: string;
  start: string | null;
  end: string | null;
  all_day: boolean;
  plant_key: string | null;
  task_key: string | null;
  site_key: string | null;
  location_key: string | null;
  metadata: Record<string, unknown>;
}

export interface CalendarEventsResponse {
  events: CalendarEvent[];
  total: number;
}

export interface CalendarFeedFilters {
  categories: string[];
  site_key: string | null;
}

export interface CalendarFeed {
  key: string;
  name: string;
  token: string;
  user_key: string;
  filters: CalendarFeedFilters;
  is_active: boolean;
  ical_url: string;
  created_at: string | null;
  updated_at: string | null;
}

// Sowing Calendar (REQ-015 §3.8)

export type SowingPhase =
  | 'indoor_sowing' | 'outdoor_planting' | 'growth' | 'harvest' | 'flowering'
  | 'germination' | 'seedling' | 'vegetative' | 'flushing' | 'ripening';

export interface SowingBar {
  phase: SowingPhase;
  color: string;
  start_date: string;
  end_date: string;
  label: string;
}

export interface SowingCalendarEntry {
  species_key: string;
  species_name: string;
  common_name: string;
  link_species_key: string;
  plant_category: string | null;
  bars: SowingBar[];
}

export interface FrostConfig {
  last_frost_date: string;
  first_frost_date: string | null;
  eisheilige_date: string;
}

export interface SowingCalendarResponse {
  entries: SowingCalendarEntry[];
  frost_config: FrostConfig;
  year: number;
  total: number;
}

// Season Overview (REQ-015 §3.9)

export interface MonthSummary {
  month: number;
  month_name: string;
  sowing_count: number;
  harvest_count: number;
  bloom_count: number;
  task_count: number;
  top_tasks: string[];
  is_current: boolean;
}

export interface SeasonOverviewResponse {
  site_key: string;
  site_name: string;
  year: number;
  months: MonthSummary[];
}

export interface WateringConfirmRequest {
  run_key: string;
  task_key: string;
  channel_id?: string;
  measured_ec?: number;
  measured_ph?: number;
  volume_liters?: number;
  overrides?: Record<string, unknown>;
}

export interface WateringQuickConfirmRequest {
  run_key: string;
  task_key: string;
  channel_id?: string;
}

export interface WateringConfirmResponse {
  watering_event_key: string;
  feeding_events_created: number;
  task_completed: boolean;
  warnings: Record<string, unknown>[];
}

// ── Watering Volume Suggestion ────────────────────────────────────────

export interface VolumeSuggestion {
  volume_ml: number;
  volume_ml_min: number;
  volume_ml_max: number;
  source: string;
  adjustments: string[];
}

// ── REQ-012 Import Types ─────────────────────────────────────────────

export type EntityType = 'species' | 'cultivar' | 'botanical_family';
export type DuplicateStrategy = 'skip' | 'update' | 'fail';
export type ImportJobStatus =
  | 'uploaded'
  | 'validating'
  | 'preview_ready'
  | 'confirmed'
  | 'importing'
  | 'completed'
  | 'failed';
export type RowStatus = 'valid' | 'invalid' | 'duplicate';

export interface RowValidationError {
  field: string;
  message: string;
  value: string;
}

export interface PreviewRow {
  row_number: number;
  data: Record<string, string>;
  status: RowStatus;
  errors: RowValidationError[];
  duplicate_key: string | null;
}

export interface ImportResult {
  created: number;
  updated: number;
  skipped: number;
  failed: number;
  errors: string[];
}

export interface ImportJob {
  key: string;
  entity_type: EntityType;
  status: ImportJobStatus;
  filename: string;
  row_count: number;
  duplicate_strategy: DuplicateStrategy;
  preview_rows: PreviewRow[];
  result: ImportResult | null;
  error_message: string | null;
  created_at: string | null;
}

// Activities (Stammdaten)

export interface Activity {
  key: string;
  tenant_key: string;
  name: string;
  name_de: string;
  description: string;
  description_de: string;
  category: ActivityCategory;
  stress_level: StressLevel;
  skill_level: SkillLevel;
  recovery_days_default: number;
  recovery_days_by_species: Record<string, number>;
  forbidden_phases: string[];
  restricted_sub_phases: string[];
  tools_required: string[];
  estimated_duration_minutes: number | null;
  requires_photo: boolean;
  species_compatible: string[];
  is_system: boolean;
  sort_order: number;
  tags: string[];
  created_at: string | null;
  updated_at: string | null;
}

export interface ActivityCreate {
  name: string;
  name_de?: string;
  description?: string;
  description_de?: string;
  category?: ActivityCategory;
  stress_level?: StressLevel;
  skill_level?: SkillLevel;
  recovery_days_default?: number;
  recovery_days_by_species?: Record<string, number>;
  forbidden_phases?: string[];
  restricted_sub_phases?: string[];
  tools_required?: string[];
  estimated_duration_minutes?: number | null;
  requires_photo?: boolean;
  species_compatible?: string[];
  sort_order?: number;
  tags?: string[];
}

// ── Activity Plans ──

export interface TaskTemplateResponse {
  key: string;
  name: string;
  name_de: string;
  instruction: string;
  instruction_de: string;
  trigger_phase: string | null;
  phase_display_name: string;
  phase_duration_days: number;
  phase_stress_tolerance: string;
  days_offset: number;
  rationale: string;
  rationale_de: string;
  category: string;
  stress_level: string;
  skill_level: string;
  estimated_duration_minutes: number | null;
  tools_required: string[];
  recovery_days: number;
  is_optional: boolean;
  enabled: boolean;
  activity_key: string | null;
  description: string;
  description_de: string;
}

export interface ActivityPlanResponse {
  workflow_template_key: string;
  name: string;
  species_name: string;
  species_key: string | null;
  auto_generated: boolean;
  growth_system: string | null;
  skill_level_filter: string | null;
  total_activities: number;
  total_duration_days: number;
  templates: TaskTemplateResponse[];
}

export interface ActivityPlanGenerateRequest {
  species_key: string;
  lifecycle_key?: string | null;
  growth_system?: string | null;
  skill_level?: string | null;
  force_regenerate?: boolean;
}

export interface ActivityPlanApplyRequest {
  workflow_template_key: string;
  plant_key?: string | null;
  run_key?: string | null;
  tenant_key?: string;
}

export interface ActivityPlanApplyResponse {
  created_count: number;
  task_keys: string[];
  plant_count: number | null;
  total_tasks: number | null;
}

export interface TaskTemplateUpdateRequest {
  enabled?: boolean | null;
  days_offset?: number | null;
  trigger_phase?: string | null;
}

// ── Admin Platform Types ──────────────────────────────────────────────

export interface AdminTenant {
  key: string;
  name: string;
  slug: string;
  tenant_type: TenantType;
  description: string | null;
  owner_user_key: string;
  is_active: boolean;
  is_platform: boolean;
  max_members: number;
  member_count: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface AdminUserTenantRole {
  tenant_key: string;
  tenant_name: string;
  tenant_slug: string;
  role: TenantRole;
}

export interface AdminUser {
  key: string;
  email: string;
  display_name: string;
  is_active: boolean;
  email_verified: boolean;
  last_login_at: string | null;
  created_at: string | null;
  tenant_count: number;
  roles: AdminUserTenantRole[];
}

export interface AdminPlatformStats {
  total_users: number;
  active_users: number;
  total_tenants: number;
  active_tenants: number;
  total_memberships: number;
}

export interface AdminTenantUpdate {
  name?: string;
  description?: string;
  max_members?: number;
  is_active?: boolean;
}

export interface AdminUserUpdate {
  display_name?: string;
  is_active?: boolean;
  email_verified?: boolean;
}

export interface AdminTenantMember {
  membership_key: string;
  user_key: string;
  display_name: string;
  email: string;
  role: TenantRole;
  is_active: boolean;
  joined_at: string | null;
}

export interface AdminAddMemberRequest {
  user_key: string;
  role: TenantRole;
}

export interface AdminUserMembership {
  membership_key: string;
  tenant_key: string;
  tenant_name: string;
  tenant_slug: string;
  role: TenantRole;
  is_active: boolean;
  joined_at: string | null;
}

export interface AdminAddUserToTenantRequest {
  tenant_key: string;
  role: TenantRole;
}

// ── Notifications (REQ-030) ──────────────────────────────────────────

export type NotificationUrgency = 'low' | 'normal' | 'high' | 'critical';
export type NotificationStatusValue = 'pending' | 'delivered' | 'failed';

export interface NotificationAction {
  action_id: string;
  title: string;
  uri: string | null;
}

export interface NotificationResponse {
  key: string;
  tenant_key: string;
  user_key: string;
  notification_type: string;
  title: string;
  body: string;
  urgency: NotificationUrgency;
  data: Record<string, unknown>;
  actions: NotificationAction[];
  image_url: string | null;
  group_key: string | null;
  channels_sent: string[];
  channels_failed: string[];
  status: NotificationStatusValue;
  read_at: string | null;
  acted_at: string | null;
  escalation_level: number;
  parent_notification_key: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface NotificationListResponse {
  items: NotificationResponse[];
  total: number;
  unread_count: number;
}

export interface UnreadCountResponse {
  unread_count: number;
}

export interface ChannelPreference {
  enabled: boolean;
  priority: number;
  config: Record<string, unknown>;
}

export interface QuietHoursPreference {
  enabled: boolean;
  start: string;
  end: string;
  timezone: string;
}

export interface BatchingPreference {
  enabled: boolean;
  window_minutes: number;
  max_batch_size: number;
}

export interface EscalationPreference {
  watering_enabled: boolean;
  escalation_days: number[];
}

export interface TypeOverride {
  channels: string[];
  ignore_quiet_hours: boolean;
}

export interface DailySummaryPreference {
  enabled: boolean;
  time: string;
  channel: string;
}

export interface NotificationPreferencesResponse {
  key: string | null;
  user_key: string;
  channels: Record<string, ChannelPreference>;
  quiet_hours: QuietHoursPreference;
  batching: BatchingPreference;
  escalation: EscalationPreference;
  type_overrides: Record<string, TypeOverride>;
  daily_summary: DailySummaryPreference;
  created_at: string | null;
  updated_at: string | null;
}

export interface NotificationPreferencesRequest {
  channels: Record<string, ChannelPreference>;
  quiet_hours: QuietHoursPreference;
  batching: BatchingPreference;
  escalation: EscalationPreference;
  type_overrides: Record<string, TypeOverride>;
  daily_summary: DailySummaryPreference;
}

export interface ChannelStatusResponse {
  channel_key: string;
  healthy: boolean;
  supports_actions: boolean;
  supports_batching: boolean;
}

export interface TestNotificationResponse {
  status: string;
  channel_key: string;
  success: boolean;
  error: string | null;
}
