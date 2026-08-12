import { useState, type ComponentProps } from 'react';
import { describe, it, expect, afterEach, beforeEach, vi } from 'vitest';
import { act, fireEvent, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe } from 'vitest-axe';
import { http, HttpResponse } from 'msw';
import { server } from '@/test/mocks/server';
import { renderWithProviders, createTestStore, type TestStore } from '@/test/helpers';
import ConnectDeviceDialog from '@/pages/auth/ConnectDeviceDialog';
import AccountSettingsPage from '@/pages/auth/AccountSettingsPage';
import { createDevicePairing } from '@/api/endpoints/auth';

/**
 * REQ-023 / #1118 — the "Connect mobile device" QR dialog.
 *
 * The code in the QR is a bearer credential with a ~90 s life: whoever scans it
 * gets a token pair for this account. Every property below is therefore an
 * assertion, not a comment in the component:
 *
 * - the QR carries the documented payload `{"v":…,"url":…,"code":…}`;
 * - the code appears in **no** visible text — a bystander must need a camera,
 *   not a glance (the issue's anti-shoulder-surfing requirement);
 * - the countdown really counts and the QR really disappears at zero, so a dead
 *   code never keeps looking scannable;
 * - a refresh replaces the rendered QR — the *rendered* one, not just the state;
 * - closing drops the code: not in Redux, not in storage, and re-opening has to
 *   ask the server again.
 *
 * `QRCodeSVG` is wrapped rather than replaced: the wrapper records the `value`
 * prop the component actually passes and then renders the real code. A stubbed
 * QR would let a payload bug through as long as *something* was handed over.
 */

const { qrValues } = vi.hoisted(() => ({ qrValues: [] as string[] }));

vi.mock('qrcode.react', async (importOriginal) => {
  const actual = await importOriginal<typeof import('qrcode.react')>();
  return {
    ...actual,
    QRCodeSVG: (props: ComponentProps<typeof actual.QRCodeSVG>) => {
      // qrcode.react v4 accepts a string or a segment array; the dialog passes
      // one string, and joining keeps the recorder faithful either way.
      qrValues.push(Array.isArray(props.value) ? props.value.join('') : props.value);
      return <actual.QRCodeSVG {...props} />;
    },
  };
});

// Only the issuance call is mocked; `listSessions` & co. stay real so the page
// test still exercises the genuine API layer through MSW.
vi.mock('@/api/endpoints/auth', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/api/endpoints/auth')>();
  return { ...actual, createDevicePairing: vi.fn() };
});

const mockCreatePairing = vi.mocked(createDevicePairing);

const CODE = 'first-code-Qm5kR2xoY0dWeUlHTnZaR1VnWm05eUlHRWc';
const SECOND_CODE = 'second-code-WkdWMmFXTmxJSEJoYVhKcGJtY2c';
const SERVER_URL = 'https://garten.example.org';
const TTL_SECONDS = 90;

function pairingResponse(code: string, expiresIn = TTL_SECONDS) {
  return {
    payload_version: 1,
    server_url: SERVER_URL,
    code,
    expires_at: new Date(Date.now() + expiresIn * 1000).toISOString(),
    expires_in: expiresIn,
  };
}

/** The `value` last handed to the QR renderer. */
function lastQrValue(): string {
  if (qrValues.length === 0) throw new Error('No QR code was rendered at all.');
  return qrValues[qrValues.length - 1];
}

/**
 * The path data of the QR currently on screen. Two different codes produce two
 * different modules, so this is what proves a *rendered* replacement rather than
 * a state change nobody can see.
 */
function renderedQrPath(): string {
  const paths = Array.from(
    document.querySelectorAll('[data-testid="device-pairing-qr"] svg path[d]'),
  );
  // The first path is the plain background square and is identical for every
  // code — reading only that one would make the comparison below vacuous. The
  // modules path is what encodes the payload, so both must be present.
  if (paths.length < 2) {
    throw new Error(`Expected a QR modules path, found ${paths.length} path(s).`);
  }
  return paths.map((path) => path.getAttribute('d') ?? '').join('|');
}

/**
 * jsdom in this environment ships no native Web Storage (same reason
 * `useTableState.test.ts` and `dashboardLayoutStorage.test.ts` stub it). A
 * map-backed stub is not just a shim here: it *records every write*, which is
 * what gives the "the code never reaches storage" assertion something real to
 * look at instead of an API that silently does nothing.
 */
