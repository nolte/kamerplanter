import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { http, HttpResponse, delay } from 'msw';
import i18n from 'i18next';
import SlotDetailPage from '@/pages/standorte/SlotDetailPage';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

const mockNavigate = vi.fn();
const routeState = vi.hoisted(() => ({ key: 'slot-1' as string | undefined }));
vi.mock('react-router-dom', async (orig) => {
  const actual = await orig<typeof import('react-router-dom')>();
  return { ...actual, useParams: () => ({ key: routeState.key }), useNavigate: () => mockNavigate };
});

const slot = {
  key: 'slot-1',
  slot_id: 'A1_B2',
  location_key: 'loc-1',
  position: [0, 0] as [number, number],
  capacity_plants: 4,
  currently_occupied: false,
  last_sanitization: null,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: null,
};

function useSlot() {
  server.use(
    http.get('/api/v1/t/:tenant/slots/:key', () => HttpResponse.json(slot)),
  );
}

function errorEnvelope(status: number) {
  return HttpResponse.json(
    {
      error_id: 'e1',
      error_code: 'INTERNAL_ERROR',
      message: 'boom',
      details: [],
      timestamp: '',
      path: '',
      method: '',
    },
    { status },
  );
}

function useDeleteResponse(status: number) {
  server.use(
    http.delete('/api/v1/t/:tenant/slots/:key', () =>
      status < 400 ? new HttpResponse(null, { status }) : errorEnvelope(status),
    ),
  );
}

describe('SlotDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    routeState.key = 'slot-1';
    i18n.changeLanguage('de');
  });
  afterEach(() => {
    i18n.changeLanguage('en');
  });

  it('stays in the loading state when no slot key is present', async () => {
    routeState.key = undefined;
    renderWithProviders(<SlotDetailPage />);

    // load() short-circuits on a missing key, so the form never appears.
    await waitFor(() =>
      expect(screen.queryByTestId('slot-detail-page')).toBeNull(),
    );
  });

  it('renders the slot and its title', async () => {
    useSlot();
    renderWithProviders(<SlotDetailPage />);

    expect(await screen.findByTestId('slot-detail-page')).toBeTruthy();
    // Title renders the slot_id.
    expect(screen.getAllByText('A1_B2').length).toBeGreaterThan(0);
  });

  it('shows the error display when the slot cannot be loaded', async () => {
    server.use(
      http.get('/api/v1/t/:tenant/slots/:key', () => errorEnvelope(500)),
    );
    renderWithProviders(<SlotDetailPage />);

    // load()'s catch sets the error string; ErrorDisplay renders with a retry.
    const retry = await screen.findByRole('button', { name: i18n.t('common.retry') });
    const user = userEvent.setup();
    await user.click(retry);
    expect(mockNavigate).toHaveBeenCalledWith(-1);
    expect(screen.queryByTestId('slot-detail-page')).toBeNull();
  });

  it('saves the edited slot and notifies success', async () => {
    useSlot();
    let putBody: Record<string, unknown> | null = null;
    server.use(
      http.put('/api/v1/t/:tenant/slots/:key', async ({ request }) => {
        putBody = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({ ...slot, ...putBody });
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<SlotDetailPage />);

    await screen.findByTestId('slot-detail-page');
    const capacity = within(screen.getByTestId('form-field-capacity_plants')).getByRole('spinbutton');
    await user.clear(capacity);
    await user.type(capacity, '6');

    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => expect(putBody).not.toBeNull());
    expect(putBody!.capacity_plants).toBe(6);
    // slot_id is transformed to upper-case by the zod schema before submit.
    expect(putBody!.slot_id).toBe('A1_B2');
  });

  it('surfaces an API error when saving fails', async () => {
    useSlot();
    server.use(
      http.put('/api/v1/t/:tenant/slots/:key', () => errorEnvelope(500)),
    );
    const user = userEvent.setup();
    renderWithProviders(<SlotDetailPage />);

    await screen.findByTestId('slot-detail-page');
    await user.click(screen.getByTestId('form-submit-button'));

    expect(await screen.findByText(i18n.t('errors.server'))).toBeTruthy();
  });

  it('navigates back when cancelling the form', async () => {
    useSlot();
    const user = userEvent.setup();
    renderWithProviders(<SlotDetailPage />);

    await screen.findByTestId('slot-detail-page');
    await user.click(screen.getByTestId('form-cancel-button'));
    expect(mockNavigate).toHaveBeenCalledWith(-1);
  });

  it('deletes the slot through the confirm dialog and navigates back', async () => {
    useSlot();
    useDeleteResponse(204);
    const user = userEvent.setup();
    renderWithProviders(<SlotDetailPage />);

    await screen.findByTestId('slot-detail-page');
    await user.click(screen.getByRole('button', { name: i18n.t('common.delete') }));

    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith(-1));
    await waitFor(() =>
      expect(screen.queryByTestId('confirm-dialog')).toBeNull(),
    );
  });

  it('shows the pending state on the confirm dialog while deleting', async () => {
    useSlot();
    server.use(
      http.delete('/api/v1/t/:tenant/slots/:key', async () => {
        await delay(60);
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<SlotDetailPage />);

    await screen.findByTestId('slot-detail-page');
    await user.click(screen.getByRole('button', { name: i18n.t('common.delete') }));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    // While the request is in flight the confirm button is disabled and the
    // live-region announces the pending state (UI-NFR-004 R-020 / R-011).
    await waitFor(() =>
      expect(screen.getByTestId('confirm-dialog-confirm')).toBeDisabled(),
    );
    expect(screen.getByTestId('confirm-dialog-live-region').textContent).toBe(
      i18n.t('common.processing'),
    );

    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith(-1));
  });

  it('surfaces an error and does not navigate when deletion fails', async () => {
    useSlot();
    useDeleteResponse(500);
    const user = userEvent.setup();
    renderWithProviders(<SlotDetailPage />);

    await screen.findByTestId('slot-detail-page');
    await user.click(screen.getByRole('button', { name: i18n.t('common.delete') }));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    expect(await screen.findByText(i18n.t('errors.server'))).toBeTruthy();
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('cancels the delete confirmation without deleting', async () => {
    useSlot();
    const user = userEvent.setup();
    renderWithProviders(<SlotDetailPage />);

    await screen.findByTestId('slot-detail-page');
    await user.click(screen.getByRole('button', { name: i18n.t('common.delete') }));
    await user.click(await screen.findByTestId('confirm-dialog-cancel'));

    await waitFor(() =>
      expect(screen.queryByTestId('confirm-dialog')).toBeNull(),
    );
    expect(mockNavigate).not.toHaveBeenCalled();
  });
});
