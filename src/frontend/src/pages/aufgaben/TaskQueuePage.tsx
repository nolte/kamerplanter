import { useEffect, useState, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardActionArea from '@mui/material/CardActionArea';
import Chip from '@mui/material/Chip';
import Typography from '@mui/material/Typography';
import CircularProgress from '@mui/material/CircularProgress';
import AddIcon from '@mui/icons-material/Add';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import CheckIcon from '@mui/icons-material/Check';
import SkipNextIcon from '@mui/icons-material/SkipNext';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import EmptyState from '@/components/common/EmptyState';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchTaskQueue, fetchOverdueTasks } from '@/store/slices/tasksSlice';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as taskApi from '@/api/endpoints/tasks';
import type { TaskItem } from '@/api/types';
import TaskCreateDialog from './TaskCreateDialog';

type UrgencyGroup = 'overdue' | 'today' | 'thisWeek' | 'future';

interface GroupedTasks {
  overdue: TaskItem[];
  today: TaskItem[];
  thisWeek: TaskItem[];
  future: TaskItem[];
}

function getUrgencyGroup(task: TaskItem, now: Date): UrgencyGroup {
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

const statusColorMap: Record<string, 'default' | 'info' | 'success' | 'warning' | 'error'> = {
  pending: 'default',
  in_progress: 'info',
  completed: 'success',
  skipped: 'warning',
  cancelled: 'error',
};

const priorityColorMap: Record<string, 'default' | 'info' | 'warning' | 'error'> = {
  low: 'default',
  medium: 'info',
  high: 'warning',
  critical: 'error',
};

const sectionColorMap: Record<UrgencyGroup, string> = {
  overdue: 'error.main',
  today: 'warning.main',
  thisWeek: 'info.main',
  future: 'text.secondary',
};

export default function TaskQueuePage() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const notification = useNotification();
  const { handleError } = useApiError();
  const { taskQueue, loading } = useAppSelector((s) => s.tasks);
  const [createOpen, setCreateOpen] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  useEffect(() => {
    dispatch(fetchTaskQueue());
    dispatch(fetchOverdueTasks());
  }, [dispatch]);

  const grouped = useMemo<GroupedTasks>(() => {
    const now = new Date();
    const groups: GroupedTasks = { overdue: [], today: [], thisWeek: [], future: [] };
    for (const task of taskQueue) {
      const group = getUrgencyGroup(task, now);
      groups[group].push(task);
    }
    return groups;
  }, [taskQueue]);

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
      } catch (err) {
        handleError(err);
      } finally {
        setActionLoading(null);
      }
    },
    [dispatch, notification, handleError, t],
  );

  const renderTaskCard = useCallback(
    (task: TaskItem) => {
      const isLoading = actionLoading === task.key;
      return (
        <Card key={task.key} sx={{ mb: 1 }} data-testid="task-card">
          <CardActionArea
            onClick={() => navigate(`/aufgaben/tasks/${task.key}`)}
            data-testid={`task-card-${task.key}`}
          >
            <CardContent sx={{ pb: 1 }}>
              <Box
                sx={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  flexWrap: 'wrap',
                  gap: 1,
                }}
              >
                <Typography variant="subtitle1" component="span">
                  {task.name}
                </Typography>
                <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                  <Chip
                    label={t(`enums.taskCategory.${task.category}`)}
                    size="small"
                    variant="outlined"
                  />
                  <Chip
                    label={t(`enums.taskPriority.${task.priority}`)}
                    size="small"
                    color={priorityColorMap[task.priority] ?? 'default'}
                  />
                  <Chip
                    label={t(`enums.taskStatus.${task.status}`)}
                    size="small"
                    color={statusColorMap[task.status] ?? 'default'}
                  />
                </Box>
              </Box>
              {task.due_date && (
                <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                  {t('pages.tasks.dueDate')}: {new Date(task.due_date).toLocaleDateString()}
                </Typography>
              )}
              {task.estimated_duration_minutes != null && (
                <Typography variant="body2" color="text.secondary">
                  {t('pages.tasks.estimatedDuration')}: {task.estimated_duration_minutes} min
                </Typography>
              )}
            </CardContent>
          </CardActionArea>
          <Box
            sx={{ display: 'flex', gap: 1, px: 2, pb: 1.5 }}
            onClick={(e) => e.stopPropagation()}
          >
            {task.status === 'pending' && (
              <Button
                size="small"
                variant="outlined"
                startIcon={
                  isLoading ? <CircularProgress size={14} /> : <PlayArrowIcon />
                }
                onClick={() => handleStart(task.key)}
                disabled={isLoading}
                data-testid={`start-task-${task.key}`}
              >
                {t('pages.tasks.startTask')}
              </Button>
            )}
            {(task.status === 'pending' || task.status === 'in_progress') && (
              <Button
                size="small"
                variant="contained"
                color="success"
                startIcon={
                  isLoading ? <CircularProgress size={14} /> : <CheckIcon />
                }
                onClick={() => handleComplete(task.key)}
                disabled={isLoading}
                data-testid={`complete-task-${task.key}`}
              >
                {t('pages.tasks.completeTask')}
              </Button>
            )}
            {(task.status === 'pending' || task.status === 'in_progress') && (
              <Button
                size="small"
                variant="text"
                startIcon={
                  isLoading ? <CircularProgress size={14} /> : <SkipNextIcon />
                }
                onClick={() => handleSkip(task.key)}
                disabled={isLoading}
                data-testid={`skip-task-${task.key}`}
              >
                {t('pages.tasks.skipTask')}
              </Button>
            )}
          </Box>
        </Card>
      );
    },
    [actionLoading, navigate, handleStart, handleComplete, handleSkip, t],
  );

  const renderSection = useCallback(
    (group: UrgencyGroup, tasks: TaskItem[]) => {
      if (tasks.length === 0) return null;

      const sectionKeys: Record<UrgencyGroup, string> = {
        overdue: 'pages.tasks.overdue',
        today: 'pages.tasks.today',
        thisWeek: 'pages.tasks.thisWeek',
        future: 'pages.tasks.future',
      };

      return (
        <Box key={group} sx={{ mb: 3 }} data-testid={`task-section-${group}`}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            {group === 'overdue' && (
              <WarningAmberIcon sx={{ color: sectionColorMap[group] }} />
            )}
            <Typography
              variant="h6"
              sx={{ color: sectionColorMap[group] }}
            >
              {t(sectionKeys[group])}
            </Typography>
            <Chip label={tasks.length} size="small" />
          </Box>
          {tasks.map(renderTaskCard)}
        </Box>
      );
    },
    [renderTaskCard, t],
  );

  if (loading) return <LoadingSkeleton variant="form" />;

  const totalTasks =
    grouped.overdue.length +
    grouped.today.length +
    grouped.thisWeek.length +
    grouped.future.length;

  return (
    <Box data-testid="task-queue-page">
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: 1,
        }}
      >
        <PageTitle title={t('pages.tasks.queueTitle')} />
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateOpen(true)}
          data-testid="create-task-button"
        >
          {t('pages.tasks.createTask')}
        </Button>
      </Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        {t('pages.tasks.queueIntro')}
      </Typography>

      {totalTasks === 0 ? (
        <EmptyState
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
    </Box>
  );
}
