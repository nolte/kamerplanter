import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import i18n from 'i18next';
import type { BotanicalFamily, Species } from '@/api/types';

const navigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ key: 'fam-1' }),
    useNavigate: () => navigate,
  };
});

const getBotanicalFamily = vi.fn();
const updateBotanicalFamily = vi.fn();
const deleteBotanicalFamily = vi.fn();
const listSpeciesByFamily = vi.fn();
const listBotanicalFamilies = vi.fn();
vi.mock('@/api/endpoints/botanicalFamilies', () => ({
  getBotanicalFamily: (...args: unknown[]) => getBotanicalFamily(...args),
  updateBotanicalFamily: (...args: unknown[]) => updateBotanicalFamily(...args),
  deleteBotanicalFamily: (...args: unknown[]) => deleteBotanicalFamily(...args),
  listSpeciesByFamily: (...args: unknown[]) => listSpeciesByFamily(...args),
  listBotanicalFamilies: (...args: unknown[]) => listBotanicalFamilies(...args),
}));

import BotanicalFamilyDetailPage from '@/pages/stammdaten/BotanicalFamilyDetailPage';
import { renderWithProviders, createTestStore } from '../helpers';

/**
 * Every render below is an authorised one, and that is load-bearing since #1155.
 *
 * #1120 made the global botanical-family mutations platform-admin-only, and
 * #1155 stopped the UI offering them to anyone else — so an ordinary member sees
 * no delete button and no save action, and the cases here would fail looking for
 * affordances the product is right to withhold. Only `auth.user.is_platform_admin`
 * is read (by `usePlatformAdmin`); the rest of the slice comes from its reducer.
 *
 * The gate itself is covered from both sides in
 * `BotanicalFamilyPlatformAdminGate.test.tsx`. This file is about what an
 * authorised user can do.
 */
function adminStore(overrides: Record<string, unknown> = {}) {
  return createTestStore({
    auth: { user: { is_platform_admin: true }, isAuthenticated: true, isLoading: false },
    ...overrides,
  });
}

function makeFamily(overrides: Partial<BotanicalFamily> = {}): BotanicalFamily {
  return {
    key: 'fam-1',
    name: 'Solanaceae',
    common_name_de: 'Nachtschattengewächse',
    common_name_en: 'Nightshades',
    order: 'Solanales',
    description: 'A family of flowering plants.',
    typical_nutrient_demand: 'heavy',
    nitrogen_fixing: false,
    typical_root_depth: 'medium',
    soil_ph_preference: { min_ph: 6, max_ph: 7 },
    frost_tolerance: 'sensitive',
    typical_growth_forms: ['herb'],
    common_pests: ['aphids'],
    common_diseases: ['blight'],
    pollination_type: ['insect'],
    rotation_category: 'fruit',
    species_count: 0,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
    ...overrides,
  };
}

function makeSpecies(overrides: Partial<Species> = {}): Species {
  return {
    key: 'sp-1',
    scientific_name: 'Solanum lycopersicum',
    common_names: ['Tomato'],
    family_key: 'fam-1',
    genus: 'Solanum',
    hardiness_zones: ['9-11'],
    native_habitat: 'South America',
    growth_habit: 'herb',
    root_type: 'fibrous',
    allelopathy_score: 0.2,
    base_temp: 10,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
    ...overrides,
  } as Species;
}

