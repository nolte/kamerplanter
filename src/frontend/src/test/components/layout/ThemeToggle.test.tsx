import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';

import ThemeToggle from '@/components/layout/ThemeToggle';
import { renderWithProviders } from '../../helpers';

/** The toggle's accessible name names the target mode, so it changes with the mode. */
function themeToggleName(): RegExp {
  const labels = [i18n.t('common.switchToDarkTheme'), i18n.t('common.switchToLightTheme')];
  return new RegExp(`^(${labels.map((l) => l.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})$`);
}

/** True when the "switch to dark" (moon) icon is showing → current mode is light. */
function isLightModeIconShown(button: HTMLElement): boolean {
  return button.querySelector('[data-testid="Brightness4Icon"]') !== null;
}

describe('ThemeToggle', () => {
  it('renders a theme-toggle button showing exactly one mode icon', () => {
    renderWithProviders(<ThemeToggle />);
    const button = screen.getByRole('button', { name: themeToggleName() });
    expect(button).toBeInTheDocument();

    const moon = button.querySelector('[data-testid="Brightness4Icon"]');
    const sun = button.querySelector('[data-testid="Brightness7Icon"]');
    // Exactly one of the two icons is rendered, reflecting the active mode.
    expect(Boolean(moon) !== Boolean(sun)).toBe(true);
  });

  it('flips the icon between light and dark on each toggle', async () => {
    const user = userEvent.setup();
    renderWithProviders(<ThemeToggle />);
    const button = screen.getByRole('button', { name: themeToggleName() });

    const initiallyLight = isLightModeIconShown(button);

    await user.click(button);
    expect(isLightModeIconShown(button)).toBe(!initiallyLight);

    await user.click(button);
    expect(isLightModeIconShown(button)).toBe(initiallyLight);
  });
});
