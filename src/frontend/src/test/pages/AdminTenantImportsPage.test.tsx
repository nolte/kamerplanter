import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { cleanup, fireEvent, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import { ApiError } from '@/api/errors';
import type { ApiErrorResponse, Plan, TenantImport } from '@/api/types';
import AdminTenantImportsPage, {
  TENANT_IMPORT_STEP_UP_SURFACE,
} from '@/pages/admin/AdminTenantImportsPage';
import { authState, createTestStore, renderWithProviders } from '@/test/helpers';
import { saveStepUpResume, storePendingStepUpToken } from '@/utils/stepUpReauth';
import { archiveStepUpTarget } from '@/utils/tenantImport';

/**
 * REQ-056 §8.4 / §15 "Admin › Importe" (#2138) — the platform admin uploads a tenant archive,
 * maps the archive's members to existing accounts with the role they confirm, picks the plan and
 * confirms with their own step-up (`tenant_import`, bound to the archive's hash). A refused
 * step-up stays in the dialog; a refused archive closes it and is explained on the page with its
 * entries; an accepted import is followed by the status card, whose key goes into the URL.
 */

vi.mock('@/api/endpoints/adminTenantImports', () => ({
  requestTenantImport: vi.fn(),
  getTenantImport: vi.fn(),
}));

vi.mock('@/api/endpoints/adminPlans', () => ({
  listPlans: vi.fn(),
  createPlan: vi.fn(),
  updatePlan: vi.fn(),
  deletePlan: vi.fn(),
}));

vi.mock('@/api/endpoints/auth', async () => ({
  ...(await vi.importActual<typeof import('@/api/endpoints/auth')>('@/api/endpoints/auth')),
  listProviders: vi.fn(),
  requestStepUpCode: vi
    .fn()
    .mockResolvedValue({ expires_at: '2026-10-12T12:10:00Z', expires_in: 600 }),
}));

const importApi = await import('@/api/endpoints/adminTenantImports');
const plansApi = await import('@/api/endpoints/adminPlans');
const auth = await import('@/api/endpoints/auth');
const requestImport = importApi.requestTenantImport as ReturnType<typeof vi.fn>;
const getImport = importApi.getTenantImport as ReturnType<typeof vi.fn>;
const listPlans = plansApi.listPlans as ReturnType<typeof vi.fn>;
const listProviders = auth.listProviders as ReturnType<typeof vi.fn>;
const requestStepUpCode = auth.requestStepUpCode as ReturnType<typeof vi.fn>;

// Credential-shaped values are assembled at runtime (GitGuardian, #1838).
const PASSWORD = ['import', 'Admin', 'pw', '1'].join('-');

const PLAN: Plan = {
  key: 'community',
  name: 'Gemeinschaftsgarten',
  description: null,
  limits: {},
  unlimited: [],
  is_default: false,
  tenant_count: 0,
  created_at: null,
  updated_at: null,
};
const DEFAULT_PLAN: Plan = { ...PLAN, key: 'standard', name: 'Standard', is_default: true };

function importRecord(overrides: Partial<TenantImport> = {}): TenantImport {
  return {
    key: 'imp-1',
    status: 'pending',
    source_format: 'kamerplanter-tenant-export/1',
    target_tenant_key: null,
    plan_key: 'community',
    verified: true,
    report: {},
    failure_reason: null,
    missing_catalog_entries: [],
    requested_at: '2026-10-12T08:00:00Z',
    completed_at: null,
    ...overrides,
  };
}

function apiError(status: number, body: Partial<ApiErrorResponse>): ApiError {
  return new ApiError(
    {
      error_id: 'e',
      error_code: 'X',
      message: 'English',
      details: [],
      timestamp: '',
      path: '/admin/platform/tenant-imports',
      method: 'POST',
      ...body,
    } as ApiErrorResponse,
    status,
  );
}

function archive(name = 'garten.zip', content = 'zip-bytes', type = 'application/zip'): File {
  return new File([content], name, { type });
}

async function renderPage(route = '/admin/tenant-imports') {
  renderWithProviders(<AdminTenantImportsPage />, {
    store: createTestStore(authState({ platformAdmin: true })),
    route,
  });
  await screen.findByTestId('tenant-import-admin-page');
}

async function chooseFile(file: File = archive()) {
  await userEvent.upload(screen.getByTestId('tenant-import-file-input'), file);
  await waitFor(() => expect(screen.queryByTestId('tenant-import-hashing')).toBeNull());
}

function fieldInput(name: string): HTMLInputElement {
  return screen.getByTestId(`form-field-${name}`).querySelector('input') as HTMLInputElement;
}

async function addMember(index: number, key: string, email: string) {
  await userEvent.click(screen.getByTestId('member-mapping-add'));
  await userEvent.type(fieldInput(`members.${index}.archive_user_key`), key);
  await userEvent.type(fieldInput(`members.${index}.email`), email);
}

async function selectOption(name: string, value: string) {
  fireEvent.mouseDown(within(screen.getByTestId(`form-field-${name}`)).getByRole('combobox'));
  await userEvent.click(await screen.findByTestId(`form-option-${name}-${value}`));
}

async function start() {
  await userEvent.click(screen.getByTestId('form-submit-button'));
}

async function confirmWithPassword() {
  const dialog = await screen.findByTestId(`${TENANT_IMPORT_STEP_UP_SURFACE}-dialog`);
  await userEvent.type(
    within(dialog)
      .getByTestId(`${TENANT_IMPORT_STEP_UP_SURFACE}-password`)
      .querySelector('input') as HTMLInputElement,
    PASSWORD,
  );
  await userEvent.click(within(dialog).getByTestId(`${TENANT_IMPORT_STEP_UP_SURFACE}-confirm`));
  return dialog;
}

describe('AdminTenantImportsPage (REQ-056 §8.4, §15, #2138)', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('de');
    vi.clearAllMocks();
    sessionStorage.clear();
    listPlans.mockResolvedValue([DEFAULT_PLAN, PLAN]);
    listProviders.mockResolvedValue([{ provider: 'local' }]);
    requestImport.mockResolvedValue(importRecord());
    getImport.mockResolvedValue(importRecord());
  });
  afterEach(() => {
    cleanup();
    sessionStorage.clear();
  });

  it('explains what an import does, the member rules and the server-side size ceiling', async () => {
    await renderPage();

    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Garten importieren');
    expect(screen.getByTestId('tenant-imports-rules')).toHaveTextContent(
      'nie mit denen aus dem Archiv',
    );
    expect(screen.getByTestId('tenant-import-file-select')).toHaveAccessibleDescription(
      /standardmäßig 512 MB \(TENANT_IMPORT_MAX_UPLOAD_MB\)/,
    );
    expect(screen.getByTestId('tenant-import-file-info')).toHaveTextContent(
      'Noch kein Archiv ausgewählt.',
    );
    expect(screen.getByTestId('member-mapping-empty')).toBeInTheDocument();
    expect(screen.queryByTestId('tenant-import-status-card')).toBeNull();
  });

  it('asks for an archive before it opens the confirmation', async () => {
    await renderPage();
    await start();

    expect(await screen.findByTestId('tenant-import-file-missing')).toBeInTheDocument();
    expect(screen.queryByTestId(`${TENANT_IMPORT_STEP_UP_SURFACE}-dialog`)).toBeNull();
    expect(requestImport).not.toHaveBeenCalled();
  });

  it('uploads the archive with the confirmed mapping, the plan and the own password, then follows the import', async () => {
    getImport.mockResolvedValue(importRecord({ status: 'running' }));
    await renderPage();
    await chooseFile();
    expect(screen.getByTestId('tenant-import-file-info')).toHaveTextContent('garten.zip (1 kB)');

    await addMember(0, 'old-anna', 'Anna@Example.org ');
    await selectOption('members.0.role', 'lead');
    await userEvent.click(
      screen
        .getByTestId('form-field-members.0.management')
        .querySelector('input') as HTMLInputElement,
    );
    await addMember(1, 'old-ben', 'ben@example.org');
    await userEvent.click(
      screen
        .getByTestId('form-field-members.1.technical')
        .querySelector('input') as HTMLInputElement,
    );
    await selectOption('plan_key', 'community');
    await start();

    const dialog = await screen.findByTestId(`${TENANT_IMPORT_STEP_UP_SURFACE}-dialog`);
    expect(dialog).toHaveTextContent('„garten.zip“');
    expect(dialog).toHaveTextContent('2 zugeordneten Mitgliedern');
    await confirmWithPassword();

    await waitFor(() => expect(requestImport).toHaveBeenCalledTimes(1));
    const input = requestImport.mock.calls[0][0];
    expect(input.archive.name).toBe('garten.zip');
    expect(input.planKey).toBe('community');
    expect(input.stepUp).toEqual({ current_password: PASSWORD });
    expect(input.memberMapping).toEqual({
      'old-anna': { email: 'Anna@Example.org', role: 'lead', admin_scopes: ['management'] },
      'old-ben': { email: 'ben@example.org', role: 'grower', admin_scopes: ['technical'] },
    });
    expect(typeof input.onUploadProgress).toBe('function');

    expect(await screen.findByTestId('tenant-import-status-card')).toHaveTextContent('imp-1');
    await waitFor(() =>
      expect(screen.queryByTestId(`${TENANT_IMPORT_STEP_UP_SURFACE}-dialog`)).toBeNull(),
    );
    expect(
      await screen.findByText('Import angenommen. Der Fortschritt erscheint oben.'),
    ).toBeInTheDocument();
    // The form starts over; the next import is a new file.
    expect(screen.getByTestId('tenant-import-file-info')).toHaveTextContent(
      'Noch kein Archiv ausgewählt.',
    );
    expect(screen.getByTestId('member-mapping-empty')).toBeInTheDocument();
  });

  it('sends no plan for the default and no mapping when no member is mapped', async () => {
    await renderPage();
    await chooseFile();
    await start();
    await confirmWithPassword();

    await waitFor(() => expect(requestImport).toHaveBeenCalled());
    expect(requestImport.mock.calls[0][0]).toMatchObject({ planKey: undefined, memberMapping: {} });
  });

  it('binds an e-mailed code to "archive:" and the first 32 hex digits of the file’s SHA-256', async () => {
    // A federated-only account confirms with a code; the code is requested for this file only.
    listProviders.mockResolvedValue([{ provider: 'github' }]);
    const file = archive('garten.zip', 'exactly-these-bytes');
    const expected = await archiveStepUpTarget(file);
    expect(expected).toMatch(/^archive:[0-9a-f]{32}$/);

    await renderPage();
    await chooseFile(file);
    await start();
    const dialog = await screen.findByTestId(`${TENANT_IMPORT_STEP_UP_SURFACE}-dialog`);
    await userEvent.click(
      await within(dialog).findByTestId(`${TENANT_IMPORT_STEP_UP_SURFACE}-send-code`),
    );

    await waitFor(() => expect(requestStepUpCode).toHaveBeenCalledWith('tenant_import', expected));
  });

  it('keeps a refused step-up inside the dialog', async () => {
    requestImport.mockRejectedValue(
      apiError(401, { error_code: 'UNAUTHORIZED', message: 'Current password is incorrect.' }),
    );
    await renderPage();
    await chooseFile();
    await start();
    const dialog = await confirmWithPassword();

    expect(
      await within(dialog).findByTestId(`${TENANT_IMPORT_STEP_UP_SURFACE}-error`),
    ).toBeInTheDocument();
    expect(screen.getByTestId(`${TENANT_IMPORT_STEP_UP_SURFACE}-dialog`)).toBeInTheDocument();
    expect(screen.queryByTestId('tenant-import-refusal')).toBeNull();
  });

  it('closes the dialog on a refused archive and marks the member rows the server could not resolve', async () => {
    requestImport.mockRejectedValue(
      apiError(422, {
        error_code: 'IMPORT_MEMBER_NOT_FOUND',
        message: 'Each mapped member must be a member of the archive.',
        details: [{ field: 'archive', reason: 'old-ben', code: 'IMPORT_MEMBER_NOT_FOUND' }],
      }),
    );
    await renderPage();
    await chooseFile();
    await addMember(0, 'old-anna', 'anna@example.org');
    await addMember(1, 'old-ben', 'ben@example.org');
    await start();
    await confirmWithPassword();

    const refusal = await screen.findByTestId('tenant-import-refusal');
    expect(refusal).toHaveTextContent('es wurde nichts geschrieben');
    expect(refusal).toHaveTextContent('Die betroffenen Zeilen sind markiert.');
    expect(screen.getByTestId('tenant-import-refusal-entries')).toHaveTextContent('old-ben');
    await waitFor(() =>
      expect(screen.queryByTestId(`${TENANT_IMPORT_STEP_UP_SURFACE}-dialog`)).toBeNull(),
    );
    expect(screen.getByTestId('form-field-members.1.archive_user_key')).toHaveTextContent(
      'Der Server konnte diese Zuordnung nicht auflösen',
    );
    expect(screen.getByTestId('form-field-members.0.archive_user_key')).not.toHaveTextContent(
      'Der Server konnte diese Zuordnung nicht auflösen',
    );
    // The file stays chosen for the corrected attempt.
    expect(screen.getByTestId('tenant-import-file-info')).toHaveTextContent('garten.zip');

    await userEvent.click(within(refusal).getByRole('button', { name: /schließen|close/i }));
    expect(screen.queryByTestId('tenant-import-refusal')).toBeNull();
  });

  it.each([
    ['MEMBER_LIMIT_REACHED', 422, 'weniger Mitglieder zu'],
    ['STORAGE_QUOTA_EXCEEDED', 409, 'mehr Speicher'],
    ['PHOTO_QUOTA_EXCEEDED', 409, 'Galeriefotos'],
    ['IMPORT_MISSING_CATALOG_ENTRIES', 422, 'Katalogeinträge'],
    ['RATE_LIMIT_EXCEEDED', 429, 'zu viele Importe'],
  ])('explains the refusal %s on the page', async (code, status, text) => {
    requestImport.mockRejectedValue(apiError(status, { error_code: code }));
    await renderPage();
    await chooseFile();
    await start();
    await confirmWithPassword();

    expect(await screen.findByTestId('tenant-import-refusal')).toHaveTextContent(text);
  });

  it('surfaces the ceiling the server named when it refuses the size', async () => {
    requestImport.mockRejectedValue(
      apiError(413, {
        error_code: 'PAYLOAD_TOO_LARGE',
        message: 'File exceeds maximum allowed size of 128 MB.',
      }),
    );
    await renderPage();
    await chooseFile();
    await start();
    await confirmWithPassword();

    const refusal = await screen.findByTestId('tenant-import-refusal');
    expect(refusal).toHaveTextContent('(128 MB, Einstellung TENANT_IMPORT_MAX_UPLOAD_MB)');
  });

  it('explains a 413 without a named limit (a proxy in front of the server)', async () => {
    requestImport.mockRejectedValue(apiError(413, { error_code: 'X', message: 'Too big' }));
    await renderPage();
    await chooseFile();
    await start();
    await confirmWithPassword();

    expect(await screen.findByTestId('tenant-import-refusal')).toHaveTextContent('HTTP 413');
  });

  it('warns about a file above the default ceiling and about a file that is no ZIP, without blocking', async () => {
    await renderPage();
    const big = archive('riesig.zip');
    Object.defineProperty(big, 'size', { value: 600 * 1024 * 1024 });
    await chooseFile(big);
    expect(screen.getByTestId('tenant-import-file-too-large')).toHaveTextContent('512 MB');
    expect(screen.queryByTestId('tenant-import-file-not-zip')).toBeNull();
    expect(screen.getByTestId('tenant-import-file-info')).toHaveTextContent('600 MB');

    // `accept` only filters the picker; a file dropped past it still arrives — and gets the warning.
    const user = userEvent.setup({ applyAccept: false });
    await user.upload(
      screen.getByTestId('tenant-import-file-input'),
      archive('notizen.txt', 'x', 'text/plain'),
    );
    await waitFor(() => expect(screen.queryByTestId('tenant-import-hashing')).toBeNull());
    expect(screen.getByTestId('tenant-import-file-not-zip')).toBeInTheDocument();
    expect(screen.queryByTestId('tenant-import-file-too-large')).toBeNull();
    expect(screen.getByTestId('tenant-import-file-select')).toHaveTextContent(
      'Anderes Archiv wählen',
    );
    expect(screen.getByTestId('form-submit-button')).toBeEnabled();
  });

  it('opens the file picker from the button', async () => {
    await renderPage();
    const input = screen.getByTestId('tenant-import-file-input') as HTMLInputElement;
    const click = vi.spyOn(input, 'click');
    await userEvent.click(screen.getByTestId('tenant-import-file-select'));
    expect(click).toHaveBeenCalled();
  });

  it('validates the mapping: required key, valid address, one row per archive key', async () => {
    await renderPage();
    await chooseFile();
    await userEvent.click(screen.getByTestId('member-mapping-add'));
    await start();
    expect(await screen.findByTestId('form-field-members.0.archive_user_key')).toHaveTextContent(
      'Pflichtfeld',
    );
    expect(screen.getByTestId('form-field-members.0.email')).toHaveTextContent(
      'gültige E-Mail-Adresse',
    );

    await userEvent.type(fieldInput('members.0.archive_user_key'), 'same');
    await userEvent.type(fieldInput('members.0.email'), 'a@example.org');
    await addMember(1, 'same', 'b@example.org');
    await start();
    expect(await screen.findByText('Dieser Schlüssel ist schon zugeordnet.')).toBeInTheDocument();
    expect(screen.queryByTestId(`${TENANT_IMPORT_STEP_UP_SURFACE}-dialog`)).toBeNull();
  });

  it('removes a mapping row', async () => {
    await renderPage();
    await addMember(0, 'old-anna', 'anna@example.org');
    expect(screen.getByRole('heading', { name: 'Mitglied 1' })).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Zuordnung 1 entfernen' }));
    expect(screen.queryByRole('heading', { name: 'Mitglied 1' })).toBeNull();
    expect(screen.getByTestId('member-mapping-empty')).toBeInTheDocument();
  });

  it('offers the default plan alone and says so when the plans cannot be read', async () => {
    listPlans.mockRejectedValue(new Error('offline'));
    await renderPage();
    expect(await screen.findByText(/Die Pläne konnten nicht geladen werden/)).toBeInTheDocument();
  });

  it('marks the installation’s default plan in the list', async () => {
    await renderPage();
    fireEvent.mouseDown(within(screen.getByTestId('form-field-plan_key')).getByRole('combobox'));
    expect(await screen.findByTestId('form-option-plan_key-standard')).toHaveTextContent(
      'Standard (Standard)',
    );
    expect(screen.getByTestId('form-option-plan_key-__default__')).toHaveTextContent(
      'Standard-Plan der Installation',
    );
  });

  it('keeps following the import named in the URL after a reload, and forgets it when hidden', async () => {
    getImport.mockResolvedValue(
      importRecord({ key: 'imp-9', status: 'completed', report: { sites: 1 } }),
    );
    await renderPage('/admin/tenant-imports?import=imp-9');

    expect(await screen.findByTestId('tenant-import-completed')).toBeInTheDocument();
    expect(getImport).toHaveBeenCalledWith('imp-9');
    await userEvent.click(screen.getByTestId('tenant-import-dismiss'));
    expect(screen.queryByTestId('tenant-import-status-card')).toBeNull();
  });

  it('after a fresh sign-in asks for the same file again and then confirms with the token bound to it', async () => {
    const file = archive('garten.zip', 'same-file-again');
    const target = await archiveStepUpTarget(file);
    saveStepUpResume({
      surface: TENANT_IMPORT_STEP_UP_SURFACE,
      action: 'tenant_import',
      target,
      returnPath: '/admin/tenant-imports',
    });
    storePendingStepUpToken('reauth-token', 'tenant_import', target);
    listProviders.mockResolvedValue([{ provider: 'oidc', provider_key: 'kc' }]);

    await renderPage();
    expect(screen.getByTestId('tenant-import-resumed')).toHaveTextContent('Wähle das Archiv');
    // The dialog does not reopen on its own: the file did not survive the redirect.
    expect(screen.queryByTestId(`${TENANT_IMPORT_STEP_UP_SURFACE}-dialog`)).toBeNull();

    await chooseFile(file);
    await start();
    const dialog = await screen.findByTestId(`${TENANT_IMPORT_STEP_UP_SURFACE}-dialog`);
    expect(
      await within(dialog).findByTestId(`${TENANT_IMPORT_STEP_UP_SURFACE}-reauth-done`),
    ).toBeInTheDocument();
    await userEvent.click(within(dialog).getByTestId(`${TENANT_IMPORT_STEP_UP_SURFACE}-confirm`));

    await waitFor(() => expect(requestImport).toHaveBeenCalled());
    expect(requestImport.mock.calls[0][0].stepUp).toEqual({ step_up_token: 'reauth-token' });
  });

  it('shows the upload progress inside the dialog while the archive is sent', async () => {
    let finish: (value: TenantImport) => void = () => undefined;
    requestImport.mockImplementation(
      (input: { onUploadProgress: (percent: number) => void }) =>
        new Promise<TenantImport>((resolve) => {
          input.onUploadProgress(40);
          finish = resolve;
        }),
    );
    await renderPage();
    await chooseFile();
    await start();
    const dialog = await confirmWithPassword();

    expect(await within(dialog).findByText(/Hochgeladen: 40 %/)).toBeInTheDocument();
    expect(
      within(dialog).getByRole('progressbar', { name: 'Fortschritt des Uploads' }),
    ).toHaveAttribute('aria-valuenow', '40');
    const progress = requestImport.mock.calls[0][0].onUploadProgress as (percent: number) => void;
    progress(100);
    expect(await within(dialog).findByText(/Der Server prüft das Archiv/)).toBeInTheDocument();
    finish(importRecord());
    expect(await screen.findByTestId('tenant-import-status-card')).toBeInTheDocument();
  });

  it('cancels the confirmation without uploading', async () => {
    await renderPage();
    await chooseFile();
    await start();
    const dialog = await screen.findByTestId(`${TENANT_IMPORT_STEP_UP_SURFACE}-dialog`);
    await userEvent.click(within(dialog).getByTestId(`${TENANT_IMPORT_STEP_UP_SURFACE}-cancel`));
    await waitFor(() =>
      expect(screen.queryByTestId(`${TENANT_IMPORT_STEP_UP_SURFACE}-dialog`)).toBeNull(),
    );
    expect(requestImport).not.toHaveBeenCalled();
  });

  it('reads in English', async () => {
    await i18n.changeLanguage('en');
    await renderPage();
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Import a garden');
    expect(screen.getByTestId('tenant-imports-rules')).toHaveTextContent(
      'never those in the archive',
    );
  });
});
