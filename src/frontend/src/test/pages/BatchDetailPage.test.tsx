import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import type { Batch } from '@/api/types';
import BatchDetailPage from '@/pages/standorte/BatchDetailPage';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

const mockNavigate = vi.fn();
const params = vi.hoisted(() => ({ key: 'batch-1' as string | undefined }));
vi.mock('react-router-dom', async (orig) => {
  const actual = await orig<typeof import('react-router-dom')>();
  return { ...actual, useParams: () => ({ key: params.key }), useNavigate: () => mockNavigate };
});

function makeBatch(overrides: Partial<Batch> = {}): Batch {
  return {
    key: 'batch-1',
    batch_id: 'B-2024-001',
    substrate_key: 'sub-1',
    volume_liters: 20,
    mixed_on: '2024-05-01',
    last_amended: null,
    cycles_used: 1,
    ph_current: 6.1,
    ec_current_ms: 1.2,
    temperature_c: null,
    ph_history: [],
    ec_history: [],
    created_at: '2024-05-01T00:00:00Z',
    updated_at: null,
    ...overrides,
  };
}

/** Registers the GET handler and returns a counter of how often it was hit. */
function useBatch(batch: Batch = makeBatch()) {
  const state = { getCount: 0 };
  server.use(
    http.get('/api/v1/substrates/batches/:key', () => {
      state.getCount += 1;
      return HttpResponse.json(batch);
    }),
  );
  return state;
}

function useGetError() {
  server.use(
    http.get('/api/v1/substrates/batches/:key', () =>
      HttpResponse.json(
        {
          error_id: 'e1',
          error_code: 'ENTITY_NOT_FOUND',
          message: 'not found',
          details: [],
          timestamp: '',
          path: '',
          method: '',
        },
        { status: 404 },
      ),
    ),
  );
}

function useUpdateResponse(status: number, batch: Batch = makeBatch()) {
  server.use(
    http.put('/api/v1/substrates/batches/:key', () =>
      status < 400
        ? HttpResponse.json(batch, { status })
        : HttpResponse.json(
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
          ),
    ),
  );
}

function useDeleteResponse(status: number) {
  server.use(
    http.delete('/api/v1/substrates/batches/:key', () =>
      status < 400
        ? new HttpResponse(null, { status })
        : HttpResponse.json(
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
          ),
    ),
  );
}

