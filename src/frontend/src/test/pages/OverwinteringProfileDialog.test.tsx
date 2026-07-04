import { screen, within, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import OverwinteringProfileDialog from '@/pages/ueberwinterung/OverwinteringProfileDialog';
import type { OverwinteringProfile, PlantInstance } from '@/api/types';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

const plant = {
  key: 'plant-1',
  instance_id: 'TOM-001',
  plant_name: 'Big Red',
} as unknown as PlantInstance;

const digStoreProfile = {
  key: 'ow-9',
  plant_key: null,
  planting_run_key: 'run-1',
  hardiness_zone_min: '6a',
  hardiness_rating: 'dig_and_store',
  winter_action: 'dig_store',
  winter_action_month: 10,
  spring_action: 'replant',
  spring_action_month: 4,
  winter_quarter_key: null,
  winter_quarter_temp_min: 4,
  winter_quarter_temp_max: 8,
  winter_quarter_light: 'dark',
  winter_watering: 'none',
  storage_medium: 'Sand',
  storage_check_interval_days: 30,
  tuber_status: 'stored',
  notes: 'Dahlien',
  auto_generated: false,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: null,
} as unknown as OverwinteringProfile;

function openCreateDialog() {
  const onSaved = vi.fn();
  renderWithProviders(
    <OverwinteringProfileDialog
      open
      onClose={() => {}}
      onSaved={onSaved}
      plants={[plant]}
    />,
  );
  return { onSaved };
}

function openEditDialog(profile: OverwinteringProfile) {
  const onSaved = vi.fn();
  renderWithProviders(
    <OverwinteringProfileDialog
      open
      profile={profile}
      onClose={() => {}}
      onSaved={onSaved}
      plants={[plant]}
    />,
  );
  return { onSaved };
}

async function selectOption(fieldTestId: string, optionLabel: string) {
  const user = userEvent.setup();
  const field = screen.getByTestId(fieldTestId);
  await user.click(within(field).getByRole('combobox'));
  const listbox = await screen.findByRole('listbox');
  await user.click(within(listbox).getByText(optionLabel));
  await waitFor(() => expect(screen.queryByRole('listbox')).toBeNull());
}

describe('OverwinteringProfileDialog', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('resets winter_action to a valid path-B default when the rating switches to dig_and_store (F2/D5)', async () => {
    openCreateDialog();

    // Default rating needs_protection -> path A default action "fleece" (Vlies).
    const winterActionField = await screen.findByTestId(
      'form-field-winter_action',
    );
    expect(
      within(winterActionField).getByText(
        i18n.t('enums.winterAction.fleece'),
      ),
    ).toBeTruthy();

    // Switching to dig_and_store implies path B, where "fleece" would be a
    // guaranteed 422. The form must move winter_action to a valid default.
    await selectOption(
      'form-field-hardiness_rating',
      i18n.t('enums.hardinessRating.dig_and_store'),
    );

    await waitFor(() =>
      expect(
        within(winterActionField).getByText(
          i18n.t('enums.winterAction.dig_store'),
        ),
      ).toBeTruthy(),
    );
    expect(
      within(winterActionField).queryByText(
        i18n.t('enums.winterAction.fleece'),
      ),
    ).toBeNull();
  });

  it('offers only path-B winter actions once the rating is frost_free (F2/D5)', async () => {
    openCreateDialog();

    await selectOption(
      'form-field-hardiness_rating',
      i18n.t('enums.hardinessRating.frost_free'),
    );

    const user = userEvent.setup();
    const winterActionField = screen.getByTestId('form-field-winter_action');
    await user.click(within(winterActionField).getByRole('combobox'));
    const listbox = await screen.findByRole('listbox');

    expect(
      within(listbox).getByText(i18n.t('enums.winterAction.move_indoors')),
    ).toBeTruthy();
    expect(
      within(listbox).getByText(i18n.t('enums.winterAction.dig_store')),
    ).toBeTruthy();
    // Path-A only actions must not be selectable for a red rating.
    expect(
      within(listbox).queryByText(i18n.t('enums.winterAction.fleece')),
    ).toBeNull();
    expect(
      within(listbox).queryByText(i18n.t('enums.winterAction.mulch')),
    ).toBeNull();
  });

  it('requires a plant in create mode and does not submit without one (F3)', async () => {
    const user = userEvent.setup();
    const { onSaved } = openCreateDialog();

    await user.click(await screen.findByTestId('form-submit-button'));

    expect(
      await screen.findByText(i18n.t('pages.overwintering.plantRequired')),
    ).toBeTruthy();
    expect(onSaved).not.toHaveBeenCalled();
  });

  it('submits in create mode once a plant is selected (F3)', async () => {
    const user = userEvent.setup();
    const { onSaved } = openCreateDialog();

    await selectOption('form-field-plant_key', 'Big Red (TOM-001)');
    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => expect(onSaved).toHaveBeenCalled());
  });

  it('shows the tuber section and updates a dig_and_store profile in edit mode', async () => {
    server.use(
      http.put('/api/v1/t/:tenant/overwintering-profiles/:key', ({ params }) =>
        HttpResponse.json({ ...digStoreProfile, key: params.key }),
      ),
    );
    const user = userEvent.setup();
    const { onSaved } = openEditDialog(digStoreProfile);

    // Edit title, no plant field, and the tuber section (dig_and_store) is shown.
    expect(
      await screen.findByText(i18n.t('pages.overwintering.edit')),
    ).toBeTruthy();
    expect(screen.queryByTestId('form-field-plant_key')).toBeNull();
    expect(screen.getByTestId('form-field-storage_medium')).toBeTruthy();
    expect(screen.getByTestId('form-field-tuber_status')).toBeTruthy();

    await user.click(screen.getByTestId('form-submit-button'));
    await waitFor(() => expect(onSaved).toHaveBeenCalled());
  });

  it('hides the tuber section for a non dig_and_store rating', async () => {
    openEditDialog({
      ...digStoreProfile,
      hardiness_rating: 'needs_protection',
      winter_action: 'fleece',
      tuber_status: null,
      storage_medium: null,
      storage_check_interval_days: null,
    } as unknown as OverwinteringProfile);

    await screen.findByText(i18n.t('pages.overwintering.edit'));
    expect(screen.queryByTestId('form-field-storage_medium')).toBeNull();
    expect(screen.queryByTestId('form-field-tuber_status')).toBeNull();
  });

  it('surfaces a server-side 422 field error on submit (D5)', async () => {
    server.use(
      http.put('/api/v1/t/:tenant/overwintering-profiles/:key', () =>
        HttpResponse.json(
          {
            error_id: 'e-422',
            error_code: 'VALIDATION_ERROR',
            message: 'invalid',
            details: [
              { field: 'body.notes', reason: 'Knollenstatus ungültig' },
            ],
            timestamp: '',
            path: '',
            method: '',
          },
          { status: 422 },
        ),
      ),
    );
    const user = userEvent.setup();
    const { onSaved } = openEditDialog(digStoreProfile);

    await screen.findByText(i18n.t('pages.overwintering.edit'));
    await user.click(screen.getByTestId('form-submit-button'));

    // The field-error branch reports a validation notification and blocks save;
    // the notes field is flagged invalid (aria-invalid) by the server detail.
    expect(await screen.findByText(i18n.t('errors.validation'))).toBeTruthy();
    expect(onSaved).not.toHaveBeenCalled();
    await waitFor(() => {
      const notesInput = screen
        .getByTestId('form-field-notes')
        .querySelector('textarea');
      expect(notesInput?.getAttribute('aria-invalid')).toBe('true');
    });
  });
});
