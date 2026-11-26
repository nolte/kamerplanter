import { act, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useForm } from 'react-hook-form';
import { Provider } from 'react-redux';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import i18n from 'i18next';
import { ThemeContextProvider } from '@/theme';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import FormNumberField from '@/components/form/FormNumberField';
import KioskShell from '@/layouts/KioskShell';
import { KioskContext, type KioskContextValue } from '@/kiosk/KioskProvider';
import { EC_QUICK_SELECT } from '@/kiosk/quickSelectPresets';
import { createTestStore } from '@/test/helpers';

/**
 * #3025 M16 review S1 — a kiosk tablet that goes offline must keep working: the shell preloads
 * every lazy kiosk chunk as soon as it mounts, and a chunk that cannot load (offline before the
 * preload) never leaves a destructive dialog with "Cancel" alone, nor breaks a number field.
 *
 * Here the two button/tile chunks fail as an offline `import()` would.
 */
const loaders = vi.hoisted(() => ({
  preload: vi.fn(() => Promise.resolve()),
}));

vi.mock('@/kiosk/kioskChunks', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/kiosk/kioskChunks')>();
  return {
    ...actual,
    loadLongPressButton: () => Promise.reject(new TypeError('Failed to fetch dynamically imported module')),
    loadKioskQuickSelect: () => Promise.reject(new TypeError('Failed to fetch dynamically imported module')),
    preloadKioskChunks: loaders.preload,
  };
});

function kioskValue(): KioskContextValue {
  return {
    isKiosk: true,
    highContrast: true,
    enableKiosk: vi.fn(),
    disableKiosk: vi.fn(),
    toggleKiosk: vi.fn(),
    setHighContrast: vi.fn(),
  };
}

function inKiosk(ui: React.ReactNode) {
  return (
    <Provider store={createTestStore()}>
      <KioskContext.Provider value={kioskValue()}>
        <ThemeContextProvider>{ui}</ThemeContextProvider>
      </KioskContext.Provider>
    </Provider>
  );
}

beforeEach(() => {
  i18n.changeLanguage('de');
  loaders.preload.mockClear();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe('kiosk chunks offline (#3025 M16 review S1)', () => {
  it('preloads every kiosk chunk when the kiosk shell mounts', async () => {
    const router = createMemoryRouter(
      [
        { path: '/giessprotokoll', element: <KioskShell><div /></KioskShell> },
        { path: '/kiosk', element: <div /> },
      ],
      { initialEntries: ['/giessprotokoll'] },
    );
    await act(async () => {
      render(inKiosk(<RouterProvider router={router} />));
    });
    expect(loaders.preload).toHaveBeenCalledTimes(1);
  });

  it('keeps a working confirm button in a destructive dialog when the hold chunk cannot load', async () => {
    const onConfirm = vi.fn();
    const user = userEvent.setup();
    render(
      inKiosk(
        <ConfirmDialog open destructive title="Löschen?" message="M" onConfirm={onConfirm} onCancel={vi.fn()} />,
      ),
    );

    // Present at once (the placeholder while loading), and enabled after the failed import.
    expect(screen.getByTestId('confirm-dialog-confirm')).toBeInTheDocument();
    await vi.waitFor(() => expect(screen.getByRole('button', { name: 'Löschen' })).toBeEnabled());
    await user.click(screen.getByRole('button', { name: 'Löschen' }));
    expect(onConfirm).toHaveBeenCalledTimes(1);
    expect(screen.getByRole('button', { name: 'Abbrechen' })).toBeInTheDocument();
  });

  it('keeps the number field usable when the quick-select chunk cannot load', async () => {
    function EcForm() {
      const { control } = useForm<{ ec: number | null }>({ defaultValues: { ec: null } });
      return <FormNumberField name="ec" control={control} label="EC vorher" quickSelect={EC_QUICK_SELECT} />;
    }
    const user = userEvent.setup();
    render(inKiosk(<EcForm />));

    const field = screen.getByRole('spinbutton', { name: 'EC vorher' });
    await user.type(field, '1.7');
    expect(field).toHaveValue(1.7);
    expect(screen.queryByRole('group', { name: /Schnellauswahl/ })).toBeNull();
  });
});
