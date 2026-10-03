/**
 * Axe pass for the resend-verification landing (#2037, #1094).
 *
 * Scanned in its initial form state — the page sends nothing before a submit.
 * The floor is what the card renders there (heading, intro, field, button, link),
 * not a number a loading skeleton could also reach.
 */

import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { describe, it, beforeEach } from 'vitest';
import i18n from 'i18next';
import { createTestStore } from '@/test/helpers';
import { expectNoA11yViolations } from './expectNoA11yViolations';
import ResendVerificationPage from '@/pages/auth/ResendVerificationPage';

describe('Resend verification page a11y', () => {
  beforeEach(() => i18n.changeLanguage('de'));

  it('ResendVerificationPage has no critical axe violations', async () => {
    const router = createMemoryRouter([{ path: '/resend-verification', element: <ResendVerificationPage /> }], {
      initialEntries: ['/resend-verification'],
    });
    const { container } = render(
      <Provider store={createTestStore()}>
        <RouterProvider router={router} />
      </Provider>,
    );
    await screen.findByTestId('resend-verification-submit');
    await expectNoA11yViolations(container, { minElements: 15 });
  });
});
