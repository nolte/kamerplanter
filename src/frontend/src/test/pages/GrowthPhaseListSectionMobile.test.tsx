import { screen, within, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

// Force the mobile breakpoint so DataTable uses the mobileCardRenderer branch.
vi.mock('@mui/material/useMediaQuery', () => ({ default: () => true }));

// Import after the mock so the mocked useMediaQuery is picked up.
import GrowthPhaseListSection from '@/pages/pflanzen/GrowthPhaseListSection';

const managedSequence = {
  key: 'seq-1',
  name: 'seq',
  display_name: 'Seq',
  display_name_de: 'Ablauf',
  description: '',
  description_de: '',
  species_key: 'sp-1',
  cycle_type: 'annual',
  is_repeating: false,
  cycle_restart_entry_order: null,
  typical_lifespan_years: null,
  dormancy_required: false,
  vernalization_required: false,
  vernalization_min_days: null,
  photoperiod_type: 'day_neutral',
  critical_day_length_hours: null,
  is_system: true,
  tags: [],
  entries: [
    {
      key: 'entry-veg',
      phase_sequence_key: 'seq-1',
      phase_definition_key: 'def-vegetative',
      sequence_order: 1,
      override_duration_days: null,
      effective_duration_days: 30,
      is_terminal: false,
      allows_harvest: false,
      is_recurring: false,
      phase_definition: {
        key: 'def-vegetative',
        name: 'vegetative',
        display_name: 'vegetative',
        display_name_de: 'Wachstum',
        description: '',
        description_de: '',
        typical_duration_days: 30,
        stress_tolerance: 'medium',
        watering_interval_days: 5,
        illustration: '',
        tags: [],
        is_system: true,
        usage_count: 0,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: null,
      },
      created_at: '2024-01-01T00:00:00Z',
      updated_at: null,
    },
  ],
  created_at: '2024-01-01T00:00:00Z',
  updated_at: null,
};

describe('GrowthPhaseListSection — mobile card actions', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('de');
  });

  it('offers the profile and delete actions on the mobile card', async () => {
    renderWithProviders(<GrowthPhaseListSection lifecycleKey="lc-sp-1" />);

    const cards = await screen.findByTestId('data-table-cards');
    const firstRow = within(cards).getAllByTestId('data-table-row')[0];

    // Regression guard: the mobile card renderer had no `trailing`, so below the
    // `sm` breakpoint a growth phase could neither be deleted nor have its
    // profile opened — the actions existed only in the desktop table.
    expect(within(firstRow).getByTestId('phase-profile-gp-veg')).toBeInTheDocument();
    const deleteButton = within(firstRow).getByTestId('phase-delete-gp-veg');
    expect(deleteButton).toHaveAttribute('aria-label', i18n.t('common.delete'));
  });

  it('deletes a phase from the mobile card without opening the edit dialog', async () => {
    let deletedKey: string | null = null;
    server.use(
      http.delete('/api/v1/growth-phases/:key', ({ params }) => {
        deletedKey = params.key as string;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<GrowthPhaseListSection lifecycleKey="lc-sp-1" />);

    await screen.findByTestId('data-table-cards');
    await user.click(screen.getByTestId('phase-delete-gp-veg'));

    // The card itself is clickable (it opens the edit dialog); the action must
    // not bubble into it.
    const confirm = await screen.findByTestId('confirm-dialog');
    await user.click(within(confirm).getByTestId('confirm-dialog-confirm'));

    await waitFor(() => expect(deletedKey).toBe('gp-veg'));
  });

  it('opens the phase profile from the mobile card', async () => {
    const user = userEvent.setup();
    renderWithProviders(<GrowthPhaseListSection lifecycleKey="lc-sp-1" />);

    await screen.findByTestId('data-table-cards');
    await user.click(screen.getByTestId('phase-profile-gp-veg'));

    // ProfilesSection renders under the list once a phase is selected; its
    // heading is "<phase> — Profil".
    expect(
      await screen.findByText(`Vegetativ — ${i18n.t('entities.profile')}`),
    ).toBeInTheDocument();
    // The action must not bubble into the card's own edit-dialog click handler.
    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it('hides the row actions for a sequence-managed phase', async () => {
    server.use(
      http.get('/api/v1/phase-sequences/:key', () => HttpResponse.json(managedSequence)),
    );
    renderWithProviders(
      <GrowthPhaseListSection lifecycleKey="lc-sp-1" phaseSequenceKey="seq-1" phaseSequenceName="Mein Ablauf" />,
    );

    await screen.findByText('Wachstum');
    // Managed phases are read-only in both views.
    expect(screen.queryByTestId('phase-delete-entry-veg')).toBeNull();
    expect(screen.queryByTestId('phase-profile-entry-veg')).toBeNull();
  });
});
