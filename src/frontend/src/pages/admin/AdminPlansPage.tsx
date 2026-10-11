import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { useSnackbar } from 'notistack';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import AddIcon from '@mui/icons-material/Add';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import StarIcon from '@mui/icons-material/Star';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import DataTable, { type Column } from '@/components/common/DataTable';
import MobileCard from '@/components/common/MobileCard';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import PlanFormDialog from '@/components/admin/PlanFormDialog';
import { deletePlan } from '@/api/endpoints/adminPlans';
import { isApiError } from '@/api/errors';
import type { EntitlementDimension, Plan } from '@/api/types';
import { useApiError } from '@/hooks/useApiError';
import { usePlanCatalogue } from '@/hooks/usePlanCatalogue';
import ErrorPage from '@/pages/ErrorPage';
import { formatPlanLimit } from '@/utils/entitlements';

/** The columns shown in the table; the AI budgets are summarised to keep it readable on a laptop. */
const TABLE_DIMENSIONS: readonly EntitlementDimension[] = ['members', 'storage_mb', 'ai_calls_per_tenant_day'];

/** Why a plan cannot be deleted right now, or `null` when it can (REQ-056 §7.6: 409 otherwise). */
function deleteBlocker(plan: Plan): 'default' | 'inUse' | null {
  if (plan.is_default) return 'default';
  if (plan.tenant_count > 0) return 'inUse';
  return null;
}

/**
 * Admin › Plans — the installation's plan catalogue (REQ-056 §7.6, §15, AK-45).
 *
 * Reached from the platform tab of the settings page and guarded by `<RequirePlatformAdmin>`: every
 * request here is `require_platform_admin`, the list included. Full mode only — in light mode the
 * plan routes are not mounted (REQ-056 §7.8) and neither is this page.
 *
 * A plan's limits are shown as the plan stores them: an empty value follows the instance setting,
 * `0` lifts the limit (unlimited / budget off). The default plan and a plan tenants are assigned to
 * cannot be deleted — the delete action says why instead of offering a request that would fail.
 * None of these actions needs a step-up (REQ-056 §7.6, E-07); each writes a security-audit row.
 */
