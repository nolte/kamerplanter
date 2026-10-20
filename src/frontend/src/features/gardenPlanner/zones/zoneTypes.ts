/**
 * Wire types of the irrigation zones (REQ-053 §20.11, GP-API-050..053), written by hand after
 * `app/api/v1/irrigation_zones/schemas.py`. `flow_rate_ha_entity_id` is never part of an answer (SR-014):
 * the client sees `flow_rate_ha_entity_bound` only.
 */

export const IRRIGATION_TYPES = ['manual', 'drip', 'sprinkler', 'soaker_hose', 'sub_irrigation'] as const;
export type IrrigationZoneType = (typeof IRRIGATION_TYPES)[number];

export type FlowRateSource = 'manual' | 'ha_entity';

/** `by_demand` is not offered yet (operator decision #2466); `measured` is never sent for a divided total. */
export type CareEventAllocation = 'measured' | 'by_area' | 'equal';
export type RoundAllocation = Exclude<CareEventAllocation, 'measured'>;
export const ROUND_ALLOCATIONS: readonly RoundAllocation[] = ['by_area', 'equal'];

export interface IrrigationZone {
  key: string;
  site_key: string;
  name: string;
  irrigation_type: IrrigationZoneType;
  water_source_key?: string | null;
  actuator_key?: string | null;
  flow_rate_l_per_min?: number | null;
  flow_rate_source: FlowRateSource;
  flow_rate_ha_entity_bound: boolean;
  application_efficiency?: number | null;
  color: string;
  schedule_hint?: string | null;
  location_keys: string[];
}

/** A zone as the plan response carries it (`include=zones`): without the HA flag. */
export type PlanZone = Pick<
  IrrigationZone,
  'key' | 'name' | 'irrigation_type' | 'color' | 'location_keys'
> &
  Partial<IrrigationZone>;

export interface ZoneCreate {
  name: string;
  irrigation_type: IrrigationZoneType;
  color: string;
  water_source_key?: string | null;
  schedule_hint?: string | null;
  application_efficiency?: number | null;
  /** Technical scope only. */
  flow_rate_l_per_min?: number | null;
}

export type ZoneUpdate = Partial<ZoneCreate>;

export interface ZoneLocationsResult extends IrrigationZone {
  added: string[];
  removed: string[];
  /** bed key → the zone it was taken from. */
  moved_from: Record<string, string>;
}

export interface LastWatering {
  at: string;
  source: 'care_event' | 'watering_event';
  location_key?: string | null;
  allocation: CareEventAllocation;
}

export interface NextPlanned {
  task_key: string;
  location_key: string;
  due_date?: string | null;
  overdue: boolean;
}

export type ConsumptionSource = 'manual_log' | 'actuator_runtime_manual_rate' | 'actuator_runtime_ha_rate';

export interface ZoneHint {
  /** `water_source_lasts_days` | `irrigation_system_differs`; an unknown code is shown generically. */
  code: string;
  params: Record<string, number | string | string[]>;
}

export interface ZoneStatus {
  last_watering?: LastWatering | null;
  next_planned?: NextPlanned | null;
  /** `null` = no bed has a demand for today: nothing is shown, nothing is estimated (E-10). */
  demand_liters_today?: number | null;
  demand_gross_liters_today?: number | null;
  application_efficiency?: number | null;
  efficiency_source?: 'zone' | 'type_default' | null;
  consumption_liters_30d: number;
  consumption_sources: { source: ConsumptionSource; liters: number }[];
  hints: ZoneHint[];
}

export interface WateringRoundRequest {
  volume_liters: number;
  allocation: RoundAllocation;
  summary?: string | null;
}

export interface WateringRoundResult {
  event_keys: string[];
  shares: { location_key: string; liters: number }[];
  allocation: CareEventAllocation;
  performed_at: string;
  skipped_location_keys: string[];
}
