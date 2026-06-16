import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import i18n from 'i18next';
import SpeciesOverview from '@/pages/stammdaten/SpeciesOverviewSection';
import { renderWithProviders } from '../helpers';
import type { Species, WateringGuide } from '@/api/types';

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
    ...overrides,
  };
}

function makeWatering(overrides: Partial<WateringGuide> = {}): WateringGuide {
  return {
    interval_days: 7,
    volume_ml_min: 200,
    volume_ml_max: 400,
    watering_method: 'top_water',
    water_quality_hint: null,
    practical_tip: null,
    seasonal_adjustments: [],
    ...overrides,
  };
}

describe('SpeciesOverviewSection', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders every chip, the description, the family link, propagation and the watering guide for a fully-populated species', () => {
    const species = makeSpecies({
      allows_harvest: true,
      frost_sensitivity: 'sensitive',
      growth_habit: 'herb',
      plant_category: 'outdoor_vegetable',
      harvest_pattern: 'continuous',
      harvested_part: 'fruit',
      description: 'Eine wärmeliebende Fruchtgemüse-Art.',
      family_key: 'fam-1',
      family_name: 'Solanaceae',
      propagation_configs: [
        // seed → success colour; months [3,4,9] exercises both the consecutive
        // merge and the non-consecutive split in monthsLabel; notes present.
        { method: 'seed', months: [3, 4, 9], wood_stage: null, notes: 'Vorziehen ab März.' },
        // non-seed (default colour), wood_stage chip, no months, no notes.
        { method: 'cutting', months: [], wood_stage: 'softwood', notes: null },
      ],
      watering_guide: makeWatering({
        water_quality_hint: 'Kalkarm gießen.',
        practical_tip: 'Morgens wässern.',
        seasonal_adjustments: [
          {
            label: 'Sommer',
            months: [6, 7, 8],
            interval_days: 3,
            volume_ml_min: 300,
            volume_ml_max: 500,
          },
        ],
      }),
    });

    renderWithProviders(
      <SpeciesOverview species={species} phaseSequenceKey="ps-1" onEdit={() => {}} />,
    );

    const chips = screen.getByTestId('overview-chips');
    expect(within(chips).getByText(i18n.t('pages.species.edible'))).toBeInTheDocument();
    expect(within(chips).getByText(i18n.t('enums.frostTolerance.sensitive'))).toBeInTheDocument();
    expect(within(chips).getByText(i18n.t('enums.growthHabit.herb'))).toBeInTheDocument();
    expect(
      within(chips).getByText(i18n.t('enums.plantCategory.outdoor_vegetable')),
    ).toBeInTheDocument();
    expect(within(chips).getByText(i18n.t('enums.harvestPattern.continuous'))).toBeInTheDocument();
    expect(within(chips).getByText(i18n.t('enums.harvestedPart.fruit'))).toBeInTheDocument();

    // Phase-sequence chip (phaseSequenceKey truthy).
    expect(screen.getByText(i18n.t('pages.phaseSequences.viewPhaseSequence'))).toBeInTheDocument();

    // Description block.
    expect(screen.getByText('Eine wärmeliebende Fruchtgemüse-Art.')).toBeInTheDocument();

    // Family link uses the family_name.
    const familyLink = screen.getByTestId('overview-family-link');
    expect(familyLink).toHaveTextContent('Solanaceae');
    expect(familyLink).toHaveAttribute('href', '/stammdaten/botanical-families/fam-1');

    // Two propagation rows; the first carries notes, the second a wood-stage chip.
    expect(screen.getByTestId('overview-propagation-0')).toBeInTheDocument();
    expect(screen.getByTestId('overview-propagation-1')).toBeInTheDocument();
    expect(screen.getByText('Vorziehen ab März.')).toBeInTheDocument();
    expect(screen.getByText(i18n.t('enums.woodStage.softwood'))).toBeInTheDocument();

    // Watering guide with all optional rows.
    expect(screen.getByText(i18n.t('pages.species.sectionWateringGuide'))).toBeInTheDocument();
    expect(screen.getByText('Kalkarm gießen.')).toBeInTheDocument();
    expect(screen.getByText('Morgens wässern.')).toBeInTheDocument();
    expect(screen.getByText(/Sommer/)).toBeInTheDocument();
  });

  it('shows the ornamental chip and omits all optional sections for a minimal species', () => {
    const species = makeSpecies({
      allows_harvest: false,
      frost_sensitivity: null,
      // plant_category set but without a matching enum label → chip suppressed.
      plant_category: 'no_such_category',
      harvest_pattern: null,
      harvested_part: null,
      description: '   ',
      family_key: null,
      propagation_configs: [],
      watering_guide: null,
    });

    renderWithProviders(
      <SpeciesOverview species={species} phaseSequenceKey={null} onEdit={() => {}} />,
    );

    const chips = screen.getByTestId('overview-chips');
    expect(within(chips).getByText(i18n.t('pages.species.ornamental'))).toBeInTheDocument();
    // The unmatched plant_category produced no chip.
    expect(within(chips).queryByText('no_such_category')).toBeNull();

    // None of the conditional sections render.
    expect(screen.queryByText(i18n.t('pages.phaseSequences.viewPhaseSequence'))).toBeNull();
    expect(screen.queryByTestId('overview-family-link')).toBeNull();
    expect(screen.queryByTestId('overview-propagation-0')).toBeNull();
    expect(screen.queryByText(i18n.t('pages.species.sectionWateringGuide'))).toBeNull();
  });

  it('falls back to the generic family label when family_name is missing', () => {
    const species = makeSpecies({ family_key: 'fam-9', family_name: null });
    renderWithProviders(
      <SpeciesOverview species={species} phaseSequenceKey={null} onEdit={() => {}} />,
    );

    const familyLink = screen.getByTestId('overview-family-link');
    expect(familyLink).toHaveTextContent(i18n.t('pages.species.viewFamily'));
  });

  it('renders the watering guide without its optional rows', () => {
    const species = makeSpecies({
      watering_guide: makeWatering({
        water_quality_hint: null,
        practical_tip: null,
        seasonal_adjustments: [],
      }),
    });
    renderWithProviders(
      <SpeciesOverview species={species} phaseSequenceKey={null} onEdit={() => {}} />,
    );

    expect(screen.getByText(i18n.t('pages.species.sectionWateringGuide'))).toBeInTheDocument();
    expect(screen.getByText(i18n.t('pages.species.wateringInterval') + ':')).toBeInTheDocument();
    // No seasonal adjustment heading when the list is empty.
    expect(screen.queryByText(i18n.t('pages.species.seasonalAdjustments') + ':')).toBeNull();
  });

  it('renders the hero image with its attribution + license caption when set', () => {
    const species = makeSpecies({
      representative_image_url: 'https://example.org/hero.jpg',
      representative_image_attribution: 'Jane Doe',
      representative_image_license: 'CC-BY',
    });
    renderWithProviders(
      <SpeciesOverview species={species} phaseSequenceKey={null} onEdit={() => {}} />,
    );

    const hero = screen.getByTestId('species-hero-image');
    expect(hero).toBeInTheDocument();
    const img = within(hero).getByRole('img', { name: 'Solanum lycopersicum' });
    expect(img).toHaveAttribute('src', 'https://example.org/hero.jpg');
    expect(img).toHaveAttribute('referrerpolicy', 'no-referrer');
    // Attribution is legally required for CC-BY and must be visible.
    expect(screen.getByTestId('species-hero-attribution')).toHaveTextContent('© Jane Doe · CC-BY');
  });

  it('omits the hero image entirely when no representative image URL is set', () => {
    renderWithProviders(
      <SpeciesOverview species={makeSpecies()} phaseSequenceKey={null} onEdit={() => {}} />,
    );
    expect(screen.queryByTestId('species-hero-image')).toBeNull();
  });

  it('invokes onEdit when the edit button is clicked', async () => {
    const user = userEvent.setup();
    const onEdit = vi.fn();
    renderWithProviders(
      <SpeciesOverview species={makeSpecies()} phaseSequenceKey={null} onEdit={onEdit} />,
    );

    await user.click(screen.getByTestId('overview-edit-button'));
    expect(onEdit).toHaveBeenCalledOnce();
  });
});