describe('BatchDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    params.key = 'batch-1';
    i18n.changeLanguage('de');
  });

  it('stays in the loading state when no batch key is present in the route', async () => {
    params.key = undefined;
    useBatch();
    renderWithProviders(<BatchDetailPage />);

    // load() returns early without a key, so the form never appears.
    expect(await screen.findByTestId('loading-skeleton')).toBeInTheDocument();
    expect(screen.queryByTestId('form-submit-button')).toBeNull();
  });

  it('navigates back when the cancel action is used', async () => {
    useBatch();
    const user = userEvent.setup();
    renderWithProviders(<BatchDetailPage />);

    await screen.findAllByText('B-2024-001');
    await user.click(screen.getByTestId('form-cancel-button'));
    expect(mockNavigate).toHaveBeenCalledWith(-1);
  });

  it('renders the batch title, edit form and cycle / pH / EC info', async () => {
    useBatch();
    renderWithProviders(<BatchDetailPage />);

    expect(await screen.findAllByText('B-2024-001')).toBeTruthy();
    expect(screen.getByText(i18n.t('pages.batches.cyclesUsed'))).toBeTruthy();
    // ph_current and ec_current_ms are non-null -> both blocks render.
    expect(screen.getByText(i18n.t('pages.batches.phCurrent'))).toBeTruthy();
    expect(screen.getByText('6.1')).toBeTruthy();
    expect(screen.getByText(i18n.t('pages.batches.ecCurrent'))).toBeTruthy();
    expect(screen.getByText('1.2 mS/cm')).toBeTruthy();
    // The edit form fields are present.
    expect(screen.getByLabelText(new RegExp(i18n.t('pages.batches.batchId')))).toBeTruthy();
  });

  it('omits the pH and EC blocks when those readings are null', async () => {
    useBatch(makeBatch({ ph_current: null, ec_current_ms: null }));
    renderWithProviders(<BatchDetailPage />);

    await screen.findAllByText('B-2024-001');
    expect(screen.getByText(i18n.t('pages.batches.cyclesUsed'))).toBeTruthy();
    expect(screen.queryByText(i18n.t('pages.batches.phCurrent'))).toBeNull();
    expect(screen.queryByText(i18n.t('pages.batches.ecCurrent'))).toBeNull();
  });

  it('shows the error display with a retry action when loading fails', async () => {
    useGetError();
    const user = userEvent.setup();
    renderWithProviders(<BatchDetailPage />);

    expect(await screen.findByTestId('error-display')).toBeInTheDocument();
    await user.click(screen.getByTestId('error-retry-button'));
    expect(mockNavigate).toHaveBeenCalledWith(-1);
  });

  it('saves the batch and reloads it on submit success', async () => {
    const getState = useBatch();
    useUpdateResponse(200);
    const user = userEvent.setup();
    renderWithProviders(<BatchDetailPage />);

    await screen.findAllByText('B-2024-001');
    await waitFor(() => expect(getState.getCount).toBe(1));
    await user.click(screen.getByTestId('form-submit-button'));

    // onSubmit calls load() again after a successful update.
    await waitFor(() => expect(getState.getCount).toBe(2));
  });

  it('surfaces a server error when saving fails', async () => {
    useBatch();
    useUpdateResponse(500);
    const user = userEvent.setup();
    renderWithProviders(<BatchDetailPage />);

    await screen.findAllByText('B-2024-001');
    await user.click(screen.getByTestId('form-submit-button'));

    expect(await screen.findByText(i18n.t('errors.server'))).toBeInTheDocument();
  });

  it('deletes the batch through the confirm dialog and navigates back', async () => {
    useBatch();
    useDeleteResponse(204);
    const user = userEvent.setup();
    renderWithProviders(<BatchDetailPage />);

    await screen.findAllByText('B-2024-001');
    await user.click(screen.getByRole('button', { name: i18n.t('common.delete') }));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith(-1));
    await waitFor(() => expect(screen.queryByTestId('confirm-dialog')).toBeNull());
  });

  it('shows the pending state on the confirm button while the delete is in flight', async () => {
    useBatch();
    let resolveDelete: (() => void) | undefined;
    server.use(
      http.delete('/api/v1/substrates/batches/:key', async () => {
        await new Promise<void>((r) => {
          resolveDelete = r;
        });
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<BatchDetailPage />);

    await screen.findAllByText('B-2024-001');
    await user.click(screen.getByRole('button', { name: i18n.t('common.delete') }));
    const confirm = await screen.findByTestId('confirm-dialog-confirm');
    await user.click(confirm);

    // While in flight the confirm button is disabled and the live region announces progress.
    await waitFor(() => expect(confirm).toBeDisabled());
    expect(screen.getByTestId('confirm-dialog-live-region')).toHaveTextContent(
      i18n.t('common.processing'),
    );

    resolveDelete?.();
    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith(-1));
  });

  it('surfaces an error and does not navigate when deletion fails', async () => {
    useBatch();
    useDeleteResponse(500);
    const user = userEvent.setup();
    renderWithProviders(<BatchDetailPage />);

    await screen.findAllByText('B-2024-001');
    await user.click(screen.getByRole('button', { name: i18n.t('common.delete') }));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    expect(await screen.findByText(i18n.t('errors.server'))).toBeInTheDocument();
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('cancels the delete confirmation without deleting', async () => {
    useBatch();
    const user = userEvent.setup();
    renderWithProviders(<BatchDetailPage />);

    await screen.findAllByText('B-2024-001');
    await user.click(screen.getByRole('button', { name: i18n.t('common.delete') }));
    await user.click(await screen.findByTestId('confirm-dialog-cancel'));

    await waitFor(() => expect(screen.queryByTestId('confirm-dialog')).toBeNull());
    expect(mockNavigate).not.toHaveBeenCalled();
  });
});
