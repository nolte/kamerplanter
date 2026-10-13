import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { act, cleanup, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import { ApiError } from '@/api/errors';
import type { ApiErrorResponse, TenantImport } from '@/api/types';
import TenantImportStatusCard, {
  TENANT_IMPORT_POLL_MS,
} from '@/components/admin/TenantImportStatusCard';
import { authState, createTestStore, renderWithProviders } from '@/test/helpers';

/**
 * REQ-056 §8.4 / §15 "Fortschritt, Bericht" (#2138) — the card that follows one tenant import:
 * it polls while the import runs, then shows the report (counts per collection) and the new
 * garden, or explains the failure by its code. The signature state is visible throughout.
 */

vi.mock('@/api/endpoints/adminTenantImports', () => ({
  getTenantImport: vi.fn(),
  requestTenantImport: vi.fn(),
}));

const api = await import('@/api/endpoints/adminTenantImports');
const getImport = api.getTenantImport as ReturnType<typeof vi.fn>;

function record(overrides: Partial<TenantImport> = {}): TenantImport {
  return {
    key: 'imp-1',
    status: 'pending',
    source_format: 'kamerplanter-tenant-export/1',
    target_tenant_key: null,
    plan_key: null,
    verified: true,
    report: {},
    failure_reason: null,
    missing_catalog_entries: [],
    requested_at: '2026-10-12T08:00:00Z',
    completed_at: null,
    ...overrides,
  };
}

function apiError(status: number): ApiError {
  return new ApiError(
    {
      error_id: 'e',
      error_code: 'NOT_FOUND',
      message: 'x',
      details: [],
      timestamp: '',
      path: '/',
      method: 'GET',
    } as ApiErrorResponse,
    status,
  );
}

function renderCard(props: Partial<Parameters<typeof TenantImportStatusCard>[0]> = {}) {
  const onDismiss = vi.fn();
  renderWithProviders(
    <TenantImportStatusCard importKey="imp-1" onDismiss={onDismiss} {...props} />,
    {
      store: createTestStore(authState({ platformAdmin: true })),
    },
  );
  return { onDismiss };
}

describe('TenantImportStatusCard (REQ-056 §8.4, #2138)', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('de');
    vi.clearAllMocks();
  });
  afterEach(() => {
    cleanup();
    vi.useRealTimers();
  });

  it('polls while the import runs and shows the report and the new garden once completed', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    getImport
      .mockResolvedValueOnce(
        record({ status: 'running', target_tenant_key: 't-new', plan_key: 'community' }),
      )
      .mockResolvedValue(
        record({
          status: 'completed',
          target_tenant_key: 't-new',
          plan_key: 'community',
          report: { plant_instances: 12, sites: 1, locations: 3 },
          completed_at: '2026-10-12T08:05:00Z',
        }),
      );
    renderCard();

    expect(await screen.findByTestId('tenant-import-status-chip')).toHaveTextContent(
      'Wird importiert',
    );
    expect(screen.getByRole('progressbar', { name: 'Import läuft' })).toBeInTheDocument();
    expect(screen.getByTestId('tenant-import-plan')).toHaveTextContent('community');
    // No way to hide the only handle on a running import.
    expect(screen.queryByTestId('tenant-import-dismiss')).toBeNull();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(TENANT_IMPORT_POLL_MS);
    });

    expect(await screen.findByTestId('tenant-import-completed')).toHaveTextContent('16 Datensätze');
    expect(screen.getByTestId('tenant-import-status-chip')).toHaveTextContent('Abgeschlossen');
    const report = screen.getByTestId('tenant-import-report');
    const rows = within(report)
      .getAllByRole('term')
      .map((term) => term.textContent);
    expect(rows).toEqual(['locations', 'plant_instances', 'sites']);
    expect(screen.getByTestId('tenant-import-report-row-plant_instances')).toHaveTextContent('12');
    expect(screen.getByTestId('tenant-import-open-tenant')).toHaveAttribute(
      'href',
      '/admin/tenants/t-new',
    );
    expect(screen.queryByRole('progressbar')).toBeNull();

    // Completed: the polling stops.
    const calls = getImport.mock.calls.length;
    await act(async () => {
      await vi.advanceTimersByTimeAsync(TENANT_IMPORT_POLL_MS * 3);
    });
    expect(getImport.mock.calls.length).toBe(calls);
  });

  it('shows the record the upload answered with at once and says when the archive is not verified', async () => {
    getImport.mockResolvedValue(record({ verified: false }));
    renderCard({ initial: record({ verified: false }) });

    expect(screen.queryByTestId('loading-skeleton')).toBeNull();
    expect(screen.getByTestId('tenant-import-verified')).toHaveTextContent('Nicht verifiziert');
    expect(screen.getByTestId('tenant-import-status-body')).toHaveTextContent(
      'keine gültige Signatur',
    );
    expect(screen.getByTestId('tenant-import-plan')).toHaveTextContent('Standard-Plan');
  });

  it('explains a failure by its code and lists the missing catalogue entries', async () => {
    getImport.mockResolvedValue(
      record({
        status: 'failed',
        failure_reason: 'IMPORT_MISSING_CATALOG_ENTRIES',
        missing_catalog_entries: ['species/ocimum-basilicum'],
        completed_at: '2026-10-12T08:05:00Z',
      }),
    );
    const { onDismiss } = renderCard();

    const failed = await screen.findByTestId('tenant-import-failed');
    expect(failed).toHaveTextContent('Import gescheitert');
    expect(failed).toHaveTextContent('Katalogeinträge');
    expect(screen.getByTestId('tenant-import-missing-entries')).toHaveTextContent(
      'species/ocimum-basilicum',
    );
    expect(screen.getByTestId('tenant-import-verified')).toHaveTextContent('Signiert');

    await userEvent.click(screen.getByTestId('tenant-import-dismiss'));
    expect(onDismiss).toHaveBeenCalled();
  });

  it('marks a rollback the sweep still has to finish, and shows an unknown code verbatim', async () => {
    getImport.mockResolvedValue(
      record({ status: 'cleanup_pending', failure_reason: 'SOMETHING_ELSE' }),
    );
    renderCard();

    const failed = await screen.findByTestId('tenant-import-failed');
    expect(failed).toHaveTextContent('Aufräumen ausstehend');
    expect(failed).toHaveTextContent('SOMETHING_ELSE');
    expect(failed).toHaveTextContent('stündlichen Aufräum-Job');
  });

  it('says when the import does not exist', async () => {
    getImport.mockRejectedValue(apiError(404));
    renderCard();
    expect(await screen.findByTestId('tenant-import-not-found')).toBeInTheDocument();
  });

  it('offers a retry after a failed read', async () => {
    getImport
      .mockRejectedValueOnce(new Error('offline'))
      .mockResolvedValue(record({ status: 'validating' }));
    renderCard();

    expect(await screen.findByTestId('tenant-import-load-error')).toBeInTheDocument();
    await userEvent.click(screen.getByTestId('tenant-import-retry'));
    expect(await screen.findByTestId('tenant-import-status-chip')).toHaveTextContent(
      'Wird geprüft',
    );
    expect(screen.getByTestId('tenant-import-status-body')).toHaveTextContent(
      'vollständig geprüft',
    );
  });

  it('keeps the last state when a poll fails', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    getImport
      .mockResolvedValueOnce(record({ status: 'pending' }))
      .mockRejectedValue(new Error('offline'));
    renderCard();

    expect(await screen.findByTestId('tenant-import-status-chip')).toHaveTextContent('Angefordert');
    await act(async () => {
      await vi.advanceTimersByTimeAsync(TENANT_IMPORT_POLL_MS);
    });
    expect(screen.getByTestId('tenant-import-status-chip')).toHaveTextContent('Angefordert');
    expect(screen.queryByTestId('tenant-import-load-error')).toBeNull();
  });

  it('reads in English', async () => {
    await i18n.changeLanguage('en');
    getImport.mockResolvedValue(record({ status: 'failed', failure_reason: 'IMPORT_ABANDONED' }));
    renderCard();
    expect(await screen.findByTestId('tenant-import-failed')).toHaveTextContent(
      'stopped reporting for too long',
    );
  });
});
