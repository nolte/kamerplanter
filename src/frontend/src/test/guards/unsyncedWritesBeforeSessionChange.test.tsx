import 'fake-indexeddb/auto';
import { act, cleanup, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import { http, HttpResponse } from 'msw';
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest';
import { setActiveTenantSlug } from '@/api/client';
import TenantSwitcher from '@/components/layout/TenantSwitcher';
import { listEntries } from '@/features/gardenPlanner/offline/queue';
import MainLayout from '@/layouts/MainLayout';
import { configureStore } from '@reduxjs/toolkit';
import { rootReducer } from '@/store/rootReducer';
import { sessionListener } from '@/store/sessionListener';
import { renderWithProviders } from '@/test/helpers';
import { server } from '@/test/mocks/server';
import { BOB_A, capture, emptyWriteQueue, noteWrite, retireFromOtherTab, testWriteQueueDatabase } from '@/test/writeQueueTestKit';

/**
 * REQ-053 WP 9.4 (#2744), G-W9 (b) with UI-NFR-012 R-050/R-051: an explicit logout discards the user's unsent
 * offline entries (in every tenant, no one else's), so it asks first — the dialog names the count, sends first
 * when there is a connection, and offers "discard and log out" or "cancel". With nothing buffered nobody is asked.
 * A tenant switch does not ask and does not discard: the entries stay bound to their tenant.
 */

const SCOPE = { userKey: 'alice', tenantKey: 'tenant_a' };
const TENANT_A = { key: 'tenant_a', slug: 'garten-a', name: 'Garten A', tenant_type: 'personal', role: 'lead' };
const TENANT_B = { key: 'tenant_b', slug: 'garten-b', name: 'Garten B', tenant_type: 'organization', role: 'grower' };

function setOnline(value: boolean) {
  Object.defineProperty(window.navigator, 'onLine', { configurable: true, get: () => value });
  act(() => {
    window.dispatchEvent(new Event(value ? 'online' : 'offline'));
  });
}

/** The real reducer and session listener: the logout's clearing runs as in the app. */
function store() {
  return configureStore({
    reducer: rootReducer,
    middleware: (getDefault) => getDefault().prepend(sessionListener.middleware),
    preloadedState: {
    auth: {
      user: { key: 'alice', email: 'alice@example.org', display_name: 'Alice', avatar_url: null },
      isAuthenticated: true,
      isLoading: false,
      error: null,
      initialized: true,
    },
    tenants: { activeTenant: TENANT_A, myTenants: [TENANT_A, TENANT_B], isLoading: false, error: null },
    } as never,
  }) as never as ReturnType<typeof import('@/test/helpers').createTestStore>;
}

async function logOut(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole('button', { name: 'Konto-Menü' }));
  await user.click(screen.getByRole('menuitem', { name: 'Abmelden' }));
}

beforeAll(() => setActiveTenantSlug('garten-a'));

beforeEach(async () => {
  await emptyWriteQueue();
  await i18n.changeLanguage('de');
  const storage = new Map<string, string>();
  vi.stubGlobal('localStorage', {
    getItem: (k: string) => (storage.has(k) ? storage.get(k)! : null),
    setItem: (k: string, v: string) => storage.set(k, String(v)),
    removeItem: (k: string) => storage.delete(k),
    clear: () => storage.clear(),
  });
  server.use(http.get('/api/v1/t/:tenant/notifications/count', () => HttpResponse.json({ unread_count: 0 })));
});

afterEach(() => {
  setOnline(true);
  vi.unstubAllGlobals();
  cleanup();
});

