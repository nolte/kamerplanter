import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterAll, vi } from 'vitest';
import i18n from 'i18next';
import type { NutrientPlan } from '@/api/types';

const navigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ key: 'np-1' }),
    useNavigate: () => navigate,
  };
});

const fetchNutrientPlan = vi.fn();
const fetchPhaseEntries = vi.fn();
const validateNutrientPlan = vi.fn();
const deleteNutrientPlan = vi.fn();
const updateNutrientPlan = vi.fn();
vi.mock('@/api/endpoints/nutrient-plans', () => ({
  fetchNutrientPlan: (...args: unknown[]) => fetchNutrientPlan(...args),
  fetchPhaseEntries: (...args: unknown[]) => fetchPhaseEntries(...args),
  validateNutrientPlan: (...args: unknown[]) => validateNutrientPlan(...args),
  deleteNutrientPlan: (...args: unknown[]) => deleteNutrientPlan(...args),
  updateNutrientPlan: (...args: unknown[]) => updateNutrientPlan(...args),
}));

const fetchFertilizers = vi.fn();
vi.mock('@/api/endpoints/fertilizers', () => ({
  fetchFertilizers: (...args: unknown[]) => fetchFertilizers(...args),
}));

const downloadNutrientPlanPdf = vi.fn();
vi.mock('@/api/endpoints/print', () => ({
  downloadNutrientPlanPdf: (...args: unknown[]) => downloadNutrientPlanPdf(...args),
}));

import NutrientPlanDetailPage from '@/pages/duengung/NutrientPlanDetailPage';
import { renderWithProviders } from '../helpers';

// jsdom ships no writable localStorage; back the favorites hook with a Map.
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

function makePlan(overrides: Partial<NutrientPlan> = {}): NutrientPlan {
  return {
    key: 'np-1',
    name: 'Veg Plan',
    description: '',
    recommended_substrate_type: null,
    reference_substrate_type: 'soil',
    author: '',
    is_template: false,
    version: '1.0',
    tags: [],
    cloned_from_key: null,
    watering_schedule: null,
    water_mix_ratio_ro_percent: null,
    cycle_restart_from_sequence: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
    ...overrides,
  } as NutrientPlan;
}