export default function AdminPlansPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const { handleError } = useApiError();
  const { plans, status, errorStatus, reload } = usePlanCatalogue();

  // `undefined` = form closed, `null` = create, a plan = edit.
  const [formTarget, setFormTarget] = useState<Plan | null | undefined>(undefined);
  const [toDelete, setToDelete] = useState<Plan | null>(null);
  const [deleting, setDeleting] = useState(false);

  const handleSaved = (saved: Plan) => {
    const created = formTarget === null;
    setFormTarget(undefined);
    reload();
    enqueueSnackbar(
      created ? t('pages.plans.snack.created', { name: saved.name }) : t('pages.plans.snack.saved', { name: saved.name }),
      { variant: 'success' },
    );
  };

  const handleConfirmDelete = async () => {
    if (!toDelete) return;
    setDeleting(true);
    try {
      await deletePlan(toDelete.key);
      enqueueSnackbar(t('pages.plans.snack.deleted', { name: toDelete.name }), { variant: 'success' });
      setToDelete(null);
      reload();
    } catch (err) {
      // 409: a tenant was assigned (or the default moved here) since the list was read.
      if (isApiError(err) && err.statusCode === 409) {
        enqueueSnackbar(t('pages.plans.delete.conflict'), { variant: 'error' });
        setToDelete(null);
        reload();
      } else {
        handleError(err);
      }
    } finally {
      setDeleting(false);
    }
  };

  const columns = useMemo<Column<Plan>[]>(
    () => [
      {
        id: 'name',
        label: t('pages.plans.list.name'),
        render: (p) => (
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                {p.name}
              </Typography>
              {p.is_default && (
                <Chip
                  icon={<StarIcon />}
                  label={t('pages.plans.list.default')}
                  size="small"
                  color="primary"
                  variant="outlined"
                  data-testid={`plan-default-${p.key}`}
                />
              )}
            </Box>
            <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
              {p.key}
            </Typography>
          </Box>
        ),
        searchValue: (p) => `${p.name} ${p.key}`,
        sortFn: (a, b) => a.name.localeCompare(b.name),
      },
      ...TABLE_DIMENSIONS.map<Column<Plan>>((d) => ({
        id: d,
        label: t(`enums.entitlementDimension.${d}`),
        render: (p) => (
          <Typography
            variant="body2"
            color={p.limits[d] == null ? 'text.secondary' : 'text.primary'}
            data-testid={`plan-limit-${p.key}-${d}`}
          >
            {formatPlanLimit(d, p.limits[d], t)}
          </Typography>
        ),
        hideBelowBreakpoint: d === 'members' ? undefined : 'md',
        sortable: false,
      })),
      {
        id: 'tenant_count',
        label: t('pages.plans.list.tenants'),
        align: 'right',
        render: (p) => <span data-testid={`plan-tenants-${p.key}`}>{p.tenant_count}</span>,
        sortFn: (a, b) => a.tenant_count - b.tenant_count,
      },
      {
        id: 'actions',
        label: t('pages.plans.list.actions'),
        align: 'right',
        sortable: false,
        searchable: false,
        render: (p) => <PlanRowActions plan={p} onEdit={() => setFormTarget(p)} onDelete={() => setToDelete(p)} />,
      },
    ],
    [t],
  );

  if (status === 'loading') return <LoadingSkeleton variant="table" />;
  if (status === 'error') {
    return <ErrorPage statusCode={errorStatus === 0 || errorStatus === null ? 503 : errorStatus} onRetry={reload} landmark={false} />;
  }

  const addButton = (
    <Button variant="contained" startIcon={<AddIcon />} onClick={() => setFormTarget(null)} data-testid="plan-add">
      {t('pages.plans.add')}
    </Button>
  );

  return (
    <Box sx={{ mt: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
        <IconButton onClick={() => navigate('/settings#platform')} aria-label={t('pages.plans.back')} data-testid="plans-back">
          <ArrowBackIcon />
        </IconButton>
        <Box sx={{ flex: 1 }}>
          <PageTitle title={t('pages.plans.title')} action={addButton} sx={{ mb: 0 }} />
        </Box>
      </Box>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
        {t('pages.plans.intro')}
      </Typography>
      <Alert severity="info" sx={{ mb: 3 }} data-testid="plans-value-legend">
        {t('pages.plans.valueLegend')}
      </Alert>

      <DataTable
        columns={columns}
        rows={[...plans]}
        getRowKey={(p) => p.key}
        variant="simple"
        ariaLabel={t('pages.plans.title')}
        emptyMessage={t('pages.plans.emptyTitle')}
        emptyDescription={t('pages.plans.emptyDescription')}
        emptyActionLabel={t('pages.plans.add')}
        onEmptyAction={() => setFormTarget(null)}
        sectionTestId="plans-table"
        mobileCardRenderer={(p) => (
          <MobileCard
            title={p.name}
            titleId="name"
            subtitle={p.key}
            subtitleId="key"
            chips={[
              ...(p.is_default
                ? [
                    {
                      id: 'default',
                      content: <Chip icon={<StarIcon />} label={t('pages.plans.list.default')} size="small" color="primary" variant="outlined" />,
                    },
                  ]
                : []),
              {
                id: 'tenants',
                content: <Chip label={t('pages.plans.list.tenantsChip', { count: p.tenant_count })} size="small" />,
              },
            ]}
            fields={TABLE_DIMENSIONS.map((d) => ({
              id: d,
              label: t(`enums.entitlementDimension.${d}`),
              value: formatPlanLimit(d, p.limits[d], t),
            }))}
            trailing={<PlanRowActions plan={p} onEdit={() => setFormTarget(p)} onDelete={() => setToDelete(p)} />}
          />
        )}
      />

      {formTarget !== undefined && (
        <PlanFormDialog open plan={formTarget} onClose={() => setFormTarget(undefined)} onSaved={handleSaved} />
      )}

      <ConfirmDialog
        open={toDelete !== null}
        title={t('pages.plans.delete.title')}
        message={t('pages.plans.delete.message', { name: toDelete?.name ?? '', key: toDelete?.key ?? '' })}
        confirmLabel={t('pages.plans.delete.confirm')}
        destructive
        loading={deleting}
        onConfirm={handleConfirmDelete}
        onCancel={() => setToDelete(null)}
      />
    </Box>
  );
}

interface PlanRowActionsProps {
  plan: Plan;
  onEdit: () => void;
  onDelete: () => void;
}

/**
 * Edit and delete of one plan. Delete is disabled with its reason while the plan is the default or in
 * use; the wrapper `span` keeps the tooltip reachable on a disabled button (MUI requirement).
 */
function PlanRowActions({ plan, onEdit, onDelete }: PlanRowActionsProps) {
  const { t } = useTranslation();
  const blocker = deleteBlocker(plan);
  const deleteLabel = t('pages.plans.actions.delete', { name: plan.name });
  const blockedReason =
    blocker === 'default'
      ? t('pages.plans.delete.blockedDefault')
      : blocker === 'inUse'
        ? t('pages.plans.delete.blockedInUse', { count: plan.tenant_count })
        : null;

  return (
    <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 0.5 }}>
      <IconButton
        onClick={onEdit}
        aria-label={t('pages.plans.actions.edit', { name: plan.name })}
        data-testid={`plan-edit-${plan.key}`}
      >
        <EditIcon />
      </IconButton>
      <Tooltip title={blockedReason ?? deleteLabel}>
        <span>
          <IconButton
            color="error"
            onClick={onDelete}
            disabled={blocker !== null}
            aria-label={blockedReason ? `${deleteLabel} – ${blockedReason}` : deleteLabel}
            data-testid={`plan-delete-${plan.key}`}
          >
            <DeleteIcon />
          </IconButton>
        </span>
      </Tooltip>
    </Box>
  );
}
