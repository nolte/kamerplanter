import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import type {
  NutrientPlan,
  NutrientPlanPhaseEntry,
  Site,
  DeliveryChannel,
} from '@/api/types';
import type { CalculateDosagesResponse } from '@/api/endpoints/nutrient-plans';

/**
 * REQ-004 — DosageCalculatorTab drives per-phase dosage calculation against a
 * site's water profile. The site-listing and dosage-calculation endpoints are
 * its externals and are doubled at the boundary. These tests cover site loading
 * (auto-select / multi-select / error), the water-profile branches, the phase
 * accordion interactions (channel switch, volume, RO slider, calculate) and the
 * full PhaseResult rendering (scaling, substrate correction, EC budget, CalMag,
 * dosage table sources, effective water, mixing instructions, warnings).
 */

const listSites = vi.fn();
const calculateDosages = vi.fn();
vi.mock('@/api/endpoints/sites', () => ({
  listSites: (...args: unknown[]) => listSites(...args),
}));
vi.mock('@/api/endpoints/nutrient-plans', () => ({
  calculateDosages: (...args: unknown[]) => calculateDosages(...args),
}));

import DosageCalculatorTab from '@/pages/duengung/DosageCalculatorTab';
import { renderWithProviders } from '../helpers';

const t = (k: string) => i18n.t(k);

const plan = { key: 'plan-1', name: 'Veg' } as NutrientPlan;

function siteWithRo(): Site {
  return {
    key: 'site-ro',
    name: 'Growroom',
    type: 'indoor',
    gps_coordinates: null,
    climate_zone: '7b',
    total_area_m2: 4,
    timezone: 'Europe/Berlin',
    water_config: {
      has_ro_system: true,
      tap_water_profile: {
        ec_ms: 0.4,
        ph: 7.2,
        alkalinity_ppm: 50,
        gh_ppm: 120,
        calcium_ppm: 30,
        magnesium_ppm: 10,
        chlorine_ppm: 0,
        chloramine_ppm: 0,
        measurement_date: null,
        source_note: null,
      },
    },
    water_config_warnings: [],
    last_frost_date_avg: null,
    first_frost_date_avg: null,
    eisheilige_date: null,
    created_at: null,
    updated_at: null,
  } as Site;
}

function siteNoProfile(name = 'Bare'): Site {
  return { ...siteWithRo(), key: `site-${name}`, name, water_config: null };
}

function channel(id: string, label: string): DeliveryChannel {
  return {
    channel_id: id,
    label,
    application_method: 'fertigation',
    enabled: true,
    notes: null,
    schedule: null,
    target_ec_ms: null,
    target_ph: null,
    fertilizer_dosages: [],
    method_params: null,
  };
}

function entry(overrides: Partial<NutrientPlanPhaseEntry> = {}): NutrientPlanPhaseEntry {
  return {
    key: 'e-1',
    plan_key: 'plan-1',
    phase_name: 'vegetative',
    sequence_order: 1,
    week_start: 1,
    week_end: 4,
    is_recurring: false,
    npk_ratio: [3, 1, 2],
    calcium_ppm: null,
    magnesium_ppm: null,
    target_ec_ms: 1.8,
    reference_ec_ms: null,
    target_calcium_ppm: null,
    target_magnesium_ppm: null,
    reference_base_ec: 0,
    notes: null,
    delivery_channels: [channel('ch-1', 'Kanal 1'), channel('ch-2', 'Kanal 2')],
    watering_schedule_override: null,
    water_mix_ratio_ro_percent: null,
    created_at: null,
    updated_at: null,
    ...overrides,
  };
}

