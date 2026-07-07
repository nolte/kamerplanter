import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import DeliveryChannelAccordion from '@/pages/duengung/DeliveryChannelAccordion';
import { renderWithProviders } from '@/test/helpers';
import type {
  DeliveryChannel,
  Fertilizer,
  FertilizerDosage,
  MethodParams,
  WateringSchedule,
} from '@/api/types';

/**
 * REQ-004 — DeliveryChannelAccordion is a pure, prop-driven presentation
 * component. These tests drive every rendering branch (method-params label
 * variants, schedule modes, EC/pH, disabled state, empty vs populated dosage
 * table, fertilizer-name resolution) and every optional callback.
 */

const fertilizers = [
  { key: 'fert-calmag', product_name: 'CalMag', brand: 'BioBizz' },
  { key: 'fert-base-a', product_name: 'Grow A', brand: 'Canna' },
] as unknown as Fertilizer[];

function dosage(overrides: Partial<FertilizerDosage> = {}): FertilizerDosage {
  return {
    fertilizer_key: 'fert-calmag',
    ml_per_liter: 1.5,
    optional: false,
    mixing_order: 1,
    ...overrides,
  };
}

function schedule(overrides: Partial<WateringSchedule> = {}): WateringSchedule {
  return {
    schedule_mode: 'interval',
    weekday_schedule: [],
    interval_days: 3,
    preferred_time: null,
    application_method: 'fertigation',
    reminder_hours_before: 2,
    times_per_day: 1,
    ...overrides,
  };
}

