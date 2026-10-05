import { screen } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import InvitationAcceptPage from '@/pages/tenants/InvitationAcceptPage';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

function refuse(errorCode: string, message: string, status: number) {
  server.use(
    http.post('/api/v1/tenants/invitations/accept', () =>
      HttpResponse.json(
        { error_id: 'e', error_code: errorCode, message, details: [], timestamp: '', path: '', method: '' },
        { status },
      ),
    ),
  );
}

describe('InvitationAcceptPage', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('explains a full tenant in the user language instead of the backend text (#2133)', async () => {
    refuse('MEMBER_LIMIT_REACHED', 'This tenant has reached its limit of 1 members.', 422);

    renderWithProviders(<InvitationAcceptPage />, { route: '/invitations/accept?token=tok' });

    const detail = await screen.findByTestId('invitation-error-detail');
    expect(detail.textContent).toContain('Mitgliedergrenze');
    expect(detail.textContent).not.toContain('This tenant has reached');
  });

  it('keeps the backend message for every other refusal', async () => {
    refuse('FORBIDDEN', 'This invitation was issued for another address.', 403);

    renderWithProviders(<InvitationAcceptPage />, { route: '/invitations/accept?token=tok' });

    const detail = await screen.findByTestId('invitation-error-detail');
    expect(detail.textContent).toBe('This invitation was issued for another address.');
  });

  it('shows the English text in English', async () => {
    await i18n.changeLanguage('en');
    refuse('MEMBER_LIMIT_REACHED', 'This tenant has reached its limit of 1 members.', 422);

    renderWithProviders(<InvitationAcceptPage />, { route: '/invitations/accept?token=tok' });

    expect((await screen.findByTestId('invitation-error-detail')).textContent).toContain('member limit');
  });
});
