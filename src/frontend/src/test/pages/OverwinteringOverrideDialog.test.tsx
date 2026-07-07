import { screen, within, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import OverwinteringOverrideDialog from '@/pages/pflanzen/OverwinteringOverrideDialog';
import type { OverwinteringProfile } from '@/api/types';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

const baseProfile = {
  key: 'ow-1',
  plant_key: 'plant-1',
  planting_run_key: null,
  hardiness_zone_min: '7a',
  hardiness_rating: 'needs_protection',
  winter_action: 'fleece',
  winter_action_month: 11,
  spring_action: 'uncover',
  spring_action_month: 4,
  winter_quarter_key: null,
  winter_quarter_temp_min: null,
  winter_quarter_temp_max: null,
  winter_quarter_light: null,
  winter_watering: null,
  storage_medium: null,
  storage_check_interval_days: null,
  tuber_status: null,
  notes: 'Vlies auflegen',
  auto_generated: true,
  user_overridden: false,
  derived_path: 'path_a',
  dormancy_care_active: false,
  materialized_at: '2024-10-01T00:00:00Z',
  source_template_key: 'tmpl-1',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: null,
} as unknown as OverwinteringProfile;

const PATCH_URL = '/api/v1/t/:tenant/plants/:plantKey/overwintering';

function renderDialog(
  profile: OverwinteringProfile = baseProfile,
  onClose = vi.fn(),
) {
  renderWithProviders(
    <OverwinteringOverrideDialog
      open
      onClose={onClose}
      plantKey="plant-1"
      profile={profile}
    />,
  );
  return { onClose };
}

async function selectOption(fieldTestId: string, optionLabel: string) {
  const user = userEvent.setup();
  const field = screen.getByTestId(fieldTestId);
  await user.click(within(field).getByRole('combobox'));
  const listbox = await screen.findByRole('listbox');
  await user.click(within(listbox).getByText(optionLabel));
  await waitFor(() => expect(screen.queryByRole('listbox')).toBeNull());
}

describe('OverwinteringOverrideDialog', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders the override dialog with title, intro and prefilled fields', async () => {
    renderDialog();

    expect(
      await screen.findByText(i18n.t('pages.season.override.dialogTitle')),
    ).toBeTruthy();
    expect(
      screen.getByText(i18n.t('pages.season.override.dialogIntro')),
    ).toBeTruthy();
    expect(screen.getByTestId('form-field-hardiness_rating')).toBeTruthy();
    expect(screen.getByTestId('form-field-winter_action')).toBeTruthy();
    // Notes come from the profile via profileToForm.
    const notes = screen
      .getByTestId('form-field-notes')
      .querySelector('textarea');
    expect(notes?.value).toBe('Vlies auflegen');
    // Path-A rating hides the tuber section.
    expect(screen.queryByTestId('form-field-tuber_status')).toBeNull();
  });

  it('submits the override and closes on success', async () => {
    const captured: Record<string, unknown>[] = [];
    server.use(
      http.patch(PATCH_URL, async ({ request }) => {
        captured.push((await request.json()) as Record<string, unknown>);
        return HttpResponse.json({
          ...baseProfile,
          user_overridden: true,
          notes: 'Vlies auflegen',
        });
      }),
    );
    const user = userEvent.setup();
    const { onClose } = renderDialog();

    await user.click(await screen.findByTestId('form-submit-button'));

    await waitFor(() => expect(onClose).toHaveBeenCalled());
    expect(captured).toHaveLength(1);
    expect(captured[0]).toMatchObject({
      hardiness_rating: 'needs_protection',
      winter_action: 'fleece',
      winter_action_month: 11,
    });
    // "" form values are normalised to null in the patch payload.
    expect(captured[0].winter_quarter_temp_min).toBeNull();
    expect(
      await screen.findByText(i18n.t('pages.season.override.saved')),
    ).toBeTruthy();
  });

  it('closes without saving when cancel is pressed', async () => {
    const patchSpy = vi.fn();
    server.use(
      http.patch(PATCH_URL, () => {
        patchSpy();
        return HttpResponse.json(baseProfile);
      }),
    );
    const user = userEvent.setup();
    const { onClose } = renderDialog();

    await user.click(await screen.findByTestId('form-cancel-button'));

    expect(onClose).toHaveBeenCalled();
    expect(patchSpy).not.toHaveBeenCalled();
  });

  it('moves winter_action to a path-B default and reveals the tuber section for dig_and_store (D5)', async () => {
    renderDialog();

    const winterActionField = await screen.findByTestId(
      'form-field-winter_action',
    );
    // Path-A default is preselected.
    expect(
      within(winterActionField).getByText(i18n.t('enums.winterAction.fleece')),
    ).toBeTruthy();

    await selectOption(
      'form-field-hardiness_rating',
      i18n.t('enums.hardinessRating.dig_and_store'),
    );

    // winter_action is corrected to a valid path-B action.
    await waitFor(() =>
      expect(
        within(winterActionField).getByText(
          i18n.t('enums.winterAction.dig_store'),
        ),
      ).toBeTruthy(),
    );
    // And the tuber-only fields become visible.
    expect(
      await screen.findByTestId('form-field-storage_check_interval_days'),
    ).toBeTruthy();
    expect(screen.getByTestId('form-field-tuber_status')).toBeTruthy();

    // Only path-B actions are offered.
    const user = userEvent.setup();
    await user.click(within(winterActionField).getByRole('combobox'));
    const listbox = await screen.findByRole('listbox');
    expect(
      within(listbox).getByText(i18n.t('enums.winterAction.move_indoors')),
    ).toBeTruthy();
    expect(
      within(listbox).queryByText(i18n.t('enums.winterAction.fleece')),
    ).toBeNull();
  });

  it('keeps the dialog open and reports the generic error when the save fails (KNOWN BUG: 422 field errors lost)', async () => {
    // KNOWN BUG — this asserts current (wrong) behaviour, not desired behaviour.
    // The override runs through a Redux thunk whose rejection RTK serialises to a
    // SerializedError, so `isApiError()` in useApiError fails and the structured
    // 422 field error ("Notiz ungültig" on `notes`) is lost; handleError falls
    // back to the generic `errors.unknown`. The sibling OverwinteringProfileDialog
    // calls the API directly and maps field errors correctly.
    // WHEN THE THUNK BUG IS FIXED: this test will break on the errors.unknown
    // assertion below — that break is expected. Update it to assert the field
    // error surfaces, e.g. `await screen.findByText('Notiz ungültig')`.
    server.use(
      http.patch(PATCH_URL, () =>
        HttpResponse.json(
          {
            error_id: 'e-422',
            error_code: 'VALIDATION_ERROR',
            message: 'invalid',
            details: [{ field: 'body.notes', reason: 'Notiz ungültig' }],
            timestamp: '',
            path: '',
            method: '',
          },
          { status: 422 },
        ),
      ),
    );
    const user = userEvent.setup();
    const { onClose } = renderDialog();

    await user.click(await screen.findByTestId('form-submit-button'));

    expect(await screen.findByText(i18n.t('errors.unknown'))).toBeTruthy();
    expect(onClose).not.toHaveBeenCalled();
    expect(
      screen.queryByText(i18n.t('pages.season.override.saved')),
    ).toBeNull();
    // Saving state is released again so the user can retry.
    await waitFor(() =>
      expect(
        screen.getByTestId('form-submit-button').hasAttribute('disabled'),
      ).toBe(false),
    );
  });
});
