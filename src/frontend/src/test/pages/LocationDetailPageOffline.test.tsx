/**
 * REQ-053 WP 9.2 (#2742) — the bed view is reachable offline: `LocationDetailPage` reads the bed summary
 * from the plan cache (`{user_key}:{tenant_key}:{location_key}`, IndexedDB via `fake-indexeddb`), shows
 * the bed view with the "Stand von hh:mm" banner and its edits locked, and only the location's master
 * data (the "Details" tab) says it needs the server. A miss is an empty state with a hint.
 */
import 'fake-indexeddb/auto';
import { act, cleanup, screen, waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { bedSummary } from '@/features/gardenPlanner/bed/bedTestKit';
import { bedSummaryEntry, readCached, writeCached, type CacheScope } from '@/features/gardenPlanner/offline/planCache';
import LocationDetailPage from '@/pages/standorte/LocationDetailPage';
import { authState, createTestStore, renderWithProviders, tenantState } from '@/test/helpers';
import { server } from '@/test/mocks/server';
import { emptyPlanCache } from '@/test/planCacheTestKit';

vi.mock('react-router-dom', async (orig) => {
  const actual = await orig<typeof import('react-router-dom')>();
  return { ...actual, useParams: () => ({ key: 'loc_b03' }) };
});

const BASE = '/api/v1/t/:tenant';
const SCOPE: CacheScope = { userKey: 'user-1', tenantKey: 'tenant-1' };
const OTHER_TENANT: CacheScope = { userKey: 'user-1', tenantKey: 'tenant-2' };
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

function renderPage(route = '/standorte/locations/loc_b03') {
  return renderWithProviders(<LocationDetailPage />, {
    store: createTestStore({ ...tenantState('lead'), ...authState() }),
    route,
  });
}

/** No connection: every request of the page goes nowhere. */
function noNetwork() {
  server.use(
    http.get(`${BASE}/locations/:key`, () => HttpResponse.error()),
    http.get(`${BASE}/locations/:key/summary`, () => HttpResponse.error()),
  );
}

beforeEach(async () => {
  await emptyPlanCache();
  // The bed view reads the tenant's members and assignments (bed head); not offline data.
  server.use(
    http.get('/api/v1/tenants/:slug/members', () => HttpResponse.json([])),
    http.get('/api/v1/tenants/:slug/assignments', () => HttpResponse.json([])),
  );
});

afterEach(() => {
  // Unmount first: a view coming back online would read from the server again and write the cache.
  cleanup();
  setOnline(true);
});

describe('bed view offline (WP 9.2)', () => {
  it('reads the summary from the cache: bed view, banner, edits locked, details need the server', async () => {
    await writeCached(bedSummaryEntry(SCOPE, 'loc_b03'), bedSummary(), CACHED_AT);
    noNetwork();
    setOnline(false);
    renderPage('/standorte/locations/loc_b03#details');
    expect(await screen.findByTestId('bed-view')).toBeInTheDocument();
    expect(screen.getByTestId('bed-view-cached-banner')).toHaveTextContent(stamp(CACHED_AT));
    expect(screen.getByTestId('bed-view-edits-locked')).toBeInTheDocument();
    expect(screen.queryByTestId('bed-status-change-button')).toBeNull();
    expect(screen.getByTestId('bed-details-offline')).toBeInTheDocument();
    expect(screen.queryByTestId('error-display')).toBeNull();
  });

  it("a cache miss offline is an empty state with a hint — another tenant's summary is no hit", async () => {
    await writeCached(bedSummaryEntry(OTHER_TENANT, 'loc_b03'), bedSummary(), CACHED_AT);
    noNetwork();
    setOnline(false);
    renderPage();
    expect(await screen.findByTestId('location-offline-miss')).toHaveTextContent('This bed is not available offline');
    expect(screen.queryByTestId('bed-view')).toBeNull();
    expect(screen.queryByTestId('error-display')).toBeNull();
  });

  it('writes the summary into the cache after an online read', async () => {
    server.use(http.get(`${BASE}/locations/:key/summary`, () => HttpResponse.json(bedSummary())));
    renderPage();
    await waitFor(async () => expect((await readCached(bedSummaryEntry(SCOPE, 'loc_b03')))?.data).toEqual(bedSummary()));
  });

  /** Back online: the summary answers; the rest of the location page is not this test's business. */
  function summaryBack(): string[] {
    const reads: string[] = [];
    server.use(
      http.get(`${BASE}/locations/:key/summary`, () => {
        reads.push('summary');
        return HttpResponse.json(bedSummary());
      }),
    );
    return reads;
  }

  it('reads a cached bed again once the connection is back: the cached banner goes', async () => {
    await writeCached(bedSummaryEntry(SCOPE, 'loc_b03'), bedSummary(), CACHED_AT);
    noNetwork();
    setOnline(false);
    renderPage();
    await screen.findByTestId('bed-view-cached-banner');
    const reads = summaryBack();
    setOnline(true);
    await waitFor(() => expect(reads).toEqual(['summary']));
    await waitFor(() => expect(screen.queryByTestId('bed-view-cached-banner')).toBeNull());
    // Let the page's own reads finish inside this test.
    await waitFor(() => expect(screen.queryByTestId('loading-skeleton')).toBeNull());
  });

  it('reads a missed bed once the connection is back', async () => {
    noNetwork();
    setOnline(false);
    renderPage();
    await screen.findByTestId('location-offline-miss');
    const reads = summaryBack();
    setOnline(true);
    await waitFor(() => expect(reads).toEqual(['summary']));
    await waitFor(() => expect(screen.queryByTestId('location-offline-miss')).toBeNull());
  });
});
