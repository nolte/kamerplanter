import { screen, within, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import GrowthPhaseListSection from '@/pages/pflanzen/GrowthPhaseListSection';
import { createPlatformAdminStore, renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

/**
 * Every case below drives or inspects an installation-wide catalogue whose writes
 * carry `require_platform_admin` since #1402 C, so the suite acts as a platform
 * admin. The non-admin half of the contract — reads still render, write
 * affordances are gone — is asserted in this same file, beside its admin
 * counterpart, so the pair cannot drift apart.
 */
const renderAsAdmin = (ui: Parameters<typeof renderWithProviders>[0]) =>
  renderWithProviders(ui, { store: createPlatformAdminStore() });


function phaseDefinition(name: string, displayNameDe: string) {
  return {
    key: `def-${name}`,
    name,
    display_name: name,
    display_name_de: displayNameDe,
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
  };
}

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
      override_duration_days: 10,
      effective_duration_days: 10,
      is_terminal: false,
      allows_harvest: false,
      is_recurring: false,
      phase_definition: phaseDefinition('vegetative', 'Wachstum'),
      created_at: '2024-01-01T00:00:00Z',
      updated_at: null,
    },
    {
      key: 'entry-harvest',
      phase_sequence_key: 'seq-1',
      phase_definition_key: 'def-harvest',
      sequence_order: 2,
      override_duration_days: null,
      effective_duration_days: 45,
      is_terminal: true,
      allows_harvest: true,
      is_recurring: false,
      phase_definition: phaseDefinition('harvest', 'Ernte'),
      created_at: '2024-01-01T00:00:00Z',
      updated_at: null,
    },
  ],
  created_at: '2024-01-01T00:00:00Z',
  updated_at: null,
};

