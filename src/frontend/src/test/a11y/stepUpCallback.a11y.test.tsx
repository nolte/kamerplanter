/**
 * Axe pass for `StepUpCallbackPage` (#1815, #1094).
 *
 * Its own file because the page navigates away in its first effect; the
 * module-scoped `useNavigate` mock below keeps it on screen so there is
 * something to scan. The page is deliberately small — a progress indicator and
 * one status line — so the floor is set to what it renders, not to a number
 * a loading skeleton could also reach.
 */

import { render, screen } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { describe, it, vi, beforeEach } from 'vitest';
import i18n from 'i18next';
import { expectNoA11yViolations } from './expectNoA11yViolations';

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useNavigate: () => () => {} };
});

import StepUpCallbackPage from '@/pages/auth/StepUpCallbackPage';

describe('StepUpCallbackPage a11y', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    sessionStorage.clear();
  });

  it('has no critical axe violations', async () => {
    const router = createMemoryRouter([{ path: '*', element: <StepUpCallbackPage /> }], {
      initialEntries: ['/auth/step-up/callback?error=step_up_failed'],
    });
    const { container } = render(<RouterProvider router={router} />);
    await screen.findByTestId('step-up-callback-page');
    await expectNoA11yViolations(container, { minElements: 3 });
  });
});
