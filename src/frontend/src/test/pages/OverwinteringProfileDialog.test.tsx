import { screen, within, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import i18n from 'i18next';
import OverwinteringProfileDialog from '@/pages/ueberwinterung/OverwinteringProfileDialog';
import type { PlantInstance } from '@/api/types';
import { renderWithProviders } from '../helpers';

const plant = {
  key: 'plant-1',
  instance_id: 'TOM-001',
  plant_name: 'Big Red',
} as unknown as PlantInstance;

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
});
