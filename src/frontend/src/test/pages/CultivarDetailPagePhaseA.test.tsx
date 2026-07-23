import { screen, within } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import i18n from 'i18next';
import type { Cultivar, Species } from '@/api/types';

// Provide stable route params for CultivarDetailPage (speciesKey + cultivarKey).
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ speciesKey: 'sp-1', cultivarKey: 'cv-1' }),
    useNavigate: () => vi.fn(),
  };
});

// Mock the API endpoints the page loads on mount.
const getCultivar = vi.fn();
const getSpecies = vi.fn();
vi.mock('@/api/endpoints/species', () => ({
  getCultivar: (...args: unknown[]) => getCultivar(...args),
  getSpecies: (...args: unknown[]) => getSpecies(...args),
  updateCultivar: vi.fn(),
  deleteCultivar: vi.fn(),
}));
vi.mock('@/api/endpoints/phases', () => ({
  getLifecycleConfig: vi.fn().mockRejectedValue(new Error('no lifecycle')),
  listGrowthPhases: vi.fn().mockResolvedValue([]),
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
    dtm_reference: 'transplant',
    bearing_start_year_min: 3,
    bearing_start_year_max: 5,
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

describe('CultivarDetailPage — Phase A fields', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    getCultivar.mockResolvedValue(makeCultivar());
    getSpecies.mockResolvedValue(makeSpecies());
  });

  it('renders dtm_reference and the bearing-year range for an expert', async () => {
    renderWithProviders(<CultivarDetailPage />, { store: createStoreWithExpertise('expert') });

    // bearing-year range (intermediate)
    const min = await screen.findByTestId('form-field-bearing_start_year_min');
    expect(within(min).getByDisplayValue('3')).toBeInTheDocument();
    const max = screen.getByTestId('form-field-bearing_start_year_max');
    expect(within(max).getByDisplayValue('5')).toBeInTheDocument();

    // dtm_reference (expert-only)
    const dtm = screen.getByTestId('form-field-dtm_reference');
    expect(within(dtm).getByDisplayValue('transplant')).toBeInTheDocument();
  });

  it('renders the seed_type select pre-filled from the cultivar (intermediate)', async () => {
    getCultivar.mockResolvedValue(makeCultivar({ seed_type: 'f1_hybrid' }));
    renderWithProviders(<CultivarDetailPage />, { store: createStoreWithExpertise('intermediate') });

    const seedType = await screen.findByTestId('form-field-seed_type');
    expect(within(seedType).getByDisplayValue('f1_hybrid')).toBeInTheDocument();
  });

  it('hides the expert-only dtm_reference field from a beginner', async () => {
    renderWithProviders(<CultivarDetailPage />, { store: createStoreWithExpertise('beginner') });

    // Wait for the page to load (name field is always present).
    await screen.findByTestId('form-field-name');
    expect(screen.queryByTestId('form-field-dtm_reference')).toBeNull();
    // intermediate bearing-year fields are also hidden for a beginner
    expect(screen.queryByTestId('form-field-bearing_start_year_min')).toBeNull();
    // seed_type is intermediate → also hidden for a beginner
    expect(screen.queryByTestId('form-field-seed_type')).toBeNull();
  });
});
