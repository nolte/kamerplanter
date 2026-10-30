import { http, HttpResponse } from 'msw';
import { server } from '@/test/mocks/server';
import type { CareEventLine, HistoryItem, RotationTimeline, RotationYear } from './historyTypes';

/** Fixtures and the mock backend of the history tests (REQ-053 WP 4.5). */

export const BASE = '/api/v1/t/:tenant';

export function careLine(key: string, overrides: Partial<CareEventLine> = {}): CareEventLine {
  return {
    key,
    location_key: 'loc_b03',
    plant_keys: [],
    plant_names: [],
    category: 'watering',
    summary: `Watered ${key}`,
    performed_at: '2026-06-01T08:00:00Z',
    performed_by: 'Tester',
    performed_by_label: null,
    created_by_me: true,
    trigger: 'manual',
    reason: null,
    product_label: null,
    quantity: null,
    unit: null,
    material: null,
    observed_outcome: null,
    supersedes_key: null,
    superseded_by_key: null,
    voided_at: null,
    void_reason: null,
    redacted_at: null,
    ...overrides,
  };
}

export function careItem(key: string, overrides: Partial<CareEventLine> = {}): HistoryItem {
  const line = careLine(key, overrides);
  return {
    id: `care:${key}`,
    kind: 'care_event',
    at: line.performed_at,
    category: line.category,
    care_event: line,
    plant_key: null,
    species_key: null,
    plant_name: null,
    termination_type: null,
    run_key: null,
    run_name: null,
    run_status: null,
  };
}

export function plantedItem(plantKey: string, name: string, at = '2026-05-01T00:00:00Z'): HistoryItem {
  return {
    ...careItem('x'),
    id: `plant_planted:${plantKey}`,
    kind: 'plant_planted',
    at,
    category: 'planting',
    care_event: null,
    plant_key: plantKey,
    plant_name: name,
  };
}

export function year(value: number, plantings: RotationYear['plantings'] = []): RotationYear {
  return { year: value, plantings };
}

export function timeline(years: RotationYear[], overrides: Partial<RotationTimeline> = {}): RotationTimeline {
  return {
    location_key: 'loc_b03',
    years: years.length,
    rotation_applicable: true,
    not_applicable_reason: null,
    rotation_reset_at: null,
    timeline: years,
    ...overrides,
  };
}

export const SOLANACEAE = {
  season: null,
  family_key: 'fam_sol',
  family_name: 'Solanaceae',
  species_key: 'sp_tomato',
  nutrient_demand: 'heavy_feeder',
  plan_role: 'main_crop',
  source: 'plant',
  care_event_key: null,
} as const;

export const FABACEAE = {
  ...SOLANACEAE,
  family_key: 'fam_fab',
  family_name: 'Fabaceae',
  species_key: 'sp_bean',
  nutrient_demand: 'light_feeder',
} as const;

/** A request as the server saw it. */
export interface Seen {
  method: string;
  path: string;
  params: Record<string, string>;
  body: unknown;
}

interface BackendOptions {
  /** The merged history of the bed; sliced by `offset` / `limit` like the server does. */
  items?: HistoryItem[];
  timeline?: RotationTimeline;
  plants?: { plant_key: string; instance_id: string }[];
  members?: { key: string; user_key: string; display_name: string }[];
  /** The tenant-wide care log. */
  careEvents?: CareEventLine[];
}

/** The backend of a bed's history: history, rotation, plantings, members, backfill and its cancellation. */
export function useHistoryBackend(options: BackendOptions = {}) {
  const items = options.items ?? [];
  const careEvents = options.careEvents ?? [];
  const seen: Seen[] = [];
  let current = options.timeline ?? timeline([]);

  const record = async (request: Request): Promise<unknown> => {
    const url = new URL(request.url);
    const text = request.method === 'GET' ? '' : await request.text();
    const body: unknown = text ? JSON.parse(text) : null;
    seen.push({
      method: request.method,
      path: url.pathname.replace(/^\/api\/v1\/t\/[^/]+/, ''),
      params: Object.fromEntries(url.searchParams),
      body,
    });
    return body;
  };
  const page = <T,>(rows: T[], params: Record<string, string>): T[] => {
    const offset = Number(params.offset ?? 0);
    const limit = Number(params.limit ?? 50);
    return rows.slice(offset, offset + limit);
  };

  server.use(
    http.get(`${BASE}/locations/:key/history`, async ({ request }) => {
      await record(request);
      return HttpResponse.json(page(items, seen[seen.length - 1].params));
    }),
    http.get(`${BASE}/locations/:key/rotation`, async ({ request }) => {
      await record(request);
      return HttpResponse.json(current);
    }),
    http.get(`${BASE}/locations/:key/plantings`, async ({ request }) => {
      await record(request);
      return HttpResponse.json(
        (options.plants ?? []).map((plant) => ({ state: 'active', species_key: 'sp', ...plant })),
      );
    }),
    http.get('/api/v1/tenants/:slug/members', () => HttpResponse.json(options.members ?? [])),
    http.get(`${BASE}/care-events`, async ({ request }) => {
      await record(request);
      return HttpResponse.json(page(careEvents, seen[seen.length - 1].params));
    }),
    http.get(`${BASE}/sites`, () => HttpResponse.json([{ key: 'site_1', name: 'Garden' }])),
    http.get(`${BASE}/locations`, () =>
      HttpResponse.json([
        { key: 'loc_b03', name: 'Raised bed 3', site_key: 'site_1', location_type_key: 'raised_bed' },
        { key: 'loc_b04', name: 'Herb spiral', site_key: 'site_1', location_type_key: 'raised_bed' },
      ]),
    ),
    http.get('/api/v1/botanical-families', () =>
      HttpResponse.json([
        { key: 'fam_sol', name: 'Solanaceae' },
        { key: 'fam_fab', name: 'Fabaceae' },
      ]),
    ),
    http.get('/api/v1/species', () =>
      HttpResponse.json({
        items: [
          {
            key: 'sp_tomato',
            scientific_name: 'Solanum lycopersicum',
            common_names: ['Tomato'],
            family_key: 'fam_sol',
            family_name: 'Solanaceae',
          },
        ],
        total: 1,
        offset: 0,
        limit: 200,
      }),
    ),
    http.post(`${BASE}/locations/:key/history/backfill`, async ({ request }) => {
      const body = (await record(request)) as { year: number };
      current = {
        ...current,
        timeline: current.timeline.map((entry) =>
          entry.year === body.year
            ? {
                ...entry,
                plantings: [{ ...SOLANACEAE, source: 'backfill', care_event_key: 'ce_bf' } as const],
              }
            : entry,
        ),
      };
      return HttpResponse.json({ care_event_key: 'ce_bf', year: body.year }, { status: 201 });
    }),
    http.delete(`${BASE}/locations/:key/history/backfill/:eventKey`, async ({ request }) => {
      await record(request);
      return new HttpResponse(null, { status: 204 });
    }),
  );
  return { seen };
}
