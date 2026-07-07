import { describe, it, expect, vi, afterEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
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
