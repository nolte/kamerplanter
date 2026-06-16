import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../helpers';
import { RecognitionStatusCard } from '@/components/admin/RecognitionStatusCard';
import type { RecognitionStatus } from '@/api/types';

// Mock the admin settings API module.
vi.mock('@/api/endpoints/adminSettings', () => ({
  getRecognitionStatus: vi.fn(),
  startRecognitionAcquisition: vi.fn(),
}));

import {
  getRecognitionStatus,
  startRecognitionAcquisition,
} from '@/api/endpoints/adminSettings';

const mockGetStatus = vi.mocked(getRecognitionStatus);
const mockStartAcquisition = vi.mocked(startRecognitionAcquisition);

function buildStatus(overrides: Partial<RecognitionStatus> = {}): RecognitionStatus {
  return {
    feature_enabled: true,
    local_adapter_available: true,
    inference_service: {
      enabled: true,
      url: 'http://kamerplanter-recognition:8000',
      ready: true,
      model: 'dinov2_vits14',
      dim: 384,
      license: 'Apache-2.0',
    },
    coverage: { total_species: 210, processed_species: 210, usable_species: 187 },
    config: {
      primary_adapter: 'local_embedding',
      confidence_auto_accept: 0.85,
      confidence_min_show: 0.1,
      reference_image_min_usable: 5,
      use_wikimedia: true,
    },
    ...overrides,
  };
}

