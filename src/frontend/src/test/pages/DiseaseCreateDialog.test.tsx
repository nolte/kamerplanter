import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import i18n from 'i18next';
import DiseaseCreateDialog from '@/pages/pflanzenschutz/DiseaseCreateDialog';
import { renderWithProviders } from '../helpers';

vi.mock('@/api/endpoints/ipm', () => ({ createDisease: vi.fn() }));
import { createDisease } from '@/api/endpoints/ipm';

/**
 * #2936 — a disease created in the UI records which language its name is in: the name
 * was typed in the UI language, so it goes into `common_names_i18n` under that language.
 */
describe('DiseaseCreateDialog — names per language (#2936)', () => {
  afterEach(async () => {
    vi.clearAllMocks();
    await i18n.changeLanguage('de');
  });

  it.each([
    ['de', 'de', 'Echter Mehltau'],
    ['en', 'en', 'Powdery Mildew'],
    ['en-GB', 'en', 'Powdery Mildew'],
  ])('records the typed name under the UI language (%s)', async (language, key, name) => {
    await i18n.changeLanguage(language);
    vi.mocked(createDisease).mockResolvedValue({} as never);
    const user = userEvent.setup();
    renderWithProviders(<DiseaseCreateDialog open onClose={() => {}} onCreated={() => {}} />);

    await user.type(within(screen.getByTestId('form-field-scientific_name')).getByRole('textbox'), 'Erysiphe spp.');
    await user.type(within(screen.getByTestId('form-field-common_name')).getByRole('textbox'), name);
    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => expect(createDisease).toHaveBeenCalledTimes(1));
    expect(vi.mocked(createDisease).mock.calls[0][0]).toMatchObject({
      common_name: name,
      common_names_i18n: { [key]: [name] },
    });
  });
});
