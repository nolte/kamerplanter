import { screen } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import type { PostHarvestBatch } from '@/api/types';

// Force the mobile layout so DataTable renders the mobileCardRenderer branch.
vi.mock('@mui/material/useMediaQuery', () => ({ default: () => true }));
vi.mock('@/api/endpoints/postHarvest');
vi.mock('@/api/endpoints/harvest');

import * as postHarvestApi from '@/api/endpoints/postHarvest';
import * as harvestApi from '@/api/endpoints/harvest';
import PostHarvestPage from '@/pages/post-harvest/PostHarvestPage';
import { renderWithProviders } from '../helpers';

const BATCH: PostHarvestBatch = {
  key: 'ph1',
  harvest_batch_key: 'hb-1',
  plant_key: 'pl1',
  stage: 'curing',
  species_type: 'herb',
  drying_method: 'rack_dry',
  start_weight_g: 450,
  current_weight_g: 120,
  target_moisture_percent: 10,
  dryness_progress_percent: 96,
  ready_for_curing: true,
  snap_test_passed: true,
  water_activity: 0.58,
  storage_location: 'Curing closet',
  pesticide_residue_status: 'clean',
  started_at: null,
  drying_started_at: null,
  curing_started_at: null,
  stored_at: null,
  released_at: null,
  completed_at: null,
  notes: null,
  created_at: null,
  updated_at: null,
};

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(postHarvestApi.getBatches).mockResolvedValue([BATCH]);
  vi.mocked(harvestApi.getBatches).mockResolvedValue([]);
});

describe('PostHarvestPage (mobile layout)', () => {
  it('renders the mobile card for a batch', async () => {
    renderWithProviders(<PostHarvestPage />);
    expect(await screen.findByTestId('post-harvest-page')).toBeInTheDocument();
    // Mobile card renders the harvest batch key as its title.
    expect(await screen.findByText('hb-1')).toBeInTheDocument();
    // Dryness field value from the mobile card renderer.
    expect(await screen.findByText('96%')).toBeInTheDocument();
  });
});
