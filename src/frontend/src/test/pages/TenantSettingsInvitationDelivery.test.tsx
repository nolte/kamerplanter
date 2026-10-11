import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen, waitFor, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import type { Invitation, InvitationCreated } from '@/api/types';
import { ApiError } from '@/api/errors';
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
  // #2166 — the page lists the account's gardens whose deletion is scheduled; none here.
  listMyTenantsWithScheduledDeletion: vi.fn().mockResolvedValue([]),
  cancelTenantErasure: vi.fn(),
  listMembers: vi.fn().mockResolvedValue([]),
  listInvitations: vi.fn().mockResolvedValue([]),
  removeMember: vi.fn(),
  createEmailInvitation: vi.fn(),
  createLinkInvitation: vi.fn(),
  revokeInvitation: vi.fn(),
}));

const tenantApi = await import('@/api/endpoints/tenants');

const ACCEPT_URL = 'https://garden.example.net/invitations/accept?token=tok-2162';

function created(delivered: boolean | null, maxUses = 1): InvitationCreated {
  return {
    invitation_key: 'i-1',
    token: 'tok-2162',
    expires_at: '2026-10-17T00:00:00Z',
    accept_url: ACCEPT_URL,
    delivered,
    max_uses: maxUses,
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


describe('TenantSettingsPage — a link for several people (#2182, REQ-024 AK-07)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    vi.clearAllMocks();
    (tenantApi.listMembers as ReturnType<typeof vi.fn>).mockResolvedValue([]);
    (tenantApi.listInvitations as ReturnType<typeof vi.fn>).mockResolvedValue([]);
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText: vi.fn().mockResolvedValue(undefined) },
      configurable: true,
    });
  });
  afterEach(() => {
    cleanup();
  });

  function maxUsesInput(): HTMLInputElement {
    return screen.getByTestId('form-field-link-max-uses').querySelector('input') as HTMLInputElement;
  }

  it('creates a single-use link unless asked for more', async () => {
    (tenantApi.createLinkInvitation as ReturnType<typeof vi.fn>).mockResolvedValue(created(null));
    await renderInvitationsTab();

    await userEvent.click(screen.getByTestId('create-link-btn'));

    await waitFor(() =>
      expect(tenantApi.createLinkInvitation).toHaveBeenCalledWith('testgarten', { role: 'viewer', max_uses: 1 }),
    );
    expect(await screen.findByTestId('invitation-link-created')).toHaveTextContent('danach ist er verbraucht');
  });

  it('sends the number of people typed and says how many the link admits', async () => {
    (tenantApi.createLinkInvitation as ReturnType<typeof vi.fn>).mockResolvedValue(created(null, 20));
    await renderInvitationsTab();

    await userEvent.clear(maxUsesInput());
    await userEvent.type(maxUsesInput(), '20');
    // Review SCR-002 — the field holds what was typed (not "120" appended to the default "1").
    expect(maxUsesInput()).toHaveValue(20);
    expect(maxUsesInput()).not.toHaveAttribute('aria-invalid', 'true');
    await userEvent.click(screen.getByTestId('create-link-btn'));

    await waitFor(() =>
      expect(tenantApi.createLinkInvitation).toHaveBeenCalledWith('testgarten', { role: 'viewer', max_uses: 20 }),
    );
    expect(await screen.findByTestId('invitation-link-created')).toHaveTextContent('Bis zu 20');
  });

  it.each(['0', '101', '2.5', ''])('refuses to create a link for %j people', async (typed) => {
    await renderInvitationsTab();

    await userEvent.clear(maxUsesInput());
    if (typed) await userEvent.type(maxUsesInput(), typed);

    expect(screen.getByTestId('create-link-btn')).toBeDisabled();
    expect(maxUsesInput()).toHaveAttribute('aria-invalid', 'true');
    expect(tenantApi.createLinkInvitation).not.toHaveBeenCalled();
  });

  function linkRow(): Invitation {
    return {
      key: 'i-7',
      tenant_key: 't1',
      email: null,
      role: 'viewer',
      invitation_type: 'link',
      status: 'pending',
      created_by: 'u-lead',
      expires_at: '2026-10-17T00:00:00Z',
      created_at: null,
      max_uses: 20,
      use_count: 3,
    };
  }

  it('lists how often each invitation was used', async () => {
    (tenantApi.listInvitations as ReturnType<typeof vi.fn>).mockResolvedValue([linkRow()]);
    await renderInvitationsTab();

    expect(await screen.findByTestId('invitation-uses-i-7')).toHaveTextContent('3 von 20');
  });

  it('lists the uses in English words too (review SCR-006)', async () => {
    await i18n.changeLanguage('en');
    (tenantApi.listInvitations as ReturnType<typeof vi.fn>).mockResolvedValue([linkRow()]);
    await renderInvitationsTab();

    expect(await screen.findByTestId('invitation-uses-i-7')).toHaveTextContent('3 of 20');
  });

  it('keeps the form and shows no link when the backend refuses the link (review SCR-003)', async () => {
    // A 422 the link route really answers: a ``max_uses`` the backend bounds refuse (the page
    // bounds the field to the same limit, an older backend may still be narrower). The link route
    // does not answer MEMBER_LIMIT_REACHED - the member limit is met per use, at acceptance.
    (tenantApi.createLinkInvitation as ReturnType<typeof vi.fn>).mockRejectedValue(
      new ApiError(
        {
          error_id: 'e-1',
          error_code: 'VALIDATION_ERROR',
          message: 'max_uses: Input should be less than or equal to 10',
          details: [{ field: 'body.max_uses', reason: 'Input should be less than or equal to 10', code: 'less_than_equal' }],
          timestamp: '',
          path: '/api/v1/t/testgarten/invitations/link',
          method: 'POST',
        },
        422,
      ),
    );
    await renderInvitationsTab();
    await userEvent.clear(maxUsesInput());
    await userEvent.type(maxUsesInput(), '20');

    await userEvent.click(screen.getByTestId('create-link-btn'));

    expect(await screen.findByText('max_uses: Input should be less than or equal to 10')).toBeInTheDocument();
    expect(screen.queryByTestId('invitation-link-created')).toBeNull();
    expect(navigator.clipboard.writeText).not.toHaveBeenCalled();
    expect(maxUsesInput()).toHaveValue(20);
    await waitFor(() => expect(screen.getByTestId('create-link-btn')).not.toBeDisabled());
  });

  it.each([
    [1, 'after that it is used up'],
    [20, 'Up to 20 people'],
  ])('says in English how many people a link for %i admits (review SCR-004)', async (maxUses, expected) => {
    await i18n.changeLanguage('en');
    (tenantApi.createLinkInvitation as ReturnType<typeof vi.fn>).mockResolvedValue(created(null, maxUses));
    await renderInvitationsTab();

    await userEvent.click(screen.getByTestId('create-link-btn'));

    expect(await screen.findByTestId('invitation-link-created')).toHaveTextContent(expected);
  });
});
