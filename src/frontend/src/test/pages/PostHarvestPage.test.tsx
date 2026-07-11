import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import type {
  PostHarvestBatch,
  PostHarvestBatchDetail,
} from '@/api/types';

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
  stage: 'drying',
  species_type: 'flower',
  drying_method: 'hang_dry',
  start_weight_g: 450,
  current_weight_g: 300,
  target_moisture_percent: 10,
  dryness_progress_percent: 40,
  ready_for_curing: false,
  snap_test_passed: null,
  water_activity: null,
  storage_location: null,
  pesticide_residue_status: 'untested',
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

const DETAIL: PostHarvestBatchDetail = {
  batch: BATCH,
  latest_drying_progress: null,
  open_mold_alerts: 0,
};

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(postHarvestApi.getBatches).mockResolvedValue([BATCH]);
  vi.mocked(postHarvestApi.getBatch).mockResolvedValue(DETAIL);
  vi.mocked(harvestApi.getBatches).mockResolvedValue([]);
});

describe('PostHarvestPage', () => {
  it('renders and loads post-harvest batches', async () => {
    renderWithProviders(<PostHarvestPage />);
    expect(await screen.findByTestId('post-harvest-page')).toBeInTheDocument();
    expect(postHarvestApi.getBatches).toHaveBeenCalled();
    expect(await screen.findByText('hb-1')).toBeInTheDocument();
    expect(screen.getByTestId('start-drying-button')).toBeInTheDocument();
  });

  it('opens the start-drying dialog', async () => {
    const user = userEvent.setup();
    renderWithProviders(<PostHarvestPage />);
    await screen.findByText('hb-1');
    await user.click(screen.getByTestId('start-drying-button'));
    expect(await screen.findByTestId('start-drying-dialog')).toBeInTheDocument();
  });

  it('opens the detail dialog on row click and shows the advance action', async () => {
    const user = userEvent.setup();
    renderWithProviders(<PostHarvestPage />);
    const row = await screen.findByText('hb-1');
    await user.click(row);
    expect(await screen.findByTestId('post-harvest-detail-dialog')).toBeInTheDocument();
    await waitFor(() => expect(postHarvestApi.getBatch).toHaveBeenCalledWith('ph1'));
    expect(await screen.findByTestId('stage-chip')).toBeInTheDocument();
    expect(await screen.findByTestId('advance-stage-button')).toBeInTheDocument();
  });

  it('advances the stage when the drying criterion is met', async () => {
    const user = userEvent.setup();
    const ready = { ...BATCH, dryness_progress_percent: 96, ready_for_curing: true };
    vi.mocked(postHarvestApi.getBatch).mockResolvedValue({ ...DETAIL, batch: ready });
    vi.mocked(postHarvestApi.advanceStage).mockResolvedValue({ ...ready, stage: 'curing' });

    renderWithProviders(<PostHarvestPage />);
    await user.click(await screen.findByText('hb-1'));
    const advance = await screen.findByTestId('advance-stage-button');
    expect(advance).not.toBeDisabled();
    await user.click(advance);
    await waitFor(() =>
      expect(postHarvestApi.advanceStage).toHaveBeenCalledWith('ph1', 'curing'),
    );
  });

  it('blocks advancing to curing while drying is incomplete', async () => {
    const user = userEvent.setup();
    renderWithProviders(<PostHarvestPage />);
    await user.click(await screen.findByText('hb-1'));
    const advance = await screen.findByTestId('advance-stage-button');
    expect(advance).toBeDisabled();
  });
});
