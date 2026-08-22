import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterAll, vi } from 'vitest';
import i18n from 'i18next';
import type { Fertilizer, FertilizerStock, Incompatibility, NutrientPlanUsage } from '@/api/types';

const navigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ key: 'fert-1' }),
    useNavigate: () => navigate,
  };
});

const fetchFertilizer = vi.fn();
const fetchFertilizerStocks = vi.fn();
const fetchNutrientPlanUsage = vi.fn();
const fetchIncompatibilities = vi.fn();
const deleteFertilizer = vi.fn();
const updateFertilizer = vi.fn();
const createFertilizerStock = vi.fn();
vi.mock('@/api/endpoints/fertilizers', () => ({
  fetchFertilizer: (...args: unknown[]) => fetchFertilizer(...args),
  fetchFertilizerStocks: (...args: unknown[]) => fetchFertilizerStocks(...args),
  fetchNutrientPlanUsage: (...args: unknown[]) => fetchNutrientPlanUsage(...args),
  fetchIncompatibilities: (...args: unknown[]) => fetchIncompatibilities(...args),
  deleteFertilizer: (...args: unknown[]) => deleteFertilizer(...args),
  updateFertilizer: (...args: unknown[]) => updateFertilizer(...args),
  createFertilizerStock: (...args: unknown[]) => createFertilizerStock(...args),
}));

import FertilizerDetailPage from '@/pages/duengung/FertilizerDetailPage';
import { renderWithProviders } from '../helpers';
import * as favoritesApi from '@/api/endpoints/favorites';

// Fertilizer favorites became server-backed in #1233. Without this mock the
// optimistic toggle posts against the real client, fails, and reverts — the
// marker flips back and the assertion below reads as a component defect.
vi.mock('@/api/endpoints/favorites');

// jsdom in this project ships no writable localStorage; back it with a Map so
// other storage users do not throw.
function installLocalStorage() {
  const store = new Map<string, string>();
  Object.defineProperty(globalThis, 'localStorage', {
    configurable: true,
    value: {
      getItem: (k: string) => (store.has(k) ? store.get(k)! : null),
      setItem: (k: string, v: string) => void store.set(k, String(v)),
      removeItem: (k: string) => void store.delete(k),
      clear: () => store.clear(),
    },
  });
}

function makeFertilizer(overrides: Partial<Fertilizer> = {}): Fertilizer {
  return {
    key: 'fert-1',
    product_name: 'Base A',
    brand: 'GrowCo',
    fertilizer_type: 'base',
    is_organic: false,
    tank_safe: true,
    recommended_application: 'fertigation',
    npk_ratio: [3, 1, 2],
    ec_contribution_per_ml: 0.4,
    ec_contribution_uncertain: false,
    max_dose_ml_per_liter: 5,
    mixing_priority: 3,
    ph_effect: 'neutral',
    bioavailability: 'immediate',
    shelf_life_days: null,
    storage_temp_min: null,
    storage_temp_max: null,
    application_rate_g_per_m2: null,
    application_rate_l_per_m2: null,
    dilution_ratio: null,
    nutrient_release_speed: null,
    notes: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
    ...overrides,
  } as Fertilizer;
}

/** A stock row expiring within the 30-day warning window. */
function soonExpiryDate(): string {
  const d = new Date(Date.now() + 10 * 24 * 60 * 60 * 1000);
  return d.toISOString().split('T')[0];
}

function makeStock(overrides: Partial<FertilizerStock> = {}): FertilizerStock {
  return {
    key: 'stock-1',
    fertilizer_key: 'fert-1',
    current_volume_ml: 1500,
    purchase_date: '2024-02-01',
    expiry_date: soonExpiryDate(),
    batch_number: 'B-42',
    cost_per_liter: 12.5,
    created_at: '2024-02-01T00:00:00Z',
    updated_at: null,
    ...overrides,
  };
}

