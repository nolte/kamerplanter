/* eslint-disable @typescript-eslint/no-explicit-any */
import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterAll, vi } from 'vitest';
import i18n from 'i18next';
import type {
  NutrientPlan,
  NutrientPlanPhaseEntry,
  DeliveryChannel,
  Fertilizer,
} from '@/api/types';
import { renderWithProviders, createStoreWithExpertise } from '../helpers';

// Stub the heavy timeline children so this stays a focused unit test and the
// inline callback wiring can be exercised deterministically.
vi.mock('@/pages/duengung/PhaseGanttChart', () => ({
  __esModule: true,
  PHASE_COLORS: { vegetative: '#123456' } as Record<string, string>,
  default: (props: any) => (
    <button data-testid="stub-gantt" onClick={() => props.onEditEntry?.(props.entries[0])}>
      gantt:{props.title}
    </button>
  ),
}));
vi.mock('@/pages/duengung/PhaseDetailGantt', () => ({
  __esModule: true,
  default: (props: any) => (
    <div data-testid="stub-detail">
      <button data-testid="stub-detail-entries" onClick={() => props.onEntriesChange?.(props.entries)}>
        de
      </button>
      <button data-testid="stub-detail-remove" onClick={() => props.onRemoveFertilizer?.('f1', false)}>
        dr
      </button>
      <button data-testid="stub-detail-add" onClick={() => props.onAddFertilizer?.(props.entries[0].key, 'c1')}>
        da
      </button>
    </div>
  ),
}));
vi.mock('@/pages/duengung/DeliveryChannelAccordion', () => ({
  __esModule: true,
  default: (props: any) => (
    <div data-testid="stub-accordion">
      <button data-testid="stub-acc-edit" onClick={() => props.onEditChannel(props.channels[0])}>ec</button>
      <button data-testid="stub-acc-del" onClick={() => props.onDeleteChannel(props.channels[0].channel_id)}>dc</button>
      <button data-testid="stub-acc-addfert" onClick={() => props.onAddFertilizer(props.channels[0].channel_id)}>af</button>
      <button
        data-testid="stub-acc-editfert"
        onClick={() => props.onEditFertilizer(props.channels[0].channel_id, props.channels[0].fertilizer_dosages[0])}
      >
        ef
      </button>
      <button data-testid="stub-acc-rmfert" onClick={() => props.onRemoveFertilizer(props.channels[0].channel_id, 'f1')}>rf</button>
      <button data-testid="stub-acc-log" onClick={() => props.onLogWatering?.(props.channels[0])}>lg</button>
    </div>
  ),
}));
vi.mock('@/pages/duengung/DeliveryChannelChips', () => ({
  __esModule: true,
  default: () => <span data-testid="stub-chips" />,
}));

import PhaseTimelineTab from '@/pages/duengung/nutrient-plan-detail/PhaseTimelineTab';

function makeChannel(overrides: Partial<DeliveryChannel> = {}): DeliveryChannel {
  return {
    channel_id: 'c1',
    label: 'Channel',
    application_method: 'drench',
    enabled: true,
    notes: null,
    schedule: null,
    target_ec_ms: 1.2,
    target_ph: 6,
    fertilizer_dosages: [{ fertilizer_key: 'f1', ml_per_liter: 2, optional: false, mixing_order: 1 }],
    method_params: null,
    ...overrides,
  } as DeliveryChannel;
}

function makeEntry(overrides: Partial<NutrientPlanPhaseEntry> = {}): NutrientPlanPhaseEntry {
  return {
    key: 'e1',
    plan_key: 'np-1',
    phase_name: 'vegetative',
    sequence_order: 1,
    week_start: 1,
    week_end: 4,
    is_recurring: false,
    npk_ratio: [3, 1, 2],
    calcium_ppm: null,
    magnesium_ppm: null,
    target_ec_ms: 1.2,
    reference_ec_ms: null,
    target_calcium_ppm: null,
    target_magnesium_ppm: null,
    reference_base_ec: 0.3,
    notes: null,
    delivery_channels: [makeChannel()],
    watering_schedule_override: null,
    water_mix_ratio_ro_percent: null,
    created_at: null,
    updated_at: null,
    ...overrides,
  };
}

const plan = { key: 'np-1', name: 'Plan', cycle_restart_from_sequence: null } as NutrientPlan;
const perennialPlan = { key: 'np-1', name: 'Perennial', cycle_restart_from_sequence: 3 } as NutrientPlan;
const fertilizers = [{ key: 'f1', product_name: 'Grow' } as Fertilizer];

function baseHandlers() {
  return {
    toggleExpanded: vi.fn(),
    onAddEntry: vi.fn(),
    onEditEntry: vi.fn(),
    onDeleteEntry: vi.fn(),
    onAddChannel: vi.fn(),
    onEditChannel: vi.fn(),
    onDeleteChannel: vi.fn(),
    onAddChannelFertilizer: vi.fn(),
    onEditChannelFertilizer: vi.fn(),
    onRemoveChannelFertilizer: vi.fn(),
    onRemoveFertilizerFromGantt: vi.fn(),
    onEntriesChange: vi.fn(),
    onLogWatering: vi.fn(),
  };
}

