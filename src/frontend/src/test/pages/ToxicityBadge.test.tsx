import { screen, within } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import i18n from 'i18next';
import ToxicityBadge from '@/pages/stammdaten/species-detail/ToxicityBadge';
import SpeciesDetailPage from '@/pages/stammdaten/SpeciesDetailPage';
import { createTestStore, renderWithProviders } from '../helpers';
import type { Species, Toxicity } from '@/api/types';

function makeToxicity(overrides: Partial<Toxicity> = {}): Toxicity {
  return {
    is_toxic_cats: false,
    is_toxic_dogs: false,
    is_toxic_children: false,
    toxic_parts: [],
    toxic_compounds: [],
    severity: null,
    ...overrides,
  };
}

/** Type-complete Species mock; overridable per test. */
function makeSpecies(overrides: Partial<Species> = {}): Species {
  return {
    key: 'sp-1',
    scientific_name: 'Nerium oleander',
    common_names: ['Oleander'],
    family_key: null,
    family_name: null,
    genus: 'Nerium',
    hardiness_zones: [],
    native_habitat: '',
    growth_habit: 'shrub',
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
    frost_sensitivity: 'sensitive',
    plant_category: null,
    harvest_pattern: null,
    harvested_part: null,
    climacteric: null,
    toxicity: null,
    propagation_configs: [],
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
        module_visibility: {},
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

describe('ToxicityBadge — component', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders a warning with affected groups, severity, parts and compounds when toxic', () => {
    renderWithProviders(
      <ToxicityBadge
        toxicity={makeToxicity({
          is_toxic_children: true,
          is_toxic_cats: true,
          is_toxic_dogs: true,
          severity: 'severe',
          toxic_parts: ['leaves', 'sap'],
          toxic_compounds: ['oleandrin'],
        })}
      />,
    );

    const badge = screen.getByTestId('species-toxicity-badge');
    expect(badge).toBeInTheDocument();
    expect(within(badge).getByText(i18n.t('pages.species.toxicity.title'))).toBeInTheDocument();

    // Affected groups rendered as chips (children/cats/dogs).
    expect(screen.getByTestId('toxicity-affected-children')).toBeInTheDocument();
    expect(screen.getByTestId('toxicity-affected-cats')).toBeInTheDocument();
    expect(screen.getByTestId('toxicity-affected-dogs')).toBeInTheDocument();

    // Severity mapped through the enum namespace.
    expect(
      within(badge).getByText(i18n.t('enums.toxicitySeverity.severe')),
    ).toBeInTheDocument();

    // Free-text data fields surfaced.
    expect(within(badge).getByText(/leaves, sap/)).toBeInTheDocument();
    expect(within(badge).getByText(/oleandrin/)).toBeInTheDocument();
  });

  it('renders even when only a severity is set (no affected group)', () => {
    renderWithProviders(<ToxicityBadge toxicity={makeToxicity({ severity: 'mild' })} />);

    expect(screen.getByTestId('species-toxicity-badge')).toBeInTheDocument();
    expect(screen.queryByTestId('toxicity-affected-groups')).toBeNull();
    expect(screen.getByText(i18n.t('enums.toxicitySeverity.mild'))).toBeInTheDocument();
  });

  it('renders nothing when toxicity is null', () => {
    renderWithProviders(<ToxicityBadge toxicity={null} />);
    expect(screen.queryByTestId('species-toxicity-badge')).toBeNull();
  });

  it('renders nothing when the species is non-toxic (all flags false, severity none)', () => {
    renderWithProviders(<ToxicityBadge toxicity={makeToxicity({ severity: 'none' })} />);
    expect(screen.queryByTestId('species-toxicity-badge')).toBeNull();
  });
});

describe('SpeciesDetailPage — toxicity badge visibility (REQ-021 safety exception)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('shows the toxicity badge even at the beginner experience level', async () => {
    renderWithProviders(<SpeciesDetailPage />, {
      store: makeStore(
        'beginner',
        makeSpecies({
          toxicity: makeToxicity({ is_toxic_children: true, severity: 'severe' }),
        }),
      ),
    });

    // Wait for the page to mount (tab strip present), then assert the badge is
    // visible for a beginner — it must never be gated behind an expertise level.
    await screen.findByRole('tab', { name: i18n.t('pages.species.overviewTab') });
    expect(screen.getByTestId('species-toxicity-badge')).toBeInTheDocument();
  });

  it('omits the toxicity badge for a non-toxic species', async () => {
    renderWithProviders(<SpeciesDetailPage />, {
      store: makeStore('beginner', makeSpecies({ toxicity: null })),
    });

    await screen.findByRole('tab', { name: i18n.t('pages.species.overviewTab') });
    expect(screen.queryByTestId('species-toxicity-badge')).toBeNull();
  });
});
