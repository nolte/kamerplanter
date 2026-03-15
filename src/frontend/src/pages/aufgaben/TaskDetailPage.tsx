import { useEffect, useState, useCallback, useMemo } from 'react';
import { useTabUrl } from '@/hooks/useTabUrl';
import { useNavigate, useParams, Link as RouterLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import Link from '@mui/material/Link';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Checkbox from '@mui/material/Checkbox';
import Divider from '@mui/material/Divider';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Paper from '@mui/material/Paper';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import TextField from '@mui/material/TextField';
import CircularProgress from '@mui/material/CircularProgress';
import Stack from '@mui/material/Stack';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import CheckIcon from '@mui/icons-material/Check';
import SkipNextIcon from '@mui/icons-material/SkipNext';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import SendIcon from '@mui/icons-material/Send';
import LocalFloristIcon from '@mui/icons-material/LocalFlorist';
import ReplayIcon from '@mui/icons-material/Replay';
import ScheduleIcon from '@mui/icons-material/Schedule';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import AddIcon from '@mui/icons-material/Add';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormActions from '@/components/form/FormActions';
import FormRow from '@/components/form/FormRow';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as taskApi from '@/api/endpoints/tasks';
import * as plantApi from '@/api/endpoints/plantInstances';
import * as speciesApi from '@/api/endpoints/species';
import type { PlantInstance } from '@/api/types';
import type { TaskItem, TaskComment, TaskAuditEntry, ChecklistItem } from '@/api/types';
import PhotoUpload from '@/components/common/PhotoUpload';
import TaskTimer from '@/components/common/TaskTimer';

/**
 * Legacy care tasks stored instruction as "care:<type>:<id>" keys.
 * Resolve these to translated reminder-type labels; return null for normal text.
 */
function resolveCareInstruction(instruction: string, t: (key: string) => string): string | null {
  const match = instruction.match(/^care:([a-z_]+):\d+$/);
  if (!match) return null;
  const translated = t(`enums.reminderType.${match[1]}`);
  if (translated === `enums.reminderType.${match[1]}`) return match[1].replace(/_/g, ' ');
  return translated;
}

const statusColorMap: Record<string, 'default' | 'info' | 'success' | 'warning' | 'error'> = {
  pending: 'default',
  in_progress: 'info',
  completed: 'success',
  skipped: 'warning',
  cancelled: 'error',
  dormant: 'default',
};

const priorityColorMap: Record<string, 'default' | 'info' | 'warning' | 'error'> = {
  low: 'default',
  medium: 'info',
  high: 'warning',
  critical: 'error',
};

const categories = [
  'maintenance', 'feeding', 'training', 'pruning', 'ausgeizen',
  'transplant', 'ipm', 'harvest', 'observation', 'care_reminder',
  'seasonal', 'phenological',
] as const;

const priorities = ['low', 'medium', 'high', 'critical'] as const;

const editSchema = z.object({
  name: z.string().min(1).max(200),
  instruction: z.string(),
  category: z.enum(categories),
  priority: z.enum(priorities),
  due_date: z.string().nullable(),
  estimated_duration_minutes: z.number().int().min(1).nullable(),
  timer_duration_seconds: z.number().int().min(1).nullable(),
  timer_label: z.string().nullable(),
  assigned_to_user_key: z.string().nullable(),
  recurrence_rule: z.string().nullable(),
});

type EditFormData = z.infer<typeof editSchema>;

const completionSchema = z.object({
  completion_notes: z.string().nullable(),
  actual_duration_minutes: z.number().int().min(1).nullable(),
  difficulty_rating: z.number().int().min(1).max(5).nullable(),
  quality_rating: z.number().int().min(1).max(5).nullable(),
});

type CompletionFormData = z.infer<typeof completionSchema>;

/** Labeled value display for the metadata grid */
function MetaItem({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <Box sx={{ minWidth: 0 }}>
      <Typography variant="caption" color="text.disabled" sx={{ display: 'block', mb: 0.25 }}>
        {label}
      </Typography>
      {children}
    </Box>
  );
}

export default function TaskDetailPage() {
  const { key } = useParams<{ key: string }>();
  const { t } = useTranslation();
  const { i18n } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();

  const [task, setTask] = useState<TaskItem | null>(null);
  const [plantName, setPlantName] = useState<string | null>(null);
  const [plantInfo, setPlantInfo] = useState<{ plant: PlantInstance; speciesName: string; cultivarName: string | null } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const [saving, setSaving] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [photoRefs, setPhotoRefs] = useState<string[]>([]);

  // Comments state
  const [comments, setComments] = useState<TaskComment[]>([]);
  const [newComment, setNewComment] = useState('');
  const [editingCommentKey, setEditingCommentKey] = useState<string | null>(null);
  const [editCommentText, setEditCommentText] = useState('');
  const [commentLoading, setCommentLoading] = useState(false);

  // History state
  const [history, setHistory] = useState<TaskAuditEntry[]>([]);

  // Checklist add state
  const [newChecklistText, setNewChecklistText] = useState('');

  const isActionable = task?.status === 'pending' || task?.status === 'in_progress';
  const tabSlugs = useMemo(
    () => isActionable
      ? ['details', 'complete', 'comments', 'history', 'edit'] as const
      : ['details', 'comments', 'history', 'edit'] as const,
    [isActionable],
  );
  const [tab, setTab] = useTabUrl(tabSlugs);

  const {
    control: editControl,
    handleSubmit: handleEditSubmit,
    reset: resetEdit,
    formState: { isDirty },
  } = useForm<EditFormData>({
    resolver: zodResolver(editSchema),
    defaultValues: {
      name: '',
      instruction: '',
      category: 'maintenance',
      priority: 'medium',
      due_date: null,
      estimated_duration_minutes: null,
      timer_duration_seconds: null,
      timer_label: null,
      assigned_to_user_key: null,
      recurrence_rule: null,
    },
  });

  const {
    control: completionControl,
    handleSubmit: handleCompletionSubmit,
    reset: resetCompletion,
  } = useForm<CompletionFormData>({
    resolver: zodResolver(completionSchema),
    defaultValues: {
      completion_notes: null,
      actual_duration_minutes: null,
      difficulty_rating: null,
      quality_rating: null,
    },
  });

  const load = useCallback(async () => {
    if (!key) return;
    setLoading(true);
    try {
      const fetched = await taskApi.getTask(key);
      setTask(fetched);
      setPhotoRefs(fetched.photo_refs ?? []);
      if (fetched.plant_key) {
        plantApi.getPlantInstance(fetched.plant_key)
          .then(async (p) => {
            setPlantName(p.plant_name || p.instance_id);
            try {
              const sp = await speciesApi.getSpecies(p.species_key);
              const speciesName = sp.common_names?.[0] || sp.scientific_name;
              let cultivarName: string | null = null;
              if (p.cultivar_key) {
                const cvList = await speciesApi.listCultivars(p.species_key);
                const cv = cvList.find((c) => c.key === p.cultivar_key);
                if (cv) cultivarName = cv.name;
              }
              setPlantInfo({ plant: p, speciesName, cultivarName });
            } catch {
              setPlantInfo(null);
            }
          })
          .catch(() => setPlantName(null));
      }
      resetEdit({
        name: fetched.name,
        instruction: fetched.instruction,
        category: fetched.category as EditFormData['category'],
        priority: fetched.priority as EditFormData['priority'],
        due_date: fetched.due_date ? fetched.due_date.split('T')[0] : null,
        estimated_duration_minutes: fetched.estimated_duration_minutes,
        timer_duration_seconds: fetched.timer_duration_seconds,
        timer_label: fetched.timer_label,
        assigned_to_user_key: fetched.assigned_to_user_key,
        recurrence_rule: fetched.recurrence_rule,
      });
      resetCompletion({
        completion_notes: fetched.completion_notes,
        actual_duration_minutes: fetched.actual_duration_minutes,
        difficulty_rating: fetched.difficulty_rating,
        quality_rating: fetched.quality_rating,
      });
      setError(null);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }, [key, resetEdit, resetCompletion]);

  const loadComments = useCallback(async () => {
    if (!key) return;
    try {
      const data = await taskApi.listTaskComments(key);
      setComments(data);
    } catch {
      // silently fail
    }
  }, [key]);

  const loadHistory = useCallback(async () => {
    if (!key) return;
    try {
      const data = await taskApi.getTaskHistory(key);
      setHistory(data);
    } catch {
      // silently fail
    }
  }, [key]);

  useEffect(() => {
    load();
  }, [load]);

  // Load comments and history when those tabs become active
  useEffect(() => {
    const commentsTabIndex = isActionable ? 2 : 1;
    const historyTabIndex = isActionable ? 3 : 2;
    if (tab === commentsTabIndex) loadComments();
    if (tab === historyTabIndex) loadHistory();
  }, [tab, isActionable, loadComments, loadHistory]);

  const onSave = async (data: EditFormData) => {
    if (!key) return;
    try {
      setSaving(true);
      await taskApi.updateTask(key, {
        name: data.name,
        instruction: data.instruction,
        category: data.category,
        priority: data.priority,
        due_date: data.due_date,
        estimated_duration_minutes: data.estimated_duration_minutes,
        timer_duration_seconds: data.timer_duration_seconds,
        timer_label: data.timer_label,
        assigned_to_user_key: data.assigned_to_user_key,
        recurrence_rule: data.recurrence_rule,
      });
      notification.success(t('common.save'));
      load();
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  const handleStart = async () => {
    if (!key) return;
    try {
      setActionLoading(true);
      await taskApi.startTask(key);
      notification.success(t('pages.tasks.taskStarted'));
      load();
    } catch (err) {
      handleError(err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleComplete = async (data: CompletionFormData) => {
    if (!key) return;
    try {
      setActionLoading(true);
      await taskApi.completeTask(key, {
        completion_notes: data.completion_notes,
        actual_duration_minutes: data.actual_duration_minutes,
        photo_refs: photoRefs.length > 0 ? photoRefs : undefined,
        difficulty_rating: data.difficulty_rating,
        quality_rating: data.quality_rating,
      });
      notification.success(t('pages.tasks.taskCompleted'));
      load();
    } catch (err) {
      handleError(err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleSkip = async () => {
    if (!key) return;
    try {
      setActionLoading(true);
      await taskApi.skipTask(key);
      notification.success(t('pages.tasks.taskSkipped'));
      load();
    } catch (err) {
      handleError(err);
    } finally {
      setActionLoading(false);
    }
  };

  const onDelete = async () => {
    if (!key) return;
    try {
      await taskApi.deleteTask(key);
      notification.success(t('pages.tasks.taskDeleted'));
      navigate('/aufgaben/queue');
    } catch (err) {
      handleError(err);
    } finally {
      setDeleteOpen(false);
    }
  };

  const handleClone = async () => {
    if (!key) return;
    try {
      setActionLoading(true);
      const cloned = await taskApi.cloneTask(key);
      notification.success(t('pages.tasks.taskCloned'));
      navigate(`/aufgaben/${cloned.key}`);
    } catch (err) {
      handleError(err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleReopen = async () => {
    if (!key) return;
    try {
      setActionLoading(true);
      await taskApi.reopenTask(key);
      notification.success(t('pages.tasks.taskReopened'));
      load();
    } catch (err) {
      handleError(err);
    } finally {
      setActionLoading(false);
    }
  };

  // ── Checklist interactions ──

  const handleChecklistToggle = async (idx: number) => {
    if (!key || !task) return;
    const updated = task.checklist.map((item, i) =>
      i === idx ? { ...item, done: !item.done } : item,
    );
    try {
      await taskApi.updateTask(key, { checklist: updated });
      setTask({ ...task, checklist: updated });
    } catch (err) {
      handleError(err);
    }
  };

  const handleChecklistAdd = async () => {
    if (!key || !task || !newChecklistText.trim()) return;
    const newItem: ChecklistItem = {
      text: newChecklistText.trim(),
      done: false,
      order: task.checklist.length,
    };
    const updated = [...task.checklist, newItem];
    try {
      await taskApi.updateTask(key, { checklist: updated });
      setTask({ ...task, checklist: updated });
      setNewChecklistText('');
    } catch (err) {
      handleError(err);
    }
  };

  // ── Comment actions ──

  const handleAddComment = async () => {
    if (!key || !newComment.trim()) return;
    try {
      setCommentLoading(true);
      await taskApi.createTaskComment(key, newComment.trim());
      setNewComment('');
      loadComments();
    } catch (err) {
      handleError(err);
    } finally {
      setCommentLoading(false);
    }
  };

  const handleUpdateComment = async (commentKey: string) => {
    if (!key || !editCommentText.trim()) return;
    try {
      setCommentLoading(true);
      await taskApi.updateTaskComment(key, commentKey, editCommentText.trim());
      setEditingCommentKey(null);
      loadComments();
    } catch (err) {
      handleError(err);
    } finally {
      setCommentLoading(false);
    }
  };

  const handleDeleteComment = async (commentKey: string) => {
    if (!key) return;
    try {
      await taskApi.deleteTaskComment(key, commentKey);
      loadComments();
    } catch (err) {
      handleError(err);
    }
  };

  const canReopen = task?.status === 'completed' || task?.status === 'skipped';

  if (loading) return <LoadingSkeleton variant="form" />;
  if (error) return <ErrorDisplay error={error} />;
  if (!task) return <ErrorDisplay error={t('errors.notFound')} />;

  const rawInstruction = (i18n.language === 'de' && task.instruction_de) ? task.instruction_de : task.instruction;
  const resolvedInstruction = rawInstruction
    ? resolveCareInstruction(rawInstruction, t) ?? rawInstruction
    : null;

  const commentsTabIndex = isActionable ? 2 : 1;
  const historyTabIndex = isActionable ? 3 : 2;
  const editTabIndex = isActionable ? 4 : 3;

  return (
    <Box data-testid="task-detail-page">
      <UnsavedChangesGuard dirty={isDirty} />

      {/* Header: Title + action buttons */}
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          mb: 2,
          gap: 2,
          flexWrap: 'wrap',
        }}
      >
        <Box>
          <PageTitle title={(i18n.language === 'de' && task.name_de) ? task.name_de : task.name} />
          <Stack direction="row" spacing={1} sx={{ mt: 0.5 }}>
            <Chip
              label={t(`enums.taskStatus.${task.status}`)}
              size="small"
              color={statusColorMap[task.status] ?? 'default'}
            />
            <Chip
              label={t(`enums.taskCategory.${task.category}`)}
              size="small"
              variant="outlined"
            />
            <Chip
              label={t(`enums.taskPriority.${task.priority}`)}
              size="small"
              color={priorityColorMap[task.priority] ?? 'default'}
              variant="outlined"
            />
          </Stack>
        </Box>

        <Stack direction="row" spacing={1} sx={{ flexShrink: 0 }}>
          {task.status === 'pending' && (
            <Button
              variant="outlined"
              size="small"
              startIcon={actionLoading ? <CircularProgress size={16} /> : <PlayArrowIcon />}
              onClick={handleStart}
              disabled={actionLoading}
              data-testid="start-task-button"
            >
              {t('pages.tasks.startTask')}
            </Button>
          )}
          {isActionable && (
            <Button
              variant="text"
              size="small"
              startIcon={actionLoading ? <CircularProgress size={16} /> : <SkipNextIcon />}
              onClick={handleSkip}
              disabled={actionLoading}
              data-testid="skip-task-button"
            >
              {t('pages.tasks.skipTask')}
            </Button>
          )}
          {canReopen && (
            <Button
              variant="outlined"
              size="small"
              startIcon={actionLoading ? <CircularProgress size={16} /> : <ReplayIcon />}
              onClick={handleReopen}
              disabled={actionLoading}
              data-testid="reopen-task-button"
            >
              {t('pages.tasks.reopenTask')}
            </Button>
          )}
          <Button
            variant="outlined"
            size="small"
            startIcon={<ContentCopyIcon />}
            onClick={handleClone}
            disabled={actionLoading}
            data-testid="clone-task-button"
          >
            {t('pages.tasks.cloneTask')}
          </Button>
          <Button
            variant="outlined"
            size="small"
            color="error"
            startIcon={<DeleteIcon />}
            onClick={() => setDeleteOpen(true)}
          >
            {t('common.delete')}
          </Button>
        </Stack>
      </Box>

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label={t('pages.tasks.tabDetails')} />
        {isActionable && <Tab label={t('pages.tasks.tabComplete')} />}
        <Tab label={t('pages.tasks.tabComments')} />
        <Tab label={t('pages.tasks.tabHistory')} />
        <Tab label={t('common.edit')} />
      </Tabs>

      {/* Tab 0: Details */}
      {tab === 0 && (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>

          {/* Metadata grid */}
          <Card variant="outlined">
            <CardContent sx={{ pb: '16px !important' }}>
              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: { xs: '1fr 1fr', sm: 'repeat(auto-fill, minmax(160px, 1fr))' },
                  gap: 2.5,
                }}
              >
                {task.plant_key && (
                  <MetaItem label={t('pages.tasks.plant')}>
                    <Tooltip
                      arrow
                      enterTouchDelay={0}
                      leaveTouchDelay={3000}
                      title={plantInfo ? (
                        <Box sx={{ p: 0.5 }}>
                          <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                            {plantInfo.plant.plant_name || plantInfo.plant.instance_id}
                          </Typography>
                          <Typography variant="caption" display="block">
                            {t('entities.species')}: {plantInfo.speciesName}
                          </Typography>
                          {plantInfo.cultivarName && (
                            <Typography variant="caption" display="block">
                              {t('entities.cultivar')}: {plantInfo.cultivarName}
                            </Typography>
                          )}
                          {plantInfo.plant.current_phase && (
                            <Typography variant="caption" display="block">
                              {t('pages.plantInstances.currentPhase')}: {t(`enums.phaseName.${plantInfo.plant.current_phase}`, { defaultValue: plantInfo.plant.current_phase })}
                            </Typography>
                          )}
                          <Typography variant="caption" display="block" color="text.secondary">
                            ID: {plantInfo.plant.instance_id}
                          </Typography>
                        </Box>
                      ) : ''}
                    >
                      <Link
                        component={RouterLink}
                        to={`/pflanzen/plant-instances/${task.plant_key}`}
                        underline="hover"
                        variant="body2"
                        sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5, fontWeight: 500 }}
                        data-testid="plant-link"
                      >
                        <LocalFloristIcon sx={{ fontSize: 16 }} />
                        {plantName ?? task.plant_key}
                      </Link>
                    </Tooltip>
                  </MetaItem>
                )}

                {task.due_date && (
                  <MetaItem label={t('pages.tasks.dueDate')}>
                    <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <CalendarTodayIcon sx={{ fontSize: 15, color: 'text.secondary' }} />
                      {new Date(task.due_date).toLocaleDateString()}
                    </Typography>
                  </MetaItem>
                )}

                {task.estimated_duration_minutes != null && (
                  <MetaItem label={t('pages.tasks.estimatedDuration')}>
                    <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <ScheduleIcon sx={{ fontSize: 15, color: 'text.secondary' }} />
                      {task.estimated_duration_minutes} min
                    </Typography>
                  </MetaItem>
                )}

                {task.actual_duration_minutes != null && (
                  <MetaItem label={t('pages.tasks.actualDuration')}>
                    <Typography variant="body2">
                      {task.actual_duration_minutes} min
                    </Typography>
                  </MetaItem>
                )}

                {task.assigned_to_user_key && (
                  <MetaItem label={t('pages.tasks.assignedTo')}>
                    <Typography variant="body2">{task.assigned_to_user_key}</Typography>
                  </MetaItem>
                )}

                {task.recurrence_rule && (
                  <MetaItem label={t('pages.tasks.recurrenceRule')}>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
                      {task.recurrence_rule}
                    </Typography>
                  </MetaItem>
                )}

                {task.started_at && (
                  <MetaItem label={t('pages.tasks.startedAt')}>
                    <Typography variant="body2">
                      {new Date(task.started_at).toLocaleString()}
                    </Typography>
                  </MetaItem>
                )}

                {task.completed_at && (
                  <MetaItem label={t('pages.tasks.completedAt')}>
                    <Typography variant="body2">
                      {new Date(task.completed_at).toLocaleString()}
                    </Typography>
                  </MetaItem>
                )}

                {/* Task source */}
                <MetaItem label={t('pages.tasks.source')}>
                  {task.activity_key ? (
                    <Link
                      component={RouterLink}
                      to={`/stammdaten/activities/${task.activity_key}`}
                      underline="hover"
                      variant="body2"
                      sx={{ fontWeight: 500 }}
                    >
                      {t('pages.tasks.sourceActivityPlan')}
                    </Link>
                  ) : task.workflow_execution_key ? (
                    <Typography variant="body2">{t('pages.tasks.sourceWorkflow')}</Typography>
                  ) : task.watering_event_key ? (
                    <Typography variant="body2">{t('pages.tasks.sourceWateringSchedule')}</Typography>
                  ) : task.planting_run_key ? (
                    <Link
                      component={RouterLink}
                      to={`/durchlaeufe/planting-runs/${task.planting_run_key}`}
                      underline="hover"
                      variant="body2"
                      sx={{ fontWeight: 500 }}
                    >
                      {t('pages.tasks.sourcePlantingRun')}
                    </Link>
                  ) : task.category === 'care_reminder' ? (
                    <Typography variant="body2">{t('pages.tasks.sourceCareReminder')}</Typography>
                  ) : (
                    <Typography variant="body2">{t('pages.tasks.sourceManual')}</Typography>
                  )}
                </MetaItem>
              </Box>
            </CardContent>
          </Card>

          {/* Instruction callout */}
          {resolvedInstruction && (
            <Paper
              variant="outlined"
              sx={{
                p: 2,
                bgcolor: 'action.hover',
                borderLeft: '4px solid',
                borderLeftColor: 'primary.main',
              }}
            >
              <Typography variant="caption" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
                <InfoOutlinedIcon sx={{ fontSize: 15 }} />
                {t('pages.tasks.instruction')}
              </Typography>
              <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                {resolvedInstruction}
              </Typography>
            </Paper>
          )}

          {/* Timer */}
          {task.status === 'in_progress' && task.timer_duration_seconds != null && (
            <Card variant="outlined">
              <CardContent>
                <TaskTimer
                  durationSeconds={task.timer_duration_seconds}
                  label={task.timer_label}
                />
              </CardContent>
            </Card>
          )}

          {/* Photos */}
          {task.photo_refs && task.photo_refs.length > 0 && (
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle2" gutterBottom>
                  {t('pages.tasks.photos')}
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  {task.photo_refs.map((ref, i) => (
                    <Box
                      key={ref}
                      component="img"
                      src={ref}
                      alt={`Photo ${i + 1}`}
                      sx={{
                        width: 120,
                        height: 120,
                        objectFit: 'cover',
                        borderRadius: 1,
                        border: '1px solid',
                        borderColor: 'divider',
                      }}
                    />
                  ))}
                </Box>
              </CardContent>
            </Card>
          )}

          {/* Tags */}
          {task.tags && task.tags.length > 0 && (
            <Card variant="outlined">
              <CardContent sx={{ pb: '16px !important' }}>
                <Typography variant="subtitle2" gutterBottom>
                  {t('pages.tasks.tags')}
                </Typography>
                <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
                  {task.tags.map((tag) => (
                    <Chip key={tag} label={tag} size="small" variant="outlined" />
                  ))}
                </Stack>
              </CardContent>
            </Card>
          )}

          {/* Interactive Checklist */}
          {(task.checklist.length > 0 || isActionable) && (
            <Card variant="outlined">
              <CardContent sx={{ pb: '16px !important' }}>
                <Typography variant="subtitle2" gutterBottom>
                  {t('pages.tasks.checklist')}
                </Typography>
                <List dense disablePadding>
                  {[...task.checklist].sort((a, b) => a.order - b.order).map((item, idx) => (
                    <ListItem key={idx} disableGutters sx={{ py: 0 }}>
                      <ListItemIcon sx={{ minWidth: 36 }}>
                        <Checkbox
                          size="small"
                          checked={item.done}
                          onChange={() => handleChecklistToggle(idx)}
                          disabled={!isActionable}
                        />
                      </ListItemIcon>
                      <ListItemText
                        primary={item.text}
                        slotProps={{ primary: { variant: 'body2', sx: item.done ? { textDecoration: 'line-through', color: 'text.disabled' } : {} } }}
                      />
                    </ListItem>
                  ))}
                </List>
                {isActionable && (
                  <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                    <TextField
                      size="small"
                      value={newChecklistText}
                      onChange={(e) => setNewChecklistText(e.target.value)}
                      placeholder={t('pages.tasks.addChecklistItem')}
                      onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); handleChecklistAdd(); } }}
                      sx={{ flex: 1 }}
                    />
                    <IconButton
                      size="small"
                      onClick={handleChecklistAdd}
                      disabled={!newChecklistText.trim()}
                    >
                      <AddIcon />
                    </IconButton>
                  </Box>
                )}
              </CardContent>
            </Card>
          )}

          {/* Completion notes */}
          {task.completion_notes && (
            <Paper
              variant="outlined"
              sx={{
                p: 2,
                borderLeft: '4px solid',
                borderLeftColor: 'success.main',
              }}
            >
              <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: 'block' }}>
                {t('pages.tasks.completionNotes')}
              </Typography>
              <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                {task.completion_notes}
              </Typography>
            </Paper>
          )}

          {/* Ratings */}
          {(task.difficulty_rating != null || task.quality_rating != null) && (
            <Card variant="outlined">
              <CardContent sx={{ pb: '16px !important' }}>
                <Box sx={{ display: 'flex', gap: 4 }}>
                  {task.difficulty_rating != null && (
                    <MetaItem label={t('pages.tasks.difficultyRating')}>
                      <Typography variant="body2">{task.difficulty_rating} / 5</Typography>
                    </MetaItem>
                  )}
                  {task.quality_rating != null && (
                    <MetaItem label={t('pages.tasks.qualityRating')}>
                      <Typography variant="body2">{task.quality_rating} / 5</Typography>
                    </MetaItem>
                  )}
                </Box>
              </CardContent>
            </Card>
          )}
        </Box>
      )}

      {/* Tab: Complete task (only when actionable) */}
      {tab === 1 && isActionable && (
        <Card variant="outlined">
          <CardContent>
            <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 0.5 }}>
              {t('pages.tasks.completeTask')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('pages.tasks.completeIntro')}
            </Typography>
            <form onSubmit={handleCompletionSubmit(handleComplete)}>
              <FormTextField
                name="completion_notes"
                control={completionControl}
                label={t('pages.tasks.completionNotes')}
                multiline
                rows={4}
              />
              <FormNumberField
                name="actual_duration_minutes"
                control={completionControl}
                label={t('pages.tasks.actualDuration')}
                min={1}
                step={1}
                helperText={t('pages.tasks.actualDurationHelper')}
              />
              <FormRow>
                <FormNumberField
                  name="difficulty_rating"
                  control={completionControl}
                  label={t('pages.tasks.difficultyRating')}
                  min={1}
                  max={5}
                  step={1}
                  helperText={t('pages.tasks.ratingHelper')}
                />
                <FormNumberField
                  name="quality_rating"
                  control={completionControl}
                  label={t('pages.tasks.qualityRating')}
                  min={1}
                  max={5}
                  step={1}
                  helperText={t('pages.tasks.ratingHelper')}
                />
              </FormRow>
              {task.requires_photo && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    {t('pages.tasks.photoRequired')}
                  </Typography>
                  <PhotoUpload
                    taskKey={key!}
                    photoRefs={photoRefs}
                    onChange={setPhotoRefs}
                  />
                </Box>
              )}
              {!task.requires_photo && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    {t('pages.tasks.photoUpload')}
                  </Typography>
                  <PhotoUpload
                    taskKey={key!}
                    photoRefs={photoRefs}
                    onChange={setPhotoRefs}
                  />
                </Box>
              )}
              <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
                <Button
                  type="submit"
                  variant="contained"
                  color="success"
                  startIcon={
                    actionLoading ? <CircularProgress size={16} /> : <CheckIcon />
                  }
                  disabled={actionLoading || (task.requires_photo && photoRefs.length === 0)}
                  data-testid="complete-task-submit"
                >
                  {t('pages.tasks.completeTask')}
                </Button>
              </Box>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Tab: Comments */}
      {tab === commentsTabIndex && (
        <Card variant="outlined">
          <CardContent>
            <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
              {t('pages.tasks.tabComments')} ({comments.length})
            </Typography>

            {comments.length === 0 && (
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('pages.tasks.noComments')}
              </Typography>
            )}

            {comments.map((c) => (
              <Paper key={c.key} variant="outlined" sx={{ p: 2, mb: 1.5 }}>
                {editingCommentKey === c.key ? (
                  <Box>
                    <TextField
                      fullWidth
                      size="small"
                      multiline
                      rows={2}
                      value={editCommentText}
                      onChange={(e) => setEditCommentText(e.target.value)}
                    />
                    <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                      <Button
                        size="small"
                        variant="contained"
                        onClick={() => handleUpdateComment(c.key)}
                        disabled={commentLoading || !editCommentText.trim()}
                      >
                        {t('common.save')}
                      </Button>
                      <Button size="small" onClick={() => setEditingCommentKey(null)}>
                        {t('common.cancel')}
                      </Button>
                    </Stack>
                  </Box>
                ) : (
                  <Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                      <Typography variant="caption" color="text.secondary">
                        {c.created_by} &mdash; {c.created_at ? new Date(c.created_at).toLocaleString() : ''}
                      </Typography>
                      <Box>
                        <IconButton
                          size="small"
                          onClick={() => {
                            setEditingCommentKey(c.key);
                            setEditCommentText(c.comment_text);
                          }}
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                        <IconButton size="small" color="error" onClick={() => handleDeleteComment(c.key)}>
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Box>
                    </Box>
                    <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                      {c.comment_text}
                    </Typography>
                  </Box>
                )}
              </Paper>
            ))}

            <Divider sx={{ my: 2 }} />

            <Box sx={{ display: 'flex', gap: 1 }}>
              <TextField
                fullWidth
                size="small"
                multiline
                rows={2}
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                placeholder={t('pages.tasks.addComment')}
              />
              <Button
                variant="contained"
                size="small"
                startIcon={commentLoading ? <CircularProgress size={16} /> : <SendIcon />}
                onClick={handleAddComment}
                disabled={commentLoading || !newComment.trim()}
                sx={{ alignSelf: 'flex-end' }}
              >
                {t('pages.tasks.send')}
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Tab: History */}
      {tab === historyTabIndex && (
        <Card variant="outlined">
          <CardContent>
            <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
              {t('pages.tasks.tabHistory')} ({history.length})
            </Typography>

            {history.length === 0 && (
              <Typography variant="body2" color="text.secondary">
                {t('pages.tasks.noHistory')}
              </Typography>
            )}

            {history.map((entry) => (
              <Paper key={entry.key} variant="outlined" sx={{ p: 1.5, mb: 1 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Box>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      {entry.action}
                      {entry.field && (
                        <Typography component="span" variant="body2" color="text.secondary">
                          {' '}&mdash; {entry.field}
                        </Typography>
                      )}
                    </Typography>
                    {(entry.old_value || entry.new_value) && (
                      <Typography variant="caption" color="text.secondary">
                        {entry.old_value && <><s>{entry.old_value}</s> &rarr; </>}
                        {entry.new_value}
                      </Typography>
                    )}
                  </Box>
                  <Typography variant="caption" color="text.secondary" sx={{ whiteSpace: 'nowrap', ml: 2 }}>
                    {entry.changed_by} &mdash; {entry.changed_at ? new Date(entry.changed_at).toLocaleString() : ''}
                  </Typography>
                </Box>
              </Paper>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Tab: Edit */}
      {tab === editTabIndex && (
        <Card variant="outlined">
          <CardContent>
            <form onSubmit={handleEditSubmit(onSave)}>
              <Box sx={{ maxWidth: 900 }}>
                <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
                  {t('pages.tasks.sectionTask')}
                </Typography>
                <FormTextField
                  name="name"
                  control={editControl}
                  label={t('pages.tasks.name')}
                  required
                />
                <FormTextField
                  name="instruction"
                  control={editControl}
                  label={t('pages.tasks.instruction')}
                  multiline
                  rows={4}
                />
                <FormSelectField
                  name="category"
                  control={editControl}
                  label={t('pages.tasks.category')}
                  options={categories.map((v) => ({
                    value: v,
                    label: t(`enums.taskCategory.${v}`),
                  }))}
                />
                <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
                  {t('pages.tasks.sectionScheduling')}
                </Typography>
                <FormRow>
                  <FormTextField
                    name="due_date"
                    control={editControl}
                    label={t('pages.tasks.dueDate')}
                    type="date"
                  />
                  <FormSelectField
                    name="priority"
                    control={editControl}
                    label={t('pages.tasks.priority')}
                    helperText={t('pages.tasks.priorityHelper')}
                    options={priorities.map((v) => ({
                      value: v,
                      label: t(`enums.taskPriority.${v}`),
                    }))}
                  />
                </FormRow>
                <Box sx={{ display: 'flex', gap: 2 }}>
                  <FormNumberField
                    name="estimated_duration_minutes"
                    control={editControl}
                    label={t('pages.tasks.estimatedDuration')}
                    min={1}
                    step={1}
                    helperText={t('pages.tasks.estimatedDurationHelper')}
                  />
                  <FormNumberField
                    name="timer_duration_seconds"
                    control={editControl}
                    label={t('pages.tasks.timerDuration')}
                    min={1}
                    step={1}
                    helperText={t('pages.tasks.timerDurationHelper')}
                  />
                </Box>
                <FormTextField
                  name="timer_label"
                  control={editControl}
                  label={t('pages.tasks.timerLabel')}
                />
                <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
                  {t('pages.tasks.sectionAssignment')}
                </Typography>
                <FormTextField
                  name="assigned_to_user_key"
                  control={editControl}
                  label={t('pages.tasks.assignedTo')}
                  helperText={t('pages.tasks.assignedToHelper')}
                />
                <FormTextField
                  name="recurrence_rule"
                  control={editControl}
                  label={t('pages.tasks.recurrenceRule')}
                  helperText={t('pages.tasks.recurrenceRuleHelper')}
                />
                <FormActions
                  onCancel={() => resetEdit()}
                  loading={saving}
                  disabled={!isDirty}
                />
              </Box>
            </form>
          </CardContent>
        </Card>
      )}

      <ConfirmDialog
        open={deleteOpen}
        title={t('common.delete')}
        message={t('common.deleteConfirm', { name: task.name })}
        onConfirm={onDelete}
        onCancel={() => setDeleteOpen(false)}
        destructive
      />
    </Box>
  );
}
