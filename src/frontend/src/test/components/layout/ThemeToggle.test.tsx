import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import ThemeToggle from '@/components/layout/ThemeToggle';
import { renderWithProviders } from '../../helpers';

/** True when the "switch to dark" (moon) icon is showing → current mode is light. */
function isLightModeIconShown(button: HTMLElement): boolean {
  return button.querySelector('[data-testid="Brightness4Icon"]') !== null;
}

describe('ThemeToggle', () => {
  it('renders a theme-toggle button showing exactly one mode icon', () => {
    renderWithProviders(<ThemeToggle />);
    const button = screen.getByRole('button', { name: 'toggle theme' });
    expect(button).toBeInTheDocument();

    const moon = button.querySelector('[data-testid="Brightness4Icon"]');
    const sun = button.querySelector('[data-testid="Brightness7Icon"]');
    // Exactly one of the two icons is rendered, reflecting the active mode.
    expect(Boolean(moon) !== Boolean(sun)).toBe(true);
  });

  it('flips the icon between light and dark on each toggle', async () => {
    const user = userEvent.setup();
    renderWithProviders(<ThemeToggle />);
    const button = screen.getByRole('button', { name: 'toggle theme' });

    const initiallyLight = isLightModeIconShown(button);

    await user.click(button);
    expect(isLightModeIconShown(button)).toBe(!initiallyLight);

    await user.click(button);
    expect(isLightModeIconShown(button)).toBe(initiallyLight);
  });
});
