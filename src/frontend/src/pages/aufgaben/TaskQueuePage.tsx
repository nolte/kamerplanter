import { useEffect, useState, useMemo, useCallback } from 'react';
import { useNavigate, Link as RouterLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardActionArea from '@mui/material/CardActionArea';
import Checkbox from '@mui/material/Checkbox';
import Chip from '@mui/material/Chip';
import Typography from '@mui/material/Typography';
import CircularProgress from '@mui/material/CircularProgress';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import Autocomplete from '@mui/material/Autocomplete';
import TextField from '@mui/material/TextField';
import Paper from '@mui/material/Paper';
import Link from '@mui/material/Link';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Stack from '@mui/material/Stack';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import AddIcon from '@mui/icons-material/Add';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import CheckIcon from '@mui/icons-material/Check';
import CheckBoxOutlineBlankIcon from '@mui/icons-material/CheckBoxOutlineBlank';
import CheckBoxIcon from '@mui/icons-material/CheckBox';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutlined';
import SkipNextIcon from '@mui/icons-material/SkipNext';
import RefreshIcon from '@mui/icons-material/Refresh';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import ClearIcon from '@mui/icons-material/Clear';
import EditIcon from '@mui/icons-material/Edit';
import LibraryAddCheckIcon from '@mui/icons-material/LibraryAddCheck';
import CloseIcon from '@mui/icons-material/Close';
import ScheduleIcon from '@mui/icons-material/Schedule';
import LocalFloristIcon from '@mui/icons-material/LocalFlorist';
import AcUnitIcon from '@mui/icons-material/AcUnit';
import WbSunnyIcon from '@mui/icons-material/WbSunny';
import TerrainIcon from '@mui/icons-material/Terrain';
import Inventory2Icon from '@mui/icons-material/Inventory2';
import HealthAndSafetyIcon from '@mui/icons-material/HealthAndSafety';
import ThermostatIcon from '@mui/icons-material/Thermostat';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import SnoozeIcon from '@mui/icons-material/Snooze';
import OpacityIcon from '@mui/icons-material/Opacity';
import YardIcon from '@mui/icons-material/Yard';
import SwapVertIcon from '@mui/icons-material/SwapVert';
import BugReportIcon from '@mui/icons-material/BugReport';
import PlaceIcon from '@mui/icons-material/Place';
import WaterDropIcon from '@mui/icons-material/WaterDrop';
import FilterListIcon from '@mui/icons-material/FilterList';
import DoneAllIcon from '@mui/icons-material/DoneAll';
import TodayIcon from '@mui/icons-material/Today';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import PageTitle from '@/components/layout/PageTitle';
import PageHeaderActions from '@/components/layout/PageHeaderActions';
import SpringReturnAssistant from '@/pages/pflege/components/SpringReturnAssistant';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import EmptyState from '@/components/common/EmptyState';
import PrintButton from '@/components/common/PrintButton';
import TaskOriginBadge from '@/components/common/TaskOriginBadge';
import { downloadCareChecklistPdf } from '@/api/endpoints/print';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchTaskQueue, fetchOverdueTasks, fetchCompletedTasks } from '@/store/slices/tasksSlice';
import { fetchDashboard, fetchProfile } from '@/store/slices/careRemindersSlice';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as taskApi from '@/api/endpoints/tasks';
import * as careApi from '@/api/endpoints/careReminders';
import * as plantApi from '@/api/endpoints/plantInstances';
import type { TaskItem, PlantInstance, CareDashboardEntry, ReminderType, CareProfile } from '@/api/types';
import { getPlantDisplayName, getPlantLabel } from '@/utils/plantDisplay';
import type { ConfirmReminderOptions } from '@/api/endpoints/careReminders';
import { kamiTasks } from '@/assets/brand/illustrations';
import TaskCreateDialog from './TaskCreateDialog';
import CareProfileEditDialog from '@/pages/pflege/components/CareProfileEditDialog';
import CareConfirmDialog from '@/pages/pflege/components/CareConfirmDialog';

// ── Constants ──────────────────────────────────────────────────────────

const taskCategories = [
  'maintenance', 'feeding', 'training', 'pruning', 'ausgeizen',
  'transplant', 'ipm', 'harvest', 'observation', 'care_reminder',
  'seasonal', 'phenological',
] as const;

type UrgencyGroup = 'overdue' | 'today' | 'thisWeek' | 'future';

type SourceFilter = 'all' | 'tasks' | 'care';

// REQ-006 FreeStyle (#1082): filter tasks by who produced them. `machine` keeps
// only producer-created tasks (origin != user), `user` keeps only user-authored.
type OriginFilter = 'all' | 'machine' | 'user';

// A unified item that wraps either a task or a care reminder
interface UnifiedItem {
  id: string;
  source: 'task' | 'care';
  task?: TaskItem;
  care?: CareDashboardEntry;
  plantKey?: string;
  dueDate?: Date;
}

// ── Helpers ────────────────────────────────────────────────────────────

function getTaskUrgency(task: TaskItem, now: Date): UrgencyGroup {
  if (!task.due_date) return 'future';
  const due = new Date(task.due_date);
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const todayEnd = new Date(todayStart);
  todayEnd.setDate(todayEnd.getDate() + 1);
  const weekEnd = new Date(todayStart);
  weekEnd.setDate(weekEnd.getDate() + 7);

  if (due < todayStart) return 'overdue';
  if (due < todayEnd) return 'today';
  if (due < weekEnd) return 'thisWeek';
  return 'future';
}

function getCareUrgency(entry: CareDashboardEntry): UrgencyGroup {
  if (entry.urgency === 'overdue') return 'overdue';
  if (entry.urgency === 'due_today') return 'today';
  if (entry.urgency === 'upcoming') return 'thisWeek';
  return 'future';
}

function getReminderIcon(type: ReminderType) {
  switch (type) {
    case 'watering': return <OpacityIcon fontSize="small" />;
    case 'fertilizing': return <YardIcon fontSize="small" />;
    case 'repotting': return <SwapVertIcon fontSize="small" />;
    case 'pest_check': return <BugReportIcon fontSize="small" />;
    case 'location_check': return <PlaceIcon fontSize="small" />;
    case 'humidity_check': return <WaterDropIcon fontSize="small" />;
    case 'deadheading': return <LocalFloristIcon fontSize="small" />;
    case 'winter_protection': return <AcUnitIcon fontSize="small" />;
    case 'spring_uncover': return <WbSunnyIcon fontSize="small" />;
    case 'tuber_dig': return <TerrainIcon fontSize="small" />;
    case 'storage_check': return <Inventory2Icon fontSize="small" />;
    case 'dormancy_health_check': return <HealthAndSafetyIcon fontSize="small" />;
    case 'quarter_climate_check': return <ThermostatIcon fontSize="small" />;
    default: return <ScheduleIcon fontSize="small" />;
  }
}

const priorityColorMap: Record<string, 'default' | 'info' | 'warning' | 'error'> = {
  low: 'default',
  medium: 'info',
  high: 'warning',
  critical: 'error',
};

