import { describe, it, expect, vi, afterEach, beforeEach } from 'vitest';
import { act, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';

import NotificationBell from '@/components/layout/NotificationBell';
import { renderWithProviders } from '../../helpers';
import { server } from '../../mocks/server';

const BASE = '/api/v1/t/test-tenant/notifications';

function useCount(count: number) {
  server.use(
    http.get(`${BASE}/count`, () => HttpResponse.json({ unread_count: count })),
    http.get(BASE, () => HttpResponse.json({ items: [], total: 0, unread_count: count })),
  );
}

describe('NotificationBell', () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders the bell and shows the polled unread count as a badge', async () => {
    useCount(3);
    renderWithProviders(<NotificationBell />);

    expect(screen.getByTestId('notification-bell')).toBeInTheDocument();
    expect(await screen.findByText('3')).toBeInTheDocument();
  });

  it('hides the badge when there are no unread notifications', async () => {
    useCount(0);
    renderWithProviders(<NotificationBell />);

    await waitFor(() =>
      // MUI marks the badge invisible for a zero count.
      expect(
        document.querySelector('.MuiBadge-invisible'),
      ).toBeInTheDocument(),
    );
  });

  it('opens the drawer on click and closes it again', async () => {
    useCount(1);
    const user = userEvent.setup();
    renderWithProviders(<NotificationBell />);

    await user.click(screen.getByTestId('notification-bell'));
    expect(await screen.findByTestId('notification-drawer')).toBeInTheDocument();

    await user.click(screen.getByTestId('notification-drawer-close'));
    await waitFor(() =>
      expect(screen.queryByTestId('notification-drawer')).toBeNull(),
    );
  });

  it('registers a polling interval and clears it on unmount', async () => {
    vi.useFakeTimers();
    const setSpy = vi.spyOn(globalThis, 'setInterval');
    const clearSpy = vi.spyOn(globalThis, 'clearInterval');
    useCount(2);

    const { unmount } = renderWithProviders(<NotificationBell />);
    expect(setSpy).toHaveBeenCalled();

    unmount();
    expect(clearSpy).toHaveBeenCalled();
  });
});

/**
 * #3023 (W-28) — a background tab must not poll. The bell stops its interval when
 * the document turns hidden and refreshes the count at once when it turns visible.
 */
describe('NotificationBell — polls only while the tab is visible (#3023)', () => {
  let visibility: DocumentVisibilityState;
  let countRequests: number;

  function setVisibility(state: DocumentVisibilityState) {
    visibility = state;
    act(() => {
      document.dispatchEvent(new Event('visibilitychange'));
    });
  }

  beforeEach(() => {
    visibility = 'visible';
    countRequests = 0;
    vi.spyOn(document, 'visibilityState', 'get').mockImplementation(() => visibility);
    server.use(
      http.get(`${BASE}/count`, () => {
        countRequests += 1;
        return HttpResponse.json({ unread_count: countRequests });
      }),
    );
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('clears the interval when hidden and fetches plus restarts it when visible again', async () => {
    const setSpy = vi.spyOn(globalThis, 'setInterval');
    const clearSpy = vi.spyOn(globalThis, 'clearInterval');
    renderWithProviders(<NotificationBell />);

    await waitFor(() => expect(countRequests).toBe(1));
    const pollsStarted = () => setSpy.mock.calls.filter(([, delay]) => delay === 60_000).length;
    expect(pollsStarted()).toBe(1);

    const pollId = setSpy.mock.results[setSpy.mock.calls.findIndex(([, delay]) => delay === 60_000)].value;
    expect(clearSpy).not.toHaveBeenCalledWith(pollId);
    setVisibility('hidden');
    expect(clearSpy).toHaveBeenCalledWith(pollId);
    // Hidden: no refresh on the transition itself.
    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(countRequests).toBe(1);

    setVisibility('visible');
    await waitFor(() => expect(countRequests).toBe(2));
    expect(pollsStarted()).toBe(2);
    expect(await screen.findByText('2')).toBeInTheDocument();
  });

  it('starts neither a request nor an interval when mounted in a hidden tab', async () => {
    visibility = 'hidden';
    const setSpy = vi.spyOn(globalThis, 'setInterval');
    renderWithProviders(<NotificationBell />);

    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(countRequests).toBe(0);
    expect(setSpy.mock.calls.filter(([, delay]) => delay === 60_000)).toHaveLength(0);

    setVisibility('visible');
    await waitFor(() => expect(countRequests).toBe(1));
  });
});
