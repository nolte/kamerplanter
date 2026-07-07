import { screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import i18n from 'i18next';
import { renderWithProviders } from '../helpers';
import PhaseDetailGantt from '@/pages/duengung/PhaseDetailGantt';
import type {
  NutrientPlanPhaseEntry,
  DeliveryChannel,
  Fertilizer,
  FertilizerDosage,
} from '@/api/types';

function makeDosage(overrides: Partial<FertilizerDosage> = {}): FertilizerDosage {
  return { fertilizer_key: 'f1', ml_per_liter: 4, optional: false, mixing_order: 0, ...overrides };
}

function makeChannel(overrides: Partial<DeliveryChannel> = {}): DeliveryChannel {
  return {
    channel_id: 'ch-1',
    label: 'Manuell',
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
    phase_name: 'flowering',
    sequence_order: 1,
    week_start: 1,
    week_end: 4,
    is_recurring: false,
    npk_ratio: [1, 3, 2],
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
    product_name: 'BioGrow',
    brand: 'BioBizz',
    fertilizer_type: 'base',
    is_organic: true,
    tank_safe: true,
    recommended_application: 'drench',
    npk_ratio: [4, 3, 6],
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

/** Manual channel entry with EC, pH, entry-level RO and one fertilizer dosage. */
function fullEntry(): NutrientPlanPhaseEntry {
  return makeEntry({
    water_mix_ratio_ro_percent: 30,
    delivery_channels: [
      makeChannel({
        target_ec_ms: 1.5,
        target_ph: 6.2,
        fertilizer_dosages: [makeDosage({ fertilizer_key: 'f1', ml_per_liter: 4 })],
      }),
    ],
  });
}

const ferts = [makeFert()];

describe('PhaseDetailGantt', () => {
  it('renders nothing for an empty entry list', () => {
    const { container } = renderWithProviders(
      <PhaseDetailGantt entries={[]} fertilizers={[]} title="Detail" />,
    );
    expect(container.querySelector('.MuiCard-root')).toBeNull();
  });

  it('renders the manual channel group with EC / RO / pH / fertilizer rows (read-only)', () => {
    renderWithProviders(
      <PhaseDetailGantt entries={[fullEntry()]} fertilizers={ferts} title="Blüte Detail" />,
    );
    expect(screen.getByText('Blüte Detail')).toBeInTheDocument();
    expect(screen.getByText(i18n.t('pages.gantt.manual'))).toBeInTheDocument();
    expect(screen.getByText(i18n.t('pages.gantt.ecTarget'))).toBeInTheDocument();
    expect(screen.getByText(i18n.t('pages.gantt.roTarget'))).toBeInTheDocument();
    expect(screen.getByText('pH')).toBeInTheDocument();
    expect(screen.getByText('BioGrow')).toBeInTheDocument();
    expect(screen.getByText('BioBizz')).toBeInTheDocument();
    // Values.
    expect(screen.getAllByText('1.5').length).toBeGreaterThan(0);
    expect(screen.getAllByText('30%').length).toBeGreaterThan(0);
    expect(screen.getAllByText('6.2').length).toBeGreaterThan(0);
    expect(screen.getAllByText('4', { exact: true }).length).toBeGreaterThan(0);
    // Read-only: no reorder controls and no inline editor on click.
    expect(document.querySelector('[data-testid="ArrowUpwardIcon"]')).toBeNull();
  });

  it('renders the automatic group chip for fertigation channels', () => {
    const entry = makeEntry({
      delivery_channels: [makeChannel({ application_method: 'fertigation', label: 'Tank', target_ec_ms: 1.8 })],
    });
    renderWithProviders(<PhaseDetailGantt entries={[entry]} fertilizers={ferts} title="Auto" />);
    expect(screen.getByText(i18n.t('pages.gantt.automatic'))).toBeInTheDocument();
  });

  it('commits an EC edit on Enter and reports the updated entries', async () => {
    const user = userEvent.setup();
    const onEntriesChange = vi.fn();
    renderWithProviders(
      <PhaseDetailGantt entries={[fullEntry()]} fertilizers={ferts} title="Detail" onEntriesChange={onEntriesChange} />,
    );
    await user.click(screen.getAllByText('1.5')[0]);
    const input = screen.getByRole('spinbutton');
    await user.clear(input);
    await user.type(input, '2.1{Enter}');
    expect(onEntriesChange).toHaveBeenCalled();
    const updated = onEntriesChange.mock.lastCall![0] as NutrientPlanPhaseEntry[];
    expect(updated[0].delivery_channels[0].target_ec_ms).toBe(2.1);
  });

  it('commits an EC edit on blur', async () => {
    const user = userEvent.setup();
    const onEntriesChange = vi.fn();
    renderWithProviders(
      <PhaseDetailGantt entries={[fullEntry()]} fertilizers={ferts} title="Detail" onEntriesChange={onEntriesChange} />,
    );
    await user.click(screen.getAllByText('1.5')[0]);
    const input = screen.getByRole('spinbutton');
    await user.clear(input);
    await user.type(input, '3');
    fireEvent.blur(input);
    const updated = onEntriesChange.mock.lastCall![0] as NutrientPlanPhaseEntry[];
    expect(updated[0].delivery_channels[0].target_ec_ms).toBe(3);
  });

  it('cancels an edit on Escape without reporting changes', async () => {
    const user = userEvent.setup();
    const onEntriesChange = vi.fn();
    renderWithProviders(
      <PhaseDetailGantt entries={[fullEntry()]} fertilizers={ferts} title="Detail" onEntriesChange={onEntriesChange} />,
    );
    await user.click(screen.getAllByText('1.5')[0]);
    const input = screen.getByRole('spinbutton');
    await user.clear(input);
    await user.type(input, '9');
    fireEvent.keyDown(input, { key: 'Escape' });
    expect(onEntriesChange).not.toHaveBeenCalled();
    // Editor closed again.
    expect(screen.queryByRole('spinbutton')).toBeNull();
  });

  it('commits an entry-level RO% edit', async () => {
    const user = userEvent.setup();
    const onEntriesChange = vi.fn();
    renderWithProviders(
      <PhaseDetailGantt entries={[fullEntry()]} fertilizers={ferts} title="Detail" onEntriesChange={onEntriesChange} />,
    );
    await user.click(screen.getAllByText('30%')[0]);
    const input = screen.getByRole('spinbutton');
    await user.clear(input);
    await user.type(input, '45{Enter}');
    const updated = onEntriesChange.mock.lastCall![0] as NutrientPlanPhaseEntry[];
    expect(updated[0].water_mix_ratio_ro_percent).toBe(45);
  });

  it('commits a pH edit', async () => {
    const user = userEvent.setup();
    const onEntriesChange = vi.fn();
    renderWithProviders(
      <PhaseDetailGantt entries={[fullEntry()]} fertilizers={ferts} title="Detail" onEntriesChange={onEntriesChange} />,
    );
    await user.click(screen.getAllByText('6.2')[0]);
    const input = screen.getByRole('spinbutton');
    await user.clear(input);
    await user.type(input, '5.9{Enter}');
    const updated = onEntriesChange.mock.lastCall![0] as NutrientPlanPhaseEntry[];
    expect(updated[0].delivery_channels[0].target_ph).toBe(5.9);
  });

  it('commits a fertilizer dosage edit', async () => {
    const user = userEvent.setup();
    const onEntriesChange = vi.fn();
    renderWithProviders(
      <PhaseDetailGantt entries={[fullEntry()]} fertilizers={ferts} title="Detail" onEntriesChange={onEntriesChange} />,
    );
    await user.click(screen.getAllByText('4', { exact: true })[0]);
    const input = screen.getByRole('spinbutton');
    await user.clear(input);
    await user.type(input, '6{Enter}');
    const updated = onEntriesChange.mock.lastCall![0] as NutrientPlanPhaseEntry[];
    expect(updated[0].delivery_channels[0].fertilizer_dosages[0].ml_per_liter).toBe(6);
  });

  it('reorders fertilizers via the move controls', async () => {
    const user = userEvent.setup();
    const onEntriesChange = vi.fn();
    const entry = makeEntry({
      delivery_channels: [
        makeChannel({
          fertilizer_dosages: [
            makeDosage({ fertilizer_key: 'f1', ml_per_liter: 4, mixing_order: 0 }),
            makeDosage({ fertilizer_key: 'f2', ml_per_liter: 5, mixing_order: 1 }),
          ],
        }),
      ],
    });
    renderWithProviders(
      <PhaseDetailGantt
        entries={[entry]}
        fertilizers={[makeFert({ key: 'f1', product_name: 'BioGrow' }), makeFert({ key: 'f2', product_name: 'BioBloom' })]}
        title="Detail"
        onEntriesChange={onEntriesChange}
      />,
    );
    // Move the first fertilizer row down (swaps mixing order with the second).
    const downIcon = document.querySelector('[data-testid="ArrowDownwardIcon"]');
    await user.click(downIcon!.closest('button')!);
    expect(onEntriesChange).toHaveBeenCalled();
    const updated = onEntriesChange.mock.lastCall![0] as NutrientPlanPhaseEntry[];
    const dosages = updated[0].delivery_channels[0].fertilizer_dosages;
    const f1 = dosages.find((d) => d.fertilizer_key === 'f1')!;
    const f2 = dosages.find((d) => d.fertilizer_key === 'f2')!;
    expect(f1.mixing_order).toBe(1);
    expect(f2.mixing_order).toBe(0);
  });

  it('invokes onRemoveFertilizer from the delete control', async () => {
    const user = userEvent.setup();
    const onRemoveFertilizer = vi.fn();
    renderWithProviders(
      <PhaseDetailGantt
        entries={[fullEntry()]}
        fertilizers={ferts}
        title="Detail"
        onEntriesChange={vi.fn()}
        onRemoveFertilizer={onRemoveFertilizer}
      />,
    );
    const deleteIcon = document.querySelector('[data-testid="DeleteOutlinedIcon"]');
    expect(deleteIcon).not.toBeNull();
    await user.click(deleteIcon!.closest('button')!);
    expect(onRemoveFertilizer).toHaveBeenCalledWith('f1', false);
  });

  it('invokes onAddFertilizer from the add button', async () => {
    const user = userEvent.setup();
    const onAddFertilizer = vi.fn();
    renderWithProviders(
      <PhaseDetailGantt
        entries={[fullEntry()]}
        fertilizers={ferts}
        title="Detail"
        onEntriesChange={vi.fn()}
        onAddFertilizer={onAddFertilizer}
      />,
    );
    await user.click(screen.getByRole('button', { name: i18n.t('pages.nutrientPlans.addFertilizer') }));
    expect(onAddFertilizer).toHaveBeenCalledWith('e-1', 'ch-1');
  });

  it('falls back to the recommended RO% from the water-mix engine', () => {
    const entry = makeEntry({
      sequence_order: 2,
      water_mix_ratio_ro_percent: null,
      delivery_channels: [makeChannel({ target_ec_ms: 1.2 })],
    });
    renderWithProviders(
      <PhaseDetailGantt
        entries={[entry]}
        fertilizers={ferts}
        title="Detail"
        recommendedRoMap={new Map([[2, 40]])}
      />,
    );
    expect(screen.getAllByText('40%').length).toBeGreaterThan(0);
  });

  it('highlights the current week without crashing', () => {
    renderWithProviders(
      <PhaseDetailGantt entries={[fullEntry()]} fertilizers={ferts} title="Detail" currentWeek={2} />,
    );
    expect(screen.getByText('Detail')).toBeInTheDocument();
  });
});
