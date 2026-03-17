import { useEffect, useMemo, useRef, useState } from 'react';
import { useTabUrl } from '@/hooks/useTabUrl';
import { useParams, useNavigate, Link as RouterLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Divider from '@mui/material/Divider';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Alert from '@mui/material/Alert';
import Link from '@mui/material/Link';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import RemoveCircleIcon from '@mui/icons-material/RemoveCircle';
import SwapHorizIcon from '@mui/icons-material/SwapHoriz';
import LabelIcon from '@mui/icons-material/Label';
import ScienceIcon from '@mui/icons-material/Science';
import TodayIcon from '@mui/icons-material/Today';
import DeleteIcon from '@mui/icons-material/Delete';
import OpacityIcon from '@mui/icons-material/Opacity';
import AddIcon from '@mui/icons-material/Add';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import RepeatIcon from '@mui/icons-material/Repeat';
import TaskAltIcon from '@mui/icons-material/TaskAlt';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import HourglassEmptyIcon from '@mui/icons-material/HourglassEmpty';
import PendingIcon from '@mui/icons-material/Pending';
import { useForm, useWatch } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import EmptyState from '@/components/common/EmptyState';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import DataTable from '@/components/common/DataTable';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormActions from '@/components/form/FormActions';
import FormRow from '@/components/form/FormRow';
import LocationTreeSelect from '@/components/form/LocationTreeSelect';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import PhaseTransitionDialog from './PhaseTransitionDialog';
import PlantTagDialog from './PlantTagDialog';
import PlantPhaseTimeline from './PlantPhaseTimeline';
import ProfilesSection from './ProfilesSection';
import PhaseHistoryTable from '@/pages/durchlaeufe/PhaseHistoryTable';
import CareConfirmDialog from '@/pages/pflege/components/CareConfirmDialog';
import CareProfileEditDialog from '@/pages/pflege/components/CareProfileEditDialog';
import type { DosagePreset } from '@/pages/pflege/components/CareConfirmDialog';
import WateringLogCreateDialog from '@/pages/giessprotokoll/WateringLogCreateDialog';
import type { ChannelPreset } from '@/pages/giessprotokoll/WateringLogCreateDialog';
import DeliveryChannelAccordion from '@/pages/duengung/DeliveryChannelAccordion';
import PhaseGanttChart from '@/pages/duengung/PhaseGanttChart';
import ActivityPlanTab from '@/pages/durchlaeufe/ActivityPlanTab';
import PhaseDetailGantt from '@/pages/duengung/PhaseDetailGantt';
import { computeCurrentWeek } from '@/utils/weekCalculation';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import { useWateringVolumeSuggestion } from '@/hooks/useWateringVolumeSuggestion';
import { useTableLocalState } from '@/hooks/useTableState';
import * as plantApi from '@/api/endpoints/plantInstances';
import * as phasesApi from '@/api/endpoints/phases';
import * as speciesApi from '@/api/endpoints/species';
import * as planApi from '@/api/endpoints/nutrient-plans';
import * as fertApi from '@/api/endpoints/fertilizers';
import * as wateringLogApi from '@/api/endpoints/watering-logs';
import * as sitesApi from '@/api/endpoints/sites';
import * as careApi from '@/api/endpoints/careReminders';
import * as taskApi from '@/api/endpoints/tasks';
import * as substrateApi from '@/api/endpoints/substrates';
import type { ConfirmReminderOptions } from '@/api/endpoints/careReminders';
import type { PlantInstance, CurrentPhaseResponse, PhaseHistoryEntry, Cultivar, NutrientPlan, NutrientPlanPhaseEntry, Fertilizer, WateringLog, GrowthPhase, Species, Site, Location as SiteLocation, Slot, CareConfirmation, Substrate, SubstrateType, TaskItem } from '@/api/types';
import SubstrateSelectField from '@/components/form/SubstrateSelectField';

const editSchema = z.object({
  plant_name: z.string().nullable(),
  cultivar_key: z.string().nullable(),
  site_key: z.string().nullable(),
  location_key: z.string().nullable(),
  slot_key: z.string().nullable(),
  substrate_key: z.string().nullable(),
  planted_on: z.string().min(1),
  container_volume_liters: z.number().min(0.1).max(500).nullable(),
});

type EditFormData = z.infer<typeof editSchema>;

const assignSchema = z.object({
  plan_key: z.string().min(1),
  assigned_by: z.string().min(1),
});

type AssignFormData = z.infer<typeof assignSchema>;

export default function PlantInstanceDetailPage() {
  const { key } = useParams<{ key: string }>();
  const { t, i18n } = useTranslation();
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
  const [tagDialogOpen, setTagDialogOpen] = useState(false);
  const [tab, setTab] = useTabUrl(['info', 'phases', 'nutrient-plan', 'watering-log', 'care', 'activity-plan', 'tasks', 'edit']);
  const [saving, setSaving] = useState(false);
  const [species, setSpecies] = useState<Species | null>(null);
  const [cultivarList, setCultivarList] = useState<Cultivar[]>([]);

  // Watering logs state (replaces feeding events)
  const [wateringLogs, setWateringLogs] = useState<WateringLog[]>([]);
  const [wateringLogCreateOpen, setWateringLogCreateOpen] = useState(false);
  const [wateringLogChannelPreset, setWateringLogChannelPreset] = useState<ChannelPreset | undefined>(undefined);
  const wateringLogTableState = useTableLocalState({ defaultSort: { column: 'loggedAt', direction: 'desc' } });

  // Nutrient plan assignment state
  const [assignedPlan, setAssignedPlan] = useState<NutrientPlan | null>(null);
  const [availablePlans, setAvailablePlans] = useState<NutrientPlan[]>([]);
  const [assignDialogOpen, setAssignDialogOpen] = useState(false);
  const [removePlanOpen, setRemovePlanOpen] = useState(false);
  const [assignSaving, setAssignSaving] = useState(false);

  // Gantt chart state
  const [planEntries, setPlanEntries] = useState<NutrientPlanPhaseEntry[]>([]);
  const [fertilizers, setFertilizers] = useState<Fertilizer[]>([]);
  const [growthPhases, setGrowthPhases] = useState<GrowthPhase[]>([]);
  const [lifecycleKey, setLifecycleKey] = useState<string | null>(null);

  // Slot picker cascade state
  const [sitesList, setSitesList] = useState<Site[]>([]);
  const [slotsList, setSlotsList] = useState<Slot[]>([]);

  // Substrate selector state
  const [substratesList, setSubstratesList] = useState<Substrate[]>([]);

  // Assigned location display (info tab)
  const [assignedSlot, setAssignedSlot] = useState<Slot | null>(null);
  const [assignedLocation, setAssignedLocation] = useState<SiteLocation | null>(null);

  // Planting run references
  const [plantRuns, setPlantRuns] = useState<plantApi.PlantRunRef[]>([]);

  // Care profile state
  const [careProfile, setCareProfile] = useState<import('@/api/types').CareProfile | null>(null);
  const [careProfileEditOpen, setCareProfileEditOpen] = useState(false);

  // Watering state
  const [lastWatering, setLastWatering] = useState<CareConfirmation | null>(null);
  const [confirmingWatering, setConfirmingWatering] = useState(false);
  const [wateringDialogOpen, setWateringDialogOpen] = useState(false);
  const [nextWateringTask, setNextWateringTask] = useState<TaskItem | null>(null);
  const [plantTasks, setPlantTasks] = useState<TaskItem[]>([]);
  const [plantTasksLoading, setPlantTasksLoading] = useState(false);
  const [completingTaskKey, setCompletingTaskKey] = useState<string | null>(null);
  const taskTableState = useTableLocalState({ defaultSort: { column: 'due_date', direction: 'asc' } });

  const {
    control,
    handleSubmit,
    reset,
    setValue,
    formState: { isDirty },
  } = useForm<EditFormData>({
    resolver: zodResolver(editSchema),
    defaultValues: {
      plant_name: null,
      cultivar_key: null,
      site_key: null,
      location_key: null,
      slot_key: null,
      substrate_key: null,
      planted_on: '',
      container_volume_liters: null,
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

  const editSiteKey = useWatch({ control, name: 'site_key' });
  const editLocationKey = useWatch({ control, name: 'location_key' });

  const load = async () => {
    if (!key) return;
    setLoading(true);
    try {
      const p = await plantApi.getPlantInstance(key);
      setPlant(p);
      let loadedSpecies: Species | null = null;
      if (p.species_key) {
        try {
          loadedSpecies = await speciesApi.getSpecies(p.species_key);
          setSpecies(loadedSpecies);
        } catch {
          setSpecies(null);
        }
        speciesApi.listCultivars(p.species_key).then(setCultivarList).catch(() => setCultivarList([]));
      }
      // Resolve location → site for form and info tab display
      let resolvedSiteKey: string | null = null;
      let resolvedLocationKey: string | null = p.location_key;
      // If no location_key but slot exists, reverse-resolve from slot
      if (!resolvedLocationKey && p.slot_key) {
        try {
          const slot = await sitesApi.getSlot(p.slot_key);
          resolvedLocationKey = slot.location_key;
        } catch { /* ignore */ }
      }
      // Resolve location → site + display
      if (resolvedLocationKey) {
        try {
          const loc = await sitesApi.getLocation(resolvedLocationKey);
          setAssignedLocation(loc);
          resolvedSiteKey = loc.site_key;
        } catch {
          setAssignedLocation(null);
        }
        sitesApi.listSlots(resolvedLocationKey).then(setSlotsList).catch(() => setSlotsList([]));
      } else {
        setAssignedLocation(null);
      }
      // Resolve slot display
      if (p.slot_key) {
        sitesApi.getSlot(p.slot_key).then(setAssignedSlot).catch(() => setAssignedSlot(null));
      } else {
        setAssignedSlot(null);
      }
      skipLocationReset.current = true;
      skipSlotReset.current = true;
      reset({
        plant_name: p.plant_name,
        cultivar_key: p.cultivar_key,
        site_key: resolvedSiteKey,
        location_key: resolvedLocationKey,
        slot_key: p.slot_key,
        substrate_key: p.substrate_key || (p.substrate_type_override ? `_type_${p.substrate_type_override}` : null),
        planted_on: p.planted_on,
        container_volume_liters: p.container_volume_liters,
      });
      // Load planting runs for this plant
      plantApi.getPlantRuns(key).then(setPlantRuns).catch(() => setPlantRuns([]));
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
      // Load last watering confirmation
      try {
        const hist = await careApi.getHistory(key, 'watering');
        setLastWatering(hist.length > 0 ? hist[0] : null);
      } catch {
        setLastWatering(null);
      }
      // Load next pending watering task
      try {
        const tasks = await taskApi.listTasks(0, 50, { plant_key: key, category: 'care_reminder', status: 'pending' });
        const wateringTask = tasks.find((t) => t.name.endsWith('\u2014 watering'));
        setNextWateringTask(wateringTask ?? null);
      } catch {
        setNextWateringTask(null);
      }
      // Load watering log history
      try {
        const wl = await wateringLogApi.getPlantWateringHistory(key);
        setWateringLogs(wl);
      } catch {
        // May not have any watering logs
      }
      // Load lifecycle growth phases for projected timeline
      try {
        const lc = await phasesApi.getLifecycleConfig(p.species_key);
        setLifecycleKey(lc.key);
        const gp = await phasesApi.listGrowthPhases(lc.key);
        setGrowthPhases(gp.sort((a, b) => a.sequence_order - b.sequence_order));
      } catch {
        setGrowthPhases([]);
      }
      // Load assigned nutrient plan + Gantt data
      // Falls back to species' default nutrient plan if no plant-specific plan assigned
      let ap = await planApi.getPlantPlan(key);
      if (!ap && loadedSpecies?.default_nutrient_plan_key) {
        try {
          ap = await planApi.fetchNutrientPlan(loadedSpecies.default_nutrient_plan_key);
        } catch {
          // Species default plan may have been deleted
        }
      }
      setAssignedPlan(ap);
      if (ap) {
        const [pe, f] = await Promise.all([
          planApi.fetchPhaseEntries(ap.key),
          fertApi.fetchFertilizers(0, 200),
        ]);
        setPlanEntries(pe);
        setFertilizers(f);
      } else {
        setPlanEntries([]);
        setFertilizers([]);
      }
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [key]); // eslint-disable-line react-hooks/exhaustive-deps

  // Load care profile when switching to Care tab
  useEffect(() => {
    if (tab === 4 && key) {
      careApi.getOrCreateProfile(key, species?.scientific_name)
        .then(setCareProfile)
        .catch(() => setCareProfile(null));
    }
  }, [tab, key, species?.scientific_name]);

  // Load all tasks when switching to Tasks tab
  useEffect(() => {
    if (tab === 6 && key && plantTasks.length === 0) {
      setPlantTasksLoading(true);
      taskApi.listTasks(0, 500, { plant_key: key })
        .then(setPlantTasks)
        .catch(() => setPlantTasks([]))
        .finally(() => setPlantTasksLoading(false));
    }
  }, [tab, key]); // eslint-disable-line react-hooks/exhaustive-deps

  // Load sites + substrates when switching to Edit tab
  useEffect(() => {
    if (tab === 7) {
      sitesApi.listSites(0, 200).then(setSitesList).catch(() => setSitesList([]));
      substrateApi.listSubstrates(0, 200).then(setSubstratesList).catch(() => setSubstratesList([]));
    }
  }, [tab]);

  // Clear location when site changes (except initial load)
  const skipLocationReset = useRef(true);
  useEffect(() => {
    if (skipLocationReset.current) {
      skipLocationReset.current = false;
      return;
    }
    setValue('location_key', null);
    setSlotsList([]);
    setValue('slot_key', null, { shouldDirty: true });
  }, [editSiteKey, setValue]);

  // Load slots when location changes (except initial load)
  const skipSlotReset = useRef(true);
  useEffect(() => {
    if (skipSlotReset.current) {
      skipSlotReset.current = false;
      return;
    }
    setSlotsList([]);
    setValue('slot_key', null, { shouldDirty: true });
    if (editLocationKey) {
      sitesApi.listSlots(editLocationKey).then(setSlotsList).catch(() => setSlotsList([]));
    }
  }, [editLocationKey, setValue]);

  const handleConfirmWatering = async (options?: ConfirmReminderOptions) => {
    if (!key) return;
    try {
      setConfirmingWatering(true);
      const confirmation = await careApi.confirmReminder(key, 'watering', options);
      setLastWatering(confirmation);
      setWateringDialogOpen(false);
      notification.success(t('pages.plantInstances.wateringConfirmed'));
      // Refresh next watering task (confirming creates a new one)
      try {
        const tasks = await taskApi.listTasks(0, 50, { plant_key: key, category: 'care_reminder', status: 'pending' });
        const wt = tasks.find((t) => t.name.endsWith('\u2014 watering'));
        setNextWateringTask(wt ?? null);
      } catch {
        setNextWateringTask(null);
      }
    } catch (err) {
      handleError(err);
    } finally {
      setConfirmingWatering(false);
    }
  };

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

  const handleQuickCompleteTask = async (taskKey: string, event: React.MouseEvent) => {
    event.stopPropagation();
    try {
      setCompletingTaskKey(taskKey);
      await taskApi.completeTask(taskKey, {});
      setPlantTasks((prev) => prev.map((t) => t.key === taskKey ? { ...t, status: 'completed' } : t));
      notification.success(t('pages.plantInstances.taskCompleted'));
    } catch (err) {
      handleError(err);
    } finally {
      setCompletingTaskKey(null);
    }
  };

  const onEditSubmit = async (data: EditFormData) => {
    if (!key || !plant) return;
    try {
      setSaving(true);
      const { site_key: _, substrate_key: rawSubstrateKey, ...payload } = data; // eslint-disable-line @typescript-eslint/no-unused-vars
      // Type-only fallback keys start with '_type_' — don't send as substrate_key
      const isTypeOnly = rawSubstrateKey?.startsWith('_type_');
      const substrateKey = isTypeOnly ? null : (rawSubstrateKey || null);
      const selectedSubstrate = substrateKey ? substratesList.find((s) => s.key === substrateKey) : null;
      const typeOverride = isTypeOnly
        ? rawSubstrateKey!.replace('_type_', '') as SubstrateType
        : (selectedSubstrate?.type ?? null);
      await plantApi.updatePlantInstance(key, {
        instance_id: plant.instance_id,
        species_key: plant.species_key,
        ...payload,
        location_key: payload.location_key || null,
        slot_key: payload.slot_key || null,
        substrate_key: substrateKey,
        substrate_type_override: typeOverride,
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

  // Derive actual current phase from phase history (more reliable than plant document)
  const actualPhase = useMemo(() => {
    const active = history.find((h) => h.exited_at == null);
    if (active) return { name: active.phase_name, startedAt: active.entered_at };
    // Fallback to plant document
    if (plant?.current_phase) return { name: plant.current_phase, startedAt: plant.current_phase_started_at ?? null };
    return null;
  }, [history, plant?.current_phase, plant?.current_phase_started_at]);

  const currentWeek = useMemo(() => {
    // Phase-based calculation: weeks since phase transition + plan entry's week_start
    if (actualPhase?.startedAt && planEntries.length > 0) {
      const phaseStart = new Date(actualPhase.startedAt);
      if (!isNaN(phaseStart.getTime())) {
        const now = new Date();
        now.setHours(0, 0, 0, 0);
        phaseStart.setHours(0, 0, 0, 0);
        const diffMs = now.getTime() - phaseStart.getTime();
        if (diffMs >= 0) {
          const weeksInPhase = Math.floor(diffMs / (7 * 24 * 60 * 60 * 1000)) + 1;
          const sorted = [...planEntries].sort((a, b) => a.sequence_order - b.sequence_order);
          const phaseEntry = sorted.find((e) => e.phase_name === actualPhase.name);
          if (phaseEntry) {
            return phaseEntry.week_start + weeksInPhase - 1;
          }
        }
      }
    }
    // Fallback: weeks since planting
    return plant?.planted_on ? computeCurrentWeek(plant.planted_on) : undefined;
  }, [plant?.planted_on, actualPhase, planEntries]);

  const monthName = (m: number) =>
    new Date(2024, m - 1).toLocaleString(i18n.language, { month: 'short' });

  const frostChipColor = (sensitivity: string | null): 'success' | 'warning' | 'error' | 'default' => {
    if (!sensitivity) return 'default';
    if (sensitivity === 'hardy' || sensitivity === 'very_hardy') return 'success';
    if (sensitivity === 'moderate') return 'warning';
    if (sensitivity === 'sensitive') return 'error';
    return 'default';
  };

  const assignedCultivar = useMemo(
    () => plant?.cultivar_key ? cultivarList.find((c) => c.key === plant.cultivar_key) ?? null : null,
    [plant?.cultivar_key, cultivarList],
  );

  // Current growth phase definition (from lifecycle config)
  const currentGrowthPhase = useMemo(
    () => actualPhase?.name ? growthPhases.find((g) => g.name === actualPhase.name) ?? null : null,
    [actualPhase?.name, growthPhases],
  );

  // Effective watering interval for current phase (cultivar override > phase default)
  const effectiveWateringInterval = useMemo(() => {
    if (!currentGrowthPhase) return null;
    const cultivarOverride = assignedCultivar?.phase_watering_overrides?.[currentGrowthPhase.name];
    if (cultivarOverride != null) return { value: cultivarOverride, source: 'cultivar' as const };
    if (currentGrowthPhase.watering_interval_days != null) return { value: currentGrowthPhase.watering_interval_days, source: 'phase' as const };
    return null;
  }, [currentGrowthPhase, assignedCultivar]);

  // Active nutrient plan phase entry for the current week (handles perennial cycle restarts)
  const activePhaseEntry = useMemo(() => {
    if (!assignedPlan || planEntries.length === 0 || currentWeek == null) return null;
    const sorted = [...planEntries].sort((a, b) => a.sequence_order - b.sequence_order);

    const currentPhaseName = actualPhase?.name;

    // 1. Direct match: phase name + week range
    const byPhase = sorted.find(
      (e) => e.phase_name === currentPhaseName && currentWeek >= e.week_start && currentWeek <= e.week_end,
    );
    if (byPhase) return byPhase;

    // 2. Direct match: week range only
    const byWeek = sorted.find((e) => currentWeek >= e.week_start && currentWeek <= e.week_end);
    if (byWeek) return byWeek;

    // 3. Cycle restart for perennial plans
    const restartSeq = assignedPlan.cycle_restart_from_sequence;
    if (restartSeq == null) return null;

    const recurring = sorted.filter((e) => e.sequence_order >= restartSeq);
    if (recurring.length === 0) return null;

    const cycleStart = recurring[0].week_start;
    const cycleEnd = recurring[recurring.length - 1].week_end;
    const cycleLen = cycleEnd - cycleStart + 1;
    if (cycleLen <= 0 || currentWeek <= cycleEnd) return null;

    const offset = (currentWeek - cycleEnd - 1) % cycleLen;
    const effectiveWeek = cycleStart + offset;

    const byPhaseCycle = recurring.find(
      (e) => e.phase_name === currentPhaseName && effectiveWeek >= e.week_start && effectiveWeek <= e.week_end,
    );
    if (byPhaseCycle) return byPhaseCycle;

    return recurring.find((e) => effectiveWeek >= e.week_start && effectiveWeek <= e.week_end) ?? null;
  }, [assignedPlan, planEntries, currentWeek, actualPhase?.name]);

  // For perennial plans: compute cycle metadata + normalized Gantt data
  const perennialCycleInfo = useMemo(() => {
    const restartSeq = assignedPlan?.cycle_restart_from_sequence;
    if (restartSeq == null || planEntries.length === 0) return null;

    const sorted = [...planEntries].sort((a, b) => a.sequence_order - b.sequence_order);
    const oneTime = sorted.filter((e) => e.sequence_order < restartSeq);
    const recurring = sorted.filter((e) => e.sequence_order >= restartSeq);
    if (recurring.length === 0) return null;

    const cycleStart = recurring[0].week_start;
    const cycleEnd = recurring[recurring.length - 1].week_end;
    const cycleLen = cycleEnd - cycleStart + 1;

    // Compute cycle number and mapped week
    let cycleNumber = 1;
    let mappedWeek: number | undefined = currentWeek;
    if (currentWeek != null) {
      if (currentWeek < cycleStart) {
        cycleNumber = 0; // still in one-time entries
        mappedWeek = undefined;
      } else if (currentWeek <= cycleEnd) {
        cycleNumber = 1;
        mappedWeek = currentWeek - cycleStart + 1;
      } else if (cycleLen > 0) {
        const pastEnd = currentWeek - cycleEnd;
        cycleNumber = Math.floor((pastEnd - 1) / cycleLen) + 2;
        const offset = (pastEnd - 1) % cycleLen;
        mappedWeek = offset + 1;
      }
    }

    return {
      oneTimeEntries: oneTime,
      recurringEntries: recurring,
      cycleStart,
      cycleEnd,
      cycleLen,
      cycleNumber,
      mappedWeek,
    };
  }, [assignedPlan, planEntries, currentWeek]);

  // Gantt data: for perennial plans show cycle view, for linear plans show everything
  // Appends a "next cycle preview" so users see fertilization resumes after dormancy
  const ganttCycleData = useMemo(() => {
    if (!perennialCycleInfo) {
      return { entries: planEntries, currentWeek };
    }

    const { recurringEntries, cycleStart, cycleLen, mappedWeek } = perennialCycleInfo;

    // Normalize entries so cycle starts at week 1
    const normalizedEntries = recurringEntries.map((e) => ({
      ...e,
      week_start: e.week_start - cycleStart + 1,
      week_end: e.week_end - cycleStart + 1,
    }));

    // Append next-cycle preview: duplicate recurring entries shifted by cycleLen
    const previewEntries = recurringEntries.map((e) => ({
      ...e,
      key: `${e.key}_preview`,
      week_start: e.week_start - cycleStart + 1 + cycleLen,
      week_end: e.week_end - cycleStart + 1 + cycleLen,
    }));

    return {
      entries: [...normalizedEntries, ...previewEntries] as typeof planEntries,
      currentWeek: mappedWeek,
    };
  }, [perennialCycleInfo, planEntries, currentWeek]);

  // Current ISO week for the seasonal calendar Gantt
  const currentIsoWeek = useMemo(() => {
    const now = new Date();
    const jan4 = new Date(now.getFullYear(), 0, 4);
    const dayOfYear = Math.floor((now.getTime() - new Date(now.getFullYear(), 0, 1).getTime()) / 86400000) + 1;
    const jan4DayOfWeek = jan4.getDay() || 7;
    return Math.ceil((dayOfYear + jan4DayOfWeek - 1) / 7);
  }, []);

  // Map recurring entries to 52-week calendar year with wrapping for month-based display
  const calendarSeasonalEntries = useMemo(() => {
    if (!perennialCycleInfo) return [];
    const { recurringEntries } = perennialCycleInfo;
    if (recurringEntries.length === 0) return [];

    const cycleStart = recurringEntries[0].week_start;
    const cycleEnd = recurringEntries[recurringEntries.length - 1].week_end;
    const cycleLen = cycleEnd - cycleStart + 1;

    if (cycleLen <= 52 && cycleStart <= 52 && cycleEnd <= 52) {
      return recurringEntries;
    }

    const result: typeof recurringEntries = [];
    for (const e of recurringEntries) {
      if (e.week_end <= 52) {
        result.push(e);
      } else if (e.week_start <= 52) {
        // Crosses year boundary — keep as single entry (week_end > 52)
        result.push(e);
      } else {
        result.push({ ...e, week_start: e.week_start - 52, week_end: e.week_end - 52 });
      }
    }
    return result.sort((a, b) => a.week_start - b.week_start);
  }, [perennialCycleInfo]);

  // Resolve dosage presets from active phase entry for the confirm dialog
  const dosagePresets = useMemo((): { dosages: DosagePreset[]; targetEc?: number; targetPh?: number } | null => {
    if (!activePhaseEntry) return null;
    const dosages: DosagePreset[] = [];
    let targetEc: number | undefined;
    let targetPh: number | undefined;
    for (const channel of activePhaseEntry.delivery_channels) {
      if (!channel.enabled) continue;
      if (channel.target_ec_ms != null && targetEc == null) targetEc = channel.target_ec_ms;
      if (channel.target_ph != null && targetPh == null) targetPh = channel.target_ph;
      for (const d of channel.fertilizer_dosages) {
        if (!d.optional) {
          dosages.push({ fertilizer_key: d.fertilizer_key, ml_per_liter: d.ml_per_liter });
        }
      }
    }
    return dosages.length > 0 ? { dosages, targetEc, targetPh } : null;
  }, [activePhaseEntry]);

  // Recommended watering volume from backend (phase + species + substrate + container)
  const { suggestion: wateringVolume } = useWateringVolumeSuggestion(key);

  // Helper: format a due date as a relative label
  const formatRelativeDueDate = (dueDate: string | null): string => {
    if (!dueDate) return '\u2014';
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const due = new Date(dueDate);
    due.setHours(0, 0, 0, 0);
    const diffDays = Math.round((due.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
    if (diffDays === 0) return t('pages.plantInstances.taskDueDateToday');
    if (diffDays === 1) return t('pages.plantInstances.taskDueDateTomorrow');
    if (diffDays > 1) return t('pages.plantInstances.taskDueDateInDays', { count: diffDays });
    if (diffDays === -1) return t('pages.plantInstances.taskDueDateOverdueToday');
    return t('pages.plantInstances.taskDueDateOverdue', { count: Math.abs(diffDays) });
  };

  // Split tasks into active (pending/in_progress) and archived (completed/skipped/cancelled)
  const ACTIVE_STATUSES = new Set(['pending', 'in_progress']);
  const activeTasks = plantTasks
    .filter((t) => ACTIVE_STATUSES.has(t.status))
    .sort((a, b) => {
      // in_progress before pending
      const statusOrder: Record<string, number> = { in_progress: 0, pending: 1 };
      const sA = statusOrder[a.status] ?? 2;
      const sB = statusOrder[b.status] ?? 2;
      if (sA !== sB) return sA - sB;
      // then by due date ascending (null last)
      if (!a.due_date && !b.due_date) return 0;
      if (!a.due_date) return 1;
      if (!b.due_date) return -1;
      return new Date(a.due_date).getTime() - new Date(b.due_date).getTime();
    });
  const archivedTasks = plantTasks.filter((t) => !ACTIVE_STATUSES.has(t.status));

  // Count overdue active tasks (due date in the past)
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const overdueCount = activeTasks.filter(
    (t) => t.due_date && new Date(t.due_date) < today,
  ).length;

  // Status chip color mapping
  const taskStatusColor = (status: string): 'success' | 'warning' | 'info' | 'error' | 'default' => {
    if (status === 'completed') return 'success';
    if (status === 'in_progress') return 'info';
    if (status === 'pending') return 'warning';
    if (status === 'cancelled' || status === 'skipped') return 'default';
    return 'default';
  };

  // Status icon mapping
  const TaskStatusIcon = ({ status }: { status: string }) => {
    if (status === 'completed') return <TaskAltIcon fontSize="small" color="success" />;
    if (status === 'in_progress') return <HourglassEmptyIcon fontSize="small" color="info" />;
    if (status === 'pending') return <PendingIcon fontSize="small" color="warning" />;
    return null;
  };

  if (loading) return <LoadingSkeleton variant="form" />;
  if (error) return <ErrorDisplay error={error} onRetry={() => navigate(-1)} />;

  return (
    <Box data-testid="plant-instance-detail-page">
      <UnsavedChangesGuard dirty={isDirty} />
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <PageTitle title={plant?.plant_name ?? plant?.instance_id ?? t('entities.plantInstance')} />
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            startIcon={<LabelIcon />}
            onClick={() => setTagDialogOpen(true)}
            data-testid="tag-button"
          >
            {t('pages.plantInstances.tag.button')}
          </Button>
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
        <Tab label={t('pages.plantingRuns.tabPhases')} data-testid="phases-tab" />
        <Tab label={t('entities.nutrientPlan')} />
        <Tab label={t('entities.wateringLog')} />
        <Tab label={t('nav.pflege')} />
        <Tab label={t('pages.activityPlan.tabTitle')} data-testid="activity-plan-tab" />
        <Tab label={t('pages.plantInstances.taskHistoryTab')} data-testid="tasks-tab" />
        <Tab label={t('common.edit')} />
      </Tabs>

      {tab === 0 && (
        <>
          {/* Compact summary bar */}
          {plant && (
            <Box
              sx={{
                display: 'flex',
                gap: { xs: 2, sm: 4 },
                flexWrap: 'wrap',
                alignItems: 'flex-start',
                mb: 3,
                p: 2,
                bgcolor: 'background.paper',
                borderRadius: 1,
                border: 1,
                borderColor: 'divider',
              }}
              data-testid="plant-info-card"
            >
              <Box>
                <Typography variant="caption" color="text.secondary">
                  {t('pages.plantInstances.instanceId')}
                </Typography>
                <Typography variant="body1" fontWeight={500}>{plant.instance_id}</Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  {t('pages.plantInstances.plantedOn')}
                </Typography>
                <Typography variant="body1">{plant.planted_on}</Typography>
              </Box>
              {assignedLocation && (
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    {assignedSlot ? t('entities.slot') : t('entities.location')}
                  </Typography>
                  <Typography variant="body1">
                    {assignedSlot
                      ? `${assignedLocation.name} / ${assignedSlot.slot_id}`
                      : assignedLocation.name}
                  </Typography>
                </Box>
              )}
              {plant.substrate_type_override && (
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    {t('pages.plantInstances.substrate')}
                  </Typography>
                  <Typography variant="body1">
                    <Chip label={t(`enums.substrateType.${plant.substrate_type_override}`)} size="small" variant="outlined" />
                  </Typography>
                </Box>
              )}
              {plantRuns.length > 0 && (
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    {t('entities.plantingRun')}
                  </Typography>
                  {plantRuns.map((r) => (
                    <Link
                      key={r.key}
                      component={RouterLink}
                      to={`/durchlaeufe/planting-runs/${r.key}`}
                      underline="hover"
                      sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
                    >
                      {r.name}
                      <Chip label={t(`enums.plantingRunStatus.${r.status}`)} size="small" variant="outlined" />
                    </Link>
                  ))}
                </Box>
              )}
              {plant.removed_on && (
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    {t('pages.plantInstances.removedOn')}
                  </Typography>
                  <Typography variant="body1" color="error">{plant.removed_on}</Typography>
                </Box>
              )}
              <Box data-testid="phase-info-card">
                <Typography variant="caption" color="text.secondary">
                  {t('pages.phases.current')}
                </Typography>
                <Box>
                  <Chip label={plant.current_phase} color="primary" size="small" data-testid="current-phase" />
                </Box>
              </Box>
              {currentPhase && (
                <>
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      {t('pages.phases.daysInPhase')}
                    </Typography>
                    <Typography variant="body1">{currentPhase.days_in_phase}</Typography>
                  </Box>
                  {currentPhase.next_phase && (
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        {t('pages.phases.nextPhase')}
                      </Typography>
                      <Typography variant="body1">{currentPhase.next_phase}</Typography>
                    </Box>
                  )}
                </>
              )}
            </Box>
          )}

          {/* Watering card */}
          {plant && !plant.removed_on && (
            <Card sx={{ mb: 3 }} data-testid="watering-card">
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2, flexWrap: 'wrap', mb: (dosagePresets || wateringVolume) ? 1.5 : 0 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 3, flexWrap: 'wrap' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <OpacityIcon color="primary" />
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          {t('pages.plantInstances.lastWatered')}
                        </Typography>
                        <Typography variant="body1" fontWeight={500}>
                          {lastWatering
                            ? new Date(lastWatering.confirmed_at).toLocaleDateString(i18n.language)
                            : '—'}
                        </Typography>
                      </Box>
                    </Box>
                    {(() => {
                      // Prefer task due_date, fallback to lastWatering + interval
                      const nextDate = nextWateringTask?.due_date
                        ? new Date(nextWateringTask.due_date)
                        : lastWatering && effectiveWateringInterval
                          ? new Date(new Date(lastWatering.confirmed_at).getTime() + effectiveWateringInterval.value * 86400000)
                          : null;
                      if (!nextDate) return null;
                      const days = Math.ceil((nextDate.getTime() - Date.now()) / 86400000);
                      const daysLabel =
                        days === 0 ? t('pages.plantInstances.today')
                        : days === 1 ? t('pages.plantInstances.tomorrow')
                        : days > 1 ? t('pages.plantInstances.inDays', { count: days })
                        : t('pages.plantInstances.overdue');
                      const isOverdue = days < 0;
                      return (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <TodayIcon color={isOverdue ? 'error' : 'info'} />
                          <Box>
                            <Typography variant="caption" color="text.secondary">
                              {t('pages.plantInstances.nextWatering')}
                            </Typography>
                            <Typography variant="body1" fontWeight={500} color={isOverdue ? 'error.main' : undefined}>
                              {nextWateringTask?.due_date ? (
                                <Link
                                  component={RouterLink}
                                  to={`/aufgaben/tasks/${nextWateringTask.key}`}
                                  underline="hover"
                                >
                                  {nextDate.toLocaleDateString(i18n.language)} ({daysLabel})
                                </Link>
                              ) : (
                                <>{nextDate.toLocaleDateString(i18n.language)} ({daysLabel})</>
                              )}
                            </Typography>
                          </Box>
                        </Box>
                      );
                    })()}
                    {effectiveWateringInterval && (
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          {t('pages.plantInstances.wateringInterval')}
                        </Typography>
                        <Typography variant="body1">
                          {effectiveWateringInterval.value} {t('common.days')}
                        </Typography>
                      </Box>
                    )}
                  </Box>
                  <Button
                    variant="contained"
                    color="success"
                    startIcon={<CheckCircleOutlineIcon />}
                    onClick={() => setWateringDialogOpen(true)}
                    disabled={confirmingWatering}
                    data-testid="confirm-watering-button"
                  >
                    {t('pages.plantInstances.confirmWatering')}
                  </Button>
                </Box>

                {/* Phase-specific watering hints */}
                {(dosagePresets || wateringVolume) && (
                  <>
                    <Divider />
                    <Box sx={{ mt: 1.5, display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'flex-start' }}>
                      {/* Water targets + volume */}
                      <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap', alignItems: 'center' }}>
                        {activePhaseEntry && (
                          <Chip
                            label={activePhaseEntry.phase_name ? t(`enums.phaseName.${activePhaseEntry.phase_name}`, activePhaseEntry.phase_name) : ''}
                            size="small"
                            color="info"
                            variant="filled"
                          />
                        )}
                        {dosagePresets?.targetEc != null && (
                          <Chip label={`EC ${dosagePresets.targetEc} mS`} size="small" variant="outlined" />
                        )}
                        {dosagePresets?.targetPh != null && (
                          <Chip label={`pH ${dosagePresets.targetPh}`} size="small" variant="outlined" />
                        )}
                        {wateringVolume && (
                          <Chip
                            label={`${wateringVolume.liters} L`}
                            size="small"
                            variant="outlined"
                            title={wateringVolume.hint}
                          />
                        )}
                      </Box>

                      {/* Fertilizer dosages */}
                      {dosagePresets && dosagePresets.dosages.length > 0 && (
                        <Box sx={{ display: 'flex', gap: 0.75, flexWrap: 'wrap' }}>
                          {dosagePresets.dosages.map((d) => {
                            const fert = fertilizers.find((f) => f.key === d.fertilizer_key);
                            return (
                              <Chip
                                key={d.fertilizer_key}
                                icon={<ScienceIcon />}
                                label={`${fert?.product_name ?? d.fertilizer_key}: ${d.ml_per_liter} ml/L`}
                                size="small"
                                color="primary"
                                variant="outlined"
                              />
                            );
                          })}
                        </Box>
                      )}
                    </Box>
                  </>
                )}
              </CardContent>
            </Card>
          )}

          {/* Current phase profile card */}
          {(currentGrowthPhase || activePhaseEntry) && (
            <Card sx={{ mb: 3 }} data-testid="phase-profile-card">
              <CardContent>
                <Typography variant="h6" sx={{ mb: 1.5 }}>
                  {t('pages.plantInstances.phaseProfile')}
                </Typography>
                <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: 'repeat(4, 1fr)' }, gap: 2 }}>
                  {/* Growth phase info */}
                  {currentGrowthPhase && (
                    <>
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          {t('pages.phases.typicalDuration')}
                        </Typography>
                        <Typography variant="body1">
                          {currentGrowthPhase.typical_duration_days} {t('pages.plantInstances.days')}
                        </Typography>
                      </Box>
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          {t('pages.phases.stressTolerance')}
                        </Typography>
                        <Typography variant="body1">
                          {t(`enums.stressTolerance.${currentGrowthPhase.stress_tolerance}`)}
                        </Typography>
                      </Box>
                    </>
                  )}

                  {/* Nutrient plan phase entry info */}
                  {activePhaseEntry && (
                    <>
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          {t('pages.nutrientPlans.npkRatio')}
                        </Typography>
                        <Typography variant="body1" fontWeight={500}>
                          {activePhaseEntry.npk_ratio[0]}-{activePhaseEntry.npk_ratio[1]}-{activePhaseEntry.npk_ratio[2]}
                        </Typography>
                      </Box>
                      {(activePhaseEntry.calcium_ppm != null || activePhaseEntry.magnesium_ppm != null) && (
                        <Box>
                          <Typography variant="caption" color="text.secondary">
                            Ca / Mg (ppm)
                          </Typography>
                          <Typography variant="body1">
                            {activePhaseEntry.calcium_ppm ?? '–'} / {activePhaseEntry.magnesium_ppm ?? '–'}
                          </Typography>
                        </Box>
                      )}
                    </>
                  )}
                </Box>

                {/* Delivery channels with target EC/pH and fertilizer dosages */}
                {activePhaseEntry && activePhaseEntry.delivery_channels.length > 0 && (
                  <>
                    <Divider sx={{ my: 1.5 }} />
                    <DeliveryChannelAccordion
                      channels={activePhaseEntry.delivery_channels}
                      fertilizers={fertilizers}
                      onLogWatering={(ch) => {
                        const volumeLiters = ch.method_params
                          ? ch.method_params.method === 'drench'
                            ? ch.method_params.volume_per_feeding_liters
                            : ch.method_params.method === 'foliar'
                              ? ch.method_params.volume_per_spray_liters
                              : null
                          : null;
                        setWateringLogChannelPreset({
                          channelId: ch.channel_id,
                          channelLabel: ch.label || ch.channel_id,
                          nutrientPlanKey: assignedPlan!.key,
                          applicationMethod: ch.application_method as 'fertigation' | 'drench' | 'foliar' | 'top_dress',
                          targetEcMs: ch.target_ec_ms,
                          targetPh: ch.target_ph,
                          fertilizers: ch.fertilizer_dosages
                            .filter((d) => !d.optional)
                            .sort((a, b) => a.mixing_order - b.mixing_order)
                            .map((d) => ({ fertilizer_key: d.fertilizer_key, ml_per_liter: d.ml_per_liter })),
                          volumeLiters,
                        });
                        setWateringLogCreateOpen(true);
                      }}
                    />
                  </>
                )}

                {/* Hint when no nutrient plan assigned */}
                {!assignedPlan && currentGrowthPhase && (
                  <>
                    <Divider sx={{ my: 1.5 }} />
                    <Alert severity="info" variant="outlined" sx={{ py: 0 }}>
                      {t('pages.plantInstances.noNutrientPlanHint')}
                    </Alert>
                  </>
                )}
              </CardContent>
            </Card>
          )}

          {/* Species & Cultivar cards */}
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: assignedCultivar ? '1fr 1fr' : '1fr' }, gap: 3 }}>
            {species && (
              <Card data-testid="species-card">
                <CardContent>
                  {/* Header with name + link */}
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                    <Box>
                      <Typography variant="h6" fontStyle="italic">{species.scientific_name}</Typography>
                      {species.common_names.length > 0 && (
                        <Typography variant="body2" color="text.secondary">
                          {species.common_names.join(', ')}
                        </Typography>
                      )}
                    </Box>
                    <Link component={RouterLink} to={`/stammdaten/species/${species.key}`} underline="hover" sx={{ whiteSpace: 'nowrap', ml: 2 }}>
                      {t('pages.plantInstances.viewSpecies')}
                    </Link>
                  </Box>

                  <Divider sx={{ my: 1.5 }} />

                  {/* Properties in 2-column grid */}
                  <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, rowGap: 0.5, columnGap: 2 }}>
                    {species.growth_habit && (
                      <Typography variant="body2">
                        <Typography component="span" variant="body2" color="text.secondary">{t('pages.species.growthHabit')}: </Typography>
                        {t(`enums.growthHabit.${species.growth_habit}`)}
                      </Typography>
                    )}
                    {species.root_type && (
                      <Typography variant="body2">
                        <Typography component="span" variant="body2" color="text.secondary">{t('pages.species.rootType')}: </Typography>
                        {t(`enums.rootType.${species.root_type}`)}
                      </Typography>
                    )}
                    {species.mature_height_cm && (
                      <Typography variant="body2">
                        <Typography component="span" variant="body2" color="text.secondary">{t('pages.species.matureHeightCm')}: </Typography>
                        {species.mature_height_cm} cm
                      </Typography>
                    )}
                    {species.mature_width_cm && (
                      <Typography variant="body2">
                        <Typography component="span" variant="body2" color="text.secondary">{t('pages.species.matureWidthCm')}: </Typography>
                        {species.mature_width_cm} cm
                      </Typography>
                    )}
                    {species.spacing_cm && (
                      <Typography variant="body2">
                        <Typography component="span" variant="body2" color="text.secondary">{t('pages.species.spacingCm')}: </Typography>
                        {species.spacing_cm} cm
                      </Typography>
                    )}
                    {species.recommended_container_volume_l && (
                      <Typography variant="body2">
                        <Typography component="span" variant="body2" color="text.secondary">{t('pages.species.recommendedContainerVolumeL')}: </Typography>
                        {species.recommended_container_volume_l} L
                      </Typography>
                    )}
                  </Box>

                  {/* Suitability + frost as compact chips */}
                  {(species.frost_sensitivity || species.indoor_suitable || species.balcony_suitable ||
                    species.container_suitable || species.greenhouse_recommended || species.support_required) && (
                    <>
                      <Divider sx={{ my: 1.5 }} />
                      <Box sx={{ display: 'flex', gap: 0.75, flexWrap: 'wrap' }}>
                        {species.frost_sensitivity && (
                          <Chip
                            label={`${t('pages.species.frostSensitivity')}: ${t(`enums.frostTolerance.${species.frost_sensitivity}`)}`}
                            size="small"
                            color={frostChipColor(species.frost_sensitivity)}
                          />
                        )}
                        {species.indoor_suitable && (
                          <Chip
                            label={`${t('pages.species.indoorSuitable')}: ${t(`enums.suitability.${species.indoor_suitable}`)}`}
                            size="small"
                            variant="outlined"
                          />
                        )}
                        {species.balcony_suitable && (
                          <Chip
                            label={`${t('pages.species.balconySuitable')}: ${t(`enums.suitability.${species.balcony_suitable}`)}`}
                            size="small"
                            variant="outlined"
                          />
                        )}
                        {species.container_suitable && (
                          <Chip
                            label={`${t('pages.species.containerSuitable')}: ${t(`enums.suitability.${species.container_suitable}`)}`}
                            size="small"
                            variant="outlined"
                          />
                        )}
                        {species.greenhouse_recommended && (
                          <Chip label={t('pages.species.greenhouseRecommended')} size="small" variant="outlined" />
                        )}
                        {species.support_required && (
                          <Chip label={t('pages.species.supportRequired')} size="small" variant="outlined" />
                        )}
                      </Box>
                    </>
                  )}

                  {/* Calendar months */}
                  {(species.harvest_months.length > 0 || species.bloom_months.length > 0 || species.direct_sow_months.length > 0) && (
                    <>
                      <Divider sx={{ my: 1.5 }} />
                      {species.harvest_months.length > 0 && (
                        <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 0.5, mb: 0.75 }}>
                          <Typography variant="caption" color="text.secondary" sx={{ mr: 0.5 }}>
                            {t('pages.species.harvestMonths')}:
                          </Typography>
                          {species.harvest_months.map((m) => (
                            <Chip key={m} label={monthName(m)} size="small" />
                          ))}
                        </Box>
                      )}
                      {species.bloom_months.length > 0 && (
                        <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 0.5, mb: 0.75 }}>
                          <Typography variant="caption" color="text.secondary" sx={{ mr: 0.5 }}>
                            {t('pages.species.bloomMonths')}:
                          </Typography>
                          {species.bloom_months.map((m) => (
                            <Chip key={m} label={monthName(m)} size="small" />
                          ))}
                        </Box>
                      )}
                      {species.direct_sow_months.length > 0 && (
                        <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 0.5 }}>
                          <Typography variant="caption" color="text.secondary" sx={{ mr: 0.5 }}>
                            {t('pages.species.directSowMonths')}:
                          </Typography>
                          {species.direct_sow_months.map((m) => (
                            <Chip key={m} label={monthName(m)} size="small" />
                          ))}
                        </Box>
                      )}
                    </>
                  )}
                </CardContent>
              </Card>
            )}

            {assignedCultivar && (
              <Card data-testid="cultivar-card">
                <CardContent>
                  {/* Header with name + link */}
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                    <Typography variant="h6">{assignedCultivar.name}</Typography>
                    <Link
                      component={RouterLink}
                      to={`/stammdaten/species/${species?.key}/cultivars/${assignedCultivar.key}`}
                      underline="hover"
                      sx={{ whiteSpace: 'nowrap', ml: 2 }}
                    >
                      {t('pages.plantInstances.viewCultivar')}
                    </Link>
                  </Box>

                  <Divider sx={{ my: 1.5 }} />

                  {/* Properties in 2-column grid */}
                  <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, rowGap: 0.5, columnGap: 2 }}>
                    {assignedCultivar.breeder && (
                      <Typography variant="body2">
                        <Typography component="span" variant="body2" color="text.secondary">{t('pages.cultivars.breeder')}: </Typography>
                        {assignedCultivar.breeder}{assignedCultivar.breeding_year ? ` (${assignedCultivar.breeding_year})` : ''}
                      </Typography>
                    )}
                    {assignedCultivar.days_to_maturity != null && (
                      <Typography variant="body2">
                        <Typography component="span" variant="body2" color="text.secondary">{t('pages.cultivars.daysToMaturity')}: </Typography>
                        {assignedCultivar.days_to_maturity}
                      </Typography>
                    )}
                    {assignedCultivar.patent_status && (
                      <Typography variant="body2">
                        <Typography component="span" variant="body2" color="text.secondary">{t('pages.cultivars.patentStatus')}: </Typography>
                        {assignedCultivar.patent_status}
                      </Typography>
                    )}
                  </Box>

                  {/* Traits */}
                  {assignedCultivar.traits.length > 0 && (
                    <>
                      <Divider sx={{ my: 1.5 }} />
                      <Typography variant="caption" color="text.secondary">{t('pages.cultivars.traits')}</Typography>
                      <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mt: 0.5 }}>
                        {assignedCultivar.traits.map((trait) => (
                          <Chip key={trait} label={t(`enums.plantTrait.${trait}`)} size="small" />
                        ))}
                      </Box>
                    </>
                  )}

                  {/* Disease resistances */}
                  {assignedCultivar.disease_resistances.length > 0 && (
                    <>
                      <Divider sx={{ my: 1.5 }} />
                      <Typography variant="caption" color="text.secondary">{t('pages.cultivars.diseaseResistances')}</Typography>
                      <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mt: 0.5 }}>
                        {assignedCultivar.disease_resistances.map((r) => (
                          <Chip key={r} label={r} size="small" variant="outlined" />
                        ))}
                      </Box>
                    </>
                  )}
                </CardContent>
              </Card>
            )}
          </Box>
        </>
      )}

      {/* Tab 1: Phases */}
      {tab === 1 && plant && key && (
        <>
          <Box data-testid="phases-tab-content">
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                {t('pages.plantingRuns.phaseTimeline')}
              </Typography>
              <Button
                startIcon={<SwapHorizIcon />}
                variant="outlined"
                size="small"
                onClick={() => setTransitionOpen(true)}
                disabled={!!plant.removed_on}
              >
                {t('pages.phases.transition')}
              </Button>
            </Box>
            <PlantPhaseTimeline plant={plant} history={history} speciesName={species?.scientific_name} />
            <Typography variant="h6" sx={{ mt: 3, mb: 2 }}>
              {t('pages.phases.history')}
            </Typography>
            <PhaseHistoryTable plantKey={key} onChanged={load} />
          </Box>
          {currentPhase?.phase_key && (
            <ProfilesSection
              phaseKey={currentPhase.phase_key}
              phaseName={currentPhase.phase}
              readOnly
            />
          )}
        </>
      )}

      {/* Tab 2: Nutrient Plan */}
      {tab === 2 && (
        <Box>
          {assignedPlan ? (
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <ScienceIcon />
                <Link component={RouterLink} to={`/duengung/plans/${assignedPlan.key}`} underline="hover">
                  {assignedPlan.name}
                </Link>
              </Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={<ScienceIcon />}
                  onClick={openAssignDialog}
                  disabled={!!plant?.removed_on}
                >
                  {t('pages.nutrientPlans.assignPlan')}
                </Button>
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
            </Box>
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

          {/* Non-perennial: PhaseGanttChart overview + PhaseDetailGantt per group */}
          {!perennialCycleInfo && planEntries.length > 0 && (
            <Box sx={{ mt: 3 }}>
              <PhaseGanttChart
                entries={ganttCycleData.entries}
                fertilizers={fertilizers}
                title=""
                currentWeek={ganttCycleData.currentWeek}
              />
              {(() => {
                const sorted = [...ganttCycleData.entries].sort((a, b) => a.sequence_order - b.sequence_order);
                const vegPhases = new Set(['vegetative', 'seedling', 'germination']);
                const flowerPhases = new Set(['flowering', 'flushing', 'harvest']);
                const vegEntries = sorted.filter((e) => vegPhases.has(e.phase_name));
                const flowerEntries = sorted.filter((e) => flowerPhases.has(e.phase_name));
                const cw = ganttCycleData.currentWeek;
                const phase = actualPhase?.name;
                const vegWeek = phase && vegPhases.has(phase) ? cw : undefined;
                const flowerWeek = phase && flowerPhases.has(phase) ? cw : undefined;
                return (
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
                    {vegEntries.length > 0 && (
                      <PhaseDetailGantt
                        entries={vegEntries}
                        fertilizers={fertilizers}
                        title={t('pages.gantt.vegetativeDetail')}
                        currentWeek={vegWeek}
                      />
                    )}
                    {flowerEntries.length > 0 && (
                      <PhaseDetailGantt
                        entries={flowerEntries}
                        fertilizers={fertilizers}
                        title={t('pages.gantt.floweringDetail')}
                        currentWeek={flowerWeek}
                      />
                    )}
                  </Box>
                );
              })()}
            </Box>
          )}

          {/* Perennial: Saisonaler Zyklus (matching duengung/plans detail layout) */}
          {perennialCycleInfo && calendarSeasonalEntries.length > 0 && (
            <Box sx={{ mt: 2 }}>
              {/* Seasonal cycle header */}
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <RepeatIcon fontSize="small" color="action" />
                <Typography variant="h6">
                  {t('pages.nutrientPlans.seasonalCycleSection')}
                </Typography>
                <Chip
                  label={`${perennialCycleInfo.cycleLen} ${t('pages.nutrientPlans.weeksPerCycle')}`}
                  size="small"
                  variant="outlined"
                />
              </Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                {perennialCycleInfo.recurringEntries.map((e) => t(`enums.phaseName.${e.phase_name}`)).join(' \u2192 ')}
              </Typography>

              {/* PhaseGanttChart: 52-week calendar with month headers */}
              <PhaseGanttChart
                entries={calendarSeasonalEntries}
                fertilizers={fertilizers}
                title=""
                currentWeek={currentIsoWeek}
                totalWeeksOverride={52}
                showMonthHeaders
                compactMode
              />

            </Box>
          )}
        </Box>
      )}

      {/* Tab 3: Feeding Events */}
      {tab === 3 && (
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">{t('entities.wateringLog')}</Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setWateringLogCreateOpen(true)}
              disabled={!!plant?.removed_on}
              data-testid="create-watering-log-button"
            >
              {t('pages.wateringLogs.create')}
            </Button>
          </Box>
          <DataTable<WateringLog>
            columns={[
              {
                id: 'loggedAt',
                label: t('pages.wateringLogs.loggedAt'),
                render: (r) => r.logged_at ? new Date(r.logged_at).toLocaleString() : '\u2014',
                searchValue: (r) => r.logged_at ? new Date(r.logged_at).toLocaleString() : '',
              },
              {
                id: 'applicationMethod',
                label: t('pages.wateringLogs.applicationMethod'),
                render: (r) => t(`enums.applicationMethod.${r.application_method}`),
                searchValue: (r) => t(`enums.applicationMethod.${r.application_method}`),
              },
              {
                id: 'volume',
                label: t('pages.wateringLogs.volumeLiters'),
                render: (r) => `${r.volume_liters} L`,
                align: 'right',
              },
              {
                id: 'isSupplemental',
                label: t('pages.wateringLogs.isSupplemental'),
                render: (r) => r.is_supplemental ? (
                  <Chip label={t('common.yes')} size="small" color="info" />
                ) : null,
              },
              {
                id: 'ecAfter',
                label: t('pages.wateringLogs.ecAfter'),
                render: (r) => r.ec_after != null ? String(r.ec_after) : '\u2014',
                align: 'right',
              },
            ]}
            rows={wateringLogs}
            getRowKey={(r) => r.key}
            onRowClick={(r) => navigate(`/giessprotokoll/${r.key}`)}
            tableState={wateringLogTableState}
            ariaLabel={t('entities.wateringLog')}
          />
        </Box>
      )}

      {/* Tab 4: Care Profile */}
      {tab === 4 && (
        <Box sx={{ maxWidth: 900 }}>
          {careProfile ? (
            <>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Chip
                  label={t(`enums.careStyle.${careProfile.care_style}`)}
                  size="small"
                  variant="outlined"
                />
                <Button variant="outlined" size="small" onClick={() => setCareProfileEditOpen(true)}>
                  {t('common.edit')}
                </Button>
              </Box>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                {([
                  { type: 'watering', enabled: careProfile.auto_create_watering_task, interval: careProfile.watering_interval_days, unit: t('common.days'), color: 'primary' as const },
                  { type: 'fertilizing', enabled: careProfile.auto_create_fertilizing_task, interval: careProfile.fertilizing_interval_days, unit: t('common.days'), color: 'success' as const },
                  { type: 'repotting', enabled: careProfile.auto_create_repotting_task, interval: careProfile.repotting_interval_months, unit: t('common.months_unit'), color: 'warning' as const },
                  { type: 'pest_check', enabled: careProfile.auto_create_pest_check_task, interval: careProfile.pest_check_interval_days, unit: t('common.days'), color: 'error' as const },
                  ...(careProfile.humidity_check_enabled ? [{ type: 'humidity_check' as const, enabled: true, interval: careProfile.humidity_check_interval_days, unit: t('common.days'), color: 'info' as const }] : []),
                ] as const).map((row) => (
                  <Box
                    key={row.type}
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 2,
                      px: 2,
                      py: 1,
                      borderRadius: 1,
                      border: 1,
                      borderColor: row.enabled ? 'divider' : 'action.disabledBackground',
                      opacity: row.enabled ? 1 : 0.5,
                    }}
                  >
                    <Chip
                      size="small"
                      color={row.enabled ? row.color : 'default'}
                      label={row.enabled ? t('common.on') : t('common.off')}
                      sx={{ minWidth: 40 }}
                    />
                    <Typography variant="body2" sx={{ flex: 1, fontWeight: 500 }}>
                      {t(`enums.reminderType.${row.type}`)}
                    </Typography>
                    {row.enabled && (
                      <Typography variant="body2" color="text.secondary">
                        {t('pages.pflege.everyN', { n: row.interval, unit: row.unit })}
                      </Typography>
                    )}
                  </Box>
                ))}
              </Box>
              {careProfile.notes && (
                <Typography variant="body2" color="text.secondary" sx={{ mt: 2, fontStyle: 'italic' }}>
                  {careProfile.notes}
                </Typography>
              )}
              <CareProfileEditDialog
                open={careProfileEditOpen}
                onClose={() => setCareProfileEditOpen(false)}
                profile={careProfile}
                onUpdated={(updated) => setCareProfile(updated)}
              />
            </>
          ) : (
            <Typography color="text.secondary">{t('common.loading')}</Typography>
          )}
        </Box>
      )}

      {/* Tab 5: Activity Plan */}
      {tab === 5 && plant && (
        <ActivityPlanTab
          speciesKey={plant.species_key}
          plantKey={key}
          currentPhaseName={actualPhase?.name}
        />
      )}

      {/* Tab 6: Tasks */}
      {tab === 6 && (
        <Box>
          {plantTasksLoading ? (
            <LoadingSkeleton variant="table" />
          ) : plantTasks.length === 0 ? (
            <EmptyState
              message={t('pages.plantInstances.noTasks')}
              actionLabel={t('pages.plantInstances.noTasksCta')}
              onAction={() => navigate('/aufgaben/queue')}
            />
          ) : (
            <>
              {/* Summary stats bar */}
              <Box
                sx={{
                  display: 'flex',
                  gap: 1.5,
                  flexWrap: 'wrap',
                  alignItems: 'center',
                  mb: 2,
                  p: 1.5,
                  bgcolor: 'background.paper',
                  border: 1,
                  borderColor: 'divider',
                  borderRadius: 1,
                }}
              >
                {overdueCount > 0 && (
                  <Chip
                    icon={<WarningAmberIcon />}
                    label={`${t('pages.plantInstances.taskTabSummaryOverdue')}: ${overdueCount}`}
                    size="small"
                    color="error"
                    variant="outlined"
                  />
                )}
                <Chip
                  label={`${t('pages.plantInstances.taskTabSummaryActive')}: ${activeTasks.length}`}
                  size="small"
                  color={activeTasks.length > 0 ? 'warning' : 'default'}
                  variant="outlined"
                />
                <Chip
                  label={`${t('pages.plantInstances.taskTabSummaryDone')}: ${archivedTasks.length}`}
                  size="small"
                  color="default"
                  variant="outlined"
                />
              </Box>

              {/* Active tasks section */}
              {activeTasks.length > 0 && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
                    {t('pages.plantInstances.taskTabActiveSection')}
                  </Typography>
                  <DataTable<TaskItem>
                    columns={[
                      {
                        id: 'status',
                        label: t('common.status'),
                        render: (row) => (
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
                            <TaskStatusIcon status={row.status} />
                            <Chip
                              size="small"
                              label={t(`enums.taskStatus.${row.status}`, { defaultValue: row.status })}
                              color={taskStatusColor(row.status)}
                              variant="filled"
                            />
                          </Box>
                        ),
                        searchValue: (row) => t(`enums.taskStatus.${row.status}`, { defaultValue: row.status }),
                      },
                      {
                        id: 'name',
                        label: t('common.name'),
                        render: (row) => (
                          <Link component={RouterLink} to={`/aufgaben/tasks/${row.key}`} underline="hover" onClick={(e) => e.stopPropagation()}>
                            {row.name}
                          </Link>
                        ),
                        searchValue: (row) => row.name,
                      },
                      {
                        id: 'category',
                        label: t('pages.tasks.category'),
                        render: (row) => (
                          <Chip
                            size="small"
                            label={t(`enums.taskCategory.${row.category}`, { defaultValue: row.category })}
                            variant="outlined"
                          />
                        ),
                        searchValue: (row) => t(`enums.taskCategory.${row.category}`, { defaultValue: row.category }),
                        hideBelowBreakpoint: 'md',
                      },
                      {
                        id: 'due_date',
                        label: t('pages.tasks.dueDate'),
                        render: (row) => {
                          const relative = formatRelativeDueDate(row.due_date);
                          const isOverdue = row.due_date && new Date(row.due_date) < today;
                          return (
                            <Typography
                              variant="body2"
                              color={isOverdue ? 'error' : 'text.primary'}
                              fontWeight={isOverdue ? 600 : undefined}
                            >
                              {relative}
                            </Typography>
                          );
                        },
                        searchValue: (row) => row.due_date ?? '',
                      },
                      {
                        id: 'priority',
                        label: t('pages.tasks.priority'),
                        render: (row) => (
                          <Chip
                            size="small"
                            label={t(`enums.taskPriority.${row.priority}`, { defaultValue: row.priority })}
                            color={row.priority === 'critical' ? 'error' : row.priority === 'high' ? 'warning' : 'default'}
                            variant="outlined"
                          />
                        ),
                        searchValue: (row) => t(`enums.taskPriority.${row.priority}`, { defaultValue: row.priority }),
                        hideBelowBreakpoint: 'md',
                      },
                      {
                        id: 'actions',
                        label: '',
                        render: (row) => (
                          <Tooltip title={t('pages.plantInstances.taskCompleteQuick')}>
                            <span>
                              <IconButton
                                size="small"
                                color="success"
                                disabled={completingTaskKey === row.key}
                                onClick={(e) => handleQuickCompleteTask(row.key, e)}
                                aria-label={t('pages.plantInstances.taskCompleteQuick')}
                                data-testid={`quick-complete-${row.key}`}
                              >
                                <CheckCircleOutlineIcon fontSize="small" />
                              </IconButton>
                            </span>
                          </Tooltip>
                        ),
                        width: 56,
                      },
                    ]}
                    rows={activeTasks}
                    getRowKey={(row) => row.key}
                    onRowClick={(row) => navigate(`/aufgaben/tasks/${row.key}`)}
                    tableState={taskTableState}
                    ariaLabel={t('pages.plantInstances.taskTabActiveSection')}
                    searchable
                  />
                </Box>
              )}

              {/* Archived tasks section */}
              {archivedTasks.length > 0 && (
                <Box>
                  <Divider sx={{ mb: 2 }} />
                  <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
                    {t('pages.plantInstances.taskTabDoneSection')}
                  </Typography>
                  <DataTable<TaskItem>
                    columns={[
                      {
                        id: 'status',
                        label: t('common.status'),
                        render: (row) => (
                          <Chip
                            size="small"
                            label={t(`enums.taskStatus.${row.status}`, { defaultValue: row.status })}
                            color={taskStatusColor(row.status)}
                            variant="outlined"
                          />
                        ),
                        searchValue: (row) => t(`enums.taskStatus.${row.status}`, { defaultValue: row.status }),
                      },
                      {
                        id: 'name',
                        label: t('common.name'),
                        render: (row) => (
                          <Link component={RouterLink} to={`/aufgaben/tasks/${row.key}`} underline="hover" onClick={(e) => e.stopPropagation()}>
                            {row.name}
                          </Link>
                        ),
                        searchValue: (row) => row.name,
                      },
                      {
                        id: 'category',
                        label: t('pages.tasks.category'),
                        render: (row) => (
                          <Chip
                            size="small"
                            label={t(`enums.taskCategory.${row.category}`, { defaultValue: row.category })}
                            variant="outlined"
                          />
                        ),
                        searchValue: (row) => t(`enums.taskCategory.${row.category}`, { defaultValue: row.category }),
                        hideBelowBreakpoint: 'md',
                      },
                      {
                        id: 'completed_at',
                        label: t('pages.tasks.completedAt'),
                        render: (row) => row.completed_at
                          ? new Date(row.completed_at).toLocaleDateString(i18n.language === 'de' ? 'de-DE' : 'en-US')
                          : '\u2014',
                        searchValue: (row) => row.completed_at ?? '',
                        hideBelowBreakpoint: 'md',
                      },
                    ]}
                    rows={archivedTasks}
                    getRowKey={(row) => row.key}
                    onRowClick={(row) => navigate(`/aufgaben/tasks/${row.key}`)}
                    ariaLabel={t('pages.plantInstances.taskTabDoneSection')}
                    searchable
                  />
                </Box>
              )}
            </>
          )}
        </Box>
      )}

      {/* Tab 7: Edit */}
      {tab === 7 && (
        <Box component="form" onSubmit={handleSubmit(onEditSubmit)} sx={{ maxWidth: 900, display: 'flex', flexDirection: 'column', gap: 4 }}>
          <Typography variant="body2" color="text.secondary">
            {t('pages.plantInstances.editIntro')}
          </Typography>

          {/* Panel 1: General */}
          <Card variant="outlined">
            <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
              <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
                {t('pages.plantInstances.sectionGeneral')}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('pages.plantInstances.sectionGeneralDesc')}
              </Typography>
              <FormRow>
                <FormTextField name="plant_name" control={control} label={t('pages.plantInstances.plantName')} helperText={t('pages.plantInstances.plantNameHelper')} autoFocus />
                <FormSelectField
                  name="cultivar_key"
                  control={control}
                  label={t('pages.plantInstances.cultivarKey')}
                  helperText={t('pages.plantInstances.cultivarKeyHelper')}
                  options={[
                    { value: '', label: '\u2014' },
                    ...cultivarList.map((c) => ({ value: c.key, label: c.name })),
                  ]}
                />
              </FormRow>
            </CardContent>
          </Card>

          {/* Panel 2: Location */}
          <Card variant="outlined">
            <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
              <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
                {t('pages.plantInstances.sectionLocation')}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('pages.plantInstances.sectionLocationDesc')}
              </Typography>
              <FormRow>
                <FormSelectField
                  name="site_key"
                  control={control}
                  label={t('entities.site')}
                  helperText={t('pages.plantInstances.siteHelper')}
                  options={[
                    { value: '', label: '\u2014' },
                    ...sitesList.map((s) => ({ value: s.key, label: s.name })),
                  ]}
                />
                <LocationTreeSelect
                  name="location_key"
                  control={control}
                  siteKey={editSiteKey}
                  label={t('entities.location')}
                />
              </FormRow>
              <FormRow>
                <FormSelectField
                  name="slot_key"
                  control={control}
                  label={t('entities.slot')}
                  helperText={t('pages.plantInstances.slotHelper')}
                  disabled={!editLocationKey}
                  options={[
                    { value: '', label: '\u2014' },
                    ...slotsList.map((s) => ({
                      value: s.key,
                      label: s.currently_occupied
                        ? `${s.slot_id} (${t('pages.plantInstances.slotOccupied')})`
                        : s.slot_id,
                    })),
                  ]}
                />
              </FormRow>
            </CardContent>
          </Card>

          {/* Panel 3: Planting Setup */}
          <Card variant="outlined">
            <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
              <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
                {t('pages.plantInstances.sectionSetup')}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('pages.plantInstances.sectionSetupDesc')}
              </Typography>
              <FormRow>
                <FormNumberField name="container_volume_liters" control={control} label={t('pages.plantInstances.containerVolumeLiters')} helperText={t('pages.plantInstances.containerVolumeLitersHelper')} min={0.1} max={500} />
                <SubstrateSelectField
                  name="substrate_key"
                  control={control}
                  label={t('pages.plantInstances.substrate')}
                  helperText={t('pages.plantInstances.substrateHelper')}
                  substrates={substratesList}
                />
              </FormRow>
              <FormTextField name="planted_on" control={control} label={t('pages.plantInstances.plantedOn')} helperText={t('pages.plantInstances.plantedOnHelper')} type="date" required />
            </CardContent>
          </Card>

          <Typography variant="caption" color="text.secondary">* {t('common.required')}</Typography>
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
        destructive
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

      {plant && (
        <PlantTagDialog
          open={tagDialogOpen}
          onClose={() => setTagDialogOpen(false)}
          plantKey={plant.key}
          plantName={plant.plant_name ?? plant.instance_id}
        />
      )}

      {key && (
        <PhaseTransitionDialog
          plantKey={key}
          lifecycleKey={lifecycleKey}
          open={transitionOpen}
          onClose={() => setTransitionOpen(false)}
          onTransitioned={(updated) => {
            setPlant(updated);
            setTransitionOpen(false);
            load();
          }}
        />
      )}

      <CareConfirmDialog
        open={wateringDialogOpen}
        onClose={() => setWateringDialogOpen(false)}
        onConfirm={handleConfirmWatering}
        plantName={plant?.plant_name || plant?.instance_id || ''}
        reminderType="watering"
        loading={confirmingWatering}
        defaultDosages={dosagePresets?.dosages}
        defaultTargetEc={dosagePresets?.targetEc}
        defaultTargetPh={dosagePresets?.targetPh}
        phaseName={activePhaseEntry?.phase_name}
        defaultVolumeLiters={wateringVolume?.liters}
        volumeHint={wateringVolume?.hint}
        availableFertilizers={fertilizers}
      />

      <WateringLogCreateDialog
        open={wateringLogCreateOpen}
        onClose={() => {
          setWateringLogCreateOpen(false);
          setWateringLogChannelPreset(undefined);
        }}
        onCreated={() => {
          setWateringLogCreateOpen(false);
          setWateringLogChannelPreset(undefined);
          notification.success(t('pages.wateringLogs.logged'));
          load();
        }}
        plantKeys={key ? [key] : undefined}
        channelPreset={wateringLogChannelPreset}
        availableFertilizers={fertilizers}
      />
    </Box>
  );
}
