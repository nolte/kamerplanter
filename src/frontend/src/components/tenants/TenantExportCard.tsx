import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import Divider from '@mui/material/Divider';
import Skeleton from '@mui/material/Skeleton';
import Typography from '@mui/material/Typography';
import ArchiveIcon from '@mui/icons-material/Archive';
import DownloadIcon from '@mui/icons-material/Download';
import * as tenantApi from '@/api/endpoints/tenants';
import { isApiError, parseApiError } from '@/api/errors';
import type { TenantExport, TenantExportStatus } from '@/api/types';
import StepUpConfirmDialog from '@/components/common/StepUpConfirmDialog';
import type { StepUpConfirmation } from '@/components/common/StepUpConfirmDialog';
import { useStepUpResume } from '@/hooks/useStepUpReauth';
import { formatDateTime, formatNumber } from '@/utils/formatting';
import { toCredentialStepUpBody } from '@/utils/stepUp';

/** The surface id the step-up dialog saves before a fresh sign-in at the identity provider. */
export const TENANT_EXPORT_STEP_UP_SURFACE = 'request-tenant-export';

/** How often the card asks again while an export is pending or running. */
export const TENANT_EXPORT_POLL_MS = 5000;

type LoadState =
  { status: 'loading' } | { status: 'error' } | { status: 'data'; exports: TenantExport[] };

/** A notice inside the card that is not an error of the dialog (the dialog shows its own). */
type Notice = { severity: 'info' | 'warning' | 'error'; message: string } | null;

const ACTIVE_STATUSES: ReadonlySet<TenantExportStatus> = new Set(['pending', 'running']);

const STATUS_COLORS: Readonly<
  Record<TenantExportStatus, 'default' | 'info' | 'success' | 'error' | 'warning'>
> = {
  pending: 'info',
  running: 'info',
  completed: 'success',
  failed: 'error',
  expired: 'default',
};

function isActive(item: TenantExport): boolean {
  return ACTIVE_STATUSES.has(item.status);
}

/** A completed archive that has not run out yet — the only state the download route serves. */
function isDownloadable(item: TenantExport): boolean {
  if (item.status !== 'completed') return false;
  if (!item.expires_at) return true;
  const expires = new Date(item.expires_at).getTime();
  return Number.isNaN(expires) || expires > Date.now();
}

/** Size in MB (or kB below one MB), locale-formatted. */
function formatSize(bytes: number): string {
  if (bytes < 1024 * 1024) {
    return `${formatNumber(Math.max(1, Math.round(bytes / 1024)))} kB`;
  }
  return `${formatNumber(bytes / (1024 * 1024), { maximumFractionDigits: 1 })} MB`;
}

interface TenantExportCardProps {
  /** URL slug of the active garden. */
  slug: string;
  /** The garden's key — the step-up is bound to it (#1884). */
  tenantKey: string;
  tenantName: string;
}

/**
 * The section "Export garden" in the garden settings (REQ-056 §8, §15, #2138).
 *
 * Shown only to a lead holding the `management` scope, in full mode — the routes exist nowhere
 * else, and the backend decides again from the stored membership. Requesting an export asks for
 * the requester's own step-up (`tenant_export`, bound to the garden's key) and answers
 * `202 Accepted`: a background task writes the archive. While one is pending or running the card
 * polls the list every {@link TENANT_EXPORT_POLL_MS} ms and offers the download once it is
 * completed, until it expires after 72 hours. Only the caller's own exports are listed.
 *
 * A second export while one runs (`409 EXPORT_ALREADY_RUNNING`) and the daily limit
 * (`429 RATE_LIMIT_EXCEEDED`) close the dialog and are explained in the card — the step-up was
 * accepted, only the export was not; a refused step-up stays inside the dialog.
 */
