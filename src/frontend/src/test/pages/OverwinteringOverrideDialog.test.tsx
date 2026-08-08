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

  it('translates a coded server 422 onto the German field, not the English reason (#1041)', async () => {
    // #1041: the override thunk now preserves the typed ApiError through
    // rejectWithValue, so the D5 winter-path violation reaches the dialog with
    // its `details[]`/`code` intact and lands — translated on the code — on the
    // winter_action field instead of being swallowed by a generic toast.
    server.use(
      http.patch(PATCH_URL, () =>
        HttpResponse.json(
          {
            error_id: 'e-422',
            error_code: 'WINTER_PATH_VIOLATION',
            message: 'invalid',
            details: [
              {
                field: 'winter_action',
                reason: "Path B requires one of move_indoors, dig_store; got 'fleece'.",
                code: 'WINTER_PATH_VIOLATION',
              },
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
    const { onClose } = renderDialog();

    await user.click(await screen.findByTestId('form-submit-button'));

    // The German, code-keyed message lands on winter_action; the English reason
    // never appears in the form (#1015).
    const field = await screen.findByTestId('form-field-winter_action');
    await waitFor(() =>
      expect(
        within(field).getByText(
          i18n.t('pages.overwintering.errors.winterPathViolation'),
        ),
      ).toBeTruthy(),
    );
    expect(
      screen.queryByText(
        "Path B requires one of move_indoors, dig_store; got 'fleece'.",
      ),
    ).toBeNull();
    expect(onClose).not.toHaveBeenCalled();
    // Saving state is released again so the user can retry.
    await waitFor(() =>
      expect(
        screen.getByTestId('form-submit-button').hasAttribute('disabled'),
      ).toBe(false),
    );
  });

  it('degrades an untranslatable coded 422 to the toast, leaving the field clean (#1041)', async () => {
    // A code the override dialog has no map entry for must fall back to the
    // generic validation toast — never render the English `reason` on the form.
    server.use(
      http.patch(PATCH_URL, () =>
        HttpResponse.json(
          {
            error_id: 'e-422',
            error_code: 'VALIDATION_ERROR',
            message: 'invalid',
            details: [
              { field: 'body.notes', reason: 'Value error: notes invalid', code: 'value_error' },
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
    const { onClose } = renderDialog();

    await user.click(await screen.findByTestId('form-submit-button'));

    expect(
      await screen.findByText(
        i18n.t('errors.validationWithDetail', { detail: 'invalid' }),
      ),
    ).toBeTruthy();
    expect(onClose).not.toHaveBeenCalled();
    expect(
      screen.queryByText(i18n.t('pages.season.override.saved')),
    ).toBeNull();
    // The English reason is never rendered on the field.
    expect(screen.queryByText('Value error: notes invalid')).toBeNull();
    const notesInput = screen
      .getByTestId('form-field-notes')
      .querySelector('textarea');
    expect(notesInput?.getAttribute('aria-invalid')).not.toBe('true');
  });
});
