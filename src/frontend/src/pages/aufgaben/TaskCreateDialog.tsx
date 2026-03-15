import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import Typography from '@mui/material/Typography';
import Autocomplete from '@mui/material/Autocomplete';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import TextField from '@mui/material/TextField';
import CircularProgress from '@mui/material/CircularProgress';
import DeleteIcon from '@mui/icons-material/Delete';
import { Controller, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormActions from '@/components/form/FormActions';
import FormRow from '@/components/form/FormRow';
import ExpertiseFieldWrapper from '@/components/common/ExpertiseFieldWrapper';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as taskApi from '@/api/endpoints/tasks';
import * as plantApi from '@/api/endpoints/plantInstances';
import type { PlantInstance } from '@/api/types';

const categories = [
  'maintenance', 'feeding', 'training', 'pruning', 'ausgeizen',
  'transplant', 'ipm', 'harvest', 'observation', 'care_reminder',
  'seasonal', 'phenological',
] as const;

const priorities = ['low', 'medium', 'high', 'critical'] as const;

const skillLevels = ['beginner', 'intermediate', 'advanced'] as const;

const schema = z.object({
  name: z.string().min(1).max(200),
  instruction: z.string(),
  category: z.enum(categories),
  plant_key: z.string().nullable(),
  due_date: z.string().nullable(),
  priority: z.enum(priorities),
  skill_level: z.enum(skillLevels),
  estimated_duration_minutes: z.union([z.number().int().min(1), z.literal('')]).nullable(),
  timer_duration_seconds: z.union([z.number().int().min(1), z.literal('')]).nullable(),
  timer_label: z.string().nullable(),
  tags: z.array(z.string()),
  recurrence_rule: z.string().nullable(),
  assigned_to_user_key: z.string().nullable(),
  checklist: z.array(z.object({ text: z.string(), done: z.boolean(), order: z.number() })),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export default function TaskCreateDialog({ open, onClose, onCreated }: Props) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);
  const [plants, setPlants] = useState<PlantInstance[]>([]);
  const [loadingPlants, setLoadingPlants] = useState(false);

  const { control, handleSubmit, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: '',
      instruction: '',
      category: 'maintenance',
      plant_key: null,
      due_date: null,
      priority: 'medium',
      skill_level: 'beginner',
      estimated_duration_minutes: null,
      timer_duration_seconds: null,
      timer_label: null,
      tags: [],
      recurrence_rule: null,
      assigned_to_user_key: null,
      checklist: [],
    },
  });

  const [checklistInput, setChecklistInput] = useState('');

  useEffect(() => {
    if (!open) return;
    const loadPlants = async () => {
      setLoadingPlants(true);
      try {
        const data = await plantApi.listPlantInstances(0, 200);
        setPlants(data);
      } catch (err) {
        handleError(err);
      } finally {
        setLoadingPlants(false);
      }
    };
    loadPlants();
  }, [open, handleError]);

  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      await taskApi.createTask({
        name: data.name,
        instruction: data.instruction || undefined,
        category: data.category,
        plant_key: data.plant_key,
        due_date: data.due_date,
        priority: data.priority,
        skill_level: data.skill_level,
        estimated_duration_minutes:
          typeof data.estimated_duration_minutes === 'number'
            ? data.estimated_duration_minutes
            : undefined,
        timer_duration_seconds:
          typeof data.timer_duration_seconds === 'number'
            ? data.timer_duration_seconds
            : undefined,
        timer_label: data.timer_label || undefined,
        tags: data.tags.length > 0 ? data.tags : undefined,
        recurrence_rule: data.recurrence_rule || undefined,
        assigned_to_user_key: data.assigned_to_user_key || undefined,
        checklist: data.checklist.length > 0 ? data.checklist : undefined,
      });
      notification.success(t('common.create'));
      reset();
      onCreated();
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{t('pages.tasks.createTask')}</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.tasks.createIntro')}
        </Typography>
        <form onSubmit={handleSubmit(onSubmit)}>
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
            {t('pages.tasks.sectionTask')}
          </Typography>
          <FormTextField
            name="name"
            control={control}
            label={t('pages.tasks.name')}
            required
            autoFocus
          />
          <FormTextField
            name="instruction"
            control={control}
            label={t('pages.tasks.instruction')}
            multiline
            rows={3}
            helperText={t('pages.tasks.instructionHelper')}
          />
          <FormSelectField
            name="category"
            control={control}
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
              control={control}
              label={t('pages.tasks.dueDate')}
              type="date"
            />
            <FormSelectField
              name="priority"
              control={control}
              label={t('pages.tasks.priority')}
              helperText={t('pages.tasks.priorityHelper')}
              options={priorities.map((v) => ({
                value: v,
                label: t(`enums.taskPriority.${v}`),
              }))}
            />
          </FormRow>
          <ExpertiseFieldWrapper minLevel="intermediate">
            <FormSelectField
              name="skill_level"
              control={control}
              label={t('pages.tasks.skillLevel')}
              options={skillLevels.map((v) => ({
                value: v,
                label: t(`enums.skillLevel.${v}`),
              }))}
            />
          </ExpertiseFieldWrapper>
          <FormNumberField
            name="estimated_duration_minutes"
            control={control}
            label={t('pages.tasks.estimatedDuration')}
            min={1}
            step={1}
            helperText={t('pages.tasks.estimatedDurationHelper')}
            suffix="min"
          />
          <ExpertiseFieldWrapper minLevel="intermediate">
            <FormTextField
              name="recurrence_rule"
              control={control}
              label={t('pages.tasks.recurrenceRule')}
              helperText={t('pages.tasks.recurrenceRuleHelper')}
            />
          </ExpertiseFieldWrapper>
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
            {t('pages.tasks.sectionAssignment')}
          </Typography>
          <Controller
            name="plant_key"
            control={control}
            render={({ field }) => (
              <Autocomplete
                options={plants}
                getOptionLabel={(p) =>
                  p.plant_name
                    ? `${p.instance_id} - ${p.plant_name}`
                    : p.instance_id
                }
                loading={loadingPlants}
                value={plants.find((p) => p.key === field.value) ?? null}
                onChange={(_, value) => field.onChange(value?.key ?? null)}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label={t('pages.tasks.plant')}
                    sx={{ mb: 2 }}
                    slotProps={{
                      input: {
                        ...params.InputProps,
                        endAdornment: (
                          <>
                            {loadingPlants && <CircularProgress size={16} />}
                            {params.InputProps.endAdornment}
                          </>
                        ),
                      },
                    }}
                    data-testid="form-field-plant_key"
                  />
                )}
              />
            )}
          />
          <ExpertiseFieldWrapper minLevel="intermediate">
            <FormTextField
              name="assigned_to_user_key"
              control={control}
              label={t('pages.tasks.assignedTo')}
              helperText={t('pages.tasks.assignedToHelper')}
            />
            <FormNumberField
              name="timer_duration_seconds"
              control={control}
              label={t('pages.tasks.timerDuration')}
              min={1}
              step={1}
              helperText={t('pages.tasks.timerDurationHelper')}
            />
            <FormTextField
              name="timer_label"
              control={control}
              label={t('pages.tasks.timerLabel')}
            />
            <Controller
              name="tags"
              control={control}
              render={({ field }) => (
                <Autocomplete
                  multiple
                  freeSolo
                  options={[]}
                  value={field.value}
                  onChange={(_, value) => field.onChange(value)}
                  renderTags={(value, getTagProps) =>
                    value.map((tag, idx) => (
                      <Chip
                        {...getTagProps({ index: idx })}
                        key={tag}
                        label={tag}
                        size="small"
                      />
                    ))
                  }
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label={t('pages.tasks.tags')}
                      helperText={t('pages.tasks.tagsHelper')}
                      sx={{ mb: 2 }}
                    />
                  )}
                />
              )}
            />
          </ExpertiseFieldWrapper>
          <Controller
            name="checklist"
            control={control}
            render={({ field }) => (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
                  {t('pages.tasks.checklist')}
                </Typography>
                {field.value.length > 0 && (
                  <List dense disablePadding>
                    {field.value.map((item, idx) => (
                      <ListItem
                        key={idx}
                        secondaryAction={
                          <IconButton
                            edge="end"
                            size="small"
                            onClick={() => {
                              const next = field.value.filter((_, i) => i !== idx);
                              field.onChange(next.map((it, i) => ({ ...it, order: i })));
                            }}
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        }
                        disablePadding
                        sx={{ pl: 1 }}
                      >
                        <ListItemText primary={item.text} />
                      </ListItem>
                    ))}
                  </List>
                )}
                <TextField
                  size="small"
                  fullWidth
                  placeholder={t('pages.tasks.addChecklistItem')}
                  value={checklistInput}
                  onChange={(e) => setChecklistInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && checklistInput.trim()) {
                      e.preventDefault();
                      field.onChange([
                        ...field.value,
                        { text: checklistInput.trim(), done: false, order: field.value.length },
                      ]);
                      setChecklistInput('');
                    }
                  }}
                />
              </Box>
            )}
          />
          <FormActions
            onCancel={onClose}
            loading={saving}
            saveLabel={t('common.create')}
          />
        </form>
      </DialogContent>
    </Dialog>
  );
}
