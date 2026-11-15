import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import i18n from 'i18next';
import PestCreateDialog from '@/pages/pflanzenschutz/PestCreateDialog';
import { renderWithProviders } from '../helpers';

vi.mock('@/api/endpoints/ipm', () => ({ createPest: vi.fn() }));
import { createPest } from '@/api/endpoints/ipm';

/**
 * #2955 — a pest created in the UI records which language its name is in: the name
 * was typed in the UI language, so it goes into `common_names_i18n` under that language.
 */
describe('PestCreateDialog — names per language (#2955)', () => {
  afterEach(async () => {
    vi.clearAllMocks();
    await i18n.changeLanguage('de');
  });

  it.each([
    ['de', 'de', 'Spinnmilben'],
    ['en', 'en', 'Spider Mites'],
    ['en-GB', 'en', 'Spider Mites'],
  ])('records the typed name under the UI language (%s)', async (language, key, name) => {
    await i18n.changeLanguage(language);
    vi.mocked(createPest).mockResolvedValue({} as never);
    const user = userEvent.setup();
    renderWithProviders(<PestCreateDialog open onClose={() => {}} onCreated={() => {}} />);

    await user.type(within(screen.getByTestId('form-field-scientific_name')).getByRole('textbox'), 'Tetranychus urticae');
    await user.type(within(screen.getByTestId('form-field-common_name')).getByRole('textbox'), name);
    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => expect(createPest).toHaveBeenCalledTimes(1));
    expect(vi.mocked(createPest).mock.calls[0][0]).toMatchObject({
      common_name: name,
      common_names_i18n: { [key]: [name] },
    });
  });
});
