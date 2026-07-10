import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { http, HttpResponse, delay } from 'msw';
import i18n from 'i18next';
import SubstrateDetailPage from '@/pages/standorte/SubstrateDetailPage';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (orig) => {
  const actual = await orig<typeof import('react-router-dom')>();
  return { ...actual, useParams: () => ({ key: 'sub-1' }), useNavigate: () => mockNavigate };
});

const substrate = {
  key: 'sub-1',
  type: 'coco',
  brand: 'CocoBrand',
  name_de: 'Kokos Substrat',
  name_en: 'Coco Substrate',
  is_mix: false,
  mix_components: [],
  ph_base: 6.0,
  ec_base_ms: 0.4,
  water_retention: 'medium',
  air_porosity_percent: 30,
  composition: {},
  buffer_capacity: 'medium',
  reusable: true,
  max_reuse_cycles: 3,
  water_holding_capacity_percent: null,
  easily_available_water_percent: null,
  cec_meq_per_100g: null,
  particle_size_mm: null,
  bulk_density_g_per_l: null,
  irrigation_strategy: null,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: null,
};

const batch = {
  key: 'batch-1',
  batch_id: 'B-001',
  substrate_key: 'sub-1',
  volume_liters: 20,
  mixed_on: '2024-05-01',
  last_amended: null,
  cycles_used: 1,
  ph_current: null,
  ec_current_ms: null,
  temperature_c: null,
  ph_history: [],
  ec_history: [],
  created_at: '2024-05-01T00:00:00Z',
  updated_at: null,
};

