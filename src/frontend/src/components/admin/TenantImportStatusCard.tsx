import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link as RouterLink } from 'react-router-dom';
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import LinearProgress from '@mui/material/LinearProgress';
import Skeleton from '@mui/material/Skeleton';
import Typography from '@mui/material/Typography';
import AssignmentTurnedInIcon from '@mui/icons-material/AssignmentTurnedIn';
import VerifiedIcon from '@mui/icons-material/Verified';
import GppMaybeIcon from '@mui/icons-material/GppMaybe';
import { getTenantImport } from '@/api/endpoints/adminTenantImports';
import { isApiError } from '@/api/errors';
import type { TenantImport, TenantImportStatus } from '@/api/types';
import { formatDateTime, formatNumber } from '@/utils/formatting';
import { failureCodeKey, isActiveImport } from '@/utils/tenantImport';

/** How often the card asks again while the import is on its way. */
export const TENANT_IMPORT_POLL_MS = 3000;

const STATUS_COLORS: Readonly<
  Record<TenantImportStatus, 'default' | 'info' | 'success' | 'error' | 'warning'>
> = {
  pending: 'info',
  validating: 'info',
  running: 'info',
  completed: 'success',
  failed: 'error',
  cleanup_pending: 'warning',
};

type LoadState =
  | { status: 'loading' }
  | { status: 'notFound' }
  | { status: 'error' }
  | { status: 'data'; record: TenantImport };

interface TenantImportStatusCardProps {
  /** Key of the import request (`TenantImportResponse.key`). */
  importKey: string;
  /** The record the upload answered with, shown at once instead of a skeleton. */
  initial?: TenantImport | null;
  /** Hides the card and forgets the import (it stays on the server). */
  onDismiss: () => void;
}

/**
 * Progress and report of one tenant import (REQ-056 §8.4, §15 "Fortschritt, Bericht").
 *
 * Polls `GET /admin/platform/tenant-imports/{key}` every {@link TENANT_IMPORT_POLL_MS} ms while the
 * import is `pending`, `validating` or `running`; a failed read keeps the last state and the
 * polling. Once completed it shows the rows written per collection (counts only — the server keeps
 * no contents) and links the new garden; a failure is explained by its code. Whether the archive
 * carried this installation's signature is shown throughout: an unsigned archive is imported, but
 * its contents were not proven to come from here.
 */
