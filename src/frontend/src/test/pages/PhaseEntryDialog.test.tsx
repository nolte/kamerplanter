import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import type { NutrientPlanPhaseEntry } from '@/api/types';

/**
 * REQ-004 — PhaseEntryDialog is the create/edit form for a nutrient-plan phase
 * entry. It talks to the nutrient-plan API on submit, so those endpoints are
 * doubled at the boundary; the WaterMixRecommendationBox child (which makes its
 * own request) is stubbed so only this component's behaviour is exercised.
 * These tests cover the add and edit branches, the schedule-override toggle,
 * the multi-channel info alert, the site-driven recommendation branch and the
 * error path.
 */

const createPhaseEntry = vi.fn();
const updatePhaseEntry = vi.fn();
vi.mock('@/api/endpoints/nutrient-plans', () => ({
  createPhaseEntry: (...args: unknown[]) => createPhaseEntry(...args),
  updatePhaseEntry: (...args: unknown[]) => updatePhaseEntry(...args),
}));

vi.mock('@/pages/duengung/WaterMixRecommendationBox', () => ({
  default: () => <div data-testid="water-mix-box-stub" />,
}));

import PhaseEntryDialog from '@/pages/duengung/PhaseEntryDialog';
import { renderWithProviders } from '../helpers';

const t = (k: string) => i18n.t(k);

function entry(overrides: Partial<NutrientPlanPhaseEntry> = {}): NutrientPlanPhaseEntry {
  return {
    key: 'e-1',
    plan_key: 'plan-1',
    phase_name: 'vegetative',
    sequence_order: 2,
    week_start: 3,
    week_end: 6,
    is_recurring: true,
    npk_ratio: [3, 1, 2],
    calcium_ppm: 40,
    magnesium_ppm: 15,
    target_ec_ms: null,
    reference_ec_ms: null,
    target_calcium_ppm: null,
    target_magnesium_ppm: null,
    reference_base_ec: 0,
    notes: 'grow phase',
    delivery_channels: [],
    watering_schedule_override: null,
    water_mix_ratio_ro_percent: 20,
    created_at: null,
    updated_at: null,
    ...overrides,
  };
}

beforeEach(() => {
  i18n.changeLanguage('de');
  createPhaseEntry.mockReset().mockResolvedValue({});
  updatePhaseEntry.mockReset().mockResolvedValue({});
});

describe('PhaseEntryDialog — add mode', () => {
  it('submits a new phase entry with a null schedule override and reports saved', async () => {
    const user = userEvent.setup();
    const onSaved = vi.fn();
    renderWithProviders(
      <PhaseEntryDialog open onClose={vi.fn()} planKey="plan-1" onSaved={onSaved} />,
    );

    expect(screen.getByText(t('pages.nutrientPlans.addEntry'))).toBeInTheDocument();

    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => expect(createPhaseEntry).toHaveBeenCalledTimes(1));
    const [planKey, payload] = createPhaseEntry.mock.calls[0];
    expect(planKey).toBe('plan-1');
    expect(payload.phase_name).toBe('germination');
    expect(payload.npk_ratio).toEqual([0, 0, 0]);
    expect(payload.watering_schedule_override).toBeNull();
    expect(updatePhaseEntry).not.toHaveBeenCalled();
    expect(onSaved).toHaveBeenCalledTimes(1);
  });

  it('builds an interval schedule override when the toggle is enabled', async () => {
    const user = userEvent.setup();
    const onSaved = vi.fn();
    renderWithProviders(
      <PhaseEntryDialog open onClose={vi.fn()} planKey="plan-1" onSaved={onSaved} />,
    );

    await user.click(
      screen.getByLabelText(t('pages.nutrientPlans.wateringScheduleOverride')),
    );
    const intervalField = within(
      screen.getByTestId('form-field-override_interval_days'),
    ).getByRole('spinbutton');
    await user.clear(intervalField);
    await user.type(intervalField, '4');

    await user.click(screen.getByTestId('form-submit-button'));
    await waitFor(() => expect(createPhaseEntry).toHaveBeenCalledTimes(1));
    expect(createPhaseEntry.mock.calls[0][1].watering_schedule_override).toMatchObject({
      schedule_mode: 'interval',
      interval_days: 4,
    });
  });
});

describe('PhaseEntryDialog — edit mode', () => {
  it('prefills the entry, shows the multi-channel alert and calls the update endpoint', async () => {
    const user = userEvent.setup();
    const onSaved = vi.fn();
    const existing = entry({
      watering_schedule_override: {
        schedule_mode: 'interval',
        weekday_schedule: [],
        interval_days: 7,
        preferred_time: '09:00',
        application_method: 'drench',
        reminder_hours_before: 2,
        times_per_day: 1,
      },
      delivery_channels: [
        {
          channel_id: 'c1',
          label: 'Tank',
          application_method: 'fertigation',
          enabled: true,
          notes: null,
          schedule: null,
          target_ec_ms: null,
          target_ph: null,
          fertilizer_dosages: [],
          method_params: null,
        },
      ],
    });

    renderWithProviders(
      <PhaseEntryDialog
        open
        onClose={vi.fn()}
        planKey="plan-1"
        entry={existing}
        onSaved={onSaved}
      />,
    );

    expect(screen.getByText(t('pages.nutrientPlans.editEntry'))).toBeInTheDocument();
    // Multi-channel info alert is rendered for entries with delivery channels.
    expect(
      screen.getByText(t('pages.deliveryChannels.multiChannelActive')),
    ).toBeInTheDocument();
    // Override is pre-enabled → the interval field is visible with the prefilled value.
    expect(screen.getByDisplayValue('7')).toBeInTheDocument();

    await user.click(screen.getByTestId('form-submit-button'));
    await waitFor(() => expect(updatePhaseEntry).toHaveBeenCalledTimes(1));
    const [planKey, entryKey, payload] = updatePhaseEntry.mock.calls[0];
    expect(planKey).toBe('plan-1');
    expect(entryKey).toBe('e-1');
    expect(payload.npk_ratio).toEqual([3, 1, 2]);
    expect(onSaved).toHaveBeenCalledTimes(1);
  });
});

describe('PhaseEntryDialog — site recommendation & errors', () => {
  it('renders the water-mix recommendation box when a site is provided', () => {
    renderWithProviders(
      <PhaseEntryDialog
        open
        onClose={vi.fn()}
        planKey="plan-1"
        onSaved={vi.fn()}
        siteKey="site-1"
        substrateType="soil"
      />,
    );
    expect(screen.getByTestId('water-mix-box-stub')).toBeInTheDocument();
  });

  it('does not report saved when the API rejects', async () => {
    const user = userEvent.setup();
    const onSaved = vi.fn();
    createPhaseEntry.mockRejectedValueOnce(new Error('boom'));
    renderWithProviders(
      <PhaseEntryDialog open onClose={vi.fn()} planKey="plan-1" onSaved={onSaved} />,
    );
    await user.click(screen.getByTestId('form-submit-button'));
    await waitFor(() => expect(createPhaseEntry).toHaveBeenCalledTimes(1));
    expect(onSaved).not.toHaveBeenCalled();
  });
});
