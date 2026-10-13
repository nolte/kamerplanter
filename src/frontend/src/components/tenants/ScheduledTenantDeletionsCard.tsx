import { useCallback, useEffect, useState, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Divider from '@mui/material/Divider';
import Typography from '@mui/material/Typography';
import * as tenantApi from '@/api/endpoints/tenants';
import { isApiError } from '@/api/errors';
import type { TenantWithRole } from '@/api/types';
import StepUpConfirmDialog from '@/components/common/StepUpConfirmDialog';
import type { StepUpConfirmation } from '@/components/common/StepUpConfirmDialog';
import TenantStatusChip from '@/components/tenants/TenantStatusChip';
import { useStepUpResume } from '@/hooks/useStepUpReauth';
import { useAppDispatch } from '@/store/hooks';
import { loadMyTenants } from '@/store/slices/tenantSlice';
import { formatDate } from '@/utils/formatting';
import { toCredentialStepUpBody } from '@/utils/stepUp';

/** The surface id the step-up dialog saves before a fresh sign-in at the identity provider. */
const STEP_UP_SURFACE = 'cancel-own-tenant-erasure';

/**
 * What the card knows about the account's scheduled deletions: nothing yet (or nothing it may
 * show), a read that failed and is worth repeating, or the list itself.
 */
type LoadState =
  | { status: 'idle' }
  | { status: 'error' }
  | { status: 'data'; tenants: TenantWithRole[] };

/**
 * A refusal that means "nothing for this account here" (403 / 404): the card stays out of the
 * page. Anything else — a 5xx, a network failure — is a read that failed and is said so, because
 * a silent card would hide a garden whose deletion is due (#2166 review SCR-003).
 */
function isQuietReadFailure(error: unknown): boolean {
  return isApiError(error) && (error.statusCode === 403 || error.statusCode === 404);
}

function isScheduledForDeletion(tenant: TenantWithRole): boolean {
  return tenant.status === 'pending_deletion' || tenant.status === 'orphaned';
}

/**
 * The cancellation rule of the backend (#2123, REQ-024 AK-52): a lead holding the `management`
 * scope, and only while the deletion is `pending_deletion` — an `orphaned` organisation has nobody
 * left who could administer it and runs out its grace (#2134).
 */
function canCancel(tenant: TenantWithRole): boolean {
  return (
    tenant.status === 'pending_deletion' &&
    tenant.role === 'lead' &&
    tenant.admin_scopes.includes('management')
  );
}

/**
 * The account's gardens whose deletion is scheduled (#2166).
 *
 * Such a tenant resolves for nobody (#2105), so it is missing from the tenant switcher and no
 * tenant-scoped page can show it. This card lists them with their deletion date and offers the
 * lead with the `management` scope the cancellation — confirmed with the requester's own step-up,
 * bound to the tenant. Renders nothing while there is none (or the list is refused with 403/404);
 * a read that failed otherwise shows a short warning with a retry.
 */
export default function ScheduledTenantDeletionsCard() {
  const { t } = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const dispatch = useAppDispatch();
  const [state, setState] = useState<LoadState>({ status: 'idle' });
  // #1815 — back from the fresh sign-in: the chosen tenant does not survive the round trip, so
  // the resume context is only consumed; the pending token is picked up when the lead repeats
  // the cancellation of the same tenant within its five minutes (#1884: bound to its key).
  useStepUpResume(STEP_UP_SURFACE);
  const [toCancel, setToCancel] = useState<TenantWithRole | null>(null);

  const load = useCallback(async () => {
    try {
      const tenants = await tenantApi.listMyTenantsWithScheduledDeletion();
      setState({ status: 'data', tenants: tenants.filter(isScheduledForDeletion) });
    } catch (error) {
      // The card is an addition to the page: a failed read never fails the page, but it is not
      // hidden either — only a refusal that means "nothing here" leaves the card out.
      setState(isQuietReadFailure(error) ? { status: 'idle' } : { status: 'error' });
    }
  }, []);

  useEffect(() => {
    void load(); // eslint-disable-line react-hooks/set-state-in-effect -- async function, setState is after await
  }, [load]);

  // The requester's OWN step-up; a rejection propagates to the dialog, which shows it and stays open.
  const handleConfirmCancel = async (credentials: StepUpConfirmation) => {
    if (!toCancel) return;
    try {
      await tenantApi.cancelTenantErasure(toCancel.slug, toCredentialStepUpBody(credentials));
    } catch (error) {
      // 422 — the grace ran out (a deletion run holds it) or the garden became orphaned in the
      // meantime: the listed state is stale, so it is read again while the dialog says why.
      if (isApiError(error) && error.statusCode === 422) void load();
      throw error;
    }
    setToCancel(null);
    enqueueSnackbar(t('pages.tenants.scheduledDeletionCancelled', { name: toCancel.name }), {
      variant: 'success',
    });
    void load();
    // The tenant resolves again: the switcher lists it once more.
    void dispatch(loadMyTenants());
  };

  const dialog = (
    <StepUpConfirmDialog
      open={toCancel !== null}
      title={t('pages.tenants.cancelScheduledDeletionTitle')}
      description={t('pages.tenants.cancelScheduledDeletionDescription', { name: toCancel?.name ?? '' })}
      confirmLabel={t('pages.tenants.cancelScheduledDeletion')}
      confirmColor="primary"
      testIdPrefix={STEP_UP_SURFACE}
      stepUpAction="tenant_erasure_cancel"
      stepUpTarget={toCancel?.key}
      onConfirm={handleConfirmCancel}
      onCancel={() => setToCancel(null)}
    />
  );

  const scheduled = state.status === 'data' ? state.tenants : [];

  let content: ReactNode = null;
  if (state.status === 'error') {
    content = (
      <Alert
        severity="warning"
        sx={{ mb: 3 }}
        data-testid="scheduled-tenant-deletions-error"
        action={
          <Button
            color="inherit"
            size="small"
            onClick={() => void load()}
            data-testid="scheduled-tenant-deletions-retry"
            sx={{ minHeight: 44 }}
          >
            {t('common.retry')}
          </Button>
        }
      >
        {t('pages.tenants.scheduledDeletionsLoadFailed')}
      </Alert>
    );
  } else if (scheduled.length > 0) {
    content = (
      <Card sx={{ mb: 3 }} data-testid="scheduled-tenant-deletions">
        <CardContent>
          <Typography variant="h6" component="h2" gutterBottom>
            {t('pages.tenants.scheduledDeletionsTitle')}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {t('pages.tenants.scheduledDeletionsIntro')}
          </Typography>
          <Box component="ul" sx={{ listStyle: 'none', m: 0, p: 0 }}>
            {scheduled.map((tenant, index) => (
              <Box component="li" key={tenant.key} data-testid={`scheduled-tenant-row-${tenant.slug}`}>
                {index > 0 && <Divider sx={{ my: 2 }} />}
                <Box
                  sx={{
                    display: 'flex',
                    flexDirection: { xs: 'column', sm: 'row' },
                    alignItems: { xs: 'stretch', sm: 'center' },
                    gap: 1.5,
                  }}
                >
                  <Box sx={{ flex: 1, minWidth: 0 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap', mb: 0.5 }}>
                      <Typography
                        variant="subtitle1"
                        component="h3"
                        id={`scheduled-tenant-name-${tenant.slug}`}
                        sx={{ overflowWrap: 'anywhere' }}
                      >
                        {tenant.name}
                      </Typography>
                      <TenantStatusChip
                        status={tenant.status}
                        isActive={tenant.is_active ?? false}
                        testId={`scheduled-tenant-status-${tenant.slug}`}
                      />
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      {t(
                        tenant.status === 'orphaned'
                          ? 'pages.tenants.scheduledDeletionOrphanedInfo'
                          : 'pages.tenants.scheduledDeletionPendingInfo',
                        { date: formatDate(tenant.deletion_scheduled_at) },
                      )}
                    </Typography>
                    {tenant.status === 'pending_deletion' && !canCancel(tenant) && (
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                        {t('pages.tenants.scheduledDeletionManagementOnly')}
                      </Typography>
                    )}
                  </Box>
                  {canCancel(tenant) && (
                    <Button
                      variant="outlined"
                      onClick={() => setToCancel(tenant)}
                      // Every row's button reads "Cancel deletion": the garden's name tells them apart.
                      aria-describedby={`scheduled-tenant-name-${tenant.slug}`}
                      data-testid={`cancel-tenant-erasure-${tenant.slug}`}
                      sx={{ flexShrink: 0, minHeight: 44 }}
                    >
                      {t('pages.tenants.cancelScheduledDeletion')}
                    </Button>
                  )}
                </Box>
              </Box>
            ))}
          </Box>
        </CardContent>
      </Card>
    );
  }

  // The dialog keeps its place beside the content: a reload that empties the list or fails while
  // it is open (e.g. after a 422) must not unmount it and tear its explanation away.
  return (
    <>
      {content}
      {dialog}
    </>
  );
}
