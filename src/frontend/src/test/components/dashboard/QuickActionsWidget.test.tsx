import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach } from 'vitest';
import i18n from 'i18next';
import QuickActionsWidget from '@/components/dashboard/widgets/QuickActionsWidget';
import { renderWithProviders } from '../../helpers';

describe('QuickActionsWidget (#3047)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders every quick action as a real link and follows it on click', async () => {
    const user = userEvent.setup();
    const { router } = renderWithProviders(<QuickActionsWidget />);

    const tile = screen.getByTestId('quick-action-/stammdaten/species');
    const link = within(tile).getByRole('link', { name: i18n.t('nav.species') });
    expect(link).toHaveAttribute('href', '/stammdaten/species');

    await user.click(link);
    expect(router.state.location.pathname).toBe('/stammdaten/species');
  });
});
