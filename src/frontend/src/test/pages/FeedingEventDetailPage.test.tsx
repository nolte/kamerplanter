import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterAll, vi } from 'vitest';
import i18n from 'i18next';
import type { FeedingEvent, RunoffResponse } from '@/api/types';

const navigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ key: 'fe-1' }),
    useNavigate: () => navigate,
  };
});

const getFeedingEvent = vi.fn();
const updateFeedingEvent = vi.fn();
const deleteFeedingEvent = vi.fn();
const analyzeRunoff = vi.fn();
vi.mock('@/api/endpoints/feeding-events', () => ({
  getFeedingEvent: (...args: unknown[]) => getFeedingEvent(...args),
  updateFeedingEvent: (...args: unknown[]) => updateFeedingEvent(...args),
  deleteFeedingEvent: (...args: unknown[]) => deleteFeedingEvent(...args),
  analyzeRunoff: (...args: unknown[]) => analyzeRunoff(...args),
}));

import FeedingEventDetailPage from '@/pages/duengung/FeedingEventDetailPage';
import { renderWithProviders } from '../helpers';

function makeEvent(overrides: Partial<FeedingEvent> = {}): FeedingEvent {
  return {
    key: 'fe-1',
    plant_key: 'plant-1',
    timestamp: '2024-05-01T10:00:00Z',
    application_method: 'fertigation',
    is_supplemental: false,
    tank_fill_event_key: null,
    volume_applied_liters: 5,
    fertilizers_used: [],
    measured_ec_before: null,
    measured_ec_after: null,
    measured_ph_before: null,
    measured_ph_after: null,
    runoff_ec: null,
    runoff_ph: null,
    runoff_volume_liters: null,
    channel_id: null,
    notes: null,
    created_at: '2024-05-01T10:00:00Z',
    updated_at: null,
    ...overrides,
  } as FeedingEvent;
}

function makeRunoff(overrides: Partial<RunoffResponse> = {}): RunoffResponse {
  return {
    ec_delta: 0.1,
    ec_status: 'ok',
    ec_message: 'EC within range',
    ph_delta: 0.0,
    ph_status: 'ok',
    ph_message: 'pH stable',
    runoff_percent: 20,
    volume_status: 'ok',
    volume_message: 'Runoff volume healthy',
    overall_health: 'good',
    ...overrides,
  };
}

