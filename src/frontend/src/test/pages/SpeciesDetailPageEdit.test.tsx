import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import i18n from 'i18next';
import type { Species } from '@/api/types';

const navigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useParams: () => ({ key: 'sp-1' }), useNavigate: () => navigate };
});

const updateSpecies = vi.fn();
const deleteSpecies = vi.fn();
const getSpecies = vi.fn();
vi.mock('@/api/endpoints/species', async () => {
  const actual = await vi.importActual<typeof import('@/api/endpoints/species')>(
    '@/api/endpoints/species',
  );
  return {
    ...actual,
    getSpecies: (...a: unknown[]) => getSpecies(...a),
    updateSpecies: (...a: unknown[]) => updateSpecies(...a),
    deleteSpecies: (...a: unknown[]) => deleteSpecies(...a),
    listSpecies: vi.fn().mockResolvedValue({ items: [], total: 0, offset: 0, limit: 200 }),
  };
});

const getCompatibleSpecies = vi.fn();
const getIncompatibleSpecies = vi.fn();
vi.mock('@/api/endpoints/companionPlanting', async () => {
  const actual = await vi.importActual<typeof import('@/api/endpoints/companionPlanting')>(
    '@/api/endpoints/companionPlanting',
  );
  return {
    ...actual,
    getCompatibleSpecies: (...a: unknown[]) => getCompatibleSpecies(...a),
    getIncompatibleSpecies: (...a: unknown[]) => getIncompatibleSpecies(...a),
    setCompatible: vi.fn().mockResolvedValue(undefined),
    setIncompatible: vi.fn().mockResolvedValue(undefined),
  };
});

vi.mock('@/api/endpoints/botanicalFamilies', async () => {
  const actual = await vi.importActual<typeof import('@/api/endpoints/botanicalFamilies')>(
    '@/api/endpoints/botanicalFamilies',
  );
  return {
    ...actual,
    listBotanicalFamilies: vi.fn().mockResolvedValue([]),
    getBotanicalFamily: vi
      .fn()
      .mockResolvedValue({ key: 'fam-1', name: 'Solanaceae', common_name_de: 'Nachtschatten', rotation_category: 'fruchtgemuese' }),
  };
});

vi.mock('@/api/endpoints/phaseSequences', async () => {
  const actual = await vi.importActual<typeof import('@/api/endpoints/phaseSequences')>(
    '@/api/endpoints/phaseSequences',
  );
  return { ...actual, getSpeciesPhaseSequence: vi.fn().mockResolvedValue({ key: 'ps-1' }) };
});

vi.mock('@/api/endpoints/cropRotation', async () => {
  const actual = await vi.importActual<typeof import('@/api/endpoints/cropRotation')>(
    '@/api/endpoints/cropRotation',
  );
  return {
    ...actual,
    getSuccessors: vi
      .fn()
      .mockResolvedValue([{ family_key: 'fam-2', family_name: 'Fabaceae', wait_years: 3 }]),
    setSuccessor: vi.fn().mockResolvedValue(undefined),
  };
});

vi.mock('@/api/endpoints/nutrient-plans', async () => {
  const actual = await vi.importActual<typeof import('@/api/endpoints/nutrient-plans')>(
    '@/api/endpoints/nutrient-plans',
  );
  return { ...actual, fetchNutrientPlans: vi.fn().mockResolvedValue([]) };
});

import SpeciesDetailPage from '@/pages/stammdaten/SpeciesDetailPage';
import { createTestStore, renderWithProviders } from '../helpers';

/** Fully-populated species — every nullable field carries a value so the reset
 *  mapping and the onSubmit `|| null` / `?? default` arms take their truthy path. */
function makeFullSpecies(overrides: Partial<Species> = {}): Species {
  return {
    key: 'sp-1',
    scientific_name: 'Solanum lycopersicum',
    common_names: ['Tomate'],
    family_key: 'fam-1',
    family_name: 'Solanaceae',
    genus: 'Solanum',
    hardiness_zones: ['7a'],
    native_habitat: 'Anden',
    growth_habit: 'herb',
    root_type: 'fibrous',
    allelopathy_score: 1,
    base_temp: 10,
    synonyms: ['Lycopersicon esculentum'],
    taxonomic_authority: 'L.',
    taxonomic_status: 'accepted',
    description: 'Wärmeliebendes Fruchtgemüse.',
    sowing_indoor_weeks_before_last_frost: 6,
    sowing_outdoor_after_last_frost_days: 14,
    direct_sow_months: [4],
    harvest_months: [8, 9],
    bloom_months: [6],
    harvest_from_year: 1,
    bloom_from_year: 1,
    frost_sensitivity: 'sensitive',
    plant_category: 'outdoor_vegetable',
    harvest_pattern: 'continuous',
    harvested_part: 'fruit',
    climacteric: 'climacteric',
    propagation_configs: [
      { method: 'seed', months: [4, 3], wood_stage: 'softwood', difficulty: 'easy', notes: 'Vorziehen.' },
    ],
    allows_harvest: true,
    growing_periods: [],
    container_suitable: 'yes',
    recommended_container_volume_l: '10',
    min_container_depth_cm: 30,
    mature_height_cm: '150',
    mature_width_cm: '60',
    spacing_cm: '50',
    indoor_suitable: 'yes',
    balcony_suitable: 'yes',
    greenhouse_recommended: true,
    support_required: true,
    watering_guide: null,
    default_nutrient_plan_key: 'np-1',
    representative_image_url: null,
    representative_image_attribution: null,
    representative_image_license: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
    ...overrides,
  };
}