describe('logout (MainLayout)', () => {
  it('names the entries not sent yet (all tenants of the user) and discards only them after "discard"', async () => {
    setOnline(false);
    await capture(SCOPE, noteWrite('one'));
    await capture({ userKey: 'alice', tenantKey: 'tenant_b' }, noteWrite('two'));
    await capture(BOB_A, noteWrite('bob'));
    const user = userEvent.setup();
    const { store: appStore } = renderWithProviders(<MainLayout />, { store: store() });

    await logOut(user);
    const dialog = await screen.findByTestId('unsynced-writes-dialog');
    expect(within(dialog).getByTestId('unsynced-writes-count')).toHaveTextContent(
      '2 Einträge sind noch nicht übertragen (auch aus anderen Gärten). Beim Abmelden werden sie von diesem Gerät gelöscht.',
    );
    // Offline, "send now" is off and the dialog says why; cancel and discard stay (UI-NFR-012 R-060).
    expect(within(dialog).getByTestId('unsynced-writes-sync')).toBeDisabled();
    expect(within(dialog).getByTestId('unsynced-writes-offline')).toHaveTextContent(
      'Keine Verbindung – „Jetzt übertragen“ geht erst wieder, wenn du online bist. Du kannst abbrechen oder die Einträge verwerfen und dich abmelden.',
    );
    expect(within(dialog).getByTestId('unsynced-writes-cancel')).toBeEnabled();
    expect(within(dialog).getByTestId('unsynced-writes-discard')).toBeEnabled();
    expect(appStore.getState().auth.user).not.toBeNull();

    await user.click(within(dialog).getByTestId('unsynced-writes-cancel'));
    await waitFor(() => expect(screen.queryByTestId('unsynced-writes-dialog')).toBeNull());
    expect(appStore.getState().auth.user).not.toBeNull();

    await logOut(user);
    await user.click(within(await screen.findByTestId('unsynced-writes-dialog')).getByTestId('unsynced-writes-discard'));
    await waitFor(() => expect(appStore.getState().auth.user).toBeNull());
    // Read the rows themselves: while the clearing runs the buffer answers nothing at all.
    const owners = async () => (await testWriteQueueDatabase().entries.toArray()).map((row) => `${row.userKey}/${row.tenantKey}`);
    // Another user's unsent entries on the same device are not alice's to discard.
    await waitFor(async () => expect(await owners()).toEqual(['bob/tenant_a']));
  });

  it('sends first when online and logs out by itself once nothing is left', async () => {
    const ids: unknown[] = [];
    server.use(
      http.post('/api/v1/t/:tenant/care-events', async ({ request }) => {
        ids.push(((await request.json()) as { client_event_id?: unknown }).client_event_id);
        return HttpResponse.json({ key: 'ce_1', category: 'note' }, { status: 201 });
      }),
    );
    // Captured offline; the app came back online before the logout.
    const entry = await capture(SCOPE, noteWrite('one'));
    const user = userEvent.setup();
    const { store: appStore } = renderWithProviders(<MainLayout />, { store: store() });
    await logOut(user);
    await waitFor(() => expect(appStore.getState().auth.user).toBeNull());
    expect(ids).toContain(entry.id);
    expect(await listEntries(SCOPE)).toEqual([]);
  });

  it('asks without a number — never discards unasked — when the buffer cannot be counted (R-056 c)', async () => {
    setOnline(false);
    await capture(SCOPE, noteWrite('one'));
    const user = userEvent.setup();
    const { store: appStore } = renderWithProviders(<MainLayout />, { store: store() });
    await retireFromOtherTab('alice'); // another tab ended this session: this tab may not read the buffer now
    await logOut(user);
    const dialog = await screen.findByTestId('unsynced-writes-dialog');
    expect(within(dialog).getByTestId('unsynced-writes-count')).toHaveTextContent(
      'Ob noch Einträge auf Übertragung warten, ließ sich gerade nicht prüfen.',
    );
    expect(appStore.getState().auth.user).not.toBeNull();
    await user.click(within(dialog).getByTestId('unsynced-writes-cancel'));
    expect(appStore.getState().auth.user).not.toBeNull();
    expect(await testWriteQueueDatabase().entries.count()).toBe(1);
  });

  it('asks nobody when the buffer is empty', async () => {
    const user = userEvent.setup();
    const { store: appStore } = renderWithProviders(<MainLayout />, { store: store() });
    await logOut(user);
    await waitFor(() => expect(appStore.getState().auth.user).toBeNull());
    expect(screen.queryByTestId('unsynced-writes-dialog')).toBeNull();
  });
});

describe('tenant switch (TenantSwitcher)', () => {
  let reload: ReturnType<typeof vi.fn>;
  let originalLocation: Location;

  beforeEach(() => {
    originalLocation = window.location;
    reload = vi.fn();
    Object.defineProperty(window, 'location', { configurable: true, value: { ...originalLocation, reload } });
  });

  afterEach(() => {
    Object.defineProperty(window, 'location', { configurable: true, value: originalLocation });
  });

  it('neither asks nor discards: the entries stay bound to the previous tenant', async () => {
    setOnline(false);
    const entry = await capture(SCOPE, noteWrite('one'));
    const user = userEvent.setup();
    const { store: appStore } = renderWithProviders(<TenantSwitcher />, { store: store() });
    await user.click(screen.getByRole('button', { name: /Garten A/ }));
    await user.click(screen.getByTestId('tenant-switcher-item-garten-b'));
    await waitFor(() => expect(reload).toHaveBeenCalledTimes(1));
    expect(screen.queryByTestId('unsynced-writes-dialog')).toBeNull();
    expect(appStore.getState().tenants.activeTenant?.slug).toBe('garten-b');
    expect((await listEntries(SCOPE)).map((row) => row.id)).toEqual([entry.id]);
    // Nothing of tenant A shows in tenant B.
    expect(await listEntries({ userKey: 'alice', tenantKey: 'tenant_b' })).toEqual([]);
  });
});

describe('the logout dialog while it waits (review 2)', () => {
  it('keeps "Cancel" usable while the sync hangs', async () => {
    let release: () => void = () => undefined;
    server.use(
      http.post('/api/v1/t/:tenant/care-events', async () => {
        await new Promise<void>((resolve) => {
          release = resolve;
        });
        return HttpResponse.json({ key: 'ce_1', category: 'note' }, { status: 201 });
      }),
    );
    await capture(SCOPE, noteWrite('one'));
    const { default: UnsyncedWritesDialog } = await import('@/features/gardenPlanner/offline/UnsyncedWritesDialog');
    const onCancel = vi.fn();
    const onProceed = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(
      <UnsyncedWritesDialog userKey="alice" scope={SCOPE} count={1} onProceed={onProceed} onCancel={onCancel} />,
      { store: store() },
    );
    const dialog = await screen.findByTestId('unsynced-writes-dialog');
    await waitFor(() => expect(within(dialog).getByTestId('unsynced-writes-sync')).toBeDisabled()); // syncing
    expect(within(dialog).getByTestId('unsynced-writes-cancel')).toBeEnabled();
    await user.click(within(dialog).getByTestId('unsynced-writes-cancel'));
    expect(onCancel).toHaveBeenCalledTimes(1);
    expect(onProceed).not.toHaveBeenCalled();
    release();
    // The released sync still finishes; wait for it, or its state update lands after the test environment is gone
    // ("window is not defined" as an unhandled rejection that fails the whole run). A cancelled sync never logs out.
    await waitFor(() => expect(within(dialog).getByTestId('unsynced-writes-discard')).toBeEnabled());
    expect(onProceed).not.toHaveBeenCalled();
  });
});
