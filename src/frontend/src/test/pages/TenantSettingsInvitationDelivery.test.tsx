import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen, waitFor, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import type { InvitationCreated } from '@/api/types';
import { createStoreWithTenantRole, renderWithProviders } from '@/test/helpers';

/**
 * #2162 — the settings page reports an e-mail invitation truthfully and hands out usable links.
 *
 * The page said "Einladung gesendet" for every e-mail invitation although nothing was mailed,
 * and threw the returned token away; a link invitation copied the bare token, which no page
 * accepts. The backend now mails the invitation and answers `delivered` plus `accept_url`:
 * "sent" only when the mail left, otherwise the link is shown for the inviter to pass on; a link
 * invitation copies (and shows) the accept page's link.
 */

vi.mock('@/api/endpoints/tenants', () => ({
  listMembers: vi.fn().mockResolvedValue([]),
  listInvitations: vi.fn().mockResolvedValue([]),
  removeMember: vi.fn(),
  createEmailInvitation: vi.fn(),
  createLinkInvitation: vi.fn(),
  revokeInvitation: vi.fn(),
}));

const tenantApi = await import('@/api/endpoints/tenants');

const ACCEPT_URL = 'https://garden.example.net/invitations/accept?token=tok-2162';

function created(delivered: boolean | null): InvitationCreated {
  return {
    invitation_key: 'i-1',
    token: 'tok-2162',
    expires_at: '2026-10-17T00:00:00Z',
    accept_url: ACCEPT_URL,
    delivered,
  };
}

async function renderInvitationsTab() {
  const { default: Page } = await import('@/pages/tenants/TenantSettingsPage');
  renderWithProviders(<Page />, {
    store: createStoreWithTenantRole('lead', ['management']),
    route: '/tenants/settings#invitations',
  });
  return screen.findByTestId('invite-email-field');
}

async function inviteByEmail(address = 'friend@example.org') {
  const field = await renderInvitationsTab();
  await userEvent.type(field.querySelector('input') as HTMLInputElement, address);
  await userEvent.click(screen.getByTestId('send-invitation-btn'));
}