function channel(overrides: Partial<DeliveryChannel> = {}): DeliveryChannel {
  return {
    channel_id: 'ch-1',
    label: 'Haupttank',
    application_method: 'fertigation',
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

beforeEach(() => {
  i18n.changeLanguage('de');
});

describe('DeliveryChannelAccordion — rendering branches', () => {
  it('renders an enabled channel with EC, pH and fertigation method params', () => {
    const ch = channel({
      target_ec_ms: 1.2,
      target_ph: 5.8,
      method_params: {
        method: 'fertigation',
        runs_per_day: 3,
        duration_seconds: 120,
        flow_rate_ml_min: null,
      } as MethodParams,
      schedule: schedule({ schedule_mode: 'interval', interval_days: 3 }),
    });
    renderWithProviders(
      <DeliveryChannelAccordion channels={[ch]} fertilizers={fertilizers} />,
    );

    expect(screen.getByText('Haupttank')).toBeInTheDocument();
    expect(screen.getByText('EC: 1.2 mS')).toBeInTheDocument();
    expect(screen.getByText('pH: 5.8')).toBeInTheDocument();
    // 120s divisible by 60 → "2 min"
    expect(screen.getByText('3x/day, 2 min')).toBeInTheDocument();
    // interval schedule chip
    expect(screen.getByText('3d')).toBeInTheDocument();
  });

  it('formats sub-minute fertigation durations in seconds', () => {
    const ch = channel({
      method_params: {
        method: 'fertigation',
        runs_per_day: 2,
        duration_seconds: 45,
        flow_rate_ml_min: null,
      } as MethodParams,
    });
    renderWithProviders(
      <DeliveryChannelAccordion channels={[ch]} fertilizers={fertilizers} />,
    );
    expect(screen.getByText('2x/day, 45s')).toBeInTheDocument();
  });

  it('renders drench, foliar and top_dress (per-plant and per-m²) labels', () => {
    const channels = [
      channel({
        channel_id: 'ch-drench',
        label: 'Drench',
        method_params: { method: 'drench', volume_per_feeding_liters: 2 } as MethodParams,
      }),
      channel({
        channel_id: 'ch-foliar',
        label: 'Foliar',
        method_params: { method: 'foliar', volume_per_spray_liters: 0.5 } as MethodParams,
      }),
      channel({
        channel_id: 'ch-td-plant',
        label: 'TopPlant',
        method_params: {
          method: 'top_dress',
          grams_per_plant: 10,
          grams_per_m2: null,
        } as MethodParams,
      }),
      channel({
        channel_id: 'ch-td-m2',
        label: 'TopM2',
        method_params: {
          method: 'top_dress',
          grams_per_plant: null,
          grams_per_m2: 25,
        } as MethodParams,
      }),
      channel({
        channel_id: 'ch-td-none',
        label: 'TopNone',
        method_params: {
          method: 'top_dress',
          grams_per_plant: null,
          grams_per_m2: null,
        } as MethodParams,
      }),
    ];
    renderWithProviders(
      <DeliveryChannelAccordion channels={channels} fertilizers={fertilizers} />,
    );
    expect(screen.getByText('2 L')).toBeInTheDocument();
    expect(screen.getByText('0.5 L spray')).toBeInTheDocument();
    expect(screen.getByText('10 g/plant')).toBeInTheDocument();
    expect(screen.getByText('25 g/m²')).toBeInTheDocument();
    // top_dress with no grams renders no method-params label (no throw)
    expect(screen.getByText('TopNone')).toBeInTheDocument();
  });

  it('renders a disabled channel with a "disabled" chip and no log-watering button', () => {
    const ch = channel({ enabled: false, label: '' });
    renderWithProviders(
      <DeliveryChannelAccordion
        channels={[ch]}
        fertilizers={fertilizers}
        onLogWatering={vi.fn()}
      />,
    );
    // label falls back to channel_id
    expect(screen.getByText('ch-1')).toBeInTheDocument();
    // disabled channels never show the log-watering shortcut
    expect(screen.queryByTestId('log-watering-ch-1')).not.toBeInTheDocument();
  });

  it('renders the weekday schedule chip variant', () => {
    const ch = channel({
      schedule: schedule({ schedule_mode: 'weekdays', weekday_schedule: [1, 3, 5] }),
    });
    renderWithProviders(
      <DeliveryChannelAccordion channels={[ch]} fertilizers={fertilizers} />,
    );
    expect(screen.getByText(i18n.t('pages.wateringSchedule.weekdays'))).toBeInTheDocument();
  });

  it('shows the empty-state text when there are no dosages', () => {
    renderWithProviders(
      <DeliveryChannelAccordion channels={[channel()]} fertilizers={fertilizers} />,
    );
    expect(
      screen.getByText(i18n.t('pages.nutrientPlans.noFertilizers')),
    ).toBeInTheDocument();
  });

  it('resolves fertilizer names and falls back to the key for unknown fertilizers', () => {
    const ch = channel({
      notes: 'Silikat zuerst',
      fertilizer_dosages: [
        dosage({ fertilizer_key: 'fert-calmag', optional: false }),
        dosage({ fertilizer_key: 'unknown-key', optional: true }),
      ],
    });
    renderWithProviders(
      <DeliveryChannelAccordion channels={[ch]} fertilizers={fertilizers} />,
    );
    expect(screen.getByText('CalMag (BioBizz)')).toBeInTheDocument();
    // unknown fertilizer → raw key
    expect(screen.getByText('unknown-key')).toBeInTheDocument();
    // notes rendered
    expect(screen.getByText('Silikat zuerst')).toBeInTheDocument();
  });
});

describe('DeliveryChannelAccordion — callbacks', () => {
  it('fires onLogWatering without toggling the accordion (stopPropagation)', async () => {
    const onLogWatering = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(
      <DeliveryChannelAccordion
        channels={[channel()]}
        fertilizers={fertilizers}
        onLogWatering={onLogWatering}
      />,
    );
    await user.click(screen.getByTestId('log-watering-ch-1'));
    expect(onLogWatering).toHaveBeenCalledTimes(1);
    expect(onLogWatering.mock.calls[0][0].channel_id).toBe('ch-1');
  });

  it('fires channel edit/delete and fertilizer add/edit/remove callbacks', async () => {
    const onEditChannel = vi.fn();
    const onDeleteChannel = vi.fn();
    const onAddFertilizer = vi.fn();
    const onEditFertilizer = vi.fn();
    const onRemoveFertilizer = vi.fn();
    const user = userEvent.setup();

    const ch = channel({
      fertilizer_dosages: [dosage()],
    });
    renderWithProviders(
      <DeliveryChannelAccordion
        channels={[ch]}
        fertilizers={fertilizers}
        onEditChannel={onEditChannel}
        onDeleteChannel={onDeleteChannel}
        onAddFertilizer={onAddFertilizer}
        onEditFertilizer={onEditFertilizer}
        onRemoveFertilizer={onRemoveFertilizer}
      />,
    );

    // Expand the accordion so the detail action buttons are interactable.
    await user.click(screen.getByText('Haupttank'));

    // Channel-level edit / delete (two icon-buttons in the action row).
    await user.click(
      screen.getByRole('button', { name: i18n.t('pages.deliveryChannels.editChannel') }),
    );
    expect(onEditChannel).toHaveBeenCalledWith(expect.objectContaining({ channel_id: 'ch-1' }));

    await user.click(
      screen.getByRole('button', { name: i18n.t('pages.deliveryChannels.deleteChannel') }),
    );
    expect(onDeleteChannel).toHaveBeenCalledWith('ch-1');

    // "Add fertilizer" button
    await user.click(
      screen.getByRole('button', { name: i18n.t('pages.nutrientPlans.addFertilizer') }),
    );
    expect(onAddFertilizer).toHaveBeenCalledWith('ch-1');

    // Row-level edit / remove — scope to the dosage table row.
    const row = screen.getByText('CalMag (BioBizz)').closest('tr') as HTMLElement;
    const iconButtons = within(row).getAllByRole('button');
    await user.click(iconButtons[0]);
    expect(onEditFertilizer).toHaveBeenCalledWith('ch-1', expect.objectContaining({ fertilizer_key: 'fert-calmag' }));
    await user.click(iconButtons[1]);
    expect(onRemoveFertilizer).toHaveBeenCalledWith('ch-1', 'fert-calmag');
  });

  it('renders nothing for an empty channel list', () => {
    const { container } = renderWithProviders(
      <DeliveryChannelAccordion channels={[]} fertilizers={fertilizers} />,
    );
    expect(container.querySelectorAll('.MuiAccordion-root').length).toBe(0);
  });
});