const urgencyBorderColor: Record<UrgencyGroup, string> = {
  overdue: 'error.main',
  today: 'warning.main',
  thisWeek: 'info.main',
  future: 'divider',
};

const urgencySectionColor: Record<UrgencyGroup, string> = {
  overdue: 'error.main',
  today: 'warning.main',
  thisWeek: 'info.main',
  future: 'text.secondary',
};

// Icon per urgency group (accessibility: colour + icon, not colour alone)
const urgencySectionIcon: Record<UrgencyGroup, React.ReactNode> = {
  overdue: <WarningAmberIcon sx={{ fontSize: 18 }} />,
  today: <TodayIcon sx={{ fontSize: 18 }} />,
  thisWeek: <AccessTimeIcon sx={{ fontSize: 18 }} />,
  future: null,
};

function formatRelativeDate(dateStr: string, t: (key: string) => string): string {
  const due = new Date(dateStr);
  const now = new Date();
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const dueStart = new Date(due.getFullYear(), due.getMonth(), due.getDate());
  const diffDays = Math.round((dueStart.getTime() - todayStart.getTime()) / (1000 * 60 * 60 * 24));

  if (diffDays < -1) return `${Math.abs(diffDays)}d ${t('pages.tasks.overdue').toLowerCase()}`;
  if (diffDays === -1) return t('common.yesterday');
  if (diffDays === 0) return t('pages.tasks.today');
  if (diffDays === 1) return t('common.tomorrow');
  if (diffDays <= 7) return `${diffDays}d`;
  return due.toLocaleDateString();
}

// ── Component ──────────────────────────────────────────────────────────

