import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CircularProgress from '@mui/material/CircularProgress';
import Skeleton from '@mui/material/Skeleton';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import { fetchAdminTenantDetail, updateAdminTenant } from '@/api/endpoints/adminPlatform';
import { isApiError } from '@/api/errors';
import type { AdminTenant, AdminTenantDetail, TenantStatus } from '@/api/types';
import EntitlementUsageList from '@/components/tenants/EntitlementUsageList';
import { useApiError } from '@/hooks/useApiError';
import { usePlanCatalogue } from '@/hooks/usePlanCatalogue';

interface TenantPlanCardProps {
  tenantKey: string;
  isPlatform: boolean;
  /** Lifecycle of the tenant; a tenant being erased (`deleted`) takes no new plan (REQ-056 §7.6). */
  status: TenantStatus;
  /** Called with the tenant as the API returned it after a plan was assigned. */
  onAssigned?: (tenant: AdminTenant) => void;
}

type DetailState =
  | { status: 'loading' }
  | { status: 'error'; errorStatus: number }
  | { status: 'ready'; detail: AdminTenantDetail };

/**
 * Plan and usage of one tenant on the platform admin's tenant page (REQ-056 §7.6/§7.7, §15, AK-45).
 *
 * Loads `GET /admin/platform/tenants/{key}` for the plan and every quota dimension (the lead-only
 * ones included) and offers the plan selector, which assigns with `PATCH .../tenants/{key}` and no
 * step-up (E-07). Two tenants take no plan, and the card says why instead of offering a control
 * the backend refuses with 422: the **platform tenant** always follows the instance settings (SEC-006),
 * and a tenant **being erased** can no longer be changed. A suspended tenant can be given a plan.
 */
export default function TenantPlanCard({ tenantKey, isPlatform, status, onAssigned }: TenantPlanCardProps) {
  const { t } = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const { handleError } = useApiError();
  const canAssign = !isPlatform && status !== 'deleted';
  const catalogue = usePlanCatalogue(canAssign);

  const [state, setState] = useState<DetailState>({ status: 'loading' });
  const [reloadToken, setReloadToken] = useState(0);
  const [selected, setSelected] = useState('');
  const [assigning, setAssigning] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetchAdminTenantDetail(tenantKey)
      .then((detail) => {
        if (cancelled) return;
        setState({ status: 'ready', detail });
        setSelected(detail.plan_key ?? detail.entitlements.plan.key);
      })
      .catch((err: unknown) => {
        if (!cancelled) setState({ status: 'error', errorStatus: isApiError(err) ? err.statusCode : 0 });
      });
    return () => {
      cancelled = true;
    };
  }, [tenantKey, reloadToken]);

  const retry = useCallback(() => {
    setState({ status: 'loading' });
    setReloadToken((n) => n + 1);
  }, []);

  const currentPlanKey = state.status === 'ready' ? (state.detail.plan_key ?? state.detail.entitlements.plan.key) : '';

  const handleAssign = async () => {
    if (!canAssign || !selected || selected === currentPlanKey) return;
    setAssigning(true);
    try {
      const updated = await updateAdminTenant(tenantKey, { plan_key: selected });
      const planName = catalogue.plans.find((p) => p.key === selected)?.name ?? selected;
      enqueueSnackbar(t('pages.plans.tenant.assigned', { name: planName }), { variant: 'success' });
      onAssigned?.(updated);
      // Re-read the detail: the effective limits follow the new plan from its next check.
      setReloadToken((n) => n + 1);
    } catch (err) {
      handleError(err);
    } finally {
      setAssigning(false);
    }
  };

  return (
    <Card data-testid="tenant-plan-card">
      <CardContent>
        <Typography variant="h6" component="h2" gutterBottom>
          {t('pages.plans.tenant.title')}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.plans.tenant.intro')}
        </Typography>

        {state.status === 'loading' && (
          <Box aria-busy="true" data-testid="tenant-plan-loading">
            {[0, 1, 2, 3].map((i) => (
              <Skeleton key={i} variant="rounded" height={32} sx={{ mb: 1 }} />
            ))}
          </Box>
        )}
        {state.status === 'error' && (
          <Alert
            severity="warning"
            data-testid="tenant-plan-error"
            action={
              <Button color="inherit" size="small" onClick={retry} data-testid="tenant-plan-retry">
                {t('common.retry')}
              </Button>
            }
          >
            {t('pages.plans.tenant.loadFailed')}
          </Alert>
        )}

        {state.status === 'ready' && (
          <>
            {isPlatform && (
              <Alert severity="info" sx={{ mb: 2 }} data-testid="tenant-plan-platform">
                {t('pages.plans.tenant.platformInfo')}
              </Alert>
            )}
            {!isPlatform && status === 'deleted' && (
              <Alert severity="info" sx={{ mb: 2 }} data-testid="tenant-plan-deleted">
                {t('pages.plans.tenant.deletedInfo')}
              </Alert>
            )}

            {canAssign ? (
              <Box
                sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, gap: 1.5, alignItems: { sm: 'flex-start' }, mb: 3 }}
              >
                <TextField
                  select
                  label={t('pages.plans.tenant.plan')}
                  value={catalogue.status === 'ready' ? selected : ''}
                  onChange={(e) => setSelected(e.target.value)}
                  disabled={catalogue.status !== 'ready' || assigning}
                  helperText={
                    catalogue.status === 'error'
                      ? t('pages.plans.tenant.catalogueFailed')
                      : t('pages.plans.tenant.planHelper')
                  }
                  error={catalogue.status === 'error'}
                  sx={{ flex: 1, minWidth: 0 }}
                  slotProps={{ select: { native: true } }}
                  data-testid="tenant-plan-select"
                >
                  {catalogue.status !== 'ready' && <option value="">{t('common.loading')}</option>}
                  {catalogue.plans.map((p) => (
                    <option key={p.key} value={p.key}>
                      {p.is_default ? t('pages.plans.tenant.optionDefault', { name: p.name }) : p.name}
                    </option>
                  ))}
                </TextField>
                <Button
                  variant="contained"
                  onClick={handleAssign}
                  disabled={assigning || catalogue.status !== 'ready' || !selected || selected === currentPlanKey}
                  startIcon={assigning ? <CircularProgress size={16} /> : undefined}
                  sx={{ mt: { sm: 1 }, minHeight: { xs: 48, sm: 36 }, flexShrink: 0 }}
                  data-testid="tenant-plan-assign"
                >
                  {t('pages.plans.tenant.assign')}
                </Button>
              </Box>
            ) : (
              <Typography variant="body2" sx={{ mb: 3 }} data-testid="tenant-plan-current">
                {t('pages.plans.tenant.currentPlan', { name: state.detail.entitlements.plan.name })}
              </Typography>
            )}

            <Typography variant="subtitle2" component="h3" sx={{ mb: 1.5 }}>
              {t('pages.plans.tenant.usageTitle')}
            </Typography>
            <EntitlementUsageList limits={state.detail.entitlements.limits} perspective="admin" testIdPrefix="tenant-plan-usage" />
          </>
        )}
      </CardContent>
    </Card>
  );
}