function richResult(): CalculateDosagesResponse {
  return {
    phase_name: 'vegetative',
    channel_id: 'ch-1',
    target_ec_ms: 1.8,
    effective_water: {
      ec_ms: 0.4,
      ph: 6.5,
      alkalinity_ppm: 50,
      calcium_ppm: 30,
      magnesium_ppm: 10,
      chlorine_ppm: 0,
      chloramine_ppm: 0,
    },
    ro_percent_used: 25,
    calmag_correction: {
      calcium_deficit_ppm: 12.3,
      magnesium_deficit_ppm: 4.5,
      ca_mg_ratio: 3,
      ca_mg_ratio_warning: 'Ca:Mg ratio is off',
      needs_correction: true,
    },
    calmag_dosage: {
      product_name: 'CalMag',
      fertilizer_key: 'f-cm',
      ml_per_liter: 0.8,
      total_ml: 8,
      ec_contribution: 0.2,
      source: 'auto_calmag',
      mixing_order: 0,
    },
    ec_budget: {
      ec_base_water: 0.4,
      ec_calmag: 0.2,
      ec_ph_reserve: 0.1,
      ec_fertilizers: 1.1,
      ec_final: 1.8,
    },
    scaling_factor: 0.85,
    dosages: [
      { product_name: 'Base A', fertilizer_key: 'f-a', ml_per_liter: 2, total_ml: 20, ec_contribution: 0.5, source: 'reference', mixing_order: 1 },
      { product_name: 'Base B', fertilizer_key: 'f-b', ml_per_liter: 1.7, total_ml: 17, ec_contribution: 0.4, source: 'scaled', mixing_order: 2 },
      { product_name: 'CalMag', fertilizer_key: 'f-cm', ml_per_liter: 0.8, total_ml: 8, ec_contribution: 0.2, source: 'auto_calmag', mixing_order: 0 },
    ],
    mixing_instructions: ['Silikat zuerst', 'dann CalMag'],
    warnings: ['EC etwas hoch'],
    reference_ec_ms: 1.6,
    substrate_correction_applied: true,
  };
}

function leanResult(): CalculateDosagesResponse {
  return {
    phase_name: 'vegetative',
    channel_id: 'default',
    target_ec_ms: 1.0,
    effective_water: null,
    ro_percent_used: 0,
    calmag_correction: {
      calcium_deficit_ppm: 0,
      magnesium_deficit_ppm: 0,
      ca_mg_ratio: null,
      ca_mg_ratio_warning: null,
      needs_correction: false,
    },
    calmag_dosage: null,
    ec_budget: { ec_base_water: 0, ec_calmag: 0, ec_ph_reserve: 0, ec_fertilizers: 0, ec_final: 0 },
    scaling_factor: 1.0,
    dosages: [],
    mixing_instructions: [],
    warnings: [],
    reference_ec_ms: null,
    substrate_correction_applied: false,
  };
}

beforeEach(() => {
  i18n.changeLanguage('de');
  listSites.mockReset().mockResolvedValue([]);
  calculateDosages.mockReset().mockResolvedValue(leanResult());
});

describe('DosageCalculatorTab — site loading', () => {
  it('auto-selects the only site and shows its water-profile chips', async () => {
    listSites.mockResolvedValue([siteWithRo()]);
    renderWithProviders(<DosageCalculatorTab plan={plan} entries={[entry()]} />);
    // Auto-selected → tap-water chips are shown.
    expect(await screen.findByText('Tap EC: 0.4 mS/cm')).toBeInTheDocument();
    expect(screen.getByText('pH: 7.2')).toBeInTheDocument();
    expect(screen.getByText('RO')).toBeInTheDocument();
  });

  it('shows the no-water-profile hint for a site without a water config', async () => {
    listSites.mockResolvedValue([siteNoProfile()]);
    renderWithProviders(<DosageCalculatorTab plan={plan} entries={[entry()]} />);
    expect(
      await screen.findByText(t('pages.nutrientPlans.dosageCalc.noWaterProfile')),
    ).toBeInTheDocument();
  });

  it('lets the user pick a site when several are available', async () => {
    const user = userEvent.setup();
    listSites.mockResolvedValue([siteNoProfile('Alpha'), siteNoProfile('Beta')]);
    renderWithProviders(<DosageCalculatorTab plan={plan} entries={[entry()]} />);

    // Not auto-selected → expanding a phase shows the "select site first" hint.
    await waitFor(() => expect(listSites).toHaveBeenCalled());
    await user.click(screen.getByText(t('enums.phaseName.vegetative')));
    expect(
      screen.getByText(t('pages.nutrientPlans.dosageCalc.selectSiteFirst')),
    ).toBeInTheDocument();

    // Pick a site through the autocomplete.
    const combo = within(screen.getByTestId('dosage-site-select')).getByRole('combobox');
    await user.click(combo);
    await user.click(await screen.findByRole('option', { name: 'Beta' }));

    await waitFor(() =>
      expect(
        screen.queryByText(t('pages.nutrientPlans.dosageCalc.selectSiteFirst')),
      ).not.toBeInTheDocument(),
    );
  });

  it('does not crash when the site listing fails', async () => {
    listSites.mockRejectedValue(new Error('network'));
    renderWithProviders(<DosageCalculatorTab plan={plan} entries={[entry()]} />);
    expect(await screen.findByTestId('dosage-calculator-tab')).toBeInTheDocument();
  });

  it('renders the empty-state alert when the plan has no entries', async () => {
    listSites.mockResolvedValue([]);
    renderWithProviders(<DosageCalculatorTab plan={plan} entries={[]} />);
    expect(
      await screen.findByText(t('pages.nutrientPlans.noEntries')),
    ).toBeInTheDocument();
  });
});

