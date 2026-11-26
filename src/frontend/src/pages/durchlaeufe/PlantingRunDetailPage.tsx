import { useEffect, useMemo, useState, useCallback } from 'react';
import { useTabUrl } from '@/hooks/useTabUrl';
import { useParams, useNavigate, Link as RouterLink } from 'react-router-dom';
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
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import DeleteIcon from '@mui/icons-material/Delete';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import StopCircleIcon from '@mui/icons-material/StopCircle';
import AgricultureIcon from '@mui/icons-material/Agriculture';
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
import OptionsLoadError from '@/components/common/OptionsLoadError';
import { useAsyncOptions } from '@/hooks/useAsyncOptions';
import { captureHandledError } from '@/observability/errorTracking';
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
import { useOnlineStatus } from '@/hooks/useOnlineStatus';
import RequiresConnectivity from '@/components/common/RequiresConnectivity';
import { useTenantPermissions } from '@/hooks/useTenantPermissions';
import { useApiError } from '@/hooks/useApiError';
import { useAbortableLoad } from '@/hooks/useAbortableLoad';
import { useWateringVolumeSuggestion } from '@/hooks/useWateringVolumeSuggestion';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { setBreadcrumbs } from '@/store/slices/uiSlice';
import * as phaseSequenceApi from '@/api/endpoints/phaseSequences';
import * as speciesApi from '@/api/endpoints/species';
import * as runApi from '@/api/endpoints/plantingRuns';
import * as planApi from '@/api/endpoints/nutrient-plans';
import * as fertApi from '@/api/endpoints/fertilizers';
import * as siteApi from '@/api/endpoints/sites';
import * as tankApi from '@/api/endpoints/tanks';
import * as harvestApi from '@/api/endpoints/harvest';
import { quickConfirmWatering } from '@/api/endpoints/wateringConfirm';
import type {
  ActiveChannel,
  NutrientPlanPhaseEntry,
  Fertilizer,
  SpeciesPhaseTimeline,
  PlantingRun,
  PlantingRunEntry,
  PlantInRun,
  PlantingRunStatus,
  WateringScheduleCalendarResponse,
  Site,
  Species,
  Cultivar,
} from '@/api/types';
import { getLocalizedCommonName, getPlantDisplayName } from '@/utils/plantDisplay';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import List from '@mui/material/List';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemText from '@mui/material/ListItemText';
import { errorKey } from '@/api/errors';
import { compareText } from '@/utils/formatting';

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
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const notification = useNotification();
  const { handleError } = useApiError();
  // Only `DELETE /planting-runs/{key}` is lead-only
  // (`require_permission(PLANTING_RUN, DELETE)`); batch-remove, detach and the
  // nutrient-plan unlink are UPDATE routes and stay grower-writable (#1467).
  const { canDelete } = useTenantPermissions();
  const [run, setRun] = useState<PlantingRun | null>(null);
  const [entries, setEntries] = useState<PlantingRunEntry[]>([]);
  const [plants, setPlants] = useState<PlantInRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useTabUrl(TAB_SLUGS);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [createPlantsOpen, setCreatePlantsOpen] = useState(false);
  const [creatingPlants, setCreatingPlants] = useState(false);
  const [batchRemoveOpen, setBatchRemoveOpen] = useState(false);
  const [batchRemoving, setBatchRemoving] = useState(false);
  const [endRunOpen, setEndRunOpen] = useState(false);
  const [endRunStatus, setEndRunStatus] = useState<'completed' | 'cancelled'>('cancelled');
  const [completeHarvestOpen, setCompleteHarvestOpen] = useState(false);
  const [completingHarvest, setCompletingHarvest] = useState(false);
  const online = useOnlineStatus();
  const [batchTransitionOpen, setBatchTransitionOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [adoptDialogOpen, setAdoptDialogOpen] = useState(false);

  // Species/cultivar name resolution for entries table
  // Cultivar names + loaded species; the species name is derived in the render so it
  // follows the UI language (#2902).
  const [cultivarNames, setCultivarNames] = useState<Map<string, string>>(new Map());
  const [loadedSpecies, setLoadedSpecies] = useState<Map<string, Species>>(new Map());
  const speciesMap = useMemo(() => {
    const names = new Map(cultivarNames);
    for (const [sk, sp] of loadedSpecies) {
      names.set(sk, getLocalizedCommonName(sp, i18n.language) ?? sp.scientific_name);
    }
    return names;
  }, [cultivarNames, loadedSpecies, i18n.language]);
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
  const [removingPlan, setRemovingPlan] = useState(false);

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
  // The channels and dosages the server applies this week (#3016) — never recomputed client-side.
  const [activeChannels, setActiveChannels] = useState<ActiveChannel[] | null>(null);

  // Site list for edit dialog
  // Secondary reads that failed (location/tank, plants; plan/schedule/timeline) — shown with a retry
  // above the tabs instead of reading as "none" (#3037).
  const [sectionLoadError, setSectionLoadError] = useState(false);
  const [wateringLoadError, setWateringLoadError] = useState(false);
  // Which watering legs failed: the tab then shows neither "no plan assigned" with
  // its assign call to action nor "no schedule" in their place (#3037).
  const [planLoadFailed, setPlanLoadFailed] = useState(false);
  const [scheduleLoadFailed, setScheduleLoadFailed] = useState(false);
  const loadSites = useCallback((): Promise<Site[]> => siteApi.listAllSites(), []);
  const sitesLoad = useAsyncOptions(loadSites);
  const sitesList = sitesLoad.options;

  // Full species/cultivar data for details tab
  const [speciesDataForTab, setSpeciesDataForTab] = useState<Species | null>(null);
  const [cultivarDataForTab, setCultivarDataForTab] = useState<Cultivar | null>(null);

  // Phase sequence key for linking from phases tab
  const [phaseSequenceKey, setPhaseSequenceKey] = useState<string | null>(null);

  // Derived nutrient data via custom hook
  const nutrientData = useRunNutrientData(planEntries, phaseTimelines, run?.started_at, activeChannels);

  // Track dirty state for UnsavedChangesGuard (edit dialog has own form)
  const isDirty = false;

  // Latest-wins: a late answer for a previously selected key must not overwrite this one (#3014).
  const beginLoad = useAbortableLoad();

  const load = useCallback(async () => {
    if (!key) return;
    const ticket = beginLoad();
    const stale = () => !ticket.isCurrent();
    setLoading(true);
    setSectionLoadError(false);
    try {
      const r = await runApi.getPlantingRun(key);
      if (stale()) return;
      setRun(r);
      if (r.location_key) {
        try {
          const loc = await siteApi.getLocation(r.location_key);
          if (stale()) return;
          setSiteKeyFromLocation(loc.site_key);
          setLocationName(loc.name);
          if (loc.tank_key) {
            const tk = await tankApi.getTank(loc.tank_key);
            if (stale()) return;
            setResolvedTank({ key: tk.key, name: tk.name, volumeLiters: tk.volume_liters });
          } else {
            // Filtered by the server (#3015) instead of searching the tenant's whole tank list.
            const [match] = await tankApi.listAllTanksAtLocation(r.location_key);
            if (stale()) return;
            if (match) {
              setResolvedTank({ key: match.key, name: match.name, volumeLiters: match.volume_liters });
            } else {
              setResolvedTank(null);
            }
          }
        } catch (err) {
          if (stale()) return;
          captureHandledError(err, { source: 'PlantingRunDetailPage.location' });
          setResolvedTank(null);
          setLocationName('');
          // Never keep the previous run's site after a sibling switch.
          setSiteKeyFromLocation(null);
          setSectionLoadError(true);
        }
      } else {
        setResolvedTank(null);
        setLocationName('');
        setSiteKeyFromLocation(null);
      }
      const e = await runApi.listEntries(key);
      if (stale()) return;
      setEntries(e);
      const uniqueSpeciesKeys = [...new Set(e.map((entry) => entry.species_key))];
      const nameMap = new Map<string, string>();
      const speciesByKey = new Map<string, Species>();
      let firstSpecies: Species | null = null;
      let firstCultivar: Cultivar | null = null;
      await Promise.all(
        uniqueSpeciesKeys.map(async (sk) => {
          try {
            const sp = await speciesApi.getSpecies(sk);
            speciesByKey.set(sk, sp);
            // Store full species for the first entry (monoculture detail card)
            if (!firstSpecies && e.length > 0 && e[0].species_key === sk) {
              firstSpecies = sp;
            }
            for (const ent of e.filter((en) => en.species_key === sk && en.cultivar_key)) {
              try {
                const cv = await speciesApi.getCultivar(sk, ent.cultivar_key!);
                nameMap.set(ent.cultivar_key!, cv.name);
                // Store full cultivar for the first entry
                if (!firstCultivar && e.length > 0 && e[0].cultivar_key === ent.cultivar_key) {
                  firstCultivar = cv;
                }
              } catch (err) {
                // A cultivar name only labels the entry; the entry itself is listed.
                captureHandledError(err, { source: 'PlantingRunDetailPage.cultivar' });
              }
            }
          } catch (err) {
            // A species only labels the entry; the entry itself is listed.
            captureHandledError(err, { source: 'PlantingRunDetailPage.species' });
          }
        }),
      );
      if (stale()) return;
      setCultivarNames(nameMap);
      setLoadedSpecies(speciesByKey);
      setSpeciesDataForTab(firstSpecies);
      setCultivarDataForTab(firstCultivar);
      // Load phase sequence for the first species (monoculture)
      const primarySpeciesKey = e.length > 0 ? e[0].species_key : null;
      if (primarySpeciesKey) {
        phaseSequenceApi
          .getSpeciesPhaseSequence(primarySpeciesKey)
          .then((seq) => { if (!stale()) setPhaseSequenceKey(seq?.key ?? null); })
          .catch((err: unknown) => {
            // Only the link to the species' phase sequence is missing; the phases tab still renders.
            captureHandledError(err, { source: 'PlantingRunDetailPage.phaseSequence' });
            if (!stale()) setPhaseSequenceKey(null);
          });
      } else {
        setPhaseSequenceKey(null);
      }
      try {
        const p = await runApi.listRunPlants(key, true);
        if (stale()) return;
        setPlants(p);
      } catch (err) {
        // A run without plants answers with an empty list; a failure is not "no plants".
        if (stale()) return;
        captureHandledError(err, { source: 'PlantingRunDetailPage.plants' });
        setSectionLoadError(true);
      }
    } catch (err) {
      if (stale()) return;
      setError(errorKey(err, 'errors.loadFailed'));
    } finally {
      if (!stale()) setLoading(false);
    }
  }, [key, beginLoad]);

  useEffect(() => {
    load();
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

  const beginWateringLoad = useAbortableLoad();
  const loadWateringData = useCallback(async () => {
    if (!key) return;
    const ticket = beginWateringLoad();
    const stale = () => !ticket.isCurrent();
    setWateringLoading(true);
    setWateringLoadError(false);
    try {
      // Each leg degrades on its own so the others still render, but a failed leg is
      // reported and announced with a retry — a missing plan must not read as "no plan
      // assigned" (#3037).
      const failedLegs = new Set<string>();
      const degrade = <T,>(source: string, fallback: T) => (err: unknown): T => {
        captureHandledError(err, { source: `PlantingRunDetailPage.${source}` });
        failedLegs.add(source);
        return fallback;
      };
      const [planResult, calendar, timelines] = await Promise.all([
        runApi.getRunNutrientPlan(key).catch(degrade('nutrientPlan', { plan: null })),
        runApi.getWateringSchedule(key, 90).catch(degrade<WateringScheduleCalendarResponse | null>('wateringSchedule', null)),
        runApi.getPhaseTimeline(key).catch(degrade<SpeciesPhaseTimeline[]>('phaseTimeline', [])),
      ]);
      if (stale()) return;
      setWateringLoadError(failedLegs.size > 0);
      setPlanLoadFailed(failedLegs.has('nutrientPlan'));
      setScheduleLoadFailed(failedLegs.has('wateringSchedule'));
      setAssignedPlan(planResult.plan);
      setWateringCalendar(calendar);
      setPhaseTimelines(timelines);
      if (planResult.plan) {
        const planKey = (planResult.plan as { key?: string }).key ?? '';
        if (planKey) {
          const [fetchedEntries, ferts, channels] = await Promise.all([
            planApi.fetchPhaseEntries(planKey),
            // The complete catalogue (#1560); one leg of an imperative sequence
            // whose surrounding loading and error state already covers it.
            fertApi.fetchAllFertilizers(),
            runApi.getActiveChannels(key),
          ]);
          if (stale()) return;
          setPlanEntries(fetchedEntries);
          setFertilizers(ferts);
          setActiveChannels(channels);
        }
      } else {
        setPlanEntries([]);
        setFertilizers([]);
        setActiveChannels(null);
      }
    } catch (err) {
      if (stale()) return;
      // One cause, one message: the section banner announces it with a retry, no toast.
      captureHandledError(err, { source: 'PlantingRunDetailPage.wateringData' });
      setWateringLoadError(true);
    } finally {
      if (!stale()) setWateringLoading(false);
    }
  }, [key, beginWateringLoad]);

  // Load watering data for details tab (tab 0), phases tab (tab 2), and nutrient+watering tab (tab 3)
  useEffect(() => {
    if (tab === 0 || tab === 2 || tab === 3) {
      loadWateringData();
    }
  }, [tab, loadWateringData]);

  const onDelete = async () => {
    if (!key) return;
    setDeleting(true);
    try {
      await runApi.deletePlantingRun(key);
      notification.success(t('common.delete'));
      navigate('/durchlaeufe/planting-runs');
    } catch (err) {
      handleError(err);
    } finally {
      setDeleting(false);
    }
    setDeleteOpen(false);
  };

  const onCreatePlants = async () => {
    if (!key) return;
    setCreatingPlants(true);
    try {
      const result = await runApi.batchCreatePlants(key);
      notification.success(
        t('pages.plantingRuns.plantsCreated', { count: result.created_count }),
      );
      load();
    } catch (err) {
      handleError(err);
    } finally {
      setCreatingPlants(false);
    }
    setCreatePlantsOpen(false);
  };

  const onBatchRemove = async () => {
    if (!key) return;
    setBatchRemoving(true);
    try {
      const result = await runApi.batchRemove(key);
      notification.success(
        t('pages.plantingRuns.plantsRemoved', { count: result.removed_count }),
      );
      load();
    } catch (err) {
      handleError(err);
    } finally {
      setBatchRemoving(false);
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

  const onCompleteHarvest = async () => {
    if (!key) return;
    try {
      setCompletingHarvest(true);
      const result = await harvestApi.completeHarvestForRun(key);
      if (result.completed_count > 0) {
        notification.success(
          t('pages.plantingRuns.completeHarvestSuccess', {
            count: result.completed_count,
          }),
        );
      } else {
        notification.info(t('pages.plantingRuns.completeHarvestNoneActive'));
      }
      setCompleteHarvestOpen(false);
      load();
    } catch (err) {
      handleError(err);
    } finally {
      setCompletingHarvest(false);
    }
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
    setRemovingPlan(true);
    try {
      await runApi.removeRunNutrientPlan(key);
      notification.success(t('pages.wateringSchedule.removePlan'));
      setAssignedPlan(null);
      setWateringCalendar(null);
      loadWateringData();
    } catch (err) {
      handleError(err);
    } finally {
      setRemovingPlan(false);
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
    { id: 'cultivar', label: t('entities.cultivar'), render: (r) => r.cultivar_key ? (speciesMap.get(r.cultivar_key) ?? r.cultivar_key) : '—', searchValue: (r) => r.cultivar_key ? (speciesMap.get(r.cultivar_key) ?? '') : '' },
    { id: 'quantity', label: t('pages.plantingRuns.quantity'), render: (r) => r.quantity, align: 'right' },
    { id: 'idPrefix', label: t('pages.plantingRuns.idPrefix'), render: (r) => r.id_prefix },
    { id: 'spacing', label: t('pages.plantingRuns.spacing'), render: (r) => r.spacing_cm ? `${r.spacing_cm} cm` : '—', align: 'right' },
  ];

  const plantColumns: Column<PlantInRun>[] = [
    { id: 'instanceId', label: t('pages.plantInstances.instanceId'), render: (r) => r.instance_id },
    { id: 'plantName', label: t('pages.plantInstances.plantName'), render: (r) => {
      const name = getPlantDisplayName(r, i18n.language);
      return name === r.instance_id ? '—' : name;
    }, searchValue: (r) => getPlantDisplayName(r, i18n.language) },
    { id: 'currentPhase', label: t('pages.plantInstances.currentPhase'), render: (r) => r.current_phase ? <Chip label={r.current_phase} size="small" color="primary" /> : '—', searchValue: (r) => r.current_phase ?? '' },
    { id: 'plantedOn', label: t('pages.plantInstances.plantedOn'), render: (r) => r.planted_on },
    { id: 'removedOn', label: t('pages.plantInstances.removedOn'), render: (r) => r.removed_on ?? '—' },
    { id: 'detached', label: t('pages.plantingRuns.detached'), render: (r) => r.detached_at ? t('common.yes') : '—' },
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
  if (error) return <ErrorDisplay error={error} onRetry={() => void load()} />;

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
              {canDelete && (
                <Button
                  variant="outlined"
                  color="error"
                  startIcon={<DeleteIcon />}
                  onClick={() => setDeleteOpen(true)}
                  data-testid="delete-button"
                >
                  {t('common.delete')}
                </Button>
              )}
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
                {t('pages.plantingRuns.runTransition')}
              </Button>
              {/* UI-NFR-012 R-020a/R-020b: moving the run's plants into harvest is validated on the server. */}
              <RequiresConnectivity offline={!online}>
                <Button
                  variant="outlined"
                  color="warning"
                  startIcon={<AgricultureIcon />}
                  onClick={() => setCompleteHarvestOpen(true)}
                  disabled={completingHarvest || !online}
                  data-testid="complete-harvest-button"
                  sx={{ minHeight: 48 }}
                >
                  {t('pages.plantingRuns.completeHarvest')}
                </Button>
              </RequiresConnectivity>
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
      <Tabs
        value={tab}
        onChange={(_, v) => setTab(v)}
        sx={{ mb: 3 }}
        variant="scrollable"
        scrollButtons="auto"
        allowScrollButtonsMobile
        aria-label={run?.name ?? t('entities.plantingRun')}
      >
        <Tab id="tab-details" label={t('pages.plantingRuns.tabDetails')} />
        <Tab id="tab-plants" label={t('pages.plantingRuns.tabPlants')} />
        <Tab id="tab-phases" label={t('pages.plantingRuns.tabPhases')} data-testid="phases-tab" />
        <Tab id="tab-nutrient-watering" label={t('pages.plantingRuns.tabNutrientWatering')} data-testid="nutrient-plan-tab" />
        <Tab id="tab-activity-plan" label={t('pages.activityPlan.tabTitle')} data-testid="activity-plan-tab" />
      </Tabs>

      {(sectionLoadError || (wateringLoadError && (tab === 0 || tab === 2 || tab === 3))) && (
        <OptionsLoadError
          messageKey="errors.loadFailed"
          onRetry={() => {
            if (sectionLoadError) void load();
            if (wateringLoadError) void loadWateringData();
          }}
          data-testid="run-section-load-error"
        />
      )}

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
          phaseTimelines={phaseTimelines}
          speciesData={speciesDataForTab}
          cultivarData={cultivarDataForTab}
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
          {phaseSequenceKey && (
            <Button
              component={RouterLink}
              to={`/phasen/ablaeufe/${phaseSequenceKey}`}
              variant="outlined"
              size="small"
              startIcon={<AccountTreeIcon />}
              sx={{ mb: 2 }}
            >
              {t('pages.phaseSequences.viewPhaseSequence')}
            </Button>
          )}
          {/* Prominent phase timeline */}
          {phaseTimelines.length > 0 && phaseTimelines[0].phases.length > 0 && (
            <Box sx={{ mb: 3, p: { xs: 1.5, sm: 2 }, bgcolor: 'background.paper', borderRadius: 1, border: 1, borderColor: 'divider' }}>
              <PhaseKamiTimeline phases={phaseTimelines[0].phases} speciesName={phaseTimelines[0].species_name} />
            </Box>
          )}
          <RunPhaseEditor
            runKey={key}
            isActive={run?.status === 'active' || run?.status === 'harvesting'}
            onPhaseDatesChanged={loadWateringData}
          />

          {/* Plant instances grouped by current phase */}
          {plants.length > 0 && (() => {
            const grouped = plants.reduce<Record<string, PlantInRun[]>>((acc, p) => {
              const phase = p.current_phase || t('common.unknown');
              if (!acc[phase]) acc[phase] = [];
              acc[phase].push(p);
              return acc;
            }, {});
            const phaseOrder = phaseTimelines.length > 0
              ? phaseTimelines[0].phases.map((ph) => ph.display_name || ph.phase_name)
              : [];
            const sortedPhases = Object.keys(grouped).sort((a, b) => {
              const ia = phaseOrder.indexOf(a);
              const ib = phaseOrder.indexOf(b);
              if (ia === -1 && ib === -1) return compareText(a, b);
              if (ia === -1) return 1;
              if (ib === -1) return -1;
              return ia - ib;
            });
            return (
              <Box sx={{ mt: 3 }}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  {t('pages.plantingRuns.plantsPerPhase')}
                </Typography>
                {sortedPhases.map((phase) => (
                  <Accordion key={phase} defaultExpanded disableGutters>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Chip
                          label={phase}
                          size="small"
                          color="primary"
                          variant="outlined"
                        />
                        <Typography variant="body2" color="text.secondary">
                          ({grouped[phase].length})
                        </Typography>
                      </Box>
                    </AccordionSummary>
                    <AccordionDetails sx={{ p: 0 }}>
                      <List dense disablePadding>
                        {grouped[phase].map((p) => (
                          <ListItemButton
                            key={p.key}
                            component={RouterLink}
                            to={`/pflanzen/plant-instances/${p.key}`}
                            data-testid={`phase-plant-${p.key}`}
                          >
                            <ListItemText
                              primary={getPlantDisplayName(p, i18n.language)}
                              secondary={[
                                getPlantDisplayName(p, i18n.language) === p.instance_id ? null : p.instance_id,
                                p.planted_on,
                                p.detached_at ? t('pages.plantingRuns.detached') : null,
                                p.removed_on ? t('pages.plantInstances.removedOn') + ': ' + p.removed_on : null,
                              ].filter(Boolean).join(' · ')}
                            />
                          </ListItemButton>
                        ))}
                      </List>
                    </AccordionDetails>
                  </Accordion>
                ))}
              </Box>
            );
          })()}
        </Box>
      )}

      {/* Tab 3: Nutrient Plan + Watering (merged) */}
      {tab === 3 && (
        <PlantingRunNutrientWateringTab
          runStatus={run?.status}
          wateringLoading={wateringLoading}
          assignedPlan={assignedPlan}
          planLoadFailed={planLoadFailed}
          scheduleLoadFailed={scheduleLoadFailed}
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
      {tab === 4 && run && (
        <ActivityPlanTab runKey={key!} speciesKey={entries[0]?.species_key ?? plants[0]?.species_key ?? ''} />
      )}

      {/* ── Dialogs ── */}

      {run && (
        <PlantingRunEditDialog
          open={editDialogOpen}
          run={run}
          sitesList={sitesList}
          sitesLoadError={sitesLoad.error}
          onRetrySites={sitesLoad.reload}
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
        loading={deleting}
      />

      <ConfirmDialog
        open={createPlantsOpen}
        title={t('pages.plantingRuns.createPlants')}
        message={t('pages.plantingRuns.createPlantsConfirm', {
          count: run?.planned_quantity ?? 0,
        })}
        onConfirm={onCreatePlants}
        onCancel={() => setCreatePlantsOpen(false)}
        loading={creatingPlants}
      />

      <ConfirmDialog
        open={batchRemoveOpen}
        title={t('pages.plantingRuns.batchRemove')}
        message={t('pages.plantingRuns.batchRemoveConfirm')}
        onConfirm={onBatchRemove}
        onCancel={() => setBatchRemoveOpen(false)}
        destructive
        loading={batchRemoving}
      />

      <Dialog fullScreen={fullScreen} open={endRunOpen}
        onClose={() => setEndRunOpen(false)}
        maxWidth="xs"
        fullWidth
        data-testid="end-run-dialog"
        aria-labelledby="end-run-dialog-title"
      >
        <DialogTitle id="end-run-dialog-title">{t('pages.plantingRuns.endRun')}</DialogTitle>
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
        open={completeHarvestOpen}
        title={t('pages.plantingRuns.completeHarvestTitle')}
        message={`${t('pages.plantingRuns.completeHarvestDesc')}\n\n${t('pages.plantingRuns.completeHarvestConfirm', {
          count: plants.filter((p) => !p.removed_on && !p.detached_at).length,
        })}`}
        confirmLabel={t('pages.plantingRuns.completeHarvestConfirmButton')}
        onConfirm={onCompleteHarvest}
        onCancel={() => setCompleteHarvestOpen(false)}
        destructive
        loading={completingHarvest}
      />

      <ConfirmDialog
        open={removePlanOpen}
        title={t('pages.nutrientPlans.removePlan')}
        message={t('common.deleteConfirm', { name: (assignedPlan as { name?: string })?.name ?? '' })}
        onConfirm={onRemovePlan}
        onCancel={() => setRemovePlanOpen(false)}
        destructive
        loading={removingPlan}
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