function useSubstrate(overrides: Partial<typeof substrate> = {}, batches = [batch]) {
  server.use(
    http.get('/api/v1/substrates/sub-1', () => HttpResponse.json({ ...substrate, ...overrides })),
    http.get('/api/v1/substrates/sub-1/batches', () => HttpResponse.json(batches)),
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

describe('SubstrateDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // jsdom provides a read-only localStorage stub whose setItem throws; the
    // favorites hook writes to it, so back it with an in-memory Map.
    const store = new Map<string, string>();
    vi.stubGlobal('localStorage', {
      getItem: (k: string) => store.get(k) ?? null,
      setItem: (k: string, v: string) => store.set(k, v),
      removeItem: (k: string) => store.delete(k),
      clear: () => store.clear(),
      key: () => null,
      length: 0,
    });
    i18n.changeLanguage('de');
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    i18n.changeLanguage('en');
  });

  it('renders the substrate detail page with its batch list', async () => {
    useSubstrate();
    renderWithProviders(<SubstrateDetailPage />);

    expect(await screen.findByTestId('substrate-detail-page')).toBeTruthy();
    expect(screen.getAllByText('B-001').length).toBeGreaterThan(0);
    // DE title uses name_de.
    expect(screen.getAllByText('Kokos Substrat').length).toBeGreaterThan(0);
  });

  it('shows the English name when the UI language is English', async () => {
    i18n.changeLanguage('en');
    useSubstrate();
    renderWithProviders(<SubstrateDetailPage />);

    await screen.findByTestId('substrate-detail-page');
    expect(screen.getAllByText('Coco Substrate').length).toBeGreaterThan(0);
  });

  it('renders the error display when the substrate cannot be loaded', async () => {
    server.use(http.get('/api/v1/substrates/sub-1', () => errorEnvelope(500)));
    renderWithProviders(<SubstrateDetailPage />);

    expect(await screen.findByTestId('error-retry-button')).toBeTruthy();
    expect(screen.queryByTestId('substrate-detail-page')).toBeNull();
  });

  it('renders the mix-component chips for a mixed substrate', async () => {
    useSubstrate({
      is_mix: true,
      mix_components: [
        { substrate_key: 'sub-2', fraction: 0.5 },
        // A component whose substrate is not in the resolved list falls back to
        // showing the raw key.
        { substrate_key: 'sub-unknown', fraction: 0.5 },
      ],
    } as never);
    server.use(
      http.get('/api/v1/substrates', () =>
        HttpResponse.json([
          { ...substrate, key: 'sub-2', name_de: 'Perlit', name_en: 'Perlite', type: 'perlite' },
        ]),
      ),
    );
    renderWithProviders(<SubstrateDetailPage />);

    await screen.findByTestId('substrate-detail-page');
    // The resolved component uses its DE name; the unresolved one shows its key.
    expect(await screen.findByText('Perlit: 50%')).toBeTruthy();
    expect(screen.getByText('sub-unknown: 50%')).toBeTruthy();
  });

  it('falls back to a type/brand label when the substrate has no name', async () => {
    // name_de/name_en null exercises the reset `?? ''` and the title `|| fallback`.
    useSubstrate({ name_de: null, name_en: null } as never);
    const user = userEvent.setup();
    renderWithProviders(<SubstrateDetailPage />);

    await screen.findByTestId('substrate-detail-page');
    // Title falls back to "<type label> <brand>".
    const fallback = `${i18n.t('enums.substrateType.coco')} CocoBrand`;
    expect(screen.getAllByText(fallback).length).toBeGreaterThan(0);

    // The delete confirmation message reuses the same fallback expression.
    await user.click(screen.getByRole('button', { name: i18n.t('common.delete') }));
    expect(await screen.findByTestId('confirm-dialog')).toBeTruthy();
  });

  it('saves the edited substrate and notifies success', async () => {
    useSubstrate();
    let putBody: Record<string, unknown> | null = null;
    server.use(
      http.put('/api/v1/substrates/sub-1', async ({ request }) => {
        putBody = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({ ...substrate, ...putBody });
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<SubstrateDetailPage />);

    await screen.findByTestId('substrate-detail-page');
    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => expect(putBody).not.toBeNull());
    expect(putBody!.type).toBe('coco');
    expect(putBody!.name_de).toBe('Kokos Substrat');
  });

  it('surfaces an API error when saving the substrate fails', async () => {
    useSubstrate();
    server.use(http.put('/api/v1/substrates/sub-1', () => errorEnvelope(500)));
    const user = userEvent.setup();
    renderWithProviders(<SubstrateDetailPage />);

    await screen.findByTestId('substrate-detail-page');
    await user.click(screen.getByTestId('form-submit-button'));

    expect(await screen.findByText(i18n.t('errors.server'))).toBeTruthy();
  });

  it('navigates back when cancelling the form', async () => {
    useSubstrate();
    const user = userEvent.setup();
    renderWithProviders(<SubstrateDetailPage />);

    await screen.findByTestId('substrate-detail-page');
    await user.click(screen.getByTestId('form-cancel-button'));
    expect(mockNavigate).toHaveBeenCalledWith(-1);
  });

  it('toggles the favorite marker', async () => {
    useSubstrate();
    const user = userEvent.setup();
    renderWithProviders(<SubstrateDetailPage />);

    await screen.findByTestId('substrate-detail-page');
    const favButton = screen.getByTestId('StarBorderIcon').closest('button')!;
    await user.click(favButton);
    // After toggling on, the filled star is rendered.
    expect(await screen.findByTestId('StarIcon')).toBeTruthy();
  });

  it('checks batch reusability and shows a success banner', async () => {
    useSubstrate();
    server.use(
      http.post('/api/v1/substrates/batches/batch-1/check-reusability', () =>
        HttpResponse.json({ can_reuse: true, treatments: [] }),
      ),
    );
    const user = userEvent.setup();
    renderWithProviders(<SubstrateDetailPage />);

    await screen.findByTestId('substrate-detail-page');
    await user.click(screen.getByRole('button', { name: i18n.t('pages.substrates.checkReusability') }));

    expect(
      await screen.findByText(i18n.t('pages.substrates.reusabilityOk', { batch: 'batch-1' })),
    ).toBeTruthy();
  });

  it('checks batch reusability and shows a warning banner with required treatments', async () => {
    useSubstrate();
    server.use(
      http.post('/api/v1/substrates/batches/batch-1/check-reusability', () =>
        HttpResponse.json({ can_reuse: false, treatments: ['sterilize', 'ph_flush'] }),
      ),
    );
    const user = userEvent.setup();
    renderWithProviders(<SubstrateDetailPage />);

    await screen.findByTestId('substrate-detail-page');
    await user.click(screen.getByRole('button', { name: i18n.t('pages.substrates.checkReusability') }));

    expect(
      await screen.findByText(
        i18n.t('pages.substrates.reusabilityRequired', {
          batch: 'batch-1',
          treatments: 'sterilize, ph_flush',
        }),
      ),
    ).toBeTruthy();
  });

  it('surfaces an API error when the reusability check fails', async () => {
    useSubstrate();
    server.use(
      http.post('/api/v1/substrates/batches/batch-1/check-reusability', () => errorEnvelope(500)),
    );
    const user = userEvent.setup();
    renderWithProviders(<SubstrateDetailPage />);

    await screen.findByTestId('substrate-detail-page');
    await user.click(screen.getByRole('button', { name: i18n.t('pages.substrates.checkReusability') }));

    expect(await screen.findByText(i18n.t('errors.server'))).toBeTruthy();
  });

  it('opens the batch-create dialog from the create button', async () => {
    useSubstrate();
    const user = userEvent.setup();
    renderWithProviders(<SubstrateDetailPage />);

    await screen.findByTestId('substrate-detail-page');
    await user.click(screen.getByRole('button', { name: i18n.t('pages.batches.create') }));
    // Opening the dialog surfaces at least one further "create" affordance in a dialog.
    expect(await screen.findByRole('dialog')).toBeTruthy();
  });

  it('navigates to a batch detail page on row click', async () => {
    useSubstrate();
    const user = userEvent.setup();
    renderWithProviders(<SubstrateDetailPage />);

    await screen.findByTestId('substrate-detail-page');
    const batchRow = screen.getAllByText('B-001')[0].closest('tr')!;
    await user.click(within(batchRow).getByText('B-001'));
    expect(mockNavigate).toHaveBeenCalledWith('/standorte/substrates/batches/batch-1');
  });

  it('renders the batch list as mobile cards on a small screen', async () => {
    // Force every media query to match so DataTable switches to its card layout,
    // exercising the batch mobileCardRenderer.
    vi.stubGlobal('matchMedia', (query: string) => ({
      matches: true,
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    }));
    useSubstrate();
    renderWithProviders(<SubstrateDetailPage />);

    await screen.findByTestId('substrate-detail-page');
    // The card renders the batch id as its title and volume as a field.
    expect(await screen.findAllByText('B-001')).toBeTruthy();
    expect(screen.getAllByText('20 L').length).toBeGreaterThan(0);
  });

  it('filters the batch table via the search field', async () => {
    useSubstrate({}, [
      batch,
      { ...batch, key: 'batch-2', batch_id: 'B-002', volume_liters: 99 },
    ]);
    const user = userEvent.setup();
    renderWithProviders(<SubstrateDetailPage />);

    await screen.findByTestId('substrate-detail-page');
    await screen.findAllByText('B-001');
    const searchInput = within(screen.getByTestId('table-search-input')).getByRole('textbox');
    await user.type(searchInput, '99');

    // Searching by the volume searchValue keeps only the matching batch.
    await waitFor(() => expect(screen.queryByText('B-001')).toBeNull());
    expect(screen.getAllByText('B-002').length).toBeGreaterThan(0);
  });

  it('deletes the substrate through the confirm dialog and navigates to the list', async () => {
    useSubstrate();
    server.use(
      http.delete('/api/v1/substrates/sub-1', () => new HttpResponse(null, { status: 204 })),
    );
    const user = userEvent.setup();
    renderWithProviders(<SubstrateDetailPage />);

    await screen.findByTestId('substrate-detail-page');
    await user.click(screen.getByRole('button', { name: i18n.t('common.delete') }));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    await waitFor(() =>
      expect(mockNavigate).toHaveBeenCalledWith('/standorte/substrates'),
    );
  });

  it('shows the pending state on the delete dialog while deleting', async () => {
    useSubstrate();
    server.use(
      http.delete('/api/v1/substrates/sub-1', async () => {
        await delay(60);
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<SubstrateDetailPage />);

    await screen.findByTestId('substrate-detail-page');
    await user.click(screen.getByRole('button', { name: i18n.t('common.delete') }));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    await waitFor(() =>
      expect(screen.getByTestId('confirm-dialog-confirm')).toBeDisabled(),
    );
    await waitFor(() =>
      expect(mockNavigate).toHaveBeenCalledWith('/standorte/substrates'),
    );
  });

  it('surfaces an error when the substrate deletion fails', async () => {
    useSubstrate();
    server.use(http.delete('/api/v1/substrates/sub-1', () => errorEnvelope(500)));
    const user = userEvent.setup();
    renderWithProviders(<SubstrateDetailPage />);

    await screen.findByTestId('substrate-detail-page');
    await user.click(screen.getByRole('button', { name: i18n.t('common.delete') }));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    expect(await screen.findByText(i18n.t('errors.server'))).toBeTruthy();
    expect(mockNavigate).not.toHaveBeenCalledWith('/standorte/substrates');
  });

  it('deletes a batch through its confirm dialog and refetches', async () => {
    useSubstrate();
    let deleteCalled = false;
    server.use(
      http.delete('/api/v1/substrates/batches/batch-1', () => {
        deleteCalled = true;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<SubstrateDetailPage />);

    await screen.findByTestId('substrate-detail-page');
    await screen.findAllByText('B-001');

    const batchRow = screen.getAllByText('B-001')[0].closest('tr')!;
    const deleteButton = within(batchRow).getByTestId('DeleteIcon').closest('button')!;
    await user.click(deleteButton);

    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    await waitFor(() => expect(deleteCalled).toBe(true));
    await waitFor(() =>
      expect(screen.queryByTestId('confirm-dialog')).toBeNull(),
    );
  });

  it('surfaces an error when a batch deletion fails', async () => {
    useSubstrate();
    server.use(
      http.delete('/api/v1/substrates/batches/batch-1', () => errorEnvelope(500)),
    );
    const user = userEvent.setup();
    renderWithProviders(<SubstrateDetailPage />);

    await screen.findByTestId('substrate-detail-page');
    await screen.findAllByText('B-001');

    const batchRow = screen.getAllByText('B-001')[0].closest('tr')!;
    await user.click(within(batchRow).getByTestId('DeleteIcon').closest('button')!);
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    expect(await screen.findByText(i18n.t('errors.server'))).toBeTruthy();
  });
});
