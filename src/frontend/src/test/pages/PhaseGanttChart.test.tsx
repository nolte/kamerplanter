import { screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import i18n from 'i18next';
import { renderWithProviders } from '../helpers';
import PhaseGanttChart from '@/pages/duengung/PhaseGanttChart';
import type {
  NutrientPlanPhaseEntry,
  DeliveryChannel,
  Fertilizer,
  FertilizerDosage,
} from '@/api/types';

function makeDosage(overrides: Partial<FertilizerDosage> = {}): FertilizerDosage {
  return { fertilizer_key: 'f1', ml_per_liter: 2, optional: false, mixing_order: 0, ...overrides };
}

function makeChannel(overrides: Partial<DeliveryChannel> = {}): DeliveryChannel {
  return {
    channel_id: 'ch-1',
    label: 'Kanal 1',
    application_method: 'drench',
    enabled: true,
    notes: null,
    schedule: null,
    target_ec_ms: null,
    target_ph: null,
    fertilizer_dosages: [],
    method_params: null,
    ...overrides,
  };
}

function makeEntry(overrides: Partial<NutrientPlanPhaseEntry> = {}): NutrientPlanPhaseEntry {
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
    target_ec_ms: null,
    reference_ec_ms: null,
    target_calcium_ppm: null,
    target_magnesium_ppm: null,
    reference_base_ec: 0,
    notes: null,
    delivery_channels: [makeChannel()],
    watering_schedule_override: null,
    water_mix_ratio_ro_percent: null,
    created_at: null,
    updated_at: null,
    ...overrides,
  };
}

function makeFert(overrides: Partial<Fertilizer> = {}): Fertilizer {
  return {
    key: 'f1',
    product_name: 'CalMag',
    brand: 'GH',
    fertilizer_type: 'base',
    is_organic: false,
    tank_safe: true,
    recommended_application: 'drench',
    npk_ratio: [2, 0, 0],
    ec_contribution_per_ml: 0.1,
    ec_contribution_uncertain: false,
    max_dose_ml_per_liter: null,
    mixing_priority: 0,
    ph_effect: 'neutral',
    bioavailability: 'medium',
    shelf_life_days: null,
    storage_temp_min: null,
    storage_temp_max: null,
    application_rate_g_per_m2: null,
    application_rate_l_per_m2: null,
    dilution_ratio: null,
    nutrient_release_speed: null,
    notes: null,
    created_at: null,
    updated_at: null,
    ...overrides,
  } as Fertilizer;
}

