import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import i18n from 'i18next';
import type { ReadinessAssessment } from '@/api/types';
import * as harvestApi from '@/api/endpoints/harvest';
import HarvestReadinessSection from '@/pages/pflanzen/HarvestReadinessSection';
import { createTestStore, renderWithProviders } from '../helpers';

// Isolated module mock: the section's four states are driven purely by how the
// readiness request settles, so control it directly rather than through MSW.
vi.mock('@/api/endpoints/harvest');

const mocked = vi.mocked(harvestApi);

function makeReadiness(overrides: Partial<ReadinessAssessment> = {}): ReadinessAssessment {
  return {
    overall_score: 92,
    recommendation: 'optimal',
    estimated_days: 1,
    indicators: [
      { indicator_key: 'trichome', stage: 'peak', score: 100, reliability: 0.9, weighted_contribution: 90 },
    ],
    ...overrides,
  };
}

/** The shape the backend returns for a plant with no ripeness observations. */
function makeNoDataReadiness(): ReadinessAssessment {
  return { overall_score: 0, recommendation: 'immature', estimated_days: null, indicators: [] };
}

describe('HarvestReadinessSection — plant-detail wiring (REQ-007 §3)', () => {
  beforeEach(async () => {
    vi.clearAllMocks();
    await i18n.changeLanguage('de');
  });

  it('dispatches fetchReadiness for its plant on mount and renders the card', async () => {
    mocked.assessReadiness.mockResolvedValue(makeReadiness());

    renderWithProviders(<HarvestReadinessSection plantKey="pl-1" />);

    await waitFor(() => expect(mocked.assessReadiness).toHaveBeenCalledWith('pl-1'));
    expect(await screen.findByTestId('harvest-readiness-card')).toBeInTheDocument();
    expect(screen.getByText('92')).toBeInTheDocument();
    expect(screen.getByText(i18n.t('pages.harvest.readinessIntro'))).toBeInTheDocument();
  });

  it('stores the assessment in the harvest slice under the requested plant key', async () => {
    mocked.assessReadiness.mockResolvedValue(makeReadiness());

    const store = createTestStore();
    renderWithProviders(<HarvestReadinessSection plantKey="pl-1" />, { store });

    await screen.findByTestId('harvest-readiness-card');
    expect(store.getState().harvest.readinessPlantKey).toBe('pl-1');
    expect(store.getState().harvest.readiness?.overall_score).toBe(92);
  });

  it('shows a skeleton while the assessment is in flight', async () => {
    // Never settles — pins the section in its loading state.
    mocked.assessReadiness.mockReturnValue(new Promise<ReadinessAssessment>(() => {}));

    renderWithProviders(<HarvestReadinessSection plantKey="pl-1" />);

    expect(await screen.findByTestId('harvest-readiness-loading')).toBeInTheDocument();
    // The suite-wide loading marker the E2E page objects wait on.
    const skeleton = screen.getByTestId('loading-skeleton');
    expect(skeleton).toHaveAttribute('aria-busy', 'true');
    expect(skeleton).toHaveAttribute('aria-label', i18n.t('pages.harvest.readinessLoading'));
    expect(screen.queryByTestId('harvest-readiness-card')).toBeNull();
  });

  it('never paints another plant\'s cached assessment while its own request is pending', () => {
    mocked.assessReadiness.mockReturnValue(new Promise<ReadinessAssessment>(() => {}));

    // A sibling plant's assessment is already in the shared slice slot.
    const store = createTestStore({
      harvest: {
        indicators: [], observations: [], batches: [], currentBatch: null, quality: null,
        yieldMetric: null, loading: false, error: null,
        readiness: makeReadiness({ overall_score: 17 }),
        readinessPlantKey: 'pl-other',
        readinessLoading: false,
        readinessError: null,
      },
    });
    renderWithProviders(<HarvestReadinessSection plantKey="pl-1" />, { store });

    expect(screen.getByTestId('harvest-readiness-loading')).toBeInTheDocument();
    expect(screen.queryByText('17')).toBeNull();
  });

  it('explains the absence of data instead of rendering a zero-score card', async () => {
    mocked.assessReadiness.mockResolvedValue(makeNoDataReadiness());

    renderWithProviders(<HarvestReadinessSection plantKey="pl-1" />);

    expect(await screen.findByTestId('harvest-readiness-empty')).toBeInTheDocument();
    expect(screen.getByText(i18n.t('pages.harvest.readinessNoData'))).toBeInTheDocument();
    expect(screen.getByText(i18n.t('pages.harvest.readinessNoDataHint'))).toBeInTheDocument();
    // A "0 / Unreif" gauge would read as a measurement rather than as missing data.
    expect(screen.queryByTestId('harvest-readiness-card')).toBeNull();
    expect(screen.queryByRole('progressbar')).toBeNull();
  });

  it('surfaces a load failure with a working retry', async () => {
    const user = userEvent.setup();
    mocked.assessReadiness.mockRejectedValueOnce(new Error('errors.server'));

    renderWithProviders(<HarvestReadinessSection plantKey="pl-1" />);

    expect(await screen.findByTestId('harvest-readiness-error')).toBeInTheDocument();
    // The slice stores an `errors.*` key; ErrorDisplay resolves it to the locale.
    expect(screen.getByTestId('error-message')).toHaveTextContent(i18n.t('errors.server'));
    expect(screen.queryByTestId('harvest-readiness-card')).toBeNull();

    mocked.assessReadiness.mockResolvedValueOnce(makeReadiness());
    await user.click(screen.getByTestId('error-retry-button'));

    expect(await screen.findByTestId('harvest-readiness-card')).toBeInTheDocument();
    expect(mocked.assessReadiness).toHaveBeenCalledTimes(2);
  });

  it('re-requests the assessment when a sibling plant is opened on the same store', async () => {
    // A shared store across both mounts reproduces navigating from one plant
    // detail page to the next: the first plant's assessment is still cached.
    const store = createTestStore();
    mocked.assessReadiness.mockResolvedValue(makeReadiness());

    const first = renderWithProviders(<HarvestReadinessSection plantKey="pl-1" />, { store });
    await screen.findByTestId('harvest-readiness-card');
    expect(screen.getByText('92')).toBeInTheDocument();
    first.unmount();

    mocked.assessReadiness.mockResolvedValue(makeReadiness({ overall_score: 41, recommendation: 'developing' }));
    renderWithProviders(<HarvestReadinessSection plantKey="pl-2" />, { store });

    await waitFor(() => expect(mocked.assessReadiness).toHaveBeenLastCalledWith('pl-2'));
    expect(await screen.findByText('41')).toBeInTheDocument();
    // The previous plant's score must not linger.
    expect(screen.queryByText('92')).toBeNull();
    expect(store.getState().harvest.readinessPlantKey).toBe('pl-2');
  });
});