export default function TenantExportCard({ slug, tenantKey, tenantName }: TenantExportCardProps) {
  const { t } = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  // #1815 — back from the fresh sign-in at the identity provider: reopen the dialog once.
  const resumed = useStepUpResume(TENANT_EXPORT_STEP_UP_SURFACE);
  const [dialogOpen, setDialogOpen] = useState(resumed);
  const [state, setState] = useState<LoadState>({ status: 'loading' });
  const [notice, setNotice] = useState<Notice>(null);
  const [downloading, setDownloading] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const exports = await tenantApi.listTenantExports(slug);
      setState({ status: 'data', exports });
    } catch {
      setState((previous) => (previous.status === 'data' ? previous : { status: 'error' }));
    }
  }, [slug]);

  useEffect(() => {
    void load(); // eslint-disable-line react-hooks/set-state-in-effect -- async function, setState is after await
  }, [load]);

  const exports = state.status === 'data' ? state.exports : [];
  const hasActive = exports.some(isActive);

  // Poll only while an export is on its way; a failed read keeps the last list and the polling.
  useEffect(() => {
    if (!hasActive) return;
    const timer = window.setInterval(() => {
      void load();
    }, TENANT_EXPORT_POLL_MS);
    return () => window.clearInterval(timer);
  }, [hasActive, load]);

  // The requester's OWN step-up; a refused step-up propagates to the dialog, which shows it.
  const handleConfirm = async (credentials: StepUpConfirmation) => {
    setNotice(null);
    try {
      await tenantApi.requestTenantExport(slug, toCredentialStepUpBody(credentials));
    } catch (error) {
      if (isApiError(error) && error.errorCode === 'EXPORT_ALREADY_RUNNING') {
        setDialogOpen(false);
        setNotice({ severity: 'info', message: t('pages.tenants.export.alreadyRunning') });
        void load();
        return;
      }
      if (isApiError(error) && error.errorCode === 'RATE_LIMIT_EXCEEDED') {
        setDialogOpen(false);
        setNotice({ severity: 'warning', message: t('pages.tenants.export.dailyLimitReached') });
        return;
      }
      throw error;
    }
    setDialogOpen(false);
    enqueueSnackbar(t('pages.tenants.export.requested'), { variant: 'success' });
    void load();
  };

  const handleDownload = async (item: TenantExport) => {
    setNotice(null);
    setDownloading(item.key);
    try {
      // The route is JWT-protected, so a plain anchor href cannot fetch it: the bytes come
      // through the authenticated client and are handed to the browser as an object URL.
      const blob = await tenantApi.downloadTenantExport(slug, item.key);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = `kamerplanter-tenant-export-${item.key}.zip`;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      if (isApiError(error) && error.statusCode === 404) {
        setNotice({ severity: 'warning', message: t('pages.tenants.export.downloadExpired') });
        void load();
      } else {
        setNotice({
          severity: 'error',
          message: t('pages.tenants.export.downloadFailed', { reason: parseApiError(error) }),
        });
      }
    } finally {
      setDownloading(null);
    }
  };

  const statusLine = (item: TenantExport): string => {
    switch (item.status) {
      case 'pending':
      case 'running':
        return t('pages.tenants.export.activeInfo');
      case 'completed':
        return item.expires_at
          ? t('pages.tenants.export.completedInfo', { date: formatDateTime(item.expires_at) })
          : t('pages.tenants.export.completedNoExpiryInfo');
      case 'failed':
        return t(`pages.tenants.export.failureReason.${item.failure_reason ?? 'internal_error'}`);
      case 'expired':
        return t('pages.tenants.export.expiredInfo');
    }
  };

  return (
    <Card sx={{ mb: 3 }} data-testid="tenant-export-card">
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1 }}>
          <ArchiveIcon color="primary" aria-hidden />
          <Typography variant="h6" component="h2">
            {t('pages.tenants.export.title')}
          </Typography>
        </Box>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {t('pages.tenants.export.intro')}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.tenants.export.contentHint')}
        </Typography>

        <Box
          sx={{
            display: 'flex',
            flexDirection: { xs: 'column', sm: 'row' },
            alignItems: { xs: 'stretch', sm: 'center' },
            gap: 1.5,
            mb: 2,
          }}
        >
          <Button
            variant="contained"
            startIcon={<ArchiveIcon />}
            onClick={() => {
              setNotice(null);
              setDialogOpen(true);
            }}
            disabled={hasActive || state.status === 'loading'}
            aria-describedby="tenant-export-request-hint"
            data-testid="request-tenant-export-btn"
            sx={{ minHeight: 44, flexShrink: 0 }}
          >
            {t('pages.tenants.export.request')}
          </Button>
          <Typography
            id="tenant-export-request-hint"
            variant="body2"
            color="text.secondary"
            aria-live="polite"
          >
            {hasActive
              ? t('pages.tenants.export.requestBlockedHint')
              : t('pages.tenants.export.requestHint')}
          </Typography>
        </Box>

        {notice && (
          <Alert
            severity={notice.severity}
            onClose={() => setNotice(null)}
            sx={{ mb: 2 }}
            data-testid="tenant-export-notice"
          >
            {notice.message}
          </Alert>
        )}

        {state.status === 'loading' && (
          <Box aria-busy="true" data-testid="loading-skeleton">
            {[0, 1].map((i) => (
              <Skeleton key={i} variant="rounded" height={48} sx={{ mb: 1 }} />
            ))}
          </Box>
        )}

        {state.status === 'error' && (
          <Alert
            severity="warning"
            data-testid="tenant-export-load-error"
            action={
              <Button
                color="inherit"
                size="small"
                onClick={() => {
                  setState({ status: 'loading' });
                  void load();
                }}
                data-testid="tenant-export-retry"
                sx={{ minHeight: 44 }}
              >
                {t('common.retry')}
              </Button>
            }
          >
            {t('pages.tenants.export.loadFailed')}
          </Alert>
        )}

        {state.status === 'data' && exports.length === 0 && (
          <Typography variant="body2" color="text.secondary" data-testid="tenant-export-empty">
            {t('pages.tenants.export.empty')}
          </Typography>
        )}

        {exports.length > 0 && (
          <>
            <Typography variant="subtitle2" component="h3" sx={{ mb: 1 }}>
              {t('pages.tenants.export.listTitle')}
            </Typography>
            <Box
              component="ul"
              aria-live="polite"
              sx={{ listStyle: 'none', m: 0, p: 0 }}
              data-testid="tenant-export-list"
            >
              {exports.map((item, index) => {
                const downloadable = isDownloadable(item);
                const requestedId = `tenant-export-requested-${item.key}`;
                return (
                  <Box component="li" key={item.key} data-testid={`tenant-export-row-${item.key}`}>
                    {index > 0 && <Divider sx={{ my: 1.5 }} />}
                    <Box
                      sx={{
                        display: 'flex',
                        flexDirection: { xs: 'column', sm: 'row' },
                        alignItems: { xs: 'stretch', sm: 'center' },
                        gap: 1.5,
                      }}
                    >
                      <Box sx={{ flex: 1, minWidth: 0 }}>
                        <Box
                          sx={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: 1,
                            flexWrap: 'wrap',
                            mb: 0.5,
                          }}
                        >
                          <Typography variant="body2" id={requestedId} sx={{ fontWeight: 500 }}>
                            {t('pages.tenants.export.requestedAt', {
                              date: formatDateTime(item.requested_at),
                            })}
                          </Typography>
                          <Chip
                            size="small"
                            label={t(`enums.tenantExportStatus.${item.status}`)}
                            color={STATUS_COLORS[item.status]}
                            data-testid={`tenant-export-status-${item.key}`}
                          />
                          {item.status === 'completed' && item.size_bytes !== null && (
                            <Typography variant="body2" color="text.secondary">
                              {formatSize(item.size_bytes)}
                            </Typography>
                          )}
                        </Box>
                        <Typography variant="body2" color="text.secondary">
                          {statusLine(item)}
                        </Typography>
                      </Box>
                      {downloadable && (
                        <Button
                          variant="outlined"
                          startIcon={<DownloadIcon />}
                          onClick={() => void handleDownload(item)}
                          loading={downloading === item.key}
                          disabled={downloading !== null}
                          // Every row's button reads "Download": the request time tells them apart.
                          aria-describedby={requestedId}
                          data-testid={`download-tenant-export-${item.key}`}
                          sx={{ minHeight: 44, flexShrink: 0 }}
                        >
                          {t('pages.tenants.export.download')}
                        </Button>
                      )}
                    </Box>
                  </Box>
                );
              })}
            </Box>
          </>
        )}
      </CardContent>

      <StepUpConfirmDialog
        open={dialogOpen}
        title={t('pages.tenants.export.dialogTitle')}
        description={t('pages.tenants.export.dialogDescription', { name: tenantName })}
        confirmLabel={t('pages.tenants.export.dialogConfirm')}
        confirmColor="primary"
        testIdPrefix={TENANT_EXPORT_STEP_UP_SURFACE}
        stepUpAction="tenant_export"
        stepUpTarget={tenantKey}
        onConfirm={handleConfirm}
        onCancel={() => setDialogOpen(false)}
      />
    </Card>
  );
}