describe('BotanicalFamilyDetailPage', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    navigate.mockReset();
    getBotanicalFamily.mockReset().mockResolvedValue(makeFamily());
    updateBotanicalFamily.mockReset().mockResolvedValue(makeFamily());
    deleteBotanicalFamily.mockReset().mockResolvedValue(undefined);
    listSpeciesByFamily.mockReset().mockResolvedValue([]);
    listBotanicalFamilies.mockReset().mockResolvedValue([]);
  });

  it('renders the loaded botanical family and its empty-species state', async () => {
    renderWithProviders(<BotanicalFamilyDetailPage />, { store: adminStore() });

    expect(await screen.findByTestId('botanical-family-detail-page')).toBeInTheDocument();
    // Family name is shown in the page title.
    expect(await screen.findByText('Solanaceae')).toBeInTheDocument();
    // No species -> EmptyState is shown.
    expect(
      await screen.findByText(i18n.t('pages.botanicalFamilies.noSpeciesInFamily')),
    ).toBeInTheDocument();
  });

  it('shows the loading skeleton while the family is being fetched', async () => {
    // Keep getBotanicalFamily pending so the slice stays in `loading`.
    getBotanicalFamily.mockReturnValue(new Promise(() => {}));
    const store = adminStore({
      botanicalFamilies: { items: [], current: null, loading: true, error: null },
    });
    renderWithProviders(<BotanicalFamilyDetailPage />, { store });

    expect(await screen.findByTestId('loading-skeleton')).toBeInTheDocument();
  });

  it('shows the error display and retries via navigate when the fetch fails', async () => {
    getBotanicalFamily.mockRejectedValue(new Error('nope'));
    const user = userEvent.setup();
    renderWithProviders(<BotanicalFamilyDetailPage />, { store: adminStore() });

    expect(await screen.findByTestId('error-display')).toBeInTheDocument();
    await user.click(screen.getByTestId('error-retry-button'));
    expect(navigate).toHaveBeenCalledWith(-1);
  });

  it('lists the species belonging to the family and links to the filtered species view', async () => {
    listSpeciesByFamily.mockResolvedValue([
      makeSpecies(),
      makeSpecies({ key: 'sp-2', scientific_name: 'Capsicum annuum', common_names: [] }),
    ]);
    renderWithProviders(<BotanicalFamilyDetailPage />, { store: adminStore() });

    await screen.findByTestId('botanical-family-detail-page');
    expect(await screen.findByText('Solanum lycopersicum')).toBeInTheDocument();
    expect(screen.getByText('Capsicum annuum')).toBeInTheDocument();
    // The filtered "show all" button links to the species list scoped to the family.
    const showAll = screen.getByRole('link', {
      name: i18n.t('pages.botanicalFamilies.showAllSpeciesFiltered'),
    });
    expect(showAll).toHaveAttribute('href', '/stammdaten/species?family=fam-1');
  });

  it('navigates to the filtered species list from the empty-state action', async () => {
    const user = userEvent.setup();
    renderWithProviders(<BotanicalFamilyDetailPage />, { store: adminStore() });

    await screen.findByTestId('botanical-family-detail-page');
    await user.click(
      await screen.findByRole('button', {
        name: i18n.t('pages.botanicalFamilies.showAllSpeciesFiltered'),
      }),
    );
    expect(navigate).toHaveBeenCalledWith('/stammdaten/species?family=fam-1');
  });

  it('tolerates a failing species lookup and still renders the form', async () => {
    listSpeciesByFamily.mockRejectedValue(new Error('boom'));
    renderWithProviders(<BotanicalFamilyDetailPage />, { store: adminStore() });

    expect(await screen.findByTestId('botanical-family-detail-page')).toBeInTheDocument();
    expect(
      await screen.findByText(i18n.t('pages.botanicalFamilies.noSpeciesInFamily')),
    ).toBeInTheDocument();
  });

  it('submits the update with a soil-pH preference derived from both bounds', async () => {
    const user = userEvent.setup();
    renderWithProviders(<BotanicalFamilyDetailPage />, { store: adminStore() });

    await screen.findByText('Solanaceae');
    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => expect(updateBotanicalFamily).toHaveBeenCalledTimes(1));
    const [key, payload] = updateBotanicalFamily.mock.calls[0];
    expect(key).toBe('fam-1');
    expect(payload).toMatchObject({
      name: 'Solanaceae',
      order: 'Solanales',
      soil_ph_preference: { min_ph: 6, max_ph: 7 },
    });
    // Reloads the family after a successful save.
    await waitFor(() => expect(getBotanicalFamily).toHaveBeenCalledTimes(2));
  });

  it('omits soil-pH and order when they are unset', async () => {
    getBotanicalFamily.mockResolvedValue(
      makeFamily({ soil_ph_preference: null, order: null }),
    );
    const user = userEvent.setup();
    renderWithProviders(<BotanicalFamilyDetailPage />, { store: adminStore() });

    await screen.findByText('Solanaceae');
    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => expect(updateBotanicalFamily).toHaveBeenCalledTimes(1));
    const [, payload] = updateBotanicalFamily.mock.calls[0];
    expect(payload.soil_ph_preference).toBeUndefined();
    expect(payload.order).toBeUndefined();
  });

  it('surfaces an error when the update fails', async () => {
    updateBotanicalFamily.mockRejectedValue(new Error('boom'));
    const user = userEvent.setup();
    renderWithProviders(<BotanicalFamilyDetailPage />, { store: adminStore() });

    await screen.findByText('Solanaceae');
    await user.click(screen.getByTestId('form-submit-button'));

    expect(await screen.findByText(i18n.t('errors.unknown'))).toBeInTheDocument();
    expect(navigate).not.toHaveBeenCalled();
  });

  it('navigates back when the cancel action is used', async () => {
    const user = userEvent.setup();
    renderWithProviders(<BotanicalFamilyDetailPage />, { store: adminStore() });

    await screen.findByText('Solanaceae');
    await user.click(screen.getByTestId('form-cancel-button'));
    expect(navigate).toHaveBeenCalledWith(-1);
  });

  it('deletes the family through the confirm dialog and navigates to the list', async () => {
    const user = userEvent.setup();
    renderWithProviders(<BotanicalFamilyDetailPage />, { store: adminStore() });

    await screen.findByTestId('botanical-family-detail-page');
    await user.click(screen.getByRole('button', { name: i18n.t('common.delete') }));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    await waitFor(() => expect(deleteBotanicalFamily).toHaveBeenCalledWith('fam-1'));
    expect(navigate).toHaveBeenCalledWith('/stammdaten/botanical-families');
    await waitFor(() => expect(screen.queryByTestId('confirm-dialog')).toBeNull());
  });

  it('shows the pending state on the confirm button while the delete is in flight', async () => {
    let resolveDelete: (() => void) | undefined;
    deleteBotanicalFamily.mockImplementation(
      () =>
        new Promise<void>((r) => {
          resolveDelete = r;
        }),
    );
    const user = userEvent.setup();
    renderWithProviders(<BotanicalFamilyDetailPage />, { store: adminStore() });

    await screen.findByTestId('botanical-family-detail-page');
    await user.click(screen.getByRole('button', { name: i18n.t('common.delete') }));
    const confirm = await screen.findByTestId('confirm-dialog-confirm');
    await user.click(confirm);

    await waitFor(() => expect(confirm).toBeDisabled());
    expect(screen.getByTestId('confirm-dialog-live-region')).toHaveTextContent(
      i18n.t('common.processing'),
    );

    resolveDelete?.();
    await waitFor(() =>
      expect(navigate).toHaveBeenCalledWith('/stammdaten/botanical-families'),
    );
  });

  it('closes the dialog without navigating when the delete request fails', async () => {
    deleteBotanicalFamily.mockRejectedValue(new Error('boom'));
    const user = userEvent.setup();
    renderWithProviders(<BotanicalFamilyDetailPage />, { store: adminStore() });

    await screen.findByTestId('botanical-family-detail-page');
    await user.click(screen.getByRole('button', { name: i18n.t('common.delete') }));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    await waitFor(() => expect(deleteBotanicalFamily).toHaveBeenCalledWith('fam-1'));
    await waitFor(() => expect(screen.queryByTestId('confirm-dialog')).toBeNull());
    expect(navigate).not.toHaveBeenCalled();
  });

  it('cancels the delete confirmation without deleting', async () => {
    const user = userEvent.setup();
    renderWithProviders(<BotanicalFamilyDetailPage />, { store: adminStore() });

    await screen.findByTestId('botanical-family-detail-page');
    await user.click(screen.getByRole('button', { name: i18n.t('common.delete') }));
    await user.click(await screen.findByTestId('confirm-dialog-cancel'));

    await waitFor(() => expect(screen.queryByTestId('confirm-dialog')).toBeNull());
    expect(deleteBotanicalFamily).not.toHaveBeenCalled();
    expect(navigate).not.toHaveBeenCalled();
  });
});
