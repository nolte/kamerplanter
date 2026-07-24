import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import i18n from 'i18next';
import type { Cultivar, GrowthPhase, Species } from '@/api/types';

const navigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ speciesKey: 'sp-1', cultivarKey: 'cv-1' }),
    useNavigate: () => navigate,
  };
});

const getCultivar = vi.fn();
const getSpecies = vi.fn();
const updateCultivar = vi.fn();
const deleteCultivar = vi.fn();
vi.mock('@/api/endpoints/species', () => ({
  getCultivar: (...args: unknown[]) => getCultivar(...args),
  getSpecies: (...args: unknown[]) => getSpecies(...args),
  updateCultivar: (...args: unknown[]) => updateCultivar(...args),
  deleteCultivar: (...args: unknown[]) => deleteCultivar(...args),
}));

const getLifecycleConfig = vi.fn();
const listGrowthPhases = vi.fn();
vi.mock('@/api/endpoints/phases', () => ({
  getLifecycleConfig: (...args: unknown[]) => getLifecycleConfig(...args),
  listGrowthPhases: (...args: unknown[]) => listGrowthPhases(...args),
}));

import CultivarDetailPage from '@/pages/stammdaten/CultivarDetailPage';
import { createStoreWithExpertise, renderWithProviders } from '../helpers';

function makeCultivar(overrides: Partial<Cultivar> = {}): Cultivar {
  return {
    key: 'cv-1',
    name: 'Gala',
    species_key: 'sp-1',
    breeder: null,
    breeding_year: null,
    traits: [],
    patent_status: '',
    seed_type: null,
    days_to_maturity: 150,
    dtm_reference: null,
    bearing_start_year_min: null,
    bearing_start_year_max: null,
    disease_resistances: [],
    phase_watering_overrides: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
    ...overrides,
  };
}

function makeSpecies(): Species {
  return {
    key: 'sp-1',
    scientific_name: 'Malus domestica',
    common_names: [],
    family_key: null,
    family_name: null,
    genus: 'Malus',
    hardiness_zones: [],
    native_habitat: '',
    growth_habit: 'tree',
    root_type: 'fibrous',
    allelopathy_score: 0,
    base_temp: 10,
    synonyms: [],
    taxonomic_authority: '',
    taxonomic_status: '',
    description: '',
    sowing_indoor_weeks_before_last_frost: null,
    sowing_outdoor_after_last_frost_days: null,
    direct_sow_months: [],
    harvest_months: [],
    bloom_months: [],
    harvest_from_year: null,
    bloom_from_year: null,
    frost_sensitivity: null,
    plant_category: null,
    harvest_pattern: null,
    harvested_part: null,
    climacteric: null,
    propagation_configs: [],
    allows_harvest: true,
    growing_periods: [],
    container_suitable: null,
    recommended_container_volume_l: null,
    min_container_depth_cm: null,
    mature_height_cm: null,
    mature_width_cm: null,
    spacing_cm: null,
    indoor_suitable: null,
    balcony_suitable: null,
    greenhouse_recommended: false,
    support_required: false,
    watering_guide: null,
    default_nutrient_plan_key: null,
    representative_image_url: null,
    representative_image_attribution: null,
    representative_image_license: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
  };
}

function makePhase(overrides: Partial<GrowthPhase> = {}): GrowthPhase {
  return {
    key: 'gp-1',
    name: 'vegetative',
    display_name: 'Vegetativ',
    description: '',
    lifecycle_key: 'lc-1',
    typical_duration_days: 30,
    sequence_order: 1,
    is_terminal: false,
    allows_harvest: false,
    stress_tolerance: 'medium',
    watering_interval_days: 4,
    created_at: null,
    updated_at: null,
    ...overrides,
  };
}