export default function TenantImportStatusCard({
  importKey,
  initial,
  onDismiss,
}: TenantImportStatusCardProps) {
  const { t } = useTranslation();
  const [state, setState] = useState<LoadState>(() =>
    initial && initial.key === importKey
      ? { status: 'data', record: initial }
      : { status: 'loading' },
  );

  const load = useCallback(async () => {
    try {
      const record = await getTenantImport(importKey);
      setState({ status: 'data', record });
    } catch (error) {
      if (isApiError(error) && error.statusCode === 404) {
        setState({ status: 'notFound' });
        return;
      }
      setState((previous) => (previous.status === 'data' ? previous : { status: 'error' }));
    }
  }, [importKey]);

  useEffect(() => {
    void load(); // eslint-disable-line react-hooks/set-state-in-effect -- async function, setState is after await
  }, [load]);

  const active = state.status === 'data' && isActiveImport(state.record.status);

  useEffect(() => {
    if (!active) return;
    const timer = window.setInterval(() => {
      void load();
    }, TENANT_IMPORT_POLL_MS);
    return () => window.clearInterval(timer);
  }, [active, load]);

  const reportRows = useMemo(() => {
    if (state.status !== 'data') return [];
    return Object.entries(state.record.report).sort(([a], [b]) => a.localeCompare(b));
  }, [state]);

  const total = useMemo(() => reportRows.reduce((sum, [, count]) => sum + count, 0), [reportRows]);

  return (
    <Card sx={{ mb: 3 }} data-testid="tenant-import-status-card">
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1, flexWrap: 'wrap' }}>
          <AssignmentTurnedInIcon color="primary" aria-hidden />
          <Typography variant="h6" component="h2" sx={{ flex: 1 }}>
            {t('pages.tenantImports.status.title')}
          </Typography>
          {state.status === 'data' && (
            <Chip
              label={t(`enums.tenantImportStatus.${state.record.status}`)}
              color={STATUS_COLORS[state.record.status]}
              data-testid="tenant-import-status-chip"
            />
          )}
        </Box>
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ mb: 2, fontFamily: 'monospace', wordBreak: 'break-all' }}
        >
          {t('pages.tenantImports.status.key', { key: importKey })}
        </Typography>

        {state.status === 'loading' && (
          <Box aria-busy="true" data-testid="loading-skeleton">
            <Skeleton variant="rounded" height={48} sx={{ mb: 1 }} />
            <Skeleton variant="rounded" height={48} />
          </Box>
        )}

        {state.status === 'notFound' && (
          <Alert severity="warning" data-testid="tenant-import-not-found">
            {t('pages.tenantImports.status.notFound')}
          </Alert>
        )}

        {state.status === 'error' && (
          <Alert
            severity="warning"
            data-testid="tenant-import-load-error"
            action={
              <Button
                color="inherit"
                size="small"
                onClick={() => {
                  setState({ status: 'loading' });
                  void load();
                }}
                data-testid="tenant-import-retry"
                sx={{ minHeight: 44 }}
              >
                {t('common.retry')}
              </Button>
            }
          >
            {t('pages.tenantImports.status.loadFailed')}
          </Alert>
        )}

        {state.status === 'data' && (
          <Box aria-live="polite" data-testid="tenant-import-status-body">
            {active && (
              <Box sx={{ mb: 2 }}>
                <LinearProgress aria-label={t('pages.tenantImports.status.progressLabel')} />
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  {t(`pages.tenantImports.status.activeInfo.${state.record.status}`)}
                </Typography>
              </Box>
            )}

            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
              <Chip
                size="small"
                variant="outlined"
                icon={state.record.verified ? <VerifiedIcon /> : <GppMaybeIcon />}
                color={state.record.verified ? 'success' : 'warning'}
                label={
                  state.record.verified
                    ? t('pages.tenantImports.status.verified')
                    : t('pages.tenantImports.status.unverified')
                }
                data-testid="tenant-import-verified"
              />
              <Chip
                size="small"
                variant="outlined"
                label={t('pages.tenantImports.status.plan', {
                  plan: state.record.plan_key ?? t('pages.tenantImports.form.planDefault'),
                })}
                data-testid="tenant-import-plan"
              />
            </Box>
            {!state.record.verified && (
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('pages.tenantImports.status.unverifiedHint')}
              </Typography>
            )}

            <Typography variant="body2" sx={{ mb: 2 }}>
              {t('pages.tenantImports.status.requestedAt', {
                date: formatDateTime(state.record.requested_at),
              })}
              {state.record.completed_at &&
                ` · ${t('pages.tenantImports.status.completedAt', { date: formatDateTime(state.record.completed_at) })}`}
            </Typography>

            {state.record.status === 'completed' && (
              <Alert severity="success" sx={{ mb: 2 }} data-testid="tenant-import-completed">
                <AlertTitle>{t('pages.tenantImports.status.completedTitle')}</AlertTitle>
                {t('pages.tenantImports.status.completedInfo', {
                  count: total,
                  formatted: formatNumber(total),
                })}
                {state.record.target_tenant_key && (
                  <Box sx={{ mt: 1 }}>
                    <Button
                      component={RouterLink}
                      to={`/admin/tenants/${encodeURIComponent(state.record.target_tenant_key)}`}
                      variant="outlined"
                      color="inherit"
                      size="small"
                      sx={{ minHeight: 44 }}
                      data-testid="tenant-import-open-tenant"
                    >
                      {t('pages.tenantImports.status.openTenant')}
                    </Button>
                  </Box>
                )}
              </Alert>
            )}

            {(state.record.status === 'failed' || state.record.status === 'cleanup_pending') && (
              <Alert
                severity={state.record.status === 'failed' ? 'error' : 'warning'}
                sx={{ mb: 2 }}
                data-testid="tenant-import-failed"
              >
                <AlertTitle>
                  {state.record.status === 'failed'
                    ? t('pages.tenantImports.status.failedTitle')
                    : t('pages.tenantImports.status.cleanupPendingTitle')}
                </AlertTitle>
                {t(`pages.tenantImports.failure.${failureCodeKey(state.record.failure_reason)}`, {
                  code: state.record.failure_reason ?? '—',
                })}
                {state.record.status === 'cleanup_pending' && (
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    {t('pages.tenantImports.status.cleanupPendingInfo')}
                  </Typography>
                )}
                {state.record.missing_catalog_entries.length > 0 && (
                  <Box
                    component="ul"
                    sx={{ m: 0, mt: 1, pl: 2.5, fontFamily: 'monospace', wordBreak: 'break-all' }}
                    data-testid="tenant-import-missing-entries"
                  >
                    {state.record.missing_catalog_entries.map((entry) => (
                      <li key={entry}>{entry}</li>
                    ))}
                  </Box>
                )}
              </Alert>
            )}

            {reportRows.length > 0 && (
              <>
                <Typography variant="subtitle2" component="h3" sx={{ mb: 1 }}>
                  {t('pages.tenantImports.status.reportTitle')}
                </Typography>
                <Box
                  component="dl"
                  sx={{
                    display: 'grid',
                    gridTemplateColumns: 'minmax(0, 1fr) auto',
                    columnGap: 2,
                    rowGap: 0.5,
                    m: 0,
                  }}
                  data-testid="tenant-import-report"
                >
                  {reportRows.map(([collection, count]) => (
                    <Box
                      key={collection}
                      sx={{ display: 'contents' }}
                      data-testid={`tenant-import-report-row-${collection}`}
                    >
                      <Typography
                        component="dt"
                        variant="body2"
                        sx={{ fontFamily: 'monospace', wordBreak: 'break-all' }}
                      >
                        {collection}
                      </Typography>
                      <Typography component="dd" variant="body2" sx={{ m: 0, textAlign: 'right' }}>
                        {formatNumber(count)}
                      </Typography>
                    </Box>
                  ))}
                </Box>
              </>
            )}
          </Box>
        )}

        {/* While the import runs the card is the only handle on it (there is no list route): no dismiss. */}
        {!active && (
          <Box sx={{ mt: 2 }}>
            <Button onClick={onDismiss} sx={{ minHeight: 44 }} data-testid="tenant-import-dismiss">
              {t('pages.tenantImports.status.dismiss')}
            </Button>
          </Box>
        )}
      </CardContent>
    </Card>
  );
}
