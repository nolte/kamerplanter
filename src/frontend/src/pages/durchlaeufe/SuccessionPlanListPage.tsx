import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import type { ChipProps } from '@mui/material/Chip';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import Alert from '@mui/material/Alert';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import PlaylistAddIcon from '@mui/icons-material/PlaylistAdd';
import MobileCard from '@/components/common/MobileCard';
import PageTitle from '@/components/layout/PageTitle';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import DataTable, { type Column } from '@/components/common/DataTable';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchSuccessionPlans } from '@/store/slices/successionPlansSlice';
import { useTableUrlState } from '@/hooks/useTableState';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as successionApi from '@/api/endpoints/successionPlans';
import * as speciesApi from '@/api/endpoints/species';
import type {
  GenerateRunsResponse,
  Species,
  SuccessionPlan,
  SuccessionPlanStatus,
} from '@/api/types';
import SuccessionPlanDialog from './SuccessionPlanDialog';
import { kamiPlantingRuns } from '@/assets/brand/illustrations';

const statusColor: Record<SuccessionPlanStatus, ChipProps['color']> = {
  planned: 'default',
  active: 'primary',
  completed: 'success',
  cancelled: 'error',
};

function formatDate(value: string | null): string {
  if (!value) return '—';
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? value : d.toLocaleDateString();
}