export default function TaskQueuePage() {
  const { t, i18n } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const notification = useNotification();
  const { handleError } = useApiError();
  const theme = useTheme();
  // Below `sm` the three 48px action targets, their 8px separations and the
  // border consume ~165px of a 361px card, which left the task name roughly
  // 50px of the content column — it was truncated to a few characters. On that
  // viewport the action row therefore moves *below* the card content and spans
  // the full width (UI-NFR-001 R-002 mobile-first, R-011/R-012 touch targets).
  const isCompactCard = useMediaQuery(theme.breakpoints.down('sm'));

  // Task state
  const { taskQueue, loading: tasksLoading, completedTasks, completedTasksLoading } = useAppSelector(
    (s) => s.tasks,
  );
  const [createOpen, setCreateOpen] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [generateLoading, setGenerateLoading] = useState(false);
  const [filterCategory, setFilterCategory] = useState<string>('');
  const [filterPlantKey, setFilterPlantKey] = useState<string | null>(null);
  const [plants, setPlants] = useState<PlantInstance[]>([]);
  // Part of the loading gate: the plant list feeds `plantNameMap`, which decides
  // whether a task card renders its plant-shortcut row. Without it the cards
  // painted first and grew a row per plant-linked task afterwards — a late
  // layout shift under the user's finger.
  const [plantsLoading, setPlantsLoading] = useState(true);
  const [sourceFilter, setSourceFilter] = useState<SourceFilter>('all');
  const [originFilter, setOriginFilter] = useState<OriginFilter>('all');
  const [showCompleted, setShowCompleted] = useState(false);

  // Care state
  const { dashboard: careDashboard, loading: careLoading, currentProfile } = useAppSelector(
    (s) => s.careReminders,
  );
  const [careActionLoading, setCareActionLoading] = useState<string | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editPlantKey, setEditPlantKey] = useState<string | null>(null);
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);
  const [confirmEntry, setConfirmEntry] = useState<CareDashboardEntry | null>(null);

  // Bulk edit mode (tasks only)
  const [bulkMode, setBulkMode] = useState(false);
  const [selectedKeys, setSelectedKeys] = useState<Set<string>>(new Set());
  const [bulkLoading, setBulkLoading] = useState(false);

  useEffect(() => {
    dispatch(fetchTaskQueue());
    dispatch(fetchOverdueTasks());
    dispatch(fetchDashboard());
    plantApi
      .listPlantInstances(0, 200)
      .then(setPlants)
      .catch(() => {})
      .finally(() => setPlantsLoading(false));
  }, [dispatch]);

  // Lazily load completed tasks only when the user reveals them.
  useEffect(() => {
    if (showCompleted) {
      dispatch(fetchCompletedTasks());
    }
  }, [showCompleted, dispatch]);

  // ── Task actions ─────────────────────────────────────────────────────

  const handleGenerateCareReminders = useCallback(async () => {
    try {
      setGenerateLoading(true);
      const result = await taskApi.generateCareReminders();
      if (result.created > 0) {
        notification.success(t('pages.tasks.careRemindersGenerated', { count: result.created }));
      } else {
        notification.info(t('pages.tasks.noNewReminders'));
      }
      dispatch(fetchTaskQueue());
      dispatch(fetchOverdueTasks());
      dispatch(fetchDashboard());
    } catch (err) {
      handleError(err);
    } finally {
      setGenerateLoading(false);
    }
  }, [dispatch, notification, handleError, t]);

  const handleStart = useCallback(
    async (key: string) => {
      try {
        setActionLoading(key);
        await taskApi.startTask(key);
        notification.success(t('pages.tasks.taskStarted'));
        dispatch(fetchTaskQueue());
      } catch (err) {
        handleError(err);
      } finally {
        setActionLoading(null);
      }
    },
    [dispatch, notification, handleError, t],
  );

  const handleComplete = useCallback(
    async (key: string) => {
      try {
        setActionLoading(key);
        await taskApi.completeTask(key, {});
        notification.success(t('pages.tasks.taskCompleted'));
        dispatch(fetchTaskQueue());
        if (showCompleted) dispatch(fetchCompletedTasks());
      } catch (err) {
        handleError(err);
      } finally {
        setActionLoading(null);
      }
    },
    [dispatch, notification, handleError, t, showCompleted],
  );

  const handleSkip = useCallback(
    async (key: string) => {
      try {
        setActionLoading(key);
        await taskApi.skipTask(key);
        notification.success(t('pages.tasks.taskSkipped'));
        dispatch(fetchTaskQueue());
        dispatch(fetchDashboard());
      } catch (err) {
        handleError(err);
      } finally {
        setActionLoading(null);
      }
    },
    [dispatch, notification, handleError, t],
  );

  // ── Care actions ─────────────────────────────────────────────────────

  const handleConfirmClick = useCallback((entry: CareDashboardEntry) => {
    setConfirmEntry(entry);
    setConfirmDialogOpen(true);
  }, []);

  const handleConfirmSubmit = useCallback(
    async (options: ConfirmReminderOptions) => {
      if (!confirmEntry) return;
      const { plant_key, reminder_type } = confirmEntry;
      const id = `care-${plant_key}-${reminder_type}`;
      try {
        setCareActionLoading(id);
        await careApi.confirmReminder(plant_key, reminder_type, options);
        notification.success(t('pages.pflege.confirmAction'));
        setConfirmDialogOpen(false);
        setConfirmEntry(null);
        dispatch(fetchDashboard());
        dispatch(fetchTaskQueue());
      } catch (err) {
        handleError(err);
      } finally {
        setCareActionLoading(null);
      }
    },
    [confirmEntry, dispatch, notification, handleError, t],
  );

  const handleSnooze = useCallback(
    async (plantKey: string, reminderType: ReminderType) => {
      const id = `care-${plantKey}-${reminderType}`;
      try {
        setCareActionLoading(id);
        await careApi.snoozeReminder(plantKey, reminderType);
        notification.info(t('pages.pflege.snoozeAction'));
        dispatch(fetchDashboard());
      } catch (err) {
        handleError(err);
      } finally {
        setCareActionLoading(null);
      }
    },
    [dispatch, notification, handleError, t],
  );

  const handleEditProfile = useCallback(
    (plantKey: string) => {
      setEditPlantKey(plantKey);
      dispatch(fetchProfile({ plantKey }));
      setEditDialogOpen(true);
    },
    [dispatch],
  );

  const handleProfileUpdated = useCallback(
    (_profile: CareProfile) => {
      setEditDialogOpen(false);
      setEditPlantKey(null);
      dispatch(fetchDashboard());
    },
    [dispatch],
  );

  // ── Bulk actions ─────────────────────────────────────────────────────

  const toggleSelection = useCallback((key: string) => {
    setSelectedKeys((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }, []);

  const handleBulkComplete = useCallback(
    async () => {
      const keys = [...selectedKeys];
      if (keys.length === 0) return;
      setBulkLoading(true);
      try {
        const result = await taskApi.batchStatusChange(keys, 'complete');
        const failCount = result.failed.length;
        const successCount = result.succeeded.length;
        if (failCount > 0) {
          notification.warning(t('pages.tasks.bulkResultPartial', { action: t('pages.tasks.bulkComplete'), success: successCount, failed: failCount }));
        } else {
          notification.success(t('pages.tasks.bulkResultSuccess', { action: t('pages.tasks.bulkComplete'), count: successCount }));
        }
      } catch (err) {
        handleError(err);
      } finally {
        setBulkLoading(false);
        setSelectedKeys(new Set());
        dispatch(fetchTaskQueue());
        dispatch(fetchOverdueTasks());
        if (showCompleted) dispatch(fetchCompletedTasks());
      }
    },
    [selectedKeys, dispatch, notification, handleError, t, showCompleted],
  );

  const handleBulkSkip = useCallback(
    async () => {
      const keys = [...selectedKeys];
      if (keys.length === 0) return;
      setBulkLoading(true);
      try {
        const result = await taskApi.batchStatusChange(keys, 'skip');
        const failCount = result.failed.length;
        const successCount = result.succeeded.length;
        if (failCount > 0) {
          notification.warning(t('pages.tasks.bulkResultPartial', { action: t('pages.tasks.bulkSkip'), success: successCount, failed: failCount }));
        } else {
          notification.success(t('pages.tasks.bulkResultSuccess', { action: t('pages.tasks.bulkSkip'), count: successCount }));
        }
      } catch (err) {
        handleError(err);
      } finally {
        setBulkLoading(false);
        setSelectedKeys(new Set());
        dispatch(fetchTaskQueue());
        dispatch(fetchOverdueTasks());
      }
    },
    [selectedKeys, dispatch, notification, handleError, t],
  );

  const handleBulkDelete = useCallback(
    async () => {
      const keys = [...selectedKeys];
      if (keys.length === 0) return;
      setBulkLoading(true);
      try {
        const result = await taskApi.batchDelete(keys);
        const failCount = result.failed.length;
        const successCount = result.succeeded.length;
        if (failCount > 0) {
          notification.warning(t('pages.tasks.bulkResultPartial', { action: t('pages.tasks.bulkDelete'), success: successCount, failed: failCount }));
        } else {
          notification.success(t('pages.tasks.bulkResultSuccess', { action: t('pages.tasks.bulkDelete'), count: successCount }));
        }
      } catch (err) {
        handleError(err);
      } finally {
        setBulkLoading(false);
        setSelectedKeys(new Set());
        dispatch(fetchTaskQueue());
        dispatch(fetchOverdueTasks());
      }
    },
    [selectedKeys, dispatch, notification, handleError, t],
  );

  const exitBulkMode = useCallback(() => {
    setBulkMode(false);
    setSelectedKeys(new Set());
  }, []);

  // ── Derived data ─────────────────────────────────────────────────────

  const plantNameMap = useMemo(() => {
    const map = new Map<string, string>();
    for (const p of plants) {
      map.set(p.key, getPlantDisplayName(p));
    }
    return map;
  }, [plants]);

  // Build unified items from both sources
  const unifiedItems = useMemo(() => {
    const now = new Date();
    const items: (UnifiedItem & { urgency: UrgencyGroup })[] = [];

    // Add tasks
    for (const task of taskQueue) {
      if (filterCategory && task.category !== filterCategory) continue;
      if (originFilter === 'machine' && task.origin === 'user') continue;
      if (originFilter === 'user' && task.origin !== 'user') continue;
      const taskPlantKey = task.entity_type === 'plant_instance' ? task.entity_key : null;
      if (filterPlantKey && taskPlantKey !== filterPlantKey) continue;
      items.push({
        id: `task-${task.key}`,
        source: 'task',
        task,
        plantKey: taskPlantKey ?? undefined,
        dueDate: task.due_date ? new Date(task.due_date) : undefined,
        urgency: getTaskUrgency(task, now),
      });
    }

    // Add care reminders (skip those that already have a pending task to avoid duplication)
    // Build dedup set from care_reminder tasks keyed by entity_key + reminder type
    const taskPlantTypes = new Set<string>();
    // Also build a name-based dedup set for tasks missing entity_key (legacy data)
    const taskNameTypes = new Set<string>();
    for (const taskItem of taskQueue) {
      if (taskItem.category !== 'care_reminder') continue;
      const parts = taskItem.name?.split('—');
      const reminderType = parts && parts.length > 1 ? parts[1].trim() : undefined;
      if (!reminderType) continue;

      if (taskItem.entity_type === 'plant_instance' && taskItem.entity_key) {
        taskPlantTypes.add(`${taskItem.entity_key}-${reminderType}`);
      }
      // Fallback: use the plant name prefix for matching (handles entity_key=null tasks)
      const namePrefix = parts[0].trim();
      if (namePrefix) {
        taskNameTypes.add(`${namePrefix}-${reminderType}`);
      }
    }

    for (const entry of careDashboard) {
      if (entry.urgency === 'not_due') continue;
      // The origin filter selects on *task* provenance; care reminders are a
      // distinct source, so any non-"all" origin selection hides them.
      if (originFilter !== 'all') continue;
      if (filterPlantKey && entry.plant_key !== filterPlantKey) continue;

      // Skip if there's already a care_reminder task for this plant + type
      const typeKey = `${entry.plant_key}-${entry.reminder_type}`;
      if (taskPlantTypes.has(typeKey)) continue;
      // Fallback: match by plant name from dashboard entry
      const nameKey = `${entry.plant_name}-${entry.reminder_type}`;
      if (taskNameTypes.has(nameKey)) continue;

      items.push({
        id: `care-${entry.plant_key}-${entry.reminder_type}`,
        source: 'care',
        care: entry,
        plantKey: entry.plant_key,
        dueDate: entry.due_date ? new Date(entry.due_date) : undefined,
        urgency: getCareUrgency(entry),
      });
    }

    return items;
  }, [taskQueue, careDashboard, filterCategory, filterPlantKey, originFilter]);

  // Apply source filter
  const filtered = useMemo(() => {
    if (sourceFilter === 'all') return unifiedItems;
    return unifiedItems.filter((item) =>
      sourceFilter === 'tasks' ? item.source === 'task' : item.source === 'care',
    );
  }, [unifiedItems, sourceFilter]);

  // Group by urgency
  const grouped = useMemo(() => {
    const groups: Record<UrgencyGroup, typeof filtered> = {
      overdue: [], today: [], thisWeek: [], future: [],
    };
    for (const item of filtered) {
      groups[item.urgency].push(item);
    }
    // Sort within each group by due date
    for (const group of Object.values(groups)) {
      group.sort((a, b) => {
        if (!a.dueDate && !b.dueDate) return 0;
        if (!a.dueDate) return 1;
        if (!b.dueDate) return -1;
        return a.dueDate.getTime() - b.dueDate.getTime();
      });
    }
    return groups;
  }, [filtered]);

  // Completed tasks respect the active category/plant filters and are sorted by
  // most-recently completed first. Care reminders are excluded from this list —
  // the "care" source has its own not-due state, not a completed status.
  const completedFiltered = useMemo(() => {
    if (!showCompleted || sourceFilter === 'care') return [];
    return completedTasks
      .filter((task) => {
        if (filterCategory && task.category !== filterCategory) return false;
        if (originFilter === 'machine' && task.origin === 'user') return false;
        if (originFilter === 'user' && task.origin !== 'user') return false;
        const taskPlantKey = task.entity_type === 'plant_instance' ? task.entity_key : null;
        if (filterPlantKey && taskPlantKey !== filterPlantKey) return false;
        return true;
      })
      .slice()
      .sort((a, b) => {
        const da = a.completed_at ?? a.due_date;
        const db = b.completed_at ?? b.due_date;
        if (!da && !db) return 0;
        if (!da) return 1;
        if (!db) return -1;
        return new Date(db).getTime() - new Date(da).getTime();
      });
  }, [showCompleted, sourceFilter, completedTasks, filterCategory, filterPlantKey, originFilter]);

  const allTaskKeys = useMemo(
    () => filtered.filter((i) => i.source === 'task').map((i) => i.task!.key),
    [filtered],
  );

  const handleSelectAll = useCallback(() => {
    setSelectedKeys((prev) => {
      const allSelected = allTaskKeys.every((k) => prev.has(k));
      if (allSelected) return new Set();
      return new Set(allTaskKeys);
    });
  }, [allTaskKeys]);

  const hasActiveFilters = filterCategory !== '' || filterPlantKey !== null || originFilter !== 'all';

  // ── Render helpers ───────────────────────────────────────────────────

  const renderTaskCard = useCallback(
    (task: TaskItem, urgency: UrgencyGroup) => {
      const isLoading = actionLoading === task.key;
      const plantName = (task.entity_type === 'plant_instance' && task.entity_key) ? plantNameMap.get(task.entity_key) : undefined;
      const isSelected = selectedKeys.has(task.key);
      const isPending = task.status === 'pending';
      const isInProgress = task.status === 'in_progress';
      const isActionable = isPending || isInProgress;
      const displayName = (i18n.language === 'de' && task.name_de) ? task.name_de : task.name;

      // One action row, rendered in one of two places: beside the content from
      // `sm` up, below it (full card width, top border instead of left border)
      // on the compact viewport. Same buttons, same test ids either way.
      const actionRow =
        !bulkMode && isActionable ? (
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              // 48x48 targets separated by the 8px minimum: three flush 40px
              // buttons right next to a large card link is mis-tap geometry
              // (UI-NFR-001 R-011 MUST, R-012 SHOULD).
              gap: 1,
              borderColor: 'divider',
              ...(isCompactCard
                ? { justifyContent: 'flex-end', px: 0.5, borderTop: '1px solid' }
                : { pr: 0.5, borderLeft: '1px solid' }),
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {isPending && (
              <Tooltip title={t('pages.tasks.startTask')}>
                <IconButton
                  size="small"
                  onClick={() => handleStart(task.key)}
                  disabled={isLoading}
                  data-testid={`start-task-${task.key}`}
                  aria-label={t('pages.tasks.startTask')}
                  sx={{ minWidth: 48, minHeight: 48 }}
                >
                  {isLoading ? <CircularProgress size={18} /> : <PlayArrowIcon fontSize="small" />}
                </IconButton>
              </Tooltip>
            )}
            <Tooltip title={t('pages.tasks.completeTask')}>
              <IconButton
                size="small"
                color="success"
                onClick={() => handleComplete(task.key)}
                disabled={isLoading}
                data-testid={`complete-task-${task.key}`}
                aria-label={t('pages.tasks.completeTask')}
                sx={{ minWidth: 48, minHeight: 48 }}
              >
                {isLoading ? <CircularProgress size={18} /> : <CheckIcon fontSize="small" />}
              </IconButton>
            </Tooltip>
            <Tooltip title={t('pages.tasks.skipTask')}>
              <IconButton
                size="small"
                onClick={() => handleSkip(task.key)}
                disabled={isLoading}
                data-testid={`skip-task-${task.key}`}
                aria-label={t('pages.tasks.skipTask')}
                sx={{ minWidth: 48, minHeight: 48 }}
              >
                {isLoading ? <CircularProgress size={18} /> : <SkipNextIcon fontSize="small" />}
              </IconButton>
            </Tooltip>
          </Box>
        ) : null;

      return (
        <Card
          key={task.key}
          variant="outlined"
          sx={{
            mb: 1,
            overflow: 'hidden',
            transition: 'box-shadow 0.15s',
            '&:hover': { boxShadow: 2 },
            ...(bulkMode && isSelected
              ? { outline: '2px solid', outlineColor: 'primary.main', outlineOffset: -2 }
              : {}),
          }}
          data-testid="task-card"
        >
          <Box sx={{ display: 'flex', alignItems: 'stretch' }}>
            {/* Urgency accent bar — colour + width convey urgency, not colour alone */}
            <Box
              aria-hidden="true"
              sx={{
                width: urgency === 'overdue' ? 6 : 4,
                flexShrink: 0,
                bgcolor: urgencyBorderColor[urgency],
                borderRadius: '4px 0 0 4px',
              }}
            />

            {bulkMode && (
              <Box
                sx={{ display: 'flex', alignItems: 'center', pl: 0.5 }}
                onClick={(e) => e.stopPropagation()}
              >
                <Checkbox
                  checked={isSelected}
                  onChange={() => toggleSelection(task.key)}
                  size="small"
                  data-testid={`bulk-select-${task.key}`}
                  slotProps={{
                    input: {
                      'aria-label': t('pages.tasks.bulkSelectTask', { name: displayName }),
                    },
                  }}
                />
              </Box>
            )}

            <Box sx={{ flex: 1, minWidth: 0 }}>
              <CardActionArea
                onClick={bulkMode ? () => toggleSelection(task.key) : () => navigate(`/aufgaben/tasks/${task.key}`)}
                data-testid={`task-card-${task.key}`}
                sx={{ minHeight: 56 }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', px: 2, py: 1.5, gap: 2 }}>
                  <Box sx={{ flex: 1, minWidth: 0 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.25, flexWrap: 'wrap' }}>
                      <Typography
                        variant="subtitle2"
                        sx={{
                          fontWeight: isInProgress ? 700 : 600,
                          // Only truncate task name on very narrow screens; prefer wrapping
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                          maxWidth: { xs: 140, sm: 'none' },
                        }}
                        title={displayName}
                      >
                        {displayName}
                      </Typography>
                      {isInProgress && (
                        <Chip
                          label={t('enums.taskStatus.in_progress')}
                          size="small"
                          color="info"
                          sx={{ height: 20, fontSize: '0.7rem' }}
                        />
                      )}
                      {/* REQ-006 FreeStyle machine-generated badge (#1082) —
                          renders only for producer-created tasks. */}
                      <TaskOriginBadge origin={task.origin} testId={`task-origin-badge-${task.key}`} />
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexWrap: 'wrap' }}>
                      <Typography variant="caption" color="text.disabled">
                        {t(`enums.taskCategory.${task.category}`)}
                        {' · '}
                        {task.activity_key
                          ? t('pages.tasks.sourceActivityPlan')
                          : task.workflow_execution_key
                            ? t('pages.tasks.sourceWorkflow')
                            : task.watering_event_key
                              ? t('pages.tasks.sourceWateringSchedule')
                              : task.category === 'care_reminder'
                                ? t('pages.tasks.sourceCareReminder')
                                : t('pages.tasks.sourceManual')}
                      </Typography>
                      {task.estimated_duration_minutes != null && (
                        <Typography variant="caption" color="text.disabled" sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5 }}>
                          <ScheduleIcon sx={{ fontSize: 13 }} />
                          {task.estimated_duration_minutes} min
                        </Typography>
                      )}
                    </Box>
                  </Box>
                  <Stack direction="row" spacing={0.5} sx={{ alignItems: 'center', flexShrink: 0 }}>
                    {task.priority !== 'medium' && (
                      <Chip
                        label={t(`enums.taskPriority.${task.priority}`)}
                        size="small"
                        color={priorityColorMap[task.priority] ?? 'default'}
                        sx={{ height: 22, fontSize: '0.7rem' }}
                      />
                    )}
                    {task.due_date && (
                      <Typography
                        variant="caption"
                        sx={{
                          color: urgencySectionColor[urgency],
                          fontWeight: urgency === 'overdue' ? 700 : 500,
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {formatRelativeDate(task.due_date, t)}
                      </Typography>
                    )}
                  </Stack>
                </Box>
              </CardActionArea>

              {/* Plant shortcut — a SIBLING of the card's action area, never a
                  descendant of it. A link nested inside the card button was
                  invalid interactive nesting (it broke keyboard and screen-reader
                  semantics) and made the card's own tap target ambiguous: on a
                  narrow viewport the card reflows tall enough that its geometric
                  centre fell on the link, so tapping the middle of a task card
                  opened the plant instead of the task. */}
              {plantName && task.entity_key && task.entity_type === 'plant_instance' && (
                // `pb` is spent on the link's own target height instead of on
                // padding, so honouring the 48px minimum costs the card 8px of
                // height rather than 16px.
                <Box sx={{ display: 'flex', px: 2, pb: 0.5 }}>
                  <Link
                    component={RouterLink}
                    to={`/pflanzen/plant-instances/${task.entity_key}`}
                    variant="caption"
                    color="text.secondary"
                    underline="hover"
                    sx={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 0.5,
                      // UI-NFR-001 R-011 (MUST): a 32px-tall link is below the
                      // touch-target minimum, and this one sits directly under
                      // the card's own action area — the two most likely
                      // mis-taps on the page are neighbours.
                      minHeight: 48,
                      minWidth: 0,
                    }}
                    data-testid={`plant-link-${task.key}`}
                  >
                    <LocalFloristIcon sx={{ fontSize: 14 }} />
                    {plantName}
                  </Link>
                </Box>
              )}
              {isCompactCard && actionRow}
            </Box>

            {!isCompactCard && actionRow}
          </Box>
        </Card>
      );
    },
    [actionLoading, navigate, handleStart, handleComplete, handleSkip, t, i18n.language, plantNameMap, bulkMode, selectedKeys, toggleSelection, isCompactCard],
  );

  const renderCareCard = useCallback(
    (entry: CareDashboardEntry, urgency: UrgencyGroup) => {
      const id = `care-${entry.plant_key}-${entry.reminder_type}`;
      const isLoading = careActionLoading === id;

      // See renderTaskCard: one action row, placed beside the content from
      // `sm` up and below it on the compact viewport.
      const actionRow = (
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            borderColor: 'divider',
            ...(isCompactCard
              ? { justifyContent: 'flex-end', px: 0.5, borderTop: '1px solid' }
              : { pr: 0.5, borderLeft: '1px solid' }),
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <Tooltip title={t('pages.pflege.editProfile')}>
            <IconButton
              size="small"
              onClick={() => handleEditProfile(entry.plant_key)}
              aria-label={t('pages.pflege.editProfile')}
              data-testid={`care-edit-profile-${id}`}
              sx={{ minWidth: 48, minHeight: 48 }}
            >
              <EditIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title={t('pages.pflege.confirmAction')}>
            <span>
              <IconButton
                size="small"
                color="success"
                onClick={() => handleConfirmClick(entry)}
                disabled={isLoading}
                aria-label={t('pages.pflege.confirmAction')}
                data-testid={`care-confirm-${id}`}
                sx={{ minWidth: 48, minHeight: 48 }}
              >
                {isLoading ? <CircularProgress size={18} /> : <CheckCircleIcon fontSize="small" />}
              </IconButton>
            </span>
          </Tooltip>
          <Tooltip title={t('pages.pflege.snoozeAction')}>
            <span>
              <IconButton
                size="small"
                onClick={() => handleSnooze(entry.plant_key, entry.reminder_type)}
                disabled={isLoading}
                aria-label={t('pages.pflege.snoozeAction')}
                data-testid={`care-snooze-${id}`}
                sx={{ minWidth: 48, minHeight: 48 }}
              >
                {isLoading ? <CircularProgress size={18} /> : <SnoozeIcon fontSize="small" />}
              </IconButton>
            </span>
          </Tooltip>
        </Box>
      );

      return (
        <Card
          key={id}
          variant="outlined"
          sx={{
            mb: 1,
            overflow: 'hidden',
            transition: 'box-shadow 0.15s',
            '&:hover': { boxShadow: 2 },
          }}
          data-testid={`care-card-${id}`}
        >
          <Box sx={{ display: 'flex', alignItems: 'stretch' }}>
            {/* Urgency accent bar — colour + width convey urgency, not colour alone */}
            <Box
              aria-hidden="true"
              sx={{
                width: urgency === 'overdue' ? 6 : 4,
                flexShrink: 0,
                bgcolor: urgencyBorderColor[urgency],
                borderRadius: '4px 0 0 4px',
              }}
            />

            <Box sx={{ flex: 1, minWidth: 0 }}>
            {/* Reminder type icon — tappable area links to plant detail */}
            <CardActionArea
              component={RouterLink}
              to={`/pflanzen/plant-instances/${entry.plant_key}`}
              aria-label={t('pages.tasks.careCardPlantLink', { plant: entry.plant_name })}
              sx={{ width: '100%', display: 'flex', alignItems: 'center', px: 2, py: 1.5, gap: 2, minHeight: 56 }}
            >
              <Box sx={{ color: urgencySectionColor[urgency], flexShrink: 0 }}>
                {getReminderIcon(entry.reminder_type)}
              </Box>

              {/* Content */}
              <Box sx={{ flex: 1, minWidth: 0 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.25, flexWrap: 'wrap' }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                    {t(`enums.reminderType.${entry.reminder_type}`)}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexWrap: 'wrap' }}>
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5 }}
                  >
                    <LocalFloristIcon sx={{ fontSize: 14 }} />
                    {entry.plant_name}
                  </Typography>
                  {entry.species_name && (
                    <Typography variant="caption" color="text.disabled">
                      {entry.species_name}
                    </Typography>
                  )}
                </Box>
              </Box>

              {/* Due date */}
              {entry.due_date && (
                <Typography
                  variant="caption"
                  sx={{
                    color: urgencySectionColor[urgency],
                    fontWeight: urgency === 'overdue' ? 700 : 500,
                    whiteSpace: 'nowrap',
                    flexShrink: 0,
                  }}
                >
                  {formatRelativeDate(entry.due_date, t)}
                </Typography>
              )}
            </CardActionArea>
            {isCompactCard && actionRow}
            </Box>

            {!isCompactCard && actionRow}
          </Box>
        </Card>
      );
    },
    [careActionLoading, handleConfirmClick, handleSnooze, handleEditProfile, t, isCompactCard],
  );

  const renderItem = useCallback(
    (item: UnifiedItem & { urgency: UrgencyGroup }) => {
      if (item.source === 'task' && item.task) {
        return renderTaskCard(item.task, item.urgency);
      }
      if (item.source === 'care' && item.care) {
        return renderCareCard(item.care, item.urgency);
      }
      return null;
    },
    [renderTaskCard, renderCareCard],
  );

  const renderSection = useCallback(
    (group: UrgencyGroup, items: (UnifiedItem & { urgency: UrgencyGroup })[]) => {
      if (items.length === 0) return null;

      const sectionKeys: Record<UrgencyGroup, string> = {
        overdue: 'pages.tasks.overdue',
        today: 'pages.tasks.today',
        thisWeek: 'pages.tasks.thisWeek',
        future: 'pages.tasks.future',
      };

      const icon = urgencySectionIcon[group];
      const sectionColor = urgencySectionColor[group];

      return (
        <Box
          key={group}
          component="section"
          aria-label={t(sectionKeys[group])}
          sx={{ mb: 3 }}
          data-testid={`task-section-${group}`}
        >
          {/* Section header: icon + label + count badge */}
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 1,
              mb: 1.5,
              // Subtle left accent for the section heading matches urgency colour
              borderLeft: '3px solid',
              borderColor: sectionColor,
              ml: -0.75,
              pl: 1,
            }}
          >
            {icon && (
              <Box sx={{ color: sectionColor, display: 'flex', alignItems: 'center' }} aria-hidden="true">
                {icon}
              </Box>
            )}
            <Typography
              variant="overline"
              component="h2"
              sx={{ color: sectionColor, fontWeight: 700, letterSpacing: 1.2, lineHeight: 1 }}
            >
              {t(sectionKeys[group])}
            </Typography>
            <Chip
              label={items.length}
              size="small"
              sx={{
                height: 20,
                fontSize: '0.7rem',
                minWidth: 24,
                // For overdue: red badge so count is also visually prominent
                ...(group === 'overdue' ? { bgcolor: 'error.main', color: 'error.contrastText' } : {}),
              }}
              aria-label={t('pages.tasks.sectionCount', { count: items.length })}
            />
          </Box>
          {items.map(renderItem)}
        </Box>
      );
    },
    [renderItem, t],
  );

  // Completed tasks live in a distinct, visually muted section below the active
  // urgency groups. They are read-only cards (no start/complete/skip actions,
  // since renderTaskCard only shows actions for pending/in_progress tasks).
  const renderCompletedSection = useCallback(
    (tasks: TaskItem[]) => (
      <Box
        component="section"
        aria-label={t('pages.tasks.completed')}
        sx={{ mb: 3, opacity: 0.85 }}
        data-testid="task-section-completed"
      >
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            mb: 1.5,
            borderLeft: '3px solid',
            borderColor: 'success.main',
            ml: -0.75,
            pl: 1,
          }}
        >
          <Box sx={{ color: 'success.main', display: 'flex', alignItems: 'center' }} aria-hidden="true">
            <DoneAllIcon sx={{ fontSize: 18 }} />
          </Box>
          <Typography
            variant="overline"
            component="h2"
            sx={{ color: 'success.main', fontWeight: 700, letterSpacing: 1.2, lineHeight: 1 }}
          >
            {t('pages.tasks.completed')}
          </Typography>
          <Chip
            label={tasks.length}
            size="small"
            sx={{ height: 20, fontSize: '0.7rem', minWidth: 24 }}
            aria-label={t('pages.tasks.sectionCount', { count: tasks.length })}
          />
        </Box>
        {completedTasksLoading && tasks.length === 0 ? (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, py: 1 }}>
            <CircularProgress size={18} />
            <Typography variant="body2" color="text.secondary">
              {t('common.loading')}
            </Typography>
          </Box>
        ) : tasks.length === 0 ? (
          <Typography variant="body2" color="text.secondary" sx={{ py: 1 }}>
            {t('pages.tasks.noCompletedTasks')}
          </Typography>
        ) : (
          tasks.map((task) => renderTaskCard(task, 'future'))
        )}
      </Box>
    ),
    [renderTaskCard, completedTasksLoading, t],
  );

  // ── Loading ──────────────────────────────────────────────────────────

  // The gate MUST cover every source the card list is built from. The plant
  // list was missing: the skeleton cleared as soon as tasks and care reminders
  // had arrived, then `plantNameMap` filled in and every plant-linked card grew
  // its shortcut row, reflowing the list after the user already saw it. Taps
  // aimed at a card's action row then landed on the container that had moved
  // into place — no handler fires and no error is reported, which is exactly
  // the class of defect a loading indicator exists to prevent.
  const loading = tasksLoading || careLoading || plantsLoading;
  if (loading) return <LoadingSkeleton variant="form" />;

  const totalItems =
    grouped.overdue.length + grouped.today.length + grouped.thisWeek.length + grouped.future.length;

  const taskCount = filtered.filter((i) => i.source === 'task').length;

  const allSelected = allTaskKeys.length > 0 && allTaskKeys.every((k) => selectedKeys.has(k));

  return (
    <Box data-testid="task-queue-page">
      <PageTitle
        title={t('pages.tasks.queueTitle')}
        action={
          bulkMode ? (
            // Bulk mode has exactly one header action; leaving it primary keeps
            // the way out of the mode a single tap on every breakpoint.
            <PageHeaderActions
              primary={{
                label: t('common.cancel'),
                icon: <CloseIcon />,
                variant: 'outlined',
                testId: 'exit-bulk-mode',
                onClick: exitBulkMode,
              }}
            />
          ) : (
            <PageHeaderActions
              /* REQ-032 §2.2: care-checklist print button on the Pflege host
                 page (the /pflege route redirects here). `PrintButton` brings
                 its own download-and-print flow and cannot be reduced to a menu
                 entry, so it stays outside the overflow. */
              extra={
                <PrintButton
                  onPrint={() => downloadCareChecklistPdf()}
                  filename="care-checklist.pdf"
                  label={t('print.careChecklist')}
                  variant="button"
                  sx={{ minHeight: 48 }}
                />
              }
              primary={{
                label: t('pages.tasks.createTask'),
                icon: <AddIcon />,
                variant: 'contained',
                testId: 'create-task-button',
                onClick: () => setCreateOpen(true),
              }}
              secondary={[
                {
                  label: t('pages.tasks.generateReminders'),
                  icon: generateLoading ? <CircularProgress size={16} /> : <RefreshIcon />,
                  variant: 'outlined',
                  disabled: generateLoading,
                  tooltip: t('pages.tasks.generateRemindersHelp'),
                  testId: 'generate-reminders-button',
                  onClick: handleGenerateCareReminders,
                },
                taskCount > 0 && {
                  label: t('pages.tasks.bulkEdit'),
                  icon: <LibraryAddCheckIcon />,
                  variant: 'outlined' as const,
                  testId: 'bulk-mode-button',
                  onClick: () => setBulkMode(true),
                },
              ]}
            />
          )
        }
      />

      {/* Page intro text — UI-NFR-017 / UI-NFR-008 R-038 */}
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3, mt: -1 }}>
        {t('pages.tasks.queueIntro')}
      </Typography>

      {/* REQ-047: spring return assistant — self-gates to the pre_spring season
          phase. Hosted here because the /pflege route redirects to this page. */}
      <SpringReturnAssistant />

      {/* Bulk action bar */}
      {bulkMode && (
        <Paper
          role="toolbar"
          aria-label={t('pages.tasks.bulkActionBarLabel')}
          variant="outlined"
          sx={{ px: 2, py: 1, mb: 2, display: 'flex', gap: 1.5, alignItems: 'center', flexWrap: 'wrap', bgcolor: 'action.hover' }}
          data-testid="bulk-action-bar"
        >
          <Button
            size="small"
            aria-pressed={allSelected}
            startIcon={allSelected ? <CheckBoxIcon /> : <CheckBoxOutlineBlankIcon />}
            onClick={handleSelectAll}
            data-testid="select-all-button"
            sx={{ minHeight: 44 }}
          >
            {allSelected ? t('pages.tasks.deselectAll') : t('pages.tasks.selectAll')}
          </Button>
          <Typography variant="body2" color="text.secondary" sx={{ mr: 'auto' }}>
            {t('pages.tasks.selectedCount', { count: selectedKeys.size })}
          </Typography>
          <Tooltip title={selectedKeys.size === 0 ? t('pages.tasks.bulkNoSelection') : ''}>
            <span>
              <Button
                size="small"
                variant="contained"
                color="success"
                startIcon={bulkLoading ? <CircularProgress size={14} /> : <CheckIcon />}
                onClick={handleBulkComplete}
                disabled={selectedKeys.size === 0 || bulkLoading}
                data-testid="bulk-complete-button"
                sx={{ minHeight: 44 }}
              >
                {t('pages.tasks.bulkComplete')}
              </Button>
            </span>
          </Tooltip>
          <Tooltip title={selectedKeys.size === 0 ? t('pages.tasks.bulkNoSelection') : ''}>
            <span>
              <Button
                size="small"
                variant="outlined"
                startIcon={bulkLoading ? <CircularProgress size={14} /> : <SkipNextIcon />}
                onClick={handleBulkSkip}
                disabled={selectedKeys.size === 0 || bulkLoading}
                data-testid="bulk-skip-button"
                sx={{ minHeight: 44 }}
              >
                {t('pages.tasks.bulkSkip')}
              </Button>
            </span>
          </Tooltip>
          <Tooltip title={selectedKeys.size === 0 ? t('pages.tasks.bulkNoSelection') : ''}>
            <span>
              <Button
                size="small"
                variant="outlined"
                color="error"
                startIcon={bulkLoading ? <CircularProgress size={14} /> : <DeleteOutlineIcon />}
                onClick={handleBulkDelete}
                disabled={selectedKeys.size === 0 || bulkLoading}
                data-testid="bulk-delete-button"
                sx={{ minHeight: 44 }}
              >
                {t('pages.tasks.bulkDelete')}
              </Button>
            </span>
          </Tooltip>
        </Paper>
      )}

      {/* Filter bar */}
      <Paper
        variant="outlined"
        aria-label={t('pages.tasks.filterBarLabel')}
        sx={{ px: { xs: 1.5, sm: 2 }, py: 1.5, mb: 3 }}
      >
        <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap', alignItems: 'center' }}>
          {/* Source filter toggle */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <FilterListIcon sx={{ fontSize: 18, color: 'text.secondary' }} aria-hidden="true" />
            <ToggleButtonGroup
              value={sourceFilter}
              exclusive
              onChange={(_, val) => val && setSourceFilter(val as SourceFilter)}
              size="small"
              aria-label={t('pages.tasks.filterSourceLabel')}
            >
              <ToggleButton value="all" data-testid="filter-all" sx={{ minHeight: 36, px: { xs: 1, sm: 1.5 } }}>
                {t('common.all')}
              </ToggleButton>
              <ToggleButton value="tasks" data-testid="filter-tasks" sx={{ minHeight: 36, px: { xs: 1, sm: 1.5 } }}>
                {t('pages.tasks.title')}
              </ToggleButton>
              <ToggleButton value="care" data-testid="filter-care" sx={{ minHeight: 36, px: { xs: 1, sm: 1.5 } }}>
                {t('nav.pflege')}
              </ToggleButton>
            </ToggleButtonGroup>
          </Box>

          {sourceFilter !== 'care' && (
            <FormControl size="small" sx={{ minWidth: 160, flex: '1 1 160px', maxWidth: 240 }}>
              <InputLabel>{t('pages.tasks.filterByCategory')}</InputLabel>
              <Select
                value={filterCategory}
                label={t('pages.tasks.filterByCategory')}
                onChange={(e) => setFilterCategory(e.target.value)}
                data-testid="filter-category"
              >
                <MenuItem value="">{t('common.all')}</MenuItem>
                {taskCategories.map((c) => (
                  <MenuItem key={c} value={c}>{t(`enums.taskCategory.${c}`)}</MenuItem>
                ))}
              </Select>
            </FormControl>
          )}

          {/* REQ-006 FreeStyle origin filter (#1082) — machine vs. manually
              created tasks. Hidden in the care-only source, which has no tasks. */}
          {sourceFilter !== 'care' && (
            <ToggleButtonGroup
              value={originFilter}
              exclusive
              onChange={(_, val) => val && setOriginFilter(val as OriginFilter)}
              size="small"
              aria-label={t('pages.tasks.filterOrigin')}
            >
              <ToggleButton value="all" data-testid="filter-origin-all" sx={{ minHeight: 36, px: { xs: 1, sm: 1.5 } }}>
                {t('pages.tasks.filterOriginAll')}
              </ToggleButton>
              <ToggleButton value="machine" data-testid="filter-origin-machine" sx={{ minHeight: 36, px: { xs: 1, sm: 1.5 } }}>
                {t('pages.tasks.filterOriginMachine')}
              </ToggleButton>
              <ToggleButton value="user" data-testid="filter-origin-user" sx={{ minHeight: 36, px: { xs: 1, sm: 1.5 } }}>
                {t('pages.tasks.filterOriginUser')}
              </ToggleButton>
            </ToggleButtonGroup>
          )}

          <Autocomplete
            size="small"
            sx={{ minWidth: 200, flex: '1 1 200px', maxWidth: 320 }}
            options={plants}
            getOptionLabel={(p) => getPlantLabel(p)}
            value={plants.find((p) => p.key === filterPlantKey) ?? null}
            onChange={(_, value) => setFilterPlantKey(value?.key ?? null)}
            renderInput={(params) => (
              <TextField {...params} label={t('pages.tasks.filterByPlant')} data-testid="filter-plant" />
            )}
          />

          {hasActiveFilters && (
            <Button
              size="small"
              startIcon={<ClearIcon />}
              onClick={() => { setFilterCategory(''); setFilterPlantKey(null); setOriginFilter('all'); }}
              data-testid="clear-filters-button"
              sx={{ minHeight: 36, whiteSpace: 'nowrap' }}
            >
              {t('common.clearFilters')}
            </Button>
          )}

          {/* Reveal completed tasks (#606) — hidden for the care-only source
              since care reminders have no completed status. */}
          {sourceFilter !== 'care' && (
            <FormControlLabel
              sx={{ ml: { xs: 0, sm: 'auto' }, mr: 0 }}
              control={
                <Switch
                  checked={showCompleted}
                  onChange={(e) => setShowCompleted(e.target.checked)}
                  size="small"
                  data-testid="show-completed-toggle"
                  slotProps={{ input: { 'aria-label': t('pages.tasks.showCompleted') } }}
                />
              }
              label={
                <Box sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5 }}>
                  <DoneAllIcon sx={{ fontSize: 16 }} aria-hidden="true" />
                  <Typography variant="body2">{t('pages.tasks.showCompleted')}</Typography>
                </Box>
              }
            />
          )}
        </Box>

        {/* Active filter summary chips — makes it obvious which filters are applied */}
        {hasActiveFilters && (
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 1 }}>
            {filterCategory && (
              <Chip
                label={t(`enums.taskCategory.${filterCategory}`)}
                size="small"
                onDelete={() => setFilterCategory('')}
                color="primary"
                variant="outlined"
                data-testid="active-filter-category"
              />
            )}
            {originFilter !== 'all' && (
              <Chip
                label={originFilter === 'machine'
                  ? t('pages.tasks.filterOriginMachine')
                  : t('pages.tasks.filterOriginUser')}
                size="small"
                onDelete={() => setOriginFilter('all')}
                color="primary"
                variant="outlined"
                data-testid="active-filter-origin"
              />
            )}
            {filterPlantKey && (
              <Chip
                label={plantNameMap.get(filterPlantKey) ?? filterPlantKey}
                size="small"
                onDelete={() => setFilterPlantKey(null)}
                color="primary"
                variant="outlined"
                icon={<LocalFloristIcon />}
                data-testid="active-filter-plant"
              />
            )}
          </Box>
        )}
      </Paper>

      {/* Content area */}
      {totalItems === 0 && !showCompleted ? (
        hasActiveFilters ? (
          // Contextual empty state when filters are active
          <EmptyState
            illustration={kamiTasks}
            message={t('pages.tasks.noTasksFiltered')}
            description={t('pages.tasks.noTasksFilteredDesc')}
            actionLabel={t('common.clearFilters')}
            onAction={() => { setFilterCategory(''); setFilterPlantKey(null); setOriginFilter('all'); }}
          />
        ) : (
          <EmptyState
            illustration={kamiTasks}
            message={t('pages.tasks.noTasks')}
            description={t('pages.tasks.noTasksDesc')}
            actionLabel={t('pages.tasks.createTask')}
            onAction={() => setCreateOpen(true)}
          />
        )
      ) : (
        <>
          {totalItems === 0 && (
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              {hasActiveFilters ? t('pages.tasks.noTasksFiltered') : t('pages.tasks.noTasks')}
            </Typography>
          )}
          {renderSection('overdue', grouped.overdue)}
          {renderSection('today', grouped.today)}
          {renderSection('thisWeek', grouped.thisWeek)}
          {renderSection('future', grouped.future)}
          {showCompleted && renderCompletedSection(completedFiltered)}
        </>
      )}

      <TaskCreateDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={() => {
          setCreateOpen(false);
          dispatch(fetchTaskQueue());
        }}
      />

      {currentProfile && editPlantKey && (
        <CareProfileEditDialog
          open={editDialogOpen}
          onClose={() => { setEditDialogOpen(false); setEditPlantKey(null); }}
          profile={currentProfile}
          onUpdated={handleProfileUpdated}
        />
      )}

      {confirmEntry && (
        <CareConfirmDialog
          open={confirmDialogOpen}
          onClose={() => { setConfirmDialogOpen(false); setConfirmEntry(null); }}
          onConfirm={handleConfirmSubmit}
          plantName={confirmEntry.plant_name}
          reminderType={confirmEntry.reminder_type}
          loading={careActionLoading === `care-${confirmEntry.plant_key}-${confirmEntry.reminder_type}`}
        />
      )}
    </Box>
  );
}
