import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { act, screen, waitFor, cleanup, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import { ApiError } from '@/api/errors';
import type { ApiErrorResponse, TenantExport } from '@/api/types';
import { createStoreWithTenantRole, renderWithProviders } from '@/test/helpers';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';

/**
 * REQ-056 §8, §15 (#2138) — the section "Export garden" in the garden settings.
 *
 * A lead with the `management` scope requests an export with their own step-up
 * (`tenant_export`, bound to the garden's key), watches it while the background task writes it
 * and downloads the archive once it is completed. A second export while one runs (409) and the
 * daily limit (429) are explained in the card; a refused step-up stays inside the dialog.
 */

vi.mock('@/api/endpoints/tenants', () => ({
  listTenantExports: vi.fn(),
  requestTenantExport: vi.fn(),
  downloadTenantExport: vi.fn(),
}));

vi.mock('@/api/endpoints/auth', async () => ({
  ...(await vi.importActual<typeof import('@/api/endpoints/auth')>('@/api/endpoints/auth')),
  listProviders: vi.fn(),
  requestStepUpCode: vi
    .fn()
    .mockResolvedValue({ expires_at: '2026-10-12T12:10:00Z', expires_in: 600 }),
}));

const tenantApi = await import('@/api/endpoints/tenants');
const auth = await import('@/api/endpoints/auth');
const listExports = tenantApi.listTenantExports as ReturnType<typeof vi.fn>;
const requestExport = tenantApi.requestTenantExport as ReturnType<typeof vi.fn>;
const downloadExport = tenantApi.downloadTenantExport as ReturnType<typeof vi.fn>;

// Credential-shaped values are assembled at runtime (GitGuardian, #1838).
const PASSWORD = ['export', 'Lead', 'pw', '1'].join('-');
const FUTURE = '2099-01-03T09:00:00Z';

function exportRecord(overrides: Partial<TenantExport>): TenantExport {
  return {
    key: 'exp-1',
    status: 'pending',
    origin: 'tenant_management',
    failure_reason: null,
    size_bytes: null,
    counts: {},
    requested_at: '2026-10-12T08:00:00Z',
    completed_at: null,
    expires_at: null,
    ...overrides,
  };
}

const COMPLETED = exportRecord({
  key: 'exp-done',
  status: 'completed',
  size_bytes: 5 * 1024 * 1024,
  completed_at: '2026-10-12T08:05:00Z',
  expires_at: FUTURE,
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
  const { default: Card } = await import('@/components/tenants/TenantExportCard');
  return renderWithProviders(
    <Card slug="testgarten" tenantKey="tenant-1" tenantName="Testgarten" />,
    {
      store: createStoreWithTenantRole('lead', ['management']),
    },
  );
}

async function openDialog() {
  await renderCard();
  const button = await screen.findByTestId('request-tenant-export-btn');
  await waitFor(() => expect(button).toBeEnabled());
  await userEvent.click(button);
  return screen.findByTestId('request-tenant-export-dialog');
}

async function confirmWithPassword(dialog: HTMLElement, password = PASSWORD) {
  await userEvent.type(
    within(dialog)
      .getByTestId('request-tenant-export-password')
      .querySelector('input') as HTMLInputElement,
    password,
  );
  await userEvent.click(within(dialog).getByTestId('request-tenant-export-confirm'));
}

describe('TenantExportCard (REQ-056 §8, #2138)', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('de');
    vi.clearAllMocks();
    sessionStorage.clear();
    listExports.mockResolvedValue([]);
    requestExport.mockResolvedValue(exportRecord({}));
    (auth.listProviders as ReturnType<typeof vi.fn>).mockResolvedValue([{ provider: 'local' }]);
  });
  afterEach(() => {
    cleanup();
    vi.useRealTimers();
    sessionStorage.clear();
  });

  it('explains the export and says when there is none yet', async () => {
    await renderCard();

    expect(await screen.findByTestId('tenant-export-empty')).toHaveTextContent(
      'Du hast für diesen Garten noch keinen Export angefordert.',
    );
    const card = screen.getByTestId('tenant-export-card');
    expect(within(card).getByRole('heading', { level: 2 })).toHaveTextContent('Garten exportieren');
    expect(card).toHaveTextContent('ohne E-Mail-Adressen');
    expect(listExports).toHaveBeenCalledWith('testgarten');
    expect(screen.getByTestId('request-tenant-export-btn')).toHaveAccessibleDescription(
      /Pro Tag sind höchstens drei Exporte möglich/,
    );
  });

  it("requests the export with the lead's own password, bound to the garden, then reads the list again", async () => {
    const dialog = await openDialog();
    expect(within(dialog).getByRole('alertdialog')).toHaveAccessibleDescription(/„Testgarten“/);
    listExports.mockResolvedValue([exportRecord({})]);

    await confirmWithPassword(dialog);

    await waitFor(() =>
      expect(requestExport).toHaveBeenCalledWith('testgarten', { current_password: PASSWORD }),
    );
    await waitFor(() => expect(screen.queryByTestId('request-tenant-export-dialog')).toBeNull());
    expect(
      await screen.findByText('Export angefordert – das Archiv wird jetzt erstellt.'),
    ).toBeInTheDocument();
    expect(await screen.findByTestId('tenant-export-status-exp-1')).toHaveTextContent(
      'Angefordert',
    );
    expect(listExports).toHaveBeenCalledTimes(2);
  });

  it('asks a federated lead for a code bound to the garden (step-up act tenant_export)', async () => {
    (auth.listProviders as ReturnType<typeof vi.fn>).mockResolvedValue([{ provider: 'github' }]);
    const dialog = await openDialog();

    await userEvent.click(await within(dialog).findByTestId('request-tenant-export-send-code'));

    await waitFor(() =>
      expect(auth.requestStepUpCode).toHaveBeenCalledWith('tenant_export', 'tenant-1'),
    );
  });

  it('keeps the dialog open and says why when the step-up is refused', async () => {
    requestExport.mockRejectedValue(
      apiError(401, { error_code: 'UNAUTHORIZED', message: 'Password confirmation failed.' }),
    );
    const dialog = await openDialog();

    await confirmWithPassword(dialog, 'wrong');

    expect(await within(dialog).findByTestId('request-tenant-export-error')).toHaveTextContent(
      'Password confirmation failed.',
    );
    expect(screen.queryByTestId('tenant-export-notice')).toBeNull();
    expect(listExports).toHaveBeenCalledTimes(1);
  });

  it('closes the dialog and explains a running export (409 EXPORT_ALREADY_RUNNING)', async () => {
    requestExport.mockRejectedValue(
      apiError(409, {
        error_code: 'EXPORT_ALREADY_RUNNING',
        message: 'An export of this tenant is already running.',
      }),
    );
    const dialog = await openDialog();
    listExports.mockResolvedValue([exportRecord({ status: 'running' })]);

    await confirmWithPassword(dialog);

    await waitFor(() => expect(screen.queryByTestId('request-tenant-export-dialog')).toBeNull());
    expect(await screen.findByTestId('tenant-export-notice')).toHaveTextContent(
      'Für diesen Garten wird bereits ein Export erstellt.',
    );
    expect(await screen.findByTestId('tenant-export-status-exp-1')).toHaveTextContent(
      'Wird erstellt',
    );
  });

  it('closes the dialog and explains the daily limit (429 RATE_LIMIT_EXCEEDED)', async () => {
    requestExport.mockRejectedValue(
      apiError(429, { error_code: 'RATE_LIMIT_EXCEEDED', message: 'Too many.' }),
    );
    const dialog = await openDialog();

    await confirmWithPassword(dialog);

    await waitFor(() => expect(screen.queryByTestId('request-tenant-export-dialog')).toBeNull());
    expect(await screen.findByTestId('tenant-export-notice')).toHaveTextContent(
      'in den letzten 24 Stunden schon drei Exporte angefordert',
    );
  });

  it('keeps a step-up lockout (429 STEP_UP_LOCKED) inside the dialog', async () => {
    requestExport.mockRejectedValue(
      apiError(429, {
        error_code: 'STEP_UP_LOCKED',
        message: 'Locked.',
        details: [
          { field: 'step_up', reason: 'locked', code: 'STEP_UP_LOCKED', retry_after_minutes: '15' },
        ],
      } as Partial<ApiErrorResponse>),
    );
    const dialog = await openDialog();

    await confirmWithPassword(dialog);

    expect(await within(dialog).findByTestId('request-tenant-export-error')).toBeInTheDocument();
    expect(screen.queryByTestId('tenant-export-notice')).toBeNull();
  });

  it('blocks a second request while one is on its way and polls until it is completed', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    listExports.mockResolvedValue([exportRecord({ status: 'running' })]);
    const { TENANT_EXPORT_POLL_MS } = await import('@/components/tenants/TenantExportCard');
    await renderCard();

    expect(await screen.findByTestId('tenant-export-status-exp-1')).toHaveTextContent(
      'Wird erstellt',
    );
    expect(screen.getByTestId('request-tenant-export-btn')).toBeDisabled();
    expect(screen.getByTestId('request-tenant-export-btn')).toHaveAccessibleDescription(
      /Ein Export wird gerade erstellt/,
    );
    expect(screen.queryByTestId('download-tenant-export-exp-1')).toBeNull();
    expect(listExports).toHaveBeenCalledTimes(1);

    listExports.mockResolvedValue([{ ...COMPLETED, key: 'exp-1' }]);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(TENANT_EXPORT_POLL_MS);
    });

    expect(listExports).toHaveBeenCalledTimes(2);
    expect(await screen.findByTestId('download-tenant-export-exp-1')).toBeInTheDocument();
    expect(screen.getByTestId('tenant-export-status-exp-1')).toHaveTextContent('Fertig');
    expect(screen.getByTestId('request-tenant-export-btn')).toBeEnabled();

    // Nothing is on its way any more: the card stops asking.
    await act(async () => {
      await vi.advanceTimersByTimeAsync(TENANT_EXPORT_POLL_MS * 3);
    });
    expect(listExports).toHaveBeenCalledTimes(2);
  });

  it('downloads a completed archive under its export file name', async () => {
    listExports.mockResolvedValue([COMPLETED]);
    downloadExport.mockResolvedValue(new Blob(['zip'], { type: 'application/zip' }));
    const click = vi
      .spyOn(HTMLAnchorElement.prototype, 'click')
      .mockImplementation(() => undefined);
    const revoke = vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => undefined);
    await renderCard();

    const row = await screen.findByTestId('tenant-export-row-exp-done');
    expect(row).toHaveTextContent('5 MB');
    expect(row).toHaveTextContent('Herunterladen kannst du es bis');
    const button = within(row).getByTestId('download-tenant-export-exp-done');
    expect(button).toHaveAccessibleName('Herunterladen');
    expect(button).toHaveAccessibleDescription(/Angefordert am/);

    await userEvent.click(button);

    await waitFor(() => expect(downloadExport).toHaveBeenCalledWith('testgarten', 'exp-done'));
    await waitFor(() => expect(click).toHaveBeenCalledTimes(1));
    const anchor = click.mock.instances[0] as unknown as HTMLAnchorElement;
    expect(anchor.download).toBe('kamerplanter-tenant-export-exp-done.zip');
    expect(revoke).toHaveBeenCalled();
    click.mockRestore();
    revoke.mockRestore();
  });

  it('says the archive expired when the download answers 404, and reads the list again', async () => {
    listExports.mockResolvedValue([COMPLETED]);
    downloadExport.mockRejectedValue(
      apiError(404, { error_code: 'NOT_FOUND', message: 'Not found.' }),
    );
    await renderCard();

    await userEvent.click(await screen.findByTestId('download-tenant-export-exp-done'));

    expect(await screen.findByTestId('tenant-export-notice')).toHaveTextContent(
      'Dieses Archiv ist abgelaufen und nicht mehr verfügbar.',
    );
    expect(listExports).toHaveBeenCalledTimes(2);
  });

  it('names any other download failure with its reason', async () => {
    listExports.mockResolvedValue([COMPLETED]);
    downloadExport.mockRejectedValue(
      apiError(503, { error_code: 'STORAGE', message: 'Storage unavailable.' }),
    );
    await renderCard();

    await userEvent.click(await screen.findByTestId('download-tenant-export-exp-done'));

    expect(await screen.findByTestId('tenant-export-notice')).toHaveTextContent(
      'Das Archiv konnte nicht heruntergeladen werden: Storage unavailable.',
    );
  });

  it('explains a failed and an expired export and offers neither for download', async () => {
    listExports.mockResolvedValue([
      exportRecord({ key: 'exp-big', status: 'failed', failure_reason: 'too_large' }),
      exportRecord({ key: 'exp-old', status: 'expired' }),
      { ...COMPLETED, key: 'exp-stale', expires_at: '2020-01-01T00:00:00Z' },
    ]);
    await renderCard();

    const failed = await screen.findByTestId('tenant-export-row-exp-big');
    expect(within(failed).getByTestId('tenant-export-status-exp-big')).toHaveTextContent(
      'Fehlgeschlagen',
    );
    expect(failed).toHaveTextContent('größer als der Speicher, den dieser Garten nutzen darf');
    expect(screen.getByTestId('tenant-export-row-exp-old')).toHaveTextContent(
      'nach 72 Stunden gelöscht',
    );
    expect(screen.queryByTestId('download-tenant-export-exp-big')).toBeNull();
    expect(screen.queryByTestId('download-tenant-export-exp-old')).toBeNull();
    // Completed, but its expiry has passed: the route would answer 404.
    expect(screen.queryByTestId('download-tenant-export-exp-stale')).toBeNull();
  });

  it('says so when the list cannot be read and reads it again on retry', async () => {
    listExports.mockRejectedValueOnce(apiError(503, { message: 'boom' }));
    await renderCard();

    const alert = await screen.findByTestId('tenant-export-load-error');
    expect(alert).toHaveTextContent('Die Exporte konnten nicht geladen werden.');

    await userEvent.click(within(alert).getByTestId('tenant-export-retry'));

    expect(await screen.findByTestId('tenant-export-empty')).toBeInTheDocument();
    expect(listExports).toHaveBeenCalledTimes(2);
  });

  it('has no accessibility violations with a list of exports', async () => {
    listExports.mockResolvedValue([
      COMPLETED,
      exportRecord({ key: 'exp-big', status: 'failed', failure_reason: 'too_large' }),
    ]);
    await renderCard();
    await screen.findByTestId('download-tenant-export-exp-done');

    await expectNoA11yViolations(screen.getByTestId('tenant-export-card'), { minElements: 10 });
  });

  it('renders in English', async () => {
    await i18n.changeLanguage('en');
    listExports.mockResolvedValue([COMPLETED]);
    await renderCard();

    expect(await screen.findByTestId('download-tenant-export-exp-done')).toHaveTextContent(
      'Download',
    );
    expect(screen.getByTestId('tenant-export-card')).toHaveTextContent('Export garden');
    expect(screen.getByTestId('tenant-export-status-exp-done')).toHaveTextContent('Ready');
  });
});
