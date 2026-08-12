import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe } from 'vitest-axe';
import { renderWithProviders } from '@/test/helpers';
import ConnectLandingPage from '@/pages/auth/ConnectLandingPage';

// Spy on the navigation so "continue in the browser" is asserted by the effect
// it actually causes, not by the button still being on screen (which is true
// regardless of what the handler does). Keep the rest of react-router-dom real
// so the helper's createMemoryRouter/RouterProvider still work.
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useNavigate: () => mockNavigate };
});

beforeEach(() => {
  mockNavigate.mockClear();
});

/**
 * #1118 P13 — the browser landing for the instance-discovery deep link
 * `https://<instance>/connect?v=1`.
 *
 * The point of this page is that the deep link must not 404 for a visitor who
 * scanned the QR with a plain system camera and has no app installed. So the two
 * things worth asserting are that the page renders addressable content at all,
 * and that it offers a way to keep going in the browser.
 */
describe('ConnectLandingPage — instance-discovery deep-link fallback', () => {
  it('renders a labelled landing with a browser-continue action', async () => {
    renderWithProviders(<ConnectLandingPage />, { route: '/connect?v=1' });

    expect(await screen.findByTestId('connect-landing-page')).toBeInTheDocument();
    // The explanatory heading is present — this is a real page, not a bare 404.
    expect(screen.getByRole('heading', { name: /open in the kamerplanter app/i })).toBeInTheDocument();
    // The escape hatch for users without the app is reachable by role, not only
    // by test id.
    expect(
      screen.getByRole('button', { name: /continue in the browser/i }),
    ).toBeInTheDocument();
  });

  it('lets the visitor continue in the browser', async () => {
    const user = userEvent.setup();
    renderWithProviders(<ConnectLandingPage />, { route: '/connect?v=1' });

    // The action stays a plain in-app navigation (no reload, no credential
    // handling): clicking it routes the anonymous visitor to the app root.
    // Asserting the navigation itself means emptying handleContinue fails here.
    await user.click(await screen.findByTestId('connect-landing-continue'));
    expect(mockNavigate).toHaveBeenCalledWith('/', { replace: true });
  });

  it('has no critical accessibility violations', async () => {
    const { container } = renderWithProviders(<ConnectLandingPage />, { route: '/connect?v=1' });
    await screen.findByTestId('connect-landing-page');

    const results = await axe(container);

    expect(results.violations.filter((violation) => violation.impact === 'critical')).toEqual([]);
  });
});