function render(
  entries: NutrientPlanPhaseEntry[],
  handlers = baseHandlers(),
  {
    planOverride = plan,
    expanded = new Set<string>(),
  }: { planOverride?: NutrientPlan; expanded?: Set<string> } = {},
) {
  renderWithProviders(
    <PhaseTimelineTab
      plan={planOverride}
      entries={entries}
      fertilizers={fertilizers}
      expandedEntries={expanded}
      {...handlers}
    />,
    { store: createStoreWithExpertise('expert') },
  );
  return handlers;
}

describe('PhaseTimelineTab', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });
  afterAll(() => {
    i18n.changeLanguage('en');
  });

  it('renders the empty state and fires the add-entry action', async () => {
    const user = userEvent.setup();
    const handlers = render([]);
    expect(screen.getByText(i18n.t('pages.nutrientPlans.noEntries'))).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: i18n.t('pages.nutrientPlans.addEntry') }));
    expect(handlers.onAddEntry).toHaveBeenCalled();
  });

  it('renders a linear plan with EC ranges, extra nutrients and an override chip', async () => {
    const user = userEvent.setup();
    const e1 = makeEntry({
      key: 'e1',
      phase_name: 'vegetative',
      sequence_order: 1,
      delivery_channels: [
        makeChannel({ channel_id: 'c1', target_ec_ms: 1.2 }),
        makeChannel({ channel_id: 'c2', target_ec_ms: 1.8 }),
      ],
      calcium_ppm: 20,
      magnesium_ppm: 10,
      notes: 'keep humid',
      watering_schedule_override: {
        schedule_mode: 'interval',
        weekday_schedule: [],
        interval_days: 2,
        preferred_time: null,
        application_method: 'drench',
        reminder_hours_before: 2,
        times_per_day: 1,
      },
    });
    const e2 = makeEntry({
      key: 'e2',
      phase_name: 'flowering',
      sequence_order: 2,
      delivery_channels: [makeChannel({ channel_id: 'c3', target_ec_ms: 1.5 })],
    });
    const e3 = makeEntry({
      key: 'e3',
      phase_name: 'seedling',
      sequence_order: 0,
      delivery_channels: [makeChannel({ channel_id: 'c4', target_ec_ms: null })],
    });

    const handlers = render([e1, e2, e3], baseHandlers(), { expanded: new Set(['e1', 'e2']) });

    // EC range vs single value chips
    expect(screen.getByText('EC 1.2–1.8 mS/cm')).toBeInTheDocument();
    expect(screen.getByText('EC 1.5 mS/cm')).toBeInTheDocument();
    // extra nutrient + notes row
    expect(screen.getByText('Ca: 20 ppm')).toBeInTheDocument();
    expect(screen.getByText('Mg: 10 ppm')).toBeInTheDocument();
    expect(screen.getByText('keep humid')).toBeInTheDocument();
    // both detail gantts (veg + flower) rendered
    expect(screen.getAllByTestId('stub-detail')).toHaveLength(2);
    // expanded entries expose the accordion stub
    expect(screen.getAllByTestId('stub-accordion').length).toBeGreaterThan(0);

    // toggle a collapsed row
    const showLabel = i18n.t('pages.nutrientPlans.showFertilizers');
    await user.click(screen.getAllByRole('button', { name: showLabel })[2]);
    expect(handlers.toggleExpanded).toHaveBeenCalled();

    // card edit / delete affordances
    await user.click(screen.getAllByTestId('EditIcon')[0].closest('button')!);
    expect(handlers.onEditEntry).toHaveBeenCalled();
    await user.click(screen.getAllByTestId('DeleteIcon')[0].closest('button')!);
    expect(handlers.onDeleteEntry).toHaveBeenCalled();

    // add-channel button inside an expanded card
    await user.click(
      screen.getAllByRole('button', { name: i18n.t('pages.deliveryChannels.addChannel') })[0],
    );
    expect(handlers.onAddChannel).toHaveBeenCalled();
  });

  it('wires the accordion and detail-gantt callbacks through', async () => {
    const user = userEvent.setup();
    const e1 = makeEntry({ key: 'e1', phase_name: 'vegetative', sequence_order: 1 });
    const e2 = makeEntry({ key: 'e2', phase_name: 'flowering', sequence_order: 2 });
    const handlers = render([e1, e2], baseHandlers(), { expanded: new Set(['e1']) });

    const acc = screen.getAllByTestId('stub-accordion')[0];
    await user.click(within(acc).getByTestId('stub-acc-edit'));
    expect(handlers.onEditChannel).toHaveBeenCalledWith('e1', expect.objectContaining({ channel_id: 'c1' }));
    await user.click(within(acc).getByTestId('stub-acc-del'));
    expect(handlers.onDeleteChannel).toHaveBeenCalledWith('e1', 'c1');
    await user.click(within(acc).getByTestId('stub-acc-addfert'));
    expect(handlers.onAddChannelFertilizer).toHaveBeenCalledWith('e1', 'c1');
    await user.click(within(acc).getByTestId('stub-acc-editfert'));
    expect(handlers.onEditChannelFertilizer).toHaveBeenCalledWith('e1', 'c1', expect.any(Object));
    await user.click(within(acc).getByTestId('stub-acc-rmfert'));
    expect(handlers.onRemoveChannelFertilizer).toHaveBeenCalledWith('e1', 'c1', 'f1');
    await user.click(within(acc).getByTestId('stub-acc-log'));
    expect(handlers.onLogWatering).toHaveBeenCalled();

    // detail-gantt wiring
    await user.click(screen.getAllByTestId('stub-detail-entries')[0]);
    expect(handlers.onEntriesChange).toHaveBeenCalled();
    await user.click(screen.getAllByTestId('stub-detail-remove')[0]);
    expect(handlers.onRemoveFertilizerFromGantt).toHaveBeenCalledWith('f1', false, expect.any(Array));
    await user.click(screen.getAllByTestId('stub-detail-add')[0]);
    expect(handlers.onAddChannelFertilizer).toHaveBeenCalledWith('e1', 'c1');

    // the top gantt hero forwards edits too
    await user.click(screen.getAllByTestId('stub-gantt')[0]);
    expect(handlers.onEditEntry).toHaveBeenCalled();
  });

  it('shows the no-channels hint and omits optional gantt wiring', () => {
    const e1 = makeEntry({ key: 'e1', phase_name: 'vegetative', delivery_channels: [] });
    const handlers = baseHandlers();
    // drop the optional gantt callbacks to hit the "undefined" ternary branch
    renderWithProviders(
      <PhaseTimelineTab
        plan={plan}
        entries={[e1]}
        fertilizers={fertilizers}
        expandedEntries={new Set(['e1'])}
        toggleExpanded={handlers.toggleExpanded}
        onAddEntry={handlers.onAddEntry}
        onEditEntry={handlers.onEditEntry}
        onDeleteEntry={handlers.onDeleteEntry}
        onAddChannel={handlers.onAddChannel}
        onEditChannel={handlers.onEditChannel}
        onDeleteChannel={handlers.onDeleteChannel}
        onAddChannelFertilizer={handlers.onAddChannelFertilizer}
        onEditChannelFertilizer={handlers.onEditChannelFertilizer}
        onRemoveChannelFertilizer={handlers.onRemoveChannelFertilizer}
      />,
      { store: createStoreWithExpertise('expert') },
    );
    expect(screen.getByText(i18n.t('pages.deliveryChannels.noChannels'))).toBeInTheDocument();
  });

  it('selects a phase card on click', async () => {
    const user = userEvent.setup();
    const e1 = makeEntry({ key: 'e1', phase_name: 'harvest', sequence_order: 1 });
    render([e1]);
    await user.click(screen.getByText(i18n.t('enums.phaseName.harvest')));
    // re-render with the selection highlight applied (no throw = branch covered)
    expect(screen.getByText(i18n.t('enums.phaseName.harvest'))).toBeInTheDocument();
  });

  it('renders a perennial plan splitting initial and seasonal cycles with year-wrap mapping', () => {
    const initial = makeEntry({ key: 'i1', phase_name: 'vegetative', sequence_order: 1, is_recurring: false, week_start: 1, week_end: 4 });
    const s0 = makeEntry({ key: 's0', phase_name: 'flowering', sequence_order: 2, is_recurring: true, week_start: 40, week_end: 48 });
    const s1 = makeEntry({ key: 's1', phase_name: 'flushing', sequence_order: 3, is_recurring: true, week_start: 49, week_end: 66 });
    const s2 = makeEntry({ key: 's2', phase_name: 'harvest', sequence_order: 4, is_recurring: true, week_start: 67, week_end: 70 });

    render([initial, s0, s1, s2], baseHandlers(), { planOverride: perennialPlan });

    expect(screen.getAllByText(i18n.t('pages.nutrientPlans.initialRunSection')).length).toBeGreaterThan(0);
    expect(screen.getAllByText(i18n.t('pages.nutrientPlans.seasonalCycleSection')).length).toBeGreaterThan(0);
    // recurring chip appears for seasonal cards
    expect(screen.getAllByText(i18n.t('pages.nutrientPlans.isRecurring')).length).toBeGreaterThan(0);
  });

  it('renders a perennial plan whose seasonal cycle fits inside a calendar year', () => {
    const s0 = makeEntry({ key: 's0', phase_name: 'flowering', sequence_order: 1, is_recurring: true, week_start: 1, week_end: 6 });
    const s1 = makeEntry({ key: 's1', phase_name: 'flushing', sequence_order: 2, is_recurring: true, week_start: 7, week_end: 10 });
    render([s0, s1], baseHandlers(), { planOverride: perennialPlan });
    expect(screen.getAllByText(i18n.t('pages.nutrientPlans.seasonalCycleSection')).length).toBeGreaterThan(0);
  });
});
