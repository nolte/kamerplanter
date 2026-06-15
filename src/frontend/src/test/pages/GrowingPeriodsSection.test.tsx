import { screen } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import i18n from 'i18next';
import GrowingPeriodsSection from '@/pages/stammdaten/GrowingPeriodsSection';
import { renderWithProviders } from '../helpers';
import type { Species } from '@/api/types';

/** Minimal but type-complete Species mock with structured propagation_configs (WP-5). */
function makeSpecies(overrides: Partial<Species> = {}): Species {
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
    propagation_configs: [
      { method: 'cutting', months: [5, 6], wood_stage: 'softwood', notes: 'Use sharp blade.' },
      { method: 'division', months: [9] },
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
    ...overrides,
  };
}

describe('GrowingPeriodsSection — propagation_configs', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders one read-only block per configured propagation method', () => {
    const species = makeSpecies();
    renderWithProviders(<GrowingPeriodsSection speciesKey="sp-1" species={species} />);

    expect(screen.getByTestId('propagation-config-0')).toBeInTheDocument();
    expect(screen.getByTestId('propagation-config-1')).toBeInTheDocument();

    // Method labels (cutting + division) are shown
    expect(screen.getByText(i18n.t('enums.propagationMethod.cutting'))).toBeInTheDocument();
    expect(screen.getByText(i18n.t('enums.propagationMethod.division'))).toBeInTheDocument();
  });

  it('shows the wood stage and notes of a config', () => {
    const species = makeSpecies();
    renderWithProviders(<GrowingPeriodsSection speciesKey="sp-1" species={species} />);

    expect(screen.getByText(i18n.t('enums.woodStage.softwood'))).toBeInTheDocument();
    expect(screen.getByText('Use sharp blade.')).toBeInTheDocument();
  });

  it('renders the propagation timeline row using the union of all config months', () => {
    // cutting [5,6] + division [9] → union {5,6,9}; the timeline propagation row
    // must render (it appears only when periods exist, so seed one).
    const species = makeSpecies({
      growing_periods: [
        {
          label: 'Main',
          sowing_indoor_weeks_before_last_frost: null,
          sowing_outdoor_after_last_frost_days: null,
          direct_sow_months: [3],
          growth_months: [],
          harvest_months: [],
          bloom_months: [],
          harvest_from_year: null,
          bloom_from_year: null,
        },
      ],
    });
    renderWithProviders(<GrowingPeriodsSection speciesKey="sp-1" species={species} />);

    // The propagation bar kind label appears in the timing chart.
    expect(screen.getAllByText(i18n.t('pages.species.barKind.propagation')).length).toBeGreaterThan(
      0,
    );
  });

  it('does not render the propagation card when there are no configs', () => {
    const species = makeSpecies({ propagation_configs: [] });
    renderWithProviders(<GrowingPeriodsSection speciesKey="sp-1" species={species} />);

    expect(screen.queryByTestId('propagation-config-0')).toBeNull();
  });
});
