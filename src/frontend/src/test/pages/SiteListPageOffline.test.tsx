/**
 * REQ-053 WP 9.2 (#2742), UI-NFR-012 R-020 — the site list is offline-readable: an online read writes it
 * into the plan cache (IndexedDB, `fake-indexeddb`), offline it is read from there with the "Stand von
 * hh:mm" banner, and a miss is an empty state with a hint.
 */
import 'fake-indexeddb/auto';
import { act, cleanup, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { readCached, siteListEntry, writeCached, type CacheScope } from '@/features/gardenPlanner/offline/planCache';
import SiteListPage from '@/pages/standorte/SiteListPage';
import { authState, createTestStore, renderWithProviders, tenantState } from '@/test/helpers';
import { emptyPlanCache } from '@/test/planCacheTestKit';

const SCOPE: CacheScope = { userKey: 'user-1', tenantKey: 'tenant-1' };
const OTHER_USER: CacheScope = { userKey: 'user-2', tenantKey: 'tenant-1' };
const CACHED_AT = Date.now() - 5 * 60 * 1000;

function stamp(at: number): string {
  return new Intl.DateTimeFormat('en', { hour: '2-digit', minute: '2-digit' }).format(new Date(at));
}

function setOnline(value: boolean) {
  Object.defineProperty(window.navigator, 'onLine', { configurable: true, get: () => value });
  act(() => {
    window.dispatchEvent(new Event(value ? 'online' : 'offline'));
  });
}

function renderSites() {
  return renderWithProviders(<SiteListPage />, { store: createTestStore({ ...tenantState('lead'), ...authState() }) });
}

beforeEach(async () => {
  await emptyPlanCache();
});

afterEach(() => {
  // Unmount first: a view coming back online would read from the server again and write the cache.
  cleanup();
  setOnline(true);
});

describe('site list offline (WP 9.2)', () => {
  it('writes the site list into the cache after an online read', async () => {
    renderSites();
    await waitFor(async () => expect(await readCached(siteListEntry(SCOPE, 50))).not.toBeNull());
    expect(screen.queryByTestId('offline-cached-banner')).toBeNull();
  });

  it('reads the cached site list offline with the banner', async () => {
    await writeCached(siteListEntry(SCOPE, 50), [{ key: 'site_1', name: 'Allotment', type: 'outdoor' }], CACHED_AT);
    setOnline(false);
    renderSites();
    expect(await screen.findByTestId('offline-cached-banner')).toHaveTextContent(stamp(CACHED_AT));
    expect(screen.getByText('Allotment')).toBeInTheDocument();
  });

  it("a cache miss offline is an empty state with a hint — another user's list is no hit", async () => {
    await writeCached(siteListEntry(OTHER_USER, 50), [{ key: 'site_9', name: 'Not mine', type: 'outdoor' }], CACHED_AT);
    setOnline(false);
    renderSites();
    expect(await screen.findByTestId('site-list-offline-miss')).toHaveTextContent('The sites are not available offline');
    expect(screen.queryByText('Not mine')).toBeNull();
  });

  it('reads a missed list once the connection is back, and offers "try again"', async () => {
    setOnline(false);
    renderSites();
    const miss = await screen.findByTestId('site-list-offline-miss');
    expect(within(miss).getByTestId('empty-state-action')).toBeInTheDocument();
    setOnline(true);
    await waitFor(() => expect(screen.queryByTestId('site-list-offline-miss')).toBeNull());
    expect(screen.queryByTestId('offline-cached-banner')).toBeNull();
  });

  it('reads a cached list again once the connection is back: the banner goes', async () => {
    await writeCached(siteListEntry(SCOPE, 50), [{ key: 'site_1', name: 'Allotment', type: 'outdoor' }], CACHED_AT);
    setOnline(false);
    renderSites();
    await screen.findByTestId('offline-cached-banner');
    setOnline(true);
    await waitFor(() => expect(screen.queryByTestId('offline-cached-banner')).toBeNull());
  });
});