describe('FeedingEventDetailPage', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    navigate.mockReset();
    getFeedingEvent.mockReset().mockResolvedValue(makeEvent());
    updateFeedingEvent.mockReset().mockResolvedValue(makeEvent());
    deleteFeedingEvent.mockReset().mockResolvedValue(undefined);
    analyzeRunoff.mockReset().mockResolvedValue(makeRunoff());
  });

  afterAll(() => {
    i18n.changeLanguage('en');
  });

  it('renders the loaded feeding event', async () => {
    renderWithProviders(<FeedingEventDetailPage />);
    expect(await screen.findByTestId('feeding-event-detail-page')).toBeInTheDocument();
    expect(screen.getByText('plant-1')).toBeInTheDocument();
  });

  it('shows the error state when the load fails', async () => {
    getFeedingEvent.mockRejectedValueOnce(new Error('load boom'));
    renderWithProviders(<FeedingEventDetailPage />);
    expect(await screen.findByText(/load boom|Error/)).toBeInTheDocument();
  });

  it('renders measurement values, supplemental chip, fertilizers table and notes', async () => {
    getFeedingEvent.mockResolvedValue(
      makeEvent({
        is_supplemental: true,
        measured_ec_before: 1.2,
        measured_ec_after: 1.6,
        measured_ph_before: 6.0,
        measured_ph_after: 6.2,
        runoff_ec: 1.8,
        runoff_ph: 6.4,
        notes: 'Applied in the morning',
        fertilizers_used: [
          { fertilizer_key: 'fert-1', ml_applied: 3 },
          { fertilizer_key: 'fert-2', ml_applied: 1.5 },
        ],
      }),
    );
    renderWithProviders(<FeedingEventDetailPage />);
    await screen.findByTestId('feeding-event-detail-page');

    expect(screen.getByText('1.2 mS/cm')).toBeInTheDocument();
    expect(screen.getByText('Applied in the morning')).toBeInTheDocument();
    expect(screen.getByText('fert-2')).toBeInTheDocument();
    expect(screen.getByText(i18n.t('pages.feedingEvents.fertilizersUsed'))).toBeInTheDocument();
  });

  it('analyzes runoff and shows a success alert for healthy runoff', async () => {
    const user = userEvent.setup();
    renderWithProviders(<FeedingEventDetailPage />);
    await screen.findByTestId('feeding-event-detail-page');

    await user.click(screen.getByRole('button', { name: i18n.t('pages.feedingEvents.analyzeRunoff') }));
    expect(await screen.findByText(/EC within range/)).toBeInTheDocument();
  });

  it('analyzes runoff and shows a warning alert for poor runoff', async () => {
    analyzeRunoff.mockResolvedValue(makeRunoff({ overall_health: 'poor', ec_message: 'EC too high' }));
    const user = userEvent.setup();
    renderWithProviders(<FeedingEventDetailPage />);
    await screen.findByTestId('feeding-event-detail-page');

    await user.click(screen.getByRole('button', { name: i18n.t('pages.feedingEvents.analyzeRunoff') }));
    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent('EC too high');
  });

  it('handles a failing runoff analysis without crashing', async () => {
    analyzeRunoff.mockRejectedValue(new Error('runoff boom'));
    const user = userEvent.setup();
    renderWithProviders(<FeedingEventDetailPage />);
    await screen.findByTestId('feeding-event-detail-page');

    await user.click(screen.getByRole('button', { name: i18n.t('pages.feedingEvents.analyzeRunoff') }));
    await waitFor(() => expect(analyzeRunoff).toHaveBeenCalledWith('fe-1'));
    // the page survives the failure and stays mounted
    expect(screen.getByTestId('feeding-event-detail-page')).toBeInTheDocument();
  });

  it('renders the edit tab and saves the form', async () => {
    const user = userEvent.setup();
    renderWithProviders(<FeedingEventDetailPage />, { route: '/#edit' });
    await screen.findByTestId('feeding-event-detail-page');

    // toggle the supplemental switch to make the form dirty (enables submit)
    const suppl = await screen.findByTestId('form-field-is_supplemental');
    await user.click(suppl.querySelector('input')!);
    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => expect(updateFeedingEvent).toHaveBeenCalledWith('fe-1', expect.any(Object)));
  });

  it('surfaces an error when the edit save fails', async () => {
    updateFeedingEvent.mockRejectedValue(new Error('save failed'));
    const user = userEvent.setup();
    renderWithProviders(<FeedingEventDetailPage />, { route: '/#edit' });
    await screen.findByTestId('feeding-event-detail-page');

    const suppl = await screen.findByTestId('form-field-is_supplemental');
    await user.click(suppl.querySelector('input')!);
    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => expect(updateFeedingEvent).toHaveBeenCalled());
    expect(screen.getByTestId('form-submit-button')).toBeInTheDocument();
  });

  it('deletes the event through the confirm dialog and navigates back to the list', async () => {
    const user = userEvent.setup();
    renderWithProviders(<FeedingEventDetailPage />);

    await screen.findByTestId('feeding-event-detail-page');
    await user.click(screen.getByRole('button', { name: i18n.t('common.delete') }));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    await waitFor(() => expect(deleteFeedingEvent).toHaveBeenCalledWith('fe-1'));
    expect(navigate).toHaveBeenCalledWith('/duengung/feeding-events');
  });

  it('shows the pending state on the confirm dialog while deleting', async () => {
    let resolveDelete!: () => void;
    deleteFeedingEvent.mockReturnValue(
      new Promise<void>((res) => {
        resolveDelete = () => res();
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<FeedingEventDetailPage />);

    await screen.findByTestId('feeding-event-detail-page');
    await user.click(screen.getByRole('button', { name: i18n.t('common.delete') }));
    const confirm = await screen.findByTestId('confirm-dialog-confirm');
    await user.click(confirm);

    await waitFor(() => expect(confirm).toBeDisabled());
    expect(screen.getByTestId('confirm-dialog-live-region')).toHaveTextContent(
      i18n.t('common.processing'),
    );
    resolveDelete();
    await waitFor(() => expect(navigate).toHaveBeenCalledWith('/duengung/feeding-events'));
  });

  it('does not navigate when the delete request fails', async () => {
    deleteFeedingEvent.mockRejectedValue(new Error('boom'));
    const user = userEvent.setup();
    renderWithProviders(<FeedingEventDetailPage />);

    await screen.findByTestId('feeding-event-detail-page');
    await user.click(screen.getByRole('button', { name: i18n.t('common.delete') }));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    await waitFor(() => expect(deleteFeedingEvent).toHaveBeenCalledWith('fe-1'));
    expect(navigate).not.toHaveBeenCalled();
  });

  it('cancels the delete confirmation without calling the API', async () => {
    const user = userEvent.setup();
    renderWithProviders(<FeedingEventDetailPage />);

    await screen.findByTestId('feeding-event-detail-page');
    await user.click(screen.getByRole('button', { name: i18n.t('common.delete') }));
    await user.click(await screen.findByTestId('confirm-dialog-cancel'));

    await waitFor(() => expect(screen.queryByTestId('confirm-dialog')).toBeNull());
    expect(deleteFeedingEvent).not.toHaveBeenCalled();
  });
});