describe('TenantSettingsPage — invitation delivery (#2162)', () => {
  let writeText: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    i18n.changeLanguage('de');
    vi.clearAllMocks();
    (tenantApi.listMembers as ReturnType<typeof vi.fn>).mockResolvedValue([]);
    (tenantApi.listInvitations as ReturnType<typeof vi.fn>).mockResolvedValue([]);
    writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, 'clipboard', { value: { writeText }, configurable: true });
  });
  afterEach(() => {
    cleanup();
  });

  it('says "sent" only when the mail left', async () => {
    (tenantApi.createEmailInvitation as ReturnType<typeof vi.fn>).mockResolvedValue(created(true));

    await inviteByEmail();

    expect(await screen.findByText('Einladung per E-Mail verschickt')).toBeInTheDocument();
    expect(tenantApi.createEmailInvitation).toHaveBeenCalledWith('testgarten', {
      email: 'friend@example.org',
      role: 'viewer',
    });
    expect(screen.queryByTestId('invitation-not-delivered')).toBeNull();
  });

  it('shows the accept link instead of claiming success when the mail did not leave', async () => {
    (tenantApi.createEmailInvitation as ReturnType<typeof vi.fn>).mockResolvedValue(created(false));

    await inviteByEmail();

    const notice = await screen.findByTestId('invitation-not-delivered');
    expect(notice).toHaveTextContent('nicht rausgegangen');
    expect(screen.getByTestId('invitation-accept-url')).toHaveValue(ACCEPT_URL);
    expect(screen.queryByText('Einladung per E-Mail verschickt')).toBeNull();
    // Review S2: the panel carries the message; no second, vanishing snackbar repeats it.
    expect(screen.queryByText(/konnte nicht verschickt werden/)).toBeNull();
    // Review S1: the next step has the focus.
    await waitFor(() => expect(screen.getByTestId('copy-invitation-link-btn')).toHaveFocus());
    // The expiry comes from the answer, not from a fixed "7 days".
    expect(notice).toHaveTextContent(new Date('2026-10-17T00:00:00Z').toLocaleDateString('de'));

    await userEvent.click(screen.getByTestId('copy-invitation-link-btn'));

    await waitFor(() => expect(writeText).toHaveBeenCalledWith(ACCEPT_URL));
  });

  it('copies the accept link of a link invitation, never the bare token', async () => {
    (tenantApi.createLinkInvitation as ReturnType<typeof vi.fn>).mockResolvedValue(created(null));
    await renderInvitationsTab();

    await userEvent.click(screen.getByTestId('create-link-btn'));

    await waitFor(() => expect(writeText).toHaveBeenCalledWith(ACCEPT_URL));
    expect(writeText).not.toHaveBeenCalledWith('tok-2162');
    expect(await screen.findByTestId('invitation-link-created')).toBeInTheDocument();
    expect(screen.getByTestId('invitation-accept-url')).toHaveValue(ACCEPT_URL);
    expect(await screen.findByText('Einladungslink in die Zwischenablage kopiert')).toBeInTheDocument();
  });

  it('still shows the link when the clipboard is refused', async () => {
    writeText.mockRejectedValue(new Error('NotAllowedError'));
    (tenantApi.createLinkInvitation as ReturnType<typeof vi.fn>).mockResolvedValue(created(null));
    await renderInvitationsTab();

    await userEvent.click(screen.getByTestId('create-link-btn'));

    expect(await screen.findByText(/Kopieren nicht möglich/)).toBeInTheDocument();
    expect(screen.getByTestId('invitation-accept-url')).toHaveValue(ACCEPT_URL);
  });

  it('reports a refused invitation as an error and shows no link', async () => {
    (tenantApi.createEmailInvitation as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('boom'));

    await inviteByEmail();

    await waitFor(() => expect(tenantApi.createEmailInvitation).toHaveBeenCalled());
    expect(screen.queryByTestId('invitation-not-delivered')).toBeNull();
    expect(screen.queryByText('Einladung per E-Mail verschickt')).toBeNull();
  });

  it('tells it in English too', async () => {
    await i18n.changeLanguage('en');
    (tenantApi.createEmailInvitation as ReturnType<typeof vi.fn>).mockResolvedValue(created(false));

    await inviteByEmail();

    expect(await screen.findByTestId('invitation-not-delivered')).toHaveTextContent('did not go out');
  });
});


describe('TenantSettingsPage — one invitation request at a time (#2162 review S5)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    vi.clearAllMocks();
    (tenantApi.listMembers as ReturnType<typeof vi.fn>).mockResolvedValue([]);
    (tenantApi.listInvitations as ReturnType<typeof vi.fn>).mockResolvedValue([]);
  });
  afterEach(() => {
    cleanup();
  });

  it('disables both invitation buttons while a request runs, so a double click sends one mail', async () => {
    let finish: (value: InvitationCreated) => void = () => undefined;
    (tenantApi.createEmailInvitation as ReturnType<typeof vi.fn>).mockReturnValue(
      new Promise<InvitationCreated>((resolve) => {
        finish = resolve;
      }),
    );
    const field = await renderInvitationsTab();
    await userEvent.type(field.querySelector('input') as HTMLInputElement, 'friend@example.org');

    await userEvent.click(screen.getByTestId('send-invitation-btn'));

    expect(screen.getByTestId('send-invitation-btn')).toBeDisabled();
    expect(screen.getByTestId('create-link-btn')).toBeDisabled();
    // A second click lands on the disabled button (pointer checks off, as a real double click would).
    await userEvent.setup({ pointerEventsCheck: 0 }).click(screen.getByTestId('send-invitation-btn'));
    expect(tenantApi.createEmailInvitation).toHaveBeenCalledTimes(1);

    finish(created(true));
    await waitFor(() => expect(screen.getByTestId('create-link-btn')).not.toBeDisabled());
  });
});
