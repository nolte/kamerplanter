import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link as RouterLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Alert from '@mui/material/Alert';
import Link from '@mui/material/Link';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import RemoveCircleIcon from '@mui/icons-material/RemoveCircle';
import SwapHorizIcon from '@mui/icons-material/SwapHoriz';
import ScienceIcon from '@mui/icons-material/Science';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import DataTable, { type Column } from '@/components/common/DataTable';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormActions from '@/components/form/FormActions';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import PhaseTransitionDialog from './PhaseTransitionDialog';
import FeedingEventCreateDialog from '@/pages/duengung/FeedingEventCreateDialog';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import { useTableLocalState } from '@/hooks/useTableState';
import * as plantApi from '@/api/endpoints/plantInstances';
import * as phasesApi from '@/api/endpoints/phases';
import * as speciesApi from '@/api/endpoints/species';
import * as planApi from '@/api/endpoints/nutrient-plans';
import * as feedingApi from '@/api/endpoints/feeding-events';
import type { PlantInstance, CurrentPhaseResponse, PhaseHistoryEntry, Cultivar, NutrientPlan, FeedingEvent } from '@/api/types';

const editSchema = z.object({
  plant_name: z.string().nullable(),
  cultivar_key: z.string().nullable(),
  slot_key: z.string().nullable(),
  substrate_batch_key: z.string().nullable(),
  planted_on: z.string().min(1),
});

type EditFormData = z.infer<typeof editSchema>;

const assignSchema = z.object({
  plan_key: z.string().min(1),
  assigned_by: z.string().min(1),
});

type AssignFormData = z.infer<typeof assignSchema>;

