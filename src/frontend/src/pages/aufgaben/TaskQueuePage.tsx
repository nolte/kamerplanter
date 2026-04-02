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
import AddIcon from '@mui/icons-material/Add';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import CheckIcon from '@mui/icons-material/Check';
import CheckBoxOutlineBlankIcon from '@mui/icons-material/CheckBoxOutlineBlank';
import CheckBoxIcon from '@mui/icons-material/CheckBox';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import SkipNextIcon from '@mui/icons-material/SkipNext';
import RefreshIcon from '@mui/icons-material/Refresh';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import ClearIcon from '@mui/icons-material/Clear';
import EditIcon from '@mui/icons-material/Edit';
import CloseIcon from '@mui/icons-material/Close';
import ScheduleIcon from '@mui/icons-material/Schedule';
import LocalFloristIcon from '@mui/icons-material/LocalFlorist';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import SnoozeIcon from '@mui/icons-material/Snooze';
import OpacityIcon from '@mui/icons-material/Opacity';
import YardIcon from '@mui/icons-material/Yard';
import SwapVertIcon from '@mui/icons-material/SwapVert';
import BugReportIcon from '@mui/icons-material/BugReport';
import PlaceIcon from '@mui/icons-material/Place';
import WaterDropIcon from '@mui/icons-material/WaterDrop';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import EmptyState from '@/components/common/EmptyState';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchTaskQueue, fetchOverdueTasks } from '@/store/slices/tasksSlice';
import { fetchDashboard, fetchProfile } from '@/store/slices/careRemindersSlice';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as taskApi from '@/api/endpoints/tasks';
import * as careApi from '@/api/endpoints/careReminders';
import * as plantApi from '@/api/endpoints/plantInstances';
import type { TaskItem, PlantInstance, CareDashboardEntry, ReminderType, CareProfile } from '@/api/types';
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

  // Task state
  const { taskQueue, loading: tasksLoading } = useAppSelector((s) => s.tasks);
  const [createOpen, setCreateOpen] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [generateLoading, setGenerateLoading] = useState(false);
  const [filterCategory, setFilterCategory] = useState<string>('');
  const [filterPlantKey, setFilterPlantKey] = useState<string | null>(null);
  const [plants, setPlants] = useState<PlantInstance[]>([]);
  const [sourceFilter, setSourceFilter] = useState<SourceFilter>('all');

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
    plantApi.listPlantInstances(0, 200).then(setPlants).catch(() => {});
  }, [dispatch]);

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
      } catch (err) {
        handleError(err);
      } finally {
        setActionLoading(null);
      }
    },
    [dispatch, notification, handleError, t],
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
      }
    },
    [selectedKeys, dispatch, notification, handleError, t],
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
      map.set(p.key, p.plant_name || p.instance_id);
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
    for (const t of taskQueue) {
      if (t.category !== 'care_reminder') continue;
      const parts = t.name?.split('\u2014');
      const reminderType = parts && parts.length > 1 ? parts[1].trim() : undefined;
      if (!reminderType) continue;

      if (t.entity_type === 'plant_instance' && t.entity_key) {
        taskPlantTypes.add(`${t.entity_key}-${reminderType}`);
      }
      // Fallback: use the plant name prefix for matching (handles entity_key=null tasks)
      const namePrefix = parts[0].trim();
      if (namePrefix) {
        taskNameTypes.add(`${namePrefix}-${reminderType}`);
      }
    }

    for (const entry of careDashboard) {
      if (entry.urgency === 'not_due') continue;
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
  }, [taskQueue, careDashboard, filterCategory, filterPlantKey]);

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

  // ── Render helpers ───────────────────────────────────────────────────

  const renderTaskCard = useCallback(
    (task: TaskItem, urgency: UrgencyGroup) => {
      const isLoading = actionLoading === task.key;
      const plantName = (task.entity_type === 'plant_instance' && task.entity_key) ? plantNameMap.get(task.entity_key) : undefined;
      const isSelected = selectedKeys.has(task.key);
      const isPending = task.status === 'pending';
      const isInProgress = task.status === 'in_progress';
      const isActionable = isPending || isInProgress;

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
            <Box
              sx={{
                width: 4,
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
                />
              </Box>
            )}

            <Box sx={{ flex: 1, minWidth: 0 }}>
              <CardActionArea
                onClick={bulkMode ? () => toggleSelection(task.key) : () => navigate(`/aufgaben/tasks/${task.key}`)}
                data-testid={`task-card-${task.key}`}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', px: 2, py: 1.5, gap: 2 }}>
                  <Box sx={{ flex: 1, minWidth: 0 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.25 }}>
                      <Typography variant="subtitle2" noWrap sx={{ fontWeight: isInProgress ? 700 : 600 }}>
                        {(i18n.language === 'de' && task.name_de) ? task.name_de : task.name}
                      </Typography>
                      {isInProgress && (
                        <Chip
                          label={t('enums.taskStatus.in_progress')}
                          size="small"
                          color="info"
                          sx={{ height: 20, fontSize: '0.7rem' }}
                        />
                      )}
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexWrap: 'wrap' }}>
                      {plantName && task.entity_key && task.entity_type === 'plant_instance' && (
                        <Link
                          component={RouterLink}
                          to={`/pflanzen/plant-instances/${task.entity_key}`}
                          variant="caption"
                          color="text.secondary"
                          underline="hover"
                          onClick={(e: React.MouseEvent) => e.stopPropagation()}
                          sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5 }}
                          data-testid={`plant-link-${task.key}`}
                        >
                          <LocalFloristIcon sx={{ fontSize: 14 }} />
                          {plantName}
                        </Link>
                      )}
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
                  <Stack direction="row" spacing={1} alignItems="center" sx={{ flexShrink: 0 }}>
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
            </Box>

            {!bulkMode && isActionable && (
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 0.25,
                  pr: 1,
                  borderLeft: '1px solid',
                  borderColor: 'divider',
                }}
                onClick={(e) => e.stopPropagation()}
              >
                {isPending && (
                  <Tooltip title={t('pages.tasks.startTask')}>
                    <IconButton size="small" onClick={() => handleStart(task.key)} disabled={isLoading} data-testid={`start-task-${task.key}`}>
                      {isLoading ? <CircularProgress size={18} /> : <PlayArrowIcon fontSize="small" />}
                    </IconButton>
                  </Tooltip>
                )}
                <Tooltip title={t('pages.tasks.completeTask')}>
                  <IconButton size="small" color="success" onClick={() => handleComplete(task.key)} disabled={isLoading} data-testid={`complete-task-${task.key}`}>
                    {isLoading ? <CircularProgress size={18} /> : <CheckIcon fontSize="small" />}
                  </IconButton>
                </Tooltip>
                <Tooltip title={t('pages.tasks.skipTask')}>
                  <IconButton size="small" onClick={() => handleSkip(task.key)} disabled={isLoading} data-testid={`skip-task-${task.key}`}>
                    {isLoading ? <CircularProgress size={18} /> : <SkipNextIcon fontSize="small" />}
                  </IconButton>
                </Tooltip>
              </Box>
            )}
          </Box>
        </Card>
      );
    },
    [actionLoading, navigate, handleStart, handleComplete, handleSkip, t, i18n.language, plantNameMap, bulkMode, selectedKeys, toggleSelection],
  );

  const renderCareCard = useCallback(
    (entry: CareDashboardEntry, urgency: UrgencyGroup) => {
      const id = `care-${entry.plant_key}-${entry.reminder_type}`;
      const isLoading = careActionLoading === id;

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
            <Box
              sx={{
                width: 4,
                flexShrink: 0,
                bgcolor: urgencyBorderColor[urgency],
                borderRadius: '4px 0 0 4px',
              }}
            />

            <Box sx={{ flex: 1, minWidth: 0, display: 'flex', alignItems: 'center', px: 2, py: 1.5, gap: 2 }}>
              {/* Reminder type icon */}
              <Box sx={{ color: urgencySectionColor[urgency], flexShrink: 0 }}>
                {getReminderIcon(entry.reminder_type)}
              </Box>

              {/* Content */}
              <Box sx={{ flex: 1, minWidth: 0 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.25 }}>
                  <Typography variant="subtitle2" noWrap sx={{ fontWeight: 600 }}>
                    {t(`enums.reminderType.${entry.reminder_type}`)}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexWrap: 'wrap' }}>
                  <Link
                    component={RouterLink}
                    to={`/pflanzen/plant-instances/${entry.plant_key}`}
                    variant="caption"
                    color="text.secondary"
                    underline="hover"
                    sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5 }}
                  >
                    <LocalFloristIcon sx={{ fontSize: 14 }} />
                    {entry.plant_name}
                  </Link>
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
            </Box>

            {/* Actions */}
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 0.25,
                pr: 1,
                borderLeft: '1px solid',
                borderColor: 'divider',
              }}
            >
              <Tooltip title={t('pages.pflege.editProfile')}>
                <IconButton size="small" onClick={() => handleEditProfile(entry.plant_key)}>
                  <EditIcon fontSize="small" />
                </IconButton>
              </Tooltip>
              <Tooltip title={t('pages.pflege.confirmAction')}>
                <span>
                  <IconButton size="small" color="success" onClick={() => handleConfirmClick(entry)} disabled={isLoading}>
                    {isLoading ? <CircularProgress size={18} /> : <CheckCircleIcon fontSize="small" />}
                  </IconButton>
                </span>
              </Tooltip>
              <Tooltip title={t('pages.pflege.snoozeAction')}>
                <span>
                  <IconButton size="small" onClick={() => handleSnooze(entry.plant_key, entry.reminder_type)} disabled={isLoading}>
                    {isLoading ? <CircularProgress size={18} /> : <SnoozeIcon fontSize="small" />}
                  </IconButton>
                </span>
              </Tooltip>
            </Box>
          </Box>
        </Card>
      );
    },
    [careActionLoading, handleConfirmClick, handleSnooze, handleEditProfile, t],
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

      return (
        <Box key={group} sx={{ mb: 3 }} data-testid={`task-section-${group}`}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5, pl: 0.5 }}>
            {group === 'overdue' && (
              <WarningAmberIcon sx={{ color: urgencySectionColor[group], fontSize: 20 }} />
            )}
            <Typography
              variant="overline"
              sx={{ color: urgencySectionColor[group], fontWeight: 700, letterSpacing: 1.2 }}
            >
              {t(sectionKeys[group])}
            </Typography>
            <Chip label={items.length} size="small" sx={{ height: 20, fontSize: '0.7rem', minWidth: 24 }} />
          </Box>
          {items.map(renderItem)}
        </Box>
      );
    },
    [renderItem, t],
  );

  // ── Loading ──────────────────────────────────────────────────────────

  const loading = tasksLoading || careLoading;
  if (loading) return <LoadingSkeleton variant="form" />;

  const totalItems =
    grouped.overdue.length + grouped.today.length + grouped.thisWeek.length + grouped.future.length;

  const taskCount = filtered.filter((i) => i.source === 'task').length;

  const allSelected = allTaskKeys.length > 0 && allTaskKeys.every((k) => selectedKeys.has(k));

  return (
    <Box data-testid="task-queue-page">
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 1, mb: 1 }}>
        <PageTitle title={t('pages.tasks.queueTitle')} />
        <Box sx={{ display: 'flex', gap: 1 }}>
          {!bulkMode && (
            <>
              <Button
                variant="outlined"
                size="small"
                startIcon={generateLoading ? <CircularProgress size={16} /> : <RefreshIcon />}
                onClick={handleGenerateCareReminders}
                disabled={generateLoading}
                data-testid="generate-reminders-button"
              >
                {t('pages.tasks.generateReminders')}
              </Button>
              {taskCount > 0 && (
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={<EditIcon />}
                  onClick={() => setBulkMode(true)}
                  data-testid="bulk-mode-button"
                >
                  {t('pages.tasks.bulkEdit')}
                </Button>
              )}
              <Button
                variant="contained"
                size="small"
                startIcon={<AddIcon />}
                onClick={() => setCreateOpen(true)}
                data-testid="create-task-button"
              >
                {t('pages.tasks.createTask')}
              </Button>
            </>
          )}
          {bulkMode && (
            <Button
              variant="outlined"
              size="small"
              startIcon={<CloseIcon />}
              onClick={exitBulkMode}
              data-testid="exit-bulk-mode"
            >
              {t('common.cancel')}
            </Button>
          )}
        </Box>
      </Box>

      {/* Bulk action bar */}
      {bulkMode && (
        <Paper
          variant="outlined"
          sx={{ px: 2, py: 1, mb: 2, display: 'flex', gap: 1.5, alignItems: 'center', flexWrap: 'wrap', bgcolor: 'action.hover' }}
          data-testid="bulk-action-bar"
        >
          <Button
            size="small"
            startIcon={allSelected ? <CheckBoxIcon /> : <CheckBoxOutlineBlankIcon />}
            onClick={handleSelectAll}
            data-testid="select-all-button"
          >
            {allSelected ? t('pages.tasks.deselectAll') : t('pages.tasks.selectAll')}
          </Button>
          <Typography variant="body2" color="text.secondary" sx={{ mr: 'auto' }}>
            {t('pages.tasks.selectedCount', { count: selectedKeys.size })}
          </Typography>
          <Button size="small" variant="contained" color="success" startIcon={bulkLoading ? <CircularProgress size={14} /> : <CheckIcon />} onClick={handleBulkComplete} disabled={selectedKeys.size === 0 || bulkLoading} data-testid="bulk-complete-button">
            {t('pages.tasks.bulkComplete')}
          </Button>
          <Button size="small" variant="outlined" startIcon={bulkLoading ? <CircularProgress size={14} /> : <SkipNextIcon />} onClick={handleBulkSkip} disabled={selectedKeys.size === 0 || bulkLoading} data-testid="bulk-skip-button">
            {t('pages.tasks.bulkSkip')}
          </Button>
          <Button size="small" variant="outlined" color="error" startIcon={bulkLoading ? <CircularProgress size={14} /> : <DeleteOutlineIcon />} onClick={handleBulkDelete} disabled={selectedKeys.size === 0 || bulkLoading} data-testid="bulk-delete-button">
            {t('pages.tasks.bulkDelete')}
          </Button>
        </Paper>
      )}

      {/* Source filter + category/plant filters */}
      <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap', alignItems: 'center' }}>
        <ToggleButtonGroup
          value={sourceFilter}
          exclusive
          onChange={(_, val) => val && setSourceFilter(val as SourceFilter)}
          size="small"
        >
          <ToggleButton value="all" data-testid="filter-all">
            {t('common.all')}
          </ToggleButton>
          <ToggleButton value="tasks" data-testid="filter-tasks">
            {t('pages.tasks.title')}
          </ToggleButton>
          <ToggleButton value="care" data-testid="filter-care">
            {t('nav.pflege')}
          </ToggleButton>
        </ToggleButtonGroup>

        {sourceFilter !== 'care' && (
          <FormControl size="small" sx={{ minWidth: 180 }}>
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
        <Autocomplete
          size="small"
          sx={{ minWidth: 220 }}
          options={plants}
          getOptionLabel={(p) =>
            p.plant_name ? `${p.instance_id} - ${p.plant_name}` : p.instance_id
          }
          value={plants.find((p) => p.key === filterPlantKey) ?? null}
          onChange={(_, value) => setFilterPlantKey(value?.key ?? null)}
          renderInput={(params) => (
            <TextField {...params} label={t('pages.tasks.filterByPlant')} data-testid="filter-plant" />
          )}
        />
        {(filterCategory || filterPlantKey) && (
          <Button
            size="small"
            startIcon={<ClearIcon />}
            onClick={() => { setFilterCategory(''); setFilterPlantKey(null); }}
          >
            {t('common.clearFilters')}
          </Button>
        )}
      </Box>

      {totalItems === 0 ? (
        <EmptyState
          illustration={kamiTasks}
          message={t('pages.tasks.noTasks')}
          actionLabel={t('pages.tasks.createTask')}
          onAction={() => setCreateOpen(true)}
        />
      ) : (
        <>
          {renderSection('overdue', grouped.overdue)}
          {renderSection('today', grouped.today)}
          {renderSection('thisWeek', grouped.thisWeek)}
          {renderSection('future', grouped.future)}
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
