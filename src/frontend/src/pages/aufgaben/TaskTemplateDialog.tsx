import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormSwitchField from '@/components/form/FormSwitchField';
import FormActions from '@/components/form/FormActions';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as taskApi from '@/api/endpoints/tasks';
import type { TaskTemplate } from '@/api/types';

const categories = [
  'maintenance', 'watering', 'feeding', 'training', 'pest_control',
  'harvest', 'pruning', 'transplant', 'monitoring', 'cleaning',
] as const;

const triggerTypes = ['manual', 'phase_change', 'time_based', 'event_based'] as const;
const stressLevels = ['none', 'low', 'medium', 'high'] as const;
const skillLevels = ['beginner', 'intermediate', 'expert'] as const;
const timesOfDay = ['morning', 'afternoon', 'evening', 'night'] as const;

const schema = z.object({
  name: z.string().min(1).max(200),
  instruction: z.string(),
  category: z.enum(categories),
  trigger_type: z.enum(triggerTypes),
  trigger_phase: z.string().nullable(),
  days_offset: z.number().int().min(0),
  stress_level: z.enum(stressLevels),
  skill_level: z.enum(skillLevels),
  optimal_time_of_day: z.string().nullable(),
  estimated_duration_minutes: z.number().int().min(1).nullable(),
  requires_photo: z.boolean(),
  sequence_order: z.number().int().min(0),
  tools_required: z.string(),
  timer_duration_seconds: z.number().int().min(1).nullable(),
  timer_label: z.string().nullable(),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  workflowKey: string;
  template?: TaskTemplate;
  onSaved: () => void;
}

export default function TaskTemplateDialog({ open, onClose, workflowKey, template, onSaved }: Props) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);
  const isEdit = !!template;

  const { control, handleSubmit, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: '', instruction: '', category: 'maintenance', trigger_type: 'manual',
      trigger_phase: null, days_offset: 0, stress_level: 'none', skill_level: 'beginner',
      optimal_time_of_day: null, estimated_duration_minutes: null, requires_photo: false,
      sequence_order: 0, tools_required: '', timer_duration_seconds: null, timer_label: null,
    },
  });

  useEffect(() => {
    if (open && template) {
      reset({
        name: template.name, instruction: template.instruction,
        category: template.category as FormData['category'],
        trigger_type: template.trigger_type as FormData['trigger_type'],
        trigger_phase: template.trigger_phase, days_offset: template.days_offset,
        stress_level: template.stress_level as FormData['stress_level'],
        skill_level: template.skill_level as FormData['skill_level'],
        optimal_time_of_day: template.optimal_time_of_day,
        estimated_duration_minutes: template.estimated_duration_minutes,
        requires_photo: template.requires_photo, sequence_order: template.sequence_order,
        tools_required: template.tools_required.join(', '),
        timer_duration_seconds: template.timer_duration_seconds,
        timer_label: template.timer_label,
      });
    } else if (open) {
      reset({
        name: '', instruction: '', category: 'maintenance', trigger_type: 'manual',
        trigger_phase: null, days_offset: 0, stress_level: 'none', skill_level: 'beginner',
        optimal_time_of_day: null, estimated_duration_minutes: null, requires_photo: false,
        sequence_order: 0, tools_required: '', timer_duration_seconds: null, timer_label: null,
      });
    }
  }, [open, template, reset]);

  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      const tools = data.tools_required ? data.tools_required.split(',').map((t) => t.trim()).filter(Boolean) : [];
      if (isEdit && template) {
        await taskApi.updateTaskTemplate(template.key, {
          name: data.name, instruction: data.instruction, category: data.category,
          trigger_type: data.trigger_type, trigger_phase: data.trigger_phase,
          days_offset: data.days_offset, stress_level: data.stress_level,
          skill_level: data.skill_level, optimal_time_of_day: data.optimal_time_of_day,
          estimated_duration_minutes: data.estimated_duration_minutes,
          requires_photo: data.requires_photo, sequence_order: data.sequence_order,
          tools_required: tools, timer_duration_seconds: data.timer_duration_seconds,
          timer_label: data.timer_label,
        });
        notification.success(t('pages.tasks.taskTemplateUpdated'));
      } else {
        await taskApi.createTaskTemplate({
          name: data.name, instruction: data.instruction, category: data.category,
          trigger_type: data.trigger_type, trigger_phase: data.trigger_phase,
          days_offset: data.days_offset, stress_level: data.stress_level,
          skill_level: data.skill_level, optimal_time_of_day: data.optimal_time_of_day,
          estimated_duration_minutes: data.estimated_duration_minutes,
          requires_photo: data.requires_photo, sequence_order: data.sequence_order,
          tools_required: tools, workflow_template_key: workflowKey,
          timer_duration_seconds: data.timer_duration_seconds,
          timer_label: data.timer_label,
        });
        notification.success(t('pages.tasks.taskTemplateCreated'));
      }
      onSaved();
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{isEdit ? t('pages.tasks.editTaskTemplate') : t('pages.tasks.addTaskTemplate')}</DialogTitle>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
            {t('pages.tasks.sectionTask')}
          </Typography>
          <FormTextField name="name" control={control} label={t('pages.tasks.name')} required autoFocus />
          <FormTextField name="instruction" control={control} label={t('pages.tasks.instruction')} multiline rows={3} helperText={t('pages.tasks.instructionHelper')} />
          <FormSelectField name="category" control={control} label={t('pages.tasks.category')} options={categories.map((v) => ({ value: v, label: t(`enums.taskCategory.${v}`) }))} />
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
            {t('pages.tasks.sectionScheduling')}
          </Typography>
          <FormSelectField name="trigger_type" control={control} label={t('pages.tasks.triggerType')} options={triggerTypes.map((v) => ({ value: v, label: t(`enums.triggerType.${v}`) }))} />
          <FormTextField name="trigger_phase" control={control} label={t('pages.tasks.triggerPhase')} />
          <Box sx={{ display: 'flex', gap: 2 }}>
            <FormNumberField name="days_offset" control={control} label={t('pages.tasks.daysOffset')} min={0} step={1} helperText={t('pages.tasks.daysOffsetHelper')} suffix={t('common.days')} />
            <FormNumberField name="sequence_order" control={control} label={t('pages.tasks.sequenceOrder')} min={0} step={1} helperText={t('pages.tasks.sequenceOrderHelper')} />
          </Box>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <FormNumberField name="estimated_duration_minutes" control={control} label={t('pages.tasks.estimatedDuration')} min={1} step={1} helperText={t('pages.tasks.estimatedDurationHelper')} />
            <FormSelectField name="optimal_time_of_day" control={control} label={t('pages.tasks.optimalTimeOfDay')} options={[{ value: '', label: '\u2014' }, ...timesOfDay.map((v) => ({ value: v, label: t(`enums.timeOfDay.${v}`) }))]} />
          </Box>
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
            {t('pages.tasks.sectionRequirements')}
          </Typography>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <FormSelectField name="stress_level" control={control} label={t('pages.tasks.stressLevel')} options={stressLevels.map((v) => ({ value: v, label: t(`enums.stressLevel.${v}`) }))} />
            <FormSelectField name="skill_level" control={control} label={t('pages.tasks.skillLevel')} options={skillLevels.map((v) => ({ value: v, label: t(`enums.difficultyLevel.${v}`) }))} />
          </Box>
          <FormSwitchField name="requires_photo" control={control} label={t('pages.tasks.requiresPhoto')} />
          <FormTextField name="tools_required" control={control} label={t('pages.tasks.toolsRequired')} helperText={t('pages.tasks.tagsHelper')} />
          <Box sx={{ display: 'flex', gap: 2 }}>
            <FormNumberField name="timer_duration_seconds" control={control} label={t('pages.tasks.timerDuration')} min={1} step={1} helperText={t('pages.tasks.timerDurationHelper')} />
            <FormTextField name="timer_label" control={control} label={t('pages.tasks.timerLabel')} />
          </Box>
          <FormActions onCancel={onClose} loading={saving} saveLabel={isEdit ? t('common.save') : t('common.create')} />
        </form>
      </DialogContent>
    </Dialog>
  );
}