function createMemoryStorage(): Storage {
  const entries = new Map<string, string>();
  return {
    get length() {
      return entries.size;
    },
    key: (index: number) => Array.from(entries.keys())[index] ?? null,
    getItem: (key: string) => entries.get(key) ?? null,
    setItem: (key: string, value: string) => {
      entries.set(key, String(value));
    },
    removeItem: (key: string) => {
      entries.delete(key);
    },
    clear: () => {
      entries.clear();
    },
  } as Storage;
}

Object.defineProperty(globalThis, 'localStorage', {
  value: createMemoryStorage(),
  writable: true,
});
Object.defineProperty(globalThis, 'sessionStorage', {
  value: createMemoryStorage(),
  writable: true,
});

function storageDump(storage: Storage): string {
  return Array.from({ length: storage.length }, (_, index) => {
    const key = storage.key(index) ?? '';
    return `${key}=${storage.getItem(key) ?? ''}`;
  }).join('\n');
}

/** Host with the open/close state the real page owns. */
function DialogHost() {
  const [open, setOpen] = useState(true);
  return (
    <>
      <button type="button" data-testid="host-reopen" onClick={() => setOpen(true)}>
        reopen
      </button>
      <ConnectDeviceDialog open={open} onClose={() => setOpen(false)} />
    </>
  );
}

function renderDialog(store: TestStore = createTestStore()) {
  return renderWithProviders(<DialogHost />, { store });
}

const AUTH_USER = {
  key: 'user-1',
  display_name: 'Tester',
  email: 'tester@example.org',
  locale: 'de',
  timezone: 'Europe/Berlin',
};

const BROWSER_SESSION = {
  key: 'sess-browser',
  user_agent: 'Mozilla/5.0 (X11; Linux x86_64) Firefox/141.0',
  device_name: null,
  ip_address: '198.51.100.4',
  created_at: '2026-08-10T09:00:00Z',
  expires_at: '2026-08-11T09:00:00Z',
  is_current: true,
  is_persistent: false,
};

/** The account settings page, opened on its sessions tab. */
function renderSessionsTab() {
  const prefs = {
    experience_level: 'expert',
    locale: 'de',
    theme: 'light',
    smart_home_enabled: false,
  };
  server.use(
    http.get('/api/v1/users/me/sessions', () => HttpResponse.json([BROWSER_SESSION])),
    http.get('/api/v1/users/me/providers', () => HttpResponse.json([])),
    http.get('/api/v1/auth/api-keys', () => HttpResponse.json([])),
    http.get('/api/v1/t/:tenant/user-preferences', () => HttpResponse.json(prefs)),
    http.get('/api/v1/user-preferences', () => HttpResponse.json(prefs)),
  );
  return renderWithProviders(<AccountSettingsPage />, {
    store: createTestStore({
      auth: {
        user: AUTH_USER,
        accessToken: 'tok',
        isAuthenticated: true,
        isLoading: false,
        error: null,
      },
    }),
    route: '/account#sessions',
  });
}

beforeEach(() => {
  qrValues.length = 0;
  mockCreatePairing.mockReset();
  localStorage.clear();
});

afterEach(() => {
  vi.useRealTimers();
});

describe('ConnectDeviceDialog — reaching it from the sessions tab', () => {
  it('opens from the sessions tab and shows a QR code for a fresh pairing code', async () => {
    mockCreatePairing.mockResolvedValue(pairingResponse(CODE));
    const user = userEvent.setup();
    renderSessionsTab();

    // The button lives with the sessions, which is the surface that also lists
    // and revokes the device once it is paired.
    await user.click(await screen.findByTestId('connect-device-button'));

    expect(await screen.findByTestId('connect-device-dialog')).toBeInTheDocument();
    expect(await screen.findByTestId('device-pairing-qr')).toBeInTheDocument();
    expect(lastQrValue()).toContain(CODE);
    // No code is minted before the user asks for one.
    expect(mockCreatePairing).toHaveBeenCalledTimes(1);
  });

  it('does not mint a code just because the sessions tab is open', async () => {
    mockCreatePairing.mockResolvedValue(pairingResponse(CODE));
    renderSessionsTab();

    await screen.findByTestId('connect-device-button');

    expect(mockCreatePairing).not.toHaveBeenCalled();
    expect(qrValues).toHaveLength(0);
  });
});

