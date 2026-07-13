import { useState } from 'react';
import { screen, waitFor, fireEvent, within } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import type { CareProfile } from '@/api/types';
import CareProfileForm from '@/pages/pflege/components/CareProfileForm';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

function makeCareProfile(overrides: Partial<CareProfile> = {}): CareProfile {
  return {
    key: 'cp-1',
    care_style: 'tropical',
    watering_interval_days: 7,
    winter_watering_multiplier: 1.0,
    watering_method: 'top_water',
    water_quality_hint: null,
    fertilizing_interval_days: 14,
    fertilizing_active_months: [3, 4, 5, 6, 7, 8, 9],
    repotting_interval_months: 12,
    pest_check_interval_days: 7,
    location_check_enabled: false,
    location_check_months: [],
    humidity_check_enabled: false,
    humidity_check_interval_days: 3,
    adaptive_learning_enabled: false,
    auto_create_watering_task: true,
    auto_create_fertilizing_task: true,
    auto_create_repotting_task: false,
    auto_create_pest_check_task: false,
    watering_interval_learned: null,
    fertilizing_interval_learned: null,
    notes: null,
    auto_generated: true,
    plant_key: 'pi-1',
    created_at: '2024-06-01T00:00:00Z',
    updated_at: null,
    ...overrides,
  };
}

const QUERY_TIMEOUT = { timeout: 5000 } as const;

describe('CareProfileForm', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('de');
  });

  it('saves the profile via careApi.updateProfile and reports the update to the host', async () => {
    const profile = makeCareProfile();
    const saved = makeCareProfile({ care_style: 'succulent' });
    let patched = false;
    server.use(
      http.patch('/api/v1/care-reminders/plants/:key/profile', () => {
        patched = true;
        return HttpResponse.json(saved);
      }),
    );

    const onUpdated = vi.fn();
    const onDone = vi.fn();
    renderWithProviders(
      <CareProfileForm profile={profile} onUpdated={onUpdated} onDone={onDone} embedded />,
    );

    fireEvent.click(screen.getByTestId('save-profile-button'));

    await waitFor(() => expect(patched).toBe(true), QUERY_TIMEOUT);
    await waitFor(() => expect(onUpdated).toHaveBeenCalledWith(saved), QUERY_TIMEOUT);
    expect(onDone).toHaveBeenCalledTimes(1);
  });

  it('resets the profile via careApi.resetProfile after confirmation and refreshes the host state', async () => {
    const profile = makeCareProfile({ care_style: 'custom' });
    const reset = makeCareProfile({ care_style: 'tropical' });
    let didReset = false;
    server.use(
      http.post('/api/v1/care-reminders/plants/:key/reset-profile', () => {
        didReset = true;
        return HttpResponse.json(reset);
      }),
    );

    const onUpdated = vi.fn();
    renderWithProviders(<CareProfileForm profile={profile} onUpdated={onUpdated} embedded />);

    // Reset is destructive, so clicking it only opens the confirmation dialog;
    // the API call fires from the dialog's confirm action.
    fireEvent.click(screen.getByTestId('reset-profile-button'));
    expect(didReset).toBe(false);
    await screen.findByTestId('confirm-dialog', {}, QUERY_TIMEOUT);
    fireEvent.click(screen.getByTestId('confirm-dialog-confirm'));

    await waitFor(() => expect(didReset).toBe(true), QUERY_TIMEOUT);
    await waitFor(() => expect(onUpdated).toHaveBeenCalledWith(reset), QUERY_TIMEOUT);
  });

  it('cancelling the reset confirmation leaves the profile untouched', async () => {
    let didReset = false;
    server.use(
      http.post('/api/v1/care-reminders/plants/:key/reset-profile', () => {
        didReset = true;
        return HttpResponse.json(makeCareProfile());
      }),
    );

    renderWithProviders(
      <CareProfileForm profile={makeCareProfile()} onUpdated={vi.fn()} embedded />,
    );

    fireEvent.click(screen.getByTestId('reset-profile-button'));
    await screen.findByTestId('confirm-dialog', {}, QUERY_TIMEOUT);
    fireEvent.click(screen.getByTestId('confirm-dialog-cancel'));

    await waitFor(() => expect(screen.queryByTestId('confirm-dialog')).toBeNull(), QUERY_TIMEOUT);
    expect(didReset).toBe(false);
  });

  it('shows an unsaved-changes hint once a field is edited and clears it once the saved profile round-trips back in', async () => {
    const profile = makeCareProfile();
    const saved = makeCareProfile({ care_style: 'succulent' });
    server.use(
      http.patch('/api/v1/care-reminders/plants/:key/profile', () => HttpResponse.json(saved)),
    );

    // A minimal stateful host, matching how the real embedding page feeds the
    // saved profile back in via `onUpdated` — that round-trip is what clears
    // the dirty state (the profile prop and the local baseline both change).
    function Host() {
      const [current, setCurrent] = useState(profile);
      return <CareProfileForm profile={current} onUpdated={setCurrent} embedded />;
    }

    renderWithProviders(<Host />);

    expect(screen.queryByTestId('care-profile-dirty-hint')).toBeNull();

    const combobox = within(screen.getByTestId('care-style-select')).getByRole('combobox');
    fireEvent.mouseDown(combobox);
    fireEvent.click(await screen.findByRole('option', { name: i18n.t('enums.careStyle.succulent') }));

    await waitFor(() => expect(screen.getByTestId('care-profile-dirty-hint')).toBeTruthy());

    fireEvent.click(screen.getByTestId('save-profile-button'));

    await waitFor(() => expect(screen.queryByTestId('care-profile-dirty-hint')).toBeNull(), QUERY_TIMEOUT);
  });

  it('omits the Cancel action for the inline (embedded) placement', () => {
    renderWithProviders(
      <CareProfileForm profile={makeCareProfile()} onUpdated={vi.fn()} embedded />,
    );
    // Inline placement is always-editable: Save + Reset, no cancel affordance.
    expect(screen.queryByTestId('cancel-button')).toBeNull();
    expect(screen.getByTestId('save-profile-button')).toBeTruthy();
    expect(screen.getByTestId('reset-profile-button')).toBeTruthy();
  });

  it('renders a Cancel action when onCancel is supplied (dialog usage)', () => {
    renderWithProviders(
      <CareProfileForm profile={makeCareProfile()} onUpdated={vi.fn()} onCancel={vi.fn()} />,
    );
    expect(screen.getByTestId('cancel-button')).toBeTruthy();
  });
});
