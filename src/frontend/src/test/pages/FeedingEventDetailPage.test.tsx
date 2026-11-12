import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterAll, vi } from 'vitest';
import i18n from 'i18next';
import type { Fertilizer, FeedingEvent, PlantInstance, RunoffResponse } from '@/api/types';

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

const getPlantInstance = vi.fn();
vi.mock('@/api/endpoints/plantInstances', () => ({
  getPlantInstance: (...args: unknown[]) => getPlantInstance(...args),
}));

const fetchFertilizer = vi.fn();
vi.mock('@/api/endpoints/fertilizers', () => ({
  fetchFertilizer: (...args: unknown[]) => fetchFertilizer(...args),
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

/** A compost dose logged in the care log (REQ-053 W-007): no volume, the dose in the dose fields (#2903). */
function makeTopDress(overrides: Partial<FeedingEvent> = {}): FeedingEvent {
  return makeEvent({
    plant_key: '121502',
    plant_keys: ['121502'],
    application_method: 'top_dress',
    volume_applied_liters: 0,
    location_key: 'bed-3',
    material: 'compost',
    dose_quantity: 2,
    dose_unit: 'l',
    ...overrides,
  });
}

function makePlant(key: string, name: string): PlantInstance {
  return { key, instance_id: `ID-${key}`, plant_name: name } as PlantInstance;
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
    getPlantInstance.mockReset().mockRejectedValue(new Error('no plant'));
    fetchFertilizer.mockReset().mockRejectedValue(new Error('no fertilizer'));
  });

  afterAll(() => {
    i18n.changeLanguage('en');
  });

  it('renders the loaded feeding event', async () => {
    renderWithProviders(<FeedingEventDetailPage />);
    expect(await screen.findByTestId('feeding-event-detail-page')).toBeInTheDocument();
    // The plant label resolves after its own request; an unloadable plant keeps its key.
    expect(await screen.findByText('plant-1')).toBeInTheDocument();
  });

  it('shows the name of the plant instead of its key', async () => {
    getPlantInstance.mockImplementation(async (key: string) => makePlant(key, 'Tomate'));
    renderWithProviders(<FeedingEventDetailPage />);

    const plants = await screen.findByTestId('feeding-event-plants');
    expect(await within(plants).findByText('ID-plant-1 (Tomate)')).toBeInTheDocument();
    expect(getPlantInstance).toHaveBeenCalledWith('plant-1');
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

  describe('a top dress (#2903)', () => {
    it('shows material, amount and the plant name and hides the liquid-only fields', async () => {
      getFeedingEvent.mockResolvedValue(makeTopDress());
      getPlantInstance.mockImplementation(async (key: string) => makePlant(key, 'Tomate'));
      renderWithProviders(<FeedingEventDetailPage />);
      await screen.findByTestId('feeding-event-detail-page');

      expect(screen.getByTestId('feeding-event-material')).toHaveTextContent('Kompost');
      expect(screen.getByTestId('feeding-event-dose')).toHaveTextContent('2 Liter');
      const plants = screen.getByTestId('feeding-event-plants');
      expect(await within(plants).findByText('ID-121502 (Tomate)')).toBeInTheDocument();
      expect(within(plants).queryByText('121502')).toBeNull();
      // no "0 L", no EC/pH/run-off, no run-off analysis
      expect(screen.queryByText(i18n.t('pages.feedingEvents.volumeApplied'))).toBeNull();
      expect(screen.queryByText('0 L')).toBeNull();
      expect(screen.queryByText(i18n.t('pages.feedingEvents.ecBefore'))).toBeNull();
      expect(screen.queryByText(i18n.t('pages.feedingEvents.runoffPh'))).toBeNull();
      expect(screen.queryByRole('button', { name: i18n.t('pages.feedingEvents.analyzeRunoff') })).toBeNull();
    });

    it('shows an area dose with the total for the bed', async () => {
      getFeedingEvent.mockResolvedValue(
        makeTopDress({ material: 'horn_shavings', dose_quantity: 50, dose_unit: 'g_per_m2', quantity_total: 125, quantity_total_unit: 'g' }),
      );
      renderWithProviders(<FeedingEventDetailPage />);
      await screen.findByTestId('feeding-event-detail-page');

      expect(screen.getByTestId('feeding-event-material')).toHaveTextContent('Hornspäne');
      expect(screen.getByTestId('feeding-event-dose')).toHaveTextContent('50 Gramm pro m² (125 Gramm gesamt)');
    });

    it('falls back to the key when the plant cannot be loaded', async () => {
      getFeedingEvent.mockResolvedValue(makeTopDress());
      renderWithProviders(<FeedingEventDetailPage />);

      const plants = await screen.findByTestId('feeding-event-plants');
      expect(await within(plants).findByText('121502')).toBeInTheDocument();
    });

    it('names several plants and counts a whole bed instead of loading every plant', async () => {
      getPlantInstance.mockImplementation(async (key: string) => makePlant(key, `Plant ${key}`));
      getFeedingEvent.mockResolvedValue(makeTopDress({ plant_keys: ['p1', 'p2'] }));
      const { unmount } = renderWithProviders(<FeedingEventDetailPage />);
      const plants = await screen.findByTestId('feeding-event-plants');
      expect(await within(plants).findByText('ID-p1 (Plant p1)')).toBeInTheDocument();
      expect(within(plants).getByText('ID-p2 (Plant p2)')).toBeInTheDocument();
      expect(screen.getByText(i18n.t('pages.feedingEvents.plants'))).toBeInTheDocument();
      unmount();

      getPlantInstance.mockClear();
      const bed = Array.from({ length: 12 }, (_, n) => `p${n}`);
      getFeedingEvent.mockResolvedValue(makeTopDress({ plant_keys: bed }));
      renderWithProviders(<FeedingEventDetailPage />);
      expect(await screen.findByTestId('feeding-event-plants')).toHaveTextContent('12 Pflanzen');
      expect(getPlantInstance).not.toHaveBeenCalled();
    });

    it('shows the product a dose names, by its catalogue name or as typed', async () => {
      fetchFertilizer.mockResolvedValue({ key: 'fert-1', product_name: 'Bio Grow' } as Fertilizer);
      getFeedingEvent.mockResolvedValue(makeTopDress({ material: null, product_key: 'fert-1', dose_unit: 'g' }));
      const { unmount } = renderWithProviders(<FeedingEventDetailPage />);
      expect(await screen.findByText('Bio Grow')).toBeInTheDocument();
      expect(screen.queryByTestId('feeding-event-material')).toBeNull();
      unmount();

      getFeedingEvent.mockResolvedValue(makeTopDress({ product_label: 'Brennnesseljauche' }));
      renderWithProviders(<FeedingEventDetailPage />);
      expect(await screen.findByTestId('feeding-event-product')).toHaveTextContent('Brennnesseljauche');
    });

    it('saves an edit without demanding a volume', async () => {
      getFeedingEvent.mockResolvedValue(makeTopDress());
      const user = userEvent.setup();
      renderWithProviders(<FeedingEventDetailPage />, { route: '/#edit' });
      await screen.findByTestId('feeding-event-detail-page');

      const volume = within(await screen.findByTestId('form-field-volume_applied_liters')).getByRole('spinbutton');
      expect(volume).toHaveValue(null);
      expect(volume).not.toBeRequired();
      expect(screen.queryByText(i18n.t('pages.feedingEvents.sectionRunoff'))).toBeNull();
      await user.type(screen.getByTestId('form-field-notes').querySelector('textarea')!, 'Mulched after');
      await user.click(screen.getByTestId('form-submit-button'));

      await waitFor(() =>
        expect(updateFeedingEvent).toHaveBeenCalledWith(
          'fe-1',
          expect.objectContaining({ application_method: 'top_dress', volume_applied_liters: null }),
        ),
      );
    });
  });

  it('still demands a volume when a solution is edited', async () => {
    const user = userEvent.setup();
    renderWithProviders(<FeedingEventDetailPage />, { route: '/#edit' });
    await screen.findByTestId('feeding-event-detail-page');

    const field = await screen.findByTestId('form-field-volume_applied_liters');
    const volume = within(field).getByRole('spinbutton');
    expect(volume).toBeRequired();
    await user.clear(volume);
    await user.click(screen.getByTestId('form-submit-button'));

    expect(await within(field).findByText(i18n.t('validation.required'))).toBeInTheDocument();
    expect(updateFeedingEvent).not.toHaveBeenCalled();
  });

  it('lets a logged concentrate dose without a volume be edited', async () => {
    // millilitres of a concentrate logged in the care log: a drench whose water is unknown (no volume)
    getFeedingEvent.mockResolvedValue(
      makeEvent({ application_method: 'drench', volume_applied_liters: 0, dose_quantity: 5, dose_unit: 'ml' }),
    );
    const user = userEvent.setup();
    renderWithProviders(<FeedingEventDetailPage />, { route: '/#edit' });
    await screen.findByTestId('feeding-event-detail-page');

    const volume = within(await screen.findByTestId('form-field-volume_applied_liters')).getByRole('spinbutton');
    expect(volume).not.toBeRequired();
    const suppl = await screen.findByTestId('form-field-is_supplemental');
    await user.click(suppl.querySelector('input')!);
    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() =>
      expect(updateFeedingEvent).toHaveBeenCalledWith('fe-1', expect.objectContaining({ volume_applied_liters: null })),
    );
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
