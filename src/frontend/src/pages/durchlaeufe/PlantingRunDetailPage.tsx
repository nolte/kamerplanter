import { useEffect, useState, useCallback } from 'react';
import { useTabUrl } from '@/hooks/useTabUrl';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import type { ChipProps } from '@mui/material/Chip';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import DeleteIcon from '@mui/icons-material/Delete';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import StopCircleIcon from '@mui/icons-material/StopCircle';
import SwapHorizIcon from '@mui/icons-material/SwapHoriz';
import EditIcon from '@mui/icons-material/Edit';
import PersonAddIcon from '@mui/icons-material/PersonAdd';
import Dialog from '@mui/material/Dialog';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import type { Column } from '@/components/common/DataTable';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import BatchPhaseTransitionDialog from './BatchPhaseTransitionDialog';
import RunPhaseEditor from './RunPhaseEditor';
import PhaseKamiTimeline from './PhaseKamiTimeline';
import WateringConfirmDialog from './WateringConfirmDialog';
import ActivityPlanTab from './ActivityPlanTab';
import PlantingRunDetailsTab from './PlantingRunDetailsTab';
import PlantingRunPlantsTab from './PlantingRunPlantsTab';
import PlantingRunNutrientWateringTab from './PlantingRunNutrientWateringTab';
import PlantingRunEditDialog from './PlantingRunEditDialog';
import AdoptPlantsDialog from './AdoptPlantsDialog';
import { useRunNutrientData } from '@/hooks/useRunNutrientData';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import { useWateringVolumeSuggestion } from '@/hooks/useWateringVolumeSuggestion';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { setBreadcrumbs } from '@/store/slices/uiSlice';
import * as speciesApi from '@/api/endpoints/species';
import * as runApi from '@/api/endpoints/plantingRuns';
import * as planApi from '@/api/endpoints/nutrient-plans';
import * as fertApi from '@/api/endpoints/fertilizers';
import * as siteApi from '@/api/endpoints/sites';
import * as tankApi from '@/api/endpoints/tanks';
import { quickConfirmWatering } from '@/api/endpoints/wateringConfirm';
import type {
  NutrientPlanPhaseEntry,
  Fertilizer,
  SpeciesPhaseTimeline,
  PlantingRun,
  PlantingRunEntry,
  PlantInRun,
  PlantingRunStatus,
  WateringScheduleCalendarResponse,
  Site,
} from '@/api/types';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';

const statusColor: Record<PlantingRunStatus, ChipProps['color']> = {
  planned: 'default',
  active: 'primary',
  harvesting: 'warning',
  completed: 'success',
  cancelled: 'error',
};

// Tab slugs — "edit" removed (now a dialog), "nutrient-plan" + "watering" merged
const TAB_SLUGS = ['details', 'plants', 'phases', 'nutrient-watering', 'activity-plan'] as const;

