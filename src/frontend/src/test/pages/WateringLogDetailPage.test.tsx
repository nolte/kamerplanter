import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterAll, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import WateringLogDetailPage from '@/pages/giessprotokoll/WateringLogDetailPage';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (orig) => {
  const actual = await orig<typeof import('react-router-dom')>();
  return { ...actual, useParams: () => ({ key: 'wl-1' }), useNavigate: () => mockNavigate };
});

type LogShape = Record<string, unknown>;

const baseLog: LogShape = {
  key: 'wl-1',
  logged_at: '2024-05-10T08:00:00Z',
  application_method: 'fertigation',
  is_supplemental: false,
  volume_liters: 3.5,
  plant_keys: [],
  slot_keys: [],
  tank_fill_event_key: null,
  nutrient_plan_key: null,
  task_key: null,
  channel_id: null,
  fertilizers_used: [],
  ec_before: 1.2,
  ec_after: 1.6,
  ph_before: 6.0,
  ph_after: 6.2,
  runoff_ec: null,
  runoff_ph: null,
  runoff_volume_liters: null,
  water_source: 'tap',
  performed_by: null,
  notes: null,
  created_at: '2024-05-10T08:00:00Z',
  updated_at: null,
  resolved_plants: [],
  resolved_fertilizers: [],
};

function useLog(overrides: LogShape = {}) {
  server.use(
    http.get('/api/v1/t/:tenant/watering-logs/:key', () =>
      HttpResponse.json({ ...baseLog, ...overrides }),
    ),
  );
}

function useRunoff(overrides: Record<string, unknown> = {}) {
  server.use(
    http.get('/api/v1/t/:tenant/watering-logs/:key/runoff', () =>
      HttpResponse.json({
        ec_delta: 0.1,
        ec_status: 'ok',
        ec_message: 'EC within range',
        ph_delta: 0,
        ph_status: 'ok',
        ph_message: 'pH stable',
        runoff_percent: 20,
        volume_status: 'ok',
        volume_message: 'Runoff volume healthy',
        overall_health: 'good',
        ...overrides,
      }),
    ),
  );
}

function useUpdate(status = 200) {
  server.use(
    http.put('/api/v1/t/:tenant/watering-logs/:key', () =>
      status < 400
        ? HttpResponse.json(baseLog)
        : HttpResponse.json({ message: 'boom', error_code: 'INTERNAL_ERROR', details: [] }, { status }),
    ),
  );
}

function useDeleteResponse(status: number) {
  server.use(
    http.delete('/api/v1/t/:tenant/watering-logs/:key', () =>
      status < 400
        ? new HttpResponse(null, { status })
        : HttpResponse.json(
            { error_id: 'e1', error_code: 'INTERNAL_ERROR', message: 'boom', details: [], timestamp: '', path: '', method: '' },
            { status },
          ),
    ),
  );
}

