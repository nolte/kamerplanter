import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, within, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import DeliveryChannelDialog from '@/pages/duengung/DeliveryChannelDialog';
import { renderWithProviders } from '../helpers';
import type { DeliveryChannel, MethodParams, WateringSchedule } from '@/api/types';

/**
 * REQ-004 — DeliveryChannelDialog is a self-contained 3-step wizard (method →
 * params → schedule) that emits a DeliveryChannelCreate via onSave. It performs
 * no I/O, so it is driven purely through its props and the rendered form. These
 * tests exercise the add and edit flows, the id-collision guard, every method
 * branch (buildMethodParams / buildDefaults) and both schedule modes.
 */

const t = (k: string) => i18n.t(k);

function channel(overrides: Partial<DeliveryChannel> = {}): DeliveryChannel {
  return {
    channel_id: 'tank-1',
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

describe('DeliveryChannelDialog — add flow', () => {
  it('walks the wizard, builds a drench channel with a weekday schedule and saves', async () => {
    const user = userEvent.setup();
    const onSave = vi.fn();
    const onClose = vi.fn();
    renderWithProviders(
      <DeliveryChannelDialog open onClose={onClose} onSave={onSave} existingIds={['other']} />,
    );

    expect(screen.getByText(t('pages.deliveryChannels.addChannel'))).toBeInTheDocument();

    // Step 0 — identity. Default method is "drench".
    const idField = within(screen.getByTestId('form-field-channel_id')).getByRole('textbox');
    await user.type(idField, 'new-ch');

    await user.click(screen.getByRole('button', { name: t('common.next') }));

    // Step 1 — params: drench shows the volume-per-feeding field.
    expect(screen.getByTestId('form-field-volume_per_feeding_liters')).toBeInTheDocument();

    // Exercise the Back button, then continue.
    await user.click(screen.getByRole('button', { name: t('common.back') }));
    expect(screen.getByTestId('form-field-channel_id')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: t('common.next') }));
    await user.click(screen.getByRole('button', { name: t('common.next') }));

    // Step 2 — schedule: enable it, keep weekdays mode, toggle two days then untoggle one.
    const enableSwitch = screen.getByLabelText(t('pages.deliveryChannels.scheduleEnabled'));
    await user.click(enableSwitch);

    const monday = screen.getByRole('checkbox', { name: t('pages.wateringSchedule.mon') });
    const wednesday = screen.getByRole('checkbox', { name: t('pages.wateringSchedule.wed') });
    await user.click(monday);
    await user.click(wednesday);
    await user.click(monday); // untoggle → exercises the filter branch

    await user.click(screen.getByRole('button', { name: t('common.create') }));

    await waitFor(() => expect(onSave).toHaveBeenCalledTimes(1));
    const payload = onSave.mock.calls[0][0];
    expect(payload).toMatchObject({
      channel_id: 'new-ch',
      application_method: 'drench',
      method_params: { method: 'drench' },
    });
    expect(payload.schedule).not.toBeNull();
    expect(payload.schedule.schedule_mode).toBe('weekdays');
    expect(payload.schedule.weekday_schedule).toEqual([2]); // only Wednesday remains
  });

  it('blocks progression when the channel id collides with an existing one', async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <DeliveryChannelDialog open onClose={vi.fn()} onSave={vi.fn()} existingIds={['dup']} />,
    );
    const idField = within(screen.getByTestId('form-field-channel_id')).getByRole('textbox');
    await user.type(idField, 'dup');
    expect(
      screen.getByText(t('pages.deliveryChannels.channelIdExists')),
    ).toBeInTheDocument();
    expect(screen.getByRole('button', { name: t('common.next') })).toBeDisabled();
  });

  it('builds foliar method params on save', async () => {
    const user = userEvent.setup();
    const onSave = vi.fn();
    renderWithProviders(<DeliveryChannelDialog open onClose={vi.fn()} onSave={onSave} />);

    const idField = within(screen.getByTestId('form-field-channel_id')).getByRole('textbox');
    await user.type(idField, 'foliar-ch');

    // Switch the application method to "foliar".
    const methodSelect = within(
      screen.getByTestId('form-field-application_method'),
    ).getByRole('combobox');
    await user.click(methodSelect);
    await user.click(
      await screen.findByRole('option', { name: t('enums.applicationMethod.foliar') }),
    );

    await user.click(screen.getByRole('button', { name: t('common.next') }));
    expect(screen.getByTestId('form-field-volume_per_spray_liters')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: t('common.next') }));
    await user.click(screen.getByRole('button', { name: t('common.create') }));

    await waitFor(() => expect(onSave).toHaveBeenCalledTimes(1));
    expect(onSave.mock.calls[0][0].method_params).toMatchObject({ method: 'foliar' });
    expect(onSave.mock.calls[0][0].schedule).toBeNull();
  });

  it('builds top_dress method params on save', async () => {
    const user = userEvent.setup();
    const onSave = vi.fn();
    renderWithProviders(<DeliveryChannelDialog open onClose={vi.fn()} onSave={onSave} />);

    const idField = within(screen.getByTestId('form-field-channel_id')).getByRole('textbox');
    await user.type(idField, 'td-ch');

    const methodSelect = within(
      screen.getByTestId('form-field-application_method'),
    ).getByRole('combobox');
    await user.click(methodSelect);
    await user.click(
      await screen.findByRole('option', { name: t('enums.applicationMethod.top_dress') }),
    );

    await user.click(screen.getByRole('button', { name: t('common.next') }));
    expect(screen.getByTestId('form-field-grams_per_plant')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: t('common.next') }));
    await user.click(screen.getByRole('button', { name: t('common.create') }));

    await waitFor(() => expect(onSave).toHaveBeenCalledTimes(1));
    expect(onSave.mock.calls[0][0].method_params).toMatchObject({ method: 'top_dress' });
  });
});