export default function PlantingRunDetailPage() {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { key } = useParams<{ key: string }>();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [run, setRun] = useState<PlantingRun | null>(null);
  const [entries, setEntries] = useState<PlantingRunEntry[]>([]);
  const [plants, setPlants] = useState<PlantInRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useTabUrl(TAB_SLUGS);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [createPlantsOpen, setCreatePlantsOpen] = useState(false);
  const [batchRemoveOpen, setBatchRemoveOpen] = useState(false);
  const [endRunOpen, setEndRunOpen] = useState(false);
  const [endRunStatus, setEndRunStatus] = useState<'completed' | 'cancelled'>('cancelled');
  const [batchTransitionOpen, setBatchTransitionOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [adoptDialogOpen, setAdoptDialogOpen] = useState(false);

  // Species/cultivar name resolution for entries table
  const [speciesMap, setSpeciesMap] = useState<Map<string, string>>(new Map());
  const [locationName, setLocationName] = useState<string>('');
  const [siteKeyFromLocation, setSiteKeyFromLocation] = useState<string | null>(null);

  // Nutrient plan / watering state
  const [assignedPlan, setAssignedPlan] = useState<Record<string, unknown> | null>(null);
  const [wateringCalendar, setWateringCalendar] = useState<WateringScheduleCalendarResponse | null>(null);
  const [wateringLoading, setWateringLoading] = useState(false);
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);
  const [confirmDate, setConfirmDate] = useState('');
  const [confirmChannelId, setConfirmChannelId] = useState<string | undefined>(undefined);
  const [quickConfirming, setQuickConfirming] = useState<string | null>(null);
  const [removePlanOpen, setRemovePlanOpen] = useState(false);

  // Volume suggestion from first plant in run
  const firstPlantKey = plants.length > 0 ? plants[0].key : undefined;
  const { suggestion: volumeSuggestion } = useWateringVolumeSuggestion(firstPlantKey);

  // Dosage display mode
  const wateringCanLiters = useAppSelector((s) => s.userPreferences.preferences?.watering_can_liters ?? 10);
  const [dosageMode, setDosageMode] = useState<'per_liter' | 'total'>('per_liter');

  // Gantt chart raw data
  const [planEntries, setPlanEntries] = useState<NutrientPlanPhaseEntry[]>([]);
  const [fertilizers, setFertilizers] = useState<Fertilizer[]>([]);
  const [resolvedTank, setResolvedTank] = useState<{ key: string; name: string; volumeLiters: number } | null>(null);
  const [phaseTimelines, setPhaseTimelines] = useState<SpeciesPhaseTimeline[]>([]);

  // Site list for edit dialog
  const [sitesList, setSitesList] = useState<Site[]>([]);

  // Derived nutrient data via custom hook
  const nutrientData = useRunNutrientData(planEntries, phaseTimelines, run?.started_at);

  // Track dirty state for UnsavedChangesGuard (edit dialog has own form)
  const isDirty = false;

  const load = useCallback(async () => {
    if (!key) return;
    setLoading(true);
    try {
      const r = await runApi.getPlantingRun(key);
      setRun(r);
      if (r.location_key) {
        try {
          const loc = await siteApi.getLocation(r.location_key);
          setSiteKeyFromLocation(loc.site_key);
          setLocationName(loc.name);
          if (loc.tank_key) {
            const tk = await tankApi.getTank(loc.tank_key);
            setResolvedTank({ key: tk.key, name: tk.name, volumeLiters: tk.volume_liters });
          } else {
            const allTanks = await tankApi.listTanks(0, 200);
            const match = allTanks.find((tk) => tk.location_key === r.location_key);
            if (match) {
              setResolvedTank({ key: match.key, name: match.name, volumeLiters: match.volume_liters });
            } else {
              setResolvedTank(null);
            }
          }
        } catch {
          setResolvedTank(null);
          setLocationName('');
        }
      } else {
        setResolvedTank(null);
        setLocationName('');
        setSiteKeyFromLocation(null);
      }
      const e = await runApi.listEntries(key);
      setEntries(e);
      const uniqueSpeciesKeys = [...new Set(e.map((entry) => entry.species_key))];
      const nameMap = new Map<string, string>();
      await Promise.all(
        uniqueSpeciesKeys.map(async (sk) => {
          try {
            const sp = await speciesApi.getSpecies(sk);
            nameMap.set(sk, sp.common_names?.length > 0 ? sp.common_names[0] : sp.scientific_name);
            for (const ent of e.filter((en) => en.species_key === sk && en.cultivar_key)) {
              try {
                const cv = await speciesApi.getCultivar(sk, ent.cultivar_key!);
                nameMap.set(ent.cultivar_key!, cv.name);
              } catch { /* ok */ }
            }
          } catch { /* ok */ }
        }),
      );
      setSpeciesMap(nameMap);
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
  }, [key]);

  useEffect(() => {
    load();
    siteApi.listSites(0, 200).then(setSitesList).catch(() => {});
  }, [load]);

  // Dynamic breadcrumbs
  useEffect(() => {
    if (!run) return;
    dispatch(setBreadcrumbs([
      { label: 'nav.dashboard', path: '/dashboard' },
      { label: 'nav.plantingRuns', path: '/durchlaeufe/planting-runs' },
      { label: run.name },
    ]));
  }, [run, dispatch]);

  // Clear dynamic breadcrumbs on unmount
  useEffect(() => () => { dispatch(setBreadcrumbs([])); }, [dispatch]);

  const loadWateringData = useCallback(async () => {
    if (!key) return;
    setWateringLoading(true);
    try {
      const [planResult, calendar, timelines] = await Promise.all([
        runApi.getRunNutrientPlan(key).catch(() => ({ plan: null })),
        runApi.getWateringSchedule(key, 90).catch(() => null),
        runApi.getPhaseTimeline(key).catch(() => [] as SpeciesPhaseTimeline[]),
      ]);
      setAssignedPlan(planResult.plan);
      setWateringCalendar(calendar);
      setPhaseTimelines(timelines);
      if (planResult.plan) {
        const planKey = (planResult.plan as { key?: string }).key ?? '';
        if (planKey) {
          const [fetchedEntries, ferts] = await Promise.all([
            planApi.fetchPhaseEntries(planKey),
            fertApi.fetchFertilizers(0, 200),
          ]);
          setPlanEntries(fetchedEntries);
          setFertilizers(ferts);
        }
      } else {
        setPlanEntries([]);
        setFertilizers([]);
      }
    } catch (err) {
      handleError(err);
    } finally {
      setWateringLoading(false);
    }
  }, [key, handleError]);

  // Load watering data for details tab (tab 0) and nutrient+watering tab (tab 3)
  useEffect(() => {
    if (tab === 0 || tab === 3) {
      loadWateringData();
    }
  }, [tab, loadWateringData]);

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

  const onEndRun = async () => {
    if (!key) return;
    try {
      const result = await runApi.batchRemove(key, {
        reason: 'run_ended',
        target_status: endRunStatus,
      });
      notification.success(
        t('pages.plantingRuns.runEnded', {
          count: result.removed_count,
          status: t(`enums.plantingRunStatus.${result.final_status}`),
        }),
      );
      load();
    } catch (err) {
      handleError(err);
    }
    setEndRunOpen(false);
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

  const onAssignPlan = async (planKey: string) => {
    if (!key) return;
    await runApi.assignNutrientPlan(key, planKey);
    notification.success(t('pages.wateringSchedule.assignPlan'));
    loadWateringData();
  };

  const onRemovePlan = async () => {
    if (!key) return;
    try {
      await runApi.removeRunNutrientPlan(key);
      notification.success(t('pages.wateringSchedule.removePlan'));
      setAssignedPlan(null);
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
    { id: 'species', label: t('entities.species'), render: (r) => speciesMap.get(r.species_key) ?? r.species_key, searchValue: (r) => speciesMap.get(r.species_key) ?? r.species_key },
    { id: 'cultivar', label: t('entities.cultivar'), render: (r) => r.cultivar_key ? (speciesMap.get(r.cultivar_key) ?? r.cultivar_key) : '\u2014', searchValue: (r) => r.cultivar_key ? (speciesMap.get(r.cultivar_key) ?? '') : '' },
    { id: 'quantity', label: t('pages.plantingRuns.quantity'), render: (r) => r.quantity, align: 'right' },
    { id: 'idPrefix', label: t('pages.plantingRuns.idPrefix'), render: (r) => r.id_prefix },
    { id: 'spacing', label: t('pages.plantingRuns.spacing'), render: (r) => r.spacing_cm ? `${r.spacing_cm} cm` : '\u2014', align: 'right' },
  ];

  const plantColumns: Column<PlantInRun>[] = [
    { id: 'instanceId', label: t('pages.plantInstances.instanceId'), render: (r) => r.instance_id },
    { id: 'currentPhase', label: t('pages.plantInstances.currentPhase'), render: (r) => <Chip label={r.current_phase} size="small" color="primary" />, searchValue: (r) => r.current_phase },
    { id: 'plantedOn', label: t('pages.plantInstances.plantedOn'), render: (r) => r.planted_on },
    { id: 'removedOn', label: t('pages.plantInstances.removedOn'), render: (r) => r.removed_on ?? '\u2014' },
    { id: 'detached', label: t('pages.plantingRuns.detached'), render: (r) => r.detached_at ? t('common.yes') : '\u2014' },
    {
      id: 'open', label: '', width: 48, sortable: false, searchable: false,
      render: (r) => (
        <Tooltip title={t('pages.plantInstances.title')}>
          <IconButton
            size="small"
            onClick={(e) => { e.stopPropagation(); navigate(`/pflanzen/plant-instances/${r.key}`); }}
            data-testid={`open-plant-${r.key}`}
            aria-label={t('pages.plantInstances.title')}
          >
            <OpenInNewIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      ),
    },
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

      {/* ── Header: responsive flex → stack on mobile ── */}
      <Box
        sx={{
          display: 'flex',
          flexDirection: { xs: 'column', sm: 'row' },
          justifyContent: 'space-between',
          alignItems: { xs: 'flex-start', sm: 'center' },
          gap: 2,
          mb: 1,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
          <PageTitle title={run?.name ?? t('entities.plantingRun')} />
          {run && (
            <Chip
              label={t(`enums.plantingRunStatus.${run.status}`)}
              color={statusColor[run.status] ?? 'default'}
              data-testid="status-chip"
            />
          )}
          <Tooltip title={t('common.edit')}>
            <IconButton
              size="small"
              onClick={() => setEditDialogOpen(true)}
              data-testid="edit-button"
              aria-label={t('common.edit')}
            >
              <EditIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          {(run?.status === 'planned' || run?.status === 'active') && (
            <Button
              variant="outlined"
              startIcon={<PersonAddIcon />}
              onClick={() => setAdoptDialogOpen(true)}
              data-testid="adopt-plants-button"
            >
              {t('pages.plantingRuns.adoptPlants')}
            </Button>
          )}
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
                variant="contained"
                color="error"
                startIcon={<StopCircleIcon />}
                onClick={() => {
                  setEndRunStatus(run?.status === 'harvesting' ? 'completed' : 'cancelled');
                  setEndRunOpen(true);
                }}
                data-testid="end-run-button"
              >
                {t('pages.plantingRuns.endRun')}
              </Button>
            </>
          )}
        </Box>
      </Box>

      {/* ── Tabs (5 instead of 7) ── */}
      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 3 }}>
        <Tab id="tab-details" label={t('pages.plantingRuns.tabDetails')} />
        <Tab id="tab-plants" label={t('pages.plantingRuns.tabPlants')} />
        <Tab id="tab-phases" label={t('pages.plantingRuns.tabPhases')} data-testid="phases-tab" />
        <Tab id="tab-nutrient-watering" label={t('pages.plantingRuns.tabNutrientWatering')} data-testid="nutrient-plan-tab" />
        <Tab id="tab-activity-plan" label={t('pages.activityPlan.tabTitle')} data-testid="activity-plan-tab" />
      </Tabs>

      {/* Tab 0: Details */}
      {tab === 0 && run && (
        <PlantingRunDetailsTab
          run={run}
          entries={entries}
          entryColumns={entryColumns}
          speciesMap={speciesMap}
          assignedPlan={assignedPlan}
          locationName={locationName}
          fertilizers={fertilizers}
          nutrientData={nutrientData}
          dosageMode={dosageMode}
          onDosageModeChange={setDosageMode}
          wateringCanLiters={wateringCanLiters}
          tankVolumeLiters={resolvedTank?.volumeLiters ?? null}
          tankName={resolvedTank?.name ?? null}
        />
      )}

      {/* Tab 1: Plants */}
      {tab === 1 && (
        <PlantingRunPlantsTab
          plants={plants}
          plantColumns={plantColumns}
          runStatus={run?.status}
          onCreatePlants={() => setCreatePlantsOpen(true)}
          onAdoptPlants={() => setAdoptDialogOpen(true)}
        />
      )}

      {/* Tab 2: Phases */}
      {tab === 2 && key && (
        <Box role="tabpanel" aria-labelledby="tab-phases" data-testid="phases-tab-content">
          {phaseTimelines.length > 0 && phaseTimelines[0].phases.length > 0 && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  {t('pages.plantingRuns.phaseTimeline')}
                </Typography>
                <PhaseKamiTimeline phases={phaseTimelines[0].phases} speciesName={phaseTimelines[0].species_name} />
              </CardContent>
            </Card>
          )}
          <RunPhaseEditor
            runKey={key}
            isActive={run?.status === 'active' || run?.status === 'harvesting'}
            onPhaseDatesChanged={loadWateringData}
          />
        </Box>
      )}

      {/* Tab 3: Nutrient Plan + Watering (merged) */}
      {tab === 3 && (
        <PlantingRunNutrientWateringTab
          runStatus={run?.status}
          wateringLoading={wateringLoading}
          assignedPlan={assignedPlan}
          nutrientData={nutrientData}
          fertilizers={fertilizers}
          wateringCalendar={wateringCalendar}
          quickConfirming={quickConfirming}
          phaseTimelines={phaseTimelines}
          planKey={(assignedPlan as { key?: string })?.key ?? null}
          siteKey={siteKeyFromLocation}
          onAssignPlan={onAssignPlan}
          onOpenRemovePlan={() => setRemovePlanOpen(true)}
          onQuickConfirm={onQuickConfirm}
          onOpenConfirmDialog={(dateStr, channelId) => {
            setConfirmDate(dateStr);
            setConfirmChannelId(channelId);
            setConfirmDialogOpen(true);
          }}
        />
      )}

      {/* Tab 4: Activity Plan */}
      {tab === 4 && run && entries.length > 0 && (
        <ActivityPlanTab runKey={key!} speciesKey={entries[0]?.species_key ?? ''} />
      )}

      {/* ── Dialogs ── */}

      {run && (
        <PlantingRunEditDialog
          open={editDialogOpen}
          run={run}
          sitesList={sitesList}
          initialSiteKey={siteKeyFromLocation}
          onClose={() => setEditDialogOpen(false)}
          onSaved={(updated) => {
            setRun(updated);
            setEditDialogOpen(false);
            load();
          }}
        />
      )}

      {key && (
        <AdoptPlantsDialog
          open={adoptDialogOpen}
          onClose={() => setAdoptDialogOpen(false)}
          runKey={key}
          adoptFn={runApi.adoptPlants}
          onAdopted={(count) => {
            setAdoptDialogOpen(false);
            notification.success(
              t('pages.plantingRuns.plantsAdopted', { count }),
            );
            load();
          }}
        />
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

      <Dialog fullScreen={fullScreen} open={endRunOpen}
        onClose={() => setEndRunOpen(false)}
        maxWidth="xs"
        fullWidth
      >
        <DialogTitle>{t('pages.plantingRuns.endRun')}</DialogTitle>
        <DialogContent>
          <Typography sx={{ mb: 2 }}>
            {t('pages.plantingRuns.endRunConfirm', {
              count: plants.filter((p) => !p.removed_on).length,
            })}
          </Typography>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>
            {t('pages.plantingRuns.endRunStatusLabel')}
          </Typography>
          <ToggleButtonGroup
            value={endRunStatus}
            exclusive
            onChange={(_, v) => { if (v) setEndRunStatus(v); }}
            fullWidth
            size="small"
            aria-label={t('pages.plantingRuns.endRunStatusLabel')}
          >
            <ToggleButton value="cancelled" color="warning">
              {t('enums.plantingRunStatus.cancelled')}
            </ToggleButton>
            <ToggleButton value="completed" color="success">
              {t('enums.plantingRunStatus.completed')}
            </ToggleButton>
          </ToggleButtonGroup>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEndRunOpen(false)}>
            {t('common.cancel')}
          </Button>
          <Button variant="contained" color="error" onClick={onEndRun}>
            {t('pages.plantingRuns.endRun')}
          </Button>
        </DialogActions>
      </Dialog>

      <ConfirmDialog
        open={removePlanOpen}
        title={t('pages.nutrientPlans.removePlan')}
        message={t('common.deleteConfirm', { name: (assignedPlan as { name?: string })?.name ?? '' })}
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
          suggestedVolumeLiters={volumeSuggestion?.liters}
          volumeHint={volumeSuggestion?.hint}
          onConfirmed={() => {
            setConfirmDialogOpen(false);
            loadWateringData();
          }}
        />
      )}
    </Box>
  );
}
