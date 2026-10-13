/**
 * Axe pass for the two e-mail-change link landings (#1848, #1094).
 *
 * Both pages are small cards; the floor is set to what they render in the state
 * scanned, not to a number a loading skeleton could also reach. Both are scanned
 * in their initial explanation state — neither sends anything before a click.
 */

import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { describe, it, beforeEach } from 'vitest';
import i18n from 'i18next';
import { createTestStore } from '@/test/helpers';
import { expectNoA11yViolations } from './expectNoA11yViolations';
import EmailChangeConfirmPage from '@/pages/auth/EmailChangeConfirmPage';
import EmailChangeRevertPage from '@/pages/auth/EmailChangeRevertPage';

describe('E-mail change pages a11y', () => {
  beforeEach(() => i18n.changeLanguage('de'));

  it('EmailChangeConfirmPage has no critical axe violations', async () => {
    const router = createMemoryRouter([{ path: '/email-change/:token', element: <EmailChangeConfirmPage /> }], {
      initialEntries: ['/email-change/abc'],
    });
    const { container } = render(
      <Provider store={createTestStore()}>
        <RouterProvider router={router} />
      </Provider>,
    );
    await screen.findByTestId('email-change-confirm-btn');
    await expectNoA11yViolations(container, { minElements: 15 });
  });

  it('EmailChangeRevertPage has no critical axe violations', async () => {
    const router = createMemoryRouter(
      [{ path: '/email-change/revert/:token', element: <EmailChangeRevertPage /> }],
      { initialEntries: ['/email-change/revert/abc'] },
    );
    const { container } = render(
      <Provider store={createTestStore()}>
        <RouterProvider router={router} />
      </Provider>,
    );
    await screen.findByTestId('email-change-revert-btn');
    await expectNoA11yViolations(container, { minElements: 15 });
  });
});
