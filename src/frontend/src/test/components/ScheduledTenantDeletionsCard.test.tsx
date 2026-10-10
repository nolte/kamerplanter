import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { act, screen, waitFor, cleanup, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import { ApiError } from '@/api/errors';
import type { ApiErrorResponse, TenantWithRole } from '@/api/types';
import { createStoreWithTenantRole, createTestStore, renderWithProviders } from '@/test/helpers';

/**
 * #2166 — a lead with the `management` scope finds the garden whose deletion is scheduled and
 * cancels it.
 *
 * A `pending_deletion` tenant resolves for nobody (#2105) and `GET /tenants` left it out, so it
 * vanished from every list: the cancellation route (#2123) had no surface. The card reads
 * `GET /tenants?include_scheduled_deletion=true`, shows the scheduled gardens with their date and
 * offers the cancellation only where the backend allows it — `pending_deletion`, lead +
 * `management`. An `orphaned` garden is shown, never cancellable (#2134).
 */

vi.mock('@/api/endpoints/tenants', () => ({
  listMyTenants: vi.fn().mockResolvedValue([]),
  listMyTenantsWithScheduledDeletion: vi.fn(),
  cancelTenantErasure: vi.fn(),
  listMembers: vi.fn().mockResolvedValue([]),
  listInvitations: vi.fn().mockResolvedValue([]),
}));

vi.mock('@/api/endpoints/auth', async () => ({
  ...(await vi.importActual<typeof import('@/api/endpoints/auth')>('@/api/endpoints/auth')),
  listProviders: vi.fn(),
  requestStepUpCode: vi.fn().mockResolvedValue({ expires_at: '2026-10-04T12:10:00Z', expires_in: 600 }),
}));

const tenantApi = await import('@/api/endpoints/tenants');
const auth = await import('@/api/endpoints/auth');

// Credential-shaped values are assembled at runtime (GitGuardian, #1838).
const PASSWORD = ['cancel', 'Lead', 'pw', '1'].join('-');
const DUE = '2027-01-03T09:00:00Z';

function garden(overrides: Partial<TenantWithRole>): TenantWithRole {
  return {
    key: 't-x',
    name: 'Garden',
    slug: 'garden',
    tenant_type: 'organization',
    description: null,
    avatar_url: null,
    owner_key: 'u-1',
    max_members: 10,
    created_at: null,
    updated_at: null,
    role: 'lead',
    admin_scopes: ['management'],
    is_active: true,
    status: 'active',
    deletion_scheduled_at: null,
    ...overrides,
  };
}

const ACTIVE = garden({ key: 't-home', name: 'Hausgarten', slug: 'hausgarten' });
const PENDING = garden({
  key: 't-club',
  name: 'Gemeinschaftsgarten Lindenhof',
  slug: 'lindenhof',
  is_active: false,
  status: 'pending_deletion',
  deletion_scheduled_at: DUE,
});
const PENDING_NO_MANAGEMENT = garden({
  key: 't-school',
  name: 'Schulgarten',
  slug: 'schulgarten',
  admin_scopes: [],
  is_active: false,
  status: 'pending_deletion',
  deletion_scheduled_at: DUE,
});
const ORPHANED = garden({
  key: 't-orphan',
  name: 'Verwaister Garten',
  slug: 'verwaist',
  is_active: false,
  status: 'orphaned',
  deletion_scheduled_at: DUE,
});

function apiError(status: number, body: Partial<ApiErrorResponse>): ApiError {
  return new ApiError(
    {
      error_id: 'err',
      error_code: 'X',
      message: 'x',
      details: [],
      timestamp: '',
      path: '/x',
      method: 'POST',
      ...body,
    } as ApiErrorResponse,
    status,
  );
}

async function renderCard() {
  const { default: Card } = await import('@/components/tenants/ScheduledTenantDeletionsCard');
  return renderWithProviders(<Card />, { store: createStoreWithTenantRole('lead', ['management']) });
}

/**
 * Render the card with the list read held back, then settle the read and flush React — the SAME
 * path for the positive and the negative outcome, so a "renders nothing" can only pass after the
 * answer was processed (the positive twin proves the flush is enough to show a render, SCR-006).
 */
async function renderSettled(outcome: { resolve: TenantWithRole[] } | { reject: unknown }) {
  let settle!: () => void;
  const answer = new Promise<TenantWithRole[]>((resolve, reject) => {
    settle = () => ('resolve' in outcome ? resolve(outcome.resolve) : reject(outcome.reject));
  });
  (tenantApi.listMyTenantsWithScheduledDeletion as ReturnType<typeof vi.fn>).mockReturnValueOnce(answer);
  await renderCard();
  expect(tenantApi.listMyTenantsWithScheduledDeletion).toHaveBeenCalledTimes(1);
  await act(async () => {
    settle();
    await answer.catch(() => undefined);
  });
}

async function openCancelDialog() {
  await renderCard();
  await userEvent.click(await screen.findByTestId('cancel-tenant-erasure-lindenhof'));
  return screen.findByTestId('cancel-own-tenant-erasure-dialog');
}

describe('ScheduledTenantDeletionsCard (#2166)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    vi.clearAllMocks();
    sessionStorage.clear();
    (tenantApi.listMyTenantsWithScheduledDeletion as ReturnType<typeof vi.fn>).mockResolvedValue([
      ACTIVE,
      PENDING,
      PENDING_NO_MANAGEMENT,
      ORPHANED,
    ]);
    (tenantApi.listMyTenants as ReturnType<typeof vi.fn>).mockResolvedValue([ACTIVE]);
    (tenantApi.cancelTenantErasure as ReturnType<typeof vi.fn>).mockResolvedValue({ ...PENDING, status: 'active' });
    (auth.listProviders as ReturnType<typeof vi.fn>).mockResolvedValue([{ provider: 'local' }]);
  });
  afterEach(() => {
    cleanup();
    sessionStorage.clear();
  });

  it('lists only the gardens whose deletion is scheduled, with their state and date', async () => {
    await renderCard();

    const pending = await screen.findByTestId('scheduled-tenant-row-lindenhof');
    expect(pending).toHaveTextContent('Gemeinschaftsgarten Lindenhof');
    expect(within(pending).getByTestId('scheduled-tenant-status-lindenhof')).toHaveTextContent('Löschung geplant');
    // The shared date format of the app (SCR-001), not the browser's default rendering.
    expect(pending).toHaveTextContent('Wird am 03.01.2027 mit allen Daten gelöscht');
    expect(within(screen.getByTestId('scheduled-tenant-row-verwaist')).getByTestId('scheduled-tenant-status-verwaist')).toHaveTextContent(
      'Verwaist',
    );
    // The active garden is the switcher's business, not this card's.
    expect(screen.queryByTestId('scheduled-tenant-row-hausgarten')).toBeNull();
  });

  it('offers the cancellation only to a lead with management, and never for an orphaned garden', async () => {
    await renderCard();

    expect(await screen.findByTestId('cancel-tenant-erasure-lindenhof')).toBeInTheDocument();
    expect(screen.queryByTestId('cancel-tenant-erasure-schulgarten')).toBeNull();
    expect(screen.getByTestId('scheduled-tenant-row-schulgarten')).toHaveTextContent(
      'Abbrechen kann die Löschung nur eine Leitung mit Verwaltungsrecht',
    );
    expect(screen.queryByTestId('cancel-tenant-erasure-verwaist')).toBeNull();
    expect(screen.getByTestId('scheduled-tenant-row-verwaist')).toHaveTextContent('lässt sich nicht abbrechen');
  });

  it('shows the card once the list is read — the positive twin of the empty and refused cases', async () => {
    await renderSettled({ resolve: [ACTIVE, PENDING] });

    expect(screen.getByTestId('scheduled-tenant-row-lindenhof')).toBeInTheDocument();
  });

  it('renders nothing while no deletion is scheduled', async () => {
    await renderSettled({ resolve: [ACTIVE] });

    expect(screen.queryByTestId('scheduled-tenant-deletions')).toBeNull();
    expect(screen.queryByTestId('scheduled-tenant-deletions-error')).toBeNull();
  });

  it.each([403, 404])('stays out of the page when the list is refused with %i', async (status) => {
    await renderSettled({ reject: apiError(status, { message: 'no' }) });

    expect(screen.queryByTestId('scheduled-tenant-deletions')).toBeNull();
    expect(screen.queryByTestId('scheduled-tenant-deletions-error')).toBeNull();
  });

  it.each([
    ['a server error', apiError(503, { message: 'boom' })],
    ['a network failure', new TypeError('Network Error')],
  ])('says so and offers a retry after %s', async (_label, failure) => {
    await renderSettled({ reject: failure });

    const alert = screen.getByTestId('scheduled-tenant-deletions-error');
    expect(alert).toHaveTextContent('Die zur Löschung vorgemerkten Gärten ließen sich gerade nicht laden');
    expect(screen.queryByTestId('scheduled-tenant-deletions')).toBeNull();

    await userEvent.click(within(alert).getByTestId('scheduled-tenant-deletions-retry'));

    expect(await screen.findByTestId('scheduled-tenant-row-lindenhof')).toBeInTheDocument();
    expect(tenantApi.listMyTenantsWithScheduledDeletion).toHaveBeenCalledTimes(2);
    expect(screen.queryByTestId('scheduled-tenant-deletions-error')).toBeNull();
  });

  it('shows a dash instead of "Invalid Date" for an unreadable deletion date', async () => {
    await renderSettled({ resolve: [{ ...PENDING, deletion_scheduled_at: 'garbage' }] });

    const row = screen.getByTestId('scheduled-tenant-row-lindenhof');
    expect(row).toHaveTextContent('Wird am — mit allen Daten gelöscht');
    expect(row).not.toHaveTextContent('Invalid Date');
  });

  it("names the garden on every row's cancel button", async () => {
    await renderSettled({
      resolve: [PENDING, { ...PENDING, key: 't-two', name: 'Kleingarten Süd', slug: 'sued' }],
    });

    expect(screen.getByTestId('cancel-tenant-erasure-lindenhof')).toHaveAccessibleName('Löschung abbrechen');
    expect(screen.getByTestId('cancel-tenant-erasure-lindenhof')).toHaveAccessibleDescription(
      'Gemeinschaftsgarten Lindenhof',
    );
    expect(screen.getByTestId('cancel-tenant-erasure-sued')).toHaveAccessibleDescription('Kleingarten Süd');
  });

  it("cancels with the lead's own password, then reloads both lists", async () => {
    const dialog = await openCancelDialog();
    expect(dialog).toHaveTextContent('Gemeinschaftsgarten Lindenhof');
    // Federated accounts confirm with a code or a fresh sign-in: the text names no factor (SCR-002).
    expect(within(dialog).getByRole('alertdialog')).toHaveAccessibleDescription(
      '„Gemeinschaftsgarten Lindenhof“ wird wieder aktiv, alle Mitgliedschaften bleiben, wie sie waren. Deshalb bestätigst du das mit deinem eigenen Zugang.',
    );
    expect(within(dialog).getByRole('alertdialog')).not.toHaveAccessibleDescription(/Passwort/);
    expect(tenantApi.cancelTenantErasure).not.toHaveBeenCalled();
    // Once cancelled the garden resolves again and the backend no longer lists it as scheduled.
    (tenantApi.listMyTenantsWithScheduledDeletion as ReturnType<typeof vi.fn>).mockResolvedValue([
      ACTIVE,
      { ...PENDING, status: 'active', is_active: true, deletion_scheduled_at: null },
    ]);

    await userEvent.type(
      within(dialog).getByTestId('cancel-own-tenant-erasure-password').querySelector('input') as HTMLInputElement,
      PASSWORD,
    );
    await userEvent.click(within(dialog).getByTestId('cancel-own-tenant-erasure-confirm'));

    await waitFor(() =>
      expect(tenantApi.cancelTenantErasure).toHaveBeenCalledWith('lindenhof', { current_password: PASSWORD }),
    );
    await waitFor(() => expect(screen.queryByTestId('cancel-own-tenant-erasure-dialog')).toBeNull());
    // The switcher's list is reloaded: the garden can be chosen again.
    await waitFor(() => expect(tenantApi.listMyTenants).toHaveBeenCalled());
    await waitFor(() => expect(screen.queryByTestId('scheduled-tenant-row-lindenhof')).toBeNull());
    expect(await screen.findByText('Löschung abgebrochen: „Gemeinschaftsgarten Lindenhof“ ist wieder aktiv')).toBeInTheDocument();
  });

  it('keeps the dialog open and says why when the step-up is refused', async () => {
    (tenantApi.cancelTenantErasure as ReturnType<typeof vi.fn>).mockRejectedValue(
      apiError(401, { error_code: 'UNAUTHORIZED', message: 'Password confirmation failed.' }),
    );
    const dialog = await openCancelDialog();

    await userEvent.type(
      within(dialog).getByTestId('cancel-own-tenant-erasure-password').querySelector('input') as HTMLInputElement,
      'wrong',
    );
    await userEvent.click(within(dialog).getByTestId('cancel-own-tenant-erasure-confirm'));

    expect(await within(dialog).findByTestId('cancel-own-tenant-erasure-error')).toHaveTextContent(
      'Password confirmation failed.',
    );
    expect(screen.getByTestId('scheduled-tenant-row-lindenhof')).toBeInTheDocument();
  });

  it('reads the list again when the cancellation comes too late (422), keeping the dialog open', async () => {
    (tenantApi.cancelTenantErasure as ReturnType<typeof vi.fn>).mockRejectedValue(
      apiError(422, { error_code: 'INVALID_STATUS_TRANSITION', message: 'The deletion can no longer be cancelled.' }),
    );
    const dialog = await openCancelDialog();
    expect(tenantApi.listMyTenantsWithScheduledDeletion).toHaveBeenCalledTimes(1);
    // A deletion run claimed the garden meanwhile: the backend no longer lists it.
    (tenantApi.listMyTenantsWithScheduledDeletion as ReturnType<typeof vi.fn>).mockResolvedValue([ACTIVE]);

    await userEvent.type(
      within(dialog).getByTestId('cancel-own-tenant-erasure-password').querySelector('input') as HTMLInputElement,
      PASSWORD,
    );
    await userEvent.click(within(dialog).getByTestId('cancel-own-tenant-erasure-confirm'));

    await waitFor(() => expect(tenantApi.listMyTenantsWithScheduledDeletion).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(screen.queryByTestId('scheduled-tenant-row-lindenhof')).toBeNull());
    // The stale row is gone, the dialog still says why.
    expect(await screen.findByTestId('cancel-own-tenant-erasure-error')).toHaveTextContent(
      'The deletion can no longer be cancelled.',
    );
  });

  it('does not read the list again when the step-up itself is refused (401)', async () => {
    (tenantApi.cancelTenantErasure as ReturnType<typeof vi.fn>).mockRejectedValue(
      apiError(401, { error_code: 'UNAUTHORIZED', message: 'Password confirmation failed.' }),
    );
    const dialog = await openCancelDialog();
    await userEvent.type(
      within(dialog).getByTestId('cancel-own-tenant-erasure-password').querySelector('input') as HTMLInputElement,
      'wrong',
    );
    await userEvent.click(within(dialog).getByTestId('cancel-own-tenant-erasure-confirm'));

    expect(await within(dialog).findByTestId('cancel-own-tenant-erasure-error')).toBeInTheDocument();
    expect(tenantApi.listMyTenantsWithScheduledDeletion).toHaveBeenCalledTimes(1);
  });

  it('asks a federated lead for a code bound to the tenant', async () => {
    (auth.listProviders as ReturnType<typeof vi.fn>).mockResolvedValue([{ provider: 'github' }]);
    const dialog = await openCancelDialog();

    await userEvent.click(await within(dialog).findByTestId('cancel-own-tenant-erasure-send-code'));

    await waitFor(() => expect(auth.requestStepUpCode).toHaveBeenCalledWith('tenant_erasure_cancel', 't-club'));
  });
});

describe('TenantSettingsPage without an active garden (#2166 review SCR-005)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    vi.clearAllMocks();
    (tenantApi.listMyTenantsWithScheduledDeletion as ReturnType<typeof vi.fn>).mockResolvedValue([PENDING]);
  });
  afterEach(() => {
    cleanup();
  });

  it('keeps its heading, says to choose a garden and lists the scheduled deletions below', async () => {
    const { default: Page } = await import('@/pages/tenants/TenantSettingsPage');
    renderWithProviders(<Page />, { store: createTestStore() });

    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Garten-Einstellungen');
    const hint = screen.getByTestId('tenant-settings-no-active-tenant');
    expect(hint).toHaveTextContent('Wähle oben in der Gartenauswahl einen Garten');
    const card = await screen.findByTestId('scheduled-tenant-deletions');
    // The hint comes first, the card below it.
    expect(hint.compareDocumentPosition(card) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(tenantApi.listMembers).not.toHaveBeenCalled();
  });
});
