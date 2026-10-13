/**
 * Axe pass for the tenant import page (REQ-056 §8.4 / §15, #2138, #1094).
 *
 * Scanned in the states a platform admin reaches: the form with a chosen archive and a member row,
 * the step-up confirmation, a refusal with its entries, and a completed import with its report.
 * Dialogs render into a portal, so the container is `document.body`; the element floor stops a scan
 * of a loading skeleton or an empty portal from counting.
 */

import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import i18n from 'i18next';
import { ApiError } from '@/api/errors';
import type { ApiErrorResponse, TenantImport } from '@/api/types';
import AdminTenantImportsPage from '@/pages/admin/AdminTenantImportsPage';
import { createTestStore, authState, renderWithProviders } from '@/test/helpers';
import { expectNoA11yViolations } from './expectNoA11yViolations';

vi.mock('@/api/endpoints/adminTenantImports', () => ({
  requestTenantImport: vi.fn(),
  getTenantImport: vi.fn(),
}));
vi.mock('@/api/endpoints/adminPlans', () => ({
  listPlans: vi.fn().mockResolvedValue([]),
  createPlan: vi.fn(),
  updatePlan: vi.fn(),
  deletePlan: vi.fn(),
}));
vi.mock('@/api/endpoints/auth', async () => ({
  ...(await vi.importActual<typeof import('@/api/endpoints/auth')>('@/api/endpoints/auth')),
  listProviders: vi.fn().mockResolvedValue([{ provider: 'local' }]),
}));

const api = await import('@/api/endpoints/adminTenantImports');

const COMPLETED: TenantImport = {
  key: 'imp-1',
  status: 'completed',
  source_format: 'kamerplanter-tenant-export/1',
  target_tenant_key: 't-new',
  plan_key: null,
  verified: false,
  report: { plant_instances: 4, sites: 1 },
  failure_reason: null,
  missing_catalog_entries: [],
  requested_at: '2026-10-12T08:00:00Z',
  completed_at: '2026-10-12T08:05:00Z',
};

async function renderPage(route = '/admin/tenant-imports') {
  renderWithProviders(<AdminTenantImportsPage />, {
    store: createTestStore(authState({ platformAdmin: true })),
    route,
  });
  await screen.findByTestId('tenant-import-admin-page');
}

async function fillForm() {
  await userEvent.upload(
    screen.getByTestId('tenant-import-file-input'),
    new File(['zip'], 'garten.zip', { type: 'application/zip' }),
  );
  await waitFor(() => expect(screen.queryByTestId('tenant-import-hashing')).toBeNull());
  await userEvent.click(screen.getByTestId('member-mapping-add'));
  await userEvent.type(
    screen
      .getByTestId('form-field-members.0.archive_user_key')
      .querySelector('input') as HTMLInputElement,
    'old-anna',
  );
  await userEvent.type(
    screen.getByTestId('form-field-members.0.email').querySelector('input') as HTMLInputElement,
    'anna@example.org',
  );
}

describe('tenant import page a11y', () => {
  beforeEach(() => i18n.changeLanguage('de'));

  it('the form with an archive and a member row has no critical axe violations', async () => {
    await renderPage();
    await fillForm();
    await expectNoA11yViolations(document.body, { minElements: 60 });
  });

  it('the step-up confirmation has no critical axe violations', async () => {
    await renderPage();
    await fillForm();
    await userEvent.click(screen.getByTestId('form-submit-button'));
    await screen.findByTestId('tenant-import-dialog');
    await expectNoA11yViolations(document.body, { minElements: 60 });
  });

  it('a refusal with its entries has no critical axe violations', async () => {
    (api.requestTenantImport as ReturnType<typeof vi.fn>).mockRejectedValue(
      new ApiError(
        {
          error_id: 'e',
          error_code: 'IMPORT_MISSING_CATALOG_ENTRIES',
          message: 'x',
          details: [
            { field: 'archive', reason: 'species/abc', code: 'IMPORT_MISSING_CATALOG_ENTRIES' },
          ],
          timestamp: '',
          path: '/',
          method: 'POST',
        } as ApiErrorResponse,
        422,
      ),
    );
    await renderPage();
    await fillForm();
    await userEvent.click(screen.getByTestId('form-submit-button'));
    const dialog = await screen.findByTestId('tenant-import-dialog');
    await userEvent.type(dialog.querySelector('input[type="password"]') as HTMLInputElement, 'pw');
    await userEvent.click(screen.getByTestId('tenant-import-confirm'));
    await screen.findByTestId('tenant-import-refusal');
    await waitFor(() => expect(screen.queryByTestId('tenant-import-dialog')).toBeNull());
    await expectNoA11yViolations(document.body, { minElements: 60 });
  });

  it('a completed import with its report has no critical axe violations', async () => {
    (api.getTenantImport as ReturnType<typeof vi.fn>).mockResolvedValue(COMPLETED);
    await renderPage('/admin/tenant-imports?import=imp-1');
    await screen.findByTestId('tenant-import-report');
    await expectNoA11yViolations(document.body, { minElements: 60 });
  });
});