describe('ConnectDeviceDialog — accessibility', () => {
  it('exposes a labelled dialog and a QR with a text alternative', async () => {
    mockCreatePairing.mockResolvedValue(pairingResponse(CODE));
    renderDialog();
    await screen.findByTestId('device-pairing-qr');

    // The accessible name comes from the title via `aria-labelledby`; a screen
    // reader landing in this dialog must be told what it is.
    expect(screen.getByRole('dialog', { name: /connect mobile device/i })).toBeInTheDocument();
    // The QR is pure graphics — without a title it is an unlabelled image.
    expect(screen.getByTitle(/qr code for connecting a mobile device/i)).toBeInTheDocument();
    // The close action is reachable by role, not only by test id.
    expect(screen.getByRole('button', { name: /close/i })).toBeInTheDocument();
  });

  it('has no critical accessibility violations', async () => {
    mockCreatePairing.mockResolvedValue(pairingResponse(CODE));
    renderDialog();
    await screen.findByTestId('device-pairing-qr');

    // The dialog renders into a portal, so the scan starts at the document body
    // rather than at the render container.
    const results = await axe(document.body);

    expect(results.violations.filter((violation) => violation.impact === 'critical')).toEqual([]);
  });
});

describe('ConnectDeviceDialog — QR payload', () => {
  it('encodes exactly the documented payload contract', async () => {
    mockCreatePairing.mockResolvedValue(pairingResponse(CODE));
    renderDialog();

    await screen.findByTestId('device-pairing-qr');

    const payload: unknown = JSON.parse(lastQrValue());
    expect(payload).toEqual({ v: 1, url: SERVER_URL, code: CODE });
    // The shape is the contract a future scanner parses: no extra field may
    // ride along (an `expires_at` here would leak into every printed QR).
    expect(Object.keys(payload as Record<string, unknown>)).toEqual(['v', 'url', 'code']);
  });

  it('never renders the code as readable text', async () => {
    mockCreatePairing.mockResolvedValue(pairingResponse(CODE));
    renderDialog();

    const dialog = await screen.findByTestId('connect-device-dialog');
    await screen.findByTestId('device-pairing-qr');

    // Positive half first, so this cannot pass by the code being absent
    // altogether: it IS in the QR …
    expect(lastQrValue()).toContain(CODE);
    // … and nowhere a bystander, a screen recording or a screenshot can read it.
    expect(screen.queryByText(CODE)).toBeNull();
    expect(dialog.textContent ?? '').not.toContain(CODE);
    expect(document.body.textContent ?? '').not.toContain(CODE);
  });
});

describe('ConnectDeviceDialog — countdown and expiry', () => {
  it('counts the remaining seconds down from the server-supplied value', async () => {
    vi.useFakeTimers();
    mockCreatePairing.mockResolvedValue(pairingResponse(CODE, 90));
    renderDialog();
    await act(async () => {});

    const countdown = screen.getByTestId('device-pairing-countdown');
    // Seeded from `expires_in` — the server's own remaining-seconds figure, not
    // a value recomputed from `expires_at` against this browser's clock.
    expect(countdown).toHaveTextContent('90');

    act(() => {
      vi.advanceTimersByTime(3000);
    });

    expect(screen.getByTestId('device-pairing-countdown')).toHaveTextContent('87');
  });

  it('replaces the QR with an expired state and a refresh action at zero', async () => {
    vi.useFakeTimers();
    mockCreatePairing.mockResolvedValue(pairingResponse(CODE, 3));
    renderDialog();
    await act(async () => {});

    expect(screen.getByTestId('device-pairing-qr')).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(3000);
    });

    expect(screen.getByTestId('device-pairing-expired')).toBeInTheDocument();
    expect(screen.getByTestId('device-pairing-refresh')).toBeInTheDocument();
    // A dead code that still looks scannable is the failure the user cannot
    // diagnose: the QR has to be gone, not merely greyed out.
    expect(screen.queryByTestId('device-pairing-qr')).toBeNull();
    expect(screen.queryByTestId('device-pairing-countdown')).toBeNull();
  });

  it('stops ticking once expired instead of counting into negative seconds', async () => {
    vi.useFakeTimers();
    mockCreatePairing.mockResolvedValue(pairingResponse(CODE, 2));
    renderDialog();
    await act(async () => {});

    act(() => {
      vi.advanceTimersByTime(60_000);
    });

    expect(screen.getByTestId('device-pairing-expired')).toBeInTheDocument();
    expect(mockCreatePairing).toHaveBeenCalledTimes(1);
  });
});

