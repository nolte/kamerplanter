import 'fake-indexeddb/auto';
import { configureStore } from '@reduxjs/toolkit';
import { act, cleanup, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import { http, HttpResponse } from 'msw';
import { SnackbarProvider } from 'notistack';
import { Provider } from 'react-redux';
import { afterEach, beforeAll, beforeEach, describe, expect, it } from 'vitest';
import { setActiveTenantSlug } from '@/api/client';
import { rootReducer } from '@/store/rootReducer';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { authState, tenantState } from '@/test/helpers';
import { server } from '@/test/mocks/server';
import { capture, completeWrite, emptyWriteQueue, noteWrite, storeRow } from '@/test/writeQueueTestKit';
import { ThemeContextProvider } from '@/theme';
import OfflineSyncHost from './OfflineSyncHost';
import { listEntries, purgeExpiredEntries, updateEntry } from './queue';
import type { ConflictCode } from './queueTypes';

/**
 * REQ-053 WP 9.4 (#2744), UI-NFR-012 R-024/R-025/R-028…R-032/R-052 — the app-wide sync host: a buffered entry is
 * sent once the connection is there and the success is announced; every WP 9.3 conflict code opens the conflict
 * dialog, "Keep" leaves the entry on the device without resending it, "Discard" removes it; failed entries offer
 * "Try again" with the same id; the dialog passes axe; the counts land in `offlineSlice`.
 */

const BASE = '/api/v1/t/:tenant';
/** The scope of `authState()` + `tenantState()`. */
const SCOPE = { userKey: 'user-1', tenantKey: 'tenant-1' };

function setOnline(value: boolean) {
  Object.defineProperty(window.navigator, 'onLine', { configurable: true, get: () => value });
  act(() => {
    window.dispatchEvent(new Event(value ? 'online' : 'offline'));
  });
}

function renderHost() {
  const store = configureStore({
    reducer: rootReducer,
    preloadedState: { ...tenantState('grower'), ...authState() } as never,
  });
  render(
    <Provider store={store}>
      <ThemeContextProvider>
        <SnackbarProvider>
          <OfflineSyncHost />
        </SnackbarProvider>
      </ThemeContextProvider>
    </Provider>,
  );
  return store;
}

async function conflictEntry(code: ConflictCode, write = completeWrite()) {
  const entry = await capture(SCOPE, write);
  await updateEntry(SCOPE, entry.seq!, { status: 'conflict', conflictCode: code, lastErrorCode: code });
  return entry;
}

beforeAll(() => setActiveTenantSlug('testgarten'));

beforeEach(async () => {
  await emptyWriteQueue();
  await i18n.changeLanguage('de');
});

afterEach(() => {
  setOnline(true);
  cleanup();
});

describe('sync on connection (R-021, R-025)', () => {
  it('sends a buffered note once online, says so and empties the buffer', async () => {
    const bodies: unknown[] = [];
    server.use(
      http.post(`${BASE}/care-events`, async ({ request }) => {
        bodies.push(await request.json());
        return HttpResponse.json({ key: 'ce_1', category: 'note' }, { status: 201 });
      }),
    );
    setOnline(false);
    const entry = await capture(SCOPE, noteWrite('Snails at the lettuce'));
    const store = renderHost();
    expect(await screen.findByTestId('offline-queue-chip')).toHaveTextContent('1 nicht übertragen');
    expect(bodies).toHaveLength(0);
    await waitFor(() => expect(store.getState().offline.counts.pending).toBe(1));

    setOnline(true);
    expect(await screen.findByText('1 Eintrag übertragen.')).toBeInTheDocument();
    expect(bodies).toEqual([expect.objectContaining({ summary: 'Snails at the lettuce', client_event_id: entry.id })]);
    await waitFor(() => expect(screen.queryByTestId('offline-queue-chip')).toBeNull());
    expect(await listEntries(SCOPE)).toEqual([]);
    expect(store.getState().offline.lastSyncAt).not.toBeNull();
  });
});

describe('retention notice (UI-NFR-012 R-056)', () => {
  const DAY = 24 * 60 * 60 * 1000;

  it('names how many of my entries the app-start purge deleted — never a silent drop, never another user\'s', async () => {
    setOnline(false);
    await storeRow(SCOPE, { capturedAt: Date.now() - 366 * DAY });
    await storeRow(SCOPE, { capturedAt: Date.now() - 100 * DAY, status: 'failed' }); // undecided for 90+ days
    await storeRow({ userKey: 'someone-else', tenantKey: 'tenant-1' }, { capturedAt: Date.now() - 400 * DAY });
    await capture(SCOPE, noteWrite('recent'));
    expect(await purgeExpiredEntries()).toBe(3); // as main.tsx does at start, before anyone is signed in
    renderHost();
    expect(
      await screen.findByText(
        '2 nicht übertragene Einträge waren älter als ein Jahr und wurden von diesem Gerät gelöscht – der Server nimmt so alte Einträge nicht mehr an.',
      ),
    ).toBeInTheDocument();
    expect(await listEntries(SCOPE)).toHaveLength(1);
  });
});

describe('retention without the start-up purge (review 10)', () => {
  it('purges and names the count once the user is signed in, also when main.tsx could not purge', async () => {
    setOnline(false);
    await storeRow(SCOPE, { capturedAt: Date.now() - 400 * 24 * 60 * 60 * 1000 });
    renderHost();
    expect(await screen.findByText(/1 nicht übertragener Eintrag war älter als ein Jahr/)).toBeInTheDocument();
    expect(await listEntries(SCOPE)).toEqual([]);
  });
});

describe('owner scope (G-W9 a, UI-NFR-012 R-050/R-051)', () => {
  it("neither shows nor sends another user's or another tenant's entries kept on the device", async () => {
    const bodies: unknown[] = [];
    server.use(
      http.post(`${BASE}/care-events`, async ({ request }) => {
        bodies.push(await request.json());
        return HttpResponse.json({ key: 'ce_1', category: 'note' }, { status: 201 });
      }),
    );
    await capture({ userKey: 'someone-else', tenantKey: 'tenant-1' }, noteWrite('not mine'));
    await capture({ userKey: 'user-1', tenantKey: 'tenant-2' }, noteWrite('other garden'));
    const store = renderHost();
    // The total is the user's own (both tenants), never another user's rows.
    await waitFor(() => expect(store.getState().offline.counts.total).toBe(1));
    expect(store.getState().offline.counts.pending).toBe(0);
    expect(screen.queryByTestId('offline-queue-chip')).toBeNull();
    act(() => {
      window.dispatchEvent(new Event('focus'));
    });
    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(bodies).toEqual([]);
  });
});

describe('conflict dialog (R-028…R-032)', () => {
  it.each<[ConflictCode, string]>([
    ['client_event.payload_mismatch', 'passt nicht zu dem'],
    ['task.already_closed', 'schon erledigt oder übersprungen'],
    ['task.missing', 'gibt es nicht mehr'],
    ['client_event.deleted', 'wurde inzwischen gelöscht'],
  ])('opens by itself for %s and names the reason', async (code, reason) => {
    const entry = await conflictEntry(code);
    renderHost();
    const dialog = await screen.findByTestId('offline-conflict-dialog');
    expect(within(dialog).getByTestId(`offline-entry-reason-${entry.id}`)).toHaveTextContent(reason);
    expect(within(dialog).getByText('Erledigt: Water the bed')).toBeInTheDocument();
    expect(within(dialog).getByTestId(`offline-entry-keep-${entry.id}`)).toBeInTheDocument();
    expect(within(dialog).getByTestId(`offline-entry-discard-${entry.id}`)).toBeInTheDocument();
  });

  it('"Keep" leaves the entry on the device, readable, never resent; "Discard" removes it', async () => {
    let sent = 0;
    server.use(
      http.post(`${BASE}/care-events`, () => {
        sent += 1;
        return HttpResponse.json({ key: 'ce_1', category: 'note' }, { status: 201 });
      }),
    );
    const entry = await conflictEntry('client_event.deleted', noteWrite('Mildew on the courgettes'));
    const user = userEvent.setup();
    renderHost();
    const dialog = await screen.findByTestId('offline-conflict-dialog');
    expect(within(dialog).getByText('Mildew on the courgettes')).toBeInTheDocument();

    await user.click(within(dialog).getByTestId(`offline-entry-keep-${entry.id}`));
    // The only conflict is decided: the dialog closes; the chip still names the kept entry.
    await waitFor(() => expect(screen.queryByTestId('offline-conflict-dialog')).toBeNull());
    expect((await listEntries(SCOPE))[0]).toMatchObject({ id: entry.id, status: 'conflict', kept: true });
    await user.click(await screen.findByTestId('offline-queue-chip'));
    const reopened = await screen.findByTestId('offline-conflict-dialog');
    expect(within(reopened).getByTestId(`offline-entry-kept-${entry.id}`)).toBeInTheDocument();
    expect(within(reopened).queryByTestId(`offline-entry-keep-${entry.id}`)).toBeNull();
    expect(sent).toBe(0);

    await user.click(within(reopened).getByTestId(`offline-entry-discard-${entry.id}`));
    await waitFor(() => expect(within(reopened).queryByTestId(`offline-entry-${entry.id}`)).toBeNull());
    expect(await listEntries(SCOPE)).toEqual([]);
    expect(sent).toBe(0);
  });

  it('offers "Try again" for a failed entry and resends it with the same id', async () => {
    const ids: unknown[] = [];
    server.use(
      http.post(`${BASE}/care-events`, async ({ request }) => {
        ids.push(((await request.json()) as { client_event_id?: unknown }).client_event_id);
        return HttpResponse.json({ key: 'ce_1', category: 'note' }, { status: 200 });
      }),
    );
    const entry = await capture(SCOPE, noteWrite());
    await updateEntry(SCOPE, entry.seq!, { status: 'failed', attempts: 5, lastErrorCode: 'network' });
    const user = userEvent.setup();
    renderHost();
    await user.click(await screen.findByTestId('offline-queue-chip'));
    const dialog = await screen.findByTestId('offline-conflict-dialog');
    expect(within(dialog).getByTestId(`offline-entry-reason-${entry.id}`)).toHaveTextContent('Nach 5 Versuchen');
    await user.click(within(dialog).getByTestId(`offline-entry-retry-${entry.id}`));
    await waitFor(() => expect(ids).toEqual([entry.id]));
    await waitFor(async () => expect(await listEntries(SCOPE)).toEqual([]));
  });

  it('has no accessibility violations', async () => {
    await conflictEntry('task.already_closed');
    const failed = await capture(SCOPE, noteWrite());
    await updateEntry(SCOPE, failed.seq!, { status: 'failed', lastErrorCode: 'VALIDATION_ERROR' });
    renderHost();
    const dialog = await screen.findByTestId('offline-conflict-dialog');
    await waitFor(() => expect(within(dialog).getAllByRole('listitem')).toHaveLength(2));
    await expectNoA11yViolations(dialog, { minImpact: 'serious' });
  });
});
