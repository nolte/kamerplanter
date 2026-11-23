/**
 * #3015 slice A: the feeding dialog's plant picker lists every plant of the tenant, not one page.
 *
 * The dialog used to call `listPlantInstances()` — one page at the endpoint's default — so on a tenant with more
 * plants than that page a freshly created plant was not in the dropdown (nightly
 * `test_req004_core_lifecycle_journey.py::TestCoreJourneyRecordFeeding`). The handler below honours `offset`/`limit`
 * like the backend, so the picker only shows plant 201 if the dialog reads past the first page.
 */
import { cleanup, fireEvent, screen, waitFor, within } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { http, HttpResponse } from 'msw';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';
import type { PlantInstance } from '@/api/types';
import FeedingEventCreateDialog from '@/pages/duengung/FeedingEventCreateDialog';

const PLANTS_URL = '/api/v1/t/test-tenant/plant-instances';
const PLANT_COUNT = 201;

function makePlant(index: number): PlantInstance {
  return {
    key: `plant-${index}`,
    instance_id: `PLANT-${index}`,
    species_key: 'sp-1',
    cultivar_key: null,
    site_key: null,
    location_key: null,
    slot_key: null,
    substrate_batch_key: null,
    substrate_key: null,
    plant_name: null,
    planted_on: '2026-03-01',
    removed_on: null,
    termination_type: null,
    termination_cause: null,
    current_phase: 'vegetative',
    current_phase_key: null,
    current_phase_started_at: null,
    container_volume_liters: null,
    substrate_type_override: null,
    species: null,
    cultivar: null,
    mother_key: null,
    created_at: '2026-03-01T00:00:00Z',
    updated_at: null,
  } as PlantInstance;
}

const PLANTS = Array.from({ length: PLANT_COUNT }, (_, i) => makePlant(i + 1));

/** Serves `PLANTS` page by page, as the backend does, and records every requested window. */
function servePagedPlants(): Array<{ offset: number; limit: number }> {
  const windows: Array<{ offset: number; limit: number }> = [];
  server.use(
    http.get(PLANTS_URL, ({ request }) => {
      const params = new URL(request.url).searchParams;
      const offset = Number(params.get('offset') ?? 0);
      const limit = Number(params.get('limit') ?? 50);
      windows.push({ offset, limit });
      return HttpResponse.json(PLANTS.slice(offset, offset + limit));
    }),
  );
  return windows;
}

afterEach(() => {
  cleanup();
});

describe('FeedingEventCreateDialog plant picker (#3015)', () => {
  it('offers plant 201 of 201 — every page is read, not only the first', async () => {
    const windows = servePagedPlants();
    renderWithProviders(<FeedingEventCreateDialog open onClose={() => {}} onCreated={() => {}} />);

    const field = await screen.findByTestId('form-field-plant_key');
    const trigger = within(field).getByRole('combobox');
    await waitFor(() => expect(trigger).not.toHaveAttribute('aria-disabled', 'true'));
    fireEvent.mouseDown(trigger);

    expect(await screen.findByTestId(`form-option-plant_key-plant-${PLANT_COUNT}`)).toBeInTheDocument();
    expect(screen.getByTestId('form-option-plant_key-plant-1')).toBeInTheDocument();
    // Two windows of 200: the first full, the second short — the short page ends the loop.
    expect(windows).toEqual([
      { offset: 0, limit: 200 },
      { offset: 200, limit: 200 },
    ]);
  });
});
