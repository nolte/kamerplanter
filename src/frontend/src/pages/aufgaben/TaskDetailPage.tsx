import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableRow from '@mui/material/TableRow';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import CircularProgress from '@mui/material/CircularProgress';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import CheckIcon from '@mui/icons-material/Check';
import SkipNextIcon from '@mui/icons-material/SkipNext';
import DeleteIcon from '@mui/icons-material/Delete';
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
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as taskApi from '@/api/endpoints/tasks';
import type { TaskItem } from '@/api/types';

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

const categories = [
  'maintenance', 'watering', 'feeding', 'training', 'pest_control',
  'harvest', 'pruning', 'transplant', 'monitoring', 'cleaning',
] as const;

const priorities = ['low', 'medium', 'high', 'critical'] as const;

const editSchema = z.object({
  name: z.string().min(1).max(200),
  instruction: z.string(),
  category: z.enum(categories),
  priority: z.enum(priorities),
  due_date: z.string().nullable(),
  estimated_duration_minutes: z.number().int().min(1).nullable(),
});

type EditFormData = z.infer<typeof editSchema>;

const completionSchema = z.object({
  completion_notes: z.string().nullable(),
  actual_duration_minutes: z.number().int().min(1).nullable(),
});

type CompletionFormData = z.infer<typeof completionSchema>;

