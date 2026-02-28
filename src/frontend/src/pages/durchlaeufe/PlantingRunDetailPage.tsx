import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import type { ChipProps } from '@mui/material/Chip';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Alert from '@mui/material/Alert';
import CircularProgress from '@mui/material/CircularProgress';
import MenuItem from '@mui/material/MenuItem';
import TextField from '@mui/material/TextField';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import DeleteIcon from '@mui/icons-material/Delete';
import RemoveCircleIcon from '@mui/icons-material/RemoveCircle';
import SwapHorizIcon from '@mui/icons-material/SwapHoriz';
import WaterDropIcon from '@mui/icons-material/WaterDrop';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import DataTable, { type Column } from '@/components/common/DataTable';
import FormTextField from '@/components/form/FormTextField';
import FormDateField from '@/components/form/FormDateField';
import FormActions from '@/components/form/FormActions';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import BatchPhaseTransitionDialog from './BatchPhaseTransitionDialog';
import PhaseTimelineStepper from './PhaseTimelineStepper';
import PhaseHistoryTable from './PhaseHistoryTable';
import WateringConfirmDialog from './WateringConfirmDialog';
import WateringCalendarView from './WateringCalendarView';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as runApi from '@/api/endpoints/plantingRuns';
import * as planApi from '@/api/endpoints/nutrient-plans';
import { quickConfirmWatering } from '@/api/endpoints/wateringConfirm';
import type {
  NutrientPlan,
  PlantingRun,
  PlantingRunEntry,
  PlantInRun,
  PlantingRunStatus,
  WateringScheduleCalendarResponse,
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
  const [batchTransitionOpen, setBatchTransitionOpen] = useState(false);
  const [selectedPlantKey, setSelectedPlantKey] = useState('');

  // Watering tab state
  const [nutrientPlans, setNutrientPlans] = useState<NutrientPlan[]>([]);
  const [assignedPlan, setAssignedPlan] = useState<Record<string, unknown> | null>(null);
  const [selectedPlanKey, setSelectedPlanKey] = useState('');
  const [assigning, setAssigning] = useState(false);
  const [wateringCalendar, setWateringCalendar] = useState<WateringScheduleCalendarResponse | null>(null);
  const [wateringLoading, setWateringLoading] = useState(false);
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);
  const [confirmDate, setConfirmDate] = useState('');
  const [confirmChannelId, setConfirmChannelId] = useState<string | undefined>(undefined);
  const [quickConfirming, setQuickConfirming] = useState<string | null>(null);
  const [removePlanOpen, setRemovePlanOpen] = useState(false);

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

  const loadWateringData = useCallback(async () => {
    if (!key) return;
    setWateringLoading(true);
    try {
      const [plans, planResult, calendar] = await Promise.all([
        planApi.fetchNutrientPlans(0, 200),
        runApi.getRunNutrientPlan(key).catch(() => ({ plan: null })),
        runApi.getWateringSchedule(key, 14).catch(() => null),
      ]);
      setNutrientPlans(plans);
      setAssignedPlan(planResult.plan);
      setWateringCalendar(calendar);
      if (planResult.plan) {
        setSelectedPlanKey((planResult.plan as { key?: string }).key ?? '');
      }
    } catch (err) {
      handleError(err);
    } finally {
      setWateringLoading(false);
    }
  }, [key, handleError]);

  useEffect(() => {
    if (tab === 3) {
      loadWateringData();
    }
  }, [tab, loadWateringData]);

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

  const onAssignPlan = async () => {
    if (!key || !selectedPlanKey) return;
    try {
      setAssigning(true);
      await runApi.assignNutrientPlan(key, selectedPlanKey);
      notification.success(t('pages.wateringSchedule.assignPlan'));
      loadWateringData();
    } catch (err) {
      handleError(err);
    } finally {
      setAssigning(false);
    }
  };

  const onRemovePlan = async () => {
    if (!key) return;
    try {
      await runApi.removeRunNutrientPlan(key);
      notification.success(t('pages.wateringSchedule.removePlan'));
      setAssignedPlan(null);
      setSelectedPlanKey('');
      setWateringCalendar(null);
      loadWateringData();
    } catch (err) {
      handleError(err);
    }
    setRemovePlanOpen(false);
  };

  const onQuickConfirm = async (date: string, channelId?: string, stateKey?: string) => {
    if (!key) return;
    const confirmKey = stateKey ?? date;
    try {
      setQuickConfirming(confirmKey);
      const result = await quickConfirmWatering({
        run_key: key,
        task_key: date,
        channel_id: channelId,
      });
      notification.success(
        t('pages.wateringSchedule.feedingEventsCreated', {
          count: result.feeding_events_created,
        }),
      );
      loadWateringData();
    } catch (err) {
      handleError(err);
    } finally {
      setQuickConfirming(null);
    }
  };

  const entryColumns: Column<PlantingRunEntry>[] = [
    { id: 'species', label: t('entities.species'), render: (r) => r.species_key },
    { id: 'cultivar', label: t('entities.cultivar'), render: (r) => r.cultivar_key ?? '-' },
    { id: 'quantity', label: t('pages.plantingRuns.quantity'), render: (r) => r.quantity, align: 'right' },
    { id: 'role', label: t('pages.plantingRuns.role'), render: (r) => t(`enums.entryRole.${r.role}`), searchValue: (r) => t(`enums.entryRole.${r.role}`) },
    { id: 'idPrefix', label: t('pages.plantingRuns.idPrefix'), render: (r) => r.id_prefix },
    { id: 'spacing', label: t('pages.plantingRuns.spacing'), render: (r) => r.spacing_cm ? `${r.spacing_cm} cm` : '-', align: 'right' },
  ];

  const plantColumns: Column<PlantInRun>[] = [
    { id: 'instanceId', label: t('pages.plantInstances.instanceId'), render: (r) => r.instance_id },
    { id: 'currentPhase', label: t('pages.plantInstances.currentPhase'), render: (r) => <Chip label={r.current_phase} size="small" color="primary" />, searchValue: (r) => r.current_phase },
    { id: 'plantedOn', label: t('pages.plantInstances.plantedOn'), render: (r) => r.planted_on },
    { id: 'removedOn', label: t('pages.plantInstances.removedOn'), render: (r) => r.removed_on ?? '-' },
    { id: 'detached', label: t('pages.plantingRuns.detached'), render: (r) => r.detached_at ? t('common.yes') : '-' },
    {
      id: 'actions', label: '', width: 80, sortable: false, searchable: false,
      render: (r) => !r.detached_at && run?.status === 'active' ? (
        <Button size="small" onClick={(e) => { e.stopPropagation(); onDetach(r.key); }}>
          {t('pages.plantingRuns.detach')}
        </Button>
      ) : null,
    },
  ];

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
            <>
              <Button
                variant="outlined"
                startIcon={<SwapHorizIcon />}
                onClick={() => setBatchTransitionOpen(true)}
                data-testid="batch-transition-button"
              >
                {t('pages.plantingRuns.batchTransition')}
              </Button>
              <Button
                color="error"
                startIcon={<RemoveCircleIcon />}
                onClick={() => setBatchRemoveOpen(true)}
                data-testid="batch-remove-button"
              >
                {t('pages.plantingRuns.batchRemove')}
              </Button>
            </>
          )}
        </Box>
      </Box>

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 3 }}>
        <Tab label={t('pages.plantingRuns.tabDetails')} />
        <Tab label={t('pages.plantingRuns.tabPlants')} />
        <Tab label={t('pages.plantingRuns.tabPhases')} data-testid="phases-tab" />
        <Tab label={t('pages.wateringSchedule.title')} data-testid="watering-tab" />
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
              <DataTable
                columns={entryColumns}
                rows={entries}
                getRowKey={(r) => r.key}
                variant="simple"
                ariaLabel={t('pages.plantingRuns.entries')}
              />
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
            <DataTable
              columns={plantColumns}
              rows={plants}
              getRowKey={(r) => r.key}
              variant="simple"
              ariaLabel={t('pages.plantingRuns.tabPlants')}
            />
          )}
        </Box>
      )}

      {/* Tab 2: Phases */}
      {tab === 2 && key && (
        <Box data-testid="phases-tab-content">
          <Typography variant="h6" sx={{ mb: 2 }}>
            {t('pages.plantingRuns.phaseTimeline')}
          </Typography>
          <PhaseTimelineStepper runKey={key} />

          {plants.length > 0 && (
            <Box sx={{ mt: 4 }}>
              <Typography variant="h6" sx={{ mb: 2 }}>
                {t('pages.plantingRuns.editPhaseDate')}
              </Typography>
              <TextField
                select
                label={t('pages.plantingRuns.selectPlant')}
                value={selectedPlantKey}
                onChange={(e) => setSelectedPlantKey(e.target.value)}
                fullWidth
                sx={{ maxWidth: 400, mb: 2 }}
                data-testid="plant-select"
              >
                {plants
                  .filter((p) => !p.detached_at)
                  .map((p) => (
                    <MenuItem key={p.key} value={p.key}>
                      {p.instance_id} ({p.current_phase})
                    </MenuItem>
                  ))}
              </TextField>
              {selectedPlantKey && <PhaseHistoryTable plantKey={selectedPlantKey} />}
            </Box>
          )}
        </Box>
      )}

      {/* Tab 3: Watering Schedule */}
      {tab === 3 && (
        <Box data-testid="watering-schedule-tab">
          {wateringLoading && (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          )}

          {!wateringLoading && (
            <>
              {/* Plan Assignment */}
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    {t('pages.nutrientPlans.assignPlan')}
                  </Typography>

                  {assignedPlan ? (
                    <Box>
                      <Alert severity="success" sx={{ mb: 2 }}>
                        {t('pages.nutrientPlans.assignedPlan')}:{' '}
                        <strong>{(assignedPlan as { name?: string }).name ?? t('pages.wateringSchedule.noPlan')}</strong>
                      </Alert>
                      <Button
                        variant="outlined"
                        color="error"
                        startIcon={<DeleteIcon />}
                        onClick={() => setRemovePlanOpen(true)}
                        data-testid="remove-plan-button"
                      >
                        {t('pages.wateringSchedule.removePlan')}
                      </Button>
                    </Box>
                  ) : (
                    <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
                      <TextField
                        select
                        label={t('pages.wateringSchedule.assignPlan')}
                        value={selectedPlanKey}
                        onChange={(e) => setSelectedPlanKey(e.target.value)}
                        fullWidth
                        sx={{ maxWidth: 400 }}
                        data-testid="plan-select"
                      >
                        {nutrientPlans.map((plan) => (
                          <MenuItem key={plan.key} value={plan.key}>
                            {plan.name}
                          </MenuItem>
                        ))}
                      </TextField>
                      <Button
                        variant="contained"
                        onClick={onAssignPlan}
                        disabled={!selectedPlanKey || assigning}
                        data-testid="assign-plan-button"
                      >
                        {assigning ? <CircularProgress size={20} /> : t('pages.wateringSchedule.assignPlan')}
                      </Button>
                    </Box>
                  )}
                </CardContent>
              </Card>

              {/* Watering Calendar */}
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    <WaterDropIcon color="primary" />
                    <Typography variant="h6">
                      {t('pages.wateringSchedule.upcomingDates')}
                    </Typography>
                  </Box>

                  {!wateringCalendar || !wateringCalendar.has_schedule ? (
                    <Alert severity="info">
                      {t('pages.wateringSchedule.noPlan')}
                    </Alert>
                  ) : (
                    <WateringCalendarView
                      dates={wateringCalendar.dates}
                      channelCalendars={wateringCalendar.channel_calendars ?? []}
                      quickConfirming={quickConfirming}
                      onQuickConfirm={onQuickConfirm}
                      onConfirm={(dateStr, channelId) => {
                        setConfirmDate(dateStr);
                        setConfirmChannelId(channelId);
                        setConfirmDialogOpen(true);
                      }}
                    />
                  )}
                </CardContent>
              </Card>
            </>
          )}
        </Box>
      )}

      {tab === 4 && (
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

      <ConfirmDialog
        open={removePlanOpen}
        title={t('pages.wateringSchedule.removePlan')}
        message={t('pages.wateringSchedule.removePlanConfirm')}
        onConfirm={onRemovePlan}
        onCancel={() => setRemovePlanOpen(false)}
        destructive
      />

      {key && run && (run.status === 'active' || run.status === 'harvesting') && (
        <BatchPhaseTransitionDialog
          open={batchTransitionOpen}
          runKey={key}
          entries={entries}
          plants={plants}
          onClose={() => setBatchTransitionOpen(false)}
          onTransitioned={() => {
            setBatchTransitionOpen(false);
            load();
          }}
        />
      )}

      {key && (
        <WateringConfirmDialog
          open={confirmDialogOpen}
          onClose={() => setConfirmDialogOpen(false)}
          runKey={key}
          taskKey={confirmDate}
          channelId={confirmChannelId}
          onConfirmed={() => {
            setConfirmDialogOpen(false);
            loadWateringData();
          }}
        />
      )}
    </Box>
  );
}
