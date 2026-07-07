import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';

import NotificationDrawer from '@/components/layout/NotificationDrawer';
import { renderWithProviders } from '../../helpers';
import { server } from '../../mocks/server';

const BASE = '/api/v1/t/test-tenant/notifications';

interface NotifOverrides {
  key: string;
  urgency?: string;
  title?: string;
  body?: string;
  read_at?: string | null;
  action_url?: string;
  created_at?: string | null;
}

function makeNotif(o: NotifOverrides) {
  return {
    key: o.key,
    tenant_key: 'test-tenant',
    user_key: 'user-1',
    notification_type: 'care_reminder',
    title: o.title ?? `Titel ${o.key}`,
    body: o.body ?? `Body ${o.key}`,
    urgency: o.urgency ?? 'normal',
    data: o.action_url ? { action_url: o.action_url } : {},
    actions: [],
    image_url: null,
    group_key: null,
    channels_sent: [],
    channels_failed: [],
    status: 'delivered',
    read_at: o.read_at ?? null,
    acted_at: null,
    escalation_level: 0,
    parent_notification_key: null,
    created_at: o.created_at === undefined ? new Date().toISOString() : o.created_at,
    updated_at: null,
  };
}

/** Registers a GET list handler backed by an in-memory, mutable list. */
function useList(items: ReturnType<typeof makeNotif>[]) {
  server.use(
    http.get(BASE, ({ request }) => {
      const url = new URL(request.url);
      const unreadOnly = url.searchParams.get('unread_only') === 'true';
      const offset = Number(url.searchParams.get('offset') ?? '0');
      const limit = Number(url.searchParams.get('limit') ?? '20');
      const visible = unreadOnly ? items.filter((n) => !n.read_at) : items;
      const page = visible.slice(offset, offset + limit);
      return HttpResponse.json({
        items: page,
        total: visible.length,
        unread_count: items.filter((n) => !n.read_at).length,
      });
    }),
    http.post(`${BASE}/:key/read`, ({ params }) => {
      const found = items.find((n) => n.key === params.key);
      const read = { ...(found ?? makeNotif({ key: String(params.key) })), read_at: new Date().toISOString() };
      if (found) found.read_at = read.read_at;
      return HttpResponse.json(read);
    }),
  );
}

const noop = () => undefined;

