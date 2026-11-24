/**
 * Axe pass for the grouped settings page (F-11, #2935): the desktop side
 * navigation with an open group, and the phone's group list. Scanned once the
 * navigation and the profile form are rendered, so the floor is the page's own
 * content rather than a loading skeleton.
 */

import { screen } from '@testing-library/react';
import { describe, it, beforeEach, vi } from 'vitest';
import i18n from 'i18next';
import { KioskProvider } from '@/kiosk/KioskProvider';
import { authState, createTestStore, renderWithProviders, tenantState } from '@/test/helpers';
import { expectNoA11yViolations } from './expectNoA11yViolations';
import AccountSettingsPage from '@/pages/auth/AccountSettingsPage';

function stubViewportWidth(width: number): void {
  window.innerWidth = width;
  window.matchMedia = ((query: string) => {
    const min = /\(min-width:\s*([\d.]+)px\)/.exec(query);
    const max = /\(max-width:\s*([\d.]+)px\)/.exec(query);
    const matches = (min === null || width >= Number(min[1])) && (max === null || width <= Number(max[1]));
    return {
      matches,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    } as unknown as MediaQueryList;
  }) as typeof window.matchMedia;
}

function renderSettings(route: string) {
  return renderWithProviders(
    <KioskProvider>
      <AccountSettingsPage />
    </KioskProvider>,
    { store: createTestStore({ ...authState({ platformAdmin: true }), ...tenantState('lead') }), route },
  );
}

describe('AccountSettingsPage a11y (F-11)', () => {
  beforeEach(() => i18n.changeLanguage('de'));

  it('has no critical axe violations with the side navigation (desktop)', async () => {
    stubViewportWidth(1280);
    const { container } = renderSettings('/settings/account');
    await screen.findByTestId('settings-nav-sidebar');
    await screen.findByTestId('profile-save-btn');
    await expectNoA11yViolations(container, { minElements: 40 });
  });

  it('has no critical axe violations with the group list (phone)', async () => {
    stubViewportWidth(390);
    const { container } = renderSettings('/settings');
    await screen.findByTestId('settings-nav-list');
    await expectNoA11yViolations(container, { minElements: 20 });
  });
});