describe('RecognitionStatusCard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows a discreet hint when the feature is disabled', async () => {
    mockGetStatus.mockResolvedValue(
      buildStatus({
        feature_enabled: false,
        local_adapter_available: false,
        inference_service: {
          enabled: false,
          url: null,
          ready: false,
          model: null,
          dim: null,
          license: null,
        },
      }),
    );

    renderWithProviders(<RecognitionStatusCard />);

    await waitFor(() =>
      expect(screen.getByTestId('recognition-disabled-hint')).toBeInTheDocument(),
    );
    expect(screen.getByText(/INFERENCE_SERVICE_ENABLED/)).toBeInTheDocument();
    // No status details / no service warning when disabled.
    expect(screen.queryByTestId('recognition-status-details')).not.toBeInTheDocument();
    expect(screen.queryByTestId('recognition-chip-active')).not.toBeInTheDocument();
  });

  it('renders status, model, coverage and config when enabled and ready', async () => {
    mockGetStatus.mockResolvedValue(buildStatus());

    renderWithProviders(<RecognitionStatusCard />);

    await waitFor(() =>
      expect(screen.getByTestId('recognition-status-details')).toBeInTheDocument(),
    );

    expect(screen.getByTestId('recognition-chip-active')).toBeInTheDocument();
    expect(screen.getByTestId('recognition-chip-ready')).toBeInTheDocument();
    // Model chip shows "model (dim)".
    expect(screen.getByText('dinov2_vits14 (384)')).toBeInTheDocument();
    // Coverage text with interpolated counts.
    expect(screen.getByTestId('recognition-coverage-text')).toHaveTextContent('187');
    expect(screen.getByTestId('recognition-coverage-text')).toHaveTextContent('210');
    expect(screen.getByTestId('recognition-processed-bar')).toBeInTheDocument();
    // Config values: percentages, min reference images, primary adapter.
    expect(screen.getByText('85%')).toBeInTheDocument();
    expect(screen.getByText('10%')).toBeInTheDocument();
    expect(screen.getByText('local_embedding')).toBeInTheDocument();
    // No service warning when ready.
    expect(screen.queryByTestId('recognition-service-warning')).not.toBeInTheDocument();
    expect(screen.queryByTestId('recognition-chip-unreachable')).not.toBeInTheDocument();
  });

  it('shows an unreachable warning when the service is not ready', async () => {
    mockGetStatus.mockResolvedValue(
      buildStatus({
        inference_service: {
          enabled: true,
          url: 'http://kamerplanter-recognition:8000',
          ready: false,
          model: null,
          dim: null,
          license: null,
        },
      }),
    );

    renderWithProviders(<RecognitionStatusCard />);

    await waitFor(() =>
      expect(screen.getByTestId('recognition-chip-unreachable')).toBeInTheDocument(),
    );
    expect(screen.getByTestId('recognition-service-warning')).toBeInTheDocument();
    // The active chip is still shown; the ready chip is not.
    expect(screen.getByTestId('recognition-chip-active')).toBeInTheDocument();
    expect(screen.queryByTestId('recognition-chip-ready')).not.toBeInTheDocument();
    // No model chip when not ready (model is null).
    expect(screen.queryByTestId('recognition-chip-model')).not.toBeInTheDocument();
  });

  it('shows "not started" + hint when no acquisition run has run yet', async () => {
    mockGetStatus.mockResolvedValue(
      buildStatus({ coverage: { total_species: 210, processed_species: 0, usable_species: 0 } }),
    );

    renderWithProviders(<RecognitionStatusCard />);

    await waitFor(() =>
      expect(screen.getByTestId('recognition-job-not-started')).toBeInTheDocument(),
    );
    expect(screen.getByTestId('recognition-processed-text')).toHaveTextContent('0');
    expect(screen.getByTestId('recognition-processed-text')).toHaveTextContent('210');
    expect(screen.queryByTestId('recognition-job-running')).not.toBeInTheDocument();
    expect(screen.queryByTestId('recognition-job-complete')).not.toBeInTheDocument();
  });

  it('shows "running" with live progress while an acquisition run is in progress', async () => {
    mockGetStatus.mockResolvedValue(
      buildStatus({ coverage: { total_species: 210, processed_species: 50, usable_species: 30 } }),
    );

    renderWithProviders(<RecognitionStatusCard />);

    await waitFor(() =>
      expect(screen.getByTestId('recognition-job-running')).toBeInTheDocument(),
    );
    expect(screen.getByTestId('recognition-processed-text')).toHaveTextContent('50');
    expect(screen.getByTestId('recognition-processed-bar')).toBeInTheDocument();
  });

  it('shows "completed" when all species have been processed', async () => {
    mockGetStatus.mockResolvedValue(buildStatus());

    renderWithProviders(<RecognitionStatusCard />);

    await waitFor(() =>
      expect(screen.getByTestId('recognition-job-complete')).toBeInTheDocument(),
    );
    expect(screen.queryByTestId('recognition-job-running')).not.toBeInTheDocument();
  });

  it('shows a discreet hint when the status request fails', async () => {
    mockGetStatus.mockRejectedValue(new Error('forbidden'));

    renderWithProviders(<RecognitionStatusCard />);

    await waitFor(() =>
      expect(screen.getByTestId('recognition-status-unavailable')).toBeInTheDocument(),
    );
    expect(screen.queryByTestId('recognition-status-details')).not.toBeInTheDocument();
  });

  it('dispatches an acquisition run when the start button is clicked', async () => {
    const user = userEvent.setup();
    mockGetStatus.mockResolvedValue(
      buildStatus({ coverage: { total_species: 210, processed_species: 0, usable_species: 0 } }),
    );
    mockStartAcquisition.mockResolvedValue({ status: 'queued', task_id: 'task-1' });

    renderWithProviders(<RecognitionStatusCard />);

    const button = await screen.findByTestId('recognition-acquire-button');
    await user.click(button);

    expect(mockStartAcquisition).toHaveBeenCalledTimes(1);
    // After dispatching, the status is re-fetched (initial + reload).
    await waitFor(() => expect(mockGetStatus).toHaveBeenCalledTimes(2));
    // While the run is queued (dispatched but no species processed yet) the card
    // shows a distinct "starting up" state instead of staying on "not started".
    await waitFor(() =>
      expect(screen.getByTestId('recognition-job-queued')).toBeInTheDocument(),
    );
    expect(screen.getByTestId('recognition-job-queued-hint')).toBeInTheDocument();
    expect(screen.queryByTestId('recognition-job-not-started')).not.toBeInTheDocument();
    // The button is disabled while the run is queued so it cannot be triggered twice.
    expect(screen.getByTestId('recognition-acquire-button')).toBeDisabled();
  });

  it('shows an error alert when starting the acquisition run fails', async () => {
    const user = userEvent.setup();
    mockGetStatus.mockResolvedValue(
      buildStatus({ coverage: { total_species: 210, processed_species: 0, usable_species: 0 } }),
    );
    mockStartAcquisition.mockRejectedValue(new Error('boom'));

    renderWithProviders(<RecognitionStatusCard />);

    const button = await screen.findByTestId('recognition-acquire-button');
    await user.click(button);

    await waitFor(() =>
      expect(screen.getByTestId('recognition-acquire-error')).toBeInTheDocument(),
    );
  });

  it('hides the start button when the inference service is unreachable', async () => {
    mockGetStatus.mockResolvedValue(
      buildStatus({
        inference_service: {
          enabled: true,
          url: 'http://kamerplanter-recognition:8000',
          ready: false,
          model: null,
          dim: null,
          license: null,
        },
      }),
    );

    renderWithProviders(<RecognitionStatusCard />);

    await waitFor(() =>
      expect(screen.getByTestId('recognition-chip-unreachable')).toBeInTheDocument(),
    );
    expect(screen.queryByTestId('recognition-acquire-button')).not.toBeInTheDocument();
  });
});
