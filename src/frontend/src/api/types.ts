// Enums (mirrors src/backend/app/common/enums.py)

export type GrowthHabit = 'herb' | 'shrub' | 'tree' | 'vine' | 'groundcover';
export type RootType = 'fibrous' | 'taproot' | 'tuberous' | 'bulbous';
export type PhotoperiodType = 'short_day' | 'long_day' | 'day_neutral';
export type CycleType = 'annual' | 'biennial' | 'perennial';
export type StressTolerance = 'low' | 'medium' | 'high';
export type TransitionTriggerType = 'time_based' | 'manual' | 'event_based' | 'conditional';
export type SiteType = 'outdoor' | 'greenhouse' | 'indoor';
export type LightType = 'natural' | 'led' | 'hps' | 'cmh' | 'mixed';
export type IrrigationSystem = 'manual' | 'drip' | 'hydro' | 'mist' | 'nft' | 'ebb_flow';
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
export type PlantingRunType = 'monoculture' | 'clone' | 'mixed_culture';
export type PlantingRunStatus = 'planned' | 'active' | 'harvesting' | 'completed' | 'cancelled';
export type EntryRole = 'primary' | 'companion' | 'trap_crop';
export type FertilizerType = 'base' | 'supplement' | 'booster' | 'biological' | 'ph_adjuster' | 'organic';
export type PhEffect = 'acidic' | 'alkaline' | 'neutral';
export type ApplicationMethod = 'fertigation' | 'drench' | 'foliar' | 'top_dress' | 'any';
export type Bioavailability = 'immediate' | 'slow_release' | 'microbial_dependent';
export type IncompatibilitySeverity = 'critical' | 'warning' | 'minor';
export type PhaseName = 'germination' | 'seedling' | 'vegetative' | 'flowering' | 'harvest';

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
  role: EntryRole;
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
  role?: EntryRole;
  id_prefix: string;
  spacing_cm?: number | null;
  notes?: string | null;
}

export interface PlantingRun {
  key: string;
  name: string;
  run_type: PlantingRunType;
  status: PlantingRunStatus;
  planned_quantity: number;
  actual_quantity: number;
  location_key: string | null;
  substrate_batch_key: string | null;
  planned_start_date: string | null;
  started_at: string | null;
  completed_at: string | null;
  source_plant_key: string | null;
  notes: string | null;
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
  notes?: string | null;
  planned_start_date?: string | null;
}

export interface BatchCreatePlantsResponse {
  run_key: string;
  created_count: number;
  plant_keys: string[];
  instance_ids: string[];
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
}

export interface BatchRemoveResponse {
  run_key: string;
  removed_count: number;
  removed_keys: string[];
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

export type TankType = 'nutrient' | 'irrigation' | 'reservoir' | 'recirculation';
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
  installed_on?: string | null;
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

// ── REQ-004 Nutrient Plan types ─────────────────────────────────────

export interface NutrientPlan {
  key: string;
  name: string;
  description: string;
  recommended_substrate_type: SubstrateType | null;
  author: string;
  is_template: boolean;
  version: string;
  tags: string[];
  cloned_from_key: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface NutrientPlanCreate {
  name: string;
  description?: string;
  recommended_substrate_type?: SubstrateType | null;
  author?: string;
  is_template?: boolean;
  version?: string;
  tags?: string[];
}

export interface NutrientPlanUpdate {
  name?: string;
  description?: string;
  recommended_substrate_type?: SubstrateType | null;
  author?: string;
  is_template?: boolean;
  version?: string;
  tags?: string[];
}

export interface FertilizerDosage {
  fertilizer_key: string;
  ml_per_liter: number;
  optional: boolean;
}

export interface NutrientPlanPhaseEntry {
  key: string;
  plan_key: string;
  phase_name: PhaseName;
  sequence_order: number;
  week_start: number;
  week_end: number;
  npk_ratio: [number, number, number];
  target_ec_ms: number;
  target_ph: number;
  calcium_ppm: number | null;
  magnesium_ppm: number | null;
  feeding_frequency_per_week: number;
  volume_per_feeding_liters: number | null;
  notes: string | null;
  fertilizer_dosages: FertilizerDosage[];
  created_at: string | null;
  updated_at: string | null;
}

export interface PhaseEntryCreate {
  phase_name: PhaseName;
  sequence_order: number;
  week_start: number;
  week_end: number;
  npk_ratio?: [number, number, number];
  target_ec_ms?: number;
  target_ph?: number;
  calcium_ppm?: number | null;
  magnesium_ppm?: number | null;
  feeding_frequency_per_week?: number;
  volume_per_feeding_liters?: number | null;
  notes?: string | null;
  fertilizer_dosages?: FertilizerDosage[];
}

export interface PhaseEntryUpdate {
  phase_name?: PhaseName;
  sequence_order?: number;
  week_start?: number;
  week_end?: number;
  npk_ratio?: [number, number, number];
  target_ec_ms?: number;
  target_ph?: number;
  calcium_ppm?: number | null;
  magnesium_ppm?: number | null;
  feeding_frequency_per_week?: number;
  volume_per_feeding_liters?: number | null;
  notes?: string | null;
  fertilizer_dosages?: FertilizerDosage[];
}

// ── REQ-004 Feeding Event types ─────────────────────────────────────

export interface FeedingEventFertilizer {
  fertilizer_key: string;
  ml_applied: number;
}

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
  notes: string | null;
  created_at: string | null;
  updated_at: string | null;
}

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

// ── WateringEvent types ─────────────────────────────────────────────

export type WaterSource = 'tank' | 'tap' | 'osmose' | 'rainwater' | 'distilled' | 'well';

export interface FertilizerSnapshot {
  product_key: string | null;
  product_name: string;
  ml_per_liter: number;
}

export interface WateringEvent {
  key: string;
  watered_at: string | null;
  application_method: ApplicationMethod;
  is_supplemental: boolean;
  volume_liters: number;
  slot_keys: string[];
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
  notes: string | null;
  created_at: string | null;
}

export interface WateringEventCreate {
  application_method?: ApplicationMethod;
  is_supplemental?: boolean;
  volume_liters: number;
  slot_keys: string[];
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
  valid: boolean;
}
