import { screen, waitFor, within } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import i18n from 'i18next';
import SpeciesDetailPage from '@/pages/stammdaten/SpeciesDetailPage';
import { createTestStore } from '../helpers';
import { renderWithProviders } from '../helpers';
import type { Species } from '@/api/types';

/** Type-complete Species mock carrying the Phase A harvest properties. */
function makeSpecies(overrides: Partial<Species> = {}): Species {
  return {
    key: 'sp-1',
    scientific_name: 'Malus domestica',
    common_names: ['Apfel'],
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
    harvest_pattern: 'perennial',
    harvested_part: 'fruit',
    climacteric: 'climacteric',
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
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
    ...overrides,
  };
}

function makeStore(level: 'beginner' | 'intermediate' | 'expert', species: Species) {
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
    species: {
      items: [],
      total: 0,
      offset: 0,
      limit: 50,
      current: species,
      loading: false,
      error: null,
    },
  });
}

describe('SpeciesDetailPage — Phase A harvest properties', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders harvest_pattern, harvested_part and climacteric values for an expert', async () => {
    renderWithProviders(<SpeciesDetailPage />, {
      store: makeStore('expert', makeSpecies()),
    });

    // intermediate fields
    const pattern = await screen.findByTestId('form-field-harvest_pattern');
    expect(within(pattern).getByDisplayValue('perennial')).toBeInTheDocument();
    const part = screen.getByTestId('form-field-harvested_part');
    expect(within(part).getByDisplayValue('fruit')).toBeInTheDocument();

    // expert-only field
    const climacteric = screen.getByTestId('form-field-climacteric');
    expect(within(climacteric).getByDisplayValue('climacteric')).toBeInTheDocument();
  });

  it('offers a newly added growth_habit value (succulent) in the select', async () => {
    renderWithProviders(<SpeciesDetailPage />, {
      store: makeStore('intermediate', makeSpecies({ growth_habit: 'succulent' })),
    });

    const growthHabit = await screen.findByTestId('form-field-growth_habit');
    // The MUI select renders the selected value; succulent must be a valid option.
    expect(within(growthHabit).getByDisplayValue('succulent')).toBeInTheDocument();
  });

  it('hides the expert-only climacteric field from a beginner', async () => {
    renderWithProviders(<SpeciesDetailPage />, {
      store: makeStore('beginner', makeSpecies()),
    });

    await waitFor(() => {
      expect(screen.queryByTestId('form-field-harvest_pattern')).toBeNull();
    });
    // intermediate fields are also hidden for a beginner
    expect(screen.queryByTestId('form-field-harvested_part')).toBeNull();
    // expert-only field is hidden
    expect(screen.queryByTestId('form-field-climacteric')).toBeNull();
  });

  it('shows intermediate harvest fields but hides the expert climacteric field for an intermediate', async () => {
    renderWithProviders(<SpeciesDetailPage />, {
      store: makeStore('intermediate', makeSpecies()),
    });

    expect(await screen.findByTestId('form-field-harvest_pattern')).toBeInTheDocument();
    expect(screen.getByTestId('form-field-harvested_part')).toBeInTheDocument();
    expect(screen.queryByTestId('form-field-climacteric')).toBeNull();
  });
});