describe('WateringLogDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    i18n.changeLanguage('de');
  });

  afterAll(() => {
    i18n.changeLanguage('en');
  });

  it('renders the watering-log detail page', async () => {
    useLog();
    renderWithProviders(<WateringLogDetailPage />);

    expect(await screen.findByTestId('watering-log-detail-page')).toBeTruthy();
    expect(screen.getByTestId('delete-watering-log-button')).toBeTruthy();
    // no plants linked message
    expect(screen.getByText(i18n.t('pages.wateringLogs.noPlantsLinked'))).toBeInTheDocument();
  });

  it('shows the error state (with retry) when loading fails', async () => {
    server.use(
      http.get('/api/v1/t/:tenant/watering-logs/:key', () =>
        HttpResponse.json({ message: 'boom', error_code: 'INTERNAL_ERROR', details: [] }, { status: 500 }),
      ),
    );
    renderWithProviders(<WateringLogDetailPage />);
    expect(await screen.findByTestId('error-display')).toBeInTheDocument();
  });

  it('renders plants, slots, runoff, fertilizers and meta info', async () => {
    useLog({
      is_supplemental: true,
      slot_keys: ['slot-a', 'slot-b'],
      runoff_ec: 1.9,
      runoff_ph: 6.5,
      runoff_volume_liters: 0.4,
      nutrient_plan_key: 'np-7',
      channel_id: 'chan-1',
      performed_by: 'Alex',
      notes: 'Evening watering',
      fertilizers_used: [{ fertilizer_key: 'fert-1', ml_per_liter: 2 }],
      resolved_plants: [{ key: 'plant-1', name: 'Tomato #1' }],
      resolved_fertilizers: [{ key: 'fert-1', name: 'Base A', ml_per_liter: 2 }],
    });
    renderWithProviders(<WateringLogDetailPage />);
    await screen.findByTestId('watering-log-detail-page');

    expect(screen.getByText('Tomato #1')).toBeInTheDocument();
    expect(screen.getByText('slot-a')).toBeInTheDocument();
    expect(screen.getByText('Base A')).toBeInTheDocument();
    expect(screen.getByText('Alex')).toBeInTheDocument();
    expect(screen.getByText('Evening watering')).toBeInTheDocument();
    expect(screen.getByText('np-7')).toBeInTheDocument();
  });

  it('analyzes runoff and shows a healthy result', async () => {
    useLog();
    useRunoff();
    const user = userEvent.setup();
    renderWithProviders(<WateringLogDetailPage />);
    await screen.findByTestId('watering-log-detail-page');

    await user.click(screen.getByTestId('analyze-runoff-button'));
    const result = await screen.findByTestId('runoff-analysis-result');
    expect(result).toHaveTextContent('EC within range');
  });

  it('analyzes runoff and shows a warning result', async () => {
    useLog();
    useRunoff({ overall_health: 'poor', ec_message: 'EC too high' });
    const user = userEvent.setup();
    renderWithProviders(<WateringLogDetailPage />);
    await screen.findByTestId('watering-log-detail-page');

    await user.click(screen.getByTestId('analyze-runoff-button'));
    const result = await screen.findByTestId('runoff-analysis-result');
    expect(result).toHaveTextContent('EC too high');
  });

  it('renders the edit tab and saves changes', async () => {
    useLog();
    useUpdate(200);
    const user = userEvent.setup();
    renderWithProviders(<WateringLogDetailPage />, { route: '/#edit' });
    await screen.findByTestId('watering-log-detail-page');

    const suppl = await screen.findByTestId('form-field-is_supplemental');
    await user.click(suppl.querySelector('input')!);
    await user.click(screen.getByTestId('form-submit-button'));

    // a successful save re-loads via getWateringLog and stays on the page
    await waitFor(() => expect(screen.getByTestId('watering-log-detail-page')).toBeInTheDocument());
  });

  it('deletes the log through the confirm dialog and navigates to the list', async () => {
    useLog();
    useDeleteResponse(204);
    const user = userEvent.setup();
    renderWithProviders(<WateringLogDetailPage />);

    await screen.findByTestId('watering-log-detail-page');
    await user.click(screen.getByTestId('delete-watering-log-button'));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/giessprotokoll'));
  });

  it('shows the pending state on the confirm dialog while deleting', async () => {
    useLog();
    let release!: () => void;
    const gate = new Promise<void>((res) => {
      release = res;
    });
    server.use(
      http.delete('/api/v1/t/:tenant/watering-logs/:key', async () => {
        await gate;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<WateringLogDetailPage />);

    await screen.findByTestId('watering-log-detail-page');
    await user.click(screen.getByTestId('delete-watering-log-button'));
    const confirm = await screen.findByTestId('confirm-dialog-confirm');
    await user.click(confirm);

    await waitFor(() => expect(confirm).toBeDisabled());
    expect(screen.getByTestId('confirm-dialog-live-region')).toHaveTextContent(
      i18n.t('common.processing'),
    );
    release();
    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/giessprotokoll'));
  });

  it('keeps the confirm dialog open and surfaces an error when deletion fails', async () => {
    useLog();
    useDeleteResponse(500);
    const user = userEvent.setup();
    renderWithProviders(<WateringLogDetailPage />);

    await screen.findByTestId('watering-log-detail-page');
    await user.click(screen.getByTestId('delete-watering-log-button'));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    expect(await screen.findByText(i18n.t('errors.server'))).toBeTruthy();
    expect(screen.getByTestId('confirm-dialog')).toBeTruthy();
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('cancels the delete confirmation without deleting', async () => {
    useLog();
    const user = userEvent.setup();
    renderWithProviders(<WateringLogDetailPage />);

    await screen.findByTestId('watering-log-detail-page');
    await user.click(screen.getByTestId('delete-watering-log-button'));
    await user.click(await screen.findByTestId('confirm-dialog-cancel'));

    await waitFor(() => expect(screen.queryByTestId('confirm-dialog')).toBeNull());
    expect(mockNavigate).not.toHaveBeenCalled();
  });
});
