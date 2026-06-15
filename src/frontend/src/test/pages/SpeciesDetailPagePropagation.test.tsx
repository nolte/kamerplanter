import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach } from 'vitest';
import i18n from 'i18next';
import SpeciesDetailPage from '@/pages/stammdaten/SpeciesDetailPage';
import { createTestStore, renderWithProviders } from '../helpers';
import type { Species } from '@/api/types';

function makeSpecies(): Species {
  return {
    key: 'sp-1',
    scientific_name: 'Monstera deliciosa',
    common_names: ['Monstera'],
    family_key: null,
    family_name: null,
    genus: 'Monstera',
    hardiness_zones: [],
    native_habitat: '',
    growth_habit: 'vine',
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
    propagation_configs: [
      { method: 'cutting', months: [5, 6], wood_stage: 'softwood', notes: 'Use sharp blade.' },
    ],
    allows_harvest: false,
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
  };
}

/** Store seeded with an expert preference and a preloaded `species.current`. */
function makeStore() {
  return createTestStore({
    userPreferences: {
      preferences: {
        key: 'pref-1',
        user_key: 'user-1',
        experience_level: 'expert',
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
      current: makeSpecies(),
      loading: false,
      error: null,
    },
  });
}

describe('SpeciesDetailPage — propagation config editor', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders the existing propagation config row from the seeded species', async () => {
    renderWithProviders(<SpeciesDetailPage />, { store: makeStore() });

    await waitFor(() => {
      expect(screen.getByTestId('propagation-config-0')).toBeInTheDocument();
    });
    // The method select for the first config is present.
    expect(screen.getByTestId('form-field-propagation_configs.0.method')).toBeInTheDocument();
  });

  it('adds a propagation method row', async () => {
    const user = userEvent.setup();
    renderWithProviders(<SpeciesDetailPage />, { store: makeStore() });

    await waitFor(() => {
      expect(screen.getByTestId('propagation-config-0')).toBeInTheDocument();
    });
    expect(screen.queryByTestId('propagation-config-1')).toBeNull();

    await user.click(screen.getByTestId('add-propagation-method'));

    await waitFor(() => {
      expect(screen.getByTestId('propagation-config-1')).toBeInTheDocument();
    });
  });

  it('removes a propagation method row', async () => {
    const user = userEvent.setup();
    renderWithProviders(<SpeciesDetailPage />, { store: makeStore() });

    await waitFor(() => {
      expect(screen.getByTestId('propagation-config-0')).toBeInTheDocument();
    });

    await user.click(screen.getByTestId('remove-propagation-config-0'));

    await waitFor(() => {
      expect(screen.queryByTestId('propagation-config-0')).toBeNull();
    });
  });
});
