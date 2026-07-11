import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import type {
  HarvestBatch,
  PostHarvestBatch,
  PostHarvestBatchDetail,
} from '@/api/types';

vi.mock('@/api/endpoints/postHarvest');
vi.mock('@/api/endpoints/harvest');

import * as postHarvestApi from '@/api/endpoints/postHarvest';
import * as harvestApi from '@/api/endpoints/harvest';
import StartDryingDialog from '@/pages/post-harvest/StartDryingDialog';
import PostHarvestDetailDialog from '@/pages/post-harvest/PostHarvestDetailDialog';
import { renderWithProviders, createTestStore } from '../helpers';

const HARVEST_BATCH = {
  key: 'hb-1',
  batch_id: 'ERNTE-001',
  plant_key: 'pl1',
} as HarvestBatch;

const DRYING_BATCH: PostHarvestBatch = {
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
  batch: DRYING_BATCH,
  latest_drying_progress: null,
  open_mold_alerts: 2,
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe('StartDryingDialog', () => {
  it('submits the start-drying request for the selected harvest batch', async () => {
    const user = userEvent.setup();
    vi.mocked(harvestApi.getBatches).mockResolvedValue([HARVEST_BATCH]);
    vi.mocked(postHarvestApi.startDrying).mockResolvedValue(DRYING_BATCH);
    const onCreated = vi.fn();

    renderWithProviders(
      <StartDryingDialog open onClose={vi.fn()} onCreated={onCreated} />,
    );

    // Wait for harvest batches to load into the select.
    await waitFor(() => expect(harvestApi.getBatches).toHaveBeenCalled());

    // Open the harvest-batch select and choose the option.
    const combos = await screen.findAllByRole('combobox');
    await user.click(combos[0]);
    await user.click(await screen.findByRole('option', { name: 'ERNTE-001' }));

    await user.click(
      screen.getByRole('button', { name: /Trocknung starten|Start drying/i }),
    );

    await waitFor(() => expect(postHarvestApi.startDrying).toHaveBeenCalled());
    const payload = vi.mocked(postHarvestApi.startDrying).mock.calls[0][0];
    expect(payload.harvest_batch_key).toBe('hb-1');
    expect(onCreated).toHaveBeenCalled();
  });

  it('disables the batch select when no harvest batches are available', async () => {
    vi.mocked(harvestApi.getBatches).mockResolvedValue([]);
    renderWithProviders(
      <StartDryingDialog open onClose={vi.fn()} onCreated={vi.fn()} />,
    );
    await waitFor(() => expect(harvestApi.getBatches).toHaveBeenCalled());
    expect(
      await screen.findByText(/Keine Erntechargen|No harvest batches/i),
    ).toBeInTheDocument();
  });
});

describe('PostHarvestDetailDialog', () => {
  it('shows the open mold-alert banner and records a new weight', async () => {
    const user = userEvent.setup();
    vi.mocked(postHarvestApi.getBatch).mockResolvedValue(DETAIL);
    vi.mocked(postHarvestApi.recordDryingProgress).mockResolvedValue({
      key: 'dp1',
    } as never);
    const store = createTestStore();
    const onChanged = vi.fn();

    renderWithProviders(
      <PostHarvestDetailDialog batchKey="ph1" onClose={vi.fn()} onChanged={onChanged} />,
      { store },
    );

    await waitFor(() => expect(postHarvestApi.getBatch).toHaveBeenCalledWith('ph1'));
    expect(await screen.findByTestId('mold-alert-banner')).toBeInTheDocument();

    const input = await screen.findByTestId('current-weight-input');
    await user.type(input.querySelector('input') as HTMLInputElement, '180');
    await user.click(screen.getByTestId('record-weight-button'));

    await waitFor(() =>
      expect(postHarvestApi.recordDryingProgress).toHaveBeenCalledWith('ph1', {
        current_weight_g: 180,
      }),
    );
    expect(onChanged).toHaveBeenCalled();
  });

  it('renders nothing actionable when no batch key is provided', () => {
    renderWithProviders(
      <PostHarvestDetailDialog batchKey={null} onClose={vi.fn()} onChanged={vi.fn()} />,
    );
    expect(screen.queryByTestId('advance-stage-button')).not.toBeInTheDocument();
  });
});
