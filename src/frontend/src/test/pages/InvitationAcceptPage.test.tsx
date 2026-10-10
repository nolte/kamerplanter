import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import InvitationAcceptPage from '@/pages/tenants/InvitationAcceptPage';
import { createTestStore, renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

let acceptCalls = 0;

function refuse(errorCode: string, message: string, status: number) {
  server.use(
    http.post('/api/v1/tenants/invitations/accept', () => {
      acceptCalls += 1;
      return HttpResponse.json(
        { error_id: 'e', error_code: errorCode, message, details: [], timestamp: '', path: '', method: '' },
        { status },
      );
    }),
  );
}

/** A store whose account is a member of one tenant (the dashboard is a useful way out). */
function memberStore() {
  return createTestStore({
    tenants: {
      activeTenant: null,
      myTenants: [
        {
          key: 't1', name: 'Garten', slug: 'garten', tenant_type: 'personal', description: null, role: 'lead',
          admin_scopes: [], avatar_url: null, owner_key: 'u1', max_members: 1, created_at: null, updated_at: null,
        },
      ],
      isLoading: false,
      error: null,
    },
  });
}

async function openAndAccept(store = memberStore()) {
  renderWithProviders(<InvitationAcceptPage />, { route: '/invitations/accept?token=tok', store });
  await userEvent.click(await screen.findByTestId('invitation-accept-btn'));
}

describe('InvitationAcceptPage', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    acceptCalls = 0;
  });

  it('accepts only on an explicit click, never on page load (#2162 review S-2)', async () => {
    refuse('FORBIDDEN', 'no', 403);

    renderWithProviders(<InvitationAcceptPage />, { route: '/invitations/accept?token=tok' });

    expect(await screen.findByTestId('invitation-accept-btn')).toHaveTextContent('Einladung annehmen');
    expect(acceptCalls).toBe(0);

    await userEvent.click(screen.getByTestId('invitation-accept-btn'));

    await waitFor(() => expect(acceptCalls).toBe(1));
  });

  it('explains a full tenant in the user language instead of the backend text (#2133)', async () => {
    refuse('MEMBER_LIMIT_REACHED', 'This tenant has reached its limit of 1 members.', 422);

    await openAndAccept();

    const detail = await screen.findByTestId('invitation-error-detail');
    expect(detail.textContent).toContain('Mitgliedergrenze');
    expect(detail.textContent).not.toContain('This tenant has reached');
    // The invitation stays valid: no request for a new one.
    expect(screen.queryByTestId('invitation-error-next-step')).toBeNull();
  });

  it('keeps the backend message for every other refusal and says what to do next', async () => {
    refuse('FORBIDDEN', 'This invitation was issued for another address.', 403);

    await openAndAccept();

    const detail = await screen.findByTestId('invitation-error-detail');
    expect(detail.textContent).toBe('This invitation was issued for another address.');
    expect(screen.getByTestId('invitation-error-next-step')).toHaveTextContent('neue Einladung');
    expect(screen.getByRole('button', { name: 'Dashboard' })).toBeInTheDocument();
  });

  it('offers no dashboard to an account without any membership (#2162 review W3)', async () => {
    refuse('FORBIDDEN', 'no', 403);

    await openAndAccept(createTestStore());

    await screen.findByTestId('invitation-error-detail');
    expect(screen.queryByRole('button', { name: 'Dashboard' })).toBeNull();
  });

  it('shows the English text in English', async () => {
    await i18n.changeLanguage('en');
    refuse('MEMBER_LIMIT_REACHED', 'This tenant has reached its limit of 1 members.', 422);

    await openAndAccept();

    expect((await screen.findByTestId('invitation-error-detail')).textContent).toContain('member limit');
  });
});