describe('NutrientPlanDetailPage', () => {
  beforeEach(() => {
    installLocalStorage();
    i18n.changeLanguage('de');
    navigate.mockReset();
    fetchNutrientPlan.mockReset().mockResolvedValue(makePlan());
    fetchPhaseEntries.mockReset().mockResolvedValue([]);
    validateNutrientPlan.mockReset().mockResolvedValue({ valid: true, issues: [] });
    deleteNutrientPlan.mockReset().mockResolvedValue(undefined);
    updateNutrientPlan.mockReset().mockResolvedValue(makePlan());
    fetchFertilizers.mockReset().mockResolvedValue([]);
    downloadNutrientPlanPdf.mockReset().mockResolvedValue(new Blob(['x']));
  });

  afterAll(() => {
    i18n.changeLanguage('en');
  });

  it('renders the loaded nutrient plan', async () => {
    renderWithProviders(<NutrientPlanDetailPage />);
    expect(await screen.findByTestId('nutrient-plan-detail-page')).toBeInTheDocument();
    expect(screen.getByText('Veg Plan')).toBeInTheDocument();
  });

  it('shows the error state when the plan fails to load', async () => {
    fetchNutrientPlan.mockRejectedValueOnce(new Error('load boom'));
    renderWithProviders(<NutrientPlanDetailPage />);
    expect(await screen.findByTestId('error-display')).toBeInTheDocument();
  });

  it('renders the template and cycle-restart chips', async () => {
    fetchNutrientPlan.mockResolvedValue(
      makePlan({ is_template: true, cycle_restart_from_sequence: 3 }),
    );
    renderWithProviders(<NutrientPlanDetailPage />);
    await screen.findByTestId('nutrient-plan-detail-page');

    expect(screen.getByText(i18n.t('pages.nutrientPlans.isTemplate'))).toBeInTheDocument();
    expect(
      screen.getByText(`${i18n.t('pages.nutrientPlans.cycleRestartFromSequence')}: #3`),
    ).toBeInTheDocument();
  });

  it('offers copy-as-template, a read-only banner and hides delete for system plans', async () => {
    fetchNutrientPlan.mockResolvedValue(makePlan({ origin: 'system' } as Partial<NutrientPlan>));
    renderWithProviders(<NutrientPlanDetailPage />);
    await screen.findByTestId('nutrient-plan-detail-page');

    expect(screen.getByTestId('nutrient-plan-readonly-banner')).toBeInTheDocument();
    expect(screen.getByTestId('copy-as-template-button')).toBeInTheDocument();
    expect(screen.queryByTestId('delete-nutrient-plan-button')).toBeNull();
  });

  it('toggles favorite, prints the plan and switches tabs', async () => {
    const user = userEvent.setup();
    renderWithProviders(<NutrientPlanDetailPage />);
    await screen.findByTestId('nutrient-plan-detail-page');

    await user.click(screen.getByRole('button', { name: i18n.t('pages.nutrientPlans.favToggle') }));
    await user.click(screen.getByTestId('print-button'));
    await waitFor(() => expect(downloadNutrientPlanPdf).toHaveBeenCalledWith('np-1'));

    // clicking the validation tab fires the tab-change handler
    await user.click(screen.getByRole('tab', { name: i18n.t('pages.nutrientPlans.tabValidation') }));
    expect(screen.getByTestId('nutrient-plan-detail-page')).toBeInTheDocument();
  });

  it('deletes the plan through the confirm dialog and navigates back to the list', async () => {
    const user = userEvent.setup();
    renderWithProviders(<NutrientPlanDetailPage />);

    await user.click(await screen.findByTestId('delete-nutrient-plan-button'));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    await waitFor(() => expect(deleteNutrientPlan).toHaveBeenCalledWith('np-1'));
    expect(navigate).toHaveBeenCalledWith('/duengung/plans');
  });

  it('shows the pending state on the confirm dialog while deleting', async () => {
    let resolveDelete!: () => void;
    deleteNutrientPlan.mockReturnValue(
      new Promise<void>((res) => {
        resolveDelete = () => res();
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<NutrientPlanDetailPage />);

    await user.click(await screen.findByTestId('delete-nutrient-plan-button'));
    const confirm = await screen.findByTestId('confirm-dialog-confirm');
    await user.click(confirm);

    await waitFor(() => expect(confirm).toBeDisabled());
    expect(screen.getByTestId('confirm-dialog-live-region')).toHaveTextContent(
      i18n.t('common.processing'),
    );
    resolveDelete();
    await waitFor(() => expect(navigate).toHaveBeenCalledWith('/duengung/plans'));
  });

  it('does not navigate when the delete request fails', async () => {
    deleteNutrientPlan.mockRejectedValue(new Error('boom'));
    const user = userEvent.setup();
    renderWithProviders(<NutrientPlanDetailPage />);

    await user.click(await screen.findByTestId('delete-nutrient-plan-button'));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    await waitFor(() => expect(deleteNutrientPlan).toHaveBeenCalledWith('np-1'));
    expect(navigate).not.toHaveBeenCalled();
  });

  it('cancels the delete confirmation without calling the API', async () => {
    const user = userEvent.setup();
    renderWithProviders(<NutrientPlanDetailPage />);

    await user.click(await screen.findByTestId('delete-nutrient-plan-button'));
    await user.click(await screen.findByTestId('confirm-dialog-cancel'));

    await waitFor(() => expect(screen.queryByTestId('confirm-dialog')).toBeNull());
    expect(deleteNutrientPlan).not.toHaveBeenCalled();
  });
});
