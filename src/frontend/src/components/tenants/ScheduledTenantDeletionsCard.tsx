import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Divider from '@mui/material/Divider';
import Typography from '@mui/material/Typography';
import * as tenantApi from '@/api/endpoints/tenants';
import type { TenantWithRole } from '@/api/types';
import StepUpConfirmDialog from '@/components/common/StepUpConfirmDialog';
import type { StepUpConfirmation } from '@/components/common/StepUpConfirmDialog';
import TenantStatusChip from '@/components/tenants/TenantStatusChip';
import { useStepUpResume } from '@/hooks/useStepUpReauth';
import { useAppDispatch } from '@/store/hooks';
import { loadMyTenants } from '@/store/slices/tenantSlice';
import { toCredentialStepUpBody } from '@/utils/stepUp';

/** The surface id the step-up dialog saves before a fresh sign-in at the identity provider. */
const STEP_UP_SURFACE = 'cancel-own-tenant-erasure';

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
 * bound to the tenant. Renders nothing while there is none (or the list cannot be read).
 */
export default function ScheduledTenantDeletionsCard() {
  const { t, i18n } = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const dispatch = useAppDispatch();
  const [scheduled, setScheduled] = useState<TenantWithRole[]>([]);
  // #1815 — back from the fresh sign-in: the chosen tenant does not survive the round trip, so
  // the resume context is only consumed; the pending token is picked up when the lead repeats
  // the cancellation of the same tenant within its five minutes (#1884: bound to its key).
  useStepUpResume(STEP_UP_SURFACE);
  const [toCancel, setToCancel] = useState<TenantWithRole | null>(null);

  const load = useCallback(async () => {
    try {
      const tenants = await tenantApi.listMyTenantsWithScheduledDeletion();
      setScheduled(tenants.filter(isScheduledForDeletion));
    } catch {
      // The card is an addition to the page; a failed read leaves it out instead of failing the page.
      setScheduled([]);
    }
  }, []);

  useEffect(() => {
    void load(); // eslint-disable-line react-hooks/set-state-in-effect -- async function, setState is after await
  }, [load]);

  // The requester's OWN step-up; a rejection propagates to the dialog, which shows it and stays open.
  const handleConfirmCancel = async (credentials: StepUpConfirmation) => {
    if (!toCancel) return;
    await tenantApi.cancelTenantErasure(toCancel.slug, toCredentialStepUpBody(credentials));
    setToCancel(null);
    enqueueSnackbar(t('pages.tenants.scheduledDeletionCancelled', { name: toCancel.name }), {
      variant: 'success',
    });
    void load();
    // The tenant resolves again: the switcher lists it once more.
    void dispatch(loadMyTenants());
  };

  if (scheduled.length === 0) return null;

  const formatDate = (iso: string | null | undefined): string =>
    iso ? new Date(iso).toLocaleDateString(i18n.language) : '—';

  return (
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
                    <Typography variant="subtitle1" component="h3" sx={{ overflowWrap: 'anywhere' }}>
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
    </Card>
  );
}