describe('CultivarDetailPage — actions', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    navigate.mockReset();
    getCultivar.mockReset().mockResolvedValue(makeCultivar());
    getSpecies.mockReset().mockResolvedValue(makeSpecies());
    updateCultivar.mockReset().mockResolvedValue(makeCultivar());
    deleteCultivar.mockReset().mockResolvedValue(undefined);
    getLifecycleConfig.mockReset().mockRejectedValue(new Error('no lifecycle'));
    listGrowthPhases.mockReset().mockResolvedValue([]);
  });

  it('submits the main form and calls updateCultivar', async () => {
    const user = userEvent.setup();
    renderWithProviders(<CultivarDetailPage />, { store: createStoreWithExpertise('expert') });

    await screen.findByTestId('form-field-name');
    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => expect(updateCultivar).toHaveBeenCalledOnce());
    expect(updateCultivar).toHaveBeenCalledWith('sp-1', 'cv-1', expect.objectContaining({ name: 'Gala' }));
  });

  it('submits the selected seed_type value', async () => {
    getCultivar.mockResolvedValue(makeCultivar({ seed_type: null }));
    const user = userEvent.setup();
    renderWithProviders(<CultivarDetailPage />, { store: createStoreWithExpertise('intermediate') });

    const seedType = await screen.findByTestId('form-field-seed_type');
    await user.click(within(seedType).getByRole('combobox'));
    await user.click(await screen.findByRole('option', { name: i18n.t('enums.seedType.f1_hybrid') }));
    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => expect(updateCultivar).toHaveBeenCalledOnce());
    expect(updateCultivar).toHaveBeenCalledWith(
      'sp-1',
      'cv-1',
      expect.objectContaining({ seed_type: 'f1_hybrid' }),
    );
  });

  it('normalises an empty seed_type selection to null on submit', async () => {
    getCultivar.mockResolvedValue(makeCultivar({ seed_type: 'f1_hybrid' }));
    const user = userEvent.setup();
    renderWithProviders(<CultivarDetailPage />, { store: createStoreWithExpertise('intermediate') });

    const seedType = await screen.findByTestId('form-field-seed_type');
    await user.click(within(seedType).getByRole('combobox'));
    // The empty "—" option clears the selection.
    await user.click(await screen.findByRole('option', { name: '—' }));
    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => expect(updateCultivar).toHaveBeenCalledOnce());
    expect(updateCultivar).toHaveBeenCalledWith(
      'sp-1',
      'cv-1',
      expect.objectContaining({ seed_type: null }),
    );
  });

  it('renders the phase-watering overrides table and persists an edited override', async () => {
    getLifecycleConfig.mockResolvedValue({ key: 'lc-1' });
    listGrowthPhases.mockResolvedValue([
      makePhase({ key: 'gp-1', name: 'vegetative', display_name: 'Vegetativ', watering_interval_days: 4 }),
      // second phase: no display_name (name fallback) and no default interval ('—').
      makePhase({ key: 'gp-2', name: 'flowering', display_name: '', watering_interval_days: null }),
    ]);
    getCultivar.mockResolvedValue(makeCultivar({ phase_watering_overrides: { vegetative: 6 } }));

    const user = userEvent.setup();
    renderWithProviders(<CultivarDetailPage />, { store: createStoreWithExpertise('expert') });

    const vegInput = await screen.findByTestId('phase-override-vegetative');
    // Pre-seeded override from the cultivar.
    expect(within(vegInput).getByDisplayValue('6')).toBeInTheDocument();
    // Name fallback row for the phase without a display_name.
    expect(screen.getByTestId('phase-override-flowering')).toBeInTheDocument();

    const flowInput = within(screen.getByTestId('phase-override-flowering')).getByRole('spinbutton');
    await user.type(flowInput, '8');

    // The save button lives in the overrides Paper, after the form actions.
    const saveButtons = screen.getAllByRole('button', { name: i18n.t('common.save') });
    await user.click(saveButtons[saveButtons.length - 1]);

    await waitFor(() => expect(updateCultivar).toHaveBeenCalled());
    expect(updateCultivar).toHaveBeenLastCalledWith(
      'sp-1',
      'cv-1',
      expect.objectContaining({
        phase_watering_overrides: expect.objectContaining({ vegetative: 6, flowering: 8 }),
      }),
    );
  });

  it('persists null overrides when every value is cleared', async () => {
    getLifecycleConfig.mockResolvedValue({ key: 'lc-1' });
    listGrowthPhases.mockResolvedValue([makePhase({ key: 'gp-1', name: 'vegetative' })]);
    getCultivar.mockResolvedValue(makeCultivar({ phase_watering_overrides: { vegetative: 6 } }));

    const user = userEvent.setup();
    renderWithProviders(<CultivarDetailPage />, { store: createStoreWithExpertise('expert') });

    const vegInput = within(await screen.findByTestId('phase-override-vegetative')).getByRole('spinbutton');
    await user.clear(vegInput);

    const saveButtons = screen.getAllByRole('button', { name: i18n.t('common.save') });
    await user.click(saveButtons[saveButtons.length - 1]);

    await waitFor(() => expect(updateCultivar).toHaveBeenCalled());
    expect(updateCultivar).toHaveBeenLastCalledWith(
      'sp-1',
      'cv-1',
      expect.objectContaining({ phase_watering_overrides: null }),
    );
  });

  it('deletes the cultivar through the confirm dialog and navigates back to the species', async () => {
    const user = userEvent.setup();
    renderWithProviders(<CultivarDetailPage />, { store: createStoreWithExpertise('expert') });

    await screen.findByTestId('form-field-name');
    await user.click(screen.getByRole('button', { name: i18n.t('common.delete') }));

    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    await waitFor(() => expect(deleteCultivar).toHaveBeenCalledWith('sp-1', 'cv-1'));
    expect(navigate).toHaveBeenCalledWith('/stammdaten/species/sp-1');
  });

  it('shows an error display when loading the cultivar fails', async () => {
    getCultivar.mockRejectedValue(new Error('boom'));
    renderWithProviders(<CultivarDetailPage />, { store: createStoreWithExpertise('expert') });

    expect(await screen.findByText(i18n.t('common.retry'))).toBeInTheDocument();
    expect(screen.queryByTestId('form-field-name')).toBeNull();
  });

  it('renders read-only enrichment data without form actions', async () => {
    getCultivar.mockResolvedValue(
      makeCultivar({ ...({ origin: 'enrichment' } as Partial<Cultivar>) }),
    );
    renderWithProviders(<CultivarDetailPage />, { store: createStoreWithExpertise('expert') });

    await screen.findByTestId('form-field-name');
    expect(screen.getByText(i18n.t('common.origin.readOnlyHint'))).toBeInTheDocument();
    expect(screen.queryByTestId('form-submit-button')).toBeNull();
    // enrichment is read-only but not deletion-protected → delete stays available.
    expect(screen.getByRole('button', { name: i18n.t('common.delete') })).toBeInTheDocument();
  });

  it('hides the delete action for deletion-protected system data', async () => {
    getCultivar.mockResolvedValue(makeCultivar({ ...({ origin: 'system' } as Partial<Cultivar>) }));
    renderWithProviders(<CultivarDetailPage />, { store: createStoreWithExpertise('expert') });

    await screen.findByTestId('form-field-name');
    expect(screen.queryByRole('button', { name: i18n.t('common.delete') })).toBeNull();
  });
});
