import { useState } from 'react';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, afterEach } from 'vitest';
import { createMemoryRouter, RouterProvider, Link } from 'react-router-dom';
import { Provider } from 'react-redux';
import { SnackbarProvider } from 'notistack';
import { ThemeContextProvider } from '@/theme';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import { ThemeProvider, createTheme, type Theme } from '@mui/material/styles';
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


/**
 * The guard next to a page dialog that links away, with a closing transition
 * long enough that the second prompt always lands while the first is still
 * fading out. The default 195 ms is the same race, only rarely hit — until a
 * loaded CI runner stretches it (#1682's frontend lane, 2026-09-23).
 */
function PageWithDialog() {
  const [open, setOpen] = useState(false);
  return (
    <>
      <UnsavedChangesGuard dirty />
      <Link to="/other">leave</Link>
      <Button onClick={() => setOpen(true)}>open picker</Button>
      <Dialog open={open} onClose={() => setOpen(false)}>
        <DialogTitle>picker</DialogTitle>
        <Link to="/other">leave from picker</Link>
      </Dialog>
    </>
  );
}

function renderGuardWithSlowExit() {
  const store = createTestStore();
  const router = createMemoryRouter(
    [
      { path: '/', element: <PageWithDialog /> },
      { path: '/other', element: <div>other page</div> },
    ],
    { initialEntries: ['/'] },
  );
  const slowExit = (outer: Theme) =>
    createTheme(outer, { transitions: { duration: { leavingScreen: 60_000 } } });
  return render(
    <Provider store={store}>
      <ThemeContextProvider>
        <ThemeProvider theme={slowExit}>
          <SnackbarProvider>
            <RouterProvider router={router} />
          </SnackbarProvider>
        </ThemeProvider>
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
  it('puts a second prompt on top while the first is still closing', async () => {
    const user = userEvent.setup();
    renderGuardWithSlowExit();

    // First prompt, dismissed: it starts its (here: minute-long) fade-out.
    await user.click(screen.getByRole('link', { name: 'leave' }));
    await user.click(await screen.findByTestId('confirm-dialog-cancel'));

    // Another dialog opens over the page and links away from inside it. The
    // fading prompt still marks the page aria-hidden, as MUI does until the
    // exit completes, so the trigger is reached by its text, not its role.
    await user.click(screen.getByText('open picker'));
    const picker = await screen.findByRole('dialog', { name: 'picker' });
    await user.click(within(picker).getByRole('link', { name: 'leave from picker' }));

    // The second prompt must be the one a user and assistive tech reach: an
    // accessible alertdialog holding focus, not the still-fading instance that
    // the picker had marked aria-hidden underneath itself.
    const prompt = await screen.findByRole('alertdialog');
    expect(prompt.contains(document.activeElement)).toBe(true);
    expect(screen.queryByText('other page')).toBeNull();
  });
});
