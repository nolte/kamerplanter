import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, afterEach } from 'vitest';
import { createMemoryRouter, RouterProvider, Link } from 'react-router-dom';
import { Provider } from 'react-redux';
import { SnackbarProvider } from 'notistack';
import { ThemeContextProvider } from '@/theme';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import { createTestStore } from '../helpers';
import '@/i18n';

/** Mount the guard inside a two-route data router so useBlocker is active. */
function renderGuard(dirty: boolean) {
  const store = createTestStore();
  const router = createMemoryRouter(
    [
      {
        path: '/',
        element: (
          <>
            <UnsavedChangesGuard dirty={dirty} />
            <Link to="/other">leave</Link>
          </>
        ),
      },
      { path: '/other', element: <div>other page</div> },
    ],
    { initialEntries: ['/'] },
  );
  return render(
    <Provider store={store}>
      <ThemeContextProvider>
        <SnackbarProvider>
          <RouterProvider router={router} />
        </SnackbarProvider>
      </ThemeContextProvider>
    </Provider>,
  );
}

describe('UnsavedChangesGuard', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('does not block navigation when not dirty', async () => {
    const user = userEvent.setup();
    renderGuard(false);
    await user.click(screen.getByRole('link', { name: 'leave' }));
    expect(await screen.findByText('other page')).toBeTruthy();
  });

  it('blocks navigation and shows the confirm dialog when dirty', async () => {
    const user = userEvent.setup();
    renderGuard(true);
    await user.click(screen.getByRole('link', { name: 'leave' }));
    expect(await screen.findByTestId('confirm-dialog')).toBeTruthy();
  });

  it('registers a beforeunload listener while dirty', () => {
    const addSpy = vi.spyOn(window, 'addEventListener');
    renderGuard(true);
    expect(addSpy).toHaveBeenCalledWith('beforeunload', expect.any(Function));
  });

  it('does not register a beforeunload listener when clean', () => {
    const addSpy = vi.spyOn(window, 'addEventListener');
    renderGuard(false);
    expect(
      addSpy.mock.calls.some(([type]) => type === 'beforeunload'),
    ).toBe(false);
  });

  it('proceeds with navigation when the dialog is confirmed', async () => {
    const user = userEvent.setup();
    renderGuard(true);
    await user.click(screen.getByRole('link', { name: 'leave' }));
    await screen.findByTestId('confirm-dialog');
    await user.click(screen.getByTestId('confirm-dialog-confirm'));
    expect(await screen.findByText('other page')).toBeTruthy();
  });

  it('stays on the page when the dialog is cancelled', async () => {
    const user = userEvent.setup();
    renderGuard(true);
    await user.click(screen.getByRole('link', { name: 'leave' }));
    await screen.findByTestId('confirm-dialog');
    await user.click(screen.getByTestId('confirm-dialog-cancel'));
    // The blocker reset keeps us on the origin route — the target page never mounts.
    expect(screen.queryByText('other page')).toBeNull();
  });

  it('invokes the registered beforeunload handler when dirty', () => {
    renderGuard(true);
    const event = new Event('beforeunload', { cancelable: true });
    const preventDefault = vi.spyOn(event, 'preventDefault');
    window.dispatchEvent(event);
    expect(preventDefault).toHaveBeenCalled();
  });
});
