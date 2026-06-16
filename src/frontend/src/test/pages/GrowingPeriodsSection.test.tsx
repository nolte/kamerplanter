import { screen, within, fireEvent } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import i18n from 'i18next';
import GrowingPeriodsSection from '@/pages/stammdaten/GrowingPeriodsSection';
import { renderWithProviders, createStoreWithExpertise } from '../helpers';
import type { GrowingPeriod, Species } from '@/api/types';

/** A growing period with the given month arrays; unspecified tracks stay empty. */
function makePeriod(overrides: Partial<GrowingPeriod> = {}): GrowingPeriod {
  return {
    label: 'Main',
    sowing_indoor_weeks_before_last_frost: null,
    sowing_outdoor_after_last_frost_days: null,
    direct_sow_months: [],
    growth_months: [],
    harvest_months: [],
    bloom_months: [],
    harvest_from_year: null,
    bloom_from_year: null,
    ...overrides,
  };
}

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
    harvest_pattern: null,
    harvested_part: null,
    climacteric: null,
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

// ── Plant-type-adaptive track visibility (§4) ───────────────────────────

describe('GrowingPeriodsSection — adaptive track visibility', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('(a) hides the harvest track and drops "Ernte" from the title for ornamentals (R-010/R-012)', () => {
    // Pure ornamental: allows_harvest=false, only bloom + vegetative propagation.
    const species = makeSpecies({
      allows_harvest: false,
      harvest_pattern: null,
      propagation_configs: [{ method: 'cutting', months: [5, 6] }],
      growing_periods: [makePeriod({ bloom_months: [6, 7, 8] })],
    });
    renderWithProviders(<GrowingPeriodsSection speciesKey="sp-1" species={species} />);

    // No harvest bar-kind label anywhere.
    expect(screen.queryByText(i18n.t('pages.species.barKind.harvest'))).toBeNull();
    // Title is "Vermehrung & Blüte" (no sow track either) and does not name harvest.
    expect(screen.getByText(i18n.t('pages.species.timingChartTitlePropBloom'))).toBeInTheDocument();
    expect(screen.queryByText(i18n.t('pages.species.timingChartTitle'))).toBeNull();
    // Bloom track is present.
    expect(screen.getAllByText(i18n.t('pages.species.barKind.bloom')).length).toBeGreaterThan(0);
  });

  it('keeps the harvest track for harvestable species (R-011)', () => {
    const species = makeSpecies({
      allows_harvest: true,
      propagation_configs: [{ method: 'seed', months: [3] }],
      growing_periods: [makePeriod({ direct_sow_months: [3], harvest_months: [8, 9] })],
    });
    renderWithProviders(<GrowingPeriodsSection speciesKey="sp-1" species={species} />);

    expect(screen.getAllByText(i18n.t('pages.species.barKind.harvest')).length).toBeGreaterThan(0);
    expect(screen.getByText(i18n.t('pages.species.timingChartTitle'))).toBeInTheDocument();
  });

  it('(b) hides the sow track for strictly vegetative species without sow data (R-013)', () => {
    const species = makeSpecies({
      allows_harvest: false,
      propagation_configs: [
        { method: 'cutting', months: [5, 6] },
        { method: 'division', months: [9] },
      ],
      growing_periods: [makePeriod({ bloom_months: [7, 8] })],
    });
    renderWithProviders(<GrowingPeriodsSection speciesKey="sp-1" species={species} />);

    expect(screen.queryByText(i18n.t('pages.species.barKind.sow'))).toBeNull();
    // Propagation row still carries the timing.
    expect(screen.getAllByText(i18n.t('pages.species.barKind.propagation')).length).toBeGreaterThan(
      0,
    );
  });

  it('shows the sow track when sow months exist despite vegetative propagation (R-013)', () => {
    const species = makeSpecies({
      propagation_configs: [{ method: 'cutting', months: [5] }],
      growing_periods: [makePeriod({ direct_sow_months: [3, 4] })],
    });
    renderWithProviders(<GrowingPeriodsSection speciesKey="sp-1" species={species} />);

    expect(screen.getAllByText(i18n.t('pages.species.barKind.sow')).length).toBeGreaterThan(0);
  });
});

// ── Harvest-pattern differentiation (R-021) ─────────────────────────────