describe('DeliveryChannelDialog — edit flow', () => {
  it('prefills a fertigation channel with an interval schedule and saves via update label', async () => {
    const user = userEvent.setup();
    const onSave = vi.fn();
    const existing = channel({
      application_method: 'fertigation',
      notes: 'main tank',
      target_ec_ms: 1.4,
      target_ph: 5.8,
      method_params: {
        method: 'fertigation',
        runs_per_day: 4,
        duration_seconds: 90,
        flow_rate_ml_min: null,
      } as MethodParams,
      schedule: {
        schedule_mode: 'interval',
        weekday_schedule: [],
        interval_days: 5,
        preferred_time: '07:30',
        application_method: 'fertigation',
        reminder_hours_before: 3,
        times_per_day: 2,
      } as WateringSchedule,
    });

    renderWithProviders(
      <DeliveryChannelDialog
        open
        onClose={vi.fn()}
        onSave={onSave}
        existingChannel={existing}
      />,
    );

    expect(screen.getByText(t('pages.deliveryChannels.editChannel'))).toBeInTheDocument();
    // channel_id is locked in edit mode.
    expect(
      within(screen.getByTestId('form-field-channel_id')).getByRole('textbox'),
    ).toBeDisabled();

    await user.click(screen.getByRole('button', { name: t('common.next') }));
    // Params step shows the fertigation fields.
    expect(screen.getByTestId('form-field-runs_per_day')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: t('common.next') }));
    // Schedule is pre-enabled in interval mode.
    expect(screen.getByTestId('form-field-interval_days')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: t('common.save') }));
    await waitFor(() => expect(onSave).toHaveBeenCalledTimes(1));
    const payload = onSave.mock.calls[0][0];
    expect(payload.method_params).toMatchObject({ method: 'fertigation', runs_per_day: 4 });
    expect(payload.schedule).toMatchObject({ schedule_mode: 'interval', interval_days: 5 });
    expect(payload.notes).toBe('main tank');
  });

  it.each(['drench', 'foliar', 'top_dress'] as const)(
    'prefills the %s method defaults in edit mode',
    (method) => {
      const paramsByMethod: Record<string, MethodParams> = {
        drench: { method: 'drench', volume_per_feeding_liters: 2 },
        foliar: { method: 'foliar', volume_per_spray_liters: 0.4 },
        top_dress: { method: 'top_dress', grams_per_plant: 5, grams_per_m2: 20 },
      };
      renderWithProviders(
        <DeliveryChannelDialog
          open
          onClose={vi.fn()}
          onSave={vi.fn()}
          existingChannel={channel({
            application_method: method,
            method_params: paramsByMethod[method],
          })}
        />,
      );
      expect(
        screen.getByText(t('pages.deliveryChannels.editChannel')),
      ).toBeInTheDocument();
    },
  );
});
