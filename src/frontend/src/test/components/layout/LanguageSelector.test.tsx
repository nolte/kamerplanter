import { describe, it, expect, afterEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';

import LanguageSelector from '@/components/layout/LanguageSelector';
import { renderWithProviders } from '../../helpers';

describe('LanguageSelector', () => {
  afterEach(async () => {
    // Restore the DE default so other suites are unaffected.
    await i18n.changeLanguage('de');
  });

  it('opens the language menu and marks the active language as selected', async () => {
    const user = userEvent.setup();
    await i18n.changeLanguage('de');
    renderWithProviders(<LanguageSelector />);

    await user.click(screen.getByRole('button', { name: 'change language' }));

    const german = screen.getByRole('menuitem', { name: 'Deutsch' });
    const english = screen.getByRole('menuitem', { name: 'English' });
    expect(german).toBeInTheDocument();
    expect(english).toBeInTheDocument();
    // MUI marks the active MenuItem with the Mui-selected class.
    expect(german).toHaveClass('Mui-selected');
    expect(english).not.toHaveClass('Mui-selected');
  });

  it('changes the language and closes the menu when a language is chosen', async () => {
    const user = userEvent.setup();
    await i18n.changeLanguage('de');
    renderWithProviders(<LanguageSelector />);

    await user.click(screen.getByRole('button', { name: 'change language' }));
    await user.click(screen.getByRole('menuitem', { name: 'English' }));

    expect(i18n.language).toBe('en');
    // Menu closed → the items are no longer in the DOM.
    expect(screen.queryByRole('menuitem', { name: 'English' })).toBeNull();
  });

  it('closes the menu via the backdrop/escape without changing the language', async () => {
    const user = userEvent.setup();
    await i18n.changeLanguage('de');
    renderWithProviders(<LanguageSelector />);

    await user.click(screen.getByRole('button', { name: 'change language' }));
    expect(screen.getByRole('menuitem', { name: 'Deutsch' })).toBeInTheDocument();

    // Escape triggers the Menu onClose handler.
    await user.keyboard('{Escape}');

    await waitFor(() =>
      expect(screen.queryByRole('menuitem', { name: 'Deutsch' })).toBeNull(),
    );
    expect(i18n.language).toBe('de');
  });
});