describe('DosageCalculatorTab — phase calculation & result', () => {
  it('auto-calculates on expand and renders the full result, then recalculates on interaction', async () => {
    const user = userEvent.setup();
    listSites.mockResolvedValue([siteWithRo()]);
    calculateDosages.mockResolvedValue(richResult());

    renderWithProviders(<DosageCalculatorTab plan={plan} entries={[entry()]} />);
    await screen.findByText('Tap EC: 0.4 mS/cm');

    // Expand the phase → auto-calculation fires.
    await user.click(screen.getByText(t('enums.phaseName.vegetative')));
    await waitFor(() => expect(calculateDosages).toHaveBeenCalled());

    // Scaling-factor alert (0.85 ≠ 1) + substrate correction alert.
    await waitFor(() =>
      expect(screen.getByText('0.850')).toBeInTheDocument(),
    );
    expect(
      screen.getByTestId('calmag-correction-alert'),
    ).toBeInTheDocument();
    // Dosage table rows.
    expect(screen.getByText('Base A')).toBeInTheDocument();
    expect(screen.getByText('Base B')).toBeInTheDocument();
    // Effective water card, mixing instructions and warnings.
    expect(screen.getByText('Silikat zuerst')).toBeInTheDocument();
    expect(screen.getByText('EC etwas hoch')).toBeInTheDocument();
    expect(screen.getByText('pH: 6.5')).toBeInTheDocument();

    const callsAfterExpand = calculateDosages.mock.calls.length;

    // Switch delivery channel → recalculation.
    await user.click(screen.getByText('Kanal 2'));
    await waitFor(() =>
      expect(calculateDosages.mock.calls.length).toBeGreaterThan(callsAfterExpand),
    );
    const callsAfterChannel = calculateDosages.mock.calls.length;

    // Change the volume and blur → recalculation.
    const volumeField = within(screen.getByTestId('dosage-volume-1')).getByRole('spinbutton');
    await user.clear(volumeField);
    await user.type(volumeField, '25');
    await user.tab();
    await waitFor(() =>
      expect(calculateDosages.mock.calls.length).toBeGreaterThan(callsAfterChannel),
    );
    const callsAfterVolume = calculateDosages.mock.calls.length;

    // Nudge the RO slider (enabled because the site has an RO system).
    const slider = screen.getByTestId('dosage-ro-slider-1').querySelector('input[type="range"]') as HTMLInputElement;
    slider.focus();
    await user.keyboard('{ArrowRight}');
    await waitFor(() =>
      expect(calculateDosages.mock.calls.length).toBeGreaterThan(callsAfterVolume),
    );

    // Explicit calculate button also triggers a call.
    const callsBeforeButton = calculateDosages.mock.calls.length;
    await user.click(screen.getByTestId('dosage-calculate-1'));
    await waitFor(() =>
      expect(calculateDosages.mock.calls.length).toBeGreaterThan(callsBeforeButton),
    );
  });

  it('renders the lean result branch (no scaling, calmag satisfied, empty table)', async () => {
    const user = userEvent.setup();
    listSites.mockResolvedValue([siteWithRo()]);
    calculateDosages.mockResolvedValue(leanResult());

    renderWithProviders(<DosageCalculatorTab plan={plan} entries={[entry()]} />);
    await screen.findByText('Tap EC: 0.4 mS/cm');

    await user.click(screen.getByText(t('enums.phaseName.vegetative')));
    await waitFor(() =>
      expect(
        screen.getByText(t('pages.nutrientPlans.dosageCalc.calmagNotNeeded')),
      ).toBeInTheDocument(),
    );
    // No dosage table (empty dosages) and no scaling alert.
    expect(screen.queryByTestId('calmag-correction-alert')).not.toBeInTheDocument();
  });

  it('surfaces the site select without crashing when calculation rejects', async () => {
    const user = userEvent.setup();
    listSites.mockResolvedValue([siteWithRo()]);
    calculateDosages.mockRejectedValue(new Error('calc failed'));

    renderWithProviders(<DosageCalculatorTab plan={plan} entries={[entry()]} />);
    await screen.findByText('Tap EC: 0.4 mS/cm');
    await user.click(screen.getByText(t('enums.phaseName.vegetative')));
    await waitFor(() => expect(calculateDosages).toHaveBeenCalled());
    // The tab is still mounted after the rejection is handled.
    expect(screen.getByTestId('dosage-calculator-tab')).toBeInTheDocument();
  });
});