describe('NotificationDrawer', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('shows the empty state and reports a zero unread count', async () => {
    useList([]);
    const onCountChange = vi.fn();
    renderWithProviders(
      <NotificationDrawer open onClose={noop} onCountChange={onCountChange} />,
    );

    expect(await screen.findByText('Keine Benachrichtigungen')).toBeInTheDocument();
    await waitFor(() => expect(onCountChange).toHaveBeenCalledWith(0));
  });

  it('does not render drawer content while closed', () => {
    useList([makeNotif({ key: 'n1' })]);
    renderWithProviders(
      <NotificationDrawer open={false} onClose={noop} onCountChange={noop} />,
    );
    expect(screen.queryByTestId('notification-drawer')).toBeNull();
  });

  it('renders notification cards, an urgency chip, and reports the unread count', async () => {
    useList([
      makeNotif({ key: 'n1', title: 'Kritisch', urgency: 'critical', read_at: null }),
      makeNotif({ key: 'n2', title: 'Gelesen', urgency: 'normal', read_at: '2024-01-01T00:00:00Z' }),
    ]);
    const onCountChange = vi.fn();
    renderWithProviders(
      <NotificationDrawer open onClose={noop} onCountChange={onCountChange} />,
    );

    expect(await screen.findByText('Kritisch')).toBeInTheDocument();
    expect(screen.getByText('Gelesen')).toBeInTheDocument();
    // High/critical urgencies surface a chip labelled with the urgency value.
    expect(screen.getByText('critical')).toBeInTheDocument();
    // One unread → mark-all-read affordance is offered.
    expect(screen.getByTestId('mark-all-read-btn')).toBeInTheDocument();
    await waitFor(() => expect(onCountChange).toHaveBeenCalledWith(1));
  });

  it('marks all notifications as read and hides the bulk button', async () => {
    useList([
      makeNotif({ key: 'n1', title: 'Eins', read_at: null }),
      makeNotif({ key: 'n2', title: 'Zwei', read_at: null }),
    ]);
    const onCountChange = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(
      <NotificationDrawer open onClose={noop} onCountChange={onCountChange} />,
    );

    const button = await screen.findByTestId('mark-all-read-btn');
    await user.click(button);

    await waitFor(() => expect(onCountChange).toHaveBeenLastCalledWith(0));
    await waitFor(() => expect(screen.queryByTestId('mark-all-read-btn')).toBeNull());
  });

  it('marks a clicked notification read and navigates + closes when it has an action url', async () => {
    useList([
      makeNotif({ key: 'n1', title: 'Mit Link', read_at: null, action_url: '/dashboard' }),
    ]);
    const onClose = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(
      <NotificationDrawer open onClose={onClose} onCountChange={noop} />,
    );

    await user.click(await screen.findByTestId('notification-action-n1'));
    await waitFor(() => expect(onClose).toHaveBeenCalledTimes(1));
  });

  it('does not close when a read notification without action url is clicked', async () => {
    useList([
      makeNotif({ key: 'n1', title: 'Ohne Link', read_at: '2024-01-01T00:00:00Z' }),
    ]);
    const onClose = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(
      <NotificationDrawer open onClose={onClose} onCountChange={noop} />,
    );

    await user.click(await screen.findByTestId('notification-action-n1'));
    // No action_url → drawer stays open.
    expect(onClose).not.toHaveBeenCalled();
  });

  it('paginates via load-more, appending the next page', async () => {
    const firstPage = Array.from({ length: 20 }, (_, i) =>
      makeNotif({ key: `p1-${i}`, title: `Seite1-${i}`, read_at: '2024-01-01T00:00:00Z' }),
    );
    const secondPage = [makeNotif({ key: 'p2-0', title: 'Seite2-0', read_at: '2024-01-01T00:00:00Z' })];
    useList([...firstPage, ...secondPage]);

    const user = userEvent.setup();
    renderWithProviders(
      <NotificationDrawer open onClose={noop} onCountChange={noop} />,
    );

    // First page fills PAGE_SIZE (20) → load-more offered.
    expect(await screen.findByText('Seite1-0')).toBeInTheDocument();
    const loadMore = await screen.findByTestId('notification-load-more');
    await user.click(loadMore);

    expect(await screen.findByText('Seite2-0')).toBeInTheDocument();
    // Remaining page is short → no further load-more.
    await waitFor(() => expect(screen.queryByTestId('notification-load-more')).toBeNull());
  });

  it('renders urgency variants and formats relative timestamps across ranges', async () => {
    const now = Date.now();
    useList([
      makeNotif({ key: 'h', title: 'Hoch', urgency: 'high', created_at: new Date(now - 5 * 60_000).toISOString() }),
      makeNotif({ key: 'l', title: 'Niedrig', urgency: 'low', created_at: new Date(now - 3 * 3_600_000).toISOString() }),
      makeNotif({ key: 'd', title: 'Tage', urgency: 'normal', created_at: new Date(now - 2 * 86_400_000).toISOString() }),
      makeNotif({ key: 'o', title: 'Alt', urgency: 'normal', created_at: new Date(now - 10 * 86_400_000).toISOString() }),
      makeNotif({ key: 'n', title: 'Ohne Datum', urgency: 'normal', created_at: null }),
    ]);
    renderWithProviders(
      <NotificationDrawer open onClose={noop} onCountChange={noop} />,
    );

    // high shows a warning chip; low shows none.
    expect(await screen.findByText('Hoch')).toBeInTheDocument();
    expect(screen.getByText('high')).toBeInTheDocument();
    expect(screen.queryByText('low')).toBeNull();
    // "5 minutes ago" range renders the minutes-ago label.
    expect(screen.getByText(/vor 5 Min\./)).toBeInTheDocument();
    // Older-than-a-week falls back to a locale date; the card still renders.
    expect(screen.getByText('Alt')).toBeInTheDocument();
    expect(screen.getByText('Ohne Datum')).toBeInTheDocument();
  });

  it('closes via the header close button', async () => {
    useList([]);
    const onClose = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(
      <NotificationDrawer open onClose={onClose} onCountChange={noop} />,
    );

    await user.click(await screen.findByTestId('notification-drawer-close'));
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