export default function TaskDetailPage() {
  const { key } = useParams<{ key: string }>();
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();

  const [task, setTask] = useState<TaskItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState(0);
  const [saving, setSaving] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

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
    },
  });

  const load = useCallback(async () => {
    if (!key) return;
    setLoading(true);
    try {
      const fetched = await taskApi.getTask(key);
      setTask(fetched);
      resetEdit({
        name: fetched.name,
        instruction: fetched.instruction,
        category: fetched.category as EditFormData['category'],
        priority: fetched.priority as EditFormData['priority'],
        due_date: fetched.due_date ? fetched.due_date.split('T')[0] : null,
        estimated_duration_minutes: fetched.estimated_duration_minutes,
      });
      resetCompletion({
        completion_notes: fetched.completion_notes,
        actual_duration_minutes: fetched.actual_duration_minutes,
      });
      setError(null);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }, [key, resetEdit, resetCompletion]);

  useEffect(() => {
    load();
  }, [load]);

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
    notification.info(t('pages.tasks.deleteNotSupported'));
    setDeleteOpen(false);
  };

  if (loading) return <LoadingSkeleton variant="form" />;
  if (error) return <ErrorDisplay error={error} />;
  if (!task) return <ErrorDisplay error={t('errors.notFound')} />;

  const isActionable = task.status === 'pending' || task.status === 'in_progress';

  return (
    <Box data-testid="task-detail-page">
      <UnsavedChangesGuard dirty={isDirty} />
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: 2,
        }}
      >
        <PageTitle title={task.name} />
        <Box sx={{ display: 'flex', gap: 1 }}>
          {task.status === 'pending' && (
            <Button
              variant="outlined"
              startIcon={
                actionLoading ? <CircularProgress size={16} /> : <PlayArrowIcon />
              }
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
              startIcon={
                actionLoading ? <CircularProgress size={16} /> : <SkipNextIcon />
              }
              onClick={handleSkip}
              disabled={actionLoading}
              data-testid="skip-task-button"
            >
              {t('pages.tasks.skipTask')}
            </Button>
          )}
          <Button
            variant="outlined"
            color="error"
            startIcon={<DeleteIcon />}
            onClick={() => setDeleteOpen(true)}
          >
            {t('common.delete')}
          </Button>
        </Box>
      </Box>

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label={t('pages.tasks.tabDetails')} />
        {isActionable && <Tab label={t('pages.tasks.tabComplete')} />}
        <Tab label={t('common.edit')} />
      </Tabs>

      {/* Tab 0: Details */}
      {tab === 0 && (
        <Box>
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {t('pages.tasks.tabDetails')}
              </Typography>
              <Table size="small" aria-label={t('pages.tasks.tabDetails')}>
                <TableBody>
                  <TableRow>
                    <TableCell component="th">{t('pages.tasks.status')}</TableCell>
                    <TableCell>
                      <Chip
                        label={t(`enums.taskStatus.${task.status}`)}
                        size="small"
                        color={statusColorMap[task.status] ?? 'default'}
                      />
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell component="th">{t('pages.tasks.category')}</TableCell>
                    <TableCell>
                      <Chip
                        label={t(`enums.taskCategory.${task.category}`)}
                        size="small"
                        variant="outlined"
                      />
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell component="th">{t('pages.tasks.priority')}</TableCell>
                    <TableCell>
                      <Chip
                        label={t(`enums.taskPriority.${task.priority}`)}
                        size="small"
                        color={priorityColorMap[task.priority] ?? 'default'}
                      />
                    </TableCell>
                  </TableRow>
                  {task.due_date && (
                    <TableRow>
                      <TableCell component="th">{t('pages.tasks.dueDate')}</TableCell>
                      <TableCell>{new Date(task.due_date).toLocaleDateString()}</TableCell>
                    </TableRow>
                  )}
                  {task.estimated_duration_minutes != null && (
                    <TableRow>
                      <TableCell component="th">
                        {t('pages.tasks.estimatedDuration')}
                      </TableCell>
                      <TableCell>{task.estimated_duration_minutes} min</TableCell>
                    </TableRow>
                  )}
                  {task.actual_duration_minutes != null && (
                    <TableRow>
                      <TableCell component="th">
                        {t('pages.tasks.actualDuration')}
                      </TableCell>
                      <TableCell>{task.actual_duration_minutes} min</TableCell>
                    </TableRow>
                  )}
                  {task.plant_key && (
                    <TableRow>
                      <TableCell component="th">{t('pages.tasks.plant')}</TableCell>
                      <TableCell>{task.plant_key}</TableCell>
                    </TableRow>
                  )}
                  {task.started_at && (
                    <TableRow>
                      <TableCell component="th">{t('pages.tasks.startedAt')}</TableCell>
                      <TableCell>
                        {new Date(task.started_at).toLocaleString()}
                      </TableCell>
                    </TableRow>
                  )}
                  {task.completed_at && (
                    <TableRow>
                      <TableCell component="th">{t('pages.tasks.completedAt')}</TableCell>
                      <TableCell>
                        {new Date(task.completed_at).toLocaleString()}
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {task.instruction && (
            <Card sx={{ mb: 2 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {t('pages.tasks.instruction')}
                </Typography>
                <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                  {task.instruction}
                </Typography>
              </CardContent>
            </Card>
          )}

          {task.completion_notes && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {t('pages.tasks.completionNotes')}
                </Typography>
                <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                  {task.completion_notes}
                </Typography>
              </CardContent>
            </Card>
          )}
        </Box>
      )}

      {/* Tab 1 (conditional): Complete task */}
      {tab === 1 && isActionable && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
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
              <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
                <Button
                  type="submit"
                  variant="contained"
                  color="success"
                  startIcon={
                    actionLoading ? <CircularProgress size={16} /> : <CheckIcon />
                  }
                  disabled={actionLoading}
                  data-testid="complete-task-submit"
                >
                  {t('pages.tasks.completeTask')}
                </Button>
              </Box>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Tab 2 (or 1 if not actionable): Edit */}
      {tab === (isActionable ? 2 : 1) && (
        <Card>
          <CardContent>
            <form onSubmit={handleEditSubmit(onSave)}>
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
              <FormSelectField
                name="priority"
                control={editControl}
                label={t('pages.tasks.priority')}
                options={priorities.map((v) => ({
                  value: v,
                  label: t(`enums.taskPriority.${v}`),
                }))}
              />
              <FormTextField
                name="due_date"
                control={editControl}
                label={t('pages.tasks.dueDate')}
                type="date"
              />
              <FormNumberField
                name="estimated_duration_minutes"
                control={editControl}
                label={t('pages.tasks.estimatedDuration')}
                min={1}
                step={1}
              />
              <FormActions
                onCancel={() => resetEdit()}
                loading={saving}
                disabled={!isDirty}
              />
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
      />
    </Box>
  );
}
