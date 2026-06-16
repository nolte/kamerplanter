import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach } from 'vitest';
import i18n from 'i18next';
import SpeciesDetailPage from '@/pages/stammdaten/SpeciesDetailPage';
import { createTestStore, renderWithProviders } from '../helpers';
import type { Species } from '@/api/types';

/** Type-complete Species mock; overridable per test. */
function makeSpecies(overrides: Partial<Species> = {}): Species {
  return {
    key: 'sp-1',
    scientific_name: 'Solanum lycopersicum',
    common_names: ['Tomate'],
    family_key: null,
    family_name: null,
    genus: 'Solanum',
    hardiness_zones: [],
    native_habitat: '',
    growth_habit: 'herb',
    root_type: 'fibrous',
    allelopathy_score: 0,
    base_temp: 10,
    synonyms: [],
    taxonomic_authority: '',
    taxonomic_status: '',
    description: 'Eine wärmeliebende Fruchtgemüse-Art.',
    sowing_indoor_weeks_before_last_frost: null,
    sowing_outdoor_after_last_frost_days: null,
    direct_sow_months: [],
    harvest_months: [],
    bloom_months: [],
    harvest_from_year: null,
    bloom_from_year: null,
    frost_sensitivity: 'sensitive',
    plant_category: null,
    harvest_pattern: 'continuous',
    harvested_part: 'fruit',
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

describe('SpeciesDetailPage — Overview tab', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('lands on the Overview tab by default and shows profile chips', async () => {
    renderWithProviders(<SpeciesDetailPage />, {
      store: makeStore('intermediate', makeSpecies()),
    });

    // The Overview tab is selected (default landing, index 0).
    const overviewTab = await screen.findByRole('tab', {
      name: i18n.t('pages.species.overviewTab'),
    });
    expect(overviewTab).toHaveAttribute('aria-selected', 'true');

    // Profile chips render the previously invisible real fields.
    const chips = await screen.findByTestId('overview-chips');
    // allows_harvest === true → "Essbar"
    expect(within(chips).getByText(i18n.t('pages.species.edible'))).toBeInTheDocument();
    // frost_sensitivity === 'sensitive' → enums.frostTolerance.sensitive
    expect(within(chips).getByText(i18n.t('enums.frostTolerance.sensitive'))).toBeInTheDocument();
    // harvest_pattern + harvested_part chips
    expect(within(chips).getByText(i18n.t('enums.harvestPattern.continuous'))).toBeInTheDocument();
    expect(within(chips).getByText(i18n.t('enums.harvestedPart.fruit'))).toBeInTheDocument();

    // The Edit form is not the default landing.
    expect(screen.queryByTestId('form-field-scientific_name')).toBeNull();
  });

  it('shows an "Zierpflanze" chip for a non-harvestable ornamental', async () => {
    renderWithProviders(<SpeciesDetailPage />, {
      store: makeStore(
        'intermediate',
        makeSpecies({ allows_harvest: false, harvest_pattern: null, harvested_part: null }),
      ),
    });

    const chips = await screen.findByTestId('overview-chips');
    expect(within(chips).getByText(i18n.t('pages.species.ornamental'))).toBeInTheDocument();
  });

  it('switches to the Edit tab when the Overview "Bearbeiten" button is clicked', async () => {
    const user = userEvent.setup();
    renderWithProviders(<SpeciesDetailPage />, {
      store: makeStore('intermediate', makeSpecies()),
    });

    const editButton = await screen.findByTestId('overview-edit-button');
    await user.click(editButton);

    // The Edit form (its required scientific_name field) is now rendered.
    await waitFor(() => {
      expect(screen.getByTestId('form-field-scientific_name')).toBeInTheDocument();
    });
    const editTab = screen.getByRole('tab', { name: i18n.t('common.edit') });
    expect(editTab).toHaveAttribute('aria-selected', 'true');
  });

  it('wires every tab panel with role=tabpanel and aria-labelledby (QW-1)', async () => {
    renderWithProviders(<SpeciesDetailPage />, {
      store: makeStore('intermediate', makeSpecies()),
    });

    // The visible Overview panel.
    const panel = await screen.findByRole('tabpanel');
    expect(panel).toHaveAttribute('id', 'species-tabpanel-0');
    expect(panel).toHaveAttribute('aria-labelledby', 'species-tab-0');

    // The owning tab points back at the panel.
    const overviewTab = screen.getByRole('tab', { name: i18n.t('pages.species.overviewTab') });
    expect(overviewTab).toHaveAttribute('id', 'species-tab-0');
    expect(overviewTab).toHaveAttribute('aria-controls', 'species-tabpanel-0');
  });

  it('hides the Companion & Crop-Rotation tabs for an intermediate but shows them for an expert (U-4)', async () => {
    const { unmount } = renderWithProviders(<SpeciesDetailPage />, {
      store: makeStore('intermediate', makeSpecies()),
    });

    await screen.findByRole('tab', { name: i18n.t('pages.species.overviewTab') });
    expect(screen.queryByRole('tab', { name: i18n.t('pages.companionPlanting.title') })).toBeNull();
    expect(screen.queryByRole('tab', { name: i18n.t('pages.cropRotation.title') })).toBeNull();

    unmount();

    renderWithProviders(<SpeciesDetailPage />, {
      store: makeStore('expert', makeSpecies()),
    });

    expect(
      await screen.findByRole('tab', { name: i18n.t('pages.companionPlanting.title') }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('tab', { name: i18n.t('pages.cropRotation.title') }),
    ).toBeInTheDocument();
  });

  it('falls back to Overview when deep-linking a tab hidden for the current expertise (U-4)', async () => {
    renderWithProviders(<SpeciesDetailPage />, {
      store: makeStore('intermediate', makeSpecies()),
      // companion-planting is expert-only → unknown slug for an intermediate.
      route: '/#companion-planting',
    });

    const overviewTab = await screen.findByRole('tab', {
      name: i18n.t('pages.species.overviewTab'),
    });
    expect(overviewTab).toHaveAttribute('aria-selected', 'true');
  });
});