describe('GrowthPhaseListSection', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders legacy growth phases with a create button and a helper legend', async () => {
    renderAsAdmin(<GrowthPhaseListSection lifecycleKey="lc-sp-1" />);

    expect(
      await screen.findByText(i18n.t('pages.growthPhases.title')),
    ).toBeTruthy();
    // Default handler returns vegetative + flowering.
    expect(await screen.findByText('Vegetativ')).toBeTruthy();
    expect(screen.getByText('Blüte')).toBeTruthy();
    // Create button present in legacy (unmanaged) mode.
    expect(
      screen.getByRole('button', { name: i18n.t('pages.growthPhases.create') }),
    ).toBeTruthy();
    // Legend surfaces the terminal + harvest explanations for the flowering row.
    expect(
      screen.getByText(i18n.t('pages.growthPhases.isTerminalHelper')),
    ).toBeTruthy();
    expect(
      screen.getByText(i18n.t('pages.growthPhases.allowsHarvestHelper')),
    ).toBeTruthy();
  });

  it('opens the create dialog when the create button is clicked', async () => {
    const user = userEvent.setup();
    renderAsAdmin(<GrowthPhaseListSection lifecycleKey="lc-sp-1" />);

    await screen.findByText('Vegetativ');
    await user.click(
      screen.getByRole('button', { name: i18n.t('pages.growthPhases.create') }),
    );

    // GrowthPhaseDialog mounts as an open dialog.
    expect(await screen.findByRole('dialog')).toBeTruthy();
  });

  it('opens the edit dialog when a legacy row is clicked', async () => {
    const user = userEvent.setup();
    renderAsAdmin(<GrowthPhaseListSection lifecycleKey="lc-sp-1" />);

    await screen.findByText('Vegetativ');
    await user.click(screen.getAllByTestId('data-table-row')[0]);

    expect(await screen.findByRole('dialog')).toBeTruthy();
  });

  it('filters the legacy rows via the table search', async () => {
    const user = userEvent.setup();
    renderAsAdmin(<GrowthPhaseListSection lifecycleKey="lc-sp-1" />);

    await screen.findByText('Vegetativ');
    const search = screen
      .getByTestId('table-search-input')
      .querySelector('input') as HTMLInputElement;
    // Typing runs every column's searchValue closure across all rows. "60"
    // matches only the flowering row's duration (60d), not the 30d vegetative row.
    await user.type(search, '60');

    await waitFor(() => expect(screen.queryByText('Vegetativ')).toBeNull());
    expect(screen.getByText('Blüte')).toBeTruthy();
  });

  it('deletes a legacy phase after confirmation', async () => {
    let deletedKey: string | null = null;
    server.use(
      http.delete('/api/v1/growth-phases/:key', ({ params }) => {
        deletedKey = params.key as string;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const user = userEvent.setup();
    renderAsAdmin(<GrowthPhaseListSection lifecycleKey="lc-sp-1" />);

    await screen.findByText('Vegetativ');
    // First delete icon belongs to the vegetative row (sorted by order).
    await user.click(screen.getAllByLabelText(i18n.t('common.delete'))[0]);

    const confirm = await screen.findByTestId('confirm-dialog');
    await user.click(
      within(confirm).getByTestId('confirm-dialog-confirm'),
    );

    await waitFor(() => expect(deletedKey).toBe('gp-veg'));
    await waitFor(() =>
      expect(screen.queryByTestId('confirm-dialog')).toBeNull(),
    );
  });

  it('cancels the delete confirmation without removing a phase', async () => {
    let deleted = false;
    server.use(
      http.delete('/api/v1/growth-phases/:key', () => {
        deleted = true;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const user = userEvent.setup();
    renderAsAdmin(<GrowthPhaseListSection lifecycleKey="lc-sp-1" />);

    await screen.findByText('Vegetativ');
    await user.click(screen.getAllByLabelText(i18n.t('common.delete'))[0]);

    const confirm = await screen.findByTestId('confirm-dialog');
    await user.click(within(confirm).getByTestId('confirm-dialog-cancel'));

    await waitFor(() =>
      expect(screen.queryByTestId('confirm-dialog')).toBeNull(),
    );
    expect(deleted).toBe(false);
    expect(screen.getByText('Vegetativ')).toBeTruthy();
  });

  it('renders a managed sequence read-only with the info alert and override chip', async () => {
    server.use(
      http.get('/api/v1/phase-sequences/:key', () =>
        HttpResponse.json(managedSequence),
      ),
    );
    renderAsAdmin(
      <GrowthPhaseListSection
        lifecycleKey="lc-sp-1"
        phaseSequenceKey="seq-1"
        phaseSequenceName="Mein Ablauf"
      />,
    );

    // Managed info alert with the sequence link.
    expect(
      await screen.findByText(i18n.t('pages.phases.managedBySequence')),
    ).toBeTruthy();
    expect(
      screen.getByRole('link', { name: 'Mein Ablauf' }),
    ).toBeTruthy();
    // German display name from phase_definition.display_name_de.
    expect(await screen.findByText('Wachstum')).toBeTruthy();
    expect(screen.getByText('Ernte')).toBeTruthy();
    // No create button in managed mode.
    expect(
      screen.queryByRole('button', {
        name: i18n.t('pages.growthPhases.create'),
      }),
    ).toBeNull();
    // Override indicator (override_duration_days set) appears with its legend.
    expect(
      screen.getAllByText(i18n.t('pages.phaseSequences.overrideIndicator')).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText(i18n.t('pages.growthPhases.overriddenHelper')),
    ).toBeTruthy();
  });

  it('handles a failed load without crashing', async () => {
    server.use(
      http.get('/api/v1/growth-phases', () =>
        HttpResponse.json({ message: 'boom' }, { status: 500 }),
      ),
    );
    renderAsAdmin(<GrowthPhaseListSection lifecycleKey="lc-sp-1" />);

    // Title still renders; the table falls back to its empty state.
    expect(
      await screen.findByText(i18n.t('pages.growthPhases.title')),
    ).toBeTruthy();
    await waitFor(() => expect(screen.queryByText('Vegetativ')).toBeNull());
  });

  /**
   * The non-admin half of #1402 C, asserted beside its admin counterpart rather
   * than in a file of its own so the pair cannot drift apart.
   *
   * `POST/PUT/DELETE /growth-phases` answers 403 for everyone below platform
   * admin, so the affordances that call it are gone. What must NOT be gone is the
   * read — the table and the profile button beside it — which is why every case
   * here asserts a surviving read in the same breath as the missing write. An
   * assertion that only counted absences would also pass on a blank render.
   */
  describe('a caller who is not a platform admin', () => {
    it('still reads the phase table but is offered no create, edit or delete', async () => {
      renderWithProviders(<GrowthPhaseListSection lifecycleKey="lc-sp-1" />);

      // The read survives — this is the control that makes the absences mean something.
      expect(await screen.findByText('Vegetativ')).toBeTruthy();
      expect(screen.getAllByTestId(/^phase-profile-/).length).toBeGreaterThan(0);

      expect(screen.queryByText(i18n.t('pages.growthPhases.create'))).toBeNull();
      expect(screen.queryAllByLabelText(i18n.t('common.delete'))).toHaveLength(0);
    });

    it('does not open the edit dialog when a row is clicked', async () => {
      const user = userEvent.setup();
      renderWithProviders(<GrowthPhaseListSection lifecycleKey="lc-sp-1" />);

      await user.click(await screen.findByText('Vegetativ'));

      // Asserted on the dialog, not on a mutation spy: the dialog is what a
      // non-admin would otherwise fill in before the save answers 403.
      await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
    });
  });
});
