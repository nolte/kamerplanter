/**
 * #3015 slice A: every `listAll*` reader added for the one-page call sites pages until a short page.
 *
 * The client double serves 201 rows and honours `offset`/`limit` like the backend, so a reader that stopped after the
 * first window would return 200 rows and miss row 201. Each case also proves the reader forwards its filters on
 * every page, not only the first — a filter dropped on page two would mix foreign rows into the result.
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';

const mocks = vi.hoisted(() => {
  const client = {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  };
  return { client };
});

vi.mock('@/api/client', () => ({
  __esModule: true,
  default: mocks.client,
  tenantClient: mocks.client,
}));

import { listAllSites } from '@/api/endpoints/sites';
import { listAllPlantingRuns } from '@/api/endpoints/plantingRuns';
import { listAllTanks } from '@/api/endpoints/tanks';
import { listAllPhaseDefinitions, listAllPhaseSequences } from '@/api/endpoints/phaseSequences';
import { listAllOverwinteringProfiles } from '@/api/endpoints/overwinteringProfiles';
import { listAllPropagationEvents } from '@/api/endpoints/propagation';
import { listAllTasks, listAllWorkflows } from '@/api/endpoints/tasks';
import { listAllFeedingEvents } from '@/api/endpoints/feeding-events';
import { listAllWateringLogs } from '@/api/endpoints/watering-logs';
import { listAllSuccessionPlans } from '@/api/endpoints/successionPlans';
import { getAllBatches as getAllPostHarvestBatches } from '@/api/endpoints/postHarvest';
import { listAllWateringEvents } from '@/api/endpoints/watering-events';
import { getAllBatches, getAllIndicators } from '@/api/endpoints/harvest';

const client = mocks.client;
const ROW_COUNT = 201;
const ROWS = Array.from({ length: ROW_COUNT }, (_, i) => ({ key: `row-${i + 1}` }));

interface GetConfig {
  params: Record<string, unknown> & { offset: number; limit: number };
}

beforeEach(() => {
  vi.clearAllMocks();
  client.get.mockImplementation((_url: string, config: GetConfig) => {
    const { offset, limit } = config.params;
    return Promise.resolve({ data: ROWS.slice(offset, offset + limit) });
  });
});

interface ReaderCase {
  name: string;
  read: () => Promise<unknown[]>;
  url: string;
  /** Parameters besides `offset`/`limit` that every page must carry. */
  filters: Record<string, unknown>;
}

const CASES: ReaderCase[] = [
  { name: 'listAllSites', read: () => listAllSites(), url: '/sites', filters: {} },
  {
    name: 'listAllPlantingRuns',
    read: () => listAllPlantingRuns('active', 'seed', 'loc-1'),
    url: '/planting-runs',
    filters: { status: 'active', run_type: 'seed', location_key: 'loc-1' },
  },
  { name: 'listAllTanks', read: () => listAllTanks('nutrient'), url: '/tanks', filters: { tank_type: 'nutrient' } },
  {
    name: 'listAllPhaseDefinitions',
    read: () => listAllPhaseDefinitions('flower'),
    url: '/phase-definitions',
    filters: { name: 'flower' },
  },
  { name: 'listAllPhaseSequences', read: () => listAllPhaseSequences(), url: '/phase-sequences', filters: {} },
  {
    name: 'listAllOverwinteringProfiles',
    read: () => listAllOverwinteringProfiles(),
    url: '/overwintering-profiles',
    filters: {},
  },
  {
    name: 'listAllPropagationEvents',
    read: () => listAllPropagationEvents({ method: 'cutting', status: 'pending' }),
    url: '/propagation/events',
    filters: { method: 'cutting', status: 'pending' },
  },
  {
    name: 'listAllTasks',
    read: () => listAllTasks({ entity_type: 'planting_run', entity_key: 'run-1' }),
    url: '/tasks',
    filters: { entity_type: 'planting_run', entity_key: 'run-1' },
  },
  { name: 'getAllIndicators', read: () => getAllIndicators(), url: '/harvest/indicators', filters: {} },
  { name: 'getAllBatches', read: () => getAllBatches(), url: '/harvest/batches', filters: {} },
  { name: 'listAllFeedingEvents', read: () => listAllFeedingEvents(), url: '/feeding-events', filters: {} },
  { name: 'listAllWateringLogs', read: () => listAllWateringLogs(), url: '/watering-logs', filters: {} },
  { name: 'listAllSuccessionPlans', read: () => listAllSuccessionPlans(), url: '/succession-plans', filters: {} },
  { name: 'postHarvest getAllBatches', read: () => getAllPostHarvestBatches(), url: '/post-harvest', filters: {} },
  { name: 'listAllWateringEvents', read: () => listAllWateringEvents(), url: '/watering-events', filters: {} },
  {
    name: 'listAllWorkflows',
    read: () => listAllWorkflows('species-1'),
    url: '/tasks/workflows',
    filters: { species_key: 'species-1' },
  },
];

describe('listAll* readers (#3015)', () => {
  it.each(CASES)('$name returns row 201 of 201 and forwards its filters on every page', async ({ read, url, filters }) => {
    const all = await read();

    expect(all).toHaveLength(ROW_COUNT);
    expect(all[ROW_COUNT - 1]).toEqual({ key: `row-${ROW_COUNT}` });
    expect(client.get).toHaveBeenCalledTimes(2);
    const calls = client.get.mock.calls as Array<[string, GetConfig]>;
    expect(calls.map(([u]) => u)).toEqual([url, url]);
    expect(calls.map(([, config]) => [config.params.offset, config.params.limit])).toEqual([
      [0, 200],
      [200, 200],
    ]);
    for (const [, config] of calls) {
      expect(config.params).toMatchObject(filters);
    }
  });

  it.each(CASES)('$name stops after one request when the first page is short', async ({ read }) => {
    client.get.mockResolvedValueOnce({ data: [{ key: 'only' }] });

    const all = await read();

    expect(all).toEqual([{ key: 'only' }]);
    expect(client.get).toHaveBeenCalledTimes(1);
  });
});