describe('ConnectDeviceDialog — refreshing', () => {
  it('requests a new code and replaces the rendered QR', async () => {
    vi.useFakeTimers();
    mockCreatePairing
      .mockResolvedValueOnce(pairingResponse(CODE, 2))
      .mockResolvedValueOnce(pairingResponse(SECOND_CODE, 90));
    renderDialog();
    await act(async () => {});
    const firstQrPath = renderedQrPath();

    act(() => {
      vi.advanceTimersByTime(2000);
    });
    // `fireEvent`, not `userEvent`: userEvent's own internal delay is itself a
    // faked timer, and pairing it with the frozen clock this test needs turns
    // the click into a wait that never returns.
    fireEvent.click(screen.getByTestId('device-pairing-refresh'));
    await act(async () => {});

    expect(mockCreatePairing).toHaveBeenCalledTimes(2);
    expect(lastQrValue()).toContain(SECOND_CODE);
    // The previous code is gone from the payload *and* from the pixels: a
    // refresh that only updated state would leave the old QR scannable.
    expect(lastQrValue()).not.toContain(CODE);
    expect(renderedQrPath()).not.toBe(firstQrPath);
    expect(document.body.textContent ?? '').not.toContain(CODE);
    // The fresh code restarts the countdown rather than inheriting the old one.
    expect(screen.getByTestId('device-pairing-countdown')).toHaveTextContent('90');
  });

  it('shows no QR at all while the replacement code is in flight', async () => {
    vi.useFakeTimers();
    let release: ((value: ReturnType<typeof pairingResponse>) => void) | undefined;
    mockCreatePairing
      .mockResolvedValueOnce(pairingResponse(CODE, 1))
      .mockReturnValueOnce(
        new Promise((resolve) => {
          release = resolve;
        }),
      );
    renderDialog();
    await act(async () => {});
    act(() => {
      vi.advanceTimersByTime(1000);
    });

    fireEvent.click(screen.getByTestId('device-pairing-refresh'));
    await act(async () => {});

    // In between the two codes there is a pending state, and it shows as one —
    // no leftover QR from the dead code, and no bare frame either.
    expect(screen.getByTestId('loading-skeleton')).toBeInTheDocument();
    expect(screen.queryByTestId('device-pairing-qr')).toBeNull();
    expect(document.body.textContent ?? '').not.toContain(CODE);

    await act(async () => {
      release?.(pairingResponse(SECOND_CODE, 90));
    });

    expect(screen.getByTestId('device-pairing-qr')).toBeInTheDocument();
    expect(lastQrValue()).toContain(SECOND_CODE);
  });
});