export default function PlantInstanceDetailPage() {
  const { key } = useParams<{ key: string }>();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [plant, setPlant] = useState<PlantInstance | null>(null);
  const [currentPhase, setCurrentPhase] = useState<CurrentPhaseResponse | null>(null);
  const [history, setHistory] = useState<PhaseHistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [removeOpen, setRemoveOpen] = useState(false);
  const [transitionOpen, setTransitionOpen] = useState(false);
  const [tab, setTab] = useState(0);
  const [saving, setSaving] = useState(false);
  const [cultivarList, setCultivarList] = useState<Cultivar[]>([]);

  // Feeding events state
  const [feedingEvents, setFeedingEvents] = useState<FeedingEvent[]>([]);
  const [feedingCreateOpen, setFeedingCreateOpen] = useState(false);
  const feedingTableState = useTableLocalState({ defaultSort: { column: 'timestamp', direction: 'desc' } });

  // Nutrient plan assignment state
  const [assignedPlan, setAssignedPlan] = useState<NutrientPlan | null>(null);
  const [availablePlans, setAvailablePlans] = useState<NutrientPlan[]>([]);
  const [assignDialogOpen, setAssignDialogOpen] = useState(false);
  const [removePlanOpen, setRemovePlanOpen] = useState(false);
  const [assignSaving, setAssignSaving] = useState(false);

  const {
    control,
    handleSubmit,
    reset,
    formState: { isDirty },
  } = useForm<EditFormData>({
    resolver: zodResolver(editSchema),
    defaultValues: {
      plant_name: null,
      cultivar_key: null,
      slot_key: null,
      substrate_batch_key: null,
      planted_on: '',
    },
  });

  const {
    control: assignControl,
    handleSubmit: handleAssignSubmit,
    reset: resetAssign,
  } = useForm<AssignFormData>({
    resolver: zodResolver(assignSchema),
    defaultValues: { plan_key: '', assigned_by: '' },
  });

  const load = async () => {
    if (!key) return;
    setLoading(true);
    try {
      const p = await plantApi.getPlantInstance(key);
      setPlant(p);
      if (p.species_key) {
        speciesApi.listCultivars(p.species_key).then(setCultivarList).catch(() => setCultivarList([]));
      }
      reset({
        plant_name: p.plant_name,
        cultivar_key: p.cultivar_key,
        slot_key: p.slot_key,
        substrate_batch_key: p.substrate_batch_key,
        planted_on: p.planted_on,
      });
      try {
        const cp = await phasesApi.getCurrentPhase(key);
        setCurrentPhase(cp);
      } catch {
        // Phase control may not be configured
      }
      try {
        const h = await phasesApi.getPhaseHistory(key);
        setHistory(h);
      } catch {
        // History may be empty
      }
      // Load feeding history
      try {
        const fe = await feedingApi.getPlantFeedingHistory(key);
        setFeedingEvents(fe);
      } catch {
        // May not have any feeding events
      }
      // Load assigned nutrient plan
      const ap = await planApi.getPlantPlan(key);
      setAssignedPlan(ap);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [key]); // eslint-disable-line react-hooks/exhaustive-deps

  const onRemove = async () => {
    if (!key) return;
    try {
      const updated = await plantApi.removePlantInstance(key);
      setPlant(updated);
      notification.success(t('pages.plantInstances.remove'));
    } catch (err) {
      handleError(err);
    }
    setRemoveOpen(false);
  };

  const onEditSubmit = async (data: EditFormData) => {
    if (!key || !plant) return;
    try {
      setSaving(true);
      await plantApi.updatePlantInstance(key, {
        instance_id: plant.instance_id,
        species_key: plant.species_key,
        ...data,
      });
      notification.success(t('common.save'));
      load();
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  const openAssignDialog = async () => {
    try {
      const plans = await planApi.fetchNutrientPlans(0, 200);
      setAvailablePlans(plans);
      resetAssign({ plan_key: '', assigned_by: '' });
      setAssignDialogOpen(true);
    } catch (err) {
      handleError(err);
    }
  };

  const onAssignPlan = async (data: AssignFormData) => {
    if (!key) return;
    try {
      setAssignSaving(true);
      await planApi.assignPlanToPlant(key, data);
      notification.success(t('pages.nutrientPlans.assignPlan'));
      setAssignDialogOpen(false);
      load();
    } catch (err) {
      handleError(err);
    } finally {
      setAssignSaving(false);
    }
  };

  const onRemovePlan = async () => {
    if (!key) return;
    try {
      await planApi.removePlantPlan(key);
      notification.success(t('pages.nutrientPlans.removePlan'));
      setAssignedPlan(null);
      setRemovePlanOpen(false);
    } catch (err) {
      handleError(err);
    }
  };

  const historyColumns: Column<PhaseHistoryEntry>[] = [
    { id: 'phase', label: t('pages.phases.current'), render: (r) => r.phase_name },
    { id: 'enteredAt', label: t('pages.phases.enteredAt'), render: (r) => new Date(r.entered_at).toLocaleDateString() },
    { id: 'exitedAt', label: t('pages.phases.exitedAt'), render: (r) => r.exited_at ? new Date(r.exited_at).toLocaleDateString() : '-' },
    { id: 'duration', label: t('pages.phases.duration'), render: (r) => r.actual_duration_days ?? '-', align: 'right' },
    { id: 'reason', label: t('pages.phases.transitionReason'), render: (r) => r.transition_reason },
  ];

  if (loading) return <LoadingSkeleton variant="form" />;
  if (error) return <ErrorDisplay error={error} onRetry={() => navigate(-1)} />;

  return (
    <Box data-testid="plant-instance-detail-page">
      <UnsavedChangesGuard dirty={isDirty} />
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <PageTitle title={plant?.plant_name ?? plant?.instance_id ?? t('entities.plantInstance')} />
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            startIcon={<SwapHorizIcon />}
            onClick={() => setTransitionOpen(true)}
            disabled={!!plant?.removed_on}
            data-testid="transition-button"
          >
            {t('pages.phases.transition')}
          </Button>
          <Button
            color="error"
            startIcon={<RemoveCircleIcon />}
            onClick={() => setRemoveOpen(true)}
            disabled={!!plant?.removed_on}
            data-testid="remove-button"
          >
            {t('pages.plantInstances.remove')}
          </Button>
        </Box>
      </Box>

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 3 }}>
        <Tab label={t('pages.plantInstances.info')} />
        <Tab label={t('entities.nutrientPlan')} />
        <Tab label={t('entities.feedingEvents')} />
        <Tab label={t('common.edit')} />
      </Tabs>

      {tab === 0 && (
        <>
          {plant && (
            <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap', mb: 4 }}>
              <Card sx={{ minWidth: 250 }} data-testid="plant-info-card">
                <CardContent>
                  <Typography variant="subtitle2" color="text.secondary">
                    {t('pages.plantInstances.instanceId')}
                  </Typography>
                  <Typography>{plant.instance_id}</Typography>
                  <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 1 }}>
                    {t('pages.plantInstances.plantedOn')}
                  </Typography>
                  <Typography>{plant.planted_on}</Typography>
                  {plant.removed_on && (
                    <>
                      <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 1 }}>
                        {t('pages.plantInstances.removedOn')}
                      </Typography>
                      <Typography>{plant.removed_on}</Typography>
                    </>
                  )}
                </CardContent>
              </Card>

              <Card sx={{ minWidth: 250 }} data-testid="phase-info-card">
                <CardContent>
                  <Typography variant="subtitle2" color="text.secondary">
                    {t('pages.phases.current')}
                  </Typography>
                  <Chip label={plant.current_phase} color="primary" sx={{ mt: 0.5 }} data-testid="current-phase" />
                  {currentPhase && (
                    <>
                      <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 1 }}>
                        {t('pages.phases.daysInPhase')}
                      </Typography>
                      <Typography>{currentPhase.days_in_phase}</Typography>
                      {currentPhase.next_phase && (
                        <>
                          <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 1 }}>
                            {t('pages.phases.nextPhase')}
                          </Typography>
                          <Typography>{currentPhase.next_phase}</Typography>
                        </>
                      )}
                    </>
                  )}
                </CardContent>
              </Card>
            </Box>
          )}

          {history.length > 0 && (
            <Box data-testid="phase-history">
              <Typography variant="h6" sx={{ mb: 2 }}>
                {t('pages.phases.history')}
              </Typography>
              <DataTable
                columns={historyColumns}
                rows={history}
                getRowKey={(r) => r.key}
                variant="simple"
                ariaLabel={t('pages.phases.history')}
              />
            </Box>
          )}
        </>
      )}

      {/* Tab 1: Nutrient Plan */}
      {tab === 1 && (
        <Box>
          {assignedPlan ? (
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <ScienceIcon />
                    {t('pages.nutrientPlans.assignedPlan')}
                  </Typography>
                  <Button
                    variant="outlined"
                    color="error"
                    size="small"
                    startIcon={<DeleteIcon />}
                    onClick={() => setRemovePlanOpen(true)}
                  >
                    {t('pages.nutrientPlans.removePlan')}
                  </Button>
                </Box>
                <Typography variant="h5" sx={{ mb: 1 }}>
                  <Link component={RouterLink} to={`/duengung/plans/${assignedPlan.key}`} underline="hover">
                    {assignedPlan.name}
                  </Link>
                </Typography>
                {assignedPlan.description && (
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    {assignedPlan.description}
                  </Typography>
                )}
                <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap', mt: 1 }}>
                  {assignedPlan.recommended_substrate_type && (
                    <Chip
                      label={t(`enums.substrateType.${assignedPlan.recommended_substrate_type}`)}
                      size="small"
                      variant="outlined"
                    />
                  )}
                  {assignedPlan.is_template && (
                    <Chip label={t('pages.nutrientPlans.isTemplate')} size="small" color="primary" />
                  )}
                  <Chip label={`v${assignedPlan.version}`} size="small" variant="outlined" />
                  {assignedPlan.author && (
                    <Chip label={assignedPlan.author} size="small" variant="outlined" />
                  )}
                  {assignedPlan.tags?.map((tag) => (
                    <Chip key={tag} label={tag} size="small" />
                  ))}
                </Box>
              </CardContent>
            </Card>
          ) : (
            <Box>
              <Alert severity="info" sx={{ mb: 2 }}>
                {t('pages.nutrientPlans.noPlanAssigned')}
              </Alert>
              <Button
                variant="contained"
                startIcon={<ScienceIcon />}
                onClick={openAssignDialog}
                disabled={!!plant?.removed_on}
              >
                {t('pages.nutrientPlans.assignPlan')}
              </Button>
            </Box>
          )}
        </Box>
      )}

      {/* Tab 2: Feeding Events */}
      {tab === 2 && (
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">{t('entities.feedingEvents')}</Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setFeedingCreateOpen(true)}
              disabled={!!plant?.removed_on}
              data-testid="create-feeding-button"
            >
              {t('pages.feedingEvents.create')}
            </Button>
          </Box>
          <DataTable<FeedingEvent>
            columns={[
              {
                id: 'timestamp',
                label: t('pages.feedingEvents.timestamp'),
                render: (r) => r.timestamp ? new Date(r.timestamp).toLocaleString() : '—',
                searchValue: (r) => r.timestamp ? new Date(r.timestamp).toLocaleString() : '',
              },
              {
                id: 'applicationMethod',
                label: t('pages.feedingEvents.applicationMethod'),
                render: (r) => t(`enums.applicationMethod.${r.application_method}`),
                searchValue: (r) => t(`enums.applicationMethod.${r.application_method}`),
              },
              {
                id: 'volume',
                label: t('pages.feedingEvents.volumeApplied'),
                render: (r) => `${r.volume_applied_liters} L`,
                align: 'right',
              },
              {
                id: 'isSupplemental',
                label: t('pages.feedingEvents.isSupplemental'),
                render: (r) => r.is_supplemental ? (
                  <Chip label={t('common.yes')} size="small" color="info" />
                ) : null,
              },
              {
                id: 'ecAfter',
                label: t('pages.feedingEvents.ecAfter'),
                render: (r) => r.measured_ec_after != null ? String(r.measured_ec_after) : '—',
                align: 'right',
              },
            ]}
            rows={feedingEvents}
            getRowKey={(r) => r.key}
            onRowClick={(r) => navigate(`/duengung/feeding-events/${r.key}`)}
            tableState={feedingTableState}
            ariaLabel={t('entities.feedingEvents')}
          />
          <FeedingEventCreateDialog
            open={feedingCreateOpen}
            onClose={() => setFeedingCreateOpen(false)}
            onCreated={() => {
              setFeedingCreateOpen(false);
              load();
            }}
            plantKey={key}
          />
        </Box>
      )}

      {/* Tab 3: Edit */}
      {tab === 3 && (
        <Box component="form" onSubmit={handleSubmit(onEditSubmit)} sx={{ maxWidth: 600 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {t('pages.plantInstances.editIntro')}
          </Typography>
          <FormTextField name="plant_name" control={control} label={t('pages.plantInstances.plantName')} helperText={t('pages.plantInstances.plantNameHelper')} />
          <FormSelectField
            name="cultivar_key"
            control={control}
            label={t('pages.plantInstances.cultivarKey')}
            helperText={t('pages.plantInstances.cultivarKeyHelper')}
            options={[
              { value: '', label: '-' },
              ...cultivarList.map((c) => ({ value: c.key, label: c.name })),
            ]}
          />
          <FormTextField name="slot_key" control={control} label={t('pages.plantInstances.slotKey')} helperText={t('pages.plantInstances.slotKeyHelper')} />
          <FormTextField name="substrate_batch_key" control={control} label={t('pages.plantInstances.substrateBatchKey')} helperText={t('pages.plantInstances.substrateBatchKeyHelper')} />
          <FormTextField name="planted_on" control={control} label={t('pages.plantInstances.plantedOn')} helperText={t('pages.plantInstances.plantedOnHelper')} type="date" required />
          <FormActions onCancel={() => setTab(0)} loading={saving} />
        </Box>
      )}

      <ConfirmDialog
        open={removeOpen}
        title={t('pages.plantInstances.remove')}
        message={t('common.deleteConfirm', { name: plant?.plant_name ?? plant?.instance_id })}
        onConfirm={onRemove}
        onCancel={() => setRemoveOpen(false)}
        destructive
      />

      <ConfirmDialog
        open={removePlanOpen}
        title={t('pages.nutrientPlans.removePlan')}
        message={t('common.deleteConfirm', { name: assignedPlan?.name ?? '' })}
        onConfirm={onRemovePlan}
        onCancel={() => setRemovePlanOpen(false)}
      />

      {/* Assign Plan Dialog */}
      <Dialog open={assignDialogOpen} onClose={() => setAssignDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{t('pages.nutrientPlans.assignPlan')}</DialogTitle>
        <DialogContent>
          <form onSubmit={handleAssignSubmit(onAssignPlan)}>
            <FormSelectField
              name="plan_key"
              control={assignControl}
              label={t('entities.nutrientPlan')}
              options={availablePlans.map((p) => ({
                value: p.key,
                label: `${p.name}${p.is_template ? ` (${t('pages.nutrientPlans.isTemplate')})` : ''}`,
              }))}
              required
            />
            <FormTextField
              name="assigned_by"
              control={assignControl}
              label={t('pages.nutrientPlans.assignedBy')}
              required
            />
            <FormActions
              onCancel={() => setAssignDialogOpen(false)}
              loading={assignSaving}
              saveLabel={t('pages.nutrientPlans.assignPlan')}
            />
          </form>
        </DialogContent>
      </Dialog>

      {key && (
        <PhaseTransitionDialog
          plantKey={key}
          lifecycleKey={plant?.current_phase_key ?? null}
          open={transitionOpen}
          onClose={() => setTransitionOpen(false)}
          onTransitioned={(updated) => {
            setPlant(updated);
            setTransitionOpen(false);
            load();
          }}
        />
      )}
    </Box>
  );
}