describe('PhaseGanttChart', () => {
  it('renders nothing for an empty entry list', () => {
    const { container } = renderWithProviders(<PhaseGanttChart entries={[]} fertilizers={[]} />);
    expect(container.querySelector('.MuiCard-root')).toBeNull();
  });

  it('renders the default title and per-week headers', () => {
    renderWithProviders(<PhaseGanttChart entries={[makeEntry()]} fertilizers={[]} />);
    expect(screen.getByText(i18n.t('pages.gantt.title'))).toBeInTheDocument();
    // Week columns are rendered as column headers (W1 … W4).
    const headers = screen.getAllByRole('columnheader');
    expect(headers.length).toBe(4);
    expect(screen.getByText(i18n.t('pages.gantt.week') + '1')).toBeInTheDocument();
  });

  it('honours the title / weekLabel overrides and highlights the current week', () => {
    renderWithProviders(
      <PhaseGanttChart
        entries={[makeEntry({ week_start: 1, week_end: 3 })]}
        fertilizers={[]}
        title="Mein Plan"
        weekLabel="KW"
        currentWeek={2}
      />,
    );
    expect(screen.getByText('Mein Plan')).toBeInTheDocument();
    expect(screen.getByText('KW2')).toBeInTheDocument();
  });

  it('renders month headers when showMonthHeaders is set', () => {
    renderWithProviders(
      <PhaseGanttChart
        entries={[makeEntry({ week_start: 1, week_end: 8 })]}
        fertilizers={[]}
        showMonthHeaders
        totalWeeksOverride={52}
        currentWeek={3}
      />,
    );
    // MONTH_WEEK_SPANS renders exactly twelve month column headers.
    expect(screen.getAllByRole('columnheader')).toHaveLength(12);
  });

  it('renders the EC target row with a numeric value', () => {
    const entries = [
      makeEntry({
        key: 'e1',
        sequence_order: 1,
        week_start: 1,
        week_end: 2,
        delivery_channels: [makeChannel({ target_ec_ms: 1.5 })],
      }),
      makeEntry({
        key: 'e2',
        sequence_order: 2,
        phase_name: 'flowering',
        week_start: 3,
        week_end: 4,
        delivery_channels: [makeChannel({ target_ec_ms: null })],
      }),
    ];
    renderWithProviders(<PhaseGanttChart entries={entries} fertilizers={[]} />);
    expect(screen.getByText(i18n.t('pages.gantt.ecTarget'))).toBeInTheDocument();
    expect(screen.getByText('1.5')).toBeInTheDocument();
  });

  it('expands and collapses a phase to reveal its delivery channel', async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <PhaseGanttChart
        entries={[makeEntry({ delivery_channels: [makeChannel({ label: 'Gießen Manuell' })] })]}
        fertilizers={[]}
      />,
    );
    const phaseBtn = screen.getByRole('button', { name: i18n.t('enums.phaseName.vegetative') });
    expect(screen.queryByText('Gießen Manuell')).toBeNull();
    await user.click(phaseBtn);
    expect(screen.getByText('Gießen Manuell')).toBeInTheDocument();
    await user.click(phaseBtn);
    expect(screen.queryByText('Gießen Manuell')).toBeNull();
  });

  it('toggles a phase via the keyboard (Enter)', () => {
    renderWithProviders(
      <PhaseGanttChart
        entries={[makeEntry({ delivery_channels: [makeChannel({ label: 'Tank A' })] })]}
        fertilizers={[]}
      />,
    );
    const phaseBtn = screen.getByRole('button', { name: i18n.t('enums.phaseName.vegetative') });
    fireEvent.keyDown(phaseBtn, { key: 'Enter' });
    expect(screen.getByText('Tank A')).toBeInTheDocument();
  });

  it('calls onPhaseClick instead of toggling when the handler is provided', async () => {
    const user = userEvent.setup();
    const onPhaseClick = vi.fn();
    renderWithProviders(
      <PhaseGanttChart
        entries={[makeEntry({ delivery_channels: [makeChannel({ label: 'Kanal X' })] })]}
        fertilizers={[]}
        onPhaseClick={onPhaseClick}
        selectedPhaseKey="e-1"
      />,
    );
    await user.click(screen.getByRole('button', { name: i18n.t('enums.phaseName.vegetative') }));
    expect(onPhaseClick).toHaveBeenCalledWith('e-1');
    // Channels are not expanded when onPhaseClick short-circuits the toggle.
    expect(screen.queryByText('Kanal X')).toBeNull();
  });

  it('invokes onEditEntry from the edit icon without toggling the phase', async () => {
    const user = userEvent.setup();
    const onEditEntry = vi.fn();
    renderWithProviders(
      <PhaseGanttChart
        entries={[makeEntry({ delivery_channels: [makeChannel({ label: 'Kanal Y' })] })]}
        fertilizers={[]}
        onEditEntry={onEditEntry}
      />,
    );
    const editIcon = document.querySelector('[data-testid="EditIcon"]');
    expect(editIcon).not.toBeNull();
    await user.click(editIcon!.closest('button')!);
    expect(onEditEntry).toHaveBeenCalledWith(expect.objectContaining({ key: 'e-1' }));
    // stopPropagation prevented the expand toggle.
    expect(screen.queryByText('Kanal Y')).toBeNull();
  });

  it('auto-expands single-channel entries when requested', () => {
    renderWithProviders(
      <PhaseGanttChart
        entries={[makeEntry({ delivery_channels: [makeChannel({ label: 'Auto Kanal' })] })]}
        fertilizers={[]}
        autoExpandSingleChannel
      />,
    );
    expect(screen.getByText('Auto Kanal')).toBeInTheDocument();
  });

  it('renders channel sub-rows directly in compact mode with dosage text', () => {
    const entries = [
      makeEntry({
        delivery_channels: [
          makeChannel({
            label: 'Kompakt Kanal',
            fertilizer_dosages: [
              makeDosage({ fertilizer_key: 'f1', ml_per_liter: 3 }),
              makeDosage({ fertilizer_key: 'unknown-fert', ml_per_liter: 7 }),
            ],
          }),
        ],
      }),
    ];
    renderWithProviders(
      <PhaseGanttChart
        entries={entries}
        fertilizers={[makeFert({ key: 'f1', product_name: 'BioGrow', brand: 'BioBizz' })]}
        compactMode
      />,
    );
    expect(screen.getByText('Kompakt Kanal')).toBeInTheDocument();
    // Merged dosage caption combines both dosages.
    expect(screen.getByText(/3 ml\/L.*7 ml\/L/)).toBeInTheDocument();
  });

  it('renders a phase that wraps across the year boundary without crashing', () => {
    const entries = [
      makeEntry({
        key: 'wrap',
        week_start: 3,
        week_end: 6,
        delivery_channels: [makeChannel({ label: 'Wrap Kanal', target_ec_ms: 2.0 })],
      }),
    ];
    renderWithProviders(
      <PhaseGanttChart
        entries={entries}
        fertilizers={[]}
        totalWeeksOverride={4}
        autoExpandSingleChannel
      />,
    );
    // Wrapped phase still renders its label and channel sub-row.
    expect(screen.getByText(i18n.t('enums.phaseName.vegetative'))).toBeInTheDocument();
    expect(screen.getByText('Wrap Kanal')).toBeInTheDocument();
  });
});