export default function SuccessionPlanListPage() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const notification = useNotification();
  const { handleError } = useApiError();
  const { plans, loading } = useAppSelector((s) => s.successionPlans);
  const tableState = useTableUrlState({ defaultSort: { column: 'name', direction: 'asc' } });

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editPlan, setEditPlan] = useState<SuccessionPlan | null>(null);
  const [deleteKey, setDeleteKey] = useState<string | null>(null);
  const [generating, setGenerating] = useState<string | null>(null);
  const [generatedResult, setGeneratedResult] = useState<GenerateRunsResponse | null>(null);
  const [speciesList, setSpeciesList] = useState<Species[]>([]);

  useEffect(() => {
    dispatch(fetchSuccessionPlans({}));
    speciesApi
      .listSpecies(0, 200)
      .then((r) => setSpeciesList(r.items))
      .catch(() => {});
  }, [dispatch]);

  const speciesNameByKey = useMemo(() => {
    const map = new Map<string, string>();
    for (const sp of speciesList) {
      map.set(sp.key, sp.common_names?.[0] ?? sp.scientific_name);
    }
    return map;
  }, [speciesList]);

  const reload = () => {
    dispatch(fetchSuccessionPlans({}));
  };

  const handleCreate = () => {
    setEditPlan(null);
    setDialogOpen(true);
  };

  const handleEdit = (plan: SuccessionPlan) => {
    setEditPlan(plan);
    setDialogOpen(true);
  };

  const handleGenerate = async (plan: SuccessionPlan) => {
    try {
      setGenerating(plan.key);
      const result = await successionApi.generateRuns(plan.key);
      setGeneratedResult(result);
      notification.success(
        t('pages.successionPlans.runsGenerated', { count: result.generated_count }),
      );
      reload();
    } catch (err) {
      handleError(err);
    } finally {
      setGenerating(null);
    }
  };

  const deleteTarget = plans.find((p) => p.key === deleteKey);

  const handleDelete = async () => {
    if (!deleteKey) return;
    try {
      await successionApi.deleteSuccessionPlan(deleteKey);
      notification.success(t('pages.successionPlans.planDeleted'));
      setDeleteKey(null);
      reload();
    } catch (err) {
      handleError(err);
    }
  };

  const speciesLabel = (plan: SuccessionPlan): string =>
    speciesNameByKey.get(plan.species_key) ?? plan.species_key;

  const batchProgress = (plan: SuccessionPlan): string =>
    `${plan.completed_batches} / ${plan.total_batches}`;

  const columns: Column<SuccessionPlan>[] = [
    { id: 'name', label: t('pages.successionPlans.name'), render: (p) => p.name },
    {
      id: 'species',
      label: t('entities.species'),
      render: (p) => speciesLabel(p),
      searchValue: (p) => speciesLabel(p),
    },
    {
      id: 'interval',
      label: t('pages.successionPlans.intervalDays'),
      render: (p) => t('pages.successionPlans.everyNDays', { count: p.interval_days }),
      searchValue: (p) => String(p.interval_days),
      align: 'right',
      hideBelowBreakpoint: 'md',
    },
    {
      id: 'batches',
      label: t('pages.successionPlans.batches'),
      render: (p) => batchProgress(p),
      searchValue: (p) => batchProgress(p),
      align: 'right',
    },
    {
      id: 'status',
      label: t('pages.successionPlans.status'),
      render: (p) => (
        <Chip
          label={t(`enums.successionPlanStatus.${p.status}`)}
          size="small"
          color={statusColor[p.status] ?? 'default'}
          data-testid={`status-chip-${p.key}`}
        />
      ),
      searchValue: (p) => t(`enums.successionPlanStatus.${p.status}`),
    },
    {
      id: 'window',
      label: t('pages.successionPlans.window'),
      render: (p) => `${formatDate(p.start_date)} – ${formatDate(p.end_date)}`,
      hideBelowBreakpoint: 'lg',
    },
    {
      id: 'actions',
      label: t('common.actions'),
      align: 'right',
      sortable: false,
      searchable: false,
      render: (p) => (
        <Box onClick={(e) => e.stopPropagation()} sx={{ whiteSpace: 'nowrap' }}>
          <Tooltip title={t('pages.successionPlans.generateRuns')}>
            <span>
              <IconButton
                size="small"
                color="primary"
                onClick={() => handleGenerate(p)}
                disabled={generating === p.key}
                aria-label={t('pages.successionPlans.generateRuns')}
                data-testid={`generate-runs-${p.key}`}
              >
                <PlaylistAddIcon fontSize="small" />
              </IconButton>
            </span>
          </Tooltip>
          <Tooltip title={t('common.edit')}>
            <IconButton
              size="small"
              onClick={() => handleEdit(p)}
              aria-label={t('common.edit')}
              data-testid={`edit-plan-${p.key}`}
            >
              <EditIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title={t('common.delete')}>
            <IconButton
              size="small"
              color="error"
              onClick={() => setDeleteKey(p.key)}
              aria-label={t('common.delete')}
              data-testid={`delete-plan-${p.key}`}
            >
              <DeleteIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
      ),
    },
  ];

  return (
    <Box data-testid="succession-plan-list-page">
      <PageTitle
        title={t('pages.successionPlans.title')}
        action={
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreate}
            data-testid="create-button"
          >
            {t('pages.successionPlans.create')}
          </Button>
        }
      />
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('pages.successionPlans.listIntro')}
      </Typography>
      <DataTable
        columns={columns}
        rows={plans}
        loading={loading}
        getRowKey={(p) => p.key}
        emptyActionLabel={t('pages.successionPlans.create')}
        onEmptyAction={handleCreate}
        emptyMessage={t('pages.successionPlans.empty')}
        emptyIllustration={kamiPlantingRuns}
        tableState={tableState}
        ariaLabel={t('pages.successionPlans.title')}
        mobileCardRenderer={(p) => (
          <Box>
            <MobileCard
              title={p.name}
              subtitle={speciesLabel(p)}
              chips={
                <>
                  <Chip
                    label={t(`enums.successionPlanStatus.${p.status}`)}
                    size="small"
                    color={statusColor[p.status] ?? 'default'}
                  />
                  <Chip
                    label={t('pages.successionPlans.everyNDays', { count: p.interval_days })}
                    size="small"
                    variant="outlined"
                  />
                </>
              }
              fields={[
                { label: t('pages.successionPlans.batches'), value: batchProgress(p) },
                { label: t('pages.successionPlans.plantsPerBatch'), value: String(p.plants_per_batch) },
                {
                  label: t('pages.successionPlans.window'),
                  value: `${formatDate(p.start_date)} – ${formatDate(p.end_date)}`,
                },
              ]}
            />
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 0.5, mb: 1 }}>
              <Button
                size="small"
                startIcon={<PlaylistAddIcon />}
                onClick={() => handleGenerate(p)}
                disabled={generating === p.key}
                data-testid={`generate-runs-mobile-${p.key}`}
              >
                {t('pages.successionPlans.generateRuns')}
              </Button>
              <Button size="small" startIcon={<EditIcon />} onClick={() => handleEdit(p)}>
                {t('common.edit')}
              </Button>
              <Button
                size="small"
                color="error"
                startIcon={<DeleteIcon />}
                onClick={() => setDeleteKey(p.key)}
              >
                {t('common.delete')}
              </Button>
            </Box>
          </Box>
        )}
      />

      <SuccessionPlanDialog
        open={dialogOpen}
        plan={editPlan}
        onClose={() => setDialogOpen(false)}
        onSaved={() => {
          setDialogOpen(false);
          reload();
        }}
      />

      <ConfirmDialog
        open={!!deleteKey}
        title={t('pages.successionPlans.deleteTitle')}
        message={t('pages.successionPlans.deleteConfirm', { name: deleteTarget?.name ?? '' })}
        onConfirm={handleDelete}
        onCancel={() => setDeleteKey(null)}
        destructive
      />

      <Dialog
        open={!!generatedResult}
        onClose={() => setGeneratedResult(null)}
        maxWidth="sm"
        fullWidth
        aria-labelledby="generated-runs-dialog-title"
        data-testid="generated-runs-dialog"
      >
        <DialogTitle id="generated-runs-dialog-title">
          {t('pages.successionPlans.generatedRunsTitle')}
        </DialogTitle>
        <DialogContent>
          <Alert severity="success" sx={{ mb: 2 }}>
            {t('pages.successionPlans.runsGenerated', {
              count: generatedResult?.generated_count ?? 0,
            })}
          </Alert>
          {generatedResult && generatedResult.runs.length > 0 ? (
            <List dense data-testid="generated-runs-list">
              {generatedResult.runs.map((run) => (
                <ListItem key={run.run_key} divider disableGutters>
                  <ListItemText
                    primary={
                      run.succession_sequence != null && run.succession_total != null
                        ? t('pages.successionPlans.runSequenceLabel', {
                            name: run.name,
                            index: run.succession_sequence,
                            total: run.succession_total,
                          })
                        : run.name
                    }
                    secondary={
                      run.planned_start_date
                        ? t('pages.successionPlans.plannedStartLabel', {
                            date: formatDate(run.planned_start_date),
                          })
                        : undefined
                    }
                  />
                </ListItem>
              ))}
            </List>
          ) : (
            <Typography variant="body2" color="text.secondary">
              {t('pages.successionPlans.noRunsGenerated')}
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setGeneratedResult(null)} data-testid="generated-runs-close">
            {t('common.close')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