describe('FertilizerDetailPage', () => {
  beforeEach(() => {
    installLocalStorage();
    // The auto-mock returns `undefined`, not a promise, so the favorites hook's
    // effect would throw on `.then` and the page would never render — a failure
    // that reads as a component defect rather than a missing stub.
    vi.mocked(favoritesApi.listFavorites).mockResolvedValue([]);
    vi.mocked(favoritesApi.addFavorite).mockResolvedValue({} as never);
    vi.mocked(favoritesApi.removeFavorite).mockResolvedValue(undefined);
    i18n.changeLanguage('de');
    navigate.mockReset();
    fetchFertilizer.mockReset().mockResolvedValue(makeFertilizer());
    fetchFertilizerStocks.mockReset().mockResolvedValue([]);
    fetchNutrientPlanUsage.mockReset().mockResolvedValue([]);
    fetchIncompatibilities.mockReset().mockResolvedValue([]);
    deleteFertilizer.mockReset().mockResolvedValue(undefined);
    updateFertilizer.mockReset().mockResolvedValue(makeFertilizer());
    createFertilizerStock.mockReset().mockResolvedValue(makeStock());
  });

  afterAll(() => {
    i18n.changeLanguage('en');
  });

  it('renders the loaded fertilizer', async () => {
    renderWithProviders(<FertilizerDetailPage />);
    expect(await screen.findByTestId('fertilizer-detail-page')).toBeInTheDocument();
    expect(screen.getByText('Base A')).toBeInTheDocument();
    // NPK hero block
    expect(screen.getByText('N 3%')).toBeInTheDocument();
    expect(screen.getByText('K 2%')).toBeInTheDocument();
  });

  it('shows the loading skeleton before data resolves and the not-found state for a missing fertilizer', async () => {
    // never-resolving load keeps the skeleton mounted
    fetchFertilizer.mockReturnValue(new Promise(() => {}));
    const { unmount } = renderWithProviders(<FertilizerDetailPage />);
    expect(screen.queryByTestId('fertilizer-detail-page')).toBeNull();
    unmount();

    fetchFertilizer.mockRejectedValueOnce(new Error('nope'));
    renderWithProviders(<FertilizerDetailPage />);
    expect(await screen.findByText(/nope|Error/)).toBeInTheDocument();
  });

  it('renders the rich details tab: incompatibilities, storage, area dosing, notes and plan usage', async () => {
    fetchFertilizer.mockResolvedValue(
      makeFertilizer({
        is_organic: true,
        ph_effect: 'acidic',
        ec_contribution_uncertain: true,
        shelf_life_days: 365,
        storage_temp_min: 5,
        storage_temp_max: 25,
        application_rate_g_per_m2: 50,
        application_rate_l_per_m2: 2,
        dilution_ratio: '1:10',
        nutrient_release_speed: 'months',
        notes: 'Handle with care',
        updated_at: '2024-03-01T00:00:00Z',
      }),
    );
    const incompatibilities: Incompatibility[] = [
      { fertilizer_key: 'fert-2', product_name: 'CalMag', reason: 'precipitates', severity: 'critical' },
    ];
    fetchIncompatibilities.mockResolvedValue(incompatibilities);
    const planUsage: NutrientPlanUsage[] = [
      { key: 'np-1', name: 'Veg Plan', phase_entries: [] },
    ];
    fetchNutrientPlanUsage.mockResolvedValue(planUsage);

    renderWithProviders(<FertilizerDetailPage />);

    await screen.findByTestId('fertilizer-detail-page');
    expect(screen.getByText('Handle with care')).toBeInTheDocument();
    expect(screen.getByText('CalMag: precipitates')).toBeInTheDocument();
    // area dosing values
    expect(screen.getByText('50 g/m²')).toBeInTheDocument();
    expect(screen.getByText('1:10')).toBeInTheDocument();
  });

  it('renders alkaline pH, no max-dose and storage-min-only variants', async () => {
    fetchFertilizer.mockResolvedValue(
      makeFertilizer({
        ph_effect: 'alkaline',
        max_dose_ml_per_liter: null,
        storage_temp_min: 8,
        storage_temp_max: null,
        shelf_life_days: 90,
      }),
    );
    renderWithProviders(<FertilizerDetailPage />);
    await screen.findByTestId('fertilizer-detail-page');
    expect(screen.getByText('≥ 8 °C')).toBeInTheDocument();
  });

  it('marks expired and far-future stock rows distinctly', async () => {
    const expired = new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    const farFuture = new Date(Date.now() + 400 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    fetchFertilizerStocks.mockResolvedValue([
      makeStock({ key: 's-exp', batch_number: 'EXP', expiry_date: expired, cost_per_liter: null }),
      makeStock({ key: 's-far', batch_number: 'FAR', expiry_date: farFuture }),
    ]);
    renderWithProviders(<FertilizerDetailPage />, { route: '/#stock' });
    await screen.findByTestId('fertilizer-detail-page');
    expect(screen.getAllByText('EXP').length).toBeGreaterThan(0);
    expect(screen.getAllByText('FAR').length).toBeGreaterThan(0);
  });

  it('shows the empty stock state on the stock tab', async () => {
    renderWithProviders(<FertilizerDetailPage />, { route: '/#stock' });
    await screen.findByTestId('fertilizer-detail-page');
    expect(
      screen.getByText(i18n.t('pages.fertilizers.stockEmptyTitle')),
    ).toBeInTheDocument();
  });

  it('renders the stock summary, expiry warning and table when stocks exist', async () => {
    fetchFertilizerStocks.mockResolvedValue([
      makeStock(),
      makeStock({ key: 'stock-2', batch_number: 'B-99', current_volume_ml: 500, expiry_date: null, cost_per_liter: null }),
    ]);
    renderWithProviders(<FertilizerDetailPage />, { route: '/#stock' });
    await screen.findByTestId('fertilizer-detail-page');

    // summary bar: total volume (2000 ml -> 2.0 L)
    expect(screen.getByText('2.0 L')).toBeInTheDocument();
    // expiry warning present (one stock expires within 30 days)
    expect(
      screen.getByText(
        i18n.t('pages.fertilizers.stockExpiringWarning', { count: 1 }),
      ),
    ).toBeInTheDocument();
    // batch number rendered in table (desktop cell + mobile card = >=1)
    expect(screen.getAllByText('B-42').length).toBeGreaterThan(0);
  });

  it('opens the add-stock dialog and creates a stock entry', async () => {
    fetchFertilizerStocks.mockResolvedValue([makeStock()]);
    const user = userEvent.setup();
    renderWithProviders(<FertilizerDetailPage />, { route: '/#stock' });
    await screen.findByTestId('fertilizer-detail-page');

    await user.click(
      screen.getByRole('button', { name: i18n.t('pages.fertilizers.addStock') }),
    );
    const dialog = await screen.findByRole('dialog');
    await user.click(within(dialog).getByRole('button', { name: i18n.t('common.save') }));

    await waitFor(() => expect(createFertilizerStock).toHaveBeenCalledWith('fert-1', expect.any(Object)));
  });

  it('renders the edit tab and saves updated values', async () => {
    const user = userEvent.setup();
    renderWithProviders(<FertilizerDetailPage />, { route: '/#edit' });
    await screen.findByTestId('fertilizer-detail-page');

    const productName = await screen.findByLabelText(/Produktname|Product name/i);
    await user.clear(productName);
    await user.type(productName, 'Base A Plus');
    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => expect(updateFertilizer).toHaveBeenCalledWith('fert-1', expect.any(Object)));
  });

  it('surfaces an error when saving the edit form fails', async () => {
    updateFertilizer.mockRejectedValue(new Error('save failed'));
    const user = userEvent.setup();
    renderWithProviders(<FertilizerDetailPage />, { route: '/#edit' });
    await screen.findByTestId('fertilizer-detail-page');

    const productName = await screen.findByLabelText(/Produktname|Product name/i);
    await user.clear(productName);
    await user.type(productName, 'X');
    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => expect(updateFertilizer).toHaveBeenCalled());
    // page stays; still shows the edit form
    expect(screen.getByTestId('form-submit-button')).toBeInTheDocument();
  });

  it('toggles the favorite marker', async () => {
    const user = userEvent.setup();
    renderWithProviders(<FertilizerDetailPage />);
    await screen.findByTestId('fertilizer-detail-page');

    const toggle = screen.getByTestId('favorite-toggle');
    await user.click(toggle);
    // after toggling the aria-label flips to "remove favorite"
    expect(
      screen.getByRole('button', { name: i18n.t('common.removeFavorite') }),
    ).toBeInTheDocument();
  });

  it('hides the delete button and shows the read-only banner for system-origin data', async () => {
    fetchFertilizer.mockResolvedValue(makeFertilizer({ origin: 'system' } as Partial<Fertilizer>));
    renderWithProviders(<FertilizerDetailPage />);
    await screen.findByTestId('fertilizer-detail-page');

    expect(screen.getByTestId('fertilizer-readonly-banner')).toBeInTheDocument();
    expect(screen.queryByTestId('delete-button')).toBeNull();
  });

  it('deletes the fertilizer through the confirm dialog and navigates back to the list', async () => {
    const user = userEvent.setup();
    renderWithProviders(<FertilizerDetailPage />);

    await user.click(await screen.findByTestId('delete-button'));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    await waitFor(() => expect(deleteFertilizer).toHaveBeenCalledWith('fert-1'));
    expect(navigate).toHaveBeenCalledWith('/duengung/fertilizers');
  });

  it('shows the pending/loading state on the confirm dialog while the delete is in flight', async () => {
    let resolveDelete!: () => void;
    deleteFertilizer.mockReturnValue(
      new Promise<void>((res) => {
        resolveDelete = () => res();
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<FertilizerDetailPage />);

    await user.click(await screen.findByTestId('delete-button'));
    const confirm = await screen.findByTestId('confirm-dialog-confirm');
    await user.click(confirm);

    await waitFor(() => expect(confirm).toBeDisabled());
    expect(screen.getByTestId('confirm-dialog-live-region')).toHaveTextContent(
      i18n.t('common.processing'),
    );

    resolveDelete();
    await waitFor(() => expect(navigate).toHaveBeenCalledWith('/duengung/fertilizers'));
  });

  it('does not navigate when the delete request fails', async () => {
    deleteFertilizer.mockRejectedValue(new Error('boom'));
    const user = userEvent.setup();
    renderWithProviders(<FertilizerDetailPage />);

    await user.click(await screen.findByTestId('delete-button'));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    await waitFor(() => expect(deleteFertilizer).toHaveBeenCalledWith('fert-1'));
    expect(navigate).not.toHaveBeenCalled();
  });

  it('cancels the delete confirmation without calling the API', async () => {
    const user = userEvent.setup();
    renderWithProviders(<FertilizerDetailPage />);

    await user.click(await screen.findByTestId('delete-button'));
    await user.click(await screen.findByTestId('confirm-dialog-cancel'));

    await waitFor(() => expect(screen.queryByTestId('confirm-dialog')).toBeNull());
    expect(deleteFertilizer).not.toHaveBeenCalled();
  });
});