/** All-null counterpart — exercises the falsy `|| null` and `?? default` arms. */
function makeNullSpecies(): Species {
  return makeFullSpecies({
    family_key: null,
    family_name: null,
    description: '',
    synonyms: [],
    taxonomic_authority: '',
    taxonomic_status: '',
    harvest_pattern: null,
    harvested_part: null,
    climacteric: null,
    propagation_configs: [],
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
    default_nutrient_plan_key: null,
  });
}

function makeStore(level: 'beginner' | 'intermediate' | 'expert', species: Species | null) {
  return createTestStore({
    userPreferences: {
      preferences: {
        key: 'pref-1',
        user_key: 'user-1',
        experience_level: level,
        onboarding_completed: true,
        locale: 'de',
        theme: 'light',
        watering_can_liters: 5,
        smart_home_enabled: false,
      },
      loading: false,
      error: null,
    },
    species: { items: [], total: 0, offset: 0, limit: 50, current: species, loading: false, error: null },
  });
}

describe('SpeciesDetailPage — edit form & actions', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    navigate.mockReset();
    updateSpecies.mockReset().mockResolvedValue(undefined);
    deleteSpecies.mockReset().mockResolvedValue(undefined);
    getSpecies.mockReset().mockResolvedValue(makeFullSpecies());
    getCompatibleSpecies.mockReset().mockResolvedValue([]);
    getIncompatibleSpecies.mockReset().mockResolvedValue([]);
  });

  it('submits the edit form of a fully-populated species and maps the payload', async () => {
    const user = userEvent.setup();
    renderWithProviders(<SpeciesDetailPage />, {
      store: makeStore('expert', makeFullSpecies()),
      route: '/#edit',
    });

    // Edit fields render (expert sees the expert-only climacteric field).
    expect(await screen.findByTestId('form-field-scientific_name')).toBeInTheDocument();
    expect(screen.getByTestId('form-field-climacteric')).toBeInTheDocument();

    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => expect(updateSpecies).toHaveBeenCalledOnce());
    const [calledKey, payload] = updateSpecies.mock.calls[0];
    expect(calledKey).toBe('sp-1');
    expect(payload).toMatchObject({ scientific_name: 'Solanum lycopersicum' });
    // months were de-duplicated and sorted in the propagation mapping.
    expect(payload.propagation_configs[0].months).toEqual([3, 4]);
  });

  it('submits the edit form of an all-null species (falsy mapping arms)', async () => {
    const user = userEvent.setup();
    getSpecies.mockResolvedValue(makeNullSpecies());
    renderWithProviders(<SpeciesDetailPage />, {
      store: makeStore('expert', makeNullSpecies()),
      route: '/#edit',
    });

    await screen.findByTestId('form-field-scientific_name');
    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => expect(updateSpecies).toHaveBeenCalledOnce());
    const payload = updateSpecies.mock.calls[0][1];
    expect(payload.harvest_pattern).toBeNull();
    expect(payload.default_nutrient_plan_key).toBeNull();
  });

  it('toggles the sowing favorite from the header action', async () => {
    const user = userEvent.setup();
    renderWithProviders(<SpeciesDetailPage />, { store: makeStore('intermediate', makeFullSpecies()) });

    const toggle = await screen.findByTestId('species-favorite-toggle');
    await user.click(toggle);
    // Clicking flips the favorite icon; the button stays in the document.
    expect(screen.getByTestId('species-favorite-toggle')).toBeInTheDocument();
  });

  it('deletes the species through the confirm dialog and navigates to the list', async () => {
    const user = userEvent.setup();
    renderWithProviders(<SpeciesDetailPage />, { store: makeStore('intermediate', makeFullSpecies()) });

    await user.click(await screen.findByRole('button', { name: i18n.t('common.delete') }));
    await user.click(await screen.findByTestId('confirm-dialog-confirm'));

    await waitFor(() => expect(deleteSpecies).toHaveBeenCalledWith('sp-1'));
    expect(navigate).toHaveBeenCalledWith('/stammdaten/species');
  });

  it('renders the companion-planting tab with compatible and incompatible panels (expert)', async () => {
    getCompatibleSpecies.mockResolvedValue([
      { species_key: 'sp-2', scientific_name: 'Basilikum', score: 0.8 },
    ]);
    getIncompatibleSpecies.mockResolvedValue([]);

    const user = userEvent.setup();
    renderWithProviders(<SpeciesDetailPage />, {
      store: makeStore('expert', makeFullSpecies()),
      route: '/#companion-planting',
    });

    // Compatible list renders the seeded entry; incompatible shows the empty state.
    expect(await screen.findByText('Basilikum')).toBeInTheDocument();
    expect(screen.getByText(i18n.t('pages.companionPlanting.noIncompatible'))).toBeInTheDocument();

    // Opening the add-compatible dialog flips the dialog-type branch.
    await user.click(screen.getByTestId('add-compatible-button'));
    expect(await screen.findByTestId('target-species-select')).toBeInTheDocument();
    expect(screen.getByTestId('score-input')).toBeInTheDocument();
  });

  it('renders the crop-rotation tab with the family card and successors (expert)', async () => {
    renderWithProviders(<SpeciesDetailPage />, {
      store: makeStore('expert', makeFullSpecies()),
      route: '/#crop-rotation',
    });

    // Family card resolves from getBotanicalFamily; successor list from getSuccessors.
    expect(await screen.findByTestId('family-card-link')).toBeInTheDocument();
    expect(await screen.findByTestId('add-successor-button')).toBeInTheDocument();
    expect(screen.getByText(i18n.t('pages.cropRotation.successorsTitle'))).toBeInTheDocument();
  });
});