describe('ConnectDeviceDialog — the code does not outlive the dialog', () => {
  it('discards the code on close and asks for a new one when re-opened', async () => {
    mockCreatePairing
      .mockResolvedValueOnce(pairingResponse(CODE))
      .mockResolvedValueOnce(pairingResponse(SECOND_CODE));
    const user = userEvent.setup();
    renderDialog();
    await screen.findByTestId('device-pairing-qr');

    await user.click(screen.getByTestId('connect-device-close'));
    // Checked synchronously, not behind a `waitFor`: the QR is gone the moment
    // the user closes, with no window in which it lingers on screen.
    expect(screen.queryByTestId('device-pairing-qr')).toBeNull();
    await waitFor(() => expect(screen.queryByTestId('connect-device-dialog')).toBeNull());
    expect(document.body.textContent ?? '').not.toContain(CODE);

    await user.click(screen.getByTestId('host-reopen'));
    await screen.findByTestId('device-pairing-qr');

    // Re-opening had to go back to the server: a retained code would have been
    // re-rendered instead, and it would already be worthless (single use, and
    // most of its 90 s spent).
    expect(mockCreatePairing).toHaveBeenCalledTimes(2);
    expect(lastQrValue()).toContain(SECOND_CODE);
    expect(lastQrValue()).not.toContain(CODE);
  });

  it('drops a code that arrives after the dialog was closed and re-opened', async () => {
    // Two issuance calls left deliberately in flight, resolved out of order:
    // the request the user abandoned answers *after* the one they are waiting
    // for was issued. Without a sequence guard the abandoned answer wins the
    // race and the dialog proudly renders a code from a session the user has
    // already walked away from — stale, and quite possibly already expired.
    let releaseAbandoned: ((value: ReturnType<typeof pairingResponse>) => void) | undefined;
    let releaseCurrent: ((value: ReturnType<typeof pairingResponse>) => void) | undefined;
    mockCreatePairing
      .mockReturnValueOnce(
        new Promise((resolve) => {
          releaseAbandoned = resolve;
        }),
      )
      .mockReturnValueOnce(
        new Promise((resolve) => {
          releaseCurrent = resolve;
        }),
      );
    const user = userEvent.setup();
    renderDialog();
    await screen.findByTestId('loading-skeleton');

    await user.click(screen.getByTestId('connect-device-close'));
    await user.click(screen.getByTestId('host-reopen'));
    await act(async () => {
      releaseCurrent?.(pairingResponse(SECOND_CODE));
    });
    expect(lastQrValue()).toContain(SECOND_CODE);

    // The abandoned request answers last. It must be dropped, not painted over
    // the code the user is currently holding up to a camera.
    await act(async () => {
      releaseAbandoned?.(pairingResponse(CODE));
    });

    expect(screen.getByTestId('device-pairing-qr')).toBeInTheDocument();
    expect(lastQrValue()).toContain(SECOND_CODE);
    expect(qrValues.some((value) => value.includes(CODE))).toBe(false);
  });

  it('keeps the code out of the Redux store and out of browser storage', async () => {
    mockCreatePairing.mockResolvedValue(pairingResponse(CODE));
    const store = createTestStore();
    const pristineState = JSON.stringify(store.getState());
    // Sentinel: proves the storage dump below actually reads something, so an
    // empty dump cannot make the negative assertions pass vacuously.
    localStorage.setItem('pairing-test-sentinel', 'sentinel-value');
    const user = userEvent.setup();
    renderDialog(store);
    await screen.findByTestId('device-pairing-qr');

    expect(JSON.stringify(store.getState())).not.toContain(CODE);

    await user.click(screen.getByTestId('connect-device-close'));
    await waitFor(() => expect(screen.queryByTestId('connect-device-dialog')).toBeNull());

    // Not one action was dispatched: the credential never entered global state.
    expect(JSON.stringify(store.getState())).toBe(pristineState);
    const dump = storageDump(localStorage);
    expect(dump).toContain('sentinel-value');
    expect(dump).not.toContain(CODE);
    expect(storageDump(sessionStorage)).not.toContain(CODE);
  });
});

describe('ConnectDeviceDialog — failure and loading states', () => {
  it('shows a retryable error instead of an empty frame when issuance fails', async () => {
    mockCreatePairing.mockRejectedValueOnce(new Error('Internal error'));
    mockCreatePairing.mockResolvedValueOnce(pairingResponse(CODE));
    const user = userEvent.setup();
    renderDialog();

    const error = await screen.findByTestId('device-pairing-error');
    expect(error).toBeInTheDocument();
    expect(screen.queryByTestId('device-pairing-qr')).toBeNull();

    await user.click(screen.getByTestId('error-retry-button'));

    expect(await screen.findByTestId('device-pairing-qr')).toBeInTheDocument();
    expect(lastQrValue()).toContain(CODE);
  });

  it('shows a loading placeholder while the code is in flight', async () => {
    let release: ((value: ReturnType<typeof pairingResponse>) => void) | undefined;
    mockCreatePairing.mockReturnValueOnce(
      new Promise((resolve) => {
        release = resolve;
      }),
    );
    renderDialog();

    // A pending QR and an absent QR must not look the same (UI-NFR-004 R-020).
    expect(await screen.findByTestId('loading-skeleton')).toBeInTheDocument();
    expect(screen.queryByTestId('device-pairing-qr')).toBeNull();

    await act(async () => {
      release?.(pairingResponse(CODE));
    });

    expect(screen.getByTestId('device-pairing-qr')).toBeInTheDocument();
    expect(screen.queryByTestId('loading-skeleton')).toBeNull();
  });
});
