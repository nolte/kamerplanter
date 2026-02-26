import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import type { ChipProps } from '@mui/material/Chip';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import DeleteIcon from '@mui/icons-material/Delete';
import RemoveCircleIcon from '@mui/icons-material/RemoveCircle';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import FormTextField from '@/components/form/FormTextField';
import FormDateField from '@/components/form/FormDateField';
import FormActions from '@/components/form/FormActions';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as runApi from '@/api/endpoints/plantingRuns';
import type {
  PlantingRun,
  PlantingRunEntry,
  PlantInRun,
  PlantingRunStatus,
} from '@/api/types';

const statusColor: Record<PlantingRunStatus, ChipProps['color']> = {
  planned: 'default',
  active: 'primary',
  harvesting: 'warning',
  completed: 'success',
  cancelled: 'error',
};

const editSchema = z.object({
  name: z.string().min(1).max(200),
  notes: z.string().nullable(),
  planned_start_date: z.string().nullable(),
});

type EditFormData = z.infer<typeof editSchema>;

export default function PlantingRunDetailPage() {
  const { key } = useParams<{ key: string }>();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [run, setRun] = useState<PlantingRun | null>(null);
  const [entries, setEntries] = useState<PlantingRunEntry[]>([]);
  const [plants, setPlants] = useState<PlantInRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState(0);
  const [saving, setSaving] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [createPlantsOpen, setCreatePlantsOpen] = useState(false);
  const [batchRemoveOpen, setBatchRemoveOpen] = useState(false);

  const {
    control,
    handleSubmit,
    reset,
    formState: { isDirty },
  } = useForm<EditFormData>({
    resolver: zodResolver(editSchema),
    defaultValues: { name: '', notes: null, planned_start_date: null },
  });

  const load = async () => {
    if (!key) return;
    setLoading(true);
    try {
      const r = await runApi.getPlantingRun(key);
      setRun(r);
      reset({
        name: r.name,
        notes: r.notes,
        planned_start_date: r.planned_start_date,
      });
      const e = await runApi.listEntries(key);
      setEntries(e);
      try {
        const p = await runApi.listRunPlants(key, true);
        setPlants(p);
      } catch {
        // Plants may not exist yet
      }
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [key]); // eslint-disable-line react-hooks/exhaustive-deps

  const onEditSubmit = async (data: EditFormData) => {
    if (!key) return;
    try {
      setSaving(true);
      const updated = await runApi.updatePlantingRun(key, {
        name: data.name,
        notes: data.notes,
        planned_start_date: data.planned_start_date,
      });
      setRun(updated);
      notification.success(t('common.save'));
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  const onDelete = async () => {
    if (!key) return;
    try {
      await runApi.deletePlantingRun(key);
      notification.success(t('common.delete'));
      navigate('/durchlaeufe/planting-runs');
    } catch (err) {
      handleError(err);
    }
    setDeleteOpen(false);
  };

  const onCreatePlants = async () => {
    if (!key) return;
    try {
      const result = await runApi.batchCreatePlants(key);
      notification.success(
        t('pages.plantingRuns.plantsCreated', { count: result.created_count }),
      );
      load();
    } catch (err) {
      handleError(err);
    }
    setCreatePlantsOpen(false);
  };

  const onBatchRemove = async () => {
    if (!key) return;
    try {
      const result = await runApi.batchRemove(key);
      notification.success(
        t('pages.plantingRuns.plantsRemoved', { count: result.removed_count }),
      );
      load();
    } catch (err) {
      handleError(err);
    }
    setBatchRemoveOpen(false);
  };

  const onDetach = async (plantKey: string) => {
    if (!key) return;
    try {
      await runApi.detachPlant(key, plantKey, 'manual_detach');
      notification.success(t('pages.plantingRuns.plantDetached'));
      load();
    } catch (err) {
      handleError(err);
    }
  };

  if (loading) return <LoadingSkeleton variant="form" />;
  if (error) return <ErrorDisplay error={error} onRetry={() => navigate(-1)} />;

  return (
    <Box data-testid="planting-run-detail-page">
      <UnsavedChangesGuard dirty={isDirty} />
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <PageTitle title={run?.name ?? t('entities.plantingRun')} />
          {run && (
            <Chip
              label={t(`enums.plantingRunStatus.${run.status}`)}
              color={statusColor[run.status] ?? 'default'}
              data-testid="status-chip"
            />
          )}
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          {run?.status === 'planned' && (
            <>
              <Button
                variant="contained"
                startIcon={<PlayArrowIcon />}
                onClick={() => setCreatePlantsOpen(true)}
                data-testid="create-plants-button"
              >
                {t('pages.plantingRuns.createPlants')}
              </Button>
              <Button
                color="error"
                startIcon={<DeleteIcon />}
                onClick={() => setDeleteOpen(true)}
                data-testid="delete-button"
              >
                {t('common.delete')}
              </Button>
            </>
          )}
          {(run?.status === 'active' || run?.status === 'harvesting') && (
            <Button
              color="error"
              startIcon={<RemoveCircleIcon />}
              onClick={() => setBatchRemoveOpen(true)}
              data-testid="batch-remove-button"
            >
              {t('pages.plantingRuns.batchRemove')}
            </Button>
          )}
        </Box>
      </Box>

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 3 }}>
        <Tab label={t('pages.plantingRuns.tabDetails')} />
        <Tab label={t('pages.plantingRuns.tabPlants')} />
        <Tab label={t('common.edit')} />
      </Tabs>

      {tab === 0 && (
        <>
          {run && (
            <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap', mb: 4 }}>
              <Card sx={{ minWidth: 250 }}>
                <CardContent>
                  <Typography variant="subtitle2" color="text.secondary">
                    {t('pages.plantingRuns.runType')}
                  </Typography>
                  <Typography>{t(`enums.plantingRunType.${run.run_type}`)}</Typography>
                  <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 1 }}>
                    {t('pages.plantingRuns.plannedQuantity')}
                  </Typography>
                  <Typography>{run.planned_quantity}</Typography>
                  <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 1 }}>
                    {t('pages.plantingRuns.actualQuantity')}
                  </Typography>
                  <Typography>{run.actual_quantity}</Typography>
                  {run.planned_start_date && (
                    <>
                      <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 1 }}>
                        {t('pages.plantingRuns.plannedStartDate')}
                      </Typography>
                      <Typography>{run.planned_start_date}</Typography>
                    </>
                  )}
                  {run.started_at && (
                    <>
                      <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 1 }}>
                        {t('pages.plantingRuns.startedAt')}
                      </Typography>
                      <Typography>{new Date(run.started_at).toLocaleString()}</Typography>
                    </>
                  )}
                  {run.notes && (
                    <>
                      <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 1 }}>
                        {t('pages.plantingRuns.notes')}
                      </Typography>
                      <Typography>{run.notes}</Typography>
                    </>
                  )}
                </CardContent>
              </Card>
            </Box>
          )}

          {entries.length > 0 && (
            <Box>
              <Typography variant="h6" sx={{ mb: 2 }}>
                {t('pages.plantingRuns.entries')}
              </Typography>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>{t('entities.species')}</TableCell>
                    <TableCell>{t('pages.plantingRuns.quantity')}</TableCell>
                    <TableCell>{t('pages.plantingRuns.role')}</TableCell>
                    <TableCell>{t('pages.plantingRuns.idPrefix')}</TableCell>
                    <TableCell>{t('pages.plantingRuns.spacing')}</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {entries.map((e) => (
                    <TableRow key={e.key}>
                      <TableCell>{e.species_key}</TableCell>
                      <TableCell>{e.quantity}</TableCell>
                      <TableCell>{t(`enums.entryRole.${e.role}`)}</TableCell>
                      <TableCell>{e.id_prefix}</TableCell>
                      <TableCell>{e.spacing_cm ? `${e.spacing_cm} cm` : '-'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Box>
          )}
        </>
      )}

      {tab === 1 && (
        <Box>
          <Typography variant="h6" sx={{ mb: 2 }}>
            {t('pages.plantingRuns.tabPlants')} ({plants.length})
          </Typography>
          {plants.length === 0 ? (
            <Typography color="text.secondary">{t('pages.plantingRuns.noPlantsYet')}</Typography>
          ) : (
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>{t('pages.plantInstances.instanceId')}</TableCell>
                  <TableCell>{t('pages.plantInstances.currentPhase')}</TableCell>
                  <TableCell>{t('pages.plantInstances.plantedOn')}</TableCell>
                  <TableCell>{t('pages.plantInstances.removedOn')}</TableCell>
                  <TableCell>{t('pages.plantingRuns.detached')}</TableCell>
                  <TableCell />
                </TableRow>
              </TableHead>
              <TableBody>
                {plants.map((p) => (
                  <TableRow key={p.key}>
                    <TableCell>{p.instance_id}</TableCell>
                    <TableCell>
                      <Chip label={p.current_phase} size="small" color="primary" />
                    </TableCell>
                    <TableCell>{p.planted_on}</TableCell>
                    <TableCell>{p.removed_on ?? '-'}</TableCell>
                    <TableCell>{p.detached_at ? t('common.yes') : '-'}</TableCell>
                    <TableCell>
                      {!p.detached_at && run?.status === 'active' && (
                        <Button size="small" onClick={() => onDetach(p.key)}>
                          {t('pages.plantingRuns.detach')}
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </Box>
      )}

      {tab === 2 && (
        <Box component="form" onSubmit={handleSubmit(onEditSubmit)} sx={{ maxWidth: 600 }}>
          <FormTextField name="name" control={control} label={t('pages.plantingRuns.name')} required />
          <FormDateField
            name="planned_start_date"
            control={control}
            label={t('pages.plantingRuns.plannedStartDate')}
          />
          <FormTextField name="notes" control={control} label={t('pages.plantingRuns.notes')} />
          <FormActions onCancel={() => setTab(0)} loading={saving} />
        </Box>
      )}

      <ConfirmDialog
        open={deleteOpen}
        title={t('common.delete')}
        message={t('common.deleteConfirm', { name: run?.name })}
        onConfirm={onDelete}
        onCancel={() => setDeleteOpen(false)}
        destructive
      />

      <ConfirmDialog
        open={createPlantsOpen}
        title={t('pages.plantingRuns.createPlants')}
        message={t('pages.plantingRuns.createPlantsConfirm', {
          count: run?.planned_quantity ?? 0,
        })}
        onConfirm={onCreatePlants}
        onCancel={() => setCreatePlantsOpen(false)}
      />

      <ConfirmDialog
        open={batchRemoveOpen}
        title={t('pages.plantingRuns.batchRemove')}
        message={t('pages.plantingRuns.batchRemoveConfirm')}
        onConfirm={onBatchRemove}
        onCancel={() => setBatchRemoveOpen(false)}
        destructive
      />
    </Box>
  );
}
