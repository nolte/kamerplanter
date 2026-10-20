import { http, HttpResponse } from 'msw';
import { vi } from 'vitest';
import { smallPlan, bed, gardenObject } from '@/test/gardenPlanFixtures';
import { server } from '@/test/mocks/server';
import type { UseIrrigationZones } from './useZoneData';
import type { IrrigationZone, ZoneStatus } from './zoneTypes';

/** Fixtures of the zone panel tests (REQ-053 WP 7.6 / 7.7). */

export const BASE = '/api/v1/t/:tenant';

export function zone(key: string, overrides: Partial<IrrigationZone> = {}): IrrigationZone {
  return {
    key,
    site_key: 'site_1',
    name: `Zone ${key}`,
    irrigation_type: 'drip',
    flow_rate_source: 'manual',
    flow_rate_ha_entity_bound: false,
    color: '#2E7D32',
    location_keys: [],
    ...overrides,
  };
}

export function zonePlan() {
  return smallPlan({
    locations: [
      bed('loc_a', 1, 1, { name: 'North bed', area_m2: 4 }),
      bed('loc_b', 4, 1, { name: 'South bed', area_m2: 0 }),
      bed('loc_c', 7, 1, { name: 'East bed', area_m2: 2 }),
    ],
    garden_objects: [
      gardenObject('go_barrel', 1, 6, {
        object_type: 'water_source',
        label: 'Rain barrel',
        props: { object_type: 'water_source', water_source_kind: 'rain_barrel' },
      }),
    ],
    slots: [],
    plants: [],
  });
}

export function zoneData(zones: IrrigationZone[]): UseIrrigationZones {
  return { zones, records: zones, status: 'ready', reload: vi.fn() };
}

export function status(overrides: Partial<ZoneStatus> = {}): ZoneStatus {
  return { consumption_liters_30d: 0, consumption_sources: [], hints: [], ...overrides };
}

export function useStatus(zoneKey: string, answer: ZoneStatus): void {
  server.use(http.get(`${BASE}/irrigation-zones/${zoneKey}/status`, () => HttpResponse.json(answer)));
}
