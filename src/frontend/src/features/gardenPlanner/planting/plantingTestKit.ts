import { http, HttpResponse } from 'msw';
import type { Species } from '@/api/types';
import { server } from '@/test/mocks/server';
import { computeLayout, type EntryLayout } from '../model/layout';
import type { Geometry } from '../model/types';
import type { PreviewResponse, ValidatePlantingResponse } from './plantingTypes';

/** Fixtures and a recording backend for the planting tests (REQ-053 WP 3.6). */

export const BASE = '/api/v1/t/:tenant';

export const BED_GEOMETRY: Geometry = {
  kind: 'rect',
  origin: [1, 1],
  width_m: 1.2,
  length_m: 2,
  rotation_deg: 0,
};

export function species(key: string, name: string, overrides: Partial<Species> = {}): Species {
  return {
    key,
    scientific_name: `${name} scientificus`,
    common_names: [name],
    family_key: 'fam_1',
    family_name: 'Family',
    genus: 'Genus',
    spacing_cm: null,
    row_spacing_cm: null,
    mature_height_cm: null,
    mature_width_cm: null,
    recommended_container_volume_l: null,
    min_container_depth_cm: null,
    support_required: false,
    ...overrides,
  } as Species;
}

export function hint(overrides: Partial<ValidatePlantingResponse> = {}): ValidatePlantingResponse {
  return {
    location_key: 'loc_b03',
    species_key: 'sp_tomato',
    severity: 'OK',
    rotation_applicable: true,
    not_applicable_reason: null,
    rotation_window_years: 3,
    rotation_reset_at: null,
    rotation: [],
    neighbour_scope: 'bed',
    neighbours: [],
    ...overrides,
  };
}

export interface Seen {
  url: string;
  body: unknown;
}

export interface PlantingBackend {
  /** Every write the backend received, in order. */
  seen: Seen[];
  /** The preview requests received. */
  previews: unknown[];
}

interface BackendOptions {
  species?: Species[];
  hints?: Record<string, ValidatePlantingResponse>;
  /** Replace the preview answer (the server differs from the port). */
  preview?: (entry: EntryLayout) => PreviewResponse;
  favorites?: string[];
  incompatible?: Record<string, { species_key: string; reason: string }[]>;
}

function toPreviewResponse(result: ReturnType<typeof computeLayout>): PreviewResponse {
  return {
    slots: result.slots.map((slot) => ({
      slot_role: slot.slot_role,
      geometry: slot.point
        ? { kind: 'point', origin: slot.point }
        : { kind: 'polygon', points: slot.outline ?? [] },
      row_index: slot.row_index,
      sequence: slot.sequence,
      capacity_plants: slot.capacity_plants,
    })),
    count: result.count,
    capacity_max: result.capacity_max,
    warnings: result.warnings,
  };
}

/** Install the handlers of the planting dialog; the preview answers like the Python reference (the port). */
export function usePlantingBackend(options: BackendOptions = {}): PlantingBackend {
  const backend: PlantingBackend = { seen: [], previews: [] };
  const items = options.species ?? [species('sp_tomato', 'Tomato', { spacing_cm: '60', row_spacing_cm: '80' })];
  const record = async (request: Request) => {
    const text = await request.text();
    const body: unknown = text ? JSON.parse(text) : null;
    backend.seen.push({ url: new URL(request.url).pathname.replace(/^\/api\/v1\/t\/[^/]+/, ''), body });
    return body;
  };
  server.use(
    http.get('/api/v1/species', () =>
      HttpResponse.json({ items, total: items.length, offset: 0, limit: 200 }),
    ),
    http.get(`${BASE}/favorites`, () =>
      HttpResponse.json(
        (options.favorites ?? []).map((key) => ({
          key: `fav_${key}`,
          target_key: key,
          target_type: 'species',
          source: 'manual',
          cascade_from_key: null,
          favorited_at: '2026-01-01T00:00:00Z',
        })),
      ),
    ),
    http.get('/api/v1/species/:key/cultivars', () => HttpResponse.json([])),
    http.get('/api/v1/companion-planting/species/:key/compatible', () => HttpResponse.json([])),
    http.get('/api/v1/companion-planting/species/:key/incompatible', ({ params }) =>
      HttpResponse.json(
        (options.incompatible?.[String(params.key)] ?? []).map((entry) => ({
          species_key: entry.species_key,
          scientific_name: null,
          common_names: [],
          reason: entry.reason,
        })),
      ),
    ),
    http.get(`${BASE}/slots`, () => HttpResponse.json([])),
    http.post(`${BASE}/locations/:key/planting-layout/preview`, async ({ request }) => {
      const body = (await request.json()) as { entry: EntryLayout & { max_count?: number | null } };
      backend.previews.push(body.entry);
      if (options.preview) return HttpResponse.json(options.preview(body.entry));
      return HttpResponse.json(
        toPreviewResponse(computeLayout(BED_GEOMETRY, body.entry, body.entry.max_count ?? null)),
      );
    }),
    http.post(`${BASE}/locations/:key/validate-planting`, async ({ request }) => {
      const body = (await request.json()) as { species_key: string };
      return HttpResponse.json(
        options.hints?.[body.species_key] ?? hint({ species_key: body.species_key }),
      );
    }),
    http.post(`${BASE}/planting-runs`, async ({ request }) => {
      await record(request);
      return HttpResponse.json({ key: 'run_1', name: 'run', status: 'planned' }, { status: 201 });
    }),
    http.get(`${BASE}/planting-runs/:key/entries`, () =>
      HttpResponse.json(
        backend.seen
          .filter((s) => s.url === '/planting-runs')
          .flatMap((s) => (s.body as { entries: unknown[] }).entries)
          .map((_, index) => ({ key: `entry_${index + 1}` })),
      ),
    ),
    http.post(`${BASE}/locations/:key/slots/batch`, async ({ request }) => {
      const body = (await record(request)) as { slots: unknown[] };
      return HttpResponse.json({
        created_keys: body.slots.map((_, index) => `slot_${index + 1}`),
        deleted_count: 0,
        kept_count: 0,
      });
    }),
    http.post(`${BASE}/planting-runs/:key/plan-slots`, async ({ request }) => {
      await record(request);
      return HttpResponse.json({ run_key: 'run_1' });
    }),
    http.post(`${BASE}/locations/:key/quick-planting`, async ({ request }) => {
      await record(request);
      return HttpResponse.json(
        { run_key: 'run_q', entry_key: 'e', slot_keys: [], plant_keys: ['p1', 'p2'], instance_ids: [], warnings: [] },
        { status: 201 },
      );
    }),
    http.get('/api/v1/growth-phases/:key', () =>
      HttpResponse.json({ key: 'ph_veg', name: 'Vegetative', display_name: 'Vegetative' }),
    ),
  );
  return backend;
}