describe('GrowingPeriodsSection — harvest pattern (R-021)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('(c) single vs continuous harvest render different harvest-bar variants', () => {
    const harvestVariant = (pattern: 'single' | 'continuous'): string | null => {
      const species = makeSpecies({
        allows_harvest: true,
        harvest_pattern: pattern,
        propagation_configs: [{ method: 'seed', months: [3] }],
        growing_periods: [makePeriod({ harvest_months: [8] })],
      });
      const { unmount, container } = renderWithProviders(
        <GrowingPeriodsSection speciesKey="sp-1" species={species} />,
        { store: createStoreWithExpertise('expert') },
      );
      // R-021: the harvest bar carries data-bar-variant = single (narrow, 40%)
      // vs continuous (full-width, 100%).
      const bar = container.querySelector('[data-bar-variant]') as HTMLElement | null;
      const variant = bar?.getAttribute('data-bar-variant') ?? null;
      unmount();
      return variant;
    };

    expect(harvestVariant('single')).toBe('single');
    expect(harvestVariant('continuous')).toBe('continuous');
  });

  it('harvest-pattern tooltip strings are distinct per pattern', () => {
    expect(i18n.t('pages.species.harvestPatternSingleTooltip')).not.toBe(
      i18n.t('pages.species.harvestPatternContinuousTooltip'),
    );
    expect(i18n.t('pages.species.harvestPatternContinuousTooltip')).not.toBe(
      i18n.t('pages.species.harvestPatternPerennialTooltip'),
    );
  });
});

// ── Keyboard editing of resize handles (R-044) ──────────────────────────

describe('GrowingPeriodsSection — keyboard handle editing (R-044)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('(d) ArrowRight on the end handle moves the month and announces the new range', () => {
    const species = makeSpecies({
      allows_harvest: true,
      harvest_pattern: 'continuous',
      propagation_configs: [{ method: 'seed', months: [3] }],
      growing_periods: [makePeriod({ harvest_months: [5, 6] })],
    });
    renderWithProviders(<GrowingPeriodsSection speciesKey="sp-1" species={species} />, {
      store: createStoreWithExpertise('expert'),
    });

    // Find the harvest end handle by its aria-label.
    const endHandle = screen.getByLabelText(
      i18n.t('pages.species.barResizeEndAriaLabel', {
        kind: i18n.t('pages.species.barKind.harvest'),
      }),
    );
    expect(endHandle).toHaveAttribute('aria-valuenow', '6');

    fireEvent.keyDown(endHandle, { key: 'ArrowRight' });

    // The end month advanced to July (7); the live region verbalises Mai–Jul.
    const live = screen.getByTestId('bar-live-0-harvest');
    expect(within(live).getByText(/Mai–Jul/)).toBeInTheDocument();
  });
});

// ── Progressive disclosure by expertise (R-030) ─────────────────────────

describe('GrowingPeriodsSection — progressive disclosure (R-030)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  function speciesWithPeriod(): Species {
    return makeSpecies({
      allows_harvest: true,
      propagation_configs: [{ method: 'seed', months: [3] }],
      growing_periods: [makePeriod({ direct_sow_months: [3], harvest_months: [8] })],
    });
  }

  it('(e) beginner hides the numeric detail fields in the expanded period', () => {
    renderWithProviders(<GrowingPeriodsSection speciesKey="sp-1" species={speciesWithPeriod()} />, {
      store: createStoreWithExpertise('beginner'),
    });

    // Expand the period detail form.
    fireEvent.click(screen.getByText(/Main/));

    expect(screen.queryByLabelText(/Voranzucht/)).toBeNull();
    expect(screen.queryByLabelText(/Auspflanzen/)).toBeNull();
  });

  it('expert shows the numeric detail fields in the expanded period', () => {
    renderWithProviders(<GrowingPeriodsSection speciesKey="sp-1" species={speciesWithPeriod()} />, {
      store: createStoreWithExpertise('expert'),
    });

    fireEvent.click(screen.getByText(/Main/));

    expect(screen.getByLabelText(/Voranzucht/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Auspflanzen/)).toBeInTheDocument();
  });

  it('beginner does not render drag handles on editable tracks', () => {
    renderWithProviders(<GrowingPeriodsSection speciesKey="sp-1" species={speciesWithPeriod()} />, {
      store: createStoreWithExpertise('beginner'),
    });

    expect(screen.queryByRole('slider')).toBeNull();
  });
});
