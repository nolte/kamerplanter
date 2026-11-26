import { act, fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useForm } from 'react-hook-form';
import { Provider } from 'react-redux';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import i18n from 'i18next';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import { ThemeContextProvider } from '@/theme';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import FormNumberField from '@/components/form/FormNumberField';
import KioskShell from '@/layouts/KioskShell';
import { KioskContext, type KioskContextValue } from '@/kiosk/KioskProvider';
import { EC_QUICK_SELECT } from '@/kiosk/quickSelectPresets';
import { KIOSK_TAP_DEBOUNCE_MS } from '@/kiosk/useTapDebounce';
import { KIOSK_LONG_PRESS_MS } from '@/components/kiosk/LongPressButton';
import { createTestStore } from '@/test/helpers';

function kioskValue(isKiosk: boolean): KioskContextValue {
  return {
    isKiosk,
    highContrast: isKiosk,
    enableKiosk: vi.fn(),
    disableKiosk: vi.fn(),
    toggleKiosk: vi.fn(),
    setHighContrast: vi.fn(),
  };
}

function inKiosk(ui: React.ReactNode, isKiosk = true) {
  return (
    <Provider store={createTestStore()}>
      <KioskContext.Provider value={kioskValue(isKiosk)}>
        <ThemeContextProvider>{ui}</ThemeContextProvider>
      </KioskContext.Provider>
    </Provider>
  );
}

/** A real tap: the press the debounce measures, then the click it produces. */
function tap(el: Element) {
  fireEvent.pointerDown(el, { button: 0 });
  fireEvent.pointerUp(el, { button: 0 });
  fireEvent.click(el, { detail: 1 });
}

beforeEach(() => {
  i18n.changeLanguage('de');
});

afterEach(() => {
  vi.useRealTimers();
});

/** Flush the lazy chunks (shell parts, long-press button, quick-select tiles) under fake timers. */
async function settle() {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(0);
  });
}

describe('kiosk tap debounce (UI-NFR-019 R-029, #3025 N-38)', () => {
  function renderShellWith(onAction: () => void, onDialogAction: () => void) {
    const router = createMemoryRouter(
      [
        {
          path: '/giessprotokoll',
          element: (
            <KioskShell>
              <Button onClick={onAction} data-testid="action">Speichern</Button>
              <Dialog open>
                <Button onClick={onDialogAction} data-testid="dialog-action">OK</Button>
              </Dialog>
            </KioskShell>
          ),
        },
        { path: '/kiosk', element: <div /> },
      ],
      { initialEntries: ['/giessprotokoll'] },
    );
    render(inKiosk(<RouterProvider router={router} />));
  }

  it('turns a double tap into one action, and lets a tap after the window through', async () => {
    vi.useFakeTimers();
    const onAction = vi.fn();
    renderShellWith(onAction, vi.fn());
    await settle();
    const action = screen.getByTestId('action');

    tap(action);
    act(() => void vi.advanceTimersByTime(KIOSK_TAP_DEBOUNCE_MS - 150));
    tap(action);
    expect(onAction).toHaveBeenCalledTimes(1);

    act(() => void vi.advanceTimersByTime(KIOSK_TAP_DEBOUNCE_MS + 1));
    tap(action);
    expect(onAction).toHaveBeenCalledTimes(2);
  });

  it('debounces a double tap inside a portalled dialog as well', async () => {
    vi.useFakeTimers();
    const onDialogAction = vi.fn();
    renderShellWith(vi.fn(), onDialogAction);
    await settle();
    const action = screen.getByTestId('dialog-action');

    tap(action);
    act(() => void vi.advanceTimersByTime(100));
    tap(action);
    expect(onDialogAction).toHaveBeenCalledTimes(1);
  });

  it('leaves keyboard activation alone — a double tap is a touch phenomenon', async () => {
    vi.useFakeTimers();
    const onAction = vi.fn();
    renderShellWith(onAction, vi.fn());
    await settle();
    const action = screen.getByTestId('action');

    // Keyboard clicks carry no pointer press.
    fireEvent.click(action, { detail: 0 });
    fireEvent.click(action, { detail: 0 });
    expect(onAction).toHaveBeenCalledTimes(2);
  });
});

describe('kiosk long-press for destructive confirmations (UI-NFR-019 R-030, R-031)', () => {
  function renderConfirm(onConfirm: () => void, isKiosk = true) {
    render(
      inKiosk(
        <ConfirmDialog
          open
          destructive
          title="Gießeintrag löschen?"
          message="Der Eintrag wird entfernt."
          onConfirm={onConfirm}
          onCancel={vi.fn()}
        />,
        isKiosk,
      ),
    );
  }

  it('confirms only after the press was held for the full two seconds', async () => {
    vi.useFakeTimers();
    const onConfirm = vi.fn();
    renderConfirm(onConfirm);
    await settle();
    const confirm = screen.getByTestId('confirm-dialog-confirm');

    // A tap — the phantom touch R-030 guards against — does nothing.
    tap(confirm);
    expect(onConfirm).not.toHaveBeenCalled();

    // Released a moment too early: still nothing.
    fireEvent.pointerDown(confirm, { button: 0 });
    act(() => void vi.advanceTimersByTime(KIOSK_LONG_PRESS_MS - 1));
    fireEvent.pointerUp(confirm, { button: 0 });
    fireEvent.click(confirm, { detail: 1 });
    expect(onConfirm).not.toHaveBeenCalled();

    // Held to the end: exactly one confirmation, the release adds none.
    fireEvent.pointerDown(confirm, { button: 0 });
    act(() => void vi.advanceTimersByTime(KIOSK_LONG_PRESS_MS));
    expect(onConfirm).toHaveBeenCalledTimes(1);
    fireEvent.pointerUp(confirm, { button: 0 });
    fireEvent.click(confirm, { detail: 1 });
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it('cancels the hold when the finger slides off the button', async () => {
    vi.useFakeTimers();
    const onConfirm = vi.fn();
    renderConfirm(onConfirm);
    await settle();
    const confirm = screen.getByTestId('confirm-dialog-confirm');

    fireEvent.pointerDown(confirm, { button: 0 });
    act(() => void vi.advanceTimersByTime(1000));
    fireEvent.pointerLeave(confirm);
    act(() => void vi.advanceTimersByTime(KIOSK_LONG_PRESS_MS));
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it('offers a keyboard path: Enter on the focused button confirms at once', async () => {
    const onConfirm = vi.fn();
    const user = userEvent.setup();
    renderConfirm(onConfirm);
    const confirm = await screen.findByTestId('confirm-dialog-confirm');

    confirm.focus();
    await user.keyboard('{Enter}');
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it('tells every user how to confirm — the hold visibly, the keyboard path to assistive technology', async () => {
    renderConfirm(vi.fn());
    const confirm = await screen.findByTestId('confirm-dialog-confirm');

    expect(confirm).toHaveAccessibleName('Löschen');
    expect(confirm).toHaveAccessibleDescription(/2 Sekunden gedrückt halten/);
    expect(confirm).toHaveAccessibleDescription(/Eingabe- oder Leertaste/);
    expect(screen.getByTestId('confirm-dialog-confirm-hint')).toBeVisible();
  });

  it('keeps the one-click confirmation outside kiosk mode', async () => {
    const onConfirm = vi.fn();
    const user = userEvent.setup();
    renderConfirm(onConfirm, false);

    await user.click(screen.getByTestId('confirm-dialog-confirm'));
    expect(onConfirm).toHaveBeenCalledTimes(1);
    expect(screen.queryByTestId('confirm-dialog-confirm-hint')).toBeNull();
  });
});

describe('kiosk quick-select tiles (UI-NFR-019 R-024..R-026)', () => {
  let latest: number | null = null;

  function EcForm() {
    const { control, watch } = useForm<{ ec: number | null }>({ defaultValues: { ec: null } });
    latest = watch('ec');
    return <FormNumberField name="ec" control={control} label="EC vorher" quickSelect={EC_QUICK_SELECT} />;
  }

  it('stores a preset with one tap and marks it pressed', async () => {
    const user = userEvent.setup();
    render(inKiosk(<EcForm />));

    const group = await screen.findByRole('group', { name: 'Schnellauswahl für EC vorher' });
    expect(group).toBeInTheDocument();
    const tile = screen.getByRole('button', { name: '1,5' });

    await user.click(tile);
    expect(latest).toBe(1.5);
    expect(tile).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByRole('button', { name: '2,0' })).toHaveAttribute('aria-pressed', 'false');
  });

  it('keeps the free entry as "Manuell" and moves the focus there (R-026)', async () => {
    const user = userEvent.setup();
    render(inKiosk(<EcForm />));

    await user.click(await screen.findByRole('button', { name: 'Manuell' }));
    expect(screen.getByRole('spinbutton', { name: 'EC vorher' })).toHaveFocus();
  });

  it('shows no tiles outside kiosk mode', () => {
    render(inKiosk(<EcForm />, false));
    expect(screen.getByRole('spinbutton', { name: 'EC vorher' })).toBeInTheDocument();
    expect(screen.queryByRole('group', { name: /Schnellauswahl/ })).toBeNull();
  });
});
